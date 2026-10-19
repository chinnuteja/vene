"""Small, explicitly fictional host: one Python process, ordinary domain services.

The local live configuration retains its separate workers. This runner never selects
providers, accepts audio or emulates a LiveKit connection.
"""
import asyncio
from contextlib import contextmanager
import signal
import threading
import uvicorn
from bring_vene.config import Settings
from bring_vene.persistence.database import make_engine
from bring_vene.main import create_app
from bring_vene.execution.office import office_app
from bring_vene.execution.worker import main as administrative
from bring_vene.understanding.worker import run as understanding


class OwnedServer(uvicorn.Server):
    @contextmanager
    def capture_signals(self):
        # The runner owns both servers' shutdown as one unit.
        yield


async def run():
    settings=Settings()
    if not(settings.bring_vene_development and settings.bring_vene_mode=='fixture' and settings.demo_guided and
           settings.voice_provider==settings.model_provider==settings.tts_provider=='fixture'):
        raise RuntimeError('The hosted runner requires explicitly selected fictional fixture providers.')
    engine=make_engine(settings.database_url)
    office_engine=make_engine(settings.database_url)
    background_engine=make_engine(settings.database_url)
    stopping=asyncio.Event();stop_thread=threading.Event();loop=asyncio.get_running_loop()
    for value in (signal.SIGTERM,signal.SIGINT):
        signal.signal(value,lambda *_:loop.call_soon_threadsafe(stopping.set))
    servers=[OwnedServer(uvicorn.Config(app,host='127.0.0.1',port=port,access_log=False,log_level='warning'))
             for app,port in [(create_app(settings,engine),8000),(office_app(settings,office_engine),8002)]]
    tasks=[asyncio.create_task(server.serve()) for server in servers]
    interpreter=asyncio.create_task(understanding(settings,background_engine))
    admin=asyncio.create_task(asyncio.to_thread(administrative,settings,background_engine,stop_thread))
    waiter=asyncio.create_task(stopping.wait())
    try:
        done,_=await asyncio.wait([*tasks,interpreter,admin,waiter],return_when=asyncio.FIRST_COMPLETED)
        if waiter not in done:
            for task in done:
                if not task.cancelled() and task.exception():raise task.exception()
            raise RuntimeError('An owned fictional service exited.')
    finally:
        stop_thread.set()
        for server in servers:server.should_exit=True
        interpreter.cancel();waiter.cancel()
        await asyncio.gather(*tasks,interpreter,admin,waiter,return_exceptions=True)
        engine.dispose();office_engine.dispose();background_engine.dispose()


if __name__=='__main__':asyncio.run(run())
