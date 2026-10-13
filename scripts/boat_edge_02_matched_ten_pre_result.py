"""Track 02 isolated pre-result matched-ten evidence contract.

Validate TWO independently produced research rankings for the same race and
pre-result input. This module neither reads files nor accesses any outcomes,
odds, scraping targets, wagers or formal Fresh. Its metadata and returned
digest are NOT independent proof of source rights or a first Git commit.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import itertools
import json
import math
import re

MODEL = "BOAT_EDGE_02_MATCHED_TEN_PRE_RESULT_CONTRACT_V1"
COMBOS = frozenset("-".join(map(str, p)) for p in itertools.permutations(range(1, 7), 3))
JST = timezone(timedelta(hours=9))
HEX = re.compile(r"[0-9a-f]{64}\Z")
KEY = re.compile(r"20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])\Z")
CONTEXT_FIELDS = {
    "scope", "race_key", "deadline_jst", "target_source_sha256",
    "entry_mapping_sha256", "source_permission_evidence_sha256",
    "parent_model_id", "candidate_model_id",
    "parent_training_end", "candidate_training_end",
    "no_target_outcome", "no_formal_fresh",
}
DOCUMENT_FIELDS = {
    "model_id", "race_key", "target_source_sha256",
    "entry_mapping_sha256", "ranked_120",
}
ROW_FIELDS = {"boat_combo", "relative_model_mass"}


def _canonical(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()


def _sha(obj):
    return hashlib.sha256(_canonical(obj)).hexdigest()


def _cutoff(value):
    if not isinstance(value, str) or not re.fullmatch(r"20\d{6}", value):
        raise ValueError("INVALID_TRAINING_DATE")
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    except ValueError as exc:
        raise ValueError("INVALID_TRAINING_DATE") from exc


def _validate_ranking(doc, context, label):
    if not isinstance(doc, dict) or set(doc) != DOCUMENT_FIELDS:
        raise ValueError("RANKING_DOCUMENT_SCHEMA_INVALID:" + label)
    for field in ("race_key", "target_source_sha256", "entry_mapping_sha256"):
        if doc[field] != context[field]:
            raise ValueError("PAIRED_SOURCE_MISMATCH:" + field)
    if doc["model_id"] != context[label + "_model_id"]:
        raise ValueError("PAIRED_MODEL_ID_MISMATCH:" + label)
    rows = doc["ranked_120"]
    if not isinstance(rows, list) or len(rows) != 120:
        raise ValueError("REQUIRE_FULL_120:" + label)
    seen, total = set(), 0.0
    previous = None
    for row in rows:
        if not isinstance(row, dict) or set(row) != ROW_FIELDS:
            raise ValueError("RANKING_ROW_SCHEMA_INVALID:" + label)
        combo, mass = row["boat_combo"], row["relative_model_mass"]
        if not isinstance(combo, str) or combo not in COMBOS or combo in seen:
            raise ValueError("INVALID_OR_REPEATED_BOAT_COMBO:" + label)
        if type(mass) not in (int, float) or not math.isfinite(mass) or mass <= 0:
            raise ValueError("INVALID_MASS:" + label)
        rankkey = (-mass, combo)
        if previous is not None and previous > rankkey:
            raise ValueError("RANK_ORDER_NOT_DETERMINISTIC:" + label)
        previous = rankkey
        seen.add(combo)
        total += mass
    if seen != COMBOS or not math.isclose(total, 1, rel_tol=0, abs_tol=1e-10):
        raise ValueError("INCOMPLETE_OR_NON_NORMALIZED_120:" + label)
    return [r["boat_combo"] for r in rows[:10]]


def prepare_matched_ten(context, parent, candidate, now):
    """Return a *research-only*, same-race equal-ten shadow pairing.

    Operator must separately archive original input bytes and prove actual
    first Git commit and source rights; timestamp claims here are local only.
    """
    if not isinstance(context, dict) or set(context) != CONTEXT_FIELDS:
        raise ValueError("EXPLICIT_CONTEXT_SCHEMA_REQUIRED")
    key = context["race_key"]
    if not isinstance(key, str) or KEY.fullmatch(key) is None:
        raise ValueError("INVALID_RACE_KEY")
    if key.startswith("20261001-"):
        raise ValueError("FORMAL_TARGET_EXCLUDED")
    if (context["scope"] != "SITE_RESEARCH_PRE_RESULT_NOT_FORMAL" or
            context["no_target_outcome"] is not True or
            context["no_formal_fresh"] is not True):
        raise ValueError("RESEARCH_PRE_RESULT_SCOPE_REQUIRED")
    if any(not isinstance(context[k], str) or HEX.fullmatch(context[k]) is None for k in (
        "target_source_sha256", "entry_mapping_sha256",
        "source_permission_evidence_sha256")):
        raise ValueError("SOURCE_AND_PERMISSION_DIGEST_REQUIRED")
    if (not isinstance(context["parent_model_id"], str) or
            not isinstance(context["candidate_model_id"], str) or
            not context["parent_model_id"].strip() or
            not context["candidate_model_id"].strip() or
            context["parent_model_id"] == context["candidate_model_id"]):
        raise ValueError("TWO_DISTINCT_MODEL_IDS_REQUIRED")
    target_day = _cutoff(key[:8])
    if any(_cutoff(context[n]) >= target_day for n in (
        "parent_training_end", "candidate_training_end")):
        raise ValueError("TRAINING_LEAKS_INTO_TARGET_DAY")
    try:
        deadline = datetime.strptime(key[:8] + context["deadline_jst"],
                                     "%Y%m%d%H:%M").replace(tzinfo=JST)
    except (ValueError, TypeError) as exc:
        raise ValueError("INVALID_DEADLINE_JST") from exc
    if (not isinstance(now, datetime) or now.tzinfo is None or
            now.utcoffset() != timedelta(hours=9) or
            now.date() != target_day or
            not 120 <= (deadline - now).total_seconds() <= 900):
        raise ValueError("NO_LIVE_FINAL_WINDOW_OR_TRUSTED_CLOCK")
    parent10 = _validate_ranking(parent, context, "parent")
    candidate10 = _validate_ranking(candidate, context, "candidate")
    return {
        "schema": MODEL,
        "scope": "SITE_RESEARCH_PRE_RESULT_NOT_FORMAL",
        "race_key": key,
        "deadline_jst": deadline.isoformat(),
        "local_pre_result_paired_at_jst": now.isoformat(),
        "target_source_sha256": context["target_source_sha256"],
        "entry_mapping_sha256": context["entry_mapping_sha256"],
        "source_permission_evidence_sha256": context["source_permission_evidence_sha256"],
        "parent_model_id": parent["model_id"],
        "candidate_model_id": candidate["model_id"],
        "parent_training_end": context["parent_training_end"],
        "candidate_training_end": context["candidate_training_end"],
        "parent_ranked_120_sha256": _sha(parent["ranked_120"]),
        "candidate_ranked_120_sha256": _sha(candidate["ranked_120"]),
        "same_ticket_count_each": 10,
        "parent_top10": parent10,
        "candidate_top10": candidate10,
        "parent_and_candidate_are_boat_tickets": True,
        "each_virtual_stake_yen": 1000,
        "per_model_virtual_budget_yen": 10000,
        "odds_used_for_ranking": False,
        "local_clock_and_provenance_claims_not_independently_attested": True,
        "source_rights_verified_by_code": False,
        "first_git_commit_time_independently_verified": False,
        "actual_entry_independently_verified": False,
        "results_read": False, "formal_fresh_read": False,
        "scoring_authorized": False, "calibrated": False,
        "accuracy_improvement_proven": False, "production_eligible": False,
        "wagers_authorized": False,
    }
