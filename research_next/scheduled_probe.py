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
    totals={"discovered":len(races),"due":0,"captured":0,"failed":0,"failures":[]}
    for x in races:
        code=x.get("レースコード","")
        if not (len(code)==12 and code.isascii() and code.isdigit() and code.startswith(day)):continue
        try:
            deadline=datetime.strptime(day+x["電話投票締切予定"],"%Y%m%d%H:%M").replace(tzinfo=JST)
        except (ValueError,KeyError,TypeError):continue
        # Capture early, from 60m before deadline until strictly 10m before.
        remaining=(deadline-now).total_seconds()/60
        if not 10<=remaining<=60:continue
        totals["due"]+=1
        try:
            cardurl=BASE+"race_cards/"+path
            probe(code,deadline.isoformat(),cardurl,root)
            totals["captured"]+=1
        except (OSError,ValueError,KeyError,TypeError) as exc:
            totals["failed"]+=1
            totals["failures"].append({"race_code":code,"reason":type(exc).__name__})
    return totals
if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False))
