# Gate 1C — 2026-10-23 Karatsu 10R pre-deadline freeze gap (read-only)
 
## Scope and status
- Race key: `20261023-23-10` (Karatsu 10R); deadline 15:20 JST.
- **UNRESOLVED / NOT PROVEN ELIGIBLE**. Do not label this as a verified missed eligible freeze.
- Site-only pre-result evidence. No outcome, payout, Formal Fresh or score reads. No prediction backfill or altered saved bytes.
- This is an evidence checkpoint, not a model change or a 99% acceptance claim.

## Observations on tracked main JSON
- `data/races/20261023-23-10.json`: racelist `ok` fetched 15:03:49+09:00; beforeinfo `ok` fetched 15:02:59+09:00; six exhibition lanes and six start-exhibition lanes marked complete. Deadline 15:20.
- `data/site_odds/20261023-23-10.json`: `available_count=120`, `odds_validation=VERIFIED`, `verified_official_dom_v167=true`; fetched 15:00:39+09:00. That observation was **19m21s before deadline**; it is not by itself evidence of valid freshness at every subsequent freeze decision.
- `data/site_scratches_v182/20261023-23-10.json`: `blocked=false`, checked at 15:04:29.170693+09:00.
- At this inspection, `data/site_prediction_snapshots/20261023-23-10.json` and `data/site_prediction_audit/20261023-23-10.json` were absent from repository main.
- V215 `data/site_paper_sim/readiness_history_v215/20261023.json`: this race's `source_gaps_seen=[]`. A sampled gap-free observation does **not** prove all V229 source/readiness conditions. No first Git commit at a fixed pre-deadline time is established by these current files alone.

## Independent 1C context (saved monitor snapshot, not all races)
- `data/site_ops_v220/gate1c_current.json` at inspection: 34 matured V215-observed races, 20 snapshot files, 14 missing; 20 first-Git-original proofs among saved. It explicitly leaves the independently source-eligible denominator `null` and `acceptance_99_percent_proven=false`.
- `data/site_ops_v220/current.json` reports a stale V216 observation during the race window. This is not proof that the V229 freezing job did not run for Karatsu 10R.
- The current rolling `data/site_autopilot/v230_fast_current.json` was for a different race (`20261023-12-02`) and is insufficient to reconstruct Karatsu 10R's past execution.

## Next decisive evidence (no backfill)
1. Resolve immutable Git tree(s) and commit times in the **15:10–15:18 JST** strict V229 decision window; verify official HTML hashes, race card, 120 odds, scratch and their **Git publication** before each attempted freeze, with the exact gate checker.
2. Enumerate V229/V235 and permitted backup dispatch run creation/job start and outcomes for the same window. Avoid treating absence from a rolling current.json file as no Action execution.
3. If all source and safety gates pass at a documented decision instant but no first Git prediction add exists, classify the execution/save path. Otherwise classify the specific source gate or `unknown`.
4. Keep Formal Fresh guards closed and do not reconstruct/publish a late prediction.

This checkpoint is a **read-only forensic account**, not closure of Gate 1C/1D.

## Additional workflow inspection (2026-10-23)
- Tracked `.github/workflows/V235.yml` declares scheduled runs at minute `2,7,12,17,22,27,32,37,42,47,52,57` during UTC hours 0–14 and 23, plus a 23:20 UTC cron and dispatch/workflow-run triggers. For the 15:10–15:18 JST (06:10–06:18 UTC) Karatsu window, nominal scheduled minutes include **06:12 and 06:17 UTC**. These are configuration, **not proof that Actions runs were actually created or executed**. GitHub schedule delay/skips cannot be inferred away.
- The V235 workflow contains a tracked V230 refresh and strict V229 freeze integration and logs a zero-freeze diagnostic. A rolling `v230_fast_current.json` for another race cannot establish Karatsu 10R run outcome.
- Required remaining evidence: actual Actions run IDs, created/start times and logs for the 06:10–06:18 UTC window, paired with same-time committed source trees. **No scheduler defect or official-source failure classified yet.**

## Additional raw-source prerequisite check
- Both current-main tracked raw official PRE_RESULT HTML paths exist: `data/raw/20261023/23_10_racelist.html` (Git blob `12a45fafbc134ecab421f8c896bad34bb34c7ba6`) and `data/raw/20261023/23_10_beforeinfo.html` (Git blob `02dc033cb0f72ccbc2d6660555f283d7371835d1`). Their **existence on current main does not prove** same bytes were committed within 15:10–15:18 JST or that their SHA-256 matches the source audit. Git blob SHA-1 and declared original-content SHA-256 are distinct hashes.
- Reviewed `scripts/boat_edge_01_gate1c_source_ready.py`: a positive source-ready receipt requires strict 2–10 minute lead time; complete, correctly identified official race and 6-lane beforeinfo; original HTML content SHA-256 parity; source_status freshness and 120 official odds; scratch consistency. **JSON flags and scheduled cron alone are insufficient**.
- The connected GitHub run-detail endpoint requires a numeric run ID; the available commit-linked run search filters to pull-request-triggered runs and cannot independently enumerate all scheduled V235 runs for the incident interval. Thus actual 15:12/15:17 scheduled execution remains unverified, not absent.
