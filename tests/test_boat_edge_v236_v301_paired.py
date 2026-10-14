"""V301 synthetic-only research audit tests: no production result/payout reads."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import boat_edge_v301_paired_evidence as m

KEY1 = "20261013-14-11"
KEY2 = "20261013-09-02"
HIT = ["1-2-3", "1-3-2", "1-2-4", "1-4-2", "1-3-4",
       "2-1-3", "2-3-1", "3-1-2", "4-1-2", "5-1-2"]
EXTRA = ["1-5-6", "2-4-1", "3-4-1", "6-1-2", "4-2-1",
         "1-6-5", "3-2-1", "2-1-4", "4-3-1", "5-2-1"]
DUE = "2026-10-13T15:00:00+09:00"
FREEZE = "2026-10-13T05:50:00+00:00"
PARENT_AT = "2026-10-13T05:45:00+00:00"
FREEZE_AT = "2026-10-13T05:51:00+00:00"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SiteOnlyPairedEvidence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        write(self.root / "data/formal_status.json",
              {"guards": {"results_seen": False, "unlock": False,
                          "scoring": False, "RESULT_UNLOCK_TOKEN": None},
               "formalFirst100": {"races": 0}})

    def proof(self, root, path):
        self.assertEqual(root, self.root)
        parent = "v232_cohort" in path.parts
        return {"commit": "a" * 40 if parent else "b" * 40,
                "at": m.time(PARENT_AT if parent else FREEZE_AT),
                "sha256": m.digest(path)}

    def add(self, study, key=KEY1, winning="1-5-6", improve=True, policy=None):
        cohort = {"schema": "BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1",
                  "scope": "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH",
                  "race_key": key, "top10": HIT,
                  "snapshot_saved_at": "2026-10-13T05:44:00+00:00",
                  "formal_results_seen": False, "formal_gate_unlocked": False,
                  "paper_purchases_authorized": False, "real_purchases_authorized": False}
        base = self.root / m.BASE
        parent = base / "v232_cohort" / (key + ".json")
        parent_sha = write(parent, cohort)
        candidates = {
            "v236": {"hit10": HIT, "balance10": HIT,
                     "scenario7plus3": HIT[:9] + ([EXTRA[0]] if improve else [HIT[9]]),
                     "coverage15": HIT + EXTRA[:5]},
            "v240": {"hit10": HIT,
                     "second_coverage10": HIT[:9] + ([EXTRA[0]] if improve else [HIT[9]]),
                     "pair_coverage10": HIT},
            "v254": {"hit10": HIT,
                     "third_tail10": HIT[:9] + ([EXTRA[0]] if improve else [HIT[9]])}
        }[study]
        if study == "v236":
            policy = policy or "PREDECLARED_HEAD_TAIL_COVERAGE_NO_ODDS_MULTIPLIER_BOOST"
            if m.V236_POLICIES[policy]:
                # A frozen separate ten-point strategy, not recomputed after score.
                candidates["headsecond10"] = HIT[:9] + [EXTRA[0]]
        names = m.CONFIG[study]
        frozen = {"schema": names[2], "scope": names[3], "race_key": key,
                  "deadline_jst": DUE, "frozen_at": FREEZE,
                  "comparators": candidates, "production_model_changed": False,
                  "model_promotion_authorized": False,
                  "results_seen_at_freeze": False,
                  names[8]: parent_sha, names[9]: "a" * 40}
        if study == "v236":
            # Mirror the REAL legacy V236 schema, rather than masking differences
            # with synthetic V240/V254 fields that do not exist in Git evidence.
            frozen.pop("model_promotion_authorized")
            frozen.pop("results_seen_at_freeze")
            frozen["result_seen_at_freeze"] = False
            frozen["proven_improvement"] = False
            frozen["actual_or_paper_purchase"] = False
            frozen["comparison_policy"] = policy
        else:
            frozen["formal_result_access"] = False
        freeze_path = base / (study + "_frozen") / (key + ".json")
        frozen_sha = write(freeze_path, frozen)
        outcomes = {k: winning in v for k, v in candidates.items()}
        scored = {"schema": names[0], "scope": names[1], "race_key": key,
                  names[4]: frozen_sha, names[5]: "b" * 40,
                  names[6]: winning, "outcomes": outcomes,
                  "production_model_changed": False,
                  "model_promotion_authorized": False}
        if study == "v236":
            scored.pop("production_model_changed")
            scored.update({"ticket_counts": {k: len(v) for k, v in candidates.items()},
                           "production_accuracy_improvement_proven": False,
                           "real_or_paper_purchase": False})
            if m.V236_POLICIES[policy]:
                scored["candidate_policy"] = policy
                scored["prefix_outcomes"] = {
                    mode: {str(k): winning in candidates[mode][:k] for k in (3, 5, 10)}
                    for mode in ("hit10", "headsecond10")}
        elif study == "v240":
            scored.update({"novelty": {k: len(set(v)-set(HIT)) for k, v in candidates.items()},
                           "real_or_paper_purchase": False})
        else:
            scored.update({"novel_tickets": len(set(candidates["third_tail10"])-set(HIT)),
                           "real_or_paper_wagers_placed": 0,
                           "accuracy_improvement_proven": False,
                           "formal_result_access": False,
                           "result_precommitted_sha256": parent_sha})
        scored_path = base / (study + "_scored") / (key + ".json")
        write(scored_path, scored)
        return scored_path

    def test_matched_safely_and_fifteen_points_never_pooled(self):
        for study in m.CONFIG:
            self.add(study)
        report = m.audit(self.root, attest=self.proof)
        self.assertEqual(report["same_race_cross_study"]["v240_vs_v254"]
                         ["identical_race_baseline_matches"], 1)
        cross = report["same_race_cross_study"]["v236_vs_v240"]["equal_ten_ticket_head_to_head_only"]
        # V236 baseline misses the synthetic winning combo; V240 second10 catches it.
        self.assertEqual(cross["hit10_vs_second_coverage10"]["right_only_hits"], 1)
        self.assertEqual(cross["hit10_vs_second_coverage10"]["left_hits"], 0)
        self.assertEqual(cross["hit10_vs_second_coverage10"]["right_hits"], 1)
        # V236 scenario catches it; V240 pair candidate misses, still 10 vs 10.
        self.assertEqual(cross["scenario7plus3_vs_pair_coverage10"]["left_only_hits"], 1)
        self.assertEqual(cross["scenario7plus3_vs_pair_coverage10"]["exact_mcnemar_two_sided_p"], 1.0)
        self.assertFalse(any("coverage15" in name for name in cross))
        self.assertFalse(any(v["improvement_proven"] for v in cross.values()))
        self.assertEqual(report["within_study"]["v240"]
                         ["equal_ten_point_modes"]["second_coverage10"]["paired_gain"], 1)
        self.assertEqual(report["within_study"]["v236"]
                         ["coverage15_separate_point_budget"]["points"], 15)
        self.assertNotIn("coverage15", report["within_study"]["v236"]
                         ["equal_ten_point_modes"])
        self.assertFalse(report["accuracy_improvement_proven"])
        self.assertFalse(report["promotion_authorized"])

    def test_v236_legacy_guard_keys_match_real_saved_records(self):
        path = self.add("v236")
        frozen_path = self.root / m.BASE / "v236_frozen" / path.name
        scored = m.read(path)
        frozen = m.read(frozen_path)
        self.assertNotIn("production_model_changed", scored)
        self.assertNotIn("model_promotion_authorized", frozen)
        self.assertNotIn("results_seen_at_freeze", frozen)
        self.assertFalse(frozen["result_seen_at_freeze"])
        self.assertFalse(frozen["proven_improvement"])
        self.assertEqual(m.checked_row(self.root, "v236", path, self.proof)["key"], KEY1)
        for corrupted in (("result_seen_at_freeze", True),
                          ("result_seen_at_freeze", None),
                          ("proven_improvement", True),
                          ("proven_improvement", None)):
            field, value = corrupted
            modified = dict(frozen)
            if value is None:
                modified.pop(field)
            else:
                modified[field] = value
            write(frozen_path, modified)
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(m.EvidenceError, "PRODUCTION_OR_FREEZE_GUARD"):
                    m.checked_row(self.root, "v236", path, self.proof)
        write(frozen_path, frozen)

    def test_v236_policy_scoped_headsecond_prefixes_and_corruption_guards(self):
        v2 = "PREDECLARED_HEAD_SECOND_COVERAGE_FROM_EXISTING_FROZEN_MODES_NO_NEW_ODDS_MULTIPLIER"
        v3 = "PREDECLARED_DISTINCT_HEAD_SECOND_TICKET_MEMBERSHIP_EXISTING_FROZEN_MODES"
        scored_v2 = self.add("v236", KEY1, policy=v2)
        scored_v3 = self.add("v236", KEY2, policy=v3)
        report = m.audit(self.root, attest=self.proof)
        groups = report["within_study"]["v236"]["headsecond10_by_frozen_policy"]
        self.assertEqual(groups[v2]["races"], 1)
        self.assertEqual(groups[v3]["races"], 1)
        self.assertEqual(groups[v2]["ranked_top3_top5_top10"]["10"]["candidate_hits"], 1)
        self.assertEqual(groups[v3]["ranked_top3_top5_top10"]["10"]["candidate_hits"], 1)
        self.assertEqual(report["within_study"]["v236"]["sample_races"], 2)
        self.assertEqual(report["within_study"]["v236"]["equal_ten_point_modes"]["balance10"]["races"], 2)
        # Legacy V2 missing candidate_policy is allowed, but V3 must be tagged.
        original = m.read(scored_v2)
        tagged = dict(original)
        tagged.pop("candidate_policy")
        write(scored_v2, tagged)
        self.assertEqual(m.audit(self.root, attest=self.proof)["within_study"]
                         ["v236"]["headsecond10_by_frozen_policy"][v2]["races"], 1)
        write(scored_v2, original)
        v3_saved = m.read(scored_v3)
        wrong = dict(v3_saved)
        wrong["prefix_outcomes"] = {mode: dict(kv) for mode, kv in
                                    wrong["prefix_outcomes"].items()}
        wrong["prefix_outcomes"]["headsecond10"]["10"] = False
        write(scored_v3, wrong)
        with self.assertRaisesRegex(m.EvidenceError, "V236_PREFIX_OUTCOME_CHANGED"):
            m.audit(self.root, attest=self.proof)
        write(scored_v3, v3_saved)
        wrong = dict(v3_saved)
        wrong.pop("candidate_policy")
        write(scored_v3, wrong)
        with self.assertRaisesRegex(m.EvidenceError, "V236_SCORED_POLICY_MISMATCH"):
            m.audit(self.root, attest=self.proof)
        write(scored_v3, v3_saved)
        frozen_v2 = self.root / m.BASE / "v236_frozen" / scored_v2.name
        freeze = m.read(frozen_v2)
        freeze["comparison_policy"] = "NEW_UNDECLARED_POLICY"
        write(frozen_v2, freeze)
        with self.assertRaisesRegex(m.EvidenceError, "UNKNOWN_V236_FROZEN_POLICY"):
            m.audit(self.root, attest=self.proof)

    def test_v236_v1_cannot_gain_posthoc_headsecond(self):
        path = self.add("v236")
        scored = m.read(path)
        scored["candidate_policy"] = "PREDECLARED_HEAD_SECOND_COVERAGE_FROM_EXISTING_FROZEN_MODES_NO_NEW_ODDS_MULTIPLIER"
        write(path, scored)
        with self.assertRaisesRegex(m.EvidenceError, "V236_V1_POSTHOC_CANDIDATE_REFUSED"):
            m.audit(self.root, attest=self.proof)

    def test_nonoverlapping_cohorts_never_pooled_or_compared(self):
        self.add("v236", KEY1)
        self.add("v254", KEY1)
        self.add("v240", KEY2)
        report = m.audit(self.root, attest=self.proof)
        self.assertEqual(report["same_race_cross_study"]["v240_vs_v254"]
                         ["identical_race_baseline_matches"], 0)
        self.assertEqual(report["same_race_cross_study"]["v236_vs_v254"]
                         ["identical_race_baseline_matches"], 1)
        self.assertEqual(report["within_study"]["v240"]["sample_races"], 1)
        self.assertFalse(report["same_race_cross_study"]["v240_vs_v254"]
                         ["cross_study_superiority_proven"])
        cross = report["same_race_cross_study"]["v240_vs_v254"]["equal_ten_ticket_head_to_head_only"]
        self.assertTrue(cross)
        self.assertTrue(all(r["races"] == 0 and r["exact_mcnemar_two_sided_p"] is None
                            for r in cross.values()))

    def test_git_frozen_within_study_all_topk_and_unequal_budget_excluded(self):
        self.add("v236", winning=EXTRA[0], improve=True)
        self.add("v254", winning=EXTRA[0], improve=True)
        self.add("v240", winning=EXTRA[0], improve=True)
        report = m.audit(self.root, attest=self.proof)["within_study"]
        rank236 = report["v236"]["ranked_top3_top5_top10"]
        self.assertEqual(rank236["hit10"]["3"], {
            "races": 1, "hits": 0, "hit_rate_percent": 0.0})
        self.assertEqual(rank236["scenario7plus3"]["10"]["hits"], 1)
        self.assertNotIn("coverage15", rank236)
        self.assertNotIn("headsecond10", rank236)
        self.assertEqual(report["v254"]["ranked_top3_top5_top10"]
                         ["third_tail10"]["10"]["hits"], 1)
        self.assertEqual(report["v240"]["ranked_top3_top5_top10"]
                         ["second_coverage10"]["10"]["hits"], 1)
        row = {"winning": EXTRA[0], "modes": {"test10": 10},
               "frozen_ticket_lists": {"test10": HIT[:9] + [EXTRA[0]]}}
        summary = m.within_study_ranked_prefixes([row], ["test10"])
        self.assertEqual(summary["test10"]["3"]["hits"], 0)
        self.assertEqual(summary["test10"]["10"]["hits"], 1)
        row["modes"]["test10"] = 15
        with self.assertRaisesRegex(m.EvidenceError, "EXACT_TEN_TICKETS_REQUIRED"):
            m.within_study_ranked_prefixes([row], ["test10"])

    def test_v236_v254_ranked_topk_cross_study_stratified_and_fail_closed(self):
        v2 = "PREDECLARED_HEAD_SECOND_COVERAGE_FROM_EXISTING_FROZEN_MODES_NO_NEW_ODDS_MULTIPLIER"
        v3 = "PREDECLARED_DISTINCT_HEAD_SECOND_TICKET_MEMBERSHIP_EXISTING_FROZEN_MODES"
        self.add("v236", KEY1, policy=v3)
        self.add("v254", KEY1)
        self.add("v236", KEY2, policy=v2)  # Not in V254; never borrow KEY1.
        report = m.audit(self.root, attest=self.proof)
        cross = report["same_race_cross_study"]["v236_vs_v254"]
        separate = cross["ranked_headsecond_vs_third_tail10_by_v236_policy"]
        self.assertEqual(cross["identical_race_baseline_matches"], 1)
        self.assertEqual(separate[v2]["races"], 0)
        self.assertEqual(separate[v3]["races"], 1)
        self.assertEqual(separate[v3]["ranked_top3_top5_top10"]["3"]["races"], 1)
        self.assertEqual(separate[v3]["ranked_top3_top5_top10"]["10"]["left_hits"], 1)
        self.assertEqual(separate[v3]["ranked_top3_top5_top10"]["10"]["right_hits"], 1)
        self.assertFalse(separate[v3]["model_promotion_authorized"])

        def row(mode, tickets):
            return {"key": KEY1, "day": KEY1[:8], "winning": EXTRA[0],
                    "modes": {mode: 10}, "outcomes": {mode: True},
                    "frozen_ticket_lists": {mode: tickets}}
        left = row("headsecond10", [EXTRA[0]] + HIT[:9])
        right = row("third_tail10", HIT[:9] + [EXTRA[0]])
        ranked = m.compare_ranked_10point_modes(
            [left], [right], "headsecond10", "third_tail10")
        self.assertEqual(ranked["ranked_top3_top5_top10"]["3"]["left_hits"], 1)
        self.assertEqual(ranked["ranked_top3_top5_top10"]["3"]["right_hits"], 0)
        self.assertEqual(ranked["ranked_top3_top5_top10"]["10"]["left_hits"], 1)
        self.assertEqual(ranked["ranked_top3_top5_top10"]["10"]["right_hits"], 1)
        with self.assertRaisesRegex(m.EvidenceError, "RACE_OR_OUTCOME_MISMATCH"):
            m.compare_ranked_10point_modes(
                [left], [dict(right, key=KEY2)], "headsecond10", "third_tail10")
        bad_tickets = dict(right)
        bad_tickets["frozen_ticket_lists"] = {"third_tail10": HIT[:9] + [HIT[8]]}
        with self.assertRaisesRegex(m.EvidenceError, "EXACT_TEN_FROZEN_TICKETS"):
            m.compare_ranked_10point_modes(
                [left], [bad_tickets], "headsecond10", "third_tail10")
        forged = dict(right, outcomes={"third_tail10": False})
        with self.assertRaisesRegex(m.EvidenceError, "OUTCOME_NOT_FROZEN"):
            m.compare_ranked_10point_modes(
                [left], [forged], "headsecond10", "third_tail10")

    def test_corrupted_score_cannot_silently_shrink_sample(self):
        path = self.add("v254")
        row = m.read(path)
        row["outcomes"]["third_tail10"] = False
        write(path, row)
        with self.assertRaisesRegex(m.EvidenceError, "SCORED_VERSUS_FROZEN"):
            m.audit(self.root, attest=self.proof)

    def test_postfreeze_mutation_and_parent_baseline_disagreement_block(self):
        path = self.add("v240")
        frozen = self.root / m.BASE / "v240_frozen" / path.name
        frozen.write_text(frozen.read_text() + " ", encoding="utf-8")
        with self.assertRaisesRegex(m.EvidenceError, "GIT_FIRST_BYTES"):
            m.audit(self.root, attest=self.proof)
        self.add("v240")
        parent = self.root / m.BASE / "v232_cohort" / path.name
        source = m.read(parent)
        source["top10"] = list(reversed(HIT))
        write(parent, source)
        with self.assertRaisesRegex(m.EvidenceError, "GIT_FIRST_BYTES"):
            m.audit(self.root, attest=self.proof)

    def test_closed_formal_guard_precedes_any_site_scored_access(self):
        self.add("v236")
        formal = self.root / "data/formal_status.json"
        for bad in ({"races": 1}, {"races": False}, {}, {"races": "0"}):
            write(formal, {"guards": {"results_seen": False, "unlock": False,
                                      "scoring": False, "RESULT_UNLOCK_TOKEN": None},
                           "formalFirst100": bad})
            with patch.object(m, "read", wraps=m.read) as calls:
                with self.assertRaisesRegex(m.EvidenceError, "FORMAL_FRESH"):
                    m.audit(self.root, attest=self.proof)
                self.assertEqual([c.args[0] for c in calls.call_args_list], [formal])

    def test_direct_paired_scorer_rejects_wrong_race_or_unequal_tickets(self):
        def row():
            return {"key": KEY1, "day": KEY1[:8], "winning": "1-2-3",
                    "outcomes": {"hit10": True, "third_tail10": False},
                    "modes": {"hit10": 10, "third_tail10": 10}}
        left, right = row(), row()
        good = m.compare_10point_modes([left], [right], "hit10", "third_tail10")
        self.assertEqual((good["races"], good["left_hits"], good["right_hits"]), (1, 1, 0))
        self.assertFalse(good["improvement_proven"])
        for field, other in (
                ("key", KEY2), ("winning", "2-1-3"), ("day", "20261012")):
            with self.subTest(field=field):
                wrong = row()
                wrong[field] = other
                with self.assertRaisesRegex(m.EvidenceError, "RACE_OR_OUTCOME_MISMATCH"):
                    m.compare_10point_modes([left], [wrong], "hit10", "third_tail10")
        wrong = row()
        wrong["modes"]["third_tail10"] = 9
        with self.assertRaisesRegex(m.EvidenceError, "EXACT_TEN_TICKETS_REQUIRED"):
            m.compare_10point_modes([left], [wrong], "hit10", "third_tail10")
        with self.assertRaisesRegex(m.EvidenceError, "RACE_COUNT_MISMATCH"):
            m.compare_10point_modes([left], [], "hit10", "third_tail10")

    def test_precise_paired_mcnemar_and_miss_slot_attribution(self):
        row = {"key": KEY1, "day": "20261013", "winning": "1-5-6",
               "baseline": HIT, "outcomes": {"hit10": False, "test10": True}}
        x = m.paired([row], "test10")
        self.assertEqual(x["exact_mcnemar_two_sided_p"], 1.0)
        self.assertEqual(x["paired_gain"], 1)
        self.assertEqual(m.misses([row]), {
            "head_missing": 0, "second_missing": 1, "third_missing": 0})
        variants = [
            dict(row, winning="6-1-2", outcomes={"hit10": False, "test10": False}),
            dict(row, winning="1-2-5", outcomes={"hit10": False, "test10": False}),
            dict(row, winning="1-2-3", outcomes={"hit10": True, "test10": False})]
        self.assertEqual(m.misses(variants),
                         {"head_missing": 1, "second_missing": 0, "third_missing": 1})
        self.assertEqual(m.paired([row]*5, "test10")["exact_mcnemar_two_sided_p"], 0.0625)


if __name__ == "__main__":
    unittest.main()
