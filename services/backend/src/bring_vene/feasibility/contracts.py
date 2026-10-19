from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime, Field
from bring_vene.domain.contracts import Contract

# What the patient lets Vene look up during the visit. Read-only; every write still needs its own approval.
StandingKind = Literal['scheduling', 'coverage', 'pharmacy']
ObstacleKind = Literal['no_slot_in_window', 'prior_authorization_required', 'not_on_formulary', 'not_in_stock',
                       'missing_supporting_document']
Choice = Literal['office_will_submit', 'review_later', 'review_coverage', 'use_another_window', 'choose_another_pharmacy',
                 'office_will_send']


class StandingRequest(Contract):
    kinds: list[StandingKind] = Field(max_length=3)


class ResolveRequest(Contract):
    choice: Choice


class ChoiceView(Contract):
    id: Choice
    label: str


class Resolution(Contract):
    choice: Choice
    label: str
    by_role: Literal['patient', 'clinician']
    by_name: str
    at: AwareDatetime


class ObstacleView(Contract):
    id: UUID
    item_id: UUID
    item_title: str
    kind: ObstacleKind
    state: Literal['open', 'resolved']
    fact: str
    source: str
    checked_at: AwareDatetime
    resolver: Literal['patient', 'clinician']
    # Plan-listed facts only. Vene never recommends one; the clinician decides.
    plan_alternatives: list[str] = Field(default_factory=list)
    choices: list[ChoiceView] = Field(default_factory=list)
    resolution: Resolution | None = None
    alternative: dict | None = None
    supporting_sources: list[UUID] = Field(default_factory=list)
    expires_at: AwareDatetime | None = None


class StandingView(Contract):
    kinds: list[StandingKind]
    active: bool


class FeasibilityView(Contract):
    standing: StandingView | None = None
    checking: int = 0
    failed: int = 0
    obstacles: list[ObstacleView]
