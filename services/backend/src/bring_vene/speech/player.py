"""SDK speech handles and a single authorized RTC audio output, no text publisher."""
import asyncio
import base64
import json
import subprocess
import sys
import time
from pathlib import Path
from livekit import rtc
from livekit.agents import Agent,AgentSession,APIConnectOptions
from livekit.agents.voice import io
from bring_vene.speech import service
from bring_vene.speech.fence import SpeechFence


class PlaybackClosed(Exception):pass


def offline_helper():
    # Same in-memory line protocol on every platform; Windows keeps its audited SAPI helper.
    scripts=Path(__file__).resolve().parents[5]/'scripts'
    if sys.platform=='win32':
        return (['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(scripts/'synthesize-fixture.ps1')],
            {'creationflags':subprocess.CREATE_NO_WINDOW})
    return [sys.executable,str(scripts/'synthesize-fixture.py')],{}


class SpeechSynthesizer:
    def __init__(self,settings):self.settings=settings;self.offline=None;self.http=None;self.tts=None

    async def warm(self):
        # Opens only an empty provider connection. No private or public text is sent here.
        if service.provider(self.settings)[0]=='cartesia' and self.tts is None:
            import aiohttp
            from livekit.plugins import cartesia
            self.http=aiohttp.ClientSession()
            self.tts=cartesia.TTS(api_key=self.settings.cartesia_api_key,model=self.settings.cartesia_model,
                voice=self.settings.cartesia_voice_id,sample_rate=24000,http_session=self.http)
            self.tts.prewarm()

    async def close(self):
        if self.tts:await self.tts.aclose();self.tts=None
        if self.http:await self.http.close();self.http=None
        process=self.offline;self.offline=None
        if process and process.returncode is None:
            process.kill();await process.wait()

    async def frames(self,text):
        name,_=service.provider(self.settings)
        if name=='fixture':
            if not self.offline or self.offline.returncode is not None:
                command,options=offline_helper()
                starting=asyncio.create_task(asyncio.create_subprocess_exec(*command,
                    stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
                    limit=8*1024*1024,**options))
                try:self.offline=await asyncio.shield(starting)
                except asyncio.CancelledError:
                    self.offline=await starting;await self.close();raise
            process=self.offline;received=False
            try:
                process.stdin.write(json.dumps({'text':text}).encode()+b'\n');await process.stdin.drain()
                stdout=await asyncio.wait_for(process.stdout.readline(),20)
                if not stdout:raise RuntimeError('offline_synthesis_failed')
                audio=json.loads(stdout.decode('utf-8-sig'));pcm=base64.b64decode(audio['pcm']);rate=audio['sample_rate']
                if rate!=24000 or not pcm:raise RuntimeError('offline_synthesis_empty')
                received=True
                size=rate//50*2
                for offset in range(0,len(pcm),size):
                    chunk=pcm[offset:offset+size]
                    if len(chunk)%2:chunk=chunk[:-1]
                    if chunk:yield rtc.AudioFrame(chunk,rate,1,len(chunk)//2)
            finally:
                # Reuse the idle in-memory engine after a completed response.
                # Cancelled/failed generation discards its owned helper process.
                if not received:await self.close()
        elif name=='cartesia':
            await self.warm()
            async with self.tts.stream(conn_options=APIConnectOptions(max_retry=0,timeout=8)) as stream:
                stream.push_text(text);stream.end_input()
                async for packet in stream:yield packet.frame
        else:raise RuntimeError('tts_unconfigured')


class AuthorizedAudioOutput(io.AudioOutput):
    """First-frame permission check, commit notifications and periodic rechecks.

    The 80 ms RTC queue is cleared on interruption. Playout position is measured at
    this publisher, not inferred as successful listening by every remote person.
    """
    def __init__(self,engine,visit_id,settings):
        super().__init__(label='VeneAuthorizedOutput',capabilities=io.AudioOutputCapabilities(pause=False),sample_rate=24000)
        self.engine=engine;self.visit_id=visit_id;self.settings=settings
        self.source=rtc.AudioSource(24000,1,queue_size_ms=80)
        self.delivery_id=None;self.duration=0.;self.played=0.;self.active=False;self.fence=None;self.first=False;self.flusher=None
        self.channel_alive=lambda:True

    def bind(self,delivery_id):
        self.delivery_id=delivery_id;self.duration=0.;self.played=0.;self.fence=None;self.first=False

    async def capture_frame(self,frame):
        if not self.channel_alive():self.fence='authorization_channel_lost'
        if not self.first:
            valid,reason=await asyncio.to_thread(service.permit_playback,self.engine,self.visit_id,self.delivery_id,self.settings)
            if not valid:self.fence=reason
        if self.fence:self.clear_buffer();raise PlaybackClosed(self.fence)
        # Native WebRTC consumes whole 10 ms blocks. A final partial PCM block
        # must be padded with silence so its capture callback can complete.
        block=frame.sample_rate//100
        samples=((frame.samples_per_channel+block-1)//block)*block
        if samples!=frame.samples_per_channel:
            frame=rtc.AudioFrame(bytes(frame.data)+bytes((samples-frame.samples_per_channel)*frame.num_channels*2),
                frame.sample_rate,frame.num_channels,samples)
        await super().capture_frame(frame)
        self.active=True
        await self.source.capture_frame(frame)
        self.duration+=frame.duration
        if not self.first:
            self.first=True;self.on_playback_started(created_at=time.time())
            await asyncio.to_thread(service.first_audio,self.engine,self.visit_id,self.delivery_id)

    def flush(self):
        super().flush()
        if not self.active:return
        async def finish():
            await self.source.wait_for_playout()
            if self.active:
                self.played=self.duration;self.active=False
                self.on_playback_finished(playback_position=self.played,interrupted=False)
        self.flusher=asyncio.create_task(finish())

    def clear_buffer(self):
        self.played=max(self.played,max(0,self.duration-self.source.queued_duration))
        self.source.clear_queue()
        if self.flusher and not self.flusher.done():self.flusher.cancel()
        if self.active:
            super().flush();self.active=False
            self.on_playback_finished(playback_position=self.played,interrupted=True)

    async def close(self):
        self.clear_buffer()
        if self.flusher:await asyncio.gather(self.flusher,return_exceptions=True)
        await self.source.aclose()


class PublicSpeaker:
    def __init__(self,room,engine,visit_id,settings,synthesizer=None):
        self.room=room;self.engine=engine;self.visit_id=visit_id;self.settings=settings
        self.output=None;self.session=None;self.handle=None;self.publication=None
        self.synthesizer=synthesizer or SpeechSynthesizer(settings)
        self.init_lock=asyncio.Lock()
        self.watcher=SpeechFence(engine,visit_id,self.invalidate)

    def invalidate(self,reason):
        if self.output and self.output.delivery_id:
            self.output.fence=reason;self.interrupt()

    async def initialize(self):
        async with self.init_lock:await self._initialize()

    async def _initialize(self):
        if self.session:return
        try:
            await self.watcher.start()
            self.output=AuthorizedAudioOutput(self.engine,self.visit_id,self.settings)
            self.output.channel_alive=lambda:self.watcher.healthy
            track=rtc.LocalAudioTrack.create_audio_track('Vene · authorized public speech',self.output.source)
            self.publication=await self.room.local_participant.publish_track(track,rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE))
            self.session=AgentSession()
            self.session.output.audio=self.output
            # No RoomIO input, transcript publication, remote session control, LLM,
            # automatic listening, recording or speech logging in this output session.
            await self.session.start(Agent(instructions='Speak only supplied authorized text.'),record=False,session_host=False)
        except BaseException:
            if self.session:await self.session.aclose()
            if self.publication:
                try:await self.room.local_participant.unpublish_track(self.publication.sid)
                except Exception:pass
            if self.output:await self.output.close()
            await self.watcher.close()
            self.session=None;self.output=None;self.publication=None
            self.watcher=SpeechFence(self.engine,self.visit_id,self.invalidate)
            raise

    async def play(self,delivery):
        await self.initialize()
        self.output.bind(delivery['id'])
        if not self.watcher.healthy:raise PlaybackClosed('authorization_channel_lost')
        # Initializing the output can take time. Reauthorize before sending any
        # text to TTS, in addition to the first-frame and ongoing speech fences.
        valid,reason=await asyncio.to_thread(service.permit_playback,self.engine,self.visit_id,delivery['id'],self.settings)
        if not valid or self.output.fence:raise PlaybackClosed(self.output.fence or reason)
        self.handle=self.session.say(delivery['text'],audio=self.synthesizer.frames(delivery['text']),
            allow_interruptions=True,add_to_chat_ctx=False)
        try:
            await self.handle.wait_for_playout()
            if self.output.fence:raise PlaybackClosed(self.output.fence)
            if self.handle.interrupted:raise PlaybackClosed('interrupted')
            if not self.output.first or self.output.played<=0:raise RuntimeError('empty_playback')
            return int(self.output.played*1000)
        finally:
            if self.handle and not self.handle.done():self.handle.interrupt(force=True)
            self.output.clear_buffer()

    def interrupt(self):
        if self.handle and not self.handle.done():self.handle.interrupt(force=True)
        if self.output:self.output.clear_buffer()

    @property
    def played_ms(self):return int(self.output.played*1000) if self.output else 0

    async def close(self):
        self.interrupt()
        await self.watcher.close()
        if self.session:await self.session.aclose()
        await self.synthesizer.close()
        if self.output:await self.output.close()


class SpeechController:
    def __init__(self,room,engine,visit_id,generation,settings,speaker=None):
        self.engine=engine;self.visit_id=visit_id;self.generation=generation;self.settings=settings
        self.speaker=speaker or PublicSpeaker(room,engine,visit_id,settings)
        self.task=None;self.delivery=None;self.reason=None

    def busy(self):return bool(self.task and not self.task.done())

    async def execute(self,delivery):
        state='completed';reason=None;played=0
        try:played=await self.speaker.play(delivery)
        except asyncio.CancelledError:
            state='interrupted';reason=self.reason or 'cancelled';played=self.speaker.played_ms
            raise
        except PlaybackClosed as error:
            state='interrupted';reason=str(error);played=self.speaker.played_ms
        except Exception as error:
            print('Speech output failure: '+type(error).__name__,flush=True)
            state='failed';reason='tts_unavailable';played=self.speaker.played_ms
        finally:
            self.speaker.interrupt()
            await asyncio.to_thread(service.finish,self.engine,self.visit_id,delivery['id'],state,played,reason)

    async def tick(self):
        if self.task:
            if self.task.done():
                if not self.task.cancelled():self.task.exception()
                self.task=None;self.delivery=None
            else:
                valid,reason=await asyncio.to_thread(service.permit_playback,self.engine,self.visit_id,self.delivery['id'],self.settings)
                if not valid:await self.stop(reason)
        if not self.task:
            delivery=await asyncio.to_thread(service.next_delivery,self.engine,self.visit_id,self.generation,self.settings)
            if delivery:
                self.delivery=delivery;self.reason=None
                self.task=asyncio.create_task(self.execute(delivery))

    async def stop(self,reason):
        self.reason=reason;self.speaker.interrupt()
        if self.task and not self.task.done():
            self.task.cancel();await asyncio.gather(self.task,return_exceptions=True)
        self.task=None;self.delivery=None

    async def close(self):
        await self.stop('worker_closed');await self.speaker.close()
