import time
from datetime import timedelta
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.domain.service import utc_now
from bring_vene.persistence.models import FamilyOutboxRecord,FamilyUpdateRecord
from bring_vene.execution.service import lock
from bring_vene.execution.gateway import OfficeGateway
from bring_vene.continuity.service import update_valid,update_digest,trace
from bring_vene.understanding.service import fingerprint

def deliver(engine,settings,claimed=None,gateway=None):
    if claimed is None:
        with Session(engine) as session,session.begin():
            job=session.scalar(select(FamilyOutboxRecord).where(FamilyOutboxRecord.next_at<=utc_now(),
                (FamilyOutboxRecord.lease_until.is_(None))|(FamilyOutboxRecord.lease_until<utc_now())).order_by(FamilyOutboxRecord.next_at).with_for_update(skip_locked=True).limit(1))
            if not job:return False
            job.lease_id=uuid4();job.lease_until=utc_now()+timedelta(seconds=5);job.attempts+=1
            claimed=job.update_id,job.lease_id
    update_id,lease_id=claimed
    with Session(engine) as session:
        row=session.get(FamilyUpdateRecord,update_id)
        if not row:return True
        visit_id=row.encounter_id
    with Session(engine) as session,session.begin():
        _,view=lock(session,visit_id);row=session.get(FamilyUpdateRecord,update_id);job=session.get(FamilyOutboxRecord,update_id,with_for_update=True)
        if not job or job.lease_id!=lease_id:return True
        if row.state in {'invalidated','delivered'}:session.delete(job);return True
        reconcile=bool(row.content.get('send_started'))
        if not reconcile and (not update_valid(session,view,row) or row.content.get('approval_digest')!=update_digest(row)):
            row.state='invalidated';session.delete(job);return True
        if not reconcile:row.state='in_flight';row.content={**row.content,'send_started':True}
        payload={'request_id':str(row.id),'recipient_id':str(row.recipient_id),'text':row.content['text'],'digest':row.content['approval_digest']}
    result=None
    try:
        adapter=gateway or OfficeGateway(settings)
        if reconcile:
            found=adapter.call('/family-updates/'+str(update_id))
            if found['found']:result=found['result']
            else:
                with Session(engine) as session,session.begin():
                    _,view=lock(session,visit_id);row=session.get(FamilyUpdateRecord,update_id);job=session.get(FamilyOutboxRecord,update_id,with_for_update=True)
                    if not job or job.lease_id!=lease_id:return True
                    if not update_valid(session,view,row):row.state='invalidated';session.delete(job);return True
        if result is None:result=adapter.call('/family-updates',payload)
    except Exception:result=None
    with Session(engine) as session,session.begin():
        lock(session,visit_id);row=session.get(FamilyUpdateRecord,update_id);job=session.get(FamilyOutboxRecord,update_id,with_for_update=True)
        if not job or job.lease_id!=lease_id:return True
        if (result and result.get('sandbox') is True and result.get('request_id')==str(row.id) and result.get('recipient_id')==str(row.recipient_id)
            and result.get('status')=='delivered' and result.get('receipt_id') and result.get('payload_hash')==fingerprint(payload)):
            row.state='delivered';row.content={**row.content,'receipt':result};session.delete(job)
            trace(session,visit_id,'family_update_delivered',update_id=str(row.id),attempts=job.attempts)
        else:
            row.state='unknown';job.lease_id=None;job.lease_until=None;job.next_at=utc_now()+timedelta(seconds=1)
    return True
