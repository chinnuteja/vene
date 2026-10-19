"""Phase 12a: one phone in the room."""
import asyncio
from types import SimpleNamespace
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.auth import COOKIE,FIXTURE_VISIT,FIXTURE_MEMBERS
from bring_vene.config import Settings
from bring_vene.domain.contracts import EncounterView,PlanItem
from bring_vene.domain.service import utc_now
from bring_vene.main import create_app
from bring_vene.persistence.models import (CallConnectionRecord,CallRecord,EncounterRecord,SpeechDeliveryRecord,CueRecord,
    TranscriptSourceRecord,SessionRecord,RoomSessionRecord)
from bring_vene.room import service as room
from bring_vene.voice import service as voice
from helpers import authenticated_client

SETTINGS=Settings(bring_vene_development=True,bring_vene_mode='fixture',cookie_secure=False)
ROOT=f'/encounters/{FIXTURE_VISIT}/room'
PEOPLE=[{'name':'Dr. Chen','role':'clinician'},{'name':'Elena','role':'family'}]

def clients(engine):
    app=create_app(SETTINGS,engine)
    return authenticated_client(app),authenticated_client(app,'clinician'),authenticated_client(app,'family')

def activate(p):
    view=p.post(ROOT+'/start',json={'people':PEOPLE}).json()
    p.post(ROOT+'/disclosure')
    for person in view['people']:p.post(ROOT+'/agreements',json={'person_id':person['id'],'agreed':True})
    return p.get(ROOT).json()

def evidence(engine,label):
    with Session(engine) as session:
        view=EncounterView.model_validate(session.get(EncounterRecord,FIXTURE_VISIT).projection)
        return [e for e in view.evidence if e.speaker_label==label]

def epoch(engine):
    with Session(engine) as session:return session.get(EncounterRecord,FIXTURE_VISIT).projection['consent_epoch']

def test_nothing_is_processed_until_the_disclosure_and_everyones_agreement(visit_engine):
    p,_,_=clients(visit_engine)
    started=p.post(ROOT+'/start',json={'people':PEOPLE}).json()
    assert started['state']=='setting_up' and [x['agreed'] for x in started['people']]==[None,None]
    turn={'label':'S0','text':'Maria will arrange the lab visit at Riverside Lab on Tuesday.'}
    assert p.post(ROOT+'/fixture-utterances',json=turn).status_code==409
    assert p.post(ROOT+'/agreements',json={'person_id':started['people'][0]['id'],'agreed':True}).status_code==409  # disclosure first
    with Session(visit_engine) as session:assert not room.gate_open(session,FIXTURE_VISIT)
    p.post(ROOT+'/disclosure')
    p.post(ROOT+'/agreements',json={'person_id':started['people'][0]['id'],'agreed':True})
    assert p.get(ROOT).json()['state']=='setting_up' and p.post(ROOT+'/fixture-utterances',json=turn).status_code==409
    p.post(ROOT+'/agreements',json={'person_id':started['people'][1]['id'],'agreed':True})
    assert p.get(ROOT).json()['state']=='active'
    assert p.post(ROOT+'/fixture-utterances',json=turn).status_code==200
    [source]=evidence(visit_engine,'S0')
    assert source.speaker=='Unattributed speaker 1' and source.attribution=='unattributed'

def test_a_declined_person_keeps_vene_off_and_a_new_arrival_closes_the_gate(visit_engine):
    p,_,_=clients(visit_engine)
    started=p.post(ROOT+'/start',json={'people':PEOPLE}).json();p.post(ROOT+'/disclosure')
    p.post(ROOT+'/agreements',json={'person_id':started['people'][0]['id'],'agreed':True})
    p.post(ROOT+'/agreements',json={'person_id':started['people'][1]['id'],'agreed':False})
    assert p.get(ROOT).json()['state']=='declined'
    with Session(visit_engine) as session:assert not room.gate_open(session,FIXTURE_VISIT)
    p.post(ROOT+'/agreements',json={'person_id':started['people'][1]['id'],'agreed':True})
    assert p.get(ROOT).json()['state']=='active'
    before=epoch(visit_engine)
    arrived=p.post(ROOT+'/people',json={'name':'A nurse','role':'other'}).json()
    assert arrived['state']=='setting_up' and arrived['disclosure_at'] is None and epoch(visit_engine)>before
    with Session(visit_engine) as session:assert not room.gate_open(session,FIXTURE_VISIT)

