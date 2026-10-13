# BOAT EDGE 03 — スマホUI・Safari・表示品質の追加調査

Date: 2026-10-14 JST. OWNER: 03 UI-only branch/PR. 01 owns final integration / Pages. RESEARCH_ONLY; no HTML/CSS/JS edited in this PR.

## External UI/testing methods

- Playwright device emulation / touch / timezone: https://playwright.dev/docs/emulation
- Playwright WebKit browser: https://playwright.dev/docs/browsers
- Playwright screenshot snapshots / visual compare: https://playwright.dev/docs/test-snapshots
- W3C WCAG 2.2 minimum touch target guidance: https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- W3C WCAG 2.2 accessible status changes: https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html
- Lighthouse CI regression testing: https://github.com/GoogleChrome/lighthouse-ci
- Core Web Vitals LCP/INP/CLS: https://web.dev/articles/vitals?hl=ja

**Important distinction**: Playwright's WebKit + iPhone device emulation is useful CI coverage but is NOT physical iOS Safari; actual iPhone acceptance remains a separate manual or verified device-farm gate. Lighthouse is lab regression evidence, not proof of accuracy or live Safari pass.

## Existing BOAT EDGE overlap

- `BOAT_EDGE_AUTODEV_TASKS.md` A01–A33 are checked, but an item checked by code review is not a device acceptance proof.
- `BOAT_EDGE_MASTER_TODO.md` T14/T15/T17/T18 call for full iPhone flow, verified hit/miss/pending/ineligible, staleness and separate completion stages.
- `data/site_ui_display_requirements.json` expects ¥10,000 mode allocation UI, all 6 lane colors, verified win only on frozen prediction and real source-confirmed outcome, no fabricated payouts.
- Merged PR #200 https://github.com/ikst2512-eng/boat-edge/pull/200 already fixes incorrect labels where `mode='blocked'` and null were called a normal reference prediction. DO NOT replicate. Open PR #202 https://github.com/ikst2512-eng/boat-edge/pull/202 independently hardens homepage/results-list 🎯 proof; 01 must review its HEAD and CI before merge. Successful CI/Pages remain separate from physical iOS Safari acceptance.
- 03 already has mobile readability CSS and multiple UI feature variants. Simplify only after live DOM ownership and tests; do not blindly rewrite or delete historical assets.

## P0 UI acceptance design (not a proposed rewrite of model)

**Single race source of truth**
A state object per selected race: `race_key, venue, R, deadline, displayed_prediction_mode, model_id, prediction_freeze_sha, prediction_created_at, input_asof, source_verification, source_freshness, official_odds_asof, rendered_ticket_ids`. The client should reject mismatched race key / stale async response and not silently substitute data from a previously selected race.

**Five clearly distinct states**
1. Official/formal CURRENT proof passed (only when independently authenticated).
2. Site reference forecast (non-formal, not blocked).
3. Prediction blocked due to missing source, scratches, or uncertainty.
4. Loading / no prediction yet.
5. Result-only state: awaiting/verified hit/verified miss/ineligible; only paired with immutable predeadline issued tickets and authorized settlement.

**Mobile information order**
Venue & R + official deadline → badge-free compact as-of/source evidence → 6 racers + course & scratch → head / Top3/5/10 → why (start, 1M attack, beneficiary, expected finish) → frozen ticket order, amount and *verified predeadline odds* → separately authorized result. Maintain selected race in URL/state where safely possible; do not auto-refresh predictions from browser at incorrect times.

**Accuracy-honest numerical labels**
- `relative_model_mass` / budget proportions are NOT win probabilities; display only as relative weights.
- Head probability must not be conflated with full trifecta Top10 coverage.
- ¥10,000 shown per mode/selection vs separate ¥50,000/day virtual research cap; no actual wager or cash transfer.
- Missing payouts/odds/source data must remain 未取得/未確認, never 0 or verified.

## Regression matrix to add after 01/03 review

