"""Read-only CORE7 gap diagnostic regression."""
import json
import tempfile
import unittest
from pathlib import Path
from core7_gap_diagnostic import diagnose

class GapTests(unittest.TestCase):
 def test_counts_and_no_mutation(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   folder=root/"data/races"
   folder.mkdir(parents=True)
   fixtures=[("01",True,{}),("02",False,{"stt":False,"tkz":False}),("03",False,{}),("04",False,{"original_exhibition":False})]
   original=[]
   for race,ready,missing in fixtures:
    path=folder/f"20261025-04-{race}.json"
    doc={"race_key":path.stem,"current_model_input":{"core7_ready":ready,"source_presence":{role:missing.get(role,True) for role in ("race_cards","stt","tkz","sui","original_exhibition")}},"source_audit":{"stt":{"availability_reason":"race_row_absent"},"tkz":{"availability_reason":"race_row_absent"},"original_exhibition":{"status":"missing"}}}
    path.write_text(json.dumps(doc))
    original.append((path,path.read_bytes()))
   result=diagnose(root,"20261025")
   self.assertEqual(result["counts"]["race_documents"],4)
   self.assertEqual(result["counts"]["core7_ready"],1)
   self.assertEqual(result["counts"]["missing_source_races"],2)
   self.assertEqual(result["counts"]["all_five_present_but_failed"],1)
   self.assertEqual(result["reasons"]["stt"]["race_row_absent"],1)
   self.assertTrue(all(p.read_bytes()==b for p,b in original))
if __name__=="__main__": unittest.main()
