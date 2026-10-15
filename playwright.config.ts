import { defineConfig, devices } from '@playwright/test';
import fs from 'node:fs';
const runtime = fs.existsSync('.local/runtime.json') ? JSON.parse(fs.readFileSync('.local/runtime.json','utf8').replace(/^\uFEFF/,'')) : { web_port: 3000 };
export default defineConfig({
  testDir: './tests/e2e', fullyParallel: false, workers: 1,
  timeout: 60000,
  expect: { timeout: 10000 },
  reporter: [['list'], ['html', { open: 'never' }], ['json', {outputFile:'.local/browser-results.json'}]],
  use: { baseURL: process.env.BRING_VENE_BASE_URL ?? 'http://127.0.0.1:' + runtime.web_port, trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], channel: 'chromium' } }],
});

