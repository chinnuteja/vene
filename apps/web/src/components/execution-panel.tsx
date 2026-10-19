'use client';
import {useDemoTools} from '@/lib/demo-tools';
import {useEffect,useState} from 'react';
import {CalendarCheck,CheckCircle2,Circle,CircleAlert,Clock,ShieldCheck,Users} from 'lucide-react';
import {request,type Encounter,type Identity,type Member} from '@/lib/api/client';
import type {components} from '../../../../packages/contracts/schema';
type View=components['schemas']['ExecutionView'];
type Action=components['schemas']['ActionView'];
type Errand=components['schemas']['ErrandOption'];
type Circle=components['schemas']['CircleView'];
type Bundle=components['schemas']['BundleResult'];
type Feasibility=components['schemas']['FeasibilityView'];
type Kind=Errand['kind'];
const labels:Record<string,string>={checking:'Checking office',suggested:'Slot suggested · not booked',no_slot:'No suitable slot',expired:'Availability expired',queued:'Approved · queued',in_flight:'Request in flight',unknown:'Completion unknown · reconciling',confirmed:'Reservation confirmed',rejected:'Office rejected request',invalidated:'Changed · check again',cancelled:'Not sent',unavailable:'Office unavailable'};
const scenarios=['normal','no_slot','expired','delayed','rejected','timeout_after_write','duplicate_callback'] as const;
const scenarioLabels:Record<typeof scenarios[number],string>={normal:'Slots available',no_slot:'No slots',expired:'Expired availability',delayed:'Delayed lookup',rejected:'Office rejects',timeout_after_write:'Timeout after write',duplicate_callback:'Duplicate response'};
const LEGACY_LAB=/\b(lab|laboratory|blood)\b/i;

function stateLabel(a:Action,errand?:Errand){
  if(a.state==='confirmed'&&errand&&a.kind!=='lab')return errand.confirmed;
  return labels[a.state]??a.state;
}
function documentName(errand?:Errand){return errand?errand.document:'order';}
// One plain sentence for what this step is waiting on. Separate facts stay separate.
function waitingOn(a:Action|undefined,errand?:Errand){
  if(!a)return 'Not checked yet';
  if(a.state==='confirmed')return a.kind==='authorization'?'Approved by the sandbox health plan':'Confirmed by the '+(errand?.place??'office')+' with a sandbox receipt';
  if(a.state==='queued'||a.state==='in_flight')return 'Sent to the '+(errand?.place??'office')+' · waiting for its receipt';
  if(a.state==='unknown')return 'Reconciling with the '+(errand?.place??'office')+' before any retry';
  if(a.state!=='suggested')return a.message;
  const missing=[];
  if(!a.clinician_confirmed)missing.push('clinician confirmation');
  if(!a.order_available)missing.push('the '+documentName(errand));
  if(/prior authorization/.test(a.message))missing.push('an approved prior authorization');
  if(!a.patient_authorized&&!missing.length)return 'Ready for your approval';
  return 'Waiting on '+missing.join(' and ');
}

