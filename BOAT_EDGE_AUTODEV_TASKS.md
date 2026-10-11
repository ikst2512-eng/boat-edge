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

Do not append new tasks automatically. Stop once the queue is complete.
