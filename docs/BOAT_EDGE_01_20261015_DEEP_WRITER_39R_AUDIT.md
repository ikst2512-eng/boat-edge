# BOAT EDGE 01 — 2026-10-15 pre-deadline freeze and scheduled-writer deep audit

**Audit scope:** read-only SITE PRE_RESULT observations for 2026-10-14; live workflow source on main; no retrospective forecast creation, result/payout endpoint, betting action, or Formal Fresh unlock. This is an operations audit, **not** proof of an accuracy improvement.

## 1. Yesterday's 124-race observation funnel (verified against saved V215 and V220)

- V215 observed **124 races**. Snapshot found for **85**; no snapshot after deadline for **39**.
- Of the 85: **84** have matching audit SHA and pre-deadline metadata, **79** have matched V229 same-run atomic attestation. **One** snapshot/audit failed that verification; six of the 85 do not have matched V229 attestation (these counts overlap with the SHA mismatch). No result must be inferred from an Actions green check.
- 39 missing: **29** with one or more *observed source gaps*, **10** with *no observed gaps*. In the 29, non-exclusive indicators include `beforeinfo_not_ok=28`, `scratch_missing_or_blocked=16`, `scratch_stale=13`, `race_card_stale=13`, `pre_result_odds_stale=13`, and single 120-odds incomplete / DOM proof missing / unverified odds records. These are overlapping indicators, not disjoint reasons.
- An early missing status later became an existing snapshot for **64** observed races; do **not** count any early failure as a final miss before the deadline.

### Ten missing with no observed gaps — investigate first, do not reconstruct

| Race key | Venue | Deadline JST | Last V215 observation, minutes before deadline | V229 2–10m window? |
| --- | --- | --- | ---: | --- |
| `20261014-04-06` | 平和島6R | 12:53 | 11.0 | No |
| `20261014-04-08` | 平和島8R | 13:57 | 11.2 | No |
| `20261014-15-11` | 丸亀11R | 20:08 | 10.8 | No |
| **`20261014-19-10`** | **下関10R** | **21:51** | **5.6** | **Yes — P0** |
| `20261014-20-01` | 若松1R | 15:25 | 13.3 | No |
| `20261014-20-02` | 若松2R | 15:54 | 10.6 | No |
| **`20261014-21-07`** | **芦屋7R** | **11:37** | **9.4** | **Yes — P0** |
| `20261014-21-12` | 芦屋12R | 14:27 | 13.0 | No |
| **`20261014-22-10`** | **福岡10R** | **15:30** | **4.0** | **Yes — P0** |
| `20261014-24-01` | 大村1R | 15:23 | 11.3 | No |

V215 `source_gaps_seen=[]` says **no gap observed during sampled checks**, not that all official race-card bytes, 120-odds SHA, exhibition source permissions, first Git add, and V229 worker execution were verified. Last V215 check in the eligible clock window does **not** prove V229 actually ran at that instant. Establish reason codes by cross-checking corresponding V229/V235 and source collection jobs, saved race and odds bytes, first Git-add timestamp and SHA. Missing snapshots cannot be recreated after result.

## 2. Workflow pressure and true vs apparent success

- The 2026-10-14 19:07Z Development CI V299 inventory reported **225 YAML workflows**, **47 scheduled** and **41 scheduled contents-write candidates**. This is a **static** count, not 41 confirmed simultaneous duplicates or proof each is currently enabled. **32** old stubs are guarded to `workflow_dispatch` in that report.
- Workflows using the same directory/path are candidates only; some are separate immutable freeze and later audit stages. Retiring a race writer without a verified substitute can worsen the 39-race deficit.
- GitHub Pages currently uses **legacy branch deployment**. Successful `pages-controlled-publish.yml` verify-source does not imply a deployment: its stage/build/deploy were actually **SKIPPED** in inspected runs, logging `PAGES_LEGACY_SOURCE_UNCHANGED_NO_CUSTOM_DEPLOY`. Legacy dynamic Pages publishes often succeed, but successive main data pushes have also cancelled earlier builds. Admin Pages Source → GitHub Actions + actual staged SHA verification is a separate required gate.
- `boat-edge-03-real-browser.yml` can return overall SUCCESS from read-only `v229-source-first-add` while `selected-race-to-prediction` is **SKIPPED** because no qualifying first Git-add exists. Do **not** call that run Chromium/WebKit live Top3/5/10 acceptance.
- 02 has draft PR **#192** (50 changed files) and **#253** (34 changed files), sharing `scripts/boat_edge_v301_paired_evidence.py` and `tests/test_boat_edge_v236_v301_paired.py`. Do not merge both wholesale; reconcile on current main in a 02-owned smaller PR.

