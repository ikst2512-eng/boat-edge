#!/usr/bin/env python3
"""V314 offline three-provider original-exhibition capture evidence audit.

No network, prediction, result, payout, odds, formal-Fresh or site writes.
A successful bytes/Git/metadata check is only *document completeness*:
timestamps and source identity are not independently authenticated, and
captured fields are not parsed/validated. This cannot authorize prediction.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

SCHEMA = "BOAT_EDGE_V314_THREE_SOURCE_CAPTURE_EVIDENCE_V1"
KEY = re.compile(r"^20[0-9]{6}-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])$")
SHA = re.compile(r"^[0-9a-f]{64}$")
PROVIDERS = {
    "official": {"www.boatrace.jp"},
    "boaters": {"boaters-boatrace.com", "www.boaters-boatrace.com"},
    "kyoteibiyori": {"kyoteibiyori.com", "www.kyoteibiyori.com"},
}
FIELDS = {"lap_time", "turn_time", "straight_time", "exhibition_time",
          "exhibition_st", "scratch_status", "beforeinfo", "start_exhibition"}


def parse_jst(value):
    if not isinstance(value, str) or not value.endswith("+09:00"):
        raise ValueError("JST_TIMESTAMP_REQUIRED")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("INVALID_TIMESTAMP") from exc
    if dt.utcoffset().total_seconds() != 9 * 3600:
        raise ValueError("WRONG_TIMESTAMP_OFFSET")
    return dt


def domain_matches(provider, url):
    if not isinstance(url, str):
        return False
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == "https" and parsed.hostname in PROVIDERS[provider]
                and not parsed.username and not parsed.password
                and parsed.port in (None, 443) and bool(parsed.path))
    except ValueError:
        return False


def first_commit_exact(root, relative, raw, deadline):
    """Git object checks only: commit author/committer dates can be spoofed."""
    try:
        p = relative.as_posix()
        commits = subprocess.run(
            ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", p],
            cwd=root, text=True, capture_output=True, check=True,
        ).stdout.splitlines()
        if len(commits) != 1:
            return False
        first = commits[0]
        initial = subprocess.run(
            ["git", "show", first + ":" + p],
            cwd=root, capture_output=True, check=True,
        ).stdout
        current = subprocess.run(
            ["git", "show", "HEAD:" + p],
            cwd=root, capture_output=True, check=True,
        ).stdout
        when_str = subprocess.run(
            ["git", "show", "-s", "--format=%cI", first],
            cwd=root, text=True, capture_output=True, check=True,
        ).stdout.strip()
        when = datetime.fromisoformat(when_str)
        return (initial == raw and current == raw and when.tzinfo is not None
                and when < deadline)
    except (OSError, ValueError, subprocess.CalledProcessError):
        return False


def capture_report(root, race_key, provider, capture, deadline):
    reasons = []
    if not isinstance(capture, dict):
        return {"provider": provider, "document_consistent": False,
                "reasons": ["CAPTURE_NOT_SUPPLIED"]}
    if set(capture) != {"source_url", "race_key", "captured_at_jst",
                        "sha256", "relative_path", "fields"}:
        reasons.append("INVALID_CAPTURE_SCHEMA")
    if capture.get("race_key") != race_key:
        reasons.append("RACE_IDENTITY_DECLARATION_MISMATCH")
    if not domain_matches(provider, capture.get("source_url")):
        reasons.append("WRONG_PROVIDER_DOMAIN")
    captured = None
    try:
        captured = parse_jst(capture.get("captured_at_jst"))
        if captured >= deadline:
            reasons.append("CAPTURE_NOT_PREDEADLINE")
    except ValueError:
        reasons.append("INVALID_CAPTURE_TIME")
    fields = capture.get("fields")
    if not isinstance(fields, list) or any(
        not isinstance(x, str) or x not in FIELDS for x in fields
    ) or len(set(fields)) != len(fields):
        reasons.append("UNVERIFIED_FIELD_DECLARATION")
    digest = capture.get("sha256")
    if not isinstance(digest, str) or not SHA.fullmatch(digest):
        reasons.append("INVALID_RECORDED_SHA256")
    date = race_key[:8]
    legacy = Path("data/source_captures") / date / race_key / (provider + ".html")
    versioned = None
    if captured is not None:
        versioned = (Path("data/source_captures") / date / race_key / "versions"
                     / (provider + "-" + captured.strftime("%Y%m%dT%H%M%S") + ".html"))
    relative = capture.get("relative_path")
    if relative == legacy.as_posix():
        expected = legacy
    elif versioned is not None and relative == versioned.as_posix():
        expected = versioned
    else:
        reasons.append("CAPTURE_PATH_NOT_CANONICAL")
        expected = legacy  # Never read an untrusted path from JSON.
    target = root / expected
    raw = None
    if target.is_symlink() or not target.is_file():
        reasons.append("RAW_BYTES_MISSING")
    else:
        try:
            raw = target.read_bytes()
            if not raw or hashlib.sha256(raw).hexdigest() != digest:
                reasons.append("RAW_SHA256_MISMATCH")
        except OSError:
            reasons.append("RAW_READ_FAILED")
    if raw is not None and "RAW_SHA256_MISMATCH" not in reasons and "INVALID_RECORDED_SHA256" not in reasons:
        if not first_commit_exact(root, expected, raw, deadline):
            reasons.append("FIRST_GIT_BYTES_OR_TIMESTAMP_NOT_ATTESTED")
    return {
        "provider": provider,
        "document_consistent": not reasons,
        "reasons": sorted(set(reasons)),
        "first_git_commit_is_independent_server_time": False,
        "source_identity_extracted_from_raw": False,
        "source_fields_extracted_and_validated": False,
    }


def audit_bundle(root, bundle):
    if not isinstance(bundle, dict) or set(bundle) != {"schema", "race_key", "deadline_jst", "captures"}:
        raise ValueError("INVALID_BUNDLE_SCHEMA")
    if bundle["schema"] != SCHEMA:
        raise ValueError("WRONG_BUNDLE_SCHEMA")
    key = bundle["race_key"]
    if not isinstance(key, str) or KEY.fullmatch(key) is None:
        raise ValueError("INVALID_RACE_KEY")
    deadline = parse_jst(bundle["deadline_jst"])
    if deadline.strftime("%Y%m%d") != key[:8]:
        raise ValueError("DEADLINE_DATE_MISMATCH")
    captures = bundle["captures"]
    if not isinstance(captures, dict) or set(captures) - set(PROVIDERS):
        raise ValueError("UNKNOWN_SOURCE")
    providers = {
        p: capture_report(root, key, p, captures.get(p), deadline)
        for p in PROVIDERS
    }
    return {
        "schema": SCHEMA,
        "race_key": key,
        "providers": providers,
        "present_consistent_captures": sum(x["document_consistent"] for x in providers.values()),
        "all_three_document_bundles_consistent": all(x["document_consistent"] for x in providers.values()),
        "independent_capture_time_authenticated": False,
        "original_exhibition_parsed_and_verified": False,
        "independently_verified_actual_entry": False,
        "eligible_for_actual_course_ranker": False,
        "candidate_model_promotion_authorized": False,
        "result_or_formal_access": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Verify saved source captures without scraping or scoring")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    bundle = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(json.dumps(audit_bundle(args.root.resolve(), bundle),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
