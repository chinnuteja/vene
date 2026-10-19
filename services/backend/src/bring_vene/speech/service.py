import re
from datetime import timedelta
from uuid import uuid4,UUID
from sqlalchemy import select,and_,text
from sqlalchemy.orm import Session,aliased
from bring_vene.auth import authenticate
from bring_vene.domain.contracts import EncounterView
from bring_vene.domain.service import DomainError,utc_now
from bring_vene.understanding.service import fingerprint
from bring_vene.persistence.models import (EncounterRecord,SpeechStateRecord,SpeechConsentRecord,CueRecord,
    SpeechDeliveryRecord,SpeechMutationRecord,SessionRecord,MembershipRecord,CallRecord,CallConnectionRecord)
from bring_vene.speech.contracts import SpeechView,SpeakingConsent,PrivateCue,SpeechReceipt
from bring_vene.voice import service as voice

ACTIVE={'queued','generating','speaking'}


def provider(settings):
    if settings.tts_provider=='fixture' and settings.bring_vene_mode=='fixture':return 'fixture','Windows offline voice'
    if settings.tts_provider=='cartesia' and settings.cartesia_api_key and settings.cartesia_voice_id:return 'cartesia',settings.cartesia_model
    return 'unavailable',settings.cartesia_model


def lock(session,visit_id):
    encounter,call=voice.lock(session,visit_id)
    row=session.get(SpeechStateRecord,visit_id)
    if not row:
        row=SpeechStateRecord(encounter_id=visit_id,mode='private',mode_revision=0,revision=0,content={})
        session.add(row);session.flush()
    return encounter,call,row,EncounterView.model_validate(encounter.projection)


def authorized(session,visit_id,token,csrf=None,mutate=False):
    authenticate(session,token,visit_id,csrf,mutate=mutate)
    result=lock(session,visit_id)
    member,credential=authenticate(session,token,visit_id,csrf,mutate=mutate)
    return *result,member,credential


def patient(member):
    if member.role!='patient':raise DomainError(403,'Private suggestions are managed by the patient.')


def audit(session,visit_id,member,request):
    payload=request.model_dump(mode='json');key=fingerprint(payload)
    prior=session.scalar(select(SpeechMutationRecord).where(SpeechMutationRecord.encounter_id==visit_id,
        SpeechMutationRecord.command_id==request.command_id))
    if prior:
        if prior.actor_id!=member.id or prior.request_hash!=key:raise DomainError(409,'This command ID was already used.')
        return False
    session.add(SpeechMutationRecord(id=uuid4(),encounter_id=visit_id,command_id=request.command_id,actor_id=member.id,
        request_hash=key,content=payload,accepted_at=utc_now()));return True


def humans(session,call):
    return [c for c in voice.connections(session,call) if c.present and voice.valid_connection(session,c)] if call else []


def context_digest(session,encounter,call,row,view):
    return fingerprint({'visit_version':view.version,'consent_epoch':view.consent_epoch,'mode_revision':row.mode_revision,
        'permission_revision':row.content.get('permission_revision',0),
        'generation':str(call.generation) if call else None,
        'humans':sorted((str(c.id),str(c.membership_id),c.consent,c.track_epoch) for c in humans(session,call))})


def authority(session,encounter,row):
    if 'speech_authority' in session.info:return session.info['speech_authority']
    credential=session.get(SessionRecord,row.session_hash,populate_existing=True) if row.session_hash else None
    member=session.get(MembershipRecord,credential.membership_id,populate_existing=True) if credential else None
    return bool(credential and not credential.revoked_at and credential.expires_at>utc_now() and member and
        member.role=='patient' and member.encounter_id==encounter.id and not member.revoked_at)


def speech_gate(session,encounter,call,row,settings):
    if row.mode=='private':return False,'Choose an agreed speaking mode first.'
    if not authority(session,encounter,row):return False,'The patient needs to renew speaking permission.'
    if provider(settings)[0]=='unavailable':return False,'The speech provider is not configured.'
    if not voice.gate(session,encounter,call):return False,'Join and resume processing after everyone agrees.'
    if call.output_silenced:return False,'Vene output is silenced.'
    for connection in humans(session,call):
        agreement=session.get(SpeechConsentRecord,(connection.id,row.mode_revision))
        if not agreement or not agreement.agreed:return False,'Everyone present must agree to this speaking mode.'
    return True,''


