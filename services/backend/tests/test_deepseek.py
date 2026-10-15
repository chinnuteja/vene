"""Provider-boundary regressions: malformed outputs must never become plans."""
import asyncio
import json
import httpx
import pytest
from openai import AsyncOpenAI
from bring_vene.config import Settings
from bring_vene.understanding import gateway


@pytest.mark.parametrize('content,reason,ok',[
    ('{"answers":[],"steps":[]}','stop',True),
    ('','stop',False),
    ('{"answers":[],"steps":[]}','length',False),
    ('{"answers":[],"steps":[],"patient_authorized":true}','stop',False),
    ('{"answers":[],"steps":[{"title":"Book now"}]}','stop',False),
])
def test_deepseek_validates_actual_http_content_and_never_uses_fixture(monkeypatch,content,reason,ok):
    requests=[]
    def respond(request):
        requests.append(json.loads(request.content))
        assert str(request.url)=='https://api.deepseek.com/chat/completions'
        return httpx.Response(200,json={'id':'synthetic','object':'chat.completion','created':1,'model':'deepseek-flash',
            'choices':[{'index':0,'finish_reason':reason,'message':{'role':'assistant','content':content}}]})
    def client(**kwargs):
        return AsyncOpenAI(**kwargs,http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)))
    monkeypatch.setattr(gateway,'AsyncOpenAI',client)
    monkeypatch.setattr(gateway,'fixture_extract',lambda _:pytest.fail('Live failure invoked fixture fallback'))
    settings=Settings(model_provider='deepseek',deepseek_api_key='synthetic-only')
    if ok:
        result=asyncio.run(gateway.ModelGateway(settings).extract({'sources':[],'priorities':[]}))
        assert result.model=='deepseek-flash' and not result.extraction.steps
    else:
        with pytest.raises((RuntimeError,ValueError)):
            asyncio.run(gateway.ModelGateway(settings).extract({'sources':[],'priorities':[]}))
    assert len(requests)==1 and 'tools' not in requests[0]
    assert requests[0]['thinking']=={'type':'disabled'}


def test_missing_deepseek_key_does_not_use_other_provider_or_fixture():
    settings=Settings(model_provider='deepseek',deepseek_api_key='',openai_api_key='other-provider')
    assert gateway.configuration(settings)[0]=='unavailable'
    with pytest.raises(RuntimeError,match='model_unconfigured'):
        asyncio.run(gateway.ModelGateway(settings).extract({}))
