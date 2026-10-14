#!/usr/bin/env python3
"""V301 read-only, same-race SITE research audit; NEVER Formal Fresh scoring.

Only independently scored site-only records and their exact PRE_RESULT Git
freezes are inspected. No result/payout/combined API, model change or bet.
Different cohorts must never be combined to claim a hit-rate improvement.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

JST = timezone(timedelta(hours=9))
KEY = re.compile(r"20[0-9]{6}-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
BASE = Path("data/site_autopilot")
CONFIG = {
    "v236": ("BOAT_EDGE_V236_HITRATE_SCORE_V1",
             "POST_RESULT_SITE_ONLY_NOT_FORMAL_FRESH",
             "BOAT_EDGE_V236_HITRATE_FORWARD_SHADOW_V1",
             "PROSPECTIVE_SITE_SHADOW_NOT_FORMAL_FRESH",
             "frozen_candidate_sha256", "candidate_first_git_commit",
             "official_result", ("hit10", "balance10", "scenario7plus3", "coverage15"),
             "v232_cohort_sha256", "v232_first_git_commit"),
    "v240": ("BOAT_EDGE_V240_INDEPENDENT_SECOND_COVERAGE_SCORE_V1",
             "POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH",
             "BOAT_EDGE_V240_INDEPENDENT_SECOND_COVERAGE_PRE_V1",
             "PRE_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH",
             "frozen_sha256", "candidate_git_commit",
             "winning_combo", ("hit10", "second_coverage10", "pair_coverage10"),
             "parent_sha256", "parent_first_commit"),
    "v254": ("BOAT_EDGE_V254_FUTURE_THIRD_TAIL_SCORED_V1",
             "POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH",
             "BOAT_EDGE_V254_FUTURE_THIRD_TAIL_FROZEN_V1",
             "FUTURE_PRE_RESULT_SITE_ONLY_NOT_FORMAL_FRESH",
             "frozen_sha256", "candidate_first_git_commit",
             "winning_combo", ("hit10", "third_tail10"),
             "parent_v232_sha256", "parent_first_git_commit"),
}

class EvidenceError(ValueError):
    """Fail closed, rather than silently shrinking a comparative denominator."""


def read(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise EvidenceError("MISSING_OR_INVALID_" + path.name) from exc
    if not isinstance(value, dict):
        raise EvidenceError("NOT_AN_OBJECT_" + path.name)
    return value


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def time(value):
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def formal_lock(root):
    # This is ALWAYS checked before reading a post-result SITE research row.
    f = read(root / "data/formal_status.json")
    g = f.get("guards") or {}
    n = (f.get("formalFirst100") or {}).get("races")
    if (any(g.get(k) is not False for k in ("results_seen", "unlock", "scoring"))
            or g.get("RESULT_UNLOCK_TOKEN") is not None or type(n) is not int or n != 0):
        raise EvidenceError("FORMAL_FRESH_CLOSED_EMPTY_GATE_REQUIRED")


def combo(value):
    if not isinstance(value, str) or not re.fullmatch(r"[1-6]-[1-6]-[1-6]", value):
        return False
    return len(set(value.split("-"))) == 3


def first_added(root, path):
    """Reattest immutable original bytes and their first Git commit (not a timestamp guess)."""
    rel = path.relative_to(root).as_posix()
    try:
        hashes = subprocess.check_output(
            ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", rel],
            cwd=root, text=True, stderr=subprocess.DEVNULL).splitlines()
        if not hashes:
            return None
        h = hashes[0]
        when = time(subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", h],
            cwd=root, text=True, stderr=subprocess.DEVNULL).strip())
        original = subprocess.check_output(
            ["git", "show", h + ":" + rel], cwd=root, stderr=subprocess.DEVNULL)
        return {"commit": h, "at": when, "sha256": hashlib.sha256(original).hexdigest()}
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def checked_row(root, study, path, attest=first_added):
    formal_lock(root)
    if study not in CONFIG or not KEY.fullmatch(path.stem) or path.name != path.stem + ".json":
        raise EvidenceError("INVALID_STUDY_OR_RACE_ID")
    key = path.stem
    (s_schema, s_scope, f_schema, f_scope, frozen_sha_field, commit_field,
     win_field, names, parent_sha_field, parent_commit_field) = CONFIG[study]
    scored = read(path)
    freeze_path = root / BASE / (study + "_frozen") / path.name
    parent_path = root / BASE / "v232_cohort" / path.name
    frozen = read(freeze_path)
    parent = read(parent_path)
    if (scored.get("schema") != s_schema or scored.get("scope") != s_scope
            or frozen.get("schema") != f_schema or frozen.get("scope") != f_scope
            or scored.get("race_key") != key or frozen.get("race_key") != key
            or parent.get("race_key") != key
            or parent.get("schema") != "BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1"
            or parent.get("scope") != "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH"):
        raise EvidenceError("SCOPE_RACE_OR_SCHEMA_MISMATCH_" + key)
    if any(parent.get(k) is not False for k in
           ("formal_results_seen", "formal_gate_unlocked",
            "paper_purchases_authorized", "real_purchases_authorized")):
        raise EvidenceError("PARENT_FRESH_GUARD_" + key)
    # V236 predates V240/V254: its frozen key is singular
    # result_seen_at_freeze, its no-promotion guard is proven_improvement,
    # and its scored record has no production_model_changed field.
    freeze_seen_key = "result_seen_at_freeze" if study == "v236" else "results_seen_at_freeze"
    if (scored.get("model_promotion_authorized") is not False
            or frozen.get("production_model_changed") is not False
            or frozen.get(freeze_seen_key) is not False
            or (study == "v236" and frozen.get("proven_improvement") is not False)
            or (study != "v236" and (
                scored.get("production_model_changed") is not False or
                frozen.get("model_promotion_authorized") is not False))):
        raise EvidenceError("PRODUCTION_OR_FREEZE_GUARD_" + key)
    if study == "v236":
        if (scored.get("production_accuracy_improvement_proven") is not False
                or scored.get("real_or_paper_purchase") is not False
                or frozen.get("actual_or_paper_purchase") is not False):
            raise EvidenceError("V236_WAGER_OR_PROMOTION_GUARD_" + key)
    elif study == "v240":
        if (scored.get("real_or_paper_purchase") is not False
                or frozen.get("formal_result_access") is not False):
            raise EvidenceError("V240_WAGER_OR_FORMAL_GUARD_" + key)
    else:
        if (scored.get("real_or_paper_wagers_placed") != 0
                or scored.get("accuracy_improvement_proven") is not False
                or scored.get("formal_result_access") is not False
                or frozen.get("formal_result_access") is not False):
            raise EvidenceError("V254_WAGER_OR_FORMAL_GUARD_" + key)
    due = time(frozen.get("deadline_jst"))
    froze = time(frozen.get("frozen_at"))
    saved = time(parent.get("snapshot_saved_at"))
    if (not due or not froze or not saved or
            due.astimezone(JST).strftime("%Y%m%d") != key[:8] or
            not saved <= froze < due):
        raise EvidenceError("PREDEADLINE_TIMING_INVALID_" + key)
    a = attest(root, freeze_path)
    p = attest(root, parent_path)
    proof_ok = (a and p and a.get("at") and p.get("at") and
                HEX.fullmatch(str(scored.get(frozen_sha_field, ""))) and
                scored[frozen_sha_field] == digest(freeze_path) == a.get("sha256") and
                scored.get(commit_field) == a.get("commit") and
                HEX.fullmatch(str(frozen.get(parent_sha_field, ""))) and
                frozen[parent_sha_field] == digest(parent_path) == p.get("sha256") and
                frozen.get(parent_commit_field) == p.get("commit") and
                saved <= p["at"] <= froze < due and p["at"] <= a["at"] < due)
    if not proof_ok:
        raise EvidenceError("GIT_FIRST_BYTES_NOT_PREDEADLINE_" + key)
    lists = frozen.get("comparators")
    if not isinstance(lists, dict) or set(lists) != set(names):
        raise EvidenceError("COMPARATORS_MISSING_" + key)
    for mode in names:
        picks = lists[mode]
        target = 15 if mode == "coverage15" else 10
        if (not isinstance(picks, list) or len(picks) != target
                or len(set(picks)) != target or any(not combo(x) for x in picks)):
            raise EvidenceError("UNEQUAL_OR_INVALID_TICKETS_" + key)
    if lists["hit10"] != parent.get("top10"):
        raise EvidenceError("PARENT_BASELINE_CHANGED_" + key)
    winning = scored.get(win_field)
    if not combo(winning) or set(scored.get("outcomes") or {}) != set(names):
        raise EvidenceError("RESULT_OR_MODES_INCOMPLETE_" + key)
    outcomes = {m: winning in lists[m] for m in names}
    if any(scored["outcomes"].get(m) is not outcomes[m] for m in names):
        raise EvidenceError("SCORED_VERSUS_FROZEN_TICKET_MISMATCH_" + key)
    if study == "v236" and scored.get("ticket_counts") != {m: len(lists[m]) for m in names}:
        raise EvidenceError("SAVED_POINTS_MISMATCH_" + key)
    if study == "v254" and scored.get("novel_tickets") != len(set(lists["third_tail10"]) - set(lists["hit10"])):
        raise EvidenceError("NOVEL_TICKETS_MISMATCH_" + key)
    if study == "v240" and scored.get("novelty") != {m: len(set(lists[m]) - set(lists["hit10"])) for m in names}:
        raise EvidenceError("NOVEL_TICKETS_MISMATCH_" + key)
    if study == "v254" and scored.get("result_precommitted_sha256") != frozen.get(parent_sha_field):
        raise EvidenceError("V254_PARENT_RESULT_IDENTITY_" + key)
    return {"key": key, "day": key[:8], "winning": winning,
            "baseline": lists["hit10"], "outcomes": outcomes,
            "modes": {m: len(lists[m]) for m in names}}


def paired(rows, mode):
    gain = sum(r["outcomes"][mode] and not r["outcomes"]["hit10"] for r in rows)
    loss = sum(r["outcomes"]["hit10"] and not r["outcomes"][mode] for r in rows)
    n = len(rows)
    discordant = gain + loss
    # Exact two-sided McNemar/binomial for discordant PAIRS, not 2 independent samples.
    p = (min(1.0, 2 * sum(math.comb(discordant, i)
                       for i in range(min(gain, loss) + 1)) / (2 ** discordant))
         if discordant else None)
    return {"races": n, "days": len({r["day"] for r in rows}),
            "point_count": 10,
            "baseline_hits": sum(r["outcomes"]["hit10"] for r in rows),
            "candidate_hits": sum(r["outcomes"][mode] for r in rows),
            "paired_gain": gain, "paired_loss": loss, "paired_discordant": discordant,
            "exact_mcnemar_two_sided_p": p,
            "accuracy_improvement_proven": False, "promotion_authorized": False}


def baseline_topk(rows):
    """Rank-sensitive baseline hits from already verified frozen predictions."""
    return {
        f"top{k}": {
            "hits": sum(r["winning"] in r["baseline"][:k] for r in rows),
            "races": len(rows),
            "hit_rate": (sum(r["winning"] in r["baseline"][:k] for r in rows) / len(rows))
                        if rows else None,
        }
        for k in (3, 5, 10)
    }


def misses(rows):
    result = {"head_missing": 0, "second_missing": 0, "third_missing": 0}
    for r in rows:
        if r["outcomes"]["hit10"]:
            continue
        h, s, _ = r["winning"].split("-")
        tickets = [x.split("-") for x in r["baseline"]]
        if not any(t[0] == h for t in tickets):
            result["head_missing"] += 1
        elif not any(t[0] == h and t[1] == s for t in tickets):
            result["second_missing"] += 1
        else:
            result["third_missing"] += 1
    return result


def compare_10point_modes(left, right, left_mode, right_mode):
    """Head-to-head only on pre-validated identical-race/10-ticket pairs.

    A paired gain means RIGHT hits and LEFT misses; paired loss the reverse.
    Both models receive exactly one 10-ticket set per same race. Never promote.
    """
    if len(left) != len(right):
        raise EvidenceError("PAIRED_MODE_RACE_COUNT_MISMATCH")
    gain = sum((not a["outcomes"][left_mode]) and b["outcomes"][right_mode]
               for a, b in zip(left, right))
    loss = sum(a["outcomes"][left_mode] and (not b["outcomes"][right_mode])
               for a, b in zip(left, right))
    disagree = gain + loss
    p = (min(1.0, 2 * sum(math.comb(disagree, i)
                         for i in range(min(gain, loss) + 1)) / (2 ** disagree))
         if disagree else None)
    return {"races": len(left), "sample_days": len({x["day"] for x in left}),
            "point_count_each": 10,
            "left_hits": sum(x["outcomes"][left_mode] for x in left),
            "right_hits": sum(x["outcomes"][right_mode] for x in right),
            "right_only_hits": gain, "left_only_hits": loss,
            "discordant_pairs": disagree, "exact_mcnemar_two_sided_p": p,
            "improvement_proven": False, "model_promotion_authorized": False}


def audit(root, attest=first_added):
    root = Path(root).resolve()
    formal_lock(root)
    available = {}
    for study in CONFIG:
        folder = root / BASE / (study + "_scored")
        items = {}
        for path in sorted(folder.glob("*.json")) if folder.exists() else []:
            if not KEY.fullmatch(path.stem):
                raise EvidenceError("NON_RACE_SCORED_PATH_" + path.name)
            items[path.stem] = checked_row(root, study, path, attest)
        available[study] = items
    within = {}
    for study, items in available.items():
        rows = list(items.values())
        within[study] = {
            "sample_races": len(rows), "sample_days": len({r["day"] for r in rows}),
            "baseline_topk": baseline_topk(rows),
            "baseline_miss_slots": misses(rows),
            "equal_ten_point_modes": {m: paired(rows, m) for m in CONFIG[study][7]
                                      if m != "hit10" and m != "coverage15"},
            "coverage15_separate_point_budget": (
                {"races": len(rows), "points": 15,
                 "hits": sum(r["outcomes"]["coverage15"] for r in rows),
                 "not_same_ten_point_comparison": True}
                if study == "v236" else None),
        }
    between = {}
    studies = list(CONFIG)
    for i, left in enumerate(studies):
        for right in studies[i+1:]:
            shared = sorted(set(available[left]) & set(available[right]))
            for key in shared:
                a, b = available[left][key], available[right][key]
                if a["baseline"] != b["baseline"] or a["winning"] != b["winning"]:
                    raise EvidenceError("CROSS_STUDY_RACE_OR_BASELINE_CONFLICT_" + key)
            left_rows = [available[left][k] for k in shared]
            right_rows = [available[right][k] for k in shared]
            # Every entry is the SAME race and 10 tickets per comparator.
            # Exclude coverage15 entirely; it is deliberately unequal budget.
            mode_pairs = {
                l_mode + "_vs_" + r_mode: compare_10point_modes(
                    left_rows, right_rows, l_mode, r_mode)
                for l_mode in CONFIG[left][7] if l_mode != "coverage15"
                for r_mode in CONFIG[right][7] if r_mode != "coverage15"
            }
            between[left + "_vs_" + right] = {
                "identical_race_baseline_matches": len(shared),
                "sample_days": len({key[:8] for key in shared}),
                "equal_ten_ticket_head_to_head_only": mode_pairs,
                "separate_cohorts_must_not_be_pooled": True,
                "cross_study_superiority_proven": False,
            }
    return {"schema": "BOAT_EDGE_V301_PAIRED_SITE_ONLY_AUDIT_V1",
            "scope": "VERIFIED_GIT_PREFREEZE_SITE_SCORE_RECHECK_NOT_FORMAL_FRESH",
            "formal_results_read": False, "production_model_changed": False,
            "real_or_paper_wagers_placed": 0, "promotion_authorized": False,
            "accuracy_improvement_proven": False, "within_study": within,
            "same_race_cross_study": between}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args()
    print(json.dumps(audit(args.root), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