def scope_allows(session,call,view,cue):
    roles={session.get(MembershipRecord,c.membership_id).role for c in humans(session,call)}-{'patient'}
    data=cue.content
    if data.get('execution_snapshots'):
        from bring_vene.execution.service import snapshot,scope_valid,fresh
        from bring_vene.persistence.models import ExecutionRecord
        for action_id,expected in data['execution_snapshots'].items():
            action=session.get(ExecutionRecord,UUID(action_id))
            if not action or action.encounter_id!=view.id or snapshot(action)!=expected or not scope_valid(session,view,action):return False
            if action.state in {'suggested','no_slot'} and not fresh(action):return False
    if data.get('priority_id'):
        item=next((p for p in view.priorities if str(p.id)==data['priority_id']),None)
        if not item or not item.selected or item.status in {'answered','deferred'}:return False
        if roles and (not view.preparation_approved or not item.approved or not roles<=set(item.audiences)):return False
    else:
        items=[p for p in view.plan if str(p.id) in data.get('plan_ids',[])]
        if not items or len(items)!=len(data.get('plan_ids',[])):return False
        visible={str(e.id) for e in view.evidence if roles<=set(e.audiences)}
        for item in items:
            if roles and (not roles<=set(item.audiences) or not item.evidence_refs or not {str(x) for x in item.evidence_refs}<=visible):return False
    return True


def plan_scope_allows(session,call,view,item):
    # Reuse the exact current participant/source gate before composing speech.
    from types import SimpleNamespace
    return scope_allows(session,call,view,SimpleNamespace(content={'plan_ids':[str(item.id)]}))


def eligible(session,encounter,call,row,view,cue,settings):
    if cue.state not in {'pending','approved'}:return False,'This suggestion is no longer pending.'
    if cue.expires_at<=utc_now():return False,'This suggestion expired; ask for a fresh one.'
    if cue.content['context_digest']!=context_digest(session,encounter,call,row,view):return False,'The conversation changed; refresh suggestions.'
    if not scope_allows(session,call,view,cue):return False,'Share the question or step and its sources with everyone present first.'
    return speech_gate(session,encounter,call,row,settings)


def make_cue(session,encounter,call,row,view,settings,*,key,title,suggestion,text,score,refs):
    digest=context_digest(session,encounter,call,row,view)
    existing=session.scalar(select(CueRecord).where(CueRecord.encounter_id==view.id,CueRecord.dedup_key==key,
        CueRecord.content['context_digest'].astext==digest,CueRecord.state.in_(['pending','approved']),CueRecord.expires_at>utc_now()))
    if existing:return existing
    recent=session.scalar(select(SpeechDeliveryRecord).join(CueRecord).where(SpeechDeliveryRecord.encounter_id==view.id,
        CueRecord.dedup_key==key,SpeechDeliveryRecord.approved_at>utc_now()-timedelta(seconds=settings.speech_cooldown_seconds)))
    if recent:return None
    cue=CueRecord(id=uuid4(),encounter_id=view.id,dedup_key=key,digest=fingerprint({'context':digest,'issuance':str(uuid4())}),score=score,state='pending',
        content={'title':title,'suggestion':suggestion,'text':text[:600],'context_digest':digest,**refs},created_at=utc_now(),
        expires_at=utc_now()+timedelta(seconds=settings.speech_ttl_seconds))
    session.add(cue);row.revision+=1;return cue


