"""Joining a visit by telephone.

A patient issues a single-use, short-lived PIN for one invited person (or herself). The phone
bridge reports the PIN and the participant identity it created; the caller's number is never
used. The PIN binds the call to that membership and role. Keypad: 1 agree, 2 decline,
9 pause Vene, 0 resume (the patient's own line only, and only when everyone agreed).
Real telephony needs a LiveKit SIP trunk and test credentials; this module is the visit side.
"""
import hashlib
import secrets
from datetime import timedelta
from uuid import uuid4
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from bring_vene.domain.service import DomainError, utc_now
from bring_vene.execution.service import access, patient
from bring_vene.persistence.models import CallConnectionRecord, CallRecord, DialPinRecord, MembershipRecord
from bring_vene.dial.contracts import BridgeAdmitted, KeypadResult, PinIssued

PIN_MINUTES = 15


def digest(pin):
    return hashlib.sha256(('bring-vene-dial:' + pin).encode()).hexdigest()


def issue(engine, visit_id, token, csrf, request, settings):
    with Session(engine) as session, session.begin():
        _, view, member, _ = access(session, visit_id, token, csrf)
        patient(member)
        target = session.get(MembershipRecord, request.membership_id, populate_existing=True)
        if not target or target.encounter_id != visit_id or target.revoked_at:
            raise DomainError(404, 'Participant not found.')
        now = utc_now()
        for old in session.scalars(select(DialPinRecord).where(DialPinRecord.membership_id == target.id,
                                                               DialPinRecord.used_at.is_(None), DialPinRecord.revoked_at.is_(None))):
            old.revoked_at = now  # one live PIN per person
        while True:
            pin = f'{secrets.randbelow(10**6):06d}'
            hashed = digest(pin)
            prior = session.scalar(select(DialPinRecord).where(DialPinRecord.pin_hash == hashed))
            if not prior:
                break
            if prior.used_at or prior.revoked_at or prior.expires_at <= now:
                session.execute(delete(DialPinRecord).where(DialPinRecord.id == prior.id))
                session.flush()
                break
        expires = now + timedelta(minutes=PIN_MINUTES)
        session.add(DialPinRecord(id=uuid4(), encounter_id=visit_id, membership_id=target.id, pin_hash=hashed,
                                  expires_at=expires, created_at=now))
        return PinIssued(pin=pin, expires_at=expires, dial_number=settings.phone_dial_number or None, name=target.name)


def bridge(settings, authorization):
    if not settings.phone_bridge_token or not secrets.compare_digest(authorization or '', 'Bearer ' + settings.phone_bridge_token):
        raise DomainError(403, 'Phone bridge access denied.')


def admit(engine, settings, authorization, request):
    bridge(settings, authorization)
    from bring_vene.voice.service import bump, configured, lock, room_name
    from bring_vene.room.service import disclosure
    with Session(engine) as session, session.begin():
        row = session.scalar(select(DialPinRecord).where(DialPinRecord.pin_hash == digest(request.pin)).with_for_update())
        if not row or row.used_at or row.revoked_at or row.expires_at <= utc_now():
            raise DomainError(401, 'That PIN is not valid.')
        member = session.get(MembershipRecord, row.membership_id, populate_existing=True)
        if not member or member.revoked_at:
            raise DomainError(401, 'That PIN is not valid.')
        if not configured(settings):
            raise DomainError(503, 'The call service is not configured.')
        encounter, call = lock(session, row.encounter_id)
        if not call or call.ended:
            raise DomainError(409, 'The visit conversation has not started.')
        row.used_at = utc_now()
        connection = CallConnectionRecord(id=uuid4(), encounter_id=row.encounter_id, generation=call.generation,
            membership_id=member.id, session_hash=None, dial_pin_id=row.id, present=False, consent='pending', track_epoch=0,
            expires_at=utc_now() + timedelta(hours=4), retired=False, channel='phone',
            external_identity=request.participant_identity)
        session.add(connection)
        call.manual_pause = True
        session.flush()
        bump(encounter, call)
        patient_name = encounter.projection['patient']['preferred_name']
        return BridgeAdmitted(connection_id=connection.id, room=room_name(call), name=member.name,
            announcement=disclosure(patient_name),
            prompt='Press 1 to let Vene listen, or 2 to keep this a human conversation. Press 9 at any time to pause Vene.')


def keypad(engine, visit_id, generation, participant_identity, digit, settings):
    """A DTMF digit from a phone participant already in the visit room."""
    from bring_vene.voice.service import bump, connections, lock, valid_connection
    from bring_vene.room.service import gate_open
    with Session(engine) as session, session.begin():
        encounter, call = lock(session, visit_id)
        if not call or call.generation != generation or call.ended:
            return KeypadResult(accepted=False, spoken='This visit conversation has ended.')
        connection = next((c for c in connections(session, call) if c.channel == 'phone'
                           and c.external_identity == participant_identity), None)
        if not connection or not valid_connection(session, connection):
            return KeypadResult(accepted=False, spoken='This phone is not part of the visit.')
        member = session.get(MembershipRecord, connection.membership_id)
        if digit in {'1', '2'}:
            connection.consent = 'agreed' if digit == '1' else 'declined'
            call.manual_pause = True
            bump(encounter, call)
            return KeypadResult(accepted=True, spoken='Thank you. Vene may listen when the patient resumes it.' if digit == '1'
                                else 'Understood. Vene will not process this conversation.')
        if digit == '9':
            # Anyone can pause; pausing stops processing, not only the voice.
            call.manual_pause = True
            bump(encounter, call)
            return KeypadResult(accepted=True, spoken='Vene is paused.')
        if digit == '0':
            humans = [c for c in connections(session, call) if c.present]
            if member.role != 'patient':
                return KeypadResult(accepted=False, spoken='Only the patient can resume Vene.')
            if not humans or not all(valid_connection(session, c) and c.consent == 'agreed' for c in humans) or not gate_open(session, visit_id):
                return KeypadResult(accepted=False, spoken='Everyone needs to agree before Vene can listen.')
            call.manual_pause = False
            bump(encounter, call)
            return KeypadResult(accepted=True, spoken='Vene is listening again.')
        return KeypadResult(accepted=False, spoken='Press 1 to agree, 2 to decline, 9 to pause, or 0 to resume.')
