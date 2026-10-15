import asyncio
from types import SimpleNamespace
import pytest
from livekit.agents.stt import SpeechEventType as Kind
from bring_vene.voice.supervisor import DeepgramSink


def event(kind,text=''):
    return SimpleNamespace(type=kind,alternatives=[SimpleNamespace(text=text)])


def test_finalized_fragments_wait_for_endpoint_and_pause_discards_pending_text():
    async def run():
        seen=[]
        async def final(text):seen.append(text)
        sink=DeepgramSink(None,final,None)
        await sink.accept_event(event(Kind.FINAL_TRANSCRIPT,'Maria will arrange the visit at Riverside'))
        await sink.accept_event(event(Kind.INTERIM_TRANSCRIPT,'wrong provisional words'))
        await sink.accept_event(event(Kind.FINAL_TRANSCRIPT,'Lab on Tuesday.'))
        assert not seen
        await sink.accept_event(event(Kind.END_OF_SPEECH))
        await sink.accept_event(event(Kind.END_OF_SPEECH))
        assert seen==['Maria will arrange the visit at Riverside Lab on Tuesday.']
        await sink.accept_event(event(Kind.FINAL_TRANSCRIPT,'discard when processing pauses'))
        await sink.close()
        await sink.accept_event(event(Kind.END_OF_SPEECH))
        assert len(seen)==1 and not sink.fragments
    asyncio.run(run())


def test_unfinished_utterance_is_bounded_without_publishing_partial_text():
    async def run():
        async def final(_):pytest.fail('Oversize unfinished utterance was published')
        sink=DeepgramSink(None,final,None)
        await sink.accept_event(event(Kind.FINAL_TRANSCRIPT,'a'*12000))
        with pytest.raises(RuntimeError,match='utterance_too_long'):
            await sink.accept_event(event(Kind.FINAL_TRANSCRIPT,'overflow'))
        await sink.close()
        assert not sink.fragments
    asyncio.run(run())
