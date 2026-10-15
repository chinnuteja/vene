from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from bring_vene.auth import COOKIE
from bring_vene.config import Settings
from bring_vene.fixtures import CASES,ensure_case,visit_id,members
from bring_vene.main import create_app
from bring_vene.domain.contracts import EncounterView
from bring_vene.persistence.models import EncounterRecord
from bring_vene.understanding.gateway import fixture_extract

def launch(app,case,role):
    client=TestClient(app);invite=client.post('/dev/invitations',headers={'x-vene-intent':'mutation'},json={'persona':role,'case':case})
    assert invite.status_code==200
    redeemed=client.post('/auth/redeem',headers={'x-vene-intent':'mutation'},json={'token':invite.json()['token']});assert redeemed.status_code==200
    client.headers.update({'x-vene-intent':'mutation','x-vene-csrf':redeemed.json()['csrf_token']});return client

def test_three_fictional_cases_are_distinct_private_and_seed_preserves_edits(visit_engine):
    settings=Settings(bring_vene_development=True,cookie_secure=False);app=create_app(settings,visit_engine)
    patients={case:launch(app,case,'patient') for case in CASES}
    for case,p in patients.items():
        view=p.get('/encounters/'+str(visit_id(case))).json();assert view['patient']['name']==CASES[case]['name']
        assert all(not q['audiences'] for q in view['priorities'])
        for other in CASES:
            if other!=case:assert p.get('/encounters/'+str(visit_id(other))).status_code==404
        for role in ['clinician','family']:
            guest=launch(app,case,role);payload=guest.get('/encounters/'+str(visit_id(case))).text;assert 'PRIVATE_CANARY' not in payload
    with Session(visit_engine) as session,session.begin():
        row=session.get(EncounterRecord,visit_id('james'));view=EncounterView.model_validate(row.projection);view.title='My preserved synthetic edit';row.projection=view.model_dump(mode='json')
    ensure_case(visit_engine,'james')
    assert patients['james'].get('/encounters/'+str(visit_id('james'))).json()['title']=='My preserved synthetic edit'

def test_case_bootstrap_is_not_available_without_explicit_local_fixture_configuration(visit_engine):
    app=create_app(Settings(bring_vene_development=False),visit_engine);client=TestClient(app)
    assert client.get('/dev/cases').status_code==404
    assert client.post('/dev/invitations',headers={'x-vene-intent':'mutation'},json={'persona':'patient','case':'asha'}).status_code==404

def test_original_fixture_variations_remain_proposals_with_exact_source_citations():
    for name,day,place in [('James','Wednesday','Harbor Lab'),('Asha','Friday','Hilltop Lab')]:
        source={'id':str(uuid4()),'version':1,'speaker':'Dr. Chris Chen','origin':'fixture','text':f'{name} will arrange the lab visit at {place} on {day} after the office sends the order.'}
        result=fixture_extract({'sources':[source],'priorities':[{'id':str(uuid4()),'title':'Where should I arrange the lab visit?','detail':''}]})
        assert result.steps[0].owner==name and result.steps[0].timeframe==day and result.steps[0].location==place
        assert result.steps[0].citations[0].quote==source['text']


def test_fictional_turn_uses_the_selected_encounters_actual_membership(visit_engine):
    app=create_app(Settings(bring_vene_development=True,cookie_secure=False),visit_engine)
    for case in ['james','asha']:
        patient=launch(app,case,'patient');launch(app,case,'clinician')
        root='/encounters/'+str(visit_id(case))
        assert patient.post(root+'/understanding/processing',json={'command_id':str(uuid4()),'enabled':True}).status_code==200
        result=patient.post(root+'/understanding/fixture-turns',json={'command_id':str(uuid4()),'speaker':'clinician','text':'Original fictional lab visit plan on Friday.'})
        assert result.status_code==200
        assert any(e['origin']=='fixture' and e['text']=='Original fictional lab visit plan on Friday.' for e in result.json()['evidence'])
