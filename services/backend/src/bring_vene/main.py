import asyncio
from urllib.parse import urlparse
from uuid import UUID
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from bring_vene.auth import COOKIE, FIXTURE_MEMBERS, FIXTURE_VISIT, authenticate, identity, issue_invitation, redeem, digest
from bring_vene.config import Settings
from bring_vene.domain.context import context_adapter
from bring_vene.domain.contracts import (CommandEnvelope, CommandResult, ContextView, EncounterSummary,
    EncounterView, Evidence, FixtureLaunch, Health, Identity, Invitation, InviteRequest, MemberView, RedeemRequest, Audience)
from bring_vene.domain.service import DomainError, apply_command, utc_now
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import EncounterRecord, InvitationRecord, MembershipRecord, SessionRecord, CallRecord
from bring_vene.voice.router import call_router
from bring_vene.understanding.router import understanding_router
from bring_vene.speech.router import speech_router
from bring_vene.execution.router import execution_router
from bring_vene.continuity.router import continuity_router
from bring_vene.circle.router import circle_router
from bring_vene.feasibility.router import feasibility_router


def authorized_view(engine, token, encounter_id):
    with Session(engine) as session, session.begin():
        session.execute(text('SET LOCAL synchronous_commit=off'))
        record = session.scalar(select(EncounterRecord).where(EncounterRecord.id == encounter_id).with_for_update(read=True))
        member, _ = authenticate(session, token, encounter_id)
        if not record:
            raise DomainError(404, "Visit not found.")
        return context_adapter.view(EncounterView.model_validate(record.projection), member.role, member.id)


async def view_stream(engine, token, encounter_id, disconnected, interval=0.35):
    """Replacements only; never publish/replay the private event journal.

    Reads and revocation serialize on the encounter. Previously delivered bytes cannot
    be recalled. Every subsequent publication rechecks membership and current scope.
    """
    last = None
    while not await disconnected():
        try:
            view = await asyncio.to_thread(authorized_view, engine, token, encounter_id)
            payload = view.model_dump_json()
            if payload != last:
                yield f"event: {'snapshot' if last is None else 'update'}\ndata: {payload}\n\n"
                last = payload
            else:
                yield ": keepalive\n\n"
        except DomainError:
            yield 'event: access_revoked\ndata: {}\n\n'
            return
        except SQLAlchemyError:
            yield 'event: unavailable\ndata: {}\n\n'
            return
        await asyncio.sleep(interval)


