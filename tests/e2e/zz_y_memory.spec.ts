import {evidence} from './platform';
import {test,expect,type BrowserContext} from '@playwright/test';
import fs from 'node:fs';
import {base,launch} from './helpers';

// Phase 11: preparation drafted from open loops in earlier visits.
const memory=base+'/memory';
const BLOOD='Do I still need to keep my blood pressure log?';
const PHARMACY='Can we sort out the message from the pharmacy about my refill?';
const LAB='What should happen with the lab work from Jul 14?';
async function confirmedLabAfterJuly(context:BrowserContext){
  const actions=(await (await context.request.get(base+'/execution')).json()).actions;
  return actions.some((a:{kind:string,state:string})=>a.kind==='lab'&&a.state==='confirmed');
}

test('drafted preparation from open loops is approved in a few interactions and stays private until approval',async({browser})=>{
  test.setTimeout(180000);
  const patient=await browser.newContext(),doctor=await browser.newContext(),family=await browser.newContext();
  await launch(patient);await launch(doctor,'clinician');await launch(family,'family');
  const p=await patient.newPage(),d=await doctor.newPage();
  const errors:string[]=[];for(const page of [p,d])page.on('pageerror',e=>errors.push(e.name));
  try{
    let interactions=0;
    await p.goto('/prepare');interactions++;
    const card=p.getByRole('region',{name:'Drafted from your earlier visits',exact:true});
    await expect(card.getByRole('heading',{name:/Vene found \d+ things? worth bringing up\./})).toBeVisible();
    await expect(card.getByRole('checkbox',{name:'Keep: '+BLOOD,exact:true})).toBeChecked();
    await expect(card.getByRole('checkbox',{name:'Keep: '+PHARMACY,exact:true})).toBeChecked();
    // A lab confirmed after July closes July's unfinished lab; otherwise it is proposed.
    if(await confirmedLabAfterJuly(patient))await expect(card.getByText(LAB,{exact:true})).toHaveCount(0);
    else await expect(card.getByText(LAB,{exact:true})).toBeVisible();
    const bloodItem=card.getByRole('listitem').filter({hasText:BLOOD});
    await bloodItem.getByText('Why Vene suggested this').click();
    await expect(bloodItem.locator('blockquote')).toContainText('Your question for the July visit · Check-in with Dr. Chen · Jul 12');
    await card.screenshot({path:evidence('phase-11-drafted.png')});
    expect((await doctor.request.get(memory)).status()).toBe(403);

    // Close the pharmacy loop as already done; it should not come back.
    await card.getByRole('listitem').filter({hasText:PHARMACY}).getByRole('button',{name:'Already done',exact:true}).click();
    await expect(card.getByText(PHARMACY,{exact:true})).toHaveCount(0);

    const add=card.getByRole('button',{name:/^Add \d+ to my visit list$/});
    await add.click();interactions++;
    await expect(card.getByRole('status')).toContainText('Added to your list as private drafts.');
    const question=p.locator('.priority-card').filter({hasText:BLOOD});
    await expect(question).toBeVisible();
    await question.getByText('Sharing and wording',{exact:true}).click();
    await expect(question.getByRole('checkbox',{name:'Dr. Chen',exact:true})).toBeChecked();
    await expect(question.getByRole('checkbox',{name:'Family',exact:true})).not.toBeChecked();
    // Before approval the clinician and family receive nothing new.
    expect(await (await doctor.request.get(base)).text()).not.toContain(BLOOD);
    expect(await (await family.request.get(base)).text()).not.toContain(BLOOD);
    await p.getByRole('button',{name:'Approve my visit list',exact:true}).click();interactions++;
    await expect(p.getByRole('button',{name:'Withdraw approval',exact:true})).toBeEnabled();
    expect(interactions).toBeLessThanOrEqual(5);
    await d.goto('/prepare');await expect(d.getByRole('heading',{name:BLOOD,exact:true})).toBeVisible();
    expect(await (await family.request.get(base)).text()).not.toContain(BLOOD);
    // The question is shared; its private imported source is not.
    expect((await (await doctor.request.get(base)).json()).evidence.some((e:{title:string})=>e.title.startsWith('From '))).toBe(false);
    await p.screenshot({path:evidence('phase-11-prepared.png'),fullPage:true});

    // The next visit inherits memory: the closed loop stays closed, the carried question appears once.
    const me=await (await patient.request.get('/api/auth/me')).json();
    const next=await patient.request.post(base+'/continuity/next-visit',{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data:{plan_ids:[],visit_at:'2026-11-20T15:00:00Z'}});
    expect(next.status()).toBe(200);const created=await next.json();
    const later=await browser.newContext();
    try{
      const redeemed=await later.request.post('/api/auth/redeem',{headers:{'x-vene-intent':'mutation'},data:{token:created.invitation.token}});expect(redeemed.status()).toBe(200);
      const lp=await later.newPage();await lp.goto('/prepare');
      const nextCard=lp.getByRole('region',{name:'Drafted from your earlier visits',exact:true});
      await expect(nextCard.getByText(BLOOD,{exact:true})).toHaveCount(1);
      await expect(nextCard.getByText(PHARMACY,{exact:true})).toHaveCount(0);
      await lp.setViewportSize({width:390,height:844});await lp.evaluate(()=>window.scrollTo(0,0));
      expect(await lp.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
      await nextCard.screenshot({path:evidence('phase-11-next-visit-mobile.png')});
      // Keyboard: the first keep-checkbox is reachable and toggles with Space.
      const first=nextCard.getByRole('checkbox').first();await first.focus();await lp.keyboard.press('Space');
      await expect(first).not.toBeChecked();
    }finally{await later.close();}
    expect(errors).toEqual([]);
    fs.writeFileSync(evidence('phase-11-memory.json'),JSON.stringify({checked_at:new Date().toISOString(),encounter:'maria (fictional)',
      interactions_to_approved_list:interactions,closed_loop:'pharmacy message (Already done)',carried:'blood pressure question',
      next_visit:'closed loop absent; carried question once'},null,2)+'\n');
  }finally{await patient.close();await doctor.close();await family.close();}
});
