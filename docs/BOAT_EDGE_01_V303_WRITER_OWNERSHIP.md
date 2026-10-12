# BOAT EDGE 01 — V303 writer ownership audit

As of main 12f6e2e47c6a0d5c2cc88eae2affcd1891331c1c, V303 retires **automatic triggers only** for five superseded workflows. All job implementations remain available via explicit manual dispatch. No race predictions, weights, freeze snapshots, results, odds or Formal Fresh status were edited.

| Superseded scheduled writer | Previously wrote | Retained automated successor / scope |
|---|---|---|
| BOAT_EDGE_site-v98.yml | old official course stats and V98 UI | site-v117.yml remains scheduled for official recent course stats |
| BOAT_EDGE_site-v99.yml | old official course stats and V99 UI | site-v117.yml remains scheduled |
| site-v114.yml | old PRE_RESULT final history and old JS/UI | site-v120.yml was successor, now site-v123.yml remains scheduled |
| site-v120.yml | legacy FINAL15M history | site-v123.yml remains scheduled; V235 frozen-source pipeline is separate |
| site-v124.yml | legacy snapshot audit | site-v125.yml remains scheduled |

Protected (not changed in V303): site-v109.yml results, site-v117.yml course stats, site-v123.yml matched history, site-v125.yml revision-safe audit, auto-update.yml collector, V235.yml immutable prediction, data/formal_status.json.

Evidence gate: Development CI must run V299 workflow inventory and prohibit reactivation of all 13 retired workflows. This is a trigger deduplication, **not** proof all remaining writers are redundant. Scheduler work beyond these five must be scoped by data ownership and consumer traces.
