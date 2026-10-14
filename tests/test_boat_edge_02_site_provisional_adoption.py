"""02: forward-only V254 site-default adoption; no results or formal Fresh read."""
import ast
import itertools
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from boat_edge_v254_third_tail import third_tail_candidate

def server_mode_factory():
    source=(ROOT/"scripts/site_final_history_v133.py").read_text(encoding="utf-8")
    tree=ast.parse(source)
    node=next(x for x in tree.body
              if isinstance(x,ast.FunctionDef) and x.name=="modes_from_tickets")
    isolated=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
    ns={"num":lambda x:float(x) if x is not None else None}
    exec(compile(isolated,"site_final_history_v133_mode_only","exec"),ns)
    return ns["modes_from_tickets"]

class V254ProvisionalSiteAdoption(unittest.TestCase):
    def rows(self):
        head=["1-2-3","1-2-4","1-3-2","1-4-2","2-1-3",
              "2-3-1","3-1-2","1-3-4","1-4-3","3-2-1"]
        other=["1-2-5","1-2-6","1-3-5","1-4-5","2-1-4",
               "2-3-4","3-1-4","3-2-4","2-4-1","3-4-1"]
        first=[{"combo":x,"p":20-i} for i,x in enumerate(head)]
        wave=([{"combo":x,"p":4-i*.1} for i,x in enumerate(other)]+first)
        return first,wave

    def test_prospective_server_mode_is_exact_v254_with_same_first_seven(self):
        hit,wave=self.rows()
        factory=server_mode_factory()
        odds={x["combo"]:20.0 for x in hit+wave}
        legacy=factory(hit,odds,wave)
        new=factory(hit,odds,wave,adopt_tail=True)
        self.assertEqual(set(legacy),{"hit","balance","hole","narrow"})
        self.assertEqual(set(new),set(legacy)|{"tail"})
        for mode in legacy:
            self.assertEqual(legacy[mode],new[mode])
        old=[r["combo"] for r in legacy["hit"]]
        hole=[r["combo"] for r in legacy["hole"]]
        promoted=[r["combo"] for r in new["tail"]]
        self.assertEqual(promoted,third_tail_candidate(old,hole))
        self.assertEqual(promoted[:7],old[:7])
        self.assertEqual(len(promoted),10)
        self.assertEqual(len(set(promoted)),10)
        self.assertEqual({x[:3] for x in promoted if x not in old}
                         <= {x[:3] for x in old[:7]},True)
        self.assertTrue(all(x in hole for x in promoted if x not in old))

    def test_new_future_snapshot_only_and_no_history_retrofit(self):
        source=(ROOT/"scripts/site_final_history_v133.py").read_text(encoding="utf-8")
        self.assertIn('if (SNAPS/f"{key}.json").is_file():',source)
        self.assertIn('adopt_tail=(pred.get("mode")!="formal" and key[:8]>="20261014")',source)
        self.assertIn('"default_display_mode"]="tail"',source)
        self.assertIn('"statistical_significance_claim"]=False',source)
        self.assertIn('"formal_current_model_changed"]=False',source)
        self.assertIn('"stake_plan_version"]="V141-10000-PROSPECTIVE"',source)
        self.assertLess(source.index('if (SNAPS/f"{key}.json").is_file():'),
                        source.index('modes=modes_from_tickets(adjusted["tickets"]'))
        self.assertNotIn("site_results",source[source.index('def modes_from_tickets'):source.index('def confidence')])

    def test_site_selected_mode_requires_new_frozen_source_and_preserves_legacy(self):
        js=(ROOT/"assets/boat_edge_v108.js").read_text(encoding="utf-8")
        self.assertIn('effectiveSnap?.modes?.tail?.tickets?.length===10',js)
        self.assertIn("effectiveSnap?.default_display_mode==='tail'",js)
        self.assertIn("pred.mode!=='formal'",js)
        self.assertIn("selectedTail?'tail'",js)
        self.assertIn("mode==='tail'&&!selectedTail",js)
        self.assertIn("writeLocal(perRaceModeKey,b.dataset.be108Mode)",js)
        self.assertIn("be181ValidModeRows",js)
        self.assertIn("const previous=readLocal(snapKey(key),null)",js)
        self.assertIn("if(previous!==null && previous!==undefined)return previous",js)

if __name__=="__main__":
    unittest.main()
