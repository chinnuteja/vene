"""Explicit real-model gate, original fictional text, dedicated test DB only.

Do not run alongside backend/browser tests: this resets bring_vene_test.
No fixture fallback. Missing credentials are checked before any DB mutation.
"""
import asyncio
import json
import time
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from bring_vene.config import Settings
from bring_vene.auth import FIXTURE_VISIT,FIXTURE_MEMBERS,issue_invitation,redeem
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import EncounterRecord,MembershipRecord,InterpretationRunRecord
from bring_vene.seed import seed
from bring_vene.understanding import service
from bring_vene.understanding.contracts import ProcessingRequest,FixtureTurn
from bring_vene.understanding.gateway import ModelGateway,configuration,PROMPT_VERSION


async def main():
    settings=Settings(bring_vene_development=True,bring_vene_mode='fixture')
    provider,requested_model=configuration(settings)
    if provider not in ('openai','deepseek'):
        print('UNVERIFIED: configure MODEL_PROVIDER and its live API key. No model call, database reset or fixture fallback occurred.')
        return 2
    url=make_url(settings.database_url)
    if url.host!='127.0.0.1' or url.database!='bring_vene_test':raise RuntimeError('Use check-model.ps1 and the isolated bring_vene_test database.')
    engine=make_engine(settings.database_url)
    observations=[]
    try:
        with engine.begin() as connection:connection.execute(delete(EncounterRecord))
        seed(engine)
        with Session(engine) as session,session.begin():invite=issue_invitation(session,session.get(MembershipRecord,FIXTURE_MEMBERS['patient']))
        token,viewer=redeem(engine,invite.token)
        service.processing(engine,FIXTURE_VISIT,token,viewer.csrf_token,ProcessingRequest(command_id=uuid4(),enabled=True),settings)
        gateway=ModelGateway(settings);models=[]
        async def extract(text):
            service.fixture_turn(engine,FIXTURE_VISIT,token,viewer.csrf_token,
                FixtureTurn(command_id=uuid4(),speaker='clinician',text=text),settings)
            run_id,snapshot=service.prepare(engine,FIXTURE_VISIT,settings)
            started=time.monotonic();result=await gateway.extract(snapshot)
            observations.append({'input':snapshot,'output':result.extraction.model_dump(mode='json'),'returned_model':result.model,
                'duration_ms':round((time.monotonic()-started)*1000)})
            if not service.apply_result(engine,run_id,result,settings):raise RuntimeError('The provider result did not pass current source/permission checks.')
            models.append(result.model)
            with Session(engine) as session:return session.get(EncounterRecord,FIXTURE_VISIT).projection
        unrelated=await extract('This is an original fictional conversation for testing. Maria will...')
        assert not any(i['origin']=='interpretation' for i in unrelated['plan'])
        assert all(q['status']=='open' for q in unrelated['priorities'])
        first=await extract('Here is the lab plan we discussed: Maria will arrange the lab visit at Harbor Lab on Wednesday, after the office sends the order. No appointment has been booked.')
        lab=next(i for i in first['plan'] if i['origin']=='interpretation' and i['timeframe']=='Wednesday')
        assert lab['location']=='Harbor Lab' and lab['owner'] and lab['evidence_refs']
        second=await extract('One correction for the lab visit: Friday, not Wednesday. The location is still Harbor Lab. Maria will arrange the lab visit after the office sends the order.')
        assert any(i['timeframe']=='Friday' and i['evidence_refs'] for i in second['plan'] if i['origin']=='interpretation')
        third=await extract("For that lab visit on Friday at Harbor Lab, they will arrange it. We have not clarified who 'they' means. Keep the owner unknown.")
        assert any(i['owner'] is None and i['needs_clarification'] for i in third['plan'] if i['origin']=='interpretation')
        assert any(i['owner'] is None and i['timeframe']=='Friday' and i['location']=='Harbor Lab' for i in third['plan'] if i['origin']=='interpretation')
        assert all(not i['patient_authorized'] and not i['external_completed'] and not i['order_available'] for i in third['plan'])
        Path('docs/qa/phase-04-real-model.json').write_text(json.dumps({'provider':provider,'requested_model':requested_model,
            'returned_models':models,'prompt_version':PROMPT_VERSION,'synthetic_only':True,'free_form_extraction':'passed',
            'checked_at':datetime.now(timezone.utc).isoformat(),'observations':observations,
            'unrelated_speech_no_invented_steps':'passed','correction':'passed','ambiguous_owner':'passed','no_automatic_authorization':'passed'},indent=2)+'\n',encoding='utf-8')
        print('Real-model synthetic conversation gate passed; evidence written to docs/qa/phase-04-real-model.json.')
        return 0
    except Exception as error:
        # Do not print sensitive provider bodies or unbounded transcript text.
        print('Real-model gate FAILED: '+type(error).__name__+'. No fixture fallback occurred.')
        Path('docs/qa/phase-04-real-model-failure.json').write_text(json.dumps({'checked_at':datetime.now(timezone.utc).isoformat(),
            'provider':provider,'requested_model':requested_model,'error_type':type(error).__name__,
            'http_status':getattr(error,'status_code',None),'synthetic_only':True,'observations':observations,'fixture_fallback':False},indent=2)+'\n')
        return 1
    finally:engine.dispose()


if __name__=='__main__':raise SystemExit(asyncio.run(main()))
