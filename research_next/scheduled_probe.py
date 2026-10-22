"""Scheduled probe runner: discover today's races from title CSV, never results."""
import csv,io,json,sys,os,hashlib
from pathlib import Path
from datetime import datetime,timedelta,timezone
from urllib.request import Request,urlopen
from probe_availability import run_probe,JST
BASE="https://boatracecsv.github.io/data/programs/"
def run(now=None,root="research_next/probes",opener=urlopen,probe=None):
    if probe is None:probe=run_probe
    now=now or datetime.now(JST)
    if now.utcoffset()!=timedelta(hours=9):raise ValueError("JST required")
    day=now.strftime("%Y%m%d")
    path=f"{day[:4]}/{day[4:6]}/{day[6:]}.csv"
    url=BASE+"title/"+path
    with opener(Request(url,headers={"User-Agent":"BOAT-EDGE-RESEARCH/1.0","Cache-Control":"no-cache"}),timeout=12) as r:
        if r.status!=200 or r.geturl()!=url:raise ValueError("invalid title response")
        body=r.read(2_000_001)
    if len(body)>2_000_000:raise ValueError("title too large")
    # Preserve the exact title bytes used to choose deadlines for this run.
    # The title's observed capture time is distinct from its publisher's release time.
    captured_at=datetime.now(JST)
    evidence_root=Path(root)/"_source_title"
    evidence_root.mkdir(parents=True,exist_ok=True)
    title_sha=hashlib.sha256(body).hexdigest()
    evidence_name=captured_at.strftime("%Y%m%dT%H%M%S%f")+"_"+title_sha
    title_file=evidence_root/(evidence_name+".body")
    with title_file.open("xb") as out:
        out.write(body)
        out.flush()
        os.fsync(out.fileno())
    (evidence_root/(evidence_name+".json")).write_text(
        json.dumps({"source_url":url,"captured_jst":captured_at.isoformat(),
                    "sha256":title_sha,"bytes":len(body),
                    "source_publication_time_proven":False},sort_keys=True),encoding="utf-8")
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
    totals={"discovered":len(races),"due":0,"captured":0,"failed":0,"failures":[],"linked_duplicate_bodies":0}
    identical_bodies={}
    due=[]
    for x in races:
        code=x.get("レースコード","")
        if not (len(code)==12 and code.isascii() and code.isdigit() and code.startswith(day)):
            continue
        try:
            deadline_text=x["電話投票締切予定"]
            if len(deadline_text)!=5 or deadline_text[2]!=":":
                continue
            deadline=datetime.strptime(day+deadline_text,"%Y%m%d%H:%M").replace(tzinfo=JST)
        except (ValueError,KeyError,TypeError):
            continue
        remaining=(deadline-now).total_seconds()/60
        if 10<=remaining<=180:
            due.append((code,deadline))
    totals["due"]=len(due)
    for code,deadline in due:
        try:
            cardurl=BASE+"race_cards/"+path
            # Fetch once per run, retain separate immutable race-specific evidence.
            if probe is run_probe:
                meta=probe(code,deadline.isoformat(),cardurl,root,opener=cached_opener)
                # Every race keeps its own timestamped manifest, but identical daily
                # CSV bytes share one inode on runners supporting hardlinks.
                body_path=Path(root)/code/meta["body_name"]
                first=identical_bodies.get(meta["sha256"])
                if first is None:
                    identical_bodies[meta["sha256"]]=body_path
                elif first.is_file() and body_path.is_file():
                    link=body_path.with_name(body_path.name+".linktmp")
                    try:
                        os.link(first,link)
                        os.replace(link,body_path)
                        totals["linked_duplicate_bodies"]+=1
                    except OSError:
                        link.unlink(missing_ok=True)
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
