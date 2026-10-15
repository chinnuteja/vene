"""Participant identities, one-use invitations and persistent sessions."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_audience"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade():
    uuid = postgresql.UUID(as_uuid=True)
    op.add_column("encounter_events", sa.Column("actor_id", uuid, nullable=True))
    op.create_table("memberships", sa.Column("id", uuid, primary_key=True),
                    sa.Column("encounter_id", uuid, sa.ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("role", sa.String(16), nullable=False), sa.Column("name", sa.String(100), nullable=False),
                    sa.Column("revoked_at", sa.DateTime(timezone=True)),
                    sa.CheckConstraint("role IN ('patient','clinician','family')", name="ck_member_role"))
    op.create_index("ix_memberships_encounter_id", "memberships", ["encounter_id"])
    op.create_table("invitations", sa.Column("id", uuid, primary_key=True),
                    sa.Column("membership_id", uuid, sa.ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
                    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
                    sa.Column("used_at", sa.DateTime(timezone=True)), sa.Column("revoked_at", sa.DateTime(timezone=True)))
    op.create_index("ix_invitations_membership_id", "invitations", ["membership_id"])
    op.create_table("participant_sessions", sa.Column("token_hash", sa.String(64), primary_key=True),
                    sa.Column("membership_id", uuid, sa.ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("csrf_token", sa.String(64), nullable=False),
                    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
                    sa.Column("revoked_at", sa.DateTime(timezone=True)))
    op.create_index("ix_participant_sessions_membership_id", "participant_sessions", ["membership_id"])


def downgrade():
    op.drop_table("participant_sessions")
    op.drop_table("invitations")
    op.drop_table("memberships")
    op.drop_column("encounter_events", "actor_id")
