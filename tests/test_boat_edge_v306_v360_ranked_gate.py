import unittest
from scripts.boat_edge_v306_v360_ranked_gate import inspect, MODEL, MODES

def fixture():
    tickets=[f"{a}-{b}-{c}" for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3]
    rows=[{"rank":i,"boat_combo":ticket,"course_combo":ticket,"relative_model_mass":1/120} for i,ticket in enumerate(tickets,1)]
    return {"research_ranked_120_schema":MODEL,
            "research_ranked_120_by_mode":{m:[dict(x) for x in rows] for m in MODES}}

class V306Tests(unittest.TestCase):
    def test_complete_ranked_modes(self):
        self.assertEqual(inspect(fixture()),"STRUCTURAL_TOP3_TOP5_TOP10_READY_NOT_ATTESTED")
    def test_missing_mode(self):
        x=fixture();del x["research_ranked_120_by_mode"]["national_motor"]
        self.assertEqual(inspect(x),"INVALID_MODES")
    def test_duplicate_ticket(self):
        x=fixture();rows=x["research_ranked_120_by_mode"]["national_only"];rows[1]["boat_combo"]=rows[0]["boat_combo"]
        self.assertEqual(inspect(x),"INVALID_TICKET")
    def test_rank_gap(self):
        x=fixture();x["research_ranked_120_by_mode"]["national_motor"][1]["rank"]=3
        self.assertEqual(inspect(x),"INVALID_RANK")
    def test_nan_mass_rejected(self):
        x=fixture();x['research_ranked_120_by_mode']['national_only'][0]['relative_model_mass']=float('nan')
        self.assertEqual(inspect(x),'INVALID_MASS')
    def test_infinite_mass_rejected(self):
        x=fixture();x['research_ranked_120_by_mode']['national_only'][0]['relative_model_mass']=float('inf')
        self.assertEqual(inspect(x),'INVALID_MASS')
    def test_missing_course_ticket(self):
        x=fixture();x['research_ranked_120_by_mode']['national_only'][0].pop('course_combo')
        self.assertEqual(inspect(x),'INVALID_COURSE_TICKET')
    def test_duplicate_course_ticket(self):
        x=fixture();rows=x['research_ranked_120_by_mode']['national_only'];rows[1]['course_combo']=rows[0]['course_combo']
        self.assertEqual(inspect(x),'INVALID_COURSE_TICKET')
    def test_mass_order_invalid(self):
        x=fixture();rows=x['research_ranked_120_by_mode']['national_only'];rows[0]['relative_model_mass']=0.001;rows[1]['relative_model_mass']=2/120-0.001
        self.assertEqual(inspect(x),'MASS_RANK_ORDER_INVALID')
    def test_inconsistent_course_boat_mapping(self):
        x=fixture();rows=x['research_ranked_120_by_mode']['national_only']
        rows[0]['boat_combo'],rows[1]['boat_combo']=rows[1]['boat_combo'],rows[0]['boat_combo']
        self.assertEqual(inspect(x),'INCONSISTENT_ENTRY_MAPPING')
    def test_cross_mode_entry_mismatch(self):
        x=fixture();rows=x['research_ranked_120_by_mode']['national_motor']
        for row in rows:
            row['course_combo']=row['course_combo'].replace('1','X').replace('2','1').replace('X','2')
        self.assertEqual(inspect(x),'CROSS_MODE_ENTRY_MISMATCH')
    def test_no_ranking(self):
        self.assertEqual(inspect({}),"NO_V360_RANKING")

if __name__=="__main__":
    unittest.main()
