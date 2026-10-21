"""Patient-scoped administrative work. External receipts survive local corrections."""
from datetime import datetime, timedelta
from uuid import UUID,uuid4
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.auth import authenticate
from bring_vene.domain.contracts import EncounterView
from bring_vene.domain.context import context_adapter
from bring_vene.domain.service import DomainError,utc_now
from bring_vene.persistence.models import (EncounterRecord,ExecutionRecord,ExecutionScopeRecord,ExecutionOutboxRecord,
    SessionRecord,MembershipRecord)
from bring_vene.understanding.service import fingerprint
from bring_vene.execution.contracts import ExecutionView,ActionView,BundleOutcome,BundleResult,ErrandOption
from bring_vene.execution import errands
from bring_vene.execution.gateway import OfficeGateway,for_run

TERMINAL={'confirmed','rejected','invalidated','cancelled'}

def lock(session,visit_id):
    encounter=session.get(EncounterRecord,visit_id,with_for_update=True)
    if not encounter:raise DomainError(404,'Visit not found.')
    return encounter,EncounterView.model_validate(encounter.projection)

def target(view,item_id):
    item=next((p for p in view.plan if p.id==item_id),None)
    if not item:raise DomainError(404,'Next step not found.')
    # Explicit choice of a lab scheduling task; model text alone cannot authorize it.
    return item

def plan_fingerprint(view,item_id):
    item=target(view,item_id)
    refs={str(e.id):e.model_dump(mode='json') for e in view.evidence if e.id in item.evidence_refs}
    snapshot={'item':item.model_dump(mode='json'),'sources':refs}
    if item.kind=='authorization':
        from bring_vene.feasibility.service import authorization_item_id
        parent=next((p for p in view.plan if p.kind=='imaging' and authorization_item_id(view,p.id)==item.id),None)
        # A plan's approval applies to the exact imaging intention and sources.
        # Changing that intention preserves the old receipt, not its authority.
        snapshot['authorized_imaging']=plan_fingerprint(view,parent.id) if parent else None
    return fingerprint(snapshot)

def intent_fingerprint(view,item_id):
    """What a request asked for: the step and its sources, without who may see them."""
    item=target(view,item_id)
    refs={str(e.id):e.model_dump(mode='json',exclude={'audiences'}) for e in view.evidence if e.id in item.evidence_refs}
    snapshot={'item':item.model_dump(mode='json',exclude={'audiences'}),'sources':refs}
    if item.kind=='authorization':
        from bring_vene.feasibility.service import authorization_item_id
        parent=next((p for p in view.plan if p.kind=='imaging' and authorization_item_id(view,p.id)==item.id),None)
        snapshot['authorized_imaging']=intent_fingerprint(view,parent.id) if parent else None
    return fingerprint(snapshot)

def receipt_current(view,row):
    """Pending work needs the exact current step. A confirmed receipt stays current when the step was only
    shared differently afterwards; any change to the step or its sources still retires it."""
    try:
        if plan_fingerprint(view,row.item_id)==row.content['plan_fingerprint']:return True
        return row.state=='confirmed' and bool(row.content.get('intent_fingerprint')) and row.content['intent_fingerprint']==intent_fingerprint(view,row.item_id)
    except DomainError:return False

def access(session,visit_id,token,csrf=None):
    encounter,view=lock(session,visit_id)
    member,credential=authenticate(session,token,visit_id,csrf,mutate=csrf is not None)
    return encounter,view,member,credential

def patient(member):
    if member.role!='patient':raise DomainError(403,'Only the patient may allow checks or approve a booking.')

def reviewed_documents(session,view,item_id):
    from bring_vene.persistence.models import DocumentRecord
    from bring_vene.continuity.documents import comparison_fingerprint
    bindings={}
    for document in session.scalars(select(DocumentRecord).where(DocumentRecord.encounter_id==view.id)):
        if str(item_id) not in document.content['plan_ids']:continue
        current=comparison_fingerprint(view,document)
        if document.content.get('review_fingerprint')!=current:
            raise DomainError(409,'Review the relevant after-visit document with the responsible clinician before confirming this booking.')
        bindings[str(document.id)]=current
    return bindings

