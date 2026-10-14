"""Fixture-only V229 first Git-add => real published Pages TopK acceptance."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import boat_edge_01_live_final_browser_acceptance as gate

KEY = "20261014-15-10"
SHA = "a" * 40
PFX = "data/site_autopilot/v229_evidence/"
SNAP = "data/site_prediction_snapshots/" + KEY + ".json"
AUDIT = "data/site_prediction_audit/" + KEY + ".json"
EVIDENCE = PFX + KEY + ".json"
FIRST = "2026-10-14T10:29:00+00:00"


class LiveFinalProof(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        combos = ["1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2",
                  "1-3-4", "1-3-5", "1-3-6", "1-4-2", "1-4-3"]
        self.snapshot = {
            "race_key": KEY, "snapshot_window": "FINAL_15M",
            "prediction_kind": "SITE_REFERENCE_V122",
            "first_saved_at": FIRST, "saved_at": FIRST,
            "deadline": "19:36",
            "guards": {"results_seen": False, "unlock": False, "scoring": False},
            "modes": {"hit": {"tickets": [{"combo": x} for x in combos]}},
        }
        self.write(SNAP, self.snapshot)
        self.digest = hashlib.sha256((self.root / SNAP).read_bytes()).hexdigest()
        self.proof = {
            "schema": "BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1",
            "scope": "SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS",
            "new_snapshot_created_this_run": True, "race_key": KEY,
            "snapshot_sha256": self.digest, "snapshot_saved_at": FIRST,
            "results_seen": False, "formal_fresh_unlock": False,
            "scoring": False,
        }
        self.audit = {"race_key": KEY, "pass": True,
                      "latest_snapshot_sha256": self.digest}
        self.formal = {"guards": {
            "results_seen": False, "unlock": False,
            "scoring": False, "RESULT_UNLOCK_TOKEN": None},
            "formalFirst100": {"races": 0}}
        self.write(EVIDENCE, self.proof)
        self.write(AUDIT, self.audit)
        self.write("data/formal_status.json", self.formal)
        self.added = [EVIDENCE, SNAP, AUDIT]
        self.commit_time = "2026-10-14T10:30:00+00:00"

    def write(self, name, obj):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")

    def fake_git(self, repo, *args):
        if args[:2] == ("rev-parse", "HEAD"):
            return SHA
        if args[0] == "diff-tree":
            return "\n".join(self.added)
        if args[0] == "log":
            return self.commit_time
        raise AssertionError("Unexpected Git access")

    def checked(self, event="push"):
        with patch.object(gate, "git", side_effect=self.fake_git):
            return gate.new_site_final(self.root, event, SHA)

    def test_atomic_add_predeadline_yes(self):
        self.assertEqual(self.checked(), [KEY])

    def test_other_event_or_no_new_evidence_does_not_run_browser(self):
        self.assertEqual(self.checked("schedule"), [])
        self.added = [SNAP, AUDIT]
        self.assertEqual(self.checked(), [])

    def test_not_first_git_add_rejected(self):
        self.added = [EVIDENCE, AUDIT]
        with self.assertRaisesRegex(gate.GateError, "NOT_ATOMIC_FIRST_GIT_ADD"):
            self.checked()

    def test_commit_time_must_be_before_race_deadline(self):
        self.commit_time = "2026-10-14T10:37:00+00:00"
        with self.assertRaisesRegex(gate.GateError, "FIRST_GIT_ADD_NOT_BEFORE"):
            self.checked()

    def test_snapshot_and_audit_hash_tamper_fail_closed(self):
        self.audit["latest_snapshot_sha256"] = "0" * 64
        self.write(AUDIT, self.audit)
        with self.assertRaisesRegex(gate.GateError, "INVALID_ATOMIC"):
            self.checked()
        self.audit["latest_snapshot_sha256"] = self.digest
        self.write(AUDIT, self.audit)
        self.snapshot["modes"]["hit"]["tickets"][0]["combo"] = "2-3-4"
        self.write(SNAP, self.snapshot)
        with self.assertRaisesRegex(gate.GateError, "INVALID_ATOMIC"):
            self.checked()

    def test_formal_closed_gate_required(self):
        self.formal["guards"]["unlock"] = True
        self.write("data/formal_status.json", self.formal)
        with self.assertRaisesRegex(gate.GateError, "FORMAL_FRESH_NOT_CLOSED"):
            self.checked()

    def test_saved_top10_required(self):
        self.snapshot["modes"]["hit"]["tickets"] = []
        self.write(SNAP, self.snapshot)
        self.digest = hashlib.sha256((self.root / SNAP).read_bytes()).hexdigest()
        self.audit["latest_snapshot_sha256"] = self.digest
        self.proof["snapshot_sha256"] = self.digest
        self.write(EVIDENCE, self.proof)
        self.write(AUDIT, self.audit)
        with self.assertRaisesRegex(gate.GateError, "SAVED_TOP10_NOT_VERIFIED"):
            self.checked()

    def test_browser_report_real_saved_final_not_merely_navigation(self):
        good = {
            "browser": "webkit", "target": gate.PAGES,
            "live_topk": {
                "status": gate.CERTIFIED, "race": KEY,
                "verified_site_final": True,
                "displayed_matches_saved_selected_mode": True,
                "saved_prediction": {"first_git_commit_verified": False},
            },
            "physical_iphone_safari_verified": False,
            "result_requests_allowed": 0,
            "formal_fresh_modified": False, "page_errors": [],
        }
        logfile = self.root / "browser.log"
        logfile.write_text("trace\nBOAT_EDGE_03_REAL_BROWSER_PASS " + json.dumps(good))
        self.assertEqual(gate.verify_browser_log(logfile, "webkit")["race"], KEY)
        good["live_topk"]["status"] = "NOT_CERTIFIED_ALL_ELIGIBLE_SOURCE_STOPPED"
        logfile.write_text("BOAT_EDGE_03_REAL_BROWSER_PASS " + json.dumps(good))
        with self.assertRaisesRegex(gate.GateError, "NOT_CERTIFIED"):
            gate.verify_browser_log(logfile, "webkit")

    def test_browser_incorrect_race_or_fake_physical_safari_rejected(self):
        bad = {"browser": "chromium", "target": gate.PAGES,
               "live_topk": {"status": gate.CERTIFIED, "race": KEY,
                             "verified_site_final": True,
                             "displayed_matches_saved_selected_mode": True,
                             "saved_prediction": {"first_git_commit_verified": False}},
               "physical_iphone_safari_verified": True,
               "result_requests_allowed": 0, "formal_fresh_modified": False,
               "page_errors": []}
        p = self.root / "log"
        p.write_text("BOAT_EDGE_03_REAL_BROWSER_PASS " + json.dumps(bad))
        with self.assertRaisesRegex(gate.GateError, "NOT_CERTIFIED"):
            gate.verify_browser_log(p, "chromium")


if __name__ == "__main__":
    unittest.main()
