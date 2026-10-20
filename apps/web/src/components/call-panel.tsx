'use client';
import {SpeechPanel} from './speech-panel';
import { useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Pause, Phone, PhoneOff, Play, ShieldCheck, Sparkles, Volume2, VolumeX } from 'lucide-react';
import { Room, RoomEvent, Track, createLocalAudioTrack, type LocalAudioTrack } from 'livekit-client';
import { RoomContext, RoomAudioRenderer, useParticipants } from '@livekit/components-react';
import type { components } from '../../../../packages/contracts/schema';
import { request, type Encounter, type Identity } from '@/lib/api/client';

type Call = components['schemas']['CallView'];
type Admission = components['schemas']['CallAdmission'];
const labels: Record<Call['state'],string> = {waiting:'Ready for your conversation',consent_needed:'Waiting for everyone’s agreement',active:'Vene processing is active',paused:'Vene processing is paused',stopping:'Stopping Vene processing…',unavailable:'Vene processing is unavailable',ended:'The call has ended'};

function People({ call }: {call: Call}) {
  const participants=useParticipants();
  return <div className="call-people">{participants.map(p=>{const assistant=p.identity.startsWith('vene:'); const server=call.participants.find(c=>'human:'+c.connection_id===p.identity);return <div key={p.identity} className={'call-person '+(assistant?'assistant':'')}><div className="person-orb">{assistant?<Sparkles size={25}/>:p.name?.split(' ').map(n=>n[0]).slice(0,2).join('')}</div><strong>{assistant?'Vene':p.name}</strong><span>{assistant ? call.state==='active'?'Listening with permission':'Disclosed assistant · paused' : server?.consent==='agreed'?'Agreed to Vene processing':server?.consent==='declined'?'Human conversation only':'Agreement needed'}</span></div>;})}</div>;
}

