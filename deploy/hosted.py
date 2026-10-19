"""One disposable fictional demo, HTTP only. No provider credentials or real integrations.

All child services bind loopback. Only Next listens on Render's public PORT.
Postgres is ephemeral by design; restarting this service discards fictional demo sessions.
"""
import os
import secrets
import signal
import subprocess
import threading
import time
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
PG='/usr/lib/postgresql/15/bin/'


def main():
    os.chdir(ROOT)
    state=Path('/tmp/bring-vene-demo');state.mkdir(exist_ok=True)
    subprocess.run(['chown','postgres:postgres',str(state)],check=True)
    def pg(*args,**kwargs):return subprocess.run(['runuser','-u','postgres','--',PG+args[0],*args[1:]],check=True,**kwargs)
    if not (state/'PG_VERSION').exists():pg('initdb','-D',str(state),'--auth-local=trust','--auth-host=scram-sha-256',stdout=subprocess.DEVNULL)
    pg('pg_ctl','start','-D',str(state),'-l','/tmp/vene-postgres.log','-o',"-h 127.0.0.1 -k /tmp -p 5432 -c shared_buffers=16MB -c max_connections=40",'-w',stdout=subprocess.DEVNULL)
    password=secrets.token_hex(32)
    pg('psql','-h','/tmp','-U','postgres','-d','postgres','-v','ON_ERROR_STOP=1',input="ALTER USER postgres PASSWORD '"+password+"';",text=True,stdout=subprocess.DEVNULL)
    exists=pg('psql','-h','/tmp','-U','postgres','-d','postgres','-Atc',"SELECT 1 FROM pg_database WHERE datname='vene_demo'",capture_output=True,text=True).stdout.strip()
    if not exists:pg('createdb','-h','/tmp','-U','postgres','vene_demo')
    env={k:v for k,v in os.environ.items() if k not in {'DEEPGRAM_API_KEY','DEEPSEEK_API_KEY','CARTESIA_API_KEY','OPENAI_API_KEY'}}
    env.update(DATABASE_URL='postgresql+psycopg://postgres:'+password+'@127.0.0.1:5432/vene_demo',
        BRING_VENE_MODE='fixture',BRING_VENE_DEVELOPMENT='true',DEMO_GUIDED='true',
        VOICE_PROVIDER='fixture',MODEL_PROVIDER='fixture',TTS_PROVIDER='fixture',COOKIE_SECURE='true',
        FRONTEND_ORIGIN=env.get('RENDER_EXTERNAL_URL','https://bring-vene.invalid'),BACKEND_URL='http://127.0.0.1:8000',
        OFFICE_URL='http://127.0.0.1:8002',OFFICE_TOKEN=secrets.token_hex(32),OFFICE_TIMEOUT_SECONDS='5',
        OFFICE_CALLBACK_URL='http://127.0.0.1:8000',OFFICE_CALLBACK_SECRET=secrets.token_hex(32),
        LIVEKIT_URL='',LIVEKIT_API_KEY='',LIVEKIT_API_SECRET='',PHONE_BRIDGE_TOKEN='',PHONE_DIAL_NUMBER='')
    subprocess.run(['alembic','-c','services/backend/alembic.ini','upgrade','head'],env=env,check=True)
    subprocess.run(['python','-c','from bring_vene.execution.office import initialize; from bring_vene.persistence.database import make_engine; from bring_vene.config import Settings; initialize(make_engine(Settings().database_url))'],env=env,check=True)
    processes=[];stopped=threading.Event()
    def stop(*_):stopped.set()
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    def start(args):
        process=subprocess.Popen(args,env=env,start_new_session=True);processes.append(process);return process
    def ready(url):
        for _ in range(120):
            if any(p.poll() is not None for p in processes):raise RuntimeError('An owned demo service exited.')
            try:
                with urlopen(url,timeout=1) as r:
                    if r.status==200:return
            except Exception:pass
            if stopped.wait(.5):raise RuntimeError('Demo startup stopped.')
        raise RuntimeError('Demo startup timed out.')
    try:
        for module,port in [('bring_vene.main:app',8000),('bring_vene.execution.office:app',8002)]:
            start(['uvicorn',module,'--host','127.0.0.1','--port',str(port),'--no-access-log'])
        ready('http://127.0.0.1:8000/health/ready')
        start(['python','-m','bring_vene.understanding.worker'])
        start(['python','-m','bring_vene.execution.worker'])
        start(['node','apps/web/node_modules/next/dist/bin/next','start','apps/web','--hostname','0.0.0.0','--port',env.get('PORT','10000')])
        print('Fictional guided demo started. No live voice, external calls or real bookings.',flush=True)
        while not stopped.wait(1):
            if any(p.poll() is not None for p in processes):raise RuntimeError('An owned demo service exited.')
    finally:
        for process in reversed(processes):
            if process.poll() is None:os.killpg(process.pid,signal.SIGTERM)
        limit=time.monotonic()+12
        for process in processes:
            try:process.wait(timeout=max(.1,limit-time.monotonic()))
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL)
        pg('pg_ctl','stop','-D',str(state),'-m','fast','-w',stdout=subprocess.DEVNULL)


if __name__=='__main__':main()
