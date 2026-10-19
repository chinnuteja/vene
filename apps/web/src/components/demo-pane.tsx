'use client';
import {useEffect,useRef,useState} from 'react';
import {loadVisit,redeemInvite,request,type Encounter,type Identity} from '@/lib/api/client';
import {DemoExperience} from './demo-experience';
type Role='patient'|'clinician'|'family';

export function DemoPane({run,role}:{run:string;role:Role}){
  const [ready,setReady]=useState(false),[error,setError]=useState('');
  const used=useRef(false),identity=useRef<Identity|null>(null);
  useEffect(()=>{
    const receive=async(event:MessageEvent)=>{
      if(event.origin!==location.origin||event.source!==parent||event.data?.run!==run)return;
      if(event.data.type==='vene-demo-invitation'&&event.data.role===role&&typeof event.data.token==='string'&&!used.current){
        used.current=true;
        try{
          let existing:Identity|null=null;
          try{existing=await request<Identity>('/auth/me');}catch{}
          const viewer=existing?.encounter_id===run&&existing.role===role?existing:await redeemInvite(event.data.token);identity.current=viewer;
          if(viewer.encounter_id!==run||viewer.role!==role)throw new Error('This invitation belongs to a different pane.');
          setReady(true);
        }catch(e){setError((e as Error).message);}
      }
      if(event.data.type==='vene-end-demo'&&role==='patient'&&identity.current){
        try{
          const root='/encounters/'+run+'/call',call=await request<{revision:number;state:string}>(root);
          if(call.revision&&call.state!=='ended')await request(root+'/controls',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({command_id:crypto.randomUUID(),expected_revision:call.revision,type:'end'})});
          parent.postMessage({type:'vene-demo-ended',run,role},location.origin);
        }catch(e){setError((e as Error).message);}
      }
    };
    window.addEventListener('message',receive);
    parent.postMessage({type:'vene-pane-ready',run,role},location.origin);
    return()=>window.removeEventListener('message',receive);
  },[run,role]);
  if(error)return <p className="demo-error" role="alert">{error}</p>;
  if(!ready)return <div className="demo-pane-loading" role="status">Opening your own visit session…</div>;
  return <div className={'demo-embedded '+role}><DemoExperience/></div>;
}