def refresh(session,encounter,call,row,view,settings):
    digest=context_digest(session,encounter,call,row,view)
    for cue in session.scalars(select(CueRecord).where(CueRecord.encounter_id==view.id,CueRecord.state.in_(['pending','approved']))):
        if cue.content['context_digest']!=digest or cue.expires_at<=utc_now():cue.state='invalidated';row.revision+=1
    ordered=[p for p in view.priorities if p.selected and p.status in {'open','partly_answered'}][:8]
    for rank,p in enumerate(ordered):
        make_cue(session,encounter,call,row,view,settings,key='priority:'+str(p.id),title=p.title,
            suggestion='This question still needs a clear answer. You can keep this cue private or ask Vene to bring it back.',
            text='Could we come back to this question? '+p.title,score=100-rank*5+(15 if p.status=='partly_answered' else 0),
            refs={'priority_id':str(p.id)})
    from bring_vene.execution.service import scope_valid,snapshot,fresh
    from bring_vene.execution import errands
    from bring_vene.persistence.models import ExecutionRecord
    for action in session.scalars(select(ExecutionRecord).where(ExecutionRecord.encounter_id==view.id).order_by(ExecutionRecord.created_at.desc()).limit(8)):
        if action.state not in {'no_slot','suggested','confirmed','unknown'} or not scope_valid(session,view,action):continue
        if action.state in {'no_slot','suggested'} and not fresh(action):continue
        data=action.content;errand=errands.for_action(data)
        place='office' if errand.kind=='lab' else errand.place  # Lab keeps its Phase 6 spoken wording.
        text=('The sandbox '+place+' found no '+data['window']+' '+errand.offered+'. Could we clarify another '+('appointment window' if errand.kind=='lab' else 'window')+'?' if action.state=='no_slot' else
            'The sandbox '+place+' reports: '+data['message'])
        make_cue(session,encounter,call,row,view,settings,key='office:'+str(action.id)+':'+action.state+':'+snapshot(action)[:12],
            title='Office check · '+data['title'],suggestion=data['message']+' Source: local sandbox '+place+', checked '+data.get('checked_at','unknown')+'.',
            text=text,score=180,refs={'plan_ids':[str(action.item_id)],'execution_snapshots':{str(action.id):snapshot(action)}})
    session.flush()
    # Bound the actionable queue; an old history is not a live generation queue.
    active=session.scalars(select(CueRecord).where(CueRecord.encounter_id==view.id,CueRecord.state=='pending')
        .order_by(CueRecord.score.desc(),CueRecord.created_at.desc())).all()
    for cue in active[8:]:cue.state='expired'


def receipt(delivery,private=False):
    end=delivery.content.get('last_human_at')
    from datetime import datetime
    end=datetime.fromisoformat(end) if end else None
    first=delivery.first_audio_at
    return SpeechReceipt(id=delivery.id,state=delivery.state,played_text=delivery.content.get('text') if delivery.state=='completed' else None,
        played_ms=delivery.played_ms,reason=delivery.reason,approved_at=delivery.approved_at,first_audio_at=first,stopped_at=delivery.stopped_at,
        stop_detected_at=delivery.content.get('stop_detected_at'),
        approval_to_audio_ms=max(0,int((first-delivery.approved_at).total_seconds()*1000)) if first else None,
        end_of_input_to_audio_ms=max(0,int((first-end).total_seconds()*1000)) if first and end else None)


def view(session,encounter,call,row,source,member,settings):
    participants=humans(session,call)
    consents=[SpeakingConsent(connection_id=c.id,name=session.get(MembershipRecord,c.membership_id).name,
        agreed=bool((agreement:=session.get(SpeechConsentRecord,(c.id,row.mode_revision))) and agreement.agreed)) for c in participants]
    delivery=session.get(SpeechDeliveryRecord,row.current_delivery) if row.current_delivery else None
    floor=delivery.state if delivery and delivery.state in {'generating','speaking'} else 'waiting' if delivery and delivery.state=='queued' else 'idle'
    if call and (call.manual_pause or call.ended):floor='paused'
    if provider(settings)[0]=='unavailable':floor='unavailable'
    cues=[]
    if member.role=='patient':
        for cue in session.scalars(select(CueRecord).where(CueRecord.encounter_id==encounter.id,CueRecord.state.in_(['pending','approved']))
            .order_by(CueRecord.score.desc(),CueRecord.created_at.desc()).limit(8)):
            if cue.content['context_digest']!=context_digest(session,encounter,call,row,source) or cue.expires_at<=utc_now():continue
            allowed,reason=eligible(session,encounter,call,row,source,cue,settings)
            cues.append(PrivateCue(id=cue.id,digest=cue.digest,title=cue.content['title'],suggestion=cue.content['suggestion'],
                public_text=cue.content['text'],score=cue.score,state=cue.state,expires_at=cue.expires_at,
                eligible_to_speak=allowed,blocked_reason=reason))
    rows=session.scalars(select(SpeechDeliveryRecord).where(SpeechDeliveryRecord.encounter_id==encounter.id)
        .order_by(SpeechDeliveryRecord.approved_at.desc()).limit(6)).all()
    # Private generation candidates never appear in a guest's API response. Receipts
    # require current membership and inclusion in the authorized playback audience.
    receipts=[]
    for d in rows:
        if member.role!='patient' and not (str(member.id) in d.content.get('audience',[]) and d.generation==getattr(call,'generation',None)):continue
        item=receipt(d)
        cue=session.get(CueRecord,d.cue_id)
        if member.role!='patient' and (d.content['digest']!=context_digest(session,encounter,call,row,source) or not cue or not scope_allows(session,call,source,cue)):
            item.played_text=None
        receipts.append(item)
    name,model=provider(settings)
    return SpeechView(observed_at=utc_now(),mode=row.mode,mode_revision=row.mode_revision,revision=row.revision,
        floor=floor,provider=name,provider_model=model,quiet_seconds=settings.speech_quiet_seconds,
        consents=consents,cues=cues,receipts=receipts,message='Private cues stay with the patient. Playback receipts do not prove what a person heard.')


