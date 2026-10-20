"""Phase 9: several errand kinds through one execution pipeline, and bundle approval."""
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID,uuid4
import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from bring_vene.auth import FIXTURE_VISIT
from bring_vene.domain.contracts import EncounterView,PlanItem
from bring_vene.domain.service import DomainError
from bring_vene.execution import service
from bring_vene.execution.contracts import ScopeRequest,LookupRequest,BundleRequest
from bring_vene.persistence.models import EncounterRecord,OfficeRequestRecord,OfficeStateRecord
from test_execution import Bridge,SETTINGS,BASE,cred,action,ready
from helpers import authenticated_client
from bring_vene.main import create_app

STEPS={
    'lab':('Arrange the lab visit','Maria will arrange the lab visit at Riverside Lab on Tuesday.','Riverside Lab','2026-10-20'),
    'imaging':('Schedule the imaging','Maria will schedule the MRI at Lakeside Imaging on Wednesday.','Lakeside Imaging','2026-10-21'),
    'referral':('Resolve the referral document','The office will send the referral to Riverside Cardiology.','Riverside Cardiology','2026-10-27'),
    'prescription':('Pick up the new prescription','Maria will pick up the prescription at Main Street Pharmacy on Thursday.','Main Street Pharmacy','2026-10-22'),
}

def setup(engine,kinds=('lab','imaging','referral','prescription'),shared=True):
    app=create_app(SETTINGS,engine);p=authenticated_client(app);d=authenticated_client(app,'clinician');f=authenticated_client(app,'family')
    items={}
    with Session(engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);view=EncounterView.model_validate(record.projection)
        for kind in kinds:
            title,detail,location,_=STEPS[kind]
            item=PlanItem(id=uuid4(),title=title,detail=detail,owner='Maria',timeframe='Soon',location=location,
                evidence_refs=[view.evidence[0].id],origin='interpretation',kind=kind,
                audiences=['clinician','family'] if shared else ['clinician'])
            view.plan.append(item);items[kind]=item.id
        view.evidence[0].audiences=['clinician','family']
        record.projection=view.model_dump(mode='json')
    return p,d,f,items,Bridge(engine)

def check(engine,p,item,bridge,kind,window='morning'):
    _,_,location,day=STEPS[kind]
    service.scope(engine,FIXTURE_VISIT,item,*cred(p),ScopeRequest(allowed=True))
    return service.lookup(engine,FIXTURE_VISIT,item,*cred(p),LookupRequest(window=window,location=location,day=day),SETTINGS,bridge)

def bundle(engine,p,digests):
    return service.approve_bundle(engine,FIXTURE_VISIT,*cred(p),BundleRequest(digests=digests))

def writes(engine,institution=None):
    with Session(engine) as session:
        rows=session.scalars(select(OfficeRequestRecord).where(OfficeRequestRecord.kind=='booking')).all()
        return [r for r in rows if institution is None or r.content['payload'].get('institution','lab')==institution]

def reserved(engine,institution):
    with Session(engine) as session:
        return session.get(OfficeStateRecord,'office' if institution=='lab' else institution).content['reserved']

@pytest.mark.parametrize('kind,institution',[('lab','lab'),('imaging','imaging'),('referral','specialist'),('prescription','pharmacy')])
def test_each_kind_reserves_at_its_own_institution_with_its_own_document(visit_engine,kind,institution):
    p,d,f,items,b=setup(visit_engine,(kind,))
    aid=check(visit_engine,p,items[kind],b,kind);a=action(visit_engine,p,aid)
    assert a.state=='suggested' and a.kind==kind and a.slot['institution']==institution
    assert a.slot['location']==STEPS[kind][2]
    ready(visit_engine,p,d,aid,b)
    assert bundle(visit_engine,p,[action(visit_engine,p,aid).digest]).outcomes[0].outcome=='queued'
    service.dispatch(visit_engine,SETTINGS,gateway=b)
    done=action(visit_engine,p,aid)
    assert done.state=='confirmed' and done.receipt['slot_id']==a.slot['id']
    assert reserved(visit_engine,institution)==[a.slot['id']]
    assert len(writes(visit_engine,institution))==1
    with Session(visit_engine) as session:
        order=session.get(OfficeRequestRecord,UUID(next(r.content['payload']['order_id'] for r in writes(visit_engine))))
        assert order.content.get('institution','lab')==institution


