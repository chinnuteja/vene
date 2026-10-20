"""Practical checks while the conversation is still happening.

With the patient's standing read-only permission, discussed steps are checked against the
institution that handles them. Obstacles are derived deterministically from institution
responses (never from model output), fenced by the exact step version and permission
revision, and surfaced as private cues. Resolving one records a person's administrative
response; it never decides care. A prior-authorization submission still needs the
patient's own approval before anything is sent.
"""
import logging
import re
from datetime import datetime
from uuid import NAMESPACE_URL, uuid4, uuid5
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from bring_vene.domain.contracts import EncounterView, PlanItem
from bring_vene.domain.context import context_adapter
from bring_vene.domain.service import DomainError, utc_now
from bring_vene.execution import errands
from bring_vene.execution.gateway import OfficeGateway,for_run
from bring_vene.execution.service import access, patient, plan_fingerprint as execution_fingerprint
from bring_vene.persistence.models import (CallRecord, EncounterRecord, ExecutionRecord, ExecutionScopeRecord, FeasibilityCheckRecord,
    MembershipRecord, ObstacleRecord, SessionRecord, StandingCheckRecord)
from bring_vene.feasibility.contracts import (ChoiceView, FeasibilityView, ObstacleView, Resolution, StandingView)

log = logging.getLogger(__name__)


def plan_fingerprint(view,item_id):
    base=execution_fingerprint(view,item_id)
    item=next(p for p in view.plan if p.id==item_id)
    from bring_vene.feasibility.availability import deadline
    preference=view.lab_preference
    if item.kind=='lab' and not item.location and preference and deadline(item.timeframe,view.visit_at):
        from bring_vene.understanding.service import fingerprint
        source=next((e for e in view.evidence if e.id==preference.source_id),None)
        return fingerprint({'plan':base,'preference':preference.model_dump(mode='json'),
                            'source':source.model_dump(mode='json') if source else None})
    return base

# Which checks each errand kind gets, and which standing permission each check needs.
CHECKS = {'lab': ['availability'], 'imaging': ['availability', 'coverage'], 'prescription': ['coverage', 'stock'],
          'referral': ['document']}
PERMISSION = {'availability': 'scheduling', 'document': 'scheduling', 'coverage': 'coverage', 'stock': 'pharmacy'}
OBSTACLE_CHECK = {'no_slot_in_window': 'availability', 'prior_authorization_required': 'coverage',
                  'not_on_formulary': 'coverage', 'not_in_stock': 'stock', 'missing_supporting_document': 'document'}
RESOLVER = {'no_slot_in_window': 'patient', 'prior_authorization_required': 'clinician', 'not_on_formulary': 'clinician',
            'not_in_stock': 'patient', 'missing_supporting_document': 'clinician'}
CHOICES = {
    'prior_authorization_required': [('office_will_submit', 'The office will submit prior authorization'),
                                     ('review_later', "I'll review this after the visit")],
    'not_on_formulary': [('review_coverage', "I'll review coverage")],
    'no_slot_in_window': [('use_another_window', "We'll use another window")],
    'not_in_stock': [('choose_another_pharmacy', "I'll choose another pharmacy")],
    'missing_supporting_document': [('office_will_send', 'The office will send the referral packet')],
}
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def authority(session, standing):
    credential = session.get(SessionRecord, standing.session_hash, populate_existing=True)
    member = session.get(MembershipRecord, credential.membership_id, populate_existing=True) if credential else None
    return bool(credential and not credential.revoked_at and credential.expires_at > utc_now() and member and
                member.role == 'patient' and member.encounter_id == standing.encounter_id and not member.revoked_at)


def lock(session, visit_id):
    encounter = session.scalar(select(EncounterRecord).where(EncounterRecord.id == visit_id).with_for_update())
    if not encounter:
        raise DomainError(404, 'Visit not found.')
    return encounter, EncounterView.model_validate(encounter.projection)


def bump(encounter, view):
    # A permission change is a consent change: pending cues and speech re-check scope.
    view.consent_epoch += 1
    view.version += 1
    view.updated_at = utc_now()
    encounter.projection = view.model_dump(mode='json')
    encounter.version = view.version
    encounter.updated_at = view.updated_at


