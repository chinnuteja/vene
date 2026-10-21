'use client';
import {useState} from 'react';
import {CheckCircle2,Circle,CircleAlert,Clock,LockKeyhole,ShieldCheck,Sparkles} from 'lucide-react';
import {useDemoVisit} from '@/lib/demo-visit';
import {VisitUpdates} from '@/lib/visit-updates';
import type {Encounter} from '@/lib/api/client';
import type {components} from '../../../../packages/contracts/schema';
import {DemoLaterLine} from './demo-later-line';
type Action=components['schemas']['ActionView'];
type Errand=components['schemas']['ErrandOption'];
type Bundle=components['schemas']['BundleResult'];
type Obstacle=components['schemas']['ObstacleView'];
type Step=Encounter['plan'][number];

export const ERRAND_KINDS=['lab','imaging','prescription','referral','authorization'];
const PROBLEM=['no_slot','rejected','expired','invalidated','unavailable','cancelled'];
const NAMES:Record<string,string>={lab:'Lab',imaging:'Imaging',prescription:'Pharmacy',referral:'Specialist',authorization:'Health plan'};

// One plain sentence per step. Approval, the clinician's part and the office's receipt stay separate facts.
export function stepStatus(a:Action|undefined,errand?:Errand,patient=true){
  if(!a)return 'Not checked yet';
  if(a.state==='confirmed'&&!a.receipt_current)return 'Earlier arrangement confirmed · plan changed. Review with the office.';
  if(a.state==='confirmed')return a.kind==='authorization'?'Approved by the health plan':'Confirmed · receipt from the '+(errand?.place??'office');
  if(a.state==='checking')return 'Checking with the '+(errand?.place??'office')+'…';
  if(a.state==='queued'||a.state==='in_flight')return 'Sent · waiting for the '+(errand?.place??'office')+'’s receipt';
  if(a.state==='unknown')return 'Confirming with the office before any retry';
  if(a.state!=='suggested')return a.message;
  const missing=[];
  if(!a.clinician_confirmed||!a.order_available)missing.push(patient?'Dr. Chen’s '+(a.document||'order'):'your '+(a.document||'order'));
  if(/prior authorization/.test(a.message))missing.push('the health plan’s approval');
  if(missing.length)return 'Waiting for '+missing.join(' and ');
  return a.patient_authorized?'Approved · sending':patient?'Ready for your approval':'Ready for Maria’s approval';
}

export function useErrands(visit:Encounter|null,services:ReturnType<typeof useDemoVisit>['services']){
  const steps=(visit?.plan??[]).filter(p=>ERRAND_KINDS.includes(p.kind??''));
  const catalog=new Map((services?.execution.errands??[]).map(e=>[e.kind as string,e]));
  const latest=(id:string)=>services?.execution.actions.find(a=>a.item_id===id);
  return {steps,catalog,latest};
}

export function Checklist({steps,catalog,latest,patient}:{steps:Step[];catalog:Map<string,Errand>;latest:(id:string)=>Action|undefined;patient:boolean}){
  return <ol className="demo-checklist" aria-label="Before you leave checklist">{steps.map(item=>{
    const a=latest(item.id),errand=catalog.get(item.kind??''),done=a?.state==='confirmed'&&a.receipt_current,problem=a&&(PROBLEM.includes(a.state)||(a.state==='confirmed'&&!a.receipt_current));
    return <li key={item.id} className={done?'done':problem?'problem':a?'moving':''}>
      <span className="demo-check-icon">{done?<CheckCircle2 size={20}/>:problem?<CircleAlert size={20}/>:a?<Clock size={20}/>:<Circle size={20}/>}</span>
      <div><small>{NAMES[item.kind??'']??'Next step'}{(a?.slot?.location??item.location)?' · '+String(a?.slot?.location??item.location).replace('Fictional ',''):''}</small><strong>{item.title}</strong>
        <p>{stepStatus(a,errand,patient)}</p>
        {done&&a?.slot&&<p className="demo-check-slot">{String(a.slot.label).replace(' · Fictional ',' · ')}</p>}
        {done&&a?.receipt&&<p className="demo-receipt-line">Receipt {String(a.receipt.receipt_id).slice(0,8)}</p>}</div></li>;})}</ol>;
}

