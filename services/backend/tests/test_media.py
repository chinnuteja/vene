import asyncio
from datetime import timedelta
from uuid import UUID,uuid4
import jwt
import pytest
from sqlalchemy.orm import Session
from bring_vene.auth import COOKIE,FIXTURE_VISIT,FIXTURE_MEMBERS
from bring_vene.config import Settings
from bring_vene.domain.service import utc_now
from bring_vene.main import create_app
from bring_vene.persistence.models import CallRecord
from bring_vene.voice import service
from bring_vene.voice.supervisor import TrackSupervisor
from helpers import authenticated_client

BASE=f'/encounters/{FIXTURE_VISIT}/call'
SETTINGS=Settings(livekit_url='ws://127.0.0.1:7880',livekit_api_key='test-key',
                  livekit_api_secret='test-only-signing-secret-at-least-32-bytes',voice_provider='fixture')


def control(client,action,**fields):
    state=client.get(BASE).json()
    return client.post(BASE+'/controls',json={'command_id':str(uuid4()),'expected_revision':state['revision'],
                                             'type':action,**fields})


def agree(client,connection,decision='agreed'):
    return client.post(BASE+'/consent',json={'command_id':str(uuid4()),'connection_id':connection,
                                          'decision':decision,'terms_version':'voice-processing-v1'})


def room(engine):
    app=create_app(settings=SETTINGS,engine=engine)
    patient,doctor=authenticated_client(app),authenticated_client(app,'clinician')
    one,two=patient.post(BASE+'/admit').json(),doctor.post(BASE+'/admit').json()
    generation=UUID(two['call']['generation'])
    identities={'human:'+one['connection_id'],'human:'+two['connection_id']}
    tracks={'human:'+one['connection_id']:'TR_patient','human:'+two['connection_id']:'TR_doctor'}
    service.sync_room(engine,FIXTURE_VISIT,generation,identities,tracks,0,True)
    return patient,doctor,one,two,generation,identities,tracks


def frame(engine,patient,connection,generation,**overrides):
    state=patient.get(BASE).json()
    row=next(p for p in state['participants'] if p['connection_id']==connection)
    args={'engine':engine,'visit_id':FIXTURE_VISIT,'generation':generation,'connection_id':UUID(connection),
          'track_sid':'TR_patient','track_epoch':row['track_epoch'],'consent_epoch':state['consent_epoch'],
          'samples':320,'non_silent':True}
    args.update(overrides)
    return service.accept_frame(**args)


def test_admission_is_bound_to_membership_room_and_server_verified_media(visit_engine):
    app=create_app(settings=SETTINGS,engine=visit_engine)
    doctor=authenticated_client(app,'clinician')
    result=doctor.post(BASE+'/admit',json={'role':'patient','identity':'attacker','room':'other'}).json()
    claims=jwt.decode(result['token'],SETTINGS.livekit_api_secret,algorithms=['HS256'])
    assert claims['sub']=='human:'+result['connection_id']
    assert claims['name']=='Dr. Chris Chen'
    assert claims['video']['room']==f"vene-{FIXTURE_VISIT}-{result['call']['generation']}"
    assert claims['video']['canPublish'] is False and claims['video']['canSubscribe'] is True
    assert claims['video']['canPublishData'] is False and claims['video']['canPublishSources']==[]
    assert not claims['video'].get('roomRecord',False) and not claims['video'].get('roomAdmin',False)
    assert claims['exp']-claims['nbf']<=120
    assert doctor.post(f'/encounters/{uuid4()}/call/admit').status_code==404
    from fastapi.testclient import TestClient
    assert TestClient(app).post(BASE+'/admit',headers={'x-vene-intent':'mutation'}).status_code==401


def test_no_frames_before_all_consent_or_after_pause(visit_engine):
    p,d,one,two,generation,_,_=room(visit_engine)
    assert not frame(visit_engine,p,one['connection_id'],generation)
    agree(p,one['connection_id']);agree(d,two['connection_id'],'declined')
    assert control(p,'resume').status_code==409
    assert not frame(visit_engine,p,one['connection_id'],generation)
    agree(d,two['connection_id'])
    assert control(p,'resume').status_code==200
    assert frame(visit_engine,p,one['connection_id'],generation)
    assert control(p,'pause').status_code==200
    assert not frame(visit_engine,p,one['connection_id'],generation)
    assert p.get(BASE+'/diagnostics').json()['receipts'][0]['frames']==1


