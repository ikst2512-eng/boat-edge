#!/usr/bin/env python3
"""Materialize display-only racer/course stats from already-frozen V146 PRE_RESULT source.
No results endpoint, settlement, or combined API is read. No predictor or formal data is written.
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SRC = Path('data/site_racer_actual_course/v146')
DEST = Path('data/site_racer_recent_v165')
CUTOFF = '2026-10-07'  # fixed provenance: never extend into formal 2026-10-08
DIGITS = ('2', '3', '4', '5')
METHODS = ('逃げ', '差し', 'まくり', 'まくり差し', '抜き', '恵まれ')
WINDOWS = ('3m', '6m', '1y')


def checked_source():
    manifest_bytes = (SRC / 'manifest.json').read_bytes()
    m = json.loads(manifest_bytes)
    if m.get('as_of_d1') != CUTOFF or m.get('status') != 'DATA_ONLY_NOT_PREDICTION_CONNECTED':
        raise ValueError('V146 source version not approved, source cutoff changed or prediction connection changed')
    if m.get('prediction_weights_changed') is not False or m.get('proxy') is not False or m.get('imputation') is not False:
        raise ValueError('V146 source safety assertion failed')
    if m.get('source',{}).get('commit') != '2d149e1ae838f6ed3426a7989be69e799ac2988f':
        raise ValueError('Unexpected V146 pinned source commit')
    coverage=m.get('coverage',{}).get('windows',{})
    if coverage.get('3m',{}).get('complete') is not True or coverage.get('6m',{}).get('complete') is not False:
        raise ValueError('Unexpected calendar coverage: revisit UI accuracy caveats')
    return m, hashlib.sha256(manifest_bytes).hexdigest()


def safe_current_cards(day, source_end):
    today = json.loads(Path('data/today.json').read_text(encoding='utf-8'))
    day_iso = f'{day[:4]}-{day[4:6]}-{day[6:8]}'
    if today.get('date') != day_iso or today.get('results_seen') is not False or today.get('unlock') is not False or today.get('scoring') is not False:
        raise ValueError('Today PRE_RESULT guarded index unavailable')
    if source_end >= day_iso:
        raise ValueError('History contains target date or is not D-minus-1 safe')
    # Only PRE_RESULT race cards may be inspected to determine racer IDs.
    racers = set()
    eligible=0
    for v in today.get('venues',[]):
        for entry in v.get('races',[]):
            key=str(entry.get('race_key',''))
            filename=str(entry.get('file',''))
            if not re.fullmatch(re.escape(day)+r'-\d\d-\d\d',key):
                raise ValueError('Race index includes incorrect date or key')
            if filename != 'data/races/'+key+'.json':
                raise ValueError('Unsafe race card filename')
            file=Path(filename)
            if not file.is_file():
                continue
            card = json.loads(file.read_text(encoding='utf-8'))
            m=card.get('meta',{})
            if (card.get('race_key')!=key or m.get('results_seen') is not False or
                m.get('unlock') is not False or m.get('scoring') is not False or
                m.get('phase') != 'PRE_RESULT'):
                raise ValueError('Race card result/formal guard failure')
            rows=card.get('racers',[])
            if len(rows)!=6:
                continue
            ids=[str(x.get('registration_no','')) for x in rows]
            if len(set(ids))!=6 or not all(re.fullmatch(r'\d{4}',x) for x in ids):
                # Do not fabricate a registration number. Skip this race entirely.
                continue
            racers.update(x for x in ids if re.fullmatch(r'[2-5]\d{3}',x))
            eligible+=1
    if not racers:
        raise ValueError('No PRE_RESULT racers to render')
    return racers,eligible,len(today.get('venues',[]))


def sample_summary(row):
    if not isinstance(row,dict) or not isinstance(row.get('starts'),int) or row['starts']<0:
        return None
    starts=row['starts']; wins=row.get('wins'); top2=row.get('top2'); top3=row.get('top3')
    if any(not isinstance(z,int) or z<0 for z in (wins,top2,top3)) or not (wins<=top2<=top3<=starts):
        raise ValueError('Impossible ordered finish counts')
    methods=row.get('win_methods') or {}
    if not isinstance(methods,dict) or any(k not in METHODS or not isinstance(v,int) or v<0 for k,v in methods.items()):
        raise ValueError('Unexpected winning method counts')
    if sum(methods.values())>wins:
        raise ValueError('Method counts exceed total wins')
    st_n=row.get('st_n')
    st=row.get('avg_st')
    if st_n is not None and (not isinstance(st_n,int) or st_n<0 or st_n>starts):
        raise ValueError('Invalid start-time sample count')
    return {'starts':starts,'wins':wins,'top2':top2,'top3':top3,
            'avg_st':st,'st_n':st_n,'win_methods':{m:methods[m] for m in METHODS if m in methods},
            'sample_band':row.get('sample_band')}


def build(day):
    if not re.fullmatch(r'\d{8}',day):
        raise ValueError('Date must be YYYYMMDD')
    m,manifest_sha=checked_source()
    ids,races,venues=safe_current_cards(day,m['as_of_d1'])
    racer_rows={}
    for digit in DIGITS:
        pending=ids.intersection({x for x in ids if x.startswith(digit)})
        if not pending:
            continue
        file=SRC/(digit+'.json')
        b=file.read_bytes(); declared=m.get('shards',{}).get(digit+'.json',{})
        if len(b)!=declared.get('bytes') or hashlib.sha256(b).hexdigest()!=declared.get('sha256'):
            raise ValueError('V146 historic shard SHA mismatch: '+digit)
        item=json.loads(b)
        if item.get('as_of_d1') != CUTOFF or item.get('schema_version') != 'boat-edge-racer-actual-course-v146':
            raise ValueError('V146 shard schema mismatch')
        for reg in sorted(pending):
            rider=item.get('racers',{}).get(reg)
            if not rider:
                continue
            courses={}
            for c,spans in rider.get('courses',{}).items():
                if c not in ('1','2','3','4','5','6'):
                    continue
                if not isinstance(spans,dict):continue
                windows={}
                for w in WINDOWS:
                    stats=sample_summary(spans.get(w))
                    if stats is not None: windows[w]=stats
                if windows:courses[c]=windows
            if courses:racer_rows[reg]={'courses':courses}
    report={'schema_version':'boat-edge-site-racer-course-display-v165',
            'site_date':f'{day[:4]}-{day[4:6]}-{day[6:8]}',
            'status':'DISPLAY_ONLY_RESEARCH_NOT_PREDICTION_CONNECTED',
            'source':{'name':'V146_ACTUAL_COURSE_HISTORY','as_of_d1':CUTOFF,
                      'source_manifest_sha256':manifest_sha,
                      'repo':m['source']['repo'],'commit':m['source']['commit'],
                      'coverage':m['coverage']['windows'],
                      'missing_or_unpaired_days':m['coverage']['missing_or_unpaired_days']},
            'quality':{'races_checked':races,'venues_indexed':venues,
                       'race_racers_requested':len(ids),'racers_with_data':len(racer_rows)},
            'racers':racer_rows}
    out=DEST/(day+'.json');out.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(report,ensure_ascii=False,separators=(',',':'),sort_keys=True)+'\n'
    out.write_text(content,encoding='utf-8')
    print('V165 DATA PASS',day,'PRE_RESULT races',races,'unique racers',len(ids),'historical racers',len(racer_rows),'bytes',len(content.encode('utf-8')))
    return report


def main():
    jst=datetime.now(timezone(timedelta(hours=9)))
    day=jst.strftime('%Y%m%d')
    data=build(day)
    if data['source']['as_of_d1']!='2026-10-07':raise ValueError('Unexpected formal history inclusion')

if __name__=='__main__':main()
