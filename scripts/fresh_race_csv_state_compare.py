#!/usr/bin/env python3
"""Read-only per-race comparison of fresh CSV publication and persisted race-state audits.
Never imports results, changes state, or implies a retrospective formal freeze.
"""
import argparse
import csv
import hashlib
import io
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

JST = timezone(timedelta(hours=9))
ROLES = ("race_cards", "stt", "tkz", "sui", "original_exhibition")
KEY = re.compile(r"^20\d{6}-\d{2}-\d{2}$")
BASE = "https://boatracecsv.github.io"

def url_for(role, date):
    path = "programs/race_cards" if role == "race_cards" else "previews/" + role
    return f"{BASE}/data/{path}/{date[:4]}/{date[4:6]}/{date[6:8]}.csv"

def compare(key, opener=urlopen, now=None):
    if not KEY.fullmatch(key):
        raise ValueError("invalid race key")
    now = now or datetime.now(JST)
    state_path = Path("data/races") / (key + ".json")
    if not state_path.is_file():
        return {"race_key": key, "status": "STATE_FILE_MISSING"}
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("race_key") != key:
        raise ValueError("state race identity mismatch")
    code = key.replace("-", "")
    deadline_text = (state.get("meta") or {}).get("deadline")
    try:
        deadline = datetime.strptime(key[:8] + " " + str(deadline_text), "%Y%m%d %H:%M").replace(tzinfo=JST)
    except ValueError:
        deadline = None
    result = {"race_key": key, "observed_at_jst": now.isoformat(),
              "deadline_jst": deadline.isoformat() if deadline else None,
              "observed_before_deadline": now < deadline if deadline else None,
              "scope": "OBSERVATION_AT_RUN_TIME_NOT_HISTORICAL_CSV_PROOF",
              "formal_eligible": False, "sources": {}}
    for role in ROLES:
        req = Request(url_for(role, key[:8]), headers={"User-Agent": "BOAT-EDGE/PRE_RESULT audit"})
        item = {"url": req.full_url, "http_status": None, "csv_sha256": None,
                "total_rows": None, "matching_rows": None, "match_kind": None}
        try:
            item["fetch_started_at_jst"] = datetime.now(JST).isoformat()
            with opener(req, timeout=20) as response:
                raw = response.read()
                item["fetch_completed_at_jst"] = datetime.now(JST).isoformat()
                item["http_status"] = getattr(response, "status", 200)
            item["csv_sha256"] = hashlib.sha256(raw).hexdigest()
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            rows = list(reader)
            if not reader.fieldnames or "レースコード" not in reader.fieldnames:
                item["match_kind"] = "MISSING_RACE_CODE_HEADER"
            else:
                hits = [r for r in rows if str(r.get("レースコード") or "").strip() == code]
                item["matching_rows"] = len(hits)
                item["match_kind"] = ("NONE" if not hits else "ONE" if len(hits) == 1 else "DUPLICATE")
            item["total_rows"] = len(rows)
            item["parse_completed_at_jst"] = datetime.now(JST).isoformat()
        except HTTPError as e:
            item["http_status"] = e.code
            item["match_kind"] = "NOT_PUBLISHED" if e.code == 404 else "HTTP_ERROR"
        except (URLError, TimeoutError, UnicodeError, csv.Error, OSError) as e:
            item["match_kind"] = "FETCH_OR_PARSE_ERROR"
            item["error_type"] = type(e).__name__
        item["observed_before_deadline_at_fetch"] = (datetime.fromisoformat(item["fetch_completed_at_jst"]) < deadline if deadline and item.get("fetch_completed_at_jst") else None)
        old = (state.get("source_audit") or {}).get("race_card" if role == "race_cards" else role) or {}
        item["saved_status"] = old.get("status")
        item["saved_availability_reason"] = old.get("availability_reason")
        item["saved_sha256"] = old.get("sha256")
        item["saved_digest_source_type"] = "official_racelist_html" if role == "race_cards" else "preview_csv"
        item["sha_comparison_applicable"] = role != "race_cards"
        item["same_bytes_as_saved_audit"] = (item["csv_sha256"] == old.get("sha256") if role != "race_cards" and item["csv_sha256"] and old.get("sha256") else None)
        item["postdeadline_observation_not_formal_proof"] = not (now < deadline) if deadline else True
        item["saved_observed_at"] = old.get("observed_at") or old.get("fetched_at")
        item["live_row_present_saved_state_missing_predeadline"] = bool(
            role != "race_cards" and item["matching_rows"] == 1
            and item["observed_before_deadline_at_fetch"] is True
            and old.get("status") != "ok"
            and state.get("meta", {}).get("phase") == "PRE_RESULT"
            and state.get("meta", {}).get("results_seen") is False
        )
        item["diagnostic_only_no_backfill"] = True
        result["sources"][role] = item
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("race_keys", nargs="*", default=["20261026-21-01", "20261026-21-02"])
    p.add_argument("--output", default="fresh_race_csv_state_comparison.json")
    a = p.parse_args()
    out = {"schema": "BOAT_EDGE_RACE_CSV_STATE_READONLY_V1",
           "results_accessed": False, "formal_unlock_authorized": False,
           "races": [compare(key) for key in a.race_keys]}
    Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
