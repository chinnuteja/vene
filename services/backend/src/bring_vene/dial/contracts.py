from uuid import UUID
from pydantic import AwareDatetime, Field
from bring_vene.domain.contracts import Contract


class PinRequest(Contract):
    membership_id: UUID


class PinIssued(Contract):
    pin: str
    expires_at: AwareDatetime
    dial_number: str | None = None
    name: str


class BridgeAdmit(Contract):
    pin: str = Field(pattern=r'^\d{6}$')
    participant_identity: str = Field(min_length=3, max_length=80)
    # Accepted so a bridge can forward what it has, then ignored: caller ID is never identity.
    caller_number: str | None = Field(default=None, max_length=40)


class BridgeAdmitted(Contract):
    connection_id: UUID
    room: str
    name: str
    announcement: str
    prompt: str


class KeypadResult(Contract):
    accepted: bool
    spoken: str
