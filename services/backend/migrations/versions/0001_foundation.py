"""Persistent encounter, evidence and transactional command history."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("encounters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("projection", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 0", name="ck_encounter_version"),
    )
    op.create_table("evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("encounter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_evidence_encounter_id", "evidence", ["encounter_id"])
    op.create_table("encounter_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("encounter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("command_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("envelope", postgresql.JSONB(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("encounter_id", "sequence", name="uq_event_sequence"),
        sa.UniqueConstraint("encounter_id", "command_id", name="uq_event_command"),
        sa.CheckConstraint("sequence >= 1", name="ck_event_sequence"),
    )

def downgrade():
    op.drop_table("encounter_events")
    op.drop_index("ix_evidence_encounter_id", table_name="evidence")
    op.drop_table("evidence")
    op.drop_table("encounters")

