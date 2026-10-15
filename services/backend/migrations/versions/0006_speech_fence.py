"""Commit-time speech invalidation; payloads contain only visit ID and reason."""
from alembic import op
revision='0006_speech_fence'
down_revision='0005_speech'
branch_labels=None
depends_on=None

TABLES=['encounters','calls','call_connections','speech_state','memberships','participant_sessions']

def upgrade():
    op.execute("""
    CREATE FUNCTION vene_speech_fence() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE visit uuid; reason text := 'context_changed'; changed boolean := false;
    BEGIN
      IF TG_TABLE_NAME='encounters' THEN
        visit:=NEW.id; changed:=NEW.version IS DISTINCT FROM OLD.version OR NEW.projection IS DISTINCT FROM OLD.projection;
      ELSIF TG_TABLE_NAME='calls' THEN
        visit:=NEW.encounter_id;
        changed:=ROW(NEW.generation,NEW.manual_pause,NEW.output_silenced,NEW.ended,NEW.worker_error)
          IS DISTINCT FROM ROW(OLD.generation,OLD.manual_pause,OLD.output_silenced,OLD.ended,OLD.worker_error);
        reason:='processing_or_agreement_stopped';
      ELSIF TG_TABLE_NAME='call_connections' THEN
        visit:=NEW.encounter_id;
        changed:=ROW(NEW.present,NEW.consent,NEW.track_epoch,NEW.retired,NEW.expires_at)
          IS DISTINCT FROM ROW(OLD.present,OLD.consent,OLD.track_epoch,OLD.retired,OLD.expires_at);
      ELSIF TG_TABLE_NAME='speech_state' THEN
        visit:=NEW.encounter_id;
        changed:=NEW.mode_revision IS DISTINCT FROM OLD.mode_revision OR
          NEW.content->'permission_revision' IS DISTINCT FROM OLD.content->'permission_revision' OR
          (NEW.content->>'cancel' IS NOT NULL AND NEW.content->>'cancel' IS DISTINCT FROM OLD.content->>'cancel');
        IF NEW.content->>'cancel' IN ('human_interruption','manual_stop','mode_changed') THEN reason:=NEW.content->>'cancel'; END IF;
      ELSIF TG_TABLE_NAME='memberships' THEN
        visit:=NEW.encounter_id; changed:=NEW.revoked_at IS DISTINCT FROM OLD.revoked_at;
      ELSE
        SELECT encounter_id INTO visit FROM memberships WHERE id=NEW.membership_id;
        changed:=NEW.revoked_at IS DISTINCT FROM OLD.revoked_at OR NEW.expires_at IS DISTINCT FROM OLD.expires_at;
      END IF;
      IF changed THEN PERFORM pg_notify('vene_speech_fence',json_build_object('visit',visit,'reason',reason)::text); END IF;
      RETURN NEW;
    END $$;
    """)
    for table in TABLES:
        op.execute(f'CREATE TRIGGER vene_speech_fence AFTER UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION vene_speech_fence()')

def downgrade():
    for table in reversed(TABLES):op.execute(f'DROP TRIGGER vene_speech_fence ON {table}')
    op.execute('DROP FUNCTION vene_speech_fence()')
