import {test,expect,chromium} from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import {chromiumLaunch,evidence} from './platform';

test('single-screen demo follows actual STT model speech and approved receipt',async({baseURL})=>{
  test.skip(process.env.BRING_VENE_LIVE_PROVIDER_GATE!=='true','Explicit actual-provider gate only.');
  test.setTimeout(240000);
  const browser=await chromium.launch({...chromiumLaunch(),args:['--allow-loopback-in-peer-connection','--disable-features=WebRtcHideLocalIpsWithMdns','--autoplay-policy=no-user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+path.resolve('fixtures/audio/demo-clinician.wav')]});
  const context=await browser.newContext({baseURL,permissions:['microphone'],viewport:{width:1440,height:1050}}),page=await context.newPage();
  if(baseURL&&new URL(baseURL).hostname==='127.0.0.1')await context.grantPermissions(['local-network-access'],{origin:baseURL});
  const result:Record<string,unknown>={physical_acoustics:false,fixture_fallback:false,stt:'deepgram',tts:'cartesia',sample_count:1};
  try{
    await page.goto('/demo');await page.getByRole('button',{name:'Start demo',exact:true}).click();
    const p=page.frameLocator('iframe[title="Maria’s private phone"]'),d=page.frameLocator('iframe[title="Dr. Chen’s clinician view"]');
    await p.getByRole('button',{name:'Join and agree',exact:true}).click();
    await expect(p.getByText('Withdraw agreement',{exact:true})).toBeVisible({timeout:45000});
    await d.getByRole('button',{name:'Join and agree',exact:true}).click();
    await d.getByRole('button',{name:'Mute microphone',exact:true}).click({timeout:45000});
    const start=p.getByRole('button',{name:'Start listening',exact:true});await expect(start).toBeEnabled({timeout:45000});await start.click();
    await expect(p.getByText('Vene processing is active',{exact:true})).toBeVisible();
    const at=Date.now();await d.getByRole('button',{name:'Unmute microphone',exact:true}).click();
    await expect(p.getByLabel('Private appointment alternative')).toContainText('Riverside Lab has no slot before Friday — Northside has Thursday 9am.',{timeout:60000});
    result.unmute_to_obstacle_ms=Date.now()-at;
    await d.getByRole('button',{name:'Mute microphone',exact:true}).click();
    await expect(d.getByText('Only what Maria shares.',{exact:true})).toBeVisible();
    await p.getByRole('button',{name:'Raise this with Dr. Chen'}).click();
    await expect(p.getByText('Vene finished the approved contribution.',{exact:true})).toBeVisible({timeout:45000});
    await d.getByRole('button',{name:'Confirm & send lab order'}).click();
    await p.getByRole('button',{name:'Book Thursday 9am'}).click();
    await expect(p.getByLabel('Confirmed reservation')).toContainText('Reservation confirmed',{timeout:20000});
    const frame=page.frames().find(f=>f.url().endsWith('/patient'))!;
    const actual=await frame.evaluate(async()=>{const run=location.pathname.split('/')[3],root='/api/demo/'+run+'/patient/encounters/'+run;return {speech:await(await fetch(root+'/speech')).json(),visit:await(await fetch(root)).json(),execution:await(await fetch(root+'/execution')).json()};});
    expect(actual.visit.evidence.some((e:{origin:string})=>e.origin==='deepgram')).toBe(true);
    expect(actual.speech.provider).toBe('cartesia');expect(actual.speech.receipts[0].played_ms).toBeGreaterThan(0);
    result.passed=true;result.speech=actual.speech;result.actions=actual.execution.actions;result.model=actual.visit.understanding;
    await page.screenshot({path:evidence('demo-live-receipt.png'),fullPage:true});
  }catch(e){result.passed=false;result.error_type=(e as Error).name;await page.screenshot({path:evidence('demo-live-failure.png'),fullPage:true});throw e;}
  finally{
    const frame=page.frames().find(f=>f.url().endsWith('/patient'));
    if(frame){try{result.room_ended=await frame.evaluate(async()=>{
      const run=location.pathname.split('/')[3],prefix='/api/demo/'+run+'/patient',root=prefix+'/encounters/'+run;
      const viewer=await(await fetch(prefix+'/auth/me')).json(),call=await(await fetch(root+'/call')).json();
      if(call.state==='ended'||!call.revision)return true;
      const reply=await fetch(root+'/call/controls',{method:'POST',headers:{'Content-Type':'application/json','x-vene-intent':'mutation','x-vene-csrf':viewer.csrf_token},body:JSON.stringify({command_id:crypto.randomUUID(),type:'end',expected_revision:call.revision})});
      return reply.ok&&(await reply.json()).state==='ended';
    });}catch{result.room_ended=false;}}
    const saved=JSON.stringify(result,null,2)+'\n';fs.writeFileSync(evidence('demo-live.json'),saved);fs.writeFileSync(evidence('demo-live-'+Date.now()+'.json'),saved);
    await context.close();await browser.close();
    if(result.passed)expect(result.room_ended).toBe(true);
  }
});
