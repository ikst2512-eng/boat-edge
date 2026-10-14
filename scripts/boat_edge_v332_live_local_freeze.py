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
import copy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

from boat_edge_v312_pre_result_ablation import build_shadow
from boat_edge_v314_three_source_evidence import (
    KEY, PROVIDERS, SHA, parse_jst,
)
from boat_edge_v315_source_capture import (
    MAX_HTML_BYTES, capture_one, check_target, real_fetch,
    assert_source_network_allowed,
)
from boat_edge_v318_shadow_freeze import JST, canonical, parse_time
from boat_edge_v333_source_urls import suggested_source_urls
from boat_edge_v360_research_ranked120 import MODEL as RANKED120_MODEL, derive_120
from boat_edge_v362_official_start_course_proof import (
    MODEL as START_PROOF_MODEL, parse_proven_course_rows,
)


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


def candidate_from_raw(raw, key, now, official_start_raw=None):
    """Pure replay of the exact input bytes at an explicitly supplied freeze time.

    This validates local metadata only; it never attests upstream authenticity.
    """
    if not isinstance(key, str) or KEY.fullmatch(key) is None:
        raise ValueError("INVALID_RACE_KEY")
    if key.startswith("20261001-"):
        raise ValueError("FORMAL_FRESH_TARGET_EXCLUDED")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("AWARE_CAPTURE_CLOCK_REQUIRED")
    now = now.astimezone(JST)
    if now.strftime("%Y%m%d") != key[:8]:
        raise ValueError("LIVE_INPUT_DATE_MISMATCH")
    if type(raw) is not bytes:
        raise ValueError("RACE_INPUT_BYTES_REQUIRED")
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
        # A timestamp older than the actual final window is not live evidence.
        freshness_minutes = 16 if provider == "race_card" else 15
        if (now - fetched).total_seconds() > freshness_minutes * 60:
            raise ValueError("SOURCE_TOO_STALE_FOR_FINAL_WINDOW:" + provider)
        # The official race-card URL itself must identify this exact race.
        try:
            check_target("official", source["source"], key)
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError("SOURCE_RACE_URL_MISMATCH:" + provider) from exc
    if official_start_raw is not None:
        official = source_audit["beforeinfo"]
        expected = official.get("sha256")
        if (not isinstance(expected, str) or SHA.fullmatch(expected) is None
                or hashlib.sha256(official_start_raw).hexdigest() != expected):
            raise ValueError("START_SOURCE_RAW_VS_OFFICIAL_AUDIT_SHA_MISMATCH")
        # Check an exact official beforeinfo endpoint, not an arbitrary
        # race-labelled page. The same-race URL has been validated above.
        from urllib.parse import urlsplit
        if urlsplit(official["source"]).path != "/owpc/pc/race/beforeinfo":
            raise ValueError("START_SOURCE_NOT_OFFICIAL_BEFOREINFO")
        proof = parse_proven_course_rows(official_start_raw, race)
        race = copy.deepcopy(race)
        for row in race["beforeinfo"]["start_exhibition"]:
            if row.get("course") is None:
                row["course"] = proof["course_by_boat"][str(row["lane"])]
    candidate = build_shadow(race)
    if official_start_raw is not None:
        candidate["start_course_official_table_proof_model"] = START_PROOF_MODEL
        candidate["start_course_official_html_sha256"] = proof["official_html_sha256"]
    candidate["race_source_sha256"] = hashlib.sha256(raw).hexdigest()
    return candidate, deadline, race


