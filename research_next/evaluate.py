"""Fail-closed, common-race assessment of two frozen 120-ticket probability distributions."""
import argparse, csv, json, math
from datetime import datetime,timedelta,timezone
from itertools import permutations
TRIPLES=tuple("-".join(map(str,p)) for p in permutations(range(1,7),3))
JST=timezone(timedelta(hours=9))
def parse_prob(raw):
    p=json.loads(raw)
    if not isinstance(p,dict) or set(p)!=set(TRIPLES):raise ValueError("need exactly 120 distinct tickets")
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in p.values()):raise ValueError("invalid probability")
    if abs(sum(p.values())-1)>1e-8:raise ValueError("sum != 1")
    return p
def score(p,actual):
    rank=sorted(p,key=lambda t:(-p[t],t)).index(actual)
    return dict(top3=int(rank<3),top5=int(rank<5),top10=int(rank<10),logloss=-math.log(p[actual]))
def evaluate(rows,margin=12):
    if margin<0 or margin>60:raise ValueError("invalid margin")
    results=[];seen=set();train_dates=set();test_dates=set()
    for r in rows:
        code=r["race_code"]
        if not(code.isascii() and code.isdigit() and len(code)==12):raise ValueError("bad race code")
        if code in seen:raise ValueError("duplicate race")
        seen.add(code)
        deadline=datetime.fromisoformat(r["deadline_jst"])
        captured=datetime.fromisoformat(r["captured_at_jst"])
        if any(t.utcoffset()!=timedelta(hours=9) for t in (deadline,captured)):raise ValueError("requires JST")
        if deadline.strftime("%Y%m%d")!=code[:8] or captured>deadline-timedelta(minutes=margin):raise ValueError("late capture or date mismatch")
        sha=r["source_sha256"]
        if len(sha)!=64 or any(c not in "0123456789abcdef" for c in sha):raise ValueError("bad SHA256")
        split=r["split"]
        if split not in ("train","test"):raise ValueError("bad split")
        (train_dates if split=="train" else test_dates).add(code[:8])
        truth=r["outcome"]
        if truth not in TRIPLES:raise ValueError("bad outcome")
        a,b=parse_prob(r["baseline_probs"]),parse_prob(r["candidate_probs"])
        if split=="test":results.append((score(a,truth),score(b,truth)))
    if not train_dates or not test_dates or max(train_dates)>=min(test_dates):raise ValueError("train/test dates overlap or not chronological")
    if not results:raise ValueError("no test races")
    def aggregate(i):
        return {k:sum(pair[i][k] for pair in results)/(len(results) if k=="logloss" else 1) for k in ("top3","top5","top10","logloss")}
    baseline,candidate=aggregate(0),aggregate(1)
    return {"n":len(results),"baseline":baseline,"candidate":candidate,"top10_candidate_only":sum(a["top10"]==0 and b["top10"]==1 for a,b in results),"top10_baseline_only":sum(a["top10"]==1 and b["top10"]==0 for a,b in results),"decision":"RESEARCH_ONLY_NOT_DEPLOYABLE"}
if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("csv");cli.add_argument("--margin",type=int,default=12)
    x=cli.parse_args()
    with open(x.csv,encoding="utf-8-sig",newline="") as f:
        print(json.dumps(evaluate(csv.DictReader(f),x.margin),ensure_ascii=False,indent=2))
