import sys,unittest,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from site_v179_patch import patch_index, audit
class V179Tests(unittest.TestCase):
    def fixture(self):
        return '''  const grade = der.selectivity?.grade || der.confidence_grade || "A";\n  const mapTickets = (world, budget) => {\n    if(typeof b === "string") return {rank:i+1, combo:b, probability:null, amount:null};\n        probability:b.confidence ?? b.probability ?? b.p ?? null,\n    if(!known){\n      const amounts = allocateByWeights(items.map(x=>num(x.probability) || 1), budget);\n      items.forEach((x,i)=>x.amount=amounts[i]);\n    }\n  const pA = num(wa?.probability ?? wa?.prob ?? wa?.rate);\n  const pB = num(wb?.probability ?? wb?.prob ?? wb?.rate);\n  Math.round(Number(a)*100)+"%"\n  Math.round(Number(b)*100)+"%"\n  Math.round(Number(w.probability)*100)+"%"\n  Math.round(Number(A.probability)*100)+"%"\n  Math.round(Number(B.probability)*100)+"%"\n  Math.round(Number(t.probability)*1000)/10+"%"\n  Math.round(Number(t.probability)*1000)/10+"%"\n  Math.round(Number(t.probability)*1000)/10+"%"\n'''
    def test_patch_exact_and_idempotent(self):
        s=self.fixture();x=patch_index(s)
        self.assertNotEqual(s,x)
        self.assertEqual(x,patch_index(x))
        self.assertIn('pAraw*100/worldSum',x)
        self.assertIn('verifiedTicketPercent.get(b.combo || b.ticket || b.bet)',x)
        self.assertNotIn('Math.round(Number(t.probability)*1000)/10',x)
        self.assertNotIn('const amounts = allocateByWeights(items',x)
    def test_reject_ambiguous_pattern(self):
        with self.assertRaises(RuntimeError):patch_index(self.fixture().replace('  const pA = num(wa?.probability ?? wa?.prob ?? wa?.rate);',''))
    def test_readiness_fail_closed_and_no_results_access(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'data').mkdir()
            (root/'data/formal_status.json').write_text(json.dumps({'target_date':'2026-10-09','formalParentSha':'a'*64,'formalFirst100':{'races':0},'guards':{'results_seen':False,'unlock':False,'scoring':False,'RESULT_UNLOCK_TOKEN':None},'connected':False,'predictions_ready':False}))
            (root/'data/model_status.json').write_text(json.dumps({'target_date':'2026-10-09','formal_parent_sha256':'a'*64,'model':'Candidate','core7':{'eligible_count':100,'core7_100_ready':True}}))
            a=audit(root)
            self.assertTrue(a['site_core7_ready'])
            self.assertFalse(a['site_consumer_ready_to_display_actual_formal_predictions'])
            self.assertIn('FORMAL_FRESH100_FREEZE_MISSING',a['blockers'])
            self.assertFalse(a['formal_current_scoring'])
if __name__=='__main__':unittest.main()
