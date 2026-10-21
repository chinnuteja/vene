'use client';
import {useEffect,useState} from 'react';
import {History,ShieldCheck} from 'lucide-react';
import {request,type Encounter} from '@/lib/api/client';
import type {components} from '../../../../packages/contracts/schema';
type View=components['schemas']['MemoryView'];

// Patient only. Open loops from earlier visits, each with its stored source and age.
// Keeping an item adds a private draft question; the patient still approves the list.
// onReplace: the visit right after a change, so a quick next action never uses a stale version.
export function DraftedAgenda({visit,onReplace,disabled=false,onBusyChange}:{visit:Encounter;onReplace?:(v:Encounter)=>void;disabled?:boolean;onBusyChange?:(busy:boolean)=>void}){
  const [view,setView]=useState<View|null>(null),[dropped,setDropped]=useState<Set<string>>(new Set());
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  const root='/encounters/'+visit.id+'/memory';
  useEffect(()=>{const c=new AbortController();request<View>(root,{signal:c.signal}).then(setView).catch(e=>{if(!c.signal.aborted)setError((e as Error).message);});return()=>c.abort();},[root,visit.version]);
  async function post(path:string,body:unknown,message:string){if(busy||disabled)return;setBusy(true);onBusyChange?.(true);setError('');setNotice('');try{setView(await request<View>(root+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}));setDropped(new Set());setNotice(message);if(onReplace)onReplace(await request<Encounter>('/encounters/'+visit.id));}catch(e){setError((e as Error).message);}finally{setBusy(false);onBusyChange?.(false);}}
  if(!view)return error?<p role="alert">{error}</p>:null;
  const kept=view.loops.filter(l=>!dropped.has(l.key));
  const count=view.loops.length;
  return <section className="card drafted-agenda" aria-label="Drafted from your earlier visits">
    <div className="panel-heading"><History size={22}/><h2>{count?`Vene found ${count} thing${count===1?'':'s'} worth bringing up.`:'Nothing left open from earlier visits.'}</h2></div>
    <p className="muted">{count?'From your earlier visits and messages. Keep what matters today; each comes with where it came from.':view.past_visits?'Everything Vene knows about from earlier visits is resolved or already on your list.':'Vene has no earlier visits for you yet.'}{view.already_listed>0?` ${view.already_listed} earlier item${view.already_listed===1?' is':'s are'} already on your list.`:''}</p>
    {count>0&&<ul className="loop-list">{view.loops.map(l=><li key={l.key} className={'loop-item'+(dropped.has(l.key)?' dropped':'')}>
      <label className="loop-choice"><input type="checkbox" checked={!dropped.has(l.key)} disabled={busy||disabled} aria-label={'Keep: '+l.question}
        onChange={e=>{const next=new Set(dropped);if(e.target.checked)next.delete(l.key);else next.add(l.key);setDropped(next);}}/>
        <span><strong>{l.question}</strong><small>{l.detail}</small></span><span className="pill">{l.age}</span></label>
      <details className="loop-why"><summary>Why Vene suggested this</summary>{l.sources.map((s,i)=><blockquote key={i}><p>{s.text}</p><cite>{s.title} · {s.from_visit} · {new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',timeZone:'America/New_York'}).format(new Date(s.observed_at))}</cite></blockquote>)}</details>
      <button className="text-link" disabled={busy||disabled} onClick={()=>void post('/outcomes',{key:l.key,outcome:'done'},'Marked as done. Vene won’t suggest it again.')}>Already done</button>
    </li>)}</ul>}
    {count>0&&<div className="office-buttons"><button className="primary-button" disabled={busy||disabled||!kept.length} onClick={()=>void post('/carry',{keys:kept.map(l=>l.key)},'Added to your list as private drafts. Review who can see each, then approve your list.')}>{kept.length?`Add ${kept.length} to my visit list`:'Nothing selected'}</button></div>}
    <p className="office-boundary"><ShieldCheck size={17}/> Added questions stay private until you approve your list. Dr. Chen is the suggested audience; nothing goes to family unless you choose.</p>
    {notice&&<p role="status">{notice}</p>}{error&&<p role="alert">{error}</p>}
  </section>;
}