def create_app(settings: Settings | None = None, engine=None):
    settings = settings or Settings()
    application = FastAPI(title="Bring Vene", version="0.2.0", description="Patient-controlled synthetic visit preparation.")
    db = engine if engine is not None else make_engine(settings.database_url)
    application.state.engine = db

    @application.exception_handler(DomainError)
    async def domain_error(_request, error):
        return JSONResponse(status_code=error.status, content={"detail": error.message}, headers={"Cache-Control": "no-store"})

    @application.exception_handler(SQLAlchemyError)
    async def database_error(_request, _error):
        print('Visit database failure: '+type(_error).__name__,flush=True)
        return JSONResponse(status_code=503, content={"detail": "The visit service is temporarily unavailable."})

    @application.middleware("http")
    async def private_responses(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def mutation(request: Request):
        # Includes redemption to prevent login CSRF. No permissive CORS.
        if request.headers.get("x-vene-intent") != "mutation":
            raise DomainError(403, "Open this visit in its own window before making a change.")
        origin = request.headers.get("origin")
        if origin and origin != settings.frontend_origin:
            parsed = urlparse(origin)
            if not (settings.bring_vene_development and parsed.hostname in {"127.0.0.1", "localhost"} and parsed.scheme == "http"):
                raise DomainError(403, "This origin is not allowed.")

    def fixture_enabled(request):
        return (settings.bring_vene_development and settings.bring_vene_mode == "fixture"
                and request.client and request.client.host in {"127.0.0.1", "::1", "testclient"})

    def credentials(request):
        return request.cookies.get(COOKIE), request.headers.get("x-vene-csrf")

    def lock_visit(session, visit_id):
        record = session.scalar(select(EncounterRecord).where(EncounterRecord.id == visit_id).with_for_update())
        if not record:
            raise DomainError(404, "Visit not found.")
        return record

    def patient(session, request, visit_id):
        token, csrf = credentials(request)
        member, _ = authenticate(session, token, visit_id, csrf, mutate=True)
        if member.role != "patient":
            raise DomainError(403, "Only the patient can manage invitations.")
        return member

    @application.get("/health/live", response_model=Health)
    def live():
        return Health(status="alive")

    @application.get("/health/ready", response_model=Health, responses={503: {"model": Health}})
    def ready():
        try:
            with db.connect() as connection:
                connection.execute(text("SELECT 1"))
                connection.execute(select(EncounterRecord.id).limit(1))
        except SQLAlchemyError as error:
            print('Visit readiness failure: '+type(error).__name__,flush=True)
            return JSONResponse(status_code=503, content={"status": "unavailable", "database": "unavailable"})
        return Health(status="ready", database="ready")

    @application.get("/dev/fixture")
    def fixture_info(request: Request):
        return {"enabled": bool(fixture_enabled(request))}

    @application.post("/dev/invitations", response_model=Invitation, dependencies=[Depends(mutation)])
    def fixture_invitation(body: FixtureLaunch, request: Request):
        if not fixture_enabled(request):
            raise DomainError(404, "Not found.")
        from bring_vene.fixtures import ensure_case,members
        selected_visit=ensure_case(db,body.case)
        with Session(db) as session, session.begin():
            lock_visit(session, selected_visit)
            member = session.get(MembershipRecord, members(body.case)[body.persona])
            if not member or member.revoked_at:
                raise DomainError(409, "This fixture participant's access was withdrawn.")
            return issue_invitation(session, member)

    @application.get('/dev/cases')
    def fixture_cases(request:Request):
        if not fixture_enabled(request):raise DomainError(404,'Not found.')
        from bring_vene.fixtures import CASES
        return [{'id':key,**value} for key,value in CASES.items()]

    @application.post("/auth/redeem", response_model=Identity, dependencies=[Depends(mutation)])
    def redeem_invitation(body: RedeemRequest, response: Response, request: Request):
        token, viewer = redeem(db, body.token, hours=settings.session_hours)
        old, _ = credentials(request)
        if old:
            with Session(db) as session, session.begin():
                row = session.get(SessionRecord, digest(old))
                if row:
                    row.revoked_at = utc_now()
        response.set_cookie(COOKIE, token, httponly=True, secure=settings.cookie_secure,
                            samesite="strict", max_age=settings.session_hours * 3600, path="/")
        return viewer

    @application.get("/auth/me", response_model=Identity)
    def me(request: Request):
        with Session(db) as session:
            member, credential = authenticate(session, request.cookies.get(COOKIE))
            return identity(member, credential)

    @application.post("/auth/logout", dependencies=[Depends(mutation)])
    def logout(request: Request, response: Response):
        with Session(db) as session, session.begin():
            token, csrf = credentials(request)
            _, credential = authenticate(session, token, csrf=csrf, mutate=True)
            credential.revoked_at = utc_now()
        response.delete_cookie(COOKIE, path="/", httponly=True, secure=settings.cookie_secure, samesite="strict")
        return {"ok": True}

    @application.get("/encounters", response_model=list[EncounterSummary])
    def encounters(request: Request):
        with Session(db) as session:
            member, _ = authenticate(session, request.cookies.get(COOKIE))
            visit_id = member.encounter_id
        view = authorized_view(db, request.cookies.get(COOKIE), visit_id)
        return [EncounterSummary(id=view.id, title=view.title, patient_name=view.patient.name, version=view.version)]

    @application.get("/encounters/{encounter_id}", response_model=EncounterView)
    def encounter(encounter_id: UUID, request: Request):
        return authorized_view(db, request.cookies.get(COOKIE), encounter_id)

    @application.get("/encounters/{encounter_id}/evidence/{evidence_id}", response_model=Evidence)
    def evidence(encounter_id: UUID, evidence_id: UUID, request: Request):
        view = authorized_view(db, request.cookies.get(COOKIE), encounter_id)
        found = next((e for e in view.evidence if e.id == evidence_id), None)
        if not found:
            raise DomainError(404, "Source not found.")
        return found

    @application.get("/encounters/{encounter_id}/context", response_model=ContextView)
    def context(encounter_id: UUID, request: Request):
        view = authorized_view(db, request.cookies.get(COOKIE), encounter_id)
        return ContextView(encounter_id=view.id, consent_epoch=view.consent_epoch, audience=view.viewer_role,
                           priorities=view.priorities, plan=view.plan, evidence=view.evidence)

    @application.get("/encounters/{encounter_id}/context/shared", response_model=ContextView)
    def shared_context(encounter_id: UUID, audience: Audience, request: Request):
        view = authorized_view(db, request.cookies.get(COOKIE), encounter_id)
        if view.viewer_role != "patient":
            raise DomainError(403, "Only the patient can preview another audience.")
        return context_adapter.context(view, audience)

    @application.get("/encounters/{encounter_id}/stream")
    async def stream(encounter_id: UUID, request: Request):
        token = request.cookies.get(COOKIE)
        await asyncio.to_thread(authorized_view, db, token, encounter_id)
        return StreamingResponse(view_stream(db, token, encounter_id, request.is_disconnected),
                                  media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})

    @application.post("/encounters/{encounter_id}/commands", response_model=CommandResult, dependencies=[Depends(mutation)])
    def command(encounter_id: UUID, body: CommandEnvelope, request: Request):
        token, csrf = credentials(request)
        with Session(db) as session:
            authenticate(session, token, encounter_id, csrf, mutate=True)
        def authorize(session):
            return authenticate(session, token, encounter_id, csrf, mutate=True)[0]
        result = apply_command(db, encounter_id, body, authorize=authorize)
        result.encounter = authorized_view(db, token, encounter_id)
        return result

    @application.get("/encounters/{encounter_id}/members", response_model=list[MemberView])
    def members(encounter_id: UUID, request: Request):
        with Session(db) as session:
            member, _ = authenticate(session, request.cookies.get(COOKIE), encounter_id)
            if member.role != "patient":
                raise DomainError(403, "Only the patient can manage invitations.")
            return [MemberView(id=m.id, role=m.role, name=m.name, revoked=bool(m.revoked_at)) for m in
                    session.scalars(select(MembershipRecord).where(MembershipRecord.encounter_id == encounter_id))]

    @application.post("/encounters/{encounter_id}/invitations", response_model=Invitation, dependencies=[Depends(mutation)])
    def invite(encounter_id: UUID, body: InviteRequest, request: Request):
        with Session(db) as session, session.begin():
            record = lock_visit(session, encounter_id)
            patient(session, request, encounter_id)
            member = session.get(MembershipRecord, body.membership_id)
            if not member or member.encounter_id != encounter_id or member.role == "patient":
                raise DomainError(404, "Participant not found.")
            # A new explicit invitation can restore membership, never its old sessions.
            if member.revoked_at:
                view = EncounterView.model_validate(record.projection)
                view.consent_epoch += 1
                view.updated_at = utc_now()
                record.projection = view.model_dump(mode="json")
                record.updated_at = view.updated_at
            member.revoked_at = None
            return issue_invitation(session, member)

    @application.post("/encounters/{encounter_id}/invitations/{invitation_id}/revoke", dependencies=[Depends(mutation)])
    def revoke_invite(encounter_id: UUID, invitation_id: UUID, request: Request):
        with Session(db) as session, session.begin():
            lock_visit(session, encounter_id)
            patient(session, request, encounter_id)
            row = session.get(InvitationRecord, invitation_id)
            member = session.get(MembershipRecord, row.membership_id) if row else None
            if not member or member.encounter_id != encounter_id:
                raise DomainError(404, "Invitation not found.")
            row.revoked_at = utc_now()
        return {"ok": True}

    @application.post("/encounters/{encounter_id}/members/{membership_id}/revoke", response_model=EncounterView, dependencies=[Depends(mutation)])
    def revoke_member(encounter_id: UUID, membership_id: UUID, request: Request):
        with Session(db) as session, session.begin():
            record = lock_visit(session, encounter_id)
            patient(session, request, encounter_id)
            member = session.get(MembershipRecord, membership_id)
            if not member or member.encounter_id != encounter_id or member.role == "patient":
                raise DomainError(404, "Participant not found.")
            if not member.revoked_at:
                member.revoked_at = utc_now()
                for credential in session.scalars(select(SessionRecord).where(SessionRecord.membership_id == member.id)):
                    credential.revoked_at = member.revoked_at
                for invitation in session.scalars(select(InvitationRecord).where(InvitationRecord.membership_id == member.id)):
                    invitation.revoked_at = member.revoked_at
                call = session.get(CallRecord, encounter_id)
                if call and not call.ended:
                    call.ended = True
                    call.manual_pause = True
                    call.revision += 1
                view = EncounterView.model_validate(record.projection)
                view.consent_epoch += 1
                view.updated_at = utc_now()
                record.projection = view.model_dump(mode="json")
                record.updated_at = view.updated_at
        return authorized_view(db, request.cookies.get(COOKIE), encounter_id)

    application.include_router(call_router(db,settings,mutation))
    application.include_router(understanding_router(db,settings,mutation))
    application.include_router(speech_router(db,settings,mutation))
    application.include_router(execution_router(db,settings,mutation))
    application.include_router(continuity_router(db,settings,mutation))
    application.include_router(circle_router(db,settings,mutation))
    application.include_router(feasibility_router(db,settings,mutation))
    return application


app = create_app()