def wanted(view, standing):
    """(item, check kind, fingerprint) for every step the current permission covers."""
    allowed = set(standing.kinds)
    for item in view.plan:
        errand = errands.for_item(item)
        if not errand or errand.kind not in CHECKS:
            continue
        try:
            fp = plan_fingerprint(view, item.id)
        except DomainError:
            continue
        for kind in CHECKS[errand.kind]:
            if PERMISSION[kind] in allowed:
                yield item, kind, fp


def supersede(session, visit_id, keep):
    """Open obstacles whose step, version or permission no longer applies stop being current."""
    for row in session.scalars(select(ObstacleRecord).where(ObstacleRecord.encounter_id == visit_id,
                                                            ObstacleRecord.state == 'open')):
        if (row.item_id, OBSTACLE_CHECK[row.kind], row.content['plan_fingerprint']) not in keep:
            row.state = 'superseded'


# ---------------------------------------------------------------- patient permission

def set_standing(engine, visit_id, token, csrf, request):
    with Session(engine) as session, session.begin():
        encounter, view = lock(session, visit_id)
        _, _, member, credential = access(session, visit_id, token, csrf)
        patient(member)
        row = session.get(StandingCheckRecord, visit_id)
        if not row:
            row = StandingCheckRecord(encounter_id=visit_id, session_hash=credential.token_hash, kinds=[], revision=0,
                                      updated_at=utc_now())
            session.add(row)
        row.kinds = sorted(set(request.kinds))
        row.session_hash = credential.token_hash
        row.revision += 1
        row.updated_at = utc_now()
        # Queued or running checks under the previous revision are discarded when they return.
        keep = {(item.id, kind, fp) for item, kind, fp in wanted(view, row)}
        supersede(session, visit_id, keep)
        bump(encounter, view)


# ---------------------------------------------------------------- worker

def enqueue(engine):
    with Session(engine) as session, session.begin():
        for standing in session.scalars(select(StandingCheckRecord).where(StandingCheckRecord.kinds!=[])).all():
            encounter = session.get(EncounterRecord, standing.encounter_id)
            if not encounter:
                continue
            view = EncounterView.model_validate(encounter.projection)
            live = authority(session, standing) and standing.kinds
            current = list(wanted(view, standing)) if live else []
            supersede(session, view.id, {(item.id, kind, fp) for item, kind, fp in current})
            for item, kind, fp in current:
                session.execute(insert(FeasibilityCheckRecord).values(
                    id=uuid4(), encounter_id=view.id, item_id=item.id, kind=kind, plan_fingerprint=fp,
                    standing_revision=standing.revision, state='queued', created_at=utc_now(),
                    content={'source_observed_at': max((e.observed_at.isoformat() for e in view.evidence
                                                         if e.id in item.evidence_refs), default=None)})
                    .on_conflict_do_nothing())


def paused(session, visit_id):
    # Pausing Vene in a live call pauses these checks too; a silenced voice alone does not.
    call = session.get(CallRecord, visit_id, populate_existing=True)
    return bool(call and call.manual_pause and not call.ended)


def claim(engine):
    with Session(engine) as session, session.begin():
        held = select(CallRecord.encounter_id).where(CallRecord.manual_pause.is_(True), CallRecord.ended.is_(False))
        row = session.scalar(select(FeasibilityCheckRecord).where(FeasibilityCheckRecord.state == 'queued',
                             FeasibilityCheckRecord.encounter_id.not_in(held))
                             .order_by(FeasibilityCheckRecord.created_at).with_for_update(skip_locked=True).limit(1))
        if not row:
            return None
        encounter = session.get(EncounterRecord, row.encounter_id)
        view = EncounterView.model_validate(encounter.projection)
        item = next((p for p in view.plan if p.id == row.item_id), None)
        standing = session.get(StandingCheckRecord, row.encounter_id)
        # Re-check permission before anything leaves the service; a withdrawn or changed
        # permission discards queued work without a network call.
        if (not item or not standing or standing.revision != row.standing_revision or not authority(session, standing)
                or PERMISSION[row.kind] not in standing.kinds):
            row.state = 'stale'
            return 'skipped'
        row.state = 'running'
        row.content = {**row.content, 'started_at': utc_now().isoformat()}
        evidence = [e.text for e in view.evidence if e.id in item.evidence_refs]
        preference=view.lab_preference
        preferred=({'location':preference.location,'source_id':str(preference.source_id)} if preference and any(e.id==preference.source_id and preference.location in e.text
            for e in view.evidence) else None)
        return row.id, row.kind, item.model_copy(deep=True), evidence, view.coverage,view.visit_at,preferred,view.demo_run


