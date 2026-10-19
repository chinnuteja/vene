import {evidence,chromiumLaunch} from './platform';
import {test,expect,chromium,type BrowserContext} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import {base,launch,endCall} from './helpers';

// Phase 12: one phone on the table, and dial-in PINs.
const room=base+'/room';
async function post(context:BrowserContext,url:string,data?:unknown){
  const me=await (await context.request.get('/api/auth/me')).json();
  return context.request.post(url,{headers:{'x-vene-intent':'mutation','x-vene-csrf':me.csrf_token},...(data===undefined?{}:{data})});
}
async function call(context:BrowserContext){return (await context.request.get(base+'/call',{maxRetries:2})).json();}

test('in-room mode keeps Vene off until everyone agrees, attributes voices without authority, and pauses for a new arrival',async({baseURL})=>{
  test.setTimeout(240000);
  // The patient's phone, with a fake microphone, at phone size.
  const browser=await chromium.launch({...chromiumLaunch(),args:['--allow-loopback-in-peer-connection','--disable-features=WebRtcHideLocalIpsWithMdns',
    '--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+path.resolve('fixtures/audio/patient.wav')]});
  const patient=await browser.newContext({baseURL,permissions:['microphone'],viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  const doctor=await browser.newContext({baseURL});
  const errors:string[]=[];
  try{
    await launch(patient);await launch(doctor,'clinician');
    const p=await patient.newPage(),d=await doctor.newPage();for(const page of [p,d])page.on('pageerror',e=>errors.push(e.message));
    await p.goto('/visit');
    const card=p.getByRole('region',{name:'One phone in the room',exact:true});
    await card.getByRole('button',{name:'+ Dr. Chris Chen',exact:true}).click();
    await card.getByLabel('Name of someone present',{exact:true}).fill('A nurse');
    await card.getByLabel('Their role',{exact:true}).selectOption('other');
    await card.getByRole('button',{name:'Add',exact:true}).click();
    await card.getByRole('button',{name:'Start in-room mode',exact:true}).click();
    await expect(card.getByText('Setting up',{exact:true})).toBeVisible();
    await expect(card.locator('blockquote')).toContainText('No audio is recorded.');
    // Nothing is processed before the disclosure and everyone's agreement.
    expect((await post(patient,room+'/fixture-utterances',{label:'S0',text:'Something said too early.'})).status()).toBe(409);
    await expect(card.getByRole('listitem',{name:'Agreement: Dr. Chris Chen'}).getByRole('button',{name:'Agreed',exact:true})).toBeDisabled();
    await card.getByRole('button',{name:'I told everyone',exact:true}).click();
    await card.getByRole('listitem',{name:'Agreement: Dr. Chris Chen'}).getByRole('button',{name:'Agreed',exact:true}).click();
    await expect(card.getByText('Setting up',{exact:true})).toBeVisible();
    await card.getByRole('listitem',{name:'Agreement: A nurse'}).getByRole('button',{name:'Agreed',exact:true}).click();
    await expect(card.getByText('Listening with agreement',{exact:true})).toBeVisible();
    await card.screenshot({path:evidence('phase-12-room-agreed-mobile.png')});

    // A real WebRTC call from this phone: agree, resume, then a new arrival pauses processing.
    await p.getByRole('button',{name:'Join conversation',exact:true}).click();
    await p.getByRole('button',{name:'Agree to Vene processing',exact:true}).click();
    await expect(p.getByRole('button',{name:'Resume Vene processing',exact:true})).toBeEnabled({timeout:30000});
    await p.getByRole('button',{name:'Resume Vene processing',exact:true}).click();
    await expect.poll(async()=>(await call(patient)).state,{timeout:20000}).toBe('active');

    // Speech heard in the room (fixture words through the same room service), then attribution.
    await card.getByText('Development sandbox · speech heard in the room').click();
    await card.getByLabel('Fictional words heard',{exact:true}).fill('I confirm the lab order. Maria will arrange the lab visit at Riverside Lab on Tuesday.');
    await card.getByRole('button',{name:'Hear this',exact:true}).click();
    const voice=card.getByLabel('Speaker S0',{exact:true});
    await expect(voice).toContainText('Unattributed speaker 1');
    await voice.getByRole('button',{name:'That\'s Dr. Chris Chen',exact:true}).click();
    await expect(voice).toContainText('Dr. Chris Chen');
    const source=(await (await patient.request.get(base)).json()).evidence.find((e:{speaker_label:string|null})=>e.speaker_label==='S0');
    expect(source.speaker).toBe('Dr. Chris Chen');expect(source.attribution).toBe('patient_attested');expect(source.version).toBe(2);
    await card.screenshot({path:evidence('phase-12-speakers-mobile.png')});

    // The clinician's browser learns only that room mode is on.
    await d.goto('/visit');
    await expect(d.getByText('The patient is using one phone in the room.',{exact:false})).toBeVisible();
    const guest=await (await doctor.request.get(room)).json();
    expect(guest.people).toEqual([]);expect(guest.speakers).toEqual([]);

    // Someone arrives: the gate closes and the call pauses; resume is refused until they agree.
    await card.getByRole('button',{name:'Someone arrived',exact:true}).click();
    await card.getByLabel('Name of the new arrival',{exact:true}).fill('A student');
    await card.locator('.room-add').getByRole('button',{name:'Add',exact:true}).click();
    await expect(card.getByText('Setting up',{exact:true})).toBeVisible();
    await expect.poll(async()=>(await call(patient)).manual_pause,{timeout:10000}).toBe(true);
    const current=await call(patient);
    const resume=await post(patient,base+'/call/controls',{command_id:crypto.randomUUID(),expected_revision:current.revision,type:'resume'});
    expect(resume.status()).toBe(409);
    expect((await post(patient,room+'/fixture-utterances',{label:'S1',text:'Said while someone new had not agreed.'})).status()).toBe(409);
    expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await p.screenshot({path:evidence('phase-12-arrival-mobile.png'),fullPage:true});

    // Dial-in PINs are issued in preparation, one live PIN per person.
    await p.goto('/prepare');
    const dial=p.getByRole('region',{name:'Join by phone',exact:true});
    await dial.getByRole('listitem').filter({hasText:'Dr. Chris Chen'}).getByRole('button',{name:'Create PIN',exact:true}).click();
    const pin=dial.getByLabel('Dial-in PIN for Dr. Chris Chen',{exact:true});
    await expect(pin).toContainText(/\d{3} \d{3}/);
    await expect(pin).toContainText('Dial-in number not configured in this preview');
    await dial.screenshot({path:evidence('phase-12-dial-in-mobile.png')});
    expect(errors).toEqual([]);
    fs.writeFileSync(evidence('phase-12-room.json'),JSON.stringify({checked_at:new Date().toISOString(),encounter:'maria (fictional)',
      viewport:'390x844 mobile',real_webrtc_call:true,gate_before_agreement:'409',attribution:'patient_attested',
      new_arrival:'call paused; resume 409; room speech 409',guest_payload:'state only',dial_in_pin:'issued (telephony not exercised)'},null,2)+'\n');
    await post(patient,room+'/end');
    await endCall(patient);
  }finally{await patient.close();await doctor.close();await browser.close();}
});
