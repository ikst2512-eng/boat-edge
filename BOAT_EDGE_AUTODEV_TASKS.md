# BOAT EDGE V240 — bounded autonomous UI improvement queue

One task per successful V240 run. Only existing tracked UI assets may be changed.
No result/payout reads, no prediction-model changes, no formal Fresh changes.
The agent must change only one checkbox after implementing and checking that task.

- [x] A01 | Make missing, stale or unverified pre-deadline odds and scratch data visibly distinguishable from verified values in the existing site UI. Never invent the latest odds or a scratch status; retain current race selection.
- [x] A02 | Check every current primary site page for a consistent BOAT EDGE home link and a clearly labeled user-initiated refresh action; safely fix the smallest missing behavior without altering prediction calculations.
- [x] A03 | Improve iPhone Safari readability of the existing prediction and racer-details UI, preserving motor, local/national statistics, head picks and the user-selected race. Avoid hiding important information.

- [x] A04 | On the currently selected race's prediction screen, make the existing FIRST/FINAL/LATEST freeze state and any confirmed pre-deadline timestamp easier to see. Use only stored source evidence and never rerank or rewrite saved picks.
- [x] A05 | In the existing racer and 6-boat comparison UI, improve legibility of race-relative standout motor and local-course metrics that are already supplied. Never invent metrics, infer missing values or alter the prediction engine.
- [x] A06 | On the existing source/evidence panel, distinguish BOATERS and 競艇日和 original exhibition provenance only if independently recorded source data exist; otherwise explicitly display 未取得. Do not scrape new sources in the browser or treat official data as either third-party source.
- [x] A07 | On the existing AI virtual-simulation page, clarify the daily 50,000-yen paper budget, actual saved stakes and no-bet conditions using current saved JSON only; do not compute synthetic profits or change betting eligibility.

- [x] A08 | Improve the existing result/hit indicator to clearly distinguish verified hit, verified miss, result pending and ineligible race only where the page already has source-backed settled evidence; never infer a past ticket or calculate winnings from unavailable snapshots.
- [x] A09 | Make the existing predicted race-development narrative readable as ordered start, first-turn attack, benefiting racer, and expected finish stages on iPhone. Use only existing description text; do not create probabilities or alter any prediction.
- [x] A10 | Keep all six racers' national, local, motor and boat metrics accessible without extra hidden tabs, using compact original comparison cards with legible labels and existing documented source-state distinctions.
- [x] A11 | Make the existing BOAT EDGE header and manual refresh affordance consistent and keyboard/mobile accessible across current site pages, preserving selected race and never dispatching data collection from the browser.
- [x] A12 | In the current paper-only simulator UI, make the saved ledger date and unverified/stale state prominent; if current-day evidence is missing, do not label past figures as today's balance or claim returns.

- [x] A13 | Clarify the timestamp and source (including stale/unverified) attached to odds shown in the existing race UI after user-initiated reload. Never imply that pressing refresh collects new odds or replace frozen tickets.
- [x] A14 | Reduce redundant mobile controls and make the top-home, selected race, and user-initiated refresh elements consistent in existing site HTML/CSS/JS. Keep selected race and navigation state intact.
- [x] A15 | On the saved paper-only simulation page, distinguish pending, settled and no-bet states with provenance-backed labels; do not backfill historical wagers, profits, winning tickets, or actual spending.
- [x] A16 | Explain existing Top3/Top5/Top10 forecasts and head-versus-trifecta confidence separately using only measured values already shown in existing prediction UI. Never claim accuracy improvement without verified prospective comparison.

- [x] A17 | Make the user-selected race's last saved odds source timestamp and validation state persistent beside prediction tickets, not only in a temporary refresh toast; distinguish verified, stale, and missing from the pre-deadline source record.
- [x] A18 | On the existing verified site-results page, clearly label the sample size and settled-day cutoff for Top10/head hit rates; do not imply this proves a better production model or use formal Fresh result data.
- [x] A19 | In the existing six-racer comparison view, make available original-exhibition lap/turn/straight measurement differences easier to compare, without using race results, imputing missing exhibition times, or changing predictions.
- [x] A20 | On the AI paper-simulation page, show only evidence-backed reason counts for skipped bets and a clearly separated status for pending/settled saved simulated bets. Keep daily 50,000-yen cap and no-real-money behavior unchanged.

New tasks require an explicit owner request; the AI agent must never invent or append tasks. Stop once the queue is complete.
## Next verified UI cycle (A21–A28)

