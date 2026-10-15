from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictBool

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')

class ScopeRequest(Input):
    allowed: StrictBool

class LookupRequest(Input):
    window: Literal['morning','afternoon']
    location: Literal['Riverside Lab','Harbor Lab','Hilltop Lab']='Riverside Lab'
    day: str=Field(default='2026-10-20',pattern=r'^\d{4}-\d{2}-\d{2}$')

class ApprovalRequest(Input):
    digest: str = Field(min_length=64,max_length=64)

class PrerequisiteRequest(Input):
    expected_fingerprint: str = Field(min_length=64,max_length=64)
    order: StrictBool = False

class ScenarioRequest(Input):
    mode: Literal['normal','no_slot','expired','delayed','rejected','timeout_after_write','duplicate_callback']

class ActionView(BaseModel):
    id: UUID
    item_id: UUID
    title: str
    window: Literal['morning','afternoon']
    state: str
    message: str
    digest: str | None = None
    slot: dict | None = None
    checked_at: str | None = None
    source: str = 'Local sandbox office'
    receipt: dict | None = None
    fingerprint: str | None = None
    clinician_confirmed: bool = False
    order_available: bool = False
    patient_authorized: bool = False
    scope_allowed: bool = False

class ExecutionView(BaseModel):
    sandbox: Literal[True] = True
    configured: bool
    actions: list[ActionView]
