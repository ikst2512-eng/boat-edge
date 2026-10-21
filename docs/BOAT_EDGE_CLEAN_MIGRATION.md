# BOAT EDGE CLEAN — minimal migration track (2026-10-21 JST)

Status: PLANNED. This branch is isolated from production. No source, history, model or workflow has been retired.

## Owner decision
Prefer a minimal **parallel migration** over further V-numbered additions. Do not replace the running site or launch parallel live first-writers until safety and performance are verified. This updates the migration direction without claiming that the C-1 production acceptance gate passed.

## Single critical path
1. Official inputs: existing `.github/workflows/auto-update.yml` (race/beforeinfo), `.github/workflows/site-odds.yml` (official trifecta odds). Preserve actual source bytes, identity, original timestamps, scratches and 120/120 odds. Missing or stale means missing.
2. Eligibility / prediction: reuse pinned **site-only** production prediction, no experimental weights; ensure identical race/venue/model identity, and strict pre-deadline readiness.
3. First Git save: reuse **one** authority `scripts/boat_edge_v229_atomic_freeze.py`; preserve first-add commit SHA and source SHA. `V235.yml` and `BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml` are wake paths to inventory for amplification, **not** invitations to create another writer.
4. Publication: existing `pages-controlled-publish.yml` and read-only V351 Actions evidence; show verified Top3/Top5/Top10 or an honest unavailable/pending state.
5. Validate against actual race results only under the formal/source safety gates of AGENTS.md, with held-out prospective cohorts.

## KEEP / REVIEW / NEVER DELETE
- KEEP: immutable frozen predictions, raw PRE_RESULT inputs, source SHA, first commit history and timing, eligibility and provenance records, official collectors, production model pin, live public site, safety gates.
- REVIEW FOR RETIREMENT (not yet approved): versioned legacy CSS/JS, inactive old pages, redundant scheduled/action completion listeners, duplicate generated snapshots, unused test scripts. Confirm readers/writers/deployment dependencies and rollback before each deletion.
- NEVER DELETE OR RECONSTRUCT: historical source, prediction-first-save, evaluation evidence, outcomes, user-visible production availability.

## First execution gate
- Inventory 96 current workflow definitions by events, writers, consumer dependencies; measure completion-event fanout, skips and latency using V351/V352; isolate one safe trigger adjustment if supported by evidence.
- For each observed eligible race: real official bytes+SHA, deadline, first Git-add timestamp, exact saved prediction match. Classify failures into source, readiness, freeze, push, mismatch.
- Require >=99% *of independently eligible races* for 3 consecutive race days with first commit 2–10 minutes before deadline. Never treat the 27/50 observed files as the denominator.
- Only then begin reversible migration of site rendering with iPhone Safari verification and 24-venue freshness.
- Run tests together with changes; failed candidates are fixed or discarded, not left as additional systems.

## Exit criteria
Production unchanged until: input provenance validated; no extra live first-writer; C-1 three-day proof; verified Pages bytes; mobile display works. Record each change as PLANNED, IMPLEMENTED, DEPLOYED, VERIFIED (VERIFIED requires live proof). Keep cleanup as deletion with evidence, not new monitoring architecture.

## Known evidence links
- `docs/C1_MINIMAL_CORE_MIGRATION.md`
- `docs/BOAT_EDGE_SINGLE_TRACK_EXECUTION.md`
- `AGENTS.md`

## Next move
Dependency inventory of workflows before any retirement, and read-only V351/V352 observed Actions pressure. No blind deletion. 
