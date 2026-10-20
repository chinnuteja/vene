import base64,json,time
from datetime import timedelta
from pathlib import Path
from uuid import UUID,uuid4
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from bring_vene.auth import COOKIE,FIXTURE_VISIT,FIXTURE_MEMBERS,digest
from bring_vene.config import Settings
from bring_vene.domain.contracts import EncounterView
from bring_vene.domain.service import DomainError,utc_now
from bring_vene.main import create_app
from bring_vene.persistence.models import (ExecutionRecord,ExecutionOutboxRecord,OfficeCallbackRecord,OfficeCallbackOutboxRecord,
    FamilyUpdateRecord,FamilyOutboxRecord,OfficeFamilyReceiptRecord,EncounterRecord,MembershipRecord,SessionRecord,DocumentRecord,
    OperationTraceRecord,DeletionAuditRecord,NextVisitRecord,CallRecord,CallbackNonceRecord)
from bring_vene.continuity import service,documents,callbacks,office_worker,worker
from bring_vene.continuity.contracts import (DocumentUpload,ReviewRequest,FamilyDraftRequest,DigestRequest,NextVisitRequest,DeleteRequest)
from bring_vene.execution import service as execution
from test_execution import setup,cred,check,ready,authorize,correct,reservation_count,action,SETTINGS as EXECUTION_SETTINGS

SETTINGS=Settings.model_validate({**EXECUTION_SETTINGS.model_dump(),'office_callback_secret':'phase-seven-isolated-callback-secret-123',
    'office_callback_url':'http://127.0.0.1:8013/integrations/office/results'})
BASE=f'/encounters/{FIXTURE_VISIT}/continuity'
TEXT='The lab visit is Friday at Hilltop Lab.\nIncrease the medication dose.\nSynthetic text only; ask the responsible clinician to clarify.'
PDF=Path(__file__).resolve().parents[3]/'fixtures/documents/after-visit-conflict.pdf'

def app(engine):return create_app(SETTINGS,engine)
def owned(engine,p):return service.state(engine,FIXTURE_VISIT,p.cookies.get(COOKIE),SETTINGS)

def booked(engine):
    p,d,f,item,b=setup(engine);aid=check(engine,p,item,b);ready(engine,p,d,aid,b);authorize(engine,p,aid)
    execution.dispatch(engine,SETTINGS,gateway=b)
    return p,d,f,item,b,aid

def callback_body(engine,aid,delivery_id=None):
    with Session(engine) as session:receipt=session.get(ExecutionRecord,aid).content['receipt']
    return json.dumps({'delivery_id':str(delivery_id or uuid4()),'result':{k:v for k,v in receipt.items() if k!='duplicate_events'}},sort_keys=True,separators=(',',':')).encode()

def callback(engine,body,signed=None):
    return TestClient(app(engine)).post('/integrations/office/results',content=body,headers=signed or callbacks.headers(SETTINGS.office_callback_secret,body))

def family_draft(engine,p,item,fields=None):
    uid=service.draft_family(engine,FIXTURE_VISIT,*cred(p),FamilyDraftRequest(recipient_id=FIXTURE_MEMBERS['family'],plan_ids=[item],fields=fields or ['title','timeframe','office_status']))
    return next(u for u in owned(engine,p).family_updates if u.id==uid)

def approve_update(engine,p,update):service.approve_family(engine,FIXTURE_VISIT,update.id,*cred(p),DigestRequest(digest=update.digest))

def test_signed_duplicate_late_callbacks_correlate_without_new_work_and_reject_replays(visit_engine):
    p,d,f,item,b,aid=booked(visit_engine);body=callback_body(visit_engine,aid)
    signed=callbacks.headers(SETTINGS.office_callback_secret,body)
    assert callback(visit_engine,body,{'x-office-signature':'0'*64}).status_code==401
    assert callback(visit_engine,body,callbacks.headers(SETTINGS.office_callback_secret,body,timestamp=int(time.time())-100)).status_code==401
    assert callback(visit_engine,body,signed).status_code==200
    assert callback(visit_engine,body,signed).status_code==409 # authentication nonce replay
    assert callback(visit_engine,body).json()['duplicate_delivery'] is True # fresh authentication, same business delivery
    correct(visit_engine,item)
    assert callback(visit_engine,callback_body(visit_engine,aid)).status_code==200 # late after correction, original receipt survives
    assert action(visit_engine,p,aid).state=='confirmed' and reservation_count(visit_engine)==1
    with Session(visit_engine) as session:
        assert session.scalar(select(func.count()).select_from(OfficeCallbackRecord))==2
        assert session.get(ExecutionOutboxRecord,aid) is None
    modified=json.loads(body);modified['result']['receipt_id']=str(uuid4())
    assert callback(visit_engine,json.dumps(modified).encode()).status_code==409

