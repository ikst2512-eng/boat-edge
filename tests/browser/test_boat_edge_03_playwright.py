#!/usr/bin/env python3
"""BOAT EDGE 03: offline Playwright iPhone-sized behavior checks.

Run after installing Playwright browsers:
  python -m playwright install chromium webkit
  python tests/browser/test_boat_edge_03_playwright.py

BOAT_EDGE_REQUIRED_BROWSERS=chromium may be used for a Chromium-only preflight;
it does NOT certify WebKit, iOS Safari, Pages, or production accuracy.
No live race, result, payout, or formal endpoint is requested.
"""
import os
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
CSS = (
    ROOT / "assets/boat_edge_v207_first_prediction.css",
    ROOT / "assets/boat_edge_v304_topk_mobile.css",
)
SCRIPT = ROOT / "assets/boat_edge_v207_first_prediction.js"
COMBOS = (
    "1-2-3", "1-3-2", "2-1-3", "2-3-1", "3-1-2",
    "3-2-1", "4-1-2", "4-2-1", "5-1-2", "6-1-2",
)
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head><body>
<div class="brandtext">BOAT EDGE <small>サイトV205</small></div>
<div id="raceView"><div class="race-summary"><div class="summary-top">浜名湖 1R</div></div>
  <div id="raceTabs"><button type="button" data-tab="before">直前</button>
  <button type="button" data-tab="scenario">展開</button></div>
  <div id="tab-pred"><div class="section stack"><section id="be108PredictionModes">
    <div class="be108-mode-tabs"><button type="button" class="on"
       data-be108-mode="hit">的中重視</button></div>
    <div class="be108-mode-top"><small>内部スコア</small><strong>未校正</strong></div>
    <div class="be181-freeze-banner" data-be181-source="first"></div>
    <div class="be108-ticket-list"></div>
    <div id="be204Budget"><span data-be204="total">10,000円</span></div>
  </section></div></div>
  <div id="scenarioHero"><div class="scenario-main">4号艇の攻めを確認中</div></div>
