"""Dedicated commit notification channel. No text, identities or credentials in payloads."""
import asyncio
import json
import psycopg
import threading


class SpeechFence:
    def __init__(self,engine,visit_id,invalidate):
        self.engine=engine;self.visit_id=str(visit_id);self.invalidate=invalidate
        self.connection=None;self.task=None;self.healthy=False
        self.stopped=threading.Event();self.loop=None

    async def start(self):
        url=self.engine.url
        def connect():
            connection=psycopg.connect(host=url.host,port=url.port or 5432,dbname=url.database,
                user=url.username,password=url.password,autocommit=True,connect_timeout=2)
            try:connection.execute('LISTEN vene_speech_fence');return connection
            except Exception:connection.close();raise
        self.loop=asyncio.get_running_loop()
        connecting=asyncio.create_task(asyncio.to_thread(connect))
        try:self.connection=await asyncio.shield(connecting)
        except asyncio.CancelledError:
            try:
                connection=await connecting;await asyncio.to_thread(connection.close)
            except Exception:pass
            raise
        self.healthy=True;self.task=asyncio.create_task(asyncio.to_thread(self.listen))

    def listen(self):
        try:
            while not self.stopped.is_set():
                for notification in self.connection.notifies(timeout=.2):
                    payload=json.loads(notification.payload)
                    if payload.get('visit')==self.visit_id:
                        self.loop.call_soon_threadsafe(self.invalidate,payload.get('reason','context_changed'))
        except Exception:
            self.healthy=False;self.loop.call_soon_threadsafe(self.invalidate,'authorization_channel_lost')
        finally:self.healthy=False

    async def close(self):
        self.stopped.set()
        if self.task:await asyncio.gather(self.task,return_exceptions=True)
        if self.connection:await asyncio.to_thread(self.connection.close)
        self.healthy=False
