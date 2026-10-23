import json
from uuid import UUID,uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from bring_vene.auth import FIXTURE_VISIT
from bring_vene.config import Settings
from bring_vene.main import create_app
from bring_vene.persistence.models import EncounterRecord


def test_fresh_demo_does_not_overwrite_saved_visits_and_uses_ordinary_sessions(visit_engine):
    app=create_app(Settings(bring_vene_development=True,cookie_secure=False),visit_engine)
    bootstrap=TestClient(app)
    with Session(visit_engine) as session:before=json.dumps(session.get(EncounterRecord,FIXTURE_VISIT).projection,sort_keys=True)
    first=bootstrap.post('/dev/demo',headers={'x-vene-intent':'mutation'}).json()
    second=bootstrap.post('/dev/demo',headers={'x-vene-intent':'mutation'}).json()
    assert first['run']!=second['run'] and first['synthetic']
    clients={}
    for role in ['patient','clinician','family']:
        client=TestClient(app)
        r=client.post('/auth/redeem',headers={'x-vene-intent':'mutation'},json={'token':first['invitations'][role]})
        assert r.status_code==200 and r.json()['role']==role and r.json()['encounter_id']==first['run']
        assert client.get('/encounters/'+second['run']).status_code==404
        clients[role]=client
    for role in ['clinician','family']:
        body=clients[role].get('/encounters/'+first['run']).json()
        assert body['priorities']==[] and body['evidence']==[] and body['plan']==[]
        assert 'PRIVATE_CANARY' not in json.dumps(body)
    assert 'PRIVATE_CANARY' in clients['patient'].get('/encounters/'+first['run']).text
    assert bootstrap.post('/auth/redeem',headers={'x-vene-intent':'mutation'},json={'token':first['invitations']['patient']}).status_code==401
    with Session(visit_engine) as session:
        assert json.dumps(session.get(EncounterRecord,FIXTURE_VISIT).projection,sort_keys=True)==before


def test_demo_bootstrap_requires_explicit_fictional_configuration(visit_engine):
    client=TestClient(create_app(Settings(bring_vene_development=False),visit_engine))
    assert client.post('/dev/demo',headers={'x-vene-intent':'mutation'}).status_code==404
    assert client.get('/dev/demo-info').status_code==404


def test_sample_instruction_is_own_clinician_only_and_never_a_live_fallback(visit_engine):
    settings=Settings(bring_vene_development=True,cookie_secure=False,voice_provider='fixture',model_provider='fixture')
    app=create_app(settings,visit_engine);bootstrap=TestClient(app)
    demo=bootstrap.post('/dev/demo',headers={'x-vene-intent':'mutation'}).json();root='/encounters/'+demo['run']
    clients={}
    for role,invite in demo['invitations'].items():
        client=TestClient(app);viewer=client.post('/auth/redeem',headers={'x-vene-intent':'mutation'},json={'token':invite}).json()
        client.headers.update({'x-vene-intent':'mutation','x-vene-csrf':viewer['csrf_token']});clients[role]=client
    refused=clients['clinician'].post(root+'/demo/turn',json={'token':str(uuid4()),'line':'errands'})
    assert refused.status_code==409 and refused.json()['detail']=='Maria must first allow private understanding.'
    assert not [e for e in clients['patient'].get(root).json()['evidence'] if e.get('origin')=='fixture']
    clients['patient'].post(root+'/understanding/processing',json={'command_id':str(uuid4()),'enabled':True})
    for role in ['patient','family']:
        assert clients[role].post(root+'/demo/turn',json={'token':str(uuid4())}).status_code==403
    command={'token':str(uuid4())}
    for _ in range(2):assert clients['clinician'].post(root+'/demo/turn',json=command).status_code==200
    assert len([e for e in clients['patient'].get(root).json()['evidence'] if e.get('origin')=='fixture'])==1
    settings.voice_provider='deepgram'
    assert clients['clinician'].post(root+'/demo/turn',json={'token':str(uuid4())}).status_code==409


def test_each_demo_has_its_own_history_and_a_second_allow_listed_line(visit_engine):
    settings=Settings(bring_vene_development=True,cookie_secure=False,voice_provider='fixture',model_provider='fixture')
    app=create_app(settings,visit_engine);bootstrap=TestClient(app)
    runs=[bootstrap.post('/dev/demo',headers={'x-vene-intent':'mutation'}).json() for _ in range(2)]
    clients=[]
    for demo in runs:
        roles={}
        for role,invite in demo['invitations'].items():
            client=TestClient(app);viewer=client.post('/auth/redeem',headers={'x-vene-intent':'mutation'},json={'token':invite}).json()
            client.headers.update({'x-vene-intent':'mutation','x-vene-csrf':viewer['csrf_token']});roles[role]=client
        clients.append(roles)
    root='/encounters/'+runs[0]['run']
    memory=clients[0]['patient'].get(root+'/memory').json()
    assert memory['past_visits']==1 and len(memory['loops'])>=2
    # A run's history belongs to that run's fictional patient only, and guests never read it.
    assert clients[0]['clinician'].get(root+'/memory').status_code in (403,404)
    patients={c['patient'].get('/encounters/'+d['run']).json()['patient']['id'] for c,d in zip(clients,runs)}
    assert len(patients)==2
    assert clients[0]['clinician'].post(root+'/demo/turn',json={'token':str(uuid4()),'line':'anything'}).status_code==422
    clients[0]['patient'].post(root+'/understanding/processing',json={'command_id':str(uuid4()),'enabled':True})
    assert clients[0]['clinician'].post(root+'/demo/turn',json={'token':str(uuid4()),'line':'errands'}).status_code==200
    import asyncio
    from bring_vene.understanding import service as understanding
    from bring_vene.understanding.gateway import ModelGateway
    run_id,snapshot=understanding.prepare(visit_engine,UUID(runs[0]['run']),settings)
    assert understanding.apply_result(visit_engine,run_id,asyncio.run(ModelGateway(settings).extract(snapshot)),settings)
    plan={step['kind']:step for step in clients[0]['patient'].get(root).json()['plan']}
    assert plan['imaging']['location']=='Lakeside Imaging' and plan['prescription']['location']=='Main Street Pharmacy'
