"""Open loops from this prototype's records. Every rule is deterministic and cites a stored source."""
import re
from datetime import timedelta
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from bring_vene.domain.contracts import EncounterView
from bring_vene.domain.service import utc_now
from bring_vene.execution import errands
from bring_vene.persistence.models import EncounterRecord, ExecutionRecord, MemoryOutcomeRecord
from bring_vene.memory.port import OpenLoop, PastVisit, Source

NOUNS = {'lab': 'lab work', 'imaging': 'imaging', 'referral': 'referral', 'prescription': 'prescription'}
OPEN_ERRAND_STATES = {'queued', 'in_flight', 'unknown'}
# Office messages that say something is still waiting on someone.
WAITING = re.compile(r'\b(waiting for|needs? a new prescription|still pending|has not received|before we can)\b', re.I)
MESSAGE_KIND = [(re.compile(r'\b(prescription|refill|pharmacy)\b', re.I), 'prescription'),
                (re.compile(r'\breferral\b', re.I), 'referral'), (re.compile(r'\b(lab|blood)\b', re.I), 'lab'),
                (re.compile(r'\b(mri|imaging|scan)\b', re.I), 'imaging')]
MESSAGE_WINDOW = timedelta(days=60)


def short_date(value):
    return value.strftime('%b ') + str(value.day)


def source(encounter_id, evidence):
    return Source(id=evidence.id, encounter_id=encounter_id, title=evidence.title, text=evidence.text,
                  observed_at=evidence.observed_at, source_type=evidence.source_type)


class PostgresMemory:
    def encounters(self, session, patient_id):
        rows = session.scalars(select(EncounterRecord).where(
            EncounterRecord.projection['patient']['id'].astext == str(patient_id))).all()
        return [(row, EncounterView.model_validate(row.projection)) for row in rows]

    def history(self, session, patient_id, before):
        return sorted((PastVisit(id=view.id, title=view.title, visit_at=view.visit_at)
                       for _, view in self.encounters(session, patient_id) if view.visit_at < before),
                      key=lambda visit: visit.visit_at, reverse=True)

    def record_outcome(self, session, patient_id, key, outcome, encounter_id):
        session.execute(insert(MemoryOutcomeRecord).values(patient_id=patient_id, loop_key=key, outcome=outcome,
            encounter_id=encounter_id, recorded_at=utc_now()).on_conflict_do_update(
            index_elements=['patient_id', 'loop_key'], set_={'outcome': outcome, 'encounter_id': encounter_id,
                                                            'recorded_at': utc_now()}))

    def open_loops(self, session, patient_id, as_of):
        visits = self.encounters(session, patient_id)
        ids = [view.id for _, view in visits]
        actions = session.scalars(select(ExecutionRecord).where(ExecutionRecord.encounter_id.in_(ids))).all() if ids else []
        recorded = {row.loop_key for row in session.scalars(select(MemoryOutcomeRecord).where(
            MemoryOutcomeRecord.patient_id == patient_id))}
        answered = {p.loop_key for _, view in visits for p in view.priorities if p.loop_key and p.status == 'answered'}

        def completed_later(kind, since):
            # A later confirmed errand of the same kind closes an earlier unfinished one.
            return any(a.state == 'confirmed' and a.content.get('kind', 'lab') == kind and a.created_at > since for a in actions)

        loops = []
        for _, view in visits:
            evidence = {e.id: e for e in view.evidence}
            past = view.visit_at < as_of
            for item in view.plan if past else []:
                errand = errands.for_item(item)
                if not errand or errand.kind not in NOUNS:
                    continue
                if any(a.item_id == item.id and a.state == 'confirmed' for a in actions):
                    continue
                if completed_later(errand.kind, view.visit_at):
                    continue
                cited = [source(view.id, evidence[r]) for r in item.evidence_refs if r in evidence]
                loops.append(OpenLoop(key='plan:' + str(item.id), rule='unfinished_step', since=view.visit_at, sources=cited,
                    question='What should happen with the ' + NOUNS[errand.kind] + ' from ' + short_date(view.visit_at) + '?',
                    detail=item.title + ' was planned at your ' + short_date(view.visit_at) + ' visit and has not been completed.'))
            for priority in view.priorities if past else []:
                if not priority.selected or priority.status not in {'open', 'partly_answered'}:
                    continue
                cited = [source(view.id, evidence[r]) for r in priority.evidence_refs if r in evidence]
                loops.append(OpenLoop(key='priority:' + str(priority.id), rule='unanswered_question', since=view.visit_at,
                    sources=cited, question=priority.title,
                    detail='You asked this at your ' + short_date(view.visit_at) + ' visit and it was not answered.'))
            for e in view.evidence:
                if e.source_type != 'office_message' or not WAITING.search(e.text):
                    continue
                if not (as_of - MESSAGE_WINDOW <= e.observed_at <= as_of):
                    continue
                kind = next((k for pattern, k in MESSAGE_KIND if pattern.search(e.title + ' ' + e.text)), None)
                if kind and completed_later(kind, e.observed_at):
                    continue
                title = e.title[0].lower() + e.title[1:]
                loops.append(OpenLoop(key='evidence:' + str(e.id), rule='office_waiting', since=e.observed_at,
                    sources=[source(view.id, e)], question='Can we sort out the ' + title + '?',
                    detail='An office said something is still waiting (' + short_date(e.observed_at) + ').'))
            for action in actions:
                if action.encounter_id != view.id or not past or action.state not in OPEN_ERRAND_STATES:
                    continue
                errand = errands.for_action(action.content)
                loops.append(OpenLoop(key='action:' + str(action.id), rule='unknown_completion', since=action.created_at,
                    sources=[source(view.id, evidence[r]) for r in next((p.evidence_refs for p in view.plan if p.id == action.item_id), [])
                             if r in evidence],
                    question='Did the ' + errand.place + ' confirm ' + action.content['title'].lower() + '?',
                    detail='The request was sent on ' + short_date(action.created_at) + ' but completion was never confirmed.'))
        # Every proposal must cite at least one stored source; resolved loops never return.
        unique = {}
        for loop in loops:
            if loop.sources and loop.key not in recorded and loop.key not in answered:
                unique.setdefault(loop.key, loop)
        return sorted(unique.values(), key=lambda loop: loop.since)
