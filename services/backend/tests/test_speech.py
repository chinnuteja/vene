import asyncio
from datetime import timedelta
from uuid import uuid4,UUID
import pytest
from sqlalchemy.orm import Session
from bring_vene.auth import FIXTURE_VISIT,COOKIE,digest
from bring_vene.config import Settings
from bring_vene.main import create_app
from bring_vene.domain.service import utc_now
from bring_vene.persistence.models import SpeechStateRecord,CueRecord,SpeechDeliveryRecord,EncounterRecord,SessionRecord
from bring_vene.speech import service
from bring_vene.speech.player import SpeechController
from test_media import room,agree as processing_agree,control,BASE as CALL_BASE,SETTINGS as MEDIA_SETTINGS
from helpers import authenticated_client

BASE=f'/encounters/{FIXTURE_VISIT}/speech'
SETTINGS=Settings.model_validate({**MEDIA_SETTINGS.model_dump(),'bring_vene_development':True,'speech_cooldown_seconds':0})


def command(c,path,**fields):
    response=c.post(BASE+path,json={'command_id':str(uuid4()),**fields})
    assert response.status_code==200,response.text
    return response.json()


def environment(engine):
    original,doctor,one,two,generation,_,_=room(engine)
    # The same server-issued connections, with a separate speaking API configuration.
    patient=authenticated_client(create_app(settings=SETTINGS,engine=engine))
    patient.cookies.set(COOKIE,original.cookies.get(COOKIE));patient.headers['x-vene-csrf']=original.headers['x-vene-csrf']
    processing_agree(patient,one['connection_id']);processing_agree(doctor,two['connection_id']);control(patient,'resume')
    with Session(engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);value=dict(record.projection)
        value['preparation_approved']=True
        value['priorities']=[{**p,'approved':p['selected'],'audiences':['clinician']} for p in value['priorities']]
        record.projection=value
    mode=command(patient,'/mode',mode='on_request')
    command(patient,'/agreement',connection_id=one['connection_id'],mode_revision=mode['mode_revision'],agreed=True)
    command(doctor,'/agreement',connection_id=two['connection_id'],mode_revision=mode['mode_revision'],agreed=True)
    return patient,doctor,one,two,generation


def cues(patient):return command(patient,'/actions',type='refresh')['cues']


def approve(patient,cue):return command(patient,'/approve',cue_id=cue['id'],digest=cue['digest'])


def test_private_cues_never_appear_in_guest_payloads_and_guest_cannot_approve(visit_engine):
    p,d,_,_,_=environment(visit_engine);queue=cues(p);assert queue
    assert not d.get(BASE).json()['cues']
    assert queue[0]['suggestion'] not in d.get(BASE).text
    assert d.post(BASE+'/approve',json={'command_id':str(uuid4()),'cue_id':queue[0]['id'],'digest':queue[0]['digest']}).status_code==403
    assert d.post(BASE+'/mode',json={'command_id':str(uuid4()),'mode':'closeout'}).status_code==403


def test_agreement_is_own_connection_and_mode_changes_require_new_agreement(visit_engine):
    p,d,one,two,_=environment(visit_engine);mode=p.get(BASE).json()
    assert d.post(BASE+'/agreement',json={'command_id':str(uuid4()),'connection_id':one['connection_id'],'mode_revision':mode['mode_revision'],'agreed':True}).status_code==404
    command(p,'/mode',mode='closeout');queue=cues(p);assert not queue[0]['eligible_to_speak']
    assert d.post(BASE+'/agreement',json={'command_id':str(uuid4()),'connection_id':two['connection_id'],'mode_revision':mode['mode_revision'],'agreed':True}).status_code==409


@pytest.mark.parametrize('change',['answer','scope','correction','expired','session'])
def test_stale_or_unauthorized_candidate_cannot_be_spoken(visit_engine,change):
    p,d,_,_,generation=environment(visit_engine);cue=cues(p)[0];approve(p,cue)
    with Session(visit_engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);value=dict(record.projection)
        if change=='answer':value['priorities']=[{**q,'status':'answered'} for q in value['priorities']]
        elif change=='scope':value['priorities']=[{**q,'audiences':[]} for q in value['priorities']]
        elif change=='correction':value['version']+=1;record.version=value['version']
        elif change=='expired':session.get(CueRecord,UUID(cue['id'])).expires_at=utc_now()-timedelta(seconds=1)
        else:session.get(SessionRecord,digest(p.cookies.get(COOKIE))).revoked_at=utc_now()
        record.projection=value
    assert service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS) is None
    with Session(visit_engine) as session:
        delivery=session.query(SpeechDeliveryRecord).one();assert delivery.state=='cancelled' and delivery.first_audio_at is None


