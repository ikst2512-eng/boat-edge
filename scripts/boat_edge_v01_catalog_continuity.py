#!/usr/bin/env python3
"""Read-only fail-closed same-day race catalog continuity check.

No network, no source/prediction writes, no result/formal data access.
The existing collector remains the sole publisher and records source health.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import json
import re

def should_keep_verified_same_day_catalog(path:Path,candidate:dict,now:datetime)->bool:
    if not isinstance(now,datetime) or now.tzinfo is None or not isinstance(candidate,dict):
        return False
    day=now.strftime('%Y%m%d')
    iso=now.strftime('%Y-%m-%d')
    if (candidate.get('date')!=iso or candidate.get('phase')!='PRE_RESULT'
            or candidate.get('venues')!=[]
            or any(candidate.get(k) is not False for k in ('results_seen','unlock','scoring'))):
        return False
    if path.is_symlink() or not path.is_file() or any(p.is_symlink() for p in path.parents):
        return False
    try:
        blob=path.read_bytes()
        if len(blob)>2_000_000:return False
        doc=json.loads(blob)
        if not isinstance(doc,dict) or any([
            doc.get('schema_version')!='boat-edge-today-v5',
            doc.get('collector_version')!='BOAT_EDGE_V18',
            doc.get('date')!=iso,
            doc.get('phase')!='PRE_RESULT',
            any(doc.get(k) is not False for k in ('results_seen','unlock','scoring'))
        ]):return False
        updated=datetime.fromisoformat(doc['updated_at'].replace('Z','+00:00'))
        if updated.tzinfo is None or updated.astimezone(now.tzinfo).strftime('%Y-%m-%d')!=iso:
            return False
        age=(now.astimezone(timezone.utc)-updated.astimezone(timezone.utc)).total_seconds()
        if not 0<=age<=90*60:return False
        venues=doc.get('venues')
        if not isinstance(venues,list) or not 1<=len(venues)<=24:return False
        meta=doc.get('collector')
        if not isinstance(meta,dict) or meta.get('active_venues')!=len(venues):
            return False
        seen=set()
        for venue in venues:
            if not isinstance(venue,dict):return False
            code=venue.get('jcd')
            if not isinstance(code,str) or not re.fullmatch(r'(?:0[1-9]|1\d|2[0-4])',code):
                return False
            if code in seen:return False
            seen.add(code)
            races=venue.get('races')
            if not isinstance(races,list) or len(races)!=12:return False
            numbers=set()
            for race in races:
                if not isinstance(race,dict) or type(race.get('race_no')) is not int:
                    return False
                rno=race['race_no']
                if not 1<=rno<=12 or rno in numbers:return False
                numbers.add(rno)
                key=f'{day}-{code}-{rno:02d}'
                if race.get('race_key')!=key or race.get('file')!=f'data/races/{key}.json':
                    return False
                deadline=race.get('deadline')
                if not isinstance(deadline,str) or re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',deadline) is None:
                    return False
                racefile=path.parent/'races'/f'{key}.json'
                if racefile.is_symlink() or not racefile.is_file():
                    return False
        return True
    except (OSError,TypeError,ValueError,UnicodeError,KeyError,OverflowError):
        return False
