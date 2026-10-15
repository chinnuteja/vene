import { chromium } from '@playwright/test';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
async function verify() {
  let browser;
  try { browser = await chromium.launch({ channel: 'chromium' }); return true; }
  catch { return false; }
  finally { if (browser) await browser.close(); }
}
if (!await verify()) {
  const result = spawnSync(process.execPath, [path.join(process.cwd(), 'node_modules/@playwright/test/cli.js'), 'install', 'chromium', '--no-shell'], { stdio: 'inherit', windowsHide: true });
  if (!await verify()) throw new Error('Chromium could not be installed or launched. Browser checks remain unverified.');
  if (result.status !== 0) console.log('Chromium launches successfully; an optional browser asset download failed. Video recording is not used.');
}
console.log('Chromium test browser verified.');
