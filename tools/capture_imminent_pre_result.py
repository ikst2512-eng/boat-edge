#!/usr/bin/env python3
"""Capture imminent PRE_RESULT evidence in a bounded, fail-closed scheduled batch.

Scans only today's data/races/*.json, excludes past deadlines and non-locked
races. Captures official beforeinfo source and its SHA256 audit as paired
files in a new output directory. Does not modify race data or infer entries.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from build_verified_entry_candidate import candidate
from parse_explicit_start_order import parse_explicit_start_order
from verify_pre_result_capture import verify as verify_receipt

from archive_pre_result_source import JST, archive
from ingest_verified_start_order import ingest
from apply_pre_result_enrichment import write_new_snapshot


def eligible(path, now):
    try:
        race = json.loads(path.read_text(encoding="utf-8"))
        meta = race.get("meta", {})
        if meta.get("date") != now.date().isoformat() or meta.get("phase") != "PRE_RESULT":
            return None
        if any(meta.get(k) is not False for k in ("results_seen", "scoring", "unlock")):
            return None
        deadline = dt.datetime.fromisoformat(meta["date"] + "T" + meta["deadline"] + ":00+09:00")
        minutes = (deadline - now).total_seconds() / 60
        # Avoid archiving early placeholder pages before start exhibition is published.
        # Ten-minute schedules still have two opportunities in this window.
        if not 3 <= minutes <= 22:
            return None
        key = race.get("race_key", "")
        if path.stem != key:
            return None
        return deadline, race
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def batch(race_dir, output, now=None, maximum=12, capture=archive, enriched_output=None):
    live_clock = now is None
    now = now or dt.datetime.now(JST)
    matches = []
    today_files = sorted(Path(race_dir).glob(now.strftime("%Y%m%d") + "-*.json"))
    for path in today_files:
        result = eligible(path, now)
        if result:
            matches.append((*result, path))
    matches.sort(key=lambda item: item[0])
    report = {"checked": len(matches), "captured": [], "enriched": [], "skipped": [], "failed": [], "t12_receipts": [],
              "selection_diagnostic": {
                  "observed_at_jst": now.astimezone(JST).isoformat(),
                  "today_race_files": len(today_files),
                  "eligible_window_races": len(matches),
                  "excluded_window_or_safety": len(today_files) - len(matches),
                  "capacity_not_attempted": max(0, len(matches) - maximum),
                  "zero_eligible_is_success": False,
              }}
    for deadline, race, path in matches[:maximum]:
        key = race["race_key"]
        dest = Path(enriched_output) / (key + ".json") if enriched_output is not None else None
        if dest is not None and dest.exists():
            report["skipped"].append({"key": key, "reason": "already_enriched"})
            continue
        for attempt in (1, 2):
            suffix = "" if attempt == 1 else f".attempt{attempt}"
            raw_path = Path(output) / (key + suffix + ".beforeinfo.html")
            audit_path = Path(output) / (key + suffix + ".beforeinfo.audit.json")
            if raw_path.exists() != audit_path.exists():
                report["failed"].append({"key": key, "attempt": attempt, "reason": "partial_capture"})
                break
            new_capture = not raw_path.exists()
            if new_capture:
                try:
                    if attempt == 1:
                        audit = capture(race, output)
                    else:
                        audit = capture(race, output, attempt=attempt)
                    report["captured"].append({"key": key, "attempt": attempt, "sha256": audit["sha256"]})
                except (OSError, ValueError, TimeoutError) as exc:
                    report["failed"].append({"key": key, "attempt": attempt, "reason": type(exc).__name__, "capture_error_code": str(exc) if isinstance(exc, ValueError) and str(exc) in {"redirect_not_allowed", "unexpected_response", "invalid_body_size", "not_html_document", "body_gzip_signature", "body_json_signature", "body_xml_signature", "body_utf8_bom", "body_unknown_signature", "unexpected_content_type", "deadline_passed_during_fetch", "not_before_deadline", "invalid_race_key", "race_identity_mismatch", "not_locked_pre_result", "capture_already_exists"} else "unclassified"})
                    break
            if not raw_path.is_file() or not audit_path.is_file():
                break
            try:
                raw = raw_path.read_bytes()
                manifest = json.loads(audit_path.read_text(encoding="utf-8"))
                receipt = verify_receipt(raw, manifest, race, observed_at=(dt.datetime.now(JST) if live_clock else now))
                explicit_entry = parse_explicit_start_order(raw) if receipt["ok"] else None
                report["t12_receipts"].append({
                    "key": key, "attempt": attempt,
                    "receipt_valid": receipt["ok"],
                    "timestamp_cutoff_ok": receipt["t12_timestamp_cutoff_ok"],
                    "status": receipt["t12_status"],
                    "start_entry_six_boats_verified": explicit_entry is not None,
                    "t12_start_entry_verified": bool(receipt["t12_timestamp_cutoff_ok"] and explicit_entry is not None),
                    "exhibition_six_boats_verified": False,
                    "source": "official_beforeinfo_html",
                })
                if not receipt["ok"]:
                    raise ValueError("invalid_captured_receipt")
                candidate(raw, manifest, race, now=now)
                if dest is not None:
                    snapshot = ingest(race, raw, manifest, now=now)
                    write_new_snapshot(dest, snapshot)
                    report["enriched"].append({"key": key, "attempt": attempt, "sha256": manifest["sha256"]})
                else:
                    report["skipped"].append({"key": key, "reason": "verified_not_published", "attempt": attempt})
                break
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                reason = str(exc)
                report["skipped"].append({"key": key, "reason": "entry_not_verified", "attempt": attempt, "detail": reason[:160]})
                # Only a verified official HTML capture with no explicit entry may be retried.
                # Audit failures, malformed sources, and unsafe race state fail closed.
                if reason != "actual_entry_not_explicit_or_ambiguous":
                    report["failed"].append({"key": key, "attempt": attempt, "reason": "verification_failed"})
                    break
                if attempt == 1:
                    # One bounded second fetch in this same ephemeral Actions run.
                    # Preserve attempt 1 evidence; a future run cannot assume artifacts persist.
                    continue
                break
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--races", type=Path, default=Path("data/races"))
    p.add_argument("--output", type=Path, default=Path("artifacts/pre-result-captures"))
    p.add_argument("--maximum", type=int, default=12)
    p.add_argument("--enriched-output", type=Path, default=None)
    args = p.parse_args()
    if not 1 <= args.maximum <= 24:
        p.error("maximum must be from 1 to 24")
    report = batch(args.races, args.output, maximum=args.maximum, enriched_output=args.enriched_output)
    # Preserve race-level capture/parse failures in a durable Actions artifact.
    report_path = args.output.parent / "capture-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Capture errors remain in the report; verified races can still publish.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