These remain UI-only work items. Every change must use already-saved source evidence, preserve the existing race selection, and pass the V240 isolation and regression gates. Do not invent odds, exhibition measurements, hits, or simulation returns.

- [x] A21 | On the selected race card, clarify whether the latest saved official odds are current, stale, or absent using only timestamp and verification state already provided; do not imply a browser refresh fetches new odds.
- [x] A22 | Improve the existing prediction-ticket list on iPhone so the frozen order, ticket amount, and source-verified payout estimate are legible; show 未確認 instead of deriving values from missing data.
- [x] A23 | Make a compact six-boat stat comparison easier to scan with race-relative emphasis only for numeric values already in the UI; do not alter classes, local statistics, motor scores, or prediction ranking.
- [x] A24 | On an existing prediction page, distinguish the predicted head racer, trifecta Top3/5/10 coverage, and separately recorded confidence values without recalibrating or fabricating probabilities.
- [x] A25 | Make the original-exhibition source state explicitly distinguish BOATERS, 競艇日和, official, and 未取得 in an existing evidence panel, but only when per-source provenance is already present; never equate official with third-party exhibition data.
- [x] A26 | Improve mobile access to verified results, race selection, and AI paper simulation through existing navigation; preserve the current chosen race and do not duplicate or replace refresh behavior.
- [x] A27 | Explain paper-only daily ¥50,000 budgeting, no-bet decisions, actual saved stake totals, and pending versus settled simulated bets without guessing missing balance or historical return.
- [x] A28 | Reduce visual clutter on existing iPhone race cards by improving grouping and contrast for scratches, verified results, deadlines, and source freshness; keep all six racer metrics accessible and retain frozen picks unchanged.

## Owner-requested next UI-only batch (2026-10-13; A29–A33)

These items were explicitly requested to continue completing the BOAT EDGE site.
The V240 isolated Codex runner must perform no more than one item per successful
run and edit existing UI files only (never model weights, odds values, results,
formal Fresh files, workflows, scripts, credentials, or frozen tickets).
A checked box does not certify Safari visual behavior or prediction accuracy.

- [x] A29 | In the existing selected-race prediction view, explicitly describe saved 10-ticket p_raw_percent as relative allocation weights, not calibrated win probabilities. Keep original ticket ordering, numbers, Top3/5/10, and all 6 racers intact. Never generate or adjust probabilities.
- [x] A30 | On iPhone, make the currently selected venue/R and official deadline unmistakable at the top of the current race/prediction view, using only existing state. Do not reset selection or infer missing deadlines.
- [x] A31 | On the existing beforeinfo/original-exhibition view, separate verified six-racer exhibition/source evidence from unknown/awaiting publication in compact labels. Do not turn missing values into zero or merge official with BOATERS/競艇日和 evidence.
- [x] A32 | On the current AI self-drive status UI, show a compact explanation that Actions PASS or Pages SUCCESS is not proof of model accuracy and that formal Fresh stays locked when stored status says so. Do not fetch result or payout endpoints, expose credentials, or claim Safari checks.
- [x] A33 | On iPhone race results view, improve the visible distinction between predeadline fixed predictions, result waiting, verified hit, verified miss, and ineligible records; use only already verified stored evidence, no retrospective pick reconstruction.

## Owner-requested next UI-only batch (2026-10-14; A34–A37)

These tasks follow the owner's instruction to continue BOAT EDGE development after A33 completed. V240 may execute at most one unchecked task per run, only through its existing isolated UI-only Codex gate and draft-PR publication. Existing implementation must be checked before editing. Never touch scripts, workflows, data, model weights, odds, results, formal Fresh, or frozen predictions. No claims of real-device Safari certification or measured accuracy.

- [x] A34 | In the existing selected-race iPhone prediction screen, keep venue/R, official deadline and saved source freshness legible together without duplicating existing controls. Use only present data; unknown deadlines remain unknown. Preserve selection, 6 racers and frozen Top3/5/10.
- [ ] A35 | In the existing no-bet/paused-picks screen, ensure no recommended stake, allocation or payout estimate is presented as actionable. Preserve access to source status and the recorded reason for the pause; do not recompute tickets or fetch odds.
- [ ] A36 | In the existing six-boat mobile comparison, make the provenance and missing-value state of exhibition/ST/turn/straight metrics readable without conflating BOATERS, 競艇日和 and official data. Do not fabricate measurements or reorder boats.
- [ ] A37 | In the existing Top3/5/10 mobile prediction list, distinguish saved rank coverage, head selection and uncalibrated allocation weights from verified outcome labels. Preserve exact saved tickets, order, yen amounts and confidence fields; never infer hits from absent results.
