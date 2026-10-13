#!/usr/bin/env python3
"""V367 offline byte-exact replay of the isolated V366 official source-only proof.

Only archived race_input.json, racelist.html, beforeinfo.html, manifest.json
are read. Does not touch mutable SITE cards, prediction snapshots, outcomes,
formal Fresh, the network or production artifacts. Integrity is local SHA and
parser parity, NOT independently authenticated upstream/server provenance.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup

from boat_edge_v230_fast_lane import extract_blocked
from boat_edge_v318_shadow_freeze import canonical, JST
from boat_edge_v370_official_racelist_lane_proof import proof_six_lane_registrations
from boat_edge_v366_isolated_source_only_capture import (
    MODEL as SOURCE_MODEL, OUTPUT_ROOT, ENDPOINTS, _source_url,
    _validate_registration_parity, _validate_official_beforeinfo, _safe_parent,
)

MODEL = "BOAT_EDGE_V367_V366_IMMUTABLE_SOURCE_REPLAY"
KEY = re.compile(r"^20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])$")
RESULT_KEYS = {"results", "result", "payout", "finish", "outcomes"}
FALSE_FLAGS = (
    "source_refresh_performed_to_shared_race_card",
    "source_publication_performed", "site_first_prediction_read",
    "site_first_prediction_changed", "site_prediction_created",
    "independent_http_source_authentication_proven",
    "independent_server_time_verified", "boaters_original_exhibition_verified",
    "kyoteibiyori_original_exhibition_verified",
    "actual_entry_independently_verified", "results_read",
    "formal_fresh_read", "formal_unlock_authorized",
    "accuracy_improvement_proven", "research_freeze_performed",
    "production_model_changed",
)


def _date(value, name):
    if not isinstance(value, str):
        raise ValueError("V367_TIMESTAMP_MISSING:" + name)
    try:
        instant = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("V367_TIMESTAMP_INVALID:" + name) from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("V367_TIMESTAMP_NAIVE:" + name)
    return instant.astimezone(JST)


def _raw(root, path, low=1, high=4_000_000):
    _safe_parent(root, path)
    if not path.is_file():
        raise ValueError("V367_ARCHIVED_SOURCE_MISSING:" + path.name)
    data = path.read_bytes()
    if not low <= len(data) <= high:
        raise ValueError("V367_ARCHIVED_SOURCE_LENGTH_INVALID:" + path.name)
    return data


def replay_one(root, key, expected_manifest_sha256=None):
    if not isinstance(key, str) or KEY.fullmatch(key) is None or key.startswith("20261001-"):
        raise ValueError("V367_INVALID_OR_FORMAL_RACE_KEY")
    root = Path(root).resolve()
    archive = root / OUTPUT_ROOT / key[:8] / key
    _safe_parent(root, archive)
    if not archive.is_dir():
        raise ValueError("V367_IMMUTABLE_SOURCE_ARCHIVE_MISSING")
    manifest_raw = _raw(root, archive / "manifest.json")
    manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
    if expected_manifest_sha256 is not None and manifest_sha != expected_manifest_sha256:
        raise ValueError("V367_EXPECTED_MANIFEST_SHA_MISMATCH")
    try:
        doc = json.loads(manifest_raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("V367_MANIFEST_JSON_INVALID") from exc
    if not isinstance(doc, dict) or canonical(doc) + b"\n" != manifest_raw:
        raise ValueError("V367_MANIFEST_NOT_CANONICAL")
    if (doc.get("model_id") != SOURCE_MODEL or doc.get("race_key") != key or
            doc.get("evidence_level") != "LOCAL_HTTP_RESPONSE_SHA_ONLY" or
            any(doc.get(field) is not False for field in FALSE_FLAGS)):
        raise ValueError("V367_UNTRUSTED_MANIFEST_CLAIMS")
    paths = set(p.name for p in archive.iterdir())
    if paths != {"manifest.json", "race_input.json", "racelist.html", "beforeinfo.html"}:
        raise ValueError("V367_ARCHIVE_UNEXPECTED_OR_MISSING_FILES")
    input_relative = (OUTPUT_ROOT / key[:8] / key / "race_input.json").as_posix()
    if doc.get("input_race_relative_path") != input_relative:
        raise ValueError("V367_NONCANONICAL_INPUT_PATH")
    input_raw = _raw(root, archive / "race_input.json", low=64)
    if hashlib.sha256(input_raw).hexdigest() != doc.get("input_race_sha256"):
        raise ValueError("V367_ARCHIVED_INPUT_SHA_MISMATCH")
    try:
        race = json.loads(input_raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("V367_ARCHIVED_RACE_JSON_INVALID") from exc
    if not isinstance(race, dict) or race.get("race_key") != key or RESULT_KEYS.intersection(race):
        raise ValueError("V367_RACE_IDENTITY_OR_RESULT_GUARD_INVALID")
    meta = race.get("meta")
    if (not isinstance(meta, dict) or meta.get("phase") != "PRE_RESULT" or
            any(meta.get(x) is not False for x in ("results_seen", "unlock", "scoring")) or
            str(meta.get("date", "")).replace("-", "") != key[:8] or
            str(meta.get("venue_code", "")).zfill(2) != key[9:11] or
            type(meta.get("race_no")) is not int or meta["race_no"] != int(key[-2:])):
        raise ValueError("V367_ARCHIVED_RACE_PRE_RESULT_INVALID")
    if not re.fullmatch(r"\d\d:\d\d", str(meta.get("deadline"))):
        raise ValueError("V367_ARCHIVED_DEADLINE_INVALID")
    deadline = _date(meta["date"] + "T" + meta["deadline"] + ":00+09:00", "deadline")
    card_time = _date(meta.get("updated_at"), "race_updated_at")
    selected = _date(doc.get("candidate_selected_at_jst"), "selected")
    frozen = _date(doc.get("source_proof_at_jst"), "source_proof")
    times = [selected]
    sources = doc.get("sources")
    if not isinstance(sources, dict) or set(sources) != set(ENDPOINTS):
        raise ValueError("V367_SOURCE_MANIFEST_SET_INVALID")
    collected = {}
    for kind in ENDPOINTS:
        s = sources[kind]
        if not isinstance(s, dict) or set(s) != {
                "url", "sha256", "bytes", "received_at_jst", "relative_path"}:
            raise ValueError("V367_SOURCE_RECEIPT_SCHEMA_INVALID")
        if (s["url"] != _source_url(key, kind) or
                s["relative_path"] != (OUTPUT_ROOT / key[:8] / key / (kind + ".html")).as_posix()):
            raise ValueError("V367_SOURCE_URL_OR_PATH_INVALID")
        original = _raw(root, archive / (kind + ".html"), low=64, high=2*1024*1024)
        if (hashlib.sha256(original).hexdigest() != s["sha256"] or
                type(s["bytes"]) is not int or len(original) != s["bytes"]):
            raise ValueError("V367_SOURCE_BYTES_SHA_MISMATCH:" + kind)
        collected[kind] = original
        times.append(_date(s["received_at_jst"], kind))
    if not (card_time <= selected <= times[1] <= times[2] <= frozen < deadline
            and all(t.strftime("%Y%m%d") == key[:8] for t in times + [frozen])):
        raise ValueError("V367_ASOF_PREDEADLINE_TIMELINE_INVALID")
    if not all(2*60 <= (deadline - t).total_seconds() <= 19*60 for t in times + [frozen]):
        raise ValueError("V367_FINAL_SELECTION_WINDOW_INVALID")
    registrations = _validate_registration_parity(race, collected["racelist"])
    lane_proof = proof_six_lane_registrations(collected["racelist"], race["racers"])
    coverage, proof = _validate_official_beforeinfo(race, collected["beforeinfo"])
    reg_text = BeautifulSoup(collected["racelist"], "lxml").get_text(" ", strip=True)
    bf_text = BeautifulSoup(collected["beforeinfo"], "lxml").get_text(" ", strip=True)
    reasons, lanes, flags = extract_blocked(race["racers"], reg_text, bf_text, True)
    if reasons or lanes or flags:
        raise ValueError("V367_EXPLICIT_WITHDRAWAL_OR_ABSENCE_FOUND")
    if (registrations != doc.get("registered_racers_matched") or
            lane_proof != doc.get("official_racelist_lane_registration_proof") or
            doc.get("official_racelist_active_race_deadline_matched") is not True or
            coverage != doc.get("official_exhibition_coverage") or
            proof != doc.get("official_start_course_proof")):
        raise ValueError("V367_ORIGINAL_OFFICIAL_PARSER_PROOF_DRIFT")
    return {
        "model_id": MODEL,
        "race_key": key,
        "status": "LOCAL_ARCHIVE_REPLAY_PASS_NOT_SOURCE_AUTHENTICATION",
        "manifest_sha256": manifest_sha,
        "input_race_sha256": hashlib.sha256(input_raw).hexdigest(),
        "official_source_sha256": {
            k: hashlib.sha256(collected[k]).hexdigest() for k in ENDPOINTS},
        "six_registrations_and_exhibition_rows_replayed": True,
        "official_selected_race_deadline_and_course_replayed": True,
        "local_receipt_timeline_consistent": True,
        "independent_source_or_server_timestamp_authenticated": False,
        "live_race_freeze_proven": False,
        "independent_actual_course_proven": False,
        "results_read": False, "formal_fresh_read": False,
        "accuracy_improvement_proven": False,
        "writes_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Offline replay only; no source refresh")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    parser.add_argument("--expected-manifest-sha256")
    args = parser.parse_args()
    print(json.dumps(replay_one(args.root, args.race_key,
                                args.expected_manifest_sha256),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
