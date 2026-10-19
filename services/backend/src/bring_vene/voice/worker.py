import asyncio
import logging
from datetime import timedelta,datetime,timezone
from uuid import UUID,uuid4
from livekit import api,rtc
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.config import Settings
from bring_vene.persistence.database import make_engine
from bring_vene.persistence.models import CallRecord
from bring_vene.voice import service
from bring_vene.voice.supervisor import TrackSupervisor,FixtureSink,DeepgramSink,audio_stream
from bring_vene.speech.player import SpeechController,SpeechSynthesizer,PublicSpeaker

# SDK/provider errors are translated into safe status codes; no transcript exception logs.
logging.basicConfig(level=logging.CRITICAL)
for namespace in ['livekit','livekit.agents','livekit.plugins','aiohttp']:
    logging.getLogger(namespace).setLevel(logging.CRITICAL)
from bring_vene.voice.diagnostics import install
install()


async def finish_connect_before_cancellation(room,url,token,options):
    # The SDK cannot safely abandon its native ready-event handshake. Keep the
    # join alive through cancellation, then let RoomWorker's finally disconnect.
    # auto_subscribe=False means an unfinished/revoked join processes no audio.
    joining=asyncio.create_task(room.connect(url,token,options))
    try:await asyncio.shield(joining)
    except asyncio.CancelledError:
        try:await asyncio.shield(joining)
        except Exception:pass
        raise


