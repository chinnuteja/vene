"""Administrative execution and independent persisted sandbox office, frozen schema."""
from alembic import op
revision = '0007_execution'
down_revision = '0006_speech_fence'
branch_labels = depends_on = None

def upgrade():
    op.execute('''CREATE TABLE execution_scopes (
      encounter_id UUID REFERENCES encounters(id) ON DELETE CASCADE,
      item_id UUID NOT NULL, session_hash VARCHAR(64) NOT NULL,
      revision INTEGER NOT NULL, allowed BOOLEAN NOT NULL,
      PRIMARY KEY(encounter_id,item_id))''')
    op.execute('''CREATE TABLE executions (
      id UUID PRIMARY KEY, encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
      item_id UUID NOT NULL, state VARCHAR(32) NOT NULL, content JSONB NOT NULL,
      created_at TIMESTAMPTZ NOT NULL)''')
    op.execute('CREATE INDEX ix_executions_encounter_id ON executions(encounter_id)')
    op.execute('CREATE INDEX ix_executions_state ON executions(state)')
    op.execute('''CREATE TABLE execution_outbox (
      action_id UUID PRIMARY KEY REFERENCES executions(id) ON DELETE CASCADE,
      lease_id UUID, lease_until TIMESTAMPTZ, next_at TIMESTAMPTZ NOT NULL, attempts INTEGER NOT NULL)''')
    op.execute('CREATE INDEX ix_execution_outbox_next_at ON execution_outbox(next_at)')
    op.execute('CREATE TABLE sandbox_office_state (id VARCHAR(20) PRIMARY KEY, content JSONB NOT NULL)')
    op.execute('CREATE TABLE sandbox_office_requests (request_id UUID PRIMARY KEY, kind VARCHAR(20) NOT NULL, content JSONB NOT NULL)')

def downgrade():
    for table in ['sandbox_office_requests','sandbox_office_state','execution_outbox','executions','execution_scopes']:
        op.drop_table(table)