def test_silencing_output_does_not_pause_processing(visit_engine):
    p,d,one,two,generation,_,_=room(visit_engine)
    agree(p,one['connection_id']);agree(d,two['connection_id']);control(p,'resume')
    silent=control(p,'silence',silenced=True)
    assert silent.status_code==200 and silent.json()['output_silenced']
    assert silent.json()['manual_pause'] is False
    assert frame(visit_engine,p,one['connection_id'],generation)


def test_own_connection_only_and_guest_cannot_resume_end_or_read_transcripts(visit_engine):
    p,d,one,two,_,_,_=room(visit_engine)
    assert agree(d,one['connection_id']).status_code==404
    for action in ['resume','end','silence']:
        assert control(d,action,silenced=True if action=='silence' else None).status_code==403
    assert control(d,'pause').status_code==200
    assert d.get(BASE+'/utterances').status_code==403
    assert d.get(BASE+'/diagnostics').status_code==403


def test_late_arrival_pauses_and_requires_its_own_consent(visit_engine):
    p,d,one,two,generation,identities,tracks=room(visit_engine)
    agree(p,one['connection_id']);agree(d,two['connection_id']);control(p,'resume')
    app=create_app(settings=SETTINGS,engine=visit_engine)
    family=authenticated_client(app,'family');third=family.post(BASE+'/admit').json()
    identities.add('human:'+third['connection_id'])
    service.sync_room(visit_engine,FIXTURE_VISIT,generation,identities,tracks,0,True)
    assert p.get(BASE).json()['manual_pause']
    assert control(p,'resume').status_code==409
    assert not frame(visit_engine,p,one['connection_id'],generation)
    agree(family,third['connection_id'])
    assert control(p,'resume').status_code==200


def test_late_transcript_cannot_write_after_consent_change_or_track_change(visit_engine):
    p,d,one,two,generation,identities,tracks=room(visit_engine)
    agree(p,one['connection_id']);agree(d,two['connection_id']);control(p,'resume')
    old=p.get(BASE).json();row=next(c for c in old['participants'] if c['connection_id']==one['connection_id'])
    args=(visit_engine,FIXTURE_VISIT,generation,UUID(one['connection_id']),'TR_patient',row['track_epoch'],old['consent_epoch'])
    assert service.finalize(*args,'A synthetic finalized utterance for a domain test.')
    control(p,'pause');assert not service.finalize(*args,'PRIVATE_CANARY_LATE_CALLBACK')
    tracks['human:'+one['connection_id']]='TR_reconnected'
    service.sync_room(visit_engine,FIXTURE_VISIT,generation,identities,tracks,0,True)
    new=p.get(BASE).json();new_row=next(c for c in new['participants'] if c['connection_id']==one['connection_id'])
    assert new_row['track_epoch']>row['track_epoch'] and new_row['consent']=='pending'
    assert not service.finalize(*args,'PRIVATE_CANARY_OLD_TRACK')
    assert len(p.get(BASE+'/utterances').json())==1
    assert 'PRIVATE_CANARY' not in p.get(BASE+'/utterances').text


def test_call_command_replay_is_idempotent_and_changed_replay_rejected(visit_engine):
    p,d,one,two,_,_,_=room(visit_engine)
    body={'command_id':str(uuid4()),'connection_id':one['connection_id'],'decision':'agreed','terms_version':'voice-processing-v1'}
    first=p.post(BASE+'/consent',json=body).json();second=p.post(BASE+'/consent',json=body).json()
    assert first['revision']==second['revision'] and first['consent_epoch']==second['consent_epoch']
    body['decision']='declined';assert p.post(BASE+'/consent',json=body).status_code==409
    assert d.post(BASE+'/consent',json=body).status_code==404


def test_revoked_membership_ends_old_room_and_blocks_new_admission(visit_engine):
    p,d,_,_,_,_,_=room(visit_engine)
    response=p.post(f'/encounters/{FIXTURE_VISIT}/members/{FIXTURE_MEMBERS["clinician"]}/revoke')
    assert response.status_code==200
    assert p.get(BASE).json()['state']=='ended'
    assert d.post(BASE+'/admit').status_code==401
    assert d.get(BASE).status_code==401


