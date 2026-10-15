import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import {ownedProcess} from './process-control';
import {setup,finish} from './speech-helpers';
import {base} from './helpers';

async function caseLaunch(context,caseName,role){
  await context.addInitScript(()=>sessionStorage.setItem('vene-demo-tools','true'));
  const invitation=await context.request.post('/api/dev/invitations',{headers:{'x-vene-intent':'mutation'},data:{case:caseName,persona:role}});expect(invitation.status()).toBe(200);
  const response=await context.request.post('/api/auth/redeem',{headers:{'x-vene-intent':'mutation'},data:{token:(await invitation.json()).token}});expect(response.status()).toBe(200);return response.json();
}

test('packaging variations exercise distinct dates locations dependencies and privacy in three fictional encounters',async({browser})=>{
  test.setTimeout(180000);const outcomes=[];
  for(const [caseName,owner,day,date,place,window] of [['james','James','Wednesday','2026-10-21','Harbor Lab','morning'],['asha','Asha','Friday','2026-10-23','Hilltop Lab','afternoon']] as const){
    const patient=await browser.newContext(),doctor=await browser.newContext(),family=await browser.newContext();
    const p=await patient.newPage(),d=await doctor.newPage(),f=await family.newPage();
    try{
      const identity=await caseLaunch(patient,caseName,'patient');await caseLaunch(doctor,caseName,'clinician');await caseLaunch(family,caseName,'family');
      const root='/api/encounters/'+identity.encounter_id;
      async function post(context,path,data){const me=await (await context.request.get('/api/auth/me')).json();const r=await context.request.post(root+path,{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data});expect(r.status()).toBe(200);return r.json();}
      async function share(id){const v=await (await patient.request.get(root)).json();return post(patient,'/commands',{command_id:crypto.randomUUID(),expected_version:v.version,command:{type:'sharing.changed',item_id:id,audiences:['clinician','family']}});}
      await p.goto('/prepare');await expect(p.locator('#main').getByText(caseName==='james'?'James Patel':'Asha Rao',{exact:true})).toBeVisible();
      await post(patient,'/understanding/processing',{command_id:crypto.randomUUID(),enabled:true});
      await post(patient,'/understanding/fixture-turns',{command_id:crypto.randomUUID(),speaker:'clinician',text:`${owner} will arrange the lab visit at ${place} on ${day} after the office sends the order.`});
      await expect.poll(async()=>(await (await patient.request.get(root)).json()).plan.some(x=>x.origin==='interpretation')).toBe(true);
      const v=await (await patient.request.get(root)).json();const step=v.plan.find(x=>x.origin==='interpretation');expect(step.owner).toBe(owner);expect(step.location).toBe(place);expect(step.timeframe).toBe(day);
      expect((await (await doctor.request.get(root)).json()).plan.some(x=>x.id===step.id)).toBe(false);
      for(const id of step.evidence_refs)await share(id);await share(step.id);
      await Promise.all([p.goto('/visit'),d.goto('/visit'),f.goto('/follow-up')]);
      const office=p.getByRole('region',{name:'Office follow-through',exact:true});const item=office.getByRole('article',{name:'Office follow-through: '+step.title,exact:true});
      await office.getByText('Development sandbox \u00b7 change office conditions',{exact:true}).click();
      await office.getByRole('button',{name:'Slots available',exact:true}).click();
      await item.getByLabel('Requested location for '+step.title,{exact:true}).selectOption(place);
      await item.getByLabel('Requested date for '+step.title,{exact:true}).fill(date);
      await item.getByLabel('Appointment window for '+step.title,{exact:true}).selectOption(window);
      await item.getByRole('button',{name:'Allow office checks',exact:true}).click();await item.getByRole('button',{name:'Check this window',exact:true}).click();
      await expect(item.getByText('Slot suggested · not booked',{exact:true})).toBeVisible();
      await item.getByRole('button',{name:'Approve this sandbox reservation',exact:true}).click();await expect(item.getByText(/Waiting on clinician confirmation, required sandbox order/)).toBeVisible();
      const dItem=d.getByRole('article',{name:'Office follow-through: '+step.title,exact:true});
      await dItem.getByRole('button',{name:'Confirm and issue sandbox order',exact:true}).click();await expect(item.getByText('Order: sandbox order available',{exact:true})).toBeVisible();
      if(caseName==='james'){
        await office.getByRole('button',{name:'Office rejects',exact:true}).click();
        await item.getByRole('button',{name:'Approve this sandbox reservation',exact:true}).click();await expect(item.getByText('Office rejected request',{exact:true})).toBeVisible();
        await office.getByRole('button',{name:'Slots available',exact:true}).click();await item.getByRole('button',{name:'Check this window',exact:true}).click();
        await dItem.getByRole('button',{name:'Confirm and issue sandbox order',exact:true}).click();await expect(item.getByText('Order: sandbox order available',{exact:true}).first()).toBeVisible();
      }
      await item.getByRole('button',{name:'Approve this sandbox reservation',exact:true}).click();await expect(item.getByText('Reservation confirmed',{exact:true})).toBeVisible({timeout:15000});
      await expect(f.getByText('Reservation confirmed',{exact:true})).toBeVisible();
      const result=(await (await patient.request.get(root+'/execution')).json()).actions[0];expect(result.slot.location).toBe(place);expect(result.slot.day).toBe(date);expect(result.receipt.slot_id).toBe(result.slot.id);
      const familyPayload=await (await family.request.get(root+'/execution')).text();expect(familyPayload).not.toContain('PRIVATE_CANARY');expect(familyPayload).not.toContain('session_hash');
      await p.goto('/follow-up');await expect(p.getByRole('region',{name:'After-visit continuity',exact:true})).toBeVisible();
      await expect(p.getByText('Reservation confirmed',{exact:true})).toBeVisible();
      await expect(p.getByLabel('Requested date for '+step.title,{exact:true})).toHaveValue(date);
      await p.evaluate(()=>{if(document.activeElement instanceof HTMLElement)document.activeElement.blur();window.scrollTo(0,0);});
      await p.screenshot({path:'docs/qa/phase-08-'+caseName+'-desktop.png',fullPage:true});
      outcomes.push({case:caseName,encounter_id:identity.encounter_id,date,place,window,missing_order_blocked:true,office_rejection_exercised:caseName==='james',receipt_id:result.receipt.receipt_id,private_payload_absent:true});
    }finally{await Promise.all([patient.close(),doctor.close(),family.close()]);}
  }
  fs.writeFileSync('docs/qa/phase-08-variations.json',JSON.stringify({checked_at:new Date().toISOString(),baseline_maria:'complete workflow in workflow.spec.ts and x_continuity.spec.ts',variations:outcomes,scripted:true,free_form_model_quality:false},null,2)+'\n');
});

