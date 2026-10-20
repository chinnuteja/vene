"""Phase 10: practical checks during the visit, obstacles, cues and resolutions."""
from uuid import UUID,uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.auth import FIXTURE_VISIT,FIXTURE_MEMBERS
from bring_vene.domain.contracts import EncounterView,PlanItem
from bring_vene.domain.service import DomainError
from bring_vene.execution import service as execution
from bring_vene.execution.contracts import BundleRequest
from bring_vene.feasibility import service as feasibility
from bring_vene.feasibility.contracts import ResolveRequest,StandingRequest
from bring_vene.persistence.models import (CallRecord,CueRecord,EncounterRecord,FeasibilityCheckRecord,ObstacleRecord,
    ExecutionRecord)
from test_errands import check
from test_execution import Bridge,SETTINGS,cred,action,ready
from helpers import authenticated_client
from bring_vene.main import create_app

ROOT=f'/encounters/{FIXTURE_VISIT}/feasibility'
STEPS={
    'imaging':('Schedule the imaging','Maria will schedule the MRI at Lakeside Imaging on Wednesday.','Lakeside Imaging','Wednesday'),
    'prescription':('Pick up the new prescription','Maria will pick up the Lorvexa prescription at Main Street Pharmacy on Thursday.','Main Street Pharmacy','Thursday'),
    'referral':('Resolve the referral document','The office will send the referral to Riverside Cardiology.','Riverside Cardiology',None),
    'lab':('Arrange the lab visit','Maria will arrange the lab visit at Riverside Lab on Tuesday.','Riverside Lab','Tuesday'),
}

def setup(engine,kinds=('imaging',),shared=True,detail=None,member_ref=None):
    app=create_app(SETTINGS,engine);p=authenticated_client(app);d=authenticated_client(app,'clinician');f=authenticated_client(app,'family')
    items={}
    with Session(engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);view=EncounterView.model_validate(record.projection)
        for kind in kinds:
            title,text,location,timeframe=STEPS[kind]
            item=PlanItem(id=uuid4(),title=title,detail=(detail or {}).get(kind,text),owner='Maria',timeframe=timeframe,location=location,
                evidence_refs=[view.evidence[0].id],origin='interpretation',kind=kind,audiences=['clinician','family'] if shared else [])
            view.plan.append(item);items[kind]=item.id
        if shared:view.evidence[0].audiences=['clinician','family']
        if member_ref:view.coverage.member_ref=member_ref
        record.projection=view.model_dump(mode='json')
    return p,d,f,items,Bridge(engine)

def grant(p,kinds=('scheduling','coverage','pharmacy')):
    response=p.post(ROOT+'/standing',json={'kinds':list(kinds)});assert response.status_code==200;return response.json()

def work(engine,b):
    while feasibility.tick(engine,SETTINGS,gateway=b):pass

def obstacles(client):return client.get(ROOT).json()['obstacles']

def correct(engine,item_id,timeframe='Thursday'):
    with Session(engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);view=EncounterView.model_validate(record.projection)
        item=next(i for i in view.plan if i.id==item_id);item.timeframe=timeframe;item.revision+=1
        record.projection=view.model_dump(mode='json')

def cues(engine):
    with Session(engine) as session:
        return [c for c in session.scalars(select(CueRecord).where(CueRecord.encounter_id==FIXTURE_VISIT)) if c.content.get('obstacle_id')]

def test_without_standing_permission_nothing_leaves_the_service(visit_engine):
    p,d,f,items,b=setup(visit_engine,('imaging','prescription','referral'))
    work(visit_engine,b)
    assert b.calls==[] and obstacles(p)==[]
    grant(p,['scheduling']);work(visit_engine,b)
    assert '/coverage' not in b.calls and '/stock' not in b.calls  # only the permitted kind ran
    assert {o['kind'] for o in obstacles(p)}=={'missing_supporting_document'}

