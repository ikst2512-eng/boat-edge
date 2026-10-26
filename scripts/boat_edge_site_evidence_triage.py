"""Read-only eligibility triage for stored SITE evidence, not model scoring.

Classifies evidentiary fields without inferring absent predictions, entries,
model SHA or unseen status. No result access, no Formal Fresh modifications.
"""
from __future__ import annotations
import json
from pathlib import Path

REQUIRED_PAIR = ("baseline_ranked_120", "candidate_ranked_120",
                 "baseline_model_sha256", "candidate_model_sha256",
                 "same_input_sha256_verified", "both_first_git_frozen_before_deadline",
                 "actual_entry_six_boats_verified", "model_unseen_independently_verified")


def inspect_site_evidence(evidence, scored=None):
    if not isinstance(evidence, dict):
        raise ValueError("EVIDENCE_OBJECT_REQUIRED")
    if scored is not None and not isinstance(scored, dict):
        raise ValueError("SCORED_OBJECT_INVALID")
    key = evidence.get("race_key")
    if not isinstance(key, str) or not key:
        raise ValueError("RACE_KEY_REQUIRED")
    if scored is not None and scored.get("race_key") != key:
        raise ValueError("RACE_KEY_MISMATCH")
    source = {
        "race_source_sha256": bool(evidence.get("race_sha256")),
        "capture_timestamp": bool(evidence.get("snapshot_saved_at")),
        "first_git_commit": bool(scored and scored.get("first_git_commit")),
        "deadline": bool(scored and scored.get("deadline_jst")),
        "post_result_label_exists": bool(scored and scored.get("winning_combo")),
    }
    paired = {field: evidence.get(field) is True if field.endswith("_verified") or field.startswith("both_")
              else bool(evidence.get(field)) for field in REQUIRED_PAIR}
    # Do not elevate self-assertions to independent Git or unseen proof.
    paired["same_input_sha256_verified"] = False
    paired["both_first_git_frozen_before_deadline"] = False
    paired["actual_entry_six_boats_verified"] = False
    paired["model_unseen_independently_verified"] = False
    return {"race_key": key, "site_evidence_fields": source,
            "comparison_requirements_observed": paired,
            "comparison_eligible": False, "actual_result_read_for_scoring": False,
            "formal_fresh_eligible": False,
            "reason": "INDEPENDENT_PAIRED_PROVENANCE_NOT_VERIFIED"}


def audit_directory(root):
    root = Path(root)
    base = root / "data/site_autopilot"
    evidence = base / "v229_evidence"
    scored = base / "v234_scored"
    rows = []
    if not evidence.is_dir():
        return {"rows": [], "checked": 0, "comparison_eligible": 0}
    for p in sorted(evidence.glob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        q = scored / p.name
        # Scored record is read only for metadata presence; no winning-combo
        # value is exported or used in predictive calculations.
        s = json.loads(q.read_text(encoding="utf-8")) if q.is_file() else None
        rows.append(inspect_site_evidence(e, s))
    return {"rows": rows, "checked": len(rows), "comparison_eligible": 0,
            "research_only": True, "formal_fresh_eligible": False}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("repository", type=Path)
    args = p.parse_args()
    print(json.dumps(audit_directory(args.repository), ensure_ascii=False, indent=2))
