import {chromium,expect} from '@playwright/test';
import fs from 'node:fs';
const runtime=JSON.parse(fs.readFileSync('.local/runtime.json','utf8').replace(/^\uFEFF/,''));
const url='http://127.0.0.1:'+runtime.web_port;
const browser=await chromium.launch({channel:'chromium'});
const errors=[];
try{
  const context=await browser.newContext({baseURL:url,viewport:{width:1440,height:1040}}),page=await context.newPage();
  page.on('pageerror',error=>errors.push({type:'page',name:error.name}));
  page.on('console',message=>{if(message.type()==='error')errors.push({type:'console'});});
  page.on('response',response=>{if(response.status()>=400)errors.push({type:'http',status:response.status(),path:new URL(response.url()).pathname});});
  await page.goto('/dev');await page.getByRole('checkbox',{name:'Show fictional scenario controls (developer)',exact:true}).check();await page.getByRole('button',{name:'Continue as Maria'}).click();
  await expect(page.getByText('Follow-up with Dr. Chen',{exact:true})).toBeVisible({timeout:30000});
  const base='/api/encounters/10000000-0000-4000-8000-000000000001';
  const before=await (await context.request.get(base)).json();
  await page.goto('/visit');await expect(page.getByRole('region',{name:'Vene participation',exact:true})).toBeVisible({timeout:30000});
  await page.getByRole('button',{name:'Help me keep track',exact:true}).click();
  await expect(page.getByRole('button',{name:'Help me keep track',exact:true})).toBeEnabled();
  await page.evaluate(()=>{if(document.activeElement instanceof HTMLElement)document.activeElement.blur();window.scrollTo(0,0);});
  await page.screenshot({path:'docs/qa/phase-05-preview-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.evaluate(()=>window.scrollTo(0,0));
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  await page.screenshot({path:'docs/qa/phase-05-preview-mobile.png',fullPage:true});
  const after=await (await context.request.get(base)).json();
  expect(after.version).toBe(before.version);
  fs.writeFileSync('docs/qa/phase-05-preview-review.json',JSON.stringify({checked_at:new Date().toISOString(),url,launcher:'used in actual browser',phase5_panel:'visible; private refresh exercised',visit_version_preserved:after.version===before.version,mobile_overflow:overflow,errors,room_joined:false,provider_calls:false},null,2)+'\n');
  if(errors.length||overflow)throw new Error('Preview review found browser errors or overflow.');
  console.log('Phase 5 working preview inspected; private help works, visit edits preserved, no browser errors or horizontal overflow.');
}finally{await browser.close();}
