import hashlib
import json
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.auth import authenticate, FIXTURE_MEMBERS
from bring_vene.domain.contracts import EncounterView, Evidence, PlanItem, UnderstandingStatus
from bring_vene.domain.service import DomainError, utc_now
from bring_vene.persistence.models import (EncounterRecord,EvidenceRecord,UnderstandingRecord,
    TranscriptSourceRecord,InterpretationRunRecord,UnderstandingMutationRecord,MembershipRecord,
    SessionRecord,CallRecord,CallConnectionRecord)
from bring_vene.understanding.gateway import configuration,PROMPT_VERSION
from bring_vene.voice.service import gate as audio_gate


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def lock(session,visit_id):
    encounter=session.scalar(select(EncounterRecord).where(EncounterRecord.id==visit_id).with_for_update())
    if not encounter:raise DomainError(404,'Visit not found.')
    row=session.get(UnderstandingRecord,visit_id)
    if not row:
        row=UnderstandingRecord(encounter_id=visit_id,enabled=False,revision=0,processed_revision=0,state='off',message='')
        session.add(row);session.flush()
    return encounter,row,EncounterView.model_validate(encounter.projection)


def authorized(session,visit_id,token,csrf):
    encounter,row,view=lock(session,visit_id)
    member,credential=authenticate(session,token,visit_id,csrf,mutate=True)
    if member.role!='patient':raise DomainError(403,'Only the patient can manage private understanding.')
    return encounter,row,view,member,credential


def status(row,settings):
    provider,model=configuration(settings)
    return UnderstandingStatus(enabled=row.enabled,state=row.state,revision=row.revision,
        processed_revision=row.processed_revision,provider=provider,model=model,prompt_version=PROMPT_VERSION,
        message=row.message,fixture_input_enabled=settings.bring_vene_development and settings.bring_vene_mode=='fixture')


def stamp(encounter,row,view,settings):
    view.understanding=status(row,settings);view.version+=1;view.updated_at=utc_now()
    encounter.projection=view.model_dump(mode='json');encounter.version=view.version;encounter.updated_at=view.updated_at


def mutation(session,visit_id,member,request,kind):
    body={'kind':kind,**request.model_dump(mode='json')};key=fingerprint(body)
    prior=session.scalar(select(UnderstandingMutationRecord).where(UnderstandingMutationRecord.encounter_id==visit_id,
        UnderstandingMutationRecord.command_id==request.command_id))
    if prior:
        if prior.actor_id!=member.id or prior.request_hash!=key:raise DomainError(409,'This command ID was already used.')
        return False
    session.add(UnderstandingMutationRecord(id=uuid4(),encounter_id=visit_id,command_id=request.command_id,
        actor_id=member.id,request_hash=key,content=body,accepted_at=utc_now()))
    return True


def processing(engine,visit_id,token,csrf,request,settings):
    with Session(engine) as session,session.begin():
        encounter,row,view,member,credential=authorized(session,visit_id,token,csrf)
        if not mutation(session,visit_id,member,request,'processing'):return view
        if request.enabled and configuration(settings)[0]=='unavailable':raise DomainError(503,'The model provider is not configured.')
        row.enabled=request.enabled;row.session_hash=credential.token_hash
        row.state='queued' if row.enabled and row.revision>row.processed_revision else 'ready' if row.enabled else 'off'
        row.message='';view.consent_epoch+=1
        stamp(encounter,row,view,settings)
        return view


def add_source(session,encounter,row,view,member,text,origin,settings,utterance_id=None):
    if len(view.evidence)>=400:raise DomainError(409,'This visit has reached its source limit.')
    source=Evidence(id=uuid4(),source_type='conversation',title=('Fictional turn \u00b7 ' if origin=='fixture' else 'Conversation \u00b7 ')+member.name,
        text=text[:2000].strip(),observed_at=utc_now(),speaker=member.name,origin=origin,version=1)
    session.add(EvidenceRecord(id=source.id,encounter_id=view.id,content=source.model_dump(mode='json')))
    session.flush()
    session.add(TranscriptSourceRecord(id=source.id,encounter_id=view.id,membership_id=member.id,utterance_id=utterance_id,
        version=1,content=source.model_dump(mode='json'),history=[],finalized_at=source.observed_at))
    view.evidence.append(source);row.revision+=1;row.state='queued' if row.enabled else 'off';row.message=''
    stamp(encounter,row,view,settings)
    session.flush()
    from bring_vene.speech.service import observe_turn
    observe_turn(session,encounter,session.get(TranscriptSourceRecord,source.id),settings)
    return source


