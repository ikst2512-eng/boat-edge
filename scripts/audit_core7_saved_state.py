#!/usr/bin/env python3
"""Read-only SITE CORE7 aggregate-vs-saved-race consistency audit.

This is NOT a formal Fresh eligibility validator and never reads results.
"""
import argparse
import json
from pathlib import Path


def audit(data_dir, target_date):
    status = json.loads((data_dir / "model_status.json").read_text(encoding="utf-8"))
    if status.get("target_date") != target_date:
        raise ValueError("model_status target_date does not match requested date")
    saved = []
    for path in sorted((data_dir / "races").glob(target_date.replace("-", "") + "-??-??.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("race_key") != path.stem:
            continue
        if (doc.get("current_model_input") or {}).get("core7_ready") is True:
            saved.append(path.stem.replace("-", ""))
    claimed = status.get("core7") or {}
    actual = {"eligible_count": len(saved),
              "first": saved[0] if saved else None,
              "last": saved[-1] if saved else None}
    declared = {field: claimed.get(field) for field in actual}
    return {"status": "MATCH" if declared == actual else "MISMATCH",
            "date": target_date, "declared": declared, "saved": actual,
            "saved_keys": saved, "site_diagnostic_only": True,
            "formal_first100_eligible": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    report = audit(args.data_dir, args.date)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "MATCH" else 1


if __name__ == "__main__":
    raise SystemExit(main())
