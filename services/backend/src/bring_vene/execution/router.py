from uuid import UUID
from fastapi import APIRouter,Depends,Request
from bring_vene.auth import COOKIE
from bring_vene.domain.service import DomainError
from bring_vene.execution import service
from bring_vene.execution.gateway import OfficeGateway
from bring_vene.execution.contracts import (ExecutionView,ScopeRequest,LookupRequest,ApprovalRequest,PrerequisiteRequest,ScenarioRequest)
from sqlalchemy.orm import Session

def execution_router(engine,settings,mutation):
    router=APIRouter(prefix='/encounters/{encounter_id}/execution')
    def credentials(request):
        csrf=request.headers.get('x-vene-csrf')
        if not csrf:raise DomainError(403,'A current participant session is required for this change.')
        return request.cookies.get(COOKIE),csrf
    def result(visit_id,request):return service.state(engine,visit_id,request.cookies.get(COOKIE),settings)

    @router.get('',response_model=ExecutionView)
    def state(encounter_id:UUID,request:Request):return result(encounter_id,request)

    @router.post('/items/{item_id}/scope',response_model=ExecutionView,dependencies=[Depends(mutation)])
    def scope(encounter_id:UUID,item_id:UUID,body:ScopeRequest,request:Request):
        service.scope(engine,encounter_id,item_id,*credentials(request),body);return result(encounter_id,request)

    @router.post('/items/{item_id}/lookup',response_model=ExecutionView,dependencies=[Depends(mutation)])
    def lookup(encounter_id:UUID,item_id:UUID,body:LookupRequest,request:Request):
        service.lookup(engine,encounter_id,item_id,*credentials(request),body,settings);return result(encounter_id,request)

    @router.post('/actions/{action_id}/approve',response_model=ExecutionView,dependencies=[Depends(mutation)])
    def approve(encounter_id:UUID,action_id:UUID,body:ApprovalRequest,request:Request):
        service.approve(engine,encounter_id,action_id,*credentials(request),body);return result(encounter_id,request)

    @router.post('/actions/{action_id}/prerequisites',response_model=ExecutionView,dependencies=[Depends(mutation)])
    def prerequisites(encounter_id:UUID,action_id:UUID,body:PrerequisiteRequest,request:Request):
        service.prerequisites(engine,encounter_id,action_id,*credentials(request),body,settings);return result(encounter_id,request)

    @router.post('/scenario',dependencies=[Depends(mutation)])
    def scenario(encounter_id:UUID,body:ScenarioRequest,request:Request):
        if not settings.bring_vene_development or not request.client or request.client.host not in {'127.0.0.1','::1','testclient'}:
            raise DomainError(404,'Not found.')
        with Session(engine) as session,session.begin():
            _,_,member,_=service.access(session,encounter_id,*credentials(request));service.patient(member)
        try:return OfficeGateway(settings).call('/scenario',body.model_dump())
        except Exception:raise DomainError(503,'The sandbox office is unavailable. No scenario change was confirmed.')
    return router
