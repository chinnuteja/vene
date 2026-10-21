"""Independent HTTP sandbox. No patient names, transcripts or clinical instructions."""
import secrets
import hashlib
import time
from datetime import date,datetime,timedelta
from uuid import UUID, uuid4
from fastapi import FastAPI, Depends, Header, HTTPException
from typing import Literal
from pydantic import Field
from sqlalchemy.orm import Session
from bring_vene.config import Settings
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import EncounterRecord,OfficeStateRecord, OfficeRequestRecord,OfficeCallbackOutboxRecord,OfficeFamilyReceiptRecord
from bring_vene.domain.service import utc_now
from bring_vene.domain.fingerprint import fingerprint
from bring_vene.execution.contracts import Input, OfficeLookup, OfficeScenario, CoverageQuery, StockQuery,CalendarSearch
from bring_vene.execution.errands import ERRANDS, BY_INSTITUTION

Institution = Literal['lab','imaging','specialist','pharmacy','plan']

class Booking(Input):
    # Deliberately minimal: no patient name, transcript, medicine, dose or instruction fields.
    request_id: UUID
    slot_id: str = Field(max_length=100)
    availability_revision: int
    order_id: UUID
    institution: Institution = 'lab'

class Order(Input):
    request_id: UUID
    institution: Institution = 'lab'

class FamilyDelivery(Input):
    request_id: UUID
    recipient_id: UUID
    text: str=Field(min_length=3,max_length=2000)
    digest: str=Field(min_length=64,max_length=64)

def state_id(institution,run=None):
    # The lab keeps the original Phase 6 row so saved sandbox data stays valid.
    return 'd:'+hashlib.sha256((str(run)+'/'+institution).encode()).hexdigest()[:18] if run else 'office' if institution=='lab' else institution

def ensure(session,institution='lab',lock=False,run=None):
    row = session.get(OfficeStateRecord,state_id(institution,run),with_for_update=lock)
    if not row:
        # Creation is a one-time launcher migration step; request access does not seed.
        raise HTTPException(503,'Sandbox office has not been initialized.')
    if run and row.content.get('sandbox_run')!=str(run):raise HTTPException(409,'Sandbox calendar namespace mismatch.')
    return row


def create_calendar(session,run):
    """Independent fictional world per rehearsal; previous receipts and saved visits remain intact."""
    for institution in BY_INSTITUTION:
        slots=institution_slots(institution)
        if institution=='lab':
            slots=[{'id':'lab:'+str(run)+':'+location.lower().replace(' ','-')+':'+day+':morning',
                'label':label+' · 9:00 AM ET · '+location,'window':'morning','location':location,'day':day,
                'starts_at':day+'T09:00:00-04:00','institution':'lab'}
                for location,day,label in [('Riverside Lab','2026-10-23','Fri, Oct 23'),('Northside','2026-10-22','Thu, Oct 22')]]
        session.add(OfficeStateRecord(id=state_id(institution,run),content={'mode':'normal','revision':1,'reserved':[],
                                      'slots':slots,'sandbox_run':str(run)}))

def serialize_writes(session):
    # One lock orders idempotency keys across every institution's writes.
    return ensure(session,'lab',lock=True)

def institution_slots(institution):
    errand=BY_INSTITUTION[institution];slots=[]
    times=[('morning','09','9:00 AM'),('afternoon','15','3:00 PM')]
    if institution=='lab':
        # Original fixed calendar: one location per day.
        offered=[(location,day,label) for location,(day,label) in zip(errand.locations,errand.days)]
    else:
        offered=[(location,day,label) for location in errand.locations for day,label in errand.days]
    for location,day,label in offered:
        for window,hour,time_label in times:
            # Stable resource identity across availability revisions.
            sid='lab:'+day+':'+window if institution=='lab' else institution+':'+location.lower().replace(' ','-')+':'+day+':'+window
            slots.append({'id':sid,'label':label+' · '+time_label+' ET · Fictional '+location,'window':window,
                'location':location,'day':day,'starts_at':day+'T'+hour+':00:00-04:00','institution':institution})
    return slots

# Fictional health plans. Rules and formulary are plan facts the sandbox returns; Vene never derives them.
PLANS={'basic':{'name':'Evergreen Basic (fictional)','prior_auth':['imaging'],
        'formulary':{'Tamorin':'covered','Celvane':'covered','Lorvexa':'not_covered'},'alternatives':{'Lorvexa':['Tamorin','Celvane']}},
    'plus':{'name':'Evergreen Plus (fictional)','prior_auth':[],
        'formulary':{'Tamorin':'covered','Celvane':'covered','Lorvexa':'covered'},'alternatives':{}}}
