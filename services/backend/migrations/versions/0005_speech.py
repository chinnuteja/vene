"""Private cue queue, scoped speech consent and actual playout receipts (frozen schema)."""
from alembic import op
revision='0005_speech'
down_revision='0004_understanding'
branch_labels=None
depends_on=None

def upgrade():
    op.execute('\nCREATE TABLE speech_state (\n\tencounter_id UUID NOT NULL, \n\tmode VARCHAR(20) NOT NULL, \n\tmode_revision INTEGER NOT NULL, \n\trevision INTEGER NOT NULL, \n\tsession_hash VARCHAR(64), \n\tcurrent_delivery UUID, \n\tlast_human_at TIMESTAMP WITH TIME ZONE, \n\tlast_output_at TIMESTAMP WITH TIME ZONE, \n\tcontent JSONB NOT NULL, \n\tPRIMARY KEY (encounter_id), \n\tFOREIGN KEY(encounter_id) REFERENCES encounters (id) ON DELETE CASCADE, \n\tFOREIGN KEY(session_hash) REFERENCES participant_sessions (token_hash) ON DELETE CASCADE\n)\n\n')
    op.execute('\nCREATE TABLE speech_consents (\n\tconnection_id UUID NOT NULL, \n\tmode_revision INTEGER NOT NULL, \n\tagreed BOOLEAN NOT NULL, \n\tPRIMARY KEY (connection_id, mode_revision), \n\tFOREIGN KEY(connection_id) REFERENCES call_connections (id) ON DELETE CASCADE\n)\n\n')
    op.execute('\nCREATE TABLE speech_cues (\n\tid UUID NOT NULL, \n\tencounter_id UUID NOT NULL, \n\tdedup_key VARCHAR(100) NOT NULL, \n\tdigest VARCHAR(64) NOT NULL, \n\tscore INTEGER NOT NULL, \n\tstate VARCHAR(20) NOT NULL, \n\tcontent JSONB NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_cue_context UNIQUE (encounter_id, dedup_key, digest), \n\tFOREIGN KEY(encounter_id) REFERENCES encounters (id) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_speech_cues_encounter_id ON speech_cues (encounter_id)')
    op.execute('CREATE INDEX ix_speech_cues_state ON speech_cues (state)')
    op.execute('\nCREATE TABLE speech_deliveries (\n\tid UUID NOT NULL, \n\tencounter_id UUID NOT NULL, \n\tcue_id UUID NOT NULL, \n\tgeneration UUID NOT NULL, \n\tstate VARCHAR(20) NOT NULL, \n\tcontent JSONB NOT NULL, \n\tapproved_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tfirst_audio_at TIMESTAMP WITH TIME ZONE, \n\tstopped_at TIMESTAMP WITH TIME ZONE, \n\tplayed_ms INTEGER NOT NULL, \n\treason VARCHAR(40), \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(encounter_id) REFERENCES encounters (id) ON DELETE CASCADE, \n\tFOREIGN KEY(cue_id) REFERENCES speech_cues (id) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_speech_deliveries_encounter_id ON speech_deliveries (encounter_id)')
    op.execute('CREATE INDEX ix_speech_deliveries_state ON speech_deliveries (state)')
    op.execute('\nCREATE TABLE speech_mutations (\n\tid UUID NOT NULL, \n\tencounter_id UUID NOT NULL, \n\tcommand_id UUID NOT NULL, \n\tactor_id UUID NOT NULL, \n\trequest_hash VARCHAR(64) NOT NULL, \n\tcontent JSONB NOT NULL, \n\taccepted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_speech_command UNIQUE (encounter_id, command_id), \n\tFOREIGN KEY(encounter_id) REFERENCES encounters (id) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_speech_mutations_encounter_id ON speech_mutations (encounter_id)')

def downgrade():
    op.drop_table('speech_mutations')
    op.drop_table('speech_deliveries')
    op.drop_table('speech_cues')
    op.drop_table('speech_consents')
    op.drop_table('speech_state')
