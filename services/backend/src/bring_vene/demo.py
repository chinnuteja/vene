"""Fresh, fictional demo visits. Invitations redeem through ordinary auth; no role bypass."""
import json
from datetime import datetime,timezone
from pathlib import Path
from uuid import UUID,uuid4,uuid5
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from bring_vene.auth import issue_invitation,authenticate
from bring_vene.domain.contracts import EncounterView
from bring_vene.domain.service import DomainError,utc_now
from bring_vene.persistence.models import EncounterRecord,EvidenceRecord,MembershipRecord

ROOT=Path(__file__).resolve().parents[4]

SCRIPT='Please get labs done within three days. We can send the lab order today.'
# Later in the same visit. Each sentence is its own turn so every step keeps its own source.
LINES={'labs':[SCRIPT],
       'errands':['Maria will schedule the MRI at Lakeside Imaging on Wednesday after the office sends the order.',
                  'Maria will pick up the new prescription at Main Street Pharmacy on Thursday.']}


def fixture_turn(engine,visit_id,token,csrf,command,settings,line='labs'):
    from bring_vene.understanding import service
    from bring_vene.understanding.contracts import Mutation
    from bring_vene.understanding.gateway import configuration
    from bring_vene.voice.service import provider
    if configuration(settings)[0]!='fixture' or provider(settings)!='fixture':
        raise DomainError(409,'This is a live voice demo. Speak the instruction through the agreed microphone; no scripted fallback was used.')
    try:request=Mutation(command_id=UUID(command))
    except ValueError:raise DomainError(422,'A fresh command is required.')
    with Session(engine) as session,session.begin():
        encounter,row,view=service.lock(session,visit_id)
        member,_=authenticate(session,token,visit_id,csrf,mutate=True)
        if not view.demo_run or member.role!='clinician':raise DomainError(403,'Only the invited fictional clinician can send this sample instruction.')
        if not row.enabled:raise DomainError(409,'Maria must first allow private understanding.')
        if service.mutation(session,visit_id,member,request,'demo_fixture_turn'):
            for text in LINES[line]:service.add_source(session,encounter,row,view,member,text,'fixture',settings)
    return {'accepted':True,'origin':'fixture','text':' '.join(LINES[line])}


def seed_history(engine,remap):
    """Maria's fictional July visit, for this run's Maria only, so preparation can find what was left open."""
    from bring_vene.seed import seed_history as add
    history=remap(json.loads((ROOT/'fixtures/maria-history.json').read_text(encoding='utf-8')))
    add(engine,EncounterView.model_validate(history))


def create(engine):
    run=uuid4()
    def remap(value):
        if isinstance(value,dict):return {k:remap(v) for k,v in value.items()}
        if isinstance(value,list):return [remap(v) for v in value]
        if isinstance(value,str):
            try:return str(uuid5(run,str(UUID(value))))
            except ValueError:pass
        return value
    fixture=json.loads((ROOT/'fixtures/maria.json').read_text(encoding='utf-8'))
    data=remap(fixture)
    data.update(id=str(run),title='Maria’s visit with Dr. Chen',version=0,consent_epoch=0,plan=[],
                visit_at='2026-10-19T15:00:00Z',updated_at=utc_now().isoformat(),preparation_approved=False,
                processing_state='preparing',understanding=None,demo_run=str(run))
    for question in data['priorities']:
        # Questions Maria already chose are addressed to Dr. Chen; approval still releases them.
        question.update(approved=False,audiences=['clinician'] if question.get('selected') else [])
    preference=data['evidence'][2]
    preference['text']='I usually go to Riverside Lab. Mornings are easier for me, and Elena can drive me on Thursday.'
    data['lab_preference']={'location':'Riverside Lab','source_id':preference['id']}
    view=EncounterView.model_validate(data)
    with Session(engine) as session,session.begin():
        # Public fictional hosting stays bounded. A busy demo fails honestly instead of erasing saved visits.
        count=session.scalar(select(func.count()).select_from(EncounterRecord).where(
            EncounterRecord.projection['demo_run'].astext.is_not(None)))
        if count>=100:raise DomainError(429,'This demo is busy. Please try a saved demonstration or return later.')
        session.add(EncounterRecord(id=run,version=0,projection=view.model_dump(mode='json'),updated_at=view.updated_at))
        session.flush()
        from bring_vene.execution.office import create_calendar
        create_calendar(session,run)
        for source in view.evidence:
            session.add(EvidenceRecord(id=source.id,encounter_id=run,content=source.model_dump(mode='json')))
        invitations={}
        for role,name in [('patient','Maria Alvarez'),('clinician','Dr. Chris Chen'),('family','Elena Alvarez')]:
            member=MembershipRecord(id=uuid4(),encounter_id=run,role=role,name=name)
            session.add(member);session.flush()
            invitations[role]=issue_invitation(session,member).token
    seed_history(engine,remap)
    return {'run':str(run),'invitations':invitations,'visit_day':'Monday, October 19, 2026','synthetic':True}
