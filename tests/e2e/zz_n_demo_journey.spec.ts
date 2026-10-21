import {test,expect,type Frame} from '@playwright/test';
import {evidence} from './platform';

// The single-tab demo beyond the lab moment: preparation memory, the plan's prior authorization,
// every errand's receipt and the family follow-through, each pane on its own session.
// Typed conversation exercises ordinary services; real WebRTC is covered separately.
async function asPatient(frame:Frame,path:string,body:unknown){
  return frame.evaluate(async({path,body})=>{
    const run=location.pathname.split('/')[3],base='/api/demo/'+run+'/patient';
    const me=await(await fetch(base+'/auth/me')).json();
    const r=await fetch(base+'/encounters/'+run+path,{method:'POST',headers:{'Content-Type':'application/json','x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},body:JSON.stringify(body)});
    return r.status;
  },{path,body});
}
async function payload(frame:Frame,role:string,path=''){
  return frame.evaluate(async({role,path})=>{const run=location.pathname.split('/')[3];return (await fetch('/api/demo/'+run+'/'+role+'/encounters/'+run+path)).text();},{role,path});
}

test('demo chapters carry memory, a prior authorization, independent receipts and a scoped family follow-through',async({page})=>{
  test.setTimeout(240000);
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1440,height:1050});
  await page.goto('/demo');
  await page.getByRole('button',{name:'Start demo',exact:true}).click();
  const p=page.frameLocator('iframe[title="Maria’s private phone"]'),d=page.frameLocator('iframe[title="Dr. Chen’s clinician view"]');

  // Before: the July visit's open loops, private until Maria approves her list.
  await expect(p.getByText(/Vene found \d things worth bringing up/)).toBeVisible();
  const patient=()=>page.frames().find(f=>f.url().endsWith('/patient'))!,doctor=()=>page.frames().find(f=>f.url().endsWith('/clinician'))!;
  expect(await payload(doctor(),'clinician')).not.toContain('blood pressure');
  // A slow carry request must prevent approval until the refreshed list is available.
  let releaseCarry!:()=>void;
  const carryHeld=new Promise<void>(resolve=>{releaseCarry=resolve;});
  await page.route('**/memory/carry',async route=>{await carryHeld;await route.continue();});
  await p.getByRole('button',{name:/^Add \d to my visit list$/}).click();
  try{await expect(p.getByRole('button',{name:'Approve my visit list'})).toBeDisabled();}
  finally{releaseCarry();}
  await p.getByRole('button',{name:'Approve my visit list'}).click();
  await expect(p.getByRole('button',{name:'Withdraw approval'})).toBeVisible();
  await expect(d.getByRole('heading',{name:'Do I still need to keep my blood pressure log?'})).toBeVisible();
  expect(await payload(doctor(),'clinician')).not.toContain('Mention my morning availability');

  // Before you leave. Maria's permission is given through her own session; the WebRTC call is covered elsewhere.
  await page.getByRole('button',{name:'Next: During'}).click();
  await page.getByRole('button',{name:'Next: Before you leave'}).click();
  expect(await asPatient(patient(),'/understanding/processing',{command_id:crypto.randomUUID(),enabled:true})).toBe(200);
  expect(await asPatient(patient(),'/feasibility/standing',{kinds:['scheduling','coverage']})).toBe(200);
  await d.getByRole('button',{name:'Say this',exact:true}).click();
  await expect(p.getByLabel('Private coverage cue')).toContainText('requires prior authorization',{timeout:30000});
  expect(await payload(doctor(),'clinician','/feasibility')).not.toContain('prior authorization');
  await p.getByRole('button',{name:'Ask Dr. Chen now'}).click();
  await d.getByRole('button',{name:'The office will submit prior authorization'}).click();
  await p.getByRole('button',{name:/with the offices$/}).click();
  for(const title of ['Schedule the imaging','Pick up the new prescription'])
    await d.getByRole('region',{name:'Your part'}).getByRole('listitem').filter({hasText:title}).getByRole('button',{name:/^Confirm & send/}).click();
  const approve=p.getByRole('button',{name:/^Approve /});
  await expect.poll(async()=>{if(await approve.isVisible())await approve.click().catch(()=>{});return p.getByText('All set before you leave.').isVisible();},{timeout:60000,intervals:[1500]}).toBe(true);
  const checklist=p.getByRole('list',{name:'Before you leave checklist'});
  await expect(checklist.getByRole('listitem')).toHaveCount(3);
  await expect(checklist).toContainText('Approved by the health plan');
  await page.screenshot({path:evidence('demo-journey-leave.png'),fullPage:true});

  // After: only what Maria sends reaches Elena, and the receipts stay current after sharing.
  await page.getByRole('button',{name:'Next: After'}).click();
  await page.getByLabel('Show Elena’s view').check();
  const f=page.frameLocator('iframe[title="Elena’s family view"]');
  await expect(f.getByRole('heading',{name:'Maria chooses what comes here.',exact:true})).toBeVisible();
  await expect(p.getByText('Elena will also be able to open these steps and their supporting notes.',{exact:false})).toBeVisible();
  await p.getByRole('button',{name:'Send to Elena'}).click();
  await expect(f.getByText('Update from Maria')).toBeVisible();
  await expect(f.locator('.demo-update-text')).toContainText('Imaging appointment confirmed (sandbox)');
  await expect(f.locator('.demo-update-text')).not.toContainText('No current office completion');
  await p.getByRole('button',{name:/to drive$/}).click();
  await f.getByRole('button',{name:'Yes, I can'}).click();
  await expect(p.getByText('Elena said yes.')).toBeVisible();
  await expect(d.getByRole('list',{name:'Before you leave checklist'}).getByRole('listitem')).toHaveCount(3);
  const family=page.frames().find(fr=>fr.url().endsWith('/family'))!;
  const shared=await payload(family,'family');
  for(const secret of ['Riverside','blood pressure','PRIVATE_CANARY'])expect(shared).not.toContain(secret);
  await page.screenshot({path:evidence('demo-journey-after.png'),fullPage:true});
  expect(errors).toEqual([]);
});
