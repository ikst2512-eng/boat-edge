# BOAT EDGE — Single execution track (2026-10-21 JST)

This document is the single coordination point for workstreams ①–⑤. It is a **plan and verified-code inventory**, not a claim that production has passed C-1. Keep historical evidence immutable.

## Immediate blockers (ordered)

1. **Actions completion-event amplification (① / prior cause ②)**: the V235 and V229 workflows still subscribe to successful completions of the same two official collectors. The code guards against untrusted, failed, or foreign-branch completions, and explicitly does not subscribe to V216 or one another. **Do not assert that the Actions run count or queue delays have normalized until measured.** Compare all-event metadata by 5-minute window using the existing read-only V351 Actions Evidence workflow and `scripts/boat_edge_v352_action_pressure.py`. Record run IDs, event types, timestamps, skipped/cancelled counts, and upstream/downstream names. Distinguish necessary independent freeze wakes from redundant wakes; preserve the strict 2–10 minute freeze window.
2. **C-1 first Git save proof (③)**: classify each observed race as official-source fetch failure, source not eligible, freeze generation failure, push failure, or proof mismatch. The 2026-10-20 observation of 27 files found among 50 observed races is **not** the validated eligibility denominator. Require original PRE_RESULT bytes and SHA, deadline, first Git commit timestamp and matching source identity. Acceptance is >=99% of eligible races for three consecutive race days, never a one-day proxy.
3. **Official source coverage (②)**: measure actual 24-venue availability, misses, retries and stale records. A unit-test pass is not a production fetch-rate measurement.
4. **24-venue mobile website (⑤)**: keep current site read-only during C-1 stabilization. Verify real on-device Safari rendering and source-linked updates only after C-1 is stable.
5. **Prediction research (④)**: use independently held-out historical data only. Do not promote unverified models.

## Verified on-repository implementation snapshot (2026-10-21)

- `.github/workflows/V235.yml`: scheduled + upstream completion-triggered source refresh and freeze; `concurrency.cancel-in-progress: false`. Calls existing V229 strict freeze and attempts Git proof.
- `.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml`: separate scheduled + upstream completion-triggered freeze and audit, constrained to trusted upstream success.
- `.github/workflows/boat-edge-v350-actions-evidence.yml`: V351 read-only workflow to export Actions event pressure and race-window evidence as artifacts.
- `docs/C1_MINIMAL_CORE_MIGRATION.md`: explicitly prohibits retiring workflows without dependency inventory and three-day proof.

These facts show *guardrails exist*, not that the runtime problem is resolved.

## Single change protocol (for all five workstreams)

- Start from one named hypothesis and one measured failure signature. Record workflow run URL, event time JST, exact race key, first Git SHA (if present), and the existing baseline before changing production code.
- Change **one trigger/collector/freeze behavior at a time**, preferably via reversible PR. State its upstream consumers and rollback.
- Prove GitHub Actions run-count/skip/cancel behavior before and after; for C-1 also prove source-SHA consistency and first-commit timing. Don't treat skipped Actions as successful snapshots.
- Mark items `PLANNED`, `IMPLEMENTED`, `DEPLOYED`, or `VERIFIED`; reserve `VERIFIED` for reproducible evidence. Avoid percentage-complete guesses.
- Each response to the user should report only **what changed**, **commit/run URL**, **measured result**, and **remaining blocker**. This file is the handoff between workstreams so independent chats do not redo the same investigation.
- No paid infrastructure, no duplicate new engine, no widening C-1 eligibility, and no deletion of evidence.

## Current handoff

| Area | Status | Next evidence needed |
| --- | --- | --- |
| Actions fanout | INVESTIGATING | Recent V351 run artifact and 5-minute event-pressure comparison |
| Official inputs | NOT VERIFIED | Per-venue fetch/retry/staleness ledger |
| Strict first-save C-1 | NOT VERIFIED | Valid eligible denominator + 3 consecutive race-day audit |
| Research model | RESEARCH ONLY | Held-out hit rate and ROI with sample size |
| iPhone site | NOT VERIFIED END-TO-END | Safari and official-source-to-page checks |

**Change log**: 2026-10-21 — created this non-executing cross-workstream handoff; no production workflow altered and no C-1 pass claimed.
