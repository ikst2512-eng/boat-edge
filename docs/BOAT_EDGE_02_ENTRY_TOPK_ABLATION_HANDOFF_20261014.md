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


## 2026-10-14 P1 continuation — paired HISTORICAL exhibition→actual course transitions

After verifying no equivalent function already exists in V307/V317/V343/V344/V360 or PR #192, Track 02 added `scripts/boat_edge_02_exhibition_to_actual_entry_research.py` and dedicated synthetic regression tests, and reused the SAME `prepare_entry_topk_ablation` 720→120 aggregator with an **explicitly exclusive alternative entry-evidence mode**. The original unconditional venue-frame marginal entry branch remains unchanged.

### What is new and precisely what it is not

From only operator-supplied and independently rights-reviewed historical *same-race six-boat* paired records, each row includes exact 6-boat **start exhibition** mapping, 6-boat **confirmed actual course** mapping, race key, venue, historic race deadline, source byte SHA, exhibition first-seen time, final course first-seen time, scratch status, and permission declaration. It derives a bijective **relative transition** `T[exhibition_course] = final_actual_course_of_the_same_boat`; 720 possible reordering patterns. It counts the same patterns nationally and by the target venue, requiring at least 30 national and 8 local paired historic examples (only rudimentary code quality thresholds, **not statistical sufficiency**). A fixed declared concentration of 30 shrinks local toward **observed** national pattern frequencies, without inventing uniformly possible unobserved patterns.

