from uuid import UUID
from fastapi import APIRouter,Depends,Request
from sqlalchemy.orm import Session
from bring_vene.auth import COOKIE,authenticate
from bring_vene.domain.contracts import EncounterView,UnderstandingStatus
from bring_vene.domain.service import DomainError
from bring_vene.persistence.models import UnderstandingRecord
from bring_vene.understanding import service
from bring_vene.understanding.contracts import ProcessingRequest,FixtureTurn,SourceCorrection,PlanCorrection,Mutation


def understanding_router(engine,settings,mutation):
    router=APIRouter(prefix='/encounters/{encounter_id}/understanding')
    def credentials(request):return request.cookies.get(COOKIE),request.headers.get('x-vene-csrf')

    @router.get('',response_model=UnderstandingStatus)
    def state(encounter_id:UUID,request:Request):
        with Session(engine) as session:
            member,_=authenticate(session,request.cookies.get(COOKIE),encounter_id)
            if member.role!='patient':raise DomainError(403,'Understanding is private to the patient.')
            row=session.get(UnderstandingRecord,encounter_id)
            if row:return service.status(row,settings)
            row=UnderstandingRecord(enabled=False,revision=0,processed_revision=0,state='off',message='')
            return service.status(row,settings)

    @router.post('/processing',response_model=EncounterView,dependencies=[Depends(mutation)])
    def processing(encounter_id:UUID,body:ProcessingRequest,request:Request):
        return service.processing(engine,encounter_id,*credentials(request),body,settings)

    @router.post('/fixture-turns',response_model=EncounterView,dependencies=[Depends(mutation)])
    def turn(encounter_id:UUID,body:FixtureTurn,request:Request):
        if not request.client or request.client.host not in {'127.0.0.1','::1','testclient'}:raise DomainError(404,'Not found.')
        return service.fixture_turn(engine,encounter_id,*credentials(request),body,settings)

    @router.post('/sources/{source_id}/correct',response_model=EncounterView,dependencies=[Depends(mutation)])
    def source(encounter_id:UUID,source_id:UUID,body:SourceCorrection,request:Request):
        return service.correct_source(engine,encounter_id,*credentials(request),source_id,body,settings)

    @router.post('/plan/{item_id}/correct',response_model=EncounterView,dependencies=[Depends(mutation)])
    def plan(encounter_id:UUID,item_id:UUID,body:PlanCorrection,request:Request):
        return service.correct_plan(engine,encounter_id,*credentials(request),item_id,body,settings)

    @router.post('/retry',response_model=EncounterView,dependencies=[Depends(mutation)])
    def retry(encounter_id:UUID,body:Mutation,request:Request):
        return service.retry(engine,encounter_id,*credentials(request),body,settings)
    return router
