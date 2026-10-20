"""Care-circle asks: the patient asks a family member for practical help with a confirmed errand.

The family member receives only what the ask is for, when and where. Their answer is their
own commitment; it is not a booking, a ride reservation or a change to the plan.
"""
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.domain.context import context_adapter
from bring_vene.domain.service import DomainError, utc_now
from bring_vene.execution.service import access, patient, receipt_current
from bring_vene.persistence.models import CareCircleRequestRecord, ExecutionRecord, MembershipRecord
from bring_vene.circle.contracts import CircleView, RideView

OPEN = {'asked', 'accepted'}


def details(view, action, recipient):
    """The ask's fields, or None when this person may not see the step or nothing is confirmed."""
    if not recipient or recipient.role != 'family' or recipient.revoked_at or recipient.encounter_id != view.id:
        return None
    visible = {item.id: item for item in context_adapter.view(view, 'family', recipient.id).plan}
    item = visible.get(action.item_id)
    slot = action.content.get('slot') or {}
    receipt = action.content.get('receipt') or {}
    if not item or action.state != 'confirmed' or receipt.get('status') != 'confirmed' or not slot:
        return None
    if not receipt_current(view, action):
        return None
    day, time = (slot['label'].split(' · ') + ['', ''])[:2]
    return {'purpose': item.title, 'when': day + (' · ' + time if time else ''), 'where': slot['location'] + ' (fictional)',
            'receipt_id': receipt.get('receipt_id')}


def still_valid(session, view, row):
    action = session.get(ExecutionRecord, row.action_id)
    recipient = session.get(MembershipRecord, row.recipient_id, populate_existing=True)
    fields = details(view, action, recipient) if action else None
    return bool(fields) and all(fields[key] == row.content[key] for key in ('purpose', 'when', 'where', 'receipt_id'))


def ask(engine, visit_id, token, csrf, request):
    with Session(engine) as session, session.begin():
        _, view, member, credential = access(session, visit_id, token, csrf); patient(member)
        action = session.get(ExecutionRecord, request.action_id)
        recipient = session.get(MembershipRecord, request.recipient_id, populate_existing=True)
        if not action or action.encounter_id != visit_id:
            raise DomainError(404, 'Next step not found.')
        fields = details(view, action, recipient)
        if not fields:
            raise DomainError(409, 'Ask after the reservation is confirmed, and share this step and its sources with this person first.')
        existing = session.scalar(select(CareCircleRequestRecord).where(CareCircleRequestRecord.action_id == action.id,
            CareCircleRequestRecord.recipient_id == recipient.id, CareCircleRequestRecord.state.in_(OPEN)))
        if existing:
            return existing.id
        row = CareCircleRequestRecord(id=uuid4(), encounter_id=visit_id, action_id=action.id, recipient_id=recipient.id,
            session_hash=credential.token_hash, state='asked', content=fields, created_at=utc_now())
        session.add(row)
        return row.id


def withdraw(engine, visit_id, request_id, token, csrf):
    with Session(engine) as session, session.begin():
        _, _, member, _ = access(session, visit_id, token, csrf); patient(member)
        row = session.get(CareCircleRequestRecord, request_id)
        if not row or row.encounter_id != visit_id:
            raise DomainError(404, 'Request not found.')
        if row.state in OPEN:
            row.state = 'withdrawn'


def answer(engine, visit_id, request_id, token, csrf, request):
    with Session(engine) as session, session.begin():
        _, view, member, _ = access(session, visit_id, token, csrf)
        row = session.get(CareCircleRequestRecord, request_id)
        # A request addressed to someone else is indistinguishable from a missing one.
        if not row or row.encounter_id != visit_id or row.recipient_id != member.id:
            raise DomainError(404, 'Request not found.')
        if row.state not in {'asked', 'accepted', 'declined'} or not still_valid(session, view, row):
            raise DomainError(409, 'This request changed or was withdrawn.')
        row.state = 'accepted' if request.answer == 'yes' else 'declined'
        row.answered_at = utc_now()


def state(engine, visit_id, token):
    with Session(engine) as session, session.begin():
        _, view, member, _ = access(session, visit_id, token)
        if member.role == 'clinician':
            return CircleView(rides=[])
        query = select(CareCircleRequestRecord).where(CareCircleRequestRecord.encounter_id == visit_id)
        if member.role == 'family':
            query = query.where(CareCircleRequestRecord.recipient_id == member.id)
        rides = []
        for row in session.scalars(query.order_by(CareCircleRequestRecord.created_at.desc()).limit(30)):
            valid = still_valid(session, view, row)
            if member.role == 'family' and (not valid or row.state == 'withdrawn'):
                continue  # Absent from the payload, not merely hidden.
            recipient = session.get(MembershipRecord, row.recipient_id)
            shown = row.state if valid or row.state == 'withdrawn' else 'unavailable'
            rides.append(RideView(id=row.id, action_id=row.action_id, recipient_id=row.recipient_id,
                recipient_name=recipient.name if recipient else 'Former participant', purpose=row.content['purpose'],
                when=row.content['when'], where=row.content['where'], state=shown, answered_at=row.answered_at))
        return CircleView(rides=rides)
