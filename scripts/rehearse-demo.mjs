// A real browser tour: distinct HttpOnly pane sessions, ordinary patient/clinician APIs,
// persisted sandbox calendar checks and an actual reservation receipt. No DB reset.
import {chromium,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd(),base=process.env.BRING_VENE_BASE_URL??'http://127.0.0.1:3000';
const count=Number(process.env.DEMO_REHEARSALS??1);
if(!Number.isInteger(count)||count<1||count>10)throw new Error('Choose 1–10 rehearsals.');
const destination=path.resolve('.local/evidence');fs.mkdirSync(destination,{recursive:true});
const recorded=fs.existsSync('.local/chromium.json')?JSON.parse(fs.readFileSync('.local/chromium.json','utf8').replace(/^\uFEFF/,'')):null;
const browser=await chromium.launch({...recorded?{executablePath:recorded.executable}:{channel:'chromium'},headless:true});
const results=[];
try{
  for(let i=0;i<count;i++){
    const context=await browser.newContext({viewport:{width:1440,height:1050},recordVideo:i===0?{dir:path.join(destination,'demo-video'),size:{width:1440,height:1050}}:undefined});
    const page=await context.newPage();page.setDefaultTimeout(45000);
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    try{
      await page.goto(base+'/demo');
      if(i===0)await page.screenshot({path:path.join(destination,'demo-welcome-desktop.png'),fullPage:true});
      await page.getByRole('button',{name:'Start demo',exact:true}).click();
      const p=page.frameLocator('iframe[title="Maria’s private phone"]'),d=page.frameLocator('iframe[title="Dr. Chen’s clinician view"]');
      await p.getByRole('button',{name:'Allow private checks',exact:true}).click();
      await d.getByRole('button',{name:'Try the sample instruction'}).click();
      await expect(p.getByLabel('Private appointment alternative')).toContainText('Riverside Lab has no slot before Friday — Northside has Thursday 9am.');
      // Before sharing, the doctor's own payload and visible DOM must lack the private fact.
      await expect(d.getByText('Only what Maria shares.',{exact:true})).toBeVisible();
      const doctorFrame=page.frames().find(f=>f.url().endsWith('/clinician'));
      const privatePayload=await doctorFrame.evaluate(async()=>{const parts=location.pathname.split('/'),run=parts[3],root='/api/demo/'+run+'/clinician/encounters/'+run;return [await(await fetch(root)).text(),await(await fetch(root+'/feasibility')).text()];});
      if(privatePayload.join('').includes('Riverside')||privatePayload.join('').includes('Northside'))throw new Error('Private preference leaked into the clinician API.');
      if(i===0){await page.screenshot({path:path.join(destination,'demo-private-desktop.png'),fullPage:true});await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(destination,'demo-private-mobile.png'),fullPage:true});await page.setViewportSize({width:1440,height:1050});}
      await p.getByRole('button',{name:'Raise this with Dr. Chen'}).click();
      await d.getByRole('button',{name:'Confirm & send lab order'}).click();
      await expect(p.getByRole('button',{name:'Book Thursday 9am'})).toBeEnabled();
      await p.getByRole('button',{name:'Book Thursday 9am'}).click();
      await expect(p.getByLabel('Confirmed reservation')).toContainText('Reservation confirmed');
      await p.getByText('View the actual receipt').click();
      if(i===0)await page.screenshot({path:path.join(destination,'demo-receipt-desktop.png'),fullPage:true});
      if(errors.length)throw new Error('Browser errors: '+errors.join('; '));
      results.push({trial:i+1,result:'passed',private_api:true,actual_sandbox_receipt:true,url:page.url()});
      console.log('Demo rehearsal '+(i+1)+' passed.');
    }catch(error){await page.screenshot({path:path.join(destination,'demo-failure.png'),fullPage:true});throw error;}
    finally{await context.close();}
  }
}finally{await browser.close();fs.writeFileSync(path.join(destination,'demo-rehearsals.json'),JSON.stringify({mode:'guided_fixture',results},null,2));}