def _eligible_race(root, key, now):
    path = root / "data/races" / (key + ".json")
    if path.is_symlink():
        raise ValueError("RACE_SYMLINK_FORBIDDEN")
    raw = path.read_bytes()
    try:
        parsed = json.loads(raw)
        starts = (parsed.get("beforeinfo") or {}).get("start_exhibition")
        needs_proof = (isinstance(starts, list) and len(starts) == 6
                       and any(isinstance(row, dict) and row.get("course") is None
                               for row in starts))
    except (ValueError, AttributeError, TypeError):
        needs_proof = False
    official_raw = None
    if needs_proof:
        # Reject locked, result-bearing, wrong-date and closed inputs *before*
        # even opening the auxiliary official source file.
        meta = parsed.get("meta") if isinstance(parsed, dict) else None
        if (parsed.get("race_key") != key or not isinstance(meta, dict)
                or meta.get("phase") != "PRE_RESULT"
                or any(meta.get(k) is not False for k in ("results_seen", "unlock", "scoring"))
                or any(name in parsed for name in ("results", "result", "payout", "finish", "outcomes"))
                or now.strftime("%Y%m%d") != key[:8]):
            raise ValueError("START_SOURCE_PRE_RESULT_ONLY")
        venue, round_no = key.split("-")[1:]
        relative = (Path("data/raw") / key[:8] /
                    (venue + "_" + round_no + "_beforeinfo.html"))
        target = root / relative
        # Reject symlinks at any ancestor, not only the final three paths.
        parent = target
        while parent != root:
            if parent.is_symlink():
                raise ValueError("START_SOURCE_RAW_SYMLINK_FORBIDDEN")
            parent = parent.parent
        if not target.is_file() or not target.resolve().is_relative_to(root):
            raise ValueError("START_SOURCE_SAME_RACE_RAW_HTML_MISSING")
        official_raw = target.read_bytes()
    candidate, deadline, race = candidate_from_raw(raw, key, now, official_raw)
    return candidate, deadline, race, raw, official_raw


def _save_race_input(root, key, raw, filename="race_input.json"):
    """Keep the original bytes, never a reread of a changing data/races file."""
    if filename not in ("race_input.json", "official_start_beforeinfo.html"):
        raise ValueError("UNSUPPORTED_IMMUTABLE_INPUT_NAME")
    relative = Path("data/source_captures") / key[:8] / key / filename
    path = root / relative
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError("RACE_INPUT_SNAPSHOT_SYMLINK_FORBIDDEN")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.resolve().is_relative_to(root):
        raise ValueError("RACE_INPUT_SNAPSHOT_OUTSIDE_ROOT")
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError:
        # A retry after an interrupted capture can reuse identical input only.
        if not path.is_file() or path.read_bytes() != raw:
            raise ValueError("IMMUTABLE_RACE_INPUT_SNAPSHOT_MISMATCH")


# V332 is a SITE-only runner: a race on any live Formal target date must
# never be opened, even if the protected cohort has not yet been frozen.
# This static denylist is a backstop, not a substitute for current status.
_KNOWN_FORMAL_DAYS = frozenset(("20261001", "20261005", "20261013"))


