"""Outcomes the patient recorded for open loops carried between visits."""
from alembic import op
revision='0012_memory'
down_revision='0011_feasibility'
branch_labels=depends_on=None
def upgrade():
    op.execute('''CREATE TABLE memory_outcomes (
        patient_id UUID NOT NULL,
        loop_key VARCHAR(80) NOT NULL,
        outcome VARCHAR(16) NOT NULL,
        encounter_id UUID REFERENCES encounters(id) ON DELETE SET NULL,
        recorded_at TIMESTAMPTZ NOT NULL,
        PRIMARY KEY (patient_id, loop_key))''')
def downgrade():op.execute('DROP TABLE memory_outcomes')