def weekday(timeframe):
    for name in WEEKDAYS:
        if timeframe and re.search(r'\b' + name + r'\b', timeframe, re.I):
            return name
    return None


def medicine(gateway, item, evidence):
    names = gateway.call('/formulary')['names']
    text = ' '.join([item.title, item.detail, *evidence])
    return next((n for n in names if re.search(r'\b' + re.escape(n) + r'\b', text, re.I)), None)


def run(kind, item, evidence, coverage, gateway,visit_at=None,preferred_lab=None):
    """One read-only check. Returns (result facts, obstacle or None). Network only, no locks held."""
    errand = errands.for_item(item)
    location = item.location if item.location in errand.locations else errand.locations[0]
    if kind == 'availability':
        if errand.kind=='lab' and visit_at:
            from bring_vene.feasibility.availability import check,deadline
            if deadline(item.timeframe,visit_at):
                stated=item.location in errand.locations
                preferred=item.location if stated else preferred_lab['location'] if preferred_lab else None
                if not preferred:return {'applicable':False,'reason':'The preferred lab needs clarification.'},None
                facts,obstacle=check(item,visit_at,gateway,preferred)
                if obstacle and not stated:obstacle['supporting_sources']=[preferred_lab['source_id']]
                return facts,obstacle
        day_name = weekday(item.timeframe)
        if not day_name:
            return {'applicable': False, 'reason': 'No weekday was stated for this step.'}, None
        windows = ['afternoon'] if re.search(r'afternoon', item.timeframe, re.I) else ['morning'] if re.search(
            r'morning', item.timeframe, re.I) else ['morning', 'afternoon']
        days = [day for day, label in errand.days if label.startswith(day_name[:3])]
        found = []
        for day in days:
            for window in windows:
                payload = {'window': window, 'location': location, 'day': day}
                if errand.institution != 'lab':
                    payload['institution'] = errand.institution
                if gateway.call('/lookup', payload).get('slot'):
                    found.append(day + ':' + window)
        facts = {'applicable': True, 'weekday': day_name, 'location': location, 'offered': found}
        if found:
            return facts, None
        return facts, {'kind': 'no_slot_in_window', 'source': 'Fictional ' + location + ' · sandbox ' + errand.place,
            'fact': 'The sandbox ' + errand.place + ' shows no ' + day_name + ' availability at ' + location + '.',
            'spoken': 'The sandbox ' + errand.place + ' shows no ' + day_name + ' availability at ' + location +
                      '. Could we agree on another window?'}
    if kind == 'coverage':
        if not coverage:
            return {'applicable': False, 'reason': 'No plan membership is on file.'}, None
        name = medicine(gateway, item, evidence) if errand.kind == 'prescription' else None
        if errand.kind == 'prescription' and not name:
            return {'applicable': False, 'reason': 'No medicine from the plan formulary was identified.'}, None
        result = gateway.call('/coverage', {'member_ref': coverage.member_ref, 'service': errand.kind,
                                            **({'medicine': name} if name else {})})
        source = result['plan'] + ' · sandbox health plan'
        facts = {'applicable': True, 'reference': result['reference'], 'plan': result['plan'],
                 'prior_authorization_required': result['prior_authorization_required'],
                 'formulary': result['formulary'], 'alternatives': result['alternatives']}
        if errand.kind == 'imaging' and result['prior_authorization_required']:
            return facts, {'kind': 'prior_authorization_required', 'source': source,
                'fact': result['plan'] + ' requires prior authorization for this imaging.',
                'spoken': 'The sandbox health plan says this imaging needs prior authorization. '
                          'Could the office submit it before we finish?'}
        if errand.kind == 'prescription' and result['formulary'] == 'not_covered':
            # Plan-listed alternatives travel as a separate, labelled field, never inside the spoken text.
            return facts, {'kind': 'not_on_formulary', 'source': source, 'alternatives': result['alternatives'],
                'fact': result['plan'] + ' does not list ' + name + ' as covered. The clinician decides whether any change is appropriate.',
                'spoken': 'The sandbox health plan does not list this prescription as covered. '
                          'Could we look at coverage before we finish?'}
        return facts, None
    if kind == 'stock':
        name = medicine(gateway, item, evidence)
        if not name:
            return {'applicable': False, 'reason': 'No medicine from the plan formulary was identified.'}, None
        result = gateway.call('/stock', {'medicine': name, 'location': location})
        facts = {'applicable': True, 'reference': result['reference'], 'in_stock': result['in_stock'], 'location': location}
        if result['in_stock']:
            return facts, None
        return facts, {'kind': 'not_in_stock', 'source': 'Fictional ' + location + ' · sandbox pharmacy',
            'fact': location + ' reports this prescription is not in stock.',
            'spoken': location + ' reports this prescription is not in stock. Could we choose another pharmacy?'}
    if kind == 'document':
        result = gateway.call('/requirements')
        return {'applicable': True, 'reference': result['reference'], 'requires': result['requires'],
                'location': location}, 'needs_document'
    raise ValueError('Unknown check kind')


