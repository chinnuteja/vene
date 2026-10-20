'use client';
import {useDemoTools} from '@/lib/demo-tools';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {ArrowRight,CircleHelp,FileText,MessageCircle,Sparkles} from 'lucide-react';
import type {components} from '../../../../packages/contracts/schema';
import {request,type Encounter,type Evidence} from '@/lib/api/client';
import {AudienceChoices} from './preparation-controls';
type Status=components['schemas']['UnderstandingStatus'];
type Plan=Encounter['plan'][number];
type SourceOpener=(item:Evidence,trigger:HTMLElement)=>void;
const examples=[
  ['A clear next step','Maria will arrange the lab visit at Riverside Lab on Thursday after the office sends the order.'],
  ['A corrected date','Actually, the lab visit is Tuesday, not Thursday. Maria will arrange it at Riverside Lab after the office sends the order.'],
  ['An unclear owner',"They'll do it for the lab visit on Tuesday."],
  ['A deferred question',"Let's defer the referral until our next visit."],
] as const;

async function mutate(visit:Encounter,suffix:string,fields:Record<string,unknown>){
  return request<Encounter>('/encounters/'+visit.id+'/understanding'+suffix,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command_id:crypto.randomUUID(),...fields})});
}

export function UnderstandingPanel({visit,onReplace}:{visit:Encounter;onReplace:(view:Encounter)=>void}){
  const demoTools=useDemoTools();
  const [initial,setInitial]=useState<Status|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [text,setText]=useState<string>(examples[0][1].replaceAll('Maria',visit.patient.preferred_name)),[speaker,setSpeaker]=useState('clinician');
  useEffect(()=>{const controller=new AbortController();request<Status>('/encounters/'+visit.id+'/understanding',{signal:controller.signal}).then(setInitial).catch(()=>{});return()=>controller.abort();},[visit.id]);
  const status=visit.understanding??initial;
  async function change(suffix:string,fields:Record<string,unknown>){setBusy(true);setError('');try{onReplace(await mutate(visit,suffix,fields));}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  return <section className="understanding-panel card" aria-label="Visit understanding">
    <div className="understanding-heading"><div><div className="eyebrow small">THE CONVERSATION, KEPT CLEAR</div><h2>One thought becomes a next step.</h2><p className="muted">Vene proposes what it understood. You can inspect the words behind it and correct what was meant.</p></div><span className="pill" role="status">{status?.state==='processing'?'Updating understanding…':status?.state==='queued'?'Waiting to understand…':status?.state==='ready'?'Understanding saved':status?.state==='paused'?'Processing paused':status?.state==='unavailable'?'Understanding unavailable':'Your choice to begin'}</span></div>
    <div className="understanding-controls"><button className="primary-button" disabled={busy||!status||status.provider==='unavailable'} onClick={()=>void change('/processing',{enabled:!status?.enabled})}>{status?.enabled?'Pause visit understanding':'Enable visit understanding'}</button>{status?.state==='unavailable'&&<button className="secondary-button" disabled={busy} onClick={()=>void change('/retry',{})}>Retry understanding</button>}<small>Private to you until you choose to share. Proposed steps do not approve or complete an action.</small></div>
    {status?.message&&<p role="status">{status.message}</p>}
    {demoTools&&status?.fixture_input_enabled&&<details className="fictional-input"><summary>Fictional conversation input</summary><p className="muted">{status.provider==="fixture"?"Local scenario interpreter · no live model or speech recognition.":"Live model extraction from fictional text · speech recognition is separate."} These original turns exercise the same source validation, corrections and visit updates.</p><div className="example-choices">{examples.map(([label,value])=><button key={label} onClick={()=>setText(value.replaceAll('Maria',visit.patient.preferred_name))}>{label}</button>)}</div><form onSubmit={e=>{e.preventDefault();void change('/fixture-turns',{speaker,text});}}><label>Fictional speaker<select value={speaker} onChange={e=>setSpeaker(e.target.value)}><option value="clinician">Dr. Chen</option><option value="patient">{visit.patient.preferred_name}</option><option value="family">Family participant</option></select></label><label>Finalized fictional turn<textarea aria-label="Finalized fictional turn" value={text} onChange={e=>setText(e.target.value)} minLength={3} maxLength={2000} rows={3} required/></label><button className="secondary-button" disabled={busy}>Add fictional turn</button></form></details>}
    {error&&<p role="alert" aria-label="Understanding error">{error}</p>}
  </section>;
}

export function ConversationSourceCorrection({visit,source,onReplace}:{visit:Encounter;source:Evidence;onReplace:(view:Encounter)=>void}){
  const [text,setText]=useState(source.text),[busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>setText(source.text),[source.id,source.version,source.text]);
  if(source.source_type!=='conversation'||visit.viewer_role!=='patient')return null;
  return <details className="source-correction"><summary>Correct these words</summary><p className="muted">A correction clears dependent interpretations and makes this source private again. It cannot reverse an external action.</p><form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{onReplace(await mutate(visit,'/sources/'+source.id+'/correct',{expected_source_version:source.version??1,text}));}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}><label>Corrected conversation source<textarea aria-label="Corrected conversation source" rows={4} maxLength={2000} minLength={3} value={text} onChange={e=>setText(e.target.value)} required/></label><button className="primary-button" disabled={busy}>Save source correction</button></form>{error&&<p role="alert">{error}</p>}</details>;
}

function Sources({item,visit,onSource}:{item:Plan;visit:Encounter;onSource:SourceOpener}){
  return <div className="step-sources">{item.evidence_refs.map(id=>{const source=visit.evidence.find(e=>e.id===id);return source?<button key={id} className="source-link" onClick={e=>onSource(source,e.currentTarget)}><FileText size={14}/>{source.source_type==='office_message'?'Read the office message':source.source_type==='conversation'?`Read conversation source · v${source.version??1}`:'Read your correction'}</button>:null;})}</div>;
}

