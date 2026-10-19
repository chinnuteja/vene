import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from bring_vene.domain.contracts import (
    CommandEnvelope, CommandResult, EncounterView, EventEnvelope,
    PrioritySelectionChanged, TitleChanged,
    SharingChanged, SharingBatchChanged, PreparationApproved, PriorityEdited, SuggestionAdded, SuggestionReviewed, Suggestion, Priority,
)
from bring_vene.persistence.models import EncounterRecord, EventRecord, EvidenceRecord


class DomainError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message


def utc_now():
    return datetime.now(timezone.utc)


def read_encounter(engine, encounter_id: UUID) -> EncounterView:
    with Session(engine) as session:
        record = session.get(EncounterRecord, encounter_id)
        if record is None:
            raise DomainError(404, "Visit not found.")
        return EncounterView.model_validate(record.projection)


def apply_command(engine, encounter_id: UUID, request: CommandEnvelope, clock=utc_now, authorize=None):
    fingerprint = hashlib.sha256(
        json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with Session(engine) as session, session.begin():
        record = session.scalar(
            select(EncounterRecord).where(EncounterRecord.id == encounter_id).with_for_update()
        )
        if record is None:
            raise DomainError(404, "Visit not found.")
        member = authorize(session) if authorize else None
        actor_id = member.id if member else None
        role = member.role if member else "patient"
        if role != "patient" and not (role == "family" and isinstance(request.command, SuggestionAdded)):
            raise DomainError(403, "Only the patient can approve or change what is shared.")
        previous = session.scalar(select(EventRecord).where(
            EventRecord.encounter_id == encounter_id,
            EventRecord.command_id == request.command_id,
        ))
        view = EncounterView.model_validate(record.projection)
        if previous:
            if previous.actor_id != actor_id or previous.request_hash != fingerprint:
                raise DomainError(409, "This command ID was already used for a different request.")
            return CommandResult(
                duplicate=True, event=EventEnvelope.model_validate(previous.envelope), encounter=view
            )
        # A family suggestion only appends a proposal and touches nothing the patient owns, so it
        # commutes with any concurrent change; fencing it would reject it for edits the guest may not see.
        if request.expected_version != record.version and not isinstance(request.command, SuggestionAdded):
            raise DomainError(409, "The visit changed. Refresh it before editing.")
        if request.evidence_refs:
            if role != "patient":
                raise DomainError(403, "Suggestions cannot attach private evidence.")
            found = set(session.scalars(select(EvidenceRecord.id).where(
                EvidenceRecord.encounter_id == encounter_id,
                EvidenceRecord.id.in_(request.evidence_refs),
            )).all())
            if found != set(request.evidence_refs):
                raise DomainError(422, "Evidence must belong to this visit.")
        command = request.command
        if isinstance(command, TitleChanged):
            cleaned = command.title.strip()
            if len(cleaned) < 3:
                raise DomainError(422, "The visit title must contain at least three characters.")
            view.title = cleaned
        elif isinstance(command, PrioritySelectionChanged):
            priority = next((p for p in view.priorities if p.id == command.priority_id), None)
            if priority is None:
                raise DomainError(404, "Priority not found.")
            priority.selected = command.selected
            priority.approved = False
            view.preparation_approved = False
        elif isinstance(command, SharingChanged):
            item = next((p for p in [*view.priorities, *view.plan, *view.evidence] if p.id == command.item_id), None)
            if item is None:
                raise DomainError(404, "Item not found.")
            item.audiences = sorted(set(command.audiences))
            if isinstance(item, Priority) and item.answer_refs:
                item.answer_audiences = sorted(set(command.audiences))
        elif isinstance(command,SharingBatchChanged):
            ids=[change.item_id for change in command.changes]
            if len(ids)!=len(set(ids)):raise DomainError(422,'Review each sharing choice once.')
            items={item.id:item for item in [*view.priorities,*view.plan,*view.evidence]}
            if any(item_id not in items for item_id in ids):raise DomainError(404,'Item not found.')
            for change in command.changes:
                item=items[change.item_id];item.audiences=sorted(set(change.audiences))
                if isinstance(item,Priority) and item.answer_refs:item.answer_audiences=list(item.audiences)
        elif isinstance(command, PreparationApproved):
            view.preparation_approved = command.approved
            for priority in view.priorities:
                priority.approved = command.approved and priority.selected
        elif isinstance(command, PriorityEdited):
            priority = next((p for p in view.priorities if p.id == command.priority_id), None)
            if not priority:
                raise DomainError(404, "Priority not found.")
            if len(command.title.strip()) < 3 or len(command.detail.strip()) < 3:
                raise DomainError(422, "Please enter a question and a little context.")
            priority.title, priority.detail = command.title.strip(), command.detail.strip()
            priority.status = 'open'
            priority.answer_detail = None
            priority.answer_refs = []
            priority.answer_audiences = []
            priority.approved = False
            view.preparation_approved = False
        elif isinstance(command, SuggestionAdded):
            if role != "family":
                raise DomainError(403, "Only family members can suggest a question here.")
            if len(command.title.strip()) < 3 or len(command.detail.strip()) < 3:
                raise DomainError(422, "Please enter a question and a little context.")
            if len(view.suggestions) >= 100:
                raise DomainError(409, "This visit has reached its suggestion limit.")
            view.suggestions.append(Suggestion(id=uuid4(), author_id=member.id, author_name=member.name,
                                              title=command.title.strip(), detail=command.detail.strip()))
        elif isinstance(command, SuggestionReviewed):
            suggestion = next((s for s in view.suggestions if s.id == command.suggestion_id), None)
            if not suggestion:
                raise DomainError(404, "Suggestion not found.")
            if suggestion.status != "pending":
                raise DomainError(409, "This suggestion has already been reviewed.")
            suggestion.status = command.decision
            if command.decision == "accepted":
                # Acceptance creates a private draft; it does not silently grant sharing.
                view.priorities.append(Priority(id=uuid4(), title=suggestion.title, detail=suggestion.detail,
                                                selected=True, evidence_refs=[]))
                view.preparation_approved = False
        now = clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("The clock must return a timezone-aware datetime.")
        view.version += 1
        view.updated_at = now
        view.consent_epoch += 1
        event = EventEnvelope(
            id=uuid4(), encounter_id=encounter_id, sequence=view.version,
            command_id=request.command_id, accepted_at=now,
            evidence_refs=request.evidence_refs, command=command,
        )
        record.projection = view.model_dump(mode="json")
        record.version = view.version
        record.updated_at = now
        session.add(EventRecord(
            id=event.id, encounter_id=encounter_id, sequence=event.sequence,
            command_id=request.command_id, request_hash=fingerprint,
            envelope=event.model_dump(mode="json"), accepted_at=now,
            actor_id=actor_id,
        ))
        return CommandResult(duplicate=False, event=event, encounter=view)

