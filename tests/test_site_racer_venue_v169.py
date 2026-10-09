import csv, io, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"scripts"))
from site_racer_venue_v169 import aggregate_pairs, calculate_comparison, derive_racer, fetch_pair, THRU
from datetime import date

def cs(rows):
    o=io.StringIO();w=csv.DictWriter(o,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);return o.getvalue().encode()

def fixture(venue='14', code='202610071401', finish=['1','3','5']):
    r={'レースコード':code,'レース場':venue,'決まり手':'逃　げ'}
    c={'レースコード':code,'レース場コード':venue}
    for n in range(1,7):
        c[f'艇{n}_登録番号']=str(4100+n)
        r[f'{n}コース_艇番']=str(n)
    for k in range(1,4):r[f'{k}着_艇番']=finish[k-1]
    return ('20261007',cs([r]),cs([c]))

class V169Test(unittest.TestCase):
    def test_counts_and_methods(self):
        stats, audit=aggregate_pairs([fixture()]); self.assertEqual(audit['eligible_races'],1)
        self.assertEqual(stats['4101']['venues']['14']['wins'],1)
        self.assertEqual(stats['4103']['venues']['14']['top3'],1)
        self.assertEqual(stats['4102']['venues']['14']['top3'],0)
        self.assertEqual(stats['4101']['all']['win_methods'],{'逃げ':1})
    def test_missing_card(self):
        d,res,card=fixture();card=card.replace(b'202610071401',b'202610071402')
        stats,a=aggregate_pairs([(d,res,card)]); self.assertEqual(a['skipped_unpaired'],1);self.assertEqual(len(stats),0)
    def test_corrupt_course_rejected(self):
        d,res,card=fixture();res=res.replace(b',4,5,6,',b',4,5,5,')
        stats,a=aggregate_pairs([(d,res,card)]);self.assertEqual(a['eligible_races'],0)
    def test_invalid_finish_rejected(self):
        stats,a=aggregate_pairs([fixture(finish=['1','1','5'])]);self.assertEqual(a['eligible_races'],0)
    def test_course_mix_and_label(self):
        p={'all':{'courses':{'1':{'starts':20,'top3':10}},'starts':20},'venues':{'14':{'starts':4,'top3':4,'courses':{'1':{'starts':4,'top3':4}}}}}
        x=calculate_comparison(p,'14');self.assertEqual(x['course_adjusted_expected_pct'],50);self.assertFalse(x['eligible_label'])
    def test_sparse_venue_missing(self):
        self.assertIsNone(calculate_comparison({'venues':{},'all':{}},'14'))
    def test_pin_hard_stop(self):
        with self.assertRaises(ValueError):fetch_pair(date(2026,10,8))
    def test_venue_split(self):
        a,b=fixture('14','202610071401'),fixture('02','202610070201')
        stats, audit=aggregate_pairs([a,b]); self.assertEqual(len(stats['4101']['venues']),2)
        self.assertEqual(stats['4101']['all']['starts'],2)

if __name__=='__main__':unittest.main()
