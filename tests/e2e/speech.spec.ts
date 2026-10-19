import {evidence} from './platform';
import {test,expect,chromium,type BrowserContext,type Page} from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import {base,launch,command} from './helpers';
import {speech,prepareQuestions,setup,finish} from './speech-helpers';
const speechBase=base+'/speech';
const liveTts=process.env.BRING_VENE_TTS_LIVE_GATE==='true';
const artifact=(name:string)=>evidence('phase-05-')+(liveTts?'live-tts-':'')+name;
test('coordinated speech is private until approved, plays real audio and yields to a human',async({baseURL})=>{
  test.setTimeout(240000);const env=await setup(baseURL);const {p,d,patient,doctor}=env;
  try{
    await p.getByRole('button',{name:'Help me keep track',exact:true}).click();
    await expect.poll(async()=>(await speech(patient)).cues.length).toBeGreaterThan(0);
    expect((await speech(doctor)).cues).toEqual([]);
    await expect(d.locator('.private-cue')).toHaveCount(0);
    const evidenceBefore=(await (await patient.request.get(base)).json()).evidence.length;
    const cue=p.locator('.private-cue').filter({hasText:'What is holding up my referral?'});
    await expect.poll(async()=>(await speech(patient)).cues.find((c:{title:string})=>c.title==='What is holding up my referral?')?.blocked_reason).toBe('');
    await expect(cue.getByRole('button',{name:'Ask Vene to say this aloud',exact:true})).toBeEnabled();
    await p.evaluate(()=>window.scrollTo(0,0));await p.screenshot({path:artifact('private-cue.png'),fullPage:true});
    await cue.getByRole('button',{name:'Ask Vene to say this aloud',exact:true}).click();
    await expect(p.locator('[data-vene-output-active="true"]')).toBeVisible({timeout:25000});
    await expect(d.locator('[data-vene-output-active="true"]')).toBeVisible();
    await expect.poll(async()=>(await speech(patient)).receipts[0]?.state,{timeout:20000}).toBe('completed');
    const first=(await speech(patient)).receipts[0];expect(first.played_ms).toBeGreaterThan(1000);expect(first.played_text).toContain('What is holding up my referral?');expect(first.hearing_confirmed).toBe(false);
    expect((await (await patient.request.get(base)).json()).evidence.length).toBe(evidenceBefore);
    // A fresh context lets us test a different approved contribution after cooldown.
    await prepareQuestions(patient,'Who will arrange the next referral step?');
    await expect.poll(async()=>Date.now()-Date.parse((await speech(patient)).receipts[0].stopped_at),{timeout:15000}).toBeGreaterThan(10100);
    await p.getByRole('button',{name:'Help me keep track',exact:true}).click();
    await p.locator('.private-cue').filter({hasText:'Who will arrange the next referral step?'}).getByRole('button',{name:'Ask Vene to say this aloud',exact:true}).click();
    await expect(p.locator('[data-vene-output-active="true"]')).toBeVisible({timeout:20000});
    await d.getByRole('button',{name:'Unmute my microphone',exact:true}).click();
    await expect.poll(async()=>(await speech(patient)).receipts[0]?.state).toBe('interrupted');
    await expect(p.locator('[data-vene-output-active="false"]')).toBeVisible();
    const interrupted=(await speech(patient)).receipts[0];expect(interrupted.played_text).toBeNull();expect(interrupted.reason).toBe('human_interruption');
    await d.getByRole('button',{name:'Mute my microphone',exact:true}).click();
    await p.getByRole('button',{name:'Pause Vene processing',exact:true}).click();
    await expect.poll(async()=>(await (await patient.request.get(base+'/call',{maxRetries:2})).json()).state).toBe('paused');
    await p.setViewportSize({width:390,height:844});await p.evaluate(()=>window.scrollTo(0,0));
    expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await p.screenshot({path:artifact('paused-mobile.png'),fullPage:true});
    const provider=(await speech(patient)).provider;expect(provider).toBe(liveTts?'cartesia':'fixture');
    fs.writeFileSync(artifact('browser-report.json'),JSON.stringify({checked_at:new Date().toISOString(),transport:'real local WebRTC',voice:liveTts?'Live Cartesia; original synthetic text; no audio files':'Windows offline speech; no audio files',private_cues:'absent from guest API and UI',completed_playout_ms:first.played_ms,self_transcription_sources:0,human_interruption:interrupted.reason,interrupted_full_text_saved:false,pause:'acknowledged',physical_acoustics:'not tested',live_tts:liveTts?'exercised':'not tested',live_stt_model:'not tested'},null,2)+'\n');
  }finally{await finish(env);}
});

