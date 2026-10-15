"""Scoped family generation, document review, and private next-visit preparation."""
from datetime import timedelta
from uuid import UUID,uuid4
from sqlalchemy import select,delete,func
from sqlalchemy.orm import Session
from bring_vene.auth import issue_invitation
from bring_vene.domain.contracts import EncounterView,Evidence,Priority
from bring_vene.domain.context import context_adapter
from bring_vene.domain.service import DomainError,utc_now
from bring_vene.execution.service import access,patient,plan_fingerprint
from bring_vene.understanding.service import fingerprint
from bring_vene.persistence.models import (EncounterRecord,EvidenceRecord,MembershipRecord,SessionRecord,ExecutionRecord,
    DocumentRecord,FamilyUpdateRecord,FamilyOutboxRecord,NextVisitRecord,OfficeCallbackRecord,CallRecord,OperationTraceRecord,
    CallbackNonceRecord,DeletionAuditRecord)
from bring_vene.continuity import documents
from bring_vene.continuity.contracts import (ContinuityView,DocumentView,FamilyUpdateView,NextVisitCreated)

def trace(session,visit_id,event,**identifiers):
    # Explicit allowlist; never accept arbitrary transcript/doc/message text.
    safe={k:v for k,v in identifiers.items() if k in {'action_id','update_id','document_id','next_id','duration_ms','attempts'}}
    session.add(OperationTraceRecord(id=uuid4(),encounter_id=visit_id,event=event,content=safe,created_at=utc_now()))

def family_input(session,view,recipient_id,plan_ids,fields):
    member=session.get(MembershipRecord,recipient_id,populate_existing=True)
    if not member or member.encounter_id!=view.id or member.role!='family' or member.revoked_at:
        raise DomainError(403,'Choose an invited family participant with current access.')
    scoped=context_adapter.view(view,'family',member.id)
    allowed={p.id:p for p in scoped.plan}
    if not set(plan_ids)<=set(allowed):raise DomainError(403,'Share each selected step and all its sources with this person first.')
    inputs=[]
    for index,item_id in enumerate(dict.fromkeys(plan_ids),1):
        item=allowed[item_id];values={}
        for field in dict.fromkeys(fields):
            if field=='office_status':
                row=session.scalar(select(ExecutionRecord).where(ExecutionRecord.encounter_id==view.id,ExecutionRecord.item_id==item_id)
                    .order_by(ExecutionRecord.created_at.desc()).limit(1))
                if row and row.content['plan_fingerprint']==plan_fingerprint(view,item_id):
                    values[field]=('Sandbox reservation confirmed' if row.state=='confirmed' else
                        'Office rejected the request' if row.state=='rejected' else 'Office completion remains '+row.state)
                    if row.state=='confirmed' and row.content.get('slot'):values[field]+=' · '+row.content['slot']['label']
                else:values[field]='No current office completion has been verified'
            elif field=='title':values[field]=item.title
            elif field=='owner':values[field]=item.owner or 'Owner needs clarification'
            elif field=='timeframe':values[field]=item.timeframe or 'Timing needs clarification'
        inputs.append({'step':index,'values':values,'plan_id':str(item_id)})
    # The formatter gets only the requested, permitted field dictionary.
    text='Next steps shared with you:\n'+'\n'.join(' · '.join(
        ('Step '+str(entry['step']),*[{'title':'Step','owner':'Who','timeframe':'When','office_status':'Office'}[k]+': '+str(v)
        for k,v in entry['values'].items()])) for entry in inputs)
    if len(text)>2000:raise DomainError(422,'Choose fewer steps or fields for this update.')
    scope_hash=fingerprint({'recipient':str(member.id),'epoch':view.consent_epoch,'inputs':inputs,'source_versions':{
        str(x):plan_fingerprint(view,x) for x in plan_ids}})
    return text,scope_hash