class RoomWorker:
    def __init__(self,engine,settings,visit_id,generation,instance=None,synthesizer=None):
        self.engine=engine;self.settings=settings;self.visit_id=visit_id;self.generation=generation
        self.room=rtc.Room();self.supervisor=TrackSupervisor(self.consume);self.epoch=None
        self.running=True
        self.instance=instance or uuid4()
        self.transport_lost=False
        self.speech=SpeechController(self.room,engine,visit_id,generation,settings,
            PublicSpeaker(self.room,engine,visit_id,settings,synthesizer))
        self.room.on('sip_dtmf_received',self.keypad)
        self.room.on('reconnecting',lambda:setattr(self,'transport_lost',True))
        self.room.on('disconnected',lambda _reason:setattr(self,'transport_lost',True))

    def keypad(self,dtmf):
        # Phone participants use the keypad for consent, pause and resume. The digit is checked
        # against the visit's current phone connections; nothing else about the caller is trusted.
        participant=getattr(dtmf,'participant',None);digit=str(getattr(dtmf,'digit','') or '')
        if not participant or not digit:return
        async def handle():
            from bring_vene.dial.service import keypad
            result=await asyncio.to_thread(keypad,self.engine,self.visit_id,self.generation,participant.identity,digit,self.settings)
            print('Phone keypad '+('accepted' if result.accepted else 'refused')+'.',flush=True)
        asyncio.ensure_future(handle())

    async def fail(self,code='stt_unavailable'):
        await asyncio.to_thread(service.worker_failed,self.engine,self.visit_id,self.generation,code,self.instance)

    async def consume(self,key,track):
        connection_id,sid,track_epoch,consent_epoch=key
        stream=None;sink=None
        async def final(text,label=None):
            await asyncio.to_thread(service.finalize,self.engine,self.visit_id,self.generation,
                connection_id,sid,track_epoch,consent_epoch,text,self.settings,label,self.instance)
        try:
            mode=service.provider(self.settings)
            if mode=='fixture':sink=FixtureSink()
            elif mode=='deepgram':
                from bring_vene.room.service import room_track
                diarize=await asyncio.to_thread(room_track,self.engine,self.visit_id,connection_id)
                sink=DeepgramSink(self.settings,final,self.fail,diarize)
            else:await self.fail();return
            await sink.start()
            stream=audio_stream(track)
            async for event in stream:
                frame=event.frame
                window=frame.sample_rate//50
                activity=[any(abs(sample)>300 for sample in frame.data[offset:offset+window])
                    for offset in range(0,frame.samples_per_channel,window)]
                non_silent=any(activity)
                accepted=await asyncio.to_thread(service.accept_frame,self.engine,self.visit_id,self.generation,
                    connection_id,sid,track_epoch,consent_epoch,frame.samples_per_channel,non_silent,activity,self.instance)
                if not accepted:break
                # Cancellation and epoch checks precede each provider delivery. No pre-roll replay.
                sink.push(frame)
        except asyncio.CancelledError:raise
        except Exception:await self.fail()
        finally:
            if stream:await stream.aclose()
            if sink:await sink.close()

    async def run(self):
        room=type('RoomIdentity',(),{'encounter_id':self.visit_id,'generation':self.generation})()
        name=service.room_name(room)
        token=api.AccessToken(self.settings.livekit_api_key,self.settings.livekit_api_secret)\
            .with_identity('vene:'+str(self.generation)+':'+str(self.instance)).with_name('Vene · disclosed assistant')\
            .with_ttl(timedelta(hours=8)).with_grants(api.VideoGrants(room_join=True,room=name,
                can_publish=True,can_publish_sources=['microphone'],can_subscribe=True,can_publish_data=False,hidden=False,
                can_update_own_metadata=False)).to_jwt()
        try:
            print('Owned runtime connecting.',flush=True)
            # The native single-PC handshake stalled at wait_pc_connection in actual
            # occupied Windows rooms. Use the SDK default two-PC transport; explicit
            # subscription and consent fences remain identical. Browser clients keep
            # their separate single-PC admission flow.
            await finish_connect_before_cancellation(self.room,self.settings.livekit_url,token,rtc.RoomOptions(auto_subscribe=False,single_peer_connection=False))
            print('Owned runtime connected.',flush=True)
            if not await asyncio.to_thread(service.worker_started,self.engine,self.visit_id,self.generation,self.instance):return
            # Publish an empty authorized output before the first contribution; never synthesize text here.
            await self.speech.speaker.initialize()
            from bring_vene.speech.service import recover
            await asyncio.to_thread(recover,self.engine,self.visit_id,self.generation)
            await asyncio.to_thread(service.worker_recovered,self.engine,self.visit_id,self.generation,self.instance)
            async with api.LiveKitAPI(self.settings.livekit_url,self.settings.livekit_api_key,self.settings.livekit_api_secret) as control:
                while self.running and not self.transport_lost and self.room.connection_state==rtc.ConnectionState.CONN_CONNECTED:
                    participants=list(self.room.remote_participants.values())
                    identities={p.identity for p in participants}
                    tracks={p.identity:publication.sid for p in participants for publication in p.track_publications.values()
                            if publication.source==rtc.TrackSource.SOURCE_MICROPHONE}
                    state=await asyncio.to_thread(service.sync_room,self.engine,self.visit_id,self.generation,
                        identities,tracks,len(self.supervisor.tasks)+int(self.speech.busy()),instance=self.instance)
                    if state is None:break
                    # Only authoritative current admissions remain in the room. Never trust metadata roles.
                    for p in participants:
                        if p.identity not in state['connections']:
                            try:await control.room.remove_participant(api.RoomParticipantIdentity(room=name,identity=p.identity))
                            except Exception:pass
                        elif not p.permissions.can_publish or not p.permissions.can_subscribe:
                            await control.room.update_participant(api.UpdateParticipantRequest(room=name,identity=p.identity,
                                permission=api.ParticipantPermission(can_publish=True,can_subscribe=True,can_publish_data=False,
                                    can_publish_sources=[api.TrackSource.MICROPHONE],can_update_metadata=False)))
                    allowed=state['allowed']
                    if not allowed or self.epoch!=state['epoch']:
                        await self.supervisor.close()
                    self.epoch=state['epoch']
                    await self.speech.tick()
                    desired=set()
                    for p in participants:
                        connection=state['connections'].get(p.identity)
                        for pub in p.track_publications.values():
                            subscribe=bool(allowed and connection and pub.source==rtc.TrackSource.SOURCE_MICROPHONE)
                            pub.set_subscribed(subscribe)
                            if subscribe and pub.track and pub.sid==connection[1]:
                                key=(connection[0],pub.sid,connection[2],state['epoch'])
                                desired.add(key);self.supervisor.start(key,pub.track)
                    await self.supervisor.retain(desired)
                    if not allowed:
                        await self.speech.stop('processing_paused')
                        await asyncio.to_thread(service.sync_room,self.engine,self.visit_id,self.generation,
                            identities,tracks,0,True,instance=self.instance)
                    await asyncio.sleep(.12)
                if self.transport_lost or self.room.connection_state!=rtc.ConnectionState.CONN_CONNECTED:
                    await self.fail('media_unavailable')
        except asyncio.CancelledError:raise
        except Exception as error:
            category=next((c for c in ['timeout','signal','ice','unauthorized','permission','connection refused','could not establish','invalid'] if c in str(error).lower()),'unclassified')
            print('Voice transport failure: '+type(error).__name__+' ['+category+']',flush=True)
            await self.fail('media_unavailable')
        finally:
            await self.speech.close()
            await self.supervisor.close()
            await self.room.disconnect()
            # A semantic end/revocation closes human transports. A failed worker must
            # not delete a live room that humans just rejoined after server recovery.
            try:
                def generation_closed():
                    with Session(self.engine) as session:
                        current=session.get(CallRecord,self.visit_id)
                        return not current or current.ended or current.generation!=self.generation
                if await asyncio.to_thread(generation_closed):
                    async with api.LiveKitAPI(self.settings.livekit_url,self.settings.livekit_api_key,self.settings.livekit_api_secret) as cleanup:
                        await cleanup.room.delete_room(api.DeleteRoomRequest(room=name))
            except Exception:pass