- Mobile WebKit + Chromium, emulated narrow and large iPhone viewports, JST timezone and touch; desktop fallback.
- Snapshot fixtures for six lanes, long racer names, clipped text, multi-mode tickets, 3/5/10, scratches/cancellations, blocked/no-data/slow network/stale/official unverified, dark/light, screen readers.
- User flows: switch venue/R rapidly while fetches complete out of order; refresh with network unavailable; preserve selected race and displayed freeze; comparison/odds/result navigation; keyboard/touch controls and tap target spacing.
- Regression asserts `rendered ticket order, numbers, freeze source SHA, stake amounts, model_id` remain byte/semantic-equal before and after UI-only change; snapshot-image differences alone are insufficient for these invariants.
- Screenshots/trace artifacts linked to PRs; actual Pages commit SHA to deployed assets and Safari device verification remain separate evidence.
- Lighthouse performance/accessibility regression with thresholds chosen from current measured baseline. Do not claim improvements without comparable measurements.

## Release ladder
prepared → PR CI passed → merged → Pages deployed exact SHA → desktop/WebKit runtime confirmed → physical iPhone Safari confirmed. Prediction calibration and prospective accuracy belong to 02, never inferred from UI tests.

No model weight, generated forecast, snapshot, Formal Fresh guard, outcome/payout collector or actual wagering changed by this research note.


## Deep-dive 2026-10-14: UI acceptance threats the existing happy path misses

### 03-A iOS Safari is not Playwright WebKit
Playwright docs https://playwright.dev/docs/browsers state its WebKit has patches and is not branded Safari; Mac-hosted WebKit gives closer behavior for certain features than Linux. Emulation https://playwright.dev/docs/emulation covers viewport/touch/locale/timezone, not actual mobile browser UI, iOS keyboard, memory/lifecycle or back/forward-cache semantics. Required ladder: synthetic DOM invariants → WebKit & Chromium CI → Pages exact-build smoke → actual iPhone Safari device QA. Never mark Safari PASS from Linux WebKit alone.

### 03-B bfcache can resurrect stale but visually plausible predictions
MDN https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control explains `no-cache` means revalidate, not “do not store”, and that history navigation/back-forward-cache may restore a past snapshot without validation. Inspect existing `pageshow` listener(s) in `assets/boat_edge_v108.js` before changing. Test back/forward to a previously selected race after time advanced, network reconnection, pending-to-result transition, and a cutoff-crossing refresh. On resume, independently verify race key, freeze ID, displayed data timestamp and status, fail closed instead of displaying a previous race's tickets as current. GitHub Pages header customization can be constrained; verify what hosting actually supports before prescribing Cache-Control rules.

### 03-C Visual screenshots alone cannot certify the result labels
Open PR #202 https://github.com/ikst2512-eng/boat-edge/pull/202 now targets home/results-list 🎯 indicators for missing immutable freeze, inconsistent mode stakes and untrusted official links; prior #200 (blocked/no-data status) may already have been superseded. **Do not reimplement** their validators; 01 coordinates merge. Build regression cases for list/detail parity across all four modes, same `race_key/model_id/precommit_sha/freeze_sha`, ¥10,000 exact stake sums, and only true site-only verified results. A source result alone is never a verified hit without a qualifying immutable, predeadline ticket.
- `NO_PREDICTION`, `BLOCKED`, `WAITING_RESULT`, `VERIFIED_HIT`, `VERIFIED_MISS`, `NOT_ELIGIBLE`: distinct readable Japanese status strings and styling.
- Stale/out-of-order network responses, invalid six-course permutation, scratches, 80–119/120 odds coverage, duplicate tickets, null official payout, zero/negative odds and source timestamp mismatch are **fail-closed** test fixtures. Do not derive missing values or synthesize historical stakes.
- WCAG status semantics: https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html use meaningful `role=status` or polite live-region for status transitions, without incessant screenreader announcements while typing. WCAG 2.2 SC2.5.8 https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html specifies **24×24 CSS px minimum** with exceptions; design targets at least ~44px in common touch flows as a usability objective, not a falsely quoted WCAG requirement.
- Explicitly distinguish per-mode ¥10,000 illustrative allocation from separate daily ¥50,000 paper-only research cap; no purchase action.

### 03-D Release and performance test strategy
Run deterministic Playwright screenshots (freeze clock/JST, font/render profile, network fixtures; preserve factual text) https://playwright.dev/docs/test-snapshots . Snapshot masking of changing datetimes must NOT conceal missing verification timestamps, ticket order or bad totals; assert those in DOM/data equality tests. Lighthouse CI can detect regressions after measured baseline; source https://github.com/GoogleChrome/lighthouse-ci . Record both site build SHA and current source/data SHA; data can be newer than code without proving UI deploy.
