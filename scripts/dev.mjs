import {pipeOwnedOutput} from './child-logs.mjs';
import {venvPython,livekitBinary} from './platform.mjs';
import { spawn, spawnSync } from 'node:child_process';
import { createWriteStream, existsSync, mkdirSync, readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import net from 'node:net';
import { randomBytes } from 'node:crypto';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const runtime = JSON.parse(readFileSync(path.join(root, '.local/runtime.json'), 'utf8').replace(/^\uFEFF/, ''));
const modeIndex=process.argv.indexOf('--mode');
const mode = modeIndex>=0?process.argv[modeIndex+1]:'fixture';
const liveProviders=process.argv.includes('--live-providers');
const guided=process.argv.includes('--guided');
if(guided&&(liveProviders||process.argv.includes('--model-live')||process.argv.includes('--tts-live')||mode==='live'))throw new Error('Guided fixture must be explicitly separate from live providers.');
process.env.DEMO_GUIDED=String(guided);
const voiceProvider=liveProviders||mode==='live'?'deepgram':'fixture';
let modelProvider='fixture';
if(process.argv.includes('--model-live')||liveProviders){
  const selected=spawnSync(venvPython(root),['scripts/model-provider.py'],{cwd:root,env:process.env,windowsHide:true,encoding:'utf8'});
  if(selected.status!==0)throw new Error('Configure MODEL_PROVIDER=openai or deepseek and its API key. No fixture fallback was started.');
  modelProvider=selected.stdout.trim();
}
const ttsProvider=process.argv.includes('--tts-live')||liveProviders?'cartesia':'fixture';
if(ttsProvider==='cartesia'){
  const gate=spawnSync(venvPython(root),['-c','from bring_vene.config import Settings; import sys; s=Settings(); sys.exit(0 if s.cartesia_api_key and s.cartesia_voice_id else 1)'],{cwd:root,env:process.env,windowsHide:true,stdio:'ignore'});
  if(gate.status!==0)throw new Error('Live TTS needs CARTESIA_API_KEY and CARTESIA_VOICE_ID. No offline fallback was started.');
}
if (!['fixture','live'].includes(mode)) throw new Error('Select fixture or live voice mode.');
if(voiceProvider==='deepgram'){
  const gate=spawnSync(venvPython(root),['-c','from bring_vene.config import Settings; import sys; sys.exit(0 if Settings().deepgram_api_key else 1)'],{cwd:root,env:process.env,windowsHide:true,stdio:'ignore'});
  if(gate.status!==0)throw new Error('Live STT needs DEEPGRAM_API_KEY in the project .env or environment. No fixture fallback was started.');
}
const production = process.argv.includes('--production');
const pidFile = path.join(root, '.local/processes.json');
if (existsSync(pidFile)) {
  const old = JSON.parse(readFileSync(pidFile, 'utf8'));
  try { process.kill(old.pid, 0); throw new Error('A project server is already running. Reuse it or run stop.ps1.'); }
  catch (e) { if (e.code !== 'ESRCH') throw e; }
}
async function available(port) {
  return new Promise(resolve => { const server = net.createServer(); server.once('error', () => resolve(false)); server.listen(port, '127.0.0.1', () => server.close(() => resolve(true))); });
}
for (const key of ['api_port', 'web_port']) {
  if (!await available(runtime[key])) { let port = runtime[key] + 1; while (!await available(port)) port++; runtime[key] = port; }
}
runtime.office_port??=8012;
runtime.office_callback_secret??=randomBytes(32).toString('hex');
if(!await available(runtime.office_port)){let port=runtime.office_port+1;while(!await available(port))port++;runtime.office_port=port;}
if (!runtime.livekit_key || !runtime.livekit_secret) throw new Error('Run scripts/setup-media.ps1 to configure the owned local media server.');
runtime.livekit_turn_port??=3478;
for (const key of ['livekit_port','livekit_tcp_port','livekit_udp_port','livekit_turn_port']) {
  if (!await available(runtime[key])) { let port=runtime[key]+1; while(!await available(port))port++; runtime[key]=port; }
}
writeFileSync(path.join(root, '.local/runtime.json'), JSON.stringify(runtime, null, 2) + '\n');
mkdirSync(path.join(root, '.local/logs'), { recursive: true });
const env = { ...process.env, DATABASE_URL: runtime.database_url, BRING_VENE_MODE: mode, VOICE_PROVIDER:voiceProvider, LIVEKIT_URL:'ws://127.0.0.1:'+runtime.livekit_port, LIVEKIT_API_KEY:runtime.livekit_key, LIVEKIT_API_SECRET:runtime.livekit_secret, BRING_VENE_DEVELOPMENT: 'true', COOKIE_SECURE: 'false', NEXT_TELEMETRY_DISABLED: '1', NEXT_DIST_DIR: production ? '.next' : '.next-dev', BACKEND_URL: 'http://127.0.0.1:' + runtime.api_port };
env.MODEL_PROVIDER=modelProvider;
env.TTS_PROVIDER=ttsProvider;
env.VOICE_ADMISSION_WAIT_SECONDS='3';
env.VOICE_RUN_ID=randomBytes(16).toString('hex');env.VOICE_READY_FILE=path.join(root,'.local/voice-ready-'+env.VOICE_RUN_ID+'.json');
env.OFFICE_URL='http://127.0.0.1:'+runtime.office_port;
env.OFFICE_TOKEN=randomBytes(32).toString('hex');
env.OFFICE_CALLBACK_SECRET=runtime.office_callback_secret;
env.OFFICE_CALLBACK_URL=env.BACKEND_URL+'/integrations/office/results';
const officeInit=spawnSync(venvPython(root),['-c','from bring_vene.execution.office import initialize; from bring_vene.config import Settings; from bring_vene.persistence.database import make_engine; initialize(make_engine(Settings().database_url))'],{cwd:root,env,windowsHide:true,stdio:'inherit'});
if(officeInit.status!==0)throw new Error('Migrate the project database before starting the sandbox office.');
const mediaConfig=path.join(root,'.local/livekit.yaml');
writeFileSync(mediaConfig,`port: ${runtime.livekit_port}\nbind_addresses: [127.0.0.1]\nrtc:\n  tcp_port: ${runtime.livekit_tcp_port}\n  udp_port: ${runtime.livekit_udp_port}\n  use_external_ip: false\n  node_ip: 127.0.0.1\n  enable_loopback_candidate: true\n  use_mdns: false\nturn:\n  enabled: true\n  udp_port: ${runtime.livekit_turn_port}\n  bind_addresses: [127.0.0.1]\n  domain: 127.0.0.1\n  allow_restricted_peer_cidrs: [127.0.0.1/32]\nkeys:\n  ${runtime.livekit_key}: ${runtime.livekit_secret}\nlogging:\n  level: error\n`);
const children = [];
function start(name, executable, args, cwd) {
  const log = createWriteStream(path.join(root, '.local/logs/' + name + '.log'), { flags: 'a' });
  const child = spawn(executable, args, { cwd, env, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  pipeOwnedOutput(child,log);
  child.on('error', e => { console.error(name + ' failed: ' + e.message); shutdown(1); });
  child.on('exit', code => { if (!closing) { console.error(name + ' exited: ' + code); shutdown(1); } });
  children.push(child);
  return child;
}
let closing = false;
function shutdown(code = 0) {
  if (closing) return; closing = true;
  for (const child of children) child.kill();
  if (existsSync(pidFile)) unlinkSync(pidFile);
  process.exit(code);
}
process.on('SIGINT', () => shutdown());
process.on('SIGTERM', () => shutdown());
const python = venvPython(root);
const media = start('livekit',livekitBinary(root),['--config',mediaConfig],root);
const api = start('backend', python, ['-m', 'uvicorn', 'bring_vene.main:app', '--host', '127.0.0.1', '--port', String(runtime.api_port)], root);
const voice=start('voice',python,['-m','bring_vene.voice.worker'],root);
const understanding=start('understanding',python,['-m','bring_vene.understanding.worker'],root);
start('office',python,['-m','uvicorn','bring_vene.execution.office:app','--host','127.0.0.1','--port',String(runtime.office_port)],root);
const execution=start('execution',python,['-m','bring_vene.execution.worker'],root);
start('office-callbacks',python,['-m','bring_vene.continuity.office_worker'],root);
const web = start('web', process.execPath, [path.join(root, 'apps/web/node_modules/next/dist/bin/next'), production ? 'start' : 'dev', '--hostname', '127.0.0.1', '--port', String(runtime.web_port)], path.join(root, 'apps/web'));
writeFileSync(pidFile, JSON.stringify({ root, pid: process.pid, started_at: new Date(Date.now() - process.uptime() * 1000).toISOString(), api_pid: api.pid, web_pid: web.pid, media_pid:media.pid,voice_pid:voice.pid,execution_pid:execution.pid }, null, 2));
async function waitReady(url) {
  for (let i = 0; i < 90; i++) {
    if (closing) return;
    try { if ((await fetch(url, { signal: AbortSignal.timeout(1500) })).ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  throw new Error('Readiness failed: ' + url + '. Inspect .local/logs.');
}
try {
  await waitReady(env.BACKEND_URL + '/health/ready');
  await waitReady(env.OFFICE_URL+'/health');
  await waitReady('http://127.0.0.1:'+runtime.livekit_port);
  await waitReady('http://127.0.0.1:' + runtime.web_port + '/prepare');
  let warmed=false;for(let i=0;i<120;i++){try{const ready=JSON.parse(readFileSync(env.VOICE_READY_FILE,'utf8'));if(ready.run_id===env.VOICE_RUN_ID&&ready.native_sdk_warmed){warmed=true;break;}}catch{}await new Promise(r=>setTimeout(r,500));}if(!warmed)throw new Error('Owned native voice SDK did not warm.');
  console.log('Local: http://127.0.0.1:' + runtime.web_port);
  console.log('Backend, PostgreSQL and real local LiveKit ready. STT mode: '+(voiceProvider==='fixture'?'fixture (transport evidence only)':'Deepgram; model: '+modelProvider+'; TTS: '+ttsProvider));
} catch (e) { console.error(e.message); shutdown(1); }


