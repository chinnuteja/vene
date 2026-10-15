"""Persistent call admission, consent and attributed media evidence (frozen schema)."""
from alembic import op
revision='0003_calls'
down_revision='0002_audience'
branch_labels=None
depends_on=None

def upgrade():
    op.execute('\nCREATE TABLE calls (\n\tencounter_id UUID NOT NULL, \n\tgeneration UUID NOT NULL, \n\trevision INTEGER NOT NULL, \n\tmanual_pause BOOLEAN NOT NULL, \n\toutput_silenced BOOLEAN NOT NULL, \n\tended BOOLEAN NOT NULL, \n\tworker_seen_at TIMESTAMP WITH TIME ZONE, \n\tstopped_epoch INTEGER NOT NULL, \n\tactive_tasks INTEGER NOT NULL, \n\tworker_error VARCHAR(32), \n\tPRIMARY KEY (encounter_id), \n\tFOREIGN KEY(encounter_id) REFERENCES encounters (id) ON DELETE CASCADE\n)\n\n')
    op.execute('\nCREATE TABLE call_connections (\n\tid UUID NOT NULL, \n\tencounter_id UUID NOT NULL, \n\tgeneration UUID NOT NULL, \n\tmembership_id UUID NOT NULL, \n\tsession_hash VARCHAR(64) NOT NULL, \n\tpresent BOOLEAN NOT NULL, \n\tconsent VARCHAR(16) NOT NULL, \n\tterms_version VARCHAR(32), \n\ttrack_epoch INTEGER NOT NULL, \n\ttrack_sid VARCHAR(100), \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tretired BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(encounter_id) REFERENCES calls (encounter_id) ON DELETE CASCADE, \n\tFOREIGN KEY(membership_id) REFERENCES memberships (id) ON DELETE CASCADE, \n\tFOREIGN KEY(session_hash) REFERENCES participant_sessions (token_hash) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_call_connections_encounter_id ON call_connections (encounter_id)')
    op.execute('CREATE INDEX ix_call_connections_membership_id ON call_connections (membership_id)')
    op.execute('CREATE INDEX ix_call_connections_session_hash ON call_connections (session_hash)')
    op.execute('\nCREATE TABLE audio_receipts (\n\tid UUID NOT NULL, \n\tconnection_id UUID NOT NULL, \n\ttrack_sid VARCHAR(100) NOT NULL, \n\ttrack_epoch INTEGER NOT NULL, \n\tconsent_epoch INTEGER NOT NULL, \n\tframes INTEGER NOT NULL, \n\tsamples INTEGER NOT NULL, \n\tnon_silent_frames INTEGER NOT NULL, \n\tfirst_received_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tlast_received_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_audio_receipt_epoch UNIQUE (connection_id, track_epoch, consent_epoch), \n\tFOREIGN KEY(connection_id) REFERENCES call_connections (id) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_audio_receipts_connection_id ON audio_receipts (connection_id)')
    op.execute('\nCREATE TABLE utterances (\n\tid UUID NOT NULL, \n\tconnection_id UUID NOT NULL, \n\tcontent JSONB NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(connection_id) REFERENCES call_connections (id) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_utterances_connection_id ON utterances (connection_id)')
    op.execute('\nCREATE TABLE call_events (\n\tid UUID NOT NULL, \n\tencounter_id UUID NOT NULL, \n\tcommand_id UUID NOT NULL, \n\tactor_id UUID NOT NULL, \n\trequest_hash VARCHAR(64) NOT NULL, \n\tcontent JSONB NOT NULL, \n\taccepted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_call_command UNIQUE (encounter_id, command_id), \n\tFOREIGN KEY(encounter_id) REFERENCES calls (encounter_id) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_call_events_encounter_id ON call_events (encounter_id)')

def downgrade():
    op.drop_table('call_events')
    op.drop_table('utterances')
    op.drop_table('audio_receipts')
    op.drop_table('call_connections')
    op.drop_table('calls')
