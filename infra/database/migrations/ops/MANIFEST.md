# ops migrations — manifest

Operations (PM) lane. SSoT: [`reference/ops/00-MASTER-INDEX.md`](../../../../reference/ops/00-MASTER-INDEX.md).
Dev DB: `ops_dev` (local PG). **Nothing here is applied to prod** (convergence = Chip N, behind the MASTER §7 invariants).

| # | Up | Down | What | Chip | Status |
|---|---|---|---|---|---|
| 001 | `001_identity_skeleton.sql` | `001_identity_skeleton_down.sql` | `ops` schema + 7 enums + projects / scopes / tasks / apparatus; FIXED scope→apparatus binding (NOT NULL + immutability trigger); soft `core` seam; provenance / offline-sync reserves | 1 | validated on `ops_dev` |

## Conventions
- Each migration ships with a reversible `_down`. Validation gate = up → down → up clean + the invariant tests in `test_001_identity_skeleton.py` (run with `uv run --with "psycopg[binary]" --with pytest pytest <file>`, local PG password in `PGPASSWORD`).
- Enums seeded verbatim from the live `public.*` enums (the workbook-verified PM model).
- Laws enforced (SSoT §4): 1 FIXED binding · 2 `auth.users` identity (soft uuid on `ops_dev`) · 3 recognition firewall (no recognized-$ columns) · 5 soft `core` seam.

## Deferred (later chips)
Quote-facts + std-hours catalog + intake envelope (Chip 2) · apparatus quoted_hours/quoted_revenue + 4-category recognition ledger + blended rate + progress billing (Chip 3/4) · Estimator extractor + 5-phase flow (Chip 5) · `public`/`seam`/`schedule`→`ops` convergence (Chip N).
