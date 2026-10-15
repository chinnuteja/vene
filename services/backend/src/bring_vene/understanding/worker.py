"""Owned local worker: durable sources, bounded generation and cancellation fencing."""
import asyncio
import logging
from sqlalchemy import select,update
from sqlalchemy.orm import Session
from bring_vene.config import Settings
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import UnderstandingRecord,InterpretationRunRecord
from bring_vene.understanding.gateway import ModelGateway
from bring_vene.understanding import service
from bring_vene.domain.service import utc_now

logging.getLogger('openai').setLevel(logging.CRITICAL)
logging.getLogger('httpx').setLevel(logging.CRITICAL)
logging.getLogger('httpcore').setLevel(logging.CRITICAL)


async def execute(engine,settings,run_id,snapshot,gateway):
    try:
        result=await asyncio.wait_for(gateway.extract(snapshot),timeout=settings.model_timeout_seconds)
        return await asyncio.to_thread(service.apply_result,engine,run_id,result,settings)
    except asyncio.CancelledError:
        await asyncio.to_thread(service.finish_failed,engine,run_id,settings,True)
        raise
    except Exception:
        # No request text, model output, provider exception or credentials in logs.
        await asyncio.to_thread(service.finish_failed,engine,run_id,settings)
        return False


async def run():
    settings=Settings();engine=make_engine(settings.database_url);gateway=ModelGateway(settings);jobs={}
    # One project-owned interpretation worker; a restart cannot leave a run authoritative.
    with engine.begin() as connection:
        connection.execute(update(InterpretationRunRecord).where(InterpretationRunRecord.state=='running')
            .values(state='stale',finished_at=utc_now()))
    try:
        while True:
            for visit_id,(run_id,task) in list(jobs.items()):
                if task.done():
                    if not task.cancelled():task.exception()
                    jobs.pop(visit_id)
                elif not await asyncio.to_thread(service.still_current,engine,run_id):
                    task.cancel();await asyncio.gather(task,return_exceptions=True);jobs.pop(visit_id)
            def wanted():
                with Session(engine) as session:
                    return list(session.scalars(select(UnderstandingRecord.encounter_id).where(
                        UnderstandingRecord.enabled.is_(True),UnderstandingRecord.revision>UnderstandingRecord.processed_revision)))
            for visit_id in await asyncio.to_thread(wanted):
                if visit_id in jobs:continue
                prepared=await asyncio.to_thread(service.prepare,engine,visit_id,settings)
                if prepared:
                    run_id,snapshot=prepared
                    jobs[visit_id]=(run_id,asyncio.create_task(execute(engine,settings,run_id,snapshot,gateway)))
            await asyncio.sleep(.25)
    finally:
        for _,task in jobs.values():task.cancel()
        await asyncio.gather(*(task for _,task in jobs.values()),return_exceptions=True);engine.dispose()


if __name__=='__main__':asyncio.run(run())
