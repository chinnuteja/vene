import base64,hashlib,json,os,re,subprocess,sys
from uuid import uuid4
from sqlalchemy.orm import Session
from bring_vene.domain.contracts import Evidence
from bring_vene.domain.service import DomainError,utc_now
from bring_vene.domain.context import context_adapter
from bring_vene.persistence.models import DocumentRecord,EvidenceRecord
from bring_vene.execution.service import access,patient,plan_fingerprint
from bring_vene.understanding.service import fingerprint
from bring_vene.continuity.contracts import Difference

DAYS=r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b'

def extract(request):
    if request.format=='text':
        raw=request.text.encode();return request.text,[{'page':1,'start':0,'end':len(request.text)}],hashlib.sha256(raw).hexdigest()
    try:
        raw=base64.b64decode(request.file_base64,validate=True)
        if len(raw)>250000 or not raw.startswith(b'%PDF-'):raise ValueError()
        # No database/provider secrets reach the parser process. No raw file is saved.
        env={key:os.environ[key] for key in ['SystemRoot','WINDIR','TEMP','TMP'] if key in os.environ}
        env['PYTHONNOUSERSITE']='1';env['PYTHONIOENCODING']='utf-8'
        result=subprocess.run([sys.executable,'-m','bring_vene.continuity.pdf_parser'],input=raw,capture_output=True,
            timeout=5,env=env,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if result.returncode or len(result.stdout)>60000:raise ValueError()
        parsed=json.loads(result.stdout);parts=[];pages=[];offset=0
        for page in parsed['pages']:
            text=page['text'];parts.append(text);pages.append({'page':page['page'],'start':offset,'end':offset+len(text)});offset+=len(text)+1
        text='\n'.join(parts)
        if not 3<=len(text)<=12000:raise ValueError()
        return text,pages,hashlib.sha256(raw).hexdigest()
    except Exception:raise DomainError(422,'Use a machine-readable, unencrypted PDF of at most 250 KB and 10 pages. Scanned PDF OCR is not included.')

def quote(text,match):
    start=text.rfind('\n',0,match.start())+1
    line_end=text.find('\n',match.end());end=line_end if line_end!=-1 else len(text)
    end=min(end,start+300)
    return text[start:end],start,end

def compare(view,text,plan_ids):
    differences=[]
    day_matches=list(re.finditer(DAYS,text,re.I));doc_days={m.group().lower() for m in day_matches}
    location=re.search(r'\bat\s+([A-Z][A-Za-z\x20\-\']{1,65}?(?:Lab|Laboratory|Clinic))\b',text)
    for item in view.plan:
        if item.origin=='preparation' or str(item.id) not in {str(x) for x in plan_ids}:continue
        expected_days={m.group().lower() for m in re.finditer(DAYS,item.timeframe or '',re.I)}
        if expected_days and doc_days and doc_days!=expected_days:
            excerpt,start,end=quote(text,day_matches[0])
            differences.append(Difference(kind='timing',plan_id=item.id,source_quote=excerpt,start=start,end=end,
                expected=item.timeframe,explanation='The document and conversation draft name different or ambiguous days. Ask the responsible clinician to clarify.'))
        if location and item.location and location.group(1).casefold()!=item.location.casefold():
            excerpt,start,end=quote(text,location)
            differences.append(Difference(kind='location',plan_id=item.id,source_quote=excerpt,start=start,end=end,
                expected=item.location,explanation='The named location differs from the conversation draft. No reservation is moved.'))
    instruction=re.search(r'\b(stop taking|increase|reduce|double|skip|dose|medication|prescription)\b',text,re.I)
    if instruction:
        excerpt,start,end=quote(text,instruction)
        differences.append(Difference(kind='clinical_instruction',source_quote=excerpt,start=start,end=end,
            explanation='This document contains wording about a clinical instruction. It remains unverified; no medication change or action is generated.'))
    if not differences:
        differences.append(Difference(kind='review',source_quote=text[:300],start=0,end=min(300,len(text)),
            explanation='Human review is still required. The limited matcher cannot establish clinical agreement or correctness.'))
    return differences[:16]

def comparison_fingerprint(view,row):
    source=next((e for e in view.evidence if e.id==row.evidence_id),None)
    if not source:return None
    selected=set(row.content['plan_ids'])
    return fingerprint({'source':source.model_dump(mode='json',exclude={'audiences'}),'plans':{
        str(p.id):{'item':p.model_dump(mode='json',exclude={'audiences'}),'sources':[
            e.model_dump(mode='json',exclude={'audiences'}) for e in view.evidence if e.id in p.evidence_refs]}
        for p in view.plan if str(p.id) in selected},'selected':sorted(selected)})

def upload(engine,visit_id,token,csrf,request):
    # Authorization precedes processing any file/text.
    with Session(engine) as session,session.begin():
        _,view,member,_=access(session,visit_id,token,csrf);patient(member)
        original_version=view.version
    text,pages,sha=extract(request)
    with Session(engine) as session,session.begin():
        encounter,view,member,_=access(session,visit_id,token,csrf);patient(member)
        if view.version!=original_version:raise DomainError(409,'The visit changed while this document was being read. Review the current step and upload again.')
        if not set(request.plan_ids)<={p.id for p in view.plan}:raise DomainError(404,'A selected conversation step was not found.')
        source=Evidence(id=uuid4(),source_type='imported_record',title=request.title.strip(),text=text,observed_at=utc_now(),origin='human')
        session.add(EvidenceRecord(id=source.id,encounter_id=visit_id,content=source.model_dump(mode='json')));view.evidence.append(source)
        session.flush() # Provenance must exist before the document's evidence foreign key.
        row=DocumentRecord(id=uuid4(),encounter_id=visit_id,evidence_id=source.id,created_at=utc_now(),content={
            'format':request.format,'sha256':sha,'pages':pages,'review_state':'unresolved','plan_ids':[str(x) for x in request.plan_ids]})
        row.content={**row.content,'comparison_fingerprint':comparison_fingerprint(view,row),
            'differences':[d.model_dump(mode='json') for d in compare(view,text,request.plan_ids)]};session.add(row)
        view.version+=1;view.consent_epoch+=1;view.updated_at=utc_now();encounter.version=view.version
        encounter.projection=view.model_dump(mode='json');encounter.updated_at=view.updated_at
        return row.id

def review(engine,visit_id,document_id,token,csrf,request):
    with Session(engine) as session,session.begin():
        _,view,member,_=access(session,visit_id,token,csrf)
        if member.role!='clinician':raise DomainError(403,'The responsible clinician records this review; a patient upload does not choose clinical correctness.')
        row=session.get(DocumentRecord,document_id)
        if not row or row.encounter_id!=visit_id:raise DomainError(404,'Document not found.')
        scoped=context_adapter.view(view,member.role,member.id)
        if row.evidence_id not in {e.id for e in scoped.evidence}:raise DomainError(404,'Document not found.')
        referenced=set(row.content['plan_ids'])
        if not referenced<={str(p.id) for p in scoped.plan}:raise DomainError(403,'The relevant step and its sources must be shared before review.')
        current=comparison_fingerprint(view,row)
        if request.fingerprint!=current:raise DomainError(409,'This source or conversation draft changed. Review it again.')
        row.content={**row.content,'review_state':'reviewed','review_fingerprint':current,'reviewed_by':member.name,
            'review_note':request.note,'reviewed_at':utc_now().isoformat()}
        # A review acknowledgment does not change a clinical plan, order or booking.
