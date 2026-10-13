"""V368 source-only cohort verification tests: exact declared keys and dual replay."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v318_shadow_freeze import canonical
from boat_edge_v368_source_only_cohort_audit import (
    audit, validate_index, INDEX,
)
from test_boat_edge_v236_v367_source_only_replay import saved
from test_boat_edge_v236_v364_v230_v336_selection_contract import KEY


def index_for(*pairs):
    return {
        "schema": INDEX,
        "source_capture_only": True,
        "no_result_inputs": True,
        "no_formal_fresh": True,
        "no_model_promotion": True,
        "expected": [
            {"race_key": key, "manifest_sha256": digest}
            for key, digest in pairs
        ],
        "declared_expected_count": len(pairs),
    }


class V368ExplicitCohort(unittest.TestCase):
    def test_valid_index_passes_even_after_mutable_site_files_are_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, frozen = saved(root)
            record = index_for((KEY, frozen["manifest_sha256"]))
            paths = [
                root / "data/today.json",
                root / "data/races" / (KEY + ".json"),
                root / "data/site_prediction_snapshots" / (KEY + ".json"),
            ]
            for path in paths:
                path.unlink()
            run1, run2 = audit(root, record), audit(root, record)
            self.assertEqual(canonical(run1), canonical(run2))
            self.assertEqual(run1["status"],
                             "ALL_DECLARED_LOCAL_SOURCE_ARCHIVES_REPLAYED_NOT_FORMAL")
            self.assertEqual(run1["expected_count"], 1)
            self.assertEqual(run1["replayed_count"], 1)
            self.assertEqual(run1["rejected_count"], 0)
            self.assertEqual(run1["accepted"][0]["race_key"], KEY)
            self.assertTrue(run1["accepted"][0]["two_independent_replay_outputs_byte_identical"])
            self.assertEqual(run1["replay_report_digest_sha256"],
                             hashlib.sha256(canonical(run1["accepted"])).hexdigest())
            self.assertTrue(run1["all_declared_sources_locally_verified"])
            for k in ("cross_run_first_seen_or_server_time_verified",
                      "external_source_authenticity_verified",
                      "boaters_and_kyoteibiyori_original_exhibition_verified",
                      "v336_research_freeze_proven",
                      "research_full_3x120_rankings_verified",
                      "results_read", "formal_fresh_read",
                      "accuracy_improvement_proven", "production_model_changed",
                      "writes_performed"):
                self.assertFalse(run1[k])
            self.assertFalse(any(p.exists() for p in paths))

    def test_expected_but_missing_second_archive_fails_whole_cohort(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, frozen = saved(root)
            missing = "20261013-22-11"
            manifest = index_for((missing, "0"*64), (KEY, frozen["manifest_sha256"]))
            report = audit(root, manifest)
            self.assertEqual(report["expected_count"], 2)
            self.assertEqual(report["replayed_count"], 1)
            self.assertEqual(report["rejected_count"], 1)
            self.assertFalse(report["all_declared_sources_locally_verified"])
            self.assertEqual(report["rejected"][0]["race_key"], missing)
            self.assertIn("ARCHIVE_MISSING", report["rejected"][0]["reason"])
            self.assertFalse(report["v336_research_freeze_proven"])

    def test_bad_independent_sha_is_not_silent_empty_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            saved(root)
            report = audit(root, index_for((KEY, "a"*64)))
            self.assertEqual(report["expected_count"], 1)
            self.assertEqual(report["replayed_count"], 0)
            self.assertFalse(report["all_declared_sources_locally_verified"])
            self.assertIn("EXPECTED_MANIFEST_SHA_MISMATCH", report["rejected"][0]["reason"])

    def test_archived_html_corrupted_only_one_race_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, frozen = saved(root)
            target = folder / "racelist.html"
            target.write_bytes(target.read_bytes() + b"tampered")
            report = audit(root, index_for((KEY, frozen["manifest_sha256"])))
            self.assertFalse(report["all_declared_sources_locally_verified"])
            self.assertIn("SOURCE_BYTES_SHA_MISMATCH", report["rejected"][0]["reason"])

    def test_duplicate_and_out_of_order_keys_rejected_before_any_archive_read(self):
        k2 = "20261013-22-11"
        for rows, reason in (
            ([(KEY, "a"*64), (KEY, "a"*64)], "DUPLICATE_COHORT"),
            ([(KEY, "a"*64), (k2, "a"*64)], "ORDER_MUST_BE_CANONICAL"),
        ):
            with self.subTest(reason=reason), patch(
                "boat_edge_v368_source_only_cohort_audit.replay_one",
                side_effect=AssertionError("NO_ARCHIVE_READ_FOR_UNTRUSTED_INDEX")
            ):
                with self.assertRaisesRegex(ValueError, reason):
                    audit(Path("/not-used"), index_for(*rows))

    def test_formal_october_first_rejected_before_any_archive_read(self):
        with patch("boat_edge_v368_source_only_cohort_audit.replay_one",
                   side_effect=AssertionError("FORMAL_READ_FORBIDDEN")):
            with self.assertRaisesRegex(ValueError, "INVALID_OR_FORMAL"):
                audit(Path("/unused"), index_for(("20261001-22-12", "a"*64)))

    def test_empty_wrong_counts_wrong_sha_extra_paths_and_claims_rejected(self):
        cases = [
            (index_for(), "EXPECTED_RACE_COUNT"),
            ({**index_for((KEY, "a"*64)), "declared_expected_count": 2}, "EXPECTED_RACE_COUNT"),
            (index_for((KEY, "NOT_A_SHA")), "MANIFEST_SHA_REQUIRED"),
            ({**index_for((KEY, "a"*64)), "result_path": "data/results/..."}, "RESEARCH_ONLY_INDEX"),
            ({**index_for((KEY, "a"*64)), "no_result_inputs": False}, "RESEARCH_ONLY_INDEX"),
            ({**index_for((KEY, "a"*64)), "no_formal_fresh": False}, "RESEARCH_ONLY_INDEX"),
            ({**index_for((KEY, "a"*64)), "no_model_promotion": False}, "RESEARCH_ONLY_INDEX"),
            ({**index_for((KEY, "a"*64)), "expected": [{
                "race_key": KEY, "manifest_sha256": "a"*64, "path": "data/results",
            }]}, "NO_IMPLICIT_PATH"),
        ]
        for item, err in cases:
            with self.subTest(error=err), patch(
                "boat_edge_v368_source_only_cohort_audit.replay_one",
                side_effect=AssertionError("SHOULD_NOT_READ")
            ):
                with self.assertRaisesRegex(ValueError, err):
                    validate_index(item)

    def test_v367_unverified_claim_and_double_run_output_drift_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, frozen = saved(root)
            original = index_for((KEY, frozen["manifest_sha256"]))
            from boat_edge_v367_source_only_replay import replay_one as real
            correct = real(root, KEY, frozen["manifest_sha256"])
            for variant in (
                dict(correct, writes_performed=True),
                dict(correct, live_race_freeze_proven=True),
                dict(correct, status="FAKE_PASS"),
            ):
                with self.subTest(variant=variant), patch(
                    "boat_edge_v368_source_only_cohort_audit.replay_one", return_value=variant
                ):
                    result = audit(root, original)
                    self.assertEqual(result["replayed_count"], 0)
                    self.assertFalse(result["all_declared_sources_locally_verified"])
                    self.assertIn("UNVERIFIED_REPLAY_PASS_CLAIM", result["rejected"][0]["reason"])
            changed = dict(correct, replayed_fictitious=True)
            with patch("boat_edge_v368_source_only_cohort_audit.replay_one",
                       side_effect=[correct, changed]):
                result = audit(root, original)
                self.assertEqual(result["replayed_count"], 0)
                self.assertIn("REPLAY_OUTPUTS_DIVERGED", result["rejected"][0]["reason"])

    def test_no_path_discovery_or_external_git_network_is_needed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, frozen = saved(root)
            (root / "data/formal_status.json").write_text("DO_NOT_READ_FORMAL_STATE")
            report = audit(root, index_for((KEY, frozen["manifest_sha256"])))
            self.assertTrue(report["all_declared_sources_locally_verified"])
            self.assertFalse(report["formal_fresh_read"])
            self.assertFalse(report["results_read"])


if __name__ == "__main__":
    unittest.main()
