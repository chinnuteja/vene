"""Phase 9: a scoped care-circle ask about a confirmed errand."""
from sqlalchemy.orm import Session
from bring_vene.auth import FIXTURE_VISIT,FIXTURE_MEMBERS
from bring_vene.domain.contracts import EncounterView
from bring_vene.domain.service import utc_now
from bring_vene.execution import service
from bring_vene.persistence.models import EncounterRecord,MembershipRecord
from test_errands import setup,check,bundle
from test_execution import SETTINGS,action,ready

CIRCLE=f'/encounters/{FIXTURE_VISIT}/care-circle'
FAMILY=str(FIXTURE_MEMBERS['family'])

def confirmed(engine,shared=True):
    p,d,f,items,b=setup(engine,('lab',),shared=shared)
    aid=check(engine,p,items['lab'],b,'lab');ready(engine,p,d,aid,b)
    bundle(engine,p,[action(engine,p,aid).digest]);service.dispatch(engine,SETTINGS,gateway=b)
    assert action(engine,p,aid).state=='confirmed'
    return p,d,f,items,aid

def unshare(engine,item_id):
    with Session(engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);view=EncounterView.model_validate(record.projection)
        next(i for i in view.plan if i.id==item_id).audiences=['clinician']
        record.projection=view.model_dump(mode='json')

def test_family_receives_only_when_where_and_purpose_and_answers_for_themselves(visit_engine):
    p,d,f,items,aid=confirmed(visit_engine)
    response=p.post(CIRCLE+'/rides',json={'action_id':str(aid),'recipient_id':FAMILY})
    assert response.status_code==200
    ride=response.json()['rides'][0]
    assert ride['state']=='asked' and ride['purpose']=='Arrange the lab visit'
    assert ride['when']=='Tue, Oct 20 · 9:00 AM ET' and ride['where']=='Riverside Lab (fictional)'
    family_view=f.get(CIRCLE).json()['rides']
    assert [r['id'] for r in family_view]==[ride['id']]
    payload=f.get(CIRCLE).text
    for private in ['receipt','slot_id','order','digest','session','Maria will arrange']:
        assert private not in payload
    assert d.get(CIRCLE).json()['rides']==[]
    assert d.post(CIRCLE+f"/rides/{ride['id']}/answer",json={'answer':'yes'}).status_code==404
    assert p.post(CIRCLE+f"/rides/{ride['id']}/answer",json={'answer':'yes'}).status_code==404
    answered=f.post(CIRCLE+f"/rides/{ride['id']}/answer",json={'answer':'yes'}).json()['rides'][0]
    assert answered['state']=='accepted' and answered['answered_at']
    assert p.get(CIRCLE).json()['rides'][0]['state']=='accepted'
    # Asking again is idempotent while the ask is open.
    assert len(p.post(CIRCLE+'/rides',json={'action_id':str(aid),'recipient_id':FAMILY}).json()['rides'])==1

def test_unconfirmed_or_unshared_steps_cannot_be_asked(visit_engine):
    p,d,f,items,b=setup(visit_engine,('lab',))
    aid=check(visit_engine,p,items['lab'],b,'lab')
    assert p.post(CIRCLE+'/rides',json={'action_id':str(aid),'recipient_id':FAMILY}).status_code==409
    p2,_,_,_,aid2=confirmed(visit_engine,shared=False)
    assert p2.post(CIRCLE+'/rides',json={'action_id':str(aid2),'recipient_id':FAMILY}).status_code==409
    assert p2.post(CIRCLE+'/rides',json={'action_id':str(aid2),'recipient_id':str(FIXTURE_MEMBERS['clinician'])}).status_code==409

def test_unsharing_removes_the_ask_from_the_family_payload_and_blocks_answers(visit_engine):
    p,d,f,items,aid=confirmed(visit_engine)
    ride=p.post(CIRCLE+'/rides',json={'action_id':str(aid),'recipient_id':FAMILY}).json()['rides'][0]
    unshare(visit_engine,items['lab'])
    assert f.get(CIRCLE).json()['rides']==[]
    assert 'Riverside' not in f.get(CIRCLE).text
    assert f.post(CIRCLE+f"/rides/{ride['id']}/answer",json={'answer':'yes'}).status_code==409
    assert p.get(CIRCLE).json()['rides'][0]['state']=='unavailable'

def test_withdrawn_or_revoked_family_cannot_answer(visit_engine):
    p,d,f,items,aid=confirmed(visit_engine)
    ride=p.post(CIRCLE+'/rides',json={'action_id':str(aid),'recipient_id':FAMILY}).json()['rides'][0]
    p.post(CIRCLE+f"/rides/{ride['id']}/withdraw")
    assert f.get(CIRCLE).json()['rides']==[]
    assert f.post(CIRCLE+f"/rides/{ride['id']}/answer",json={'answer':'yes'}).status_code==409
    again=p.post(CIRCLE+'/rides',json={'action_id':str(aid),'recipient_id':FAMILY}).json()['rides']
    fresh=next(r for r in again if r['state']=='asked')
    with Session(visit_engine) as session,session.begin():
        session.get(MembershipRecord,FIXTURE_MEMBERS['family']).revoked_at=utc_now()
    assert f.post(CIRCLE+f"/rides/{fresh['id']}/answer",json={'answer':'yes'}).status_code==401
    assert next(r for r in p.get(CIRCLE).json()['rides'] if r['id']==fresh['id'])['state']=='unavailable'


def test_a_step_shared_with_family_after_booking_can_still_be_asked(visit_engine):
    p,d,f,items,aid=confirmed(visit_engine,shared=False)
    assert p.post(CIRCLE+'/rides',json={'action_id':str(aid),'recipient_id':FAMILY}).status_code==409
    with Session(visit_engine) as session,session.begin():
        record=session.get(EncounterRecord,FIXTURE_VISIT);view=EncounterView.model_validate(record.projection)
        item=next(i for i in view.plan if i.id==items['lab'])
        for source in view.evidence:
            if source.id in item.evidence_refs:source.audiences=sorted({*source.audiences,'family'})
        item.audiences=['clinician','family'];record.projection=view.model_dump(mode='json')
    response=p.post(CIRCLE+'/rides',json={'action_id':str(aid),'recipient_id':FAMILY})
    assert response.status_code==200 and response.json()['rides'][0]['state']=='asked'