@pytest.mark.parametrize('kind,institution',[('lab','lab'),('imaging','imaging'),('referral','specialist'),('prescription','pharmacy')])
def test_each_kind_reconciles_a_lost_receipt_after_permission_is_withdrawn(visit_engine,kind,institution):
    p,d,_,items,b=setup(visit_engine,(kind,))
    aid=check(visit_engine,p,items[kind],b,kind);ready(visit_engine,p,d,aid,b)
    bundle(visit_engine,p,[action(visit_engine,p,aid).digest])
    b.fail_after_write=True
    service.dispatch(visit_engine,SETTINGS,gateway=b)
    assert action(visit_engine,p,aid).state=='unknown'
    # A lost response does not mean the office failed. Revocation prevents new
    # work but cannot erase the actual write; reconcile it without another one.
    service.scope(visit_engine,FIXTURE_VISIT,items[kind],*cred(p),ScopeRequest(allowed=False))
    from bring_vene.persistence.models import ExecutionOutboxRecord
    from bring_vene.domain.service import utc_now
    with Session(visit_engine) as session,session.begin():
        session.get(ExecutionOutboxRecord,aid).next_at=utc_now()
    service.dispatch(visit_engine,SETTINGS,gateway=b)
    done=action(visit_engine,p,aid)
    assert done.state=='confirmed' and done.receipt['request_id']==str(aid)
    assert not done.scope_allowed and len(writes(visit_engine,institution))==1
    assert reserved(visit_engine,institution)==[done.slot['id']]

def test_unclassified_step_and_wrong_location_are_refused_before_the_office_is_called(visit_engine):
    p,d,f,items,b=setup(visit_engine,('imaging',))
    with Session(visit_engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);view=EncounterView.model_validate(record.projection)
        other=PlanItem(id=uuid4(),title='Ask about the bill',detail='Billing question',evidence_refs=[view.evidence[0].id],kind='other')
        view.plan.append(other);record.projection=view.model_dump(mode='json')
    service.scope(visit_engine,FIXTURE_VISIT,other.id,*cred(p),ScopeRequest(allowed=True))
    with pytest.raises(DomainError) as refused:
        service.lookup(visit_engine,FIXTURE_VISIT,other.id,*cred(p),LookupRequest(window='morning'),SETTINGS,b)
    assert refused.value.status==422
    service.scope(visit_engine,FIXTURE_VISIT,items['imaging'],*cred(p),ScopeRequest(allowed=True))
    with pytest.raises(DomainError) as wrong:
        service.lookup(visit_engine,FIXTURE_VISIT,items['imaging'],*cred(p),LookupRequest(window='morning',location='Riverside Lab'),SETTINGS,b)
    assert wrong.value.status==422 and b.calls==[]

def test_institutions_are_isolated_documents_cannot_cross_and_pharmacy_takes_no_medicine_fields(visit_engine):
    p,d,f,items,b=setup(visit_engine)
    b.call('/scenario',{'mode':'no_slot','institution':'imaging'})
    assert action(visit_engine,p,check(visit_engine,p,items['imaging'],b,'imaging')).state=='no_slot'
    assert action(visit_engine,p,check(visit_engine,p,items['lab'],b,'lab')).state=='suggested'
    lab_order=uuid4();b.call('/orders',{'request_id':str(lab_order)})
    slot=b.call('/lookup',{'window':'morning','location':'Main Street Pharmacy','day':'2026-10-22','institution':'pharmacy'})
    headers={'Authorization':'Bearer '+SETTINGS.office_token}
    payload={'request_id':str(uuid4()),'slot_id':slot['slot']['id'],'availability_revision':slot['revision'],
        'order_id':str(lab_order),'institution':'pharmacy'}
    assert b.client.post('/bookings',json=payload,headers=headers).status_code==409  # a lab order is not a prescription
    prescription=uuid4();b.call('/orders',{'request_id':str(prescription),'institution':'pharmacy'})
    assert b.client.post('/bookings',json={**payload,'order_id':str(prescription),'medication':'anything'},headers=headers).status_code==422
    assert b.client.post('/bookings',json={**payload,'order_id':str(prescription),'dose':'10 mg'},headers=headers).status_code==422
    assert b.client.post('/bookings',json={**payload,'order_id':str(prescription)},headers=headers).json()['status']=='confirmed'

def test_bundle_reports_each_errand_honestly_without_rolling_back_others(visit_engine):
    p,d,f,items,b=setup(visit_engine,('lab','imaging','prescription'))
    ids={kind:check(visit_engine,p,items[kind],b,kind) for kind in items}
    for kind in ('lab','imaging'):ready(visit_engine,p,d,ids[kind],b)
    ready(visit_engine,p,d,ids['prescription'],b,order=False)  # clinician confirmed, prescription not yet sent
    b.call('/scenario',{'mode':'rejected','institution':'imaging'})
    result=bundle(visit_engine,p,[action(visit_engine,p,ids[k]).digest for k in ids])
    outcomes={o.action_id:o for o in result.outcomes}
    assert outcomes[ids['lab']].outcome=='queued' and outcomes[ids['imaging']].outcome=='queued'
    assert outcomes[ids['prescription']].outcome=='waiting' and 'prescription' in outcomes[ids['prescription']].message
    while service.dispatch(visit_engine,SETTINGS,gateway=b):pass
    assert action(visit_engine,p,ids['lab']).state=='confirmed'
    assert action(visit_engine,p,ids['imaging']).state=='rejected'
    assert action(visit_engine,p,ids['prescription']).state=='suggested'
    assert len(writes(visit_engine))==2 and len(writes(visit_engine,'lab'))==1  # nothing undone, nothing retried

