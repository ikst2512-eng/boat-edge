# BOAT EDGE CURRENT TODO

Current UI target: V122

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

- V117 collects BOAT RACE official recent-3-month course finish rates and winning-method shares.

- V117 validates all six course rows and percentage ranges before publishing.

- V117 maps stats to actual entry course when all six actual courses are available; otherwise it labels frame=assumed course.

- V117 highlights only clearly standout first-rate / escape / makuri / sashi / makuri-sashi values.

- V117 keeps course stats display-only; prediction logic does not use them yet.

- V117 adds no MutationObserver and no setInterval.

- V119 mobile race header is compact and no longer sticky on iPhone-width screens.

- V119 shows current confirmed result and current-mode hit/miss directly inside the prediction panel; history tap is not required.

- V119 resets default prediction mode to hit-priority using a new storage key.

- V119 removes odds from ticket ranking in all four modes; odds remain display/payout-only.

- V119 renames old hole mode to scenario variance and selects alternate-head scenarios by prediction probability, not price.

- V119 clearly labels non-formal output as reference/simple while formal CURRENT is disconnected.

- V119 keeps zero MutationObserver and zero extension setInterval.

- V119 changes current site selection only; existing V114 server-history workflow is left untouched to avoid workflow-write permission failure.

- V120 replaces V114 scheduled history because V114 validation was tied to the old UI version.

- V120 disables obsolete V114 and keeps FINAL_15M history independent of UI version.

- V120 server snapshot selection is probability-first; odds are display/payout-only.

- V120 preserves settled_at and index updated_at when content is unchanged to avoid needless commits.

- V120 does not modify current V119 UI.

- V121 failed before validation because its main-pick patch expected the wrong V119 function signature; production stayed V119.

- V122 fixes the patch against the exact V119 runtime.

- V122 reference input order: venue-course -> actual entry -> exhibition ST -> exhibition time -> original exhibition.

- V122 uses actual course over frame only when all six actual courses are available.

- V122 uses real exhibition/original-exhibition gaps and neighboring exhibition-ST differences; missing inputs are not imputed.

- V122 caps scenario modifiers so player/base strength remains dominant over exhibition noise.

- V122 main pick, four modes, buy board, direct mode and racer-tap head picks share the same adjusted order.

- V122 bypasses all reference adjustment when formal CURRENT exists.

- V122 uses odds for display/payout only, never ranking.

- V122 preserves V119 compact mobile header and inline result/hit display.

- V122 adds no MutationObserver and no setInterval.

- V123 replaces V114/V120 history schedulers and disables both obsolete workflows.

- V123 saves FINAL_15M with the same scenario-aware ordering as V122.

- V123 prefers formal CURRENT server snapshots automatically when a valid formal overlay exists.

- V123 keeps odds display/payout-only and never uses odds to rank tickets.

- V123 does not modify V122 production UI.

- V124 audits every V123 FINAL_15M snapshot without changing production prediction logic.

- V124 records snapshot/race/odds SHA-256, PRE_RESULT guards, used inputs, deadline timing and hit-mode top10.

- V124 fails if a snapshot is outside FINAL_15M, guard-invalid, hash-mismatched or not V122/formal policy.

- V124 is evidence-only; production UI remains V122 and server snapshot generation remains V123.

## NEXT
- Verify V101 iPhone layout.
- DONE V112: four modes rerender from the newly selected race key on every race change.
- DONE V112: official trifecta_odds schema matches V108/V112 mode-row odds lookup.
- DONE V112: only FINAL_15M pre-result snapshots are eligible for post-result 🎯 settlement.
- DONE V116: server-side cross-device history is connected to the prediction tab using V114 PRE_RESULT FINAL_15M snapshots.
- DONE V117: official recent-3-month venue course stats collector and event-driven scenario display.
