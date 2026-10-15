from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from helpers import authenticated_client
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bring_vene.domain.contracts import CommandEnvelope
from bring_vene.domain.service import DomainError, apply_command, read_encounter
from bring_vene.main import create_app
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import EncounterRecord, EventRecord, EvidenceRecord

VISIT = UUID("10000000-0000-4000-8000-000000000001")
PRIORITY = UUID("20000000-0000-4000-8000-000000000001")


def change(**overrides):
    body = {"command_id": str(uuid4()), "expected_version": 0, "evidence_refs": [],
            "command": {"type": "priority.selection_changed", "priority_id": str(PRIORITY), "selected": False}}
    body.update(overrides)
    return body


def events_count(engine):
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(EventRecord))


def test_seed_survives_new_engine_and_app(visit_engine):
    result = apply_command(visit_engine, VISIT, CommandEnvelope.model_validate(change()))
    assert not result.encounter.priorities[0].selected
    # Recreate the entire engine/app; no process-local state carries the visit.
    new_engine = make_engine(visit_engine.url.render_as_string(hide_password=False))
    try:
        with authenticated_client(create_app(engine=new_engine)) as client:
            saved = client.get(f"/encounters/{VISIT}").json()
        assert saved["version"] == 1
        assert saved["priorities"][0]["selected"] is False
    finally:
        new_engine.dispose()


@pytest.mark.parametrize("mutate", [
    lambda body: body.update(expected_version=True),
    lambda body: body.update(command_id="not-an-id"),
    lambda body: body["command"].update(selected="yes"),
    lambda body: body["command"].update(type="action.execute"),
    lambda body: body.update(unexpected_permission="all"),
])
def test_invalid_commands_cannot_write(visit_engine, mutate):
    body = change()
    mutate(body)
    with authenticated_client(create_app(engine=visit_engine)) as client:
        response = client.post(f"/encounters/{VISIT}/commands", json=body)
    assert response.status_code == 422
    assert read_encounter(visit_engine, VISIT).version == 0
    assert events_count(visit_engine) == 0


def test_replay_is_idempotent_and_changed_replay_is_rejected(visit_engine):
    body = change()
    first = apply_command(visit_engine, VISIT, CommandEnvelope.model_validate(body))
    replay = apply_command(visit_engine, VISIT, CommandEnvelope.model_validate(body))
    assert replay.duplicate
    assert first.event.id == replay.event.id
    assert replay.encounter.version == 1
    assert events_count(visit_engine) == 1
    body["command"]["selected"] = True
    with pytest.raises(DomainError) as error:
        apply_command(visit_engine, VISIT, CommandEnvelope.model_validate(body))
    assert error.value.status == 409
    assert events_count(visit_engine) == 1


def test_stale_edit_cannot_overwrite_newer_selection(visit_engine):
    apply_command(visit_engine, VISIT, CommandEnvelope.model_validate(change()))
    with authenticated_client(create_app(engine=visit_engine)) as client:
        stale = client.post(f"/encounters/{VISIT}/commands", json=change(
            command={"type": "priority.selection_changed", "priority_id": str(PRIORITY), "selected": True}
        ))
    assert stale.status_code == 409
    assert read_encounter(visit_engine, VISIT).priorities[0].selected is False
    assert events_count(visit_engine) == 1


def test_evidence_cannot_cross_visit_boundary(visit_engine):
    other_id, evidence_id = uuid4(), uuid4()
    view = read_encounter(visit_engine, VISIT)
    with Session(visit_engine) as session, session.begin():
        session.add(EncounterRecord(id=other_id, version=0, projection=view.model_dump(mode="json"), updated_at=view.updated_at))
        session.flush()
        session.add(EvidenceRecord(id=evidence_id, encounter_id=other_id, content={"synthetic": True}))
    body = change(evidence_refs=[str(evidence_id)])
    with authenticated_client(create_app(engine=visit_engine)) as client:
        result = client.post(f"/encounters/{VISIT}/commands", json=body)
    assert result.status_code == 422
    assert read_encounter(visit_engine, VISIT).version == 0
    assert events_count(visit_engine) == 0


def test_clock_is_injected_and_event_projection_are_atomic(visit_engine):
    fixed = datetime(2026, 10, 12, 18, 0, tzinfo=timezone.utc)
    result = apply_command(visit_engine, VISIT, CommandEnvelope.model_validate(change()), clock=lambda: fixed)
    assert result.encounter.updated_at == fixed
    assert result.event.accepted_at == fixed
    assert result.event.sequence == result.encounter.version == 1


def test_failed_transaction_leaves_no_partial_projection(visit_engine):
    with pytest.raises(ValueError):
        apply_command(visit_engine, VISIT, CommandEnvelope.model_validate(change()), clock=lambda: datetime(2026, 10, 12))
    assert read_encounter(visit_engine, VISIT).version == 0
    assert read_encounter(visit_engine, VISIT).priorities[0].selected
    assert events_count(visit_engine) == 0


def test_concurrent_edits_have_one_winner(visit_engine):
    barrier = Barrier(2)
    def submit():
        body = CommandEnvelope.model_validate(change())
        barrier.wait(timeout=5)
        try:
            return apply_command(visit_engine, VISIT, body).encounter.version
        except DomainError as error:
            return error.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: submit(), range(2)))
    assert sorted(outcomes) == [1, 409]
    assert events_count(visit_engine) == 1


def test_concurrent_duplicate_has_one_event(visit_engine):
    barrier = Barrier(2)
    body = CommandEnvelope.model_validate(change())
    def submit():
        barrier.wait(timeout=5)
        return apply_command(visit_engine, VISIT, body)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: submit(), range(2)))
    assert sum(result.duplicate for result in results) == 1
    assert {result.event.sequence for result in results} == {1}
    assert events_count(visit_engine) == 1


def test_missing_priority_cannot_advance_version(visit_engine):
    with pytest.raises(DomainError) as error:
        apply_command(visit_engine, VISIT, CommandEnvelope.model_validate(change(
            command={"type": "priority.selection_changed", "priority_id": str(uuid4()), "selected": True}
        )))
    assert error.value.status == 404
    assert events_count(visit_engine) == 0


def test_database_unavailable_is_distinct_from_api_alive():
    engine = make_engine("postgresql+psycopg://nobody@127.0.0.1:1/unavailable")
    try:
        with TestClient(create_app(engine=engine)) as client:
            assert client.get("/health/live").status_code == 200
            assert client.get("/health/ready").status_code == 503
            assert client.get("/encounters").status_code == 401
    finally:
        engine.dispose()


