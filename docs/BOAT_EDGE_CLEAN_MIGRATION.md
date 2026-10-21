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


## Trigger inventory — targeted static inspection (2026-10-21)
Repository tree currently lists 97 workflow YAMLs (the previous count 96 was not a reliable complete current inventory). This is a *targeted inspection of seven files*, not an exhaustive runtime dependency audit.

| Workflow | Automatic wake observed in YAML | Write permission | Decision |
| --- | --- | --- | --- |
| `auto-update.yml` | every 5m + successful V71 completion | contents:write | KEEP official pre-result producer |
| `site-odds.yml` | every 5m offset + push on self | contents:write | KEEP official odds producer |
| `V235.yml` | staggered schedule + both official producer completions + self push | contents:write | KEEP while C-1 unverified; REVIEW duplicate wakes |
| `BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml` | staggered schedule + both official producer completions + self push | contents:write | KEEP independent freeze fallback pending live evidence |
| `pages-controlled-publish.yml` | 5m fallback + V229 completion + relevant push | contents:read | KEEP conditional Pages publication |
| `boat-edge-v350-actions-evidence.yml` | daily + manual | read-only | KEEP for evidence; no extra reporter |
| `improvement-gate.yml` | hourly + targeted push + manual | contents:read | REVIEW for later optional retirement, not part of critical C-1 path |

### Specific redundant-work *candidate*, not yet a confirmed defect
Each successful official collector can trigger both V235 and V229, while each also has a staggered schedule. V235 invokes the shared V229 freeze logic. These are overlapping **wake paths**, but V229's independent fallback may be essential if V235 or GitHub schedule dispatch is delayed. No trigger was removed: lack of actual per-window run IDs, skipped/cancelled counts and eligible-race saves precludes a safe cut. The original collector and odds workflow are also connected by a V71-to-auto-update completion subscription; do not accidentally create a reverse subscription.

### Verified scope and next smallest change
- Existing production workflows, model, site and evidence: **unchanged**.
- New predictor, collector, scheduler, monitoring service and extra website: **none**.
- Actions live pressure: **NOT VERIFIED**. GitHub connector's approved repository fetch endpoint does not accept Actions workflow-runs collection URLs; use existing V351 artifact/live Actions view instead of inventing measurements.
- Next: assess V351 V352 pressure together with three-day C-1 evidence; only then select a reversible reduction with rollback.