def update_digest(row):
    return fingerprint({'update_id':str(row.id),'recipient_id':str(row.recipient_id),
        'scope_hash':row.content['scope_hash'],'fields':row.content['fields'],'text':row.content['text']})

def update_valid(session,view,row,require_owner=True):
    credential=session.get(SessionRecord,row.session_hash,populate_existing=True)
    owner=session.get(MembershipRecord,credential.membership_id,populate_existing=True) if credential else None
    if require_owner and (not credential or credential.revoked_at or credential.expires_at<=utc_now() or not owner or owner.revoked_at or owner.encounter_id!=view.id or owner.role!='patient'):return False
    try:
        _,current=family_input(session,view,row.recipient_id,[UUID(x) for x in row.content['plan_ids']],row.content['fields'])
        return current==row.content['scope_hash']
    except DomainError:return False

def draft_family(engine,visit_id,token,csrf,request):
    with Session(engine) as session,session.begin():
        _,view,member,credential=access(session,visit_id,token,csrf);patient(member)
        text,scope_hash=family_input(session,view,request.recipient_id,request.plan_ids,request.fields)
        row=FamilyUpdateRecord(id=uuid4(),encounter_id=visit_id,recipient_id=request.recipient_id,session_hash=credential.token_hash,
            state='draft',created_at=utc_now(),content={'text':text,'scope_hash':scope_hash,'plan_ids':[str(x) for x in request.plan_ids],
                'fields':list(dict.fromkeys(request.fields))})
        session.add(row);trace(session,visit_id,'family_update_drafted',update_id=str(row.id));return row.id

def approve_family(engine,visit_id,update_id,token,csrf,request):
    with Session(engine) as session,session.begin():
        _,view,member,credential=access(session,visit_id,token,csrf);patient(member)
        row=session.get(FamilyUpdateRecord,update_id)
        if not row or row.encounter_id!=visit_id:raise DomainError(404,'Update not found.')
        if row.session_hash!=credential.token_hash or request.digest!=update_digest(row):raise DomainError(409,'Review the current update in the session that prepared it.')
        if row.state in {'queued','in_flight','unknown','delivered'}:return
        if row.state!='draft' or not update_valid(session,view,row):raise DomainError(409,'The selected fields, source or permission changed. Prepare a new update.')
        row.state='queued';row.content={**row.content,'approved_at':utc_now().isoformat(),'approval_digest':request.digest}
        session.add(FamilyOutboxRecord(update_id=row.id,next_at=utc_now(),attempts=0))
        trace(session,visit_id,'family_update_approved',update_id=str(row.id))

def source_snapshot(session,view,plan_ids):
    return fingerprint({'plans':{str(x):plan_fingerprint(view,x) for x in plan_ids},
        'office':[(str(a.id),a.state,a.content.get('receipt',{}).get('receipt_id')) for a in session.scalars(
            select(ExecutionRecord).where(ExecutionRecord.encounter_id==view.id,ExecutionRecord.item_id.in_(plan_ids)).order_by(ExecutionRecord.id))]})

