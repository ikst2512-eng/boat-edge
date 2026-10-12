"""V310 pre-result source coverage audit, research-only, no results.

Do not promote a claim of source verification based on a boolean alone.
Every required field must carry a concrete source ID and capture timestamp.
This is a provenance completeness check, not independent source authentication.
"""
import datetime

REQUIRED_FIELDS = ("actual_course_by_boat", "strength_by_boat")
REQUIRED_SOURCES = ("official", "boaters", "kyoteibiyori")


def source_coverage(record):
    if not isinstance(record, dict):
        raise ValueError("INVALID_RECORD")
    deadline = record.get("deadline_jst")
    if not isinstance(deadline, str) or not deadline.endswith("+09:00"):
        raise ValueError("DEADLINE_JST_REQUIRED")
    deadline_dt = datetime.datetime.fromisoformat(deadline)
    captures = record.get("captures")
    if not isinstance(captures, list):
        raise ValueError("CAPTURES_REQUIRED")
    coverage = {s: {"present": False, "fields": [], "pre_deadline": False} for s in REQUIRED_SOURCES}
    reasons = []
    for capture in captures:
        if not isinstance(capture, dict):
            reasons.append("INVALID_CAPTURE")
            continue
        source = capture.get("source")
        if source not in REQUIRED_SOURCES:
            reasons.append("UNKNOWN_SOURCE")
            continue
        identifier = capture.get("source_id")
        fields = capture.get("fields")
        when = capture.get("captured_at_jst")
        if not isinstance(identifier, str) or not identifier.strip() or not isinstance(fields, list):
            reasons.append("INCOMPLETE_CAPTURE_PROVENANCE")
            continue
        try:
            if not isinstance(when, str) or not when.endswith("+09:00"):
                raise ValueError("JST_REQUIRED")
            pre_deadline = datetime.datetime.fromisoformat(when) < deadline_dt
        except ValueError:
            reasons.append("INVALID_CAPTURE_TIMESTAMP")
            continue
        if not pre_deadline:
            reasons.append("CAPTURE_NOT_BEFORE_DEADLINE")
            continue
        coverage[source]["present"] = True
        coverage[source]["pre_deadline"] = True
        coverage[source]["fields"] = sorted(set(coverage[source]["fields"]) | set(
            field for field in fields if isinstance(field, str)))
    missing = [s for s in REQUIRED_SOURCES if not coverage[s]["present"]]
    missing_fields = [f for f in REQUIRED_FIELDS
                      if not any(f in coverage[s]["fields"] for s in REQUIRED_SOURCES)]
    # A claimed actual-course mapping cannot be independently certified by\n    # pre-deadline exhibition or predicted entry. Review must verify semantics.\n    return {"sources": coverage, "missing_sources": missing,
            "missing_required_fields": missing_fields, "reasons": sorted(set(reasons)),
            "ready_for_independent_review": not (missing or missing_fields or reasons),
            "independently_authenticated": False,\n            "actual_course_semantics_verified": False,
            "model_promotion_authorized": False}
