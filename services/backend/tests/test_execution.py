from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID,uuid4
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from bring_vene.auth import COOKIE,FIXTURE_VISIT,FIXTURE_MEMBERS
from bring_vene.config import Settings
from bring_vene.domain.contracts import EncounterView,PlanItem
from bring_vene.domain.service import DomainError,utc_now
from bring_vene.main import create_app
from bring_vene.execution import service
from bring_vene.execution.office import office_app,initialize
from bring_vene.execution.contracts import ScopeRequest,LookupRequest,ApprovalRequest,PrerequisiteRequest
from bring_vene.persistence.models import EncounterRecord,ExecutionRecord,ExecutionOutboxRecord,OfficeRequestRecord,MembershipRecord
from helpers import authenticated_client

SETTINGS=Settings(bring_vene_development=True,cookie_secure=False,office_url='http://127.0.0.1:8012',office_token='isolated-test-token')
BASE=f'/encounters/{FIXTURE_VISIT}/execution'

class Bridge:
    def __init__(self,engine):
        initialize(engine);self.client=TestClient(office_app(SETTINGS,engine));self.calls=[];self.fail_after_write=False
    def call(self,path,payload=None):
        self.calls.append(path)
        method=self.client.post if payload is not None else self.client.get
        response=method(path,headers={'Authorization':'Bearer '+SETTINGS.office_token},**({'json':payload} if payload is not None else {}))
        response.raise_for_status();result=response.json()
        if path=='/bookings' and self.fail_after_write:
            self.fail_after_write=False;raise TimeoutError('Synthetic loss after real office commit')
        return result

def setup(engine):
    app=create_app(SETTINGS,engine);p=authenticated_client(app);d=authenticated_client(app,'clinician');f=authenticated_client(app,'family')
    with Session(engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);view=EncounterView.model_validate(record.projection)
        item=PlanItem(id=uuid4(),title='Arrange the lab visit',detail='Maria will arrange the lab visit after the clinician supplies the order.',
            owner='Maria',timeframe='Thursday',evidence_refs=[view.evidence[0].id])
        view.plan.append(item)
        item.origin='interpretation';item.audiences=['clinician','family']
        for e in view.evidence:
            if e.id in item.evidence_refs:e.audiences=['clinician','family']
        record.projection=view.model_dump(mode='json');item_id=item.id
    bridge=Bridge(engine)
    return p,d,f,item_id,bridge

def cred(c):return c.cookies.get(COOKIE),c.headers['x-vene-csrf']

def check(engine,p,item,bridge,window='morning'):
    service.scope(engine,FIXTURE_VISIT,item,*cred(p),ScopeRequest(allowed=True))
    return service.lookup(engine,FIXTURE_VISIT,item,*cred(p),LookupRequest(window=window),SETTINGS,bridge)

def action(engine,p,action_id):return next(a for a in service.state(engine,FIXTURE_VISIT,p.cookies.get(COOKIE),SETTINGS).actions if a.id==action_id)

def ready(engine,p,d,action_id,bridge,order=True):
    a=action(engine,p,action_id)
    service.prerequisites(engine,FIXTURE_VISIT,action_id,*cred(d),PrerequisiteRequest(expected_fingerprint=a.fingerprint,order=order),SETTINGS,bridge)
    return action(engine,p,action_id)

def authorize(engine,p,action_id):
    service.approve(engine,FIXTURE_VISIT,action_id,*cred(p),ApprovalRequest(digest=action(engine,p,action_id).digest))

def correct(engine,item):
    with Session(engine) as session,session.begin():
        record,view=service.lock(session,FIXTURE_VISIT);target=service.target(view,item)
        target.revision+=1;target.timeframe='Different day';record.projection=view.model_dump(mode='json')

def reservation_count(engine):
    with Session(engine) as session:return session.scalar(select(func.count()).select_from(OfficeRequestRecord).where(OfficeRequestRecord.kind=='booking'))

def test_denied_lookup_leaks_nothing_and_mutations_require_csrf(visit_engine,monkeypatch):
    p,d,f,item,b=setup(visit_engine)
    class Forbidden:
        def __init__(self,_):raise AssertionError('Out-of-scope request reached adapter')
    monkeypatch.setattr(service,'OfficeGateway',Forbidden)
    assert p.post(BASE+f'/items/{item}/lookup',json={'window':'morning'}).status_code==403
    assert f.post(BASE+f'/items/{item}/scope',json={'allowed':True}).status_code==403
    del p.headers['x-vene-csrf']
    assert p.post(BASE+f'/items/{item}/scope',json={'allowed':True}).status_code==403
    assert b.calls==[]

