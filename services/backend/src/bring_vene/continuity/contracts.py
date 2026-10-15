from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime,Field,model_validator
from bring_vene.domain.contracts import Contract,Invitation,Evidence

class OfficeReceipt(Contract):
    sandbox: Literal[True]
    request_id: UUID
    receipt_id: UUID
    status: Literal['confirmed','rejected']
    slot_id: str=Field(min_length=1,max_length=120)
    recorded_at: AwareDatetime
    reason: str=Field(max_length=500)

class OfficeCallback(Contract):
    delivery_id: UUID
    result: OfficeReceipt

class DocumentUpload(Contract):
    title: str=Field(min_length=3,max_length=120)
    format: Literal['text','pdf']='text'
    text: str|None=Field(default=None,min_length=3,max_length=12000)
    file_base64: str|None=Field(default=None,max_length=350000)
    plan_ids: list[UUID]=Field(default_factory=list,max_length=8)
    @model_validator(mode='after')
    def matching_input(self):
        if self.format=='text' and (not self.text or self.file_base64 is not None):raise ValueError('Provide text for a text document.')
        if self.format=='pdf' and (not self.file_base64 or self.text is not None):raise ValueError('Provide one PDF file.')
        return self

class ReviewRequest(Contract):
    fingerprint: str=Field(min_length=64,max_length=64)
    note: str=Field(min_length=3,max_length=300)

class FamilyDraftRequest(Contract):
    recipient_id: UUID
    plan_ids: list[UUID]=Field(min_length=1,max_length=8)
    fields: list[Literal['title','owner','timeframe','office_status']]=Field(min_length=1,max_length=4)

class DigestRequest(Contract):
    digest: str=Field(min_length=64,max_length=64)

class NextVisitRequest(Contract):
    plan_ids: list[UUID]=Field(max_length=8)
    visit_at: AwareDatetime

class NextVisitCreated(Contract):
    encounter_id: UUID
    invitation: Invitation

class DeleteRequest(Contract):
    confirmation: Literal['DELETE SYNTHETIC VISIT']
    expected_version: int=Field(ge=0)

class Difference(Contract):
    kind: Literal['timing','location','clinical_instruction','review']
    plan_id: UUID|None=None
    source_quote: str
    start: int
    end: int
    expected: str|None=None
    explanation: str

class DocumentView(Contract):
    id: UUID
    source: Evidence
    format: Literal['text','pdf']
    sha256: str
    pages: list[dict]
    differences: list[Difference]
    review_state: Literal['unresolved','reviewed','stale']
    fingerprint: str|None=None
    reviewed_by: str|None=None
    review_note: str|None=None

class FamilyUpdateView(Contract):
    id: UUID
    recipient_id: UUID
    state: str
    text: str
    fields: list[str]
    digest: str|None=None
    receipt: dict|None=None

class ContinuityView(Contract):
    documents: list[DocumentView]
    family_updates: list[FamilyUpdateView]
    family_recipients: list[dict]
    next_visits: list[dict]
    callback_count: int
    conversation_gap_since: AwareDatetime|None=None
    sandbox_tools_enabled: bool=False
