// A real browser tour: distinct HttpOnly pane sessions, ordinary patient/clinician APIs,
// persisted sandbox calendar checks and an actual reservation receipt. No DB reset.
import {chromium,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd(),base=process.env.BRING_VENE_BASE_URL??'http://127.0.0.1:3000';
const count=Number(process.env.DEMO_REHEARSALS??1);
// DEMO_VIDEO=0 skips the walkthrough video where Playwright's ffmpeg is not installed.
const record=process.env.DEMO_VIDEO!=='0';
if(!Number.isInteger(count)||count<1||count>10)throw new Error('Choose 1–10 rehearsals.');
const destination=path.resolve(process.env.DEMO_EVIDENCE_DIR??'.local/evidence');
if(!destination.startsWith(path.resolve('.local/evidence')))throw new Error('Demo evidence must stay project-local.');
fs.mkdirSync(destination,{recursive:true});
const recorded=fs.existsSync('.local/chromium.json')?JSON.parse(fs.readFileSync('.local/chromium.json','utf8').replace(/^\uFEFF/,'')):null;
const browser=await chromium.launch({...recorded?{executablePath:recorded.executable}:{channel:'chromium'},headless:true});
const verify=expect.configure({timeout:20000});
const results=[];
try{
  for(let i=0;i<count;i++){
    const context=await browser.newContext({viewport:{width:1440,height:1050},recordVideo:record&&i===0?{dir:path.join(destination,'demo-video'),size:{width:1440,height:1050}}:undefined});
    const page=await context.newPage();page.setDefaultTimeout(45000);let passed=false;const began=Date.now();
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    try{
      await page.goto(base+'/demo');
      if(i===0)await page.screenshot({path:path.join(destination,'demo-welcome-desktop.png'),fullPage:true});
      await page.getByRole('button',{name:'Start demo',exact:true}).click();
      const p=page.frameLocator('iframe[title="Maria’s private phone"]'),d=page.frameLocator('iframe[title="Dr. Chen’s clinician view"]');
      const shot=async name=>{if(i===0)await page.screenshot({path:path.join(destination,name),fullPage:true});};
      // Before: memory from her July visit, then an approved list for Dr. Chen only.
      await verify(p.getByText(/Vene found \d things worth bringing up/)).toBeVisible();
      await p.getByRole('button',{name:/^Add \d to my visit list$/}).click();
      await verify(p.getByText('QUESTION 05',{exact:true})).toBeVisible(); // the visit list itself, not the found cards
      await p.getByRole('button',{name:'Approve my visit list'}).click();
      await verify(p.getByRole('button',{name:'Withdraw approval'})).toBeVisible();
      await verify(d.getByRole('heading',{name:'What should happen with the lab work from Jul 14?'})).toBeVisible();
      await shot('demo-before-desktop.png');
      // During: the private deadline catch, raised, ordered and booked.
      await page.getByRole('button',{name:'Next: During'}).click();
      await p.getByRole('button',{name:'Allow private checks',exact:true}).click();
      await verify(p.getByRole('button',{name:'Pause understanding',exact:true})).toBeEnabled();
      await d.getByRole('button',{name:'Say this',exact:true}).click();
      await verify(p.getByLabel('Private appointment alternative')).toContainText('Riverside Lab has no slot before Friday — Northside has Thursday 9am.',{timeout:20000});
      // Before sharing, the doctor's own payload and visible DOM must lack the private fact.
      await verify(d.getByText('Only what Maria shares.',{exact:true})).toBeVisible();
      const doctorFrame=page.frames().find(f=>f.url().endsWith('/clinician'));
      const privatePayload=await doctorFrame.evaluate(async()=>{const parts=location.pathname.split('/'),run=parts[3],root='/api/demo/'+run+'/clinician/encounters/'+run;return [await(await fetch(root)).text(),await(await fetch(root+'/feasibility')).text()];});
      if(privatePayload.join('').includes('Riverside')||privatePayload.join('').includes('Northside'))throw new Error('Private preference leaked into the clinician API.');
      if(i===0){await page.screenshot({path:path.join(destination,'demo-private-desktop.png'),fullPage:true});await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(destination,'demo-private-mobile.png'),fullPage:true});await page.setViewportSize({width:1440,height:1050});}
      await p.getByRole('button',{name:'Raise this with Dr. Chen'}).click();
      await d.getByRole('button',{name:'Confirm & send lab order'}).click();
      await verify(p.getByRole('button',{name:'Book Thursday 9am'})).toBeEnabled();
      await p.getByRole('button',{name:'Book Thursday 9am'}).click();
      await verify(p.getByLabel('Confirmed reservation')).toContainText('One less thing to chase');
      await p.getByText('View the actual receipt').click();
      await shot('demo-receipt-desktop.png');
      // Before you leave: the plan's prior authorization is caught, answered by Dr. Chen, and every errand
      // returns its own receipt after Maria's approval.
      await page.getByRole('button',{name:'Next: Before you leave'}).click();
      await d.getByRole('button',{name:'Say this',exact:true}).click();
      await verify(p.getByLabel('Private coverage cue')).toContainText('requires prior authorization');
      await p.getByRole('button',{name:'Ask Dr. Chen now'}).click();
      await d.getByRole('button',{name:'The office will submit prior authorization'}).click();
      await p.getByRole('button',{name:/with the offices$/}).click();
      for(const title of ['Schedule the imaging','Pick up the new prescription']){
        const row=d.getByRole('region',{name:'Your part'}).getByRole('listitem').filter({hasText:title});
        await row.getByRole('button',{name:/^Confirm & send/}).click();
      }
      const list=p.getByRole('list',{name:'Before you leave checklist'});
      for(let round=0;round<3&&await list.getByRole('listitem').filter({hasNotText:/Confirmed|Approved by the health plan/}).count();round++){
        const approve=p.getByRole('button',{name:/^Approve /});
        if(await approve.isVisible())await approve.click();
        await page.waitForTimeout(2500);
      }
      await verify(p.getByText('All set before you leave.')).toBeVisible({timeout:30000});
      await shot('demo-leave-desktop.png');
      // After: a scoped family update, a ride Elena answers herself, and what carries forward.
      await page.getByRole('button',{name:'Next: After'}).click();
      await page.getByLabel('Show Elena’s view').check();
      const f=page.frameLocator('iframe[title="Elena’s family view"]');
      await p.getByRole('button',{name:'Send to Elena'}).click();
      await verify(f.getByText('Update from Maria')).toBeVisible();
      await p.getByRole('button',{name:'Ask Elena to drive'}).click();
      await f.getByRole('button',{name:'Yes, I can'}).click();
      await verify(p.getByText('Elena said yes.')).toBeVisible();
      const familyFrame=page.frames().find(fr=>fr.url().endsWith('/family'));
      const familyPayload=await familyFrame.evaluate(async()=>{const run=location.pathname.split('/')[3];return await(await fetch('/api/demo/'+run+'/family/encounters/'+run)).text();});
      if(familyPayload.includes('Riverside')||familyPayload.includes('blood pressure'))throw new Error('Unshared context leaked into the family API.');
      await shot('demo-after-desktop.png');
      // End this fictional visit's standing checks before closing its browser session.
      await page.getByRole('button',{name:'During',exact:false}).first().click();
      await p.getByRole('button',{name:'Pause understanding',exact:true}).click();
      await verify(p.getByRole('button',{name:'Allow private checks',exact:true})).toBeEnabled();
      if(errors.length)throw new Error('Browser errors: '+errors.join('; '));
      results.push({trial:i+1,result:'passed',private_api:true,actual_sandbox_receipt:true,chapters:['before','during','leave','after'],duration_ms:Date.now()-began,url:page.url()});
      passed=true;
      console.log('Demo rehearsal '+(i+1)+' passed.');
    }catch(error){await page.screenshot({path:path.join(destination,'demo-failure.png'),fullPage:true});throw error;}
    finally{const video=page.video();await context.close();if(passed&&i===0&&video)await video.saveAs(path.join(destination,'bring-vene-walkthrough.webm'));}
  }
}finally{await browser.close();fs.writeFileSync(path.join(destination,'demo-rehearsals.json'),JSON.stringify({mode:'guided_fixture',results},null,2));}
