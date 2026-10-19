"""Explicit live Deepgram check with original, two-voice synthetic audio only. No database writes."""
import asyncio
import json
import logging
import struct
import subprocess
import sys
import time
import wave
from pathlib import Path
from livekit import rtc
from bring_vene.config import Settings
from bring_vene.voice.supervisor import DeepgramSink

logging.basicConfig(level=logging.CRITICAL)
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / '.local/evidence'
TURNS = [
    ('Microsoft David Desktop', 'Maria, please get the lab work done within three days. We can send the order today.'),
    ('Microsoft Zira Desktop', 'I usually go to Riverside Lab. I need an appointment that my daughter can drive me to.'),
    ('Microsoft David Desktop', 'We should check another lab if Riverside has no appointment before Friday. Thursday morning is within that window.'),
    ('Microsoft Zira Desktop', 'Thursday at nine works for me. Please ask me before booking anything. Thank you for helping me keep track.'),
]


def original_audio():
    if sys.platform != 'win32':
        raise RuntimeError('This original two-voice gate currently needs the Windows David and Zira voices.')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
        str(ROOT/'scripts/synthesize-fixture.ps1')], input=''.join(json.dumps({'voice':v,'text':t})+'\n' for v,t in TURNS),
        capture_output=True, text=True, encoding='utf-8', timeout=45, creationflags=subprocess.CREATE_NO_WINDOW, check=True)
    import base64
    clips = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert len(clips) == len(TURNS) and all(c.get('pcm') and c['sample_rate']==24000 for c in clips)
    pcm = bytes(24000*2) + bytes(24000*2//2).join(base64.b64decode(c['pcm']) for c in clips) + bytes(24000*2)
    EVIDENCE.mkdir(exist_ok=True, parents=True)
    with wave.open(str(EVIDENCE/'original-two-voices.wav'),'wb') as out:
        out.setparams((1,2,24000,0,'NONE','not compressed')); out.writeframes(pcm)
    samples=struct.unpack('<%dh'%(len(pcm)//2),pcm)
    # Exact rational 24 kHz -> 16 kHz linear interpolation for generated fixtures.
    output=[samples[3*i//2] if i%2==0 else (samples[3*i//2]+samples[min(3*i//2+1,len(samples)-1)])//2
            for i in range(len(samples)*2//3)]
    return struct.pack('<%dh'%len(output),*output)


async def main():
    settings=Settings()
    if not settings.deepgram_api_key:
        print('UNVERIFIED: Deepgram key is absent. No fixture substitution.'); return 2
    report={'provider':'deepgram','model':settings.deepgram_model,'original_synthetic_audio':True,'fixture_fallback':False,
            'expected':[{'voice':v,'text':t} for v,t in TURNS]}
    sink=None
    try:
        pcm=original_audio(); finals=[]; errors=[]
        async def final(text,label=None): finals.append({'label':label,'text':text,'elapsed_ms':round((time.monotonic()-started)*1000)})
        async def failed(): errors.append('stt_unavailable')
        sink=DeepgramSink(settings,final,failed,diarize=True); await sink.start()
        started=time.monotonic()
        for offset in range(0,len(pcm),3200):
            chunk=pcm[offset:offset+3200]
            sink.push(rtc.AudioFrame(chunk,16000,1,len(chunk)//2))
            await asyncio.sleep(max(0,(offset+len(chunk))/32000-(time.monotonic()-started)))
        await asyncio.sleep(2)
        report.update(finals=finals,audio_seconds=len(pcm)/32000,errors=errors)
        labels={f['label'] for f in finals}
        doctors=[f['label'] for f in finals if 'order today' in f['text'].lower() or 'before friday' in f['text'].lower()]
        patients=[f['label'] for f in finals if 'daughter' in f['text'].lower() or 'before booking' in f['text'].lower()]
        assert not errors and len(labels)>=2 and doctors and patients
        assert set(doctors).isdisjoint(patients),'Different generated voices collapsed into the same speaker label.'
        report['passed']=True
        print('Actual Deepgram two-voice diarization passed; original synthetic audio and labelled turns saved locally.')
        return 0
    except Exception as error:
        report.update(passed=False,error_type=type(error).__name__)
        print('Live diarization FAILED ('+type(error).__name__+'); no fixture fallback.')
        return 1
    finally:
        if sink: await sink.close()
        EVIDENCE.mkdir(exist_ok=True,parents=True)
        (EVIDENCE/'live-diarization.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':raise SystemExit(asyncio.run(main()))
