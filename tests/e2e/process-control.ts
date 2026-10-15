import {expect} from '@playwright/test';
export async function ownedProcess(operation:'stop'|'restart',service:'api'|'execution'|'voice'){
  if(process.env.BRING_VENE_BROWSER_TEST!=='true'||!process.env.BRING_VENE_TEST_CONTROL_URL||!process.env.BRING_VENE_TEST_CONTROL_TOKEN)throw new Error('Owned isolated test-process control is unavailable.');
  const response=await fetch(process.env.BRING_VENE_TEST_CONTROL_URL+'/'+operation+'/'+service,{method:'POST',headers:{'x-vene-test-control':process.env.BRING_VENE_TEST_CONTROL_TOKEN},signal:AbortSignal.timeout(45000)});
  expect(response.status).toBe(200);expect((await response.json()).owned_test_database).toBe(true);
}
