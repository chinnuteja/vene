import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {finished} from 'node:stream/promises';
import {pipeOwnedOutput} from './child-logs.mjs';

test('a restarted child drains large stdout through the same owned log', async()=>{
  fs.mkdirSync('.local/logs',{recursive:true});
  const file=path.resolve('.local/logs/child-log-regression.log');
  const sink=fs.createWriteStream(file);
  const children=[];
  try {
    for(let index=0;index<2;index++){
      assert.equal(sink.writableEnded,false);
      const child=spawn(process.execPath,['-e',"process.stdout.write('x'.repeat(1024*1024));process.stderr.write('stage\\n');"],{windowsHide:true,stdio:['ignore','pipe','pipe']});
      children.push(child);pipeOwnedOutput(child,sink);
      let timer;
      try {
        const [code]=await Promise.race([once(child,'close'),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Owned child output did not drain.')),15000);})]);
        assert.equal(code,0);
      }finally{clearTimeout(timer);}
    }
  }finally{
    for(const child of children)if(child.exitCode===null&&child.signalCode===null)child.kill();
    sink.end();await finished(sink);
  }
  const bytes=fs.readFileSync(file);
  assert.equal(bytes.length,2*(1024*1024+6));
  assert.equal(bytes.toString().split('stage\n').length-1,2);
});
