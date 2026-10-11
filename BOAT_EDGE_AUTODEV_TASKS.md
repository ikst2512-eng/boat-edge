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

Do not append new tasks automatically. Stop once the queue is complete.
