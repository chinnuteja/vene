"""Signed callback authentication is independent of participant/session authority."""
import hashlib,hmac,json,time
from uuid import UUID,uuid4
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from bring_vene.domain.service import DomainError,utc_now
from bring_vene.persistence.models import ExecutionRecord,ExecutionOutboxRecord,OfficeCallbackRecord,CallbackNonceRecord,OperationTraceRecord
from bring_vene.execution.service import lock,finish_result
from bring_vene.continuity.contracts import OfficeCallback

def signature(secret,timestamp,nonce,body):
    return hmac.new(secret.encode(),str(timestamp).encode()+b'.'+str(nonce).encode()+b'.'+body,hashlib.sha256).hexdigest()

def headers(secret,body,nonce=None,timestamp=None):
    timestamp=timestamp if timestamp is not None else int(time.time());nonce=nonce or uuid4()
    return {'Content-Type':'application/json','x-office-timestamp':str(timestamp),'x-office-nonce':str(nonce),
        'x-office-signature':signature(secret,timestamp,nonce,body)}

def ingest(engine,settings,body,request_headers):
    if not settings.office_callback_secret or len(settings.office_callback_secret)<32:
        raise DomainError(503,'Office callback authentication is not configured.')
    try:
        timestamp=request_headers['x-office-timestamp'];nonce=UUID(request_headers['x-office-nonce']);signed=request_headers['x-office-signature']
        if len(timestamp)>12 or abs(time.time()-int(timestamp))>60 or len(signed)!=64:raise ValueError()
        if not hmac.compare_digest(signature(settings.office_callback_secret,timestamp,nonce,body),signed):raise ValueError()
        callback=OfficeCallback.model_validate_json(body)
    except Exception:raise DomainError(401,'Office callback authentication or envelope is invalid.')
    payload_hash=hashlib.sha256(body).hexdigest()
    with Session(engine) as session:
        action=session.get(ExecutionRecord,callback.result.request_id)
        if not action:raise DomainError(404,'Office request not found.')
        visit_id=action.encounter_id
    with Session(engine) as session,session.begin():
        lock(session,visit_id);action=session.get(ExecutionRecord,callback.result.request_id)
        if not action or not action.content.get('send_started'):raise DomainError(409,'No dispatched request matches this receipt.')
        result=callback.result.model_dump(mode='json')
        # Canonical JSON serialization of AwareDatetime may use Z vs +00:00.
        # Preserve the receipt's observed time but compare identifiers/outcome/slot.
        if result['slot_id']!=action.content.get('slot',{}).get('id'):raise DomainError(409,'The office result names another slot.')
        prior_receipt=action.content.get('receipt')
        if prior_receipt and any(str(prior_receipt.get(k))!=str(result.get(k)) for k in ['request_id','receipt_id','status','slot_id']):
            raise DomainError(409,'A conflicting office receipt needs human review.')
        prior=session.get(OfficeCallbackRecord,callback.delivery_id)
        if prior and (prior.action_id!=action.id or prior.payload_hash!=payload_hash):raise DomainError(409,'This delivery ID was reused.')
        accepted=session.scalar(insert(CallbackNonceRecord).values(nonce=nonce,encounter_id=visit_id,accepted_at=utc_now())
            .on_conflict_do_nothing().returning(CallbackNonceRecord.nonce))
        if not accepted:raise DomainError(409,'This authenticated callback nonce was already used.')
        if not prior:
            if not prior_receipt:finish_result(action,result)
            job=session.get(ExecutionOutboxRecord,action.id)
            if job:session.delete(job)
            session.add(OfficeCallbackRecord(id=callback.delivery_id,encounter_id=visit_id,action_id=action.id,
                payload_hash=payload_hash,accepted_at=utc_now()))
            session.add(OperationTraceRecord(id=uuid4(),encounter_id=visit_id,event='office_callback_accepted',
                content={'action_id':str(action.id),'delivery_id':str(callback.delivery_id)},created_at=utc_now()))
        return {'accepted':True,'duplicate_delivery':bool(prior),'action_id':str(action.id)}