def test_office_callback_outbox_survives_lost_acknowledgement(visit_engine):
    p,d,f,item,b,aid=booked(visit_engine)
    with Session(visit_engine) as session,session.begin():
        row=session.scalar(select(OfficeCallbackOutboxRecord).where(OfficeCallbackOutboxRecord.request_id==aid));row.next_at=utc_now()-timedelta(seconds=1)
    def lose_ack(body,signed):
        response=callback(visit_engine,body,signed);assert response.status_code==200
        raise TimeoutError('Synthetic loss after receiver commit')
    assert office_worker.deliver(visit_engine,SETTINGS,lose_ack)
    with Session(visit_engine) as session,session.begin():
        row=session.scalar(select(OfficeCallbackOutboxRecord).where(OfficeCallbackOutboxRecord.request_id==aid));assert row.acknowledged_at is None;row.next_at=utc_now()-timedelta(seconds=1)
    assert office_worker.deliver(visit_engine,SETTINGS,lambda body,signed:callback(visit_engine,body,signed).json())
    assert owned(visit_engine,p).callback_count==1
    with Session(visit_engine) as session:assert session.scalar(select(OfficeCallbackOutboxRecord).where(OfficeCallbackOutboxRecord.request_id==aid)).acknowledged_at

@pytest.mark.parametrize('format',['text','pdf'])
def test_document_provenance_and_conflicts_do_not_change_clinical_or_execution_state(visit_engine,format):
    p,d,f,item,b=setup(visit_engine)
    with Session(visit_engine) as session,session.begin():
        record,view=execution.lock(session,FIXTURE_VISIT);step=execution.target(view,item);step.timeframe='Thursday';step.location='Riverside Lab';record.projection=view.model_dump(mode='json')
    before=p.get(f'/encounters/{FIXTURE_VISIT}').json()['plan']
    request=DocumentUpload(title='Synthetic office document',format=format,plan_ids=[item],**({'text':TEXT} if format=='text' else {'file_base64':base64.b64encode(PDF.read_bytes()).decode()}))
    doc_id=documents.upload(visit_engine,FIXTURE_VISIT,*cred(p),request)
    doc=owned(visit_engine,p).documents[0];assert doc.id==doc_id
    assert {d.kind for d in doc.differences}>={'timing','location','clinical_instruction'}
    assert doc.review_state=='unresolved' and len(doc.sha256)==64 and doc.pages[0]['page']==1
    for difference in doc.differences:assert doc.source.text[difference.start:difference.end]==difference.source_quote
    assert p.get(f'/encounters/{FIXTURE_VISIT}').json()['plan']==before
    assert service.state(visit_engine,FIXTURE_VISIT,f.cookies.get(COOKIE)).documents==[]
    with pytest.raises(DomainError):documents.review(visit_engine,FIXTURE_VISIT,doc_id,*cred(p),ReviewRequest(fingerprint=doc.fingerprint,note='Reviewed.'))
    with Session(visit_engine) as session,session.begin():
        record,view=execution.lock(session,FIXTURE_VISIT);source=next(e for e in view.evidence if e.id==doc.source.id);source.audiences=['clinician'];record.projection=view.model_dump(mode='json')
    clinician_doc=service.state(visit_engine,FIXTURE_VISIT,d.cookies.get(COOKIE)).documents[0]
    documents.review(visit_engine,FIXTURE_VISIT,doc_id,*cred(d),ReviewRequest(fingerprint=clinician_doc.fingerprint,note='Discuss the difference; no clinical change authorized.'))
    assert owned(visit_engine,p).documents[0].review_state=='reviewed'
    correct(visit_engine,item)
    assert owned(visit_engine,p).documents[0].review_state=='stale'
    assert reservation_count(visit_engine)==0

