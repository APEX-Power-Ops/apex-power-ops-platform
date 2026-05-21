# APEX PM Lane 421 Schema Architecture Correction - Public To Seam FK Retarget No-Live Packet

Date: 2026-05-21

Status: Executed and accepted closed

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_421_SCHEMA_ARCHITECTURE_CORRECTION_PUBLIC_TO_SEAM_FK_RETARGET_NO_LIVE`

## Purpose

This packet corrects the architectural assumption surfaced by the historical PM Lane 421 blocked preflight.

The lane family inherited a Dataverse-era belief that the operational financial scope anchor should remain `public.scopes.id`. Live production discovery proved that belief false for current work: `public.*` is frozen at LASNAP sample data and no governed onboarding flow creates Temp Power rows there.

This packet therefore adds `seam.scopes` as the operational scope anchor and retargets the seam-side financial `scope_id` foreign keys from `public.scopes` to `seam.scopes`.

This packet does not continue the earlier blocked preflight and does not supersede it as historical record. The blocked packet remains accurate for the old architecture. This packet corrects the architecture so a later onboarding lane can populate truthful seam-side scope anchors for new projects.

## Selected Outcome

Selected outcome:

`LANE_421_SCHEMA_ARCHITECTURE_CORRECTION_APPLIED_PUBLIC_TO_SEAM_FK_RETARGET_NO_LIVE`

Meaning:

1. `seam.scopes` now exists in production as the operational scope tier with `TEXT` ids.
2. `seam.scope_labor_details.scope_id` now targets `seam.scopes.id` and uses `TEXT`.
3. `seam.apparatus_revenue_events.scope_id` now targets `seam.scopes.id` and uses `TEXT`.
4. The financial tables remain empty after the retarget, so no undocumented business writes were uncovered.
5. The historical Lane 421 blocked packet remains preserved, but the future rollback-only atomic probe now has the correct schema target once a later onboarding lane creates real `seam.scopes` rows for Temp Power.

## Phase 0 Discovery

### 1. Lane 421 blocked state confirmed

Discovery result:

1. The historical Lane 421 blocked packet exists and truthfully records the missing Temp Power scope-anchor blocker.
2. Migration `014_pm_lane_411_revision_c_role_contract_grants.sql` had already been applied live and verified earlier the same day.
3. `LANE_412_DRY_RUN_ENABLED` remained absent in the same-day authenticated Render inspection recorded by the historical Lane 421 packet and handoff.

Conclusion:

The architectural correction starts from a truthful blocked-preflight baseline rather than reopening a solved grant problem.

### 2. `seam.scopes` non-existence in production before implementation

Discovery result:

1. Live `information_schema.tables` inspection returned `seam_scopes_exists = false` before migration 015 was applied.
2. `seam.projects` already existed in production, so a `seam.scopes.project_id -> seam.projects(id)` foreign key remained viable.

Conclusion:

`seam.scopes` was absent and needed to be created; no conflicting pre-existing table had to be reconciled.

### 3. Current FK targets before retarget

Discovery result:

1. The seam-side financial scope FKs before migration 015 were:
   - `seam.scope_labor_details.scope_id -> public.scopes.id` via `scope_labor_details_scope_id_fkey`
   - `seam.apparatus_revenue_events.scope_id -> public.scopes.id` via `apparatus_revenue_events_scope_id_fkey`
2. Additional `public.*` legacy tables also reference `public.scopes.id` and were surfaced during Phase 0:
   - `public.ahas.scope_id`
   - `public.apparatus.scope_id`
   - `public.apparatus_revenue.scope_id`
   - `public.resource_assignments.scope_id`
   - `public.scope_financial_summaries.scope_id`
   - `public.scope_labor_details.scope_id`
   - `public.tasks.scope_id`

Conclusion:

The only seam-side retargets required in this packet were `seam.scope_labor_details` and `seam.apparatus_revenue_events`. The legacy `public.*` references remain untouched and out of scope.

### 4. Existing seam-side key shapes and scope columns before retarget

Discovery result:

1. `seam.projects.id` is `TEXT NOT NULL`.
2. `seam.apparatus.id` is `TEXT NOT NULL`.
3. `seam.scope_labor_details.scope_id` was `UUID NOT NULL` before migration 015.
4. `seam.apparatus_revenue_events.scope_id` was `UUID NOT NULL` before migration 015.

Conclusion:

The new `seam.scopes.id` needed to use the existing operational-tier `TEXT` key shape, not the legacy `UUID` shape from `public.scopes`.

### 5. Existing data in financial tables before retarget

Discovery result:

1. `seam.project_contract_snapshots` row count was `0`.
2. `seam.scope_labor_details` row count was `0`.
3. `seam.apparatus_financials` row count was `0`.
4. `seam.apparatus_revenue_events` row count was `0`.

Conclusion:

The retarget and type change were safe to perform without backfill or cleanup work.

### 6. LASNAP scope-row references inside `seam.*`

Discovery result:

1. `seam.scope_labor_details` had `0` rows with any `scope_id` value.
2. `seam.apparatus_revenue_events` had `0` rows with any `scope_id` value.

Conclusion:

No seam-side legacy LASNAP scope references had to be preserved or remapped during this packet.

### 7. Lane 412 design-body location

Discovery result:

1. The current Lane 412 design body exists at `docs/operations/APEX-PM-LANE-412-REVISION-B-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md`.
2. The historical base design and Revision A files also remain present.
3. The latest revision body was selected for the in-place Correction Note so the preserved design lineage remains readable in one place.

Conclusion:

The Correction Note was appended to the current Revision B design body without rewriting earlier historical packet text.

## Implementation Executed

### 1. Migration 015

Implemented surface:

1. `apps/mutation-seam/migrations/015_seam_scopes_addition_and_fk_retarget.sql`

What the migration does:

1. Creates `seam.scopes` with `TEXT` primary key and `project_id -> seam.projects(id)`.
2. Applies insert-only triggers to `seam.scopes` using the existing seam insert-only guard function.
3. Enables RLS on `seam.scopes`.
4. Revokes `anon` and `authenticated` from `seam.scopes`.
5. Grants `SELECT` and `INSERT` on `seam.scopes` to `pm` and `operations` and revokes any access from field-facing roles when present.
6. Retargets `seam.scope_labor_details.scope_id` from `public.scopes.id` to `seam.scopes.id` and changes the column type from `UUID` to `TEXT`.
7. Retargets `seam.apparatus_revenue_events.scope_id` from `public.scopes.id` to `seam.scopes.id` and changes the column type from `UUID` to `TEXT`.

Production application result:

1. Migration 015 was applied live through the governed administrative Postgres session available in this workspace.
2. The live application returned `MIGRATION_015_STATUS applied`.

### 2. Verification surface

Implemented surface:

1. `apps/mutation-seam/scripts/lane_421_schema_correction/run_lane_421_schema_correction_verification.py`
2. `apps/mutation-seam/scripts/lane_421_schema_correction/README.md`
3. `apps/mutation-seam/scripts/lane_421_schema_correction/output/schema_correction_verification_20260521T023011Z.json`

Verification result:

1. `seam.scopes` exists and row count is `0`.
2. `seam.scope_labor_details.scope_id` now targets `seam.scopes.id` via `scope_labor_details_scope_id_fkey`.
3. `seam.apparatus_revenue_events.scope_id` now targets `seam.scopes.id` via `apparatus_revenue_events_scope_id_fkey`.
4. Both seam-side `scope_id` columns now resolve as `TEXT`.
5. `pm` and `operations` each retain `USAGE` on schema `seam` plus `SELECT` and `INSERT` on `seam.scopes`.

Verification nuance:

1. Both `pm` and `operations` are `NOLOGIN` roles.
2. The governed admin DSN in this workspace cannot `SET ROLE` or `SET SESSION AUTHORIZATION` to those roles, so the verifier truthfully falls back to `pg_roles`, `has_schema_privilege`, and `has_table_privilege` metadata for the role-access check.
3. The final artifact therefore records `probe_mode = privilege_metadata_only` for both roles while still returning `overall_status = passed`.

### 3. Lane 421 probe helper correction

Updated surface:

1. `apps/mutation-seam/scripts/lane_421_grant_verification/run_lane_421_atomic_transaction_probe.py`
2. `apps/mutation-seam/scripts/lane_421_grant_verification/README.md`

Update made:

1. The rollback-only atomic probe now expects `seam.scopes.id` instead of `public.scopes.id`.
2. The probe now validates the seam-side scope anchor against `seam.scopes` and inserts `TEXT` scope ids into the seam financial tables.

## Boundaries Preserved

This packet does not admit:

1. any business-row insert into the seam financial tables
2. any route-handler or persistence-module change
3. any change to existing migrations `013` or `014`
4. any write to `public.*`
5. any project onboarding or backfill of `seam.scopes`
6. any Lane 422 admission phrase
7. any billing, payroll, invoice, accounting, or external-finance output
8. any autonomous AI business-state mutation

## Next Truth

The next truthful move is still not a first-write packet.

The next truthful move is a separate onboarding lane that creates real `seam.projects`, `seam.scopes`, and `seam.apparatus` rows for Miner Temp Power from the governed estimator-export path.

After that onboarding work lands, the corrected Lane 421 rollback-only atomic probe can run against a truthful `seam.scopes.id` anchor. Only after that probe passes should any later first-write admission phrase be considered.