test('packaging recovery marks actual processing gaps and preserves the human room',async({baseURL})=>{
  test.setTimeout(240000);const env=await setup(baseURL);const {p,patient}=env;const observations=[];const started=Date.now();
  try{
    await ownedProcess('stop','voice');await ownedProcess('restart','voice');
    await expect.poll(async()=>{const c=await (await patient.request.get(base+'/call',{maxRetries:2})).json();observations.push({elapsed_ms:Date.now()-started,state:c.state,ready:c.worker_ready,paused:c.manual_pause,gap:!!c.gap_since,people:c.participants.filter(x=>x.present).length});return c.worker_ready&&!!c.gap_since&&c.manual_pause&&c.state==='paused';},{timeout:60000}).toBe(true);
    await expect(p.getByText('Vene processing was interrupted. Some words may be missing from these notes. Ask the speaker to repeat anything important.',{exact:true})).toBeVisible();
    const recovered=await (await patient.request.get(base+'/call',{maxRetries:2})).json();expect(recovered.manual_pause).toBe(true);expect(recovered.participants.filter(c=>c.present).length).toBe(2);
    await p.getByRole('button',{name:'Resume Vene processing',exact:true}).click();await expect.poll(async()=>(await (await patient.request.get(base+'/call',{maxRetries:2})).json()).state).toBe('active');
    fs.writeFileSync('docs/qa/phase-08-voice-recovery.json',JSON.stringify({checked_at:new Date().toISOString(),owned_voice_process_restarted:true,gap_visible:true,manual_resume_required:true,human_room_preserved:true},null,2)+'\n');
  }finally{fs.writeFileSync('docs/qa/phase-08-voice-recovery-observations.json',JSON.stringify({checked_at:new Date().toISOString(),observations},null,2)+'\n');await finish(env);}
});

