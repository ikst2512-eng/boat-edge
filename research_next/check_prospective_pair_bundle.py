"""Research-only evidence gate. Never reads race outcomes or Formal Fresh files.

All evidence references are local snapshot paths. Local integrity alone does not
prove independent publication, model execution, or outcome blindness.
"""
import hashlib
import json
from pathlib import Path


def check(root, manifest):
    root = Path(root).resolve()
    report = {"scope": "RESEARCH_PRE_RESULT_ONLY",
              "ready_for_scoring": False, "independently_time_attested": False,
              "formal_fresh_read": False, "outcomes_read": False, "errors": []}
    if not isinstance(manifest, dict) or manifest.get("scope") != "RESEARCH_PRE_RESULT_ONLY":
        report["errors"].append("INVALID_SCOPE")
        return report
    for side in ("baseline", "candidate"):
        item = manifest.get(side)
        if not isinstance(item, dict):
            report["errors"].append("MISSING_" + side.upper())
            continue
        for kind in ("input", "model", "prediction"):
            src = item.get(kind)
            if not isinstance(src, dict):
                report["errors"].append("MISSING_" + side.upper() + "_" + kind.upper())
                continue
            name, digest = src.get("path"), src.get("sha256")
            if (not isinstance(name, str) or not isinstance(digest, str)
                    or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest)):
                report["errors"].append("INVALID_REFERENCE")
                continue
            p = Path(name)
            if (p.is_absolute() or ".." in p.parts or
                    any(word in name.lower() for word in
                        ("result", "outcome", "payout", "finish", "formal", "settlement"))):
                report["errors"].append("UNSAFE_REFERENCE")
                continue
            target = root / p
            if any(part.is_symlink() for part in (target, *target.parents) if part != root):
                report["errors"].append("SYMLINK_FORBIDDEN")
                continue
            if not target.is_file() or not target.resolve().is_relative_to(root):
                report["errors"].append("REFERENCE_NOT_FOUND")
                continue
            if target.stat().st_size > 10_000_000:
                report["errors"].append("REFERENCE_OVERSIZE")
                continue
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                report["errors"].append("SHA_MISMATCH")
    baseline, candidate = manifest.get("baseline"), manifest.get("candidate")
    if isinstance(baseline, dict) and isinstance(candidate, dict):
        if baseline.get("input", {}).get("sha256") != candidate.get("input", {}).get("sha256"):
            report["errors"].append("INPUT_NOT_IDENTICAL")
    if not report["errors"]:
        report["local_byte_integrity"] = "PASS"
        report["errors"].append("INDEPENDENT_PREDEADLINE_RECEIPT_MISSING")
        report["errors"].append("MODEL_EXECUTION_ATTESTATION_MISSING")
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    # Refuse symlinked input manifest and oversized files.
    if args.manifest.is_symlink() or args.manifest.stat().st_size > 100000:
        raise SystemExit("UNSAFE_MANIFEST")
    print(json.dumps(check(args.root, json.loads(args.manifest.read_text(encoding="utf-8"))),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
