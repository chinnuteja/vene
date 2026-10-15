import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, text
from sqlalchemy.engine import make_url

from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import EncounterRecord, EventRecord, EvidenceRecord,OfficeRequestRecord,OfficeStateRecord,OfficeFamilyReceiptRecord
from bring_vene.seed import seed

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def engine():
    runtime = json.loads((ROOT / ".local/runtime.json").read_text(encoding="utf-8-sig"))
    url = make_url(runtime["test_database_url"])
    if url.database != "bring_vene_test" or url.host != "127.0.0.1":
        raise RuntimeError("Tests must use the dedicated local bring_vene_test database.")
    import os
    old = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = str(url.render_as_string(hide_password=False))
    config = Config(str(ROOT / "services/backend/alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "services/backend/migrations"))
    # Exercise migrations from an empty application schema, not create_all.
    command.downgrade(config, "base")
    result = make_engine(os.environ["DATABASE_URL"])
    with result.connect() as connection:
        assert connection.scalar(text("SELECT to_regclass('public.encounters')")) is None
    command.upgrade(config, "head")
    if old is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = old
    yield result
    result.dispose()


@pytest.fixture
def visit_engine(engine):
    with engine.begin() as connection:
        connection.execute(delete(EventRecord))
        connection.execute(delete(EvidenceRecord))
        connection.execute(delete(EncounterRecord))
        connection.execute(delete(OfficeRequestRecord))
        connection.execute(delete(OfficeFamilyReceiptRecord))
        connection.execute(delete(OfficeStateRecord))
    seed(engine, ROOT / "fixtures/maria.json")
    return engine