function CorrectStep({item,visit,onReplace}:{item:Plan;visit:Encounter;onReplace:(view:Encounter)=>void}){
  const [owner,setOwner]=useState(item.owner??''),[time,setTime]=useState(item.timeframe??''),[location,setLocation]=useState(item.location??''),[detail,setDetail]=useState(item.detail);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>{setOwner(item.owner??'');setTime(item.timeframe??'');setLocation(item.location??'');setDetail(item.detail);},[item.revision,item.owner,item.timeframe,item.location,item.detail]);
  return <details className="step-correction"><summary>Correct this next step</summary><form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{onReplace(await mutate(visit,'/plan/'+item.id+'/correct',{expected_item_revision:item.revision??1,owner:owner||null,timeframe:time||null,location:location||null,detail}));}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}><label>Who will do it<input value={owner} maxLength={100} onChange={e=>setOwner(e.target.value)} placeholder="Leave empty if unclear"/></label><label>When<input value={time} maxLength={200} onChange={e=>setTime(e.target.value)}/></label><label>Where<input value={location} maxLength={200} onChange={e=>setLocation(e.target.value)}/></label><label>What you mean<textarea aria-label="What you mean" value={detail} maxLength={1200} minLength={3} onChange={e=>setDetail(e.target.value)} required/></label><p className="muted">This saves your correction privately. It does not approve an action.</p><button className="secondary-button" disabled={busy}>Save step correction</button></form>{error&&<p role="alert">{error}</p>}</details>;
}

export function EvolvingVisitCard({visit,patient,onSource,onReplace,sharing,disabled}:{visit:Encounter;patient:boolean;onSource:SourceOpener;onReplace:(view:Encounter)=>void;sharing:Parameters<typeof AudienceChoices>[0]['mutate'];disabled:boolean}){
  const priorities=visit.priorities.filter(p=>p.selected),steps=visit.plan.filter(p=>p.origin&&p.origin!=='preparation'),context=visit.plan.filter(p=>!p.origin||p.origin==='preparation');
  const labels={open:'Still open',partly_answered:'Partly answered',answered:'Answer identified · review',deferred:'Deferred'};
  return <div className="visit-grid evolving-visit">
    <section className="card"><div className="area-icon green"><CircleHelp size={21}/></div><h2>{patient?'What I wanted to discuss':"Patient’s questions"}</h2><p className="muted">{patient?'The questions you chose to bring.':'Approved questions shared with you.'}</p><div className="simple-list">{priorities.length?priorities.map(p=><div key={p.id}><span className="status-dot"/><strong>{p.title}</strong><span className="item-status">{labels[p.status??'open']}</span>{p.answer_detail&&<p className="answer-explanation">{p.answer_detail}</p>}{p.answer_refs?.map(id=>{const source=visit.evidence.find(e=>e.id===id);return source?<button key={id} className="source-link" onClick={e=>onSource(source,e.currentTarget)}>Why this answer?</button>:null;})}</div>):<p>No questions {patient?'selected.':'shared with you.'}</p>}</div>{patient&&<Link className="text-link" href="/prepare">Edit my questions <ArrowRight size={15}/></Link>}</section>
    <section className="card"><div className="area-icon peach"><MessageCircle size={21}/></div><h2>What we understood</h2><p className="muted">Sources and interpretations stay distinct.</p>{context.map(item=><div className="plan-block" key={item.id}><span className="pill amber">Needs clarification</span><h3>{item.title}</h3><p>{item.detail}</p><Sources item={item} visit={visit} onSource={onSource}/></div>)}{steps.map(item=><div className="plan-block interpretation" key={item.id}><span className={'pill '+(item.needs_clarification?'amber':'')}>{item.origin==='human'?'Your correction':item.needs_clarification?'Needs clarification':'Proposed understanding'}</span><h3>{item.title}</h3><p>{item.explanation||item.detail}</p><Sources item={item} visit={visit} onSource={onSource}/></div>)}{!context.length&&!steps.length&&<p className="muted">No understanding has been shared yet.</p>}</section>
    <section className="card"><div className="area-icon lavender"><ArrowRight size={21}/></div><h2>What happens next</h2><p className="muted">Keep the owner and next step clear.</p>{steps.length?steps.map(item=><article className="next-step" key={item.id} aria-label={item.title}><span className="pill">Draft · not approved</span><h3>{item.title}</h3><dl><div><dt>Who</dt><dd>{item.owner||'Who will do this is unclear'}</dd></div><div><dt>When</dt><dd>{item.timeframe||'Timing needs clarification'}</dd></div><div><dt>Where</dt><dd>{item.location||'Location not specified'}</dd></div></dl>{!!item.dependencies?.length&&<p className="step-dependency">Waiting on: {item.dependencies.join('; ')}</p>}<p className="step-boundary">Order: {item.order_available?'available':'unconfirmed'} · External completion: {item.external_completed?'reported complete':'unconfirmed'}</p>{patient&&<><CorrectStep item={item} visit={visit} onReplace={onReplace}/><AudienceChoices item={item} label={'step: '+item.title} mutate={sharing} disabled={disabled}/><small>Supporting sources must also be shared for this step to appear in an invited view.</small></>}</article>):<div className="empty-state"><div className="empty-lines" aria-hidden="true"><i/><i/><i/></div><h3>Let&apos;s clarify it together.</h3><p>No new action has been approved or completed.</p></div>}</section>
    <div className="call-note"><Sparkles size={18}/><span>Interpretations can change. Clinical decisions, your approval, required orders and actual completion stay separate.</span></div>
  </div>;
}