def scope_valid(session,view,action):
    data=action.content;scope=session.get(ExecutionScopeRecord,(view.id,action.item_id))
    credential=session.get(SessionRecord,data['session_hash'],populate_existing=True)
    member=session.get(MembershipRecord,credential.membership_id,populate_existing=True) if credential else None
    clinician=session.get(MembershipRecord,UUID(data['clinician_id']),populate_existing=True) if data.get('clinician_id') else None
    try:current=plan_fingerprint(view,action.item_id)==data['plan_fingerprint'] and data.get('sandbox_run')==(str(view.demo_run) if view.demo_run else None)
    except DomainError:current=False
    if data.get('clinician_id'):
        try:current=current and reviewed_documents(session,view,action.item_id)==data.get('document_bindings',{})
        except DomainError:current=False
    return bool((not data.get('clinician_id') or clinician and clinician.role=='clinician' and not clinician.revoked_at and clinician.encounter_id==view.id) and current and scope and scope.allowed and scope.revision==data['scope_revision'] and
        scope.session_hash==data['session_hash'] and credential and not credential.revoked_at and credential.expires_at>utc_now() and
        member and member.role=='patient' and not member.revoked_at and member.encounter_id==view.id)

def fresh(action):
    value=action.content.get('expires_at')
    return bool(value and datetime.fromisoformat(value)>utc_now())

def action_digest(action):
    # Non-lab errands also bind their kind; lab keeps the Phase 6 digest shape.
    kind={} if action.content.get('kind','lab')=='lab' else {'kind':action.content['kind']}
    tenant={'sandbox_run':action.content['sandbox_run']} if action.content.get('sandbox_run') else {}
    return fingerprint({**kind,**tenant,'action_id':str(action.id),'plan':action.content['plan_fingerprint'],
        'scope_revision':action.content['scope_revision'],'window':action.content['window'],
        'location':action.content.get('location','Riverside Lab'),'day':action.content.get('day','2026-10-20'),
        'slot':action.content.get('slot'),'availability_revision':action.content.get('availability_revision'),
        'expires_at':action.content.get('expires_at'),'order_id':action.content.get('order_id'),
        'clinician_id':action.content.get('clinician_id'),'document_bindings':action.content.get('document_bindings',{})})

def snapshot(action):return fingerprint({'state':action.state,'content':action.content})

def state(engine,visit_id,token,settings):
    with Session(engine) as session,session.begin():
        _,view,member,_=access(session,visit_id,token)
        visible={p.id for p in context_adapter.view(view,member.role,member.id).plan}
        rows=session.scalars(select(ExecutionRecord).where(ExecutionRecord.encounter_id==visit_id).order_by(ExecutionRecord.created_at.desc())).all()
        actions=[]
        for row in rows:
            if row.item_id not in visible:continue
            # Even if a changed plan is shared again, the old request cannot inherit its audience.
            current=plan_fingerprint(view,row.item_id)==row.content['plan_fingerprint']
            if member.role!='patient' and not receipt_current(view,row):continue
            data=row.content;allowed=scope_valid(session,view,row);shown=row.state;message=data.get('message','')
            if row.state not in TERMINAL and row.state not in {'unknown','in_flight'} and not allowed:
                shown='invalidated';message='The step, source or permission changed. Check again.'
            elif row.state=='suggested' and not fresh(row):
                shown='expired';message='The availability check expired. Check again before approval.'
            errand=errands.for_action(data)
            actions.append(ActionView(id=row.id,item_id=row.item_id,kind=errand.kind,place=errand.place,document=errand.document,
                title=data['title'],window=data['window'],state=shown,
                message=message,slot=data.get('slot'),checked_at=data.get('checked_at'),receipt=data.get('receipt'),
                receipt_current=row.state=='confirmed' and receipt_current(view,row),
                digest=action_digest(row) if member.role=='patient' and shown=='suggested' else None,
                fingerprint=data['plan_fingerprint'] if member.role in {'patient','clinician'} and current else None,
                clinician_confirmed=bool(data.get('clinician_id')),order_available=bool(data.get('order_id')),
                patient_authorized=bool(data.get('approved_at')),scope_allowed=allowed if member.role=='patient' else False))
        catalog=[ErrandOption(kind=e.kind,place=e.place,document=e.document,offered=e.offered,confirmed=e.confirmed,
            locations=list(e.locations),days=[{'day':day,'label':label} for day,label in e.days]) for e in errands.ERRANDS.values()]
        return ExecutionView(configured=bool(settings.office_url and settings.office_token),actions=actions,errands=catalog)

