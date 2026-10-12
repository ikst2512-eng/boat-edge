#!/usr/bin/env python3
"""V297: never silently reactivate the deprecated V182 periodic writer."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class V182RetirementGate(unittest.TestCase):
    def test_legacy_v182_has_manual_trigger_only(self):
        text = (ROOT / ".github/workflows/BOAT_EDGE_V182_SCRATCH_AND_MIDODDS.yml").read_text(encoding="utf-8")
        header = text.split("\npermissions:", 1)[0]
        self.assertEqual(header.count("  workflow_dispatch:"), 1)
        for trigger in ("  schedule:", "    - cron:", "  push:", "  workflow_run:"):
            self.assertNotIn(trigger, header)
        self.assertIn("  fix-ui-and-audit:", text)
        self.assertIn("boat-edge-v182-urgent-scratch-safety", text)
        self.assertIn("if github.ref == 'refs/heads/main'", text)
    def test_current_v235_automatic_owner_preserved(self):
        v235 = (ROOT / ".github/workflows/V235.yml").read_text(encoding="utf-8")
        header = v235.split("\npermissions:", 1)[0]
        self.assertIn("  schedule:", header)
        self.assertIn("  workflow_run:", header)
        self.assertIn("  workflow_dispatch:", header)
        self.assertIn("cancel-in-progress: false", v235)

if __name__ == "__main__":
    unittest.main()
