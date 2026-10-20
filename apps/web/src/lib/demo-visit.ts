'use client';
import {createContext,createElement,useContext,useEffect,useState,type ReactNode} from 'react';
import {loadVisit,request,sendCommand,type Encounter,type Identity} from '@/lib/api/client';
import {apiBase} from '@/lib/api/demo-scope';
import type {ServiceViews} from '@/lib/visit-updates';
type Audience='clinician'|'family';
type Shared={visit:Encounter|null;viewer:Identity|null;services:ServiceViews|null;error:string;setVisit:(v:Encounter)=>void};

// One live stream per demo pane. Browsers allow only a few connections per host, so every
// chapter in a pane reads this instead of opening its own.
export const DemoVisit=createContext<Shared|null>(null);

export function DemoVisitProvider({children}:{children:ReactNode}){
  const [visit,setVisit]=useState<Encounter|null>(null),[viewer,setViewer]=useState<Identity|null>(null);
  const [services,setServices]=useState<ServiceViews|null>(null),[error,setError]=useState('');
  useEffect(()=>{const controller=new AbortController();
    loadVisit(controller.signal).then(r=>{setVisit(r.visit);setViewer(r.viewer);}).catch(e=>{if(!controller.signal.aborted)setError(e.message);});
    return()=>controller.abort();},[]);
  useEffect(()=>{
    if(!visit?.id)return;
    const stream=new EventSource(apiBase()+'/encounters/'+visit.id+'/stream?services=true');
    // A command response and the stream can race; never step back to an older version.
    const update=(event:MessageEvent)=>{const incoming=JSON.parse(event.data) as Encounter;
      setVisit(current=>!current||incoming.version>current.version||(incoming.version===current.version&&incoming.consent_epoch>=current.consent_epoch)?incoming:current);};
    stream.addEventListener('snapshot',update as EventListener);stream.addEventListener('update',update as EventListener);
    stream.addEventListener('services',((event:MessageEvent)=>setServices(JSON.parse(event.data))) as EventListener);
    const clear=()=>{stream.close();setVisit(null);setServices(null);setError('This session ended. Start a fresh demo.');};
    stream.addEventListener('access_revoked',clear);stream.addEventListener('unavailable',clear);
    stream.onerror=()=>{stream.close();setError('Live updates disconnected. Reload and start a fresh demo.');};
    return()=>stream.close();
  },[visit?.id]);
  const keep=(incoming:Encounter)=>setVisit(current=>!current||incoming.version>=current.version?incoming:current);
  return createElement(DemoVisit.Provider,{value:{visit,viewer,services,error,setVisit:keep}},children);
}

export function useDemoVisit(){
  const shared=useContext(DemoVisit);
  if(!shared)throw new Error('useDemoVisit needs a DemoVisitProvider.');
  const {visit,viewer,services,setVisit}=shared;
  const [error,setError]=useState('');
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
  return {visit,viewer,services,setVisit,error:error||shared.error,setError,post,share,root};
}
