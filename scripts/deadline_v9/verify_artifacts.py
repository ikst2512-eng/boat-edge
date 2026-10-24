"""Fail-closed V10 capture artifact verifier; does not certify race deadlines."""
import argparse, hashlib, json, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs
JST=timezone(timedelta(hours=9))
def verify(root, report_path):
    root=Path(root).resolve()
    report=json.loads(Path(report_path).read_text(encoding='utf8'))
    day=report.get('date_jst','')
    errors=[]; verified=[]
    if not re.fullmatch(r'\d{8}',day): errors.append('INVALID_DATE')
    seen=set()
    for i,item in enumerate(report.get('captures',[])):
        ident=f'capture[{i}]'
        try:
            venue=item['venue_code'];rno=item['race_number_requested'];sha=item['sha256']
            if not re.fullmatch(r'\d{2}',venue) or not 1<=int(venue)<=24 or type(rno)!=int or not 1<=rno<=12:raise ValueError('invalid venue/race')
            if not re.fullmatch(r'[a-f0-9]{64}',sha):raise ValueError('invalid sha')
            key=(venue,rno)
            if key in seen:raise ValueError('duplicate race')
            seen.add(key)
            expected=f'https://www.boatrace.jp/owpc/pc/race/racelist?hd={day}&jcd={venue}&rno={rno}'
            if item['source_url']!=expected or item['final_url']!=expected:raise ValueError('URL/race mismatch')
            start=datetime.fromisoformat(item['capture_started_at_jst']);end=datetime.fromisoformat(item['capture_finished_at_jst'])
            if start.utcoffset()!=timedelta(hours=9) or end.utcoffset()!=timedelta(hours=9) or end<start or start.strftime('%Y%m%d')!=day:raise ValueError('capture time mismatch')
            if item.get('formal_eligible') is not False or item.get('race_deadlines_verified') is not False:raise ValueError('unsafe formal claim')
            path=root/'snapshots'/day/venue/(sha+'.html')
            if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):raise ValueError('missing/unsafe HTML')
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=sha or len(raw)!=item['bytes'] or not raw:raise ValueError('HTML integrity mismatch')
            verified.append({'venue':venue,'rno':rno,'sha256':sha})
        except (KeyError,ValueError,TypeError,OSError) as e:
            errors.append(f'{ident}: {e}')
    for failure in report.get('errors',[]):
        if not isinstance(failure,dict) or 'venue' not in failure or 'race_number_requested' not in failure:errors.append('INVALID_ERROR_RECORD')
    if not isinstance(report.get('captures'),list) or not isinstance(report.get('errors'),list):errors.append('INVALID_REPORT')
    if report.get('formal_eligible') is not False or report.get('results_seen') is not False:errors.append('UNSAFE_REPORT_FLAGS')
    return {'status':'CAPTURE_INTEGRITY_PASS_RESEARCH_ONLY' if not errors and verified and not report['errors'] else 'LOCKED',
            'verified_count':len(verified),'capture_errors':len(report.get('errors',[])),
            'integrity_errors':errors,'formal_eligible':False,'results_seen':False,'scoring':'NOT_RUN','unlock':'LOCKED'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--report',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();result=verify(a.root,a.report);Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    if result['status']=='LOCKED':raise SystemExit(2)
