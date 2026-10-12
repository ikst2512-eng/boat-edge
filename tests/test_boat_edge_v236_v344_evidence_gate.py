"""Synthetic-only unified evidence gate regressions, no live results."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v318_shadow_freeze import canonical
from boat_edge_v344_site_research_evidence_gate import check
from test_boat_edge_v236_v340_artifact_integrity import make, KEY
from test_boat_edge_v236_v334_live_batch import prepare, NOW, fake_fetch
from boat_edge_v334_live_batch_runner import run


class V344EvidenceGate(unittest.TestCase):
    def test_distinct_races_across_bundles_pass_without_claiming_complete_history(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ra, rb = Path(a), Path(b)
            first = make(ra)
            prepare(rb, key="20261013-22-11")
            second = run(rb, capture=True, clock=lambda: NOW, fetcher=fake_fetch)
            result = check([{"root": ra, "report": first}, {"root": rb, "report": second}])
            self.assertTrue(result["all_supplied_local_evidence_checks_passed"])
            self.assertEqual(result["distinct_frozen_races_in_supplied_reports"], 2)
            self.assertFalse(result["complete_actions_history_or_global_uniqueness_attested"])

    def test_valid_but_changed_same_race_input_reports_divergent_freezes(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ra, rb = Path(a), Path(b)
            first = make(ra)
            prepare(rb)
            card = rb / f"data/races/{KEY}.json"
            obj = json.loads(card.read_bytes())
            obj["racers"][0]["national"]["win_rate"] = 1.5
            card.write_text(json.dumps(obj))
            second = run(rb, capture=True, clock=lambda: NOW, fetcher=fake_fetch)
            result = check([{"root": ra, "report": first}, {"root": rb, "report": second}])
            self.assertEqual(result["status"], "DIVERGENT_REPEATED_FREEZES")
            self.assertFalse(result["all_supplied_local_evidence_checks_passed"])
            self.assertEqual(result["rejected"], [])

    def test_all_three_checks_pass_without_formal_or_current_card_reads(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = make(root)
            (root / f"data/races/{KEY}.json").unlink()
            result = check([{"root": root, "report": report}])
            self.assertTrue(result["all_supplied_local_evidence_checks_passed"])
            self.assertEqual(result["status"], "LOCAL_EVIDENCE_CHECKS_PASSED_NOT_FORMAL")
            self.assertFalse(result["scoring_authorized"])
            self.assertFalse(result["accuracy_improvement_proven"])
            self.assertFalse(result["complete_actions_history_or_global_uniqueness_attested"])

    def test_same_race_even_identical_bytes_cannot_inflate_unique_cohort(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ra, rb = Path(a), Path(b)
            result = check([{"root": ra, "report": make(ra)}, {"root": rb, "report": make(rb)}])
            self.assertFalse(result["all_supplied_local_evidence_checks_passed"])
            self.assertEqual(result["completed_attempts"], 2)
            self.assertEqual(result["distinct_frozen_races_in_supplied_reports"], 1)
            self.assertEqual(result["status"], "REPEATED_RACES_NOT_UNIQUE")

    def test_raw_html_tamper_fails_even_if_candidate_replay_still_passes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = make(root)
            path = root / f"data/source_captures/20261013/{KEY}/boaters.html"
            path.write_bytes(path.read_bytes() + b"modified")
            result = check([{"root": root, "report": report}])
            self.assertFalse(result["all_supplied_local_evidence_checks_passed"])
            self.assertTrue(result["bundle_checks"][0]["candidate_replay"][
                "candidate_replay_verified_within_supplied_report"])
            self.assertEqual(result["rejected"][0]["stage"], "SOURCE_BYTES")

    def test_ticket_edit_with_new_hashes_fails_even_if_v340_bytes_consistent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = make(root)
            path = root / report["completed"][0]["path"]
            frozen = json.loads(path.read_bytes())
            tickets = frozen["candidate"]["modes"]["national_only"]["top10_boat_research_only"]
            tickets[0], tickets[1] = tickets[1], tickets[0]
            frozen["candidate_sha256"] = hashlib.sha256(canonical(frozen["candidate"])).hexdigest()
            raw = canonical(frozen) + b"\n"
            path.write_bytes(raw)
            report["completed"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
            result = check([{"root": root, "report": report}])
            self.assertTrue(result["bundle_checks"][0]["source_bytes"][
                "all_reported_artifacts_locally_consistent"])
            self.assertFalse(result["all_supplied_local_evidence_checks_passed"])
            self.assertIn("CANDIDATE_INPUT_REPLAY_MISMATCH", result["rejected"][0]["reason"])

    def test_missing_input_snapshot_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = make(root)
            (root / f"data/source_captures/20261013/{KEY}/race_input.json").unlink()
            result = check([{"root": root, "report": report}])
            self.assertFalse(result["all_supplied_local_evidence_checks_passed"])
            self.assertEqual(result["rejected"][0]["stage"], "CANDIDATE_REPLAY")

    def test_unreported_selected_race_rejected_before_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            report = make(Path(d))
            report["window"]["candidates"].append({"race_key": "20261013-22-11"})
            report["window"]["coverage"]["selected"] = 2
            with self.assertRaisesRegex(ValueError, "UNACCOUNTED_SELECTED_RACES"):
                check([{"root": "/missing", "report": report}])

    def test_declared_capture_failure_prevents_complete_batch_claim(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = make(root)
            report["window"]["candidates"].append({"race_key": "20261013-22-11"})
            report["window"]["coverage"]["selected"] = 2
            report["failures"].append({"race_key": "20261013-22-11", "reason": "SOURCE_NOT_READY"})
            result = check([{"root": root, "report": report}])
            self.assertFalse(result["all_supplied_local_evidence_checks_passed"])
            self.assertEqual(result["reported_capture_failures"], 1)

    def test_all_report_validation_happens_before_first_artifact_access(self):
        with tempfile.TemporaryDirectory() as d:
            report = make(Path(d))
            bad = copy.deepcopy(report)
            bad["formal_fresh_read"] = True
            with self.assertRaisesRegex(ValueError, "RESEARCH_ONLY_RUN_FLAGS"):
                check([{"root": "/missing", "report": report}, {"root": "/missing", "report": bad}])
            bad = copy.deepcopy(report)
            bad["window"]["date"] = "20261001"
            with self.assertRaisesRegex(ValueError, "NONFORMAL_DATE"):
                check([{"root": "/missing", "report": bad}])

    def test_cli_zero_freezes_exits_nonzero_without_false_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = make(root)
            report["completed"] = []
            report["completed_count"] = 0
            report["failures"] = [{"race_key": KEY, "reason": "CAPTURE_FAILED"}]
            path = root / "run.json"
            path.write_text(json.dumps(report))
            script = Path(__file__).resolve().parents[1] / "scripts/boat_edge_v344_site_research_evidence_gate.py"
            result = subprocess.run([sys.executable, str(script), "--bundle", str(root), str(path)],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(json.loads(result.stdout)["all_supplied_local_evidence_checks_passed"])

    def test_cli_valid_bundle_exits_zero_with_local_only_claim(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "run.json"
            path.write_text(json.dumps(make(root)))
            script = Path(__file__).resolve().parents[1] / "scripts/boat_edge_v344_site_research_evidence_gate.py"
            result = subprocess.run([sys.executable, str(script), "--bundle", str(root), str(path)],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["all_supplied_local_evidence_checks_passed"])
            self.assertFalse(json.loads(result.stdout)["accuracy_improvement_proven"])

    def test_unverified_global_immutability_claim_rejected_before_reads(self):
        with tempfile.TemporaryDirectory() as d:
            report = make(Path(d))
            report["immutable_across_independent_actions_runs_verified"] = True
            with self.assertRaisesRegex(ValueError, "NO_UNVERIFIED_GLOBAL_IMMUTABILITY_CLAIM"):
                check([{"root": "/missing", "report": report}])


if __name__ == "__main__":
    unittest.main()
