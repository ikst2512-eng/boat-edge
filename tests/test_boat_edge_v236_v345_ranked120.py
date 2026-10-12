"""V345 full 120-way predeadline research freeze, synthetic-only regressions."""
from datetime import timedelta
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v318_shadow_freeze import canonical
from boat_edge_v332_live_local_freeze import candidate_from_raw, live_local_freeze
from boat_edge_v343_race_input_replay import verify
from boat_edge_v345_research_ranked120 import MODEL, MODES, derive_120
from test_boat_edge_v236_v332_live_local_e2e import (
    KEY, PRE, LATE, mock_page, prepare,
)
from test_boat_edge_v236_v339_cross_run_audit import report


def fixture(root):
    prepare(root)
    freeze = live_local_freeze(root, KEY, capture=True,
                               fetcher=mock_page, clock=lambda: PRE)
    report_doc = report(digest=freeze["sha256"])
    frozen_path = root / freeze["path"]
    input_path = (root / "data/source_captures" / KEY[:8] / KEY / "race_input.json")
    return report_doc, frozen_path, input_path


def resign(frozen_path, report_doc, data):
    raw = canonical(data) + b"\n"
    frozen_path.write_bytes(raw)
    report_doc["completed"][0]["sha256"] = hashlib.sha256(raw).hexdigest()