def test_invalid_scanned_encrypted_and_oversized_pdf_fail_without_recording_content(visit_engine):
    p,d,f,item,b=setup(visit_engine)
    for raw in [b'%PDF-broken',b'not a pdf',b'%PDF-'+b'x'*250000]:
        with pytest.raises(DomainError):documents.upload(visit_engine,FIXTURE_VISIT,*cred(p),DocumentUpload(title='Unsupported document',format='pdf',file_base64=base64.b64encode(raw).decode()))
    from pypdf import PdfWriter
    from io import BytesIO
    for encrypted in [False,True]:
        writer=PdfWriter();writer.add_blank_page(width=612,height=792)
        if encrypted:writer.encrypt('synthetic-password')
        stream=BytesIO();writer.write(stream)
        with pytest.raises(DomainError):documents.extract(DocumentUpload(title='Blank or encrypted',format='pdf',file_base64=base64.b64encode(stream.getvalue()).decode()))
    with Session(visit_engine) as session:assert session.scalar(select(func.count()).select_from(DocumentRecord))==0

def test_family_generation_uses_only_scoped_selected_fields_and_receipt(visit_engine):
    p,d,f,item,b,aid=booked(visit_engine)
    update=family_draft(visit_engine,p,item,['title','office_status']);assert 'Owner:' not in update.text and 'Who:' not in update.text
    assert 'PRIVATE_CANARY' not in update.text
    assert service.state(visit_engine,FIXTURE_VISIT,f.cookies.get(COOKIE)).family_updates==[]
    approve_update(visit_engine,p,update);worker.deliver(visit_engine,SETTINGS,gateway=b)
    family=service.state(visit_engine,FIXTURE_VISIT,f.cookies.get(COOKIE)).family_updates[0]
    assert family.state=='delivered' and family.receipt['request_id']==str(update.id)
    assert family.digest is None and family.fields==['title','office_status']
    with Session(visit_engine) as session:
        inbox=session.get(OfficeFamilyReceiptRecord,update.id);assert 'text' not in inbox.content
    with Session(visit_engine) as session,session.begin():
        record,view=execution.lock(session,FIXTURE_VISIT);execution.target(view,item).audiences=['clinician'];view.consent_epoch+=1;record.projection=view.model_dump(mode='json')
    assert service.state(visit_engine,FIXTURE_VISIT,f.cookies.get(COOKIE)).family_updates==[]

@pytest.mark.parametrize('change',['source','recipient','owner_session'])
def test_scope_change_wins_over_queued_family_delivery(visit_engine,change):
    p,d,f,item,b=setup(visit_engine);update=family_draft(visit_engine,p,item);approve_update(visit_engine,p,update)
    if change=='source':correct(visit_engine,item)
    else:
        with Session(visit_engine) as session,session.begin():
            if change=='recipient':session.get(MembershipRecord,FIXTURE_MEMBERS['family']).revoked_at=utc_now()
            else:session.get(SessionRecord,digest(p.cookies.get(COOKIE))).revoked_at=utc_now()
    worker.deliver(visit_engine,SETTINGS,gateway=b)
    assert '/family-updates' not in b.calls
    with Session(visit_engine) as session:assert session.get(FamilyUpdateRecord,update.id).state=='invalidated'

def test_family_timeout_after_actual_receipt_reconciles_once_and_survives_owner_expiry(visit_engine):
    p,d,f,item,b=setup(visit_engine);update=family_draft(visit_engine,p,item);approve_update(visit_engine,p,update)
    class LoseAck:
        def call(self,path,payload=None):
            value=b.call(path,payload)
            if path=='/family-updates':raise TimeoutError('Synthetic lost acknowledgement')
            return value
    worker.deliver(visit_engine,SETTINGS,gateway=LoseAck())
    with Session(visit_engine) as session,session.begin():session.get(FamilyOutboxRecord,update.id).next_at=utc_now()-timedelta(seconds=1)
    worker.deliver(visit_engine,SETTINGS,gateway=b)
    assert b.calls.count('/family-updates')==1
    with Session(visit_engine) as session,session.begin():session.get(SessionRecord,digest(p.cookies.get(COOKIE))).expires_at=utc_now()-timedelta(seconds=1)
    assert service.state(visit_engine,FIXTURE_VISIT,f.cookies.get(COOKIE)).family_updates[0].state=='delivered'

