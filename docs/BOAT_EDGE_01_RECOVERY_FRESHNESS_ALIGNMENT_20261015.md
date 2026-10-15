# Recovery monitor freshness alignment

## Defect and scope

`source_status()` in V220 treated an official race card as current until 20 minutes old. The unchanged V229 first-save validator independently requires at most 960 seconds (16 minutes). A 17–20 minute card with otherwise ready evidence could therefore trigger V229 recovery instead of the collector; V229 would correctly refuse that source. The monitor also rounded ages to tenths of minutes before comparing, allowing 961 seconds to appear as 16.0 minutes or 901 seconds as 15.0 minutes.

Align only the monitor to the existing authoritative limits: race card 960 seconds; beforeinfo, scratch and odds 900 seconds. Compare unrounded ages. This routes stale-card diagnostics to the existing collector recovery candidate and suppresses a source-incomplete V229 recovery. The unchanged workflow cooldown and every independent V229 gate still apply. No model, first-save implementation, deadline window, immutable snapshot, formal flag, schedule or outcome file is changed.

## Verification

- Synthetic fixtures cover 960s accepted, 961s / 17m / 20m stale, and each 900s accepted versus 901s stale; negative/future ages rejected. Stale cards request collection instead of V229. No snapshot is created.
- Existing V220 direct test runner PASS, including the new regression.
- V23 fixtures: 395 PASS; collector/prune/rebase/V277: 13 PASS; V271 health: 7 PASS; source pins: 5 workflows PASS.

## Live observations before this change

- At 14:19 JST, official collector workflow was enabled (`active`) but its last observed run started 13:59:18 JST, before PR #402; there was not yet a post-fix normal collector invocation to establish live expiry-pruning improvement.
- Existing guarded V220 recovery run 38686073676 requested V229. V229 run 38686123015 executed at 14:19:25 JST and reported one new atomic snapshot: `20261015-10-12` (deadline 14:27 JST). This confirms an existing recovery invocation and new snapshot log, not this freshness fix's effect or independent first Git-add / browser acceptance.
- PR #402's source blob remains on latest inspected main `d2dd14dbd0ea1987578bf7bec77d1781445c182c`. Formal First100=0, results_seen/unlock/scoring=false, token=null. No formal results read.
- October 14's 39 absent snapshot paths remain a separate historical audit, not retroactive predictions. No measured accuracy or full-39R resolution is claimed.

Independent PRE_RESULT verification subsequently confirmed that snapshot path history contains exactly one commit: `47c1ea3c47d7c8338ca1ac68ddef2624bf0c4a19`, addition at 14:19:26 JST (deadline 14:27). Exact snapshot SHA256 `ff97b9e4b24313a0f21b8bccafed6f246f51e17d497fa773ecfa9e08f8afe105` matches V229 attestation and audit; the race-source digest also matches the snapshot and attestation. This proves one predeadline Git-save and matching bytes, not browser rendering or any accuracy gain. No result data was used.
