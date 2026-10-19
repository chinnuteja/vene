"""One phone in the room (patient-attested people and speaker labels) and dial-in PINs."""
from alembic import op
revision='0013_room'
down_revision='0012_memory'
branch_labels=depends_on=None
def upgrade():
    op.execute('''CREATE TABLE room_sessions (
        encounter_id UUID PRIMARY KEY REFERENCES encounters(id) ON DELETE CASCADE,
        session_hash VARCHAR(64) NOT NULL,
        state VARCHAR(16) NOT NULL,
        content JSONB NOT NULL,
        revision INTEGER NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL)''')
    op.execute('''CREATE TABLE speaker_attributions (
        encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
        label VARCHAR(16) NOT NULL,
        person_id VARCHAR(40),
        attested_at TIMESTAMPTZ NOT NULL,
        PRIMARY KEY (encounter_id, label))''')
    op.execute('''CREATE TABLE dial_pins (
        id UUID PRIMARY KEY,
        encounter_id UUID NOT NULL REFERENCES encounters(id) ON DELETE CASCADE,
        membership_id UUID NOT NULL REFERENCES memberships(id) ON DELETE CASCADE,
        pin_hash VARCHAR(64) NOT NULL UNIQUE,
        expires_at TIMESTAMPTZ NOT NULL,
        used_at TIMESTAMPTZ,
        revoked_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL)''')
    op.execute("ALTER TABLE call_connections ADD COLUMN channel VARCHAR(8) NOT NULL DEFAULT 'browser'")
def downgrade():
    op.execute('ALTER TABLE call_connections DROP COLUMN channel')
    op.execute('DROP TABLE dial_pins')
    op.execute('DROP TABLE speaker_attributions')
    op.execute('DROP TABLE room_sessions')
