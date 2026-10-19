from uuid import UUID
from fastapi import APIRouter, Depends, Request
from bring_vene.auth import COOKIE
from bring_vene.domain.service import DomainError
from bring_vene.room import service
from bring_vene.room.contracts import Attest, LabelMap, PersonIn, RoomStart, RoomUtterance, RoomView


def room_router(engine, settings, mutation):
    router = APIRouter(prefix='/encounters/{encounter_id}/room')

    def credentials(request):
        csrf = request.headers.get('x-vene-csrf')
        if not csrf:
            raise DomainError(403, 'A current participant session is required for this change.')
        return request.cookies.get(COOKIE), csrf

    def result(visit_id, request):
        return service.state(engine, visit_id, request.cookies.get(COOKIE), settings)

    @router.get('', response_model=RoomView)
    def state(encounter_id: UUID, request: Request):
        return result(encounter_id, request)

    @router.post('/start', response_model=RoomView, dependencies=[Depends(mutation)])
    def start(encounter_id: UUID, body: RoomStart, request: Request):
        service.start(engine, encounter_id, *credentials(request), body)
        return result(encounter_id, request)

    @router.post('/people', response_model=RoomView, dependencies=[Depends(mutation)])
    def add_person(encounter_id: UUID, body: PersonIn, request: Request):
        service.add_person(engine, encounter_id, *credentials(request), body)
        return result(encounter_id, request)

    @router.post('/disclosure', response_model=RoomView, dependencies=[Depends(mutation)])
    def disclosure(encounter_id: UUID, request: Request):
        service.give_disclosure(engine, encounter_id, *credentials(request))
        return result(encounter_id, request)

    @router.post('/agreements', response_model=RoomView, dependencies=[Depends(mutation)])
    def attest(encounter_id: UUID, body: Attest, request: Request):
        service.attest(engine, encounter_id, *credentials(request), body)
        return result(encounter_id, request)

    @router.post('/speakers', response_model=RoomView, dependencies=[Depends(mutation)])
    def map_label(encounter_id: UUID, body: LabelMap, request: Request):
        service.map_label(engine, encounter_id, *credentials(request), body, settings)
        return result(encounter_id, request)

    @router.post('/end', response_model=RoomView, dependencies=[Depends(mutation)])
    def end(encounter_id: UUID, request: Request):
        service.end(engine, encounter_id, *credentials(request))
        return result(encounter_id, request)

    @router.post('/fixture-utterances', response_model=RoomView, dependencies=[Depends(mutation)])
    def fixture(encounter_id: UUID, body: RoomUtterance, request: Request):
        service.fixture_utterance(engine, encounter_id, *credentials(request), body, settings)
        return result(encounter_id, request)

    return router
