"""Prevent V229's historical source-pin outage before a PR reaches main.

Live V229 once failed with V229_PIN_DRIFT_REFUSE_DEPLOY before running its
pre-result freeze. These tests inspect tracked Git blobs and workflow source
only. No source data, race outcomes, payouts or formal targets are opened.
"""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
V229 = ROOT / ".github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml"
PINNED = {
    "scripts/site_final_history_v133.py",
    "scripts/boat_edge_v228_freeze_only.py",
    "scripts/boat_edge_v229_atomic_freeze.py",
    "tests/test_boat_edge_v229_atomic_freeze.py",
}


def source_pins(workflow):
    block = re.search(r"(?ms)^\s*expected = \{\n(.*?)^\s*\}", workflow)
    if block is None:
        raise AssertionError("V229_EXPECTED_GIT_BLOB_MAP_MISSING")
    rows = re.findall(
        r"'((?:scripts|tests)/[^']+)': '([0-9a-f]{40})'",
        block.group(1),
    )
    if len(rows) != len({name for name, _ in rows}):
        raise AssertionError("V229_DUPLICATE_SOURCE_PIN")
    return dict(rows)


class V229PreMergePinGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = V229.read_text(encoding="utf-8")
        cls.pins = source_pins(cls.workflow)

    def test_exact_live_source_blobs_are_pinned_before_merge(self):
        self.assertEqual(set(self.pins), PINNED)
        for filename, expected in self.pins.items():
            with self.subTest(filename=filename):
                path = ROOT / filename
                self.assertTrue(path.is_file() and not path.is_symlink())
                actual = subprocess.check_output(
                    ["git", "hash-object", "--", filename],
                    cwd=ROOT, text=True,
                ).strip()
                self.assertEqual(actual, expected, "V229_PIN_DRIFT_PREMERGE_" + filename)

    def test_model_source_chain_matches_v228_constant(self):
        model = (ROOT / "scripts/boat_edge_v228_freeze_only.py").read_text(encoding="utf-8")
        match = re.search(
            r'(?m)^MODEL_SHA\s*=\s*[\'"]([0-9a-f]{40})[\'"]\s*$',
            model,
        )
        self.assertIsNotNone(match)
        self.assertEqual(
            match.group(1), self.pins["scripts/site_final_history_v133.py"],
        )

    def test_no_old_installer_and_valid_pre_result_entrypoints(self):
        source = self.workflow
        self.assertNotIn("PY_V229_INSTALL", source)
        self.assertNotIn("gzip.decompress", source)
        self.assertIn("V229_TRACKED_SOURCE_PIN_DRIFT_", source)
        self.assertIn("V229_TRACKED_SOURCE_PINS_PASS", source)
        self.assertIn("scripts/boat_edge_v229_atomic_freeze.py", source)
        self.assertIn("data/site_prediction_snapshots/", source)
        self.assertIn("data/site_prediction_audit/", source)
        self.assertIn("data/site_autopilot/v229_evidence/", source)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", source)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", source)
        self.assertIn("  schedule:", source)
        self.assertIn("  workflow_run:", source)


if __name__ == "__main__":
    unittest.main()