def scope(engine,visit_id,item_id,token,csrf,request):
    with Session(engine) as session,session.begin():
        _,view,member,credential=access(session,visit_id,token,csrf);patient(member);target(view,item_id)
        row=session.get(ExecutionScopeRecord,(visit_id,item_id))
        if not row:
            row=ExecutionScopeRecord(encounter_id=visit_id,item_id=item_id,session_hash=credential.token_hash,revision=0,allowed=False);session.add(row)
        row.revision+=1;row.allowed=request.allowed;row.session_hash=credential.token_hash
        # Revision changes mean restoring a permission never resurrects prior work.
        for action in session.scalars(select(ExecutionRecord).where(ExecutionRecord.encounter_id==visit_id,ExecutionRecord.item_id==item_id)):
            if action.state not in TERMINAL and action.state not in {'in_flight','unknown'}:
                action.state='invalidated';action.content={**action.content,'message':'Lookup permission changed; request a new check.'}

def lookup(engine,visit_id,item_id,token,csrf,request,settings,gateway=None):
    with Session(engine) as session,session.begin():
        _,view,member,credential=access(session,visit_id,token,csrf);patient(member);item=target(view,item_id)
        errand=errands.for_item(item)
        if not errand:
            raise DomainError(422,'The sandbox handles sourced lab, imaging, referral and prescription steps only.')
        if request.location not in errand.locations:
            raise DomainError(422,'Choose one of the fictional '+errand.place+' locations.')
        from bring_vene.feasibility.availability import deadline
        dates=deadline(item.timeframe,view.visit_at)
        if dates and not dates[0].isoformat()<=request.day<=dates[1].isoformat():
            raise DomainError(422,'This appointment is outside the stated time window. Clarify it with the clinician first.')
        sandbox_run=view.demo_run
        grant=session.get(ExecutionScopeRecord,(visit_id,item_id))
        if not grant or not grant.allowed or grant.session_hash!=credential.token_hash:
            raise DomainError(403,'Allow this sandbox availability lookup first.')
        existing=session.scalars(select(ExecutionRecord).where(ExecutionRecord.encounter_id==visit_id,ExecutionRecord.item_id==item_id)).all()
        if any(a.state in {'confirmed','queued','in_flight','unknown'} for a in existing):
            raise DomainError(409,'Resolve the existing request or reservation before starting another.')
        for old in existing:
            if old.state not in TERMINAL:old.state='invalidated'
        action=ExecutionRecord(id=uuid4(),encounter_id=visit_id,item_id=item_id,state='checking',created_at=utc_now(),content={
            'kind':errand.kind,'title':item.title,'window':request.window,'plan_fingerprint':plan_fingerprint(view,item_id),'intent_fingerprint':intent_fingerprint(view,item_id),
            'location':request.location,'day':request.day,
            'scope_revision':grant.revision,'session_hash':credential.token_hash,'message':'Checking the local sandbox '+errand.place+'.'})
        if sandbox_run:action.content={**action.content,'sandbox_run':str(sandbox_run)}
        session.add(action);action_id=action.id
    # No transcript, name, visit ID or plan detail goes to the office. Recheck scope on return.
    payload=request.model_dump(mode='json')
    if errand.institution!='lab':payload['institution']=errand.institution
    try:response=(gateway or for_run(settings,sandbox_run)).call('/lookup',payload)
    except Exception as error:
        # Type only: never log request fields, credentials or provider bodies.
        logging.getLogger(__name__).warning('Sandbox lookup failed (%s)',type(error).__name__)
        response=None
    with Session(engine) as session,session.begin():
        _,view=lock(session,visit_id);action=session.get(ExecutionRecord,action_id)
        if not scope_valid(session,view,action):
            action.state='invalidated';action.content={**action.content,'message':'The lookup returned after a correction or permission change; its result was discarded.'}
        elif response is None:
            action.state='unavailable';action.content={**action.content,'message':'The sandbox '+errand.place+' did not return a verified result. Nothing was sent.'}
        else:
            action.content={**action.content,'slot':response['slot'],'availability_revision':response['revision'],
                'checked_at':response['checked_at'],'expires_at':response['expires_at']}
            action.state='suggested' if response['slot'] and fresh(action) else 'expired' if response['slot'] else 'no_slot'
            action.content={**action.content,'message':{'suggested':'The '+errand.place+' offered a '+errand.offered+'. It is not reserved. Clinician confirmation, a sandbox '+errand.document+' and your separate approval are needed.',
                'expired':'The '+errand.place+' returned expired availability. Check again.','no_slot':'No '+errand.offered+' fits this window. Clarify another window before checking again.'}[action.state]}
    return action_id

