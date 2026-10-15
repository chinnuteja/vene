import { chromium } from '@playwright/test';
import fs from 'node:fs';
const runtime=JSON.parse(fs.readFileSync('.local/runtime.json','utf8').replace(/^\uFEFF/,''));
const url='http://127.0.0.1:'+runtime.web_port;
const mode=process.argv.includes('--after-restart')?'after':'before';
const browser=await chromium.launch({channel:'chromium'});
const base='/api/encounters/10000000-0000-4000-8000-000000000001';
try {
  const context=await browser.newContext({baseURL:url,viewport:{width:1440,height:1040},...(mode==='after'?{storageState:'.local/phase2-restart-session.json'}:{})});
  const page=await context.newPage(), errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error') errors.push(m.text());});
  page.on('response',r=>{if(r.status()>=400) errors.push(r.status()+' '+new URL(r.url()).pathname);});
  if(mode==='before') {
    await page.goto('/dev');
    await page.getByRole('button',{name:'Continue as Maria'}).waitFor();
    await page.screenshot({path:'docs/qa/phase-02-launcher.png',fullPage:true});
    await page.getByRole('button',{name:'Continue as Maria'}).click();
    await page.getByText('Follow-up with Dr. Chen',{exact:true}).waitFor();
  }else{
    await page.goto('/prepare');
    await page.getByText('Follow-up with Dr. Chen',{exact:true}).waitFor();
  }
  const me=await (await context.request.get('/api/auth/me')).json();
  async function approve(value){
    const v=await (await context.request.get(base)).json();
    const r=await context.request.post(base+'/commands',{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data:{command_id:crypto.randomUUID(),expected_version:v.version,command:{type:'preparation.approved',approved:value}}});
    if(!r.ok())throw new Error('Could not save preparation.');
  }
  if(mode==='after'){
    const previous=JSON.parse(fs.readFileSync('.local/phase2-restart-check.json','utf8'));
    const v=await (await context.request.get(base)).json();
    if(!v.preparation_approved || me.membership_id!==previous.membership_id || v.version!==previous.version)throw new Error('Restart did not preserve the session and approved preparation.');
    await approve(previous.original_approval);
    fs.writeFileSync('docs/qa/phase-02-restart.json',JSON.stringify({checked_at:new Date().toISOString(),actual_process_restart:true,session_membership:'preserved',approved_preparation:'preserved',version:'preserved',original_approval:'restored',runtime_errors:errors},null,2)+'\n');
    console.log('Actual process restart preserved session, approval and version.');
  }else{
    for(const route of ['prepare','visit','follow-up']){
      await page.goto('/'+route);await page.getByText('Follow-up with Dr. Chen',{exact:true}).waitFor();
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:'docs/qa/phase-02-'+route+'-review.png',fullPage:true});
    }
    await page.goto('/prepare');await page.getByRole('button',{name:'View source'}).first().click();
    await page.getByRole('dialog').waitFor();await page.screenshot({path:'docs/qa/phase-02-source-dialog.png'});
    await page.keyboard.press('Escape');
    await page.setViewportSize({width:390,height:844});await page.evaluate(()=>window.scrollTo(0,0));
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
    await page.screenshot({path:'docs/qa/phase-02-mobile-review.png',fullPage:true});
    const original=await (await context.request.get(base)).json();
    await approve(true);
    const approved=await (await context.request.get(base)).json();
    await context.storageState({path:'.local/phase2-restart-session.json'});
    fs.writeFileSync('.local/phase2-restart-check.json',JSON.stringify({membership_id:me.membership_id,version:approved.version,original_approval:original.preparation_approved})+'\n');
    fs.writeFileSync('docs/qa/phase-02-browser-review.json',JSON.stringify({checked_at:new Date().toISOString(),url,normal_page_errors:errors,mobile_overflow:overflow,launcher:'used through browser',routes:['prepare','visit','follow-up'],source_dialog:'captured and keyboard dismissed',synthetic_only:true},null,2)+'\n');
    if(overflow)throw new Error('Mobile horizontal overflow.');
    console.log('Local launcher, routes and source dialog reviewed; restart checkpoint saved privately.');
  }
  if(errors.length)throw new Error('Browser errors: '+errors.join('; '));
  await context.close();
}finally{await browser.close();}
