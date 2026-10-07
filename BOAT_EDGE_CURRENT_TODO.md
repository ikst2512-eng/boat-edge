# BOAT EDGE CURRENT TODO

Current UI target: V104

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

## NEXT
- Verify V101 iPhone layout.
- Verify four modes update when changing race.
- Verify official odds appear in mode rows.
- Verify pre-result snapshot -> result confirmation -> 🎯 flow.
- Consider server-side cross-device prediction history only after a true PRE_RESULT snapshot pipeline is added.
- Continue official course-stat collector work separately.