def read(engine,visit_id,token,settings):
    with Session(engine) as session,session.begin():
        # Polling shares the scope lock after initialization. Readers can run
        # together; source/membership revocation still serializes with payload
        # assembly. Audio cancellation uses its independent notification path.
        member,_=authenticate(session,token,visit_id)
        row=session.get(SpeechStateRecord,visit_id)
        if not row:encounter,call,row,source=lock(session,visit_id)
        else:
            session.execute(text('SET LOCAL synchronous_commit=off'))
            encounter,call=voice.lock_media_snapshot(session,visit_id,read=True)
            session.refresh(row);source=EncounterView.model_validate(encounter.projection)
        member,_=authenticate(session,token,visit_id)
        return view(session,encounter,call,row,source,member,settings)


def mode(engine,visit_id,token,csrf,request,settings):
    with Session(engine) as session,session.begin():
        encounter,call,row,source,member,credential=authorized(session,visit_id,token,csrf,True);patient(member)
        if audit(session,visit_id,member,request):
            row.mode=request.mode;row.mode_revision+=1;row.revision+=1;row.session_hash=credential.token_hash
            row.content={**row.content,'cancel':'mode_changed'}
        return view(session,encounter,call,row,source,member,settings)


def agree(engine,visit_id,token,csrf,request,settings):
    with Session(engine) as session,session.begin():
        encounter,call,row,source,member,credential=authorized(session,visit_id,token,csrf,True)
        connection=session.get(CallConnectionRecord,request.connection_id)
        if (not call or not connection or connection.generation!=call.generation or connection.encounter_id!=visit_id or
            connection.session_hash!=credential.token_hash or not connection.present or not voice.valid_connection(session,connection)):
            raise DomainError(404,'Your current call connection is required.')
        if request.mode_revision!=row.mode_revision:raise DomainError(409,'The speaking mode changed.')
        if audit(session,visit_id,member,request):
            agreement=session.get(SpeechConsentRecord,(connection.id,row.mode_revision))
            changed=not agreement or agreement.agreed!=request.agreed
            if not agreement:session.add(SpeechConsentRecord(connection_id=connection.id,mode_revision=row.mode_revision,agreed=request.agreed))
            else:agreement.agreed=request.agreed
            if changed:row.content={**row.content,'permission_revision':row.content.get('permission_revision',0)+1}
            row.revision+=1
        session.flush();return view(session,encounter,call,row,source,member,settings)


