import { test, expect } from '@playwright/test';
import { launch } from './helpers';
test.beforeEach(async ({ context }) => { await launch(context); });

test('selected question persists after refresh and is visible in the visit', async ({ page }) => {
  await page.goto('/prepare');
  const choice = page.getByRole('checkbox', { name: 'Mention my morning availability' });
  await expect(choice).toBeEnabled();
  const before = await choice.isChecked();
  await choice.setChecked(!before);
  await expect(choice).toBeEnabled();
  await expect(choice).toBeChecked({ checked: !before });
  await page.reload();
  await expect(page.getByRole('checkbox', { name: 'Mention my morning availability' })).toBeChecked({ checked: !before });
  await page.getByRole('link', { name: 'Review your visit' }).click();
  await expect(page.getByRole('heading', { name: 'What I wanted to discuss' })).toBeVisible();
  const selectedTitle = page.locator('.simple-list').getByText('Mention my morning availability');
  if (!before) await expect(selectedTitle).toBeVisible(); else await expect(selectedTitle).toHaveCount(0);
  await page.goto('/prepare');
  await page.getByRole('checkbox', { name: 'Mention my morning availability' }).setChecked(before);
  await expect(page.getByRole('checkbox', { name: 'Mention my morning availability' })).toBeEnabled();
});

test('source dialog has evidence and keyboard dismissal restores focus', async ({ page }) => {
  await page.goto('/prepare');
  const trigger = page.getByRole('button', { name: 'View source' }).first();
  await trigger.click();
  const dialog = page.getByRole('dialog');
  await expect(dialog.getByRole('heading', { name: 'Message from the referral office' })).toBeVisible();
  await expect(dialog.getByText('Office message · Oct 12, 2026')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
});

test('direct routes load and mobile layout stays within the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const [route, heading] of [
    ['/prepare', "Let's make room for what matters."],
    ['/visit', 'Keep the important things in view.'],
    ['/follow-up', 'A clear way forward.'],
  ]) {
    await page.goto(route);
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
    await expect(page.getByText('Follow-up with Dr. Chen', { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
});

test('connection failure shows retry and recovers without a fake visit', async ({ page }) => {
  await page.route('**/api/**', route => route.abort());
  await page.goto('/prepare');
  await expect(page.getByRole('alert', { name: 'Visit error' })).toBeVisible();
  await expect(page.getByText('Connection unavailable')).toBeVisible();
  await expect(page.getByRole('checkbox')).toHaveCount(0);
  await page.unroute('**/api/**');
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.locator('.priority-choice input')).toHaveCount(3);
  await expect(page.getByText('Visit saved', { exact: true })).toBeVisible();
});

test('second window updates live and a stale API edit cannot overwrite it', async ({ browser, baseURL }) => {
  const one = await browser.newContext();
  const two = await browser.newContext();
  try {
    await launch(one); await launch(two);
    const first = await one.newPage(); const second = await two.newPage();
    await first.goto(baseURL! + '/prepare'); await second.goto(baseURL! + '/prepare');
    const label = 'Mention my morning availability';
    await expect(first.getByRole('checkbox', { name: label })).toBeEnabled();
    await expect(second.getByRole('checkbox', { name: label })).toBeEnabled();
    const before = await first.getByRole('checkbox', { name: label }).isChecked();
    const previous = await (await two.request.get('/api/encounters/10000000-0000-4000-8000-000000000001')).json();
    const me = await (await two.request.get('/api/auth/me')).json();
    await first.getByRole('checkbox', { name: label }).setChecked(!before);
    await expect(first.getByRole('checkbox', { name: label })).toBeEnabled();
    const response = await two.request.post('/api/encounters/'+previous.id+'/commands', {headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data:{command_id:crypto.randomUUID(),expected_version:previous.version,command:{type:'priority.selection_changed',priority_id:previous.priorities[2].id,selected:before}}});
    expect(response.status()).toBe(409);
    await expect(second.getByRole('checkbox', { name: label })).toBeChecked({ checked: !before });
    await second.getByRole('checkbox', { name: label }).setChecked(before);
    await expect(second.getByRole('checkbox', { name: label })).toBeEnabled();
  } finally { await one.close(); await two.close(); }
});

