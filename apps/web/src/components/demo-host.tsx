'use client';
import {useEffect,useRef,useState} from 'react';
import {ArrowRight,Check,Leaf,RotateCcw,ShieldCheck,Sparkles,Users} from 'lucide-react';
import {request} from '@/lib/api/client';
type Role='patient'|'clinician'|'family';
type Setup={run:string;invitations:Record<Role,string>;synthetic:true;visit_day:string};
type Chapter='before'|'during'|'leave'|'after';
const CHAPTERS:{id:Chapter;label:string;title:string;lead:string}[]=[
  {id:'before',label:'Before',title:'Bring what was left unfinished.',lead:'Vene read Maria’s July visit and her pharmacy message, and found what is still open. She decides what joins her list and what Dr. Chen sees.'},
  {id:'during',label:'During',title:'Catch the obstacle while everyone is still here.',lead:'Dr. Chen asks for labs within three days. Vene checks the calendars privately and tells only Maria what it found. She chooses whether to raise it.'},
  {id:'leave',label:'Before you leave',title:'Start every errand before you reach the car.',lead:'Later in the visit, an MRI and a new prescription come up. Each errand checks with its own office, waits for the clinician’s part and Maria’s approval, and returns its own receipt.'},
  {id:'after',label:'After',title:'Keep the thread after the door closes.',lead:'Maria sends Elena only the parts she picks, asks for a ride, and carries anything unanswered into her next visit.'},
];