def test_room_changes_pause_the_call_and_resume_requires_the_room(visit_engine):
    p,_,_=clients(visit_engine)
    with Session(visit_engine) as session,session.begin():
        session.add(CallRecord(encounter_id=FIXTURE_VISIT,generation=uuid4(),revision=1,manual_pause=False,ended=False,
            output_silenced=False,stopped_epoch=0,active_tasks=0))
    p.post(ROOT+'/start',json={'people':PEOPLE})
    with Session(visit_engine) as session:assert session.get(CallRecord,FIXTURE_VISIT).manual_pause
    with Session(visit_engine) as session:
        call=session.get(CallRecord,FIXTURE_VISIT);encounter=session.get(EncounterRecord,FIXTURE_VISIT)
        call.manual_pause=False
        assert not voice.gate(session,encounter,call)  # setting up: processing gate closed

def test_mapping_a_speaker_corrects_sources_and_invalidates_dependent_interpretations(visit_engine):
    p,_,_=clients(visit_engine);people=activate(p)['people']
    p.post(ROOT+'/fixture-utterances',json={'label':'S1','text':'Maria will arrange the lab visit at Riverside Lab on Tuesday.'})
    [source]=evidence(visit_engine,'S1')
    with Session(visit_engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);view=EncounterView.model_validate(record.projection)
        view.plan.append(PlanItem(id=uuid4(),title='Arrange the lab visit',detail='From the room.',evidence_refs=[source.id],origin='interpretation',kind='lab'))
        record.projection=view.model_dump(mode='json')
    mapped=p.post(ROOT+'/speakers',json={'label':'S1','person_id':people[0]['id']}).json()
    assert [s['name'] for s in mapped['speakers'] if s['label']=='S1']==['Dr. Chen']
    [after]=evidence(visit_engine,'S1')
    assert after.speaker=='Dr. Chen' and after.attribution=='patient_attested' and after.version==2
    assert after.title.endswith('· Dr. Chen')
    with Session(visit_engine) as session:
        view=EncounterView.model_validate(session.get(EncounterRecord,FIXTURE_VISIT).projection)
        assert not any(i.title=='Arrange the lab visit' and source.id in i.evidence_refs for i in view.plan)
        assert len(session.get(TranscriptSourceRecord,source.id).history)==1
    # Mapping to the device owner is session-backed attribution.
    p.post(ROOT+'/speakers',json={'label':'S1','person_id':'patient'})
    assert evidence(visit_engine,'S1')[0].attribution=='session' and evidence(visit_engine,'S1')[0].speaker=='Maria Alvarez'
    assert p.post(ROOT+'/speakers',json={'label':'S1','person_id':str(uuid4())}).status_code==404

def test_an_attributed_clinician_cannot_confirm_or_order(visit_engine):
    from bring_vene.execution.contracts import ScopeRequest,LookupRequest,PrerequisiteRequest
    from bring_vene.execution import service as execution
    from test_execution import Bridge
    p,d,_=clients(visit_engine);people=activate(p)['people']
    p.post(ROOT+'/fixture-utterances',json={'label':'S0','text':'I confirm the lab order. Maria will arrange the lab visit at Riverside Lab on Tuesday.'})
    p.post(ROOT+'/speakers',json={'label':'S0','person_id':people[0]['id']})
    [source]=evidence(visit_engine,'S0')
    with Session(visit_engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);view=EncounterView.model_validate(record.projection)
        item=PlanItem(id=uuid4(),title='Arrange the lab visit',detail=source.text,evidence_refs=[source.id],origin='interpretation',kind='lab',
            owner='Maria',timeframe='Tuesday',location='Riverside Lab')
        view.plan.append(item);record.projection=view.model_dump(mode='json')
    settings=Settings(bring_vene_development=True,cookie_secure=False,office_url='http://127.0.0.1:8012',office_token='isolated-test-token')
    b=Bridge(visit_engine);cred=lambda c:(c.cookies.get(COOKIE),c.headers['x-vene-csrf'])
    execution.scope(visit_engine,FIXTURE_VISIT,item.id,*cred(p),ScopeRequest(allowed=True))
    aid=execution.lookup(visit_engine,FIXTURE_VISIT,item.id,*cred(p),LookupRequest(window='morning'),settings,b)
    action=next(a for a in execution.state(visit_engine,FIXTURE_VISIT,cred(p)[0],settings).actions if a.id==aid)
    assert not action.clinician_confirmed and not action.order_available
    # The patient's device carried the clinician's words; it cannot act as the clinician.
    import pytest
    from bring_vene.domain.service import DomainError
    with pytest.raises(DomainError) as refused:
        execution.prerequisites(visit_engine,FIXTURE_VISIT,aid,*cred(p),PrerequisiteRequest(expected_fingerprint=action.fingerprint,order=True),settings,b)
    assert refused.value.status==403 and '/orders' not in b.calls

