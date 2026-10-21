"""Regression tests for the read-only Actions completion graph."""
import tempfile
import unittest
from pathlib import Path
from scripts.boat_edge_actions_topology_guard import inventory


class ActionsTopologyTests(unittest.TestCase):
    def test_fanout_and_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.yml").write_text("name: A\non:\n  workflow_run:\n    workflows:\n      - 'C'\n    types: [completed]\n")
            (root / "b.yml").write_text("name: B\non:\n  workflow_run:\n    workflows:\n      - 'A'\n    types: [completed]\n")
            (root / "c.yml").write_text("name: C\non:\n  workflow_run:\n    workflows:\n      - 'A'\n    types: [completed]\n")
            report = inventory(root)
            self.assertIn("A", report["multiple_completion_consumers"])
            self.assertTrue(report["completion_cycles"])
            self.assertFalse(report["unknown_producers"])

    def test_acyclic_and_unknown_producer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.yml").write_text("name: A\non:\n  schedule:\n    - cron: '* * * * *'\n")
            (root / "b.yml").write_text("name: B\non:\n  workflow_run:\n    workflows:\n      - 'A'\n      - 'External'\n    types: [completed]\n")
            report = inventory(root)
            self.assertFalse(report["completion_cycles"])
            self.assertEqual(report["unknown_producers"], ["External"])
            self.assertEqual(report["completion_edges"], 2)


if __name__ == "__main__":
    unittest.main()
