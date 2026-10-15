import json
from urllib.request import Request, build_opener,HTTPRedirectHandler
from urllib.parse import urlparse

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

class OfficeGateway:
    def __init__(self,settings):
        parsed=urlparse(settings.office_url)
        if (not settings.bring_vene_development or parsed.scheme!='http' or parsed.hostname!='127.0.0.1' or
            parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'','/'} or not settings.office_token):
            raise RuntimeError('The explicit local sandbox office is not configured; no fallback is available.')
        self.settings=settings

    def call(self,path,payload=None):
        data=json.dumps(payload).encode() if payload is not None else None
        request=Request(self.settings.office_url+path,data=data,headers={
            'Authorization':'Bearer '+self.settings.office_token,'Content-Type':'application/json'})
        with build_opener(NoRedirect).open(request,timeout=self.settings.office_timeout_seconds) as response:
            result=json.loads(response.read(65537))
        if result.get('sandbox') is not True:raise ValueError('Expected a sandbox response.')
        return result