def finish(engine, settings, check_id, outcome):
    """Commit a result only if the step, its version and the permission are unchanged."""
    with Session(engine) as session, session.begin():
        row = session.get(FeasibilityCheckRecord, check_id)
        if not row or row.state != 'running':
            return
        encounter, view = lock(session, row.encounter_id)
        standing = session.get(StandingCheckRecord, row.encounter_id)
        item = next((p for p in view.plan if p.id == row.item_id), None)
        current = bool(item and standing and standing.revision == row.standing_revision and authority(session, standing)
                       and PERMISSION[row.kind] in standing.kinds and not paused(session, row.encounter_id))
        try:
            current = current and plan_fingerprint(view, row.item_id) == row.plan_fingerprint
        except DomainError:
            current = False
        now = utc_now()
        row.finished_at = now
        if not current:
            row.state = 'stale'
            row.content = {**row.content, 'discarded': 'The step or permission changed while the check ran.'}
            return
        if outcome is None:
            row.state = 'failed'
            row.content = {**row.content, 'message': 'The sandbox did not return a verified result.'}
            return
        facts, obstacle = outcome
        if obstacle == 'needs_document':
            # Known to Vene: whether this office has issued the specialist's required packet.
            issued = any(a.content.get('order_id') for a in session.scalars(select(ExecutionRecord).where(
                ExecutionRecord.encounter_id == view.id, ExecutionRecord.item_id == item.id)))
            location = facts['location']
            obstacle = None if issued else {'kind': 'missing_supporting_document', 'source': 'Fictional ' + location + ' · sandbox specialist office',
                'fact': location + ' needs a referral packet from this office before it can offer an appointment.',
                'spoken': location + ' needs a referral packet from this office before it can offer an appointment. '
                          'Could the office send it?'}
        row.state = 'done'
        row.content = {**row.content, 'result': facts}
        if not obstacle:
            return
        already = session.scalar(select(ObstacleRecord).where(
            ObstacleRecord.encounter_id == view.id, ObstacleRecord.item_id == item.id, ObstacleRecord.kind == obstacle['kind'],
            ObstacleRecord.content['plan_fingerprint'].astext == row.plan_fingerprint,
            ObstacleRecord.state.in_(['open', 'resolved'])))
        if already:
            return  # A person already has this exact fact; re-checking does not reopen it.
        timings = {'source_observed_at': row.content.get('source_observed_at'), 'check_started_at': row.content.get('started_at'),
                   'check_finished_at': now.isoformat()}
        record = ObstacleRecord(id=uuid4(), encounter_id=view.id, item_id=item.id, check_id=row.id, kind=obstacle['kind'],
            state='open', created_at=now, content={**obstacle, 'plan_fingerprint': row.plan_fingerprint,
                                                   'checked_at': now.isoformat(), 'timings': timings})
        session.add(record)
        session.flush()
        from bring_vene.speech import service as speech
        speech.obstacle_cue(session, view.id, record, settings)


