import {evidence} from './platform';
import {test,expect,type BrowserContext,type Page} from '@playwright/test';
import fs from 'node:fs';

// Phase 9: several errands from one conversation, approved together, confirmed separately.
// Uses the James and Asha fictional encounters so Maria's Phase 6 lab flow stays untouched.
async function caseLaunch(context:BrowserContext,caseName:string,role:string){
  await context.addInitScript(()=>sessionStorage.setItem('vene-demo-tools','true'));
  const invitation=await context.request.post('/api/dev/invitations',{headers:{'x-vene-intent':'mutation'},data:{case:caseName,persona:role}});expect(invitation.status()).toBe(200);
  const response=await context.request.post('/api/auth/redeem',{headers:{'x-vene-intent':'mutation'},data:{token:(await invitation.json()).token}});expect(response.status()).toBe(200);return response.json();
}

async function encounter(browser:any,caseName:string){
  const patient=await browser.newContext(),doctor=await browser.newContext(),family=await browser.newContext();
  const identity=await caseLaunch(patient,caseName,'patient');await caseLaunch(doctor,caseName,'clinician');await caseLaunch(family,caseName,'family');
  const root='/api/encounters/'+identity.encounter_id;
  async function post(context:BrowserContext,path:string,data:unknown){
    const me=await (await context.request.get('/api/auth/me')).json();
    const r=await context.request.post(root+path,{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data});
    expect(r.status(),await r.text()).toBe(200);return r.json();
  }
  async function share(id:string,audiences=['clinician','family']){
    const v=await (await patient.request.get(root)).json();
    return post(patient,'/commands',{command_id:crypto.randomUUID(),expected_version:v.version,command:{type:'sharing.changed',item_id:id,audiences}});
  }
  async function shareStep(title:string,audiences=['clinician','family']){
    const step=(await (await patient.request.get(root)).json()).plan.find((x:{title:string})=>x.title===title);
    for(const ref of step.evidence_refs)await share(ref,audiences);await share(step.id,audiences);return step;
  }
  async function actions(context:BrowserContext){return (await (await context.request.get(root+'/execution')).json()).actions;}
  return {patient,doctor,family,root,post,shareStep,actions,close:()=>Promise.all([patient.close(),doctor.close(),family.close()])};
}

async function speak(env:Awaited<ReturnType<typeof encounter>>,owner:string,turns=TURNS){
  await env.post(env.patient,'/understanding/processing',{command_id:crypto.randomUUID(),enabled:true});
  for(const text of turns)await env.post(env.patient,'/understanding/fixture-turns',{command_id:crypto.randomUUID(),speaker:'clinician',text:text.replaceAll('OWNER',owner)});
  await expect.poll(async()=>(await (await env.patient.request.get(env.root)).json()).plan.filter((x:{kind:string})=>['imaging','prescription'].includes(x.kind)).length,{timeout:20000}).toBe(2);
}

function row(checklist:ReturnType<Page['getByRole']>,title:string){
  return checklist.locator('.walkout-row').filter({hasText:title});
}

async function check(page:Page,title:string){
  const step=page.getByRole('article',{name:'Office follow-through: '+title,exact:true});
  await step.getByRole('button',{name:'Allow office checks',exact:true}).click();
  await step.getByRole('button',{name:'Check this window',exact:true}).click();
  return step;
}

const TURNS=['OWNER will schedule the MRI at Lakeside Imaging on Wednesday after the office sends the order.',
  'OWNER will pick up the new prescription at Main Street Pharmacy on Thursday.'];
// The sandbox offices are one shared fictional calendar, so a second encounter asks elsewhere.
const OTHER_TURNS=['OWNER will schedule the MRI at Northgate Imaging on Wednesday after the office sends the order.',
  'OWNER will pick up the new prescription at Harbor Pharmacy on Thursday.'];

// Latest action per step, for these steps only; earlier scenarios may have added others.
async function stepStates(env:Awaited<ReturnType<typeof encounter>>,titles:string[]){
  const plan=(await (await env.patient.request.get(env.root)).json()).plan;
  const ids=new Map(plan.filter((x:{title:string})=>titles.includes(x.title)).map((x:{id:string,title:string})=>[x.id,x.title]));
  const latest=new Map<string,{state:string,kind:string,receipt:{receipt_id:string}|null}>();
  for(const a of await env.actions(env.patient))if(ids.has(a.item_id)&&!latest.has(a.item_id))latest.set(a.item_id,a);
  return [...latest.values()];
}
const STEPS={imaging:'Schedule the imaging',pharmacy:'Pick up the new prescription',referral:'Referral document still needed'};

