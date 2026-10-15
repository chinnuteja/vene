"""Versioned conversation sources and bounded interpretation journal (frozen schema)."""
from alembic import op
revision='0004_understanding'
down_revision='0003_calls'
branch_labels=None
depends_on=None

def upgrade():
    op.execute('\nCREATE TABLE understanding (\n\tencounter_id UUID NOT NULL, \n\tenabled BOOLEAN NOT NULL, \n\tsession_hash VARCHAR(64), \n\trevision INTEGER NOT NULL, \n\tprocessed_revision INTEGER NOT NULL, \n\tstate VARCHAR(20) NOT NULL, \n\tmessage VARCHAR(300) NOT NULL, \n\tPRIMARY KEY (encounter_id), \n\tFOREIGN KEY(encounter_id) REFERENCES encounters (id) ON DELETE CASCADE, \n\tFOREIGN KEY(session_hash) REFERENCES participant_sessions (token_hash) ON DELETE CASCADE\n)\n\n')
    op.execute('\nCREATE TABLE transcript_sources (\n\tid UUID NOT NULL, \n\tencounter_id UUID NOT NULL, \n\tmembership_id UUID NOT NULL, \n\tutterance_id UUID, \n\tversion INTEGER NOT NULL, \n\tcontent JSONB NOT NULL, \n\thistory JSONB NOT NULL, \n\tfinalized_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(id) REFERENCES evidence (id) ON DELETE CASCADE, \n\tFOREIGN KEY(encounter_id) REFERENCES encounters (id) ON DELETE CASCADE, \n\tFOREIGN KEY(membership_id) REFERENCES memberships (id) ON DELETE CASCADE, \n\tUNIQUE (utterance_id), \n\tFOREIGN KEY(utterance_id) REFERENCES utterances (id) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_transcript_sources_encounter_id ON transcript_sources (encounter_id)')
    op.execute('CREATE INDEX ix_transcript_sources_finalized_at ON transcript_sources (finalized_at)')
    op.execute('\nCREATE TABLE interpretation_runs (\n\tid UUID NOT NULL, \n\tencounter_id UUID NOT NULL, \n\tfingerprint VARCHAR(64) NOT NULL, \n\tstate VARCHAR(20) NOT NULL, \n\tprovider VARCHAR(20) NOT NULL, \n\tmodel VARCHAR(100) NOT NULL, \n\tinput_snapshot JSONB NOT NULL, \n\toutput JSONB, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tfinished_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(encounter_id) REFERENCES encounters (id) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_interpretation_runs_encounter_id ON interpretation_runs (encounter_id)')
    op.execute('\nCREATE TABLE understanding_mutations (\n\tid UUID NOT NULL, \n\tencounter_id UUID NOT NULL, \n\tcommand_id UUID NOT NULL, \n\tactor_id UUID NOT NULL, \n\trequest_hash VARCHAR(64) NOT NULL, \n\tcontent JSONB NOT NULL, \n\taccepted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_understanding_command UNIQUE (encounter_id, command_id), \n\tFOREIGN KEY(encounter_id) REFERENCES encounters (id) ON DELETE CASCADE\n)\n\n')
    op.execute('CREATE INDEX ix_understanding_mutations_encounter_id ON understanding_mutations (encounter_id)')

def downgrade():
    op.drop_table('understanding_mutations')
    op.drop_table('interpretation_runs')
    op.drop_table('transcript_sources')
    op.drop_table('understanding')
