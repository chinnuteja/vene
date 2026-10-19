from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ExecutionScopeRecord(Base):
    __tablename__ = 'execution_scopes'
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'), primary_key=True)
    item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    session_hash: Mapped[str] = mapped_column(String(64))
    revision: Mapped[int] = mapped_column(Integer)
    allowed: Mapped[bool] = mapped_column(Boolean)


class ExecutionRecord(Base):
    __tablename__ = 'executions'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'), index=True)
    item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    state: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ExecutionOutboxRecord(Base):
    __tablename__ = 'execution_outbox'
    action_id: Mapped[UUID] = mapped_column(ForeignKey('executions.id', ondelete='CASCADE'), primary_key=True)
    lease_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    attempts: Mapped[int] = mapped_column(Integer)


class OfficeStateRecord(Base):
    # Independent sandbox service storage: deliberately no patient/visit FK.
    __tablename__ = 'sandbox_office_state'
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    content: Mapped[dict] = mapped_column(JSONB)


class OfficeRequestRecord(Base):
    __tablename__ = 'sandbox_office_requests'
    request_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    content: Mapped[dict] = mapped_column(JSONB)


class EncounterRecord(Base):
    __tablename__ = "encounters"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    projection: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvidenceRecord(Base):
    __tablename__ = "evidence"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(
        ForeignKey("encounters.id", ondelete="CASCADE"), index=True, nullable=False
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)


class EventRecord(Base):
    __tablename__ = "encounter_events"
    __table_args__ = (
        UniqueConstraint("encounter_id", "sequence", name="uq_event_sequence"),
        UniqueConstraint("encounter_id", "command_id", name="uq_event_command"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(
        ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    command_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    envelope: Mapped[dict] = mapped_column(JSONB, nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)


class MembershipRecord(Base):
    __tablename__ = "memberships"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey("encounters.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(100))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class InvitationRecord(Base):
    __tablename__ = "invitations"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    membership_id: Mapped[UUID] = mapped_column(ForeignKey("memberships.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SessionRecord(Base):
    __tablename__ = "participant_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    membership_id: Mapped[UUID] = mapped_column(ForeignKey("memberships.id", ondelete="CASCADE"), index=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CallRecord(Base):
    __tablename__ = 'calls'
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'), primary_key=True)
    generation: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    revision: Mapped[int] = mapped_column(Integer, default=0)
    manual_pause: Mapped[bool] = mapped_column(Boolean, default=True)
    output_silenced: Mapped[bool] = mapped_column(Boolean, default=False)
    ended: Mapped[bool] = mapped_column(Boolean, default=False)
    worker_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_epoch: Mapped[int] = mapped_column(Integer, default=0)
    active_tasks: Mapped[int] = mapped_column(Integer, default=0)
    worker_error: Mapped[str | None] = mapped_column(String(32))
    gap_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_instance: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))


class OfficeCallbackOutboxRecord(Base):
    __tablename__ = 'sandbox_callback_outbox'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    request_id: Mapped[UUID] = mapped_column(ForeignKey('sandbox_office_requests.request_id', ondelete='CASCADE'),index=True)
    content: Mapped[dict] = mapped_column(JSONB)
    lease_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),index=True)
    attempts: Mapped[int] = mapped_column(Integer)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OfficeFamilyReceiptRecord(Base):
    __tablename__ = 'sandbox_family_receipts'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    content: Mapped[dict] = mapped_column(JSONB)


class CallbackNonceRecord(Base):
    __tablename__ = 'callback_nonces'
    nonce: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),index=True)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),index=True)


class OfficeCallbackRecord(Base):
    __tablename__ = 'office_callbacks'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),index=True)
    action_id: Mapped[UUID] = mapped_column(ForeignKey('executions.id',ondelete='CASCADE'),index=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DocumentRecord(Base):
    __tablename__ = 'after_visit_documents'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),index=True)
    evidence_id: Mapped[UUID] = mapped_column(ForeignKey('evidence.id',ondelete='CASCADE'),unique=True)
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FamilyUpdateRecord(Base):
    __tablename__ = 'family_updates'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),index=True)
    recipient_id: Mapped[UUID] = mapped_column(ForeignKey('memberships.id',ondelete='CASCADE'),index=True)
    session_hash: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(24),index=True)
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FamilyOutboxRecord(Base):
    __tablename__ = 'family_outbox'
    update_id: Mapped[UUID] = mapped_column(ForeignKey('family_updates.id',ondelete='CASCADE'),primary_key=True)
    lease_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),index=True)
    attempts: Mapped[int] = mapped_column(Integer)


