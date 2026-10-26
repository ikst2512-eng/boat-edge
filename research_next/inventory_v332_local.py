"""Read-only V332 inventory. It never reads results or Formal Fresh data."""
import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

SHA = re.compile(r"^[0-9a-f]{64}$")
MODEL = "BOAT_EDGE_V332_LIVE_LOCAL_SHA_RESEARCH_ONLY"
KEY = re.compile(r"^20[0-9]{6}-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])$")
JST = timedelta(hours=9)

def inspect(root, day):
    if not re.fullmatch(r"20[0-9]{6}", day):
        raise ValueError("BAD_DAY")
    folder = Path(root) / "data/research_local_v332" / day
    result = {"day_jst": day, "scope": "RESEARCH_ONLY_V332_LOCAL_INVENTORY",
              "files_seen": 0, "local_receipt_valid": 0, "invalid": [],
              "independently_attested": 0, "comparable_for_scoring": 0,
              "formal_fresh_read": False, "outcomes_read": False}
    if folder.is_symlink() or not folder.is_dir():
        result["status"] = "NO_LOCAL_V332_DIRECTORY"
        return result
    for path in sorted(folder.iterdir()):
        if path.suffix != ".json":
            continue
        result["files_seen"] += 1
        key = path.stem
        try:
            if path.is_symlink() or not path.is_file() or not KEY.fullmatch(key) or not key.startswith(day):
                raise ValueError("UNSAFE_OR_MISMATCHED_PATH")
            if path.stat().st_size > 2_000_000:
                raise ValueError("OVERSIZE")
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict) or record.get("race_key") != key:
                raise ValueError("RACE_MISMATCH")
            if any(k in record for k in ("results", "result", "outcomes", "payout", "finish", "settlement")):
                raise ValueError("RESULT_BEARING_RECORD")
            freeze = datetime.fromisoformat(record["frozen_at_jst"])
            deadline = datetime.fromisoformat(record["deadline_jst"])
            if freeze.utcoffset() != JST or deadline.utcoffset() != JST or freeze >= deadline or freeze.strftime("%Y%m%d") != day:
                raise ValueError("NOT_PREDEADLINE_LOCAL_RECEIPT")
            if record.get("evidence_level") != "LOCAL_RECEIPT_RAW_SHA_ONLY" or record.get("scoring_authorized") is not False:
                raise ValueError("RESEARCH_GUARDS_INVALID")
            if (record.get("model_id") != MODEL or
                    not isinstance(record.get("race_source_sha256"), str) or
                    not SHA.fullmatch(record["race_source_sha256"]) or
                    not isinstance(record.get("candidate_sha256"), str) or
                    not SHA.fullmatch(record["candidate_sha256"]) or
                    not isinstance(record.get("candidate"), dict) or
                    record.get("results_read") is not False or
                    record.get("formal_fresh_read") is not False):
                raise ValueError("INCOMPLETE_V332_LOCAL_EVIDENCE")
            result["local_receipt_valid"] += 1
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            result["invalid"].append({"race_key": key, "reason": str(exc)})
    result["status"] = "LOCAL_RECEIPTS_ONLY_NOT_INDEPENDENT_PROOF"
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--day", required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.root, args.day), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
