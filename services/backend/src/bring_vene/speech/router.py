from uuid import UUID
from fastapi import APIRouter,Depends,Request
from bring_vene.auth import COOKIE
from bring_vene.speech import service
from bring_vene.speech.contracts import SpeechView,ModeRequest,SpeechAgreement,CueApproval,SpeechAction


def speech_router(engine,settings,mutation):
    router=APIRouter(prefix='/encounters/{encounter_id}/speech')
    def credentials(request):return request.cookies.get(COOKIE),request.headers.get('x-vene-csrf')

    @router.get('',response_model=SpeechView)
    def state(encounter_id:UUID,request:Request):return service.read(engine,encounter_id,request.cookies.get(COOKIE),settings)

    @router.post('/mode',response_model=SpeechView,dependencies=[Depends(mutation)])
    def mode(encounter_id:UUID,body:ModeRequest,request:Request):return service.mode(engine,encounter_id,*credentials(request),body,settings)

    @router.post('/agreement',response_model=SpeechView,dependencies=[Depends(mutation)])
    def agree(encounter_id:UUID,body:SpeechAgreement,request:Request):return service.agree(engine,encounter_id,*credentials(request),body,settings)

    @router.post('/approve',response_model=SpeechView,dependencies=[Depends(mutation)])
    def approve(encounter_id:UUID,body:CueApproval,request:Request):return service.approve(engine,encounter_id,*credentials(request),body,settings)

    @router.post('/actions',response_model=SpeechView,dependencies=[Depends(mutation)])
    def action(encounter_id:UUID,body:SpeechAction,request:Request):return service.action(engine,encounter_id,*credentials(request),body,settings)
    return router