class NextVisitRecord(Base):
    __tablename__ = 'next_visits'
    origin_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),primary_key=True)
    next_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),primary_key=True)
    content: Mapped[dict] = mapped_column(JSONB)


class OperationTraceRecord(Base):
    __tablename__ = 'operation_traces'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),index=True)
    event: Mapped[str] = mapped_column(String(40))
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),index=True)


class DeletionAuditRecord(Base):
    __tablename__ = 'deletion_audit'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    visit_count: Mapped[int] = mapped_column(Integer)
    # Deliberately no patient, encounter, request, text, or reversible identifier.


class CallConnectionRecord(Base):
    __tablename__ = 'call_connections'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('calls.encounter_id', ondelete='CASCADE'), index=True)
    generation: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    membership_id: Mapped[UUID] = mapped_column(ForeignKey('memberships.id', ondelete='CASCADE'), index=True)
    session_hash: Mapped[str] = mapped_column(ForeignKey('participant_sessions.token_hash', ondelete='CASCADE'), index=True)
    present: Mapped[bool] = mapped_column(Boolean, default=False)
    consent: Mapped[str] = mapped_column(String(16), default='pending')
    terms_version: Mapped[str | None] = mapped_column(String(32))
    track_epoch: Mapped[int] = mapped_column(Integer, default=0)
    track_sid: Mapped[str | None] = mapped_column(String(100))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    retired: Mapped[bool] = mapped_column(Boolean, default=False)


class AudioReceiptRecord(Base):
    __tablename__ = 'audio_receipts'
    __table_args__ = (UniqueConstraint('connection_id','track_epoch','consent_epoch',name='uq_audio_receipt_epoch'),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    connection_id: Mapped[UUID] = mapped_column(ForeignKey('call_connections.id', ondelete='CASCADE'), index=True)
    track_sid: Mapped[str] = mapped_column(String(100))
    track_epoch: Mapped[int] = mapped_column(Integer)
    consent_epoch: Mapped[int] = mapped_column(Integer)
    frames: Mapped[int] = mapped_column(Integer)
    samples: Mapped[int] = mapped_column(Integer)
    non_silent_frames: Mapped[int] = mapped_column(Integer)
    first_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UtteranceRecord(Base):
    __tablename__ = 'utterances'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    connection_id: Mapped[UUID] = mapped_column(ForeignKey('call_connections.id', ondelete='CASCADE'), index=True)
    content: Mapped[dict] = mapped_column(JSONB)


class CallEventRecord(Base):
    __tablename__ = 'call_events'
    __table_args__ = (UniqueConstraint('encounter_id','command_id',name='uq_call_command'),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('calls.encounter_id', ondelete='CASCADE'), index=True)
    command_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    actor_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    request_hash: Mapped[str] = mapped_column(String(64))
    content: Mapped[dict] = mapped_column(JSONB)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UnderstandingRecord(Base):
    __tablename__ = 'understanding'
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    session_hash: Mapped[str | None] = mapped_column(ForeignKey('participant_sessions.token_hash', ondelete='CASCADE'))
    revision: Mapped[int] = mapped_column(Integer, default=0)
    processed_revision: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[str] = mapped_column(String(20), default='off')
    message: Mapped[str] = mapped_column(String(300), default='')


class TranscriptSourceRecord(Base):
    __tablename__ = 'transcript_sources'
    id: Mapped[UUID] = mapped_column(ForeignKey('evidence.id', ondelete='CASCADE'), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'), index=True)
    membership_id: Mapped[UUID] = mapped_column(ForeignKey('memberships.id', ondelete='CASCADE'))
    utterance_id: Mapped[UUID | None] = mapped_column(ForeignKey('utterances.id', ondelete='CASCADE'), unique=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[dict] = mapped_column(JSONB)
    history: Mapped[list] = mapped_column(JSONB, default=list)
    finalized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class InterpretationRunRecord(Base):
    __tablename__ = 'interpretation_runs'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[str] = mapped_column(String(100))
    input_snapshot: Mapped[dict] = mapped_column(JSONB)
    output: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UnderstandingMutationRecord(Base):
    __tablename__ = 'understanding_mutations'
    __table_args__ = (UniqueConstraint('encounter_id','command_id',name='uq_understanding_command'),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'), index=True)
    command_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    actor_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    request_hash: Mapped[str] = mapped_column(String(64))
    content: Mapped[dict] = mapped_column(JSONB)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SpeechStateRecord(Base):
    __tablename__ = 'speech_state'
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),primary_key=True)
    mode: Mapped[str] = mapped_column(String(20),default='private')
    mode_revision: Mapped[int] = mapped_column(Integer,default=0)
    revision: Mapped[int] = mapped_column(Integer,default=0)
    session_hash: Mapped[str | None] = mapped_column(ForeignKey('participant_sessions.token_hash',ondelete='CASCADE'))
    current_delivery: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    last_human_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_output_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content: Mapped[dict] = mapped_column(JSONB,default=dict)


class SpeechConsentRecord(Base):
    __tablename__ = 'speech_consents'
    connection_id: Mapped[UUID] = mapped_column(ForeignKey('call_connections.id',ondelete='CASCADE'),primary_key=True)
    mode_revision: Mapped[int] = mapped_column(Integer,primary_key=True)
    agreed: Mapped[bool] = mapped_column(Boolean)


class CueRecord(Base):
    __tablename__ = 'speech_cues'
    __table_args__ = (UniqueConstraint('encounter_id','dedup_key','digest',name='uq_cue_context'),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),index=True)
    dedup_key: Mapped[str] = mapped_column(String(100))
    digest: Mapped[str] = mapped_column(String(64))
    score: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(20),index=True)
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SpeechDeliveryRecord(Base):
    __tablename__ = 'speech_deliveries'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),index=True)
    cue_id: Mapped[UUID] = mapped_column(ForeignKey('speech_cues.id',ondelete='CASCADE'))
    generation: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    state: Mapped[str] = mapped_column(String(20),index=True)
    content: Mapped[dict] = mapped_column(JSONB)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    first_audio_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    played_ms: Mapped[int] = mapped_column(Integer,default=0)
    reason: Mapped[str | None] = mapped_column(String(40))


