# BOAT EDGE 02 — V343 exact research input preservation and replay

Track 02; tested against main `f80cda33d90b817b42964502fe5b6e1e368677a1`.
Branch: `feature/02-v343-race-input-replay-20261013`. Track 01 owns integration.

## Problem and behavior

V332 records the SHA256 of the input `data/races/<race_key>.json`, but V336's
uploaded artifact previously contained only frozen candidates and three HTML
captures/receipts. The changing race input was absent, so its features and all
three candidate outputs could not be independently reproduced from that bundle.

V343 preserves the exact bytes read before source capture as
`data/source_captures/<date>/<race_key>/race_input.json`. The existing V336 upload
glob includes this file without changing any common workflow. A later race-card
update cannot replace the bytes used by the candidate. An interrupted capture
can reuse an identical snapshot; a different snapshot is never overwritten.
Source freshness is checked again at the final freeze instant.

`scripts/boat_edge_v343_race_input_replay.py` accepts one explicit V336 run report
and extracted artifact root. Before opening artifacts it rejects invalid report
flags, paths, hashes and the locked 2026-10-01 formal date. It verifies the
report's frozen JSON SHA, the original race input SHA, and reconstructs every
V312 candidate field at the frozen time. Recomputing internal hashes after
editing candidate tickets still fails replay. Missing snapshots, stale input,
symlinks and elevated research claims fail closed. Zero completed freezes do
not produce a verified replay claim.

```sh
python3 scripts/boat_edge_v343_race_input_replay.py \
  --root /explicit/unpacked/v336-artifact \
  --report /explicit/v336_report.json
```

## Isolation and limits

- Changed paths: V332 capture implementation, new V343 verifier, synthetic V343
  regression and this handoff. No UI, production weights, shared workflow,
  formal state or scoring implementation changes.
- Frozen JSON schema/model IDs remain V332/V312. V343 is an evidence verifier,
  not a new predictive model or adoption decision.
- Exact replay establishes reproducibility against supplied local bytes only.
  V340 raw HTML/receipt verification is a separate check. Provider fields,
  source authenticity, capture timestamps, first-seen Git/server provenance,
  actual entry and global unique cohort history remain unverified.
- Existing artifacts without race_input.json cannot be repaired by reading
  today's changing race card. No historical backfill is performed.
- No result endpoint/page, payouts, combined API or formal outcome was read.
  Formal locks and improvement/promotion claims remain false.

## Synthetic validation and next step

Local checks including the V344 extension: 264 Python regressions (262 passed, 2 skipped), seven V271
JavaScript checks passed, all five workflow source pins matched, diff whitespace
clean. The V343 cases are included in the Python total. No workflow edits.

V343 regression covers exact byte replay without current race-card/formal files,
mid-capture input changes, missing snapshots, raw/candidate/freeze mutations,
staleness during capture, interrupted retry, file/ancestor symlinks, bad flags,
formal target rejection and empty reports. Two independent synthetic runs produce
identical snapshot, frozen JSON and replay report bytes. These are fixture tests,
not an independent Formal Fresh Run1/Run2 PASS.

After Track 01 reviews/merges the PR, a future successful V336 capture should
include the snapshot automatically. Inspect its actual artifact before claiming
live completeness. Combine V339 cross-run collision checks, V340 source-byte
integrity and V343 candidate replay before any separately authorized research
comparison; this PR does not authorize outcome access or Formal Fresh scoring.

## V344 extension — one command for the three local evidence checks

The same PR also includes `scripts/boat_edge_v344_site_research_evidence_gate.py`
and 13 additional synthetic regression cases. It validates every explicitly
supplied run report before artifact access, requires each selected race to have
a completion or declared failure, and combines V339 collisions, V340 frozen
JSON/HTML/receipt integrity and V343 exact candidate replay. A missing report
entry cannot silently remove a difficult race from the batch denominator.

```sh
python3 scripts/boat_edge_v344_site_research_evidence_gate.py \
  --bundle /explicit/bundle-one /explicit/report-one.json \
  --bundle /explicit/bundle-two /explicit/report-two.json
```

CLI exit 0 means only `LOCAL_EVIDENCE_CHECKS_PASSED_NOT_FORMAL` for the supplied
bundles. Empty captures, repeated races (even identical hashes), divergent
freezes, capture failures, missing inputs or byte/replay failures exit 2 with
explicit diagnostics. Invalid scope/report contracts fail before artifact reads.
No gate result attests complete Actions history, true source fields, independent
timestamps, actual entry or prospective accuracy; scoring and promotion remain
unauthorized. No network, output mutation, workflow integration or result read
is added. This is a verifier ID, not a production prediction model version.


## V345 extension — complete three-mode 120-way predeadline research record

Added in Track 02 to the same PR, without changing the V312 research
candidate itself or the production model. V332's already-gated, live-only
freeze now generates and embeds:

- research_ranked_120_schema = BOAT_EDGE_V345_PREDEADLINE_RESEARCH_RANKED120
- research_ranked_120_by_mode: national_only, national_motor,
  national_motor_st, each with exactly **120** ranked objects:
  rank, course_combo, boat_combo, relative_model_mass.

Ranking uses the V307 Plackett–Luce **relative, uncalibrated model mass**,
not payout odds or measured win probability. Each course combination is
mapped to a **boat-number** combination using the provisional start-exhibition
course permutation, NOT independently verified actual entry. The original
three candidate hypotheses, their Top10 order, and head-mass fields are
unchanged.

V345 independently reruns the three fixed V312 feature hypotheses,
validates 120 unique course and boat combinations per mode, normalized
mass 1, exact positional Top10 equality in both course and boat labels,
and all six course-head and boat-head totals. Any mismatch aborts the
V332 freeze before its frozen JSON is written. The output cannot be
generated by V345 independently of the V332 live predeadline freeze.
Existing V336 artifact upload already includes the enlarged frozen V332
JSON; no shared workflow edit.

V343 offline replay uses the preserved V343 race_input.json and V332
candidate at the self-declared freeze instant, then recomputes and
compares all 360 saved rows. Altered row, rank, mass, missing mode or
inconsistent schema fails. Pre-V345 frozen records missing both fields
are explicitly marked all_supplied_full_120_verified=false and are
**never backfilled**. V344 reports all_supplied_full_120_rankings_replayed
separately from its local evidence PASS, so Top10-only does not become a
claim of 120-way persisted evidence.

Synthetic regression:
tests/test_boat_edge_v236_v345_ranked120.py verifies full-card rank
uniqueness, mode Top10/head parity, course-to-boat swaps, replay without
current cards, tamper detection even after rehash, missing modes,
legacy-only records, deadline guards, immutable retry and replay
determinism. This is not a validated source timestamp, actual-entry
record or independently verified model probability.

Track 01 still owns PR merge and live V336 artifact confirmation.
No main merge, Pages publication, actual future capture, Formal Fresh
Run1/Run2, scoring, site prediction change, model promotion, or proven
accuracy improvement is claimed by this PR.