def test_prior_authorization_obstacle_reaches_the_patient_privately_and_the_clinician_scoped(visit_engine):
    p,d,f,items,b=setup(visit_engine);grant(p,['coverage']);work(visit_engine,b)
    [obstacle]=obstacles(p)
    assert obstacle['kind']=='prior_authorization_required' and obstacle['state']=='open'
    assert obstacle['fact']=='Evergreen Basic (fictional) requires prior authorization for this imaging.'
    assert obstacle['resolver']=='clinician' and obstacle['choices']==[]  # the patient sees it but cannot answer for the clinician
    seen=obstacles(d)[0];assert [c['id'] for c in seen['choices']]==['office_will_submit','review_later']
    assert f.get(ROOT).json()=={'standing':None,'checking':0,'failed':0,'obstacles':[]}
    assert 'standing' not in d.get(ROOT).text.replace('"standing":null','')
    [cue]=cues(visit_engine)
    assert cue.content['obstacle_id']==obstacle['id'] and 'Maria' not in cue.content['text'] and 'prior authorization' in cue.content['text']
    with Session(visit_engine) as session:
        timings=session.get(ObstacleRecord,UUID(obstacle['id'])).content['timings']
    assert timings['cue_at'] and timings['check_finished_at'] and timings['source_observed_at']

def test_unshared_steps_are_absent_from_guest_payloads(visit_engine):
    p,d,f,items,b=setup(visit_engine,shared=False);grant(p,['coverage']);work(visit_engine,b)
    assert len(obstacles(p))==1 and obstacles(d)==[]
    assert 'imaging' not in d.get(ROOT).text.lower()

def test_formulary_obstacle_lists_plan_facts_and_never_speaks_a_medicine(visit_engine):
    p,d,f,items,b=setup(visit_engine,('prescription',));grant(p,['coverage']);work(visit_engine,b)
    [obstacle]=obstacles(d)
    assert obstacle['kind']=='not_on_formulary' and obstacle['plan_alternatives']==['Tamorin','Celvane']
    assert 'clinician decides' in obstacle['fact']
    [cue]=cues(visit_engine)
    for name in ['Lorvexa','Tamorin','Celvane']:assert name not in cue.content['text']

def test_other_plans_and_unidentified_medicines_raise_nothing(visit_engine):
    p,d,f,items,b=setup(visit_engine,('imaging','prescription'),member_ref='EVG-P-2002',
        detail={'prescription':'Maria will pick up the new prescription at Main Street Pharmacy on Thursday.'})
    grant(p,['coverage','pharmacy']);work(visit_engine,b)
    assert obstacles(p)==[] and '/stock' not in b.calls  # nothing identified, so no medicine left the service

def test_correction_supersedes_the_obstacle_and_its_cue(visit_engine):
    p,d,f,items,b=setup(visit_engine);grant(p,['coverage']);work(visit_engine,b)
    first=obstacles(p)[0]['id'];[cue]=cues(visit_engine)
    correct(visit_engine,items['imaging']);work(visit_engine,b)
    current=obstacles(p);assert len(current)==1 and current[0]['id']!=first
    with Session(visit_engine) as session:
        assert session.get(ObstacleRecord,UUID(first)).state=='superseded'
        from bring_vene.speech.service import scope_allows
        view=EncounterView.model_validate(session.get(EncounterRecord,FIXTURE_VISIT).projection)
        assert not scope_allows(session,None,view,session.get(CueRecord,cue.id))

def test_revoked_or_changed_permission_discards_queued_and_in_flight_checks(visit_engine):
    p,d,f,items,b=setup(visit_engine);grant(p,['coverage'])
    feasibility.enqueue(visit_engine);grant(p,[])
    work(visit_engine,b);assert b.calls==[] and obstacles(p)==[]
    grant(p,['coverage'])
    class Revoking:
        def call(self,path,payload=None):
            result=b.call(path,payload)
            if path=='/coverage':grant(p,[])
            return result
    work(visit_engine,Revoking())
    assert obstacles(p)==[]
    with Session(visit_engine) as session:
        states={r.state for r in session.scalars(select(FeasibilityCheckRecord))}
    assert 'stale' in states and 'done' not in states

