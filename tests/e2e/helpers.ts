import { expect, type BrowserContext } from '@playwright/test';
export const visitId = '10000000-0000-4000-8000-000000000001';
export const base = '/api/encounters/' + visitId;
export async function launch(context: BrowserContext, role: 'patient'|'clinician'|'family' = 'patient') {
  const origin=process.env.BRING_VENE_BASE_URL;
  if(context.browser()?.browserType().name()==='chromium'&&origin&&new URL(origin).hostname==='127.0.0.1'){
    await context.grantPermissions(['local-network-access'],{origin});
  }
  await context.addInitScript(()=>sessionStorage.setItem('vene-demo-tools','true'));
  const invite = await context.request.post('/api/dev/invitations', {headers:{'x-vene-intent':'mutation'}, data:{persona:role}});
  expect(invite.status()).toBe(200);
  const response = await context.request.post('/api/auth/redeem', {headers:{'x-vene-intent':'mutation'}, data:{token:(await invite.json()).token}});
  expect(response.status()).toBe(200);
  return response.json();
}
export async function command(context: BrowserContext, change: unknown) {
  const me = await (await context.request.get('/api/auth/me')).json();
  let view = await (await context.request.get(base)).json();
  const reviewed=JSON.stringify([view.priorities,view.evidence,view.plan,view.preparation_approved,view.suggestions]);
  const commandId=crypto.randomUUID();
  for(let attempt=0;attempt<4;attempt++){
    const response=await context.request.post(base+'/commands',{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data:{command_id:commandId,expected_version:view.version,command:change}});
    const body=await response.json();
    if(response.status()===409&&body.detail==='The visit changed. Refresh it before editing.'&&attempt<3){
      view=await (await context.request.get(base)).json();
      // Only pipeline/room metadata may change. A changed question/source/plan
      // requires a fresh review and must still fail this intended mutation.
      expect(JSON.stringify([view.priorities,view.evidence,view.plan,view.preparation_approved,view.suggestions])).toBe(reviewed);
      continue;
    }
    expect(response.status()).toBe(200);return body.encounter;
  }
  throw new Error('The reviewed synthetic visit did not settle.');
}

export async function endCall(context:BrowserContext){
  const me=await (await context.request.get('/api/auth/me')).json();
  const call=await (await context.request.get(base+'/call')).json();
  if(call.state==='ended'||!call.generation||!call.generation.replaceAll('0','').replaceAll('-',''))return;
  const result=await context.request.post(base+'/call/controls',{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data:{command_id:crypto.randomUUID(),type:'end',expected_revision:call.revision}});
  expect(result.status()).toBe(200);
}
