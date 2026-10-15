"""Explicitly reset only the three known fictional roots and their derived visits."""
import argparse,json,os
from pathlib import Path
from uuid import UUID
from sqlalchemy import select,delete
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import (EncounterRecord,NextVisitRecord,ExecutionRecord,OfficeRequestRecord,OfficeStateRecord,
    OfficeFamilyReceiptRecord,FamilyUpdateRecord,CallRecord)
from bring_vene.fixtures import CASES,ensure_case,visit_id
from bring_vene.execution.office import initialize

parser=argparse.ArgumentParser();parser.add_argument('--test',action='store_true');parser.add_argument('--reset-saved-synthetic-visits',action='store_true')
args=parser.parse_args();root=Path(__file__).resolve().parent.parent
runtime=json.loads((root/'.local/runtime.json').read_text(encoding='utf-8-sig'))
url=runtime['test_database_url' if args.test else 'database_url'];parsed=make_url(url)
if parsed.host!='127.0.0.1' or parsed.database!=('bring_vene_test' if args.test else 'bring_vene'):raise RuntimeError('Only the verified project-local database is allowed.')
if not args.test and not args.reset_saved_synthetic_visits:raise RuntimeError('Saved fictional edits are preserved by default. Use --reset-saved-synthetic-visits only for an intentional demo reset.')
if not args.test and (root/'.local/processes.json').exists():raise RuntimeError('Stop the owned application with scripts/stop.ps1 before resetting saved fictional visits.')
engine=make_engine(url)
try:
    with Session(engine) as session,session.begin():
        ids=[];todo=[visit_id(case) for case in CASES]
        while todo:
            vid=todo.pop()
            if vid in ids:continue
            ids.append(vid);todo.extend(session.scalars(select(NextVisitRecord.next_id).where(NextVisitRecord.origin_id==vid)).all())
        calls=session.scalars(select(CallRecord).where(CallRecord.encounter_id.in_(ids))).all()
        if any(not c.ended and c.active_tasks for c in calls):raise RuntimeError('End active processing before a demo reset.')
        action_ids=session.scalars(select(ExecutionRecord.id).where(ExecutionRecord.encounter_id.in_(ids))).all()
        update_ids=session.scalars(select(FamilyUpdateRecord.id).where(FamilyUpdateRecord.encounter_id.in_(ids))).all()
        requests=session.scalars(select(OfficeRequestRecord).where(OfficeRequestRecord.request_id.in_(action_ids))).all()
        slots={r.content['result']['slot_id'] for r in requests if r.kind=='booking' and r.content['result']['status']=='confirmed'}
        office=session.get(OfficeStateRecord,'office',with_for_update=True)
        if office:office.content={**office.content,'mode':'normal','revision':office.content['revision']+1,'reserved':[x for x in office.content['reserved'] if x not in slots]}
        session.execute(delete(OfficeFamilyReceiptRecord).where(OfficeFamilyReceiptRecord.id.in_(update_ids)))
        session.execute(delete(OfficeRequestRecord).where(OfficeRequestRecord.request_id.in_(action_ids)))
        for vid in reversed(ids):session.execute(delete(EncounterRecord).where(EncounterRecord.id==vid))
    for case in CASES:ensure_case(engine,case)
    initialize(engine)
    print('Three original fictional encounters reset and seeded in the '+('isolated test' if args.test else 'explicitly selected development')+' database.')
finally:engine.dispose()