def test_reconnect_and_new_room_generation_do_not_reuse_old_authority(visit_engine):
    p,d,one,two,generation,_,_=room(visit_engine)
    old=one['connection_id'];new=p.post(BASE+'/admit').json()
    assert new['connection_id']!=old
    assert agree(p,old).status_code==404
    control(p,'end');assert d.post(BASE+'/admit').status_code==409
    fresh=p.post(BASE+'/admit').json()
    assert fresh['call']['generation']!=str(generation)
    assert agree(p,new['connection_id']).status_code==404


def test_provider_failure_has_no_fixture_fallback_and_stale_worker_stays_closed(visit_engine):
    p,d,one,two,generation,_,_=room(visit_engine)
    agree(p,one['connection_id']);agree(d,two['connection_id'])
    service.worker_failed(visit_engine,FIXTURE_VISIT,generation,'stt_unavailable')
    assert p.get(BASE).json()['state']=='unavailable'
    assert control(p,'resume').status_code==503
    assert not frame(visit_engine,p,one['connection_id'],generation)
    live=create_app(settings=Settings(livekit_url=SETTINGS.livekit_url,livekit_api_key=SETTINGS.livekit_api_key,
        livekit_api_secret=SETTINGS.livekit_api_secret,voice_provider='deepgram',deepgram_api_key=''),engine=visit_engine)
    client=authenticated_client(live)
    assert client.get(BASE).json()['provider']=='unavailable'
    with Session(visit_engine) as session,session.begin():
        call=session.get(CallRecord,FIXTURE_VISIT);call.worker_error=None;call.worker_seen_at=utc_now()-timedelta(seconds=10)
    assert client.get(BASE).json()['state']=='unavailable'


def test_transport_recovery_gets_a_new_generation_and_fences_old_connections(visit_engine):
    p,d,one,two,generation,_,_=room(visit_engine)
    # Real server loss leaves no verified present humans in the old room.
    service.sync_room(visit_engine,FIXTURE_VISIT,generation,set(),{},0,True)
    service.worker_failed(visit_engine,FIXTURE_VISIT,generation,'media_unavailable')
    fresh=p.post(BASE+'/admit')
    assert fresh.status_code==200
    assert fresh.json()['call']['generation']!=str(generation)
    assert fresh.json()['call']['manual_pause'] is True
    assert agree(d,two['connection_id']).status_code==404
    assert agree(p,one['connection_id']).status_code==404


def test_assistant_connection_failure_does_not_replace_a_healthy_human_room_for_a_guest(visit_engine):
    p,d,_,_,generation,_,_=room(visit_engine)
    service.worker_failed(visit_engine,FIXTURE_VISIT,generation,'media_unavailable')
    family=authenticated_client(create_app(settings=SETTINGS,engine=visit_engine),'family')
    fresh=family.post(BASE+'/admit');assert fresh.status_code==200
    assert fresh.json()['call']['generation']==str(generation)
    assert fresh.json()['call']['manual_pause'] and not fresh.json()['call']['worker_ready']
    assert p.get(BASE).json()['generation']==str(generation)


def test_leaving_during_startup_and_repeated_cycles_leave_no_orphan_tasks():
    async def scenario():
        startup=asyncio.Event();released=[];created=[]
        async def consume(key,track):
            try:
                await startup.wait();created.append(key);await asyncio.Event().wait()
            finally:released.append(key)
        supervisor=TrackSupervisor(consume)
        for index in range(30):
            key=('participant','track',index)
            supervisor.start(key,None);supervisor.start(key,None)
            await asyncio.sleep(0)
            assert len(supervisor.tasks)==1
            await supervisor.retain(set())
            assert not supervisor.tasks
        assert not created and len(released)==30
        startup.set();supervisor.start(('participant','new-track',31),None)
        await asyncio.sleep(0);assert len(supervisor.tasks)==1
        await supervisor.close();assert not supervisor.tasks
    asyncio.run(scenario())