export function DemoHost(){
  const [demo,setDemo]=useState<Setup|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [family,setFamily]=useState(false),[providers,setProviders]=useState<Record<string,string>|null>(null);
  const panes=useRef<Partial<Record<Role,HTMLIFrameElement|null>>>({});
  const checksAllowed=useRef(false);
  const [milestones,setMilestones]=useState<string[]>([]);
  const [chapter,setChapter]=useState<Chapter>('before');const chapterRef=useRef<Chapter>('before');
  function go(next:Chapter){chapterRef.current=next;setChapter(next);for(const pane of Object.values(panes.current))pane?.contentWindow?.postMessage({type:'vene-demo-chapter',run:demo?.run,chapter:next},location.origin);}
  useEffect(()=>{request<Record<string,string>>('/dev/demo-info').then(setProviders).catch(()=>{});},[]);
  useEffect(()=>{
    if(!demo)return;
    const receive=(event:MessageEvent)=>{
      if(event.origin!==location.origin||event.data?.run!==demo.run)return;
      const role=event.data?.role as Role;
      if(!['patient','clinician','family'].includes(role)||event.source!==panes.current[role]?.contentWindow)return;
      if(event.data.type==='vene-pane-ready'){panes.current[role]?.contentWindow?.postMessage({type:'vene-demo-invitation',
        run:demo.run,role,token:demo.invitations[role]},location.origin);
        panes.current[role]?.contentWindow?.postMessage({type:'vene-demo-chapter',run:demo.run,chapter:chapterRef.current},location.origin);}
      if(event.data.type==='vene-demo-checks'&&role==='patient'){
        checksAllowed.current=event.data.enabled===true;
        panes.current.clinician?.contentWindow?.postMessage({type:'vene-demo-checks-state',run:demo.run,enabled:checksAllowed.current},location.origin);
      }
      if(event.data.type==='vene-demo-checks-request'&&role==='clinician')panes.current.clinician?.contentWindow?.postMessage({type:'vene-demo-checks-state',run:demo.run,enabled:checksAllowed.current},location.origin);
      if(event.data.type==='vene-demo-milestone')setMilestones(current=>current.includes(event.data.milestone)?current:[...current,event.data.milestone]);
    };
    window.addEventListener('message',receive);return()=>window.removeEventListener('message',receive);
  },[demo]);
  async function start(){
    setBusy(true);setError('');
    try{
      if(demo){
        // The patient pane ends its actual room before its iframe is replaced.
        await new Promise<void>((resolve,reject)=>{
          const timer=setTimeout(()=>{window.removeEventListener('message',receive);reject(new Error('End the current conversation in Maria’s pane before starting another demo.'));},8000);
          const receive=(event:MessageEvent)=>{if(event.origin===location.origin&&event.source===panes.current.patient?.contentWindow&&
            event.data?.type==='vene-demo-ended'&&event.data.run===demo.run){clearTimeout(timer);window.removeEventListener('message',receive);resolve();}};
          window.addEventListener('message',receive);panes.current.patient?.contentWindow?.postMessage({type:'vene-end-demo',run:demo.run},location.origin);
        });
      }
      const created=await request<Setup>('/dev/demo',{method:'POST'});
      checksAllowed.current=false;
      setMilestones([]);setFamily(false);chapterRef.current='before';setChapter('before');setDemo(created);
    }catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  const guided=providers?.transport==='guided';
  const index=CHAPTERS.findIndex(c=>c.id===chapter),current=CHAPTERS[index];
  const mode=guided?'Sample visit · no microphone':providers?.stt==='deepgram'?'Live voice selected':'Offline voice · real WebRTC';
  return <div className={'demo-host'+(demo?' running':'')}>
    <header className="demo-nav"><a href="/demo" className="demo-brand"><span className="brand-mark">v<span/></span>bring vene</a>
      <div className="demo-nav-right"><span className="demo-sandbox"><ShieldCheck size={14}/>Fictional visit · sandbox offices</span>
      {demo&&<button className="small-button" disabled={busy} onClick={()=>void start()}><RotateCcw size={14}/>New demo</button>}</div></header>
    {!demo?<main className="demo-welcome"><div className="demo-intro"><div className="eyebrow">THE MOMENT CARE STARTS MOVING</div>
      <h1>Don’t take the<br/>whole visit home.</h1><p>Your questions come in. The practical obstacles come out.<br className="desktop-only"/>The next step starts before you leave.</p>
      <button className="primary-button demo-start" disabled={busy} onClick={()=>void start()}>{busy?'Preparing Maria’s visit…':'Start demo'}<ArrowRight size={19}/></button>
      <p className="demo-start-note">One fictional visit in four short chapters, about three minutes.<br/>Every booking still needs Maria’s approval.</p>
      <div className="demo-provider-chips"><span><i/>{mode}</span><span>{guided?'A real session per person':'LiveKit'}</span><span>{providers?.model==='fixture'?'Rule-based sample interpreter':providers?.model??'Checking interpreter'}</span><span>{guided?'Device voice preview':providers?.tts==='fixture'?'Offline voice':providers?.tts??'Checking voice'}</span></div>
    </div><div className="demo-preview-art" aria-label="A preview of the private appointment cue"><div className="demo-art-phone"><div className="phone-island"/><span className="demo-art-time">9:41</span>
      <div className="demo-art-avatar">M</div><h2>Here with you,<br/>Maria.</h2><p>YOUR VISIT WITH DR. CHEN</p>
      <div className="demo-art-wave">{Array.from({length:19},(_,i)=><i key={i} style={{height:[8,14,22,32,18,40,27,17,34,46,26,15,34,21,12,29,19,13,7][i]}}/>)}</div>
      <div className="demo-art-cue"><span><Sparkles size={13}/>JUST FOR YOU</span><strong>There’s a way to get<br/>this done on time.</strong><p>Northside has Thursday at 9am.</p><div>Let’s bring it up <ArrowRight size={15}/></div></div>
      <small>Illustrative preview · start to check actual availability</small></div><div className="demo-art-note"><Leaf size={18}/><span>A little less to carry.</span></div></div>
    </main>:<main className="demo-stage">
      <div className="demo-stage-heading"><div><span className="eyebrow">MARIA’S VISIT WITH DR. CHEN · {demo.visit_day.toUpperCase()}</span><h1>{current.title}</h1><p>{current.lead}</p></div>
        <label className="demo-family-toggle"><input type="checkbox" checked={family} onChange={e=>setFamily(e.target.checked)}/><Users size={16}/>Show Elena’s view</label></div>
      <nav className="demo-chapters" aria-label="Visit chapters">{CHAPTERS.map((c,i)=><button key={c.id} aria-current={chapter===c.id?'step':undefined} className={(chapter===c.id?'current ':'')+(i<index?'done':'')} onClick={()=>go(c.id)}>
        <i>{i<index?<Check size={12}/>:i+1}</i>{c.label}</button>)}
        {index<CHAPTERS.length-1&&<button className="demo-next" onClick={()=>go(CHAPTERS[index+1].id)}>Next: {CHAPTERS[index+1].label} <ArrowRight size={14}/></button>}</nav>
      {chapter==='during'&&<div className="demo-story"><span className={milestones.includes('heard')?'done':''}><i>{milestones.includes('heard')?<Check size={12}/>:1}</i>Hear the next step</span>
        <span className={milestones.includes('obstacle')?'done':''}><i>{milestones.includes('obstacle')?<Check size={12}/>:2}</i>Catch the obstacle privately</span>
        <span className={milestones.includes('booked')?'done':''}><i>{milestones.includes('booked')?<Check size={12}/>:3}</i>Leave with a receipt</span></div>}
      <div className={'demo-panes'+(family?' with-family':'')}>
        <section className="demo-patient-column"><div className="demo-pane-caption"><span>MARIA</span>Her phone. Her choice.</div><div className="demo-phone"><div className="phone-island"/>
          <iframe ref={el=>{panes.current.patient=el;}} src={'/demo/pane/'+demo.run+'/patient'} title="Maria’s private phone" allow="microphone; autoplay"/></div></section>
        <section className="demo-clinician-column"><div className="demo-pane-caption"><span>DR. CHEN</span>Only what Maria shares.</div><div className="demo-clinician-window"><div className="demo-window-bar"><i/><i/><i/><span>Visit with Maria</span></div>
          <iframe ref={el=>{panes.current.clinician=el;}} src={'/demo/pane/'+demo.run+'/clinician'} title="Dr. Chen’s clinician view" allow="microphone; autoplay"/></div>
          {chapter==='during'&&<details className="demo-prompt"><summary>The 60-second path</summary><p>{guided?'Allow private checks as Maria, then choose Say this as Dr. Chen.':'Join and agree in both panes, then choose Start listening as Maria.'}</p><blockquote>“Please get labs done within three days. We can send the lab order today.”</blockquote><p>Maria reviews the private cue and chooses whether to raise it. Dr. Chen sends the lab order. Maria approves the offered booking.</p></details>}</section>
        {family&&<section className="demo-family-column"><div className="demo-pane-caption"><span>ELENA</span>Only what Maria chooses.</div><iframe ref={el=>{panes.current.family=el;}} src={'/demo/pane/'+demo.run+'/family'} title="Elena’s family view"/></section>}
      </div>
    </main>}
    {!demo&&<section className="demo-capabilities" aria-label="Full product capabilities">
      <div className="demo-capability-heading"><div><span className="eyebrow">THE WHOLE VISIT, NOT JUST THE LAB</span><h2>One conversation. Several next steps.</h2>
        <p>The tour follows Maria from her preparation to the ride home, on the same services as the complete workspace. Every step below is in it.</p></div>
        <a className="secondary-button" href="/dev">Open complete workspace <ArrowRight size={17}/></a></div>
      <div className="demo-capability-grid">
        <article><span className="eyebrow small">BEFORE</span><h3>Bring unfinished things.</h3><p>Draft an agenda from open questions and unfinished steps. The patient reviews it and chooses what to share.</p></article>
        <article><span className="eyebrow small">DURING</span><h3>Catch the obstacle privately.</h3><p>Check availability, coverage, pharmacy stock and missing documents. Raise the fact while the right person can respond.</p></article>
        <article><span className="eyebrow small">BEFORE YOU LEAVE</span><h3>Start every ready errand.</h3><p>Labs, imaging, specialist intake and prescription pickup each have their own approvals and receipt. Prior-authorization submissions follow the same approval path.</p></article>
        <article><span className="eyebrow small">AFTER</span><h3>Keep the thread.</h3><p>Compare after-visit documents, approve a scoped family update, ask for practical help and carry open questions into the next visit.</p></article>
      </div><p className="demo-capability-boundary">Fictional offices and health-plan responses throughout. A confirmed arrangement is not a completed appointment, a dispensed medicine or a clinical decision. The workspace opens with ordinary invitations for each role.</p>
    </section>}
    {error&&<p className="demo-error" role="alert">{error}</p>}
    <footer className="demo-footer">Built to fit Vene’s follow-through. Clinical decisions stay with the clinician.</footer>
  </div>;
}
