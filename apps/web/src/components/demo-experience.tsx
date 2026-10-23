'use client';
import {useContext,useEffect,useState} from 'react';
import dynamic from 'next/dynamic';
import {ArrowRight,CalendarCheck,Check,LockKeyhole,Mic,ShieldCheck,Sparkles,Volume2} from 'lucide-react';
import {request,sendCommand,type Encounter} from '@/lib/api/client';
import {DemoVisit} from '@/lib/demo-visit';
import {VisitUpdates} from '@/lib/visit-updates';
import type {components} from '../../../../packages/contracts/schema';
const CallPanel=dynamic(()=>import('./call-panel').then(m=>m.CallPanel),{ssr:false});
type Speech=components['schemas']['SpeechView'];
const SCRIPT='Please get labs done within three days. We can send the lab order today.';
const delay=(ms:number)=>new Promise(r=>setTimeout(r,ms));

export function DemoExperience(){
  const pane=useContext(DemoVisit);if(!pane)throw new Error('DemoExperience needs a DemoVisitProvider.');
  const {visit,viewer,services,setVisit,checksAllowed}=pane;
  const [speech,setSpeech]=useState<Speech|null>(null);
  const [config,setConfig]=useState<Record<string,string>|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [shared,setShared]=useState(false),[preview,setPreview]=useState(false);
  const [sampleSent,setSampleSent]=useState(false);
  useEffect(()=>{const controller=new AbortController();
    fetch('/api/dev/demo-info',{cache:'no-store',signal:controller.signal}).then(async r=>{if(!r.ok)throw new Error('Demo configuration is unavailable.');setConfig(await r.json());}).catch(e=>{if(!controller.signal.aborted)setError(e.message);});return()=>controller.abort();},[]);
  useEffect(()=>{
    if(!visit?.id||config?.transport==='guided')return;
    let stopped=false;const controller=new AbortController();
    async function poll(){while(!stopped){try{setSpeech(await request<Speech>('/encounters/'+visit!.id+'/speech',{signal:controller.signal}));}catch{}await delay(450);}}
    void poll();return()=>{stopped=true;controller.abort();};
  },[visit?.id,config?.transport]);
  const root='/encounters/'+visit?.id;
  const patient=viewer?.role==='patient',doctor=viewer?.role==='clinician',guided=config?.transport==='guided',fixture=config?.stt==='fixture';
  const item=visit?.plan.find(p=>p.kind==='lab'),obstacle=services?.feasibility.obstacles.find(o=>o.item_id===item?.id&&o.alternative);
  const action=services?.execution.actions.find(a=>a.item_id===item?.id),confirmed=!!action?.receipt_current;
  const settled=visit?.understanding?.state==='ready'&&visit.understanding.revision===visit.understanding.processed_revision&&(fixture||!!speech&&speech.floor!=='paused'&&speech.quiet_for_seconds>=1);
  useEffect(()=>{if(action?.state==='invalidated')setShared(false);},[action?.state]);
  useEffect(()=>{if(patient&&obstacle&&!busy&&!shared&&!confirmed){const element=document.getElementById('private-alternative');if(element)window.scrollTo({top:element.offsetTop-20,behavior:'smooth'});}},[patient,obstacle?.id]);
  useEffect(()=>{if(!visit||!viewer)return;const send=(milestone:string)=>parent.postMessage({type:'vene-demo-milestone',run:visit.id,role:viewer.role,milestone},location.origin);
    if(item)send('heard');if(obstacle)send('obstacle');if(confirmed)send('booked');
  },[visit?.id,viewer?.role,item?.id,obstacle?.id,confirmed]);
  async function post<T=unknown>(path:string,body:unknown){return request<T>(root+path,{method:'POST',body:JSON.stringify(body)});}
  async function act(fn:()=>Promise<void>){setBusy(true);setError('');try{await fn();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  async function allow(){setVisit(await post<Encounter>('/understanding/processing',{command_id:crypto.randomUUID(),enabled:true}));await post('/feasibility/standing',{kinds:['scheduling','coverage']});}
  async function raise(){
    if(!item||!obstacle)return;
    const refs=[item.id,...item.evidence_refs,...(obstacle.supporting_sources??[])];
    const current=await request<Encounter>(root),changes=[];
    for(const id of [...new Set(refs)]){
      const target=[...current.plan,...current.evidence].find(e=>e.id===id);
      if(!target)throw new Error('The source changed. Review the new instruction first.');
      if(!(target.audiences??[]).includes('clinician'))changes.push({item_id:id,audiences:[...(target.audiences??[]),'clinician' as const]});
    }
    if(changes.length)setVisit(await sendCommand(current,{type:'sharing.batch_changed',changes}));
    await post('/execution/items/'+item.id+'/scope',{allowed:true});
    await post('/execution/items/'+item.id+'/lookup',{window:'morning',location:obstacle.alternative!.location,day:obstacle.alternative!.day});
    setShared(true);
    if(guided){
      // Device preview only: never creates a played/heard/LiveKit delivery receipt.
      if('speechSynthesis' in window){const audio=new SpeechSynthesisUtterance(obstacle.fact+' Would Thursday morning work?');audio.rate=.95;speechSynthesis.cancel();speechSynthesis.speak(audio);setPreview(true);}
      return;
    }
    // Sharing changed the fingerprint. Approve only the newly checked, identical public fact.
    for(let i=0;i<50;i++){
      await post('/speech/actions',{command_id:crypto.randomUUID(),type:'refresh'});
      const current=await request<Speech>(root+'/speech'),cue=current.cues.find(c=>c.public_text.includes(obstacle.fact)&&c.eligible_to_speak);
      if(cue){await post('/speech/approve',{command_id:crypto.randomUUID(),cue_id:cue.id,digest:cue.digest});return;}
      await delay(300);
    }
    throw new Error('The alternative was shared and checked. Spoken permission or a fresh cue is still needed; no speech was approved.');
  }
  if(!visit||!viewer)return <div className="demo-pane-loading" role="status">{error||pane.error||'Opening your visit…'}</div>;
  return <VisitUpdates.Provider value={services}><main className={'demo-experience '+viewer.role}>
    <div className="demo-person-header"><div className="demo-person-avatar">{patient?'M':doctor?'C':'E'}</div><div><span>{patient?'YOUR PRIVATE SPACE':doctor?'CLINICIAN VIEW':'FAMILY VIEW'}</span><h1>{patient?'Here with you, Maria.':doctor?'With Maria, today.':'Here for Maria.'}</h1></div></div>
    {guided?<section className="demo-call"><span className="demo-live-dot"/><strong>Sample visit · no microphone</strong><p>Dr. Chen’s words are typed for this preview. They go through the same understanding, private checks and booking services as live speech.</p>
      {patient&&<button className="primary-button" disabled={busy} onClick={()=>void act(async()=>{if(visit.understanding?.enabled){await post('/understanding/processing',{command_id:crypto.randomUUID(),enabled:false});await post('/feasibility/standing',{kinds:[]});}else await allow();})}>{visit.understanding?.enabled?'Pause understanding':'Allow private checks'}</button>}</section>:viewer.role!=='family'?<CallPanel visit={visit} viewer={viewer} compact/>:null}
    {patient&&<p className="demo-private-note"><LockKeyhole size={12}/>Your sources and suggestions stay private until you share.</p>}
    {doctor&&fixture&&<section className="demo-sample"><span className="eyebrow small">DR. CHEN SAYS · SAMPLE WORDS</span><blockquote>“{SCRIPT}”</blockquote><button className="primary-button" disabled={busy||!checksAllowed||sampleSent} onClick={()=>void act(async()=>{await post('/demo/turn',{token:crypto.randomUUID()});setSampleSent(true);})}>{sampleSent?'Heard':checksAllowed?'Say this':'Waiting for Maria’s permission'} <ArrowRight size={15}/></button><small>Typed, not spoken: this preview does not test speech recognition.</small></section>}
    {doctor&&!fixture&&<section className="demo-sample"><span className="eyebrow small"><Mic size={12}/>SAY THIS INTO THE AGREED MICROPHONE</span><blockquote>“{SCRIPT}”</blockquote><small>Real Deepgram → {config?.model} → Cartesia. No scripted fallback.</small></section>}
    {patient&&!item&&<section className="demo-waiting"><div className="demo-listening-wave">{[12,23,36,18,29,43,26,16,32,20,11].map((h,i)=><i key={i} style={{height:h}}/>)}</div><h2>A little less to carry.</h2><p>{visit.understanding?.enabled?'Ready for Dr. Chen’s next step.':'Agree to private understanding to begin.'}</p></section>}
    {item&&<section className="demo-step"><span className="eyebrow small">{patient?'FROM YOUR CONVERSATION':'SHARED NEXT STEP'}</span><h2>Labs, {item.timeframe||'timing to clarify'}.</h2><p>{item.timeframe} · proposed by the clinician</p><small>Source: {visit.evidence.find(e=>item.evidence_refs.includes(e.id))?.speaker||'visit instruction'}</small></section>}
    {patient&&item&&!obstacle&&!confirmed&&<p className="demo-progress" role="status">{services?.feasibility.failed?'The calendar did not return a verified result.':services?.feasibility.checking?'Checking the requested deadline with the lab calendars…':'No alternative has been confirmed.'}{!!services?.feasibility.failed&&<button className="small-button" disabled={busy} onClick={()=>void act(async()=>{await post('/feasibility/standing',{kinds:['scheduling','coverage']});})}>Retry calendar check</button>}</p>}
    {patient&&obstacle&&!confirmed&&<section id="private-alternative" className="demo-alternative" aria-label="Private appointment alternative"><span><Sparkles size={14}/>JUST FOR YOU</span><h2>There’s a way to get this done on time.</h2><p>{obstacle.fact}</p><div className="demo-slot"><CalendarCheck size={24}/><div><strong>Thursday · 9:00 am</strong><small>Northside · before your deadline</small></div></div>
      {!shared?<><p className="demo-share-review">Share this lab instruction and your Riverside preference with Dr. Chen, allow a Northside lookup, and invite Vene to raise this exact fact aloud.</p><button className="primary-button" disabled={busy||!settled} onClick={()=>void act(raise)}><Volume2 size={15}/>{busy?'Checking the current facts…':!settled?'Finishing the latest instruction…':'Raise this with Dr. Chen'}</button></>:<p className="demo-shared"><Check size={14}/>Shared with Dr. Chen. {preview?'Device voice preview requested.':'Spoken contribution requested.'}</p>}
      <small className="demo-source-note">Checked against the sandbox lab calendar. Slots can change.</small></section>}
    {doctor&&!item&&<section className="demo-guest-empty"><ShieldCheck size={25}/><h2>Only what Maria shares.</h2><p>Her private preferences and appointment suggestions are absent from this session.</p></section>}
    {doctor&&action?.state==='suggested'&&<section className="demo-clinician-action"><span className="eyebrow small">YOUR CLINICAL DECISION</span><h2>Northside is in time.</h2><p>Maria shared the lab step and asked about Thursday 9am. Confirm that this is intended, then issue the required sandbox lab order.</p><button className="primary-button" disabled={busy||action.order_available} onClick={()=>void act(async()=>{await post('/execution/actions/'+action.id+'/prerequisites',{expected_fingerprint:action.fingerprint,order:true});})}>{action.order_available?'Order sent ✓':'Confirm & send lab order'}</button><small>This records your decision. The model cannot issue an order.</small></section>}
    {patient&&shared&&action?.state==='suggested'&&<section className="demo-booking"><span className="eyebrow small">YOUR LAST WORD</span><h2>Thursday works for you?</h2><p>{action.order_available?'Dr. Chen’s lab order is ready.':'Waiting for Dr. Chen’s confirmation and lab order.'}</p><button className="primary-button" disabled={busy||!action.order_available||!action.clinician_confirmed} onClick={()=>void act(async()=>{await post('/execution/actions/'+action.id+'/approve',{digest:action.digest});})}>Book Thursday 9am <ArrowRight size={15}/></button><small>One sandbox reservation at Northside. Your approval is required.</small></section>}
    {action&&['queued','in_flight','unknown','rejected','invalidated','expired','unavailable'].includes(action.state)&&<p className="demo-progress" role="status">{action.message}</p>}
    {confirmed&&<section className="demo-confirmation" aria-label="Confirmed reservation"><div className="demo-confirm-icon"><Check size={24}/></div><span className="eyebrow small">READY BEFORE YOU LEAVE</span><h2>One less thing to chase.</h2><strong>Northside · Thursday, 9am</strong><p>Lab order received. Reservation confirmed by the sandbox office.</p><details><summary>View the actual receipt</summary><dl><dt>Receipt</dt><dd>{String(action.receipt?.receipt_id)}</dd><dt>Status</dt><dd>{String(action.receipt?.status)}</dd><dt>Recorded</dt><dd>{String(action.receipt?.recorded_at)}</dd></dl></details><small>Fictional booking. No real lab was contacted.</small></section>}
    {viewer.role==='family'&&<section className="demo-guest-empty"><LockKeyhole size={24}/><h2>Maria chooses what comes here.</h2><p>{visit.plan.length?'These are the next steps Maria shared with you.':'No lab instruction, private preference or appointment cue has been shared with you.'}</p></section>}
    {!guided&&patient&&speech?.receipts.slice(0,1).map(r=><p className="demo-playback" key={r.id}>{r.state==='completed'?'Vene finished the approved contribution.':r.state==='failed'?'Voice failed. No replacement audio was used.':'Vene contribution: '+r.state}</p>)}
    {error&&<p className="demo-error" role="alert">{error}</p>}
  </main></VisitUpdates.Provider>;
}
