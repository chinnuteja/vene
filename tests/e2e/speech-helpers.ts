import {expect,chromium,type BrowserContext,type Page} from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import {base,launch,command,endCall} from './helpers';
const speechBase=base+'/speech';
const liveTts=process.env.BRING_VENE_TTS_LIVE_GATE==='true';
const artifact=(name:string)=>'docs/qa/phase-05-'+(liveTts?'live-tts-':'')+name;
export async function speech(context:BrowserContext){return (await context.request.get(speechBase)).json();}
export async function prepareQuestions(patient:BrowserContext,title?:string){
  const id='20000000-0000-4000-8000-000000000001';
  if(title)await command(patient,{type:'priority.edited',priority_id:id,title,detail:'Original fictional question for a local speech test.'});
  await command(patient,{type:'priority.selection_changed',priority_id:id,selected:true});
  await command(patient,{type:'sharing.changed',item_id:id,audiences:['clinician']});
  await command(patient,{type:'preparation.approved',approved:true});
}
export async function setMode(p:Page,d:Page){
  // A previous room can preserve its mode; a new patient session must explicitly
  // renew the grant and every participant's mode revision, rather than inherit it.
  await p.getByLabel('Vene participation mode',{exact:true}).selectOption('private');
  await expect(d.getByText('Maria chose: Private cues only.',{exact:true})).toBeVisible();
  await p.getByLabel('Vene participation mode',{exact:true}).selectOption('on_request');
  await expect(d.getByRole('button',{name:'Allow Vene to speak',exact:true})).toBeVisible();
  await p.getByRole('button',{name:'Allow Vene to speak',exact:true}).click();
  await d.getByRole('button',{name:'Allow Vene to speak',exact:true}).click();
}
export async function setup(baseURL:string|undefined){
  const patientBrowser=await chromium.launch({channel:'chromium',args:['--allow-loopback-in-peer-connection','--disable-features=WebRtcHideLocalIpsWithMdns','--autoplay-policy=no-user-gesture-required']});
  const doctorBrowser=await chromium.launch({channel:'chromium',args:['--allow-loopback-in-peer-connection','--disable-features=WebRtcHideLocalIpsWithMdns','--autoplay-policy=no-user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+path.resolve(process.env.BRING_VENE_LIVE_PROVIDER_GATE==='true'?'fixtures/audio/live-clinician.wav':'fixtures/audio/clinician.wav')]});
  const patient=await patientBrowser.newContext({baseURL}),doctor=await doctorBrowser.newContext({baseURL,permissions:['microphone']});
  for(const context of [patient,doctor])await context.addInitScript(()=>{
    const Native=window.RTCPeerConnection,peers:RTCPeerConnection[]=[],events:unknown[]=[];
    const last=new Map<RTCPeerConnection,unknown[]>();
    const capture=async(pc:RTCPeerConnection)=>{
      const stats=await pc.getStats(),selected:unknown[]=[];
      stats.forEach(s=>{
        if(s.type==='candidate-pair')selected.push({type:s.type,state:s.state,nominated:s.nominated,requestsSent:s.requestsSent,responsesReceived:s.responsesReceived,bytesReceived:s.bytesReceived});
        if(s.type==='local-candidate'||s.type==='remote-candidate')selected.push({type:s.type,candidateType:s.candidateType,protocol:s.protocol,loopback:s.address==='127.0.0.1'});
      });
      if(selected.length)last.set(pc,selected);
    };
    window.RTCPeerConnection=class extends Native{
      constructor(config?:RTCConfiguration){super(config);peers.push(this);
        this.addEventListener('iceconnectionstatechange',()=>{events.push({at:Date.now(),ice:this.iceConnectionState,connection:this.connectionState,signaling:this.signalingState});void capture(this);});
        const timer=setInterval(()=>{if(this.connectionState==='closed'||this.connectionState==='connected'){clearInterval(timer);return;}void capture(this);},500);
      }
    };
    (window as unknown as {veneRtcDiagnostics:()=>Promise<unknown>}).veneRtcDiagnostics=async()=>({events,peers:await Promise.all(peers.map(async pc=>{
      await capture(pc);return {connection:pc.connectionState,ice:pc.iceConnectionState,signaling:pc.signalingState,policy:pc.getConfiguration().iceTransportPolicy,pairs:last.get(pc)??[]};
    }))});
  });
  try{
  await launch(patient);await launch(doctor,'clinician');await prepareQuestions(patient);
  const p=await patient.newPage(),d=await doctor.newPage();
  await d.addInitScript(()=>{
    const capture=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    navigator.mediaDevices.getUserMedia=constraints=>capture({...constraints,audio:typeof constraints.audio==='object'?{...constraints.audio,echoCancellation:false,noiseSuppression:false,autoGainControl:false}:constraints.audio});
  });
  for(const page of [p,d])page.on('console',message=>{if(message.text().startsWith('Vene join status: '))console.log(message.text());});
  await p.addInitScript(()=>{
    (window as unknown as {lastVeneAudio:number}).lastVeneAudio=0;
    setInterval(()=>{if(document.querySelector('[data-vene-output-active="true"]'))(window as unknown as {lastVeneAudio:number}).lastVeneAudio=Date.now();},20);
  });
  await Promise.all([p.goto('/visit'),d.goto('/visit')]);
  await expect(p.getByRole('button',{name:'Join without a microphone',exact:true})).toBeVisible();
  await expect(d.getByRole('button',{name:'Join conversation',exact:true})).toBeVisible();
  await p.getByRole('button',{name:'Join without a microphone',exact:true}).click();
  await expect(p.getByRole('button',{name:'Agree to Vene processing',exact:true})).toBeVisible({timeout:30000});
  await d.getByRole('button',{name:'Join conversation',exact:true}).click();
  await expect(d.getByRole('button',{name:'Mute my microphone',exact:true})).toBeVisible({timeout:30000});
  await d.getByRole('button',{name:'Mute my microphone',exact:true}).click();
  await expect.poll(async()=>{
    const call=await (await patient.request.get(base+'/call',{maxRetries:2})).json();
    return call.participants.filter((c:{present:boolean})=>c.present).length===2&&
      call.participants.some((c:{role:string;present:boolean;track_epoch:number})=>c.role==='clinician'&&c.present&&c.track_epoch>0);
  },{timeout:30000}).toBe(true);
  await p.getByRole('button',{name:'Agree to Vene processing',exact:true}).click();
  await d.getByRole('button',{name:'Agree to Vene processing',exact:true}).click();
  await p.getByRole('button',{name:'Resume Vene processing',exact:true}).click();
  await expect.poll(async()=>(await (await patient.request.get(base+'/call',{maxRetries:2})).json()).state).toBe('active');
  // An earlier room may preserve Maria's deliberate output-silence preference.
  // Speaking mode never overrides it: this test explicitly allows audio again.
  if((await (await patient.request.get(base+'/call',{maxRetries:2})).json()).output_silenced){
    await p.getByRole('button',{name:'Allow Vene output',exact:true}).click();
    await expect.poll(async()=>(await (await patient.request.get(base+'/call',{maxRetries:2})).json()).output_silenced).toBe(false);
  }
  await setMode(p,d);
  await expect.poll(async()=>{const state=await speech(patient);return state.consents.length===2&&state.consents.every((c:{agreed:boolean})=>c.agreed);}).toBe(true);
  return {patientBrowser,doctorBrowser,patient,doctor,p,d};
  }catch(error){
    try{
      const collect=async(context:BrowserContext)=>Promise.all(context.pages().map(page=>page.evaluate(async()=>
        (window as unknown as {veneRtcDiagnostics?:()=>Promise<unknown>}).veneRtcDiagnostics?.()).catch(()=>null)));
      fs.writeFileSync('docs/qa/phase-08-media-join-failure.json',JSON.stringify({checked_at:new Date().toISOString(),synthetic:true,
        patient:await collect(patient),doctor:await collect(doctor),
        call:await (await patient.request.get(base+'/call')).json(),sdp_or_credentials_saved:false},null,2)+'\n');
    }catch{console.warn('Synthetic media diagnostics could not be saved.');}
    finally{try{await endCall(patient);}finally{await Promise.all([patientBrowser.close(),doctorBrowser.close()]);}}
    throw error;}
}
export async function finish(env:Awaited<ReturnType<typeof setup>>){
  try{await env.p.getByRole('button',{name:'End this conversation for everyone',exact:true}).click();await expect.poll(async()=>(await (await env.patient.request.get(base+'/call',{maxRetries:2})).json()).state).toBe('ended');}finally{await Promise.all([env.patientBrowser.close(),env.doctorBrowser.close()]);}
}

