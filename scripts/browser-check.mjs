import {pipeOwnedOutput} from './child-logs.mjs';
import {venvPython,livekitBinary} from './platform.mjs';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import net from 'node:net';
import path from 'node:path';
import {randomBytes} from 'node:crypto';
import http from 'node:http';
import {timingSafeEqual} from 'node:crypto';
const root = process.cwd();
const runtime = JSON.parse(fs.readFileSync('.local/runtime.json', 'utf8').replace(/^\uFEFF/, ''));
async function freePort() { return new Promise((resolve, reject) => {
  const probe = net.createServer(); probe.on('error', reject);
  probe.listen(0, '127.0.0.1', () => { const port = probe.address().port; probe.close(() => resolve(port)); });
}); }
const port = await freePort(), apiPort = await freePort();
const mediaPort=await freePort(),mediaTcp=await freePort(),mediaUdp=await freePort();
const mediaTurn=await freePort();
const officePort=await freePort();
const env = { ...process.env, NEXT_DIST_DIR: process.env.NEXT_DIST_DIR ?? '.next', NEXT_TELEMETRY_DISABLED: '1', DATABASE_URL: runtime.test_database_url, BRING_VENE_MODE:'fixture', VOICE_PROVIDER:'fixture', LIVEKIT_URL:'ws://127.0.0.1:'+mediaPort,LIVEKIT_API_KEY:runtime.livekit_key,LIVEKIT_API_SECRET:runtime.livekit_secret, BRING_VENE_DEVELOPMENT:'true', COOKIE_SECURE:'false', BACKEND_URL: 'http://127.0.0.1:' + apiPort, BRING_VENE_BASE_URL: 'http://127.0.0.1:' + port, BRING_VENE_BROWSER_TEST:'true' };
if(fs.existsSync('.local/chromium.json'))env.BRING_VENE_CHROMIUM_PATH=JSON.parse(fs.readFileSync('.local/chromium.json','utf8')).executable;
env.BRING_VENE_EVIDENCE_DIR??=path.join(root,'.local/evidence');
if(!runtime.livekit_key||!runtime.livekit_secret)throw new Error('Run setup-media.ps1 before media browser checks.');
const python=venvPython(root);
const allLive=process.env.BRING_VENE_LIVE_PROVIDER_GATE==='true';
if(allLive){const configured=spawnSync(python,['scripts/live-config-check.py'],{cwd:root,env,windowsHide:true,stdio:'inherit'});if(configured.status!==0)throw new Error('Live-provider gate not configured. No reset or scripted fallback was started.');}
env.VOICE_PROVIDER=allLive?'deepgram':'fixture';
env.OFFICE_URL='http://127.0.0.1:'+officePort;env.OFFICE_TOKEN=randomBytes(32).toString('hex');
env.OFFICE_CALLBACK_SECRET=randomBytes(32).toString('hex');env.OFFICE_CALLBACK_URL=env.BACKEND_URL+'/integrations/office/results';
env.TTS_PROVIDER=allLive||process.env.BRING_VENE_TTS_LIVE_GATE==='true'?'cartesia':'fixture';
if(env.TTS_PROVIDER==='cartesia'){
  const configured=spawnSync(python,['-c','from bring_vene.config import Settings; import sys; s=Settings(); sys.exit(0 if s.cartesia_api_key and s.cartesia_voice_id else 1)'],{cwd:root,env,windowsHide:true,stdio:'ignore'});
  if(configured.status!==0)throw new Error('Live speech gate needs CARTESIA_API_KEY and CARTESIA_VOICE_ID. No database reset, provider call or offline fallback was started.');
}
// The dedicated measurement run uses a shorter cooldown for repeated trials.
if(process.env.BRING_VENE_SPEECH_MEASURE==='true')env.SPEECH_COOLDOWN_SECONDS='.2';
const reset=spawnSync(python,[path.join(root,'scripts/reset-browser-fixture.py')],{cwd:root,env,windowsHide:true,stdio:'inherit'});
if(reset.status!==0)throw new Error('Could not prepare the isolated browser test fixture.');
const officeInit=spawnSync(python,['-c','from bring_vene.execution.office import initialize; from bring_vene.config import Settings; from bring_vene.persistence.database import make_engine; initialize(make_engine(Settings().database_url))'],{cwd:root,env,windowsHide:true,stdio:'inherit'});
if(officeInit.status!==0)throw new Error('Sandbox office initialization failed.');
const officeLog=fs.createWriteStream('.local/logs/browser-check-office.log',{flags:'a'});
const office=spawn(python,['-m','uvicorn','bring_vene.execution.office:app','--host','127.0.0.1','--port',String(officePort)],{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
pipeOwnedOutput(office,officeLog);
const executionLog=fs.createWriteStream('.local/logs/browser-check-execution.log',{flags:'a'});
let execution=spawn(python,['-m','bring_vene.execution.worker'],{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
pipeOwnedOutput(execution,executionLog);
const callbacksLog=fs.createWriteStream('.local/logs/browser-check-callbacks.log',{flags:'a'});
const callbacks=spawn(python,['-m','bring_vene.continuity.office_worker'],{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
pipeOwnedOutput(callbacks,callbacksLog);
const mediaConfig=path.join(root,'.local/browser-livekit.yaml');
fs.writeFileSync(mediaConfig,`port: ${mediaPort}\nbind_addresses: [127.0.0.1]\nrtc:\n  tcp_port: ${mediaTcp}\n  udp_port: ${mediaUdp}\n  use_external_ip: false\n  node_ip: 127.0.0.1\n  enable_loopback_candidate: true\n  use_mdns: false\nturn:\n  enabled: true\n  udp_port: ${mediaTurn}\n  bind_addresses: [127.0.0.1]\n  domain: 127.0.0.1\n  allow_restricted_peer_cidrs: [127.0.0.1/32]\nkeys:\n  ${runtime.livekit_key}: ${runtime.livekit_secret}\nlogging:\n  level: error\n`);
const mediaLog=fs.createWriteStream('.local/logs/browser-check-media.log',{flags:'a'});
const media=spawn(livekitBinary(root),['--config',mediaConfig],{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
env.BRING_VENE_MEDIA_PID=String(media.pid);
fs.writeFileSync('.local/browser-media-process.json',JSON.stringify({root,pid:media.pid,parent_pid:process.pid,started_at:new Date().toISOString(),config:mediaConfig})+'\n');
pipeOwnedOutput(media,mediaLog);
const voiceLog=fs.createWriteStream('.local/logs/browser-check-voice.log',{flags:'a'});
env.MODEL_PROVIDER='fixture';
if(allLive){
  const selected=spawnSync(python,['scripts/model-provider.py'],{cwd:root,env:process.env,windowsHide:true,encoding:'utf8'});
  if(selected.status!==0)throw new Error('Configured live model is unavailable. No fixture model fallback was started.');
  env.MODEL_PROVIDER=selected.stdout.trim();
}

env.VOICE_RUN_ID=randomBytes(16).toString('hex');env.VOICE_READY_FILE=path.join(root,'.local/voice-ready-'+env.VOICE_RUN_ID+'.json');
const understandingLog=fs.createWriteStream('.local/logs/browser-check-understanding.log',{flags:'a'});
const understanding=spawn(python,['-m','bring_vene.understanding.worker'],{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
pipeOwnedOutput(understanding,understandingLog);
let voice=spawn(python,['-m','bring_vene.voice.worker'],{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
pipeOwnedOutput(voice,voiceLog);
const apiLog=fs.createWriteStream('.local/logs/browser-check-api.log',{flags:'a'});
let api=spawn(python,['-m','uvicorn','bring_vene.main:app','--host','127.0.0.1','--port',String(apiPort)],{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
pipeOwnedOutput(api,apiLog);
const log = fs.createWriteStream('.local/logs/browser-check-web.log', { flags: 'a' });
const server = spawn(process.execPath, [path.join(root, 'apps/web/node_modules/next/dist/bin/next'), 'start', '--hostname', '127.0.0.1', '--port', String(port)], { cwd: path.join(root, 'apps/web'), env, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
pipeOwnedOutput(server,log);
// A test-only control broker owns these exact ChildProcess objects. Callers cannot
// supply a PID, executable or arguments, and cannot affect the saved preview.
async function stopOwned(child){
  if(!child||child.exitCode!==null||child.signalCode!==null)return;
  const exited=new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('Owned process tree did not exit.')),10000);child.once('exit',()=>{clearTimeout(timer);resolve();});});
  // Windows virtualenv launchers can have a Python child. This exact live
  // ChildProcess owns that tree; never enumerate or select unrelated services.
  if(process.platform==='win32'){
    const killed=spawn('taskkill.exe',['/PID',String(child.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});
    await new Promise((resolve,reject)=>{killed.once('error',reject);killed.once('exit',resolve);});
  }else child.kill();
  await exited;
}
const controlToken=randomBytes(32).toString('hex');
const control=http.createServer(async(req,res)=>{
  const supplied=String(req.headers['x-vene-test-control']??'');
  if(req.method!=='POST'||supplied.length!==controlToken.length||!timingSafeEqual(Buffer.from(supplied),Buffer.from(controlToken))){res.writeHead(403);res.end();return;}
  const match=/^\/(stop|restart)\/(api|voice|execution)$/.exec(req.url??'');
  if(!match){res.writeHead(404);res.end();return;}
  const [_,operation,name]=match;
  try{
    let child={api,voice,execution}[name];
    await stopOwned(child);
    if(operation==='restart'){
      const args=name==='api'?['-m','uvicorn','bring_vene.main:app','--host','127.0.0.1','--port',String(apiPort)]:['-m',name==='voice'?'bring_vene.voice.worker':'bring_vene.execution.worker'];
      child=spawn(python,args,{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
      const sink={api:apiLog,voice:voiceLog,execution:executionLog}[name];pipeOwnedOutput(child,sink);
      if(name==='api'){api=child;let ready=false;const deadline=Date.now()+30000;while(Date.now()<deadline){try{if((await fetch(env.BACKEND_URL+'/health/ready',{signal:AbortSignal.timeout(500)})).ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,250));}if(!ready)throw new Error('Owned test API restart did not become ready.');}
      if(name==='voice')voice=child;if(name==='execution')execution=child;
    }
    res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({service:name,operation,owned_test_database:true}));
  }catch{res.writeHead(503);res.end();}
});
await new Promise(resolve=>control.listen(0,'127.0.0.1',resolve));
env.BRING_VENE_TEST_CONTROL_URL='http://127.0.0.1:'+control.address().port;
env.BRING_VENE_TEST_CONTROL_TOKEN=controlToken;
let serverError;
server.on('error', error => { serverError = error; });
try {
  let mediaReady=false;
  for(let i=0;i<30;i++){
    if(media.exitCode!==null)throw new Error('Owned LiveKit server exited before readiness.');
    try{if((await fetch(env.LIVEKIT_URL.replace('ws://','http://'),{signal:AbortSignal.timeout(1500)})).ok){mediaReady=true;break;}}catch{}
    await new Promise(resolve=>setTimeout(resolve,1000));
  }
  if(!mediaReady)throw new Error('Owned LiveKit server did not become ready.');
  let apiReady=false;
  for(let i=0;i<30;i++){
    try{if((await fetch(env.BACKEND_URL+'/health/ready',{signal:AbortSignal.timeout(1500)})).ok){apiReady=true;break;}}catch{}
    await new Promise(resolve=>setTimeout(resolve,1000));
  }
  if(!apiReady)throw new Error('Isolated test API did not become ready.');
  if(allLive){const officeGate=spawnSync(python,['scripts/check-office.py'],{cwd:root,env,windowsHide:true,stdio:'inherit'});if(officeGate.status!==0)throw new Error('Actual sandbox lookup preflight failed; no booking was sent.');}
  let ready = false;
  for (let i = 0; i < 45; i++) {
    if (serverError || server.exitCode !== null) throw new Error('Test frontend could not start. Inspect browser-check-web.log.');
    try { if ((await fetch(env.BRING_VENE_BASE_URL + '/prepare', { signal: AbortSignal.timeout(1500) })).ok) { ready = true; break; } } catch {}
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  if (!ready) throw new Error('Production test frontend did not become ready.');
  let voiceWarmed=false;for(let i=0;i<120;i++){try{const ready=JSON.parse(fs.readFileSync(env.VOICE_READY_FILE,'utf8'));if(ready.run_id===env.VOICE_RUN_ID&&ready.native_sdk_warmed){voiceWarmed=true;break;}}catch{}await new Promise(r=>setTimeout(r,500));}if(!voiceWarmed)throw new Error('Owned native voice SDK did not warm; no media pass was inferred.');
  console.log('Browser checks against isolated production frontend/API and bring_vene_test: ' + env.BRING_VENE_BASE_URL);
  const args=[path.join(root,'node_modules/@playwright/test/cli.js'),'test'];
  if(process.env.BRING_VENE_E2E_GREP)args.push('--grep',process.env.BRING_VENE_E2E_GREP);
  const excluded=[];
  if(process.env.BRING_VENE_PHASE&&Number(process.env.BRING_VENE_PHASE)<3)excluded.push('WebRTC|microphone|device loss|server loss');
  if(process.env.BRING_VENE_PHASE&&Number(process.env.BRING_VENE_PHASE)<4)excluded.push('evolving understanding|untrusted fictional turn');
  if(process.env.BRING_VENE_PHASE&&Number(process.env.BRING_VENE_PHASE)<5)excluded.push('coordinated speech|speech latency');
  if(process.env.BRING_VENE_PHASE&&Number(process.env.BRING_VENE_PHASE)<6)excluded.push('sandbox execution');
  if(process.env.BRING_VENE_PHASE&&Number(process.env.BRING_VENE_PHASE)<7)excluded.push('continuity recovery');
  if(process.env.BRING_VENE_PHASE&&Number(process.env.BRING_VENE_PHASE)<8)excluded.push('packaging');
  if(excluded.length)args.push('--grep-invert',excluded.join('|'));
  // Keep this event loop alive: API/media/worker pipe logs must drain throughout
  // the suite. A synchronous CLI wait can fill an access-log pipe and stall HTTP.
  const status=await new Promise((resolve,reject)=>{
    const runner=spawn(process.execPath,args,{cwd:root,env,windowsHide:true,stdio:'inherit'});
    runner.once('error',reject);runner.once('exit',resolve);
  });
  if (status !== 0) throw new Error('Browser checks failed.');
} finally { control.close();await Promise.allSettled([server,api,voice,media,understanding,office,execution,callbacks].map(stopOwned)); log.end(); apiLog.end(); voiceLog.end(); mediaLog.end(); understandingLog.end();officeLog.end();executionLog.end();callbacksLog.end(); }