def tick(engine, settings, gateway=None):
    try:
        enqueue(engine)
    except Exception as error:
        log.warning('Feasibility enqueue unavailable (%s)', type(error).__name__)
        return False
    claimed = claim(engine)
    if not claimed:
        return False
    if claimed == 'skipped':
        return True
    check_id, kind, item, evidence, coverage,visit_at,preferred_lab,sandbox_run = claimed
    try:
        outcome = run(kind, item, evidence, coverage, gateway or for_run(settings,sandbox_run),visit_at,preferred_lab)
    except Exception as error:
        # Type only: never log request fields, credentials or provider bodies.
        log.warning('Feasibility check failed (%s)', type(error).__name__)
        outcome = None
    finish(engine, settings, check_id, outcome)
    return True


# ---------------------------------------------------------------- views and resolution

def present(session, view, row, member):
    item = next((p for p in view.plan if p.id == row.item_id), None)
    resolver = RESOLVER[row.kind]
    choices = [ChoiceView(id=c, label=label) for c, label in CHOICES[row.kind]] if (
        row.state == 'open' and member.role == resolver) else []
    return ObstacleView(id=row.id, item_id=row.item_id, item_title=item.title if item else 'Changed step', kind=row.kind,
        state=row.state, fact=row.content['fact'], source=row.content['source'],
        checked_at=datetime.fromisoformat(row.content['checked_at']), resolver=resolver,
        plan_alternatives=row.content.get('alternatives', []), choices=choices,
        resolution=Resolution.model_validate(row.content['resolution']) if row.content.get('resolution') else None,
        alternative=row.content.get('alternative'),supporting_sources=row.content.get('supporting_sources',[]),
        expires_at=row.content.get('expires_at'))


def state(engine, visit_id, token):
    with Session(engine) as session, session.begin():
        _, view, member, _ = access(session, visit_id, token)
        if member.role == 'family':
            return FeasibilityView(obstacles=[])
        visible = {p.id for p in context_adapter.view(view, member.role, member.id).plan}
        rows = session.scalars(select(ObstacleRecord).where(ObstacleRecord.encounter_id == visit_id,
            ObstacleRecord.state.in_(['open', 'resolved'])).order_by(ObstacleRecord.created_at.desc()).limit(20)).all()
        obstacles = []
        for row in rows:
            try:
                if plan_fingerprint(view,row.item_id)!=row.content['plan_fingerprint']:continue
            except DomainError:continue
            if member.role != 'patient':
                # A guest sees an obstacle only for a step and sources shared with them, at the same version.
                try:
                    visible_sources={str(e.id) for e in context_adapter.view(view,member.role,member.id).evidence}
                    shared = (row.item_id in visible and plan_fingerprint(view, row.item_id) == row.content['plan_fingerprint'] and
                              set(row.content.get('supporting_sources',[]))<=visible_sources)
                except DomainError:
                    shared = False
                if not shared:
                    continue
            obstacles.append(present(session, view, row, member))
        if member.role != 'patient':
            return FeasibilityView(obstacles=obstacles)
        standing = session.get(StandingCheckRecord, visit_id)
        checking = len(session.scalars(select(FeasibilityCheckRecord.id).where(
            FeasibilityCheckRecord.encounter_id == visit_id, FeasibilityCheckRecord.state.in_(['queued', 'running']))).all())
        current=set((item.id,kind,fp) for item,kind,fp in wanted(view,standing)) if standing else set()
        failed=sum(1 for check in session.scalars(select(FeasibilityCheckRecord).where(
            FeasibilityCheckRecord.encounter_id==visit_id,FeasibilityCheckRecord.state=='failed'))
            if standing and check.standing_revision==standing.revision and (check.item_id,check.kind,check.plan_fingerprint) in current)
        return FeasibilityView(standing=StandingView(kinds=standing.kinds if standing else [],
            active=bool(standing and standing.kinds and authority(session, standing))), checking=checking, failed=failed,obstacles=obstacles)


def authorization_item_id(view, item_id):
    return uuid5(NAMESPACE_URL, str(view.id) + '/authorization/' + str(item_id))


