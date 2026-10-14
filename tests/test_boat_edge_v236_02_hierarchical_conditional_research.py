"""Synthetic only: never opens race outcomes, results, site data or formal files."""
import copy
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from boat_edge_02_hierarchical_conditional_research import rank_120

KEY = "20261014-12-01"
SCOPE = dict(schema="BE02_RESEARCH_AGGREGATE_SCOPE_V1", race_key=KEY,
             train_end="20261013", first_frozen_at="2026-10-14T10:00:00+09:00", deadline_jst="10:20",
             authorized_training_aggregate=True,
             source_class="REVIEWED_AUTHORIZED_OFFICIAL_DERIVED_AGGREGATES",
             reviewed_permission_evidence_sha256="a"*64, source_manifest_sha256="b"*64,
             no_target_outcome=True, formal_fresh_not_used=True)

def groups():
    def entry(labels, leader):
        return dict(national={x:(17 if x == leader else 2) for x in labels},
                    venue={x:(8 if x == leader else 1) for x in labels}, racer=None, motor=None)
    return dict(
        head=entry(range(1,7),1),
        second={h:entry([x for x in range(1,7) if x!=h],2 if h!=2 else 1) for h in range(1,7)},
        third={(h,s):entry([x for x in range(1,7) if x not in (h,s)],
                           next(x for x in range(1,7) if x not in (h,s)))
               for h in range(1,7) for s in range(1,7) if h!=s})

class ConditionalResearch(unittest.TestCase):
    def test_full120_exactly10_deterministic_and_head_parity(self):
        one=rank_120(KEY,SCOPE,groups());two=rank_120(KEY,SCOPE,groups())
        self.assertEqual(one,two)
        scores=one['ranked_120']
        self.assertEqual(len(scores),120)
        self.assertEqual(len({r['boat_combo'] for r in scores}),120)
        self.assertEqual(len(one['top10_boat_research_only']),10)
        self.assertAlmostEqual(sum(r['relative_model_mass'] for r in scores),1)
        self.assertAlmostEqual(sum(one['head_mass_boat'].values()),1)
        self.assertEqual(one['top10_boat_research_only'],[x['boat_combo'] for x in scores[:10]])
        self.assertFalse(one['production_eligible'])
    def test_absent_racer_motor_not_inferred_and_nonzero_mass(self):
        a=rank_120(KEY,SCOPE,groups())
        self.assertEqual(a['used_layers']['head'],['national','venue'])
        self.assertGreater(min(x['relative_model_mass'] for x in a['ranked_120']),0)
    def test_strict_perm_no_head_second_or_third_repeats(self):
        a=rank_120(KEY,SCOPE,groups())
        for r in a['ranked_120']:
            self.assertEqual(len(set(r['boat_combo'].split('-'))),3)
    def test_unauthorized_and_wrong_source_never_accepted(self):
        a=copy.deepcopy(SCOPE);a['authorized_training_aggregate']=False
        with self.assertRaisesRegex(ValueError,'RESEARCH_GUARDS'):rank_120(KEY,a,groups())
        a=copy.deepcopy(SCOPE);a['source_class']='BOATERS_UNLICENSED_SCRAPE'
        with self.assertRaisesRegex(ValueError,'UNAUTHORIZED'):rank_120(KEY,a,groups())
        a=copy.deepcopy(SCOPE);a['reviewed_permission_evidence_sha256']=''
        with self.assertRaisesRegex(ValueError,'PROVENANCE'):rank_120(KEY,a,groups())
    def test_no_target_day_or_formal_leakage(self):
        a=copy.deepcopy(SCOPE);a['train_end']='20261014'
        with self.assertRaisesRegex(ValueError,'TRAINING_NOT_EARLIER'):rank_120(KEY,a,groups())
        with self.assertRaisesRegex(ValueError,'FORMAL_FRESH_EXCLUDED'):rank_120('20261001-12-01',SCOPE,groups())
        a=copy.deepcopy(SCOPE);a['first_frozen_at']='2026-10-15T10:00:00+09:00'
        with self.assertRaisesRegex(ValueError,'INVALID_FIRST_FREEZE'):rank_120(KEY,a,groups())
    def test_after_deadline_and_wrong_timezone_rejected(self):
        a=copy.deepcopy(SCOPE);a['first_frozen_at']='2026-10-14T10:21:00+09:00'
        with self.assertRaisesRegex(ValueError,'INVALID_FIRST_FREEZE'):rank_120(KEY,a,groups())
        a=copy.deepcopy(SCOPE);a['first_frozen_at']='2026-10-14T01:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'INVALID_FIRST_FREEZE'):rank_120(KEY,a,groups())
    def test_no_missing_layers_synthetic_counts_and_no_zero_as_missing(self):
        a=groups();a['second'][1]['racer']={2:0,3:0,4:0,5:0,6:0}
        rank_120(KEY,SCOPE,a)
        a=groups();a['third'][(1,2)]['national']=None;a['third'][(1,2)]['venue']=None
        with self.assertRaisesRegex(ValueError,'NO_OBSERVED'):rank_120(KEY,SCOPE,a)
        a=groups();a['head']['racer']={1:-1,2:0,3:0,4:0,5:0,6:0}
        with self.assertRaisesRegex(ValueError,'INVALID_LAYER_COUNTS'):rank_120(KEY,SCOPE,a)
    def test_each_conditional_distribution_sums_to_one(self):
        a=rank_120(KEY,SCOPE,groups());rows=a['ranked_120']
        for h in range(1,7):
            m=sum(r['relative_model_mass'] for r in rows if r['boat_combo'].startswith(f'{h}-'))
            self.assertAlmostEqual(m,a['head_mass_boat'][str(h)])
    def test_extra_input_key_rejected(self):
        a=copy.deepcopy(SCOPE);a['result']='no'
        with self.assertRaisesRegex(ValueError,'EXPLICIT_SOURCE'):rank_120(KEY,a,groups())
        g=groups();g['third'][(1,2)]['motor']={1:5}
        with self.assertRaisesRegex(ValueError,'BAD_LAYER_COUNT_LABELS'):rank_120(KEY,SCOPE,g)

if __name__=='__main__':unittest.main()
