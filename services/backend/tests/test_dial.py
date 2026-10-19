"""Phase 12b: dial-in admission and keypad controls (visit side; real telephony is credential-gated)."""
from datetime import timedelta
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.auth import FIXTURE_VISIT,FIXTURE_MEMBERS
from bring_vene.config import Settings
from bring_vene.domain.service import utc_now
from bring_vene.main import create_app
from bring_vene.persistence.models import CallConnectionRecord,CallRecord,DialPinRecord,MembershipRecord,EncounterRecord
from bring_vene.dial import service as dial
from bring_vene.voice import service as voice
from helpers import authenticated_client

SETTINGS=Settings(bring_vene_development=True,cookie_secure=False,livekit_url='ws://127.0.0.1:7880',livekit_api_key='k',
    livekit_api_secret='s'*32,phone_bridge_token='bridge-test-token',phone_dial_number='+1 555 0100 (sandbox)')
BRIDGE={'Authorization':'Bearer bridge-test-token'}

def setup(engine,call=True):
    app=create_app(SETTINGS,engine);p=authenticated_client(app);d=authenticated_client(app,'clinician')
    generation=uuid4()
    if call:
        with Session(engine) as session,session.begin():
            session.add(CallRecord(encounter_id=FIXTURE_VISIT,generation=generation,revision=1,manual_pause=True,ended=False,
                output_silenced=False,stopped_epoch=0,active_tasks=0))
    from fastapi.testclient import TestClient
    return p,d,TestClient(app),generation

def pin_for(p,role):
    response=p.post(f'/encounters/{FIXTURE_VISIT}/dial-pins',json={'membership_id':str(FIXTURE_MEMBERS[role])})
    assert response.status_code==200;return response.json()

def admit(bridge,pin,identity='sip_caller_1',caller='+15550199',headers=BRIDGE):
    return bridge.post('/integrations/phone/admit',json={'pin':pin,'participant_identity':identity,'caller_number':caller},headers=headers)

def phone(engine,identity='sip_caller_1'):
    with Session(engine) as session:
        return session.scalar(select(CallConnectionRecord).where(CallConnectionRecord.external_identity==identity))

def test_only_the_patient_issues_short_lived_single_use_pins(visit_engine):
    p,d,bridge,_=setup(visit_engine)
    assert d.post(f'/encounters/{FIXTURE_VISIT}/dial-pins',json={'membership_id':str(FIXTURE_MEMBERS['clinician'])}).status_code==403
    issued=pin_for(p,'clinician')
    assert len(issued['pin'])==6 and issued['pin'].isdigit() and issued['name']=='Dr. Chris Chen'
    assert issued['dial_number']=='+1 555 0100 (sandbox)'
    with Session(visit_engine) as session:
        row=session.scalar(select(DialPinRecord))
        assert row.pin_hash!=issued['pin'] and issued['pin'] not in row.pin_hash  # stored hashed
    replacement=pin_for(p,'clinician')
    assert admit(bridge,issued['pin']).status_code==401  # a new PIN replaces the old one
    assert admit(bridge,replacement['pin']).status_code==200
    assert admit(bridge,replacement['pin'],identity='sip_caller_2').status_code==401  # single use

def test_the_bridge_must_authenticate_and_caller_id_is_never_identity(visit_engine):
    p,d,bridge,generation=setup(visit_engine);issued=pin_for(p,'clinician')
    assert admit(bridge,issued['pin'],headers={}).status_code==403
    assert admit(bridge,issued['pin'],headers={'Authorization':'Bearer wrong'}).status_code==403
    assert admit(bridge,'000000' if issued['pin']!='000000' else '111111').status_code==401
    admitted=admit(bridge,issued['pin'],caller='+15550123').json()
    assert admitted['name']=='Dr. Chris Chen' and 'No audio is recorded' in admitted['announcement'] and 'Press 1' in admitted['prompt']
    connection=phone(visit_engine)
    assert connection.channel=='phone' and connection.consent=='pending' and connection.membership_id==FIXTURE_MEMBERS['clinician']
    assert '+15550123' not in str([getattr(connection,c.key) for c in CallConnectionRecord.__table__.columns])
    assert voice.identity(connection)=='sip_caller_1'