def resolve(engine, visit_id, obstacle_id, token, csrf, request, settings, gateway=None):
    with Session(engine) as session, session.begin():
        encounter, view = lock(session, visit_id)
        _, _, member, _ = access(session, visit_id, token, csrf)
        row = session.get(ObstacleRecord, obstacle_id)
        if not row or row.encounter_id != visit_id:
            raise DomainError(404, 'Obstacle not found.')
        visible = {p.id for p in context_adapter.view(view, member.role, member.id).plan}
        if member.role == 'family' or row.item_id not in visible:
            raise DomainError(404, 'Obstacle not found.')
        if member.role != RESOLVER[row.kind]:
            raise DomainError(403, 'This needs the ' + RESOLVER[row.kind] + "'s response.")
        if row.state != 'open':
            raise DomainError(409, 'This obstacle changed or was already answered.')
        labels = dict(CHOICES[row.kind])
        if request.choice not in labels:
            raise DomainError(422, 'Choose one of the listed responses.')
        if plan_fingerprint(view, row.item_id) != row.content['plan_fingerprint']:
            raise DomainError(409, 'This obstacle changed or was already answered.')
        row.state = 'resolved'
        row.resolved_at = utc_now()
        row.content = {**row.content, 'resolution': {'choice': request.choice, 'label': labels[request.choice],
            'by_role': member.role, 'by_name': member.name, 'at': row.resolved_at.isoformat()}}
        open_authorization = request.choice == 'office_will_submit'
        if open_authorization:
            standing = session.get(StandingCheckRecord, visit_id)
            if not standing or not authority(session, standing):
                raise DomainError(409, 'The patient needs to renew permission for coverage checks first.')
            source = next(p for p in view.plan if p.id == row.item_id)
            auth_id = authorization_item_id(view, row.item_id)
            if not any(p.id == auth_id for p in view.plan):
                view.plan.append(PlanItem(id=auth_id, title='Prior authorization for ' + source.title.lower().removeprefix('schedule '),
                    detail=member.name + ' said the office will submit prior authorization to the plan. The plan decides.',
                    owner=member.name + "'s office", timeframe='Before the imaging', status='waiting',
                    evidence_refs=list(source.evidence_refs), origin='resolution', kind='authorization',
                    needs_clarification=False, audiences=['clinician'],
                    explanation='Created from the clinician’s response. Submitting it still needs your approval.'))
                encounter.projection = view.model_dump(mode='json')
            scope = session.get(ExecutionScopeRecord, (visit_id, auth_id))
            if not scope:
                session.add(ExecutionScopeRecord(encounter_id=visit_id, item_id=auth_id, session_hash=standing.session_hash,
                                                 revision=1, allowed=True))
            clinician_id = member.id
        bump(encounter, view)
    if open_authorization:
        open_review(engine, visit_id, auth_id, clinician_id, settings, gateway)