def test_bundle_refuses_only_the_changed_step(visit_engine):
    p,d,f,items,b=setup(visit_engine,('lab','imaging'))
    ids={kind:check(visit_engine,p,items[kind],b,kind) for kind in items}
    for kind in ids:ready(visit_engine,p,d,ids[kind],b)
    digests=[action(visit_engine,p,ids[k]).digest for k in ids]
    with Session(visit_engine) as session,session.begin():
        record,view=service.lock(session,FIXTURE_VISIT);step=service.target(view,items['imaging'])
        step.revision+=1;step.timeframe='Another week';record.projection=view.model_dump(mode='json')
    result=bundle(visit_engine,p,digests)
    outcomes={o.action_id:o.outcome for o in result.outcomes}
    assert outcomes[ids['lab']]=='queued'
    assert outcomes.get(ids['imaging'],'refused')=='refused'
    while service.dispatch(visit_engine,SETTINGS,gateway=b):pass
    assert len(writes(visit_engine,'imaging'))==0 and len(writes(visit_engine,'lab'))==1

def test_bundle_of_only_changed_steps_is_refused_and_guests_cannot_approve(visit_engine):
    p,d,f,items,b=setup(visit_engine,('lab',))
    with pytest.raises(DomainError):bundle(visit_engine,p,['0'*64])
    aid=check(visit_engine,p,items['lab'],b,'lab');ready(visit_engine,p,d,aid,b)
    digest=action(visit_engine,p,aid).digest
    assert f.post(BASE+'/approve-ready',json={'digests':[digest]}).status_code==403
    assert d.post(BASE+'/approve-ready',json={'digests':[digest]}).status_code==403
    response=p.post(BASE+'/approve-ready',json={'digests':[digest]})
    assert response.status_code==200 and response.json()['outcomes'][0]['outcome']=='queued'

def test_concurrent_bundles_dispatch_each_errand_once(visit_engine):
    p,d,f,items,b=setup(visit_engine,('lab','referral'))
    ids={kind:check(visit_engine,p,items[kind],b,kind) for kind in items}
    for kind in ids:ready(visit_engine,p,d,ids[kind],b)
    digests=[action(visit_engine,p,ids[k]).digest for k in ids]
    with ThreadPoolExecutor(3) as pool:
        results=list(pool.map(lambda _:bundle(visit_engine,p,digests),range(3)))
        list(pool.map(lambda _:service.dispatch(visit_engine,SETTINGS,gateway=b),range(4)))
    while service.dispatch(visit_engine,SETTINGS,gateway=b):pass
    queued=[o for r in results for o in r.outcomes if o.outcome=='queued']
    assert len(queued)==2 and len(writes(visit_engine))==2
    assert {action(visit_engine,p,ids[k]).state for k in ids}=={'confirmed'}

def test_guests_see_only_shared_errands_with_honest_kind_wording(visit_engine):
    p,d,f,items,b=setup(visit_engine,('lab','prescription'),shared=False)
    for kind in items:check(visit_engine,p,items[kind],b,kind)
    assert f.get(BASE).json()['actions']==[]
    clinician=d.get(BASE).json()['actions']
    assert {a['kind'] for a in clinician}=={'lab','prescription'}
    assert all(a['digest'] is None for a in clinician)
    pharmacy=next(a for a in clinician if a['kind']=='prescription')
    assert pharmacy['place']=='pharmacy' and pharmacy['document']=='prescription' and 'pickup window' in pharmacy['message']

def test_fixture_interpretation_sets_errand_kinds():
    from bring_vene.understanding.gateway import fixture_extract
    texts=['Maria will schedule the MRI at Lakeside Imaging on Wednesday after the office sends the order.',
        'Maria will pick up the new prescription at Main Street Pharmacy on Thursday.',
        'Maria will arrange the lab visit at Riverside Lab on Tuesday after the office sends the order.']
    snapshot={'sources':[{'id':str(uuid4()),'version':1,'speaker':'Dr. Chen','origin':'fixture','text':t} for t in texts],'priorities':[]}
    steps={s.topic:s for s in fixture_extract(snapshot).steps}
    assert set(steps)=={'imaging','prescription','lab'}
    assert steps['imaging'].location=='Lakeside Imaging' and steps['prescription'].location=='Main Street Pharmacy'
