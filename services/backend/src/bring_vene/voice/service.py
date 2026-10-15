import hashlib
import json
import asyncio
import aiohttp
from datetime import timedelta
from uuid import UUID, uuid4
from livekit import api
from sqlalchemy import select,and_,text
from sqlalchemy.orm import Session
from bring_vene.auth import authenticate, digest
from bring_vene.domain.service import DomainError, utc_now
from bring_vene.persistence.models import (EncounterRecord, MembershipRecord, SessionRecord, CallRecord,
    CallConnectionRecord, AudioReceiptRecord, UtteranceRecord, CallEventRecord)
from bring_vene.voice.contracts import (CallView, CallParticipant, CallAdmission, AudioReceipt, CallDiagnostics, Utterance)


def room_name(call):
    return f'vene-{call.encounter_id}-{call.generation}'


def identity(connection):
    return f'human:{connection.id}'


def configured(settings):
    return bool(settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret)


def provider(settings):
    if settings.voice_provider == 'fixture' and settings.bring_vene_mode == 'fixture': return 'fixture'
    if settings.voice_provider == 'deepgram' and settings.deepgram_api_key: return 'deepgram'
    return 'unavailable'


def valid_connection(session, connection, now=None):
    now=now or utc_now()
    credential=session.get(SessionRecord,connection.session_hash)
    member=session.get(MembershipRecord,connection.membership_id)
    return bool(not connection.retired and credential and member and not credential.revoked_at
                and credential.expires_at>now and not member.revoked_at and connection.expires_at>now)


def epoch(encounter):
    return encounter.projection.get('consent_epoch',0)


def bump(encounter, call):
    projection=dict(encounter.projection)
    projection['consent_epoch']=epoch(encounter)+1
    projection['updated_at']=utc_now().isoformat()
    projection['processing_state']='paused' if call.manual_pause or call.ended else 'active'
    encounter.projection=projection
    encounter.updated_at=utc_now()
    call.revision+=1


def lock(session, visit_id):
    encounter=session.scalar(select(EncounterRecord).where(EncounterRecord.id==visit_id).with_for_update())
    if not encounter: raise DomainError(404,'Visit not found.')
    call=session.get(CallRecord,visit_id)
    return encounter,call


def lock_media_snapshot(session,visit_id,read=False):
    """Lock first, then read current participant authority in one statement.

    Strong references live only for this transaction. No stale permission cache
    is used across frames, room updates, or authenticated requests.
    """
    # A joined SELECT FOR UPDATE can retain pre-wait joined rows after the
    # encounter lock becomes available. The second statement sees the state
    # committed by the mutation we waited for, including a reopened generation.
    encounter=session.scalar(select(EncounterRecord).where(EncounterRecord.id==visit_id).with_for_update(read=read))
    if not encounter:raise DomainError(404,'Visit not found.')
    rows=session.execute(select(EncounterRecord,CallRecord,CallConnectionRecord,SessionRecord,MembershipRecord)
        .outerjoin(CallRecord,CallRecord.encounter_id==EncounterRecord.id)
        .outerjoin(CallConnectionRecord,and_(CallConnectionRecord.encounter_id==EncounterRecord.id,
            CallConnectionRecord.generation==CallRecord.generation,CallConnectionRecord.retired.is_(False)))
        .outerjoin(SessionRecord,SessionRecord.token_hash==CallConnectionRecord.session_hash)
        .outerjoin(MembershipRecord,MembershipRecord.id==CallConnectionRecord.membership_id)
        .where(EncounterRecord.id==visit_id)).all()
    if not rows:raise DomainError(404,'Visit not found.')
    encounter,call=rows[0][:2]
    session.info['media_snapshot']=rows
    if call:session.info['voice_connections']=((visit_id,call.generation),[r[2] for r in rows if r[2]])
    return encounter,call


def authorized_lock(session,visit_id,token,csrf):
    authenticate(session,token,visit_id,csrf,mutate=True)
    encounter,call=lock(session,visit_id)
    member,credential=authenticate(session,token,visit_id,csrf,mutate=True)
    return encounter,call,member,credential


