"""Read presence only; reject before resetting data, generating audio or calling providers."""
import sys
import json
from datetime import datetime,timezone
from pathlib import Path
from bring_vene.config import Settings
s=Settings()
model_key={'openai':('OPENAI_API_KEY',s.openai_api_key),'deepseek':('DEEPSEEK_API_KEY',s.deepseek_api_key)}.get(s.model_provider,('MODEL_PROVIDER (openai or deepseek)',False))
missing=[name for name,value in [model_key,('DEEPGRAM_API_KEY',s.deepgram_api_key),
    ('CARTESIA_API_KEY',s.cartesia_api_key),('CARTESIA_VOICE_ID',s.cartesia_voice_id)] if not value]
Path('docs/qa/phase-08-live-config.json').write_text(json.dumps({'checked_at':datetime.now(timezone.utc).isoformat(),
    'model_provider':s.model_provider,'model_key_present':bool(model_key[1]),'deepgram_key_present':bool(s.deepgram_api_key),
    'cartesia_key_present':bool(s.cartesia_api_key),'cartesia_voice_present':bool(s.cartesia_voice_id),
    'missing':missing,'credential_validity':'not_established_by_presence_check'},indent=2)+'\n')
if missing:
    print('Live gates remain unverified. Missing configuration: '+', '.join(missing)+'. No provider call or database reset was started.')
    sys.exit(2)
print('All live-provider configuration fields are present. Values are not displayed; credentials still require actual verification.')
