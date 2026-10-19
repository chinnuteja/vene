import {evidence,venvPython} from './platform';
import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { base, command, launch } from './helpers';
const canary = 'PRIVATE_CANARY_MARIA_BLUE_ORCHID';
const privateId = '30000000-0000-4000-8000-000000000004';
const q1 = '20000000-0000-4000-8000-000000000001';
const q2 = '20000000-0000-4000-8000-000000000002';
const q3 = '20000000-0000-4000-8000-000000000003';
const sourceId = '30000000-0000-4000-8000-000000000001';
const familyId = '50000000-0000-4000-8000-000000000003';
test('patient, clinician and family remain isolated through approval and live revocation', async ({browser, baseURL}) => {
  const patient = await browser.newContext({baseURL}), doctor = await browser.newContext({baseURL}), family = await browser.newContext({baseURL});
  const payloads: string[] = [];
  try {
    const owner = await launch(patient); await launch(doctor,'clinician'); await launch(family,'family');
    const original = await (await patient.request.get(base)).json();
    const p = await patient.newPage(), d = await doctor.newPage(), f = await family.newPage();
    for (const page of [d,f]) {
      page.on('response', async r => { if (r.url().includes('/api/') && !(r.headers()['content-type']??'').includes('text/event-stream')) { try { payloads.push(await r.text()); } catch {} } });
    }
    // Capture actual EventSource messages in each isolated renderer.
    await Promise.all([d,f].map(page => page.addInitScript(() => {
      const Original = window.EventSource;
      (window as unknown as {sharedMessages:string[]}).sharedMessages=[];
      window.EventSource = class extends Original { constructor(url: string | URL, options?: EventSourceInit) { super(url,options); for (const name of ['snapshot','update','access_revoked']) this.addEventListener(name,(e) => (window as unknown as {sharedMessages:string[]}).sharedMessages.push((e as MessageEvent).data)); } };
    })));
    for(const id of [q1,q2]) { await command(patient,{type:'priority.selection_changed',priority_id:id,selected:true}); await command(patient,{type:'sharing.changed',item_id:id,audiences:['clinician']}); }
    await command(patient,{type:'priority.selection_changed',priority_id:q3,selected:false});
    await command(patient,{type:'sharing.changed',item_id:sourceId,audiences:[]});
    await command(patient,{type:'sharing.changed',item_id:privateId,audiences:[]});
    await command(patient,{type:'preparation.approved',approved:false});
    await Promise.all([p.goto('/prepare'),d.goto('/prepare'),f.goto('/prepare')]);
    await expect(d.getByText('No questions have been shared with you yet.')).toBeVisible();
    await p.getByRole('button',{name:'Approve my visit list'}).click();
    await expect(p.getByRole('button',{name:'Withdraw approval'})).toBeEnabled();
    await expect(d.getByRole('heading',{name:'What is holding up my referral?'})).toBeVisible();
    await expect(d.getByRole('heading',{name:'Where should I arrange my lab visit?'})).toBeVisible();
    await expect(f.getByText('No questions have been shared with you yet.')).toBeVisible();
    await p.getByText('What Vene can carry with you',{exact:true}).click(); // sources are collapsed by default
    const sourceGroup = p.getByRole('group',{name:'Share source: Message from the referral office with'});
    await sourceGroup.getByRole('checkbox',{name:'Dr. Chen'}).click();
    await expect(sourceGroup.getByRole('checkbox',{name:'Dr. Chen'})).toBeEnabled();
    await expect(sourceGroup.getByRole('checkbox',{name:'Dr. Chen'})).toBeChecked();
    await expect(d.getByRole('button',{name:/Message from the referral office/})).toBeVisible();
    await d.getByRole('button',{name:/Message from the referral office/}).click();
    await expect(d.getByRole('dialog')).toBeVisible();
    await sourceGroup.getByRole('checkbox',{name:'Dr. Chen'}).click();
    await expect(sourceGroup.getByRole('checkbox',{name:'Dr. Chen'})).toBeEnabled();
    await expect(sourceGroup.getByRole('checkbox',{name:'Dr. Chen'})).not.toBeChecked();
    await expect(d.getByRole('dialog')).not.toBeVisible();
    await expect(d.getByRole('button',{name:/Message from the referral office/})).toHaveCount(0);
    await f.getByLabel('Question',{exact:true}).fill('Could I help with transport?');
    await f.getByLabel('A little context',{exact:true}).fill('I could drive you on Tuesday morning.');
    await f.getByRole('button',{name:'Suggest to Maria'}).click();
    await expect(p.getByRole('heading',{name:'Could I help with transport?'}).last()).toBeVisible();
    await p.getByRole('button',{name:'Keep off my list'}).last().click();
    await expect(f.locator('.suggestion').last().getByText('Maria kept this off her list')).toBeVisible();
    expect((await doctor.request.get(base+'/evidence/'+privateId)).status()).toBe(404);
    expect((await family.request.get(base+'?role=patient')).status()).toBe(200);
    for(const page of [d,f]) {
      const events = await page.evaluate(() => (window as unknown as {sharedMessages:string[]}).sharedMessages);
      expect(events.length).toBeGreaterThan(1);
      payloads.push(...events);
    }
    expect(payloads.join('\n')).not.toContain(canary);
    expect(payloads.join('\n')).not.toContain(privateId);
    
    for(const page of [p,d,f]) await page.evaluate(()=>window.scrollTo(0,0));
    await p.screenshot({path:evidence('phase-02-patient-desktop.png'),fullPage:true});
    await d.screenshot({path:evidence('phase-02-clinician-desktop.png'),fullPage:true});
    await f.screenshot({path:evidence('phase-02-family-desktop.png'),fullPage:true});
    await p.setViewportSize({width:390,height:844});
    await p.evaluate(()=>window.scrollTo(0,0));
    expect(await p.evaluate(() => document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
    await p.screenshot({path:evidence('phase-02-patient-mobile.png'),fullPage:true});
    const familyRow = p.locator('.member-row').filter({hasText:'Elena Alvarez'});
    await familyRow.getByRole('button',{name:'Withdraw access',exact:true}).click();
    await familyRow.getByRole('button',{name:'Yes, withdraw access'}).click();
    await expect(f.getByRole('heading',{name:'This visit is no longer open.'})).toBeVisible();
    await expect(f.getByText('Could I help with transport?')).toHaveCount(0);
    expect((await family.request.get(base)).status()).toBe(401);
    await f.screenshot({path:evidence('phase-02-revoked.png'),fullPage:true});
    // Restore by issuing a new invitation; earlier sessions must remain invalid.
    expect((await patient.request.post(base+'/invitations',{headers:{'x-vene-intent':'mutation','x-vene-csrf':owner.csrf_token},data:{membership_id:familyId}})).status()).toBe(200);
    expect((await family.request.get(base)).status()).toBe(401);
    for(const id of [q1,q2,sourceId,privateId]) {
      const item=[...original.priorities,...original.evidence].find(x=>x.id===id);
      await command(patient,{type:'sharing.changed',item_id:id,audiences:item?.audiences??[]});
    }
    for(const item of original.priorities) await command(patient,{type:'priority.selection_changed',priority_id:item.id,selected:item.selected});
    await command(patient,{type:'preparation.approved',approved:original.preparation_approved});
    fs.writeFileSync(evidence('phase-02-network-review.json'),JSON.stringify({checked_at:new Date().toISOString(),synthetic_only:true,shared_payloads_checked:payloads.length,canary_leaks:0,scope_revocation:'open source dialog cleared',membership_revocation:'stream closed and REST denied',old_session_after_new_invitation:'denied'},null,2)+'\n');
  } finally { await Promise.all([patient.close(),doctor.close(),family.close()]); }
});

test('invitation opens once, hides its token from the URL and has an HttpOnly cookie',async({browser,baseURL})=>{
  const p=await browser.newContext({baseURL}),guest=await browser.newContext({baseURL});
  try{
    const me=await launch(p);
    const invitation=await (await p.request.post(base+'/invitations',{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data:{membership_id:familyId}})).json();
    const page=await guest.newPage();
    await page.goto('/join#invite='+invitation.token);
    await expect(page.getByText('Family view · Shared by Maria')).toBeVisible();
    expect(page.url()).not.toContain(invitation.token);
    const cookie=(await guest.cookies()).find(c=>c.name==='vene_session');
    expect(cookie?.httpOnly).toBe(true);expect(cookie?.sameSite).toBe('Strict');
    expect(await page.evaluate(()=>document.cookie)).not.toContain('vene_session');
    await page.goto('/join#invite='+invitation.token);
    await expect(page.getByRole('heading',{name:'A new invitation is needed.'})).toBeVisible();
  }finally{await p.close();await guest.close();}
});

test('unauthenticated routes show the invitation gate and spoofing has no effect',async({page,context})=>{
  await page.goto('/prepare?role=patient');
  await expect(page.getByRole('heading',{name:'Your visit, by invitation.'})).toBeVisible();
  expect((await context.request.get(base+'?role=patient')).status()).toBe(401);
  await page.goto('/join#invite=THIS_IS_NOT_A_VALID_INVITATION_TOKEN');
  await expect(page.getByRole('heading',{name:'A new invitation is needed.'})).toBeVisible();
});

test('an actually expired fixture invitation cannot open the visit',async({page})=>{
  const invite=JSON.parse(execFileSync(venvPython,[path.resolve('scripts/expired-fixture-invite.py')],{encoding:'utf8',windowsHide:true}));
  await page.goto('/join#invite='+invite.token);
  await expect(page.getByRole('heading',{name:'A new invitation is needed.'})).toBeVisible();
  expect(page.url()).not.toContain(invite.token);
});

test('leaving a session clears the cookie and denies further access',async({page,context})=>{
  await launch(context);
  await page.goto('/prepare');
  await page.getByRole('button',{name:'Leave this session'}).click();
  await expect(page.getByRole('heading',{name:'This visit is no longer open.'})).toBeVisible();
  expect((await context.cookies()).some(c=>c.name==='vene_session')).toBe(false);
  expect((await context.request.get(base)).status()).toBe(401);
});
