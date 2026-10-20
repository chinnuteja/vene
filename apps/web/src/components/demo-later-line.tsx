'use client';
import {useState} from 'react';
import {ArrowRight} from 'lucide-react';
import {request} from '@/lib/api/client';

const LINES=['Maria will schedule the MRI at Lakeside Imaging on Wednesday after the office sends the order.',
  'Maria will pick up the new prescription at Main Street Pharmacy on Thursday.'];

// Later in the same fictional visit. The server accepts only its own allow-listed sample lines.
export function DemoLaterLine({run}:{run:string}){
  const [state,setState]=useState<'idle'|'busy'|'sent'>('idle'),[error,setError]=useState('');
  async function send(){setState('busy');setError('');
    try{await request('/encounters/'+run+'/demo/turn',{method:'POST',body:JSON.stringify({token:crypto.randomUUID(),line:'errands'})});setState('sent');}
    catch(e){setState('idle');setError((e as Error).message);}}
  return <section className="demo-sample later"><span className="eyebrow small">LATER IN THE VISIT · SAMPLE WORDS</span>
    {LINES.map(line=><blockquote key={line}>“{line}”</blockquote>)}
    <button className="primary-button" disabled={state!=='idle'} onClick={()=>void send()}>{state==='sent'?'Heard':state==='busy'?'Sending…':'Say this'} <ArrowRight size={15}/></button>
    {error&&<p role="alert">{error}</p>}</section>;
}
