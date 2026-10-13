# BOAT EDGE 02 — pre-result entry-uncertainty × course-strength TopK isolation

Research protocol updated 2026-10-14 JST; **no real source or score has been inspected, no verified Top3/Top5/Top10 delta exists**. The authoritative root INBOX and merged PR #201 02 addendum remain read-only; the Track 02 draft PR #192 is the research location. Merged V307/V317/V360 are reused, not replaced.

## What was actually added

`scripts/boat_edge_02_entry_marginalized_topk_research.py` uses the already existing V307 research 120 COURSE-order Plackett–Luce ranker and V317 provisional exhibition BOAT mapper. It also consumes the separately implemented Track 02 `joint_entry_distribution` (720 full course permutations, a **research-only uncalibrated weight** for each) generated from *self-reported authorized* same-cohort 6×6 observed course acquisition counts.

It generates **three strictly paired shadow research arms** from exactly the same positive 6-racer per-BOAT base strengths and the same target race input SHA:

| Arm | Course factor? | Entry model? | Interpretation |
| --- | --- | --- | --- |
| A `NO_FACTOR` | No | One observed six-boat start-exhibition permutation | Strict V307 single-entry **ability-only control** for the new feature |
| B `BASELINE` | Yes, fixed pre-target historical 6 COURSE factors | Same observed start-exhibition permutation | Isolates **course factor incremental effect** compared with A |
| C `CANDIDATE` | Same exact six COURSE factors as B | Weighted all 720 *hypothetical* course entry permutations | Isolates **entry-uncertainty incremental effect** compared with B |

This is a research decomposition: it does **not** claim A is the production CURRENT V133 model. Production-CURRENT head/TopK is a separate, independently frozen comparator that 01 would connect only after evidence gates. Site reference V360 already implements historical V307-based three feature modes using a single provisional exhibition mapping and remains **untouched**.

## Correct marginalization and invariants

For valid permutation π (boat→course), with historical relative mass q(π):

1. Set `strength(course) = pretarget_strength(boat_assigned_there) * pretarget_course_factor(course)`.
2. Call existing V307 `rank_120(strengths)` and convert each COURSE trifecta to **BOAT-number trifecta** under this hypothetical π. Hypothetical π is **not** labelled actual race course or an observed exhibition snapshot: V317 only supports real exhibition or unverified actual-course labels, so the counterfactual branch performs the short label transform without pretending 720 hypothetical π's were actually observed exhibition permutations.
3. Compute `S(boat_i,boat_j,boat_k) = Σ_π q(π)*S(boat_i,boat_j,boat_k | π)` for **all 120 distinct ordered boat triples**; sum to 1 and rank descending with deterministic boat ID tie break.
4. Return immutable-shape research documents for A,B,C (`{model_id,race_key,target_source_sha256,entry_mapping_sha256,ranked_120}`), each separately eligible for the existing **pre-result** `prepare_matched_ten` contract (never a scoring or first-Git publication certificate).
5. Report Top3 / Top5 / Top10 lists per arm and L1 distances `||A-B||₁` and `||B-C||₁`. These are measures of **changed relative model masses**, NOT improvements in hit rate and NOT calibrated probabilities.

**Core negative control:** if all course factors equal one, boat-only V307 strengths make a 720-entry mixture mathematically invariant to entry permutations. Thus `A=B=C` except floating noise. This negative control matters: without a documented course-dependent effect, 720-way computation cannot be credibly advertised as adding predictive power or new TopK accuracy. Synthetic tests explicitly enforce this.

## Eligibility / anti-leakage

All inputs are pre-result and explicit: official provisional six-boat exhibition course-permutation SHA, base target-source SHA, no scratch, no target actual course/outcome, pre-target cutoff for authorized historical venue entry counts and COURSE factors, source permission evidence, consistent 6×6 denominator N, original source first-seen time. The function does not read files, Git timestamps, the network, protected result endpoints, payouts or odds. The source/license/freeze flags are **self-assertions**; require independent 01 code review, real archive byte SHA, first Git server commit and actual permissions before any genuine frozen research trial.

The shared 02 research scope additionally **rejects** known protected formal dates 2026-10-01, 2026-10-05 and 2026-10-13; this list is conservative and **NOT exhaustive**. Source owners must check active `data/formal_status.json` protected cohorts every run, not treat a static denylist as permission for other protected dates. Never read locked Formal outcomes, now or retroactively.

## Prospective TopK evaluation decision design