def run_warm_runtime(connection):
    # IPC carries only a readiness marker and one opaque room/generation pair.
    # Preload native SDK state before a patient joins, without opening a track,
    # subscribing, connecting to a room, or processing any audio.
    settings=Settings();engine=make_engine(settings.database_url)
    print('Owned runtime imports complete.',flush=True)
    async def execute():
        warm=rtc.AudioSource(24000,1,queue_size_ms=80)
        synthesizer=SpeechSynthesizer(settings)
        await synthesizer.warm()
        print('Owned runtime warmed.',flush=True);connection.send('ready')
        try:
            try:key=await asyncio.to_thread(connection.recv)
            except EOFError:return
            connection.close();print('Owned runtime assigned.',flush=True)
            await RoomWorker(engine,settings,UUID(key[0]),UUID(key[1]),UUID(key[2]),synthesizer).run()
        finally:await synthesizer.close();await warm.aclose()
    try:asyncio.run(execute())
    finally:connection.close();engine.dispose()


def transport_ready(settings):
    from urllib.request import urlopen
    try:
        with urlopen(settings.livekit_url.replace('ws://','http://').replace('wss://','https://'),timeout=.5) as response:
            return response.status==200
    except Exception:return False


def stop_runtime(process):
    # multiprocessing owns the actual process handle (including Windows venvs).
    if process.is_alive():process.terminate()
    process.join(timeout=2)
    if process.is_alive():process.kill();process.join(timeout=2)
    process.close()


def close_old_room(settings,key):
    async def close():
        import aiohttp
        async with api.LiveKitAPI(settings.livekit_url,settings.livekit_api_key,settings.livekit_api_secret,
            timeout=aiohttp.ClientTimeout(total=2),failover=False) as control:
            room=type('ClosedGeneration',(),{'encounter_id':key[0],'generation':key[1]})()
            await control.room.delete_room(api.DeleteRoomRequest(room=service.room_name(room)))
    try:asyncio.run(close())
    except Exception:pass # already closed or unavailable; never delete a new generation


def main():
    import multiprocessing,time
    settings=Settings();engine=make_engine(settings.database_url)
    if not service.configured(settings):raise RuntimeError('Configure the local LiveKit transport first.')
    context=multiprocessing.get_context('spawn');jobs={};spare=None;reported_offline=set();health_failures=0
    print('Owned voice supervisor ready.',flush=True)
    try:
        while True:
            with Session(engine) as session:
                calls=session.scalars(select(CallRecord).where(CallRecord.ended.is_(False))).all()
                wanted={(c.encounter_id,c.generation):(c.worker_error,c.worker_seen_at) for c in calls}
            health_failures=0 if transport_ready(settings) else health_failures+1
            online=health_failures<3
            for key,(process,started,admitted_at) in list(jobs.items()):
                error,seen=wanted.get(key,(None,None))
                # A prewarmed SDK join must make an actual connected heartbeat.
                # Never leave a native handshake parked indefinitely. Hard stops
                # are safe here because each room owns its process, not the FFI
                # state of other rooms. No readiness or fixture success is faked.
                overdue=time.monotonic()-started>15
                startup_stuck=bool(overdue and (seen is None or seen<admitted_at))
                stuck=startup_stuck or bool(error=='media_unavailable' and overdue)
                if startup_stuck and key in wanted:service.worker_failed(engine,*key,'media_unavailable')
                if key not in wanted or not online or not process.is_alive() or stuck:
                    stop_runtime(process);jobs.pop(key)
                    if key not in wanted and online:close_old_room(settings,key)
            if spare:
                process,channel,ready,started=spare
                if not process.is_alive() or (not ready and time.monotonic()-started>120):
                    stop_runtime(process);channel.close();spare=None
                elif not ready and channel.poll():
                    try:ready=channel.recv()=='ready'
                    except EOFError:ready=False
                    spare=(process,channel,ready,started)
                    if ready:
                        print('Owned runtime ready for admission.',flush=True)
                        import os,json
                        from pathlib import Path
                        target=os.environ.get('VOICE_READY_FILE')
                        if target:
                            ready_file=Path(target).resolve();local_root=Path(__file__).resolve().parents[5]/'.local'
                            if not ready_file.is_relative_to(local_root.resolve()):raise RuntimeError('Voice readiness must remain project-local.')
                            ready_file.write_text(json.dumps({'run_id':os.environ.get('VOICE_RUN_ID'),'native_sdk_warmed':True}))
            if not online:
                for key in wanted:
                    if key not in reported_offline:
                        service.worker_failed(engine,*key,'media_unavailable');reported_offline.add(key)
            else:
                reported_offline.clear()
                for key in wanted:
                    if key not in jobs and spare and spare[2]:
                        instance=uuid4()
                        if not service.worker_admitted(engine,*key,instance):continue
                        process,channel,_,_=spare;channel.send(tuple(str(x) for x in (*key,instance)));channel.close()
                        jobs[key]=(process,time.monotonic(),datetime.now(timezone.utc));spare=None;print('Owned runtime admitted.',flush=True)
                # Four total native runtimes, including one warm spare.
                if spare is None and len(jobs)<4:
                    parent,child=context.Pipe();process=context.Process(target=run_warm_runtime,args=(child,),daemon=True)
                    process.start();child.close();spare=(process,parent,False,time.monotonic())
            time.sleep(.3)
    finally:
        for process,_,_ in jobs.values():stop_runtime(process)
        if spare:stop_runtime(spare[0]);spare[1].close()
        engine.dispose()


if __name__=='__main__':main()
