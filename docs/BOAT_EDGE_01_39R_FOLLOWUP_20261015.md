# 2026-10-15 01 follow-up: 39 missing race saves and writer audit

Pinned inspection: `932f84ee6c7a86308014349e66ca5d1923a27e04`. Actions refreshed at approximately 2026-10-15 13:54 JST. This report changes no operational workflow, prediction, source data, first-save gate, model or Formal Fresh lock.

## Evidence and limits

Read only V215 PRE_RESULT history and snapshot path existence for 2026-10-14; no result/payout reads. History SHA256: `da4161606c7fb524d427a21fe8479445da6fc600605e55b896ba89ea895a342b`. 124 observed, 85 snapshot paths present, 39 absent. Path existence does not independently prove first Git-add or valid snapshot bytes. Prior SHA/attestation figures are not re-certified here. Source gaps below are the union of sampled observations, not a proven cause at every freeze attempt. No gaps means NOT_OBSERVED, not eligible.

## Every missing race

|Race key|Venue|Deadline JST|Last observation lead (min)|Observed gaps|Follow-up classification|
|---|---|---|---:|---|---|
|20261014-04-06|平和島|12:53|11.0|none observed|NO_GAPS_OBSERVED; eligibility unproven|
|20261014-04-08|平和島|13:57|11.2|none observed|NO_GAPS_OBSERVED; eligibility unproven|
|20261014-04-11|平和島|15:40|3.7|beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_missing_or_blocked, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-06-06|浜名湖|13:47|7.7|beforeinfo_not_ok, pre_result_odds_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-06-07|浜名湖|14:15|3.5|beforeinfo_not_ok, pre_result_odds_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-06-10|浜名湖|15:37|11.0|beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-11-05|びわこ|12:08|7.7|beforeinfo_not_ok, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-11-08|びわこ|13:45|5.7|beforeinfo_not_ok, pre_result_odds_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-12-06|住之江|17:25|12.4|beforeinfo_not_ok, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-12-07|住之江|17:52|2.8|beforeinfo_not_ok, race_card_stale, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-13-02|尼崎|11:08|11.3|beforeinfo_not_ok, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-13-08|尼崎|14:05|3.4|beforeinfo_not_ok, race_card_stale, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-13-11|尼崎|15:33|7.0|beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-13-12|尼崎|16:05|12.1|beforeinfo_not_ok, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-14-10|鳴門|12:58|2.8|beforeinfo_not_ok, official_dom_proof_missing, pre_result_odds_120_incomplete, pre_result_odds_stale, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-14-12|鳴門|14:11|9.4|beforeinfo_not_ok, race_card_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-15-02|丸亀|15:44|7.7|beforeinfo_not_ok, pre_result_odds_unverified, race_card_stale, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-15-07|丸亀|17:58|8.0|beforeinfo_not_ok, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-15-11|丸亀|20:08|10.8|none observed|NO_GAPS_OBSERVED; eligibility unproven|
|20261014-18-04|徳山|10:01|12.1|beforeinfo_not_ok, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-19-03|下関|18:34|3.6|beforeinfo_not_ok, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-19-04|下関|19:03|3.3|beforeinfo_not_ok, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-19-10|下関|21:51|5.6|none observed|NO_GAPS_OBSERVED; eligibility unproven; no V229/V235 run created in 2–10m query|
|20261014-19-11|下関|22:20|10.5|pre_result_odds_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-20-01|若松|15:25|13.3|none observed|NO_GAPS_OBSERVED; eligibility unproven|
|20261014-20-02|若松|15:54|10.6|none observed|NO_GAPS_OBSERVED; eligibility unproven|
|20261014-20-05|若松|17:19|6.4|beforeinfo_not_ok, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-20-10|若松|19:49|6.1|beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-20-11|若松|20:18|4.2|beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-21-07|芦屋|11:37|9.4|none observed|NO_GAPS_OBSERVED; eligibility unproven; inspected V229 execution outside 2–10m window|
|20261014-21-12|芦屋|14:27|13.0|none observed|NO_GAPS_OBSERVED; eligibility unproven|
|20261014-22-08|福岡|14:24|10.0|beforeinfo_not_ok, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-22-10|福岡|15:30|4.0|none observed|NO_GAPS_OBSERVED; eligibility unproven; no V229/V235 run created in 2–10m query|
|20261014-22-12|福岡|16:31|5.6|beforeinfo_not_ok, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-24-01|大村|15:23|11.3|none observed|NO_GAPS_OBSERVED; eligibility unproven|
|20261014-24-07|大村|18:03|13.0|beforeinfo_not_ok, race_card_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-24-08|大村|18:40|9.6|beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-24-09|大村|19:11|6.4|beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|
|20261014-24-10|大村|19:42|3.1|beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_missing_or_blocked|SOURCE_GAPS_OBSERVED; exact attempt cause unproven|

