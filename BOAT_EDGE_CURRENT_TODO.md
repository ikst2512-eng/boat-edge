# BOAT EDGE CURRENT TODO

Current UI target: V116

## Fixed operating rules
- User upload: provide a single file whenever possible.
- Always provide the exact GitHub upload URL together with the file.
- Download filename must exactly match workflow trigger path.
- ZIP only when multiple files are genuinely required.
- After upload verify Actions -> assets -> index -> Pages.
- Never fabricate missing odds, results, or source data.
- Historical hit badges must use a prediction snapshot saved before result confirmation.

## DONE / carried forward
- V96 racer tap -> that boat as head prediction.
- V96 four-stage scenario display.
- V97 official trifecta odds -> stake / payout / P&L / ROI.
- V100 top race selector with deadline times.
- V100 top tabs and in-site back button.
- V100 main prediction above detailed prediction.
- V101 prediction-style tabs: 的中重視 / バランス重視 / 穴重視 / 激絞り重視.
- V101 激絞り = up to 3 probability-leading picks.
- V101 internal confidence display.
- V101 pre-result local snapshot per race.
- V101 post-result comparison using data/site_results.
- V101 🎯 badge on hit mode / hit ticket.
- V101 🎯 hit history for pre-result snapshots on this device.
- V101 does not backfill a fake historical prediction if first opened after result.

- V104 top page previous/next day navigation.

- V104 saved dates available from 2026-10-05.

- V104 venue grid -> linked 1R-12R list with deadline times.

- V104 race page keeps 1R-12R selector directly above prediction tabs.

- V104 site back navigation restores date / venue / scroll context.

- Historical odds/results are shown only when saved; missing values remain unavailable.

- V105 BOATERS-style 24-venue grid with inactive venues grayed out.

- V105 previous/current/next day navigation remains at top.

- V105 venue selection immediately exposes 1R-12R and deadline times.

- V105 old home panels hidden to keep the top page focused.

- V105 race selector stays directly above prediction tabs.

- V106 fixes V105 as the CURRENT UI.

- V106 disables legacy scheduled V98/V103/V104 UI installers.

- V106 cancels legacy queued/in-progress runs when first installed.

- V106 keeps only archive rebuilding on a 5-minute schedule.

- V106 removes V103/V104 navigation overlays from index.html to avoid duplicate controls.

- Historical archive remains available from 2026-10-05 using saved source data.

- V107 race tabs fixed to 予想 / 展開 / 選手 / 直前 / データ / 監査.

- V107 hides legacy 直前モード tab.

- V107 bottom navigation レース -> 予想.

- V107 site-local back stack replaces browser-history back for internal views.

- V107 becomes the only scheduled CURRENT stabilizer/archive builder.

- V108 performance consolidation: legacy V86/V88/V90/V96/V97/V100/V101/V105/V107 JS removed from page.

- V108 keeps only base V48 + consolidated V108 external runtime.

- V108 removes extension MutationObservers and extension setInterval loops.

- V108 disables hidden legacy-home 30s redraw and hidden direct-mode 1s redraw.

- V108 preserves date/venue/race navigation, prediction modes, hit history, odds/payout, racer-head picks and standout highlighting.

- V108 archive scheduler writes only when saved archive content changes.

- V109 replaces the legacy result collector without changing V108 UI.

- V109 treats confirmed + payout null as incomplete and refetches it.

- V109 payout parser supports ¥ / ￥ / 円.

- V109 backfills historical confirmed payout gaps from 2026-10-07.

- V109 keeps result/trifecta data factual; missing payout is never fabricated.

- V109 repaired all 144/144 missing 2026-10-07 trifecta payouts with zero errors.

- V110 failure cause: GitHub returns 403 when disabling an already-disabled workflow.

- V111 checks workflow state first and disables only active legacy UI workflows.

- V111 disables V103/V104/V106/V107/V108/V110 and cancels their queued/in-progress runs.

- V111 reasserts exactly V48 + V108 runtime for lightweight production UI.

- V111 owns archive refresh; V109 owns result/payout collection.

- V112 does not treat early-day page opens as historical final predictions.

- V112 updates the final snapshot while 0-15 minutes remain and freezes it after deadline.

- V112 reloads the current race JSON on app resume or manual refresh without adding polling timers.

- V112 keeps V111 lightweight runtime architecture: no MutationObserver and no new setInterval.

- V113 isolates FINAL_15M snapshots from legacy V101/V108 local snapshot storage.

- V113 isolates final-only hit history from legacy local hit history.

- V113 hit-history rows require FINAL_15M provenance and v113 snapshot schema.

- V113 stores final snapshot saved time/deadline provenance with each settled hit.

- V113 adds no MutationObserver and no setInterval.

- V114 server history starts prospectively; no retrospective prediction backfill.

- V114 saves only 0-15 minute PRE_RESULT site-final snapshots with results_seen/unlock/scoring false.

- V114 never creates a snapshot after a confirmed result exists.

- V114 settles saved snapshots against factual site_results and exposes cross-device 🎯 on archived race rows.

- V114 labels these snapshots SITE_FALLBACK; they are not formal predictions.

- V114 adds no browser MutationObserver or setInterval.

- V115 disables obsolete V111/V72/V73/V95/V83 workflows.

- V115 cancels queued/in-progress runs from those obsolete workflows.

- V115 leaves V109 result/payout collection, V114 server final-history, odds, learning and auto-update active.

- V115 does not modify the V114 production UI runtime.

- V115 removes obsolete workflow churn that caused unnecessary failed Actions and Pages rebuilds.

- V116 merges server and local FINAL_15M hit history without duplicate race rows.

- V116 prefers the server-saved final snapshot on settled races so all devices see the same historical prediction.

- V116 restores historical mode hits, winning ticket and payout from server history on other devices.

- V116 labels server-sourced hit-history rows as shared.

- V116 invalidates server-history cache on race refresh/resume.

- V116 adds no MutationObserver and no setInterval.

## NEXT
- Verify V101 iPhone layout.
- DONE V112: four modes rerender from the newly selected race key on every race change.
- DONE V112: official trifecta_odds schema matches V108/V112 mode-row odds lookup.
- DONE V112: only FINAL_15M pre-result snapshots are eligible for post-result 🎯 settlement.
- DONE V116: server-side cross-device history is connected to the prediction tab using V114 PRE_RESULT FINAL_15M snapshots.
- Continue official course-stat collector work separately.
