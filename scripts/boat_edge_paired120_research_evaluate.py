"""Fail-closed paired 120-ticket research evaluation; never a Formal Fresh scorer.

JSON: {"baseline": [record,...], "candidate": [record,...]}.
Each record supplies race_key, input_sha256, model_sha256, first_git_sha,
first_git_at, deadline_at (ISO8601 offsets), ranked_120 [{boat_combo,
relative_model_mass},...], and actual_trifecta. Historical evidence MUST
come from immutable, independently audited Git receipts. Timestamps and
hash strings supplied to this tool are assertions, not independently verified.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import itertools
import json
import math
import re
from pathlib import Path

SHA = re.compile(r"^[a-f0-9]{40,64}$")
TRIPLES = {"-".join(map(str, c)) for c in itertools.permutations(range(1, 7), 3)}
TOPS = (1, 3, 5, 10)


def _time(value):
    if not isinstance(value, str):
        raise ValueError("OFFSET_TIMESTAMP_REQUIRED")
    x = dt.datetime.fromisoformat(value)
    if x.tzinfo is None or x.utcoffset() is None:
        raise ValueError("OFFSET_TIMESTAMP_REQUIRED")
    return x


def _validated(rows, name):
    if not isinstance(rows, list) or not rows:
        raise ValueError("NONEMPTY_RECORDS_REQUIRED")
    index = {}
    for rec in rows:
        if not isinstance(rec, dict):
            raise ValueError("INVALID_RECORD")
        key = rec.get("race_key")
        if not isinstance(key, str) or not re.fullmatch(r"20[0-9]{6}-[0-9]{2}-(?:0[1-9]|1[0-2])", key) or key in index:
            raise ValueError("RACE_KEY_DUPLICATE_OR_INVALID")
        for field in ("input_sha256", "model_sha256", "first_git_sha"):
            if not isinstance(rec.get(field), str) or not SHA.fullmatch(rec[field]):
                raise ValueError("MISSING_EVIDENCE_SHA:" + field)
        if len(rec["input_sha256"]) != 64 or len(rec["model_sha256"]) != 64:
            raise ValueError("REQUIRE_SHA256_FOR_INPUT_AND_MODEL")
        if _time(rec.get("first_git_at")) >= _time(rec.get("deadline_at")):
            raise ValueError("NOT_GIT_FROZEN_BEFORE_DEADLINE")
        ranking = rec.get("ranked_120")
        if not isinstance(ranking, list) or len(ranking) != 120:
            raise ValueError("RANKED_120_REQUIRED")
        tickets = [r.get("boat_combo") for r in ranking if isinstance(r, dict)]
        probs = [r.get("relative_model_mass") for r in ranking if isinstance(r, dict)]
        if len(tickets) != 120 or set(tickets) != TRIPLES or len(set(tickets)) != 120:
            raise ValueError("TICKET_SET_INVALID")
        if any(type(p) not in (float, int) or not math.isfinite(p) or p <= 0 for p in probs):
            raise ValueError("PROBABILITY_INVALID")
        if not math.isclose(math.fsum(probs), 1, abs_tol=1e-9):
            raise ValueError("PROBABILITY_NOT_NORMALIZED")
        if any(probs[i] < probs[i+1] - 1e-13 for i in range(119)):
            raise ValueError("RANKING_NOT_DESCENDING")
        result = rec.get("actual_trifecta")
        if result not in TRIPLES:
            raise ValueError("ACTUAL_RESULT_REQUIRED")
        index[key] = rec
    return index


def _metrics(records):
    n = len(records)
    if not n:
        return None
    hits = {k: 0 for k in TOPS}
    losses = []
    conf = []
    outcomes = []
    for rec in records:
        rank = [r["boat_combo"] for r in rec["ranked_120"]]
        probs = [r["relative_model_mass"] for r in rec["ranked_120"]]
        actual = rec["actual_trifecta"]
        pos = rank.index(actual)
        for k in TOPS:
            hits[k] += int(pos < k)
        p_actual = probs[pos]
        losses.append(-math.log(p_actual))
        conf.append(probs[0])
        outcomes.append(int(pos == 0))
    return {"n": n, "hits": {str(k): hits[k] for k in TOPS},
            "topk_rate": {str(k): hits[k] / n for k in TOPS},
            "log_loss": math.fsum(losses) / n,
            "top1_brier": math.fsum((p-y)**2 for p,y in zip(conf,outcomes))/n,
            "top1_ece": _ece(conf,outcomes)}


def _ece(p, y):
    n = len(p)
    ece = 0.
    for b in range(10):
        ids = [i for i, x in enumerate(p) if min(int(x*10),9) == b]
        if ids:
            ece += len(ids)/n * abs(math.fsum(p[i] for i in ids)/len(ids) - math.fsum(y[i] for i in ids)/len(ids))
    return ece


def evaluate(data):
    if not isinstance(data, dict) or set(data) != {"baseline", "candidate"}:
        raise ValueError("PAIRED_MODELS_REQUIRED")
    a = _validated(data["baseline"], "baseline")
    b = _validated(data["candidate"], "candidate")
    common = sorted(set(a) & set(b))
    paired_a, paired_b = [], []
    for key in common:
        x, y = a[key], b[key]
        if x["input_sha256"] != y["input_sha256"] or x["actual_trifecta"] != y["actual_trifecta"]:
            raise ValueError("COMMON_INPUT_OR_RESULT_MISMATCH:" + key)
        paired_a.append(x)
        paired_b.append(y)
    old, new = _metrics(paired_a), _metrics(paired_b)
    return {"research_only": True, "formal_fresh_eligible": False,
            "git_provenance_independently_authenticated": False,
            "unseen_status_independently_proven": False,
            "common_races": len(common), "baseline": old, "candidate": new,
            "topk_rate_delta": None if old is None else {
                str(k): new["topk_rate"][str(k)]-old["topk_rate"][str(k)] for k in TOPS},
            "improvement_proven": False}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("paired_json", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(json.loads(args.paired_json.read_text())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
