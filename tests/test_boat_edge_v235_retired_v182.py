#!/usr/bin/env python3
"""V297: never silently reactivate the deprecated V182 periodic writer."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class V182RetirementGate(unittest.TestCase):
    def test_legacy_v182_workflow_remains_deleted(self):
        # The obsolete writer was fully retired. Its absence is a stronger
        # contract than a manual-only trigger that could be re-enabled.
        path = ROOT / ".github/workflows/BOAT_EDGE_V182_SCRATCH_AND_MIDODDS.yml"
        self.assertFalse(path.exists(), "Obsolete V182 writer must not return")

    def test_current_v235_automatic_owner_preserved(self):
        v235 = (ROOT / ".github/workflows/V235.yml").read_text(encoding="utf-8")
        header = v235.split("\npermissions:", 1)[0]
        self.assertIn("  schedule:", header)
        self.assertIn("  workflow_run:", header)
        self.assertIn("  workflow_dispatch:", header)
        self.assertIn("cancel-in-progress: false", v235)

if __name__ == "__main__":
    unittest.main()