def connections(session,call):
    snapshot=session.info.get('voice_connections')
    if snapshot is not None and snapshot[0]==(call.encounter_id,call.generation):return snapshot[1]
    return session.scalars(select(CallConnectionRecord).where(CallConnectionRecord.encounter_id==call.encounter_id,
        CallConnectionRecord.generation==call.generation,CallConnectionRecord.retired.is_(False))).all()


def gate(session,encounter,call):
    if not call or call.ended or call.manual_pause or call.worker_error:return False
    humans=[c for c in connections(session,call) if c.present]
    return bool(humans and all(valid_connection(session,c) and c.consent=='agreed' for c in humans))


def view(session,encounter,call,settings,member,credential):
    if not call:
        return CallView(observed_at=utc_now(),encounter_id=encounter.id,generation=UUID(int=0),revision=0,consent_epoch=epoch(encounter),
            state='waiting' if configured(settings) else 'unavailable',manual_pause=True,output_silenced=False,
            worker_ready=False,provider=provider(settings),participants=[])
    rows=connections(session,call)
    active=[c for c in rows if c.present and valid_connection(session,c)]
    worker_ready=bool(not call.worker_error and call.worker_seen_at and (utc_now()-call.worker_seen_at).total_seconds()<3)
    if call.ended:state='ended'
    elif not configured(settings) or not worker_ready or provider(settings)=='unavailable' or call.worker_error:state='unavailable'
    elif call.manual_pause:state='paused' if call.stopped_epoch>=epoch(encounter) else 'stopping'
    elif not active:state='waiting'
    elif any(c.consent!='agreed' for c in active):state='consent_needed'
    else:state='active'
    return CallView(observed_at=utc_now(),encounter_id=encounter.id,generation=call.generation,revision=call.revision,
        consent_epoch=epoch(encounter),state=state,manual_pause=call.manual_pause,output_silenced=call.output_silenced,
        worker_ready=worker_ready,provider=provider(settings),gap_since=call.gap_since,participants=[CallParticipant(connection_id=c.id,
        membership_id=c.membership_id,name=session.get(MembershipRecord,c.membership_id).name,
        role=session.get(MembershipRecord,c.membership_id).role,present=c.present,consent=c.consent,track_epoch=c.track_epoch)
        for c in rows if valid_connection(session,c)],own_connection_id=next((c.id for c in rows if c.session_hash==credential.token_hash and valid_connection(session,c)),None))


def read_call(engine,visit_id,token,settings):
    with Session(engine) as session,session.begin():
        # Row-lock WAL is ephemeral on these read-only polls. Authority-changing
        # transactions retain the database's durable commit default.
        session.execute(text('SET LOCAL synchronous_commit=off'))
        member,credential=authenticate(session,token,visit_id)
        encounter,call=lock_media_snapshot(session,visit_id,read=True)
        return view(session,encounter,call,settings,member,credential)


def admit(engine,visit_id,token,csrf,settings):
    with Session(engine) as session,session.begin():
        encounter,call,member,credential=authorized_lock(session,visit_id,token,csrf)
        if not configured(settings):raise DomainError(503,'The call service is not configured.')
        if not call:
            call=CallRecord(encounter_id=visit_id,generation=uuid4(),revision=0,manual_pause=True,
                            output_silenced=False,ended=False,stopped_epoch=0,active_tasks=0)
            session.add(call);session.flush()
        if call.ended:
            if member.role!='patient':raise DomainError(409,'Ask the patient to reopen this conversation first.')
            call.generation=uuid4();call.ended=False;call.worker_seen_at=None;call.worker_error=None
        elif call.worker_error=='media_unavailable' and not any(c.present and c.session_hash!=credential.token_hash and valid_connection(session,c) for c in connections(session,call)):
            # Retry an empty/own failed room. An assistant handshake failure
            # must not replace the healthy human room when another guest joins.
            # Retired SDK sockets cannot hold up admission to the recovered server.
            call.generation=uuid4();call.worker_error=None;call.worker_seen_at=None
            call.active_tasks=0;call.stopped_epoch=0
        # One current admission per browser session. Reconnect gets a fresh identity and consent.
        for previous in connections(session,call):
            if previous.session_hash==credential.token_hash:
                previous.retired=True;previous.present=False
        call.manual_pause=True
        expires=utc_now()+timedelta(minutes=2)
        connection=CallConnectionRecord(id=uuid4(),encounter_id=visit_id,generation=call.generation,
            membership_id=member.id,session_hash=credential.token_hash,present=False,consent='pending',
            track_epoch=0,expires_at=credential.expires_at,retired=False)
        session.add(connection);session.flush();bump(encounter,call)
        jwt=api.AccessToken(settings.livekit_api_key,settings.livekit_api_secret).with_identity(identity(connection))\
            .with_name(member.name).with_ttl(timedelta(minutes=2)).with_grants(api.VideoGrants(
                room_join=True,room=room_name(call),can_publish=False,can_subscribe=True,can_publish_data=False,
                can_publish_sources=[],can_update_own_metadata=False)).to_jwt()
        return CallAdmission(connection_id=connection.id,token=jwt,server_url=settings.livekit_url,
            expires_at=expires,call=view(session,encounter,call,settings,member,credential))