def state(engine,visit_id,token,settings=None):
    with Session(engine) as session,session.begin():
        _,view,member,_=access(session,visit_id,token)
        scoped=context_adapter.view(view,member.role,member.id);visible_sources={e.id:e for e in scoped.evidence};visible_plans={p.id for p in scoped.plan}
        docs=[]
        for row in session.scalars(select(DocumentRecord).where(DocumentRecord.encounter_id==visit_id).order_by(DocumentRecord.created_at.desc()).limit(30)):
            if row.evidence_id not in visible_sources:continue
            source=visible_sources[row.evidence_id];data=row.content;current=documents.comparison_fingerprint(view,row)
            selected={UUID(x) for x in data['plan_ids']};can_review=selected<=visible_plans
            review_state='reviewed' if data.get('review_fingerprint')==current else 'stale' if data.get('review_fingerprint') or data['comparison_fingerprint']!=current else 'unresolved'
            # Guest comparison uses only their scoped steps; no unrestricted comparison followed by redaction.
            differences=documents.compare(scoped,source.text,[x for x in selected if x in visible_plans])
            docs.append(DocumentView(id=row.id,source=source,format=data['format'],sha256=data['sha256'],pages=data['pages'],
                differences=differences,review_state=review_state,fingerprint=current if member.role in {'patient','clinician'} and can_review else None,
                reviewed_by=data.get('reviewed_by') if review_state=='reviewed' and can_review else None,
                review_note=data.get('review_note') if review_state=='reviewed' and can_review else None))
        updates=[]
        for row in session.scalars(select(FamilyUpdateRecord).where(FamilyUpdateRecord.encounter_id==visit_id).order_by(FamilyUpdateRecord.created_at.desc()).limit(30)):
            valid=update_valid(session,view,row,require_owner=row.state!='delivered')
            if member.role!='patient' and not (member.id==row.recipient_id and row.state=='delivered' and valid):continue
            shown=row.state if valid or row.state in {'in_flight','unknown','delivered'} else 'invalidated'
            updates.append(FamilyUpdateView(id=row.id,recipient_id=row.recipient_id,state=shown,text=row.content['text'],fields=row.content['fields'],
                digest=update_digest(row) if member.role=='patient' and shown=='draft' else None,receipt=row.content.get('receipt')))
        recipients=[];next_visits=[]
        if member.role=='patient':
            recipients=[{'id':str(m.id),'name':m.name} for m in session.scalars(select(MembershipRecord).where(MembershipRecord.encounter_id==visit_id,MembershipRecord.role=='family',MembershipRecord.revoked_at.is_(None)))]
            for link in session.scalars(select(NextVisitRecord).where(NextVisitRecord.origin_id==visit_id)):
                try:stale=source_snapshot(session,view,[UUID(x) for x in link.content['plan_ids']])!=link.content['source_digest']
                except DomainError:stale=True
                next_visits.append({'encounter_id':str(link.next_id),'stale':stale,'visit_at':link.content['visit_at']})
        count=session.scalar(select(func.count()).select_from(OfficeCallbackRecord).where(OfficeCallbackRecord.encounter_id==visit_id)) if member.role=='patient' else 0
        call=session.get(CallRecord,visit_id)
        return ContinuityView(documents=docs,family_updates=updates,family_recipients=recipients,next_visits=next_visits,
            callback_count=count,conversation_gap_since=call.gap_since if call else None,
            sandbox_tools_enabled=bool(settings and settings.bring_vene_development and settings.bring_vene_mode=='fixture' and member.role=='patient'))

