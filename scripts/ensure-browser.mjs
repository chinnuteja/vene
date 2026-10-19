import { chromium } from '@playwright/test';
import { spawnSync } from 'node:child_process';
import { existsSync, readdirSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import path from 'node:path';
// Records which Chromium the browser checks use. Default: Playwright's pinned revision.
// When that revision is not installed and cannot be downloaded, an existing Chromium
// from PLAYWRIGHT_BROWSERS_PATH is used and named in .local/chromium.json.
const record = path.join(process.cwd(), '.local/chromium.json');
async function verify(options) {
  let browser;
  try { browser = await chromium.launch(options); return true; }
  catch { return false; }
  finally { if (browser) await browser.close(); }
}
function candidates() {
  const found = [];
  if (process.env.BRING_VENE_CHROMIUM_PATH) found.push(process.env.BRING_VENE_CHROMIUM_PATH);
  const folder = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (folder && existsSync(folder)) {
    for (const name of readdirSync(folder).filter(n => /^chromium-\d+$/.test(n)).sort().reverse()) {
      for (const sub of ['chrome-linux64/chrome', 'chrome-linux/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium', 'chrome-win/chrome.exe', 'chrome-win64/chrome.exe']) {
        const file = path.join(folder, name, sub);
        if (existsSync(file)) found.push(file);
      }
    }
  }
  return found;
}
mkdirSync(path.dirname(record), { recursive: true });
async function settle() {
  if (await verify({ channel: 'chromium' })) { rmSync(record, { force: true }); return 'Playwright pinned Chromium'; }
  for (const file of candidates()) {
    if (await verify({ executablePath: file })) { writeFileSync(record, JSON.stringify({ executable: file }, null, 2) + '\n'); return file; }
  }
  if (process.env.PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD !== '1') {
    spawnSync(process.execPath, [path.join(process.cwd(), 'node_modules/@playwright/test/cli.js'), 'install', 'chromium', '--no-shell'], { stdio: 'inherit', windowsHide: true });
    if (await verify({ channel: 'chromium' })) { rmSync(record, { force: true }); return 'Playwright pinned Chromium'; }
  }
  throw new Error('Chromium could not be installed or launched. Browser checks remain unverified.');
}
console.log('Chromium test browser verified: ' + await settle());
