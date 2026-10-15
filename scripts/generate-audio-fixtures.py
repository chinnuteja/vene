"""Original tones for repeatable WebRTC transport checks; these are not speech."""
import math
import struct
import wave
from pathlib import Path

directory=Path(__file__).resolve().parent.parent/'fixtures/audio'
directory.mkdir(parents=True,exist_ok=True)
for name,frequency in [('patient',440),('clinician',660)]:
    samples=[]
    for index in range(48000*3):
        envelope=.5+.5*math.sin(2*math.pi*2*index/48000)
        samples.append(struct.pack('<h',int(7000*envelope*math.sin(2*math.pi*frequency*index/48000))))
    with wave.open(str(directory/f'{name}.wav'),'wb') as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(48000);output.writeframes(b''.join(samples))
print('Generated two original 3-second mono tone fixtures (no speech or patient recording).')
