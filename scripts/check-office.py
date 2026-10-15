"""Actual read-only sandbox availability through the application gateway."""
import json
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse
from bring_vene.config import Settings
from bring_vene.execution.gateway import OfficeGateway

s=Settings()
report={'checked_at':datetime.now(timezone.utc).isoformat(),'sandbox':True,'booking_sent':False,
    'development':s.bring_vene_development,'loopback':urlparse(s.office_url).hostname=='127.0.0.1',
    'timeout_seconds':s.office_timeout_seconds}
try:
    result=OfficeGateway(s).call('/lookup',{'location':'Riverside Lab','day':'2026-10-20','window':'morning'})
    assert result['sandbox'] and result['slot'] and result['slot']['location']=='Riverside Lab'
    report['status']='passed'
except Exception as error:
    report.update(status='failed',error_type=type(error).__name__,http_status=getattr(error,'code',None))
Path('docs/qa/phase-08-office-preflight.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
raise SystemExit(0 if report['status']=='passed' else 1)
