'use client';
import {useEffect,useState} from 'react';
import {Phone} from 'lucide-react';
import {request,type Encounter,type Member} from '@/lib/api/client';
import type {components} from '../../../../packages/contracts/schema';
type Pin=components['schemas']['PinIssued'];

// Patient only. A single-use PIN lets one invited person join the visit conversation by phone.
export function DialIn({visit}:{visit:Encounter}){
  const [members,setMembers]=useState<Member[]>([]),[pins,setPins]=useState<Record<string,Pin>>({});
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>{request<Member[]>('/encounters/'+visit.id+'/members').then(m=>setMembers(m.filter(x=>!x.revoked))).catch(e=>setError((e as Error).message));},[visit.id]);
  async function issue(member:Member){setBusy(true);setError('');try{
    const pin=await request<Pin>('/encounters/'+visit.id+'/dial-pins',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({membership_id:member.id})});
    setPins({...pins,[member.id]:pin});}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  return <section className="card dial-in" aria-label="Join by phone">
    <div className="panel-heading"><Phone size={20}/><h2>Join by phone</h2></div>
    <p className="muted">A PIN works once, for 15 minutes, for one person. Their phone number is never used to identify them; they press 1 to agree, 2 to decline and 9 to pause Vene.</p>
    <ul className="room-list">{members.map(m=><li key={m.id}><span>{m.role==='patient'?'You':m.name}</span>
      {pins[m.id]?<span className="dial-pin" aria-label={'Dial-in PIN for '+m.name}><strong>{pins[m.id].pin.slice(0,3)} {pins[m.id].pin.slice(3)}</strong>
        <span className="muted">{pins[m.id].dial_number?'Call '+pins[m.id].dial_number:'Dial-in number not configured in this preview'} · until {new Date(pins[m.id].expires_at).toLocaleTimeString()}</span></span>
      :<button className="small-button" disabled={busy} onClick={()=>void issue(m)}>Create PIN</button>}</li>)}</ul>
    {error&&<p role="alert">{error}</p>}
  </section>;
}