def test_suggestion_requires_separate_order_and_approval_then_real_receipt(visit_engine):
    p,d,f,item,b=setup(visit_engine);aid=check(visit_engine,p,item,b)
    assert action(visit_engine,p,aid).state=='suggested';assert reservation_count(visit_engine)==0
    authorize(visit_engine,p,aid)
    assert not action(visit_engine,p,aid).patient_authorized
    assert 'required sandbox order' in action(visit_engine,p,aid).message
    ready(visit_engine,p,d,aid,b,order=False);authorize(visit_engine,p,aid)
    assert reservation_count(visit_engine)==0
    with Session(visit_engine) as session:assert session.get(ExecutionOutboxRecord,aid) is None
    ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid)
    assert action(visit_engine,p,aid).state=='queued'
    service.dispatch(visit_engine,SETTINGS,gateway=b)
    result=action(visit_engine,p,aid);assert result.state=='confirmed';assert result.receipt['request_id']==str(aid)
    assert reservation_count(visit_engine)==1
    assert 'session_hash' not in f.get(BASE).text and 'digest' not in f.get(BASE).text.replace('"digest":null','')

def test_lookup_correction_discards_response_and_old_approval(visit_engine):
    p,d,f,item,b=setup(visit_engine)
    class Correcting:
        def call(self,path,payload):
            response=b.call(path,payload);correct(visit_engine,item);return response
    aid=check(visit_engine,p,item,Correcting())
    assert action(visit_engine,p,aid).state=='invalidated'
    assert action(visit_engine,p,aid).slot is None
    assert f.get(BASE).json()['actions']==[]

@pytest.mark.parametrize('kind',['correction','scope','membership','clinician'])
def test_revocation_or_correction_wins_over_queued_work(visit_engine,kind):
    p,d,f,item,b=setup(visit_engine);aid=check(visit_engine,p,item,b);ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid)
    if kind=='correction':correct(visit_engine,item)
    elif kind=='scope':service.scope(visit_engine,FIXTURE_VISIT,item,*cred(p),ScopeRequest(allowed=False))
    else:
        with Session(visit_engine) as session,session.begin():session.get(MembershipRecord,FIXTURE_MEMBERS['patient' if kind=='membership' else 'clinician']).revoked_at=utc_now()
    service.dispatch(visit_engine,SETTINGS,gateway=b)
    assert '/bookings' not in b.calls;assert reservation_count(visit_engine)==0

def test_concurrent_approvals_and_workers_create_one_reservation(visit_engine):
    p,d,f,item,b=setup(visit_engine);aid=check(visit_engine,p,item,b);a=ready(visit_engine,p,d,aid,b)
    request=ApprovalRequest(digest=a.digest)
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda _:service.approve(visit_engine,FIXTURE_VISIT,aid,*cred(p),request),range(2)))
        list(pool.map(lambda _:service.dispatch(visit_engine,SETTINGS,gateway=b),range(2)))
    assert reservation_count(visit_engine)==1
    assert action(visit_engine,p,aid).state=='confirmed'

def test_ambiguous_write_reconciles_after_correction_without_second_booking(visit_engine):
    p,d,f,item,b=setup(visit_engine);aid=check(visit_engine,p,item,b);ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid)
    b.fail_after_write=True;service.dispatch(visit_engine,SETTINGS,gateway=b)
    assert action(visit_engine,p,aid).state=='unknown';assert reservation_count(visit_engine)==1
    correct(visit_engine,item)
    with Session(visit_engine) as session,session.begin():session.get(ExecutionOutboxRecord,aid).next_at=utc_now()-timedelta(seconds=1)
    service.dispatch(visit_engine,SETTINGS,gateway=b)
    assert action(visit_engine,p,aid).state=='confirmed';assert b.calls.count('/bookings')==1
    assert f.get(BASE).json()['actions']==[]
    with pytest.raises(DomainError):check(visit_engine,p,item,b,'afternoon')

@pytest.mark.parametrize('mode,expected',[('no_slot','no_slot'),('expired','expired'),('rejected','suggested')])
def test_controllable_office_conditions(visit_engine,mode,expected,monkeypatch):
    p,d,f,item,b=setup(visit_engine);b.call('/scenario',{'mode':mode});aid=check(visit_engine,p,item,b)
    assert action(visit_engine,p,aid).state==expected
    if mode=='rejected':
        ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid);service.dispatch(visit_engine,SETTINGS,gateway=b)
        assert action(visit_engine,p,aid).state=='rejected'
    else:assert reservation_count(visit_engine)==0
    if mode=='no_slot':
        from types import SimpleNamespace
        from bring_vene.speech.service import scope_allows
        with Session(visit_engine) as session:
            row=session.get(ExecutionRecord,aid);view=EncounterView.model_validate(session.get(EncounterRecord,FIXTURE_VISIT).projection)
            cue=SimpleNamespace(content={'plan_ids':[str(item)],'execution_snapshots':{str(aid):service.snapshot(row)}})
            assert scope_allows(session,None,view,cue)
            future=utc_now()+timedelta(minutes=3);monkeypatch.setattr(service,'utc_now',lambda:future)
            assert not scope_allows(session,None,view,cue)

