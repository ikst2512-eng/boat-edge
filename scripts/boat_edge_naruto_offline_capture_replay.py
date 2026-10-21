#!/usr/bin/env python3
"""Isolated replay of already-captured official Naruto original-exhibition HTML.

NO network calls, writes to production data, results access, or assertions that
an arbitrary HTML page belongs to a race. A signed/independent capture system
must supply trustworthy identity/timestamp evidence before production adoption.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from boat_edge_naruto_original_exhibition_parser import parse_naruto_original_exhibition

JST = timezone(timedelta(hours=9))
KEY = re.compile(r"^(20\d{6})-14-(0[1-9]|1[0-2])$")
ALLOWED_HOSTS = {"n14.jp", "www.n14.jp"}


def inspect_capture(html: bytes, *, race_key: str, source_url: str,
                    captured_at: str, deadline: str,
                    expected_sha256: str, independent_race_proof: bool = False):
    """Read-only; returns explicit unverified status when proof is absent."""
    if not isinstance(race_key, str) or not KEY.fullmatch(race_key):
        return {"status": "INVALID_RACE_KEY"}
    try:
        source = urlsplit(source_url)
        valid_url = (source.scheme == "https" and source.hostname in ALLOWED_HOSTS
                     and not source.username and not source.password
                     and not source.fragment and source.port in (None, 443))
    except (TypeError, ValueError):
        valid_url = False
    if not valid_url:
        return {"status": "UNTRUSTED_SOURCE_URL"}
    if type(html) is not bytes or not html or len(html) > 2_000_000:
        return {"status": "INVALID_HTML"}
    digest = hashlib.sha256(html).hexdigest()
    if type(expected_sha256) is not str or digest != expected_sha256:
        return {"status": "SHA256_MISMATCH", "actual_sha256": digest}
    try:
        received = datetime.fromisoformat(captured_at)
        due = datetime.fromisoformat(deadline)
        if (received.utcoffset() is None or due.utcoffset() is None
                or received >= due):
            return {"status": "INVALID_OR_LATE_RECEIPT"}
        if received.astimezone(JST).strftime("%Y%m%d") != race_key[:8]:
            return {"status": "RECEIPT_RACE_DATE_MISMATCH"}
    except (TypeError, ValueError, OverflowError):
        return {"status": "INVALID_TIMESTAMPS"}
    # URL host and hash are NOT independent proof of a particular race.
    if independent_race_proof is not True:
        return {"status": "RACE_IDENTITY_UNVERIFIED", "sha256": digest}
    parsed = parse_naruto_original_exhibition(
        html, identity_verified=True, fetched_at=received, deadline=due)
    parsed["race_key"] = race_key
    parsed["source_url"] = source_url
    parsed["raw_sha256"] = digest
    parsed["capture_proof_supplied_by_caller"] = True
    return parsed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--html", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ns = ap.parse_args()
    # CLI defaults to fail-closed: a JSON manifest alone is not independent
    # proof of the race, even when it claims success.
    manifest = json.loads(ns.manifest.read_text(encoding="utf-8"))
    result = inspect_capture(ns.html.read_bytes(),
        race_key=manifest.get("race_key"), source_url=manifest.get("source_url"),
        captured_at=manifest.get("captured_at"), deadline=manifest.get("deadline"),
        expected_sha256=manifest.get("sha256"), independent_race_proof=False)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("status") == "COMPLETE_SIX_BOATS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