</div></body></html>"""


class MobilePredictionBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = sync_playwright()
        cls.pw = cls.manager.__enter__()
        cls.browsers = {}
        kinds = [s.strip() for s in os.getenv(
            "BOAT_EDGE_REQUIRED_BROWSERS", "chromium,webkit").split(",") if s.strip()]
        if not kinds:
            raise AssertionError("At least one browser is required")
        try:
            for kind in kinds:
                if kind not in ("chromium", "webkit"):
                    raise AssertionError("Only Chromium and WebKit are approved for UI checks")
                browser_type = getattr(cls.pw, kind)
                extra = {}
                if kind == "chromium" and os.getenv("BOAT_EDGE_CHROMIUM_EXECUTABLE"):
                    extra["executable_path"] = os.environ["BOAT_EDGE_CHROMIUM_EXECUTABLE"]
                    extra["args"] = ["--no-sandbox"]
                # Missing WebKit is a setup FAIL, never a silent Safari PASS.
                cls.browsers[kind] = browser_type.launch(headless=True, **extra)
        except Exception:
            for browser in cls.browsers.values():
                browser.close()
            cls.manager.__exit__(None, None, None)
            raise

    @classmethod
    def tearDownClass(cls):
        for browser in cls.browsers.values():
            browser.close()
        cls.manager.__exit__(None, None, None)

    def boot(self, browser, width=390):
        context = browser.new_context(
            viewport={"width": width, "height": 844}, device_scale_factor=2,
            is_mobile=True, has_touch=True, locale="ja-JP", timezone_id="Asia/Tokyo",
            color_scheme="light",
        )
        page = context.new_page()
        # Bound missing selectors/actions; never wait 30s per broken mobile interaction.
        page.set_default_timeout(12000)
        page.set_content(HTML)
        for path in CSS:
            page.add_style_tag(path=str(path))
        # All ten are synthetic, valid, distinct 3連単 combos, not predictions.
        rows = "".join(
            '<div class="be108-ticket" data-be257-view="reference">'
            '<b>' + combo + '</b><em>相対重み</em><small>倍率未確認</small>'
            '<div class="be140-ticket-money">現在の参考配分 1,000円</div></div>'
            for combo in COMBOS
        )
        page.locator(".be108-ticket-list").evaluate(
            "(node, rows) => { node.innerHTML = rows; }", rows
        )
        page.evaluate("""() => {
          window.state = {race:{race_key:'20261014-06-01'}};
          window.boatEdgeTestKind = 'partial';
          window.BoatEdgeV205 = {sourceStatus:()=>({
            kind:window.boatEdgeTestKind,
            title:window.boatEdgeTestKind==='stop'?'買い目停止':'出走照合済み',
            detail:'合成データ・実出走の証明ではない'
          })};
          window.BoatEdgeV204 = {
            summarize:()=>({settled:false,fresh:false}),
            sourceLabel:()=> 'FIRST保存（合成）',
            oddsProof:()=>({quality:'unknown',label:'未取得'}),
            parsePayout:()=>null
          };
        }""")
        page.add_script_tag(path=str(SCRIPT))
        # Injected scripts may observe a document whose DOMContentLoaded event
        # happened before injection. Trigger the listener if pending, then render
        # the source-only panel explicitly (the real code guards duplicate init).
        page.evaluate("""() => {
          document.dispatchEvent(new Event('DOMContentLoaded'));
          window.BoatEdgeV207.render();
        }""")
        page.locator("#be207Top.ready").wait_for()
        return context, page

    def test_top3_top5_top10_order_and_reference_amount(self):
        for kind, browser in self.browsers.items():
            with self.subTest(browser=kind):
                context, page = self.boot(browser)
                try:
                    tickets = page.locator("#be207Top .be207-bets > .be207-ticket")
                    self.assertEqual(tickets.count(), 3)
                    self.assertEqual("".join(tickets.first.locator(".be207-lane").all_text_contents()), "123")
                    page.locator('#be207Top [data-be207="five"]').click()
                    self.assertEqual(tickets.count(), 5)
                    page.locator('#be207Top [data-be207="ten"]').click()
                    self.assertEqual(tickets.count(), 10)
                    self.assertEqual(
                        "".join(tickets.nth(9).locator(".be207-lane").all_text_contents()), "612"
                    )
                    self.assertIn("参考配分", tickets.first.inner_text())
                    self.assertIn("10,000円", page.locator("#be207Top .be207-budget").inner_text())
                    self.assertIn("未校正", page.locator("#be207Top .be259-confidence").inner_text())
                    self.assertIn("4号艇の攻め", page.locator("#be207Top .be207-explain").inner_text())
                    self.assertIn("FIRST", page.locator("#be207Top .be207-freeze").inner_text())
                    self.assertIn("未確認", page.locator("#be207Top .be207-odds").inner_text())
                finally:
                    context.close()

    def test_prediction_display_state_from_source_and_deadline(self):
        """Display-only waiting/provisional/final/closed statuses in real mobile browsers."""
        for kind, browser in self.browsers.items():
            with self.subTest(browser=kind):
                context, page = self.boot(browser, 390)
                try:
                    states = page.evaluate("""() => {
                      const date=new Date(Date.now()+9*3600000).toISOString().slice(0,10);
                      const key=date.replaceAll('-','')+'-06-01';
                      const d={race_key:key,meta:{date,venue_code:'06',race_no:1,deadline:'23:59'}};
                      const f=window.BoatEdgeV207.predictionDisplayPhase;
                      const before=Date.parse(date+'T12:00:00+09:00');
                      const after=Date.parse(date+'T23:59:05+09:00');
                      return [
                        f(d,'first',true,false,before),
                        f(d,'first',false,false,before),
                        f(d,'final',false,false,before),
                        f(d,'final',false,false,after),
                        f(d,'first',true,false,after),
                        f({...d,meta:{...d.meta,venue_code:'02'}},'final',false,false,before)
                      ];
                    }""")
                    self.assertEqual([x["phase"] for x in states],
                        ["waiting","provisional","final-source","closed","closed","unverified"])
                    self.assertIn("暫定",states[1]["title"])
                    self.assertIn("最終",states[2]["title"])
                    self.assertIn("独立",states[2]["detail"])
                    self.assertIn("保存",states[3]["detail"])
                    self.assertIn("非表示",states[4]["detail"])
                    page.evaluate("""() => {
                      const date=new Date(Date.now()+9*3600000).toISOString().slice(0,10);
                      window.state.race={race_key:date.replaceAll('-','')+'-06-01',
                         meta:{date,venue_code:'06',race_no:1,deadline:'23:59'}};
                      window.BoatEdgeV207.render();
                    }""")
                    phase = page.locator("#be207Top .be207-display-phase")
                    self.assertTrue(phase.is_visible())
                    self.assertEqual(phase.get_attribute("role"),"status")
                    self.assertIn(phase.get_attribute("data-phase"),
                        ("provisional","closed"))
                    self.assertTrue(phase.locator("strong").inner_text().strip())
                    self.assertEqual(page.locator("#be207Top .be207-ticket").count(),3)
                finally:
                    context.close()

    def test_blocked_tickets_hide_amounts_and_odds(self):
        for kind, browser in self.browsers.items():
            with self.subTest(browser=kind):
                context, page = self.boot(browser)
                try:
                    page.evaluate("""() => {
                      window.boatEdgeTestKind='stop';window.BoatEdgeV207.render();
                    }""")
                    self.assertEqual(page.locator("#be207Top .be207-ticket").count(), 0)
                    self.assertIn("買い目を停止", page.locator("#be207Top .be207-budget").inner_text())
                    self.assertNotIn("10,000円", page.locator("#be207Top .be207-budget").inner_text())
                    self.assertIn("非表示", page.locator("#be207Top .be207-odds").inner_text())
                    self.assertEqual(page.locator('[data-be259="head"]').inner_text(), "未確認")
                finally:
                    context.close()

    def test_race_switch_discards_old_list_until_new_dom(self):
        for kind, browser in self.browsers.items():
            with self.subTest(browser=kind):
                context, page = self.boot(browser)
                try:
                    page.evaluate("""() => {
                      window.state.race.race_key='20261014-06-02';
                      window.BoatEdgeV207.render();
                    }""")
                    self.assertEqual(page.locator("#be207Top .be207-ticket").count(), 0)
                    self.assertIn("前レースの買い目は表示しません",
                                  page.locator("#be207Top .be207-stop").inner_text())
                    page.evaluate("""() => {
                      const old=document.querySelector('.be108-ticket-list');
                      const replacement=old.cloneNode(true);
                      replacement.querySelector('b').textContent='6-5-4';
                      old.replaceWith(replacement);
                      window.BoatEdgeV207.render();
                    }""")
                    self.assertEqual(page.locator("#be207Top .be207-ticket").count(), 3)
                    self.assertEqual(
                        "".join(page.locator("#be207Top .be207-ticket").first
                        .locator(".be207-lane").all_text_contents()), "654"
                    )
                    self.assertNotIn("123", page.locator("#be207Top .be207-bets").inner_text())
                finally:
                    context.close()

    def test_touch_targets_narrow_mobile(self):
        for kind, browser in self.browsers.items():
            for width in (320, 375, 390, 430):
                with self.subTest(browser=kind, width=width):
                    context, page = self.boot(browser, width)
                    try:
                        for selector in (
                            '#be207Top [data-be207="five"]',
                            '#be207Top [data-be207="ten"]',
                            '#be207Top .be305-evidence-head button',
                        ):
                            locator = page.locator(selector)
                            self.assertTrue(locator.is_visible(), selector)
                            rect = locator.bounding_box()
                            self.assertGreaterEqual(rect["height"], 44, selector)
                            self.assertGreaterEqual(rect["width"], 44, selector)
                        page.locator('#be207Top [data-be207="ten"]').tap()
                        self.assertEqual(page.locator("#be207Top .be207-ticket").count(), 10)
                        screenshot_dir = os.getenv("BOAT_EDGE_SCREENSHOT_DIR")
                        if screenshot_dir and width == 390:
                            dest = Path(screenshot_dir)
                            dest.mkdir(parents=True, exist_ok=True)
                            page.screenshot(path=str(dest / f"boatedge03_{kind}_{width}.png"),
                                            full_page=True)
                    finally:
                        context.close()


    def test_six_boat_comparison_original_and_head_focus(self):
        # Reuse the actual V206 comparison renderer, but no external data/forecast.
        for kind, browser in self.browsers.items():
            with self.subTest(browser=kind):
                context, page = self.boot(browser, 390)
                try:
                    page.locator("#tab-pred .section.stack").evaluate("""host => {
                      host.insertAdjacentHTML('afterbegin',
                        '<div id="be203Layout"></div><div id="be204Overview"></div>');
                      window.state.race.meta = {phase:'PRE_RESULT',
                        results_seen:false,unlock:false,scoring:false,
                        deadline:'18:00'};
                      window.BoatEdgeV203 = {getRows:()=>Array.from(
                        {length:6},(_,i)=>({
                          lane:i+1,name:'選手'+(i+1),grade:'A1',
                          national:{win_rate:5+i*0.2,quinella_rate:30},
                          local:{win_rate:4.5,quinella_rate:28},
                          motor:{quinella_rate:35},
                          time:null,st:null,lap:null,turn:null,straight:null
                        }))};
                    }""")
                    page.add_style_tag(path=str(ROOT / "assets/boat_edge_v206_quickview.css"))
                    page.add_script_tag(path=str(ROOT / "assets/boat_edge_v206_quickview.js"))
                    page.evaluate("""() => {
                      document.dispatchEvent(new Event('DOMContentLoaded'));
                      window.BoatEdgeV206.sync();
                    }""")
                    page.locator("#be206Quick").wait_for()
                    # V376: legacy desktop-style matrix and V371 mobile row
                    # default are both supported, but each must show all six.
                    racer_rows=page.locator("#be206Quick .be206-table tbody tr").count()
                    lane_columns=page.locator("#be206Quick .be206-matrix th[data-be206-lane]").count()
                    if (ROOT / "assets/boat_edge_v371_simple_ui.css").is_file():
                        self.assertEqual(racer_rows, 6, "mobile row default must show all six racers")
                        self.assertEqual(lane_columns, 0, "hidden legacy matrix must not duplicate the six racers")
                        self.assertTrue(page.locator("#be206Quick .be206-table-scroll").is_visible())
                    else:
                        self.assertEqual(lane_columns, 6, "legacy default must retain six lanes")
                    # Explicit user toggle must still restore the six-lane matrix,
                    # with correct original-exhibition missingness and back to rows.
                    page.locator('#be206Quick [data-be206-layout="lanes"]').tap()
                    self.assertEqual(
                        page.locator('#be206Quick .be206-matrix th[data-be206-lane]').count(), 6
                    )
                    page.locator('#be206Quick [data-be206-metric="original"]').tap()
                    self.assertEqual(page.locator("#be206Quick .be206-matrix tbody tr").count(), 3)
                    # Absent original exhibition never becomes a made-up numeric value.
                    self.assertIn("－", page.locator("#be206Quick .be206-matrix").inner_text())
                    page.locator('#be206Quick [data-be206-layout="rows"]').tap()
                    self.assertTrue(page.locator("#be206Quick .be206-table-scroll").is_visible())
                    page.locator('.be206-table-scroll [data-be206-head="1"]').click()
                    panel = page.locator("#be206HeadPanel")
                    self.assertTrue(panel.is_visible())
                    self.assertIn("1-2-3", panel.inner_text())
                    panel.locator("[data-be206-head-close]").click()
                    self.assertTrue(panel.is_hidden())
                    self.assertEqual(
                        page.evaluate("document.activeElement?.dataset?.be206Head || ''"), "1"
                    )
                finally:
                    context.close()



    def test_actual_race_loader_last_selection_wins_and_404_is_nonblocking(self):
        """Execute the actual index.html race loader in both mobile engines.

        The fetches are synthetic, pre-result-only; no result/odds/final data.
        This specifically catches late responses overwriting the selected race.
        """
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        start = html.index("/* BOAT EDGE 03: last selected race wins.")
        end = html.index("async function refreshFormalStatus(){", start)
        actual_loader = html[start:end]
        self.assertIn("be03RaceRequestSerial", actual_loader)
        self.assertIn("be03RaceLoadNotice", actual_loader)
        for kind, browser in self.browsers.items():
            with self.subTest(browser=kind):
                context = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    device_scale_factor=2, is_mobile=True, has_touch=True,
                    locale="ja-JP", timezone_id="Asia/Tokyo",
                )
                page = context.new_page()
                page.set_default_timeout(12000)
                try:
                    page.set_content("""<!doctype html><meta name="viewport"
                     content="width=device-width,initial-scale=1">
                     <style>.view:not(.active){display:none}.be03-retry-button{min-height:44px}</style>
                     <main id="homeView" class="view"></main>
                     <div id="raceView" class="view active">
                     <div class="race-summary"><div class="summary-top" id="raceTitle">以前のレース</div></div>
                     <div id="be207Top">以前のレースの買い目</div></div>
                     <span id="live">正常</span><div id="refreshToast"></div>""")
                    page.evaluate("""() => {
                      window.state={currentVenue:'14',race:{race_key:'20261014-14-10'}};
                      window.__renders=[];
                      window.__toasts=[];
                      window.alert=()=>{throw new Error('blocking alert is forbidden')};
                      window.be182FetchScratch=async race=>race;
                      window.refreshFormalStatus=async()=>{};
                      window.loadFormalOverlay=async()=>null;
                      window.mergeFormalOverlay=(race)=>race;
                      window.renderRace=(race)=>{
                        window.state.race=race;
                        window.__renders.push(race.race_key);
                        document.querySelector('#raceTitle').textContent=race.meta.race_no+'R';
                      };
                      window.showToast=(message)=>{window.__toasts.push(message)};
                      window.fetch=(url)=>new Promise(resolve=>{
                        const file=String(url);
                        const delay=file.includes('20261014-14-01.json')?230:15;
                        setTimeout(()=>{
                          if(file.includes('20261014-14-03.json') &&
                             !window.__allowHomeRetry)resolve({ok:false,status:404});
                          else{
                            const n=file.includes('20261014-14-01.json')?1:
                              file.includes('20261014-14-03.json')?3:2;
                            resolve({ok:true,json:async()=>({
                              race_key:'20261014-14-0'+n,
                              meta:{date:'2026-10-14',venue_code:'14',race_no:n,
                                phase:'PRE_RESULT',results_seen:false,
                                unlock:false,scoring:false}
                            })});
                          }
                        },delay);
                      });
                    }""")
                    page.add_script_tag(content=actual_loader)
                    result = page.evaluate("""async () => {
                      const earlier=loadRace('data/races/20261014-14-01.json','14');
                      const newer=loadRace('data/races/20261014-14-02.json','14');
                      await Promise.all([earlier,newer]);
                      return {key:state.race.race_key,renders:window.__renders,
                        loading:document.getElementById('raceView').classList
                          .contains('be03-race-loading'),
                        note:document.getElementById('be03RaceLoadNotice')?.textContent||''};
                    }""")
                    self.assertEqual(result["key"], "20261014-14-02")
                    self.assertEqual(result["renders"], ["20261014-14-02"])
                    self.assertFalse(result["loading"])
                    self.assertFalse(result["note"])
                    self.assertEqual(page.locator("#raceTitle").inner_text(), "2R")
                    failed = page.evaluate("""async () => {
                      await loadRace('data/races/20261014-14-03.json','14');
                      const note=document.getElementById('be03RaceLoadNotice');
                      return {key:state.race.race_key,role:note?.getAttribute('role'),
                        message:note?.textContent||'',
                        loading:document.getElementById('raceView').classList
                          .contains('be03-race-loading'),
                        toast:window.__toasts.at(-1)||''};
                    }""")
                    self.assertEqual(failed["key"], "20261014-14-02")
                    self.assertEqual(failed["role"], "alert")
                    self.assertIn("404", failed["message"])
                    self.assertFalse(failed["loading"])
                    self.assertIn("404", failed["toast"])
                    self.assertEqual(page.locator("#raceTitle").inner_text(), "2R")
                    # A well-formed but mismatched selected file must also fail closed.
                    mismatch = page.evaluate("""async () => {
                      await loadRace('data/races/20261014-14-04.json','14');
                      const note=document.getElementById('be03RaceLoadNotice');
                      return {key:state.race.race_key,role:note?.getAttribute('role'),
                        message:note?.textContent||''};
                    }""")
                    self.assertEqual(mismatch["key"], "20261014-14-02")
                    self.assertEqual(mismatch["role"], "alert")
                    self.assertIn("一致しません", mismatch["message"])
                    self.assertEqual(page.locator("#raceTitle").inner_text(), "2R")
                    # First selection while only HOME is visible must
                    # keep the error visible, actionable, and race-scoped.
                    home_fail = page.evaluate("""async () => {
                      document.getElementById('raceView').classList.remove('active');
                      document.getElementById('homeView').classList.add('active');
                      await loadRace('data/races/20261014-14-03.json','14');
                      const note=document.getElementById('be03HomeRaceLoadNotice');
                      return {role:note?.getAttribute('role'),
                        message:note?.textContent||'',
                        visible:!!note&&getComputedStyle(note).display!=='none',
                        retry:note?.querySelector('button')?.textContent||'',
                        key:state.race.race_key};
                    }""")
                    self.assertEqual(home_fail["role"], "alert")
                    self.assertTrue(home_fail["visible"])
                    self.assertIn("404", home_fail["message"])
                    self.assertIn("再取得", home_fail["retry"])
                    self.assertEqual(home_fail["key"], "20261014-14-02")
                    button = page.locator('#be03HomeRaceLoadNotice .be03-retry-button')
                    self.assertTrue(button.is_visible())
                    self.assertGreaterEqual(button.bounding_box()["height"], 44)
                    page.evaluate("window.__allowHomeRetry=true")
                    button.tap()
                    page.wait_for_function(
                        """() => state.race.race_key === '20261014-14-03' &&
                            !document.querySelector('#be03HomeRaceLoadNotice') &&
                            !document.querySelector('#be03RaceLoadNotice')""",
                        timeout=12000
                    )
                    self.assertEqual(page.locator("#raceTitle").inner_text(), "3R")
                    # Mismatched venue/code must not create a retry control.
                    page.evaluate("""() => {
                      be03RaceLoadNotice('出走表取得に失敗',true,
                        {file:'data/races/20261014-14-01.json',jcd:'24'});
                    }""")
                    self.assertEqual(page.locator('#be03HomeRaceLoadNotice button').count(), 0)
                    page.evaluate("() => be03RaceLoadNotice('')")
                    self.assertEqual(page.locator('#be03HomeRaceLoadNotice').count(), 0)
                    screenshot_dir = os.getenv("BOAT_EDGE_SCREENSHOT_DIR")
                    if screenshot_dir:
                        dest = Path(screenshot_dir)
                        dest.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(dest / f"be03_race_switch_{kind}.png"))
                finally:
                    context.close()


    def test_midnight_catalog_guard_hides_prior_day_home_races(self):
        """Real Chromium/WebKit, same production guard, result-unseen synthetic."""
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        a = html.index("function be03UsableTodayCatalog(data){")
        b = html.index("async function refreshModel(){", a)
        script = html[a:b]
        assert "data-be03-catalog" in html
        for kind, browser in self.browsers.items():
            with self.subTest(browser=kind):
                context = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    device_scale_factor=2, is_mobile=True, has_touch=True,
                    locale="ja-JP", timezone_id="Asia/Tokyo")
                page = context.new_page()
                try:
                    page.set_content("""<!doctype html><meta name="viewport"
                      content="width=device-width,initial-scale=1">
                      <style>
                      #homeView[data-be03-catalog="blocked"] #be108Hub,
                      #homeView[data-be03-catalog="blocked"] #deadlineBoard,
                      #homeView[data-be03-catalog="blocked"] #venues{display:none!important}
                      </style>
                      <main id="homeView" class="view active">
                      <div id="be108Hub">legacy hub race choices</div>
                      <div id="deadlineBoard">last-day race</div>
                      <div id="venues">last-day venues</div></main>
                      <div id="live">-</div>""")
                    page.evaluate("""() => {
                      const now=new Date(Date.now()+9*3600000);
                      const yesterday=new Date(now.getTime()-86400000);
                      const today=now.toISOString().slice(0,10);
                      const prior=yesterday.toISOString().slice(0,10);
                      const card=date=>({date,phase:'PRE_RESULT',
                        results_seen:false,unlock:false,scoring:false,
                        venues:[{jcd:'02',races:[{
                          race_key:date.replaceAll('-','')+'-02-01',
                          race_no:1,file:'data/races/'+date.replaceAll('-','')+'-02-01.json'
                        }]}]});
                      window.state={today:card(prior)};
                      window.__card=card(prior);
                      window.__errors=0;
                      window.renderHome=()=>{};
                      window.updateSystemBanner=()=>{};
                      window.fetch=async()=>({ok:true,json:async()=>window.__card});
                      window.__validCard=card(today);
                    }""")
                    page.add_script_tag(content=script)
                    page.evaluate("async()=>await refreshToday()")
                    note = page.locator("#be03TodayCatalogNotice")
                    self.assertTrue(note.is_visible())
                    self.assertEqual(note.get_attribute("role"), "alert")
                    self.assertEqual(page.locator("#homeView").get_attribute(
                        "data-be03-catalog"), "blocked")
                    self.assertFalse(page.locator("#be108Hub").is_visible())
                    self.assertFalse(page.locator("#deadlineBoard").is_visible())
                    self.assertEqual(page.evaluate("state.today"), None)
                    page.evaluate("""async()=>{
                       window.__card=window.__validCard;
                       await refreshToday();
                    }""")
                    self.assertEqual(note.count(), 0)
                    self.assertTrue(page.locator("#be108Hub").is_visible())
                    self.assertIsNone(page.locator("#homeView").get_attribute(
                        "data-be03-catalog"))
                    self.assertEqual(page.evaluate("state.today.date"),
                                     page.evaluate("window.__validCard.date"))
                finally:
                    context.close()

    def test_early_card_real_renderer_mobile_status_and_race_switch(self):
        """Run the production V392 UI with synthetic, result-free data in both engines."""
        for kind, browser in self.browsers.items():
            with self.subTest(browser=kind):
                context = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    device_scale_factor=2, is_mobile=True, has_touch=True,
                    locale="ja-JP", timezone_id="Asia/Tokyo",
                )
                page = context.new_page()
                page.set_default_timeout(12000)
                try:
                    page.set_content("""<!doctype html><meta name="viewport"
                     content="width=device-width,initial-scale=1">
                     <div id="tab-pred"><div class="section stack">
                     <div id="predictionAlert"></div></div></div>""")
                    page.add_script_tag(path=str(
                        ROOT / "assets/boat_edge_v392_early_prediction.js"))
                    result = page.evaluate("""async () => {
                      // Always use next JST calendar day; never request results.
                      const date = new Date(Date.now()+9*3600000+86400000)
                        .toISOString().slice(0,10);
                      const key = date.replaceAll('-','')+'-14-01';
                      const fetched = new Date(Date.now()-60000).toISOString();
                      const produced = new Date().toISOString();
                      const racers = Array.from({length:6},(_,i)=>({
                        lane:i+1,registration_no:String(5001+i),class:'B1',
                        avg_st:0.16,national:{win_rate:5},local:{win_rate:4},
                        motor:{quinella_rate:35},raw_text:'出走表'
                      }));
                      const race={race_key:key,
                        meta:{date,venue_code:'14',race_no:1,deadline:'23:59',
                          phase:'PRE_RESULT',results_seen:false,unlock:false,
                          scoring:false},
                        source_audit:{race_card:{status:'ok',fetched_at:fetched,
                          sha256:'a'.repeat(64)}},racers};
                      const inputs=racers.map(x=>[x.lane,x.registration_no,
                        x.class,x.avg_st,x.national.win_rate,x.local.win_rate,
                        x.motor.quinella_rate]);
                      const combos=[];
                      for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)
                        for(let c=1;c<=6;c++)
                          if(new Set([a,b,c]).size===3)combos.push(a+'-'+b+'-'+c);
                      const preview={
                        schema:'BOAT_EDGE_V392_CARD_ONLY_PREVIEW_V1',
                        model_id:'V392-CARD-HEURISTIC-UNCALIBRATED',
                        prediction_kind:'EARLY_CARD_ONLY_REFERENCE_NOT_FINAL',
                        race_key:key,source_date:date,deadline:'23:59',
                        produced_at:produced,source_card_fetched_at:fetched,
                        source_card_sha256:'a'.repeat(64),
                        card_fingerprint_sha256:'b'.repeat(64),
                        racer_inputs_by_lane:inputs,head_candidate:1,
                        ranked_120:combos.map((combo,i)=>({
                          combo,rank:i+1,relative_score:120-i
                        })),
                        top3:combos.slice(0,3),top5:combos.slice(0,5),
                        top10:combos.slice(0,10),
                        guards:{results_seen:false,unlock:false,scoring:false},
                        formal_fresh_claim:false,
                        score_is_calibrated_probability:false,
                        odds_used:false,betting_enabled:false,stake_yen:null
                      };
                      window.state={race};
                      window.fetch=async()=>({ok:false,status:404});
                      await BoatEdgeV392.render(race);
                      const missing=document.querySelector('#be392EarlyPreview');
                      const missingOk=missing.dataset.ready==='status'
                        &&missing.textContent.includes('まだ公開')
                        &&missing.querySelectorAll('.be392-lines li').length===0;
                      window.fetch=async()=>({ok:true,json:async()=>preview});
                      await BoatEdgeV392.render(race);
                      const ready=document.querySelector('#be392EarlyPreview');
                      const readyOk=ready.dataset.ready==='true'
                        &&ready.querySelectorAll('.be392-lines li').length===10
                        &&ready.textContent.includes('未凍結');
                      ready.querySelector('button[data-count="3"]').click();
                      const threeOk=ready.querySelectorAll('.be392-lines li').length===3;
                      ready.querySelector('button[data-count="5"]').click();
                      const fiveOk=ready.querySelectorAll('.be392-lines li').length===5;
                      const blocked={...race,racers:racers.map((x,i)=>
                        i===0?{...x,status:'欠場'}:x)};
                      await BoatEdgeV392.render(blocked);
                      const blockedOk=ready.dataset.ready==='status'
                        &&ready.textContent.includes('欠場')
                        &&ready.querySelectorAll('.be392-lines li').length===0;
                      // A delayed request for race 1 cannot repaint race 2.
                      let resolveOld;
                      window.fetch=()=>new Promise(resolve=>resolveOld=resolve);
                      const oldRequest=BoatEdgeV392.render(race);
                      const nextRace={...race,race_key:key.slice(0,-2)+'02',
                        meta:{...race.meta,race_no:2}};
                      window.fetch=async()=>({ok:false,status:404});
                      window.state.race=nextRace;
                      await BoatEdgeV392.render(nextRace);
                      resolveOld({ok:true,json:async()=>preview});
                      await oldRequest;
                      const current=document.querySelector('#be392EarlyPreview');
                      const switchOk=current.dataset.raceKey===nextRace.race_key
                        &&current.dataset.ready==='status'
                        &&current.querySelectorAll('.be392-lines li').length===0;
                      return {missingOk,readyOk,threeOk,fiveOk,blockedOk,switchOk,
                        state:current.dataset.ready,reason:current.textContent};
                    }""")
                    for label in ("missingOk", "readyOk", "threeOk", "fiveOk",
                                  "blockedOk", "switchOk"):
                        self.assertTrue(result[label], f"{kind} {label}: {result}")
                    screenshot_dir = os.getenv("BOAT_EDGE_SCREENSHOT_DIR")
                    if screenshot_dir:
                        dest = Path(screenshot_dir)
                        dest.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(dest / f"be03_early_status_{kind}.png"))
                finally:
                    context.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
