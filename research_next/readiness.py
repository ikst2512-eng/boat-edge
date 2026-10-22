"""Report readiness of real frozen intake records; never invent race values."""
import argparse,json
from collections import Counter
from pathlib import Path
REQUIRED=("race_code","source_sha256","captured_at_jst","deadline_jst","boats")
def summarize(paths):
    seen=set();totals=Counter()
    for path in paths:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
        if any(k not in data for k in REQUIRED):raise ValueError(f"incomplete record {path}")
        if data["race_code"] in seen:raise ValueError("duplicate race")
        seen.add(data["race_code"])
        boats=data["boats"]
        if not isinstance(boats,list) or len(boats)!=6:raise ValueError("invalid boat count")
        totals["races"]+=1
        if len({b.get("actual_entry") for b in boats})==6:totals["actual_entry_complete"]+=1
        if data.get("exhibition_complete") and all(all(f in b for f in ("exhibition_st","lap_time","turn_time","straight_time")) for b in boats):
            totals["exhibition_complete"]+=1
        else:totals["exhibition_missing"]+=1
    return dict(totals)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("paths",nargs="+");a=p.parse_args()
    print(json.dumps(summarize(a.paths),ensure_ascii=False,indent=2))
