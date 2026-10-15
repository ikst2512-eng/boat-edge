# Collector publication: isolate expired evidence instead of losing future races

## Observed production failure

On 2026-10-15, PRE_RESULT collector run [38683399185](https://github.com/ikst2512-eng/boat-edge/actions/runs/38683399185), job 116252738963, completed collection but failed before publication. V277 correctly blocked changing concurrently frozen races `20261015-04-08` and `20261015-06-07`. Its conservative filter then stopped the entire commit on `V01_REMAINING_SOURCE_DEADLINE_PASSED_20261015-10-11`. Unrelated not-yet-due source evidence was therefore not published by that attempt. This does not establish the cause of all 39 missing predictions on 10/14.

## Fix

Only inside the existing opt-in collector recovery after a concurrent freeze: identify expired remaining source races and verify an existing origin/main race has the same race key and deadline. Discard the unpublished local race/raw/scratch/early-preview changes for those races using the remote original, replacing their catalog rows with the remote rows. Preserve unrelated future race changes. Expose both frozen and expired exclusions in the existing health exclusion list and report expired IDs separately in the Actions log.

Missing remote originals, mismatched race identities/deadlines, unknown deadlines, unsafe Formal state and unauthorized frozen paths still stop publication. The unchanged V277 audit runs after the amendment. This changes neither the prediction first-save implementation nor its time window, model weights, snapshot bytes or Formal Fresh locks. No expired prediction is generated or backfilled. No source or schedule is disabled. No real race result/payout is read.

## Validation

- Synthetic Git integration: a frozen race, an exactly-deadline race and a future race compete in one collector commit. Frozen and expired evidence stays remote-byte-identical, future evidence survives rebase and a regular fast-forward push; formal state and snapshot proof unchanged. No expired or future snapshot fabricated.
- Missing remote proof, changed remote deadline, changed identity, unknown local deadline and absence of a concurrent freeze each remain fail-closed.
- Collector/prune/rebase/V277 tests: 13 PASS; required V23* fixtures: 395 PASS; V271 health: 7 PASS; source pins: 5 workflows PASS.
- Existing CI already invokes the changed test module; no workflow change needed.

Prepared and fixture-verified locally. Deployment and the next real invocation must be checked by exact commit/run. Broader cron gaps, all-39R causal proof and controlled Pages source remain separate outstanding work.
