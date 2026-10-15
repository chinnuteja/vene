import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd();
const text='Maria will arrange the lab visit at Riverside Lab on Tuesday after the office sends the order. This is an original fictional conversation for testing.';
const response=spawnSync('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(root,'scripts/synthesize-fixture.ps1')],
  {cwd:root,input:JSON.stringify({text})+'\n',encoding:'utf8',windowsHide:true,maxBuffer:8*1024*1024});
if(response.status!==0)throw new Error('Original offline speech generation failed; no provider fallback was started.');
const result=JSON.parse(response.stdout.trim());if(!result.pcm||result.sample_rate!==24000)throw new Error('Unverified offline speech output.');
const pcm=Buffer.from(result.pcm,'base64');const header=Buffer.alloc(44);
header.write('RIFF',0);header.writeUInt32LE(36+pcm.length,4);header.write('WAVEfmt ',8);header.writeUInt32LE(16,16);header.writeUInt16LE(1,20);header.writeUInt16LE(1,22);
header.writeUInt32LE(24000,24);header.writeUInt32LE(48000,28);header.writeUInt16LE(2,32);header.writeUInt16LE(16,34);header.write('data',36);header.writeUInt32LE(pcm.length,40);
fs.mkdirSync('fixtures/audio',{recursive:true});fs.writeFileSync('fixtures/audio/live-clinician.wav',Buffer.concat([header,pcm]));
fs.writeFileSync('fixtures/audio/live-clinician.json',JSON.stringify({original:true,synthetic:true,text,sample_rate:24000,voice:result.voice,duration_seconds:pcm.length/48000,provider_calls:false},null,2)+'\n');
console.log('Original synthetic spoken WAV generated for the explicit live-STT gate.');
