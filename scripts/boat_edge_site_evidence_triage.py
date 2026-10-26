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
    scored_record_present = scored is not None
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
    missing_source = sorted(k for k, present in source.items() if not present)
    missing_pair = sorted(k for k, present in paired.items() if not present)
    return {"race_key": key, "scored_record_present": scored_record_present,
            "site_evidence_fields": source,
            "missing_source_fields": missing_source,
            "missing_comparison_requirements": missing_pair,
            "comparison_requirements_observed": paired,
            "comparison_eligible": False, "actual_result_read_for_scoring": False,
            "formal_fresh_eligible": False,
            "reason": "INDEPENDENT_PAIRED_PROVENANCE_NOT_VERIFIED"}


def audit_directory(root):
    root = Path(root)
    base = root / "data/site_autopilot"
    evidence = base / "v229_evidence"
    scored = base / "v234_scored"
    cohorts = base / "v232_cohort"
    rows = []
    if not evidence.is_dir():
        return {"rows": [], "checked": 0, "comparison_eligible": 0}
    for p in sorted(evidence.glob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        q = scored / p.name
        # Scored record is read only for metadata presence; no winning-combo
        # value is exported or used in predictive calculations.
        s = json.loads(q.read_text(encoding="utf-8")) if q.is_file() else None
        row = inspect_site_evidence(e, s)
        row["v232_cohort_file_present"] = (cohorts / p.name).is_file()
        rows.append(row)
    counts = {name: sum(name in row["missing_comparison_requirements"] for row in rows)
              for name in REQUIRED_PAIR}
    missing_scored_records = sum(not row["scored_record_present"] for row in rows)
    source_counts = {name: sum(name in row["missing_source_fields"] for row in rows)
                     for name in ("race_source_sha256", "capture_timestamp",
                                  "first_git_commit", "deadline", "post_result_label_exists")}
    by_date = {}
    for row in rows:
        day = row["race_key"][:8]
        bucket = by_date.setdefault(day, {"v229_evidence": 0, "v234_scored_present": 0,
                                          "v234_scored_absent": 0})
        bucket["v229_evidence"] += 1
        bucket["v234_scored_present" if row["scored_record_present"]
               else "v234_scored_absent"] += 1
    v232_missing = sum(not row["v232_cohort_file_present"] for row in rows)
    missing_both = sum(not row["v232_cohort_file_present"] and not row["scored_record_present"] for row in rows)
    cohort_unscored = sum(row["v232_cohort_file_present"] and not row["scored_record_present"] for row in rows)
    v232_present = len(rows) - v232_missing
    v232_unscored = cohort_unscored
    v234_without_v232 = sum(r["scored_record_present"] and not r["v232_cohort_file_present"] for r in rows)
    return {"rows": rows, "checked": len(rows), "by_race_date": by_date,
            "v229_without_v232": v232_missing,
            "v229_with_v232": v232_present,
            "v232_without_v234": v232_unscored,
            "v234_without_v232": v234_without_v232,
            "v232_cohort_absent": v232_missing,
            "v232_and_v234_both_absent": missing_both,
            "v232_present_v234_absent": cohort_unscored,
            "scored_record_absent_in_v234": missing_scored_records,
            "scored_record_present_in_v234": len(rows) - missing_scored_records,
            "missing_scored_does_not_prove_git_absent": True,
            "comparison_eligible": 0,
            "missing_comparison_counts": counts, "missing_source_counts": source_counts,
            "research_only": True, "formal_fresh_eligible": False}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("repository", type=Path)
    args = p.parse_args()
    print(json.dumps(audit_directory(args.repository), ensure_ascii=False, indent=2))
