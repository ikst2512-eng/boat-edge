"""V335 strictly user-supplied SITE outcomes and protected paired calculations."""
from datetime import datetime
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from boat_edge_v318_shadow_freeze import canonical
from boat_edge_v335_site_paired_outcomes import (
    SCOPE, _two_sided_sign_pvalue, evaluate, score_one, summarize,
)

KEY = "20261013-22-12"
DEADLINE = "2026-10-13T16:40:00+09:00"
CANDIDATE = [
    "1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2",
    "1-3-4", "1-3-5", "1-3-6", "1-4-2", "1-4-3",
]
BASELINE = [
    "2-1-3", "2-1-4", "2-1-5", "2-1-6", "2-3-1",
    "2-3-4", "2-3-5", "2-3-6", "2-4-1", "2-4-3",
]


def inputs():
    heads_a = {"1": .50, "2": .20, "3": .10, "4": .10, "5": .05, "6": .05}
    heads_b = {"1": .20, "2": .50, "3": .10, "4": .10, "5": .05, "6": .05}
    candidate = {
        "race_key": KEY,
        "entry_basis": "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL",
        "race_source_sha256": "a" * 64,
        "scoring_authorized": False, "improvement_proven": False,
        "production_eligible": False,
        "modes": {
            "national_motor_st": {
                "top10_boat_research_only": list(CANDIDATE),
                "head_mass_boat_research_only": heads_a,
            },
            "national_only": {
                "top10_boat_research_only": list(BASELINE),
                "head_mass_boat_research_only": heads_b,
            },
        },
    }
    receipts = {provider: {"sha256": (code * 64)}
                for provider, code in [("official", "a"), ("boaters", "b"),
                                       ("kyoteibiyori", "c")]}
    freeze = {
        "model_id": "BOAT_EDGE_V332_LIVE_LOCAL_SHA_RESEARCH_ONLY",
        "race_key": KEY, "deadline_jst": DEADLINE,
        "frozen_at_jst": "2026-10-13T16:20:00+09:00",
        "evidence_level": "LOCAL_RECEIPT_RAW_SHA_ONLY",
        "race_source_sha256": "a" * 64,
        "source_receipts": receipts,
        "candidate": candidate,
        "source_bundle_sha256": hashlib.sha256(canonical(receipts)).hexdigest(),
        "candidate_sha256": hashlib.sha256(canonical(candidate)).hexdigest(),
        "results_read": False, "formal_fresh_read": False,
        "accuracy_improvement_proven": False,
        "model_promotion_authorized": False,
        "production_eligible": False, "scoring_authorized": False,
        "wagers_authorized": False,
    }
    baseline = {
        "race_key": KEY, "scope": "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
        "formal_results_seen": False, "formal_gate_unlocked": False,
        "production_accuracy_claim": "NOT_PROVEN", "real_purchases_authorized": False,
        "deadline_jst": DEADLINE, "evidence_committed_at": "2026-10-13T07:10:00+00:00",
        "model_id": "SITE_V232", "top10": list(BASELINE),
        "top3": list(BASELINE[:3]), "top5": list(BASELINE[:5]), "head_top1": "2",
    }
    outcome = {
        "race_key": KEY, "finish_order_boat": [1, 2, 3, 4, 5, 6],
        "observed_at_jst": "2026-10-13T16:50:00+09:00",
    }
    return freeze, baseline, outcome