export function ExecutionPanel({visit,viewer}:{visit:Encounter;viewer:Identity}){
  const demoTools=useDemoTools();
  const [view,setView]=useState<View|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [pollError,setPollError]=useState('');
  const [circle,setCircle]=useState<Circle|null>(null),[family,setFamily]=useState<Member[]>([]);
  const [checks,setChecks]=useState<Feasibility|null>(null);
  const [windows,setWindows]=useState<Record<string,'morning'|'afternoon'>>({});
  const [places,setPlaces]=useState<Record<string,string>>({}),[days,setDays]=useState<Record<string,string>>({});
  const [scenarioKind,setScenarioKind]=useState<Kind>('lab');
  const [notice,setNotice]=useState('');
  const root='/encounters/'+visit.id+'/execution',circleRoot='/encounters/'+visit.id+'/care-circle';
  const patient=viewer.role==='patient',clinician=viewer.role==='clinician',familyViewer=viewer.role==='family';
  useEffect(()=>{
    let alive=true;let pending=false;
    async function poll(){if(pending)return;pending=true;try{
      const [data,asks,found]=await Promise.all([request<View>(root),viewer.role==='clinician'?Promise.resolve(null):request<Circle>(circleRoot),
        viewer.role==='family'?Promise.resolve(null):request<Feasibility>('/encounters/'+visit.id+'/feasibility')]);
      if(alive){setView(data);setCircle(asks);setChecks(found);setPollError('');}
    }catch(e){if(alive){setView(null);setPollError((e as Error).message);}}finally{pending=false;}}
    void poll();const timer=setInterval(()=>void poll(),750);return()=>{alive=false;clearInterval(timer);};
  },[root,circleRoot,viewer.membership_id,viewer.role,visit.version]);
  useEffect(()=>{
    if(!patient)return;
    request<Member[]>('/encounters/'+visit.id+'/members').then(all=>setFamily(all.filter(m=>m.role==='family'&&!m.revoked))).catch(()=>setFamily([]));
  },[patient,visit.id,visit.version]);
  async function change(path:string,body:Record<string,unknown>,base=root){setBusy(true);setError('');setNotice('');try{
    const result=await request<unknown>(base+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    setView(await request<View>(root));
    if(base===circleRoot)setCircle(result as Circle);
    if(path.endsWith('/scope'))setNotice(body.allowed?'Office checks allowed. Booking still needs your separate approval.':'Office permission withdrawn. Already dispatched requests will still be reconciled; confirmed reservations are not cancelled.');
    if(path==='/approve-ready'){
      const outcomes=(result as Bundle).outcomes;const queued=outcomes.filter(o=>o.outcome==='queued').length;
      const held=outcomes.filter(o=>o.outcome!=='queued'&&o.outcome!=='already_approved');
      setNotice(queued+' step'+(queued===1?'':'s')+' sent to the sandbox.'+(held.length?' '+held.map(o=>o.message).join(' '):'')+' Each one is confirmed or rejected separately.');
    }
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}}

  const catalog=new Map((view?.errands??[]).map(e=>[e.kind,e]));
  const steps=visit.plan.map(item=>({item,kind:(item.kind&&item.kind!=='other'?item.kind:!item.kind&&LEGACY_LAB.test(item.title+' '+item.detail)?'lab':null) as Kind|null})).filter(s=>s.kind);
  const latestFor=(id:string)=>view?.actions.find(a=>a.item_id===id);
  const ready=steps.map(s=>latestFor(s.item.id)).filter((a):a is Action=>!!a&&a.state==='suggested'&&!!a.digest&&a.clinician_confirmed&&a.order_available&&!a.patient_authorized);

  function info(a:Action){const errand=catalog.get(a.kind);const lab=a.kind==='lab';return <div className="office-result">
    <span className={'pill '+(a.state==='confirmed'?'green':'amber')}>{stateLabel(a,errand)}</span>
    <p>{a.message}</p>{a.slot&&<strong>{String(a.slot.label)}</strong>}
    <p className="muted">{lab?a.source:'Local sandbox '+a.place}{a.checked_at?' · checked '+new Date(a.checked_at).toLocaleTimeString():''}</p>
    <div className="office-prerequisites"><span>Clinician: {a.clinician_confirmed?'confirmed':'awaiting confirmation'}</span><span>{lab?'Order: ':a.document.charAt(0).toUpperCase()+a.document.slice(1)+': '}{a.order_available?(lab?'sandbox order available':'sandbox '+a.document+' available'):(lab?'required order missing':'required '+a.document+' missing')}</span><span>Your booking approval: {a.patient_authorized?'recorded':'not given'}</span></div>
    {clinician&&a.state==='suggested'&&a.fingerprint&&<div className="office-buttons">
      <button className="secondary-button" disabled={busy||a.clinician_confirmed} onClick={()=>void change('/actions/'+a.id+'/prerequisites',{expected_fingerprint:a.fingerprint,order:false})}>{lab?'Confirm intended lab step':'Confirm intended '+a.kind+' step'}</button>
      <button className="secondary-button" disabled={busy||a.order_available} onClick={()=>void change('/actions/'+a.id+'/prerequisites',{expected_fingerprint:a.fingerprint,order:true})}>{lab?'Confirm and issue sandbox order':'Confirm and send sandbox '+a.document}</button>
    </div>}
    {patient&&a.state==='suggested'&&a.digest&&<button className="primary-button" disabled={busy} onClick={()=>void change('/actions/'+a.id+'/approve',{digest:a.digest})}>Approve this sandbox reservation</button>}
    {a.receipt&&<details className="office-receipt" open><summary>Sandbox {lab?'office':a.place} receipt</summary><dl><div><dt>Receipt</dt><dd>{String(a.receipt.receipt_id)}</dd></div><div><dt>Request</dt><dd>{String(a.receipt.request_id)}</dd></div><div><dt>Status</dt><dd>{String(a.receipt.status)}</dd></div><div><dt>Recorded</dt><dd>{String(a.receipt.recorded_at)}</dd></div></dl><small>A changed draft does not cancel this external reservation.</small></details>}
  </div>;}

  const asks=circle?.rides??[];
  return <section className="card execution-panel" aria-label="Office follow-through">
    <div className="panel-heading"><CalendarCheck size={23}/><h2>Before you leave.</h2><span className="pill amber">Local sandbox offices</span></div>
    <p className="muted">Each next step is checked with the office that handles it, then sent only after the clinician&apos;s part and your approval. These are fictional offices; nothing real is contacted.</p>
    {!view&&!pollError&&<p role="status">Loading saved office status.</p>}
    {view&&!view.configured&&<p className="soft-note">The sandbox offices are unavailable. No result or booking can be verified.</p>}

    {steps.length>0&&<ol className="walkout-list" aria-label="Before you leave checklist">
      {steps.map(({item,kind})=>{const a=latestFor(item.id);const errand=catalog.get(kind!);const done=a?.state==='confirmed';const problem=a&&['no_slot','rejected','expired','invalidated','unavailable','cancelled'].includes(a.state);
        return <li key={item.id} className={'walkout-row'+(done?' done':problem?' problem':'')}>
          {done?<CheckCircle2 size={20} aria-hidden/>:problem?<CircleAlert size={20} aria-hidden/>:a?<Clock size={20} aria-hidden/>:<Circle size={20} aria-hidden/>}
          <div><strong>{item.title}</strong><span className="muted"> · {errand?.place??kind}</span><p>{waitingOn(a,errand)}{done&&a?.slot?' · '+String(a.slot.label):''}</p>
            {(checks?.obstacles??[]).filter(o=>o.item_id===item.id&&o.state==='open').map(o=><p key={o.id} className="walkout-obstacle">Still open: {o.fact}</p>)}</div>
        </li>;})}
    </ol>}
    {patient&&ready.length>0&&<button className="primary-button walkout-approve" disabled={busy} onClick={()=>void change('/approve-ready',{digests:ready.map(a=>a.digest)})}>Approve the ready steps ({ready.length})</button>}

    {steps.map(({item,kind})=>{const errand=catalog.get(kind!);const actions=view?.actions.filter(a=>a.item_id===item.id)??[],latest=actions[0];const unresolved=actions.some(a=>['confirmed','queued','in_flight','unknown'].includes(a.state));
      const locations=errand?.locations??['Riverside Lab'];const defaultPlace=locations.includes(item.location??'')?item.location!:locations[0];
      const defaultDay=typeof latest?.slot?.day==='string'?latest.slot.day:String(errand?.days[0]?.day??'2026-10-20');
      return <article className="office-step" key={item.id} aria-label={'Office follow-through: '+item.title}>
      <h3>{item.title}</h3>
      {patient&&!unresolved&&<div className="office-date-place"><label>Requested location<select aria-label={'Requested location for '+item.title} value={places[item.id]??defaultPlace} onChange={e=>setPlaces({...places,[item.id]:e.target.value})}>{locations.map(place=><option key={place}>{place}</option>)}</select></label><label>Requested date<input aria-label={'Requested date for '+item.title} type="date" value={days[item.id]??defaultDay} onChange={e=>setDays({...days,[item.id]:e.target.value})}/></label><small>Fixed fictional calendar. Offered days: {(errand?.days??[]).map(d=>String(d.label)).join(', ')}.</small></div>}
      {patient&&!unresolved&&<div className="office-controls"><label>Appointment window<select aria-label={'Appointment window for '+item.title} value={windows[item.id]??(latest?.slot?.window==='afternoon'?'afternoon':'morning')} onChange={e=>setWindows({...windows,[item.id]:e.target.value as 'morning'|'afternoon'})}><option value="morning">Morning</option><option value="afternoon">Afternoon</option></select></label><div className="office-buttons">
        <button className="secondary-button" disabled={busy||!view?.configured||unresolved} onClick={()=>void change('/items/'+item.id+'/scope',{allowed:true})}>Allow office checks</button>
        <button className="primary-button" disabled={busy||!view?.configured||unresolved} onClick={()=>void change('/items/'+item.id+'/lookup',{window:windows[item.id]??'morning',location:places[item.id]??defaultPlace,day:days[item.id]??defaultDay})}>Check this window</button>
        <button className="text-link" disabled={busy||!view?.configured} onClick={()=>void change('/items/'+item.id+'/scope',{allowed:false})}>Withdraw office permission</button>
      </div></div>}
      {latest?info(latest):view&&<p className="muted">No office check has been requested. Sharing a step does not authorize dispatch.</p>}
      {patient&&latest?.state==='confirmed'&&family.map(member=>{const open=asks.find(r=>r.action_id===latest.id&&r.recipient_id===member.id&&['asked','accepted','declined'].includes(r.state));
        return open?null:<button key={member.id} className="secondary-button" disabled={busy} onClick={()=>void change('/rides',{action_id:latest.id,recipient_id:member.id},circleRoot)}>Ask {member.name.split(' ')[0]} to help with this</button>;})}
      {actions.length>1&&<details><summary>Earlier office checks ({actions.length-1})</summary>{actions.slice(1).map(a=><div key={a.id}>{info(a)}</div>)}</details>}
    </article>;})}
    {!steps.length&&<p className="muted">Lab, imaging, referral and prescription steps appear here once they are part of your plan.</p>}

    {(patient||familyViewer)&&asks.length>0&&<div className="care-circle" aria-label="Care circle">
      <h3><Users size={18} aria-hidden/> {patient?'Asked of your care circle':'Asked of you'}</h3>
      {asks.map(r=><div className="care-ask" key={r.id}>
        <p><strong>{r.purpose}</strong> · {r.when} · {r.where}</p>
        {patient&&<p className="muted">{r.recipient_name}: {({asked:'not answered yet',accepted:'said yes',declined:'said no',withdrawn:'you withdrew this ask',unavailable:'no longer shared or confirmed'})[r.state]}</p>}
        {patient&&['asked','accepted'].includes(r.state)&&<button className="text-link" disabled={busy} onClick={()=>void change('/rides/'+r.id+'/withdraw',{},circleRoot)}>Withdraw this ask</button>}
        {familyViewer&&<><p className="muted">{r.state==='asked'?'Can you help with this?':r.state==='accepted'?'You said yes.':'You said no.'} Your answer is your own commitment; it does not book anything.</p>
          <div className="office-buttons"><button className="primary-button" disabled={busy||r.state==='accepted'} onClick={()=>void change('/rides/'+r.id+'/answer',{answer:'yes'},circleRoot)}>Yes, I can help</button><button className="secondary-button" disabled={busy||r.state==='declined'} onClick={()=>void change('/rides/'+r.id+'/answer',{answer:'no'},circleRoot)}>I can&apos;t this time</button></div></>}
      </div>)}
    </div>}

    {patient&&demoTools&&view?.configured&&<details className="sandbox-controls"><summary>Development sandbox · change office conditions</summary><p>Changes persisted availability at one sandbox office. It does not change your permissions or the clinician&apos;s decision.</p>
      <label>Office<select aria-label="Sandbox office" value={scenarioKind} onChange={e=>setScenarioKind(e.target.value as Kind)}>{(view.errands??[]).map(e=><option key={e.kind} value={e.kind}>{e.place}</option>)}</select></label>
      <div className="example-choices">{scenarios.map(mode=><button key={mode} disabled={busy} onClick={()=>void change('/scenario',{mode,kind:scenarioKind})}>{scenarioLabels[mode]}</button>)}</div></details>}
    <p className="office-boundary"><ShieldCheck size={17}/> A suggested slot, your approval, a required order and an office receipt are separate facts.</p>
    {notice&&<p role="status">{notice}</p>}{(error||pollError)&&<p role="alert">{error||pollError}</p>}
  </section>;
}
