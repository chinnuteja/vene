"""Reset only the dedicated loopback test database before browser acceptance."""
import json
from pathlib import Path
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import EncounterRecord,OfficeRequestRecord,OfficeStateRecord,OfficeFamilyReceiptRecord,MemoryOutcomeRecord
from bring_vene.seed import seed

root = Path(__file__).resolve().parent.parent
runtime = json.loads((root / '.local/runtime.json').read_text(encoding='utf-8-sig'))
url = make_url(runtime['test_database_url'])
if url.host != '127.0.0.1' or url.database != 'bring_vene_test':
    raise RuntimeError('Browser tests must use the dedicated local bring_vene_test database.')
engine = make_engine(runtime['test_database_url'])
try:
    with engine.begin() as connection:
        connection.execute(delete(EncounterRecord))
        connection.execute(delete(OfficeRequestRecord))
        connection.execute(delete(OfficeFamilyReceiptRecord))
        connection.execute(delete(MemoryOutcomeRecord))
        connection.execute(delete(OfficeStateRecord))
    seed(engine, root / 'fixtures/maria.json')
finally:
    engine.dispose()
