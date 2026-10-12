#!/usr/bin/env python3
"""V332: usable live-only, immutable SITE research freeze without a Git commit.

V316/V314 require source captures to have been committed to Git HEAD before a
candidate may be frozen, creating a circular operational dependency at the
deadline. This *separate* local-evidence lane validates raw HTML bytes against
V315 immutable receipts and freezes V312 research candidate immediately.

Evidence level is LOCAL_SHA_ONLY, explicitly NOT Git/server-authenticated,
NOT original-exhibition parsed/validated and NOT an independently verified
actual entry. No results, formal Fresh, payouts, odds, model promotion, wagers,
automatic URL discovery or retrospective freezing.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

from boat_edge_v312_pre_result_ablation import build_shadow
from boat_edge_v314_three_source_evidence import (
    KEY, PROVIDERS, SHA, parse_jst,
)
from boat_edge_v315_source_capture import (
    MAX_HTML_BYTES, capture_one, check_target, real_fetch,
)
from boat_edge_v318_shadow_freeze import JST, canonical, parse_time
from boat_edge_v333_source_urls import suggested_source_urls


MODEL = "BOAT_EDGE_V332_LIVE_LOCAL_SHA_RESEARCH_ONLY"


def _now(clock):
    instant = clock() if clock is not None else datetime.now(JST)
    if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("AWARE_CAPTURE_CLOCK_REQUIRED")
    return instant.astimezone(JST)


def _receipt_location(root, key, provider):
    folder = root / "data/source_captures" / key[:8] / key
    return folder / (provider + ".receipt.json"), folder / (provider + ".html")


def _local_capture(root, key, provider, deadline, now, expected_url=None):
    receipt_path, raw_path = _receipt_location(root, key, provider)
    if (receipt_path.is_symlink() or raw_path.is_symlink()
            or receipt_path.parent.is_symlink() or
            receipt_path.parent.parent.is_symlink()):
        raise ValueError("SOURCE_SYMLINK_FORBIDDEN:" + provider)
    if (not receipt_path.resolve().is_relative_to(root) or
            not raw_path.resolve().is_relative_to(root)):
        raise ValueError("SOURCE_OUTSIDE_REPOSITORY:" + provider)
    if not receipt_path.is_file() or not raw_path.is_file():
        raise ValueError("SOURCE_RECEIPT_OR_RAW_MISSING:" + provider)
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise ValueError("INVALID_RECEIPT:" + provider) from exc
    if not isinstance(receipt, dict) or set(receipt) != {
        "source_url", "race_key", "captured_at_jst",
        "sha256", "relative_path", "fields",
    }:
        raise ValueError("RECEIPT_SCHEMA_INVALID:" + provider)
    if receipt["race_key"] != key:
        raise ValueError("RECEIPT_RACE_ID_MISMATCH:" + provider)
    check_target(provider, receipt["source_url"], key)
    if expected_url is not None and receipt["source_url"] != expected_url:
        raise ValueError("CAPTURE_SOURCE_URL_MISMATCH:" + provider)
    expected_path = Path("data/source_captures") / key[:8] / key / (provider + ".html")
    if receipt["relative_path"] != expected_path.as_posix():
        raise ValueError("NONCANONICAL_RECEIPT_PATH:" + provider)
    if receipt["fields"] != []:
        raise ValueError("UNPARSED_FIELDS_MUST_NOT_BE_ASSERTED:" + provider)
    captured = parse_jst(receipt["captured_at_jst"])
    if (captured.strftime("%Y%m%d") != key[:8] or
            captured >= deadline or captured > now):
        raise ValueError("CAPTURE_TIMESTAMP_NOT_VALID:" + provider)
    digest = receipt["sha256"]
    if not isinstance(digest, str) or SHA.fullmatch(digest) is None:
        raise ValueError("INVALID_SOURCE_DIGEST:" + provider)
    raw = raw_path.read_bytes()
    if (len(raw) < 64 or len(raw) > MAX_HTML_BYTES or
            hashlib.sha256(raw).hexdigest() != digest):
        raise ValueError("SOURCE_RAW_SHA256_MISMATCH:" + provider)
    return receipt


def _eligible_race(root, key, now):
    path = root / "data/races" / (key + ".json")
    if path.is_symlink():
        raise ValueError("RACE_SYMLINK_FORBIDDEN")
    raw = path.read_bytes()
    race = json.loads(raw)
    if not isinstance(race, dict) or race.get("race_key") != key:
        raise ValueError("RACE_KEY_MISMATCH")
    if any(x in race for x in ("results", "result", "payout", "finish", "outcomes")):
        raise ValueError("RESULT_BEARING_RACE_DOCUMENT_FORBIDDEN")
    meta = race.get("meta")
    if not isinstance(meta, dict) or meta.get("phase") != "PRE_RESULT":
        raise ValueError("PRE_RESULT_REQUIRED")
    if any(meta.get(x) is not False for x in ("results_seen", "unlock", "scoring")):
        raise ValueError("RESULT_OR_UNLOCK_FLAG_FORBIDDEN")
    if not isinstance(meta.get("date"), str) or meta["date"].replace("-", "") != key[:8]:
        raise ValueError("RACE_DATE_MISMATCH")
    deadline = parse_time(meta["date"] + "T" + meta["deadline"] + ":00+09:00")
    if now >= deadline:
        raise ValueError("LIVE_WINDOW_CLOSED_NO_BACKFILL")
    try:
        updated = datetime.fromisoformat(meta["updated_at"])
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("INVALID_RACE_UPDATED_AT") from exc
    if updated.tzinfo is None or updated >= deadline or updated > now:
        raise ValueError("RACE_FILE_NOT_ASOF_PREDEADLINE")
    source_audit = race.get("source_audit")
    if not isinstance(source_audit, dict):
        raise ValueError("SOURCE_AUDIT_REQUIRED")
    for provider in ("race_card", "beforeinfo"):
        source = source_audit.get(provider)
        if not isinstance(source, dict) or source.get("status") != "ok":
            raise ValueError("SOURCE_NOT_OK:" + provider)
        try:
            fetched = datetime.fromisoformat(source["fetched_at"])
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError("INVALID_SOURCE_FETCH_TIME:" + provider) from exc
        if fetched.tzinfo is None or fetched >= deadline or fetched > now:
            raise ValueError("SOURCE_NOT_ASOF_PREDEADLINE:" + provider)
        # The official race-card URL itself must identify this exact race.
        try:
            check_target("official", source["source"], key)
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError("SOURCE_RACE_URL_MISMATCH:" + provider) from exc
    candidate = build_shadow(race)
    candidate["race_source_sha256"] = hashlib.sha256(raw).hexdigest()
    return candidate, deadline, race


def live_local_freeze(root, race_key, source_urls=None, capture=False,
                      fetcher=real_fetch, clock=None):
    """One live race. Optional opt-in fetch of missing pages; never overwrite."""
    if not isinstance(race_key, str) or KEY.fullmatch(race_key) is None:
        raise ValueError("INVALID_RACE_KEY")
    # The untouched 2026-10-01 Formal Fresh target is never a SITE fixture.
    if race_key.startswith("20261001-"):
        raise ValueError("FORMAL_FRESH_TARGET_EXCLUDED")
    root = Path(root).resolve()
    now = _now(clock)
    candidate, deadline, race = _eligible_race(root, race_key, now)
    output = root / "data/research_local_v332" / race_key[:8] / (race_key + ".json")
    if output.exists() or output.is_symlink():
        raise ValueError("IMMUTABLE_RESEARCH_FREEZE_ALREADY_EXISTS")
    source_urls = dict(source_urls or {})
    if set(source_urls) - set(PROVIDERS):
        raise ValueError("UNKNOWN_SOURCE_PROVIDER")
    for provider, url in source_urls.items():
        check_target(provider, url, race_key)
    if capture:
        # Opt-in live capture: derive documented public race-page URL candidates
        # for *all* three providers. User-supplied URLs take precedence; the
        # result is still only self-reported local evidence, never source auth.
        for provider, url in suggested_source_urls(race_key).items():
            source_urls.setdefault(provider, url)
        missing = [provider for provider in PROVIDERS
                   if not _receipt_location(root, race_key, provider)[0].is_file()]
        for provider in missing:
            capture_one(root, race_key, deadline.isoformat(), provider,
                        source_urls[provider], fetcher=fetcher, clock=clock)
    now = _now(clock)
    if now >= deadline:
        raise ValueError("LIVE_WINDOW_CLOSED_DURING_CAPTURE")
    receipts = {provider: _local_capture(root, race_key, provider, deadline, now,
                                         source_urls.get(provider))
                for provider in PROVIDERS}
    # A final live deadline guard prevents a slow validation or capture from
    # being mistaken for a frozen prospective prediction.
    now = _now(clock)
    if (deadline - now).total_seconds() < 5:
        raise ValueError("INSUFFICIENT_PREDEADLINE_WRITE_MARGIN")
    if (candidate.get("production_eligible") is not False
            or candidate.get("scoring_authorized") is not False
            or candidate.get("calibrated") is not False
            or candidate.get("improvement_proven") is not False):
        raise ValueError("UNVERIFIED_MODEL_CLAIM_FORBIDDEN")
    payload = {
        "model_id": MODEL, "race_key": race_key,
        "deadline_jst": deadline.isoformat(),
        "frozen_at_jst": now.isoformat(timespec="microseconds"),
        "entry_basis": "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL",
        "evidence_level": "LOCAL_RECEIPT_RAW_SHA_ONLY",
        "race_source_sha256": candidate["race_source_sha256"],
        "source_receipts": receipts,
        "source_bundle_sha256": hashlib.sha256(canonical(receipts)).hexdigest(),
        "candidate_sha256": hashlib.sha256(canonical(candidate)).hexdigest(),
        "candidate": candidate,
        "git_first_seen_before_deadline_verified": False,
        "independent_capture_time_authenticated": False,
        "source_race_identity_extracted_from_raw": False,
        "original_exhibition_fields_parsed": False,
        "boaters_original_exhibition_verified": False,
        "kyoteibiyori_original_exhibition_verified": False,
        "actual_course_independently_verified": False,
        "results_read": False, "formal_fresh_read": False,
        "accuracy_improvement_proven": False,
        "model_promotion_authorized": False,
        "production_eligible": False, "scoring_authorized": False,
        "wagers_authorized": False,
    }
    if output.parent.is_symlink():
        raise ValueError("OUTPUT_DIRECTORY_SYMLINK_FORBIDDEN")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.parent.is_symlink() or output.is_symlink():
        raise ValueError("OUTPUT_DIRECTORY_SYMLINK_FORBIDDEN")
    serialized = canonical(payload) + b"\n"
    with output.open("xb") as stream:
        stream.write(serialized)
    return {
        "path": output.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(serialized).hexdigest(),
        "record": payload,
    }


def main():
    parser = argparse.ArgumentParser(description="Live research capture+freeze; never formal or scoring")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    parser.add_argument("--capture", action="store_true",
                        help="Opt in to one public HTML fetch per missing provider")
    parser.add_argument("--official-url")
    parser.add_argument("--boaters-url")
    parser.add_argument("--kyoteibiyori-url")
    args = parser.parse_args()
    urls = {p: getattr(args, p + "_url") for p in PROVIDERS
            if getattr(args, p + "_url") is not None}
    print(json.dumps(live_local_freeze(args.root, args.race_key,
                                      source_urls=urls, capture=args.capture),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
