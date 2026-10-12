"""Offline, synthetic-only tests. Does not open any race-result, payout, or network source."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "boat_edge_master_todo_audit.py"
spec = importlib.util.spec_from_file_location("boat_edge_master_todo_audit", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def put(root, path, value):
    dst = root / path
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def safe_fixture(root):
    put(root, "data/formal_status.json", {
        "asOf": "2026-10-12T23:26:00+09:00",
        "formalFirst100": {"races": 0},
        "guards": {"results_seen": False, "unlock": False,
                   "scoring": False, "RESULT_UNLOCK_TOKEN": None}})
    put(root, "data/model_status.json", {"model": "research-only"})
    put(root, "data/site_current_state.json", {"as_of": "2026-10-08"})
    put(root, "data/site_prediction_policy.json", {
        "ticket_policy": {"odds_rank_weight": False},
        "site_reference_120way_full_distribution_ready": False})
    put(root, "data/site_autopilot/v236_score_current.json", {
        "production_model_changed": False, "promotion_authorized": False,
        "scope": "POST_RESULT_SAME_COHORT_COMPARISON_NOT_FORMAL_FRESH"})
    put(root, "data/site_paper_sim/current.json", {
        "mode": "PAPER_ONLY", "money": {"virtual_only": True}})
    (root / "BOAT_EDGE_AUTODEV_TASKS.md").write_text(
        "- [x] A01 | complete\n- [x] A28 | complete\n", encoding="utf-8")


class TodoAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        safe_fixture(self.root)

    def test_locked_and_incomplete_does_not_claim_success(self):
        s = audit.check(self.root)
        self.assertEqual(s["status"], "SAFETY_GUARDS_OBSERVED_NOT_COMPLETION")
        self.assertEqual(s["checks"]["formal_freeze"], "WAITING_0_OF_100")
        self.assertEqual(s["checks"]["site_status_freshness"], "STALE_SITE_SNAPSHOT")
        self.assertEqual(s["checks"]["autodev_task_queue"], "EMPTY")
        self.assertEqual(s["checks"]["site_full_120_distribution"], "NOT_READY")
        self.assertFalse(s["safe_to_claim_complete"])

    def test_formal_unlock_fails_closed(self):
        p = self.root / "data/formal_status.json"
        d = json.loads(p.read_text())
        d["guards"]["unlock"] = True
        put(self.root, "data/formal_status.json", d)
        self.assertEqual(audit.check(self.root)["status"], "SAFETY_BLOCK")

    def test_missing_formal_file_fails_closed(self):
        (self.root / "data/formal_status.json").unlink()
        self.assertEqual(audit.check(self.root)["status"], "SAFETY_BLOCK")

    def test_promotion_guard_must_be_false(self):
        put(self.root, "data/site_autopilot/v236_score_current.json", {
            "production_model_changed": True, "promotion_authorized": True,
            "scope": "POST_RESULT_SAME_COHORT_COMPARISON_NOT_FORMAL_FRESH"})
        self.assertEqual(audit.check(self.root)["status"], "SAFETY_BLOCK")

    def test_paper_only_must_remain_virtual(self):
        put(self.root, "data/site_paper_sim/current.json", {
            "mode": "PAPER_ONLY", "money": {"virtual_only": False}})
        self.assertEqual(audit.check(self.root)["status"], "SAFETY_BLOCK")

    def test_backlog_pending_does_not_claim_agent_operational(self):
        (self.root / "BOAT_EDGE_AUTODEV_TASKS.md").write_text(
            "- [x] A28 | done\n- [ ] A29 | queued\n", encoding="utf-8")
        report = audit.check(self.root)
        self.assertEqual(report["checks"]["autodev_pending_tasks"], ["A29"])
        self.assertEqual(report["checks"]["autodev_task_queue"], "PENDING")
        self.assertFalse(report["safe_to_claim_complete"])


if __name__ == "__main__":
    unittest.main()
