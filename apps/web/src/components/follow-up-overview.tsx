'use client';
import Link from 'next/link';
import {ArrowRight,Leaf,ShieldCheck} from 'lucide-react';
import type {Encounter,Identity} from '@/lib/api/client';
import {useVisitUpdates} from '@/lib/visit-updates';

export function FollowUpOverview({visit,viewer}:{visit:Encounter;viewer:Identity}){
  const updates=useVisitUpdates();
  const rows=visit.plan.map(item=>{
    const action=updates?.execution.actions.find(a=>a.item_id===item.id);
    // The server distinguishes receipt validity from permission to approve new work.
    const current=!!action?.receipt_current;
    const confirmed=current&&action?.state==='confirmed'&&action.receipt?.status==='confirmed';
    const errand=updates?.execution.errands.find(e=>e.kind===action?.kind);
    const label=!updates?'Checking saved office status…':!action?'No office arrangement checked':
      action.state==='confirmed'?!current?'Earlier arrangement confirmed · plan changed':errand?.confirmed??'Office outcome confirmed':
      ({checking:'Checking the office',suggested:'Offered · awaiting required approvals',queued:'Approved · waiting to send',
        in_flight:'Sent · awaiting the office',unknown:'Completion unknown · reconciling',rejected:'Office rejected the request',
        no_slot:'No suitable availability',expired:'Availability expired · check again',invalidated:'Changed · review and check again',
        cancelled:'Not sent',unavailable:'Office unavailable'})[action.state]??action.state;
    return {item,action,confirmed,label};
  });
  const confirmed=rows.filter(r=>r.confirmed).length;
  return <div className="content-grid follow-overview" aria-label="Next-step overview">
    <section className="card follow-card"><div className="section-heading"><div><div className="eyebrow small">KEEPING THINGS CLEAR</div><h2>Your next steps</h2></div>
      {updates&&<span className="pill">{confirmed} office {confirmed===1?'outcome':'outcomes'} confirmed</span>}</div>
      {rows.map(({item,action,confirmed,label})=><article className="follow-item" key={item.id} aria-label={'Next-step status: '+item.title}>
        <div className="timeline-dot"/><div><h3>{item.title}</h3><p>{item.detail}</p>
          <p className={confirmed?'confirmed-outcome':'muted'}><strong>{label}</strong></p>
          {action?.slot&&<p>{String(action.slot.label)}</p>}
          <div className="detail-tags"><span>Owner: {item.owner||'not yet clarified'}</span><span>When: {item.timeframe||'not yet clarified'}</span>
            {item.location&&<span>Where: {item.location}</span>}{item.external_completed&&<span>Completion reported · separate from the office receipt</span>}</div></div>
      </article>)}
      {!rows.length&&<p className="muted">Next steps will appear when they are discussed and recorded.</p>}
      <div className="soft-note"><ShieldCheck size={20}/><p>An office confirmation is a concrete outcome. It does not mean the appointment, pickup or treatment has happened. Review individual receipts and anything still waiting below.</p></div>
    </section>
    <aside className="right-column"><section className="card compact"><h3>{viewer.role==='patient'?'Keep the next step moving.':'Only what was shared with you.'}</h3>
      <p className="muted">{viewer.role==='patient'?'Review office outcomes, compare after-visit documents and choose the fields to include in a family update below. Each update still needs your approval.':'Office outcomes and documents appear here only when the patient shares their supporting context. Family members answer their own help requests.'}</p>
      <Link className="text-link" href="/visit">Back to your visit <ArrowRight size={15}/></Link></section>
      <div className="gentle-note"><Leaf size={18}/><p>Care moves forward<br/>one clear step at a time.</p></div></aside>
  </div>;
}
