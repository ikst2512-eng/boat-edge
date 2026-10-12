#!/usr/bin/env python3
"""V275: preserve existing site-reference PRE_RESULT evidence after first freeze.

Presence of either the per-race site snapshot or immutable prospective V232
cohort blocks source rewrites. Malformed evidence is not a license to overwrite
its source or fabricate a new proof.
This helper never reads a snapshot, a result, a payout, or formal Fresh data.
"""
from pathlib import Path
import re

RACE_KEY = re.compile(r"^20\d{6}-\d{2}-\d{2}$")


def protected_site_snapshot(data_root, race_key):
    if not isinstance(race_key, str) or RACE_KEY.fullmatch(race_key) is None:
        raise ValueError("V275_INVALID_RACE_KEY_FAIL_CLOSED")
    root = Path(data_root)
    # V288: the prospectively Git-committed V232 research cohort is also
    # immutable, even when the separate site snapshot is absent. Never read
    # either frozen record here; existence is a conservative write lock.
    return any((root / prefix / (race_key + ".json")).is_file()
               for prefix in ("site_prediction_snapshots",
                              "site_autopilot/v232_cohort"))
