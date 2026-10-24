"""Research-only, same-day immutable official HTML capture. Not formal race-deadline proof."""
import argparse, hashlib, json, os, re, tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError('Redirect refused; capture canonical source URL directly')
JST=timezone(timedelta(hours=9))

def capture(url, directory, timeout=15, opener=None):
    u=urlparse(url)
    if u.scheme!='https' or u.hostname not in ('www.boatrace.jp','boatrace.jp'):
        raise ValueError('Official BOAT RACE HTTPS only')
    qs=parse_qs(u.query)
    day=qs.get('hd',[''])[0]
    venue=qs.get('jcd',[''])[0]
    if not re.fullmatch(r'\d{8}',day) or not re.fullmatch(r'\d{2}',venue) or not 1<=int(venue)<=24:
        raise ValueError('Explicit date and venue required')
    if day!=datetime.now(JST).strftime('%Y%m%d'):
        raise ValueError('No retrospective evidence capture')
    request=Request(url,headers={'User-Agent':'BoatraceResearchSnapshot/1.0','Accept':'text/html'})
    started=datetime.now(JST)
    if opener is None:
        opener=build_opener(NoRedirect()).open
    with opener(request,timeout=timeout) as response:
        final=response.geturl()
        f=urlparse(final)
        if f.scheme!='https' or f.hostname not in ('www.boatrace.jp','boatrace.jp'):
            raise ValueError('Redirect outside official origin')
        data=response.read(3_000_001)
        mime=response.headers.get('Content-Type','')
        status=response.status
    finished=datetime.now(JST)
    if final!=url:
        raise ValueError('Unexpected final URL')
    if status!=200 or not data or len(data)>3_000_000 or 'html' not in mime.lower():
        raise ValueError('Invalid official HTML response')
    sha=hashlib.sha256(data).hexdigest()
    folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
    dest=folder/(sha+'.html')
    if dest.exists():
        if dest.read_bytes()!=data: raise RuntimeError('SHA collision')
    else:
        with tempfile.NamedTemporaryFile(dir=folder,delete=False) as tmp:
            tmp.write(data)
            name=tmp.name
        try:os.link(name,dest)
        except FileExistsError:
            if dest.read_bytes()!=data:raise RuntimeError('Concurrent collision')
        finally:os.unlink(name)
    rec={'source_url':url,'final_url':final,'date_jst':day,'venue_code':venue,
         'capture_started_at_jst':started.isoformat(),'capture_finished_at_jst':finished.isoformat(),
         'sha256':sha,'bytes':len(data),'http_status':status,'content_type':mime,
         'race_deadlines_verified':False,'independent_timestamp_attested':False,
         'formal_eligible':False}
    with (folder/'ledger.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(rec,ensure_ascii=False,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
    return rec

def run(day, venues, outdir, capturer=capture):
    if day!=datetime.now(JST).strftime('%Y%m%d'):raise ValueError('Must capture on current JST date')
    results={'date_jst':day,'formal_eligible':False,'results_seen':False,'captures':[],'errors':[]}
    for venue in dict.fromkeys(venues):
        if not re.fullmatch(r'\d{2}',venue) or not 1<=int(venue)<=24:raise ValueError('Invalid venue')
        url=f'https://www.boatrace.jp/owpc/pc/race/racelist?hd={day}&jcd={venue}&rno=1'
        try: results['captures'].append(capturer(url,str(Path(outdir)/day/venue)))
        except Exception as e: results['errors'].append({'venue':venue,'error':str(e)[:300]})
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--date',required=True);p.add_argument('--venues',nargs='+',required=True)
    p.add_argument('--outdir',required=True);p.add_argument('--report',required=True)
    a=p.parse_args()
    report=run(a.date,a.venues,a.outdir)
    file=Path(a.report);file.parent.mkdir(parents=True,exist_ok=True)
    with file.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({'captured':len(report['captures']),'failed':len(report['errors']),'formal_eligible':False}))
    if report['errors']:raise SystemExit(2)