def test_expired_pin_and_unstarted_conversation_are_refused(visit_engine):
    p,d,bridge,_=setup(visit_engine,call=False);issued=pin_for(p,'family')
    assert admit(bridge,issued['pin']).status_code==409
    with Session(visit_engine) as session,session.begin():
        session.scalar(select(DialPinRecord)).expires_at=utc_now()-timedelta(seconds=1)
        session.add(CallRecord(encounter_id=FIXTURE_VISIT,generation=uuid4(),revision=1,manual_pause=True,ended=False,
            output_silenced=False,stopped_epoch=0,active_tasks=0))
    assert admit(bridge,issued['pin']).status_code==401

def test_keypad_consent_pause_and_patient_only_resume(visit_engine):
    p,d,bridge,generation=setup(visit_engine)
    admit(bridge,pin_for(p,'clinician')['pin'],identity='sip_doctor')
    admit(bridge,pin_for(p,'patient')['pin'],identity='sip_patient')
    with Session(visit_engine) as session,session.begin():
        for c in session.scalars(select(CallConnectionRecord)):c.present=True  # the worker reports presence
        session.get(CallRecord,FIXTURE_VISIT).worker_seen_at=utc_now()
    key=lambda identity,digit:dial.keypad(visit_engine,FIXTURE_VISIT,generation,identity,digit,SETTINGS)
    assert not key('sip_patient','0').accepted  # nobody has agreed yet
    assert key('sip_doctor','1').accepted and key('sip_patient','1').accepted
    assert not key('sip_doctor','0').accepted and key('sip_doctor','0').spoken=='Only the patient can resume Vene.'
    assert key('sip_patient','0').accepted
    with Session(visit_engine) as session:assert not session.get(CallRecord,FIXTURE_VISIT).manual_pause
    assert key('sip_doctor','9').accepted  # anyone can pause
    with Session(visit_engine) as session:assert session.get(CallRecord,FIXTURE_VISIT).manual_pause
    assert key('sip_doctor','2').accepted
    assert not key('sip_patient','0').accepted  # a declined phone participant keeps processing off
    assert not key('sip_stranger','1').accepted and not key('sip_doctor','5').accepted

def test_withdrawing_access_disconnects_the_caller(visit_engine):
    p,d,bridge,generation=setup(visit_engine)
    admit(bridge,pin_for(p,'family')['pin'],identity='sip_family')
    connection=phone(visit_engine,'sip_family')
    with Session(visit_engine) as session:assert voice.valid_connection(session,session.get(CallConnectionRecord,connection.id))
    assert p.post(f'/encounters/{FIXTURE_VISIT}/members/{FIXTURE_MEMBERS["family"]}/revoke').status_code==200
    with Session(visit_engine) as session:assert not voice.valid_connection(session,session.get(CallConnectionRecord,connection.id))
    assert not dial.keypad(visit_engine,FIXTURE_VISIT,generation,'sip_family','1',SETTINGS).accepted
    # The worker's room sync drops identities that are no longer valid connections.
    state=voice.sync_room(visit_engine,FIXTURE_VISIT,generation,{'sip_family'},{},0)
    assert state is None or 'sip_family' not in state['connections']

def test_a_revoked_pin_invalidates_an_admitted_phone_connection(visit_engine):
    p,d,bridge,generation=setup(visit_engine)
    admit(bridge,pin_for(p,'clinician')['pin'],identity='sip_doctor')
    pin_for(p,'clinician')  # issuing a new PIN revokes earlier unused ones only
    with Session(visit_engine) as session:assert voice.valid_connection(session,phone(visit_engine,'sip_doctor'))
    with Session(visit_engine) as session,session.begin():
        for row in session.scalars(select(DialPinRecord)):row.revoked_at=utc_now()
    with Session(visit_engine) as session:assert not voice.valid_connection(session,phone(visit_engine,'sip_doctor'))