1. Preregister three predictions A/B/C **and** actual CURRENT 120-ranked/fixed ten tickets before each race's deadline. For the same target official source, preserve every model ID, 120 relative weights, source/factor/cohort SHA, actual immutable Git first-commit evidence, and reason for exclusions.
2. Run **paired equal-ten** shadow comparisons A↔B and B↔C first (same race and ten tickets, equal virtual ¥10,000 each). Only compare candidate C against real CURRENT after separately establishing the same input availability, cohort, rights and pre-result Git evidence.
3. For each predeclared race report Top3/5/10 hit rates (indicator that the confirmed ordered 3連単 boat triple is in each arm's first K ranked list), head accuracy and 2着/3着 miss categories. Compute paired per-race difference `ΔK=mean(1_hit_candidate−1_hit_parent)` in **percentage points**, N/race/date/venue/eligibility, matched-pair uncertainty CI; do not use mismatched Ns, retrospective opponent selection or stake/odds boosting.
4. Log loss / multiclass Brier for all **120** require a valid joint categorical probability model with out-of-sample calibration. Outputs here are **relative masses** and are explicitly `calibration_validated=false`. Do not call their log loss/Brier proven risk scores before a distinct held-out calibration study and evidence-gated scoring.
5. The promotion condition remains a **multi-day untouched independently frozen comparison**, no sample-specific cherry-picking, statistically supported Top3/5/10 gain and no material guardrail regressions. No cohort meeting those conditions has been produced.

## Coordination

01 owns provider-rights review, provenance/first Git SHA verification, live-source/archive infrastructure, merges, and eventual production change. 03 owns UI explanation only after adoption. 02 does **not** directly change shared workflows, site prediction policy or site JSON and has not created a results scorer. The merged PR #201 remains source-research documentation rather than authorization to scrape BOATERS/日和 or inject self-attested びわこ example percentages into an actual model.

Formal latest status re-read from `data/formal_status.json` at this audit: snapshot `asOf=2026-10-13T23:59:44+09:00`, First100 0/100, `results_seen/unlock/scoring=false` and TOKEN null. This timestamp describes the file, not proof of today's verified real-time status.


## Subsequent TopK movement diagnostics and temporal source-method distinction

The ablation now emits **three-arm** BOAT-number Top3/Top5/Top10 ticket membership deltas `topk_membership_a_to_b_not_hit_rates` and `topk_membership_b_to_c_not_hit_rates`, with each K's sorted removed and added ticket IDs, `changed_ticket_count_per_side`, and whether order is identical. It separately emits `head_relative_mass_a/b/c` (six normalized **relative** values, NOT calibrated head probabilities), predicted top-head boat A/B/C and two changes in the top-head label. These are prospective pre-result movement metrics, not scored hit rates. A nonzero \(\ell_1\) difference may still leave Top3/Top5/Top10 **identical**; never report such a case as TopK improvement. Conversely a new Top3 ticket is merely a candidate until actual **unseen** paired target settles under a separately authorized source.

**Critical limitation of current research arm C:** the venue×boat frame→actual course counts induce an unconditional, historical *marginal prior*. The calculation does **not** estimate `P(final actual course permutation | today's already observed start exhibition, six named racers, weather, deep-in/前付け)`. Computing a distribution from those historic marginals and comparing it to the observed exhibition single-entry baseline is **not** proof that 720 alternatives are a well-calibrated posterior. The module sets `live_exhibition_conditioned_entry_transition_learned=false`, `entry_720_relative_weights_are_not_calibrated_posterior=true`. This is a **methodology blocker**, not merely a missing ingestion file.

**Next genuine, nonduplicative feature contract R03/R04/R13:** after independent data-rights confirmation, require only *historically paired* start-exhibition permutation AND confirmed final actual-course permutation under same unique race ID, recorded publication times for each, real six-racer identifiers, scratched races excluded, target-day and Formal-protected dates excluded. From strictly older records fit `P(final permutation | observed exhibition, venue, racer competing entry intentions)` with proper shrinkage and explicit support counts, avoiding impossible independent per-boat courses. The single marginal-prior C remains a negative diagnostic, **not** an eligible production-candidate adoption without this conditional entry evidence.

**Existing freeze/replay is already solved structurally:** V343 stores exact predeadline race input bytes; V344 combines V339/V340/V343 local integrity/replay and accounts for failed races; V360 stores 120 research tuples per mode. No new snapshot capturer or scorer is being built in this branch. Even V344 local PASS is not independent trusted Git first-publication evidence or proof of rights. Track 01 must validate actual server-time and each required official/BOATERS/日和 source before any historical claims. Site and protected Formal data remain untouched.
