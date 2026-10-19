import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from bring_vene.auth import COOKIE
from bring_vene.voice import service
from bring_vene.voice.contracts import (CallAdmission, CallView, CallControl, ConsentRequest, CallDiagnostics, Utterance)


def call_router(engine,settings,mutation):
    router=APIRouter(prefix='/encounters/{encounter_id}/call')
    def credentials(request):return request.cookies.get(COOKIE),request.headers.get('x-vene-csrf')

    @router.get('',response_model=CallView)
    def state(encounter_id:UUID,request:Request):
        return service.read_call(engine,encounter_id,request.cookies.get(COOKIE),settings)

    @router.post('/admit',response_model=CallAdmission,dependencies=[Depends(mutation)])
    def admit(encounter_id:UUID,request:Request):
        admission=service.admit(engine,encounter_id,*credentials(request),settings)
        # Commit the admission first. In an empty room the owned warm native
        # participant can establish RTC before a listen-only human joins. Waiting
        # is bounded; unavailable AI never fabricates readiness or blocks humans.
        if not any(p.present for p in admission.call.participants):
            import time
            deadline=time.monotonic()+min(5,max(0,settings.voice_admission_wait_seconds))
            while time.monotonic()<deadline:
                current=service.read_call(engine,encounter_id,request.cookies.get(COOKIE),settings)
                if current.generation!=admission.call.generation:break
                admission.call=current
                if current.worker_ready:break
                time.sleep(.1)
        return admission

    @router.post('/consent',response_model=CallView,dependencies=[Depends(mutation)])
    def consent(encounter_id:UUID,body:ConsentRequest,request:Request):
        return service.consent(engine,encounter_id,*credentials(request),body,settings)

    @router.post('/controls',response_model=CallView,dependencies=[Depends(mutation)])
    async def control(encounter_id:UUID,body:CallControl,request:Request):
        token,csrf=credentials(request)
        result=await asyncio.to_thread(service.control,engine,encounter_id,token,csrf,body,settings)
        if body.type in {'pause','end'} and result.worker_ready:
            # Wait for provider/track tasks to close, instead of claiming success on a muted speaker.
            for _ in range(25):
                await asyncio.sleep(.08)
                result=await asyncio.to_thread(service.read_call,engine,encounter_id,token,settings)
                if result.state in {'paused','ended','unavailable'}:break
        return result

    @router.post('/connections/{connection_id}/leave',response_model=CallView,dependencies=[Depends(mutation)])
    def leave(encounter_id:UUID,connection_id:UUID,request:Request):
        return service.leave(engine,encounter_id,*credentials(request),connection_id,settings)

    @router.post('/connections/{connection_id}/verify',response_model=CallView,dependencies=[Depends(mutation)])
    def verify(encounter_id:UUID,connection_id:UUID,request:Request):
        return service.verify_admission(engine,encounter_id,*credentials(request),connection_id,settings)

    @router.get('/diagnostics',response_model=CallDiagnostics)
    def diagnostics(encounter_id:UUID,request:Request):
        return service.diagnostics(engine,encounter_id,request.cookies.get(COOKIE))

    @router.get('/utterances',response_model=list[Utterance])
    def utterances(encounter_id:UUID,request:Request):
        return service.utterances(engine,encounter_id,request.cookies.get(COOKIE))

    return router
