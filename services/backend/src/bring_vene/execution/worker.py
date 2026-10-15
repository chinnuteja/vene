import time
from bring_vene.config import Settings
from bring_vene.persistence.database import make_engine
from bring_vene.execution.gateway import OfficeGateway
from bring_vene.execution.service import dispatch
from bring_vene.continuity.worker import deliver
from bring_vene.continuity.service import prune_metadata

def main():
    settings=Settings();OfficeGateway(settings) # explicit configuration, never silently simulate
    engine=make_engine(settings.database_url)
    print('Administrative worker ready: LOCAL SANDBOX ONLY.',flush=True)
    try:
        last_prune=0
        while True:
            try:
                worked=dispatch(engine,settings)
                worked=deliver(engine,settings) or worked
                if time.monotonic()-last_prune>60:prune_metadata(engine,settings);last_prune=time.monotonic()
            except Exception as error:
                print('Administrative worker unavailable: '+type(error).__name__,flush=True);worked=False
            time.sleep(.2 if worked else .5)
    finally:engine.dispose()

if __name__=='__main__':main()
