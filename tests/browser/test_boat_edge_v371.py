"""BOAT EDGE V371: offline Playwright visual/interaction checks of actual UI stylesheet.

Run on checked-out repository:
  python -m playwright install chromium webkit
  python tests/browser/test_boat_edge_v371.py --engine chromium
  python tests/browser/test_boat_edge_v371.py --engine webkit
Optional --screenshots /tmp/boat-edge-v371-shots. Browser emulation != physical Safari.
No site fetches, results, payouts, prediction model, or formal Fresh access.
"""
import argparse
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
STYLE = ROOT / "assets" / "boat_edge_v371_simple_ui.css"

# Static UI fixture, not a fabricated real-race prediction.
FIXTURE = """<!doctype html><html lang="ja"><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:#fff;font-family:Arial,sans-serif}
.app{width:100%;max-width:1080px;margin:auto}.topbar{padding:10px}
#homeView .hero,#homeView>.section{padding:12px;background:#f00}
.be108-venue-grid{display:grid}.be108-venue{padding:10px}
.be207-ticket{display:grid}.be207-moneys{display:flex}
.be207-condition{padding:8px}.be206-table{border-collapse:collapse}
.be206-table td,.be206-table th{padding:6px;border:1px solid #ccc}
.be206-layout-switch button,.be207-actions button{padding:10px}
</style><link rel="stylesheet" href="./assets/boat_edge_v371_simple_ui.css"></head>
<body><div class="app">
<header class="topbar"><a class="be241-brand-home" href="#">BOAT EDGE</a></header>
<main id="homeView">
 <div id="be108Hub"><div class="be108-shell">
  <div id="be135Upcoming"><div class="be135-upcoming-head">まもなく締切</div></div>
  <div class="be108-date-nav">本日のレース</div>
  <div class="be108-venue-grid">
   <button class="be108-venue active"><b>桐生</b></button><button class="be108-venue active"><b>戸田</b></button>
   <button class="be108-venue active"><b>浜名湖</b></button><button class="be108-venue active"><b>尼崎</b></button>
   <button class="be108-venue active"><b>若松</b></button><button class="be108-venue active"><b>大村</b></button>
  </div>
  <div class="be108-place"><div class="be108-race-strip">
  <button class="be108-race-chip">1R</button><button class="be108-race-chip">2R</button><button class="be108-race-chip">3R</button>
  <button class="be108-race-chip">4R</button><button class="be108-race-chip">5R</button><button class="be108-race-chip">6R</button>
  </div></div>
 </div></div>
 <section class="hero">旧トップ説明</section><section class="section">旧ダッシュボード</section>
 <section class="be241-home-shortcuts">旧リンク集</section>
</main>
<main id="raceView">
 <div class="race-head"><div class="race-summary">
  <div class="summary-top"><h1 id="raceTitle">浜名湖 1R</h1><div id="deadlineBig">10:50</div></div>
  <div id="be108RaceNav"><div class="be108-race-strip"><button class="be108-race-chip">1R</button></div></div>
 </div><div id="raceTabs"><button data-tab="pred">予想</button><button data-tab="scenario">展開</button><button data-tab="before">直前</button></div></div>
 <section id="tab-pred"><div class="section stack">
  <section id="be207Top">
   <div class="be207-topline"><strong>3連単の予想</strong><span class="be207-version">画面番号</span></div>
   <div class="be207-condition"><strong>欠場・取消確認待ち</strong><span>買い目は非表示</span></div>
   <div class="be305-evidence"><div class="be305-evidence-head"><b>取得状況</b><button type="button">詳しく</button></div><div class="be305-evidence-items">取得証跡の詳細</div><small>長い注記</small></div>
   <div class="be207-modes"><button class="on">的中重視</button><button>バランス</button></div>
   <div class="be207-explain"><strong>展開</strong><span>先頭艇の攻防</span></div>
   <section class="be259-head-coverage"><div class="be259-head-row"><small>Top1の1着</small><strong>1号艇</strong></div>
    <div class="be259-top-grid"><span>Top3 1-2-3</span><span>Top5</span><span>Top10</span></div>
    <div class="be259-confidence">未校正値の詳細</div><div class="be259-disclaimer">長い注意書き</div></section>
   <div class="be207-bets"><div class="be207-ticket"><span class="be207-rank">1</span>
      <span class="be207-combo"><b class="be207-lane">1</b><b class="be207-lane">2</b><b class="be207-lane">3</b></span>
      <span class="be207-multi">10.0倍</span><div class="be207-moneys">参考配分 1,000円</div><span class="be207-prob">相対重み</span></div></div>
   <div class="be207-budget">参考配分合計 10,000円</div><div class="be207-odds">公式オッズ未確認</div>
   <div class="be208-detail-actions"><button id="detail" type="button">詳しいデータ・監査を開く</button></div>
  </section>
  <section id="be206Quick"><div class="be206-title"><h2>6艇比較</h2></div>
   <div class="be206-switch"><button>基本</button><button>直前・展示</button><button>オリ展</button><button>連対</button></div>
   <div class="be206-layout-switch"><button>6艇横並び</button><button>選手ごと</button></div>
   <div class="be206-table-scroll"><table class="be206-table"><thead><tr><th>選手</th><th>全国</th><th>当地</th><th>M2連</th></tr></thead><tbody>
""" + "".join(f'<tr><th><button class="be206-racername">選手{i}</button></th><td>6.2</td><td>5.0</td><td>35%</td></tr>' for i in range(1, 7)) + """</tbody></table></div>
   <p class="be206-swipe-help">長い説明</p><section class="be206-headpanel" hidden>候補</section>
  </section>
 </div></section>
</main></div>
<script>document.getElementById('detail').onclick=function(){
 const open=document.documentElement.classList.toggle('be208-details-on');
 this.textContent=open?'詳しいデータ・監査を閉じる':'詳しいデータ・監査を開く';
}</script></body></html>"""

