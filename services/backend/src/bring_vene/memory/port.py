"""What Vene remembers between visits, behind one interface.

The Postgres implementation reads this prototype's own records. The same interface could be
implemented over Vene's existing memory service; callers depend only on this port.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class Source:
    id: UUID
    encounter_id: UUID
    title: str
    text: str
    observed_at: datetime
    source_type: str


@dataclass(frozen=True)
class OpenLoop:
    key: str            # stable identity, e.g. 'plan:<id>', 'priority:<id>', 'evidence:<id>', 'action:<id>'
    rule: str           # which deterministic rule found it
    question: str       # proposed agenda wording (template, never model-generated)
    detail: str
    since: datetime     # when the loop opened; age is measured from here
    sources: list[Source] = field(default_factory=list)


@dataclass(frozen=True)
class PastVisit:
    id: UUID
    title: str
    visit_at: datetime


class MemoryPort(Protocol):
    def open_loops(self, session, patient_id: UUID, as_of: datetime) -> list[OpenLoop]: ...
    def history(self, session, patient_id: UUID, before: datetime) -> list[PastVisit]: ...
    def record_outcome(self, session, patient_id: UUID, key: str, outcome: str, encounter_id: UUID) -> None: ...
