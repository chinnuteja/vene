import { spawnSync } from 'node:child_process';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import openapiTS, { astToString } from 'openapi-typescript';
import { venvPython } from './platform.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const check = process.argv.includes('--check');
const target = path.join(root, check ? '.local/contracts-check' : 'packages/contracts');
mkdirSync(target, { recursive: true });
const spec = path.join(target, 'openapi.json');
const python = venvPython(root);
const result = spawnSync(python, [path.join(root, 'scripts/export_contracts.py'), '--output', spec], { cwd: root, stdio: 'inherit', windowsHide: true });
if (result.status !== 0) throw new Error('Contract export failed.');
const generated = astToString(await openapiTS(pathToFileURL(spec)));
writeFileSync(path.join(target, 'schema.ts'), generated);
if (check) {
  for (const file of ['openapi.json', 'schema.ts']) {
    if (readFileSync(path.join(target, file), 'utf8') !== readFileSync(path.join(root, 'packages/contracts', file), 'utf8')) throw new Error('Contract drift: ' + file + '. Regenerate explicitly.');
  }
}
console.log(check ? 'API contract matches generated client.' : 'API contract and TypeScript types generated.');

