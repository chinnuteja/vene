import {evidence} from './platform';
import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import {base,command} from './helpers';
import {setup,finish,speech} from './speech-helpers';

test('live providers complete an observed synthetic conversation and approved sandbox reservation',async({baseURL})=>{
  test.skip(process.env.BRING_VENE_LIVE_PROVIDER_GATE!=='true','Explicit live credentials and generated original speech are required.');
  test.setTimeout(240000);const env=await setup(baseURL);const {p,d,patient,doctor}=env;
  const started=Date.now();
  try{
    await p.getByRole('button',{name:'Enable visit understanding',exact:true}).click();
    const understanding=await (await patient.request.get(base+'/understanding')).json();expect(['deepseek','openai']).toContain(understanding.provider);
    expect((await speech(patient)).provider).toBe('cartesia');expect((await (await patient.request.get(base+'/call')).json()).provider).toBe('deepgram');
    await d.getByRole('button',{name:'Unmute my microphone',exact:true}).click();
    // The controlled file input may be part-way through its loop at consent.
    // Require the complete recognized plan rather than its closing marker.
    await expect.poll(async()=>{const turns=await (await patient.request.get(base+'/call/utterances')).json();return turns.some(t=>t.provider==='deepgram'&&/Maria will arrange.*Riverside Lab.*Tuesday.*order/i.test(t.text));},{timeout:45000}).toBe(true);
    await d.getByRole('button',{name:'Mute my microphone',exact:true}).click();
    await expect.poll(async()=>{const state=await (await patient.request.get(base+'/understanding')).json();return state.state==='ready'&&state.revision===state.processed_revision;},{timeout:45000}).toBe(true);
    await expect.poll(async()=>{const v=await (await patient.request.get(base)).json();return v.plan.some(x=>x.origin==='interpretation'&&x.evidence_refs.length&&/lab/i.test(x.title));},{timeout:45000}).toBe(true);
    const view=await (await patient.request.get(base)).json();const item=view.plan.find(x=>x.origin==='interpretation'&&/lab/i.test(x.title));
    expect(item.timeframe).toMatch(/Tuesday/i);expect(item.location).toMatch(/Riverside Lab/i);expect(item.owner).toBe('Maria');
    expect(item.clinician_confirmed).toBe(false);expect(item.order_available).toBe(false);expect(item.external_completed).toBe(false);
    await p.getByLabel('Vene participation mode',{exact:true}).selectOption('closeout');
    await expect(d.getByText('Maria chose: Agreed closeout.',{exact:true})).toBeVisible();
    await p.getByRole('button',{name:'Allow Vene to speak',exact:true}).click();await d.getByRole('button',{name:'Allow Vene to speak',exact:true}).click();
    await p.getByRole('button',{name:'Review shared next steps aloud',exact:true}).click();
    await expect(p.getByRole('alert',{name:'Speech error'})).toHaveText('Share a next step and its sources with everyone present before requesting a closeout.');
    expect((await speech(patient)).receipts).toHaveLength(0);
    for(const ref of item.evidence_refs){const source=view.evidence.find(e=>e.id===ref);expect(source.origin).toBe('deepgram');await command(patient,{type:'sharing.changed',item_id:ref,audiences:['clinician']});}
    await command(patient,{type:'sharing.changed',item_id:item.id,audiences:['clinician']});
    await p.getByRole('button',{name:'Review shared next steps aloud',exact:true}).click();
    await expect(p.locator('[data-vene-output-active="true"]')).toBeVisible({timeout:25000});
    await expect(d.locator('[data-vene-output-active="true"]')).toBeVisible();
    await expect.poll(async()=>(await speech(patient)).receipts[0]?.state,{timeout:25000}).toBe('completed');
    const speechReceipt=(await speech(patient)).receipts[0];expect(speechReceipt.hearing_confirmed).toBe(false);
    const step=p.getByRole('article',{name:'Office follow-through: '+item.title,exact:true});
    await step.getByRole('button',{name:'Allow office checks',exact:true}).click();await step.getByRole('button',{name:'Check this window',exact:true}).click();
    await expect.poll(async()=>(await (await patient.request.get(base+'/execution')).json()).actions[0]?.state,{timeout:10000}).toBe('suggested');
    const doctorStep=d.getByRole('article',{name:'Office follow-through: '+item.title,exact:true});
    await doctorStep.getByRole('button',{name:'Confirm and issue sandbox order',exact:true}).click();
    await expect(step.getByText('Order: sandbox order available',{exact:true})).toBeVisible();
    await step.getByRole('button',{name:'Approve this sandbox reservation',exact:true}).click();
    await expect(step.getByText('Reservation confirmed',{exact:true})).toBeVisible({timeout:15000});
    const action=(await (await patient.request.get(base+'/execution')).json()).actions[0];
    const finalView=await (await patient.request.get(base)).json();
    await p.evaluate(()=>{if(document.activeElement instanceof HTMLElement)document.activeElement.blur();window.scrollTo(0,0);});
    await p.screenshot({path:evidence('phase-08-live-providers.png'),fullPage:true});
    // Outputs are intentionally retained only as synthetic QA material, never ordinary logs.
    fs.writeFileSync(evidence('phase-08-live-providers.json'),JSON.stringify({checked_at:new Date().toISOString(),synthetic:true,provider_calls:true,
      capture_note:'sources/proposed_step precede sharing and approvals; final_step/final_sources follow the confirmed reservation',
      final_step:finalView.plan.find(x=>x.id===item.id),final_sources:finalView.evidence.filter(e=>item.evidence_refs.includes(e.id)),
      stt:'deepgram',model:understanding.provider,tts:'cartesia',duration_ms:Date.now()-started,sources:view.evidence.filter(e=>e.origin==='deepgram'),
      proposed_step:item,unanswered_priorities:view.priorities.filter(q=>q.selected&&q.status!=='answered').length,
      speech_receipt:speechReceipt,sandbox_action_receipt:action.receipt,
      audio_ingestion:await (await patient.request.get(base+'/call/diagnostics')).json(),
      physical_acoustics:false,human_acceptance:false},null,2)+'\n');
  }catch(error){
    fs.writeFileSync(evidence('phase-08-live-providers-failure.json'),JSON.stringify({checked_at:new Date().toISOString(),synthetic:true,
      status:'failed',view:await (await patient.request.get(base)).json(),speech:await speech(patient),
      understanding:await (await patient.request.get(base+'/understanding')).json()},null,2)+'\n');
    throw error;
  }finally{await finish(env);}
});
