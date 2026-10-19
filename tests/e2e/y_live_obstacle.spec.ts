import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import {evidence} from './platform';
import {base} from './helpers';
import {setup,finish,speech} from './speech-helpers';

test('live obstacle latency follows real STT model and institution response',async({baseURL})=>{
  test.skip(process.env.BRING_VENE_LIVE_PROVIDER_GATE!=='true','Explicit live provider gate only.');
  test.setTimeout(240000);
  const env=await setup(baseURL),{patient,doctor,p,d}=env;
  const observations:Record<string,unknown>={synthetic:true,stt:'deepgram',tts:'cartesia',fixture_fallback:false};
  try{
    const me=await (await patient.request.get('/api/auth/me')).json();
    const post=async(path:string,data:unknown)=>{const r=await patient.request.post(base+path,{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},data});expect(r.status()).toBe(200);return r.json();};
    await post('/understanding/processing',{command_id:crypto.randomUUID(),enabled:true});
    await post('/feasibility/standing',{kinds:['scheduling']});
    await post('/execution/scenario',{mode:'no_slot',kind:'lab'});
    const started=Date.now();
    await d.getByRole('button',{name:'Unmute my microphone',exact:true}).click();
    await expect.poll(async()=>{const v=await (await patient.request.get(base+'/call/utterances')).json();return v.some(x=>x.provider==='deepgram'&&/Maria will arrange.*Riverside Lab.*Tuesday.*order/i.test(x.text));},{timeout:60000}).toBe(true);
    await d.getByRole('button',{name:'Mute my microphone',exact:true}).click();
    let obstacle;
    await expect.poll(async()=>{const v=await (await patient.request.get(base+'/feasibility')).json();obstacle=v.obstacles.find(x=>x.kind==='no_slot_in_window');return !!obstacle;},{timeout:45000}).toBe(true);
    const observedMs=Date.now()-started;
    await expect.poll(async()=>{const u=await (await patient.request.get(base+'/understanding')).json();return u.state==='ready'&&u.processed_revision===u.revision;},{timeout:30000}).toBe(true);
    await expect.poll(async()=>(await speech(patient)).cues.some(x=>x.title.includes('Practical check')),{timeout:15000}).toBe(true);
    obstacle=(await (await patient.request.get(base+'/feasibility')).json()).obstacles.find(x=>x.kind==='no_slot_in_window'&&x.state==='open');
    expect(obstacle).toBeTruthy();
    const timing=await (await patient.request.get(base+'/feasibility/obstacles/'+obstacle.id+'/timings')).json();
    const model=await (await patient.request.get(base+'/understanding')).json();
    expect(['deepseek','openai']).toContain(model.provider);
    const turn=(await (await patient.request.get(base)).json()).evidence.filter(x=>x.origin==='deepgram');
    expect(turn.length).toBeGreaterThan(0);
    Object.assign(observations,{model:model.provider,microphone_unmute_to_first_obstacle_ms:observedMs,
      microphone_unmute_to_current_cue_ms:Date.now()-started,finalized_source_to_cue_ms:timing.source_to_cue_ms,timing,obstacle,turns:turn});
    expect((await speech(doctor)).cues).toEqual([]);
    await expect(p.locator('.private-cue').filter({hasText:'Practical check'}).first()).toBeVisible();
    Object.assign(observations,{passed:true,model:model.provider,microphone_unmute_to_obstacle_ms:observedMs,
      finalized_source_to_cue_ms:timing.source_to_cue_ms,timing,obstacle,turns:turn,
      sample_count:1,p95:null,physical_acoustics:false});
    await p.screenshot({path:evidence('live-obstacle.png'),fullPage:true});
  }catch(error){Object.assign(observations,{passed:false,error_type:(error as Error).name,
    speech:await speech(patient),understanding:await (await patient.request.get(base+'/understanding')).json()});throw error;}
  finally{const text=JSON.stringify(observations,null,2)+'\n';fs.writeFileSync(evidence('live-obstacle.json'),text);
    fs.writeFileSync(evidence('live-obstacle-'+Date.now()+'.json'),text);await finish(env);}
});
