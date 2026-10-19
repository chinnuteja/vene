import asyncio
from uuid import UUID,uuid4
import pytest
from fastapi.testclient import TestClient
from bring_vene.auth import COOKIE
from bring_vene.config import Settings
from bring_vene.main import create_app
from bring_vene.execution.office import initialize,office_app
from bring_vene.feasibility import service as feasibility
from bring_vene.understanding import service as understanding
from bring_vene.understanding.gateway import ModelGateway

SETTINGS=Settings(bring_vene_development=True,cookie_secure=False,office_url='http://127.0.0.1:8012',office_token='isolated-deadline-test')


class Calendar:
    def __init__(self,engine,run):
        initialize(engine);self.calls=[]
        self.client=TestClient(office_app(SETTINGS,engine));self.client.headers.update({
            'authorization':'Bearer '+SETTINGS.office_token,'x-vene-sandbox-run':run})
    def call(self,path,payload=None):
        self.calls.append(path)
        r=self.client.post(path,json=payload) if payload is not None else self.client.get(path)
        assert r.status_code==200,r.text
        return r.json()


def scenario(engine):
    app=create_app(SETTINGS,engine);bootstrap=TestClient(app)
    seed=bootstrap.post('/dev/demo',headers={'x-vene-intent':'mutation'}).json()
    clients={}
    for role,invitation in seed['invitations'].items():
        c=TestClient(app);me=c.post('/auth/redeem',headers={'x-vene-intent':'mutation'},json={'token':invitation}).json()
        c.headers.update({'x-vene-intent':'mutation','x-vene-csrf':me['csrf_token']});clients[role]=c
    return seed['run'],clients,Calendar(engine,seed['run'])


def plan(engine,run,p):
    root='/encounters/'+run
    assert p.post(root+'/understanding/processing',json={'command_id':str(uuid4()),'enabled':True}).status_code==200
    assert p.post(root+'/understanding/fixture-turns',json={'command_id':str(uuid4()),'speaker':'clinician',
        'text':'Please get labs done within three days. We can send the lab order today.'}).status_code==200
    run_id,snapshot=understanding.prepare(engine,UUID(run),SETTINGS)
    result=asyncio.run(ModelGateway(SETTINGS).extract(snapshot))
    assert understanding.apply_result(engine,run_id,result,SETTINGS)
    return p.get(root).json()['plan'][0]


def share(p,root,item_id):
    version=p.get(root).json()['version']
    r=p.post(root+'/commands',json={'command_id':str(uuid4()),'expected_version':version,
        'command':{'type':'sharing.changed','item_id':item_id,'audiences':['clinician']}})
    assert r.status_code==200


def test_deadline_finds_actual_alternative_without_inventing_an_order_or_leaking_preference(visit_engine):
    run,clients,calendar=scenario(visit_engine);p,d,f=[clients[r] for r in ['patient','clinician','family']]
    root='/encounters/'+run;item=plan(visit_engine,run,p)
    assert item['timeframe']=='within three days' and item['location'] is None and not item['order_available']
    assert not feasibility.tick(visit_engine,SETTINGS,calendar) and calendar.calls==[]
    p.post(root+'/feasibility/standing',json={'kinds':['scheduling']})
    assert feasibility.tick(visit_engine,SETTINGS,calendar)
    [obstacle]=p.get(root+'/feasibility').json()['obstacles']
    assert obstacle['fact']=='Riverside Lab has no slot before Friday — Northside has Thursday 9am.'
    assert obstacle['alternative']['day']=='2026-10-22' and obstacle['alternative']['starts_at'].endswith('09:00:00-04:00')
    assert calendar.calls==['/availability']
    for source in item['evidence_refs']:share(p,root,source)
    share(p,root,item['id'])
    # Sharing changes the approval fingerprint; the running worker rechecks that current version.
    assert feasibility.tick(visit_engine,SETTINGS,calendar)
    # Sharing a general lab instruction does not share Maria's private facility preference.
    assert d.get(root+'/feasibility').json()['obstacles']==[]
    for source in obstacle['supporting_sources']:share(p,root,str(source))
    assert feasibility.tick(visit_engine,SETTINGS,calendar)
    assert len(d.get(root+'/feasibility').json()['obstacles'])==1
    assert f.get(root+'/feasibility').json()['obstacles']==[]
    assert d.get(root).json()['lab_preference'] is None
    # A correction fences the old fact immediately, before the asynchronous worker runs again.
    changed=p.post(root+'/understanding/plan/'+item['id']+'/correct',json={'command_id':str(uuid4()),
        'expected_item_revision':item['revision'],'detail':'The clinician clarified labs within one day.',
        'owner':None,'timeframe':'within one day','location':None})
    assert changed.status_code==200
    assert p.get(root+'/feasibility').json()['obstacles']==[]
    assert p.post(root+'/speech/actions',json={'command_id':str(uuid4()),'type':'refresh'}).status_code==200
    assert not any(c['title'].startswith('Practical check') for c in p.get(root+'/speech').json()['cues'])


