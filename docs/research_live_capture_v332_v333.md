# BOAT EDGE prospective research capture (V332 + V333)

This is a **SITE research-only** workflow, separate from the untouched Formal Fresh target. It is the first live path that can go from a pre-result site race JSON to a frozen 120-way *research* candidate using raw third-party evidence without requiring those raw captures to be committed to Git first.

## Run only before the actual deadline

From the repository root, with a current PRE_RESULT `data/races/YYYYMMDD-VV-RR.json`:

```bash
python3 scripts/boat_edge_v332_live_local_freeze.py \
  --root . --race-key YYYYMMDD-VV-RR --capture
```

Replace `YYYYMMDD-VV-RR` with the **real current race ID**. The command refuses late, backfilled, missing-beforeinfo, cancelled or result-bearing inputs instead of filling gaps. The `--capture` flag explicitly opts in to a bounded HTTPS fetch of one HTML page from each of the three public providers. V333 constructs race-specific official, BOATERS original exhibition, and ボートレース日和 race-page URL candidates; page routes may change or fail, and successful HTTP fetch alone does **not** prove page identity or parsed original exhibition values.

When source pages already exist as immutable V315 capture receipts and local HTML:

```bash
python3 scripts/boat_edge_v332_live_local_freeze.py \
  --root . --race-key YYYYMMDD-VV-RR
```

Optionally override URLs with `--official-url`, `--boaters-url`, `--kyoteibiyori-url`. A mismatched existing receipt is rejected. No hidden crawling, account login, bypass, or results/payout/odds endpoint is used.

## Output and precise status

- Captures: `data/source_captures/YYYYMMDD/YYYYMMDD-VV-RR/{official,boaters,kyoteibiyori}.html` and immutable `.receipt.json`.
- Freeze: `data/research_local_v332/YYYYMMDD/YYYYMMDD-VV-RR.json` written **once**, before deadline, with the complete V312 provisional course research candidate, boat-number Top10 for all three ablation modes, exact race input SHA, each captured HTML SHA, frozen-at timestamp and candidate digest.
- Evidence level is `LOCAL_RECEIPT_RAW_SHA_ONLY`: local bytes and receipts agree, but original website authenticity, capture timestamp by an independent server, displayed race identity, and all four original exhibition measurements are **not independently verified**.
- Exhibition entry is **provisional**, never substituted for independently verified actual course. Probabilities are **uncalibrated**, and no model improvement, scoring, production use or purchase is authorized.
- The 2026-10-01 Formal Fresh cohort is explicitly excluded and never read.
- If any fetch fails, previously completed captures remain immutable for the next *predeadline* attempt; there is never a retrospective freeze.

A later independently authenticated source-data review and a strictly prospective result-separated validation cohort are needed before an accuracy-improvement claim. CI uses synthetic racer data and mocked HTTP; it does not prove success against live third-party providers.
