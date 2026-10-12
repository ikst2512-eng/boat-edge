#!/usr/bin/env python3
"""V315 explicit, one-page-at-a-time predeadline source capture.

Manual opt-in only: caller supplies an exact public source URL and race key.
No endpoint discovery, scheduled crawling, paywall bypass, authentication,
result/payout/odds, formal data, scoring, prediction, or site writes.
This writes raw HTML ONCE and prints metadata; it does not confirm that page
text belongs to the race, or that an original-exhibition field exists.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urlsplit
from urllib.request import (
    HTTPRedirectHandler, Request, build_opener, HTTPSHandler,
)

from boat_edge_v314_three_source_evidence import (
    KEY, PROVIDERS, domain_matches, parse_jst,
)

JST = timezone(timedelta(hours=9))
MAX_HTML_BYTES = 2 * 1024 * 1024
# Conservative: never fetch endpoints that could expose a result, payout,
# score, win combo or odds. Inspect path AND query after URL decoding.
BLOCKED = re.compile(
    r"result|payout|payoff|refund|odds|raceresult|race_result|払戻|払い戻し|結果|オッズ",
    re.IGNORECASE,
)


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def check_target(provider, source_url, race_key):
    if provider not in PROVIDERS or not domain_matches(provider, source_url):
        raise ValueError("UNTRUSTED_SOURCE_URL")
    parsed = urlsplit(source_url)
    target = unquote(parsed.path + "?" + parsed.query)
    if BLOCKED.search(target):
        raise ValueError("RESULT_ODDS_OR_PAYOUT_ENDPOINT_PROHIBITED")
    if len(source_url) > 2048 or "\x00" in source_url:
        raise ValueError("INVALID_SOURCE_URL")
    if provider == "official":
        if parsed.path not in (
            "/owpc/pc/race/racelist", "/owpc/pc/race/beforeinfo",
        ):
            raise ValueError("OFFICIAL_SOURCE_ENDPOINT_NOT_ALLOWLISTED")
        date, venue, race_no = race_key.split("-")
        query = parse_qs(parsed.query)
        if (query.get("hd") != [date] or query.get("jcd") != [venue]
                or query.get("rno") != [str(int(race_no))]):
            raise ValueError("OFFICIAL_RACE_IDENTITY_MISMATCH")
    elif parsed.path in ("", "/"):
        raise ValueError("SOURCE_RACE_PAGE_REQUIRED")
    return source_url


def real_fetch(source_url):
    opener = build_opener(HTTPSHandler(), NoRedirects())
    req = Request(source_url, headers={
        "User-Agent": "BOAT-EDGE-ResearchSourceAudit/1.0 (one-page manual capture)",
        "Accept": "text/html",
    })
    try:
        with opener.open(req, timeout=12) as response:
            content_type = response.headers.get_content_type()
            final_url = response.geturl()
            if content_type != "text/html":
                raise ValueError("HTML_CONTENT_TYPE_REQUIRED")
            raw = response.read(MAX_HTML_BYTES + 1)
            return raw, content_type, final_url
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ValueError("SOURCE_FETCH_FAILED") from exc


def capture_one(root, race_key, deadline_jst, provider, source_url,
                fetcher=real_fetch, clock=None):
    if not isinstance(race_key, str) or KEY.fullmatch(race_key) is None:
        raise ValueError("INVALID_RACE_KEY")
    deadline = parse_jst(deadline_jst)
    if deadline.strftime("%Y%m%d") != race_key[:8]:
        raise ValueError("DEADLINE_DATE_MISMATCH")
    check_target(provider, source_url, race_key)
    def now():
        dt = clock() if clock else datetime.now(JST)
        if not isinstance(dt, datetime) or dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("AWARE_CAPTURE_CLOCK_REQUIRED")
        return dt.astimezone(JST)
    if now() >= deadline:
        raise ValueError("CAPTURE_WINDOW_CLOSED")
    relative = (Path("data") / "source_captures" / race_key[:8] / race_key
                / (provider + ".html"))
    root = root.resolve()
    path = root / relative
    receipt_path = path.with_suffix(".receipt.json")
    if path.is_symlink() or path.exists() or receipt_path.exists() or receipt_path.is_symlink():
        raise ValueError("IMMUTABLE_SOURCE_CAPTURE_ALREADY_EXISTS")
    raw, content_type, final_url = fetcher(source_url)
    captured = now()  # Timestamp AFTER all bytes have been received.
    if captured >= deadline:
        raise ValueError("FETCH_COMPLETED_AFTER_DEADLINE")
    if final_url != source_url:
        raise ValueError("SOURCE_REDIRECT_NOT_ALLOWED")
    if content_type != "text/html":
        raise ValueError("HTML_CONTENT_TYPE_REQUIRED")
    if type(raw) is not bytes or not (64 <= len(raw) <= MAX_HTML_BYTES):
        raise ValueError("EMPTY_OVERSIZE_OR_INVALID_HTML")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.parent.resolve().is_relative_to(root):
        raise ValueError("UNSAFE_CAPTURE_DIRECTORY")
    # Exclusive create: no overwrite, even if race metadata later changes.
    with path.open("xb") as stream:
        stream.write(raw)
    receipt = {
        "source_url": source_url,
        "race_key": race_key,
        "captured_at_jst": captured.isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "relative_path": relative.as_posix(),
        # Intentionally empty. Field presence must be separately PARSED,
        # NOT inferred from a successful HTTP fetch or URL.
        "fields": [],
    }
    # Immutable sidecar for later V314 bundle assembly. A sidecar is not an
    # independent proof of HTTP authenticity or GitHub reception time.
    with receipt_path.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description="One explicit public HTML source before deadline only")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    parser.add_argument("--deadline-jst", required=True)
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument("--source-url", required=True)
    args = parser.parse_args()
    record = capture_one(args.root, args.race_key, args.deadline_jst,
                         args.provider, args.source_url)
    print(json.dumps(record, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