MEMBERS={'EVG-B-1001':'basic','EVG-P-2002':'plus','EVG-B-3003':'basic'}

def initialize(engine):
    with Session(engine) as session, session.begin():
        if not session.get(OfficeStateRecord,'plan',with_for_update=True):
            # Review resources are created per lookup; members and rules are fixed fictional data.
            session.add(OfficeStateRecord(id='plan',content={'mode':'normal','revision':1,'reserved':[],'slots':[]}))
        for institution in BY_INSTITUTION:
            if institution=='plan':continue
            slots=institution_slots(institution);key=state_id(institution)
            row=session.get(OfficeStateRecord,key,with_for_update=True)
            if not row:session.add(OfficeStateRecord(id=key,content={'mode':'normal','revision':1,'reserved':[],'slots':slots}))
            elif 'slots' not in row.content:
                row.content={**row.content,'slots':slots,'reserved':[s['id'] for s in slots if any(x.endswith(':'+s['window']) for x in row.content['reserved'])]}
            else:
                existing={s['id']:s for s in row.content['slots']}
                row.content={**row.content,'slots':[{**s,**existing.get(s['id'],{}),'location':s['location'],'day':s['day']} for s in slots]}

def office_app(settings=None,engine=None):
    settings=settings or Settings();engine=engine if engine is not None else make_engine(settings.database_url)
    app=FastAPI(title='Bring Vene — LOCAL SANDBOX OFFICE')
    def authorized(authorization: str | None = Header(default=None),
                   run:UUID|None=Header(default=None,alias='x-vene-sandbox-run')):
        if not settings.bring_vene_development or not settings.office_token or not secrets.compare_digest(authorization or '', 'Bearer '+settings.office_token):
            raise HTTPException(403,'Sandbox service access denied.')
        if run:
            with Session(engine) as session:
                visit=session.get(EncounterRecord,run)
                if not visit or visit.projection.get('demo_run')!=str(run):raise HTTPException(404,'Sandbox calendar not found.')
        return run

    @app.get('/health')
    def health():return {'sandbox':True}

    @app.post('/scenario',dependencies=[Depends(authorized)])
    def scenario(body:OfficeScenario,run=Depends(authorized)):
        with Session(engine) as session,session.begin():
            row=ensure(session,body.institution,lock=True,run=run)
            row.content={**row.content,'mode':body.mode,'revision':row.content['revision']+1}
            return {'sandbox':True,'institution':body.institution,'mode':body.mode,'revision':row.content['revision']}

    @app.get('/formulary',dependencies=[Depends(authorized)])
    def formulary():
        # Published medicine names only, so a caller can match locally without sending free text.
        return {'sandbox':True,'institution':'plan','names':sorted({n for plan in PLANS.values() for n in plan['formulary']})}

    @app.post('/coverage',dependencies=[Depends(authorized)])
    def coverage(body:CoverageQuery,run=Depends(authorized)):
        with Session(engine) as session:
            mode=ensure(session,'plan',run=run).content['mode']
        if body.member_ref not in MEMBERS:raise HTTPException(404,'Member not found in the sandbox plan.')
        plan=PLANS[MEMBERS[body.member_ref]]
        if mode=='delayed':time.sleep(1.4)
        result={'sandbox':True,'institution':'plan','plan':plan['name'],'service':body.service,'reference':str(uuid4()),
            'checked_at':utc_now().isoformat(),'prior_authorization_required':body.service in plan['prior_auth'],
            'formulary':None,'alternatives':[]}
        if body.service=='prescription':
            result['formulary']=plan['formulary'].get(body.medicine or '','unknown')
            result['alternatives']=plan['alternatives'].get(body.medicine or '',[]) if result['formulary']=='not_covered' else []
        return result

    @app.post('/stock',dependencies=[Depends(authorized)])
    def stock(body:StockQuery,run=Depends(authorized)):
        with Session(engine) as session:
            content=ensure(session,'pharmacy',run=run).content
        if body.location not in BY_INSTITUTION['pharmacy'].locations:raise HTTPException(404,'Pharmacy not found.')
        return {'sandbox':True,'institution':'pharmacy','location':body.location,'checked_at':utc_now().isoformat(),
            'reference':str(uuid4()),'in_stock':content['mode']!='out_of_stock'}

    @app.get('/requirements',dependencies=[Depends(authorized)])
    def requirements():
        return {'sandbox':True,'institution':'specialist','reference':str(uuid4()),'checked_at':utc_now().isoformat(),
            'requires':['referral packet']}

    @app.post('/lookup',dependencies=[Depends(authorized)])
    def lookup(body:OfficeLookup,run=Depends(authorized)):
        if body.institution=='plan':
            # A prior-authorization review is opened per request rather than chosen from a calendar.
            with Session(engine) as session,session.begin():
                row=ensure(session,'plan',lock=True,run=run);content=row.content
                slot={'id':'plan:review:'+str(uuid4()),'label':'Prior authorization review · Evergreen Health Plan (fictional)',
                    'window':body.window,'location':'Evergreen Health Plan','day':body.day,'institution':'plan'}
                row.content={**content,'slots':[*content['slots'],slot][-200:]}
                stamp=utc_now()
                return {'sandbox':True,'institution':'plan','revision':content['revision'],'checked_at':stamp.isoformat(),
                    'expires_at':(stamp+timedelta(seconds=120)).isoformat(),'slot':slot}
        with Session(engine) as session:
            content=ensure(session,body.institution,run=run).content
            delay=content['mode']=='delayed'
            stamp=utc_now();revision=content['revision']
            slot=next((s for s in content['slots'] if s['window']==body.window and s['location']==body.location and s['day']==body.day and s['id'] not in content['reserved']),None)
            result={'sandbox':True,'institution':body.institution,'revision':revision,'checked_at':stamp.isoformat(),
                'expires_at':(stamp+timedelta(seconds=-1 if content['mode']=='expired' else 120)).isoformat(),
                'slot':None if content['mode']=='no_slot' else slot}
        if delay:time.sleep(1.4)
        return result

    @app.post('/availability',dependencies=[Depends(authorized)])
    def availability(body:CalendarSearch,run=Depends(authorized)):
        start,end=date.fromisoformat(body.earliest),date.fromisoformat(body.latest)
        if end<start or (end-start).days>14:raise HTTPException(422,'Choose a window of up to fourteen days.')
        if body.preferred not in BY_INSTITUTION['lab'].locations:raise HTTPException(422,'Unknown lab.')
        with Session(engine) as session:
            content=ensure(session,'lab',run=run).content
            available=[] if content['mode']=='no_slot' else [s for s in content['slots'] if s['id'] not in content['reserved'] and s['day']>=body.earliest]
            def expose(slot):
                day=date.fromisoformat(slot['day']);hour=datetime.fromisoformat(slot['starts_at']).hour
                return {**slot,'day_name':day.strftime('%A'),'time_label':str(hour%12 or 12)+('am' if hour<12 else 'pm')}
            preferred=sorted((s for s in available if s['location']==body.preferred),key=lambda s:s['starts_at'])
            alternatives=sorted((s for s in available if s['location']!=body.preferred and s['day']<=body.latest),key=lambda s:s['starts_at'])
            stamp=utc_now()
            return {'sandbox':True,'institution':'lab','reference':str(uuid4()),'revision':content['revision'],
                'checked_at':stamp.isoformat(),'expires_at':(stamp+timedelta(seconds=120)).isoformat(),
                'preferred_first':expose(preferred[0]) if preferred else None,'alternatives':[expose(s) for s in alternatives[:8]]}

    @app.post('/orders',dependencies=[Depends(authorized)])
    def order(body:Order,run=Depends(authorized)):
        with Session(engine) as session,session.begin():
            serialize_writes(session)
            old=session.get(OfficeRequestRecord,body.request_id)
            if old:
                if old.kind!='order' or old.content.get('institution','lab')!=body.institution or old.content.get('sandbox_run')!=(str(run) if run else None):raise HTTPException(409,'Request ID reused.')
                return old.content
            # A synthetic clinician document (order, referral packet or prescription) for one institution.
            receipt={'sandbox':True,'order_id':str(body.request_id),'status':'available','issued_at':utc_now().isoformat(),
                'institution':body.institution,'document':BY_INSTITUTION[body.institution].document}
            if run:receipt['sandbox_run']=str(run)
            session.add(OfficeRequestRecord(request_id=body.request_id,kind='order',content=receipt));return receipt

    @app.post('/bookings',dependencies=[Depends(authorized)])
    def booking(body:Booking,run=Depends(authorized)):
        ambiguous=False
        with Session(engine) as session,session.begin():
            serialize_writes(session);row=ensure(session,body.institution,lock=True,run=run)
            old=session.get(OfficeRequestRecord,body.request_id)
            payload=body.model_dump(mode='json')
            if body.institution=='lab':payload.pop('institution') # Original Phase 6 request shape.
            if old:
                if old.kind!='booking' or old.content['payload']!=payload or old.content.get('sandbox_run')!=(str(run) if run else None):raise HTTPException(409,'Request ID reused with different content.')
                return old.content['result']
            order=session.get(OfficeRequestRecord,body.order_id)
            if not order or order.kind!='order' or order.content.get('institution','lab')!=body.institution or order.content.get('sandbox_run')!=(str(run) if run else None):
                raise HTTPException(409,'Required sandbox '+BY_INSTITUTION[body.institution].document+' missing.')
            content=row.content
            valid_slots={s['id'] for s in content['slots']}
            rejected=(content['mode'] in {'no_slot','expired','rejected'} or body.availability_revision!=content['revision'] or
                      body.slot_id not in valid_slots or body.slot_id in content['reserved'])
            result={'sandbox':True,'status':'rejected' if rejected else 'confirmed','request_id':str(body.request_id),
                    'receipt_id':str(uuid4()),'slot_id':body.slot_id,'recorded_at':utc_now().isoformat(),
                    'reason':'Availability changed or office rejected the request.' if rejected else 'Persisted sandbox reservation.'}
            if content['mode']=='duplicate_callback':
                # Two identical receipt events in one sandbox response exercise ingestion
                # without pretending to send authenticated office callbacks (Phase 7).
                result['duplicate_events']=[dict(result),dict(result)]
            session.add(OfficeRequestRecord(request_id=body.request_id,kind='booking',content={'payload':payload,'result':result,**({'sandbox_run':str(run)} if run else {})}))
            session.flush() # Persist the office parent before its independent callback outbox.
            for _ in range(2 if content['mode']=='duplicate_callback' else 1):
                session.add(OfficeCallbackOutboxRecord(id=uuid4(),request_id=body.request_id,content=result,
                    next_at=utc_now()+timedelta(seconds=2),attempts=0))
            if not rejected:row.content={**content,'reserved':[*content['reserved'],body.slot_id]}
            ambiguous=content['mode']=='timeout_after_write' and not rejected
        if ambiguous:time.sleep(1.4) # Commit succeeded; client may time out before receiving it.
        return result

    @app.get('/requests/{request_id}',dependencies=[Depends(authorized)])
    def reconcile(request_id:UUID,run=Depends(authorized)):
        with Session(engine) as session:
            old=session.get(OfficeRequestRecord,request_id)
            if old and old.content.get('sandbox_run')!=(str(run) if run else None):old=None
            return {'sandbox':True,'found':bool(old),'result':old.content['result'] if old and old.kind=='booking' else None}

    @app.post('/callbacks/{request_id}/repeat',dependencies=[Depends(authorized)])
    def repeat_callback(request_id:UUID):
        with Session(engine) as session,session.begin():
            old=session.get(OfficeRequestRecord,request_id)
            if not old or old.kind!='booking':raise HTTPException(404,'Office request not found.')
            job=OfficeCallbackOutboxRecord(id=uuid4(),request_id=request_id,content=old.content['result'],next_at=utc_now(),attempts=0)
            session.add(job);return {'sandbox':True,'delivery_id':str(job.id)}

    @app.post('/family-updates',dependencies=[Depends(authorized)])
    def family_delivery(body:FamilyDelivery):
        payload_hash=fingerprint(body.model_dump(mode='json'));delayed=False
        with Session(engine) as session,session.begin():
            office=serialize_writes(session)
            prior=session.get(OfficeFamilyReceiptRecord,body.request_id)
            if prior:
                if prior.payload_hash!=payload_hash:raise HTTPException(409,'Delivery ID reused with different fields.')
                return prior.content
            receipt={'sandbox':True,'request_id':str(body.request_id),'recipient_id':str(body.recipient_id),
                'receipt_id':str(uuid4()),'status':'delivered','payload_hash':payload_hash,'received_at':utc_now().isoformat()}
            # Acknowledges receipt of the approved payload without retaining its
            # sensitive text in the independent service or ordinary logs.
            session.add(OfficeFamilyReceiptRecord(id=body.request_id,payload_hash=payload_hash,content=receipt))
            delayed=office.content['mode']=='timeout_after_write'
        if delayed:time.sleep(1.4)
        return receipt

    @app.get('/family-updates/{request_id}',dependencies=[Depends(authorized)])
    def family_receipt(request_id:UUID):
        with Session(engine) as session:
            row=session.get(OfficeFamilyReceiptRecord,request_id)
            return {'sandbox':True,'found':bool(row),'result':row.content if row else None}
    return app

app=office_app()