def test_pause_holds_checks_and_discards_results_that_return_during_pause(visit_engine):
    p,d,f,items,b=setup(visit_engine)
    with Session(visit_engine) as session,session.begin():
        session.add(CallRecord(encounter_id=FIXTURE_VISIT,generation=uuid4(),revision=1,manual_pause=True,ended=False))
    grant(p);work(visit_engine,b);assert b.calls==[]
    with Session(visit_engine) as session,session.begin():session.get(CallRecord,FIXTURE_VISIT).manual_pause=False
    class Pausing:
        def call(self,path,payload=None):
            result=b.call(path,payload)
            with Session(visit_engine) as session,session.begin():session.get(CallRecord,FIXTURE_VISIT).manual_pause=True
            return result
    work(visit_engine,Pausing());assert obstacles(p)==[]
    with Session(visit_engine) as session,session.begin():session.get(CallRecord,FIXTURE_VISIT).ended=True
    work(visit_engine,b);assert [o['kind'] for o in obstacles(p)]==['prior_authorization_required']

def test_availability_stock_and_document_obstacles(visit_engine):
    p,d,f,items,b=setup(visit_engine,('imaging','prescription','referral'),
        detail={'prescription':'Maria will pick up the Tamorin prescription at Main Street Pharmacy on Thursday.'})
    b.call('/scenario',{'mode':'no_slot','institution':'imaging'});b.call('/scenario',{'mode':'out_of_stock','institution':'pharmacy'})
    grant(p);work(visit_engine,b)
    kinds={o['kind']:o for o in obstacles(p)}
    assert set(kinds)=={'no_slot_in_window','prior_authorization_required','not_in_stock','missing_supporting_document'}
    assert kinds['no_slot_in_window']['fact']=='The sandbox imaging center shows no Wednesday availability at Lakeside Imaging.'
    assert kinds['not_in_stock']['resolver']=='patient' and kinds['missing_supporting_document']['resolver']=='clinician'
    assert 'not_on_formulary' not in kinds  # Tamorin is covered

def test_only_the_named_resolver_can_answer_with_a_listed_response(visit_engine):
    p,d,f,items,b=setup(visit_engine);grant(p,['coverage']);work(visit_engine,b)
    obstacle=obstacles(d)[0]['id']
    assert p.post(ROOT+f'/obstacles/{obstacle}/resolve',json={'choice':'review_later'}).status_code==403
    assert f.post(ROOT+f'/obstacles/{obstacle}/resolve',json={'choice':'review_later'}).status_code==404
    assert d.post(ROOT+f'/obstacles/{obstacle}/resolve',json={'choice':'review_coverage'}).status_code==422
    assert d.post(ROOT+f'/obstacles/{obstacle}/resolve',json={'choice':'review_later'}).status_code==200
    assert d.post(ROOT+f'/obstacles/{obstacle}/resolve',json={'choice':'review_later'}).status_code==409

def test_full_prior_authorization_flow(visit_engine):
    p,d,f,items,b=setup(visit_engine);grant(p,['coverage']);work(visit_engine,b)
    obstacle=UUID(obstacles(d)[0]['id'])
    feasibility.resolve(visit_engine,FIXTURE_VISIT,obstacle,*cred(d),ResolveRequest(choice='office_will_submit'),SETTINGS,b)
    assert obstacles(p)[0]['state']=='resolved' and obstacles(p)[0]['resolution']['by_name']=='Dr. Chris Chen'
    assert cues(visit_engine) and not any(c.state=='pending' and _cue_ok(visit_engine,c) for c in cues(visit_engine))
    with Session(visit_engine) as session:
        view=EncounterView.model_validate(session.get(EncounterRecord,FIXTURE_VISIT).projection)
        auth=next(i for i in view.plan if i.kind=='authorization')
        assert auth.audiences==['clinician'] and auth.origin=='resolution'
        auth_action=session.scalar(select(ExecutionRecord).where(ExecutionRecord.item_id==auth.id))
    assert auth_action.state=='suggested' and auth_action.content['clinician_id']==str(FIXTURE_MEMBERS['clinician'])
    assert 'family' not in [a['kind'] for a in f.get(f'/encounters/{FIXTURE_VISIT}/execution').json()['actions']]
    # The imaging booking itself now waits on an approved prior authorization.
    imaging=check(visit_engine,p,items['imaging'],b,'imaging');ready(visit_engine,p,d,imaging,b)
    outcome=execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),BundleRequest(digests=[action(visit_engine,p,imaging).digest])).outcomes[0]
    assert outcome.outcome=='waiting' and 'approved prior authorization' in outcome.message
    # Nothing goes to the plan until the patient approves the submission.
    assert b.calls.count('/bookings')==0
    execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),BundleRequest(digests=[action(visit_engine,p,auth_action.id).digest]))
    while execution.dispatch(visit_engine,SETTINGS,gateway=b):pass
    approved=action(visit_engine,p,auth_action.id);assert approved.state=='confirmed' and approved.kind=='authorization'
    result=execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),BundleRequest(digests=[action(visit_engine,p,imaging).digest]))
    assert result.outcomes[0].outcome=='queued'
    while execution.dispatch(visit_engine,SETTINGS,gateway=b):pass
    assert action(visit_engine,p,imaging).state=='confirmed'