async def check(engine, shot_dir=None):
    assert STYLE.is_file(), f"Missing actual repository style: {STYLE}"
    async with async_playwright() as pw:
        kind = getattr(pw, engine)
        browser = await kind.launch(headless=True)
        for width in (320, 390, 768, 1280):
            context = await browser.new_context(
                viewport={"width": width, "height": 844},
                device_scale_factor=2 if width <= 390 else 1,
                is_mobile=width <= 390,
                has_touch=width <= 390,
                locale="ja-JP", timezone_id="Asia/Tokyo",
            )
            page = await context.new_page()
            # Completely offline; serve only the tested CSS from the checked-out branch.
            await page.route("**/assets/boat_edge_v371_simple_ui.css",
                             lambda route: route.fulfill(status=200, content_type="text/css", body=STYLE.read_text(encoding="utf-8")))
            await page.set_content(FIXTURE)
            await page.add_style_tag(content=STYLE.read_text(encoding="utf-8"))
            await page.wait_for_load_state("domcontentloaded")
            assert await page.locator("#homeView .hero").is_hidden(), "old duplicate hero is visible"
            assert await page.locator("#homeView>.section").is_hidden(), "old duplicate sections are visible"
            assert await page.locator("#homeView #be108Hub").is_visible(), "venue selection vanished"
            venues = page.locator("#homeView #be108Hub .be108-venue")
            assert await venues.count() == 6, "six venue selection buttons missing"
            assert await venues.first.is_visible(), "venue selection hidden"
            # Real responsive CSS: 320px keeps 2 columns, 390px 3 and
            # tablet/desktop use four. The six venue buttons remain visible.
            expected_cols = 2 if width <= 360 else 3 if width <= 760 else 4
            actual_cols = await page.locator("#homeView .be108-venue-grid").evaluate(
                "(el) => getComputedStyle(el).gridTemplateColumns.split(' ').filter(Boolean).length"
            )
            assert actual_cols == expected_cols, f"responsive venue grid {actual_cols} != {expected_cols}"
            assert await page.locator("#raceView #be207Top .be207-condition").is_visible(), "scratch stop hidden"
            assert await page.locator("#raceView #be207Top .be207-budget").is_visible(), "allocation hidden"
            assert await page.locator("#raceView #be207Top .be207-odds").is_visible(), "odds verification state hidden"
            assert await page.locator("#raceView #be206Quick .be206-table").is_visible(), "six boats hidden"
            assert await page.locator("#raceView #be206Quick .be206-table tbody tr").count() == 6, "six racer rows missing"
            assert await page.locator("#raceView #be206Quick .be206-headpanel").is_hidden(), "head detail must not auto-open"
            assert await page.locator("#raceView #be207Top .be305-evidence-items").is_hidden(), "audit clutter not collapsed"
            details = page.get_by_role("button", name="詳しいデータ・監査を開く")
            if width <= 390:
                for selector in (
                    "#raceView #be207Top .be207-modes button",
                    "#raceView #be108RaceNav .be108-race-chip",
                    "#raceView #be206Quick .be206-layout-switch button",
                    "#raceView #be207Top .be208-detail-actions button",
                ):
                    control = page.locator(selector).first
                    assert await control.is_visible(), f"missing mobile control: {selector}"
                    box = await control.bounding_box()
                    assert box and box["height"] >= 44, f"undersized touch target: {selector}"
                assert await page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
                ), "unintended full-page horizontal scrolling on an iPhone"
            before = await page.locator("#raceView #be207Top .be207-combo").inner_text()
            await details.click()
            assert await page.locator("#raceView #be207Top .be305-evidence-items").is_visible(), "audit details inaccessible"
            assert await page.locator("#raceView #be207Top .be207-combo").inner_text() == before
            await page.get_by_role("button", name="詳しいデータ・監査を閉じる").click()
            assert await page.locator("#raceView #be207Top .be305-evidence-items").is_hidden()
            if shot_dir:
                Path(shot_dir).mkdir(parents=True, exist_ok=True)
                await page.screenshot(path=str(Path(shot_dir) / f"v371-{engine}-{width}.png"), full_page=True)
            await context.close()
        await browser.close()
    print(f"V371_{engine.upper()}_OFFLINE_UI_FIXTURE_PASS viewports=320,390,768,1280")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("chromium", "webkit"), default="chromium")
    parser.add_argument("--screenshots", default=None)
    args = parser.parse_args()
    try:
        asyncio.run(check(args.engine, args.screenshots))
    except Exception as e:
        print(f"V371_{args.engine.upper()}_NOT_VERIFIED: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