29 races have observed gaps, 10 have none. The ten comprise three last sampled inside the freeze clock window and seven outside. These are observation categories, not ten proven scheduler failures.

## Narrow Actions cross-check

- 芦屋7R deadline 02:37Z: query 02:27–02:37Z returned 31 runs (below 100-page limit). V229 run [38501888932](https://github.com/ikst2512-eng/boat-edge/actions/runs/38501888932) executed freeze at **02:36:34Z**, only 26 seconds before deadline. It logged `new_snapshots: 0`, `V229_NO_NEW_ELIGIBLE_SNAPSHOT_NO_FABRICATED_PASS`. This inspected attempt missed the 2–10m window; it does not exclude an earlier-started attempt. Job 115650530873.
- 福岡10R deadline 06:30Z: 06:20–06:30Z query returned 18 runs, no V229/V235 created.
- 下関10R deadline 12:51Z: 12:41–12:51Z query returned 16 runs, no V229/V235 created.
- Creation-time queries do not cover jobs created before the queried window and still running inside it. Full per-race causal proof remains incomplete; do not re-create past predictions.

## Current scheduled ownership

225 YAML workflows, **44 scheduled**, **38 scheduled contents-write candidates**. Previous report 47/41 was stale. These are source-level counts, not GitHub enabled-state or proven simultaneous-writer counts.

|Overlap / unnecessary work|Current evidence|Disposition|
|---|---|---|
|V238 / V241 cron plus V235 event fanout|Event fanout already absent on pinned main|Keep bounded hourly/manual jobs; no repeat edit|
|V109 / V125 CURRENT_TODO writer|V109 restores local TODO before staging only results/archive; V125 stages audit TODO|Already separated; no repeat edit|
|V180 / V185 / V186 bundled source restoration|Tracked-source checks already replace historical reinstalls|Existing guard regression PASS; keep frequencies|
|V234 / V235 / V254|All explicitly stage `data/site_autopilot/v254_pre_current.json` and `v254_frozen/`|Exact path overlap established; per-race redundant writes and replacement coverage unproved. Preserve first-save logic|
|V228 / V229 / V133|Snapshot directory overlap with independent validation/history roles|Do not disable from directory overlap alone|
|V125 / V229|Audit directory overlap|Need exact race/SHA and consumer tracing before retirement|
|V133 installer TODO staging|Installer job has constant false condition|Dormant, not a current scheduled TODO writer|

## Current failure requiring separate guarded investigation

Collector [38683399185](https://github.com/ikst2512-eng/boat-edge/actions/runs/38683399185), job 116252738963: PRE_RESULT collection and same-commit scratch passed; publication failed. Log: `V277_FROZEN_RACE_SOURCE_MUTATION_BLOCKED_20261015-04-08,20261015-06-07`, then `V01_REMAINING_SOURCE_DEADLINE_PASSED_20261015-10-11`. This is a verified current publication stop, NOT evidence that it caused yesterday’s 39 misses. Do not bypass guards or alter source preservation/first-save policy in this cleanup.

## Validation and disposition

- Existing scheduling/reinstall/inventory tests: 21 PASS.
- Source pin verification: PASS (5 workflows).
- V271 health: 7 PASS.
- No additional production cleanup was proven safe beyond already merged fixes. This follow-up adds only this audit; it deliberately does not retire speculative duplicates.
- Formal status independently read at pinned main: first100=0, results_seen/unlock/scoring=false, token=null.
- Pages dynamic run 38683615831 on pinned SHA succeeded; controlled publishing success still does not prove deploy, and older cancelled Pages runs alone do not prove current outage.
- Remaining: exact historical job coverage / per-attempt source blockers for all 39; real enabled-state inventory; first scheduled runs after existing cleanup; controlled Pages exact SHA and live browser acceptance.
- Required V23* fixture suite: **395 PASS** with the primary runtime (requests/bs4/lxml/yaml available). Initial system-Python run had dependency errors; it was not a product failure or passing result.
