#!/usr/bin/env python3
"""V230 rapid official PRE_RESULT fetch for imminent races, then V229 atomic freeze.

Site-reference ONLY. No results, payout, historical outcome, or combined API reads.
Future-only, fail-closed; if official data is absent, no new green eligibility proof.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlencode,urlsplit,parse_qs

JST=timezone(timedelta(hours=9))
UTC=timezone.utc
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
REG=re.compile(r'\b(\d{4})\s*/\s*(A1|A2|B1|B2)\b')
SCRATCH=re.compile(r'欠場|出走取消|出走取り消し|不出走|欠航|scratched|withdrawn',re.I)
BANNED=re.compile(r'欠場|出走取消|取消|不出走|scratched|withdrawn',re.I)
SCHEMA='BOAT_EDGE_V230_OFFICIAL_IMMINENT_REFRESH_V1'

def txt(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s or '')).strip()
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,UnicodeError,ValueError):return None

def write_bytes_exact(p,content):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.is_file() and p.read_bytes()==content:return
    p.write_bytes(content)

def write_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    if p.is_file() and p.read_bytes()==data:return
    p.write_bytes(data)

def due_for(key,clock):
    if not KEY.fullmatch(str(key)) or not re.fullmatch(r'\d\d:\d\d',str(clock)):return None
    try:return datetime.strptime(key[:8]+clock,'%Y%m%d%H:%M').replace(tzinfo=JST)
    except ValueError:return None

def parse_regs(html):
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(html,'lxml'); regs=[]; seen=set()
    for tr in soup.find_all('tr'):
        t=txt(tr.get_text(' ',strip=True))
        m=REG.search(t)
        if m and m.group(1) not in seen:
            regs.append(m.group(1));seen.add(m.group(1))
    return regs

def parse_before(html):
    """Mirror original V18 parse_before fields, no extrapolated exhibition."""
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(html,'lxml')
    # V291 parity: never confuse a 6.x racer/statistic row with the official
    # exhibition-time table. Ambiguous or absent labelled tables fail closed.
    exhibition_tables=[table for table in soup.find_all('table')
        if any(txt(th.get_text(' ',strip=True)).replace(' ','')=='展示タイム'
               for th in table.find_all('th'))]
    racers=[]
    for tr in (exhibition_tables[0].find_all('tr') if len(exhibition_tables)==1 else []):
        cells=tr.find_all(['th','td'])
        if not cells:continue
        c0=txt(cells[0].get_text(' ',strip=True))
        if not re.fullmatch(r'[1-6]',c0):continue
        lane=int(c0); t=txt(tr.get_text(' ',strip=True))
        # V294: same official indexed cells as the V292 rolling collector.
        # Other 6.x numbers in racer row are never exhibition time evidence.
        ex_cell=txt(cells[4].get_text(' ',strip=True)) if len(cells)>4 else ''
        ex=float(ex_cell) if re.fullmatch(r'\d{1,2}\.\d{1,2}',ex_cell) and 6.0<=float(ex_cell)<=8.5 else None
        tilt_cell=txt(cells[5].get_text(' ',strip=True)) if len(cells)>5 else ''
        tilt=float(tilt_cell) if re.fullmatch(r'-?(?:0\.(?:0|5)|1\.(?:0|5)|2\.0|3\.0)',tilt_cell) else None
        racers.append({'lane':lane,'exhibition_time':ex,'tilt':tilt,'raw_text':t})
    # V289: official START exhibition is the *same containing table* as
    # the header. It carries separately labelled boat-number and ST spans.
    # Picking the next unrelated table can mistake partial/other data for ST.
    starts=[]
    tag=soup.find('th',string=re.compile(r'^\s*スタート展示\s*$'))
    table=tag.find_parent('table') if tag else None
    if table:
        for div in table.select('div.table1_boatImage1'):
            lane_tag=div.select_one('.table1_boatImage1Number')
            st_tag=div.select_one('.table1_boatImage1Time')
            if not lane_tag or not st_tag:continue
            lane_str=txt(lane_tag.get_text(' ',strip=True))
            st=txt(st_tag.get_text(' ',strip=True))
            if not re.fullmatch(r'[1-6]',lane_str):continue
            if not re.fullmatch(r'(?:F|[+-])?0?\.\d{1,2}',st):continue
            starts.append({'lane':int(lane_str),'st':st})
    full=txt(soup.get_text(' ',strip=True));weather={}
    for k,p in {'air_temp_c':r'気温\s*([\d.]+)\s*℃',
                'water_temp_c':r'水温\s*([\d.]+)\s*℃',
                'wind_speed_ms':r'風速\s*([\d.]+)\s*m',
                'wave_cm':r'波高\s*([\d.]+)\s*cm'}.items():
        mm=re.search(p,full)
        weather[k]=float(mm.group(1)) if mm else None
    return {'racers':racers,'start_exhibition':starts,'weather':weather}

def beforeinfo_coverage(parsed):
    """Strict official 6/6 exhibition and 6/6 START ST; never infer missing rows."""
    expect=set(range(1,7))
    racers=parsed.get('racers',[]) if isinstance(parsed,dict) else []
    start=parsed.get('start_exhibition',[]) if isinstance(parsed,dict) else []
    ex={row.get('lane') for row in racers if isinstance(row,dict)
        and type(row.get('lane')) is int and row['lane'] in expect
        and type(row.get('exhibition_time')) in (int,float)
        and 6.0<=row['exhibition_time']<=8.5}
    st={row.get('lane') for row in start if isinstance(row,dict)
        and type(row.get('lane')) is int and row['lane'] in expect
        and isinstance(row.get('st'),str)
        and re.fullmatch(r'(?:F|[+-])?0?\.\d{1,2}',row['st'])}
    full_ex=len(racers)==6 and ex==expect
    full_st=len(start)==6 and st==expect
    return {'exhibition_lanes':len(ex),'start_exhibition_lanes':len(st),
            'exhibition_complete':full_ex,'start_exhibition_complete':full_st,
            'six_boat_complete':full_ex and full_st}


def targets(root,now,max_target=12):
    today=now.strftime('%Y%m%d'); summary=load(root/'data/today.json') or {}
    if str(summary.get('date','')).replace('-','')!=today:return []
    selected=[]
    for venue in summary.get('venues') or []:
        for row in venue.get('races') or []:
            key=row.get('race_key')
            due=due_for(key,row.get('deadline'))
            if not due or not str(key).startswith(today+'-'):continue
            mins=(due-now).total_seconds()/60
            if not 2<=mins<=19:continue
            if (root/'data/site_prediction_snapshots'/f'{key}.json').is_file():continue
            race=load(root/'data/races'/f'{key}.json') or {}
            m=race.get('meta') or {}
            if m.get('phase')!='PRE_RESULT' or any(m.get(f) is not False for f in ('results_seen','unlock','scoring')):continue
            if len(race.get('racers') or [])!=6:continue
            if race.get('race_key') not in (None,key):continue
            if str(m.get('venue_code')).zfill(2)!=key.split('-')[1] or int(m.get('race_no') or 0)!=int(key.split('-')[2]):continue
            selected.append((due,key))
    return [key for _,key in sorted(selected)[:max_target]]

def target_diagnostic(root, now):
    """Read-only eligibility counts; never loads results or relaxes targets()."""
    today=now.strftime('%Y%m%d')
    summary=load(root/'data/today.json') or {}
    counts={'today_mismatch':0,'invalid_deadline_or_key':0,
            'outside_2_to_19_min_window':0,'snapshot_exists':0,
            'race_missing_or_unsafe':0,'racers_not_six':0,
            'race_identity_mismatch':0,'eligible':0}
    if str(summary.get('date','')).replace('-','')!=today:
        counts['today_mismatch']=1
        return counts
    for venue in summary.get('venues') or []:
        for row in venue.get('races') or []:
            key=row.get('race_key')
            due=due_for(key,row.get('deadline'))
            if not due or not str(key).startswith(today+'-'):
                counts['invalid_deadline_or_key']+=1;continue
            mins=(due-now).total_seconds()/60
            if not 2<=mins<=19:
                counts['outside_2_to_19_min_window']+=1;continue
            if (root/'data/site_prediction_snapshots'/f'{key}.json').is_file():
                counts['snapshot_exists']+=1;continue
            race=load(root/'data/races'/f'{key}.json') or {}
            meta=race.get('meta') or {}
            if meta.get('phase')!='PRE_RESULT' or any(meta.get(f) is not False for f in ('results_seen','unlock','scoring')):
                counts['race_missing_or_unsafe']+=1;continue
            if len(race.get('racers') or [])!=6:
                counts['racers_not_six']+=1;continue
            if race.get('race_key') not in (None,key) or str(meta.get('venue_code')).zfill(2)!=key.split('-')[1] or int(meta.get('race_no') or 0)!=int(key.split('-')[2]):
                counts['race_identity_mismatch']+=1;continue
            counts['eligible']+=1
    return counts


def source_identity(url):
    """Accept only one explicit official PRE_RESULT race, before any request."""
    u=urlsplit(url)
    if (u.scheme!='https' or u.netloc!='www.boatrace.jp' or u.fragment
            or u.path not in ('/owpc/pc/race/racelist',
                             '/owpc/pc/race/beforeinfo','/owpc/pc/race/odds3t')):
        raise ValueError('V278_NON_PRE_RESULT_SOURCE')
    q=parse_qs(u.query,keep_blank_values=True,strict_parsing=True)
    if set(q)!={'hd','jcd','rno'} or any(len(v)!=1 for v in q.values()):
        raise ValueError('V278_AMBIGUOUS_RACE_QUERY')
    day,venue,race=(q[k][0] for k in ('hd','jcd','rno'))
    if (not re.fullmatch(r'20[0-9]{6}',day)
            or not re.fullmatch(r'[0-9]{2}',venue) or not 1<=int(venue)<=24
            or not re.fullmatch(r'[0-9]{1,2}',race) or not 1<=int(race)<=12):
        raise ValueError('V278_INVALID_RACE_IDENTITY')
    datetime.strptime(day,'%Y%m%d')
    return u.path,day,venue,int(race)

def fetch(session,url):
    requested=source_identity(url)
    # Never visit an unchecked redirect, including results/combined endpoints.
    r=session.get(url,timeout=(4,13),allow_redirects=False)
    if 300<=r.status_code<400:
        raise RuntimeError('V278_REDIRECT_BLOCKED_BEFORE_FOLLOW')
    r.raise_for_status()
    if source_identity(r.url)!=requested:
        raise RuntimeError('V278_RESPONSE_RACE_IDENTITY_MISMATCH')
    r.encoding=r.apparent_encoding or r.encoding or 'utf-8'
    return r.content,r.text,datetime.now(JST)

def fetch_one(root,key):
    import requests
    import time
    params={'hd':key[:8],'jcd':key.split('-')[1],'rno':str(int(key.split('-')[2]))}
    session=requests.Session()
    session.headers.update({'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36',
        'Accept-Language':'ja-JP,ja;q=0.9,en;q=0.7','Connection':'close'})
    q=urlencode(params)
    base='https://www.boatrace.jp/owpc/pc/race/'
    def retry_transient_only(url):
        # V230: one bounded second attempt for transient transport / official
        # 429/5xx responses. The original fetch() still rejects redirects,
        # different race identity, non-official URLs, or malformed inputs.
        for attempt in range(2):
            try:
                return fetch(session,url)
            except (requests.exceptions.ConnectionError,requests.exceptions.Timeout):
                if attempt:raise
            except requests.exceptions.HTTPError as exc:
                status=getattr(getattr(exc,'response',None),'status_code',None)
                if attempt or status not in (429,500,502,503,504):raise
            time.sleep(0.35)
        raise RuntimeError('V230_TRANSIENT_RETRY_EXHAUSTED')
    try:
        rb,rtext,rt=retry_transient_only(base+'racelist?'+q)
        bb,btext,bt=retry_transient_only(base+'beforeinfo?'+q)
        ob,otext,ot=retry_transient_only(base+'odds3t?'+q)
        return key,{'racelist':(rb,rtext,rt),'beforeinfo':(bb,btext,bt),'odds':(ob,otext,ot)},None
    except Exception as ex:
        return key,None,type(ex).__name__+': '+str(ex)[:130]
    finally:session.close()

def verified_odds(html):
    """The independent V167 DOM label audit must pass before any stored price."""
    from bs4 import BeautifulSoup
    from site_odds_v167_dom_verifier import verify_official_dom_price_mapping
    proof=verify_official_dom_price_mapping(html)
    if proof.get('status')!='PASS' or proof.get('checked')!=120 or proof.get('available')!=120:
        raise ValueError('V230_INCOMPLETE_OR_UNVERIFIED_OFFICIAL_ODDS_120')
    soup=BeautifulSoup(html,'lxml')
    raw=[re.sub(r'\s+','',x.get_text('',strip=True)).replace(',','') for x in soup.select('td.oddsPoint')]
    if len(raw)!=120:raise ValueError('V230_ODDS_DOM_SIZE_INVALID')
    matrix=[raw[i*6:(i+1)*6] for i in range(20)]
    ordered=[matrix[row][col] for col in range(6) for row in range(20)]
    combos=[f'{a}-{b}-{c}' for a in range(1,7) for b in range(1,7) for c in range(1,7)
            if len({a,b,c})==3]
    odds={k:float(v) for k,v in zip(combos,ordered)}
    if len(odds)!=120 or any(not (0 < v < float('inf')) for v in odds.values()):
        raise ValueError('V230_ODDS_VALUES_INVALID')
    return odds

def extract_blocked(racers,rtext,btext,parse_ok):
    lanes=[]
    for row in racers:
        fields=[row.get('status'),row.get('race_status'),row.get('entry_status'),row.get('scratch_status'),row.get('raw_text')]
        if (any(row.get(f) is True for f in ('scratched','withdrawn','absent','cancelled','canceled'))
                or any(BANNED.search(v) for v in fields if isinstance(v,str))):
            lanes.append(row.get('lane'))
    flagged=[]
    if SCRATCH.search(rtext):flagged.append('racelist')
    if SCRATCH.search(btext):flagged.append('beforeinfo')
    reasons=[]
    if not parse_ok:reasons.append('公式直前情報の展示データを検証できない')
    if lanes:reasons.append('選手行に欠場・取消の明示情報あり')
    if flagged:reasons.append('公式HTMLに欠場・取消の表記あり')
    return reasons,lanes,flagged

def update_one(root,key,data,now):
    racer_path=root/'data/races'/f'{key}.json'
    race=load(racer_path)
    if not isinstance(race,dict):return 'race_missing'
    m=race.get('meta') or {}
    due=due_for(key,m.get('deadline'))
    if not due or not 2<=(due-now).total_seconds()/60<=19:return 'window_passed'
    if m.get('phase')!='PRE_RESULT' or any(m.get(f) is not False for f in ('results_seen','unlock','scoring')):return 'pre_result_unverified'
    rb,rtext,rt=data['racelist'];bb,btext,bt=data['beforeinfo']
    ob,otext,ot=data['odds']
    try: odds=verified_odds(otext)
    except (ValueError,TypeError,OverflowError):odds=None
    stored=[str(x.get('registration_no')) for x in (race.get('racers') or [])]
    actual=parse_regs(rtext)
    # Require precisely the same six official registrations, no invented identity.
    if len(stored)!=6 or len(set(stored))!=6 or len(actual)!=6 or set(stored)!=set(actual):return 'six_registration_mismatch'
    parsed=parse_before(btext)
    coverage=beforeinfo_coverage(parsed)
    ready=coverage['six_boat_complete']
    reasons,lanes,flags=extract_blocked(race['racers'],rtext,btext,ready)
    # This is a verified official refresh, even if exhibition still unavailable.
    # Unavailable data remains 'published_wait' and cannot become a green snapshot.
    audit=race.setdefault('source_audit',{})
    urlbase='https://www.boatrace.jp/owpc/pc/race/'
    param=urlencode({'hd':key[:8],'jcd':key.split('-')[1],'rno':int(key.split('-')[2])})
    audit['race_card']={'status':'ok','source':urlbase+'racelist?'+param,
                        'fetched_at':rt.isoformat(timespec='seconds'),'sha256':sha(rb),'error':None}
    audit['beforeinfo']={'status':'ok' if ready else 'published_wait',
                         'source':urlbase+'beforeinfo?'+param,'fetched_at':bt.isoformat(timespec='seconds'),
                         'sha256':sha(bb),'error':None,
                         'six_boat_coverage':coverage}
    race['beforeinfo']=parsed
    m['updated_at']=bt.isoformat(timespec='seconds')
    race['meta']=m
    raw=root/'data/raw'/key[:8];vv,rr=key.split('-')[1:]
    # Stage HTML + parsed source + scratch check for the very same official bytes.
    write_bytes_exact(raw/f'{vv}_{rr}_racelist.html',rb)
    write_bytes_exact(raw/f'{vv}_{rr}_beforeinfo.html',bb)
    write_json(racer_path,race)
    proof={'schema_version':'boat-edge-v182-scratch-evidence-v1',
           'race_key':key,'source_date':key[:8],
           'checked_at':datetime.now(JST).isoformat(),
           'blocked':bool(reasons),'reason':' / '.join(reasons) if reasons else None,
           'suspect_lanes':lanes,'official_raw_flags':flags,
           'race_card_source_status':'ok',
           'official_beforeinfo_source_status':audit['beforeinfo']['status'],
           'official_beforeinfo_six_boat_complete':ready,
           'limitations':'No scratch signal detected is not certified 6-boat participation; raw collector freshness limits detection.'}
    write_json(root/'data/site_scratches_v182'/f'{key}.json',proof)
    if odds is not None:
        # V167 source-label parity has passed on exactly these fetched bytes.
        odds_doc={'schema_version':'boat-edge-site-odds-v71','race_key':key,
            'fetched_at':ot.isoformat(timespec='seconds'),
            'source':'BOAT RACE オフィシャルウェブサイト 3連単オッズ',
            'source_url':urlbase+'odds3t?'+param,
            'phase':'PRE_RESULT_PURCHASE_ONLY',
            'results_seen':False,'scoring':False,
            'deadline':m.get('deadline'),
            'minutes_to_deadline':round((due-now).total_seconds()/60,2),
            'trifecta_odds':odds,'available_count':120,
            'unavailable_count':0,'unavailable_combinations':[],
            'verified_official_dom_v167':True,
            'raw_official_html_sha256':sha(ob)}
        # Raw compressed odds HTML permits independent byte-level replay of the V167 mapping.
        import gzip
        write_bytes_exact(raw/f'{vv}_{rr}_odds3t.html.gz',gzip.compress(ob,compresslevel=9,mtime=0))
        write_json(root/'data/site_odds'/f'{key}.json',odds_doc)
    if reasons:return 'source_blocked'
    return 'fresh_verified' if odds is not None else 'odds_incomplete'

def run(root,now=None,worker=6):
    from boat_edge_v228_freeze_only import check_formal_closed
    from boat_edge_v229_atomic_freeze import run as atomic_freeze
    root=Path(root).resolve();now=now or datetime.now(JST)
    now=now.astimezone(JST)
    check_formal_closed(root)
    selected=targets(root,now)
    diagnostic=target_diagnostic(root,now)
    status={'schema':SCHEMA,'day_jst':now.strftime('%Y%m%d'),'targets':selected,'target_diagnostic':diagnostic,
            'source_refreshed':0,'source_blocked':0,'odds_incomplete':0,'network_error':0,'outcomes':{}}
    if selected:
        with ThreadPoolExecutor(max_workers=worker) as pool:
            futures=[pool.submit(fetch_one,root,key) for key in selected]
            for task in as_completed(futures):
                key,data,err=task.result()
                if err:
                    status['network_error']+=1;status['outcomes'][key]='fetch_failed:'+err
                    continue
                state=update_one(root,key,data,datetime.now(JST))
                if state=='fresh_verified':status['source_refreshed']+=1
                if state=='source_blocked':status['source_blocked']+=1
                if state=='odds_incomplete':status['odds_incomplete']+=1
                status['outcomes'][key]=state
    # Existing V229 is the only authority allowed to create the immutable first snapshot.
    # It reads neither historical results nor formal prediction data.
    count=atomic_freeze(root)
    status['new_snapshots_atomic_audited']=count
    # Observability only. A race marked source_blocked remains ineligible.
    output=root/'data/site_autopilot/v230_fast_current.json'
    write_json(output,status)
    print('V230_FAST_OFFICIAL_PRE_RESULT '+json.dumps({k:v for k,v in status.items() if k!='outcomes'},ensure_ascii=False,sort_keys=True))
    return status

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--workers',type=int,default=6)
    args=p.parse_args();run(args.root,worker=min(8,max(1,args.workers)))
