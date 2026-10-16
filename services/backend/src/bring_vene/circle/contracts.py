from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime
from bring_vene.domain.contracts import Contract


class RideAsk(Contract):
    action_id: UUID
    recipient_id: UUID


class RideAnswer(Contract):
    answer: Literal['yes', 'no']


class RideView(Contract):
    id: UUID
    action_id: UUID
    recipient_id: UUID
    recipient_name: str
    # Only the fields the patient chose to send: what it is for, when and where.
    purpose: str
    when: str
    where: str
    # 'unavailable' means the step, its sharing or the confirmed reservation no longer supports the ask.
    state: Literal['asked', 'accepted', 'declined', 'withdrawn', 'unavailable']
    answered_at: AwareDatetime | None = None


class CircleView(Contract):
    rides: list[RideView]