def fixture_turn(engine,visit_id,token,csrf,request,settings):
    if not (settings.bring_vene_development and settings.bring_vene_mode=='fixture'):
        raise DomainError(404,'Not found.')
    with Session(engine) as session,session.begin():
        encounter,row,view,member,_=authorized(session,visit_id,token,csrf)
        if not mutation(session,visit_id,member,request,'fixture_turn'):return view
        speaker=session.scalar(select(MembershipRecord).where(MembershipRecord.encounter_id==visit_id,MembershipRecord.role==request.speaker,MembershipRecord.revoked_at.is_(None)).order_by(MembershipRecord.id).limit(1))
        if not speaker or speaker.encounter_id!=visit_id or speaker.revoked_at:raise DomainError(404,'Fictional participant not found.')
        if len(request.text.strip())<3:raise DomainError(422,'A finalized turn needs text.')
        add_source(session,encounter,row,view,speaker,request.text,'fixture',settings)
        return view


def ingest_voice(session,visit_id,utterance,settings):
    # Called in the same transaction after the transport's epoch/consent permit.
    encounter,row,view=lock(session,visit_id)
    member=session.get(MembershipRecord,utterance.membership_id)
    if not member or member.encounter_id!=visit_id or member.revoked_at:return
    if session.scalar(select(TranscriptSourceRecord.id).where(TranscriptSourceRecord.utterance_id==utterance.id)):return
    add_source(session,encounter,row,view,member,utterance.text,'deepgram',settings,utterance.id)


def invalidate(view,source_id):
    retained=[]
    for item in view.plan:
        if item.origin!='preparation' and source_id in item.evidence_refs:
            if item.external_completed:
                item.needs_clarification=True;item.status='waiting';item.revision+=1
                item.explanation='Source corrected. External completion still needs reconciliation; no booking was reversed.'
                retained.append(item)
        else:retained.append(item)
    view.plan=retained
    for priority in view.priorities:
        if source_id in priority.answer_refs:
            priority.status='open';priority.answer_detail=None;priority.answer_refs=[];priority.answer_audiences=[]


def correct_source(engine,visit_id,token,csrf,source_id,request,settings):
    with Session(engine) as session,session.begin():
        encounter,row,view,member,_=authorized(session,visit_id,token,csrf)
        if not mutation(session,visit_id,member,request,'correct_source:'+str(source_id)):return view
        source=session.get(TranscriptSourceRecord,source_id)
        if not source or source.encounter_id!=visit_id:raise DomainError(404,'Conversation source not found.')
        if source.version!=request.expected_source_version:raise DomainError(409,'This source was corrected in another window.')
        if len(source.history)>=20:raise DomainError(409,'This source has reached its correction limit.')
        if len(request.text.strip())<3:raise DomainError(422,'A corrected source needs text.')
        old=source.content;source.history=[*source.history,old];source.version+=1
        evidence=next(e for e in view.evidence if e.id==source_id)
        evidence.text=request.text.strip();evidence.version=source.version;evidence.origin='human'
        evidence.observed_at=utc_now();source.finalized_at=evidence.observed_at
        # A changed source is private again until the patient deliberately shares it.
        evidence.audiences=[];source.content=evidence.model_dump(mode='json')
        session.get(EvidenceRecord,source_id).content=source.content
        invalidate(view,source_id);row.revision+=1;row.message='';row.state='queued' if row.enabled else 'off'
        view.consent_epoch+=1;stamp(encounter,row,view,settings)
        return view


