from typing import Literal
from pydantic import AwareDatetime, Field
from bring_vene.domain.contracts import Contract

PersonRole = Literal['clinician', 'family', 'other']


class PersonIn(Contract):
    name: str = Field(min_length=2, max_length=60)
    role: PersonRole


class RoomStart(Contract):
    people: list[PersonIn] = Field(min_length=1, max_length=6)


class Attest(Contract):
    person_id: str = Field(min_length=3, max_length=40)
    agreed: bool


class LabelMap(Contract):
    label: str = Field(pattern=r'^S\d{1,2}$')
    # 'patient' for the device owner, a declared person's id, or None for "someone else / not sure".
    person_id: str | None = Field(default=None, max_length=40)


class RoomUtterance(Contract):
    label: str = Field(pattern=r'^S\d{1,2}$')
    text: str = Field(min_length=3, max_length=2000)


class Person(Contract):
    id: str
    name: str
    role: PersonRole
    agreed: bool | None = None
    attested_at: AwareDatetime | None = None


class SpeakerView(Contract):
    label: str
    person_id: str | None = None
    name: str
    attributed: bool
    last_heard: str | None = None


class RoomView(Contract):
    state: Literal['off', 'setting_up', 'active', 'declined']
    people: list[Person] = Field(default_factory=list)
    disclosure: str
    disclosure_at: AwareDatetime | None = None
    speakers: list[SpeakerView] = Field(default_factory=list)
    suppressed_self_speech: int = 0
    fixture_input_enabled: bool = False
