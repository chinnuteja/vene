from uuid import UUID
from fastapi import APIRouter, Depends, Request
from bring_vene.auth import COOKIE
from bring_vene.domain.service import DomainError
from bring_vene.circle import service
from bring_vene.circle.contracts import CircleView, RideAnswer, RideAsk


def circle_router(engine, settings, mutation):
    router = APIRouter(prefix='/encounters/{encounter_id}/care-circle')

    def credentials(request):
        csrf = request.headers.get('x-vene-csrf')
        if not csrf:
            raise DomainError(403, 'A current participant session is required for this change.')
        return request.cookies.get(COOKIE), csrf

    def result(visit_id, request):
        return service.state(engine, visit_id, request.cookies.get(COOKIE))

    @router.get('', response_model=CircleView)
    def state(encounter_id: UUID, request: Request):
        return result(encounter_id, request)

    @router.post('/rides', response_model=CircleView, dependencies=[Depends(mutation)])
    def ask(encounter_id: UUID, body: RideAsk, request: Request):
        service.ask(engine, encounter_id, *credentials(request), body)
        return result(encounter_id, request)

    @router.post('/rides/{request_id}/withdraw', response_model=CircleView, dependencies=[Depends(mutation)])
    def withdraw(encounter_id: UUID, request_id: UUID, request: Request):
        service.withdraw(engine, encounter_id, request_id, *credentials(request))
        return result(encounter_id, request)

    @router.post('/rides/{request_id}/answer', response_model=CircleView, dependencies=[Depends(mutation)])
    def answer(encounter_id: UUID, request_id: UUID, body: RideAnswer, request: Request):
        service.answer(engine, encounter_id, request_id, *credentials(request), body)
        return result(encounter_id, request)

    return router