def prerequisites(engine,visit_id,action_id,token,csrf,request,settings,gateway=None):
    def validate(session):
        _,view,member,_=access(session,visit_id,token,csrf)
        if member.role!='clinician':raise DomainError(403,'The clinician must confirm the intended step and its required sandbox document.')
        action=session.get(ExecutionRecord,action_id)
        if not action or action.encounter_id!=visit_id or action.item_id not in {p.id for p in context_adapter.view(view,member.role,member.id).plan}:
            raise DomainError(404,'Request not found.')
        if action.state!='suggested' or not scope_valid(session,view,action) or request.expected_fingerprint!=plan_fingerprint(view,action.item_id):
            raise DomainError(409,'This step or request changed. Check again.')
        reviewed_documents(session,view,action.item_id)
        return action,member,view
    with Session(engine) as session,session.begin():
        action,_,_=validate(session)
        needs_order=request.order and not action.content.get('order_id')
        errand=errands.for_action(action.content)
        sandbox_run=action.content.get('sandbox_run')
    receipt=None;order_id=None
    if needs_order:
        # The external order is explicitly synthetic. Its original request ID is
        # stable across retry, and a stale response never grants booking authority.
        from uuid import uuid5,NAMESPACE_URL
        order_id=uuid5(NAMESPACE_URL,'bring-vene:sandbox-order:'+str(action_id))
        body={'request_id':str(order_id)}
        if errand.institution!='lab':body['institution']=errand.institution
        try:receipt=(gateway or for_run(settings,sandbox_run)).call('/orders',body)
        except Exception:raise DomainError(503,'The sandbox '+errand.document+' could not be verified. Nothing was approved.')
        if (receipt.get('status')!='available' or receipt.get('order_id')!=str(order_id) or
            receipt.get('institution','lab')!=errand.institution or receipt.get('sandbox_run')!=sandbox_run):raise DomainError(503,'Unverified sandbox document response.')
    with Session(engine) as session,session.begin():
        action,member,view=validate(session)
        data={**action.content,'clinician_id':str(member.id),'clinician_at':utc_now().isoformat(),
            'document_bindings':reviewed_documents(session,view,action.item_id)}
        if receipt:data.update(order_id=str(order_id),order_receipt=receipt)
        action.content=data


