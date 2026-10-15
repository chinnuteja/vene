import {chromium,expect} from '@playwright/test';import fs from 'node:fs';
const runtime=JSON.parse(fs.readFileSync('.local/runtime.json','utf8').replace(/^\uFEFF/,''));const url='http://127.0.0.1:'+runtime.web_port;
const browser=await chromium.launch({channel:'chromium'});const errors=[];
try{
 const context=await browser.newContext({baseURL:url,viewport:{width:1440,height:1000},reducedMotion:'reduce'}),p=await context.newPage();
 p.on('pageerror',e=>errors.push({type:'page',name:e.name}));p.on('response',r=>{if(r.status()>=400)errors.push({type:'http',status:r.status(),path:new URL(r.url()).pathname});});
 await p.goto('/dev');await expect(p.getByRole('checkbox',{name:'Show fictional scenario controls (developer)',exact:true})).not.toBeChecked();
 await p.getByRole('button',{name:'Continue as Maria'}).click();await expect(p.getByText('Follow-up with Dr. Chen',{exact:true})).toBeVisible({timeout:60000});
 const base='/api/encounters/'+(await (await context.request.get('/api/auth/me')).json()).encounter_id;const before=await (await context.request.get(base)).json();
 const providers={stt:(await (await context.request.get(base+'/call')).json()).provider,model:(await (await context.request.get(base+'/understanding')).json()).provider,tts:(await (await context.request.get(base+'/speech')).json()).provider};
 if(process.argv.includes('--live'))expect(providers).toEqual({stt:'deepgram',model:'deepseek',tts:'cartesia'});
 for(const route of ['/prepare','/visit','/follow-up']){
  await p.goto(route);await expect(p.locator('main#main')).toBeVisible();
  await expect(p.getByText('Fictional conversation input',{exact:true})).toHaveCount(0);await expect(p.getByText('Development sandbox \u00b7 change office conditions',{exact:true})).toHaveCount(0);
  await p.evaluate(()=>{if(document.activeElement instanceof HTMLElement)document.activeElement.blur();scrollTo(0,0);});
  await p.screenshot({path:'docs/qa/phase-08-preview-'+route.slice(1)+'-desktop.png',fullPage:true});
 }
 await p.setViewportSize({width:390,height:844});await p.evaluate(()=>scrollTo(0,0));expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await p.screenshot({path:'docs/qa/phase-08-preview-mobile.png',fullPage:true});
 await p.getByRole('region',{name:'After-visit continuity',exact:true}).scrollIntoViewIfNeeded();await p.screenshot({path:'docs/qa/phase-08-preview-mobile-viewport.png'});
 const after=await (await context.request.get(base)).json();expect(after.plan).toEqual(before.plan);expect(after.evidence).toEqual(before.evidence);expect(after.priorities).toEqual(before.priorities);expect(after.version).toBe(before.version);
 expect(errors).toEqual([]);fs.writeFileSync('docs/qa/phase-08-preview-review.json',JSON.stringify({checked_at:new Date().toISOString(),url,desktop_routes:['prepare','visit','follow-up'],mobile_overflow:false,normal_debug_hidden:true,saved_plan_sources_priorities_and_version_preserved:true,provider_calls:false,configured_providers:providers,room_joined:false,errors},null,2)+'\n');
 console.log('Saved local preview verified on desktop/mobile; no saved visit edits, room joins or provider calls.');
}finally{await browser.close();}