def test_stale_approval_and_availability_change_reject_without_false_confirmation(visit_engine):
    p,d,f,item,b=setup(visit_engine);aid=check(visit_engine,p,item,b);old=action(visit_engine,p,aid).digest
    ready(visit_engine,p,d,aid,b)
    with pytest.raises(DomainError):service.approve(visit_engine,FIXTURE_VISIT,aid,*cred(p),ApprovalRequest(digest=old))
    authorize(visit_engine,p,aid);b.call('/scenario',{'mode':'normal'});service.dispatch(visit_engine,SETTINGS,gateway=b)
    assert action(visit_engine,p,aid).state=='rejected'

def test_office_rejects_forged_orders_and_conflicting_idempotency_payloads(visit_engine):
    p,d,f,item,b=setup(visit_engine)
    assert b.client.post('/lookup',json={'window':'morning'}).status_code==403
    order=uuid4();b.call('/orders',{'request_id':str(order)})
    lookup=b.call('/lookup',{'window':'morning'});aid=uuid4()
    payload={'request_id':str(aid),'slot_id':lookup['slot']['id'],'availability_revision':lookup['revision'],'order_id':str(order)}
    first=b.call('/bookings',payload);second=b.call('/bookings',payload)
    assert first==second and reservation_count(visit_engine)==1
    headers={'Authorization':'Bearer '+SETTINGS.office_token}
    assert b.client.post('/bookings',json={**payload,'slot_id':'other'},headers=headers).status_code==409
    assert b.client.post('/bookings',json={**payload,'request_id':str(uuid4()),'order_id':str(uuid4())},headers=headers).status_code==409
    b.call('/scenario',{'mode':'normal'})
    assert b.call('/lookup',{'window':'morning'})['slot'] is None # revision changes cannot resurrect a reserved slot

def test_expired_worker_lease_reconciles_send_intent(visit_engine):
    p,d,f,item,b=setup(visit_engine);aid=check(visit_engine,p,item,b);ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid)
    claimed=service.claim(visit_engine)
    with Session(visit_engine) as session,session.begin():
        row=session.get(ExecutionRecord,aid);row.state='in_flight';row.content={**row.content,'send_started':True}
        session.get(ExecutionOutboxRecord,aid).lease_until=utc_now()-timedelta(seconds=1)
    service.dispatch(visit_engine,SETTINGS,gateway=b)
    assert '/requests/'+str(aid) in b.calls;assert reservation_count(visit_engine)==1
    service.dispatch(visit_engine,SETTINGS,claimed=claimed,gateway=b)
    assert reservation_count(visit_engine)==1

def test_missing_office_does_not_return_fixture_success_and_duplicate_events_are_idempotent(visit_engine):
    p,d,f,item,b=setup(visit_engine)
    service.scope(visit_engine,FIXTURE_VISIT,item,*cred(p),ScopeRequest(allowed=True))
    aid=service.lookup(visit_engine,FIXTURE_VISIT,item,*cred(p),LookupRequest(window='morning'),Settings())
    assert action(visit_engine,p,aid).state=='unavailable';assert reservation_count(visit_engine)==0
    b.call('/scenario',{'mode':'duplicate_callback'});aid=check(visit_engine,p,item,b)
    ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid);service.dispatch(visit_engine,SETTINGS,gateway=b)
    assert action(visit_engine,p,aid).state=='confirmed' and reservation_count(visit_engine)==1
    assert 'duplicate_events' not in action(visit_engine,p,aid).receipt

def test_network_wait_does_not_hold_visit_lock_and_already_dispatched_receipt_survives(visit_engine):
    p,d,f,item,b=setup(visit_engine);aid=check(visit_engine,p,item,b);ready(visit_engine,p,d,aid,b);authorize(visit_engine,p,aid)
    class WithdrawDuringSend:
        def call(self,path,payload=None):
            if path=='/bookings':
                # This executes a genuine competing visit mutation while network
                # dispatch is pending. Holding the encounter lock would deadlock.
                service.scope(visit_engine,FIXTURE_VISIT,item,*cred(p),ScopeRequest(allowed=False))
            return b.call(path,payload)
    service.dispatch(visit_engine,SETTINGS,gateway=WithdrawDuringSend())
    assert action(visit_engine,p,aid).state=='confirmed';assert reservation_count(visit_engine)==1
