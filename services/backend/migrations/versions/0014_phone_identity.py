"""Phone participants: the identity reported by the phone bridge and the PIN that admitted them.

A browser connection is bound to a participant session; a phone connection to its single-use PIN.
"""
from alembic import op
revision='0014_phone_identity'
down_revision='0013_room'
branch_labels=depends_on=None
def upgrade():
    op.execute('ALTER TABLE call_connections ADD COLUMN external_identity VARCHAR(80)')
    op.execute('ALTER TABLE call_connections ADD COLUMN dial_pin_id UUID REFERENCES dial_pins(id) ON DELETE CASCADE')
    op.execute('ALTER TABLE call_connections ALTER COLUMN session_hash DROP NOT NULL')
    op.execute("""ALTER TABLE call_connections ADD CONSTRAINT ck_connection_binding CHECK (
        (channel = 'browser' AND session_hash IS NOT NULL AND dial_pin_id IS NULL) OR
        (channel = 'phone' AND session_hash IS NULL AND dial_pin_id IS NOT NULL AND external_identity IS NOT NULL))""")
def downgrade():
    op.execute('ALTER TABLE call_connections DROP CONSTRAINT ck_connection_binding')
    op.execute('DELETE FROM call_connections WHERE session_hash IS NULL')
    op.execute('ALTER TABLE call_connections ALTER COLUMN session_hash SET NOT NULL')
    op.execute('ALTER TABLE call_connections DROP COLUMN dial_pin_id')
    op.execute('ALTER TABLE call_connections DROP COLUMN external_identity')