def approve_in_session(session,encounter,call,row,source,cue,settings,standing=False):
    allowed,reason=eligible(session,encounter,call,row,source,cue,settings)
    if not allowed:raise DomainError(409,reason)
    if row.current_delivery:
        old=session.get(SpeechDeliveryRecord,row.current_delivery)
        if old and old.state in ACTIVE:raise DomainError(409,'Vene already has a queued contribution.')
    if row.last_output_at and (utc_now()-row.last_output_at).total_seconds()<settings.speech_cooldown_seconds:
        raise DomainError(409,'Give the conversation a moment before another contribution.')
    delivery=SpeechDeliveryRecord(id=uuid4(),encounter_id=source.id,cue_id=cue.id,generation=call.generation,state='queued',
        content={'text':cue.content['text'],'digest':cue.content['context_digest'],'audience':[str(c.membership_id) for c in humans(session,call)],
            'last_human_at':row.last_human_at.isoformat() if row.last_human_at else None,'standing_mode':standing},
        approved_at=utc_now(),played_ms=0)
    session.add(delivery);cue.state='approved';row.current_delivery=delivery.id;row.revision+=1
    row.content={**row.content,'cancel':None};session.flush();return delivery


def approve(engine,visit_id,token,csrf,request,settings):
    with Session(engine) as session,session.begin():
        encounter,call,row,source,member,_=authorized(session,visit_id,token,csrf,True);patient(member)
        if audit(session,visit_id,member,request):
            cue=session.get(CueRecord,request.cue_id)
            if not cue or cue.encounter_id!=visit_id:raise DomainError(404,'Suggestion not found.')
            if cue.digest!=request.digest:raise DomainError(409,'This suggestion changed.')
            approve_in_session(session,encounter,call,row,source,cue,settings)
        return view(session,encounter,call,row,source,member,settings)


def action(engine,visit_id,token,csrf,request,settings):
    with Session(engine) as session,session.begin():
        encounter,call,row,source,member,_=authorized(session,visit_id,token,csrf,True)
        if request.type!='stop':patient(member)
        if audit(session,visit_id,member,request):
            if request.type=='stop':row.content={**row.content,'cancel':'manual_stop'};row.revision+=1
            elif request.type=='refresh':refresh(session,encounter,call,row,source,settings)
            else:
                if row.mode!='closeout':raise DomainError(409,'Choose and agree to closeout mode first.')
                items=[p for p in source.plan if p.origin!='preparation' and plan_scope_allows(session,call,source,p)][:2]
                if not items:raise DomainError(409,'Share a next step and its sources with everyone present before requesting a closeout.')
                text='Before we finish, these are proposed next steps, not completed actions. '
                text+=' '.join(p.title+'. '+('Owner: '+p.owner+'. ' if p.owner else 'The owner still needs clarification. ')+
                    ('Timing: '+p.timeframe+'. ' if p.timeframe else 'Timing still needs clarification. ') for p in items)
                text+='Please confirm the required orders and who will follow through.'
                from bring_vene.execution.service import scope_valid,snapshot,fresh
                from bring_vene.persistence.models import ExecutionRecord
                checks=[a for a in session.scalars(select(ExecutionRecord).where(ExecutionRecord.encounter_id==source.id))
                    if a.item_id in {p.id for p in items} and scope_valid(session,source,a) and
                    (a.state in {'confirmed','unknown'} or a.state in {'suggested','no_slot'} and fresh(a))]
                if checks:text+=' Sandbox office checks: '+' '.join(a.content['message'] for a in checks)
                cue=make_cue(session,encounter,call,row,source,settings,key='closeout',title='Review the proposed next steps',
                    suggestion='A short review of shared proposed steps; it cannot authorize or complete them.',text=text,score=150,
                    refs={'plan_ids':[str(p.id) for p in items],'execution_snapshots':{str(a.id):snapshot(a) for a in checks}})
                session.flush()
                if not cue:raise DomainError(409,'A closeout was just requested; wait before repeating it.')
                approve_in_session(session,encounter,call,row,source,cue,settings)
        session.flush();return view(session,encounter,call,row,source,member,settings)


def observe_audio(session,visit_id,connection_id,non_silent):
    row=session.get(SpeechStateRecord,visit_id)
    if not row:return
    now=utc_now();data=dict(row.content);activity=dict(data.get('activity',{}));key=str(connection_id)
    old=activity.get(key,{})
    # Consecutive accepted media frames, not the database's processing speed.
    consecutive=int(old.get('count',0))+1
    if not non_silent:consecutive=0
    activity[key]={'count':consecutive,'at':now.isoformat()};data['activity']=dict(list(activity.items())[-12:])
    if non_silent:
        row.last_human_at=now
        if consecutive>=3 and row.current_delivery:
            delivery=session.get(SpeechDeliveryRecord,row.current_delivery)
            if delivery and delivery.state in {'generating','speaking'}:
                data['cancel']='human_interruption'
                if not delivery.content.get('stop_detected_at'):delivery.content={**delivery.content,'stop_detected_at':now.isoformat()}
    row.content=data


