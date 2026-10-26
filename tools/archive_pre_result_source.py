#!/usr/bin/env python3
"""Archive official BOATRACE pre-race HTML before deadline.

Creates two new files exclusively: the exact response body and immutable
capture manifest. Does NOT parse predicted entries, results or race outcomes.
Usage: python tools/archive_pre_result_source.py RACE.json OUTPUT_DIRECTORY
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request
import urllib.error

JST = dt.timezone(dt.timedelta(hours=9))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect_not_allowed")


def archive(race, output_dir, now=None, opener=None, attempt=1):
    if type(attempt) is not int or not 1 <= attempt <= 2:
        raise ValueError("invalid_attempt")
    meta = race.get("meta") or {}
    key = race.get("race_key", "")
    if not re.fullmatch(r"\d{8}-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])", key):
        raise ValueError("invalid_race_key")
    date, venue, no = key.split("-")
    if meta.get("date") != f"{date[:4]}-{date[4:6]}-{date[6:]}" or meta.get("venue_code") != venue or int(meta.get("race_no", 0)) != int(no):
        raise ValueError("race_identity_mismatch")
    if meta.get("phase") != "PRE_RESULT" or any(meta.get(k) is not False for k in ("results_seen", "scoring", "unlock")):
        raise ValueError("not_locked_pre_result")
    deadline = dt.datetime.fromisoformat(meta["date"] + "T" + meta["deadline"] + ":00+09:00")
    effective_now = now if now is not None else dt.datetime.now(JST)
    if effective_now.tzinfo is None or effective_now >= deadline or effective_now.date() != deadline.date():
        raise ValueError("not_before_deadline")
    url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd={date}&jcd={venue}&rno={int(no)}"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if attempt == 1 else f".attempt{attempt}"
    rawpath = output_dir / (key + suffix + ".beforeinfo.html")
    manifestpath = output_dir / (key + suffix + ".beforeinfo.audit.json")
    if rawpath.exists() or manifestpath.exists():
        raise FileExistsError("capture_already_exists")
    request = urllib.request.Request(url, headers={"User-Agent": "BOAT-EDGE-PreResult-Audit/1.0", "Accept": "text/html"})
    opener = opener or urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=12) as response:
        if response.geturl() != url or response.status != 200:
            raise ValueError("unexpected_response")
        raw = response.read(2_000_001)
        if not raw or len(raw) > 2_000_000:
            raise ValueError("invalid_body_size")
        if not raw.lstrip().lower().startswith((b"<!doctype html", b"<html")):
            raise ValueError("not_html_document")
        content_type = response.headers.get("Content-Type", "") if hasattr(response, "headers") else ""
        if content_type and "text/html" not in content_type.lower():
            raise ValueError("unexpected_content_type")
    captured_at = now if now is not None else dt.datetime.now(JST)
    if captured_at >= deadline:
        raise ValueError("deadline_passed_during_fetch")
    digest = hashlib.sha256(raw).hexdigest()
    manifest = {"race_key": key, "status": "ok", "source": url,
                "fetched_at": captured_at.isoformat(), "sha256": digest,
                "bytes": len(raw), "kind": "official_beforeinfo_html"}
    # Exclusive files; never overwrite evidence.
    fd = os.open(rawpath, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
        fd = os.open(manifestpath, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except BaseException:
        # Do not leave a partially paired capture that appears complete.
        if not manifestpath.exists():
            rawpath.unlink(missing_ok=True)
        raise
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("race", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    race = json.loads(args.race.read_text(encoding="utf-8"))
    print(json.dumps(archive(race, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