test('walk-out follow-through confirms several errands and a family member answers a scoped ask',async({browser})=>{
  test.setTimeout(180000);
  const env=await encounter(browser,'james');
  const p=await env.patient.newPage(),d=await env.doctor.newPage(),f=await env.family.newPage();
  const errors:string[]=[];for(const page of [p,d,f])page.on('pageerror',e=>errors.push(e.name));
  try{
    await speak(env,'James');
    for(const title of Object.values(STEPS))await env.shareStep(title,['clinician']);
    await Promise.all([p.goto('/visit'),d.goto('/visit'),f.goto('/follow-up')]);
    const region=p.getByRole('region',{name:'Office follow-through',exact:true});
    const checklist=region.getByRole('list',{name:'Before you leave checklist',exact:true});
    // Earlier scenarios may have added other steps to this encounter; assert these three.
    for(const title of Object.values(STEPS))await expect(row(checklist,title)).toContainText('Not checked yet');
    await p.screenshot({path:evidence('phase-09-checklist-start.png'),fullPage:true});

    for(const title of Object.values(STEPS)){const step=await check(p,title);await expect(step.getByText('Slot suggested · not booked',{exact:true})).toBeVisible();}
    await expect(checklist).toContainText('Waiting on clinician confirmation and the imaging order');
    await expect(region.getByRole('button',{name:/Approve the ready steps/})).toHaveCount(0);

    // The clinician confirms each step and sends the institution's own sandbox document.
    for(const [title,button] of [[STEPS.imaging,'Confirm and send sandbox imaging order'],[STEPS.pharmacy,'Confirm and send sandbox prescription'],[STEPS.referral,'Confirm and send sandbox referral packet']]){
      const step=d.getByRole('article',{name:'Office follow-through: '+title,exact:true});
      await step.getByRole('button',{name:button,exact:true}).click();
      await expect(step.getByText('Clinician: confirmed',{exact:true})).toBeVisible();
    }
    const approve=region.getByRole('button',{name:'Approve the ready steps (3)',exact:true});
    await expect(approve).toBeVisible();await expect(checklist).toContainText('Ready for your approval');
    await p.screenshot({path:evidence('phase-09-ready.png'),fullPage:true});
    await approve.click();
    await expect(region.getByRole('status')).toContainText('3 steps sent to the sandbox.');
    await expect.poll(async()=>(await stepStates(env,Object.values(STEPS))).map(a=>a.state).sort().join(','),{timeout:20000}).toBe('confirmed,confirmed,confirmed');
    for(const title of Object.values(STEPS))await expect(row(checklist,title)).toHaveClass(/done/);
    await expect(checklist).toContainText('Confirmed by the pharmacy with a sandbox receipt');
    const receipts=(await stepStates(env,Object.values(STEPS))).map(a=>a.receipt!.receipt_id);
    expect(new Set(receipts).size).toBe(3);

    // Sharing after confirmation changes approval fingerprints, not what the office booked.
    for(const title of Object.values(STEPS))await env.shareStep(title);

    await p.goto('/follow-up');
    const overview=p.getByLabel('Next-step overview',{exact:true});
    for(const [title,label] of [[STEPS.imaging,'Imaging appointment confirmed'],[STEPS.pharmacy,'Pickup confirmed'],[STEPS.referral,'Specialist appointment confirmed']])
      await expect(overview.getByRole('article',{name:'Next-step status: '+title,exact:true})).toContainText(label);
    await expect(overview.getByText('Nothing for you to relay yet.',{exact:true})).toHaveCount(0);
    await overview.screenshot({path:evidence('product-follow-up-desktop.png')});
    await p.setViewportSize({width:390,height:844});
    expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await overview.screenshot({path:evidence('product-follow-up-mobile.png')});
    await p.setViewportSize({width:1280,height:720});
    // Even a completed arrangement retains the patient's permission control.
    const confirmedPharmacy=p.getByRole('region',{name:'Office follow-through',exact:true}).getByRole('article',{name:'Office follow-through: '+STEPS.pharmacy,exact:true});
    await confirmedPharmacy.getByRole('button',{name:'Withdraw office permission',exact:true}).click();
    await expect(confirmedPharmacy).toContainText('Pickup confirmed');
    await p.goto('/visit');

    // A scoped ask: the family member sees purpose, when and where, and answers for themselves.
    const pharmacy=region.getByRole('article',{name:'Office follow-through: '+STEPS.pharmacy,exact:true});
    await pharmacy.getByRole('button',{name:'Ask Nina to help with this',exact:true}).click();
    const familyCircle=f.getByLabel('Care circle',{exact:true});
    await expect(familyCircle).toContainText('Pick up the new prescription');
    await expect(familyCircle).toContainText('Main Street Pharmacy (fictional)');
    await f.screenshot({path:evidence('phase-09-family-ask.png'),fullPage:true});
    await familyCircle.getByRole('button',{name:'Yes, I can help',exact:true}).click();
    await expect(p.getByLabel('Care circle',{exact:true})).toContainText('Nina Patel: said yes');
    const familyCirclePayload=await (await env.family.request.get(env.root+'/care-circle')).text();
    for(const hidden of ['receipt','order','digest','session'])expect(familyCirclePayload).not.toContain(hidden);
    const familyOffice=await env.actions(env.family);
    expect(familyOffice.every((a:{digest:string|null})=>a.digest===null)).toBe(true);

    await p.screenshot({path:evidence('phase-09-confirmed-desktop.png'),fullPage:true});
    await p.setViewportSize({width:390,height:844});await p.evaluate(()=>window.scrollTo(0,0));
    expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await region.screenshot({path:evidence('phase-09-confirmed-mobile.png')});
    expect(errors).toEqual([]);
    fs.writeFileSync(evidence('phase-09-walkout.json'),JSON.stringify({checked_at:new Date().toISOString(),encounter:'james (fictional)',
      errands:['imaging','prescription','referral'],receipts,family_answer:'accepted',interpreter:'fixture'},null,2)+'\n');
  }finally{await env.close();}
});

