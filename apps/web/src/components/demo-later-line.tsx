'use client';
import {useEffect,useState} from 'react';
import {ArrowRight} from 'lucide-react';
import {request} from '@/lib/api/client';
import {useDemoVisit} from '@/lib/demo-visit';

const LINES=['Maria will schedule the MRI at Lakeside Imaging on Wednesday after the office sends the order.',
  'Maria will pick up the new prescription at Main Street Pharmacy on Thursday.'];

// Later in the same fictional visit. The server accepts only its own allow-listed sample lines.
export function DemoLaterLine({run}:{run:string}){
  const {checksAllowed}=useDemoVisit();
  const [state,setState]=useState<'idle'|'busy'|'sent'>('idle'),[error,setError]=useState('');
  const [mode,setMode]=useState<'loading'|'fixture'|'live'|'unavailable'>('loading');
  useEffect(()=>{const controller=new AbortController();
    fetch('/api/dev/demo-info',{cache:'no-store',signal:controller.signal}).then(async r=>{
      if(!r.ok)throw new Error('Demo configuration is unavailable.');
      const c=await r.json();setMode(c.stt==='fixture'?'fixture':'live');
    }).catch(()=>{if(!controller.signal.aborted)setMode('unavailable');});
    return()=>controller.abort();},[]);
  async function send(){setState('busy');setError('');
    try{await request('/encounters/'+run+'/demo/turn',{method:'POST',body:JSON.stringify({token:crypto.randomUUID(),line:'errands'})});setState('sent');}
    catch(e){setState('idle');setError((e as Error).message);}}
  return <section className="demo-sample later"><span className="eyebrow small">{mode==='live'?'LATER IN THE VISIT · SAY THIS INTO THE AGREED MICROPHONE':'DEMO INPUT · DR. CHEN’S NEXT WORDS'}</span>
    <p>These are new example words from Dr. Chen, later in the same visit. They are not Vene’s recommendations or completed orders.</p>
    {LINES.map(line=><blockquote key={line}>“{line}”</blockquote>)}
    {mode==='live'?<small>Speak into the agreed microphone. These words are prompts, not a transcript. No scripted fallback.</small>
      :mode==='fixture'?<><small>“Say this” adds these two statements as sample conversation text. No microphone is used. Maria’s checklist updates after Vene processes them.</small>
        <button className="primary-button" disabled={state!=='idle'||!checksAllowed} onClick={()=>void send()}>{state==='sent'?'Sample words added':state==='busy'?'Adding sample words…':checksAllowed?'Say this':'Waiting for Maria’s permission'} <ArrowRight size={15}/></button>
        {!checksAllowed&&state!=='sent'&&<p>Maria needs to allow private checks in her pane first.</p>}</>
      :<p role="status">{mode==='loading'?'Checking the conversation mode…':'Conversation mode is unavailable. No sample words were added.'}</p>}
    {error&&<p role="alert">{error}</p>}</section>;
}
