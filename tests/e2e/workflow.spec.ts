import {test,expect,type BrowserContext} from '@playwright/test';
import fs from 'node:fs';
import {base,command,launch} from './helpers';
import {setup,finish,speech} from './speech-helpers';
const office=base+'/execution';
async function state(context:BrowserContext){return (await context.request.get(office)).json();}
async function post(context:BrowserContext,path:string,data:unknown){
  const me=await (await context.request.get('/api/auth/me')).json();
  const response=await context.request.post(base+path,{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data});
  expect(response.status()).toBe(200);return response.json();
}

test('sandbox execution completes the conversation loop with a reconciled office receipt',async({baseURL,browser})=>{
  test.setTimeout(180000);const env=await setup(baseURL);const {p,d,patient,doctor}=env;
  const family=await browser.newContext();await launch(family,'family');const f=await family.newPage();
  const errors:string[]=[];for(const page of [p,d,f])page.on('pageerror',e=>errors.push(e.name));
  try{
    await post(patient,'/understanding/processing',{command_id:crypto.randomUUID(),enabled:true});
    await post(patient,'/understanding/fixture-turns',{command_id:crypto.randomUUID(),speaker:'clinician',text:'Maria will arrange the lab visit at Riverside Lab on Thursday after the office sends the order.'});
    await expect.poll(async()=>{const v=await (await patient.request.get(base)).json();return v.plan.some((x:{title:string})=>x.title==='Arrange the lab visit');}).toBe(true);
    let visit=await (await patient.request.get(base)).json();let item=visit.plan.find((x:{title:string})=>x.title==='Arrange the lab visit');
    const itemId=item.id;
    async function share(){
      visit=await (await patient.request.get(base)).json();item=visit.plan.find((x:{id:string})=>x.id===itemId);
      for(const ref of item.evidence_refs)await command(patient,{type:'sharing.changed',item_id:ref,audiences:['clinician','family']});
      await command(patient,{type:'sharing.changed',item_id:itemId,audiences:['clinician','family']});
    }
    await expect.poll(async()=>(await state(family)).actions.length).toBe(0);
    await share();await f.goto('/follow-up');
    const region=p.getByRole('region',{name:'Office follow-through',exact:true});
    const step=region.getByRole('article',{name:'Office follow-through: Arrange the lab visit',exact:true});
    const doctorStep=d.getByRole('article',{name:'Office follow-through: Arrange the lab visit',exact:true});
    await expect(step).toBeVisible();
    await region.getByText('Development sandbox · change office conditions',{exact:true}).click();
    await region.getByRole('button',{name:'No slots',exact:true}).click();
    await step.getByRole('button',{name:'Allow office checks',exact:true}).click();
    await step.getByRole('button',{name:'Check this window',exact:true}).click();
    await expect(step.getByText('No suitable slot',{exact:true})).toBeVisible();
    await p.getByRole('button',{name:'Help me keep track',exact:true}).click();
    const cue=p.locator('.private-cue').filter({hasText:'Office check · Arrange the lab visit'});
    await expect(cue).toBeVisible();expect((await speech(doctor)).cues).toEqual([]);
    await expect(cue.getByRole('button',{name:'Ask Vene to say this aloud',exact:true})).toBeEnabled();
    await cue.getByRole('button',{name:'Ask Vene to say this aloud',exact:true}).click();
    await expect(p.locator('[data-vene-output-active="true"]')).toBeVisible({timeout:25000});
    await expect.poll(async()=>(await speech(patient)).receipts[0]?.state,{timeout:20000}).toBe('completed');
    expect((await speech(patient)).receipts[0].played_text).toContain('sandbox office found no morning slot');
    await p.screenshot({path:'docs/qa/phase-06-no-slot-cue.png',fullPage:true});
    // Correct the sourced step through the normal product service, then share its new source.
    await post(patient,'/understanding/plan/'+itemId+'/correct',{command_id:crypto.randomUUID(),expected_item_revision:item.revision,owner:'Maria',timeframe:'Tuesday afternoon',location:'Riverside Lab',detail:'I will arrange the lab visit on Tuesday afternoon after Dr. Chen confirms the order.'});
    await share();await region.getByRole('button',{name:'Slots available',exact:true}).click();
    await step.getByLabel('Appointment window for Arrange the lab visit',{exact:true}).selectOption('afternoon');
    await step.getByRole('button',{name:'Check this window',exact:true}).click();
    await expect(step.getByText('Slot suggested · not booked',{exact:true})).toBeVisible();
    await doctorStep.getByRole('button',{name:'Confirm intended lab step',exact:true}).click();
    await expect(step.getByText('Clinician: confirmed',{exact:true})).toBeVisible();
    await step.getByRole('button',{name:'Approve this sandbox reservation',exact:true}).click();
    await expect(step.getByText('Waiting on required sandbox order. No booking dispatched.',{exact:true})).toBeVisible();
    expect((await state(patient)).actions[0].receipt).toBeNull();
    await p.screenshot({path:'docs/qa/phase-06-missing-order.png',fullPage:true});
    // Expired and delayed availability do not become suggested or booked slots.
    await region.getByRole('button',{name:'Expired availability',exact:true}).click();await step.getByRole('button',{name:'Check this window',exact:true}).click();
    await expect(step.getByText('Availability expired',{exact:true})).toBeVisible();
    await region.getByRole('button',{name:'Delayed lookup',exact:true}).click();await step.getByRole('button',{name:'Check this window',exact:true}).click();
    await expect(step.getByText('Office unavailable',{exact:true})).toBeVisible();
    // Actual HTTP timeout after an actual persisted write; the worker must reconcile.
    await region.getByRole('button',{name:'Timeout after write',exact:true}).click();await step.getByRole('button',{name:'Check this window',exact:true}).click();
    await doctorStep.getByRole('button',{name:'Confirm and issue sandbox order',exact:true}).click();
    await expect.poll(async()=>(await state(patient)).actions[0].order_available).toBe(true);
    await expect(step.getByText('Order: sandbox order available',{exact:true})).toBeVisible();
    await step.getByRole('button',{name:'Approve this sandbox reservation',exact:true}).click();
    const observed:string[]=[];
    await expect.poll(async()=>{const a=(await state(patient)).actions[0];observed.push(a.state);return a.state;},{intervals:[100,100,150,250],timeout:20000}).toBe('confirmed');
    expect(observed).toContain('unknown');
    const confirmed=(await state(patient)).actions[0];expect(confirmed.receipt.request_id).toBe(confirmed.id);
    await expect(f.getByText('Reservation confirmed',{exact:true})).toBeVisible();
    await expect(step.getByText(confirmed.receipt.receipt_id,{exact:true})).toBeVisible();
    await p.screenshot({path:'docs/qa/phase-06-confirmed-desktop.png',fullPage:true});
    await region.screenshot({path:'docs/qa/phase-06-office-desktop.png'});
    await p.setViewportSize({width:390,height:844});await p.evaluate(()=>{if(document.activeElement instanceof HTMLElement)document.activeElement.blur();window.scrollTo(0,0);});
    expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await p.screenshot({path:'docs/qa/phase-06-confirmed-mobile.png',fullPage:true});
    await region.screenshot({path:'docs/qa/phase-06-office-mobile.png'});
    await post(patient,'/execution/items/'+itemId+'/scope',{allowed:false});
    expect((await state(patient)).actions[0].receipt.receipt_id).toBe(confirmed.receipt.receipt_id);
    expect(await (await family.request.get(office)).text()).not.toContain('session_hash');
    expect(errors).toEqual([]);
    fs.writeFileSync('docs/qa/phase-06-browser-evidence.json',JSON.stringify({checked_at:new Date().toISOString(),actual_media:true,office:'independent local HTTP service',conversation_input:'original fictional text; fixture interpreter',tts:'Windows offline voice',observed_states:observed,receipt_id:confirmed.receipt.receipt_id,request_id:confirmed.id,missing_order_prevented_dispatch:true,expired_and_delayed_results_honest:true,family_confirmed:true,receipt_survived_withdrawal:true,mobile_overflow:false,errors},null,2)+'\n');
  }finally{await family.close();await finish(env);}
});
