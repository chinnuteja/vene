import {evidence} from './platform';
import {test,expect,type BrowserContext} from '@playwright/test';
import fs from 'node:fs';
import {base,command,launch} from './helpers';

// Phase 10: an obstacle found while the clinician is still in the room, answered there.
const checks=base+'/feasibility';
async function post(context:BrowserContext,path:string,data:unknown){
  const me=await (await context.request.get('/api/auth/me')).json();
  const response=await context.request.post(base+path,{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data});
  expect(response.status(),await response.text()).toBe(200);return response.json();
}
async function step(context:BrowserContext,title:string){return (await (await context.request.get(base)).json()).plan.find((x:{title:string})=>x.title===title);}
async function shareStep(context:BrowserContext,title:string){
  const item=await step(context,title);
  for(const ref of item.evidence_refs)await command(context,{type:'sharing.changed',item_id:ref,audiences:['clinician']});
  await command(context,{type:'sharing.changed',item_id:item.id,audiences:['clinician']});return item;
}
async function open(context:BrowserContext,kind:string){return (await (await context.request.get(checks)).json()).obstacles.filter((o:{kind:string,state:string})=>o.kind===kind&&o.state==='open');}
function percentile(values:number[],p:number){const sorted=[...values].sort((a,b)=>a-b);return sorted[Math.max(0,Math.ceil(p/100*sorted.length)-1)];}

test('in-room obstacle reaches the patient privately and the clinician resolves it before the visit ends',async({browser})=>{
  test.setTimeout(180000);
  const patient=await browser.newContext(),doctor=await browser.newContext(),family=await browser.newContext();
  await launch(patient);await launch(doctor,'clinician');await launch(family,'family');
  const p=await patient.newPage(),d=await doctor.newPage();
  const errors:string[]=[];for(const page of [p,d])page.on('pageerror',e=>errors.push(e.name));
  try{
    // Preparation: the patient chooses which read-only checks Vene may run.
    await p.goto('/prepare');
    await p.getByText('Practical checks during the visit',{exact:true}).click();
    const permission=p.getByRole('region',{name:'Visit checks permission',exact:true});
    await permission.getByRole('checkbox',{name:/Coverage/}).check();await permission.getByRole('checkbox',{name:/Pharmacy/}).check();
    await permission.getByRole('button',{name:'Save what Vene may check',exact:true}).click();
    await expect(permission).toContainText('On: coverage, pharmacy');
    await permission.screenshot({path:evidence('phase-10-permission.png')});

    await post(patient,'/understanding/processing',{command_id:crypto.randomUUID(),enabled:true});
    const spoken=Date.now();
    await post(patient,'/understanding/fixture-turns',{command_id:crypto.randomUUID(),speaker:'clinician',text:'Maria will schedule the MRI at Lakeside Imaging on Wednesday after the office sends the order.'});
    await post(patient,'/understanding/fixture-turns',{command_id:crypto.randomUUID(),speaker:'clinician',text:'Maria will pick up the Lorvexa prescription at Main Street Pharmacy on Thursday.'});
    await expect.poll(async()=>(await open(patient,'prior_authorization_required')).length,{timeout:15000}).toBe(1);
    const firstObstacleMs=Date.now()-spoken;
    await expect.poll(async()=>(await open(patient,'not_on_formulary')).length,{timeout:15000}).toBe(1);

    // Privately: the obstacle and its cue appear for the patient only.
    await p.goto('/visit');
    const panel=p.getByRole('region',{name:'In-visit checks',exact:true});
    await expect(panel.getByRole('article',{name:'Obstacle: Schedule the imaging',exact:true})).toContainText('Evergreen Basic (fictional) requires prior authorization for this imaging.');
    await expect(panel.getByRole('article',{name:'Obstacle: Pick up the new prescription',exact:true})).toContainText('Plan-listed covered options in the same class: Tamorin, Celvane. These are plan facts, not a recommendation.');
    const cue=p.locator('.private-cue').filter({hasText:'Practical check · Schedule the imaging'});
    await expect(cue).toBeVisible();
    const speech=await (await patient.request.get(base+'/speech')).json();
    const spokenTexts=speech.cues.map((c:{public_text:string})=>c.public_text).join(' ');
    for(const name of ['Lorvexa','Tamorin','Celvane','Maria'])expect(spokenTexts).not.toContain(name);
    expect((await (await doctor.request.get(base+'/speech')).json()).cues).toEqual([]);
    expect(await (await doctor.request.get(checks)).json()).toEqual({standing:null,checking:0,obstacles:[]});
    await panel.screenshot({path:evidence('phase-10-patient-obstacles.png')});await cue.screenshot({path:evidence('phase-10-private-cue.png')});

    // Shared with the clinician: they see the same facts and answer in their own view.
    await shareStep(patient,'Schedule the imaging');await shareStep(patient,'Pick up the new prescription');
    await d.goto('/visit');
    const clinicianPanel=d.getByRole('region',{name:'In-visit checks',exact:true});
    const auth=clinicianPanel.getByRole('article',{name:'Obstacle: Schedule the imaging',exact:true});
    await expect(auth).toBeVisible();
    expect(await (await family.request.get(checks)).json()).toEqual({standing:null,checking:0,obstacles:[]});
    await clinicianPanel.screenshot({path:evidence('phase-10-clinician-obstacles.png')});
    await auth.getByRole('button',{name:'The office will submit prior authorization',exact:true}).click();
    await clinicianPanel.getByRole('article',{name:'Obstacle: Pick up the new prescription',exact:true}).getByRole('button',{name:"I'll review coverage",exact:true}).click();
    await expect(clinicianPanel.getByRole('heading',{name:'Practical checks.',exact:true})).toBeVisible();

    // The patient sees the answers, and approves the plan submission herself.
    await expect(panel.getByRole('heading',{name:'Practical checks.',exact:true})).toBeVisible({timeout:10000});
    await expect(cue).toHaveCount(0,{timeout:10000});
    const region=p.getByRole('region',{name:'Office follow-through',exact:true});
    const checklist=region.getByRole('list',{name:'Before you leave checklist',exact:true});
    const authRow=checklist.locator('.walkout-row').filter({hasText:'Prior authorization for the imaging'});
    await expect(authRow).toContainText('Ready for your approval');
    await region.getByRole('button',{name:/Approve the ready steps/}).click();
    await expect(authRow).toContainText('Approved by the sandbox health plan',{timeout:20000});
    await checklist.screenshot({path:evidence('phase-10-authorized.png')});
    await p.setViewportSize({width:390,height:844});await p.evaluate(()=>window.scrollTo(0,0));
    expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await panel.screenshot({path:evidence('phase-10-checks-mobile.png')});
    expect(errors).toEqual([]);
    fs.writeFileSync(evidence('phase-10-in-room.json'),JSON.stringify({checked_at:new Date().toISOString(),encounter:'maria (fictional)',
      first_obstacle_ms_from_turn:firstObstacleMs,resolutions:['office_will_submit','review_coverage'],authorization:'approved by sandbox plan',interpreter:'fixture'},null,2)+'\n');
  }finally{await patient.close();await doctor.close();await family.close();}
});

