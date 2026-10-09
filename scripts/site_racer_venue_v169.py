#!/usr/bin/env python3
"""V169 display-only racer x venue: pinned PRE_RESULT history, 3m fully covered.
Never accesses 2026-10-08 formal target, its results, payouts, or combined API.
"""
from __future__ import annotations
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
import csv
import hashlib
import io
import json
import re
import sys
import time
import requests

PIN = "2d149e1ae838f6ed3426a7989be69e799ac2988f"
FROM = date(2026, 7, 8)
THRU = date(2026, 10, 7)
ROOT = "https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/" + PIN
DATA_SCHEMA = "boat-edge-v169-racer-venue-display-only-v1"
RESULT_SCHEMA = "data/results/realtime/{year}/{month}/{day}.csv"
CARDS_SCHEMA = "data/programs/race_cards/{year}/{month}/{day}.csv"


def parse_csv(data: bytes) -> list[dict[str, str]]:
    txt = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(txt))
    return list(reader)


def valid_number(v, lo=1, hi=6):
    try:
        n = int(str(v).strip())
        return n if lo <= n <= hi else None
    except (ValueError, TypeError):
        return None


def newstat():
    return {"starts": 0, "wins": 0, "top2": 0, "top3": 0,
            "courses": {str(c): {"starts": 0, "top3": 0} for c in range(1, 7)},
            "win_methods": {}}


def normal_method(raw):
    s = re.sub(r"\s+", "", str(raw or ""))
    return s if s in ("逃げ", "差し", "まくり", "まくり差し", "抜き", "恵まれ") else None


def aggregate_pairs(pairs):
    """Each element (YYYYMMDD, result CSV bytes, card CSV bytes)."""
    racers = defaultdict(lambda: {"all": newstat(), "venues": {}})
    audits = {"paired_days": 0, "result_races": 0, "joined_races": 0,
              "eligible_races": 0, "skipped_unpaired": 0, "skipped_invalid": 0}
    for ymd, results_bytes, cards_bytes in sorted(pairs):
        results = parse_csv(results_bytes)
        cards = {r.get("レースコード", ""): r for r in parse_csv(cards_bytes)}
        if not results or not cards:
            raise RuntimeError("empty result/card day " + ymd)
        audits["paired_days"] += 1
        for result in results:
            audits["result_races"] += 1
            code = str(result.get("レースコード", "")).strip()
            card = cards.get(code)
            if not card:
                audits["skipped_unpaired"] += 1
                continue
            audits["joined_races"] += 1
            venue = str(card.get("レース場コード") or "").zfill(2)
            result_venue = str(result.get("レース場") or "").zfill(2)
            reg_ids = [str(card.get(f"艇{i}_登録番号") or "").strip() for i in range(1,7)]
            place = [valid_number(result.get(f"{i}着_艇番")) for i in range(1,4)]
            course_to_lane = [valid_number(result.get(f"{i}コース_艇番")) for i in range(1,7)]
            good = (re.fullmatch(r"\d{12}",code) and code.startswith(ymd)
                    and re.fullmatch(r"\d{2}", venue) and venue != "00"
                    and result_venue == venue and len(set(reg_ids)) == 6
                    and all(re.fullmatch(r"\d{4}",p) for p in reg_ids)
                    and set(course_to_lane) == set(range(1, 7))
                    and len(set(place)) == 3 and all(p is not None for p in place))
            if not good:
                audits["skipped_invalid"] += 1
                continue
            audits["eligible_races"] += 1
            lane_to_course = {lane: c + 1 for c,lane in enumerate(course_to_lane)}
            method = normal_method(result.get("決まり手"))
            for lane, racer in enumerate(reg_ids, 1):
                ent = racers[racer]
                venue_stat = ent["venues"].setdefault(venue, newstat())
                for stat in (ent["all"], venue_stat):
                    stat["starts"] += 1
                    if lane == place[0]:
                        stat["wins"] += 1
                        if method: stat["win_methods"][method] = stat["win_methods"].get(method, 0)+1
                    if lane in place[:2]: stat["top2"] += 1
                    if lane in place: stat["top3"] += 1
                    course_stat = stat["courses"][str(lane_to_course[lane])]
                    course_stat["starts"] += 1
                    if lane in place: course_stat["top3"] += 1
    return dict(racers), audits


def leanstat(d):
    return {"starts": d["starts"], "wins": d["wins"], "top2": d["top2"], "top3": d["top3"],
            "courses": {key: val for key, val in d["courses"].items() if val["starts"]>0},
            "win_methods": d["win_methods"]}


def derive_racer(rec):
    return {"all": leanstat(rec["all"]),
            "venues": {v: leanstat(s) for v,s in rec["venues"].items()}}


def calculate_comparison(rec, venue):
    """For descriptive display only: expected venue top3 rate adjusted for course mix."""
    local = rec["venues"].get(venue)
    if not local or not local["starts"]: return None
    n=local["starts"]
    exp=0.0
    for course, row in local["courses"].items():
        overall=rec["all"]["courses"].get(course)
        if not overall or not overall["starts"]:
            return None
        exp += row["starts"] * overall["top3"] / overall["starts"]
    observed=local["top3"] / n
    return {"starts": n, "observed_top3_pct": round(observed * 100, 2),
            "course_adjusted_expected_pct": round(exp * 100 / n, 2),
            "course_adjusted_diff_pct_points": round(100 * (observed-exp/n),2),
            "eligible_label": n>=12 and (observed-exp/n)>=0.10}