def test_denied_authorization_keeps_imaging_blocked(visit_engine):
    p,d,f,items,b=setup(visit_engine);grant(p,['coverage']);work(visit_engine,b)
    feasibility.resolve(visit_engine,FIXTURE_VISIT,UUID(obstacles(d)[0]['id']),*cred(d),ResolveRequest(choice='office_will_submit'),SETTINGS,b)
    b.call('/scenario',{'mode':'rejected','institution':'plan'})
    with Session(visit_engine) as session:
        auth=session.scalar(select(ExecutionRecord).where(ExecutionRecord.content['kind'].astext=='authorization'))
    execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),BundleRequest(digests=[action(visit_engine,p,auth.id).digest]))
    while execution.dispatch(visit_engine,SETTINGS,gateway=b):pass
    assert action(visit_engine,p,auth.id).state=='rejected'
    imaging=check(visit_engine,p,items['imaging'],b,'imaging');ready(visit_engine,p,d,imaging,b)
    outcome=execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),BundleRequest(digests=[action(visit_engine,p,imaging).digest])).outcomes[0]
    assert outcome.outcome=='waiting' and b.calls.count('/bookings')==1


@pytest.mark.parametrize('uncertain',[False,True])
def test_new_coverage_requirement_stops_an_unsent_or_provably_absent_request(visit_engine,uncertain):
    p,d,_,items,b=setup(visit_engine)
    imaging=check(visit_engine,p,items['imaging'],b,'imaging');ready(visit_engine,p,d,imaging,b)
    approved=execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),
        BundleRequest(digests=[action(visit_engine,p,imaging).digest]))
    assert approved.outcomes[0].outcome=='queued'
    if uncertain:
        class LostBeforeWrite:
            def call(self,path,payload=None):
                if path=='/bookings':raise TimeoutError('Synthetic loss before any office commit')
                return b.call(path,payload)
        execution.dispatch(visit_engine,SETTINGS,gateway=LostBeforeWrite())
        assert action(visit_engine,p,imaging).state=='unknown'
    # Coverage finishes after approval, but before the office has committed.
    grant(p,['coverage']);work(visit_engine,b)
    assert any(o['kind']=='prior_authorization_required' for o in obstacles(p))
    from bring_vene.persistence.models import ExecutionOutboxRecord
    from bring_vene.domain.service import utc_now
    with Session(visit_engine) as session,session.begin():
        session.get(ExecutionOutboxRecord,imaging).next_at=utc_now()
    execution.dispatch(visit_engine,SETTINGS,gateway=b)
    result=action(visit_engine,p,imaging)
    assert result.state==('cancelled' if uncertain else 'invalidated')
    assert result.receipt is None and b.calls.count('/bookings')==0


