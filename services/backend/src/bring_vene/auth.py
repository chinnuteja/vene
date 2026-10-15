import hashlib
import secrets
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from bring_vene.domain.contracts import Identity, Invitation
from bring_vene.domain.service import DomainError, utc_now
from bring_vene.persistence.models import EncounterRecord, InvitationRecord, MembershipRecord, SessionRecord

COOKIE = "vene_session"
FIXTURE_VISIT = UUID("10000000-0000-4000-8000-000000000001")
FIXTURE_MEMBERS = {role: UUID(f"50000000-0000-4000-8000-{index:012d}")
                   for index, role in enumerate(["patient", "clinician", "family"], 1)}


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def authenticate(session: Session, token: str | None, encounter_id=None, csrf=None, mutate=False, clock=utc_now):
    if not token or len(token) > 128:
        raise DomainError(401, "Your invitation is needed to open this visit.")
    credential = session.get(SessionRecord, digest(token), populate_existing=True)
    if not credential or credential.revoked_at or credential.expires_at <= clock():
        raise DomainError(401, "This session has ended. Ask for a new invitation.")
    member = session.get(MembershipRecord, credential.membership_id, populate_existing=True)
    if not member or member.revoked_at:
        raise DomainError(401, "Access to this visit has been withdrawn.")
    if encounter_id is not None and member.encounter_id != encounter_id:
        raise DomainError(404, "Visit not found.")
    if mutate and (not csrf or not secrets.compare_digest(csrf, credential.csrf_token)):
        raise DomainError(403, "Refresh this page before making a change.")
    return member, credential


def identity(member, credential):
    return Identity(membership_id=member.id, encounter_id=member.encounter_id, role=member.role,
                    name=member.name, csrf_token=credential.csrf_token)


def issue_invitation(session, member, clock=utc_now):
    if member.revoked_at:
        raise DomainError(409, "This person's access has been withdrawn.")
    token = secrets.token_urlsafe(32)
    invitation = InvitationRecord(id=uuid4(), membership_id=member.id, token_hash=digest(token),
                                  expires_at=clock() + timedelta(minutes=15))
    session.add(invitation)
    return Invitation(id=invitation.id, token=token, expires_at=invitation.expires_at)


def redeem(engine, token, hours=8, clock=utc_now):
    with Session(engine) as session, session.begin():
        # Lock encounter first, matching commands/revocation, then invitation. No lock inversion.
        invite = session.scalar(select(InvitationRecord).where(InvitationRecord.token_hash == digest(token)))
        if not invite:
            raise DomainError(401, "This invitation is no longer available.")
        member = session.get(MembershipRecord, invite.membership_id)
        session.scalar(select(EncounterRecord).where(EncounterRecord.id == member.encounter_id).with_for_update())
        invite = session.scalar(select(InvitationRecord).where(InvitationRecord.id == invite.id)
                                .with_for_update().execution_options(populate_existing=True))
        session.refresh(member)
        if invite.used_at or invite.revoked_at or invite.expires_at <= clock() or member.revoked_at:
            raise DomainError(401, "This invitation is no longer available.")
        invite.used_at = clock()
        cookie = secrets.token_urlsafe(32)
        credential = SessionRecord(token_hash=digest(cookie), membership_id=member.id,
                                   csrf_token=secrets.token_urlsafe(32), expires_at=clock() + timedelta(hours=hours))
        session.add(credential)
        return cookie, identity(member, credential)