def approve_action(session,view,action,digest):
    """One approval decision. Returns (outcome, message); the caller holds the visit lock."""
    if digest!=action_digest(action):raise DomainError(409,'The proposed action changed. Review it again.')
    if action.state in {'queued','in_flight','unknown','confirmed'}:return 'already_approved',action.content.get('message','') # never another write
    if action.state!='suggested' or not scope_valid(session,view,action) or not fresh(action):
        raise DomainError(409,'This suggestion expired or its source or permission changed.')
    errand=errands.for_action(action.content)
    dependencies=[]
    if not action.content.get('clinician_id'):dependencies.append('clinician confirmation')
    if not action.content.get('order_id'):dependencies.append('required sandbox '+('order' if errand.kind=='lab' else errand.document))
    from bring_vene.feasibility.service import requires_authorization
    if requires_authorization(session,view,action):dependencies.append('approved prior authorization')
    if dependencies:
        message='Waiting on '+', '.join(dependencies)+('. No booking dispatched.' if errand.kind=='lab' else '. Nothing was sent.')
        action.content={**action.content,'message':message}
        return 'waiting',message
    message='You approved this exact sandbox request. Queued for the '+errand.place+'.'
    action.state='queued';action.content={**action.content,'approved_at':utc_now().isoformat(),'approval_digest':digest,'message':message}
    session.add(ExecutionOutboxRecord(action_id=action.id,next_at=utc_now(),attempts=0))
    return 'queued',message

def approve(engine,visit_id,action_id,token,csrf,request):
    with Session(engine) as session,session.begin():
        _,view,member,_=access(session,visit_id,token,csrf);patient(member)
        action=session.get(ExecutionRecord,action_id)
        if not action or action.encounter_id!=visit_id:raise DomainError(404,'Request not found.')
        approve_action(session,view,action,request.digest)

def approve_bundle(engine,visit_id,token,csrf,request):
    """One patient action over several exact digests. Not a transaction across institutions:
    each errand is queued, held for a named prerequisite or refused on its own, then
    dispatched and reconciled independently."""
    with Session(engine) as session,session.begin():
        _,view,member,_=access(session,visit_id,token,csrf);patient(member)
        rows=session.scalars(select(ExecutionRecord).where(ExecutionRecord.encounter_id==visit_id)).all()
        by_digest={action_digest(row):row for row in rows}
        outcomes=[]
        for digest in dict.fromkeys(request.digests):
            action=by_digest.get(digest)
            if not action:
                # A changed step changes its digest; nothing matching it is approved.
                continue
            try:outcome,message=approve_action(session,view,action,digest)
            except DomainError as error:outcome,message='refused',error.message
            outcomes.append(BundleOutcome(action_id=action.id,outcome=outcome,message=message))
        unmatched=len(dict.fromkeys(request.digests))-len(outcomes)
        if unmatched and not outcomes:raise DomainError(409,'These steps changed. Review them again.')
        return BundleResult(outcomes=outcomes,unmatched=unmatched)

def claim(engine):
    with Session(engine) as session,session.begin():
        row=session.scalar(select(ExecutionOutboxRecord).where(ExecutionOutboxRecord.next_at<=utc_now(),
            (ExecutionOutboxRecord.lease_until.is_(None)) | (ExecutionOutboxRecord.lease_until<utc_now()))
            .order_by(ExecutionOutboxRecord.next_at).with_for_update(skip_locked=True).limit(1))
        if not row:return None
        row.lease_id=uuid4();row.lease_until=utc_now()+timedelta(seconds=5);row.attempts+=1
        return row.action_id,row.lease_id

def finish_result(action,result):
    if (result.get('request_id')!=str(action.id) or result.get('status') not in {'confirmed','rejected'} or not result.get('receipt_id') or
        result.get('slot_id')!=action.content.get('slot',{}).get('id') or result.get('sandbox') is not True):
        raise ValueError('Unverified correlated office receipt.')
    for duplicate in result.get('duplicate_events',[]):
        if duplicate!={k:v for k,v in result.items() if k!='duplicate_events'}:raise ValueError('Conflicting duplicate receipt.')
    result={k:v for k,v in result.items() if k!='duplicate_events'}
    errand=errands.for_action(action.content)
    action.state=result['status'];action.content={**action.content,'receipt':result,
        'message':'Confirmed by the sandbox '+errand.place+' with a persisted receipt.' if action.state=='confirmed' else 'Rejected by the sandbox '+errand.place+'. Nothing is reserved.'}

