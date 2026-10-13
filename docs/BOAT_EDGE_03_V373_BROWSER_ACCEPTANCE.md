# BOAT EDGE 03 — V373 mobile browser acceptance and release gates

Owner: 03 (UI and tests). Integration/Pages: 01. Prediction/data accuracy and Formal Fresh: 02. Last research input: `docs/BOAT_EDGE_03_RESEARCH_METHODS_20261014.md` (PR #201).

## Nonduplicating implementation

- V359 / PR #200: **merged**, blocked/no-prediction label fixed; do not duplicate.
- V360–V361 / PR #202: **open at planning**, homepage/result-list 🎯 verification; this PR does not edit V241 results or its UI test hook.
- Existing V342 head-selection/focus/scroll regression is retained without rewriting V206.
- V373: only V207 display stop-state hides cached per-mode budget and odds summaries. Retains original ticket/Top3/Top5/Top10 ordering and the verified source/freeze gate.
- This PR adds offline browser tests to cover an actual V207 JS/CSS renderer at iPhone widths, instead of inferring browser acceptance from source code.

## How to run browser checks

Use a checked-out `boat-edge` repo with Python 3.11+ and Playwright installed:

```bash
python -m pip install playwright
python -m playwright install chromium webkit
BOAT_EDGE_REQUIRED_BROWSERS=chromium,webkit \
  BOAT_EDGE_SCREENSHOT_DIR=artifacts/ui-03 \
  python tests/browser/test_boat_edge_03_playwright.py
```

Runs viewport widths **320, 375, 390, 430 px**, JST clock, Japanese locale, mobile/touch. It loads checked-in V207 JS and CSS, with 10 synthetic non-result tickets, no real API calls, and exercises Top3/5/10 ordering, scenario/freeze and uncalibrated-confidence labels, display-only reference amount, blocked/frozen-source state, stale old-race tickets, 6艇比較・オリ展欠測・選手頭候補・フォーカス復帰, and touch targets. The smoke suite is **not** a production Pages test.

For a Chromium-only local preflight (explicitly not WebKit):

```bash
BOAT_EDGE_REQUIRED_BROWSERS=chromium \
  BOAT_EDGE_CHROMIUM_EXECUTABLE=/usr/bin/chromium \
  python tests/browser/test_boat_edge_03_playwright.py
```

Browser missing/executable failure is a failing setup; do **not** mark unexecuted WebKit as PASS. The existing V307 GitHub Node CI runs `tests/test_boat_edge_v373_browser_contract.cjs` via the V304 test hook; it validates source contracts and suite presence, **not** the actual browser interaction. 01 can add a separate permissions-minimal browser runner to Actions after review. Do not alter the shared V307 workflow in 03.

## UI acceptance matrix / latest TODO integration

| Gate | What to verify | Automated evidence | Remaining |
| --- | --- | --- | --- |
| P0 iPhone layout | 320–430px top bets and touch targets | V373 Playwright emulation | Real Safari #162 |
| P0 race switch | no old race top-3 or budget during async transition | V306 + V373 | Pages runtime #168 |
| P0 6艇, 展示, オッズ | six lanes, missing source labels, course and ST distinct | V342 + V356–V358, V373 odds | independent BOATERS/競艇日和 acquisition, field snapshot |
| P0 head / explanation / Top3/5/10 | no invented head/trifecta confidence; preserve source rank | V304/V306 + V373 | Pages source/model version parity |
| P0 ¥10,000 / 🎯 | no stale money on blocked picks; no result guessed | V373 and PR #202 (separate) | #202 merge and actual Pages result verification |
| P1 accessibility | 44px tap targets, aria-pressed, status and focus | V342 and V373 emulated browser | VoiceOver on physical iPhone |
| Release | exact main SHA → Pages commit → browser → iOS Safari | 01's V277 Pages SHA audit | Record browser/device evidence |

## Stage definitions — never conflate them

prepared → PR CI (Node) → **WebKit browser PASS** → main merged (01) → Pages exact SHA (01) → public runtime → **physical iOS Safari PASS** (#162).

- A passing Node/static suite is *not* WebKit. Playwright WebKit is *not* iPhone Safari.
- Synthetic UI fixtures are *not* model validation or real race results.
- All new UI changes are read-only. No prediction engine, odds/ranking algorithm, real wager, payout collectors or Formal Fresh gate changes.
- Formal Fresh first100 must remain zero, `results_seen/unlock/scoring=false` and unlock token null. No results/payout requests from these fixtures.
