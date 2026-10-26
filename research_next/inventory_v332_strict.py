"""Strict research-only V332 inventory; does not promote local evidence to scoring."""
import argparse
import json
from pathlib import Path
from inventory_v332_local import inspect
from verify_v332_candidate_digest import verify_candidate_digest


def inspect_strict(root, day):
    report = inspect(root, day)
    report["weak_schema_only_count"] = report.pop("local_receipt_valid")
    report["local_digest_verified_count"] = 0
    folder = Path(root) / "data/research_local_v332" / day
    if not folder.is_dir() or folder.is_symlink():
        return report
    rejected = {item["race_key"] for item in report["invalid"]}
    for path in sorted(folder.glob("*.json")):
        if path.stem in rejected:
            continue
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 2000000:
                raise ValueError("UNSAFE_V332_PATH")
            record = json.loads(path.read_text(encoding="utf-8"))
            verify_candidate_digest(record)
            report["local_digest_verified_count"] += 1
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            report["invalid"].append({"race_key": path.stem, "reason": str(exc)})
    report["independently_attested"] = 0
    report["comparable_for_scoring"] = 0
    report["status"] = "DIGEST_ONLY_NOT_INDEPENDENT_PROOF"
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--day", required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_strict(args.root, args.day), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