def observe_turn(session,encounter,source,settings):
    row=session.get(SpeechStateRecord,encounter.id)
    if not row:return
    # A transcript is a signal, never a new grant. The patient-selected on-request
    # mode is the standing authorization, bounded by current public scope/agreements.
    member=session.get(MembershipRecord,source.membership_id)
    text=source.content['text'].strip()
    target='vene' if re.match(r'^(?:Vene|Vini)\b[, :]',text,re.I) else 'other'
    row.content={**row.content,'last_target':target,'last_turn_at':utc_now().isoformat()}
    if row.mode!='on_request' or not member or member.role!='patient' or target!='vene':return
    if not re.search(r'\b(help|clarify|question)\b',text,re.I):return
    call=session.get(CallRecord,encounter.id);view_source=EncounterView.model_validate(encounter.projection)
    refresh(session,encounter,call,row,view_source,settings)
    pending=session.scalars(select(CueRecord).where(CueRecord.encounter_id==encounter.id,CueRecord.state=='pending')
        .order_by(CueRecord.score.desc())).all()
    for cue in pending:
        if eligible(session,encounter,call,row,view_source,cue,settings)[0]:
            try:approve_in_session(session,encounter,call,row,view_source,cue,settings,True)
            except DomainError:pass
            break


def playback_valid(session,encounter,call,row,view_source,delivery,settings):
    cue=session.get(CueRecord,delivery.cue_id)
    if not cue or cue.expires_at<=utc_now():return False,'expired'
    if delivery.generation!=getattr(call,'generation',None) or delivery.content['digest']!=context_digest(session,encounter,call,row,view_source):return False,'context_changed'
    if row.content.get('cancel'):return False,row.content['cancel']
    if not scope_allows(session,call,view_source,cue):return False,'scope_changed'
    if not speech_gate(session,encounter,call,row,settings)[0]:return False,'processing_or_agreement_stopped'
    return True,''


def next_delivery(engine,visit_id,generation,settings):
    with Session(engine) as session,session.begin():
        encounter,call,row,source=lock(session,visit_id)
        if not call or call.generation!=generation or not row.current_delivery:return None
        delivery=session.get(SpeechDeliveryRecord,row.current_delivery)
        if not delivery or delivery.state!='queued':return None
        valid,reason=playback_valid(session,encounter,call,row,source,delivery,settings)
        if not valid:
            finish_in_session(session,row,delivery,'cancelled',0,reason);return None
        if row.last_human_at and (utc_now()-row.last_human_at).total_seconds()<settings.speech_quiet_seconds:return None
        delivery.state='generating';row.revision+=1
        # A new quiet-floor claim starts a fresh interruption detector. A muted
        # track may send no silence frames; its prior speech must not turn one
        # later false-start frame into three consecutive frames.
        row.content={**row.content,'activity':{}}
        delivery.content={**delivery.content,'last_human_at':row.last_human_at.isoformat() if row.last_human_at else None}
        return {'id':delivery.id,'text':delivery.content['text']}


