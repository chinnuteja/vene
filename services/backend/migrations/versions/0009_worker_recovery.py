"""Distinguish a real worker restart from an ordinary slow heartbeat."""
from alembic import op
revision='0009_worker_recovery'
down_revision='0008_continuity'
branch_labels=depends_on=None
def upgrade():op.execute('ALTER TABLE calls ADD COLUMN worker_instance UUID')
def downgrade():op.execute('ALTER TABLE calls DROP COLUMN worker_instance')