def test_dedup_and_replayed_approval_produce_one_delivery(visit_engine):
    p,_,_,_,_=environment(visit_engine);one=cues(p);two=cues(p)
    assert [q['id'] for q in one]==[q['id'] for q in two] and len(one)<=8
    payload={'command_id':str(uuid4()),'cue_id':one[0]['id'],'digest':one[0]['digest']}
    assert p.post(BASE+'/approve',json=payload).status_code==200
    assert p.post(BASE+'/approve',json=payload).status_code==200
    with Session(visit_engine) as session:assert session.query(SpeechDeliveryRecord).count()==1


def test_quiet_floor_false_start_and_overlap_do_not_create_an_automatic_turn(visit_engine):
    p,_,one,two,generation=environment(visit_engine);cue=cues(p)[0];approve(p,cue)
    with Session(visit_engine) as session,session.begin():
        for _ in range(3):service.observe_audio(session,FIXTURE_VISIT,UUID(one['connection_id']),True)
    assert service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS) is None
    with Session(visit_engine) as session,session.begin():session.get(SpeechStateRecord,FIXTURE_VISIT).last_human_at=utc_now()-timedelta(seconds=2)
    delivery=service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS);assert delivery
    with Session(visit_engine) as session,session.begin():
        service.observe_audio(session,FIXTURE_VISIT,UUID(one['connection_id']),True)
    assert service.permit_playback(visit_engine,FIXTURE_VISIT,delivery['id'],SETTINGS)[0]
    with Session(visit_engine) as session,session.begin():
        service.observe_audio(session,FIXTURE_VISIT,UUID(two['connection_id']),True)
        service.observe_audio(session,FIXTURE_VISIT,UUID(two['connection_id']),True)
        service.observe_audio(session,FIXTURE_VISIT,UUID(two['connection_id']),True)
    assert service.permit_playback(visit_engine,FIXTURE_VISIT,delivery['id'],SETTINGS)==(False,'human_interruption')


def test_slow_generation_cancels_on_pause_without_saving_unplayed_text(visit_engine):
    p,_,_,_,generation=environment(visit_engine);approve(p,cues(p)[0]);closed=[]
    class SlowSpeaker:
        played_ms=0
        async def play(self,_):
            try:await asyncio.Event().wait()
            finally:closed.append(True)
        def interrupt(self):pass
        async def close(self):pass
    async def scenario():
        controller=SpeechController(None,visit_engine,FIXTURE_VISIT,generation,SETTINGS,SlowSpeaker())
        await controller.tick();await asyncio.sleep(.01);assert controller.busy()
        control(p,'pause');await controller.tick();assert not controller.busy();await controller.close()
    asyncio.run(scenario());assert closed
    receipt=p.get(BASE).json()['receipts'][0]
    assert receipt['state']=='interrupted' and receipt['played_text'] is None and receipt['played_ms']==0


def test_other_addressee_silence_and_quoted_invitation_do_not_authorize_speech(visit_engine):
    from bring_vene.understanding.contracts import FixtureTurn
    from bring_vene.understanding.service import fixture_turn
    p,_,_,_,_=environment(visit_engine)
    for text in ['Maria, can you clarify the lab question?', '"Vene, help with that question," is what she said.', 'It has been quiet for a long time.']:
        fixture_turn(visit_engine,FIXTURE_VISIT,p.cookies.get(COOKIE),p.headers['x-vene-csrf'],FixtureTurn(command_id=uuid4(),speaker='patient',text=text),SETTINGS)
    with Session(visit_engine) as session:assert session.query(SpeechDeliveryRecord).count()==0


def test_direct_invitation_uses_standing_permission_and_cannot_expand_scope(visit_engine):
    from bring_vene.understanding.contracts import FixtureTurn
    from bring_vene.understanding.service import fixture_turn
    p,_,_,_,_=environment(visit_engine)
    fixture_turn(visit_engine,FIXTURE_VISIT,p.cookies.get(COOKIE),p.headers['x-vene-csrf'],FixtureTurn(command_id=uuid4(),speaker='patient',text='Vene, help us return to my question.'),SETTINGS)
    with Session(visit_engine) as session:
        delivery=session.query(SpeechDeliveryRecord).one();assert delivery.content['standing_mode'] is True
        assert delivery.content['text'].startswith('Could we come back')


def test_interrupted_audio_receipt_has_no_full_text_and_revoked_scope_hides_completed_text(visit_engine):
    p,d,_,_,generation=environment(visit_engine);approve(p,cues(p)[0]);delivery=service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS)
    service.first_audio(visit_engine,FIXTURE_VISIT,delivery['id']);service.finish(visit_engine,FIXTURE_VISIT,delivery['id'],'interrupted',130,'human_interruption')
    assert p.get(BASE).json()['receipts'][0]['played_text'] is None
    assert not p.get(BASE).json()['receipts'][0]['hearing_confirmed']