class V335SiteOnlyScores(unittest.TestCase):
    def test_paired_head_and_top_n_exploratory_metrics(self):
        freeze, baseline, outcome = inputs()
        result = score_one(freeze, baseline, outcome)
        self.assertEqual(result["baseline"]["trifecta_top10"], 0)
        self.assertEqual(result["baseline"]["head_top1"], 0)
        self.assertEqual(result["candidate_modes"]["national_motor_st"]["trifecta_top1"], 1)
        self.assertEqual(result["candidate_modes"]["national_motor_st"]["trifecta_top10"], 1)
        self.assertEqual(result["candidate_modes"]["national_motor_st"]["head_top1"], 1)
        self.assertEqual(result["candidate_modes"]["national_only"]["trifecta_top10"], 0)
        study = summarize([result])
        self.assertEqual(study["races"], 1)
        self.assertEqual(study["candidate_modes"]["national_motor_st"]["hits"]["trifecta_top10"], 1)
        self.assertEqual(study["candidate_modes"]["national_motor_st"]["delta_hit_rate_vs_baseline"]["trifecta_top10"], 1.0)
        self.assertEqual(study["candidate_modes"]["national_motor_st"]["paired_discordance"]["trifecta_top10"]["exploratory_two_sided_sign_pvalue"], 1.0)
        self.assertFalse(result["accuracy_improvement_proven"])
        self.assertFalse(result["formal_fresh_read"])

    def test_digests_and_early_or_nonboat_outcomes_fail_closed(self):
        freeze, baseline, outcome = inputs()
        freeze["candidate"]["modes"]["national_motor_st"]["top10_boat_research_only"][0] = "1-3-2"
        with self.assertRaisesRegex(ValueError, "FROZEN_CANDIDATE_SHA_MISMATCH"):
            score_one(freeze, baseline, outcome)
        freeze, baseline, outcome = inputs()
        freeze["source_receipts"]["boaters"]["sha256"] = "b" * 63 + "a"
        with self.assertRaisesRegex(ValueError, "FROZEN_SOURCE_RECEIPT_SHA_MISMATCH"):
            score_one(freeze, baseline, outcome)
        freeze, baseline, outcome = inputs()
        outcome["observed_at_jst"] = DEADLINE
        with self.assertRaisesRegex(ValueError, "POSTDEADLINE_OBSERVATION_REQUIRED"):
            score_one(freeze, baseline, outcome)
        freeze, baseline, outcome = inputs()
        outcome["finish_order_boat"] = [1, 1, 3, 4, 5, 6]
        with self.assertRaisesRegex(ValueError, "SIX_REAL_BOAT_FINISH_ORDER_REQUIRED"):
            score_one(freeze, baseline, outcome)

    def test_formal_and_guard_blocked(self):
        freeze, baseline, outcome = inputs()
        freeze["formal_fresh_read"] = True
        with self.assertRaisesRegex(ValueError, "RESEARCH_ONLY_GUARD_REQUIRED"):
            score_one(freeze, baseline, outcome)
        freeze, baseline, outcome = inputs()
        freeze["race_key"] = "20261001-22-12"
        with self.assertRaisesRegex(ValueError, "NONFORMAL_RACE_KEY_REQUIRED"):
            score_one(freeze, baseline, outcome)

    def test_batch_reads_only_explicit_site_outcome_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            freeze, baseline, outcome = inputs()
            frozen = root / "data/research_local_v332/20261013" / (KEY + ".json")
            site = root / "data/site_autopilot/v232_cohort" / (KEY + ".json")
            frozen.parent.mkdir(parents=True)
            site.parent.mkdir(parents=True)
            frozen.write_text(json.dumps(freeze))
            site.write_text(json.dumps(baseline))
            (root / "data/formal_status.json").write_text("READ_FORBIDDEN")
            manifest = {"scope": SCOPE, "date": "20261013",
                        "outcomes": [outcome, outcome]}
            report = evaluate(root, manifest)
            self.assertEqual(report["supplied_outcome_rows"], 2)
            self.assertEqual(report["paired_evaluated"], 1)
            self.assertEqual(len(report["rejected"]), 1)
            self.assertFalse(report["formal_fresh_read"])
            self.assertFalse(report["formal_scoring_performed"])
            self.assertFalse(report["accuracy_improvement_proven"])
            manifest["scope"] = "FORMAL"
            with self.assertRaisesRegex(ValueError, "EXPLICIT_SITE_ONLY"):
                evaluate(root, manifest)
            manifest["scope"] = SCOPE
            manifest["date"] = "20261001"
            with self.assertRaisesRegex(ValueError, "INVALID_OR_FORMAL_DATE"):
                evaluate(root, manifest)

    def test_two_sided_sign_pvalue(self):
        self.assertIsNone(_two_sided_sign_pvalue(0, 0))
        self.assertEqual(_two_sided_sign_pvalue(1, 0), 1.0)
        self.assertAlmostEqual(_two_sided_sign_pvalue(7, 0), 0.015625)


if __name__ == "__main__":
    unittest.main()