// Which offered day matches what was said ("on Wednesday"), else the first offered day.
function dayFor(item:Step,errand?:Errand){
  const days=errand?.days??[];const spoken=(item.timeframe??'').slice(0,3).toLowerCase();
  return String((days.find(d=>String(d.label).toLowerCase().startsWith(spoken))??days[0])?.day??'');
}

export function DemoLeave({run}:{run:string}){
  const {visit,viewer,services,error,setError,post,share}=useDemoVisit();
  const [busy,setBusy]=useState(false),[notice,setNotice]=useState('');
  const {steps,catalog,latest}=useErrands(visit,services);
  if(!visit||!viewer)return <div className="demo-pane-loading" role="status">{error||'Opening your visit…'}</div>;
  const patient=viewer.role==='patient',doctor=viewer.role==='clinician';
  async function act(fn:()=>Promise<void>){setBusy(true);setError('');setNotice('');try{await fn();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  const obstacles=(services?.feasibility.obstacles??[]).filter(o=>o.state==='open'&&o.resolver==='clinician'&&steps.some(s=>s.id===o.item_id)) as Obstacle[];
  const unchecked=steps.filter(s=>s.kind!=='authorization'&&(!latest(s.id)||PROBLEM.includes(latest(s.id)!.state)));
  const ready=steps.map(s=>latest(s.id)).filter((a):a is Action=>!!a&&a.state==='suggested'&&!!a.digest&&a.clinician_confirmed&&a.order_available&&!a.patient_authorized);
  const yours=steps.map(s=>latest(s.id)).filter((a):a is Action=>!!a&&a.state==='suggested'&&!!a.fingerprint&&!(a.clinician_confirmed&&a.order_available));
  const allDone=steps.length>1&&steps.every(s=>latest(s.id)?.receipt_current);
  const later=steps.some(s=>s.kind!=='lab');
  async function checkAll(){
    await share(unchecked.map(s=>s.id),'clinician');
    for(const item of unchecked){
      const errand=catalog.get(item.kind??'');const locations=errand?.locations??[];
      await post('/execution/items/'+item.id+'/scope',{allowed:true});
      await post('/execution/items/'+item.id+'/lookup',{window:'morning',location:locations.includes(item.location??'')?item.location:locations[0],day:dayFor(item,errand)});
    }
  }
  async function approve(){
    const result=await post<Bundle>('/execution/approve-ready',{digests:ready.map(a=>a.digest)});
    const held=result.outcomes.filter(o=>o.outcome!=='queued'&&o.outcome!=='already_approved');
    const sent=result.outcomes.length-held.length;
    setNotice(sent+' sent. Each office confirms on its own.'+(held.length?' '+held.map(o=>o.message).join(' '):''));
  }
  return <VisitUpdates.Provider value={services}><main className={'demo-experience demo-chapter '+viewer.role}>
    {doctor&&<DemoLaterLine run={run}/>}
    <div className="demo-chapter-head"><span className="eyebrow small">BEFORE YOU LEAVE</span>
      <h1>{patient?'Everything Dr. Chen asked for.':doctor?'Your part, while Maria is here.':'What Maria shared.'}</h1>
      <p>{patient?'Vene sets each step up with its office. Nothing is booked or sent without you.':doctor?'Orders and responses you give now save a call later. Nothing private reaches this window.':'Only steps Maria shares with you appear here.'}</p></div>

    {patient&&!later&&<section className="demo-waiting compact"><div className="demo-listening-wave">{[12,23,36,18,29,43,26,16,32,20,11].map((h,i)=><i key={i} style={{height:h}}/>)}</div><p>{visit.understanding?.enabled?'Listening for what Dr. Chen asks next…':'Allow private checks in “During” to begin.'}</p></section>}

    {obstacles.map(o=>patient?<section key={o.id} className="demo-alternative coverage-cue" aria-label="Private coverage cue"><span><Sparkles size={14}/>JUST FOR YOU</span><h2>Your plan needs to approve this first.</h2><p>{o.fact}</p>
        {(visit.plan.find(p=>p.id===o.item_id)?.audiences??[]).includes('clinician')?<p className="demo-shared">Shared with Dr. Chen. Only the clinician can answer this.</p>
          :<><p className="demo-share-review">Without it the imaging can be refused, and you would find out at the front desk. Share this step with Dr. Chen so the office can act now.</p>
          <button className="primary-button" disabled={busy} onClick={()=>void act(()=>share([o.item_id],'clinician'))}>Ask Dr. Chen now</button></>}
        <small className="demo-source-note">{o.source}. The plan decides; Vene only reports what it said.</small></section>
      :doctor?<section key={o.id} className="demo-clinician-action" aria-label="Coverage question"><span className="eyebrow small">MARIA ASKS · {o.item_title.toUpperCase()}</span><h2>Prior authorization needed.</h2><p>{o.fact}</p>
        <div className="office-buttons">{(o.choices??[]).map(c=><button key={c.id} className={c.id==='office_will_submit'?'primary-button':'secondary-button'} disabled={busy} onClick={()=>void act(async()=>{await post('/feasibility/obstacles/'+o.id+'/resolve',{choice:c.id});})}>{c.label}</button>)}</div>
        <small>Your answer is recorded as yours. Submitting still needs Maria’s approval.</small></section>:null)}

    {doctor&&yours.length>0&&<section className="demo-clinician-action" aria-label="Your part"><span className="eyebrow small">YOUR CLINICAL DECISIONS</span><h2>{yours.length===1?'One thing needs you.':yours.length+' things need you.'}</h2>
      <ul className="demo-yours">{yours.map(a=><li key={a.id}><div><strong>{a.title}</strong><small>{a.place}{a.slot?' · '+String(a.slot.label):''}</small></div>
        <button className="primary-button" disabled={busy} onClick={()=>void act(async()=>{await post('/execution/actions/'+a.id+'/prerequisites',{expected_fingerprint:a.fingerprint,order:true});})}>Confirm & send {a.document||'order'}</button></li>)}</ul>
      <small>This records your decision. Vene cannot issue an order or a prescription.</small></section>}

    {steps.length>0?<Checklist steps={steps} catalog={catalog} latest={latest} patient={!doctor}/>
      :!patient&&<section className="demo-guest-empty"><LockKeyhole size={24}/><h2>{doctor?'Only what Maria shares.':'Maria chooses what comes here.'}</h2><p>Steps appear here when Maria shares them.</p></section>}

    {patient&&later&&<div className="demo-leave-action">
      {unchecked.length>0?<button className="primary-button" disabled={busy} onClick={()=>void act(checkAll)}>{busy?'Checking with the offices…':'Check '+(unchecked.length===1?'it':'all '+unchecked.length)+' with the offices'}</button>
        :ready.length>0?<button className="primary-button" disabled={busy} onClick={()=>void act(approve)}>Approve {ready.length===1?'the ready step':'all '+ready.length+' ready steps'}</button>
        :allDone?<p className="demo-all-set"><CheckCircle2 size={18}/>All set before you leave.</p>
        :<p className="demo-progress" role="status">{yours.length||steps.some(s=>/Dr. Chen/.test(stepStatus(latest(s.id),catalog.get(s.kind??''))))?'Waiting for Dr. Chen’s part…':'Offices are answering…'}</p>}
      <small>Checking shares the step and its source with Dr. Chen. Booking needs your approval.</small></div>}
    {notice&&<p className="demo-progress" role="status">{notice}</p>}
    <p className="demo-boundary"><ShieldCheck size={13}/>Fictional offices and health plan. Nothing real is contacted.</p>
    {error&&<p className="demo-error" role="alert">{error}</p>}
  </main></VisitUpdates.Provider>;
}