def audit(session,call,member,request):
    payload=request.model_dump(mode='json')
    fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    prior=session.scalar(select(CallEventRecord).where(CallEventRecord.encounter_id==call.encounter_id,
                                                     CallEventRecord.command_id==request.command_id))
    if prior:
        if prior.actor_id!=member.id or prior.request_hash!=fingerprint:
            raise DomainError(409,'This command ID was already used for a different request.')
        return False
    session.add(CallEventRecord(id=uuid4(),encounter_id=call.encounter_id,command_id=request.command_id,
        actor_id=member.id,request_hash=fingerprint,content=payload,accepted_at=utc_now()))
    return True


def verify_admission(engine,visit_id,token,csrf,connection_id,settings):
    """Verify real room presence independently of the assistant's RTC worker.

    The encounter lock fences revocation through the bounded administrative RPC.
    A media permission grant never grants processing consent or worker readiness.
    """
    with Session(engine) as session,session.begin():
        encounter,call,member,credential=authorized_lock(session,visit_id,token,csrf)
        connection=session.get(CallConnectionRecord,connection_id)
        if not configured(settings):raise DomainError(503,'The call service is unavailable.')
        if not call or call.ended or not connection or connection.encounter_id!=visit_id or connection.generation!=call.generation or connection.session_hash!=credential.token_hash or not valid_connection(session,connection):
            raise DomainError(404,'Your current call admission is required.')
        async def grant():
            async with api.LiveKitAPI(settings.livekit_url,settings.livekit_api_key,settings.livekit_api_secret,
                timeout=aiohttp.ClientTimeout(total=3),failover=False) as control:
                participant=await control.room.get_participant(api.RoomParticipantIdentity(room=room_name(call),identity=identity(connection)))
                if participant.identity!=identity(connection):raise DomainError(404,'Your participant is not in this conversation.')
                if not valid_connection(session,connection):raise DomainError(401,'Your admission expired.')
                await control.room.update_participant(api.UpdateParticipantRequest(room=room_name(call),identity=identity(connection),
                    permission=api.ParticipantPermission(can_publish=True,can_subscribe=True,can_publish_data=False,
                        can_publish_sources=[api.TrackSource.MICROPHONE],can_update_metadata=False)))
        try:asyncio.run(asyncio.wait_for(grant(),timeout=3))
        except DomainError:raise
        except Exception:raise DomainError(503,'Call admission could not be verified. Retry joining.') from None
        if not connection.present:
            connection.present=True;connection.consent='pending';call.manual_pause=True;bump(encounter,call)
        session.flush()
        return view(session,encounter,call,settings,member,credential)


def consent(engine,visit_id,token,csrf,request,settings):
    with Session(engine) as session,session.begin():
        encounter,call,member,credential=authorized_lock(session,visit_id,token,csrf)
        connection=session.get(CallConnectionRecord,request.connection_id)
        if not call or not connection or connection.encounter_id!=visit_id or connection.generation!=call.generation\
            or connection.session_hash!=credential.token_hash or not valid_connection(session,connection):
            raise DomainError(404,'Call connection not found.')
        if audit(session,call,member,request):
            connection.consent=request.decision;connection.terms_version=request.terms_version
            call.manual_pause=True;bump(encounter,call)
        return view(session,encounter,call,settings,member,credential)