test('in-room obstacle latency measured over twenty fixture turns',async({browser})=>{
  test.setTimeout(240000);
  const patient=await browser.newContext();await launch(patient);
  try{
    const samples:{turn_to_obstacle_ms:number,source_to_cue_ms:number}[]=[];
    for(let trial=0;trial<20;trial++){
      // Each new turn changes the step's sources, so the plan re-checks it and finds the rule again.
      const day=trial%2?'Thursday':'Wednesday';const before=new Set((await (await patient.request.get(checks)).json()).obstacles.map((o:{id:string})=>o.id));
      const sent=Date.now();
      await post(patient,'/understanding/fixture-turns',{command_id:crypto.randomUUID(),speaker:'clinician',text:`Actually, Maria will schedule the MRI at Lakeside Imaging on ${day} after the office sends the order.`});
      let found:{id:string}|undefined;
      await expect.poll(async()=>{found=(await (await patient.request.get(checks)).json()).obstacles.find((o:{id:string,kind:string,state:string})=>o.kind==='prior_authorization_required'&&o.state==='open'&&!before.has(o.id));return !!found;},{intervals:[50],timeout:15000}).toBe(true);
      const turnToObstacle=Date.now()-sent;
      const timing=await (await patient.request.get(base+'/feasibility/obstacles/'+found!.id+'/timings')).json();
      samples.push({turn_to_obstacle_ms:turnToObstacle,source_to_cue_ms:timing.source_to_cue_ms});
    }
    const report={checked_at:new Date().toISOString(),configuration:'fixture interpreter, local sandbox plan, Linux',trials:samples.length,samples,
      p95_turn_to_obstacle_ms:percentile(samples.map(s=>s.turn_to_obstacle_ms),95),p95_source_to_cue_ms:percentile(samples.map(s=>s.source_to_cue_ms),95),
      target_ms:3000,note:'Client-observed time includes understanding and API polling; source-to-cue is the server-side span from the finalized turn to the private cue.'};
    fs.writeFileSync(evidence('phase-10-latency.json'),JSON.stringify(report,null,2)+'\n');
    console.log('Phase 10 latency p95: turn→obstacle '+report.p95_turn_to_obstacle_ms+' ms, source→cue '+report.p95_source_to_cue_ms+' ms');
    expect(report.p95_source_to_cue_ms).toBeLessThan(3000);
  }finally{await patient.close();}
});
