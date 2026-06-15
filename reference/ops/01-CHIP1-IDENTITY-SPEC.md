# Chip 1 — `ops` Identity Skeleton — Spec

- **Status:** APPROVED (operator, 2026-06-15) — build in progress
- **Lane:** Operations (PM) · SSoT: [`00-MASTER-INDEX.md`](00-MASTER-INDEX.md) · Dev DB: `ops_dev` (local PG)
- **Scope:** the **four identity entities only** — `ops.projects` · `ops.scopes` · `ops.apparatus` · `ops.tasks`. Revenue ledger, quote-facts, intake, and convergence are later chips.

## 1. Approach

Greenfield `ops.*` on a fresh `ops_dev`, modeled on the live `public.*` PM core (proven faithful by the Project Miner workbooks — SSoT §5a) with seam's disciplines layered in. Each entity = **`public.<table>` + deltas** (§2). No `public`/`seam` data is touched (convergence = Chip N).

## 2. Entities (deltas vs `public.*`)

### `ops.projects` (= `public.projects`, refined)
- **KEEP:** `id` · `project_number` (UNIQUE NOT NULL) · `project_name` · `status` · `project_type` · `business_unit` · `quote_date`/`quote_revision` · `start_date`/`end_date` · `contract_value` · `po_number` · `project_lead` · `estimator` · `description` · `notes` · rollups (`total_apparatus_count`/`completed_apparatus_count`/`percent_complete`, scope due/start/complete dates) · `is_active` · `created_at`/`updated_at`.
- **SOFT REFS** (uuid null, D-010 seam, documented targets): `client_ref` · `site_ref` · `location_ref`.
- **ADD** (discipline): `tenant_id` (null, reserved) · provenance trio (`source`/`provenance_status`/`legacy_source_id`) · `created_by`/`updated_by` → `auth.users`.

### `ops.scopes` (= `public.scopes`, refined)
- **FK:** `project_id` NOT NULL → `ops.projects`.
- **KEEP:** `id` · `scope_number` · `scope_name` (NOT NULL) · `scope_type` · `status` · `percent_complete` · planned/actual dates + `date_due` · `total_apparatus_count`/`completed_apparatus_count` · `sort_order` · `notes` · `is_active` · timestamps.
- **SOFT REFS:** `client_ref` · `site_ref`.
- **DEFER to Chip 2/3:** `quoted_hours`/`actual_hours` · `quoted_revenue`/`actual_revenue` · `labor_cost` · the 4-category breakdown · blended rate.
- **ADD:** `tenant_id` · provenance · auth refs.

### `ops.apparatus` (= `public.apparatus`, refined — **the recognition unit**)
- **FIXED BINDING (Law 1):** `scope_id` uuid **NOT NULL** FK → `ops.scopes`. Cross-scope *reassignment* guarded by a `BEFORE UPDATE` trigger that raises on `scope_id` change (lean; confirm vs documented-invariant at build).
- **KEEP:** `task_id` (null FK → `ops.tasks`) · `apparatus_designation` (NOT NULL) · `apparatus_name` · `apparatus_type` · `manufacturer`/`model`/`serial_number` · `status` · `assessment` · `availability` · `percent_complete` · `anticipated_start`/`actual_start`/`actual_end`/`date_due` · `building`/`floor`/`room` · `drawing_reference` · `datasheet_complete` · `sort_order`/`priority` · `notes`/`tech_notes` · `is_active` · timestamps.
- **DROP (Law 3 firewall):** `actual_revenue` — recognized revenue is the Chip 3 event ledger, never a mutable column.
- **DEFER to Chip 2:** `quoted_hours` · `actual_hours` · `quoted_revenue` (land with the quote/std-hours catalog).
- **RATIONALIZE:** drop the duplicate `designation` (keep `apparatus_designation`); collapse `equipment_type` into `apparatus_type` (keep one — confirm at build).
- **ADD:** `equipment_model_ref` (uuid null → `core.equipment_models`, Law 5 soft seam) · `tenant_id` · provenance trio · offline-sync reserves (`origin_device`/`client_rev`/`client_captured_at`/`synced_at` — MASTER §6; PowerSync wiring deferred) · auth refs (`created_by`/`updated_by`/`submitted_by`/`approved_by` → `auth.users`).

### `ops.tasks` (= `public.tasks` — the work-grouping layer)
- **FK:** `scope_id` NOT NULL → `ops.scopes`; `parent_task_id` (null self-FK).
- **KEEP:** `task_number` · `task_name` (NOT NULL) · `task_type` · `status` · `percent_complete` · `estimated_hours`/`actual_hours` · planned/actual dates + `date_due` · `apparatus_count` · `sort_order` · `description`/`notes` · `is_active` · timestamps.
- **ADD:** `tenant_id` · provenance · auth refs.

> **Note on grain:** `ops.tasks` is the *optional* work-grouping above apparatus (apparatus → `task_id`), per `public`. It is **not** the NETA-test-line; revenue recognition is at the **apparatus** grain (operator ruling, D-OPS-8). The per-test detail, if needed, arrives with the Chip 3 recognition model.

## 3. Enums (`ops.*`)

`project_status` · `scope_status` · `scope_type` · `apparatus_status` · `apparatus_assessment` · `apparatus_availability` · `task_status` — values seeded **faithfully from the live `public.*` enums** (exact labels pulled from prod at build).

## 4. Laws applied (from SSoT §4)

1 FIXED scope→apparatus (NOT NULL FK + reassignment guard) · 2 `auth.users` identity · 3 recognition firewall (no recognized-$ columns) · 5 soft `core` seam (`equipment_model_ref` null) · §6 provenance + `tenant_id` + offline-sync reserves. (Law 4 field-trust and Law 6 migration-invariants bind at Chip 3 / Chip N.)

## 5. Implementation plan (TDD)

- **Dev DB:** fresh `ops_dev` on local PG (`PGSSLMODE=disable`). Never reuse `apex_pm_stage`/`records_dev` (one-DB-per-workstream).
- **Files:** `infra/database/migrations/ops/001_identity_skeleton.sql` + `001_identity_skeleton_down.sql` + `MANIFEST.md`.
- **TDD test list** (write failing first, run against `ops_dev`):
  1. After up: schema `ops` + the 4 tables + 7 enums exist.
  2. **FIXED binding:** INSERT apparatus with NULL `scope_id` → fails; UPDATE apparatus `scope_id` → blocked by the guard.
  3. **FKs enforced:** apparatus.scope_id→scopes · tasks.scope_id→scopes · scopes.project_id→projects · apparatus.task_id→tasks · tasks.parent_task_id self-FK.
  4. apparatus has **no** `actual_revenue` column; **has** nullable `equipment_model_ref`.
  5. soft refs + `tenant_id` + `equipment_model_ref` nullable; provenance columns present.
  6. **reversibility:** up → down → up clean (down drops `ops` schema + enums; re-up succeeds).
- **Gates:** all tests green · reversibility clean → chip-sized PR `ops/chip1-identity` → `main` on operator authorization.

## 6. Deferred (explicit)

Quote-facts + std-hours catalog + intake envelope (Chip 2) · apparatus `quoted_hours`/`quoted_revenue` + 4-category recognition ledger + blended rate + progress billing (Chip 3/4) · Estimator extractor + 5-phase flow (Chip 5) · `public`/`seam`/`schedule`→`ops` convergence (Chip N) · `ops.clients`/`sites`/org (when a chip needs them; soft refs until then).
