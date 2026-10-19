from uuid import UUID
from fastapi import APIRouter, Depends, Request
from bring_vene.auth import COOKIE
from bring_vene.domain.service import DomainError
from bring_vene.feasibility import service
from bring_vene.feasibility.contracts import FeasibilityView, ResolveRequest, StandingRequest


def feasibility_router(engine, settings, mutation):
    router = APIRouter(prefix='/encounters/{encounter_id}/feasibility')

    def credentials(request):
        csrf = request.headers.get('x-vene-csrf')
        if not csrf:
            raise DomainError(403, 'A current participant session is required for this change.')
        return request.cookies.get(COOKIE), csrf

    def result(visit_id, request):
        return service.state(engine, visit_id, request.cookies.get(COOKIE))

    @router.get('', response_model=FeasibilityView)
    def state(encounter_id: UUID, request: Request):
        return result(encounter_id, request)

    @router.post('/standing', response_model=FeasibilityView, dependencies=[Depends(mutation)])
    def standing(encounter_id: UUID, body: StandingRequest, request: Request):
        service.set_standing(engine, encounter_id, *credentials(request), body)
        return result(encounter_id, request)

    @router.post('/obstacles/{obstacle_id}/resolve', response_model=FeasibilityView, dependencies=[Depends(mutation)])
    def resolve(encounter_id: UUID, obstacle_id: UUID, body: ResolveRequest, request: Request):
        service.resolve(engine, encounter_id, obstacle_id, *credentials(request), body, settings)
        return result(encounter_id, request)

    @router.get('/obstacles/{obstacle_id}/timings')
    def timings(encounter_id: UUID, obstacle_id: UUID, request: Request):
        return service.timings(engine, encounter_id, obstacle_id, request.cookies.get(COOKIE))

    return router