def dispatch(engine,settings,claimed=None,gateway=None):
    from bring_vene.feasibility.service import requires_authorization
    claimed=claimed or claim(engine)
    if not claimed:return False
    action_id,lease_id=claimed
    with Session(engine) as session:
        initial=session.get(ExecutionRecord,action_id)
        if not initial:return True
        visit_id=initial.encounter_id
        sandbox_run=initial.content.get('sandbox_run')
    with Session(engine) as session,session.begin():
        _,view=lock(session,visit_id);action=session.get(ExecutionRecord,action_id)
        job=session.get(ExecutionOutboxRecord,action_id,with_for_update=True)
        if not job or job.lease_id!=lease_id:return True
        if action.state in TERMINAL:session.delete(job);return True
        reconcile=bool(action.content.get('send_started'))
        if not reconcile and (not scope_valid(session,view,action) or not fresh(action) or
            action.content.get('approval_digest')!=action_digest(action) or not action.content.get('order_id') or
            not action.content.get('clinician_id') or requires_authorization(session,view,action)):
            action.state='invalidated';action.content={**action.content,'message':'Scope, approval or prerequisite changed before dispatch. No request sent.'}
            session.delete(job);return True
        if not reconcile:
            # Dispatch linearizes at this durable decision, before network I/O.
            # Later revocation cannot recall already dispatched work. A crash/lost
            # response is reconciled; the office's request ID prevents duplicates.
            action.state='in_flight';action.content={**action.content,'send_started':True,'message':'Sandbox request dispatched; completion is not yet known.'}
        payload={'request_id':str(action.id),'slot_id':action.content['slot']['id'],
            'availability_revision':action.content['availability_revision'],'order_id':action.content['order_id']}
        institution=errands.for_action(action.content).institution
        if institution!='lab':payload['institution']=institution
    result=None
    try:
        adapter=gateway or for_run(settings,sandbox_run)
        if reconcile:
            check=adapter.call('/requests/'+str(action_id))
            if check['found']:
                if not check['result']:raise ValueError('Unverified reconciliation.')
                result=check['result']
            else:
                # Only authoritative absence permits another dispatch decision.
                with Session(engine) as session,session.begin():
                    _,view=lock(session,visit_id);action=session.get(ExecutionRecord,action_id)
                    job=session.get(ExecutionOutboxRecord,action_id,with_for_update=True)
                    if not job or job.lease_id!=lease_id:return True
                    if (not scope_valid(session,view,action) or not fresh(action) or
                        action.content.get('approval_digest')!=action_digest(action) or requires_authorization(session,view,action)):
                        action.state='cancelled';action.content={**action.content,'message':'Office reports no reservation; current permission or availability no longer permits dispatch.'}
                        session.delete(job);return True
                    action.state='in_flight'
        if result is None:result=adapter.call('/bookings',payload)
    except Exception:result=None
    # Office latency never holds a visit/media lock. Reacquire for receipt commit.
    with Session(engine) as session,session.begin():
        lock(session,visit_id);action=session.get(ExecutionRecord,action_id)
        job=session.get(ExecutionOutboxRecord,action_id,with_for_update=True)
        if not job or job.lease_id!=lease_id:return True
        try:
            if result is None:raise ValueError('No verified receipt.')
            finish_result(action,result);session.delete(job)
        except Exception:
            action.state='unknown';action.content={**action.content,'message':'Completion unknown. Reconciling with the office before any retry; do not book again.'}
            job.lease_id=None;job.lease_until=None;job.next_at=utc_now()+timedelta(seconds=1)
    return True