def test_next_preparation_is_private_and_deletion_purges_derived_content(visit_engine):
    p,d,f,item,b=setup(visit_engine);documents.upload(visit_engine,FIXTURE_VISIT,*cred(p),DocumentUpload(title='Synthetic document',text=TEXT,plan_ids=[item]))
    created=service.next_visit(visit_engine,FIXTURE_VISIT,*cred(p),NextVisitRequest(plan_ids=[item],visit_at=utc_now()+timedelta(days=7)))
    with Session(visit_engine) as session:
        row=session.get(EncounterRecord,created.encounter_id);fresh=EncounterView.model_validate(row.projection)
        assert not fresh.preparation_approved and all(not p.approved and p.audiences==[] for p in fresh.priorities)
        assert fresh.plan==[] and all(e.audiences==[] for e in fresh.evidence)
        assert set(session.scalars(select(MembershipRecord.role).where(MembershipRecord.encounter_id==fresh.id)))=={'patient'}
    assert f.get(f'/encounters/{created.encounter_id}').status_code==404
    version=p.get(f'/encounters/{FIXTURE_VISIT}').json()['version']
    result=service.delete_encounter(visit_engine,FIXTURE_VISIT,*cred(p),DeleteRequest(confirmation='DELETE SYNTHETIC VISIT',expected_version=version))
    assert result['visits_purged']==2 and not result['external_reservations_cancelled']
    with Session(visit_engine) as session:
        for model in [DocumentRecord,FamilyUpdateRecord,OperationTraceRecord,NextVisitRecord]:
            assert session.scalar(select(func.count()).select_from(model))==0
        # The deleted visit and its next-visit copy are gone; the earlier July visit is separate history.
        remaining={r.projection['title'] for r in session.scalars(select(EncounterRecord))}
        assert remaining=={'Check-in with Dr. Chen'}
        assert session.scalar(select(DeletionAuditRecord)).visit_count==2

def test_delete_refuses_unreconciled_external_work(visit_engine):
    p,d,f,item,b,aid=booked(visit_engine)
    with Session(visit_engine) as session,session.begin():session.get(ExecutionRecord,aid).state='unknown'
    with pytest.raises(DomainError):service.delete_encounter(visit_engine,FIXTURE_VISIT,*cred(p),DeleteRequest(confirmation='DELETE SYNTHETIC VISIT',expected_version=p.get(f'/encounters/{FIXTURE_VISIT}').json()['version']))
    assert reservation_count(visit_engine)==1

def test_new_related_document_invalidates_queued_booking_until_review_and_new_approval(visit_engine):
    p,d,f,item,b=setup(visit_engine);aid=check(visit_engine,p,item,b);ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid)
    documents.upload(visit_engine,FIXTURE_VISIT,*cred(p),DocumentUpload(title='New conflicting document',text=TEXT,plan_ids=[item]))
    execution.dispatch(visit_engine,SETTINGS,gateway=b)
    assert '/bookings' not in b.calls and reservation_count(visit_engine)==0
    assert action(visit_engine,p,aid).state=='invalidated'

def test_worker_crash_after_external_success_reconciles_existing_reservation(visit_engine):
    p,d,f,item,b=setup(visit_engine);aid=check(visit_engine,p,item,b);ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid)
    with Session(visit_engine) as session,session.begin():
        row=session.get(ExecutionRecord,aid);row.state='in_flight';row.content={**row.content,'send_started':True}
        payload={'request_id':str(aid),'slot_id':row.content['slot']['id'],'availability_revision':row.content['availability_revision'],'order_id':row.content['order_id']}
    b.call('/bookings',payload) # Actual independent office commit; local worker result never recorded.
    execution.dispatch(visit_engine,SETTINGS,gateway=b)
    assert b.calls.count('/bookings')==1 and action(visit_engine,p,aid).state=='confirmed'

def test_metadata_traces_exclude_content_and_expired_nonce_retention(visit_engine):
    p,d,f,item,b=setup(visit_engine);family_draft(visit_engine,p,item)
    with Session(visit_engine) as session:
        records=session.scalars(select(OperationTraceRecord)).all();assert records
        assert all(set(r.content)<={'action_id','update_id','document_id','next_id','duration_ms','attempts'} for r in records)
        assert 'PRIVATE_CANARY' not in json.dumps([r.content for r in records])
    nonce=uuid4()
    with Session(visit_engine) as session,session.begin():
        session.add(CallbackNonceRecord(nonce=nonce,encounter_id=FIXTURE_VISIT,accepted_at=utc_now()-timedelta(minutes=5)))
    service.prune_metadata(visit_engine,SETTINGS)
    with Session(visit_engine) as session:assert session.get(CallbackNonceRecord,nonce) is None