def open_review(engine, visit_id, auth_id, clinician_id, settings, gateway=None):
    """Prepare (not send) the plan submission: a review slot and the office's authorization request."""
    from bring_vene.execution import service as execution
    with Session(engine) as session, session.begin():
        _, view = execution.lock(session, visit_id)
        current_fingerprint=plan_fingerprint(view,auth_id)
        prior=session.scalars(select(ExecutionRecord).where(ExecutionRecord.encounter_id==visit_id,
                                                          ExecutionRecord.item_id==auth_id)).all()
        if any(a.state in {'in_flight','unknown'} for a in prior):
            raise DomainError(409,'Reconcile the existing health-plan submission before starting another.')
        if any(a.content['plan_fingerprint']==current_fingerprint and a.state in {'checking','suggested','queued','confirmed'} for a in prior):
            return
        scope = session.get(ExecutionScopeRecord, (visit_id, auth_id))
        action = ExecutionRecord(id=uuid4(), encounter_id=visit_id, item_id=auth_id, state='checking', created_at=utc_now(),
            content={'kind': 'authorization', 'title': next(p.title for p in view.plan if p.id == auth_id), 'window': 'morning',
                     'plan_fingerprint': plan_fingerprint(view, auth_id), 'location': 'Evergreen Health Plan', 'day': '2026-10-15',
                     'scope_revision': scope.revision, 'session_hash': scope.session_hash,
                     'message': 'Preparing the submission with the sandbox health plan.'})
        sandbox_run=view.demo_run
        if sandbox_run:action.content={**action.content,'sandbox_run':str(sandbox_run)}
        session.add(action)
        action_id = action.id
    adapter = gateway or for_run(settings,sandbox_run)
    order_id = uuid5(NAMESPACE_URL, 'bring-vene:sandbox-order:' + str(action_id))
    try:
        review = adapter.call('/lookup', {'window': 'morning', 'location': 'Evergreen Health Plan', 'day': '2026-10-15',
                                          'institution': 'plan'})
        order = adapter.call('/orders', {'request_id': str(order_id), 'institution': 'plan'}) if review.get('slot') else None
    except Exception as error:
        log.warning('Authorization preparation failed (%s)', type(error).__name__)
        review = order = None
    with Session(engine) as session, session.begin():
        _, view = execution.lock(session, visit_id)
        action = session.get(ExecutionRecord, action_id)
        if (review and 'slot' in review and review['slot'] is None and review.get('institution')=='plan'
            and execution.scope_valid(session,view,action)):
            action.state='no_slot'
            action.content={**action.content,'message':'The sandbox health plan could not offer a review. Nothing was sent; check again.'}
            return
        if (not review or not review.get('slot') or not order or order.get('status')!='available' or
            order.get('order_id')!=str(order_id) or order.get('institution')!='plan' or order.get('sandbox_run')!=(str(sandbox_run) if sandbox_run else None) or
            review['slot'].get('institution')!='plan' or not execution.scope_valid(session,view,action)):
            action.state = 'unavailable'
            action.content = {**action.content, 'message': 'The sandbox health plan did not return a verified result. Nothing was sent.'}
            return
        action.state = 'suggested'
        action.content = {**action.content, 'slot': review['slot'], 'availability_revision': review['revision'],
            'checked_at': review['checked_at'], 'expires_at': review['expires_at'], 'clinician_id': str(clinician_id),
            'clinician_at': utc_now().isoformat(), 'order_id': str(order_id), 'order_receipt': order,
            'message': 'The office will submit this to the sandbox health plan. Nothing is sent until you approve it.'}


def requires_authorization(session, view, action):
    """True when a current coverage check for this imaging step says the plan requires prior authorization."""
    if action.content.get('kind') != 'imaging':
        return False
    check = session.scalar(select(FeasibilityCheckRecord).where(
        FeasibilityCheckRecord.encounter_id == view.id, FeasibilityCheckRecord.item_id == action.item_id,
        FeasibilityCheckRecord.kind == 'coverage', FeasibilityCheckRecord.state == 'done',
        FeasibilityCheckRecord.plan_fingerprint == action.content['plan_fingerprint'])
        .order_by(FeasibilityCheckRecord.finished_at.desc()).limit(1))
    if not check or not check.content.get('result', {}).get('prior_authorization_required'):
        return False
    auth_id=authorization_item_id(view,action.item_id)
    try:current_fingerprint=execution_fingerprint(view,auth_id)
    except DomainError:return True
    approved = session.scalar(select(ExecutionRecord.id).where(
        ExecutionRecord.encounter_id == view.id, ExecutionRecord.item_id == auth_id,
        ExecutionRecord.state == 'confirmed',ExecutionRecord.content['plan_fingerprint'].astext==current_fingerprint))
    return not approved


def timings(engine, visit_id, obstacle_id, token):
    """Patient-only diagnostic: when the turn was finalized, checked and cued. No content."""
    with Session(engine) as session, session.begin():
        _, _, member, _ = access(session, visit_id, token)
        patient(member)
        row = session.get(ObstacleRecord, obstacle_id)
        if not row or row.encounter_id != visit_id:
            raise DomainError(404, 'Obstacle not found.')
        spans = dict(row.content.get('timings', {}))
        if spans.get('source_observed_at') and spans.get('cue_at'):
            spans['source_to_cue_ms'] = int((datetime.fromisoformat(spans['cue_at']) -
                                            datetime.fromisoformat(spans['source_observed_at'])).total_seconds() * 1000)
        return spans