def control(engine,visit_id,token,csrf,request,settings):
    with Session(engine) as session,session.begin():
        encounter,call,member,credential=authorized_lock(session,visit_id,token,csrf)
        if not call:raise DomainError(404,'Call not found.')
        if request.type!='pause' and member.role!='patient':raise DomainError(403,'Only the patient can resume, end or change Vene output.')
        if not audit(session,call,member,request):return view(session,encounter,call,settings,member,credential)
        if request.expected_revision!=call.revision:raise DomainError(409,'The call changed. Try again with the current state.')
        if request.type=='resume':
            humans=[c for c in connections(session,call) if c.present]
            if call.ended or not humans or not all(valid_connection(session,c) and c.consent=='agreed' for c in humans):
                raise DomainError(409,'Everyone in the room needs to agree before Vene can process audio.')
            if provider(settings)=='unavailable' or call.worker_error or not call.worker_seen_at or (utc_now()-call.worker_seen_at).total_seconds()>3:
                raise DomainError(503,'Voice processing is unavailable. The human conversation can continue.')
            call.manual_pause=False
        elif request.type=='pause':call.manual_pause=True
        elif request.type=='silence':
            if request.silenced is None:raise DomainError(422,'Specify whether Vene output is silenced.')
            call.output_silenced=request.silenced
        elif request.type=='end':call.ended=True;call.manual_pause=True
        bump(encounter,call)
        return view(session,encounter,call,settings,member,credential)


def leave(engine,visit_id,token,csrf,connection_id,settings):
    with Session(engine) as session,session.begin():
        encounter,call,member,credential=authorized_lock(session,visit_id,token,csrf)
        row=session.get(CallConnectionRecord,connection_id)
        if not call or not row or row.encounter_id!=visit_id or row.session_hash!=credential.token_hash:
            raise DomainError(404,'Call connection not found.')
        if not row.retired:
            row.retired=True;row.present=False;call.manual_pause=True;bump(encounter,call)
        return view(session,encounter,call,settings,member,credential)


def sync_room(engine,visit_id,generation,identities,tracks,active_tasks,stopped=False):
    """Only the owned RTC supervisor calls this; browser metadata cannot grant presence."""
    with Session(engine) as session,session.begin():
        encounter,call=lock_media_snapshot(session,visit_id)
        if not call or call.generation!=generation or call.ended:return None
        changed=False
        for row in connections(session,call):
            present=identity(row) in identities and valid_connection(session,row)
            if row.present!=present:
                row.present=present;row.consent='pending';changed=True
            sid=tracks.get(identity(row))
            if sid and sid!=row.track_sid:
                row.track_sid=sid;row.track_epoch+=1;row.consent='pending';changed=True
        if changed:call.manual_pause=True;bump(encounter,call)
        now=utc_now()
        if not call.worker_seen_at or (now-call.worker_seen_at).total_seconds()>=.75:call.worker_seen_at=now
        call.active_tasks=active_tasks
        if stopped:call.stopped_epoch=epoch(encounter)
        if not changed and not stopped:
            # Heartbeat/task-count diagnostics may lose recent updates on a
            # hard crash. Presence, track, consent and stop acknowledgments may not.
            session.execute(text('SET LOCAL synchronous_commit=off'))
        session.flush()
        return {'allowed':gate(session,encounter,call), 'epoch':epoch(encounter), 'generation':call.generation,
            'connections':{identity(c):(c.id,c.track_sid,c.track_epoch) for c in connections(session,call) if c.present and valid_connection(session,c)}}


def permit(session,visit_id,generation,connection_id,track_sid,track_epoch,consent_epoch):
    encounter,call=lock_media_snapshot(session,visit_id)
    row=session.get(CallConnectionRecord,connection_id)
    return bool(call and call.generation==generation and epoch(encounter)==consent_epoch and row and
        row.encounter_id==visit_id and row.generation==generation and row.present and valid_connection(session,row) and
        row.track_sid==track_sid and row.track_epoch==track_epoch and gate(session,encounter,call))


