'use client';
import {useEffect,useState} from 'react';
import {Mic,PauseCircle,ShieldCheck,Smartphone,UserPlus} from 'lucide-react';
import {useDemoTools} from '@/lib/demo-tools';
import {request,type Encounter,type Identity,type Member} from '@/lib/api/client';
import type {components} from '../../../../packages/contracts/schema';
type Room=components['schemas']['RoomView'];
type Role=components['schemas']['PersonIn']['role'];
type Call=components['schemas']['CallView'];
const ROLE:Record<Role,string>={clinician:'Clinician',family:'Family',other:'Someone else'};

// One phone on the table. Everything here is attested by the patient on her own device;
// a name given to a voice is attribution only, never that person's authority.
export function InRoomMode({visit,viewer}:{visit:Encounter;viewer:Identity}){
  const demoTools=useDemoTools();
  const [room,setRoom]=useState<Room|null>(null),[members,setMembers]=useState<Member[]>([]);
  const [draft,setDraft]=useState<{name:string;role:Role}[]>([]),[name,setName]=useState(''),[role,setRole]=useState<Role>('clinician');
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  const [fixture,setFixture]=useState({label:'S0',text:''});
  const root='/encounters/'+visit.id+'/room';const patient=viewer.role==='patient';
  useEffect(()=>{let alive=true,pending=false;
    async function poll(){if(pending)return;pending=true;try{const r=await request<Room>(root);if(alive){setRoom(r);setError('');}}catch(e){if(alive)setError((e as Error).message);}finally{pending=false;}}
    void poll();const t=setInterval(()=>void poll(),1000);return()=>{alive=false;clearInterval(t);};},[root,visit.version]);
  useEffect(()=>{if(!patient)return;request<Member[]>('/encounters/'+visit.id+'/members').then(m=>setMembers(m.filter(x=>x.role!=='patient'&&!x.revoked))).catch(()=>setMembers([]));},[patient,visit.id]);
  async function post(path:string,body?:unknown,message=''){setBusy(true);setError('');setNotice('');try{setRoom(await request<Room>(root+path,{method:'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)}));setNotice(message);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  async function pause(){setBusy(true);setError('');try{const call=await request<Call>('/encounters/'+visit.id+'/call');
    if(!call.revision||call.state==='ended'){setNotice('Vene is not in a conversation yet, so nothing is being processed.');return;}
    await request('/encounters/'+visit.id+'/call/controls',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command_id:crypto.randomUUID(),expected_revision:call.revision,type:'pause'})});
    setNotice('Vene is paused. Nothing is processed until you resume it.');}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  function speak(text:string){try{const u=new SpeechSynthesisUtterance(text);u.rate=.95;window.speechSynthesis.speak(u);}catch{setNotice('This device cannot play speech. Read the disclosure aloud instead.');}}
  if(!room)return error?<p role="alert">{error}</p>:null;
  if(!patient)return room.state==='active'?<p className="soft-note in-room-note"><Smartphone size={16}/> The patient is using one phone in the room. Vene listens only with everyone&apos;s agreement.</p>:null;
  const people=room.people??[];const speakers=room.speakers??[];const disclosed=!!room.disclosure_at;
  return <section className="card in-room-mode" aria-label="One phone in the room">
    <div className="panel-heading"><Smartphone size={22}/><h2>One phone in the room.</h2>
      <span className={'pill '+(room.state==='active'?'green':'amber')}>{({off:'Off',setting_up:'Setting up',active:'Listening with agreement',declined:'Someone declined'})[room.state]}</span></div>
    {room.state==='off'&&<>
      <p className="muted">Seeing your clinician in person? Put this phone on the table. Vene listens only after you tell everyone and each person agrees.</p>
      <fieldset className="room-people"><legend>Who is here with you?</legend>
        {members.length>0&&<div className="example-choices">{members.map(m=><button key={m.id} disabled={busy||draft.some(d=>d.name===m.name)} onClick={()=>setDraft([...draft,{name:m.name,role:m.role==='clinician'?'clinician':'family'}])}>+ {m.name}</button>)}</div>}
        <div className="room-add"><label>Name<input value={name} onChange={e=>setName(e.target.value)} aria-label="Name of someone present"/></label>
          <label>Role<select aria-label="Their role" value={role} onChange={e=>setRole(e.target.value as Role)}>{(Object.keys(ROLE) as Role[]).map(r=><option key={r} value={r}>{ROLE[r]}</option>)}</select></label>
          <button className="secondary-button" disabled={busy||name.trim().length<2} onClick={()=>{setDraft([...draft,{name:name.trim(),role}]);setName('');}}><UserPlus size={16}/> Add</button></div>
        {draft.length>0&&<ul className="room-list">{draft.map((d,i)=><li key={i}>{d.name} · {ROLE[d.role]} <button className="text-link" onClick={()=>setDraft(draft.filter((_,j)=>j!==i))}>Remove</button></li>)}</ul>}
      </fieldset>
      <button className="primary-button" disabled={busy||!draft.length} onClick={()=>void post('/start',{people:draft},'Next: tell everyone what Vene does.')}>Start in-room mode</button>
    </>}
    {room.state!=='off'&&<>
      {/* While listening, setup collapses so Pause and the speakers stay within reach on a phone. */}
      <details className="room-setup" open={room.state!=='active'}><summary>{room.state==='active'?`Disclosure given · ${people.length} ${people.length===1?'person':'people'} agreed`:'Set up in-room mode'}</summary>
      <ol className="room-steps">
        <li className={disclosed?'done':''}><strong>Tell everyone</strong>
          <blockquote>{room.disclosure}</blockquote>
          <div className="office-buttons"><button className="secondary-button" disabled={busy} onClick={()=>speak(room.disclosure)}>Play on this phone</button>
            <button className="primary-button" disabled={busy||disclosed} onClick={()=>void post('/disclosure',undefined,'Now ask each person whether they agree.')}>{disclosed?'Disclosure given':'I told everyone'}</button></div></li>
        <li className={people.every(p=>p.agreed===true)?'done':''}><strong>Ask each person</strong>
          <ul className="room-list">{people.map(p=><li key={p.id} aria-label={'Agreement: '+p.name}><span>{p.name} · {ROLE[p.role as Role]}</span>
            <span className="muted">{p.agreed===true?'agreed':p.agreed===false?'declined':'not asked yet'}</span>
            <span className="office-buttons"><button className="small-button" disabled={busy||!disclosed||p.agreed===true} onClick={()=>void post('/agreements',{person_id:p.id,agreed:true})}>Agreed</button>
              <button className="small-button" disabled={busy||!disclosed||p.agreed===false} onClick={()=>void post('/agreements',{person_id:p.id,agreed:false})}>Declined</button></span></li>)}</ul>
          <p className="muted">You are recording what each person said. Vene cannot verify it.</p></li>
      </ol></details>
      {room.state==='declined'&&<p className="soft-note">Someone declined. Vene stays off; the conversation continues as usual.</p>}
      {room.state==='active'&&<>
        <p className="room-live"><Mic size={18}/> Everyone agreed. Join the conversation below with this phone&apos;s microphone; Vene processes only while it is not paused.</p>
        <button className="pause-big" disabled={busy} onClick={()=>void pause()}><PauseCircle size={28}/> Pause Vene</button>
        <div className="room-speakers"><h3>Who is speaking?</h3>
          {!speakers.length&&<p className="muted">Voices appear here as Vene hears them. Tell Vene who each one is.</p>}
          {speakers.map(s=><div key={s.label} className={'room-speaker'+(s.attributed?'':' unknown')} aria-label={'Speaker '+s.label}>
            <p><strong>{s.name}</strong>{s.last_heard&&<span className="muted"> · “{s.last_heard}”</span>}</p>
            <div className="example-choices"><button disabled={busy||s.person_id==='patient'} onClick={()=>void post('/speakers',{label:s.label,person_id:'patient'})}>That&apos;s me</button>
              {people.map(p=><button key={p.id} disabled={busy||s.person_id===p.id} onClick={()=>void post('/speakers',{label:s.label,person_id:p.id})}>That&apos;s {p.name}</button>)}
              <button disabled={busy||s.person_id===null} onClick={()=>void post('/speakers',{label:s.label,person_id:null})}>Not sure</button></div></div>)}
          <p className="muted">Naming a voice helps the notes; it never lets anyone approve or order something on another person&apos;s behalf.</p>
          {(room.suppressed_self_speech??0)>0&&<p className="muted">Vene ignored {room.suppressed_self_speech} time{room.suppressed_self_speech===1?'':'s'} it heard itself.</p>}
        </div>
      </>}
      <div className="office-buttons room-more">
        <AddArrival busy={busy} onAdd={(n,r)=>void post('/people',{name:n,role:r},'New arrival: tell them and ask before Vene continues.')}/>
        <button className="text-link" disabled={busy} onClick={()=>void post('/end',undefined,'In-room mode ended.')}>End in-room mode</button></div>
      {demoTools&&room.fixture_input_enabled&&room.state==='active'&&<details className="sandbox-controls"><summary>Development sandbox · speech heard in the room</summary>
        <div className="room-add"><label>Voice<select aria-label="Fictional voice label" value={fixture.label} onChange={e=>setFixture({...fixture,label:e.target.value})}>{['S0','S1','S2'].map(l=><option key={l}>{l}</option>)}</select></label>
          <label>Words<input aria-label="Fictional words heard" value={fixture.text} onChange={e=>setFixture({...fixture,text:e.target.value})}/></label>
          <button disabled={busy||fixture.text.trim().length<3} onClick={()=>{void post('/fixture-utterances',fixture);setFixture({...fixture,text:''});}}>Hear this</button></div></details>}
    </>}
    <p className="office-boundary"><ShieldCheck size={17}/> No audio is recorded. Agreement and names are recorded as you attest them.</p>
    {notice&&<p role="status">{notice}</p>}{error&&<p role="alert">{error}</p>}
  </section>;
}

function AddArrival({busy,onAdd}:{busy:boolean;onAdd:(name:string,role:Role)=>void}){
  const [open,setOpen]=useState(false),[name,setName]=useState(''),[role,setRole]=useState<Role>('other');
  if(!open)return <button className="secondary-button" disabled={busy} onClick={()=>setOpen(true)}><UserPlus size={16}/> Someone arrived</button>;
  return <span className="room-add"><input aria-label="Name of the new arrival" value={name} onChange={e=>setName(e.target.value)}/>
    <select aria-label="New arrival role" value={role} onChange={e=>setRole(e.target.value as Role)}>{(Object.keys(ROLE) as Role[]).map(r=><option key={r} value={r}>{ROLE[r]}</option>)}</select>
    <button className="secondary-button" disabled={busy||name.trim().length<2} onClick={()=>{onAdd(name.trim(),role);setOpen(false);setName('');}}>Add</button></span>;
}
