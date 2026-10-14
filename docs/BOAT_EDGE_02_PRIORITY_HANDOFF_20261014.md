# BOAT EDGE 02 — priority and evidence handoff (2026-10-14)

## Ownership and nonduplication
Track02 owns prospective Top3/Top5/Top10 accuracy, model research, error attribution and evidence. Track01 owns V232 upstream pipeline, Actions scheduling, deployment, and merging. Track03 owns mobile display and must consume the same approved model ID. Do not duplicate Track01 V232/Actions fixes or Track03 UI.

## PR #220 review
PR #220 `fix/02-v254-upstream-zero-diagnostics-20261014` adds upstream V232 cohort availability classification for V254 zero-cohort. GitHub Actions on head `9d6b54e72195aa5cc10c0e0e1c2b931daf70707c`: Development CI `38427704506` SUCCESS, Formal Empty Fixture Regression `38427704738` SUCCESS. Main `data/site_autopilot/v254_pre_current.json` for 20261014 reports `source_cohorts_today=0`, `future_window_cohorts_seen=0`, `new_frozen_this_run=0`. This is a V232 upstream availability blocker, **not** a V254 candidate model failure. Ask Track01 to resolve V232 0R and prove predeadline commits. PR #220 is open, unmerged; Track02 must not merge it.

## Actual matched SITE-only Top10 evidence (V301)
- V236 balance10: 43 same races, baseline 15/43=34.88%, candidate 17/43=39.53%, +4.65 percentage points, gains/losses 2/0, exact p=0.5.
- V240 second_coverage10: 50 races, 19/50=38%, candidate 19/50=38%, +0pt, gains/losses 3/3, p=1.
- V254 third_tail10: 58 races, baseline 24/58=41.38%, candidate 25/58=43.10%, +1.72pt, gains/losses 2/1, p=1.
- Cohorts overlap: never add 43+50+58 as independent 151 races. These are SITE-only prospective scored audits, not Formal Fresh.
- **Top3/Top5 not yet measured on comparable frozen ranking artifacts**; do not derive from unordered 10-ticket sets or fabricate.
- Head, course-entry, scenario, second and third leg attribution requires original predeadline source snapshots; no post-result reconstructed predictions.

## V236 freeze-time defect and safe boundary
V302 CI run `38430200881` SUCCESS, 40/40 unmatched V236 frozen rows have `frozen_at - first-add Git committer timestamp` strictly between 0.029188 and 0.839312 seconds. This establishes a Git-second-precision rejection gate, not independent server receipt time. Preserve all original files; do not bypass guard or backfill until predeadline publication independently verified. The V302 metadata-only diagnostic and this report are Track02 research work, not Track01 Actions management.

## Next gates
1. Track01: repair V232 0R, report source capture counts, deadline timestamps, first-added commit and original bytes; distinguish no source, no future window, and commit failures.
2. Track02: compare V360 and PR #192 existing research contracts before new features. Freeze new candidates before deadlines; report Top3/5/10 per same race with paired gains/losses, and split head / entry / scenario / second / third errors.
3. Only after sufficient independent prospective cohorts and statistical/operational validation: request Track01 integration with exact model ID for Track03. Until then: `IMPROVEMENT_NOT_PROVEN`, `NO_PROMOTION`, Formal Fresh LOCKED.
