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


## V360 extension — complete three-mode 120-way predeadline research record

Added in Track 02 to the same PR, without changing the V312 research
candidate itself or the production model. V332's already-gated, live-only
freeze now generates and embeds:

- research_ranked_120_schema = BOAT_EDGE_V360_PREDEADLINE_RESEARCH_RANKED120
- research_ranked_120_by_mode: national_only, national_motor,
  national_motor_st, each with exactly **120** ranked objects:
  rank, course_combo, boat_combo, relative_model_mass.

Ranking uses the V307 Plackett–Luce **relative, uncalibrated model mass**,
not payout odds or measured win probability. Each course combination is
mapped to a **boat-number** combination using the provisional start-exhibition
course permutation, NOT independently verified actual entry. The original
three candidate hypotheses, their Top10 order, and head-mass fields are
unchanged.

V360 independently reruns the three fixed V312 feature hypotheses,
validates 120 unique course and boat combinations per mode, normalized
mass 1, exact positional Top10 equality in both course and boat labels,
and all six course-head and boat-head totals. Any mismatch aborts the
V332 freeze before its frozen JSON is written. The output cannot be
generated by V360 independently of the V332 live predeadline freeze.
Existing V336 artifact upload already includes the enlarged frozen V332
JSON; no shared workflow edit.

V343 offline replay uses the preserved V343 race_input.json and V332
candidate at the self-declared freeze instant, then recomputes and
compares all 360 saved rows. Altered row, rank, mass, missing mode or
inconsistent schema fails. Pre-V360 frozen records missing both fields
are explicitly marked all_supplied_full_120_verified=false and are
**never backfilled**. V344 reports all_supplied_full_120_rankings_replayed
separately from its local evidence PASS, so Top10-only does not become a
claim of 120-way persisted evidence.

Synthetic regression:
tests/test_boat_edge_v236_v360_ranked120.py verifies full-card rank
uniqueness, mode Top10/head parity, course-to-boat swaps, replay without
current cards, tamper detection even after rehash, missing modes,
legacy-only records, deadline guards, immutable retry and replay
determinism. This is not a validated source timestamp, actual-entry
record or independently verified model probability.

Track 01 still owns PR merge and live V336 artifact confirmation.
No main merge, Pages publication, actual future capture, Formal Fresh
Run1/Run2, scoring, site prediction change, model promotion, or proven
accuracy improvement is claimed by this PR.


## V361 extension — explicit source readiness reason at race selection

New V361 is a read-only preflight derived from the exact bytes V334
read while selecting current-day predeadline PRE_RESULT race cards. V334
attaches selection_scan to each candidate and, if freezing fails, its
failure row. It distinguishes:

- official race_card and beforeinfo statuses and self-reported ages
  (race_card >16min; beforeinfo >15min remain stale, never accepted);
- start-exhibition rows with an **explicit** course field; six boat/ST
  observations without the six-course permutation are NOT mapped from
  lane number to course number;
- six racer rows with usable national win rate, motor quinella rate and
  average ST, with no imputation;
- input SHA256 at **selection**, explicitly not proof that V332 used
  identical bytes at its later freeze attempt.

V361 may only run after V334 has verified that the day and PRE_RESULT
locks match and the deadline is future. Any result-bearing race document
is rejected. It neither calls providers nor loosens the V312/V332 freeze
gates; the original freeze attempt and error code remain authoritative.
The full diagnostic in V336's JSON job report helps identify which
upstream inputs to repair without misreporting a green Actions job as a
successful research freeze. No historical candidate recovery.

Observed operational examples on 2026-10-13 (JST), before any V361
post-merge live artifact exists:

- 15:06 V336 run 38354920151: selected 5, frozen 0.
  Three course/metadata readiness failures and two beforeinfo not-ok.
- 15:35 V336 run 38357552542: selected 3, frozen 0.
  One readiness failure and two stale race-card metadata failures.
- Stored race 20261013-15-02 has six start-exhibition lane/ST rows but
  no explicit course keys: it is **not** six-course-qualified merely
  because a separate coverage flag says six boats are present.
