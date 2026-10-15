from uuid import UUID
from fastapi import APIRouter,Depends,Request
from sqlalchemy.orm import Session
from bring_vene.auth import COOKIE
from bring_vene.domain.service import DomainError
from bring_vene.execution.gateway import OfficeGateway
from bring_vene.execution.service import access,patient
from bring_vene.persistence.models import ExecutionRecord
from bring_vene.continuity import service,documents,callbacks
from bring_vene.continuity.contracts import (ContinuityView,DocumentUpload,ReviewRequest,FamilyDraftRequest,DigestRequest,
    NextVisitRequest,NextVisitCreated,DeleteRequest)

def continuity_router(engine,settings,mutation):
    router=APIRouter()
    base='/encounters/{encounter_id}/continuity'
    def credentials(request):
        csrf=request.headers.get('x-vene-csrf')
        if not csrf:raise DomainError(403,'A current participant session is required.')
        return request.cookies.get(COOKIE),csrf
    def view(visit_id,request):return service.state(engine,visit_id,request.cookies.get(COOKIE),settings)

    @router.post('/integrations/office/results')
    async def office_callback(request:Request):
        body=bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body)>16000:raise DomainError(413,'Office callback is too large.')
        import asyncio
        return await asyncio.to_thread(callbacks.ingest,engine,settings,bytes(body),request.headers)

    @router.get(base,response_model=ContinuityView)
    def state(encounter_id:UUID,request:Request):return view(encounter_id,request)

    @router.post(base+'/documents',response_model=ContinuityView,dependencies=[Depends(mutation)])
    def upload(encounter_id:UUID,body:DocumentUpload,request:Request):
        documents.upload(engine,encounter_id,*credentials(request),body);return view(encounter_id,request)

    @router.post(base+'/documents/{document_id}/review',response_model=ContinuityView,dependencies=[Depends(mutation)])
    def review(encounter_id:UUID,document_id:UUID,body:ReviewRequest,request:Request):
        documents.review(engine,encounter_id,document_id,*credentials(request),body);return view(encounter_id,request)

    @router.post(base+'/family-updates',response_model=ContinuityView,dependencies=[Depends(mutation)])
    def draft(encounter_id:UUID,body:FamilyDraftRequest,request:Request):
        service.draft_family(engine,encounter_id,*credentials(request),body);return view(encounter_id,request)

    @router.post(base+'/family-updates/{update_id}/approve',response_model=ContinuityView,dependencies=[Depends(mutation)])
    def approve(encounter_id:UUID,update_id:UUID,body:DigestRequest,request:Request):
        service.approve_family(engine,encounter_id,update_id,*credentials(request),body);return view(encounter_id,request)

    @router.post(base+'/next-visit',response_model=NextVisitCreated,dependencies=[Depends(mutation)])
    def next_visit(encounter_id:UUID,body:NextVisitRequest,request:Request):return service.next_visit(engine,encounter_id,*credentials(request),body)

    @router.post(base+'/delete',dependencies=[Depends(mutation)])
    def delete_visit(encounter_id:UUID,body:DeleteRequest,request:Request):return service.delete_encounter(engine,encounter_id,*credentials(request),body)

    @router.post(base+'/sandbox-callbacks/{action_id}',dependencies=[Depends(mutation)])
    def repeat_callback(encounter_id:UUID,action_id:UUID,request:Request):
        if not settings.bring_vene_development or not request.client or request.client.host not in {'testclient','127.0.0.1','::1'}:raise DomainError(404,'Not found.')
        with Session(engine) as session,session.begin():
            _,_,member,_=access(session,encounter_id,*credentials(request));patient(member)
            action=session.get(ExecutionRecord,action_id)
            if not action or action.encounter_id!=encounter_id or not action.content.get('receipt'):raise DomainError(404,'Receipt not found.')
        try:return OfficeGateway(settings).call('/callbacks/'+str(action_id)+'/repeat',{})
        except Exception:raise DomainError(503,'No repeated sandbox callback was queued.')
    return router
