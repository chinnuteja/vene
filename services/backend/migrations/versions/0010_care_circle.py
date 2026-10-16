"""Care-circle requests: a patient asks a family member for practical help with a confirmed errand."""
from alembic import op
revision='0010_care_circle'
down_revision='0009_worker_recovery'
branch_labels=depends_on=None
def upgrade():
    op.execute('''CREATE TABLE care_circle_requests (
        id UUID PRIMARY KEY,
        encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
        action_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
        recipient_id UUID NOT NULL REFERENCES memberships(id) ON DELETE CASCADE,
        session_hash VARCHAR(64) NOT NULL,
        state VARCHAR(16) NOT NULL,
        content JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        answered_at TIMESTAMPTZ)''')
    op.execute('CREATE INDEX ix_care_circle_requests_encounter ON care_circle_requests (encounter_id)')
    # At most one open ask per errand and person; a declined or withdrawn ask can be asked again.
    op.execute("CREATE UNIQUE INDEX ux_care_circle_open ON care_circle_requests (action_id, recipient_id) WHERE state IN ('asked','accepted')")
def downgrade():op.execute('DROP TABLE care_circle_requests')
