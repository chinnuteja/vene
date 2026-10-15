"""Three explicit fictional encounters; seeded only in local fixture mode."""
import json
from pathlib import Path
from uuid import UUID,uuid5,NAMESPACE_URL
from sqlalchemy.orm import Session
from bring_vene.auth import FIXTURE_VISIT,FIXTURE_MEMBERS
from bring_vene.domain.contracts import EncounterView
from bring_vene.persistence.models import EncounterRecord,EvidenceRecord,MembershipRecord

CASES={
    'maria':{'name':'Maria Alvarez','preferred':'Maria','age':72,'family':'Elena Alvarez','description':'Referral question, morning preference and a corrected appointment window.'},
    'james':{'name':'James Patel','preferred':'James','age':79,'family':'Nina Patel','description':'Different lab/date, a missing order and a rejected office request.'},
    'asha':{'name':'Asha Rao','preferred':'Asha','age':68,'family':'Arun Rao','description':'Afternoon transport, late office replies and conflicting after-visit instructions.'},
}

def visit_id(case):return FIXTURE_VISIT if case=='maria' else uuid5(NAMESPACE_URL,'bring-vene:fictional:'+case)
def members(case):return FIXTURE_MEMBERS if case=='maria' else {role:uuid5(visit_id(case),role) for role in FIXTURE_MEMBERS}

def ensure_case(engine,case):
    if case not in CASES:raise ValueError('Unknown fictional case.')
    if case=='maria':
        from bring_vene.seed import seed
        seed(engine);return visit_id(case)
    template=json.loads((Path(__file__).resolve().parents[4]/'fixtures/maria.json').read_text(encoding='utf-8'))
    info=CASES[case];vid=visit_id(case);mapping={}
    for collection in ['priorities','plan','evidence']:
        for entry in template[collection]:mapping[entry['id']]=str(uuid5(vid,entry['id']))
    template['id']=str(vid);template['patient']={'id':str(uuid5(vid,'patient-person')),'name':info['name'],'preferred_name':info['preferred'],'age':info['age']}
    for collection in ['priorities','plan','evidence']:
        for entry in template[collection]:
            entry['id']=mapping[entry['id']]
            if 'evidence_refs' in entry:entry['evidence_refs']=[mapping[x] for x in entry['evidence_refs']]
            for key in ['title','detail','text']:
                if key in entry:entry[key]=entry[key].replace('Maria',info['preferred']).replace('Elena',info['family'].split()[0]).replace('PRIVATE_CANARY_MARIA_BLUE_ORCHID','PRIVATE_CANARY_'+case.upper()+'_DO_NOT_SHARE')
    if case=='asha':
        template['priorities'][2]['title']='Mention my afternoon transport window';template['priorities'][2]['detail']='My ride is available in the afternoon. Confirm the date and place before arranging anything.'
        template['evidence'][2]['text']='Afternoon appointments work with my ride; I need an agreed date and place.'
    view=EncounterView.model_validate(template)
    with Session(engine) as session,session.begin():
        if session.get(EncounterRecord,vid):return vid # Never overwrite saved fixture changes.
        session.add(EncounterRecord(id=vid,version=0,projection=view.model_dump(mode='json'),updated_at=view.updated_at));session.flush()
        for source in view.evidence:session.add(EvidenceRecord(id=source.id,encounter_id=vid,content=source.model_dump(mode='json')))
        for role,mid in members(case).items():session.add(MembershipRecord(id=mid,encounter_id=vid,role=role,
            name=info['name'] if role=='patient' else info['family'] if role=='family' else 'Dr. Chris Chen'))
    return vid
