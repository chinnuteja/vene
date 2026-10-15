"""Owned sandbox callback delivery; fresh signed nonce on every retry."""
import json,time
from datetime import timedelta
from uuid import uuid4
from urllib.parse import urlparse
from urllib.request import Request,build_opener
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.config import Settings
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import OfficeCallbackOutboxRecord
from bring_vene.domain.service import utc_now
from bring_vene.execution.gateway import NoRedirect
from bring_vene.continuity.callbacks import headers

def deliver(engine,settings,transport=None):
    if not settings.office_callback_url or not settings.office_callback_secret:return False
    with Session(engine) as session,session.begin():
        job=session.scalar(select(OfficeCallbackOutboxRecord).where(OfficeCallbackOutboxRecord.acknowledged_at.is_(None),
            OfficeCallbackOutboxRecord.next_at<=utc_now(),(OfficeCallbackOutboxRecord.lease_until.is_(None))|
            (OfficeCallbackOutboxRecord.lease_until<utc_now())).order_by(OfficeCallbackOutboxRecord.next_at).with_for_update(skip_locked=True).limit(1))
        if not job:return False
        job.lease_id=uuid4();job.lease_until=utc_now()+timedelta(seconds=5);job.attempts+=1
        job_id,lease_id=job.id,job.lease_id
        payload={'delivery_id':str(job.id),'result':{k:v for k,v in job.content.items() if k!='duplicate_events'}}
        body=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    accepted=False
    try:
        parsed=urlparse(settings.office_callback_url)
        if not settings.bring_vene_development or parsed.scheme!='http' or parsed.hostname!='127.0.0.1' or parsed.path!='/integrations/office/results' or parsed.username or parsed.query or parsed.fragment:
            raise ValueError('Only an explicit local callback receiver is allowed.')
        signed=headers(settings.office_callback_secret,body)
        if transport:accepted=bool(transport(body,signed).get('accepted'))
        else:
            request=Request(settings.office_callback_url,data=body,headers=signed)
            with build_opener(NoRedirect).open(request,timeout=2) as response:
                accepted=json.loads(response.read(4096)).get('accepted') is True
    except Exception:accepted=False
    with Session(engine) as session,session.begin():
        job=session.get(OfficeCallbackOutboxRecord,job_id,with_for_update=True)
        if not job or job.lease_id!=lease_id:return True
        job.lease_id=None;job.lease_until=None
        if accepted:job.acknowledged_at=utc_now()
        else:job.next_at=utc_now()+timedelta(seconds=min(60,2**min(job.attempts,5)))
    return True

def main():
    settings=Settings();engine=make_engine(settings.database_url)
    print('Sandbox office callback worker ready.',flush=True)
    try:
        while True:
            try:worked=deliver(engine,settings)
            except Exception as error:print('Office callback worker unavailable: '+type(error).__name__,flush=True);worked=False
            time.sleep(.2 if worked else .5)
    finally:engine.dispose()

if __name__=='__main__':main()
