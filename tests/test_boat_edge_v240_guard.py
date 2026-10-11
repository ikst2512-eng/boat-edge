import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import boat_edge_v240_guard as guard


class TestV240Guard(unittest.TestCase):
    def test_picks_only_first_pending(self):
        q = "- [x] A00 | done\n- [ ] A01 | missing label\n- [ ] A02 | next\n"
        self.assertEqual(guard.first_pending(q), ("A01", "missing label"))

    def test_exactly_one_checkbox_can_change(self):
        q = "- [ ] A01 | missing label\n- [ ] A02 | next\n"
        good = "- [x] A01 | missing label\n- [ ] A02 | next\n"
        self.assertTrue(guard.completed_once(q, good))
        self.assertFalse(guard.completed_once(q, good.replace("A02", "A22")))
        self.assertFalse(guard.completed_once(q, q))

    def test_never_allow_data_formal_workflow_or_model(self):
        for path in (
            ".github/workflows/V235.yml", "data/formal_status.json",
            "data/site_results/abc.json", "scripts/site_final_history_v133.py",
            "scripts/boat_edge_v240_guard.py", "tests/test_boat_edge_v240_guard.py",
        ):
            self.assertFalse(guard.permitted_ui(path))
        for path in ("index.html", "health.html", "assets/boat_edge_v203_readable.js"):
            self.assertTrue(guard.permitted_ui(path))

    def test_reject_code_exfil_patterns(self):
        text = " ".join(guard.PROHIBITED_ADDITIONS)
        self.assertIn("data/formal_", text)
        self.assertIn("RESULT_UNLOCK_TOKEN", text)


if __name__ == "__main__":
    unittest.main()
