# ops migrations — manifest

Operations (PM) lane. SSoT: [`reference/ops/00-MASTER-INDEX.md`](../../../../reference/ops/00-MASTER-INDEX.md).
Dev DB: `ops_dev` (local PG). **Nothing here is applied to prod** (convergence = Chip N, behind the MASTER §7 invariants).

| # | Up | Down | What | Chip | Status |
|---|---|---|---|---|---|
| 001 | `001_identity_skeleton.sql` | `001_identity_skeleton_down.sql` | `ops` schema + 7 enums + projects / scopes / tasks / apparatus; FIXED scope→apparatus binding (NOT NULL + immutability trigger); soft `core` seam; provenance / offline-sync reserves | 1 | validated on `ops_dev` |
| 002 | `002_quote_model.sql` | `002_quote_model_down.sql` | std-hours catalog + scope_quote_line (qty × hrs_per_unit) + scope_quote (4 D-OPS-9 categories + M4/N4 + generated P3/P4/blended_rate) + apparatus quoted_hours/quoted_revenue/quote_line_id + `v_apparatus_quote` | 2 | validated on `ops_dev` |
| 003 | `003_intake_unique_keys.sql` | `003_intake_unique_keys_down.sql` | partial-unique indexes (scopes / scope_quote_line / apparatus) enabling idempotent estimator-intake upserts | 5 | validated on `ops_dev` |
| 004 | `004_person_anchor.sql` | `004_person_anchor_down.sql` | `ops.persons` LOCAL person anchor (identity contract C1/D2/D4): canonical spine = prod `public.employees.id` via `employee_ref` (cross-DB contract-FK, not a DB FK; partial-unique). STANDALONE — does NOT retrofit FKs onto the `ops.*` audit cols (`created_by`/`updated_by`/`approved_by` stay provenance-only per D6); down drops the TABLE only, never the `ops` schema. | identity slice | validated on `ops_test` (6/6), applied to `ops_dev` |
| 005 | `005_recognition_ledger.sql` | `005_recognition_ledger_down.sql` | append-only `revenue_recognition_event` ledger (signed recognized/reversal rows) + gated `approve_and_recognize`/`reverse_recognition` + insert-integrity & append-only triggers + lifecycle-protection guards (apparatus/scope/project) + frozen-basis immutability guard + 4 recognition views | 3 | validated on `ops_test` |
| 006 | `006_progress_billing.sql` | `006_progress_billing_down.sql` | `billing_application_status` enum + `billing_application` (snapshot header) + `billing_application_line` (event-grain) + `billing_application_draft` tables; `retainage_pct` column on projects; function-only mutation gate + immutability + insert-integrity triggers; deferred header=sum-lines constraint trigger; 5 functions (`record`, 6-param `issue`, 3-param `issue`, `discard`, `void`); 4 views (`v_unbilled_recognition`, `v_draft_preview`, `v_billing_application_sov`, `v_project_billing`); sub-cent parity guard in positive-branch sweep; reversibility verified (Chip 1-3 survive DOWN) | 4 | validated on `ops_test` (63+ tests) |
| 007 | `007_intake_envelope.sql` | `007_intake_envelope_down.sql` | 3 enums (`intake_run_status` / `intake_conflict_kind` / `intake_source_format`) + 3 envelope tables: `intake_runs` (lifecycle header), `intake_source_files` (sha256 + 25 MB cap + raw_bytes integrity), `intake_validation_findings` (PM-safe `message` / finance-only `diagnostic_detail` split); BEFORE INSERT OR UPDATE immutability/approval-shape trigger; one-active-run partial unique (`uq_intake_one_active`); apparatus-task-same-scope guard; `tasks.scope_id`-immutable guard; `uq_ops_tasks_intake`; 6 `source_*` columns on `projects`. `ops.*` domain tables are written ONLY by `approve_run` (the package). Reversible — Chips 1-6 survive DOWN. | Chip 5 | validated on `ops_test` (10/10 migration tests; full package suite 38 + API 14 + UI smoke green) |
| 008 | `008_core_equipment_models.sql` | `008_core_equipment_models_down.sql` | `core` schema + `core.equipment_models` (canonical equipment identity, 120-row active estimator-core seed sha256 dfe59bc3) + cycle-safe merge-chasing resolver view (id|model_key entry) + **hard FK** on `ops.apparatus.equipment_model_ref` (mig-001 soft seam → co-located). Reversible — Chips 1–7 survive DOWN. | Step 4a | validated on `ops_test` |

## Intake (Chip 5)
The Estimator `.xlsm` → `ops.*` loader lives at [`packages/ops-intake/`](../../../../packages/ops-intake): openpyxl extractor + reconciliation validator + idempotent loader + `ops-intake` CLI. **Project Miner** (product name *Project Jupiter*; source `Cupertino - Miner Estimator PHX Bldg A & B MV Rev10.xlsm`) is loaded into `ops_dev` — 1 project ($4,692,078.98) / 9 scopes (7 MV + 2 chiller estimates) / 118 lines / **5,344 QTY-expanded apparatus** / 153 std-hours; reconciles to the contract total. Run: `ops-intake load <xlsm> --dsn "<ops_dev dsn>" --approve`. The real workbook lives gitignored under `packages/ops-intake/_data/`; `MINER_WORKBOOK` gates the integration + e2e tests.

## Conventions
- Each migration ships with a reversible `_down`. Validation gate = up → down → up clean + the invariant tests `test_00N_*.py` (run with `uv run --with "psycopg[binary]" --with pytest pytest <file>`; pin `OPS_DEV_PGPASSWORD` / `OPS_DEV_DSN` — ambient PG env points at prod).
- Enums seeded verbatim from the live `public.*` enums (the workbook-verified PM model).
- Laws enforced (SSoT §4): 1 FIXED binding · 2 `auth.users` identity (soft uuid on `ops_dev`) · 3 recognition firewall (no recognized-$ columns) · 5 soft `core` seam.

## Deferred (later chips)
Production tracking (Chip 6+) · `public`/`seam`/`schedule` → `ops` convergence (Chip N) · prod application of `ops.*`.

> **Chip 5 BUILT** (2026-06-21): intake envelope (mig 007) + `ops-intake` parse/approve package + host-gated control-plane API + `operations-web` pm-review page. Dev-only on `ops_test`; operator-gated merge.
