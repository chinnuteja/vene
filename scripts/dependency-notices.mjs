import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
const root = process.cwd();
const node = [];
for (const [scope, file] of [['workspace','package.json'],['web','apps/web/package.json']]) {
  const project = JSON.parse(fs.readFileSync(file,'utf8'));
  for (const name of Object.keys({ ...project.dependencies, ...project.devDependencies })) {
    const base = scope === 'web' ? 'apps/web/node_modules' : 'node_modules';
    const metadata = JSON.parse(fs.readFileSync(path.join(base,name,'package.json'),'utf8'));
    node.push({ name, version: metadata.version, license: metadata.license ?? 'See package license', scope });
  }
}
const python = spawnSync(path.join(root,'.venv/Scripts/python.exe'),['-c','import importlib.metadata as m,json; print(json.dumps([{"name":d.metadata["Name"],"version":d.version,"license":d.metadata.get("License-Expression") or d.metadata.get("License") or "See distribution license files"} for d in m.distributions()]))'],{encoding:'utf8',windowsHide:true});
if (python.status !== 0) throw new Error('Python dependency inspection failed.');
fs.mkdirSync('docs/qa',{recursive:true});
fs.writeFileSync('docs/qa/dependency-licenses.json',JSON.stringify({ node, python: JSON.parse(python.stdout), native_postgres: JSON.parse(fs.readFileSync('infra/postgres-binary.json','utf8')) },null,2)+'\n');
console.log('Resolved dependency license metadata recorded.');

