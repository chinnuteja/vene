'use client';
import {useDemoTools} from '@/lib/demo-tools';
import {useEffect,useState} from 'react';
import {CalendarCheck,ShieldCheck} from 'lucide-react';
import {request,type Encounter,type Identity} from '@/lib/api/client';
import type {components} from '../../../../packages/contracts/schema';
type View=components['schemas']['ExecutionView'];
type Action=components['schemas']['ActionView'];
const labels:Record<string,string>={checking:'Checking office',suggested:'Slot suggested · not booked',no_slot:'No suitable slot',expired:'Availability expired',queued:'Approved · queued',in_flight:'Request in flight',unknown:'Completion unknown · reconciling',confirmed:'Reservation confirmed',rejected:'Office rejected request',invalidated:'Changed · check again',cancelled:'Not sent',unavailable:'Office unavailable'};

export function ExecutionPanel({visit,viewer}:{visit:Encounter;viewer:Identity}){
  const demoTools=useDemoTools();
  const [view,setView]=useState<View|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [pollError,setPollError]=useState('');
  const [windows,setWindows]=useState<Record<string,'morning'|'afternoon'>>({});
  const [places,setPlaces]=useState<Record<string,string>>({}),[days,setDays]=useState<Record<string,string>>({});
  const [notice,setNotice]=useState('');
  const root='/encounters/'+visit.id+'/execution';
  useEffect(()=>{
    let alive=true;let pending=false;
    async function poll(){if(pending)return;pending=true;try{const data=await request<View>(root);if(alive){setView(data);setPollError('');}}catch(e){if(alive){setView(null);setPollError((e as Error).message);}}finally{pending=false;}}
    void poll();const timer=setInterval(()=>void poll(),750);return()=>{alive=false;clearInterval(timer);};
  },[root,viewer.membership_id,visit.version]);
  async function change(path:string,body:Record<string,unknown>){setBusy(true);setError('');setNotice('');try{
    await request(root+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    setView(await request<View>(root));
    if(path.endsWith('/scope'))setNotice(body.allowed?'Office checks allowed. Booking still needs your separate approval.':'Office permission withdrawn. Already dispatched requests will still be reconciled; confirmed reservations are not cancelled.');
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  const patient=viewer.role==='patient',clinician=viewer.role==='clinician';
  const steps=visit.plan.filter(p=>/\b(lab|laboratory|blood)\b/i.test(p.title+' '+p.detail));
  function info(a:Action){return <div className="office-result">
    <span className={'pill '+(a.state==='confirmed'?'green':'amber')}>{labels[a.state]??a.state}</span>
    <p>{a.message}</p>{a.slot&&<strong>{String(a.slot.label)}</strong>}
    <p className="muted">{a.source}{a.checked_at?' · checked '+new Date(a.checked_at).toLocaleTimeString():''}</p>
    <div className="office-prerequisites"><span>Clinician: {a.clinician_confirmed?'confirmed':'awaiting confirmation'}</span><span>Order: {a.order_available?'sandbox order available':'required order missing'}</span><span>Your booking approval: {a.patient_authorized?'recorded':'not given'}</span></div>
    {clinician&&a.state==='suggested'&&a.fingerprint&&<div className="office-buttons">
      <button className="secondary-button" disabled={busy||a.clinician_confirmed} onClick={()=>void change('/actions/'+a.id+'/prerequisites',{expected_fingerprint:a.fingerprint,order:false})}>Confirm intended lab step</button>
      <button className="secondary-button" disabled={busy||a.order_available} onClick={()=>void change('/actions/'+a.id+'/prerequisites',{expected_fingerprint:a.fingerprint,order:true})}>Confirm and issue sandbox order</button>
    </div>}
    {patient&&a.state==='suggested'&&a.digest&&<button className="primary-button" disabled={busy} onClick={()=>void change('/actions/'+a.id+'/approve',{digest:a.digest})}>Approve this sandbox reservation</button>}
    {a.receipt&&<details className="office-receipt" open><summary>Sandbox office receipt</summary><dl><div><dt>Receipt</dt><dd>{String(a.receipt.receipt_id)}</dd></div><div><dt>Request</dt><dd>{String(a.receipt.request_id)}</dd></div><div><dt>Status</dt><dd>{String(a.receipt.status)}</dd></div><div><dt>Recorded</dt><dd>{String(a.receipt.recorded_at)}</dd></div></dl><small>A changed draft does not cancel this external reservation.</small></details>}
  </div>;}
  return <section className="card execution-panel" aria-label="Office follow-through">
    <div className="panel-heading"><CalendarCheck size={23}/><h2>Make the next step possible.</h2><span className="pill amber">Local sandbox office</span></div>
    <p className="muted">Check a practical obstacle together, then approve the exact next step. These are fictional lab windows; no real office is contacted.</p>
    {!view&&!pollError&&<p role="status">Loading saved office status.</p>}
    {view&&!view.configured&&<p className="soft-note">The sandbox office is unavailable. No result or booking can be verified.</p>}
    {steps.map(item=>{const actions=view?.actions.filter(a=>a.item_id===item.id)??[],latest=actions[0];const unresolved=actions.some(a=>['confirmed','queued','in_flight','unknown'].includes(a.state));return <article className="office-step" key={item.id} aria-label={'Office follow-through: '+item.title}>
      <h3>{item.title}</h3>
      {patient&&<div className="office-date-place"><label>Requested location<select aria-label={'Requested location for '+item.title} value={places[item.id]??(['Riverside Lab','Harbor Lab','Hilltop Lab'].includes(item.location??'')?item.location:'Riverside Lab')} onChange={e=>setPlaces({...places,[item.id]:e.target.value})}>{['Riverside Lab','Harbor Lab','Hilltop Lab'].map(place=><option key={place}>{place}</option>)}</select></label><label>Requested date<input aria-label={'Requested date for '+item.title} type="date" value={days[item.id]??(typeof latest?.slot?.day==='string'?latest.slot.day:'2026-10-20')} onChange={e=>setDays({...days,[item.id]:e.target.value})}/></label><small>Fixed fictional calendar. Available resources include Oct 20 Riverside, Oct 21 Harbor, and Oct 23 Hilltop.</small></div>}
      {patient&&<div className="office-controls"><label>Appointment window<select aria-label={'Appointment window for '+item.title} value={windows[item.id]??(latest?.slot?.window==='afternoon'?'afternoon':'morning')} onChange={e=>setWindows({...windows,[item.id]:e.target.value as 'morning'|'afternoon'})}><option value="morning">Morning</option><option value="afternoon">Afternoon</option></select></label><div className="office-buttons">
        <button className="secondary-button" disabled={busy||!view?.configured||unresolved} onClick={()=>void change('/items/'+item.id+'/scope',{allowed:true})}>Allow office checks</button>
        <button className="primary-button" disabled={busy||!view?.configured||unresolved} onClick={()=>void change('/items/'+item.id+'/lookup',{window:windows[item.id]??'morning',location:places[item.id]??(['Riverside Lab','Harbor Lab','Hilltop Lab'].includes(item.location??'')?item.location:'Riverside Lab'),day:days[item.id]??(typeof latest?.slot?.day==='string'?latest.slot.day:'2026-10-20')})}>Check this window</button>
        <button className="text-link" disabled={busy||!view?.configured} onClick={()=>void change('/items/'+item.id+'/scope',{allowed:false})}>Withdraw office permission</button>
      </div></div>}

      {latest?info(latest):view&&<p className="muted">No office check has been requested. Sharing a step does not authorize dispatch.</p>}
      {actions.length>1&&<details><summary>Earlier office checks ({actions.length-1})</summary>{actions.slice(1).map(a=><div key={a.id}>{info(a)}</div>)}</details>}
    </article>;})}
    {!steps.length&&<p className="muted">A sourced laboratory next step will appear here when it is part of your plan.</p>}
    {patient&&demoTools&&view?.configured&&<details className="sandbox-controls"><summary>Development sandbox · change office conditions</summary><p>Changes persisted office availability. It does not change your permissions or clinician&apos;s decision.</p><div className="example-choices">{(['normal','no_slot','expired','delayed','rejected','timeout_after_write','duplicate_callback'] as const).map(mode=><button key={mode} disabled={busy} onClick={()=>void change('/scenario',{mode})}>{({normal:'Slots available',no_slot:'No slots',expired:'Expired availability',delayed:'Delayed lookup',rejected:'Office rejects',timeout_after_write:'Timeout after write',duplicate_callback:'Duplicate response'})[mode]}</button>)}</div></details>}
    <p className="office-boundary"><ShieldCheck size={17}/> A suggested slot, your approval, a required order and an office receipt are separate facts.</p>
    {notice&&<p role="status">{notice}</p>}{(error||pollError)&&<p role="alert">{error||pollError}</p>}
  </section>;
}