export function CallPanel({visit,viewer,compact=false}:{visit:Encounter;viewer:Identity;compact?:boolean}) {
  const [call,storeCall]=useState<Call|null>(null),[room,setRoom]=useState<Room|null>(null),[admission,setAdmission]=useState<Admission|null>(null);
  const [unsupportedBrowser,setUnsupportedBrowser]=useState(false);
  const [audioNeedsStart,setAudioNeedsStart]=useState(false),[receiving,setReceiving]=useState(false);
  const meterContext=useRef<AudioContext|null>(null),meterTimer=useRef<ReturnType<typeof setInterval>|null>(null);
  function stopMeter(){if(meterTimer.current)clearInterval(meterTimer.current);meterTimer.current=null;void meterContext.current?.close();meterContext.current=null;setReceiving(false);}
  function setCall(incoming:Call){storeCall(current=>!current||Date.parse(incoming.observed_at)>=Date.parse(current.observed_at)?incoming:current);}
  const [error,setError]=useState(''),[busy,setBusy]=useState(false),[mic,setMic]=useState(false);
  const [devices,setDevices]=useState<MediaDeviceInfo[]>([]),[device,setDevice]=useState(''),[level,setLevel]=useState<number|null>(null);
  const resource=useRef<Room|null>(null),preview=useRef<LocalAudioTrack|null>(null),intentional=useRef(false),alive=useRef(true);
  const base='/encounters/'+visit.id+'/call';
  useEffect(()=>{
    alive.current=true;setUnsupportedBrowser(typeof RTCPeerConnection!=='function'||!navigator.mediaDevices?.getUserMedia);const controller=new AbortController();let stopped=false;
    async function poll(){
      while(!stopped){try{const current=await request<Call>(base,{signal:controller.signal});if(alive.current)setCall(current);}catch{if(!controller.signal.aborted&&alive.current)setError('Call status is unavailable. Your saved visit remains here.');}await new Promise(r=>setTimeout(r,350));}
    }
    void poll();
    return()=>{stopped=true;alive.current=false;controller.abort();preview.current?.stop();intentional.current=true;void resource.current?.disconnect();resource.current=null;stopMeter();};
  },[base]);
  useEffect(()=>{
    if(!room||!call)return;
    for(const participant of room.remoteParticipants.values())if(participant.identity.startsWith('vene:'))participant.setVolume(call.output_silenced?0:1);
    if(admission&&(call.state==='ended'||call.generation!==admission.call.generation)){
      intentional.current=true;void room.disconnect();resource.current=null;setRoom(null);setAdmission(null);setMic(false);
      stopMeter();
    }
  },[room,call,admission]);
  async function deviceCheck(){
    setBusy(true);setError('');
    try{
      preview.current=await createLocalAudioTrack({deviceId:device||undefined});
      const list=await navigator.mediaDevices.enumerateDevices();setDevices(list.filter(d=>d.kind==='audioinput'));
      const audio=new AudioContext(),source=audio.createMediaStreamSource(new MediaStream([preview.current.mediaStreamTrack])),analyser=audio.createAnalyser();source.connect(analyser);
      const samples=new Uint8Array(analyser.frequencyBinCount);analyser.getByteTimeDomainData(samples);setLevel(Math.max(...samples.map(n=>Math.abs(n-128))));
      await audio.close();preview.current.stop();preview.current=null;
    }catch{setError('Microphone access is unavailable. You can retry device access or join without a microphone.');}
    finally{preview.current?.stop();preview.current=null;setBusy(false);}
  }
  async function join(withMic:boolean){
    if(busy)return;setBusy(true);setError('');intentional.current=false;
    let next:Room|null=null,details:Admission|null=null,joined=false;
    try{
      if(compact&&viewer.role==='patient'){
        await request('/encounters/'+visit.id+'/understanding/processing',{method:'POST',body:JSON.stringify({command_id:crypto.randomUUID(),enabled:true})});
        await request('/encounters/'+visit.id+'/feasibility/standing',{method:'POST',body:JSON.stringify({kinds:['scheduling']})});
        await request('/encounters/'+visit.id+'/speech/mode',{method:'POST',body:JSON.stringify({command_id:crypto.randomUUID(),mode:'on_request'})});
      }
      stopMeter();meterContext.current=new AudioContext();void meterContext.current.resume();
      next=new Room({adaptiveStream:true,dynacast:true,singlePeerConnection:true});resource.current=next;
      // Unlock playback in this click's user activation, before network awaits.
      void next.startAudio().then(()=>setAudioNeedsStart(false)).catch(()=>setAudioNeedsStart(true));
      // Device capture starts only after this user action. No audio pre-connect buffer.
      let track:LocalAudioTrack|null=null;
      if(withMic){track=await createLocalAudioTrack({deviceId:device||undefined});preview.current=track;}
      details=await request<Admission>(base+'/admit',{method:'POST'});
      const connectionLost=()=>{
        // Initial signaling retries are owned by the SDK's bounded connect
        // attempt. Only an admitted, displayed call needs the rejoin cleanup.
        if(!joined||!alive.current||intentional.current||resource.current!==next)return;
        intentional.current=true;resource.current=null;setRoom(null);setAdmission(null);setMic(false);
        stopMeter();
        setError('The call disconnected. Rejoin when you are ready; Vene will ask for agreement again.');
        void next?.disconnect().catch(()=>{});
        if(details)void request(base+'/connections/'+details.connection_id+'/leave',{method:'POST'}).catch(()=>{});
      };
      // Do not leave a silent, stale call on screen during the SDK's retry backoff.
      next.on(RoomEvent.Reconnecting,connectionLost);
      next.on(RoomEvent.SignalReconnecting,connectionLost);
      next.on(RoomEvent.TrackSubscribed,(track,_publication,participant)=>{
        if(resource.current!==next||!participant.identity.startsWith('vene:')||track.kind!==Track.Kind.Audio||!meterContext.current)return;
        if(meterTimer.current)clearInterval(meterTimer.current);
        const context=meterContext.current,source=context.createMediaStreamSource(new MediaStream([track.mediaStreamTrack]));
        const analyser=context.createAnalyser(),silent=context.createGain();silent.gain.value=0;
        source.connect(analyser);analyser.connect(silent);silent.connect(context.destination);
        const samples=new Float32Array(analyser.fftSize);
        meterTimer.current=setInterval(()=>{analyser.getFloatTimeDomainData(samples);let square=0;for(const sample of samples)square+=sample*sample;setReceiving(context.state==='running'&&Math.sqrt(square/samples.length)>.005);},20);
      });
      next.on(RoomEvent.Disconnected,()=>{if(alive.current&&resource.current===next){stopMeter();setRoom(null);setMic(false);setAdmission(null);if(!intentional.current)setError('The call disconnected. Rejoin when you are ready; Vene will ask for agreement again.');}});
      next.on(RoomEvent.MediaDevicesError,()=>setError('Your microphone disconnected. The conversation can continue while you reconnect it.'));
      next.on(RoomEvent.LocalTrackPublished,publication=>{
        if(publication.source!==Track.Source.Microphone||!publication.track)return;
        const track=publication.track;
        track.mediaStreamTrack.addEventListener('ended',()=>{
          if(alive.current&&!intentional.current){setMic(false);setError('Your microphone disconnected. Unmute to reconnect it, or continue without a microphone.');void next?.localParticipant.unpublishTrack(track);}
        },{once:true});
      });
      // Verify as soon as signaling registers this identity. Waiting until the
      // whole listen-only media connection finishes can depend on another
      // publisher becoming ready. The backend verifies real room presence.
      const pendingAdmission=details;
      let resolveVerification:(value:Call)=>void=()=>{},rejectVerification:(error:unknown)=>void=()=>{},verificationStarted=false;
      const verified=new Promise<Call>((resolve,reject)=>{resolveVerification=resolve;rejectVerification=reject;});
      const verify=()=>{if(verificationStarted)return;verificationStarted=true;void request<Call>(base+'/connections/'+pendingAdmission.connection_id+'/verify',{method:'POST'}).then(resolveVerification,rejectVerification);};
      next.on(RoomEvent.SignalConnected,verify);
      const connecting=next.connect(details.server_url,details.token).then(()=>verify());
      const [,verifiedCall]=await Promise.all([connecting,verified]);
      details.call=verifiedCall;
      setCall(details.call);
      for(let attempt=0;attempt<60&&!next.localParticipant.permissions?.canPublish;attempt++)await new Promise(r=>setTimeout(r,100));
      if(!next.localParticipant.permissions?.canPublish)throw new Error('Admission was not verified.');
      if(track){await next.localParticipant.publishTrack(track,{source:Track.Source.Microphone});preview.current=null;}
      joined=true;setMic(withMic);setAdmission(details);setCall(details.call);setRoom(next);
      if(compact){
        for(let i=0;i<40;i++){
          const current=await request<Call>(base),own=current.participants.find(p=>p.connection_id===pendingAdmission.connection_id);
          if(own?.present&&(!withMic||own.track_epoch>0))break;
          await new Promise(r=>setTimeout(r,100));
        }
        setCall(await request<Call>(base+'/consent',{method:'POST',body:JSON.stringify({command_id:crypto.randomUUID(),connection_id:details.connection_id,decision:'agreed',terms_version:'voice-processing-v1'})}));
        const speech=await request<components['schemas']['SpeechView']>('/encounters/'+visit.id+'/speech');
        if(speech.mode==='on_request')await request('/encounters/'+visit.id+'/speech/agreement',{method:'POST',body:JSON.stringify({command_id:crypto.randomUUID(),connection_id:details.connection_id,mode_revision:speech.mode_revision,agreed:true})});
      }
    }catch(error){
      const message=error instanceof Error?error.message.toLowerCase():'';
      const category=['admission was not verified','pc connection','signal','unauthorized','timeout','permission'].find(c=>message.includes(c))??'media';
      console.warn('Vene join status: '+category);
      intentional.current=true;await next?.disconnect();resource.current=null;preview.current?.stop();preview.current=null;
      if(details)await request(base+'/connections/'+details.connection_id+'/leave',{method:'POST'}).catch(()=>{});
      stopMeter();setError(withMic?'Could not join with this microphone. Check device access, retry, or join without it.':'The call service is unavailable. Retry when the connection is back.');
    }finally{setBusy(false);}
  }
  async function leave(){
    setBusy(true);intentional.current=true;
    try{await room?.disconnect();if(admission)setCall(await request<Call>(base+'/connections/'+admission.connection_id+'/leave',{method:'POST'}));}
    catch{setError('The call disconnected. Its processing permission will stop when the room detects the departure.');}
    finally{resource.current=null;setRoom(null);setAdmission(null);setMic(false);setBusy(false);stopMeter();}
  }
  async function agreement(decision:'agreed'|'declined'){
    if(!admission)return;setBusy(true);setError('');
    try{setCall(await request<Call>(base+'/consent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command_id:crypto.randomUUID(),connection_id:admission.connection_id,decision,terms_version:'voice-processing-v1'})}));}
    catch{setError('Could not save your agreement. Vene stays paused; please retry.');}finally{setBusy(false);}
  }
  async function control(type:'pause'|'resume'|'silence'|'end'){
    if(!call)return;setBusy(true);setError('');
    try{
      const reviewed=type==='end'?await request<Call>(base):call;
      if(reviewed.generation!==call.generation)throw new Error('The conversation changed.');
      setCall(await request<Call>(base+'/controls',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command_id:crypto.randomUUID(),expected_revision:reviewed.revision,type,...(type==='silence'?{silenced:!call.output_silenced}:{})})}));}
    catch{setError(type==='resume'?'Everyone in the room needs to agree, and the processing service must be ready. Please check the current call status.':'Could not confirm this control. Check the call status and retry.');}finally{setBusy(false);}
  }
  async function toggleMic(){
    if(!room)return;setBusy(true);
    try{await room.localParticipant.setMicrophoneEnabled(!mic,{deviceId:device||undefined});setMic(!mic);}
    catch{setError('Could not change the microphone. Check device access and retry.');}finally{setBusy(false);}
  }
  const own=call?.participants.find(p=>p.connection_id===admission?.connection_id);
  const allAgreed=Boolean(call?.participants.filter(p=>p.present).length&&call?.participants.filter(p=>p.present).every(p=>p.consent==='agreed'));
  if(compact)return <section className="demo-call" aria-label="Visit conversation">
    <span className={'demo-live-dot '+(call?.state==='active'?'active':'')}/><strong>{room?labels[call?.state??'waiting']:'Join this fictional conversation'}</strong>
    {!room?<><p>Audio can be processed into private notes. No recording. Vene may speak when {visit.patient.preferred_name} invites it. {viewer.role==='patient'?'I also allow private understanding and read-only scheduling checks.':''}</p>
      <button className="primary-button" disabled={busy} onClick={()=>void join(viewer.role==='clinician')}><Phone size={15}/>{busy?'Connecting…':'Join and agree'}</button></>:<><RoomContext.Provider value={room}><RoomAudioRenderer volume={viewer.role==='patient'?1:0}/></RoomContext.Provider>
      <div className="button-row">{viewer.role==='patient'&&call?.state!=='active'&&<button className="primary-button" disabled={busy||!allAgreed||!call?.worker_ready} onClick={()=>void control('resume')}><Play size={14}/>Start listening</button>}
      {call?.state==='active'&&<button className="small-button" disabled={busy} onClick={()=>void control('pause')}><Pause size={14}/>Pause</button>}
      {viewer.role==='clinician'&&<button className="small-button" disabled={busy} onClick={()=>void toggleMic()}>{mic?<MicOff size={14}/>:<Mic size={14}/>} {mic?'Mute microphone':'Unmute microphone'}</button>}
      <button className="source-link" onClick={()=>void agreement(own?.consent==='agreed'?'declined':'agreed')}>{own?.consent==='agreed'?'Withdraw agreement':'Agree again'}</button></div>
      <span data-vene-output-active={receiving?'true':'false'} className="demo-audio-status">{receiving?'Receiving Vene audio':allAgreed?call?.worker_ready?'Everyone agreed':'Waiting for voice service':'Waiting for everyone’s agreement'}</span></>}
    {error&&<p role="alert">{error}</p>}
  </section>;
  return <section className="card call-panel" aria-label="Visit conversation"><div className="call-heading"><div><div className="eyebrow small">BRING VENE INTO THE CONVERSATION</div><h2>{room?'Here, together.':'A place to talk it through.'}</h2></div><span className={'pill '+(call?.state==='active'?'call-live':'')}>{call?labels[call.state]:'Checking call availability…'}</span></div>
    {error&&<p className="call-error" role="alert" aria-label="Call error">{error}<button className="source-link" onClick={()=>setError('')}>Dismiss</button></p>}
    {room&&audioNeedsStart&&<button className="small-button" onClick={()=>{void room.startAudio().then(()=>setAudioNeedsStart(false)).catch(()=>setError('Audio playback is blocked. Check browser audio permission and retry.'));}}>Enable call audio</button>}
    {call?.gap_since&&<p className="soft-note" role="status">Vene processing was interrupted. Some words may be missing from these notes. Ask the speaker to repeat anything important.</p>}
    {!room&&unsupportedBrowser?<p role="status">Voice conversations are unavailable in this browser. You can still prepare questions and review your follow-up here.</p>:!room?<div className="prejoin-grid"><div><p>Join by voice with the people invited to your visit. Vene is a visible assistant; its processing starts only after everyone agrees.</p><div className="device-row"><label>Microphone<select value={device} onChange={e=>setDevice(e.target.value)}><option value="">Default microphone</option>{devices.map(d=><option key={d.deviceId} value={d.deviceId}>{d.label||'Microphone'}</option>)}</select></label><button className="small-button" disabled={busy} onClick={()=>void deviceCheck()}>Check microphone</button></div>{level!==null&&<p className="muted" role="status">Microphone opened successfully. Audio stayed on this device.</p>}<div className="button-row"><button className="primary-button" disabled={busy||call?.state==='unavailable'&&!call.generation.replaceAll('0','').replaceAll('-','')} onClick={()=>void join(true)}><Phone size={17}/>Join conversation</button><button className="source-link" disabled={busy} onClick={()=>void join(false)}>Join without a microphone</button></div></div><div className="call-privacy"><ShieldCheck size={25}/><h3>People first. Your choice.</h3><p>Your microphone can reach the humans in this room while Vene stays paused. Declining Vene processing keeps the human conversation available.</p></div></div>:<RoomContext.Provider value={room}><RoomAudioRenderer/><People call={call??admission!.call}/><div className="consent-box"><ShieldCheck size={22}/><div><h3>{own?.consent==='agreed'?'You agreed to Vene processing.':own?.consent==='declined'?'Human conversation only, for now.':'May Vene process your audio?'}</h3><p>Vene can process audio and keep attributed notes for {visit.patient.preferred_name}. Audio is not recorded. Notes and transcripts are not automatically shared with other participants. Pausing stops the processing path; muting a microphone or silencing Vene is separate.</p><div className="button-row"><button className="small-button" disabled={busy||own?.consent==='agreed'} onClick={()=>void agreement('agreed')}>{own?.consent==='agreed'?'Agreement saved':'Agree to Vene processing'}</button><button className="source-link" disabled={busy||own?.consent==='declined'} onClick={()=>void agreement('declined')}>{own?.consent==='agreed'?'Withdraw my agreement':'Keep this a human conversation'}</button></div></div></div><div className="call-controls"><button className="small-button" disabled={busy} onClick={()=>void toggleMic()}>{mic?<MicOff size={17}/>:<Mic size={17}/>} {mic?'Mute my microphone':'Unmute my microphone'}</button><button className="small-button" disabled={busy||call?.state!=='active'} onClick={()=>void control('pause')}><Pause size={17}/>Pause Vene processing</button>{viewer.role==='patient'&&<><button className="primary-button" disabled={busy||!allAgreed||!call?.worker_ready||call.state==='active'||call.state==='unavailable'} onClick={()=>void control('resume')}><Play size={17}/>Resume Vene processing</button><button className="small-button" disabled={busy} onClick={()=>void control('silence')}>{call?.output_silenced?<Volume2 size={17}/>:<VolumeX size={17}/>} {call?.output_silenced?'Allow Vene output':'Silence Vene output'}</button></>}<button className="leave-call" disabled={busy} onClick={()=>void leave()}><PhoneOff size={17}/>Leave conversation</button></div>{viewer.role==='patient'&&<button className="source-link" disabled={busy} onClick={()=>void control('end')}>End this conversation for everyone</button>}</RoomContext.Provider>}
    <SpeechPanel visit={visit} viewer={viewer} call={call} connected={!!room} receiving={receiving}/>
    <div className="call-foot"><ShieldCheck size={15}/><span>{call?.provider==='fixture'?'Local media preview · Synthetic audio transport checks · Speech recognition is not connected.':`Audio is processed live without recording. Transcripts remain private to ${visit.patient.preferred_name} until they choose to share them.`} Spoken contributions use separate agreement and current sharing.</span></div></section>;
}