def test_human_admission_verifies_without_claiming_assistant_readiness(visit_engine,monkeypatch):
    from types import SimpleNamespace
    from livekit import api
    calls=[]
    class Control:
        def __init__(self,*args,**kwargs):self.room=self
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def get_participant(self,request):calls.append('presence');return SimpleNamespace(identity=request.identity)
        async def update_participant(self,request):calls.append(request.permission)
    monkeypatch.setattr(api,'LiveKitAPI',Control)
    p=authenticated_client(create_app(settings=SETTINGS,engine=visit_engine))
    admission=p.post(BASE+'/admit').json()
    response=p.post(BASE+'/connections/'+admission['connection_id']+'/verify')
    assert response.status_code==200
    state=response.json();assert not state['worker_ready'] and state['manual_pause']
    assert state['participants'][0]['present'] and state['participants'][0]['consent']=='pending'
    assert calls[0]=='presence' and calls[1].can_publish and not calls[1].can_publish_data
    assert list(calls[1].can_publish_sources)==[api.TrackSource.MICROPHONE]


def test_guest_cannot_verify_another_session_admission(visit_engine,monkeypatch):
    from livekit import api
    calls=[]
    monkeypatch.setattr(api,'LiveKitAPI',lambda *args,**kwargs:calls.append(True))
    app=create_app(settings=SETTINGS,engine=visit_engine)
    p,d=authenticated_client(app),authenticated_client(app,'clinician')
    admission=p.post(BASE+'/admit').json()
    assert d.post(BASE+'/connections/'+admission['connection_id']+'/verify').status_code==404
    assert not calls


@pytest.mark.parametrize('failure',['provider','identity'])
def test_unverified_media_never_grants_publish_permission(visit_engine,monkeypatch,failure):
    from types import SimpleNamespace
    from livekit import api
    granted=[]
    class Control:
        def __init__(self,*args,**kwargs):self.room=self
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def get_participant(self,request):
            if failure=='provider':raise RuntimeError('PRIVATE_MEDIA_ERROR')
            return SimpleNamespace(identity='another-person')
        async def update_participant(self,request):granted.append(True)
    monkeypatch.setattr(api,'LiveKitAPI',Control)
    p=authenticated_client(create_app(settings=SETTINGS,engine=visit_engine))
    admission=p.post(BASE+'/admit').json()
    response=p.post(BASE+'/connections/'+admission['connection_id']+'/verify')
    assert response.status_code==(503 if failure=='provider' else 404)
    assert not granted and 'PRIVATE_MEDIA_ERROR' not in response.text


def test_slow_admission_rpc_is_bounded_and_its_client_is_closed(visit_engine,monkeypatch):
    import time
    from livekit import api
    closed=[];granted=[]
    class Control:
        def __init__(self,*args,**kwargs):self.room=self
        async def __aenter__(self):return self
        async def __aexit__(self,*args):closed.append(True)
        async def get_participant(self,request):await asyncio.sleep(10)
        async def update_participant(self,request):granted.append(True)
    monkeypatch.setattr(api,'LiveKitAPI',Control)
    p=authenticated_client(create_app(settings=SETTINGS,engine=visit_engine));admission=p.post(BASE+'/admit').json()
    started=time.monotonic();response=p.post(BASE+'/connections/'+admission['connection_id']+'/verify')
    assert response.status_code==503 and time.monotonic()-started<4.5
    assert closed==[True] and not granted


def test_audio_batch_rechecks_current_authority_and_preserves_activity_windows(visit_engine):
    p,d,one,two,generation,_,_=room(visit_engine)
    batch={'samples':1600,'activity':[False,True,True,True,False]}
    assert not frame(visit_engine,p,one['connection_id'],generation,**batch)
    agree(p,one['connection_id']);agree(d,two['connection_id']);control(p,'resume')
    assert frame(visit_engine,p,one['connection_id'],generation,**batch)
    receipt=p.get(BASE+'/diagnostics').json()['receipts'][0]
    assert receipt['frames']==5 and receipt['samples']==1600 and receipt['non_silent_frames']==3
    control(p,'pause')
    assert not frame(visit_engine,p,one['connection_id'],generation,**batch)
    assert p.get(BASE+'/diagnostics').json()['receipts'][0]['samples']==1600
