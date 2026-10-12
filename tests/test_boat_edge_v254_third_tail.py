"""No results are fetched in these V254 PRE_RESULT fixture tests."""
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from scripts.boat_edge_v254_third_tail import (
    third_tail_candidate, make_pre, freeze, formal_guard, stamp, valid
)

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/'data/site_autopilot/v232_cohort/20261012-09-02.json'

class ProspectiveThirdTail(unittest.TestCase):
    def test_reuse_precommitted_ticket_ranks_without_odds_retraining(self):
        cohort=json.loads(FROZEN.read_text(encoding='utf-8'))
        hit=cohort['top10']
        hole=[x['combo'] for x in cohort['frozen_mode_tickets']['hole']]
        candidate=third_tail_candidate(hit,hole)
        self.assertEqual(candidate[:7],hit[:7])
        self.assertEqual(len(candidate),10)
        self.assertEqual(len(set(candidate)),10)
        novel=set(candidate)-set(hit)
        self.assertGreater(len(novel),0)
        self.assertLessEqual(len(novel),3)
        first_two={x[:3] for x in hit[:7]}
        self.assertTrue(all(c[:3] in first_two and c in hole for c in novel))
        self.assertEqual(third_tail_candidate(hit,hole),candidate)

    def test_partial_coverage_never_invents_unknown_tickets(self):
        hit=['1-2-3','1-3-2','2-1-3','2-3-1','3-1-2',
             '3-2-1','1-2-4','1-4-2','2-1-4','3-1-4']
        hole=hit[:]+['2-3-4']
        selected=third_tail_candidate(hit,hole)
        self.assertEqual(len(selected),10)
        self.assertEqual(selected[:7],hit[:7])
        self.assertEqual(set(selected)-set(hit),{'2-3-4'})
        self.assertTrue(all(valid(x) for x in selected))
        self.assertIsNone(third_tail_candidate(hit+hit[:1],hole))

    def test_git_committed_cohort_can_only_freeze_before_deadline(self):
        now=stamp('2026-10-12T01:54:00+00:00')
        obj,error=make_pre(ROOT,FROZEN,now)
        self.assertIsNone(error,error)
        self.assertEqual(obj['comparators']['hit10'][:7],obj['comparators']['third_tail10'][:7])
        self.assertFalse(obj['results_seen_at_freeze'])
        self.assertFalse(obj['formal_result_access'])
        self.assertFalse(obj['production_model_changed'])
        self.assertFalse(obj['accuracy_improvement_proven'])
        self.assertFalse(obj['model_promotion_authorized'])
        self.assertEqual(obj['real_or_paper_wagers_placed'],0)
        self.assertEqual(obj['race_key'],'20261012-09-02')
        self.assertEqual(obj['parent_v232_sha256'],obj['parent_v232_sha256'].lower())
        too_late=stamp('2026-10-12T01:57:20+00:00')
        later,reason=make_pre(ROOT,FROZEN,too_late)
        self.assertIsNone(later)
        self.assertEqual(reason,'NOT_IN_FUTURE_FREEZE_WINDOW')

    def test_older_race_never_retroactively_frozen(self):
        now=stamp('2026-10-13T02:00:00+00:00')
        row,reason=make_pre(ROOT,FROZEN,now)
        self.assertIsNone(row)
        self.assertEqual(reason,'NOT_IN_FUTURE_FREEZE_WINDOW')

    def test_bad_formal_guard_blocks_even_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'data/formal_status.json'
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({'guards':{'results_seen':True,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None}}))
            with self.assertRaisesRegex(RuntimeError,'FORMAL_GATE'):formal_guard(Path(tmp))

if __name__=='__main__':unittest.main()
