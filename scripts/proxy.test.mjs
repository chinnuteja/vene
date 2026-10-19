import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {proxyRequest} from '../apps/web/src/lib/api/proxy.ts';

test('TLS-terminated origin and pane cookie routing preserve CSRF and session isolation',async()=>{
  const seen=[];
  const server=http.createServer((req,res)=>{seen.push(req.headers.cookie??'');res.setHeader('Set-Cookie','vene_session=new; HttpOnly; Path=/; SameSite=strict; Secure');res.setHeader('Content-Type','application/json');res.end('{}');});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const old={BACKEND_URL:process.env.BACKEND_URL,RENDER_EXTERNAL_URL:process.env.RENDER_EXTERNAL_URL};
  process.env.BACKEND_URL='http://127.0.0.1:'+server.address().port;process.env.RENDER_EXTERNAL_URL='https://concept.example';
  const jar={name:'vene_demo_patient',path:'/api/demo/run/patient'};
  const request=(origin,cookie)=>new Request('http://internal:10000/api/demo/run/patient/auth/redeem',{method:'POST',headers:{host:'concept.example',origin,cookie,'x-vene-intent':'mutation'}});
  try{
    const accepted=await proxyRequest(request('https://concept.example','vene_session=ordinary; vene_demo_clinician=doctor; vene_demo_patient=patient'),['auth','redeem'],jar);
    assert.equal(accepted.status,200);assert.equal(seen[0],'vene_session=patient');
    assert.match(accepted.headers.get('set-cookie'),/^vene_demo_patient=new;/);assert.match(accepted.headers.get('set-cookie'),/Path=\/api\/demo\/run\/patient;/);
    assert.equal((await proxyRequest(request('https://evil.example','vene_demo_patient=patient'),['auth','redeem'],jar)).status,403);
    assert.equal(seen.length,1);
    assert.equal((await proxyRequest(request('https://concept.example','vene_session=ordinary; vene_demo_clinician=doctor'),['auth','redeem'],jar)).status,200);
    assert.equal(seen[1],'');
  }finally{await new Promise(r=>server.close(r));for(const [key,value]of Object.entries(old)){if(value===undefined)delete process.env[key];else process.env[key]=value;}}
});
