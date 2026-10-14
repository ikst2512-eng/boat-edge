"""V228 strict offline regression: pinned server extraction and formal isolation."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

SRC=Path(__file__).resolve().parents[1]/'scripts/boat_edge_v228_freeze_only.py'
spec=importlib.util.spec_from_file_location('freeze228',SRC)
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)


def src():
    return '''from __future__ import annotations
import json
from pathlib import Path
ROOT=Path('.')
SNAPS=ROOT/'data/site_prediction_snapshots'
HIST=ROOT/'data/site_prediction_history'
RESULTS=ROOT/'data/site_results'
FORMAL_DIRS=[ROOT/'data/formal_predictions']
NOW='not referenced in fixture'
TODAY='20261011'
changed=0;snapshots=0
# V226_IMMUTABLE_ORIGINAL_SNAPSHOT
# V226_SOURCE_GUARD
# V226_DECISION_WINDOW
# V226_ODDS_GUARD
for race_path in []:
    key=race_path.stem
    result=read_json(RESULTS/f"{key}.json")
    if result and result.get("status")=="confirmed":
        continue
    race=merge_formal(race,key)
    pred=formal_pred(race) if has_formal(race) else build_fallback(race)
for sp in sorted(SNAPS.glob("????????-??-??.json")):
    result=read_json(RESULTS/f"{key}.json")
for hp in sorted(HIST.glob("*.json")):
    pass
'''

class FreezeTests(unittest.TestCase):
    def test_current_live_model_pin_preserves_v254_and_strips_all_outcomes(self):
        # Guard the actual checkout, not merely a synthetic V133 lookalike.
        root=Path(__file__).resolve().parents[1]
        actual=(root/'scripts/site_final_history_v133.py').read_text(encoding='utf-8')
        self.assertEqual(f.git_blob(actual.encode('utf-8')),f.MODEL_SHA)
        # The source SHA must have been explicitly reapproved at adoption.
        self.assertIn('PROVISIONAL_V254_THIRD_TAIL10_FIXED_TOP7',actual)
        output=f.build_frozen_source(actual)
        self.assertIn('PROVISIONAL_V254_THIRD_TAIL10_FIXED_TOP7',output)
        self.assertIn('V228_SITE_ONLY_FIRST_FREEZE_NO_RESULT_INPUT',output)
        self.assertNotIn('read_json(RESULTS',output)
        self.assertNotIn('race=merge_formal(race,key)',output)
        self.assertNotIn('for hp in sorted(HIST.glob(',output)
        with self.assertRaisesRegex(AssertionError,'SOURCE_BLOB_SHA_DRIFT'):
            f.build_frozen_source(actual+'\\n')

    def test_exact_cut_and_forbidden_read_removed(self):
        raw=src()
        out=f.build_frozen_source(raw,f.git_blob(raw.encode()))
        self.assertNotIn('read_json(RESULTS',out)
        self.assertNotIn('race=merge_formal(',out)
        self.assertIn('if has_formal(race) or any(',out)
        self.assertNotIn('for sp in sorted',out)
        self.assertIn('V228_SITE_ONLY_FIRST_FREEZE_NO_RESULT_INPUT',out)

    def test_sha_drift_fails_closed(self):
        raw=src()
        with self.assertRaisesRegex(AssertionError,'SOURCE_BLOB_SHA_DRIFT'):
            f.build_frozen_source(raw+' ', f.git_blob(raw.encode()))

    def test_missing_required_anchor_fails_closed(self):
        raw=src().replace('# V226_ODDS_GUARD','not marker')
        with self.assertRaisesRegex(AssertionError,'GUARDS_NOT_PINNED'):
            f.build_frozen_source(raw, f.git_blob(raw.encode()))

    def test_formal_gate_closed_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'data').mkdir()
            with self.assertRaisesRegex(AssertionError,'GUARD_FILE_MISSING'):
                f.check_formal_closed(p)
            x=p/'data/formal_status.json'
            x.write_text('{"guards":{"results_seen":true,"unlock":false,"scoring":false,"RESULT_UNLOCK_TOKEN":null}}')
            with self.assertRaisesRegex(AssertionError,'FORMAL_LANE_NOT_CLOSED'):
                f.check_formal_closed(p)
            x.write_text('{"guards":{"results_seen":false,"unlock":false,"scoring":false,"RESULT_UNLOCK_TOKEN":null}}')
            f.check_formal_closed(p)

    def test_does_not_mutate_old_snapshot_from_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'data/site_prediction_snapshots/20261011-09-08.json'
            p.parent.mkdir(parents=True)
            p.write_bytes(b'pre-existing-prospective-snapshot')
            blob=p.read_bytes()
            raw=src()
            exec(compile(f.build_frozen_source(raw,f.git_blob(raw.encode())), 'fixture','exec'), {})
            self.assertEqual(p.read_bytes(),blob)

if __name__=='__main__':unittest.main()