def fetch_pair(d:date):
    # Source frozen at PIN; no formal October 8 result access is possible by construction.
    if d > THRU: raise ValueError("Post-cutoff result forbidden")
    vals={"year":d.strftime("%Y"), "month":d.strftime("%m"),"day":d.strftime("%d")}
    def get(path):
        url=ROOT+"/"+path.format(**vals)
        err=None
        for i in range(3):
            try:
                res=requests.get(url,timeout=(8,40),headers={"User-Agent":"BOAT-EDGE-V169-PINNED-D1-DISPLAY"})
                res.raise_for_status()
                if len(res.content)<50: raise ValueError("source too short")
                return res.content
            except Exception as e:
                err=e
                time.sleep(0.5*(i+1))
        raise RuntimeError(f"Required historical source unavailable {d} {path}: {err}")
    return d.strftime("%Y%m%d"), get(RESULT_SCHEMA),get(CARDS_SCHEMA)


def get_history():
    days=[]
    day=FROM
    while day<=THRU:
        days.append(day)
        day+=timedelta(days=1)
    pairs=[]
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures={executor.submit(fetch_pair,d):d for d in days}
        for future in as_completed(futures):
            pairs.append(future.result())
    if len(pairs)!=92 or len({x[0] for x in pairs})!=92:
        raise RuntimeError("Historical coverage 92/92 required")
    return pairs


def load_today_racers(repo:Path):
    path=repo/"data/today.json"
    obj=json.loads(path.read_text(encoding="utf-8"))
    day=str(obj.get("date","")).replace("-","")
    if not re.fullmatch(r"\d{8}", day): raise RuntimeError("Bad today.json date")
    ids=set()
    missing=0
    for venue in obj.get("venues",[]):
        for race in venue.get("races",[]):
            f=race.get("file")
            if not re.fullmatch(r"data/races/\d{8}-\d{2}-\d{2}\.json",str(f or "")) or not f.startswith("data/races/"+day):
                raise RuntimeError("Invalid race file path")
            p=repo/f
            if not p.is_file():
                missing+=1;continue
            row=json.loads(p.read_text(encoding="utf-8"))
            if row.get("race_key")!=race.get("race_key"): raise RuntimeError("Race key mismatch")
            for racer in row.get("racers",[]):
                reg=str(racer.get("registration_no","")).strip()
                if re.fullmatch(r"\d{4}",reg):ids.add(reg)
    if missing:raise RuntimeError(f"Missing current race cards {missing}")
    return day,ids


def run(repo:Path):
    outdir=repo/"data/site_racer_venue_v169"
    outdir.mkdir(parents=True,exist_ok=True)
    master=outdir/"master_20261007.json"
    if master.exists():
        source=json.loads(master.read_text(encoding="utf-8"))
        if source.get("schema_version")!=DATA_SCHEMA or source.get("source_sha")!=PIN or source.get("as_of_d1")!="2026-10-07" or source.get("coverage",{}).get("paired_days")!=92:
            raise RuntimeError("Existing master provenance mismatch; never silently overwrite")
        racers=source["racers"]
        print("V169 MASTER_REUSE 92/92 verified-source-manifest")
    else:
        pairs=get_history()
        racers, audits=aggregate_pairs(pairs)
        if audits["paired_days"]!=92 or audits["eligible_races"]<1000:
            raise RuntimeError("Insufficient historical source or eligible races")
        source={"schema_version":DATA_SCHEMA,"source_sha":PIN,"as_of_d1":"2026-10-07",
                "source_window":{"start":"2026-07-08","end":"2026-10-07","complete":True},
                "coverage":audits,"formal_20261008_results_accessed":False,
                "prediction_weights_changed":False,"research_only":True,
                "racers":{r:derive_racer(row) for r,row in racers.items()}}
        master.write_text(json.dumps(source,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
        racers=source["racers"]
    day,active_ids=load_today_racers(repo)
    export={r:racers[r] for r in sorted(active_ids) if r in racers}
    if not active_ids or not export:raise RuntimeError("No eligible active racers")
    payload={"schema_version":DATA_SCHEMA,"status":"DISPLAY_ONLY_NOT_PREDICTION_CONNECTED",
             "site_day":day,"as_of_d1":"2026-10-07","window":{"start":"2026-07-08","end":"2026-10-07","days":92,"complete":True},
             "source_sha":PIN,"racer_count":len(export),"total_active_racers":len(active_ids),
             "formal_20261008_results_accessed":False,"prediction_weights_changed":False,
             "racers":export}
    (outdir/(day+".json")).write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({"V169":"DAY_DISPLAY_BUILT","day":day,"active":len(active_ids),"matched":len(export),"coverage":source["coverage"],"days":92,"source_cutoff":"2026-10-07","model_changes":False},ensure_ascii=False))


if __name__=="__main__":
    base=Path(sys.argv[1]) if len(sys.argv)>1 else Path(".")
    run(base)
