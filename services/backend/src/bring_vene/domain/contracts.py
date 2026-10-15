from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, StrictInt


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


Role = Literal["patient", "clinician", "family"]
Audience = Literal["clinician", "family"]


class Sharing(Contract):
    audiences: list[Audience] = Field(default_factory=list, max_length=2)


class Patient(Contract):
    id: UUID
    name: str
    preferred_name: str
    age: int = Field(ge=18, le=120)


class Evidence(Sharing):
    id: UUID
    source_type: Literal["patient_report", "office_message", "imported_record", "conversation"]
    title: str
    text: str
    observed_at: AwareDatetime
    version: int = 1
    speaker: str | None = None
    origin: Literal["fixture", "deepgram", "human"] | None = None


class Priority(Sharing):
    id: UUID
    title: str
    detail: str
    selected: StrictBool
    status: Literal["open", "partly_answered", "answered", "deferred"] = "open"
    evidence_refs: list[UUID]
    approved: bool = False
    answer_detail: str | None = None
    answer_refs: list[UUID] = Field(default_factory=list)
    answer_audiences: list[Audience] = Field(default_factory=list)


class PlanItem(Sharing):
    id: UUID
    title: str
    detail: str
    owner: str | None = None
    timeframe: str | None = None
    status: Literal["draft", "waiting", "confirmed"] = "draft"
    evidence_refs: list[UUID]
    clinician_confirmed: bool = False
    patient_authorized: bool = False
    order_available: bool = False
    external_completed: bool = False
    origin: Literal["preparation", "interpretation", "human"] = "preparation"
    location: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    needs_clarification: bool = True
    explanation: str = ""
    revision: int = 1


class UnderstandingStatus(Contract):
    enabled: bool = False
    state: Literal["off", "queued", "processing", "ready", "unavailable", "paused"] = "off"
    revision: int = 0
    processed_revision: int = 0
    provider: Literal["fixture", "openai", "deepseek", "unavailable"] = "fixture"
    model: str = "original-scenarios-v1"
    prompt_version: str = "visit-extraction-v4"
    message: str = ""
    fixture_input_enabled: bool = False


class Suggestion(Contract):
    id: UUID
    author_id: UUID
    author_name: str
    title: str
    detail: str
    status: Literal["pending", "accepted", "rejected"] = "pending"


class EncounterView(Contract):
    id: UUID
    version: int = Field(ge=0)
    patient: Patient
    title: str
    clinician: str
    visit_at: AwareDatetime
    processing_state: Literal["preparing", "active", "paused", "ended"]
    priorities: list[Priority]
    plan: list[PlanItem]
    evidence: list[Evidence]
    updated_at: AwareDatetime
    synthetic: Literal[True] = True
    consent_epoch: int = 0
    preparation_approved: bool = False
    suggestions: list[Suggestion] = Field(default_factory=list)
    viewer_role: Role = "patient"
    understanding: UnderstandingStatus | None = None


class EncounterSummary(Contract):
    id: UUID
    title: str
    patient_name: str
    version: int


class TitleChanged(Contract):
    type: Literal["encounter.title_changed"]
    title: str = Field(min_length=3, max_length=160)


class PrioritySelectionChanged(Contract):
    type: Literal["priority.selection_changed"]
    priority_id: UUID
    selected: StrictBool


class SharingChanged(Contract):
    type: Literal["sharing.changed"]
    item_id: UUID
    audiences: list[Audience] = Field(max_length=2)


class PreparationApproved(Contract):
    type: Literal["preparation.approved"]
    approved: StrictBool


class PriorityEdited(Contract):
    type: Literal["priority.edited"]
    priority_id: UUID
    title: str = Field(min_length=3, max_length=160)
    detail: str = Field(min_length=3, max_length=1200)


class SuggestionAdded(Contract):
    type: Literal["suggestion.added"]
    title: str = Field(min_length=3, max_length=160)
    detail: str = Field(min_length=3, max_length=1200)


class SuggestionReviewed(Contract):
    type: Literal["suggestion.reviewed"]
    suggestion_id: UUID
    decision: Literal["accepted", "rejected"]


Command = Annotated[TitleChanged | PrioritySelectionChanged | SharingChanged | PreparationApproved |
                    PriorityEdited | SuggestionAdded | SuggestionReviewed, Field(discriminator="type")]


class CommandEnvelope(Contract):
    command_id: UUID
    expected_version: Annotated[StrictInt, Field(ge=0)]
    evidence_refs: list[UUID] = Field(default_factory=list, max_length=20)
    command: Command


class EventEnvelope(Contract):
    id: UUID
    encounter_id: UUID
    sequence: int = Field(ge=1)
    command_id: UUID
    accepted_at: AwareDatetime
    evidence_refs: list[UUID]
    command: Command


class CommandResult(Contract):
    duplicate: bool
    event: EventEnvelope
    encounter: EncounterView


class Health(Contract):
    status: Literal["alive", "ready", "unavailable"]
    database: Literal["ready", "unavailable"] | None = None


class Identity(Contract):
    membership_id: UUID
    encounter_id: UUID
    role: Role
    name: str
    csrf_token: str


class InviteRequest(Contract):
    membership_id: UUID


class Invitation(Contract):
    id: UUID
    token: str
    expires_at: AwareDatetime


class RedeemRequest(Contract):
    token: str = Field(min_length=30, max_length=128)


class FixtureLaunch(Contract):
    persona: Role
    case: Literal['maria','james','asha']='maria'


class MemberView(Contract):
    id: UUID
    role: Role
    name: str
    revoked: bool


class ContextView(Contract):
    encounter_id: UUID
    consent_epoch: int
    audience: Role
    priorities: list[Priority]
    plan: list[PlanItem]
    evidence: list[Evidence]