def test_each_demo_has_its_own_calendar_and_cross_demo_orders_are_refused(visit_engine):
    first,_,a=scenario(visit_engine);second,_,b=scenario(visit_engine)
    payload={'window':'morning','location':'Northside','day':'2026-10-22'}
    one=a.call('/lookup',payload);two=b.call('/lookup',payload)
    assert one['slot']['id']!=two['slot']['id']
    order=uuid4();a.call('/orders',{'request_id':str(order)})
    body={'request_id':str(uuid4()),'slot_id':two['slot']['id'],'availability_revision':two['revision'],'order_id':str(order)}
    assert b.client.post('/bookings',json=body).status_code==409
    assert b.client.get('/requests/'+str(order)).json()['found'] is False


def test_outside_deadline_is_refused_before_an_office_lookup(visit_engine):
    run,clients,calendar=scenario(visit_engine);p=clients['patient'];root='/encounters/'+run
    item=plan(visit_engine,run,p)
    p.post(root+'/execution/items/'+item['id']+'/scope',json={'allowed':True})
    result=p.post(root+'/execution/items/'+item['id']+'/lookup',json={'window':'morning','location':'Riverside Lab','day':'2026-10-23'})
    assert result.status_code==422 and calendar.calls==[]


def test_calendar_timeout_is_visible_to_patient_and_a_retry_uses_a_fresh_check(visit_engine):
    run,clients,calendar=scenario(visit_engine);p=clients['patient'];root='/encounters/'+run
    plan(visit_engine,run,p)
    p.post(root+'/feasibility/standing',json={'kinds':['scheduling']})
    class TimeoutCalendar:
        def call(self,*args,**kwargs):raise TimeoutError()
    assert feasibility.tick(visit_engine,SETTINGS,TimeoutCalendar())
    view=p.get(root+'/feasibility').json()
    assert view['failed']==1 and view['obstacles']==[]
    assert clients['clinician'].get(root+'/feasibility').json()['failed']==0
    assert clients['family'].get(root+'/feasibility').json()['failed']==0
    p.post(root+'/feasibility/standing',json={'kinds':['scheduling']})
    assert feasibility.tick(visit_engine,SETTINGS,calendar)
    view=p.get(root+'/feasibility').json()
    assert view['failed']==0 and len(view['obstacles'])==1


def test_sharing_instruction_and_preference_is_one_authorized_atomic_change(visit_engine):
    run,clients,_=scenario(visit_engine);p,d=clients['patient'],clients['clinician'];root='/encounters/'+run
    item=plan(visit_engine,run,p);view=p.get(root).json();ids=[item['id'],*item['evidence_refs'],view['lab_preference']['source_id']]
    changes=[{'item_id':id,'audiences':['clinician']}for id in set(ids)]
    def command(changes):return {'command_id':str(uuid4()),'expected_version':view['version'],'command':{'type':'sharing.batch_changed','changes':changes}}
    assert d.post(root+'/commands',json=command(changes)).status_code==403
    assert p.post(root+'/commands',json=command(changes+[{'item_id':str(uuid4()),'audiences':['clinician']}])).status_code==404
    assert p.get(root).json()['version']==view['version'] and d.get(root).json()['evidence']==[]
    request=command(changes);r=p.post(root+'/commands',json=request)
    assert r.status_code==200 and r.json()['encounter']['version']==view['version']+1
    assert p.post(root+'/commands',json=request).json()['duplicate']
    shared=d.get(root).json();assert len(shared['plan'])==1 and len(shared['evidence'])==2
    assert all('family'not in source['audiences']for source in p.get(root).json()['evidence'])