class SpeechMutationRecord(Base):
    __tablename__ = 'speech_mutations'
    __table_args__ = (UniqueConstraint('encounter_id','command_id',name='uq_speech_command'),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id',ondelete='CASCADE'),index=True)
    command_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    actor_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    request_hash: Mapped[str] = mapped_column(String(64))
    content: Mapped[dict] = mapped_column(JSONB)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))



class CareCircleRequestRecord(Base):
    __tablename__ = 'care_circle_requests'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'), index=True)
    action_id: Mapped[UUID] = mapped_column(ForeignKey('executions.id', ondelete='CASCADE'))
    recipient_id: Mapped[UUID] = mapped_column(ForeignKey('memberships.id', ondelete='CASCADE'))
    session_hash: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16))
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StandingCheckRecord(Base):
    __tablename__ = 'standing_checks'
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'), primary_key=True)
    session_hash: Mapped[str] = mapped_column(String(64))
    kinds: Mapped[list] = mapped_column(JSONB)
    revision: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FeasibilityCheckRecord(Base):
    __tablename__ = 'feasibility_checks'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'))
    item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(String(16))
    plan_fingerprint: Mapped[str] = mapped_column(String(64))
    standing_revision: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(16))
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ObstacleRecord(Base):
    __tablename__ = 'obstacles'
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    encounter_id: Mapped[UUID] = mapped_column(ForeignKey('encounters.id', ondelete='CASCADE'))
    item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    check_id: Mapped[UUID] = mapped_column(ForeignKey('feasibility_checks.id', ondelete='CASCADE'))
    kind: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(16))
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MemoryOutcomeRecord(Base):
    __tablename__ = 'memory_outcomes'
    patient_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    loop_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    outcome: Mapped[str] = mapped_column(String(16))
    encounter_id: Mapped[UUID | None] = mapped_column(ForeignKey('encounters.id', ondelete='SET NULL'))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
