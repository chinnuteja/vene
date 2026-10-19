"""In-visit practical checks: standing read-only permission, check runs and obstacles."""
from alembic import op
revision='0011_feasibility'
down_revision='0010_care_circle'
branch_labels=depends_on=None
def upgrade():
    op.execute('''CREATE TABLE standing_checks (
        encounter_id UUID PRIMARY KEY REFERENCES encounters(id) ON DELETE CASCADE,
        session_hash VARCHAR(64) NOT NULL,
        kinds JSONB NOT NULL,
        revision INTEGER NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL)''')
    op.execute('''CREATE TABLE feasibility_checks (
        id UUID PRIMARY KEY,
        encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
        item_id UUID NOT NULL,
        kind VARCHAR(16) NOT NULL,
        plan_fingerprint VARCHAR(64) NOT NULL,
        standing_revision INTEGER NOT NULL,
        state VARCHAR(16) NOT NULL,
        content JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        finished_at TIMESTAMPTZ)''')
    op.execute('CREATE INDEX ix_feasibility_checks_state ON feasibility_checks (state, created_at)')
    # One check per step, kind and exact step version under one permission revision.
    op.execute('CREATE UNIQUE INDEX ux_feasibility_once ON feasibility_checks (encounter_id, item_id, kind, plan_fingerprint, standing_revision)')
    op.execute('''CREATE TABLE obstacles (
        id UUID PRIMARY KEY,
        encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
        item_id UUID NOT NULL,
        check_id UUID NOT NULL REFERENCES feasibility_checks(id) ON DELETE CASCADE,
        kind VARCHAR(40) NOT NULL,
        state VARCHAR(16) NOT NULL,
        content JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        resolved_at TIMESTAMPTZ)''')
    op.execute('CREATE INDEX ix_obstacles_encounter ON obstacles (encounter_id, state)')
def downgrade():
    op.execute('DROP TABLE obstacles')
    op.execute('DROP TABLE feasibility_checks')
    op.execute('DROP TABLE standing_checks')
