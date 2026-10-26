"""Synthetic-only: paired comparison constraints, not historical evidence."""
import copy
import itertools
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from boat_edge_paired120_research_evaluate import evaluate


def record():
    triples = ["-".join(map(str,t)) for t in itertools.permutations(range(1,7),3)]
    return {"race_key":"20261026-01-01","input_sha256":"a"*64,
            "model_sha256":"b"*64,"first_git_sha":"c"*40,\n            "actual_entry_verified":True,"model_unseen_attested":True,\n            "git_receipt_independently_verified":True,
            "first_git_at":"2026-10-26T09:00:00+09:00",
            "deadline_at":"2026-10-26T10:00:00+09:00",
            "actual_trifecta":triples[0],
            "ranked_120":[{"boat_combo":t,"relative_model_mass":1/120} for t in triples]}


class Paired120(unittest.TestCase):
    def test_equal_paired_fixture(self):
        a=record()
        b=copy.deepcopy(a);b["model_sha256"]="d"*64
        result=evaluate({"baseline":[a],"candidate":[b]})
        self.assertEqual(result["common_races"],1)
        self.assertEqual(result["baseline"]["hits"]["1"],1)
        self.assertAlmostEqual(result["baseline"]["log_loss"],math.log(120))
        self.assertEqual(result["topk_rate_delta"]["1"],0)
        self.assertFalse(result["improvement_proven"])

    def test_gate_rejects_late_git_and_input_drift(self):
        a=record()
        b=copy.deepcopy(a)
        b["first_git_at"]=b["deadline_at"]
        with self.assertRaisesRegex(ValueError,"NOT_GIT_FROZEN"):
            evaluate({"baseline":[a],"candidate":[b]})
        b=copy.deepcopy(a);b["input_sha256"]="e"*64
        with self.assertRaisesRegex(ValueError,"COMMON_INPUT"):
            evaluate({"baseline":[a],"candidate":[b]})

    def test_missing_independent_evidence_rejected(self):
        for field, code in (
            ("actual_entry_verified", "ACTUAL_ENTRY_PROOF_REQUIRED"),
            ("model_unseen_attested", "UNSEEN_MODEL_ATTESTATION_REQUIRED"),
            ("git_receipt_independently_verified", "INDEPENDENT_GIT_RECEIPT_REQUIRED"),
        ):
            a = record()
            a[field] = False
            with self.assertRaisesRegex(ValueError, code):
                evaluate({"baseline": [a], "candidate": [record()]})

    def test_invalid_rank_and_probabilities(self):
        a=record()
        b=copy.deepcopy(a)
        b["ranked_120"][1]["boat_combo"]=b["ranked_120"][0]["boat_combo"]
        with self.assertRaisesRegex(ValueError,"TICKET_SET_INVALID"):
            evaluate({"baseline":[a],"candidate":[b]})
        b=copy.deepcopy(a);b["ranked_120"][0]["relative_model_mass"]=0
        with self.assertRaisesRegex(ValueError,"PROBABILITY_INVALID"):
            evaluate({"baseline":[a],"candidate":[b]})


if __name__=="__main__":
    unittest.main()