def next_visit(engine,visit_id,token,csrf,request):
    with Session(engine) as session,session.begin():
        _,view,member,_=access(session,visit_id,token,csrf);patient(member)
        if request.visit_at<=utc_now():raise DomainError(422,'Choose a future date for this preparation.')
        if not set(request.plan_ids)<={p.id for p in view.plan}:raise DomainError(404,'A selected step was not found.')
        source_digest=source_snapshot(session,view,request.plan_ids)
        prior=session.scalar(select(NextVisitRecord).where(NextVisitRecord.origin_id==visit_id,NextVisitRecord.content['source_digest'].astext==source_digest,
            NextVisitRecord.content['visit_at'].astext==request.visit_at.isoformat()))
        if prior:
            owner=session.scalar(select(MembershipRecord).where(MembershipRecord.encounter_id==prior.next_id,MembershipRecord.role=='patient',MembershipRecord.revoked_at.is_(None)))
            if owner:return NextVisitCreated(encounter_id=prior.next_id,invitation=issue_invitation(session,owner))
        evidence=[];priorities=[]
        for item in view.plan:
            if item.id not in request.plan_ids:continue
            source=Evidence(id=uuid4(),source_type='patient_report',title='Carried into your private preparation',observed_at=utc_now(),origin='human',
                text='Earlier draft: '+item.title+'. Owner: '+(item.owner or 'unclear')+'. Timing: '+(item.timeframe or 'unclear')+'. Review the outcome with your clinician; this is not a new order.')
            evidence.append(source);priorities.append(Priority(id=uuid4(),title='What happened with '+item.title.lower()+'?',detail=source.text,selected=True,status='open',evidence_refs=[source.id]))
        if not priorities:
            priorities=[Priority(id=uuid4(),title='What still needs an answer?',detail='Choose what to bring into this new visit.',selected=True,status='open',evidence_refs=[])]
        fresh=EncounterView(id=uuid4(),version=0,patient=view.patient.model_copy(deep=True),title='Preparing for your next visit',clinician='Your next clinician',
            visit_at=request.visit_at,processing_state='preparing',priorities=priorities,plan=[],evidence=evidence,updated_at=utc_now())
        session.add(EncounterRecord(id=fresh.id,version=0,projection=fresh.model_dump(mode='json'),updated_at=fresh.updated_at));session.flush()
        for source in evidence:session.add(EvidenceRecord(id=source.id,encounter_id=fresh.id,content=source.model_dump(mode='json')))
        owner=MembershipRecord(id=uuid4(),encounter_id=fresh.id,role='patient',name=member.name);session.add(owner);session.flush()
        session.add(NextVisitRecord(origin_id=visit_id,next_id=fresh.id,content={'source_digest':source_digest,'plan_ids':[str(x) for x in request.plan_ids],'visit_at':request.visit_at.isoformat()}))
        trace(session,visit_id,'next_preparation_created',next_id=str(fresh.id))
        return NextVisitCreated(encounter_id=fresh.id,invitation=issue_invitation(session,owner))

def delete_encounter(engine,visit_id,token,csrf,request):
    with Session(engine) as session,session.begin():
        _,view,member,_=access(session,visit_id,token,csrf);patient(member)
        if view.version!=request.expected_version:raise DomainError(409,'The saved visit changed; review it before deletion.')
        ids=[];frontier=[visit_id]
        while frontier:
            current=frontier.pop()
            if current in ids:continue
            ids.append(current)
            frontier.extend(session.scalars(select(NextVisitRecord.next_id).where(NextVisitRecord.origin_id==current)).all())
        # A local purge cannot safely discard identifiers needed to reconcile dispatched work.
        if session.scalar(select(ExecutionRecord.id).where(ExecutionRecord.encounter_id.in_(ids),ExecutionRecord.state.in_(['in_flight','unknown'])).limit(1)) or session.scalar(
            select(FamilyUpdateRecord.id).where(FamilyUpdateRecord.encounter_id.in_(ids),FamilyUpdateRecord.state.in_(['in_flight','unknown'])).limit(1)):
            raise DomainError(409,'Reconcile the dispatched work before deleting its local record. Deletion cannot cancel an external reservation.')
        calls=session.scalars(select(CallRecord).where(CallRecord.encounter_id.in_(ids)).with_for_update()).all()
        if any(not c.ended and c.active_tasks for c in calls):raise DomainError(409,'End active processing before deleting this visit.')
        # Cascades purge projections, sources, sessions, commands, proposals, outboxes,
        # document text, callback records, next-visit copies and operational traces.
        for target_id in reversed(ids):session.execute(delete(EncounterRecord).where(EncounterRecord.id==target_id))
        session.add(DeletionAuditRecord(id=uuid4(),deleted_at=utc_now(),visit_count=len(ids)))
        return {'deleted':True,'visits_purged':len(ids),'external_reservations_cancelled':False}

def prune_metadata(engine,settings):
    with Session(engine) as session,session.begin():
        session.execute(delete(CallbackNonceRecord).where(CallbackNonceRecord.accepted_at<utc_now()-timedelta(minutes=3)))
        session.execute(delete(OperationTraceRecord).where(OperationTraceRecord.created_at<utc_now()-timedelta(days=settings.continuity_retention_days)))
