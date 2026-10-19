from uuid import UUID
from fastapi import APIRouter, Depends, Request
from bring_vene.auth import COOKIE
from bring_vene.domain.service import DomainError
from bring_vene.memory import service
from bring_vene.memory.contracts import CarryRequest, MemoryView, OutcomeRequest


def memory_router(engine, settings, mutation):
    router = APIRouter(prefix='/encounters/{encounter_id}/memory')

    def credentials(request):
        csrf = request.headers.get('x-vene-csrf')
        if not csrf:
            raise DomainError(403, 'A current participant session is required for this change.')
        return request.cookies.get(COOKIE), csrf

    @router.get('', response_model=MemoryView)
    def state(encounter_id: UUID, request: Request):
        return service.state(engine, encounter_id, request.cookies.get(COOKIE))

    @router.post('/carry', response_model=MemoryView, dependencies=[Depends(mutation)])
    def carry(encounter_id: UUID, body: CarryRequest, request: Request):
        service.carry(engine, encounter_id, *credentials(request), body)
        return service.state(engine, encounter_id, request.cookies.get(COOKIE))

    @router.post('/outcomes', response_model=MemoryView, dependencies=[Depends(mutation)])
    def outcome(encounter_id: UUID, body: OutcomeRequest, request: Request):
        service.outcome(engine, encounter_id, *credentials(request), body)
        return service.state(engine, encounter_id, request.cookies.get(COOKIE))

    return router
