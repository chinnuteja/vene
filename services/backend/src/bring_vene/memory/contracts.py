from typing import Literal
from pydantic import AwareDatetime, Field
from bring_vene.domain.contracts import Contract


class LoopSource(Contract):
    title: str
    text: str
    observed_at: AwareDatetime
    from_visit: str


class LoopView(Contract):
    key: str
    rule: Literal['unfinished_step', 'unanswered_question', 'office_waiting', 'unknown_completion']
    question: str
    detail: str
    days: int
    age: str
    sources: list[LoopSource]


class MemoryView(Contract):
    loops: list[LoopView]
    already_listed: int = 0
    past_visits: int = 0


class CarryRequest(Contract):
    keys: list[str] = Field(min_length=1, max_length=8)


class OutcomeRequest(Contract):
    key: str = Field(min_length=3, max_length=80)
    outcome: Literal['done', 'not_relevant']
