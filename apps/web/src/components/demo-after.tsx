'use client';
import {useEffect,useState} from 'react';
import {CalendarClock,Car,HeartHandshake,LockKeyhole,MessageSquareText,ShieldCheck} from 'lucide-react';
import {request} from '@/lib/api/client';
import {useDemoVisit} from '@/lib/demo-visit';
import type {components} from '../../../../packages/contracts/schema';
import {Checklist,useErrands} from './demo-leave';
type Continuity=components['schemas']['ContinuityView'];
type Member=components['schemas']['MemberView'];

export function DemoAfter(){
  const {visit,viewer,services,error,setError,post,share,root}=useDemoVisit();
  const [continuity,setContinuity]=useState<Continuity|null>(null),[family,setFamily]=useState<Member|null>(null);
  const [busy,setBusy]=useState(false);
  const {steps,catalog,latest}=useErrands(visit,services);
  const patient=viewer?.role==='patient',doctor=viewer?.role==='clinician',elena=viewer?.role==='family';
  useEffect(()=>{if(!visit?.id||doctor)return;let alive=true;
    const poll=()=>request<Continuity>(root+'/continuity').then(v=>{if(alive)setContinuity(v);}).catch(()=>{});
    void poll();const timer=setInterval(poll,1500);return()=>{alive=false;clearInterval(timer);};},[visit?.id,doctor,root]);
  useEffect(()=>{if(!visit?.id||!patient)return;request<Member[]>(root+'/members').then(m=>setFamily(m.find(x=>x.role==='family'&&!x.revoked)??null)).catch(()=>{});},[visit?.id,patient,root]);
  if(!visit||!viewer)return <div className="demo-pane-loading" role="status">{error||'Opening your visit…'}</div>;
  async function act(fn:()=>Promise<void>){setBusy(true);setError('');try{await fn();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  const booked=steps.filter(s=>latest(s.id)?.state==='confirmed');
  // A ride to an appointment: the lab if booked, otherwise the imaging.
  const confirmed=booked.map(s=>latest(s.id)!),lab=confirmed.find(a=>a.kind==='lab')??confirmed.find(a=>a.kind==='imaging');
  const update=continuity?.family_updates[0];
  const rides=services?.circle.rides??[];const ride=rides.find(r=>r.state!=='withdrawn');
  const unanswered=visit.priorities.filter(p=>p.selected&&(p.status??'open')==='open');
  const first=family?.name.split(' ')[0]??'Elena';
  async function tell(){
    await share(booked.map(s=>s.id),'family');
    const recipient=continuity?.family_recipients[0]?.id??family?.id;
    const view=await post<Continuity>('/continuity/family-updates',{recipient_id:recipient,plan_ids:booked.map(s=>s.id),fields:['title','timeframe','office_status']});
    const draft=view.family_updates.find(u=>u.state==='draft'&&u.digest);
    if(!draft)throw new Error('The update could not be prepared. Nothing was sent.');
    setContinuity(await post<Continuity>('/continuity/family-updates/'+draft.id+'/approve',{digest:draft.digest}));
  }
  async function askRide(){if(!lab||!family)return;await share([lab.item_id],'family');await post('/care-circle/rides',{action_id:lab.id,recipient_id:family.id});}
  return <main className={'demo-experience demo-chapter '+viewer.role}>
    <div className="demo-chapter-head"><span className="eyebrow small">AFTER THE VISIT</span>
      <h1>{patient?'A clear way forward.':doctor?'What Maria is leaving with.':'Here for Maria.'}</h1>
      <p>{patient?'Booked, sent and shared, with a receipt for each. The rest comes with you next time.':doctor?'Each step carries its own receipt. Nothing here needs a phone call back.':'You see only what Maria chose to send you.'}</p></div>

    {!elena&&(booked.length?<Checklist steps={booked} catalog={catalog} latest={latest} patient={patient}/>
      :<section className="demo-guest-empty"><CalendarClock size={24}/><h2>Nothing booked yet.</h2><p>Finish “During” and “Before you leave” first.</p></section>)}

    {patient&&booked.length>0&&<section className="demo-after-card"><HeartHandshake size={20}/><div><h3>Tell {first} what’s booked.</h3>
      {!update?<><p>Only the step, when, and the office’s answer. Nothing about your questions or health.</p><button className="primary-button" disabled={busy||!family} onClick={()=>void act(tell)}>Send to {first}</button></>
        :<><p className="demo-shared">{update.state==='delivered'?'Delivered to '+first+'.':'Sending…'}</p><pre className="demo-update-text">{update.text}</pre></>}</div></section>}

    {patient&&lab&&<section className="demo-after-card"><Car size={20}/><div><h3>Need a ride to {String(lab.slot?.location??'the lab')}?</h3>
      {!ride?<><p>{first} sees where and when, and answers for herself.</p><button className="secondary-button" disabled={busy||!family} onClick={()=>void act(askRide)}>Ask {first} to drive</button></>
        :<p className="demo-shared">{ride.state==='accepted'?first+' said yes.':ride.state==='declined'?first+' can’t this time.':'Asked. Waiting for '+first+'.'}</p>}</div></section>}

    {patient&&unanswered.length>0&&<section className="demo-after-card"><MessageSquareText size={20}/><div><h3>Still unanswered today.</h3>
      <ul className="demo-carry">{unanswered.map(p=><li key={p.id}>{p.title}</li>)}</ul><p>Vene will bring these to your next visit’s preparation, with where each came from.</p></div></section>}

    {elena&&<>{(continuity?.family_updates??[]).filter(u=>u.state==='delivered').map(u=><section key={u.id} className="demo-after-card arrived"><MessageSquareText size={20}/><div><h3>Update from Maria</h3><pre className="demo-update-text">{u.text}</pre></div></section>)}
      {rides.filter(r=>r.state!=='withdrawn').map(r=><section key={r.id} className="demo-after-card arrived"><Car size={20}/><div><h3>Maria asks: can you drive?</h3><p><strong>{r.purpose}</strong> · {r.when} · {r.where}</p>
        {r.state==='asked'?<div className="office-buttons"><button className="primary-button" disabled={busy} onClick={()=>void act(async()=>{await post('/care-circle/rides/'+r.id+'/answer',{answer:'yes'});})}>Yes, I can</button><button className="secondary-button" disabled={busy} onClick={()=>void act(async()=>{await post('/care-circle/rides/'+r.id+'/answer',{answer:'no'});})}>I can’t</button></div>
          :<p className="demo-shared">{r.state==='accepted'?'You said yes. Maria can see your answer.':'You said no.'}</p>}</div></section>)}
      {!(continuity?.family_updates??[]).some(u=>u.state==='delivered')&&!rides.length&&<section className="demo-guest-empty"><LockKeyhole size={24}/><h2>Maria chooses what comes here.</h2><p>Nothing has been sent to you yet.</p></section>}</>}

    {doctor&&booked.length>0&&<p className="demo-progress">Orders went out during the visit. The office has no follow-up calls to make for these steps.</p>}
    <p className="demo-boundary"><ShieldCheck size={13}/>A confirmed booking is not a completed appointment. Fictional people and offices.</p>
    {error&&<p className="demo-error" role="alert">{error}</p>}
  </main>;
}
