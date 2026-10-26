"""Pure pre-result candidate digest verifier for V332 local inventory.

This does not authenticate third-party sources, freeze time or model identity.
"""
import hashlib
import json


def verify_candidate_digest(record):
    candidate = record.get("candidate")
    digest = record.get("candidate_sha256")
    if not isinstance(candidate, dict) or not isinstance(digest, str):
        raise ValueError("V332_CANDIDATE_DIGEST_MISSING")
    try:
        serialized = json.dumps(candidate, sort_keys=True, ensure_ascii=False,
                                separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("V332_CANDIDATE_NOT_CANONICAL") from exc
    if hashlib.sha256(serialized).hexdigest() != digest:
        raise ValueError("V332_CANDIDATE_SHA_MISMATCH")
    return True
