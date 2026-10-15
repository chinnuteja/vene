from typing import Literal
from uuid import UUID
from pydantic import Field, StrictBool, StrictInt
from bring_vene.domain.contracts import Contract


class Citation(Contract):
    source_id: UUID
    version: int = Field(ge=1)
    quote: str = Field(min_length=3, max_length=1200)


class ProposedAnswer(Contract):
    priority_id: UUID
    status: Literal['open','partly_answered','answered','deferred']
    explanation: str = Field(min_length=3,max_length=600)
    citations: list[Citation] = Field(max_length=8)


class ProposedStep(Contract):
    topic: Literal['lab','referral','other']
    title: str = Field(min_length=3,max_length=160)
    detail: str = Field(min_length=3,max_length=1200)
    owner: str | None
    timeframe: str | None
    location: str | None
    dependencies: list[str] = Field(max_length=8)
    needs_clarification: StrictBool
    explanation: str = Field(min_length=3,max_length=600)
    citations: list[Citation] = Field(max_length=8)


class Extraction(Contract):
    answers: list[ProposedAnswer] = Field(max_length=20)
    steps: list[ProposedStep] = Field(max_length=20)


class Mutation(Contract):
    command_id: UUID


class ProcessingRequest(Mutation):
    enabled: StrictBool


class FixtureTurn(Mutation):
    speaker: Literal['patient','clinician','family']
    text: str = Field(min_length=3,max_length=2000)


class SourceCorrection(Mutation):
    expected_source_version: StrictInt = Field(ge=1)
    text: str = Field(min_length=3,max_length=2000)


class PlanCorrection(Mutation):
    expected_item_revision: StrictInt = Field(ge=1)
    detail: str = Field(min_length=3,max_length=1200)
    owner: str | None = Field(max_length=100)
    timeframe: str | None = Field(max_length=200)
    location: str | None = Field(max_length=200)
