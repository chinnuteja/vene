import {test,expect} from '@playwright/test';
import {evidence} from './platform';

test('chapter three explains sample speech and recovers from paused private checks',async({page})=>{
  test.setTimeout(120000);
  await page.goto('/demo');
  await page.getByRole('button',{name:'Start demo',exact:true}).click();
  const p=page.frameLocator('iframe[title="Maria’s private phone"]');
  const d=page.frameLocator('iframe[title="Dr. Chen’s clinician view"]');
  await expect(p.getByText(/Vene found \d things worth bringing up/)).toBeVisible();
  await page.getByRole('button',{name:'Next: During'}).click();
  await p.getByRole('button',{name:'Allow private checks',exact:true}).click();
  await p.getByRole('button',{name:'Pause understanding',exact:true}).click();
  await expect(d.getByRole('button',{name:'Waiting for Maria’s permission',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Next: Before you leave'}).click();
  await expect(d.getByRole('button',{name:'Waiting for Maria’s permission',exact:true})).toBeDisabled();
  await expect(d.getByText('These are new example words from Dr. Chen, later in the same visit. They are not Vene’s recommendations or completed orders.',{exact:true})).toBeVisible();
  await expect(p.getByRole('list',{name:'Before you leave checklist'})).toHaveCount(0);
  // Chapter 3 supplies its own patient control; no navigation to a hidden chapter or automatic consent.
  await p.getByRole('button',{name:'Allow private checks',exact:true}).click();
  await expect(d.getByRole('button',{name:'Say this',exact:true})).toBeEnabled();
  // The actual server refuses a paused turn (covered by test_demo.py). Its safe reason must
  // survive the client boundary instead of being relabelled as a version conflict.
  await page.route('**/demo/turn',route=>route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({detail:'Maria must first allow private understanding.'})}));
  await d.getByRole('button',{name:'Say this',exact:true}).click();
  await expect(d.getByRole('alert').filter({hasText:'Ask Maria to allow private checks'})).toHaveText('Ask Maria to allow private checks before adding sample words.');
  await expect(d.getByText('Your visit changed in another window. Refresh and try again.')).toHaveCount(0);
  await page.unroute('**/demo/turn');
  await d.getByRole('button',{name:'Say this',exact:true}).click();
  await expect(d.getByRole('button',{name:'Sample words added',exact:true})).toBeDisabled();
  await expect(p.getByLabel('Private coverage cue')).toContainText('requires prior authorization',{timeout:30000});
  await expect(p.getByRole('list',{name:'Before you leave checklist'}).getByRole('listitem')).toHaveCount(2);
  await expect(d.getByRole('list',{name:'Before you leave checklist'})).toHaveCount(0);
  await page.screenshot({path:evidence('chapter-three-permission-recovered.png'),fullPage:true});
});
