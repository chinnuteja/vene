from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime, Field, StrictBool
from bring_vene.domain.contracts import Contract, Role


class CallParticipant(Contract):
    connection_id: UUID
    membership_id: UUID
    name: str
    role: Role
    present: bool
    consent: Literal['pending','agreed','declined']
    track_epoch: int


class CallView(Contract):
    observed_at: AwareDatetime
    encounter_id: UUID
    generation: UUID
    revision: int
    consent_epoch: int
    state: Literal['waiting','consent_needed','active','paused','stopping','unavailable','ended']
    manual_pause: bool
    output_silenced: bool
    worker_ready: bool
    provider: Literal['fixture','deepgram','unavailable']
    participants: list[CallParticipant]
    own_connection_id: UUID | None = None
    audio_recorded: Literal[False] = False
    transcripts_shared: Literal[False] = False
    terms_version: Literal['voice-processing-v1'] = 'voice-processing-v1'
    gap_since: AwareDatetime | None = None


class CallAdmission(Contract):
    connection_id: UUID
    token: str
    server_url: str
    expires_at: AwareDatetime
    call: CallView


class ConsentRequest(Contract):
    command_id: UUID
    connection_id: UUID
    decision: Literal['agreed','declined']
    terms_version: Literal['voice-processing-v1']


class CallControl(Contract):
    command_id: UUID
    type: Literal['pause','resume','silence','end']
    expected_revision: int = Field(ge=0)
    silenced: StrictBool | None = None


class AudioReceipt(Contract):
    connection_id: UUID
    track_sid: str
    track_epoch: int
    consent_epoch: int
    frames: int
    samples: int
    non_silent_frames: int
    first_received_at: AwareDatetime
    last_received_at: AwareDatetime


class CallDiagnostics(Contract):
    active_tasks: int
    stopped_epoch: int
    receipts: list[AudioReceipt]


class Utterance(Contract):
    id: UUID
    connection_id: UUID
    membership_id: UUID
    track_epoch: int
    consent_epoch: int
    text: str
    finalized_at: AwareDatetime
    provider: Literal['deepgram']