def test_authorization_with_no_review_available_never_becomes_approvable(visit_engine):
    p,d,_,_,b=setup(visit_engine);grant(p,['coverage']);work(visit_engine,b)
    class NoReview:
        def call(self,path,payload=None):
            response=b.call(path,payload)
            if path=='/lookup' and payload.get('institution')=='plan':response['slot']=None
            return response
    feasibility.resolve(visit_engine,FIXTURE_VISIT,UUID(obstacles(d)[0]['id']),*cred(d),
        ResolveRequest(choice='office_will_submit'),SETTINGS,NoReview())
    with Session(visit_engine) as session:
        request=session.scalar(select(ExecutionRecord).where(ExecutionRecord.content['kind'].astext=='authorization'))
    shown=action(visit_engine,p,request.id)
    assert shown.state=='no_slot' and shown.digest is None
    assert b.calls.count('/bookings')==0


def test_old_authorization_cannot_satisfy_a_corrected_imaging_plan(visit_engine):
    p,d,_,items,b=setup(visit_engine);grant(p,['coverage']);work(visit_engine,b)
    feasibility.resolve(visit_engine,FIXTURE_VISIT,UUID(obstacles(d)[0]['id']),*cred(d),
        ResolveRequest(choice='office_will_submit'),SETTINGS,b)
    with Session(visit_engine) as session:
        prior=session.scalar(select(ExecutionRecord).where(ExecutionRecord.content['kind'].astext=='authorization'))
    execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),BundleRequest(digests=[action(visit_engine,p,prior.id).digest]))
    while execution.dispatch(visit_engine,SETTINGS,gateway=b):pass
    original_receipt=action(visit_engine,p,prior.id).receipt
    assert original_receipt['status']=='confirmed'
    correct(visit_engine,items['imaging']);work(visit_engine,b)
    imaging=check(visit_engine,p,items['imaging'],b,'imaging');ready(visit_engine,p,d,imaging,b)
    outcome=execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),
        BundleRequest(digests=[action(visit_engine,p,imaging).digest])).outcomes[0]
    assert outcome.outcome=='waiting' and 'approved prior authorization' in outcome.message
    earlier=action(visit_engine,p,prior.id)
    assert earlier.receipt==original_receipt and earlier.fingerprint is None
    # The clinician can prepare a fresh submission for the changed intention.
    fresh_obstacle=next(o for o in obstacles(d) if o['kind']=='prior_authorization_required' and o['state']=='open')
    feasibility.resolve(visit_engine,FIXTURE_VISIT,UUID(fresh_obstacle['id']),*cred(d),
        ResolveRequest(choice='office_will_submit'),SETTINGS,b)
    auth_actions=[a for a in execution.state(visit_engine,FIXTURE_VISIT,cred(p)[0],SETTINGS).actions if a.kind=='authorization']
    renewed=auth_actions[0]
    assert renewed.id!=prior.id and renewed.state=='suggested'
    execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),BundleRequest(digests=[renewed.digest]))
    while execution.dispatch(visit_engine,SETTINGS,gateway=b):pass
    assert action(visit_engine,p,renewed.id).state=='confirmed'
    assert execution.approve_bundle(visit_engine,FIXTURE_VISIT,*cred(p),
        BundleRequest(digests=[action(visit_engine,p,imaging).digest])).outcomes[0].outcome=='queued'
    while execution.dispatch(visit_engine,SETTINGS,gateway=b):pass
    assert action(visit_engine,p,imaging).state=='confirmed'

def test_a_resolved_fact_is_not_reopened_by_a_new_permission_revision(visit_engine):
    p,d,f,items,b=setup(visit_engine);grant(p,['coverage']);work(visit_engine,b)
    feasibility.resolve(visit_engine,FIXTURE_VISIT,UUID(obstacles(d)[0]['id']),*cred(d),ResolveRequest(choice='review_later'),SETTINGS,b)
    grant(p,['coverage','scheduling']);work(visit_engine,b)
    assert [o['state'] for o in obstacles(p) if o['kind']=='prior_authorization_required']==['resolved']

def _cue_ok(engine,cue):
    from bring_vene.speech.service import scope_allows
    with Session(engine) as session:
        view=EncounterView.model_validate(session.get(EncounterRecord,FIXTURE_VISIT).projection)
        return scope_allows(session,None,view,session.get(CueRecord,cue.id))
