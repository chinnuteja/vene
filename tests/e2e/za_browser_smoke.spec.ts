import {test,expect,firefox,webkit} from '@playwright/test';
import fs from 'node:fs';import path from 'node:path';
import {base,launch} from './helpers';
function executable(name:string){
  const root=path.resolve('.local/pw-extra');if(!fs.existsSync(root))return null;
  const folder=fs.readdirSync(root).filter(p=>p.startsWith(name+'-')).sort().at(-1);
  if(!folder)return null;const file=path.join(root,folder,name==='firefox'?'firefox/firefox.exe':'Playwright.exe');return fs.existsSync(file)?file:null;
}
for(const name of ['firefox','webkit'] as const){
  test('packaging '+name+' forms room and microphone smoke',async({baseURL})=>{
    test.setTimeout(100000);const binary=executable(name);
    test.skip(!binary,'Install project-owned Firefox/WebKit with scripts/install-extra-browsers.ps1. This platform is unverified.');
    const browser=await (name==='firefox'?firefox:webkit).launch({executablePath:binary!,...(name==='firefox'?{firefoxUserPrefs:{'media.navigator.streams.fake':true,'media.navigator.permission.disabled':true,'media.peerconnection.ice.loopback':true,'media.peerconnection.ice.obfuscate_host_addresses':false}}:{})});
    const patient=await browser.newContext({baseURL}),doctor=await browser.newContext({baseURL});const p=await patient.newPage(),d=await doctor.newPage();
    try{
      await launch(patient);await launch(doctor,'clinician');await p.goto('/prepare');await expect(p.getByText('Follow-up with Dr. Chen',{exact:true})).toBeVisible();
      await p.getByRole('link',{name:'Your visit',exact:true}).click();await d.goto('/visit');
      const capabilities=await p.evaluate(()=>({rtc:typeof RTCPeerConnection==='function',microphone:!!navigator.mediaDevices?.getUserMedia}));
      if(!capabilities.rtc||!capabilities.microphone){
        await expect(p.getByText('Voice conversations are unavailable in this browser. You can still prepare questions and review your follow-up here.',{exact:true})).toBeVisible();
        await p.goto('/follow-up');await expect(p.getByRole('region',{name:'After-visit continuity',exact:true})).toBeVisible();
        fs.writeFileSync('docs/qa/phase-08-'+name+'-smoke.json',JSON.stringify({checked_at:new Date().toISOString(),browser:name,platform:'Windows',forms:'passed',capabilities,room:'unavailable in this browser build; accessible error verified',microphone:'not exercised',full_media_gate:false},null,2)+'\n');return;
      }
      await d.getByRole('button',{name:'Check microphone',exact:true}).click();await expect(d.getByText('Microphone opened successfully. Audio stayed on this device.',{exact:true})).toBeVisible();
      await p.getByRole('button',{name:'Join without a microphone',exact:true}).click();await expect(p.getByRole('button',{name:'Agree to Vene processing',exact:true})).toBeVisible({timeout:30000});
      await d.getByRole('button',{name:'Join conversation',exact:true}).click();await expect(d.getByRole('button',{name:'Mute my microphone',exact:true})).toBeVisible({timeout:30000});
      await expect.poll(async()=>{const c=await (await patient.request.get(base+'/call')).json();return c.participants.filter(x=>x.present).length===2&&c.participants.some(x=>x.role==='clinician'&&x.track_epoch>0);},{timeout:25000}).toBe(true);
      await d.getByRole('button',{name:'Mute my microphone',exact:true}).click();await expect(d.getByRole('button',{name:'Unmute my microphone',exact:true})).toBeVisible();
      await p.getByRole('button',{name:'End this conversation for everyone',exact:true}).click();
      fs.writeFileSync('docs/qa/phase-08-'+name+'-smoke.json',JSON.stringify({checked_at:new Date().toISOString(),browser:name,platform:'Windows',forms:'passed',room:'actual two-peer LiveKit connection',microphone:'browser synthetic device opened published and muted',physical_device:false,full_media_gate:true},null,2)+'\n');
    }finally{await browser.close();}
  });
}
