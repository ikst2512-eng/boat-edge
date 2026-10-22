"""Independent pre-race exhibition/actual-entry intake. No predictions or results."""
import argparse, csv, hashlib, json, re
from datetime import datetime,timedelta
from pathlib import Path
JST=timedelta(hours=9)
ST_FIELDS=("exhibition_st","lap_time","turn_time","straight_time")
def ingest(raw, source_bytes, captured_at_jst, deadline_jst, margin=12):
    if not isinstance(raw,dict):raise ValueError("source object required")
    code=raw.get("race_code")
    if not isinstance(code,str) or not re.fullmatch(r"20[0-9]{10}",code):raise ValueError("invalid race code")
    if type(margin) is not int or not 0<=margin<=60:raise ValueError("invalid margin")
    captured=datetime.fromisoformat(captured_at_jst);deadline=datetime.fromisoformat(deadline_jst)
    if captured.utcoffset()!=JST or deadline.utcoffset()!=JST:raise ValueError("JST timestamp required")
    if captured>deadline-timedelta(minutes=margin):raise ValueError("capture after cutoff")
    if deadline.strftime("%Y%m%d")!=code[:8]:raise ValueError("race date does not match deadline")
    boats=raw.get("boats")
    if not isinstance(boats,list) or len(boats)!=6:raise ValueError("exactly six boats required")
    normalized={};entries=[]
    for item in boats:
        if not isinstance(item,dict) or type(item.get("boat")) is not int or item["boat"] not in range(1,7) or item["boat"] in normalized:
            raise ValueError("boat identity is missing/duplicated")
        boat=item["boat"]
        entry=item.get("actual_entry")
        if type(entry) is not int or entry not in range(1,7):raise ValueError("actual entry missing/invalid")
        entries.append(entry)
        current={"boat":boat,"actual_entry":entry}
        for name in ST_FIELDS:
            value=item.get(name)
            if value is None:continue
            if type(value) not in (float,int) or not __import__("math").isfinite(value):
                raise ValueError("invalid measured value")
            if name=="exhibition_st" and not -1.0<=value<=2.0:raise ValueError("out-of-range exhibition ST")
            if name!="exhibition_st" and not 0<value<300:raise ValueError("out-of-range timing")
            current[name]=value
        normalized[boat]=current
    if sorted(entries)!=list(range(1,7)):raise ValueError("entry is not a permutation")
    if not isinstance(source_bytes,bytes) or not source_bytes:raise ValueError("raw source required")
    return {"schema":"pre_race_features_v1","race_code":code,
            "source_sha256":hashlib.sha256(source_bytes).hexdigest(),
            "captured_at_jst":captured_at_jst,"deadline_jst":deadline_jst,
            "cutoff_minutes":margin,"boats":[normalized[i] for i in range(1,7)],
            "exhibition_complete":all(all(k in x for k in ST_FIELDS) for x in normalized.values())}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("source",type=Path,help="UTF-8 JSON original payload")
    parser.add_argument("--captured-at-jst",required=True)
    parser.add_argument("--deadline-jst",required=True)
    parser.add_argument("--margin",type=int,default=12)
    parser.add_argument("--output",type=Path,required=True)
    x=parser.parse_args()
    original=x.source.read_bytes()
    record=ingest(json.loads(original),original,x.captured_at_jst,x.deadline_jst,x.margin)
    x.output.parent.mkdir(parents=True,exist_ok=True)
    with x.output.open("x",encoding="utf-8") as out:
        json.dump(record,out,ensure_ascii=False,indent=2,sort_keys=True)
    print(json.dumps({"race_code":record["race_code"],"exhibition_complete":record["exhibition_complete"]}))
