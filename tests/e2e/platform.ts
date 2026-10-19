import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';

export const isWindows=process.platform==='win32';
export const venvPython=path.resolve(isWindows?'.venv/Scripts/python.exe':'.venv/bin/python');
export function livekitServer(){
  const owned=path.resolve('.local/tools/livekit',isWindows?'livekit-server.exe':'livekit-server');
  if(fs.existsSync(owned)||process.platform!=='darwin')return owned;
  return execFileSync('which',['livekit-server'],{encoding:'utf8'}).trim();
}
// Default: Playwright's pinned Chromium. An explicit executable is used only when
// that revision is unavailable on this machine (recorded by setup in runtime state).
export function chromiumLaunch():{channel:'chromium'}|{executablePath:string}{
  const recorded=path.resolve('.local/chromium.json');
  const explicit=process.env.BRING_VENE_CHROMIUM_PATH??(fs.existsSync(recorded)?JSON.parse(fs.readFileSync(recorded,'utf8').replace(/^\uFEFF/,'')).executable:undefined);
  return explicit?{executablePath:explicit}:{channel:'chromium'};
}
// Test runs write evidence under ignored .local; selected files are promoted to docs/qa deliberately.
export function evidence(name:string){
  const folder=process.env.BRING_VENE_EVIDENCE_DIR??path.resolve('.local/evidence');
  const file=path.join(folder,name);
  fs.mkdirSync(path.dirname(file),{recursive:true});
  return file;
}

// Stops only the browser runner's own media server: same recorded PID, same parent,
// same executable and config. Windows keeps its audited PowerShell check.
export function stopOwnedMedia(pid:number){
  if(isWindows){
    execFileSync('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',path.resolve('scripts/kill-test-media.ps1'),'-ProcessId',String(pid)],{windowsHide:true});
    return;
  }
  const record=JSON.parse(fs.readFileSync('.local/browser-media-process.json','utf8'));
  if(record.root!==process.cwd()||record.pid!==pid)throw new Error('Test process ownership does not match this workspace.');
  const command=execFileSync('ps',['-o','ppid=,args=','-p',String(pid)],{encoding:'utf8'}).trim();
  const [parent,...args]=command.split(/\s+/);
  const line=args.join(' ');
  if(Number(parent)!==record.parent_pid||!line.includes(livekitServer())||!line.includes(path.resolve('.local/browser-livekit.yaml')))
    throw new Error('Refusing to stop a process outside the owned browser test server.');
  process.kill(pid,'SIGKILL'); // Abrupt loss, like Stop-Process on Windows; SIGTERM is a graceful LiveKit shutdown.
}
