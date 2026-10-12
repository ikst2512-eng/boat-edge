import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('p',ROOT/'scripts/boat_edge_v249_patch.py')
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
CSS=(ROOT/'assets/boat_edge_v249_focus.css').read_text(encoding='utf-8')
JS=(ROOT/'assets/boat_edge_v249_focus.js').read_text(encoding='utf-8')

class FocusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample='''<!doctype html><html><head><title>BOAT EDGE</title></head><body>
<main id="raceView" class="view"><div class="race-summary"><div class="summary-top"></div></div>
<div id="raceTabs"></div><section id="tab-pred"></section><section id="tab-before"></section>
<section id="tab-scenario"></section><section id="tab-card"></section></main>
<div id="be241HomeResults"></div><button data-view="raceView"></button></body></html>'''
    def test_add_refs(self):
        x=p.modify(self.sample)
        self.assertEqual(x.count(p.STYLE),1)
        self.assertEqual(x.count(p.SCRIPT),1)
    def test_idempotent(self):
        x=p.modify(self.sample)
        self.assertEqual(p.modify(x),x)
    def test_preserves_page_except_asset_refs(self):
        x=p.modify(self.sample)
        self.assertEqual(x.replace(p.STYLE+'\n','').replace(p.SCRIPT+'\n',''),self.sample)
    def test_no_silent_missing_race_root(self):
        with self.assertRaisesRegex(ValueError,'UNEXPECTED_SITE_STRUCTURE'):
            p.modify(self.sample.replace('id="raceTabs"','id="bad"'))
    def test_duplicate_document_end_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNEXPECTED_DOCUMENT_ENDINGS'):
            p.modify(self.sample+'</body>')
    def test_changed_asset_ref_must_fail_closed(self):
        s=p.modify(self.sample).replace('v249_focus.css?v=248','v249_focus.css?v=1')
        with self.assertRaisesRegex(ValueError,'ASSET_REF_DRIFT'):
            p.modify(s)
    def test_css_mobile_four_navigation(self):
        self.assertIn('repeat(4,minmax(0,1fr))',CSS)
        self.assertIn('#be249Focus .be249-anchors button',CSS)
    def test_css_six_racers_remain_visible(self):
        self.assertIn('.be203-card',CSS)
        self.assertNotIn('.be203-card{display:none',CSS.replace(' ',''))
    def test_css_table_horizontal_and_lanes(self):
        self.assertIn('overflow-x:auto',CSS)
        self.assertIn('th:first-child',CSS)
        self.assertIn('position:sticky',CSS)
    def test_navigation_reuses_existing_tab_click(self):
        self.assertIn('button.click()',JS)
        for token in ("'tickets'","'racers'","'scenario'","'before'"):
            self.assertIn(token,JS)
    def test_no_model_results_odds_fetch(self):
        for token in ('fetch(', 'XMLHttpRequest', 'localStorage.setItem', 'official_payout', 'winning_combo', 'getPrediction(', 'buildFallbackPrediction(', 'window.location=', 'location.href='):
            self.assertNotIn(token,JS)
    def test_guarded_frozen_state(self):
        for token in ('be181Source',"type==='final'","type==='first'","type==='latest'",'照合待ち'):
            self.assertIn(token,JS)
    def test_browser_navigation_keeps_selection(self):
        self.assertNotIn('loadRace(',JS)
        self.assertNotIn('state.currentVenue=',JS)
        self.assertNotIn('history.pushState(',JS)
    def test_no_formal_or_prediction_mutation(self):
        for name in ['results_seen','RESULT_UNLOCK_TOKEN','v234_scored','v240_frozen','updateOdds','setTickets','rankPredictions']:
            self.assertNotIn(name,JS)
    def test_source_status_no_fabricated_timestamp(self):
        self.assertNotIn('Date.now(',JS)
        self.assertIn('オッズは元の取得時刻表示を確認',JS)
    def test_focus_keyboard(self):
        self.assertIn('focus-visible',CSS)
        self.assertIn('onceButton',JS)
        self.assertIn("button.type='button'",JS)

if __name__=='__main__':unittest.main()
