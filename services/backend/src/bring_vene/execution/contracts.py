from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StrictBool

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')

class ScopeRequest(Input):
    allowed: StrictBool

class LookupRequest(Input):
    window: Literal['morning','afternoon']
    # Validated against the step's errand kind; defaults keep the original lab request shape.
    location: str=Field(default='Riverside Lab',min_length=3,max_length=60)
    day: str=Field(default='2026-10-20',pattern=r'^\d{4}-\d{2}-\d{2}$')

class OfficeLookup(LookupRequest):
    institution: Literal['lab','imaging','specialist','pharmacy','plan']='lab'

class ApprovalRequest(Input):
    digest: str = Field(min_length=64,max_length=64)

class PrerequisiteRequest(Input):
    expected_fingerprint: str = Field(min_length=64,max_length=64)
    order: StrictBool = False

class ScenarioRequest(Input):
    mode: Literal['normal','no_slot','expired','delayed','rejected','timeout_after_write','duplicate_callback','out_of_stock']
    kind: Literal['lab','imaging','referral','prescription','authorization']='lab'

class OfficeScenario(Input):
    mode: Literal['normal','no_slot','expired','delayed','rejected','timeout_after_write','duplicate_callback','out_of_stock']
    institution: Literal['lab','imaging','specialist','pharmacy','plan']='lab'

class BundleRequest(Input):
    digests: list[str]=Field(min_length=1,max_length=8)

class BundleOutcome(BaseModel):
    action_id: UUID
    outcome: Literal['queued','already_approved','waiting','refused']
    message: str

class BundleResult(BaseModel):
    outcomes: list[BundleOutcome]
    unmatched: int = 0  # digests that no longer match a current request

class ActionView(BaseModel):
    id: UUID
    item_id: UUID
    kind: Literal['lab','imaging','referral','prescription','authorization']='lab'
    place: str='lab'
    document: str='lab order'
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

class ErrandOption(BaseModel):
    kind: Literal['lab','imaging','referral','prescription','authorization']
    place: str
    document: str
    offered: str
    confirmed: str
    locations: list[str]
    days: list[dict]

class ExecutionView(BaseModel):
    sandbox: Literal[True] = True
    configured: bool
    actions: list[ActionView]
    errands: list[ErrandOption] = []

class CoverageQuery(Input):
    member_ref: str=Field(min_length=3,max_length=40)
    service: Literal['imaging','prescription']
    medicine: str|None=Field(default=None,max_length=60)

class StockQuery(Input):
    medicine: str=Field(min_length=2,max_length=60)
    location: str=Field(min_length=3,max_length=60)
