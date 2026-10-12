"""V295: simulated racing Git retry; no historical result or payout access."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import boat_edge_v295_retry_trace as audit

NOW=datetime(2026,10,13,0,0,tzinfo=timezone.utc)
ONE="20261013-14-01"
TWO="20261013-14-02"


def setup(root):
    p=root/"data/formal_status.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({
        "formalFirst100":{"races":0},
        "guards":{"results_seen":False,"unlock":False,"scoring":False,
                  "RESULT_UNLOCK_TOKEN":None}}),encoding="utf-8")


def evidence(root,key):
    p=root/"data/site_autopilot/v229_evidence"/(key+".json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text("UNPUSHED_PRE_RESULT_ATTESTATION",encoding="utf-8")
    return p


class RetryCase(unittest.TestCase):
    def test_lost_then_committed_by_other_writer(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);setup(root);state=root.parent/(root.name+"-retry.json")
            try:
                proof=evidence(root,ONE)
                with patch.object(audit,"tracked",return_value=False):
                    first=audit.append_state(root,state,1,NOW)
                self.assertEqual(first["new_this_attempt"],1)
                self.assertEqual(first["seen_candidate_local"],1)
                self.assertEqual(first["seen_candidate_absent_unpublished"],0)
                proof.unlink()
                with patch.object(audit,"tracked",return_value=False):
                    second=audit.append_state(root,state,2,NOW)
                self.assertEqual(second["seen_candidate_absent_unpublished"],1)
                self.assertEqual(second["potentially_lost_keys"],[ONE])
                self.assertEqual(second["new_this_attempt"],0)
                def published(_repo,relative):
                    return relative=="data/site_prediction_snapshots/"+ONE+".json"
                with patch.object(audit,"tracked",side_effect=published):
                    third=audit.append_state(root,state,3,NOW)
                self.assertEqual(third["seen_candidate_tracked"],1)
                self.assertEqual(third["seen_candidate_absent_unpublished"],0)
                self.assertEqual(len(json.loads(state.read_text())["observations"]),3)
            finally:
                state.unlink(missing_ok=True)

    def test_later_new_candidates_also_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);setup(root);state=root.parent/(root.name+"-retry.json")
            try:
                with patch.object(audit,"tracked",return_value=False):
                    initial=audit.append_state(root,state,1,NOW)
                    self.assertEqual(initial["new_this_attempt"],0)
                    proof=evidence(root,TWO)
                    second=audit.append_state(root,state,2,NOW)
                    self.assertEqual(second["ever_seen_proposed_total"],1)
                    proof.unlink()
                    third=audit.append_state(root,state,3,NOW)
                self.assertEqual(third["potentially_lost_keys"],[TWO])
            finally:
                state.unlink(missing_ok=True)

    def test_no_retroactive_authorization_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);setup(root);state=root.parent/(root.name+"-retry.json")
            try:
                with patch.object(audit,"tracked",return_value=False):
                    with self.assertRaises(ValueError):
                        audit.append_state(root,state,0,NOW)
                    with self.assertRaises(RuntimeError):
                        audit.append_state(root,state,2,NOW)
                    x=audit.append_state(root,state,1,NOW)
                    self.assertEqual(x["ever_seen_proposed_total"],0)
                gpath=root/"data/formal_status.json"
                doc=json.loads(gpath.read_text());doc["guards"]["results_seen"]=True
                gpath.write_text(json.dumps(doc))
                with patch.object(audit,"tracked",return_value=False):
                    with self.assertRaisesRegex(RuntimeError,"LOCK_NOT_CLOSED"):
                        audit.append_state(root,state,2,NOW)
                self.assertEqual(len(json.loads(state.read_text())["observations"]),1)
            finally:
                state.unlink(missing_ok=True)

    def test_exact_race_key_and_safe_v235_wiring(self):
        repo=Path(__file__).resolve().parents[1]
        source=(repo/"scripts/boat_edge_v295_retry_trace.py").read_text(encoding="utf-8")
        wf=(repo/".github/workflows/V235.yml").read_text(encoding="utf-8")
        self.assertTrue(audit.RACE.fullmatch(ONE))
        self.assertFalse(audit.RACE.fullmatch("20261013-14-001"))
        self.assertFalse(audit.RACE.fullmatch("20261013-14-01.json"))
        self.assertIn('directory.glob("20??????-??-??.json")',source)
        self.assertIn("python3 scripts/boat_edge_v230_fast_lane.py --workers 8",wf)
        self.assertIn('python3 scripts/boat_edge_v295_retry_trace.py',wf)
        self.assertIn('--attempt "$attempt"',wf)
        self.assertIn('--state-path "$RUNNER_TEMP/boat_edge_v295_retry_trace.json"',wf)
        self.assertLess(wf.index("scripts/boat_edge_v230_fast_lane.py --workers 8"),
                        wf.index("scripts/boat_edge_v295_retry_trace.py"))
        self.assertLess(wf.index("scripts/boat_edge_v295_retry_trace.py"),
                        wf.index("scripts/boat_edge_v232_pre_result_cohort.py",
                                 wf.index("scripts/boat_edge_v295_retry_trace.py")))
        # No source-only status can be interpreted as a bet or calibrated accuracy.
        self.assertIn("UNPUBLISHED_AFTER_RETRY_NOT_PROOF_OF_ELIGIBILITY_OR_PERMANENT_LOSS",source)
        self.assertIn("SITE_PRE_RESULT_ONLY_NO_FORMAL_NO_RESULTS",source)


if __name__=="__main__":
    unittest.main()