def test_interrupted_processing_marks_a_gap_and_requires_resume(visit_engine):
    from test_media import room,agree,control,BASE as CALL_BASE
    from bring_vene.voice import service as voice
    p,d,one,two,generation,identities,tracks=room(visit_engine)
    first=uuid4();voice.worker_admitted(visit_engine,FIXTURE_VISIT,generation,first)
    voice.worker_started(visit_engine,FIXTURE_VISIT,generation,first)
    agree(p,one['connection_id']);agree(d,two['connection_id']);assert control(p,'resume').status_code==200
    with Session(visit_engine) as session,session.begin():session.get(CallRecord,FIXTURE_VISIT).worker_seen_at=utc_now()-timedelta(seconds=5)
    # A delayed heartbeat alone is not evidence that processing restarted.
    assert voice.sync_room(visit_engine,FIXTURE_VISIT,generation,identities,tracks,0)['allowed']
    replacement=uuid4();voice.worker_admitted(visit_engine,FIXTURE_VISIT,generation,replacement)
    voice.worker_started(visit_engine,FIXTURE_VISIT,generation,replacement)
    outcome=voice.sync_room(visit_engine,FIXTURE_VISIT,generation,identities,tracks,0)
    assert not outcome['allowed']
    current=p.get(CALL_BASE).json();assert current['manual_pause'] and current['gap_since']
    assert current['audio_recorded'] is False and current['transcripts_shared'] is False


def test_cancelled_room_join_finishes_native_handshake_before_cleanup():
    import asyncio
    from bring_vene.voice.worker import finish_connect_before_cancellation
    async def scenario():
        started=asyncio.Event();finish=asyncio.Event();events=[]
        class Room:
            async def connect(self,*args):
                events.append('started');started.set()
                try:await finish.wait();events.append('native-ready')
                except asyncio.CancelledError:events.append('abandoned');raise
        async def owner():
            try:await finish_connect_before_cancellation(Room(),'synthetic-loopback','synthetic-token',None)
            finally:events.append('disconnect')
        task=asyncio.create_task(owner());await started.wait();task.cancel();await asyncio.sleep(0)
        assert not task.done() and 'abandoned' not in events
        finish.set()
        try:await task
        except asyncio.CancelledError:pass
        assert events==['started','native-ready','disconnect']
    asyncio.run(scenario())


def test_sharing_a_booked_step_later_keeps_its_receipt_but_a_changed_step_does_not(visit_engine):
    # Booked while shared with Dr. Chen only; Maria tells family afterwards.
    p,d,f,item,b=setup(visit_engine)
    with Session(visit_engine) as session,session.begin():
        record,view=execution.lock(session,FIXTURE_VISIT);execution.target(view,item).audiences=['clinician'];record.projection=view.model_dump(mode='json')
    aid=check(visit_engine,p,item,b);ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid);execution.dispatch(visit_engine,SETTINGS,gateway=b)
    assert action(visit_engine,p,aid).state=='confirmed'
    with Session(visit_engine) as session,session.begin():
        record,view=execution.lock(session,FIXTURE_VISIT);execution.target(view,item).audiences=['clinician','family'];record.projection=view.model_dump(mode='json')
    doctor=execution.state(visit_engine,FIXTURE_VISIT,d.cookies.get(COOKIE),SETTINGS).actions
    assert [a.state for a in doctor if a.id==aid]==['confirmed']
    family=execution.state(visit_engine,FIXTURE_VISIT,f.cookies.get(COOKIE),SETTINGS).actions
    assert [a.state for a in family if a.id==aid]==['confirmed']
    assert 'Office: Sandbox:' in family_draft(visit_engine,p,item).text
    # Changing the step itself still retires the old receipt for everyone but the patient.
    correct(visit_engine,item)
    assert all(a.id!=aid for a in execution.state(visit_engine,FIXTURE_VISIT,d.cookies.get(COOKIE),SETTINGS).actions)
    assert 'No current office completion has been verified' in family_draft(visit_engine,p,item).text
