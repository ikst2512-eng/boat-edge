#!/usr/bin/env python3
"""V366: isolated, strictly predeadline source-only official refresh proof.

Opt-in direct call uses the V365 read-only selection gate. Fetches only the
same-race official racelist and beforeinfo HTML, checks six racer identities,
six official exhibition times, six labelled start-course/ST rows and immutable
race/deadline parity, then writes an *independent research-only* bundle once.

Does NOT edit data/races, data/raw, SITE predictions, V230/V235/V336, formal
Fresh, model ranks, or any site publication. No odds/results/combined APIs.
Even a PASS is LOCAL_HTTP_RESPONSE_AND_SHA_ONLY, not independently
authenticated server time, official final entry, source parity vs BOATERS
and 競艇日和, or evidence of better prediction accuracy.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import tempfile

from boat_edge_v230_fast_lane import parse_regs, parse_before, beforeinfo_coverage
from boat_edge_v315_source_capture import check_target, real_fetch, MAX_HTML_BYTES
from boat_edge_v318_shadow_freeze import JST, canonical
from boat_edge_v362_official_start_course_proof import parse_proven_course_rows
from boat_edge_v365_source_only_selection_contract import select_source_refresh

MODEL = "BOAT_EDGE_V366_ISOLATED_OFFICIAL_SOURCE_ONLY_PROOF"
ENDPOINTS = ("racelist", "beforeinfo")
OUTPUT_ROOT = Path("data/research_source_only_v366")


def _clock(clock):
    now = clock() if clock is not None else datetime.now(JST)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("V366_AWARE_JST_CLOCK_REQUIRED")
    return now.astimezone(JST)


def _source_url(key, endpoint):
    if endpoint not in ENDPOINTS:
        raise ValueError("V366_NON_PRE_RESULT_ENDPOINT")
    day, venue, race = key.split("-")
    url = ("https://www.boatrace.jp/owpc/pc/race/" + endpoint
           + "?hd=" + day + "&jcd=" + venue + "&rno=" + str(int(race)))
    check_target("official", url, key)
    return url


def _trusted_raw(raw, content_type, final_url, requested_url):
    if (final_url != requested_url or content_type != "text/html"
            or type(raw) is not bytes or not 64 <= len(raw) <= MAX_HTML_BYTES):
        raise ValueError("V366_UNVERIFIED_HTML_RESPONSE")
    return raw


def _safe_parent(root, dest):
    root = root.resolve()
    if not dest.is_relative_to(root):
        raise ValueError("V366_OUTPUT_PATH_NOT_WITHIN_ROOT")
    p = dest
    while p != root:
        if p.is_symlink():
            raise ValueError("V366_OUTPUT_SYMLINK_FORBIDDEN")
        p = p.parent
    return root


def _race_snapshot(root, key):
    path = root / "data/races" / (key + ".json")
    _safe_parent(root, path)
    raw = path.read_bytes()
    obj = json.loads(raw)
    if not isinstance(obj, dict) or obj.get("race_key") != key:
        raise ValueError("V366_RACE_INPUT_IDENTITY_MISMATCH")
    return raw, obj


def _validate_registration_parity(race, racelist):
    expected = [str(r.get("registration_no")) for r in race.get("racers", [])]
    observed = parse_regs(racelist.decode("utf-8", errors="replace"))
    if (len(expected) != 6 or len(set(expected)) != 6
            or any(not x.isdecimal() or len(x) != 4 for x in expected)
            or len(observed) != 6 or set(expected) != set(observed)):
        raise ValueError("V366_SIX_REGISTERED_RACERS_NOT_PROVEN")
    return sorted(observed)


def _validate_official_beforeinfo(race, beforeinfo):
    # V230's parsing is used solely for evidence; the first site prediction is
    # not rebuilt, replaced, or re-ranked by this source-only proof.
    parsed = parse_before(beforeinfo.decode("utf-8", errors="replace"))
    coverage = beforeinfo_coverage(parsed)
    if not coverage.get("six_boat_complete"):
        raise ValueError("V366_OFFICIAL_EXHIBITION_SIX_BOAT_INCOMPLETE")
    doc = copy.deepcopy(race)
    doc["beforeinfo"] = parsed
    proof = parse_proven_course_rows(beforeinfo, doc)
    if not proof.get("active_official_beforeinfo_race_and_deadline_matched"):
        raise ValueError("V366_OFFICIAL_RACE_OR_DEADLINE_UNPROVEN")
    return coverage, proof


def capture_source_only(root, key, *, fetcher=real_fetch, clock=None):
    """Write-once proof; no shared state writes, no first-prediction access."""
    root = Path(root).resolve()
    now = _clock(clock)
    # The independent V365 selector rejects stale/outcome-bearing index/race
    # records and validates the exact indexed R, date, venue and deadline.
    selected = select_source_refresh(root, now)
    if key not in [x["race_key"] for x in selected["candidates"]]:
        raise ValueError("V366_SOURCE_REFRESH_NOT_CURRENTLY_ELIGIBLE")
    original, race = _race_snapshot(root, key)
    record = {
        "model_id": MODEL,
        "race_key": key,
        "input_race_sha256": hashlib.sha256(original).hexdigest(),
        "candidate_selected_at_jst": now.isoformat(),
    }
    capture = {}
    for endpoint in ENDPOINTS:
        start = _clock(clock)
        # Live opening/selection gates must hold before each network request.
        if key not in [x["race_key"]
                       for x in select_source_refresh(root, start)["candidates"]]:
            raise ValueError("V366_WINDOW_CLOSED_BEFORE_FETCH")
        url = _source_url(key, endpoint)
        raw, ctype, returned_url = fetcher(url)
        received = _clock(clock)
        if (received.date() != now.date() or
                (received - now).total_seconds() < 0 or
                key not in [x["race_key"]
                            for x in select_source_refresh(root, received)["candidates"]]):
            raise ValueError("V366_FETCH_ENDED_OUTSIDE_LIVE_WINDOW")
        capture[endpoint] = {
            "url": url,
            "raw": _trusted_raw(raw, ctype, returned_url, url),
            "received_at_jst": received.isoformat(),
        }
    registrations = _validate_registration_parity(race, capture["racelist"]["raw"])
    coverage, proof = _validate_official_beforeinfo(race, capture["beforeinfo"]["raw"])
    # Re-read and byte-compare sources before writing. An external collector
    # update during this capture cannot silently change what was validated.
    if (root / "data/races" / (key + ".json")).read_bytes() != original:
        raise ValueError("V366_RACE_CHANGED_DURING_SOURCE_FETCH")
    final = _clock(clock)
    if (final - now).total_seconds() < 0 or key not in [
            x["race_key"] for x in select_source_refresh(root, final)["candidates"]]:
        raise ValueError("V366_WINDOW_CLOSED_BEFORE_SOURCE_WRITE")
    out = root / OUTPUT_ROOT / key[:8] / key
    _safe_parent(root, out)
    if out.exists() or out.is_symlink():
        raise ValueError("V366_IMMUTABLE_SOURCE_PROOF_ALREADY_EXISTS")
    manifest = {
        **record,
        "source_proof_at_jst": final.isoformat(),
        "evidence_level": "LOCAL_HTTP_RESPONSE_SHA_ONLY",
        "registered_racers_matched": registrations,
        "official_exhibition_coverage": coverage,
        "official_start_course_proof": proof,
        "sources": {
            name: {"url": data["url"], "sha256": hashlib.sha256(data["raw"]).hexdigest(),
                   "bytes": len(data["raw"]), "received_at_jst": data["received_at_jst"],
                   "relative_path": (OUTPUT_ROOT / key[:8] / key / (name + ".html")).as_posix()}
            for name, data in capture.items()
        },
        "source_refresh_performed_to_shared_race_card": False,
        "source_publication_performed": False,
        "site_first_prediction_read": False,
        "site_first_prediction_changed": False,
        "site_prediction_created": False,
        "independent_http_source_authentication_proven": False,
        "independent_server_time_verified": False,
        "boaters_original_exhibition_verified": False,
        "kyoteibiyori_original_exhibition_verified": False,
        "actual_entry_independently_verified": False,
        "results_read": False,
        "formal_fresh_read": False,
        "formal_unlock_authorized": False,
        "accuracy_improvement_proven": False,
        "research_freeze_performed": False,
        "production_model_changed": False,
    }
    parent = out.parent
    _safe_parent(root, parent)
    parent.mkdir(parents=True, exist_ok=True)
    # Prepare the entire immutable bundle in a separate temporary directory,
    # then rename once. Never overwrite an existing same-race proof.
    with tempfile.TemporaryDirectory(prefix=".v366-stage-", dir=parent) as staged:
        stage = Path(staged)
        for name, data in capture.items():
            (stage / (name + ".html")).write_bytes(data["raw"])
        (stage / "manifest.json").write_bytes(canonical(manifest) + b"\n")
        if out.exists() or out.is_symlink():
            raise ValueError("V366_IMMUTABLE_SOURCE_PROOF_ALREADY_EXISTS")
        stage.rename(out)
    return {
        "race_key": key, "path": out.relative_to(root).as_posix(),
        "manifest_sha256": hashlib.sha256(canonical(manifest) + b"\n").hexdigest(),
        "source_only_capture_completed": True,
        "site_first_prediction_changed": False,
        "research_freeze_performed": False,
        "results_read": False, "formal_fresh_read": False,
    }


def main():
    parser = argparse.ArgumentParser(description="V366: opt-in source-only research proof, not site refresh")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key")
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        if not args.race_key:
            parser.error("--race-key is required with --capture")
        report = capture_source_only(args.root, args.race_key)
    else:
        report = select_source_refresh(args.root, _clock(None))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