def test_tts_failure_preserves_human_call_and_never_falls_back(visit_engine):
    p,_,_,_,generation=environment(visit_engine);approve(p,cues(p)[0])
    class BrokenSpeaker:
        played_ms=0
        async def play(self,_):raise RuntimeError('PRIVATE_PROVIDER_ERROR')
        def interrupt(self):pass
        async def close(self):pass
    async def scenario():
        controller=SpeechController(None,visit_engine,FIXTURE_VISIT,generation,SETTINGS,BrokenSpeaker())
        await controller.tick();await controller.task;await controller.close()
    asyncio.run(scenario())
    state=p.get(BASE).json();assert state['receipts'][0]['state']=='failed' and state['receipts'][0]['reason']=='tts_unavailable'
    assert p.get(CALL_BASE).json()['state']=='active' and 'PRIVATE_PROVIDER_ERROR' not in str(state)
    assert service.provider(Settings(tts_provider='cartesia',cartesia_api_key=''))[0]=='unavailable'


def test_revocation_then_reagreement_does_not_resurrect_an_old_approval(visit_engine):
    p,d,_,two,generation=environment(visit_engine);approve(p,cues(p)[0]);mode=p.get(BASE).json()
    command(d,'/agreement',connection_id=two['connection_id'],mode_revision=mode['mode_revision'],agreed=False)
    command(d,'/agreement',connection_id=two['connection_id'],mode_revision=mode['mode_revision'],agreed=True)
    assert service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS) is None
    assert p.get(BASE).json()['receipts'][0]['state']=='cancelled'


def test_expired_suggestion_gets_a_new_issuance_and_old_approval_stays_invalid(visit_engine):
    p,_,_,_,_=environment(visit_engine);old=cues(p)[0]
    with Session(visit_engine) as session,session.begin():session.get(CueRecord,UUID(old['id'])).expires_at=utc_now()-timedelta(seconds=1)
    fresh=cues(p)[0];assert fresh['id']!=old['id'] and fresh['digest']!=old['digest']
    assert p.post(BASE+'/approve',json={'command_id':str(uuid4()),'cue_id':old['id'],'digest':old['digest']}).status_code==409


@pytest.mark.parametrize('shared',[False,True])
def test_closeout_requires_shared_sources_and_does_not_confirm_actions(visit_engine,shared):
    p,d,one,two,generation=environment(visit_engine)
    with Session(visit_engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);value=dict(record.projection)
        source=value['evidence'][0];source['audiences']=['clinician'] if shared else []
        value['plan']=[{**value['plan'][0],'origin':'interpretation','audiences':['clinician'],
            'evidence_refs':[source['id']],'owner':'Clinic team','timeframe':'Needs confirmation'}]
        record.projection=value
    mode=command(p,'/mode',mode='closeout')
    for client,connection in [(p,one),(d,two)]:
        command(client,'/agreement',connection_id=connection['connection_id'],mode_revision=mode['mode_revision'],agreed=True)
    response=p.post(BASE+'/actions',json={'command_id':str(uuid4()),'type':'closeout'})
    assert response.status_code==(200 if shared else 409)
    if shared:
        delivery=service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS)
        assert 'proposed next steps, not completed actions' in delivery['text']
        assert 'confirm the required orders' in delivery['text']
        assert not p.get(f'/encounters/{FIXTURE_VISIT}').json()['plan'][0]['external_completed']
    else:
        with Session(visit_engine) as session:assert session.query(SpeechDeliveryRecord).count()==0



def test_closeout_filters_private_steps_before_selecting_public_steps(visit_engine):
    p,d,one,two,generation=environment(visit_engine)
    with Session(visit_engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);value=dict(record.projection)
        source=value['evidence'][0];source['audiences']=['clinician']
        template={**value['plan'][0],'origin':'interpretation','evidence_refs':[source['id']]}
        value['plan']=[{**template,'id':str(uuid4()),'title':'PRIVATE_STEP_'+str(n),'audiences':[]} for n in range(3)]
        value['plan'].append({**template,'id':str(uuid4()),'title':'Shared lab visit','audiences':['clinician']})
        record.projection=value
    mode=command(p,'/mode',mode='closeout')
    for client,connection in [(p,one),(d,two)]:
        command(client,'/agreement',connection_id=connection['connection_id'],mode_revision=mode['mode_revision'],agreed=True)
    command(p,'/actions',type='closeout')
    delivery=service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS)
    assert delivery and 'Shared lab visit' in delivery['text'] and 'PRIVATE_STEP' not in delivery['text']
    assert 'PRIVATE_STEP' not in d.get(BASE).text

