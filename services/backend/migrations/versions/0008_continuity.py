"""Scoped continuity, signed callbacks and independent sandbox acknowledgements."""
from alembic import op
revision='0008_continuity'
down_revision='0007_execution'
branch_labels=depends_on=None

def upgrade():
    op.execute('ALTER TABLE calls ADD COLUMN gap_since TIMESTAMPTZ')
    op.execute('''CREATE TABLE sandbox_callback_outbox (
      id UUID PRIMARY KEY, request_id UUID NOT NULL REFERENCES sandbox_office_requests(request_id) ON DELETE CASCADE,
      content JSONB NOT NULL, lease_id UUID, lease_until TIMESTAMPTZ, next_at TIMESTAMPTZ NOT NULL,
      attempts INTEGER NOT NULL, acknowledged_at TIMESTAMPTZ)''')
    op.execute('CREATE INDEX ix_sandbox_callback_outbox_request_id ON sandbox_callback_outbox(request_id)')
    op.execute('CREATE INDEX ix_sandbox_callback_outbox_next_at ON sandbox_callback_outbox(next_at)')
    op.execute('CREATE TABLE sandbox_family_receipts(id UUID PRIMARY KEY, payload_hash VARCHAR(64) NOT NULL, content JSONB NOT NULL)')
    op.execute('''CREATE TABLE callback_nonces(nonce UUID PRIMARY KEY,
      encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE, accepted_at TIMESTAMPTZ NOT NULL)''')
    op.execute('CREATE INDEX ix_callback_nonces_encounter_id ON callback_nonces(encounter_id)')
    op.execute('CREATE INDEX ix_callback_nonces_accepted_at ON callback_nonces(accepted_at)')
    op.execute('''CREATE TABLE office_callbacks(id UUID PRIMARY KEY,
      encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
      action_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
      payload_hash VARCHAR(64) NOT NULL, accepted_at TIMESTAMPTZ NOT NULL)''')
    op.execute('CREATE INDEX ix_office_callbacks_encounter_id ON office_callbacks(encounter_id)')
    op.execute('CREATE INDEX ix_office_callbacks_action_id ON office_callbacks(action_id)')
    op.execute('''CREATE TABLE after_visit_documents(id UUID PRIMARY KEY,
      encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
      evidence_id UUID NOT NULL UNIQUE REFERENCES evidence(id) ON DELETE CASCADE,
      content JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL)''')
    op.execute('CREATE INDEX ix_after_visit_documents_encounter_id ON after_visit_documents(encounter_id)')
    op.execute('''CREATE TABLE family_updates(id UUID PRIMARY KEY,
      encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
      recipient_id UUID NOT NULL REFERENCES memberships(id) ON DELETE CASCADE,
      session_hash VARCHAR(64) NOT NULL, state VARCHAR(24) NOT NULL, content JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL)''')
    for column in ['encounter_id','recipient_id','state']:op.execute(f'CREATE INDEX ix_family_updates_{column} ON family_updates({column})')
    op.execute('''CREATE TABLE family_outbox(update_id UUID PRIMARY KEY REFERENCES family_updates(id) ON DELETE CASCADE,
      lease_id UUID, lease_until TIMESTAMPTZ, next_at TIMESTAMPTZ NOT NULL, attempts INTEGER NOT NULL)''')
    op.execute('CREATE INDEX ix_family_outbox_next_at ON family_outbox(next_at)')
    op.execute('''CREATE TABLE next_visits(origin_id UUID REFERENCES encounters(id) ON DELETE CASCADE,
      next_id UUID REFERENCES encounters(id) ON DELETE CASCADE, content JSONB NOT NULL, PRIMARY KEY(origin_id,next_id))''')
    op.execute('''CREATE TABLE operation_traces(id UUID PRIMARY KEY,
      encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
      event VARCHAR(40) NOT NULL, content JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL)''')
    op.execute('CREATE INDEX ix_operation_traces_encounter_id ON operation_traces(encounter_id)')
    op.execute('CREATE INDEX ix_operation_traces_created_at ON operation_traces(created_at)')
    op.execute('CREATE TABLE deletion_audit(id UUID PRIMARY KEY, deleted_at TIMESTAMPTZ NOT NULL, visit_count INTEGER NOT NULL)')

def downgrade():
    for table in ['deletion_audit','operation_traces','next_visits','family_outbox','family_updates','after_visit_documents','office_callbacks','callback_nonces','sandbox_family_receipts','sandbox_callback_outbox']:op.drop_table(table)
    op.execute('ALTER TABLE calls DROP COLUMN gap_since')
