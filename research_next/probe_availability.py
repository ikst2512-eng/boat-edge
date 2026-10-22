"""Measure observed availability at 12/11/10-minute cutoffs from real HTTP captures.

Fetches must be made at the capture timestamp; this code never backdates availability.
This probe stores exact response bytes and metadata; it does not parse results or score.
"""
import argparse, csv, io, hashlib, json, os, math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
JST=timezone(timedelta(hours=9))
MARGINS=(12,11,10)
def run_probe(race_code, deadline_jst, source_url, root, clock=None, opener=urlopen):
    clock=clock or (lambda:datetime.now(JST))
    deadline=datetime.fromisoformat(deadline_jst)
    if deadline.utcoffset()!=timedelta(hours=9):raise ValueError("JST deadline required")
    if not(isinstance(race_code,str) and len(race_code)==12 and race_code.isascii() and race_code.isdigit() and race_code[:8]==deadline.strftime("%Y%m%d")):raise ValueError("bad race")
    date_path=f"{race_code[:4]}/{race_code[4:6]}/{race_code[6:8]}.csv"
    permitted={f"https://boatracecsv.github.io/data/programs/race_cards/{date_path}"}
    if source_url not in permitted:raise ValueError("unsupported source or wrong race date")
    before=clock()
    if before.utcoffset()!=timedelta(hours=9):raise ValueError("JST clock required")
    if before>deadline:raise ValueError("race deadline passed")
    with opener(Request(source_url,headers={"User-Agent":"BOAT-EDGE-RESEARCH/1.0","Cache-Control":"no-cache"}),timeout=12) as response:
        if response.status!=200:raise ValueError("HTTP not OK")
        content=response.read(2_000_001)
        if len(content)>2_000_000:raise ValueError("oversize")
        final=response.geturl()
        if final!=source_url:raise ValueError("redirect not allowed")
    after=clock()
    if after<before or after.utcoffset()!=timedelta(hours=9):raise ValueError("clock inconsistent")
    # HTTP success alone does not prove usable race data.
    try:
        rows=list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
        hits=[row for row in rows if row.get("レースコード")==race_code]
        if len(hits)!=1:raise ValueError("target race absent or duplicate")
        if "/race_cards/" in source_url:
            values=[float(hits[0][f"艇{i}_全国勝率"]) for i in range(1,7)]
            if not all(math.isfinite(v) and 0<v<20 for v in values):raise ValueError("invalid rates")
        else:raise ValueError("unsupported source family")
    except (UnicodeError,KeyError,TypeError) as exc:
        raise ValueError("bad source content") from exc
    digest=hashlib.sha256(content).hexdigest()
    # Body is saved first using exclusive create. A duplicate probe is not overwritten.
    dest=Path(root)/race_code
    dest.mkdir(parents=True,exist_ok=True)
    marker=after.strftime("%Y%m%dT%H%M%S%f")
    raw=dest/(marker+"_"+digest+".body")
    with raw.open("xb") as f:
        f.write(content);f.flush();os.fsync(f.fileno())
    meta={"race_code":race_code,"source_url":source_url,"deadline_jst":deadline_jst,
          "started_jst":before.isoformat(),"completed_jst":after.isoformat(),
          "sha256":digest,"body_name":raw.name,"bytes":len(content),"target_race_validated":True,
          "eligible_margins":[m for m in MARGINS if after<=deadline-timedelta(minutes=m)],
          "source_publication_time_proven":False}
    with (dest/(raw.stem+".json")).open("x",encoding="utf-8") as f:
        json.dump(meta,f,ensure_ascii=False,sort_keys=True)
    return meta
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--race-code",required=True)
    p.add_argument("--deadline-jst",required=True)
    p.add_argument("--source-url",required=True)
    p.add_argument("--output",default="research_next/probes")
    x=p.parse_args()
    print(json.dumps(run_probe(x.race_code,x.deadline_jst,x.source_url,x.output),ensure_ascii=False,indent=2))
