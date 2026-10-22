"""Scheduled probe runner: discover today's races from title CSV, never results."""
import csv,io,json,sys
from datetime import datetime,timedelta,timezone
from urllib.request import Request,urlopen
from probe_availability import run_probe,JST
BASE="https://boatracecsv.github.io/data/programs/"
def run(now=None,root="research_next/probes",opener=urlopen,probe=run_probe):
    now=now or datetime.now(JST)
    if now.utcoffset()!=timedelta(hours=9):raise ValueError("JST required")
    day=now.strftime("%Y%m%d")
    path=f"{day[:4]}/{day[4:6]}/{day[6:]}.csv"
    url=BASE+"title/"+path
    with opener(Request(url,headers={"User-Agent":"BOAT-EDGE-RESEARCH/1.0","Cache-Control":"no-cache"}),timeout=12) as r:
        if r.status!=200 or r.geturl()!=url:raise ValueError("invalid title response")
        body=r.read(2_000_001)
    if len(body)>2_000_000:raise ValueError("title too large")
    races=list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
    # Fetching the same card CSV for every race is wasteful. Cache exact bytes
    # for this runner invocation, while each probe still timestamps verification.
    card_cache={}
    class CachedResponse:
        def __init__(self,url,body):self.status=200;self._url=url;self._body=body
        def read(self,n):return self._body[:n]
        def geturl(self):return self._url
        def __enter__(self):return self
        def __exit__(self,*args):return False
    def cached_opener(req,timeout=12):
        target=req.full_url
        if target not in card_cache:
            with opener(req,timeout=timeout) as response:
                if response.status!=200 or response.geturl()!=target:raise ValueError("bad card response")
                content=response.read(2_000_001)
                if len(content)>2_000_000:raise ValueError("card too large")
                card_cache[target]=content
        return CachedResponse(target,card_cache[target])
    totals={"discovered":len(races),"due":0,"captured":0,"failed":0,"failures":[]}
    for x in races:
        code=x.get("レースコード","")
        if not (len(code)==12 and code.isascii() and code.isdigit() and code.startswith(day)):continue
        try:
            deadline_text=x["電話投票締切予定"]
            if not isinstance(deadline_text,str) or len(deadline_text)!=5 or deadline_text[2]!=":":
                raise ValueError("invalid deadline format")
            deadline=datetime.strptime(day+deadline_text,"%Y%m%d%H:%M").replace(tzinfo=JST)
        except (ValueError,KeyError,TypeError):continue
        # Start probing up to three hours early. Avoid relying on a late 60-minute window.
        # Repeated scheduled runs can track availability as the cutoff approaches.
        remaining=(deadline-now).total_seconds()/60
        if not 10<=remaining<=180:continue
        totals["due"]+=1
        try:
            cardurl=BASE+"race_cards/"+path
            if probe is run_probe:
                probe(code,deadline.isoformat(),cardurl,root,opener=cached_opener)
            else:
                probe(code,deadline.isoformat(),cardurl,root)
            totals["captured"]+=1
        except (OSError,ValueError,KeyError,TypeError) as exc:
            totals["failed"]+=1
            totals["failures"].append({"race_code":code,"reason":type(exc).__name__})
    return totals
if __name__=="__main__":
    from pathlib import Path
    try:
        outcome=run()
        outcome["status"]="ok"
    except (OSError,ValueError,TypeError,UnicodeError) as e:
        outcome={"status":"collector_failed","error_type":type(e).__name__}
    dest=Path("research_next/probe_run_status.json")
    dest.write_text(json.dumps(outcome,ensure_ascii=False,sort_keys=True),encoding="utf-8")
    print(json.dumps(outcome,ensure_ascii=False))
    if outcome["status"]!="ok" or outcome.get("failed",0):
        sys.exit(1)