def correct_plan(engine,visit_id,token,csrf,item_id,request,settings):
    with Session(engine) as session,session.begin():
        encounter,row,view,member,_=authorized(session,visit_id,token,csrf)
        if not mutation(session,visit_id,member,request,'correct_plan:'+str(item_id)):return view
        item=next((i for i in view.plan if i.id==item_id),None)
        if not item:raise DomainError(404,'Plan item not found.')
        if item.revision!=request.expected_item_revision:raise DomainError(409,'This step changed in another window.')
        if len(request.detail.strip())<3:raise DomainError(422,'A correction needs context.')
        source=Evidence(id=uuid4(),source_type='patient_report',title='Your correction · '+item.title,
            text=request.detail.strip(),observed_at=utc_now(),speaker=member.name,origin='human')
        session.add(EvidenceRecord(id=source.id,encounter_id=visit_id,content=source.model_dump(mode='json')))
        view.evidence.append(source)
        item.detail=request.detail.strip();item.owner=request.owner.strip() if request.owner else None
        item.timeframe=request.timeframe.strip() if request.timeframe else None;item.location=request.location.strip() if request.location else None
        item.origin='human';item.audiences=[];item.evidence_refs=[source.id];item.revision+=1
        item.needs_clarification=not item.owner or not item.timeframe
        item.explanation='Corrected by the patient. This does not confirm a clinical decision, order or external completion.'
        row.revision+=1;row.state='queued' if row.enabled else 'off';view.consent_epoch+=1
        stamp(encounter,row,view,settings)
        return view


def authority(session,encounter,row):
    if not row.enabled or not row.session_hash:return False
    credential=session.get(SessionRecord,row.session_hash,populate_existing=True)
    member=session.get(MembershipRecord,credential.membership_id,populate_existing=True) if credential else None
    return bool(credential and not credential.revoked_at and credential.expires_at>utc_now() and member and
        member.encounter_id==encounter.id and member.role=='patient' and not member.revoked_at)


def input_snapshot(session,encounter,row,view):
    sources=session.scalars(select(TranscriptSourceRecord).where(TranscriptSourceRecord.encounter_id==view.id)
        .order_by(TranscriptSourceRecord.finalized_at.desc(),TranscriptSourceRecord.id).limit(30)).all()
    # Real audio sources also require the intended call processing path to be active.
    if any(s.utterance_id for s in sources):
        call=session.get(CallRecord,view.id)
        if not call or not audio_gate(session,encounter,call):return None
    bounded=[];characters=0
    for source in reversed(sources):
        if characters+len(source.content['text'])>24000:continue
        characters+=len(source.content['text'])
        bounded.append({'id':str(source.id),'version':source.version,'speaker':source.content['speaker'],
            'text':source.content['text'],'origin':source.content['origin']})
    return {'encounter_version':view.version,'consent_epoch':view.consent_epoch,'revision':row.revision,
        'prompt_version':PROMPT_VERSION,'sources':bounded,
        'priorities':[{'id':str(p.id),'title':p.title[:160],'detail':p.detail[:400]} for p in view.priorities if p.selected][:20]}


def prepare(engine,visit_id,settings):
    with Session(engine) as session,session.begin():
        encounter,row,view=lock(session,visit_id)
        if not authority(session,encounter,row) or row.revision<=row.processed_revision:return None
        snapshot=input_snapshot(session,encounter,row,view)
        if snapshot is None:
            if row.state!='paused':row.state='paused';stamp(encounter,row,view,settings)
            return None
        row.state='processing';row.message='';stamp(encounter,row,view,settings)
        snapshot=input_snapshot(session,encounter,row,view)
        provider,model=configuration(settings)
        run=InterpretationRunRecord(id=uuid4(),encounter_id=visit_id,fingerprint=fingerprint(snapshot),state='running',
            provider=provider,model=model,input_snapshot=snapshot,created_at=utc_now())
        session.add(run)
        return run.id,snapshot


def current(session,run,encounter,row,view):
    snapshot=input_snapshot(session,encounter,row,view)
    return authority(session,encounter,row) and snapshot is not None and fingerprint(snapshot)==run.fingerprint


def still_current(engine,run_id):
    with Session(engine) as session,session.begin():
        run=session.get(InterpretationRunRecord,run_id)
        if not run or run.state!='running':return False
        encounter,row,view=lock(session,run.encounter_id)
        return current(session,run,encounter,row,view)


def valid_citations(citations,sources):
    return bool(citations) and all(str(c.source_id) in sources and c.version==sources[str(c.source_id)]['version'] and
        c.quote.strip() in sources[str(c.source_id)]['text'] for c in citations)


