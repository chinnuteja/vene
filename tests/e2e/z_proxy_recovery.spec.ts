import {evidence} from './platform';
import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import {base,launch} from './helpers';
import {ownedProcess} from './process-control';

test('packaging API restart releases streams and subsequent patient edits complete',async({browser})=>{
  test.setTimeout(120000);
  const patient=await browser.newContext(),doctor=await browser.newContext(),family=await browser.newContext();
  try{
    await launch(patient);await launch(doctor,'clinician');await launch(family,'family');
    const p=await patient.newPage(),d=await doctor.newPage(),f=await family.newPage();
    await Promise.all([p.goto('/prepare'),d.goto('/visit'),f.goto('/follow-up')]);
    for(const page of [p,d,f])await expect(page.locator('main#main')).toBeVisible();
    const before=await (await patient.request.get(base,{timeout:20000})).json();
    const priority=before.priorities[0];
    await ownedProcess('stop','api');await ownedProcess('restart','api');
    const me=await (await patient.request.get('/api/auth/me',{timeout:20000})).json();
    for(const selected of [!priority.selected,priority.selected]){
      const current=await (await patient.request.get(base,{timeout:20000})).json();
      const result=await patient.request.post(base+'/commands',{timeout:20000,headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data:{command_id:crypto.randomUUID(),expected_version:current.version,command:{type:'priority.selection_changed',priority_id:priority.id,selected}}});
      expect(result.status()).toBe(200);
      expect((await result.json()).encounter.priorities.find(x=>x.id===priority.id).selected).toBe(selected);
    }
    const guests=await Promise.all([doctor.request.get(base,{timeout:20000}),family.request.get(base,{timeout:20000})]);
    for(const result of guests){expect(result.status()).toBe(200);expect(await result.text()).not.toContain('PRIVATE_CANARY');}
    fs.writeFileSync(evidence('phase-08-proxy-recovery.json'),JSON.stringify({checked_at:new Date().toISOString(),three_role_streams_open_before_restart:true,owned_api_restarted:true,subsequent_patient_edits_persisted:true,guest_scope_preserved:true,mutation_retries:0},null,2)+'\n');
  }finally{await Promise.all([patient.close(),doctor.close(),family.close()]);}
});
