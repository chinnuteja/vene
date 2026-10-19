import {evidence,chromiumLaunch,livekitServer,stopOwnedMedia} from './platform';
import {test,expect,chromium} from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import {execFileSync,spawn} from 'node:child_process';
import {base,launch,endCall} from './helpers';
async function state(context:any){return (await context.request.get(base+'/call',{maxRetries:2})).json();}
test('server loss clears the call and offers a recoverable rejoin state',async({baseURL})=>{
  test.setTimeout(120000);
  test.skip(!process.env.BRING_VENE_MEDIA_PID,'Requires the owned isolated media runner.');
  const browser=await chromium.launch({...chromiumLaunch(),args:['--allow-loopback-in-peer-connection','--disable-features=WebRtcHideLocalIpsWithMdns']});
  let restarted: ReturnType<typeof spawn>|null=null;
  let context:Awaited<ReturnType<typeof browser.newContext>>|null=null;
  try{
    context=await browser.newContext({baseURL});await launch(context);const page=await context.newPage();
    page.on('console',message=>{if(message.text().startsWith('Vene join status: '))console.log(message.text());});
    await page.goto('/visit');
    await page.getByRole('button',{name:'Join without a microphone',exact:true}).click();
    await expect(page.getByRole('heading',{name:'May Vene process your audio?'})).toBeVisible();
    stopOwnedMedia(Number(process.env.BRING_VENE_MEDIA_PID));
    await expect(page.getByRole('alert',{name:'Call error'})).toContainText('call disconnected',{timeout:30000});
    await expect(page.getByRole('button',{name:'Join without a microphone',exact:true})).toBeEnabled();
    await expect.poll(async()=>(await state(context)).state,{timeout:15000}).toBe('unavailable');
    await page.screenshot({path:evidence('phase-03-server-loss.png'),fullPage:true});
    restarted=spawn(livekitServer(),['--config',path.resolve('.local/browser-livekit.yaml')],{windowsHide:true,stdio:'ignore'});
    await expect.poll(async()=>{try{return (await fetch(process.env.LIVEKIT_URL!.replace('ws://','http://'))).ok;}catch{return false;}},{timeout:15000}).toBe(true);
    const recoveryStarted=Date.now();const observations=[];
    await page.getByRole('button',{name:'Join without a microphone',exact:true}).click();
    await expect(page.getByRole('heading',{name:'May Vene process your audio?'})).toBeVisible({timeout:20000});
    await expect.poll(async()=>{const s=await state(context);observations.push({elapsed_ms:Date.now()-recoveryStarted,state:s.state,ready:s.worker_ready,error:s.worker_error});return s.worker_ready&&s.state==='paused';},{timeout:45000}).toBe(true);
    fs.writeFileSync(evidence('phase-08-server-recovery.json'),JSON.stringify({checked_at:new Date().toISOString(),actual_owned_server_restarted:true,observations,recovery_ms:Date.now()-recoveryStarted,processing_resumed_automatically:false},null,2)+'\n');
    await page.getByRole('button',{name:'End this conversation for everyone',exact:true}).click();
    // Click dispatches an async control. Keep the browser and restarted media server
    // alive until its actual end acknowledgement, before another scenario starts.
    await expect.poll(async()=>(await state(context)).state).toBe('ended');
  }finally{if(context)await endCall(context);await browser.close();restarted?.kill();}
});

