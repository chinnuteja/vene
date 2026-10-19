from uuid import UUID
from fastapi import APIRouter, Depends, Header, Request
from bring_vene.auth import COOKIE
from bring_vene.domain.service import DomainError
from bring_vene.dial import service
from bring_vene.dial.contracts import BridgeAdmit, BridgeAdmitted, PinIssued, PinRequest


def dial_router(engine, settings, mutation):
    router = APIRouter()

    def credentials(request):
        csrf = request.headers.get('x-vene-csrf')
        if not csrf:
            raise DomainError(403, 'A current participant session is required for this change.')
        return request.cookies.get(COOKIE), csrf

    @router.post('/encounters/{encounter_id}/dial-pins', response_model=PinIssued, dependencies=[Depends(mutation)])
    def issue(encounter_id: UUID, body: PinRequest, request: Request):
        return service.issue(engine, encounter_id, *credentials(request), body, settings)

    @router.post('/integrations/phone/admit', response_model=BridgeAdmitted)
    def admit(body: BridgeAdmit, authorization: str | None = Header(default=None)):
        # Server-to-server: the phone bridge authenticates with its own token, not a browser session.
        return service.admit(engine, settings, authorization, body)

    return router
