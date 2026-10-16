"""Original test speech for Linux/macOS, same line protocol as synthesize-fixture.ps1.

Input text and PCM stay in memory on Linux (espeak-ng writes WAV to stdout). macOS
`say` can only write a file, so one private temporary file is removed immediately.
A missing engine reports an error; there is no silent or tone fallback.
"""
import base64
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

RATE = 24000


def wav_pcm(data):
    # Streamed WAV headers can carry placeholder sizes; read the format, then the data chunk to the end.
    if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        raise ValueError('not a WAV stream')
    offset, rate, channels, bits = 12, None, None, None
    while offset + 8 <= len(data):
        chunk, size = data[offset:offset + 4], struct.unpack('<I', data[offset + 4:offset + 8])[0]
        body = offset + 8
        if chunk == b'fmt ':
            _, channels, rate, _, _, bits = struct.unpack('<HHIIHH', data[body:body + 16])
        elif chunk == b'data':
            pcm = data[body:body + size] if body + size <= len(data) else data[body:]
            if bits != 16 or channels != 1:
                raise ValueError('unsupported WAV format')
            return rate, pcm[:len(pcm) - len(pcm) % 2]
        offset = body + size + (size % 2)
    raise ValueError('WAV data missing')


def resample(pcm, source):
    if source == RATE:
        return pcm
    samples = struct.unpack('<%dh' % (len(pcm) // 2), pcm)
    count = int(len(samples) * RATE / source)
    out = []
    for index in range(count):
        position = index * source / RATE
        left = int(position)
        right = min(left + 1, len(samples) - 1)
        fraction = position - left
        out.append(int(samples[left] * (1 - fraction) + samples[right] * fraction))
    return struct.pack('<%dh' % len(out), *out)


def synthesize(text):
    if shutil.which('espeak-ng'):
        result = subprocess.run(['espeak-ng', '--stdout', '-v', 'en-us', '-s', '165', text],
                                capture_output=True, timeout=20, check=True)
        return 'espeak-ng en-us', *wav_pcm(result.stdout)
    if sys.platform == 'darwin' and shutil.which('say'):
        handle, path = tempfile.mkstemp(suffix='.wav')
        os.close(handle)
        try:
            subprocess.run(['say', '-o', path, '--data-format=LEI16@24000', text], capture_output=True, timeout=20, check=True)
            with open(path, 'rb') as file:
                return 'macOS say', *wav_pcm(file.read())
        finally:
            os.remove(path)
    raise RuntimeError('No offline speech engine. Install espeak-ng (Linux) or use macOS say.')


def main():
    for line in sys.stdin:
        try:
            text = json.loads(line)['text']
            if not isinstance(text, str) or not text or len(text) > 600:
                raise ValueError('Invalid speech input.')
            voice, rate, pcm = synthesize(text)
            pcm = resample(pcm, rate)
            if not pcm:
                raise ValueError('empty speech')
            reply = {'sample_rate': RATE, 'voice': voice, 'pcm': base64.b64encode(pcm).decode()}
        except Exception:
            reply = {'error': 'offline_synthesis_failed'}
        sys.stdout.write(json.dumps(reply) + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
