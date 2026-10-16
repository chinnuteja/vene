import {evidence,chromiumLaunch} from './platform';
import {test,expect,chromium,type BrowserContext} from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import {execFileSync,spawn} from 'node:child_process';
import {base,launch,endCall} from './helpers';
const callBase=base+'/call';
async function state(context:BrowserContext){return (await context.request.get(callBase,{maxRetries:2})).json();}
async function diagnostic(context:BrowserContext){return (await context.request.get(callBase+'/diagnostics')).json();}
test('real WebRTC tracks, consent, pause, late arrival and reconnect preserve attribution',async({baseURL})=>{
  test.setTimeout(240000);
  const browsers=await Promise.all(['patient','clinician'].map(person=>chromium.launch({...chromiumLaunch(),args:['--allow-loopback-in-peer-connection','--disable-features=WebRtcHideLocalIpsWithMdns','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+path.resolve('fixtures/audio/'+person+'.wav')]})));
  const patient=await browsers[0].newContext({baseURL,permissions:['microphone']}),doctor=await browsers[1].newContext({baseURL,permissions:['microphone']}),family=await browsers[1].newContext({baseURL,permissions:['microphone']});
  // Original transport tones are not speech. Disable browser speech DSP only
  // for this controlled fixture so sustained tones remain observable.
  for(const context of [patient,doctor,family])await context.addInitScript(()=>{
    const capture=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    navigator.mediaDevices.getUserMedia=constraints=>capture({...constraints,audio:constraints.audio?{...(typeof constraints.audio==='object'?constraints.audio:{}),echoCancellation:false,noiseSuppression:false,autoGainControl:false}:false});
  });
  const runtimeErrors:string[]=[];
  try{
    await launch(patient);await launch(doctor,'clinician');await launch(family,'family');
    const p=await patient.newPage(),d=await doctor.newPage(),f=await family.newPage();
    for(const page of [p,d,f]){page.on('pageerror',error=>runtimeErrors.push(error.message));page.on('console',message=>{if(message.text().startsWith('Vene join status: '))console.log(message.text());});}
    await Promise.all([p.goto('/visit'),d.goto('/visit')]);
    await p.getByRole('button',{name:'Join conversation',exact:true}).click();
    await expect(p.getByRole('heading',{name:'May Vene process your audio?'})).toBeVisible();
    const humanGeneration=(await state(patient)).generation;
    await d.getByRole('button',{name:'Join conversation',exact:true}).click();
    expect((await state(patient)).generation).toBe(humanGeneration);
    await expect(p.getByRole('heading',{name:'May Vene process your audio?'})).toBeVisible();
    await expect.poll(async()=>{const s=await state(patient);return s.participants.filter(x=>x.present&&x.track_epoch>0).length;}).toBe(2);
    await expect(p.getByText('Vene',{exact:true})).toBeVisible();
    const before=await diagnostic(patient);expect(before.receipts).toHaveLength(0);
    await p.getByRole('button',{name:'Agree to Vene processing',exact:true}).click();
    await d.getByRole('button',{name:'Keep this a human conversation',exact:true}).click();
    await expect.poll(async()=>{const s=await state(patient);return s.participants.some(x=>x.consent==='declined');}).toBe(true);
    await expect(p.getByRole('button',{name:'Resume Vene processing',exact:true})).toBeDisabled();
    expect((await diagnostic(patient)).receipts).toHaveLength(0);
    await d.getByRole('button',{name:'Agree to Vene processing',exact:true}).click();
    await expect(p.getByRole('button',{name:'Resume Vene processing',exact:true})).toBeEnabled();
    await p.getByRole('button',{name:'Resume Vene processing',exact:true}).click();
    await expect.poll(async()=>{const evidence=await diagnostic(patient);return evidence.receipts.filter(x=>x.non_silent_frames>3).length;}).toBe(2);
    const received=await diagnostic(patient),members=await state(patient);
    expect(new Set(received.receipts.map(x=>x.connection_id)).size).toBe(2);
    expect(new Set(received.receipts.map(x=>x.track_sid)).size).toBe(2);
    const times=received.receipts.map(x=>[new Date(x.first_received_at).getTime(),new Date(x.last_received_at).getTime()]);
    expect(Math.max(...times.map(x=>x[0]))).toBeLessThan(Math.min(...times.map(x=>x[1])));
    expect((await doctor.request.get(callBase+'/utterances')).status()).toBe(403);
    expect(await (await patient.request.get(callBase+'/utterances')).json()).toEqual([]);
    await p.getByRole('button',{name:'Silence Vene output',exact:true}).click();
    await expect(p.getByRole('button',{name:'Allow Vene output',exact:true})).toBeEnabled();
    expect((await state(patient)).manual_pause).toBe(false);
    await p.getByRole('button',{name:'Pause Vene processing',exact:true}).click();
    await expect.poll(async()=>({state:(await state(patient)).state,tasks:(await diagnostic(patient)).active_tasks})).toEqual({state:'paused',tasks:0});
    const stopped=await diagnostic(patient);const count=stopped.receipts.reduce((n,x)=>n+x.frames,0);
    await expect.poll(async()=>{await new Promise(r=>setTimeout(r,500));return (await diagnostic(patient)).receipts.reduce((n,x)=>n+x.frames,0);}).toBe(count);
    await expect(p.getByRole('button',{name:'Mute my microphone',exact:true})).toBeEnabled();
    expect((await state(patient)).participants.filter(x=>x.present)).toHaveLength(2);
    await p.getByRole('button',{name:'Resume Vene processing',exact:true}).click();
    await expect.poll(async()=>(await state(patient)).state).toBe('active');
    await f.goto('/visit');await f.getByRole('button',{name:'Join without a microphone',exact:true}).click();
    await expect.poll(async()=>{const s=await state(patient);return s.participants.filter(x=>x.present).length===3&&s.manual_pause;}).toBe(true);
    await expect.poll(async()=>(await diagnostic(patient)).active_tasks).toBe(0);
    const lateCount=(await diagnostic(patient)).receipts.reduce((n,x)=>n+x.frames,0);
    await f.getByRole('button',{name:'Keep this a human conversation',exact:true}).click();
    await expect(p.getByRole('button',{name:'Resume Vene processing',exact:true})).toBeDisabled();
    expect((await diagnostic(patient)).receipts.reduce((n,x)=>n+x.frames,0)).toBe(lateCount);
    await f.getByRole('button',{name:'Leave conversation',exact:true}).click();
    await d.getByRole('button',{name:'Leave conversation',exact:true}).click();
    await d.getByRole('button',{name:'Join conversation',exact:true}).click();
    await expect.poll(async()=>{const s=await state(patient);return s.participants.some(x=>x.role==='clinician'&&x.present&&x.track_epoch>0&&x.consent==='pending');}).toBe(true);
    const rejoined=await state(doctor);
    expect(rejoined.own_connection_id).not.toBe(members.participants.find(x=>x.role==='clinician').connection_id);
    await d.getByRole('button',{name:'Agree to Vene processing',exact:true}).click();
    await expect(p.getByRole('button',{name:'Resume Vene processing',exact:true})).toBeEnabled();
    await p.getByRole('button',{name:'Resume Vene processing',exact:true}).click();
    await expect.poll(async()=>(await diagnostic(patient)).receipts.filter(x=>x.connection_id===rejoined.own_connection_id&&x.non_silent_frames>2).length).toBe(1);
    
    await p.evaluate(()=>window.scrollTo(0,0));await p.screenshot({path:evidence('phase-03-call-desktop.png'),fullPage:true});
    await p.setViewportSize({width:390,height:844});expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await p.screenshot({path:evidence('phase-03-call-mobile.png'),fullPage:true});
    await p.getByRole('button',{name:'Pause Vene processing',exact:true}).click();
    await expect.poll(async()=>({state:(await state(patient)).state,tasks:(await diagnostic(patient)).active_tasks})).toEqual({state:'paused',tasks:0});
    await expect(p.locator('.call-heading')).toContainText('Vene processing is paused');
    await p.evaluate(()=>window.scrollTo(0,0));
    await p.screenshot({path:evidence('phase-03-paused.png'),fullPage:true});
    const final=await diagnostic(patient);
    expect(runtimeErrors).toEqual([]);
    fs.writeFileSync(evidence('phase-03-media-report.json'),JSON.stringify({checked_at:new Date().toISOString(),transport:'real local LiveKit/WebRTC',input:'two original tone WAVs',initial_source_count:2,overlapping_frame_windows:true,before_consent_frames:0,after_acknowledged_pause_frames:0,late_arrival:'pauses processing',reconnect:'fresh connection and track epoch',active_tasks_after_pause:final.active_tasks,runtime_errors:runtimeErrors,live_stt_accuracy:'not tested',physical_microphone:'not tested'},null,2)+'\n');
    await p.getByRole('button',{name:'End this conversation for everyone',exact:true}).click();
  }finally{try{await endCall(patient);}finally{await Promise.all(browsers.map(b=>b.close()));}}
});

test('microphone denial allows a human call without publishing audio',async({baseURL})=>{
  const browser=await chromium.launch({...chromiumLaunch(),args:['--allow-loopback-in-peer-connection','--disable-features=WebRtcHideLocalIpsWithMdns','--deny-permission-prompts','--use-fake-device-for-media-stream']});
  try{
    const context=await browser.newContext({baseURL});await launch(context);const page=await context.newPage();await page.goto('/visit');
    await page.getByRole('button',{name:'Check microphone',exact:true}).click();
    await expect(page.getByRole('alert',{name:'Call error'})).toContainText('Microphone access is unavailable');
    await page.getByRole('button',{name:'Join without a microphone',exact:true}).click();
    await expect(page.getByRole('button',{name:'Unmute my microphone',exact:true})).toBeVisible();
    await expect(page.getByRole('heading',{name:'May Vene process your audio?'})).toBeVisible();
    const own=(await state(context)).own_connection_id;
    expect((await diagnostic(context)).receipts.filter(r=>r.connection_id===own)).toHaveLength(0);
    await page.screenshot({path:evidence('phase-03-microphone-denied.png'),fullPage:true});
    await page.getByRole('button',{name:'End this conversation for everyone',exact:true}).click();
  }finally{await browser.close();}
});

test('device loss pauses processing and a replacement track requires consent again',async({baseURL})=>{
  test.setTimeout(120000);
  const browser=await chromium.launch({...chromiumLaunch(),args:['--allow-loopback-in-peer-connection','--disable-features=WebRtcHideLocalIpsWithMdns','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+path.resolve('fixtures/audio/patient.wav')]});
  const context=await browser.newContext({baseURL,permissions:['microphone']});
  try{
    await launch(context);const page=await context.newPage();
    await page.addInitScript(()=>{const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);(window as unknown as {testStreams:MediaStream[]}).testStreams=[];navigator.mediaDevices.getUserMedia=async c=>{const stream=await original(c);(window as unknown as {testStreams:MediaStream[]}).testStreams.push(stream);return stream;};});
    await page.goto('/visit');await page.getByRole('button',{name:'Join conversation',exact:true}).click();
    await expect.poll(async()=>(await state(context)).participants.filter(x=>x.present&&x.track_epoch>0).length,{timeout:30000}).toBe(1);
    await page.getByRole('button',{name:'Agree to Vene processing',exact:true}).click();
    await page.getByRole('button',{name:'Resume Vene processing',exact:true}).click();
    await expect.poll(async()=>(await state(context)).state).toBe('active');
    const before=await state(context),epoch=before.participants[0].track_epoch;
    await page.evaluate(()=>{for(const stream of (window as unknown as {testStreams:MediaStream[]}).testStreams)for(const track of stream.getAudioTracks())track.stop();});
    // stop() does not emit the browser's hardware-ended event; dispatch that real track event.
    await page.evaluate(()=>{for(const stream of (window as unknown as {testStreams:MediaStream[]}).testStreams)for(const track of stream.getAudioTracks())track.dispatchEvent(new Event('ended'));});
    await expect(page.getByRole('alert',{name:'Call error'})).toContainText('microphone disconnected');
    await page.getByRole('button',{name:'Unmute my microphone',exact:true}).click();
    await expect.poll(async()=>{const s=await state(context);return s.participants.some(x=>x.track_epoch>epoch&&x.consent==='pending')&&s.manual_pause;}).toBe(true);
    await expect.poll(async()=>(await diagnostic(context)).active_tasks).toBe(0);
    await expect(page.getByRole('heading',{name:'May Vene process your audio?'})).toBeVisible();
    await page.getByRole('button',{name:'End this conversation for everyone',exact:true}).click();
  }finally{try{await endCall(context);}finally{await browser.close();}}
});