test('packaging accessibility supports ordinary views keyboard focus reduced motion and 200 percent reflow',async({browser})=>{
  test.setTimeout(120000);const context=await browser.newContext({reducedMotion:'reduce',viewport:{width:1280,height:900}}),p=await context.newPage();
  const errors:string[]=[];p.on('pageerror',e=>errors.push(e.name));
  try{
    await p.goto('/dev');await expect(p.getByLabel('Fictional encounter',{exact:true})).toBeVisible();
    await expect(p.getByRole('checkbox',{name:'Show fictional scenario controls (developer)',exact:true})).not.toBeChecked();
    await p.getByRole('button',{name:'Continue as Maria'}).click();
    await expect(p.getByText('Follow-up with Dr. Chen',{exact:true})).toBeVisible();
    await p.keyboard.press('Tab');await expect(p.getByRole('link',{name:'Skip to content',exact:true})).toBeFocused();
    const focus=await p.getByRole('link',{name:'Skip to content',exact:true}).evaluate(el=>({outline:getComputedStyle(el).outlineStyle,rect:el.getBoundingClientRect().toJSON()}));
    expect(focus.outline).not.toBe('none');expect(focus.rect.width).toBeGreaterThan(0);
    await p.keyboard.press('Enter');expect(await p.evaluate(()=>location.hash)).toBe('#main');
    const checks=[];
    for(const route of ['/prepare','/visit','/follow-up']){
      await p.goto(route);await expect(p.locator('main#main')).toBeVisible();
      await expect(p.getByText('Fictional conversation input',{exact:true})).toHaveCount(0);
      await expect(p.getByText('Development sandbox \u00b7 change office conditions',{exact:true})).toHaveCount(0);
      await expect(p.getByText('Development sandbox \u00b7 office replies',{exact:true})).toHaveCount(0);
      const unnamed=await p.evaluate(()=>Array.from(document.querySelectorAll('button,input,select,textarea')).filter(el=>{
        if(el instanceof HTMLInputElement&&el.type==='hidden')return false;
        return !(el.getAttribute('aria-label')||el.getAttribute('aria-labelledby')||el.textContent?.trim()||(el instanceof HTMLInputElement||el instanceof HTMLSelectElement||el instanceof HTMLTextAreaElement)&&el.labels?.length);
      }).map(el=>el.tagName));expect(unnamed).toEqual([]);
      await p.evaluate(()=>{document.documentElement.style.zoom='2';window.scrollTo(0,0);});
      const reflow=await p.evaluate(()=>({route:location.pathname,width:innerWidth,scroll:document.documentElement.scrollWidth,offenders:Array.from(document.querySelectorAll('main *')).filter(el=>el.getBoundingClientRect().right>innerWidth+1).map(el=>({tag:el.tagName,class:el.className,right:el.getBoundingClientRect().right,text:el.textContent?.slice(0,60)})).slice(0,12)}));
      expect(reflow.scroll,JSON.stringify(reflow)).toBeLessThanOrEqual(reflow.width);
      expect(await p.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);
      await p.screenshot({path:'docs/qa/phase-08-'+route.slice(1)+'-zoom.png'});checks.push({route,zoom:2,unnamed_controls:0,overflow:false});
      await p.evaluate(()=>document.documentElement.style.zoom='1');
    }
    expect(errors).toEqual([]);
    fs.writeFileSync('docs/qa/phase-08-accessibility.json',JSON.stringify({checked_at:new Date().toISOString(),keyboard_skip_link:true,focus_outline:focus.outline,reduced_motion:true,ordinary_debug_hidden:true,checks,errors,screen_reader_audit:'not exercised'},null,2)+'\n');
  }finally{await context.close();}
});
