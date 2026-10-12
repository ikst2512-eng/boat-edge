#!/usr/bin/env python3
"""V275: preserve existing site-reference PRE_RESULT evidence after first freeze.

Presence of the per-race frozen snapshot is sufficient to block writes. A broken
snapshot is not permission to rewrite its referenced source and fabricate proof.
This helper never reads a snapshot, a result, a payout, or formal Fresh data.
"""
from pathlib import Path
import re

RACE_KEY = re.compile(r"^20\d{6}-\d{2}-\d{2}$")


def protected_site_snapshot(data_root, race_key):
    if not isinstance(race_key, str) or RACE_KEY.fullmatch(race_key) is None:
        raise ValueError("V275_INVALID_RACE_KEY_FAIL_CLOSED")
    return (Path(data_root) / "site_prediction_snapshots" / (race_key + ".json")).is_file()