For the next race's actual *observed exhibition permutation*, every reordering pattern maps the BOAT identifiers into a hypothetical *final* six-course permutation. That produces 720 relative research weights with a fixed target exhibition; the exact pre-result marginalizer sums them into 120 BOAT-number trifecta relative weights. In the existing A/B/C design, A=no course factor and exhibition entry, B=same exhibition entry with course factor, C=B factors with exclusively selected one of:
1. Existing venue frame→actual course **marginal prior** (`entry_evidence`, not conditioned on today's exhibition);
2. **NEW** pooled historical exhibition→actual relative transition patterns (`paired_history_evidence` + `paired_history_rows`). Caller must select **exactly one**; mixing is rejected.

The new transition counts are **pooled across historic exhibition permutations**; they are **NOT** yet `P(final six-entry permutation | exactly this historic exhibition pattern, named six racers, weather, deep-in)`. Applying the observed target exhibition transformation does **not** make the original pooled frequencies fully conditionally calibrated. Code labels `historic_transition_counts_conditioned_on_exact_exhibition_pattern=false`, `full_conditional_entry_posterior_calibrated=false`, `entry_720_relative_weights_are_not_calibrated_posterior=true`, `production_eligible=false`. This honest distinction prevents promoting synthetic-only model movement to measured TopK improvements.

### Fail-closed timeline and provenance requirements

- The target's actual final entry or outcomes may NEVER be inputs. Target's six actual exhibition entries and SHA must be present BEFORE caller-claimed first freeze.
- Every historical exhibit timestamp must be **strictly before that historical race's own deadline**; the historical final course timestamp must be at/after that deadline and available no later than `scope.train_end` and before target freeze. Reject wrong timezone, dates, duplicate IDs, unsorted records and missing fields.
- Exclude known protected Formal dates 2026-10-01/05/13 plus the **current dynamically reviewed protected-date list** supplied by an operator; never assume that the static list is complete. Self-reported source rights, first-Git-clock and hashes are only input shape claims; third-party authentication has **NOT** happened.
- No BOATERS or 競艇日和 numeric input collected; no unsupported provider login/scrape, API or result/payout endpoint. Official historic pair acquisition is **blocked** pending operator review of permission, immutable original source manifests, six-course availability and server-time provenance.
- Existing matched-ten code `prepare_matched_ten` is reused for B↔C Top10 and for A↔B; no duplicate scorer or live workflow is created. Top3/5/10 ticket membership replacements and head-mass changes are model movement diagnostics only.
- Training measurements and prospective scoring must be strictly separate, and an authentic multi-day untouched comparison with CURRENT must precede any claim of accuracy lift.

### Next gate for Tracks 01 / 03

01 to determine whether independently licensed **historical exhibition + independently verified final actual course** pairs can be archived without entering any protected Formal result periods; review actual historical course provenance, use rights, source availability and first Git server-time SHA. If missing, leave this research blocked. 02 would then measure venue/sample-specific uncertainty and ablations, controlling pre-result exhibition as-of time. 03 gets **no** new production UI features until independently demonstrated Top3/5/10 lift and Track 01 promotion.


## 2026-10-14 next step — EXPLICIT exact six-boat exhibition-pattern cohort

New **optional** `conditioning_mode=EXACT_EXHIBITION_PATTERN` on the existing history-only `estimate_exhibition_conditioned_entry`. No duplicate result fetcher, no new scoring engine, no modification to V307/V317/V343/V344/V360. Input shape and source rights/clock verification remain as before; the new work uses the same strictly sorted historical paired 6-boat exhibition → officially verified final-actual-course observations.

**Previously** the pooled estimator counted relative six-course reordering patterns across **all** historical exhibition BOAT configurations. It then applied that pooled transition rate to today's exhibition BOAT configuration. This is not the same as selecting the historical subpopulation whose observed full-six BOAT→exhibition-course permutation **exactly equals today's**.

**Now** the exact-pattern branch collects four observed, mutually nested populations: all national historic paired transitions, same-venue pairs, exact exhibition-pattern national pairs, exact exhibition-pattern at the same venue. Fixed training-only concentration `30` shrinks pooled venue toward the all-national distribution, then national exact toward pooled venue, then venue exact toward national exact. The ordering/alpha is a **hypothesis, not calibrated evidence**; venue and national rows share a population and may not be independent. Do **not** describe these shrinkage layers as causal racer interaction or validated likelihood. The mathematical 720 permutation constraint is preserved; no synthetic observed events are added, but zero historic support can still produce zero model weight for physically possible permutations.

**Fail closed on exact-pattern absence:** the new branch requires at least 30 observed matched exact exhibitions nationwide and 8 at the target venue, on top of pooled 30 national / 8 local; otherwise raise `EXACT_EXHIBITION_PATTERN_SUPPORT_TOO_SPARSE`. These limits are *minimum research input* thresholds, **not** a statistically justified signal-detection sample size. The branch does **not** silently use the pooled model when exact support is absent.

**Output versioning:** historical transition producer uses `BOAT_EDGE_02_EXACT_EXHIBITION_PATTERN_TRANSITIONS_RESEARCH_V2`; associated TopK marginal study uses `BOAT_EDGE_02_V307_EXACT_EXHIBITION_PATTERN_RESEARCH_V3`. Pooled historic transition and old frame-course prior preserve **different** IDs. The caller must opt in via `paired_history_mode=EXACT_EXHIBITION_PATTERN`, supplying paired historic evidence and rows and excluding the separate unconditional frame prior. Both create full BOAT 120 relative-weight orders using the already installed V307/V317 research logic and Top3/5/10 ticket turnover diagnostics. Mixing modes or unknown mode values fails.

### Important remaining blockers

- **No independent source or rights verification:** historical source URLs, immutable raw bytes, permitted bulk training rights, event-time receipts, first-Git-server SHA/time and actual-course authenticity are *not* verified by research functions; all sample fixtures are fabricated. The 01 evidence/source owner must validate those before any authentic test.
- **No outcome-proof:** all 720 entry scores and 120 trifecta scores remain **relative model masses**, not prospective calibrated probabilities. Even exact-exhibition-pattern cohorts are not named-racer, weather, deep-in, slot-gap or start-timing conditioned. No actual unseen Top3/5/10 gain is claimed.
- **No protected results:** dynamic Formal protected cohort list must be independently checked (static known 10/01, 10/05, 10/13 remains additional deny-list). Formal First100 is still locked; do not access any result page, combined API or payout to fill training rows.
- **Ablation program:** compare **(A)** V307 strengths-only single exhibition, **(B)** V307 + historical course factors single exhibition, **(C1)** B with pooled historic exhibition→final transitions, **(C2)** B with the **exact** exhibition-pattern relative transition study. Each must be independently predeadline Git-frozen on the *same race*, source SHA, with **10 tickets vs 10** at equal virtual budget. Use matched pair Top3/5/10 deltas, head and omissions, per-day N/CIs and only authorized later **SITE research** outcomes. CURRENT production is an additional separately recorded true comparator, not assumed equal to arm A.
- **No auto merge/promotion:** 02 PR remains draft; Track 01 owns integration, and Track 03 must not expose results as calibrated prediction probabilities without true prospective proof.