def apply_result(engine,run_id,result,settings):
    with Session(engine) as session,session.begin():
        run=session.get(InterpretationRunRecord,run_id)
        if not run or run.state!='running':return False
        encounter,row,view=lock(session,run.encounter_id)
        if not current(session,run,encounter,row,view):
            run.state='stale';run.finished_at=utc_now();return False
        sources={s['id']:s for s in run.input_snapshot['sources']};invalid=False
        selected={str(p.id):p for p in view.priorities if p.selected}
        # A run assesses the whole supplied question set. Omitted/ungrounded answers
        # cannot leave a previous model interpretation looking current.
        for target in selected.values():
            if target.answer_refs:
                target.status='open';target.answer_detail=None;target.answer_refs=[];target.answer_audiences=[]
        answer_ids=set();topics=set()
        for answer in result.extraction.answers:
            target=selected.get(str(answer.priority_id))
            if target and target.id not in answer_ids and answer.status=='open' and not answer.citations:
                # An absence of an answer has no supporting quote. Keep it open
                # without storing unsourced prose or inventing a clarification.
                answer_ids.add(target.id);continue
            if not target or target.id in answer_ids or not valid_citations(answer.citations,sources):invalid=True;continue
            answer_ids.add(target.id);target.status=answer.status;target.answer_detail=answer.explanation
            target.answer_refs=list(dict.fromkeys(c.source_id for c in answer.citations))
            target.answer_audiences=[]
        for proposal in result.extraction.steps:
            if proposal.topic in topics or not valid_citations(proposal.citations,sources):invalid=True;continue
            topics.add(proposal.topic)
            item_id=uuid5(NAMESPACE_URL,str(view.id)+'/interpretation/'+proposal.topic)
            old=next((i for i in view.plan if i.id==item_id),None)
            if old and (old.origin=='human' or old.external_completed):continue
            quote=' '.join(c.quote for c in proposal.citations).casefold()
            values=[proposal.owner,proposal.timeframe,proposal.location]
            if any(v and (v.casefold() not in quote or v.casefold() in {'they','them','someone','it','we'}) for v in values):
                invalid=True;proposal.owner=None;proposal.timeframe=None;proposal.location=None;proposal.needs_clarification=True
                proposal.explanation='Some proposed details were not directly supported. Clarify who, when and where.'
            item=PlanItem(id=item_id,title=proposal.title,detail=proposal.detail,owner=proposal.owner,
                timeframe=proposal.timeframe,location=proposal.location,dependencies=proposal.dependencies,
                status='draft',evidence_refs=list(dict.fromkeys(c.source_id for c in proposal.citations)),origin='interpretation',
                needs_clarification=proposal.needs_clarification,explanation=proposal.explanation,
                revision=(old.revision+1 if old else 1),audiences=[])
            view.plan=[i for i in view.plan if i.id!=item_id];view.plan.append(item)
        # Untrusted citation failures never publish invented details or change approvals.
        if invalid:
            item_id=uuid5(NAMESPACE_URL,str(view.id)+'/interpretation/clarification')
            view.plan=[i for i in view.plan if i.id!=item_id]
            view.plan.append(PlanItem(id=item_id,title='Clarify what was meant',
                detail='An interpretation could not be grounded in the current sources. Please clarify before relying on it.',
                evidence_refs=[],origin='interpretation',needs_clarification=True))
        run.state='applied';run.output=result.extraction.model_dump(mode='json');run.model=result.model[:100];run.finished_at=utc_now()
        row.processed_revision=row.revision;row.state='ready';row.message='Some details need clarification.' if invalid else ''
        stamp(encounter,row,view,settings);return True


def finish_failed(engine,run_id,settings,stale=False):
    with Session(engine) as session,session.begin():
        run=session.get(InterpretationRunRecord,run_id)
        if not run or run.state!='running':return
        encounter,row,view=lock(session,run.encounter_id)
        valid=current(session,run,encounter,row,view)
        run.state='stale' if stale or not valid else 'failed';run.finished_at=utc_now()
        if valid and not stale:
            row.state='unavailable';row.message='Understanding is unavailable. Your conversation and saved plan remain usable.'
            row.processed_revision=row.revision;stamp(encounter,row,view,settings)


def retry(engine,visit_id,token,csrf,request,settings):
    with Session(engine) as session,session.begin():
        encounter,row,view,member,_=authorized(session,visit_id,token,csrf)
        if not mutation(session,visit_id,member,request,'retry'):return view
        row.revision+=1;row.state='queued' if row.enabled else 'off';row.message='';stamp(encounter,row,view,settings)
        return view
