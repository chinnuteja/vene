# Derived lifecycle structure from livekit/agents multi-user-transcriber.py
# commit b58e83f5c77d5b4bd4c8586793885151a91c4c83 (Apache-2.0).
# Changed: per-track generations, consent gates, pending-task cancellation,
# bounded raw streams, no transcript broadcasting/logging, immediate close.
import asyncio
from livekit import rtc


class TrackSupervisor:
    """Register starts before awaiting them; cancellation owns every resource.

    A completed old startup can never replace a new track's task. close() is
    cancellation, not drain: paused audio is discarded rather than transcribed.
    """
    def __init__(self, consume):
        self.consume=consume
        self.tasks={}

    def start(self,key,track):
        if key in self.tasks:return
        task=asyncio.create_task(self.consume(key,track))
        self.tasks[key]=task
        def done(finished):
            if self.tasks.get(key) is finished:self.tasks.pop(key,None)
            if not finished.cancelled():finished.exception()
        task.add_done_callback(done)

    async def retain(self,keys):
        retired=[task for key,task in list(self.tasks.items()) if key not in keys]
        for task in retired:task.cancel()
        if retired:await asyncio.gather(*retired,return_exceptions=True)

    async def close(self):
        await self.retain(set())


class FixtureSink:
    """Transport fixture only. It never invents speech from a test waveform."""
    async def start(self):pass
    def push(self,frame):pass
    async def close(self):pass


class DeepgramSink:
    def __init__(self,settings,on_final,on_error,diarize=False):
        self.settings=settings;self.on_final=on_final;self.on_error=on_error
        self.stt=None;self.stream=None;self.reader=None
        self.http=None;self.diarize=diarize
        self.fragments=[];self.fragment_chars=0

    async def accept_event(self,event):
        from livekit.agents.stt import SpeechEventType
        if event.type==SpeechEventType.FINAL_TRANSCRIPT and event.alternatives:
            text=event.alternatives[0].text.strip()
            if text:
                size=len(text)+(1 if self.fragments else 0)
                if self.fragment_chars+size>12000:raise RuntimeError('utterance_too_long')
                speaker=event.alternatives[0].speaker_id if self.diarize else None
                self.fragments.append((speaker,text));self.fragment_chars+=size
        elif event.type==SpeechEventType.END_OF_SPEECH and self.fragments:
            fragments=self.fragments;self.fragments=[];self.fragment_chars=0
            if not self.diarize:
                await self.on_final(' '.join(text for _,text in fragments));return
            # One turn can hold several room speakers; finalize each consecutive speaker separately.
            groups=[]
            for speaker,text in fragments:
                if groups and groups[-1][0]==speaker:groups[-1][1].append(text)
                else:groups.append((speaker,[text]))
            for speaker,texts in groups:
                await self.on_final(' '.join(texts),speaker or 'S0')

    async def start(self):
        from livekit.plugins import deepgram
        from livekit.agents.stt import SpeechEventType
        from livekit.agents import APIConnectOptions
        import aiohttp
        self.http=aiohttp.ClientSession()
        self.stt=deepgram.STT(api_key=self.settings.deepgram_api_key,model=self.settings.deepgram_model,
                              sample_rate=16000,interim_results=False,endpointing_ms=300,mip_opt_out=True,http_session=self.http,
                              enable_diarization=self.diarize)
        self.stream=self.stt.stream(conn_options=APIConnectOptions(max_retry=0,timeout=8))
        async def read():
            try:
                async for event in self.stream:
                    await self.accept_event(event)
            except asyncio.CancelledError:raise
            except Exception:await self.on_error()
        self.reader=asyncio.create_task(read())

    def push(self,frame):
        self.stream.push_frame(frame)

    async def close(self):
        if self.reader:
            self.reader.cancel();await asyncio.gather(self.reader,return_exceptions=True)
        # Pause/revocation is cancellation, never a flush of pending text.
        self.fragments=[];self.fragment_chars=0
        if self.stream:await self.stream.aclose()
        if self.stt:await self.stt.aclose()
        if self.http:await self.http.close()


def audio_stream(track):
    # One current authorization transaction per 100 ms native frame, rather
    # than 50 database round trips/second. Keep at most 200 ms queued; pause
    # discards the owned stream. Activity is still measured in 20 ms windows.
    return rtc.AudioStream(track,sample_rate=16000,num_channels=1,capacity=2,frame_size_ms=100)
