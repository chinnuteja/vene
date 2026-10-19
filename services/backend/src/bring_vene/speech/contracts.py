from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime,Field,StrictBool
from bring_vene.domain.contracts import Contract

Mode=Literal['private','on_request','closeout']


class SpeechRequest(Contract):
    command_id: UUID


class ModeRequest(SpeechRequest):
    mode: Mode


class SpeechAgreement(SpeechRequest):
    connection_id: UUID
    mode_revision: int = Field(ge=0)
    agreed: StrictBool


class CueApproval(SpeechRequest):
    cue_id: UUID
    digest: str = Field(min_length=64,max_length=64)


class SpeechAction(SpeechRequest):
    type: Literal['refresh','stop','closeout']


class PrivateCue(Contract):
    id: UUID
    digest: str
    title: str
    suggestion: str
    public_text: str
    score: int
    state: str
    expires_at: AwareDatetime
    eligible_to_speak: bool
    blocked_reason: str


class SpeakingConsent(Contract):
    connection_id: UUID
    name: str
    agreed: bool


class SpeechReceipt(Contract):
    id: UUID
    state: str
    played_text: str | None
    played_ms: int
    reason: str | None
    approved_at: AwareDatetime
    first_audio_at: AwareDatetime | None
    stopped_at: AwareDatetime | None
    stop_detected_at: AwareDatetime | None = None
    approval_to_audio_ms: int | None
    end_of_input_to_audio_ms: int | None
    recognition_delay_ms: int | None = None
    hearing_confirmed: Literal[False] = False


class SpeechView(Contract):
    observed_at: AwareDatetime
    mode: Mode
    mode_revision: int
    revision: int
    floor: Literal['idle','waiting','generating','speaking','paused','unavailable']
    provider: Literal['fixture','cartesia','unavailable']
    provider_model: str
    quiet_seconds: float
    quiet_for_seconds: float = 0
    consents: list[SpeakingConsent]
    cues: list[PrivateCue]
    receipts: list[SpeechReceipt]
    message: str
