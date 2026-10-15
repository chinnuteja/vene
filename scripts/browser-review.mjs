import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const runtime = JSON.parse(fs.readFileSync('.local/runtime.json', 'utf8').replace(/^\uFEFF/,''));
const url = 'http://127.0.0.1:' + runtime.web_port;
fs.mkdirSync('docs/qa', { recursive: true });
const browser = await chromium.launch({ channel: 'chromium' });
try {
const context = await browser.newContext({ viewport: { width: 1440, height: 1040 } });
const page = await context.newPage();
page.setDefaultNavigationTimeout(60000);
const errors = [];
const expectedFaults = [];
let injectingFailure = false;
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => {
  if (message.type() !== 'error') return;
  if (injectingFailure && message.text().includes('Failed to load resource: net::ERR_FAILED')) expectedFaults.push(message.text());
  else errors.push(message.text());
});
page.on('response', response => { if (response.status() >= 400) errors.push(response.status() + ' ' + response.url()); });
for (const route of ['prepare', 'visit', 'follow-up']) {
  await page.goto(url + '/' + route);
  await page.getByText('Follow-up with Dr. Chen', { exact: true }).waitFor();
  await page.screenshot({ path: 'docs/qa/phase-01-' + route + '-desktop.png', fullPage: true });
}
await page.goto(url + '/prepare');
await page.getByRole('button', { name: 'View source' }).first().click();
await page.getByRole('dialog').waitFor();
await page.screenshot({ path: 'docs/qa/phase-01-source.png' });
await page.keyboard.press('Escape');
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({ path: 'docs/qa/phase-01-prepare-mobile.png', fullPage: true });
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
injectingFailure = true;
await page.route('**/api/**', route => route.abort());
await page.reload();
await page.getByRole('alert', { name: 'Visit error' }).waitFor();
await page.screenshot({ path: 'docs/qa/phase-01-unavailable-mobile.png', fullPage: true });
await context.close();
fs.writeFileSync('docs/qa/phase-01-browser-review.json', JSON.stringify({ url, viewport: '1440x1040 and 390x844', routes: ['prepare','visit','follow-up'], normal_page_errors: errors, intentionally_aborted_requests: expectedFaults, mobile_overflow: overflow, source_dialog: 'captured', connection_failure: 'captured', synthetic: true }, null, 2) + '\n');
if (errors.length || overflow) throw new Error('Browser review found errors or horizontal overflow: ' + errors.join('; '));
console.log('Browser review captured; normal pages had no console/request errors.');
} finally { await browser.close(); }