def test_worker_restart_cancels_unknown_playout_instead_of_replaying(visit_engine):
    p,_,_,_,generation=environment(visit_engine);approve(p,cues(p)[0])
    delivery=service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS)
    service.first_audio(visit_engine,FIXTURE_VISIT,delivery['id'])
    service.recover(visit_engine,FIXTURE_VISIT,generation)
    receipt=p.get(BASE).json()['receipts'][0]
    assert receipt['state']=='cancelled' and receipt['played_text'] is None
    assert receipt['reason']=='worker_restarted_playout_unknown'
    assert service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS) is None


def test_permission_fence_only_emits_after_commit_and_has_no_private_payload(visit_engine):
    from bring_vene.speech.fence import SpeechFence
    seen=[]
    async def scenario():
        fence=SpeechFence(visit_engine,FIXTURE_VISIT,seen.append);await fence.start()
        try:
            with Session(visit_engine) as session:
                record=session.get(EncounterRecord,FIXTURE_VISIT);record.version+=1;session.flush()
                await asyncio.sleep(.05);assert seen==[];session.rollback()
            await asyncio.sleep(.05);assert seen==[]
            with Session(visit_engine) as session,session.begin():session.get(EncounterRecord,FIXTURE_VISIT).version+=1
            for _ in range(50):
                if seen:break
                await asyncio.sleep(.02)
            assert seen==['context_changed'] and fence.healthy
        finally:await fence.close()
    asyncio.run(scenario())


def test_losing_owned_permission_listener_fails_closed(visit_engine):
    from bring_vene.speech.fence import SpeechFence
    from sqlalchemy import text
    seen=[]
    async def scenario():
        fence=SpeechFence(visit_engine,FIXTURE_VISIT,seen.append);await fence.start()
        try:
            # This PID belongs to this test's dedicated listener, never a shared process.
            with visit_engine.begin() as connection:
                connection.execute(text('SELECT pg_terminate_backend(:pid)'),{'pid':fence.connection.info.backend_pid})
            for _ in range(50):
                if seen:break
                await asyncio.sleep(.02)
            assert seen==['authorization_channel_lost'] and not fence.healthy
        finally:await fence.close()
    asyncio.run(scenario())


def test_waiting_scope_snapshot_reads_the_reopened_generation(visit_engine):
    from concurrent.futures import ThreadPoolExecutor
    import threading,time
    from sqlalchemy import select,text
    from bring_vene.persistence.models import CallRecord
    from bring_vene.voice import service as media
    environment(visit_engine)
    with Session(visit_engine) as session,session.begin():session.get(CallRecord,FIXTURE_VISIT).ended=True
    expected=uuid4();ready=threading.Event()
    def reader():
        with Session(visit_engine) as session,session.begin():
            session.execute(text("SET LOCAL application_name='phase5-owned-race-reader'"));ready.set()
            _,call=media.lock_media_snapshot(session,FIXTURE_VISIT,read=True)
            return call.generation,call.ended
    with ThreadPoolExecutor(max_workers=1) as pool:
        with Session(visit_engine) as writer:
            writer.scalar(select(EncounterRecord).where(EncounterRecord.id==FIXTURE_VISIT).with_for_update())
            pending=pool.submit(reader);assert ready.wait(2)
            blocked=False
            for _ in range(100):
                with visit_engine.connect() as observer:
                    blocked=observer.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE application_name='phase5-owned-race-reader' AND wait_event_type='Lock')"))
                if blocked:break
                time.sleep(.01)
            assert blocked,'The read must actually wait for the mutation before this regression is exercised.'
            call=writer.get(CallRecord,FIXTURE_VISIT);call.generation=expected;call.ended=False
            writer.commit()
        assert pending.result(timeout=3)==(expected,False)


def test_pause_during_output_initialization_prevents_tts_generation(visit_engine):
    from types import SimpleNamespace
    from bring_vene.speech.player import PublicSpeaker,PlaybackClosed
    p,_,_,_,generation=environment(visit_engine);approve(p,cues(p)[0])
    delivery=service.next_delivery(visit_engine,FIXTURE_VISIT,generation,SETTINGS);calls=[]
    async def scenario():
        speaker=PublicSpeaker(None,visit_engine,FIXTURE_VISIT,SETTINGS)
        async def initialize():
            # The real consent changes while the output SDK is initializing.
            control(p,'pause')
            speaker.output=SimpleNamespace(bind=lambda _:None,fence=None)
            speaker.session=SimpleNamespace(say=lambda *args,**kwargs:calls.append('tts'))
            speaker.watcher.healthy=True
        speaker.initialize=initialize
        with pytest.raises(PlaybackClosed):await speaker.play(delivery)
    asyncio.run(scenario());assert calls==[]