def test_vene_hearing_itself_through_the_phone_speaker_is_dropped(visit_engine):
    p,_,_=clients(visit_engine);activate(p)
    with Session(visit_engine) as session,session.begin():
        cue=CueRecord(id=uuid4(),encounter_id=FIXTURE_VISIT,dedup_key='t',digest='0'*64,score=1,state='delivered',content={},
            created_at=utc_now(),expires_at=utc_now())
        session.add(cue);session.flush()
        session.add(SpeechDeliveryRecord(id=uuid4(),encounter_id=FIXTURE_VISIT,cue_id=cue.id,generation=uuid4(),state='speaking',
            content={'text':'Could we come back to this question? Where should I arrange my lab visit?'},approved_at=utc_now(),
            first_audio_at=utc_now(),played_ms=0))
    p.post(ROOT+'/fixture-utterances',json={'label':'S2','text':'could we come back to this question where should I arrange my lab visit'})
    assert evidence(visit_engine,'S2')==[] and p.get(ROOT).json()['suppressed_self_speech']==1
    p.post(ROOT+'/fixture-utterances',json={'label':'S2','text':'Yes, Riverside Lab on Tuesday morning works for me.'})
    assert len(evidence(visit_engine,'S2'))==1

def test_guests_learn_only_whether_room_mode_is_on(visit_engine):
    p,d,f=clients(visit_engine);activate(p)
    p.post(ROOT+'/fixture-utterances',json={'label':'S0','text':'Something said in the room today.'})
    for guest in (d,f):
        body=guest.get(ROOT).json()
        assert body['state']=='active' and body['people']==[] and body['speakers']==[]
        assert guest.post(ROOT+'/start',json={'people':PEOPLE}).status_code==403
        assert guest.post(ROOT+'/speakers',json={'label':'S0','person_id':'patient'}).status_code==403

def test_live_room_turns_from_the_patients_device_carry_their_speaker_label(visit_engine):
    p,_,_=clients(visit_engine);activate(p)
    with Session(visit_engine) as session,session.begin():
        credential=session.scalar(select(SessionRecord).where(SessionRecord.membership_id==FIXTURE_MEMBERS['patient']).order_by(SessionRecord.expires_at.desc()))
        room_row=session.get(RoomSessionRecord,FIXTURE_VISIT);room_row.session_hash=credential.token_hash
        call=CallRecord(encounter_id=FIXTURE_VISIT,generation=uuid4(),revision=1,manual_pause=False,ended=False,output_silenced=False,
            stopped_epoch=0,active_tasks=0)
        session.add(call);session.flush()
        connection=CallConnectionRecord(id=uuid4(),encounter_id=FIXTURE_VISIT,generation=call.generation,membership_id=FIXTURE_MEMBERS['patient'],
            session_hash=credential.token_hash,present=True,consent='agreed',track_sid='TR_1',track_epoch=1,expires_at=credential.expires_at,retired=False)
        session.add(connection);generation=call.generation;connection_id=connection.id
    assert room.room_track(visit_engine,FIXTURE_VISIT,connection_id)
    assert voice.finalize(visit_engine,FIXTURE_VISIT,generation,connection_id,'TR_1',1,epoch(visit_engine),'Thursday afternoon works better for me.',SETTINGS,'S3')
    [source]=evidence(visit_engine,'S3')
    assert source.origin=='deepgram' and source.attribution=='unattributed'

def test_diarized_turns_are_finalized_per_consecutive_speaker():
    from livekit.agents.stt import SpeechEvent,SpeechEventType,SpeechData
    from bring_vene.voice.supervisor import DeepgramSink
    finals=[]
    async def on_final(text,label=None):finals.append((label,text))
    sink=DeepgramSink(SETTINGS,on_final,None,diarize=True)
    def final(text,speaker):return SpeechEvent(type=SpeechEventType.FINAL_TRANSCRIPT,alternatives=[SpeechData(language='en',text=text,speaker_id=speaker)])
    async def run():
        for event in [final('When is the lab open?','S0'),final('Tuesday mornings.','S1'),final('From eight.','S1'),final('Thank you.','S0'),
                      SpeechEvent(type=SpeechEventType.END_OF_SPEECH)]:
            await sink.accept_event(event)
    asyncio.run(run())
    assert finals==[('S0','When is the lab open?'),('S1','Tuesday mornings. From eight.'),('S0','Thank you.')]
    plain=[];single=DeepgramSink(SETTINGS,lambda text,label=None:plain.append((label,text)) or asyncio.sleep(0),None)
    asyncio.run(single.accept_event(final('Hello there.','S0')));asyncio.run(single.accept_event(SpeechEvent(type=SpeechEventType.END_OF_SPEECH)))
    assert plain==[(None,'Hello there.')]