class V345Ranked120(unittest.TestCase):
    def test_three_full_boat_rankings_match_saved_top10_and_head_mass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rep, frozen_path, original = fixture(root)
            frozen = json.loads(frozen_path.read_bytes())
            self.assertEqual(frozen["research_ranked_120_schema"], MODEL)
            self.assertEqual(set(frozen["research_ranked_120_by_mode"]), set(MODES))
            for name in MODES:
                rows = frozen["research_ranked_120_by_mode"][name]
                cand = frozen["candidate"]["modes"][name]
                self.assertEqual(len(rows), 120)
                self.assertEqual([row["rank"] for row in rows], list(range(1, 121)))
                self.assertEqual(len({row["boat_combo"] for row in rows}), 120)
                self.assertEqual(len({row["course_combo"] for row in rows}), 120)
                self.assertEqual([x["boat_combo"] for x in rows[:10]],
                                 cand["top10_boat_research_only"])
                self.assertEqual([x["course_combo"] for x in rows[:10]], cand["top10"])
                self.assertAlmostEqual(sum(x["relative_model_mass"] for x in rows), 1)
                self.assertTrue(all(rows[i]["relative_model_mass"] >=
                                    rows[i + 1]["relative_model_mass"]
                                    for i in range(119)))
                for boat in range(1, 7):
                    weight = sum(x["relative_model_mass"] for x in rows
                                 if x["boat_combo"].startswith(f"{boat}-"))
                    self.assertAlmostEqual(
                        weight, cand["head_mass_boat_research_only"][str(boat)])
            # 1 and 2 swap provisional courses; tickets remain BOAT numbers.
            self.assertNotEqual(
                frozen["research_ranked_120_by_mode"]["national_only"][0]["boat_combo"],
                frozen["research_ranked_120_by_mode"]["national_only"][0]["course_combo"])
            self.assertEqual(
                frozen["frozen_at_jst"], PRE.isoformat(timespec="microseconds"))
            self.assertEqual(original.read_bytes(),
                             (root / "data/races" / (KEY + ".json")).read_bytes())
            self.assertEqual(verify(root, rep)["saved_full_120_verified_count"], 1)

    def test_offline_replay_needs_no_live_race_card_results_or_network(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rep, frozen_path, _ = fixture(root)
            (root / "data/races" / (KEY + ".json")).unlink()
            (root / "data/formal_status.json").write_text("MUST_NOT_READ")
            result = verify(root, rep)
            self.assertTrue(result["all_supplied_full_120_verified"])
            self.assertTrue(result["rows"][0][
                "saved_full_120_top10_and_head_parity_verified"])
            self.assertFalse(result["results_read"])
            self.assertFalse(result["eligible_for_formal_fresh_scoring"])
            self.assertFalse(result["production_model_changed"])
            self.assertFalse(result["wagers_authorized"])

    def test_edit_full120_even_after_rehash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rep, frozen_path, _ = fixture(root)
            obj = json.loads(frozen_path.read_bytes())
            obj["research_ranked_120_by_mode"]["national_motor"][0][
                "relative_model_mass"] += 0.01
            resign(frozen_path, rep, obj)
            with self.assertRaisesRegex(ValueError, "RESEARCH_120_SAVED_REPLAY_MISMATCH"):
                verify(root, rep)

    def test_swapped_rank_rows_even_after_rehash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rep, frozen_path, _ = fixture(root)
            obj = json.loads(frozen_path.read_bytes())
            rows = obj["research_ranked_120_by_mode"]["national_only"]
            rows[0], rows[1] = rows[1], rows[0]
            resign(frozen_path, rep, obj)
            with self.assertRaisesRegex(ValueError, "RESEARCH_120_SAVED_REPLAY_MISMATCH"):
                verify(root, rep)

    def test_missing_one_mode_or_schema_marker_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rep, frozen_path, _ = fixture(root)
            obj = json.loads(frozen_path.read_bytes())
            del obj["research_ranked_120_by_mode"]["national_motor_st"]
            resign(frozen_path, rep, obj)
            with self.assertRaisesRegex(ValueError, "RESEARCH_120_SAVED_SCHEMA_INVALID"):
                verify(root, rep)

    def test_legacy_top10_only_record_never_mislabelled_full120(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rep, frozen_path, _ = fixture(root)
            obj = json.loads(frozen_path.read_bytes())
            del obj["research_ranked_120_by_mode"]
            del obj["research_ranked_120_schema"]
            resign(frozen_path, rep, obj)
            result = verify(root, rep)
            self.assertEqual(result["saved_full_120_verified_count"], 0)
            self.assertFalse(result["all_supplied_full_120_verified"])
            self.assertTrue(result["candidate_replay_verified_within_supplied_report"])

    def test_candidate_top10_and_head_mismatch_fail_without_writing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            raw = (root / "data/races" / (KEY + ".json")).read_bytes()
            candidate, deadline, race = candidate_from_raw(raw, KEY, PRE)
            bad = copy.deepcopy(candidate)
            top = bad["modes"]["national_only"]["top10_boat_research_only"]
            top[0], top[1] = top[1], top[0]
            with self.assertRaisesRegex(ValueError, "TOP10_PARITY"):
                derive_120(race, bad)
            bad = copy.deepcopy(candidate)
            bad["modes"]["national_motor"]["head_mass_boat_research_only"]["1"] = 0
            with self.assertRaisesRegex(ValueError, "HEAD_MASS_PARITY"):
                derive_120(race, bad)
            self.assertFalse((root / "data/research_local_v332").exists())

    def test_postdeadline_capture_forbidden_and_formal_target_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            with self.assertRaisesRegex(ValueError, "LIVE_WINDOW_CLOSED"):
                live_local_freeze(root, KEY, capture=True,
                                  fetcher=lambda _: self.fail("NO_NETWORK_AFTER_DEADLINE"),
                                  clock=lambda: LATE)
            self.assertFalse((root / "data/research_local_v332").exists())
            with self.assertRaisesRegex(ValueError, "FORMAL_FRESH_TARGET_EXCLUDED"):
                live_local_freeze(root, "20261001-22-12",
                                  clock=lambda: PRE)

    def test_immutable_single_freeze_no_rank_rewrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rep, frozen_path, _ = fixture(root)
            original = frozen_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "ALREADY_EXISTS"):
                live_local_freeze(root, KEY, clock=lambda: PRE)
            self.assertEqual(original, frozen_path.read_bytes())
            self.assertTrue(verify(root, rep)["all_supplied_full_120_verified"])

    def test_read_only_repeated_full120_replay_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rep, frozen_path, _ = fixture(root)
            source = frozen_path.read_bytes()
            first = canonical(verify(root, rep))
            second = canonical(verify(root, rep))
            self.assertEqual(first, second)
            self.assertEqual(frozen_path.read_bytes(), source)


if __name__ == "__main__":
    unittest.main()
