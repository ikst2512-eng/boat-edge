"""V167 official pre-race odds layout parity audit; never reads outcomes."""
from __future__ import annotations
import json
import re
import sys
import time
from datetime import datetime,timedelta,timezone
from pathlib import Path
import requests
from scripts.site_odds_v167_dom_verifier import verify_official_dom_price_mapping

JST=timezone(timedelta(hours=9))
ROOT=Path('.')
REPORT=ROOT/'data/site_odds/verification_v167.json'
WORKFLOW=ROOT/'.github/workflows/site-odds.yml'
VERIFY_INSERT='              # V167: fail closed unless all 120 DOM labels match their odds.\n              from scripts.site_odds_v167_dom_verifier import verify_official_dom_price_mapping\n              verify_official_dom_price_mapping(html)\n'
MARKER='              # Do not publish a suspicious partial scrape.\n'


def run():
    now=datetime.now(JST)
    state=json.loads(Path('data/today.json').read_text(encoding='utf-8'))
    wf=WORKFLOW.read_text(encoding='utf-8')
    if VERIFY_INSERT in wf:
        print('V167 collector already guarded; safe no-op')
        return
    if MARKER not in wf or wf.count(MARKER)!=1:
        raise ValueError('Unexpected V71 collector anchors; cannot auto-patch')
    choices=[]
    if state.get('date')==now.strftime('%Y-%m-%d'):
        for venue in state.get('venues',[]):
            jcd=str(venue.get('jcd','')).zfill(2)
            if not re.fullmatch(r'\d{2}',jcd):continue
            for race in venue.get('races',[]):
                dl=str(race.get('deadline') or '')
                mm=re.fullmatch(r'(\d{1,2}):(\d{2})',dl)
                if not mm:continue
                deadline=now.replace(hour=int(mm.group(1)),minute=int(mm.group(2)),second=0,microsecond=0)
                delta=(deadline-now).total_seconds()/60
                key=str(race.get('race_key') or '')
                if not 8<=delta<=45 or not re.fullmatch(r'\d{8}-\d{2}-\d{2}',key):continue
                if key[:8]!=now.strftime('%Y%m%d') or key[9:11]!=jcd:continue
                choices.append((delta,jcd,int(race.get('race_no')),key))
    # Choose 2 different venues when possible; avoid duplicating site load.
    choices.sort()
    selected=[]
    seen=set()
    for c in choices:
        if c[1] in seen:continue
        selected.append(c);seen.add(c[1])
        if len(selected)==2:break
    report={'schema_version':'boat-edge-official-odds-dom-parity-v167',
            'date_jst':now.strftime('%Y-%m-%d'),
            'result_payout_combined_apis_accessed':False,
            'formal_2026_10_08_unchanged':True,
            'model_weights_changed':False,
            'purpose':'check live official 3連単 DOM labels + numeric order before collector promotion',
            'required_independent_races':2,
            'samples':[]}
    session=requests.Session()
    session.headers.update({'User-Agent':'Mozilla/5.0 (compatible; BOAT-EDGE-ODDS-VERIFY/1.0)', 'Accept-Language':'ja-J,ja;q=0.9'})
    for _,jcd,rno,key in selected:
        url='https://www.boatrace.jp/owpc/pc/race/odds3t?hd='+key[:8]+'&jcd='+jcd+'&rno='+str(rno)
        item={'race_key':key,'venue':jcd,'official_odds_url':url}
        try:
            response=session.get(url,timeout=(5,20));response.raise_for_status()
            response.encoding=response.apparent_encoding or response.encoding or 'utf-8'
            check=verify_official_dom_price_mapping(response.text)
            if check.get('checked')!=120:
                raise ValueError('non-120 parity')
            item.update(check)
        except Exception as exc:
            item.update({'status':'FAIL','error':type(exc).__name__+': '+str(exc)[:230]})
        report['samples'].append(item)
        time.sleep(.4)
    passes=sum(item['status']=='PASS' for item in report['samples'])
    if len(report['samples'])<2:
        report['status']='WAITING_TWO_LIVE_VENUES'
    elif passes!=len(report['samples']):
        report['status']='FAIL_UNVERIFIED_NO_COLLECTOR_CHANGE'
    else:
        report['status']='TWO_LIVE_RACES_120_PARITY_PASS'
    report['collector_guard_promoted']=False
    if report['status']=='TWO_LIVE_RACES_120_PARITY_PASS':
        WORKFLOW.write_text(wf.replace(MARKER,VERIFY_INSERT+MARKER),encoding='utf-8')
        report['collector_guard_promoted']=True
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':run()
