"""Bounded local native-transport diagnostic. No audio, transcripts, provider calls or patient DB."""
import asyncio,json,logging,os,secrets,socket,subprocess,sys,time
from pathlib import Path
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'.local'


def port():
    # Local LiveKit has TCP and UDP listeners. A TCP-only probe cannot establish UDP availability.
    for _ in range(100):
        with socket.socket() as tcp:
            tcp.bind(('127.0.0.1',0));candidate=tcp.getsockname()[1]
            with socket.socket(type=socket.SOCK_DGRAM) as udp:
                try:udp.bind(('127.0.0.1',candidate));return candidate
                except OSError:pass
    raise RuntimeError('No free local media port.')


async def child(variant):
    from livekit import api,rtc
    import yaml
    config=yaml.safe_load((LOCAL/'native-probe.yaml').read_text(encoding='utf-8'))
    key,secret=next(iter(config['keys'].items()))
    records=[]
    class Safe(logging.Handler):
        def emit(self,record):
            message=record.getMessage().lower()
            for category in ['wait_pc_connection','connection refused','ice connection state','signaling state',
                             'connected','timed out','connecting','failed to connect','turn','stun']:
                if category in message:records.append(category);break
    logger=logging.getLogger('livekit');logger.handlers=[Safe()];logger.propagate=False;logger.setLevel(logging.INFO)
    warm=rtc.AudioSource(24000,1,queue_size_ms=80) if variant=='warm' else None
    if warm:await asyncio.to_thread(time.sleep,.2)
    room=rtc.Room();started=time.monotonic()
    jwt=api.AccessToken(key,secret).with_identity('vene:probe:'+str(uuid4())).with_grants(api.VideoGrants(
        room_join=True,room='vene-00000000-0000-4000-8000-000000000001-00000000-0000-4000-8000-000000000002',can_publish=True,can_subscribe=True,can_publish_data=False,
        can_publish_sources=['microphone'],can_update_own_metadata=False)).to_jwt()
    options=rtc.RoomOptions(auto_subscribe=False,single_peer_connection=variant!='dual',connect_timeout=3)
    if variant=='relay':options.rtc_config=rtc.RtcConfiguration(ice_transport_type=rtc.IceTransportType.TRANSPORT_RELAY)
    try:
        await room.connect('ws://127.0.0.1:'+str(config['port']),jwt,options)
        if variant=='host':
            source=rtc.AudioSource(24000,1)
            await room.local_participant.publish_track(rtc.LocalAudioTrack.create_audio_track('Original silent probe',source),rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE))
            (LOCAL/'probe-host-ready').write_text('ready',encoding='utf-8')
            await asyncio.sleep(60)
            await source.aclose()
        print(json.dumps({'variant':variant,'connected':True,'ms':round((time.monotonic()-started)*1000),'events':records}),flush=True)
    except Exception as error:
        print(json.dumps({'variant':variant,'connected':False,'error':type(error).__name__,'events':records}),flush=True)
    finally:
        await room.disconnect()
        if warm:await warm.aclose()


def main():
    import urllib.request
    ports=[port() for _ in range(4)];assert len(set(ports))==4
    key='probe_'+secrets.token_hex(16);secret=secrets.token_hex(32)
    config=LOCAL/'native-probe.yaml'
    config.write_text(f'port: {ports[0]}\nbind_addresses: [127.0.0.1]\nrtc:\n  tcp_port: {ports[1]}\n  udp_port: {ports[2]}\n  use_external_ip: false\n  node_ip: 127.0.0.1\n  enable_loopback_candidate: true\n  use_mdns: false\nturn:\n  enabled: true\n  udp_port: {ports[3]}\n  bind_addresses: [127.0.0.1]\n  domain: 127.0.0.1\n  allow_restricted_peer_cidrs: [127.0.0.1/32]\nkeys:\n  {key}: {secret}\nlogging:\n  level: error\n',encoding='utf-8')
    if '--saved-config' in sys.argv:
        import yaml
        config.write_text((LOCAL/'browser-livekit.yaml').read_text(encoding='utf-8'),encoding='utf-8')
        ports[0]=yaml.safe_load(config.read_text(encoding='utf-8'))['port']
    binary=LOCAL/'tools/livekit'/('livekit-server.exe' if os.name=='nt' else 'livekit-server')
    options={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    server=subprocess.Popen([str(binary),'--config',str(config)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**options)
    report=[]
    host=None
    try:
        for _ in range(30):
            try:
                urllib.request.urlopen('http://127.0.0.1:'+str(ports[0]),timeout=.5).close();break
            except OSError:time.sleep(.2)
        if '--inhabited' in sys.argv:
            (LOCAL/'probe-host-ready').unlink(missing_ok=True)
            host=subprocess.Popen([sys.executable,__file__,'--child','host'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**options)
            for _ in range(100):
                if (LOCAL/'probe-host-ready').exists():break
                time.sleep(.1)
            else:raise RuntimeError('Probe publisher did not join.')
        for variant in ['single','warm','dual']:
            process=subprocess.Popen([sys.executable,__file__,'--child',variant],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,**options)
            try:
                stdout,_=process.communicate(timeout=12)
                rows=[json.loads(l) for l in stdout.decode('utf-8').splitlines() if l.startswith('{')]
                report.append(rows[-1] if rows else {'variant':variant,'connected':False,'error':'no_result'})
            except subprocess.TimeoutExpired:
                if os.name=='nt':subprocess.run(['taskkill.exe','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**options)
                else:process.kill()
                process.communicate(timeout=5);report.append({'variant':variant,'connected':False,'error':'native_join_timeout'})
        print(json.dumps(report,indent=2))
        (LOCAL/'evidence/native-probes.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    finally:
        if host:
            if os.name=='nt':subprocess.run(['taskkill.exe','/PID',str(host.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**options)
            else:host.kill()
            host.wait(timeout=5)
        server.terminate();server.wait(timeout=5)


if __name__=='__main__':
    if '--child' in sys.argv:asyncio.run(child(sys.argv[-1]))
    else:main()
