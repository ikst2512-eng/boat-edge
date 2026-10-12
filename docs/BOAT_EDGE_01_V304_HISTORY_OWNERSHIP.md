# BOAT EDGE 01 V304 — History/legacy UI owner

Main parent: `c3c75e3ec2cb8c8eb5f86aee6817691a9ee22519`.

Automatic push and five-minute cron removed from five outdated workflows: `site-v123.yml`, `site-v129.yml`, `site-v130.yml`, `site-v131.yml`, and `site-v132.yml`. All jobs preserved for explicit emergency manual dispatch. No original snapshots, predictors, race result collectors, payout tables, odds or Formal Fresh guards changed.

**Retained owners:** `site-v133.yml` remains scheduled as the current FINAL15M policy/history generator, and `site-v134.yml` remains scheduled/event-driven for current TODO reconciliation. `site-v125.yml` retains its independent cron for revision-safe legacy audits, even though its retired V123 workflow_run hint may no longer occur. `V235.yml` continues frozen prediction and pre-result evidence.

**Evidence:** V129 labels V123 obsolete; V130 labels V129 obsolete; V131 labels V130 obsolete; V132 labels V130/V131 obsolete; V133 labels V130/V131/V132 obsolete. The previous schedules could all write `index.html`, `assets/boat_edge_v108.js`, and/or `data/site_prediction_history`. This preserves the latest retained owner while reducing stale-writer and Pages cancellation exposure.

**Limit:** The audit does not prove model accuracy or that remaining scheduled jobs are nonoverlapping. Do not promote a formal Fresh claim or modify immutable prediction bytes.