- Stored race 20261013-04-11 has later updated source timestamps than
  the earlier failed V336 execution; an updated Git file after the
  execution cannot retroactively make a prior freeze valid.

Regression tests: tests/test_boat_edge_v236_v361_source_readiness.py.
These exercise healthy synthetic cards, course missing, both stale
sources, missing average ST, bad PRE_RESULT/locked/result flags, closed
deadline, input SHA, and diagnostics attached to failure records.
No source freshness threshold, actual-entry claim, model weights,
formal locks, public site UI, or Actions workflow file is changed.

Track 01 still owns main integration and upstream collector work.
After merge, actual success is counted ONLY if a genuinely new
predeadline freeze with source receipts and all three 120-row lists
passes V344/V343; Actions exit status alone is insufficient.


## V360/V361 naming correction and V362 labelled official start-table proof

Track 01 merged unrelated V345 writer-trigger evidence and V346 runtime
duplicate proof to main while Track 02 was developing. To avoid two
different features sharing version identifiers, Track 02's full-ranked
research module/test was renamed **V360**, and selection-time source
diagnostic module/test was renamed **V361**. V312 (hypotheses), V332
(immutable local freeze), V343 (exact replay), V344 (evidence audit) and
the existing V336 Actions workflow are unchanged in name.

**V362** adds a source-backed, strictly optional repair for
V332 candidate input containing six start-exhibition ST entries but no
explicit course indices:

1. Require an existing same-race official pre-result HTML file at
   data/raw/<date>/<venue>_<round>_beforeinfo.html. Neither a network
   fetch nor a substituted race/venue is attempted.
2. Require its SHA256 to equal the same PRE_RESULT race card's
   source_audit.beforeinfo.sha256 and its source URL to be the exact
   official beforeinfo endpoint for that race. Existing 15-minute
   beforeinfo and 16-minute race-card freshness constraints, six
   racer-feature requirements and all formal/result locks stay active.
3. Identify **one** official table labelled スタート展示 with
   explicitly labelled コース / 並び / ST headers. Require exactly
   six rows, unique boat numbers, matching printed boat image IDs,
   six verified ST strings that agree with the race input, and no
   conflicts with any already recorded course indices.
4. Only when these tests pass, assign course=official-labelled-table
   **row position** in a local candidate copy. This is not inferred
   from boat number and is still the *provisional exhibition course*,
   not independently authenticated final actual entry.
5. Preserve the exact original race_input.json **unchanged** and
   the exact original official HTML as
   data/source_captures/<date>/<race_key>/official_start_beforeinfo.html.
   Record its digest in frozen JSON and candidate; V343 must replay the
   same full 3x120 against both archived originals. Any source
   mismatch, missing/symlinked capture, wrong result/lock status or
   expired deadline aborts without an immutable research freeze.
6. When all six course fields are already valid, the former V312/V332
   path remains unchanged and V362 is unused. No historical V332
   freeze lacking original HTML may be retroactively upgraded.

Synthetic tests:
tests/test_boat_edge_v236_v362_official_start_course.py. Covers
course-swap parity, archived original byte identity, V343 360-row
replay after deleting mutable local cards, mismatched SHA, bad headers,
duplicated boat, icon mismatch, changed ST, conflicting course,
missing source, symlink, closed deadline, lock and formal exclusion.
No real race freeze, authentic upstream timestamp, external network,
official result or model-accuracy claim is established by those tests.

**Operational observation still outstanding:** an actual new
post-merge V336 run must have completed_count > 0, a valid V332
predeadline frozen record, all 3 x 120 persisted rows and a PASS
from V344/V343 on its exact uploaded artifacts. A green workflow
that reports frozen=0 remains zero valid research races.

No change to site UI, production prediction engine, model weights,
official current/future outcomes, formal Fresh results_seen/unlock/
scoring, or main/shared workflow ownership. Track 01 alone handles
PR integration and live source-collector remediation.


