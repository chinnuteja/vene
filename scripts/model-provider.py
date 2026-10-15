"""Return only the explicitly configured live provider; never print credentials."""
from bring_vene.config import Settings
from bring_vene.understanding.gateway import configuration
provider,_=configuration(Settings())
if provider not in ('openai','deepseek'):
    raise SystemExit(2)
print(provider)
