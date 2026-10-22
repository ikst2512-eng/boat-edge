"""Aggregate only validated, on-disk probe manifests with intact captured bytes."""
import argparse,hashlib,json
from datetime import datetime,timedelta
from pathlib import Path
def report(root):
    output={"manifests":0,"eligible_12":0,"eligible_11":0,"eligible_10":0,"invalid":0}
    unique={12:set(),11:set(),10:set()}
    races={12:set(),11:set(),10:set()}
    for p in Path(root).glob("*/*.json"):
        try:
            m=json.loads(p.read_text(encoding="utf-8"))
            name=m["body_name"]
            if not isinstance(name,str) or Path(name).name!=name or not name.endswith(".body"):raise ValueError("unsafe body name")
            body=p.parent/name
            if body.is_symlink() or body.parent!=p.parent or not body.is_file():raise ValueError("invalid body")
            data=body.read_bytes()
            if len(data)!=m["bytes"] or hashlib.sha256(data).hexdigest()!=m["sha256"]:raise ValueError("hash mismatch")
            if m["target_race_validated"] is not True:raise ValueError("race unverified")
            deadline=datetime.fromisoformat(m["deadline_jst"])
            started=datetime.fromisoformat(m["started_jst"])
            completed=datetime.fromisoformat(m["completed_jst"])
            if any(t.utcoffset()!=timedelta(hours=9) for t in (deadline,started,completed)):
                raise ValueError("not JST")
            if started>completed or completed>deadline or m["race_code"][:8]!=deadline.strftime("%Y%m%d"):
                raise ValueError("invalid chronology")
            actual=[minute for minute in (12,11,10) if completed<=deadline-timedelta(minutes=minute)]
            if m["eligible_margins"]!=actual:raise ValueError("inconsistent cutoff labels")
            import csv,io,math
            date_code=m["race_code"]
            expected=f"https://boatracecsv.github.io/data/programs/race_cards/{date_code[:4]}/{date_code[4:6]}/{date_code[6:8]}.csv"
            if m["source_url"]!=expected:raise ValueError("unexpected data source")
            if p.parent.name!=m["race_code"] or p.stem+".body"!=name:
                raise ValueError("manifest identity mismatch")
            records=list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
            matches=[r for r in records if r.get("レースコード")==m["race_code"]]
            if len(matches)!=1:raise ValueError("race not in archived bytes")
            if "/race_cards/" in m["source_url"]:
                rates=[float(matches[0][f"艇{i}_全国勝率"]) for i in range(1,7)]
                if not all(math.isfinite(v) and 0<v<20 for v in rates):raise ValueError("bad national rates")
            elif "/title/" in m["source_url"]:
                if not matches[0].get("電話投票締切予定"):raise ValueError("missing deadline")
            else:raise ValueError("unsupported CSV type")
            for minute in actual:
                unique[minute].add((m["race_code"],m["source_url"]))
                races[minute].add(m["race_code"])
            output["manifests"]+=1
        except (ValueError,KeyError,TypeError,OSError,UnicodeError,json.JSONDecodeError):
            output["invalid"]+=1
    for minute in (12,11,10):
        output[f"eligible_{minute}"]=len(unique[minute])
        output[f"unique_races_{minute}"]=len(races[minute])
    return output
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root");a=p.parse_args()
    print(json.dumps(report(a.root),ensure_ascii=False,indent=2))