### V362 active official race-identity hardening (2026-10-13)

The initially introduced labelled-table proof is insufficient by itself to
exclude identical six-boat/ST data from a **different race**: source URLs
and hashes are recorded metadata, not independent proof of HTML identity.

V362 now requires exactly one official current-race navigation table matching
the saved official markup `div.table1.h-mt10 > table`, with the printed
`レース` header and 12 individually labelled `beforeinfo` links for the
same day and venue. It requires exactly one selected, uncolored race tab and
that tab's R number to equal the frozen race key. The single `締切予定時刻`
row must contain 12 displayed times and exactly one selected-time cell;
that time must equal the frozen race metadata deadline. These checks are
**in addition** to all six original source table boat/icon/ST checks and
SHA256 matching. Any mismatch is a fail-closed exception.

This was designed against actual existing repository official HTML shapes
under data/raw/20261013/{15_02,04_11,12_01}_beforeinfo.html.
Checking those HTML structures is *not* a formal future freeze, server
timestamp authentication, or independent source authorization.

V362 synthetic regression adds wrong venue/date, duplicate/incorrect race
tabs, conflicting selected race, altered deadline and wrong official page
type. It still never reads race outcomes, nor touches main or the live
source refresh workflow. Strictness can lower coverage when source and
race metadata differ; such cases must be reported, never bypassed.


### V363: V230 upstream refresh gap classification (2026-10-13 evening JST)

V334 records new optional V363 diagnostics for every selected future race.
V363 **only** checks whether the independent SITE prediction snapshot path
already exists, then cross-references V361 selection-time source status/age.
It never opens a site prediction, fetches the internet, authorizes a
late/invalid freeze, changes V230 target selection, or touches result data.

The concrete currently checked-in V230 target selector contains
`if (root/'data/site_prediction_snapshots'/f'{key}.json').is_file(): continue`.
Therefore a preexisting regular SITE freeze is a sufficient **structural
skip condition** for V230's later official refresh. V363 records this
potential overlap separately from a stale card that has no SITE snapshot;
it does not assert that this was the sole cause of a particular live run.
Symlink targets are identified but never opened or followed as evidence.

Observed **real** PRE_RESULT publishing timing on 2026-10-13:
- V336 run 38363133649 around 16:31 JST scanned 3R, frozen 0R,
  all reporting `SOURCE_TOO_STALE_FOR_FINAL_WINDOW:race_card`.
- The tracked 20261013-12-04 and 20261013-22-12 card files show Git
  commits at 16:06:56 and then 16:33:05 JST. The later commit is
  **after** the V336 failure; no retrospective validity is inferred.
- Latest V336 run 38394468129 at 21:03 JST scanned 132 cards but selected
  0R and froze 0R (`NO_ELIGIBLE_RACES_IN_CURRENT_FINAL_WINDOW`),
  which is expected when the day's final-deadline window is over.
- Existing V235 target selection can stop refreshing a card when a
  separate SITE prediction snapshot already exists. Track 01 should
  review this dependency and the source publishing cadence, but never
  republish historical source stamps as if they were live.

Synthetic V363 tests in
`tests/test_boat_edge_v236_v363_fast_lane_gap.py` cover four cases:
stale source + existing site prediction, stale source without a
prediction, fresh source with a prediction, and a symlinked path.
The independent SITE prediction file is deliberately invalid opaque
bytes in fixtures, so an accidental read would break the contract.
The classification is diagnostic only, not proof of actual causal history.

Required Track 01 follow-up: establish a **source-only** fresh official
racelist/beforeinfo refresh that is independently validated and available
before the actual final-window research execution for every still-open
candidate, regardless of whether a prior SITE prediction was frozen.
Preserve all official source hashes, timestamps, scratch checks, guards,
race identity and single-writer ownership. Do not weaken freshness,
backdate sources, overwrite immutable forecasts, or change formal
Fresh `results_seen/unlock/scoring`. After eventual merge, the actual
V336 artifact and V343/V344 replay must verify full 3×120 research coverage.
