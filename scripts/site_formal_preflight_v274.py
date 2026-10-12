"""Read-only V274 formal overlay preflight, NOT formal validation or unlocking.

Mirrors the V177/V178 browser-consumer requirements using local prediction files.
It cannot certify provenance or substitute for independent formal Fresh100 freeze.
"""
import hashlib
import itertools
import json
import re
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{64}\Z")
KEY = re.compile(r"(\d{8})-(\d{2})-(\d{2})\Z")
LEGAL = {"-".join(t) for t in itertools.permutations("123456", 3)}


def _sha(v):
    blob = json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _guard(g):
    return isinstance(g, dict) and all(g.get(k) is False for k in ("results_seen", "unlock", "scoring")) and g.get("RESULT_UNLOCK_TOKEN", object()) is None


def _valid_worlds(d):
    worlds = [d.get("world_a"), d.get("world_b")]
    if any(not isinstance(w, dict) for w in worlds):
        return False
    probs = [w.get("probability") for w in worlds]
    if any(type(p) not in (float, int) or not 0 < p <= 100 for p in probs):
        return False
    total_p = sum(probs)
    if abs(total_p - 1) > 0.0001 and abs(total_p - 100) > 0.01:
        return False
    expected_a = int((10000 * probs[0] / total_p) / 100 + 0.5) * 100
    for w, budget in zip(worlds, (expected_a, 10000 - expected_a)):
        tickets = w.get("tickets")
        if not isinstance(tickets, list) or not 1 <= len(tickets) <= 120:
            return False
        combos = [t.get("combo") for t in tickets if isinstance(t, dict)]
        if len(combos) != len(tickets) or any(not isinstance(x, str) for x in combos):
            return False
        if len(set(combos)) != len(combos) or any(x not in LEGAL for x in combos):
            return False
        stakes = [t.get("amount") for t in tickets]
        if any(type(v) is not int or v < 100 or v % 100 for v in stakes) or sum(stakes) != budget:
            return False
    return True


def _valid_rank120(d):
    ranked = d.get("ranked_120")
    if not isinstance(ranked, list) or len(ranked) != 120:
        return False
    seen = set()
    prev, total = float("inf"), 0
    for row in ranked:
        if not isinstance(row, dict):
            return False
        combo, probability = row.get("combo"), row.get("probability")
        if not isinstance(combo, str) or combo not in LEGAL or combo in seen or type(probability) not in (int, float):
            return False
        if not 0 <= probability <= 1 or probability > prev + 1e-11:
            return False
        seen.add(combo)
        prev, total = probability, total + probability
    return seen == LEGAL and abs(total - 1) <= 0.0001



def _reject_duplicate_keys(pairs):
    """Reject ambiguous JSON where the same key is repeated in an object."""
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("DUPLICATE_JSON_KEY")
        obj[key] = value
    return obj


def check(root, status):
    """Returns (pass, verified_files, reason). Never touches results or write paths."""
    prediction_dir = Path(root) / "data" / "formal_predictions"
    files = sorted(prediction_dir.glob("*.json")) if prediction_dir.is_dir() else []
    trusted = status.get("approved_prediction_sha256_by_race")
    model = status.get("active_model_id")
    date = str(status.get("target_date", "")).replace("-", "")
    formal = status.get("formalFirst100") or {}
    freeze = formal.get("freezeManifestSha")
    if not _guard(status.get("guards")):
        return False, 0, "STATUS_PRE_RESULT_GUARD_INVALID"
    if not isinstance(trusted, dict) or len(trusted) != 100:
        return False, 0, "APPROVED_RACE_SHA_MAP_NOT_100"
    if len(files) != 100 or {p.stem for p in files} != set(trusted):
        return False, 0, "APPROVED_RACE_FILE_SET_MISMATCH"
    if not isinstance(model, str) or len(model) < 6 or not isinstance(freeze, str) or not SHA.fullmatch(freeze):
        return False, 0, "MODEL_OR_FREEZE_DIGEST_INVALID"
    # An overlay cannot borrow the approval map of an unfrozen or different cohort.
    # This is a site-consumer consistency check, NOT provenance certification.
    if formal.get("races") != 100 or not isinstance(formal.get("coreSha"), str) or not SHA.fullmatch(formal["coreSha"]):
        return False, 0, "FORMAL_COHORT_NOT_FROZEN_100"
    if not isinstance(status.get("formalParentSha"), str) or not SHA.fullmatch(status["formalParentSha"]):
        return False, 0, "PARENT_DIGEST_INVALID"
    verified = 0
    for path in files:
        key = path.stem
        m = KEY.fullmatch(key)
        if not m or m.group(1) != date or not 1 <= int(m.group(2)) <= 24 or not 1 <= int(m.group(3)) <= 12:
            return False, verified, "RACE_KEY_INVALID"
        if not isinstance(trusted[key], str) or not SHA.fullmatch(trusted[key]):
            return False, verified, "APPROVED_DIGEST_INVALID"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
        except (OSError, ValueError, UnicodeError):
            return False, verified, "PREDICTION_JSON_INVALID"
        if not isinstance(raw, dict):
            return False, verified, "PREDICTION_SCHEMA_INVALID"
        meta, derived = raw.get("formal_meta"), raw.get("derived")
        if not isinstance(meta, dict) or not isinstance(derived, dict):
            return False, verified, "PREDICTION_SCHEMA_INVALID"
        if (meta.get("schema_version") != "boat-edge-formal-approved-overlay-v1" or
            meta.get("race_key") != key or meta.get("model_id") != model or
            meta.get("scope") != "FORMAL_FRESH_APPROVED_PRE_RESULT" or
            meta.get("model_approved") is not True or meta.get("formal_gate_pass") is not True or
            meta.get("parent_sha256") != status["formalParentSha"] or
            meta.get("freeze_sha256") != freeze or
            not _guard(meta.get("guards"))):
            return False, verified, "PREDICTION_METADATA_INVALID"
        if meta.get("prediction_sha256") != trusted[key]:
            return False, verified, "PREDICTION_SHA_BINDING_MISMATCH"
        try:
            digest = _sha(derived)
        except (TypeError, ValueError, OverflowError):
            return False, verified, "PREDICTION_CANONICALIZATION_INVALID"
        if digest != trusted[key]:
            return False, verified, "PREDICTION_CONTENT_SHA_MISMATCH"
        if not _valid_rank120(derived) or not _valid_worlds(derived):
            return False, verified, "PREDICTION_RANK_OR_STAKE_INVALID"
        verified += 1
    return True, verified, "VERIFIED_100_SITE_PREFLIGHT_ONLY"
