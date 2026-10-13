# Track02 prospective TopK integration gate — 2026-10-14

## Read-only main snapshot; do not confuse off-hours 0R with outage

At inspection, `data/site_autopilot/v230_fast_current.json` for day 20261014 reported `eligible=0`, `targets=[]`, `outside_2_to_19_min_window=156`, `new_snapshots_atomic_audited=0`. `data/site_autopilot/v232_current.json` for the same day reported `current_prediction_window_races=0`, `frozen_research_races_today=0`, `new_research_races_this_run=0`. `v254_pre_current.json` reported `source_cohorts_today=0`, `upstream_diagnostic=NO_V232_COHORTS_TODAY`. These are observed snapshots, **not proof** that a daytime eligible race failed. Track01 must distinguish no live deadline window from real missed eligible deadlines, and inspect V235 action runs/logs.

## Reuse existing work, avoid parallel estimators

Main `scripts/boat_edge_v360_research_ranked120.py` already supplies 120 ranked boat combinations for three V312 research modes, via the V332 live predeadline freeze, with uncalibrated relative mass and provisional exhibition entry. `docs/BOAT_EDGE_02_V343_INPUT_REPLAY_HANDOFF.md` specifies V343 exact race-input bytes, V344 evidence gate, V339 collision checks and V340 source receipt verification. Reuse these rather than reconstruct rankings or capture provenance.

Draft PR #192 owns V301 paired SITE score audit, V302 Git-clock diagnostic, V303 PRE_RESULT ranked TopK structural audit, V304 ranked baseline Top3/5/10, V305 exclusive head/second/third miss categories. V303 is **structural readiness only** (139/139 at last successful CI), not independent server publication attestation. V304 unique baseline 85R: Top3 18/85, Top5 23/85, Top10 33/85. V305 unique misses 52R: head 9, second 15, third 28. No candidate Top3/5 lift demonstrated. V303 regression after malformed-ticket fix: all six workflows succeeded at commit `7ffe416034f30b9d4f1128a74c3d49115ce1d3e4`.

## Minimum next genuinely prospective same-race trial

1. Track01 produces a live eligible V230/V232/V235 cohort **before deadline**, and preserves original bytes, deadline, publication/receipt evidence, race key, immutable input SHA, model ID, ordered Top120 or Top10 tickets, capture time, and first-add commit. Missing fields = excluded with explicit reason, not zero hits.
2. Track02 declares challenger model ID and hypothesis **before observing target outcome**. Use existing V360 three-mode national/national+motor/national+motor+ST rankings as research-only candidates where independently frozen V332/V343/V344 evidence exists. Do not relabel exhibition entry as actual entry; no post-result reconstruction or promotion.
3. For every valid race, same exact deadline and cohort, equal Top3/Top5/Top10 ticket budgets for baseline and candidate. Verify original frozen bytes and both independent time proofs, dedupe race keys, and score only through separately authorized SITE-only outcomes after race closure. Compute paired gains/losses, exact discordance p and uncertainty by day. Unavailable candidate rank or receipt => **not comparable**.
4. Keep Formal First100 0, results_seen/unlock/scoring false and token null. Never use Formal results/payout/combined API, and never use retrospective 85R as prospective V360 lift.

## Ownership / merge

Track01: scheduler, V230/V232/V235 live 0R triage, GitHub Actions ownership, release and PR merge. Track02: paired accuracy and evidence gate. Track03: Safari/UI only after model approval. PR #192 stays draft until same-race evidence and owner review. MASTER TODO T07/T08/T10/T12/T13 remain open; no checkbox is closed based solely on code/CI.