def _nonformal_target_preflight(root, race_key, now):
    """Inspect *metadata only* before any SITE race file or network access.

    Formal-status timestamps are repository claims, not independently attested
    server receipts. Fail closed on missing/stale/malformed or unlocked status.
    Neither Formal outcomes nor prediction content are opened.
    """
    if race_key[:8] in _KNOWN_FORMAL_DAYS:
        raise ValueError("FORMAL_FRESH_TARGET_EXCLUDED")
    status_path = root / "data/formal_status.json"
    if status_path.is_symlink() or not status_path.is_file():
        raise ValueError("FORMAL_STATUS_METADATA_REQUIRED")
    try:
        if status_path.stat().st_size > 131072:
            raise ValueError("FORMAL_STATUS_METADATA_TOO_LARGE")
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("FORMAL_STATUS_METADATA_INVALID") from exc
    if (not isinstance(status, dict) or
            status.get("schema_version") != "boat-edge-formal-status-v2"):
        raise ValueError("FORMAL_STATUS_METADATA_SCHEMA_INVALID")
    guards = status.get("guards")
    races = (status.get("formalFirst100") or {}).get("races")
    if (not isinstance(guards, dict) or
            any(guards.get(k) is not False
                for k in ("results_seen", "unlock", "scoring")) or
            guards.get("RESULT_UNLOCK_TOKEN", False) is not None or
            type(races) is not int or races != 0):
        raise ValueError("FORMAL_FRESH_MUST_REMAIN_LOCKED")
    try:
        updated = datetime.fromisoformat(status["asOf"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("FORMAL_STATUS_ASOF_INVALID") from exc
    if (updated.tzinfo is None or updated.utcoffset() != timedelta(hours=9)
            or updated.strftime("%Y%m%d") != race_key[:8] or updated > now):
        raise ValueError("FORMAL_STATUS_NOT_CURRENT_PREDEADLINE")
    target = status.get("target_date")
    last = status.get("last_cohort")
    dates = [target]
    if last is not None:
        if not isinstance(last, dict):
            raise ValueError("FORMAL_LAST_COHORT_INVALID")
        dates.append(last.get("date"))
    for value in dates:
        try:
            day = datetime.strptime(value, "%Y-%m-%d").strftime("%Y%m%d")
        except (TypeError, ValueError) as exc:
            raise ValueError("FORMAL_PROTECTED_DATE_METADATA_INVALID") from exc
        if day == race_key[:8]:
            raise ValueError("FORMAL_FRESH_TARGET_EXCLUDED")
    protected_prediction = root / "data/formal_predictions" / (race_key + ".json")
    if protected_prediction.is_symlink() or protected_prediction.exists():
        # Path presence only. Protected prediction contents are NEVER opened.
        raise ValueError("FORMAL_PREDICTION_PATH_EXCLUDED")


def live_local_freeze(root, race_key, source_urls=None, capture=False,
                      fetcher=real_fetch, clock=None):
    """One live race. Optional opt-in fetch of missing pages; never overwrite."""
    if not isinstance(race_key, str) or KEY.fullmatch(race_key) is None:
        raise ValueError("INVALID_RACE_KEY")
    root = Path(root).resolve()
    now = _now(clock)
    _nonformal_target_preflight(root, race_key, now)
    candidate, deadline, race, race_raw, official_start_raw = _eligible_race(root, race_key, now)
    output = root / "data/research_local_v332" / race_key[:8] / (race_key + ".json")
    if output.exists() or output.is_symlink():
        raise ValueError("IMMUTABLE_RESEARCH_FREEZE_ALREADY_EXISTS")
    source_urls = dict(source_urls or {})
    if set(source_urls) - set(PROVIDERS):
        raise ValueError("UNKNOWN_SOURCE_PROVIDER")
    for provider, url in source_urls.items():
        check_target(provider, url, race_key)
    if capture and fetcher is real_fetch:
        # Fail BEFORE the first official/third-party network call. Mocked
        # offline fixtures keep testing parsing, never source rights.
        candidates = suggested_source_urls(race_key)
        for provider in ('boaters', 'kyoteibiyori'):
            assert_source_network_allowed(source_urls.get(provider, candidates[provider]))
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
    # V360: reconstruct all three 120-way lists from the exact V312 candidate
    # input, fail closed unless stored Top10 and both head-mass labels match.
    # This runs only on the existing live predeadline path; no backfill CLI.
    research_ranked120 = derive_120(race, candidate)
    # V343: the existing V336 source_captures artifact glob includes this exact
    # input snapshot. Hash-only provenance cannot reproduce the candidate.
    _save_race_input(root, race_key, race_raw)
    if official_start_raw is not None:
        _save_race_input(root, race_key, official_start_raw,
                         filename="official_start_beforeinfo.html")
    # A final live deadline guard prevents a slow validation or capture from
    # being mistaken for a frozen prospective prediction.
    now = _now(clock)
    if (deadline - now).total_seconds() < 5:
        raise ValueError("INSUFFICIENT_PREDEADLINE_WRITE_MARGIN")
    # Input freshness must still hold at the recorded freeze instant, even if
    # provider capture was slow. Revalidate the original bytes, not current data.
    replayed, _, _ = candidate_from_raw(
        race_raw, race_key, now, official_start_raw)
    if canonical(replayed) != canonical(candidate):
        raise ValueError("START_SOURCE_FINAL_CANDIDATE_REPLAY_DRIFT")
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
        "official_start_course_source_sha256": (
            hashlib.sha256(official_start_raw).hexdigest()
            if official_start_raw is not None else None),
        "source_receipts": receipts,
        "source_bundle_sha256": hashlib.sha256(canonical(receipts)).hexdigest(),
        "candidate_sha256": hashlib.sha256(canonical(candidate)).hexdigest(),
        "candidate": candidate,
        "research_ranked_120_schema": RANKED120_MODEL,
        "research_ranked_120_by_mode": research_ranked120,
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
