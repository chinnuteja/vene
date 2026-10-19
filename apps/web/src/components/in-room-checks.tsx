'use client';
import {useEffect,useState} from 'react';
import {CircleAlert,CircleCheck,SearchCheck,ShieldCheck} from 'lucide-react';
import {request,type Encounter,type Identity} from '@/lib/api/client';
import {useVisitUpdates} from '@/lib/visit-updates';
import type {components} from '../../../../packages/contracts/schema';
type View=components['schemas']['FeasibilityView'];
type Kind=components['schemas']['StandingRequest']['kinds'][number];
const KINDS:{id:Kind,label:string,detail:string}[]=[
  {id:'scheduling',label:'Scheduling',detail:'Whether the stated day or window has availability, and what a specialist needs first.'},
  {id:'coverage',label:'Coverage',detail:'Whether your plan requires prior authorization or covers a prescription. Only your plan member number is sent.'},
  {id:'pharmacy',label:'Pharmacy',detail:'Whether the chosen pharmacy has the prescription in stock.'},
];

// Patient: chooses what Vene may look up during the visit. Patient and clinician: see what
// those checks found and, if theirs to answer, respond. Family members see nothing here.
export function InRoomChecks({visit,viewer,mode}:{visit:Encounter;viewer:Identity;mode:'permission'|'checks'}){
  const updates=useVisitUpdates();
  const [view,setView]=useState<View|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [chosen,setChosen]=useState<Kind[]|null>(null);
  const root='/encounters/'+visit.id+'/feasibility';const patient=viewer.role==='patient';
  useEffect(()=>{if(updates)setView(updates.feasibility);},[updates]);
  async function post(path:string,body:unknown){setBusy(true);setError('');try{setView(await request<View>(root+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}));setChosen(null);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  if(viewer.role==='family')return null;
  const saved=view?.standing?.kinds??[];const selection=chosen??saved;
  const open=(view?.obstacles??[]).filter(o=>o.state==='open'),resolved=(view?.obstacles??[]).filter(o=>o.state==='resolved');
  const permission=patient&&<div className="standing-checks">
    <fieldset><legend>During my visit, Vene may check:</legend>
      {KINDS.map(k=><label key={k.id} className="standing-option"><input type="checkbox" checked={selection.includes(k.id)} disabled={busy}
        onChange={e=>setChosen(e.target.checked?[...selection,k.id]:selection.filter(x=>x!==k.id))}/><span><strong>{k.label}</strong><small>{k.detail}</small></span></label>)}
    </fieldset>
    <div className="office-buttons"><button className="primary-button" disabled={busy||!chosen} onClick={()=>void post('/standing',{kinds:selection})}>{selection.length?'Save what Vene may check':'Turn off visit checks'}</button>
      <span className="muted">{view?.standing?.active?'On: '+saved.join(', '):'Off'}{view&&view.checking>0?' · checking '+view.checking+'…':''}</span></div>
    <p className="soft-note">These are read-only lookups with fictional sandbox offices. Booking, submitting or messaging anyone still needs your separate approval.</p>
  </div>;
  if(mode==='permission')return <section className="card in-room-checks" aria-label="Visit checks permission">
    <div className="panel-heading"><SearchCheck size={22}/><h2>Catch problems while you&apos;re still in the room.</h2></div>
    <p className="muted">If something we discuss won&apos;t work in practice — no appointment that week, a prior authorization, a prescription your plan doesn&apos;t cover — Vene can tell you privately while the clinician can still help.</p>
    {permission}{error&&<p role="alert">{error}</p>}
  </section>;
  return <section className="card in-room-checks" aria-label="In-visit checks">
    <div className="panel-heading"><SearchCheck size={22}/><h2>{open.length?'Something to raise before you leave.':'Practical checks.'}</h2>{open.length>0&&<span className="pill amber">{open.length} open</span>}</div>
    {patient&&!view?.standing?.active&&<details className="standing-collapsed"><summary>Vene is not checking practical details during this visit</summary>{permission}</details>}
    {patient&&view?.standing?.active&&<p className="muted">Checking {saved.join(', ')} with sandbox offices{view.checking>0?' · '+view.checking+' in progress':''}. <button className="text-link" disabled={busy} onClick={()=>void post('/standing',{kinds:[]})}>Stop visit checks</button></p>}
    {!open.length&&!resolved.length&&<p className="muted">{patient?'Nothing to raise so far.':'Nothing has been shared with you.'}</p>}
    {open.map(o=><article key={o.id} className="obstacle" aria-label={'Obstacle: '+o.item_title}>
      <CircleAlert size={20} aria-hidden/>
      <div><strong>{o.item_title}</strong><p>{o.fact}</p>
        {(o.plan_alternatives??[]).length>0&&<p className="plan-facts">Plan-listed covered options in the same class: {(o.plan_alternatives??[]).join(', ')}. These are plan facts, not a recommendation.</p>}
        <p className="muted">{o.source} · checked {new Date(o.checked_at).toLocaleTimeString()}</p>
        {(o.choices??[]).length>0?<div className="office-buttons">{(o.choices??[]).map(c=><button key={c.id} className="secondary-button" disabled={busy} onClick={()=>void post('/obstacles/'+o.id+'/resolve',{choice:c.id})}>{c.label}</button>)}</div>
          :<p className="muted">{o.resolver==='clinician'?(patient?'Waiting for the clinician’s response. You can raise it privately or ask Vene to say it aloud from your cues.':''):'Waiting for the patient’s response.'}</p>}
      </div></article>)}
    {resolved.length>0&&<details><summary>Answered ({resolved.length})</summary>{resolved.map(o=><div key={o.id} className="obstacle answered"><CircleCheck size={18} aria-hidden/><p><strong>{o.item_title}</strong> · {o.fact} <em>{o.resolution?.by_name}: {o.resolution?.label}.</em></p></div>)}</details>}
    <p className="office-boundary"><ShieldCheck size={17}/> A check reports what a sandbox office said. The clinician decides what it means for care.</p>
    {error&&<p role="alert">{error}</p>}
  </section>;
}
