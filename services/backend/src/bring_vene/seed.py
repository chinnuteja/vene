import json
from pathlib import Path
from uuid import UUID
from sqlalchemy.orm import Session
from bring_vene.domain.contracts import EncounterView
from bring_vene.persistence.models import EncounterRecord, EvidenceRecord
from bring_vene.persistence.database import make_engine
from bring_vene.config import Settings
from bring_vene.auth import FIXTURE_MEMBERS
from bring_vene.persistence.models import MembershipRecord


def seed(engine, fixture: Path | None = None):
    fixture = fixture or Path(__file__).resolve().parents[4] / "fixtures" / "maria.json"
    view = EncounterView.model_validate_json(fixture.read_text(encoding="utf-8"))
    with Session(engine) as session, session.begin():
        existing = session.get(EncounterRecord, view.id)
        if not existing:
            session.add(EncounterRecord(id=view.id, version=view.version, projection=view.model_dump(mode="json"), updated_at=view.updated_at))
        else:
            saved = EncounterView.model_validate(existing.projection)
            for evidence in view.evidence:
                if not any(e.id == evidence.id for e in saved.evidence):
                    saved.evidence.append(evidence)
            existing.projection = saved.model_dump(mode="json")
        session.flush()
        for evidence in view.evidence:
            if not session.get(EvidenceRecord, evidence.id):
                session.add(EvidenceRecord(id=evidence.id, encounter_id=view.id, content=evidence.model_dump(mode="json")))
        for role, member_id in FIXTURE_MEMBERS.items():
            if not session.get(MembershipRecord, member_id):
                session.add(MembershipRecord(id=member_id, encounter_id=view.id, role=role,
                    name={"patient": "Maria Alvarez", "clinician": "Dr. Chris Chen", "family": "Elena Alvarez"}[role]))
    return view.id


if __name__ == "__main__":
    seed(make_engine(Settings().database_url))
    print("Fictional visit seeded; existing edits preserved.")

