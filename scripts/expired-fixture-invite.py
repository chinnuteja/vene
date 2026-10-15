"""Create an expired synthetic invite for the local browser acceptance test only."""
import json
import os
from datetime import timedelta
from pathlib import Path
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from bring_vene.auth import FIXTURE_MEMBERS, issue_invitation
from bring_vene.domain.service import utc_now
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import MembershipRecord

root = Path(__file__).resolve().parent.parent
runtime = json.loads((root / '.local/runtime.json').read_text(encoding='utf-8-sig'))
database_url = runtime['test_database_url'] if os.environ.get('BRING_VENE_BROWSER_TEST') == 'true' else runtime['database_url']
url = make_url(database_url)
if url.host != '127.0.0.1' or url.database not in {'bring_vene','bring_vene_test'}:
    raise RuntimeError('This helper is restricted to the project-local fictional database.')
engine = make_engine(database_url)
try:
    with Session(engine) as session, session.begin():
        member = session.get(MembershipRecord, FIXTURE_MEMBERS['family'])
        invite = issue_invitation(session, member, clock=lambda: utc_now()-timedelta(minutes=16))
        print(json.dumps({'token': invite.token}))
finally:
    engine.dispose()