def accept_frame(engine,visit_id,generation,connection_id,track_sid,track_epoch,consent_epoch,samples,non_silent,activity=None):
    activity=[non_silent] if activity is None else activity
    if not 1<=len(activity)<=5:raise ValueError('Invalid audio activity batch')
    with Session(engine) as session,session.begin():
        # Counters, current activity and stop-detection timing are transient;
        # transcripts, permission changes and playout receipts stay durable.
        session.execute(text('SET LOCAL synchronous_commit=off'))
        if not permit(session,visit_id,generation,connection_id,track_sid,track_epoch,consent_epoch):return False
        receipt=session.scalar(select(AudioReceiptRecord).where(AudioReceiptRecord.connection_id==connection_id,
            AudioReceiptRecord.track_epoch==track_epoch,AudioReceiptRecord.consent_epoch==consent_epoch).with_for_update())
        now=utc_now()
        if not receipt:
            receipt=AudioReceiptRecord(id=uuid4(),connection_id=connection_id,track_sid=track_sid,track_epoch=track_epoch,
                consent_epoch=consent_epoch,frames=0,samples=0,non_silent_frames=0,first_received_at=now,last_received_at=now)
            session.add(receipt)
        receipt.frames+=len(activity);receipt.samples+=samples;receipt.non_silent_frames+=sum(activity);receipt.last_received_at=now
        from bring_vene.speech.service import observe_audio
        for active in activity:observe_audio(session,visit_id,connection_id,active)
        return True


def finalize(engine,visit_id,generation,connection_id,track_sid,track_epoch,consent_epoch,text,settings=None):
    with Session(engine) as session,session.begin():
        if not permit(session,visit_id,generation,connection_id,track_sid,track_epoch,consent_epoch):return False
        row=session.get(CallConnectionRecord,connection_id)
        utterance=Utterance(id=uuid4(),connection_id=row.id,membership_id=row.membership_id,track_epoch=track_epoch,
            consent_epoch=consent_epoch,text=text[:12000],finalized_at=utc_now(),provider='deepgram')
        session.add(UtteranceRecord(id=utterance.id,connection_id=row.id,content=utterance.model_dump(mode='json')))
        session.flush()
        from bring_vene.understanding.service import ingest_voice
        from bring_vene.config import Settings
        ingest_voice(session,visit_id,utterance,settings or Settings())
        return True


def diagnostics(engine,visit_id,token):
    with Session(engine) as session:
        member,_=authenticate(session,token,visit_id)
        if member.role!='patient':raise DomainError(403,'Only the patient can inspect processing evidence.')
        call=session.get(CallRecord,visit_id)
        rows=session.scalars(select(AudioReceiptRecord).join(CallConnectionRecord).where(CallConnectionRecord.encounter_id==visit_id)
                             .order_by(AudioReceiptRecord.last_received_at.desc()).limit(100)).all()
        return CallDiagnostics(active_tasks=call.active_tasks if call else 0,stopped_epoch=call.stopped_epoch if call else 0,
            receipts=[AudioReceipt(**{name:getattr(row,name) for name in AudioReceipt.model_fields}) for row in rows])


def utterances(engine,visit_id,token):
    with Session(engine) as session:
        member,_=authenticate(session,token,visit_id)
        if member.role!='patient':raise DomainError(403,'Transcripts have not been shared with this role.')
        rows=session.scalars(select(UtteranceRecord).join(CallConnectionRecord).where(CallConnectionRecord.encounter_id==visit_id).limit(100)).all()
        return [Utterance.model_validate(row.content) for row in rows]


def worker_failed(engine,visit_id,generation,code='media_unavailable'):
    with Session(engine) as session,session.begin():
        encounter,call=lock(session,visit_id)
        if call and call.generation==generation and not call.ended:
            if not call.manual_pause:call.gap_since=call.gap_since or utc_now()
            call.worker_error=code;call.manual_pause=True;bump(encounter,call)


def worker_started(engine,visit_id,generation,instance):
    with Session(engine) as session,session.begin():
        encounter,call=lock(session,visit_id)
        if not call or call.generation!=generation or call.ended:return
        if call.worker_instance and call.worker_instance!=instance and call.worker_seen_at:
            call.gap_since=call.gap_since or call.worker_seen_at
            call.manual_pause=True;bump(encounter,call)
        call.worker_instance=instance;call.worker_seen_at=utc_now()


def worker_recovered(engine,visit_id,generation):
    with Session(engine) as session,session.begin():
        encounter,call=lock(session,visit_id)
        if call and call.generation==generation and not call.ended and call.worker_error=='media_unavailable':
            call.worker_error=None;call.manual_pause=True;bump(encounter,call)