test('speech latency measured through real decoded audio over twenty controlled trials',async({baseURL})=>{
  test.skip(process.env.BRING_VENE_SPEECH_MEASURE!=='true','Run the explicit speech measurement gate.');
  test.setTimeout(600000);const env=await setup(baseURL);const {p,d,patient}=env;const samples=[];
  try{
    const title='Could we clarify who arranges this next step, when it should happen, where I need to go, and what we are still waiting for?';
    await prepareQuestions(patient,title);
    for(let index=0;index<20;index++){
      // Real microphone energy then silence: includes a quiet-gap floor wait, not STT.
      const energy=async()=>{const state=await (await patient.request.get(base+'/call/diagnostics')).json();return state.receipts.reduce((sum:number,x:{non_silent_frames:number})=>sum+x.non_silent_frames,0);};
      const baseline=await energy();
      await d.getByRole('button',{name:'Unmute my microphone',exact:true}).click();
      await expect.poll(energy).toBeGreaterThan(baseline+3);
      await d.getByRole('button',{name:'Mute my microphone',exact:true}).click();
      await p.getByRole('button',{name:'Help me keep track',exact:true}).click();
      const cue=p.locator('.private-cue').filter({hasText:title});
      await expect(cue.getByRole('button',{name:'Ask Vene to say this aloud',exact:true})).toBeEnabled();
      await cue.getByRole('button',{name:'Ask Vene to say this aloud',exact:true}).scrollIntoViewIfNeeded();
      // Position the remote control before timing starts. Scrolling another
      // window must not consume a short contribution's interruption window.
      await d.getByRole('button',{name:'Unmute my microphone',exact:true}).scrollIntoViewIfNeeded();
      await p.evaluate(()=>(window as unknown as {firstVeneAudio:number}).firstVeneAudio=0);
      const requestedAt=Date.now();await cue.getByRole('button',{name:'Ask Vene to say this aloud',exact:true}).click();
      await expect(p.locator('[data-vene-output-active="true"]')).toBeVisible({timeout:20000});
      const assertedAt=Date.now();
      await expect.poll(()=>p.evaluate(()=>(window as unknown as {firstVeneAudio:number}).firstVeneAudio),{intervals:[20]}).toBeGreaterThan(0);
      const receivedAt=await p.evaluate(()=>(window as unknown as {firstVeneAudio:number}).firstVeneAudio);
      expect(receivedAt).toBeGreaterThanOrEqual(requestedAt);
      expect((await speech(patient)).receipts[0]?.state).toBe('speaking');
      await d.getByRole('button',{name:'Unmute my microphone',exact:true}).click();
      await expect.poll(async()=>(await speech(patient)).receipts[0]?.state).toBe('interrupted');
      await expect.poll(async()=>p.evaluate(()=>Date.now()-(window as unknown as {lastVeneAudio:number}).lastVeneAudio)).toBeGreaterThan(250);
      const lastAudio=await p.evaluate(()=>(window as unknown as {lastVeneAudio:number}).lastVeneAudio);
      const receipt=(await speech(patient)).receipts[0];
      expect(receipt.stop_detected_at).toBeTruthy();expect(receipt.reason).toBe('human_interruption');
      samples.push({trial:index+1,approval_to_received_audio_ms:receivedAt-requestedAt,approval_to_asserted_audio_ms:assertedAt-requestedAt,
        publisher_end_of_input_to_audio_ms:receipt.end_of_input_to_audio_ms,
        stop_detection_to_last_received_audio_ms:Math.max(0,lastAudio-Date.parse(receipt.stop_detected_at)),
        recognition_delay_ms:null});
      fs.writeFileSync(artifact('latency-partial.json'),JSON.stringify({completed_samples:samples.length,target_samples:20,complete:false,trials:samples},null,2)+'\n');
      console.log('Speech timing sample '+samples.length+'/20 recorded.');
      await d.getByRole('button',{name:'Mute my microphone',exact:true}).click();
    }
    const percentile=(values:number[])=>[...values].sort((a,b)=>a-b)[Math.ceil(values.length*.95)-1];
    expect((await speech(patient)).provider).toBe(liveTts?'cartesia':'fixture');
    fs.writeFileSync(artifact('latency.json'),JSON.stringify({checked_at:new Date().toISOString(),samples:20,conditions:{transport:'local LiveKit loopback; two isolated Chromium instances with local-network permission',tts:liveTts?'Live Cartesia; original synthetic text':'Windows offline voice',question_text:title,actuation:'Remote unmute control positioned before approval; receipt must still be speaking at interruption request',human_input:'original tone WAV; three accepted 20 ms activity windows within authorized 100 ms input batches',quiet_seconds:.7,cooldown_seconds:.2,physical_microphone:false,recognition:'not exercised',receiver_observation:'20 ms sampler of decoded-audio RMS UI signal; first timestamp and later Playwright assertion retained separately'},trials:samples,p95:{approval_to_received_audio_ms:percentile(samples.map(s=>s.approval_to_received_audio_ms)),approval_to_asserted_audio_ms:percentile(samples.map(s=>s.approval_to_asserted_audio_ms)),publisher_end_of_input_to_audio_ms:percentile(samples.map(s=>s.publisher_end_of_input_to_audio_ms)),stop_detection_to_last_received_audio_ms:percentile(samples.map(s=>s.stop_detection_to_last_received_audio_ms))},clinical_standard:false,targets:{approval_to_received_audio_ms:2000,stop_detection_to_last_received_audio_ms:500}},null,2)+'\n');
    expect(percentile(samples.map(s=>s.approval_to_received_audio_ms))).toBeLessThan(2000);
    expect(percentile(samples.map(s=>s.stop_detection_to_last_received_audio_ms))).toBeLessThan(500);
  }finally{await finish(env);}
});
