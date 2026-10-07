# BOAT EDGE CURRENT TODO

Current UI target: V111

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

## NEXT
- Verify V101 iPhone layout.
- Verify four modes update when changing race.
- Verify official odds appear in mode rows.
- Verify pre-result snapshot -> result confirmation -> 🎯 flow.
- Consider server-side cross-device prediction history only after a true PRE_RESULT snapshot pipeline is added.
- Continue official course-stat collector work separately.
