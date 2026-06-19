# ops migrations — manifest

Operations (PM) lane. SSoT: [`reference/ops/00-MASTER-INDEX.md`](../../../../reference/ops/00-MASTER-INDEX.md).
Dev DB: `ops_dev` (local PG). **Nothing here is applied to prod** (convergence = Chip N, behind the MASTER §7 invariants).

| # | Up | Down | What | Chip | Status |
|---|---|---|---|---|---|
| 001 | `001_identity_skeleton.sql` | `001_identity_skeleton_down.sql` | `ops` schema + 7 enums + projects / scopes / tasks / apparatus; FIXED scope→apparatus binding (NOT NULL + immutability trigger); soft `core` seam; provenance / offline-sync reserves | 1 | validated on `ops_dev` |
| 002 | `002_quote_model.sql` | `002_quote_model_down.sql` | std-hours catalog + scope_quote_line (qty × hrs_per_unit) + scope_quote (4 D-OPS-9 categories + M4/N4 + generated P3/P4/blended_rate) + apparatus quoted_hours/quoted_revenue/quote_line_id + `v_apparatus_quote` | 2 | validated on `ops_dev` |
| 003 | `003_intake_unique_keys.sql` | `003_intake_unique_keys_down.sql` | partial-unique indexes (scopes / scope_quote_line / apparatus) enabling idempotent estimator-intake upserts | 5 | validated on `ops_dev` |

## Intake (Chip 5)
The Estimator `.xlsm` → `ops.*` loader lives at [`packages/ops-intake/`](../../../../packages/ops-intake): openpyxl extractor + reconciliation validator + idempotent loader + `ops-intake` CLI. **Project Miner** (product name *Project Jupiter*; source `Cupertino - Miner Estimator PHX Bldg A & B MV Rev10.xlsm`) is loaded into `ops_dev` — 1 project ($4,692,078.98) / 9 scopes (7 MV + 2 chiller estimates) / 118 lines / **5,344 QTY-expanded apparatus** / 153 std-hours; reconciles to the contract total. Run: `ops-intake load <xlsm> --dsn "<ops_dev dsn>" --approve`. The real workbook lives gitignored under `packages/ops-intake/_data/`; `MINER_WORKBOOK` gates the integration + e2e tests.

## Conventions
- Each migration ships with a reversible `_down`. Validation gate = up → down → up clean + the invariant tests `test_00N_*.py` (run with `uv run --with "psycopg[binary]" --with pytest pytest <file>`; pin `OPS_DEV_PGPASSWORD` / `OPS_DEV_DSN` — ambient PG env points at prod).
- Enums seeded verbatim from the live `public.*` enums (the workbook-verified PM model).
- Laws enforced (SSoT §4): 1 FIXED binding · 2 `auth.users` identity (soft uuid on `ops_dev`) · 3 recognition firewall (no recognized-$ columns) · 5 soft `core` seam.

## Deferred (later chips)
4-category recognition **ledger** + progress billing (Chip 3 / 4) · review-edit UI + production tracking · `public`/`seam`/`schedule` → `ops` convergence (Chip N) · prod application of `ops.*`.
