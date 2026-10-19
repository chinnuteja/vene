"""Administrative calendar constraints from an explicitly stated interval, never clinical inference."""
import re
from datetime import timedelta
NUMBERS={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7}


def deadline(timeframe,visit_at):
    match=re.search(r'\bwithin\s+(\d{1,2}|one|two|three|four|five|six|seven)\s+days?\b',timeframe or '',re.I)
    if not match:return None
    word=match[1].lower();days=NUMBERS.get(word,int(word) if word.isdigit() else 0)
    if not 1<=days<=14:return None
    start=visit_at.date()
    return start,start+timedelta(days=days)


def check(item,visit_at,gateway,preferred):
    dates=deadline(item.timeframe,visit_at)
    if not dates:return None
    start,end=dates
    response=gateway.call('/availability',{'institution':'lab','earliest':start.isoformat(),'latest':end.isoformat(),
                                           'preferred':preferred})
    if response.get('institution')!='lab' or not response.get('reference') or not response.get('checked_at'):
        raise ValueError('Calendar response lacks provenance.')
    current=response.get('preferred_first')
    if current and start.isoformat()<=current['day']<=end.isoformat():
        return response,None
    options=response.get('alternatives',[])
    # The institution supplies every slot and time; the model cannot invent alternatives.
    options=[s for s in options if start.isoformat()<=s['day']<=end.isoformat()]
    option=options[0] if options else None
    first_day=current['day_name'] if current else None
    fact=preferred+(' has no slot before '+first_day if first_day else ' has no slot in the requested window')
    if option:
        fact+=' — '+option['location']+' has '+option['day_name']+' '+option['time_label']
    fact+='.'
    return response,{'kind':'no_slot_in_window','source':'Lab calendars · '+response['reference'],
        'fact':fact,'spoken':fact+' Would that work before we finish?',
        'alternative':option,'reference':response['reference'],'expires_at':response['expires_at'],
        'requested_start':start.isoformat(),'requested_end':end.isoformat()}
