"""Preparation drafted from open loops. Patient-only; carrying a loop creates a private draft question."""
from uuid import uuid5
from sqlalchemy.orm import Session
from bring_vene.domain.contracts import Evidence, Priority
from bring_vene.domain.service import DomainError, utc_now
from bring_vene.execution.service import access, patient
from bring_vene.persistence.models import EvidenceRecord
from bring_vene.memory.contracts import LoopSource, LoopView, MemoryView
from bring_vene.memory.postgres import PostgresMemory, short_date

memory = PostgresMemory()


def age(days):
    if days < 14:
        return 'today' if days <= 0 else str(days) + ' day' + ('s' if days != 1 else '') + ' ago'
    if days < 60:
        return str(days // 7) + ' weeks ago'
    return str(days // 30) + ' months ago'


def listed(view, loop):
    """Already on this visit's list: carried before, or the same office message is already cited."""
    cited = {ref for p in view.priorities for ref in p.evidence_refs}
    return any(p.loop_key == loop.key for p in view.priorities) or any(
        s.id in cited and s.encounter_id == view.id for s in loop.sources)


def current(session, view):
    loops = memory.open_loops(session, view.patient.id, view.visit_at)
    fresh = [loop for loop in loops if not listed(view, loop)]
    return fresh, len(loops) - len(fresh)


def state(engine, visit_id, token):
    with Session(engine) as session, session.begin():
        _, view, member, _ = access(session, visit_id, token)
        patient(member)
        fresh, already = current(session, view)
        visits = {v.id: v for v in memory.history(session, view.patient.id, view.visit_at)}
        loops = []
        for loop in fresh:
            days = (view.visit_at - loop.since).days
            loops.append(LoopView(key=loop.key, rule=loop.rule, question=loop.question, detail=loop.detail, days=days, age=age(days),
                sources=[LoopSource(title=s.title, text=s.text, observed_at=s.observed_at,
                    from_visit='This visit' if s.encounter_id == view.id else
                    visits[s.encounter_id].title if s.encounter_id in visits else 'An earlier record') for s in loop.sources]))
        return MemoryView(loops=loops, already_listed=already, past_visits=len(visits))


def carry(engine, visit_id, token, csrf, request):
    with Session(engine) as session, session.begin():
        encounter, view, member, _ = access(session, visit_id, token, csrf)
        patient(member)
        fresh = {loop.key: loop for loop in current(session, view)[0]}
        chosen = [fresh[key] for key in dict.fromkeys(request.keys) if key in fresh]
        if not chosen:
            raise DomainError(409, 'These items changed. Review them again.')
        if len(view.priorities) + len(chosen) > 20:
            raise DomainError(409, 'This visit has reached its question limit.')
        for loop in chosen:
            refs = []
            for s in loop.sources:
                # A private copy in this visit, so the source can be read and shared on its own terms.
                copy_id = uuid5(view.id, 'memory/' + str(s.id))
                if not any(e.id == copy_id for e in view.evidence):
                    # Typed as an imported record so the copy is never mistaken for a new office message.
                    copied = Evidence(id=copy_id, source_type='imported_record',
                        title='From ' + short_date(s.observed_at) + ' · ' + s.title, text=s.text, observed_at=s.observed_at,
                        origin='human', audiences=[])
                    view.evidence.append(copied)
                    session.add(EvidenceRecord(id=copy_id, encounter_id=view.id, content=copied.model_dump(mode='json')))
                refs.append(copy_id)
            # Default audience is the clinician, visible only after the patient approves the list; never family.
            view.priorities.append(Priority(id=uuid5(view.id, 'loop/' + loop.key), title=loop.question[:160], detail=loop.detail,
                selected=True, status='open', evidence_refs=refs, approved=False, audiences=['clinician'], loop_key=loop.key))
        view.preparation_approved = False
        for priority in view.priorities:
            priority.approved = False
        view.version += 1
        view.consent_epoch += 1
        view.updated_at = utc_now()
        encounter.projection = view.model_dump(mode='json')
        encounter.version = view.version
        encounter.updated_at = view.updated_at


def outcome(engine, visit_id, token, csrf, request):
    with Session(engine) as session, session.begin():
        _, view, member, _ = access(session, visit_id, token, csrf)
        patient(member)
        loops = {loop.key for loop in memory.open_loops(session, view.patient.id, view.visit_at)}
        if request.key not in loops:
            raise DomainError(404, 'This item is no longer open.')
        memory.record_outcome(session, view.patient.id, request.key, request.outcome, view.id)