test('walk-out follow-through reports a rejection and reconciles a timeout without rolling back the others',async({browser})=>{
  test.setTimeout(180000);
  const env=await encounter(browser,'asha');
  const p=await env.patient.newPage(),d=await env.doctor.newPage();
  try{
    await speak(env,'Asha',OTHER_TURNS);
    for(const title of [STEPS.imaging,STEPS.pharmacy])await env.shareStep(title);
    await Promise.all([p.goto('/visit'),d.goto('/visit')]);
    const region=p.getByRole('region',{name:'Office follow-through',exact:true});
    // Two different sandbox offices misbehave; scenario changes precede lookups because they
    // advance that office's availability revision.
    await region.getByText('Development sandbox · change office conditions',{exact:true}).click();
    await region.getByLabel('Sandbox office',{exact:true}).selectOption('imaging');
    await region.getByRole('button',{name:'Office rejects',exact:true}).click();
    await region.getByLabel('Sandbox office',{exact:true}).selectOption('prescription');
    await region.getByRole('button',{name:'Timeout after write',exact:true}).click();
    for(const title of [STEPS.imaging,STEPS.pharmacy])await check(p,title);
    for(const [title,button] of [[STEPS.imaging,'Confirm and send sandbox imaging order'],[STEPS.pharmacy,'Confirm and send sandbox prescription']])
      await d.getByRole('article',{name:'Office follow-through: '+title,exact:true}).getByRole('button',{name:button,exact:true}).click();
    await region.getByRole('button',{name:'Approve the ready steps (2)',exact:true}).click();
    const observed:string[]=[];
    await expect.poll(async()=>{const a=await stepStates(env,[STEPS.imaging,STEPS.pharmacy]);const states=Object.fromEntries(a.map(x=>[x.kind,x.state]));observed.push(states.prescription);
      return states.imaging+','+states.prescription;},{intervals:[100,150,250],timeout:25000}).toBe('rejected,confirmed');
    expect(observed).toContain('unknown');
    const checklist=region.getByRole('list',{name:'Before you leave checklist',exact:true});
    await expect(row(checklist,STEPS.imaging)).toHaveClass(/problem/);
    await expect(row(checklist,STEPS.pharmacy)).toHaveClass(/done/);
    await p.screenshot({path:evidence('phase-09-partial.png'),fullPage:true});
  }finally{await env.close();}
});
