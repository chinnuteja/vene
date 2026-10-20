'use client';
import {useEffect,useState} from 'react';
import {loadVisit,request,sendCommand,type Encounter,type Identity} from '@/lib/api/client';
import {apiBase} from '@/lib/api/demo-scope';
import type {ServiceViews} from '@/lib/visit-updates';
type Audience='clinician'|'family';

// The live visit for one demo pane: its own session, the server-filtered projection and service views.
export function useDemoVisit(){
  const [visit,setVisit]=useState<Encounter|null>(null),[viewer,setViewer]=useState<Identity|null>(null);
  const [services,setServices]=useState<ServiceViews|null>(null),[error,setError]=useState('');
  useEffect(()=>{const controller=new AbortController();
    loadVisit(controller.signal).then(r=>{setVisit(r.visit);setViewer(r.viewer);}).catch(e=>{if(!controller.signal.aborted)setError(e.message);});
    return()=>controller.abort();},[]);
  useEffect(()=>{
    if(!visit?.id)return;
    const stream=new EventSource(apiBase()+'/encounters/'+visit.id+'/stream?services=true');
    const update=(event:MessageEvent)=>setVisit(JSON.parse(event.data));
    stream.addEventListener('snapshot',update as EventListener);stream.addEventListener('update',update as EventListener);
    stream.addEventListener('services',((event:MessageEvent)=>setServices(JSON.parse(event.data))) as EventListener);
    const clear=()=>{stream.close();setVisit(null);setServices(null);setError('This session ended. Start a fresh demo.');};
    stream.addEventListener('access_revoked',clear);stream.addEventListener('unavailable',clear);
    stream.onerror=()=>{stream.close();setError('Live updates disconnected. Reload and start a fresh demo.');};
    return()=>stream.close();
  },[visit?.id]);
  const root='/encounters/'+visit?.id;
  async function post<T=unknown>(path:string,body:unknown){return request<T>(root+path,{method:'POST',body:JSON.stringify(body)});}
  // Adds one audience to items and every source they cite, in one versioned command.
  async function share(ids:string[],audience:Audience){
    const current=await request<Encounter>(root),changes=[];
    const items=[...current.plan,...current.evidence,...current.priorities];
    const wanted=new Set<string>();
    for(const id of ids){wanted.add(id);for(const ref of current.plan.find(p=>p.id===id)?.evidence_refs??[])wanted.add(ref);}
    for(const id of wanted){
      const target=items.find(e=>e.id===id);
      if(!target)throw new Error('This step changed. Review it again.');
      const audiences=(target.audiences??[]) as Audience[];
      if(!audiences.includes(audience))changes.push({item_id:id,audiences:[...audiences,audience]});
    }
    if(changes.length)setVisit(await sendCommand(current,{type:'sharing.batch_changed',changes}));
  }
  return {visit,viewer,services,error,setError,post,share,root};
}
