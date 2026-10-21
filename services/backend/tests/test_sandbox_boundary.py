"""The independent receiver must not cold-load model or RTC SDKs during delivery."""
import json
import os
from pathlib import Path
import subprocess
import sys


def test_first_family_receipt_needs_no_model_or_voice_imports(visit_engine):
    code='''
import json,sys
from uuid import uuid4
from fastapi.testclient import TestClient
from bring_vene.config import Settings
from bring_vene.persistence.database import make_engine
from bring_vene.execution.office import office_app,initialize
settings=Settings(bring_vene_development=True,office_token='cold-receiver-test')
engine=make_engine(settings.database_url)
initialize(engine)
with TestClient(office_app(settings,engine)) as client:
    result=client.post('/family-updates',headers={'Authorization':'Bearer cold-receiver-test'},json={
        'request_id':str(uuid4()),'recipient_id':str(uuid4()),'text':'A fictional update.','digest':'a'*64})
    print(json.dumps({'status':result.status_code,'delivered':result.json().get('status')=='delivered',
        'sdk_loaded':any(name=='openai' or name.startswith('livekit') or name=='bring_vene.understanding.gateway' for name in sys.modules)}))
engine.dispose()
'''
    env={**os.environ,'DATABASE_URL':visit_engine.url.render_as_string(hide_password=False)}
    result=subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[3],env=env,
                          capture_output=True,text=True,timeout=60)
    # Never copy a failed connection's potentially credential-bearing traceback into a report.
    assert result.returncode==0,'The isolated cold receiver failed.'
    assert json.loads(result.stdout.strip().splitlines()[-1])=={'status':200,'delivered':True,'sdk_loaded':False}