def permit_playback(engine,visit_id,delivery_id,settings):
    with Session(engine) as session,session.begin():
        # This reads authority and may stamp diagnostic stop detection, but
        # never grants permission or confirms a delivered contribution.
        session.execute(text('SET LOCAL synchronous_commit=off'))
        # Lock before the joined snapshot so it cannot retain rows from before
        # a concurrent mutation committed. No permission cache survives this
        # transaction or bypasses the encounter mutation lock.
        encounter=session.scalar(select(EncounterRecord).where(EncounterRecord.id==visit_id).with_for_update())
        if not encounter:return False,'ended'
        grant=aliased(SessionRecord);owner=aliased(MembershipRecord)
        snapshot=session.execute(select(EncounterRecord,CallRecord,SpeechStateRecord,SpeechDeliveryRecord,CueRecord,
            CallConnectionRecord,SessionRecord,MembershipRecord,SpeechConsentRecord,grant,owner)
            .join(CallRecord,CallRecord.encounter_id==EncounterRecord.id)
            .join(SpeechStateRecord,SpeechStateRecord.encounter_id==EncounterRecord.id)
            .join(SpeechDeliveryRecord,and_(SpeechDeliveryRecord.encounter_id==EncounterRecord.id,SpeechDeliveryRecord.id==delivery_id))
            .join(CueRecord,CueRecord.id==SpeechDeliveryRecord.cue_id)
            .outerjoin(CallConnectionRecord,and_(CallConnectionRecord.encounter_id==EncounterRecord.id,
                CallConnectionRecord.generation==CallRecord.generation,CallConnectionRecord.retired.is_(False)))
            .outerjoin(SessionRecord,SessionRecord.token_hash==CallConnectionRecord.session_hash)
            .outerjoin(MembershipRecord,MembershipRecord.id==CallConnectionRecord.membership_id)
            .outerjoin(SpeechConsentRecord,and_(SpeechConsentRecord.connection_id==CallConnectionRecord.id,
                SpeechConsentRecord.mode_revision==SpeechStateRecord.mode_revision))
            .outerjoin(grant,grant.token_hash==SpeechStateRecord.session_hash)
            .outerjoin(owner,owner.id==grant.membership_id)
            .where(EncounterRecord.id==visit_id)).all()
        if not snapshot:return False,'ended'
        encounter,call,row,delivery,cue,*_=snapshot[0]
        if delivery.state not in {'generating','speaking'}:return False,'ended'
        session.info['voice_connections']=((visit_id,call.generation),[r[5] for r in snapshot if r[5]])
        credential,member=snapshot[0][-2:];now=utc_now()
        session.info['speech_authority']=bool(credential and not credential.revoked_at and credential.expires_at>now and
            member and member.role=='patient' and member.encounter_id==visit_id and not member.revoked_at)
        source=EncounterView.model_validate(encounter.projection)
        valid,reason=playback_valid(session,encounter,call,row,source,delivery,settings)
        if not valid and not delivery.content.get('stop_detected_at'):
            delivery.content={**delivery.content,'stop_detected_at':utc_now().isoformat()}
        return valid,reason


def first_audio(engine,visit_id,delivery_id):
    with Session(engine) as session,session.begin():
        _,_,row,_=lock(session,visit_id);delivery=session.get(SpeechDeliveryRecord,delivery_id)
        if delivery and delivery.encounter_id==visit_id and not delivery.first_audio_at:
            delivery.first_audio_at=utc_now();delivery.state='speaking';row.revision+=1


def finish_in_session(session,row,delivery,state,played_ms,reason):
    if delivery.state not in ACTIVE:return
    delivery.state=state;delivery.played_ms=max(0,played_ms);delivery.reason=reason;delivery.stopped_at=utc_now()
    cue=session.get(CueRecord,delivery.cue_id)
    if cue:cue.state='played' if state=='completed' else 'interrupted' if state=='interrupted' else 'invalidated'
    row.last_output_at=delivery.stopped_at;row.revision+=1
    if row.current_delivery==delivery.id:row.current_delivery=None


def finish(engine,visit_id,delivery_id,state,played_ms,reason):
    with Session(engine) as session,session.begin():
        _,_,row,_=lock(session,visit_id);delivery=session.get(SpeechDeliveryRecord,delivery_id)
        if delivery and delivery.encounter_id==visit_id:finish_in_session(session,row,delivery,state,played_ms,reason)


def recover(engine,visit_id,generation):
    with Session(engine) as session,session.begin():
        _,call,row,_=lock(session,visit_id)
        if not call or call.generation!=generation or not row.current_delivery:return
        delivery=session.get(SpeechDeliveryRecord,row.current_delivery)
        if delivery and (delivery.generation!=generation or delivery.state in {'generating','speaking'}):
            finish_in_session(session,row,delivery,'cancelled',delivery.played_ms,'worker_restarted_playout_unknown')