## 3. High-confidence removal of obsolete overwrite pathways

A new exact-source audit found three scheduled workers with old gzip/base64 asset bundles that unconditionally or conditionally **overwrite current tracked scripts**:

| Worker | Cron configured | Historical overwritten assets | Action |
| --- | --- | --- | --- |
| V180 | every 10 minutes during JST 08–24 | `scripts/site_v180_shadow.py`, `tests/test_v180_shadow.py` | Replace installer with tracked-files existence check |
| V185 | every 10 minutes during JST 08–24 | `scripts/site_v185_role_shadow.py`, `scripts/site_v185_score.py`, two tracked tests | Same |
| V186 | every 5 minutes during JST 08–24 | `scripts/site_v186_refresh_scratch.py`, `scripts/site_v186_patch_ui.py`, one tracked test | Same |

All nine paths already exist in main. This eliminates the mechanism for a live worker to silently restore an older implementation and stage the diff for a subsequent main commit. **No schedule is retired**, because V180/V185 are prospective-only research and V186 supplies near-deadline scratch evidence; required tests, output paths, Git-first-add boundaries and immutable data remain unchanged. The number of static scheduled writers is therefore not reduced by this PR; instead its highest-risk historical code rollback path is removed.

## 4. Other suspected redundancy — deliberately NOT deleted yet

1. V234 and V254 both stage `data/site_autopilot/v254_pre_current.json` and `data/site_autopilot/v254_frozen/`; possible exact writer collision, but prospective source-window coverage and first-add preservation require independent runtime proof before reducing either path.
2. V125/V229 both write per-race audit JSON. PR #376 protects V229 proof on exact snapshot SHA; verify next live matching race before merging the jobs.
3. V180/V185 research, V194 prospect diagnostics, V197 independent quality gate, V198 miss diagnosis, V183 scorer and V190 scorer overlap conceptually, but each publishes different evidence and may have distinct source-before-result requirements. Compare **actual downstream readers and last unique changed bytes** before disabling.
4. V171 restores a historical research-only script that is not currently tracked as `scripts/site_v171_prospective.py`; this is not a safe candidate for the blanket tracked-file conversion above. Needs separate dependency/status audit.
5. V216 runs a multi-stage source/readiness/paper chain. V220 event recovery is gated to same-repo main success with a 15-minute per-workflow cooldown. Shorten only after deadline-window first Git-add evidence confirms no regression.
6. The daily restart of official PRE_RESULT collection and 120 odds is still required. Do not mistake no overnight frozen snapshot for a missing freeze when no race is within 2–10 minutes of local deadline.

## 5. Release gates (strict)

1. Fixture CI tests assert V180/V185/V186 can no longer reinstall old code, and retain their scheduled validation/freezing paths.
2. PR merged by 01 only after clean merge and CI; independently observe **main CI and the first scheduled V180/V185/V186 runs**, including whether their original prediction source files remain unchanged.
3. Monitor V215 matured observation → eligible source → first Git-add SHA → V229 audit → browser TopK evidence per race. Distinguish `NOT_ELIGIBLE`, `NOT_OBSERVED`, `SCHEDULER_OR_FREEZE_FAILED`, and `PROVEN_FROZEN`; never backfill.
4. Confirm Pages build_type=`workflow`, controlled build/deploy success, published source SHA and Top3/5/10 in both browser engines before calling production deployment stable. **A green PR/main CI is insufficient.**
5. Formal Fresh 2026-10-15 remains `formalFirst100.races=0`, `results_seen=false`, `unlock=false`, `scoring=false`, token null; leave formal results untouched.

**Three-chat verdict:** independently branched 01/02/03 development can proceed with shared-path ownership, but a claim of completed production stabilization remains **NOT PASS** until the source, deployment, and live browser gates are met.
