# APEX PM Lane 500 Migration 016 Structural Supplement No-Live Packet

Date: 2026-05-21

Status: Executed and accepted closed

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_500_MIGRATION_016_STRUCTURAL_SUPPLEMENT_NO_LIVE`

## Purpose

This packet applies the minimum structural supplement needed after the blocked Lane 500 onboarding recheck.

It does only two things:

1. adds the missing relational `seam.apparatus.scope_id` anchor
2. extends the operational grant posture on `seam.projects`, `seam.tasks`, and `seam.apparatus`

This packet does not implement onboarding, backfill `scope_id`, normalize JSONB payloads, change routes, or admit any business write.

## Selected Outcome

Selected outcome:

`LANE_500_MIGRATION_016_APPLIED_SCOPE_ID_AND_OPERATIONAL_GRANTS_NO_LIVE`

Meaning:

1. `seam.apparatus.scope_id` now exists as nullable `TEXT`.
2. `seam.apparatus.scope_id` now targets `seam.scopes(id)`.
3. `apparatus_scope_id_idx` now exists.
4. `pm` and `operations` now have `SELECT`, `INSERT`, and `UPDATE` on `seam.projects`, `seam.tasks`, and `seam.apparatus`.
5. `anon` and `authenticated` are now denied those same table privileges.
6. Production seam row counts remained unchanged and every current `seam.apparatus.scope_id` value remains `NULL`.

## Phase 0 Discovery

### 1. Live predecessor state

Discovery result:

1. PM Lane 421 schema correction was already live and verified.
2. `seam.scopes` existed and row count remained `0`.
3. Migration 015 content was already represented in the live Supabase migration ledger.

Conclusion:

Migration 016 started from a stable post-015 floor rather than attempting to repair an unresolved 421 defect.

### 2. Missing apparatus scope anchor

Discovery result before migration 016:

1. `seam.apparatus` had no `scope_id` column.
2. No generated or legacy equivalent column existed.
3. Existing apparatus JSONB carried `0` populated `scope_id` keys.

Conclusion:

The apparatus-to-scope relationship still lacked a governed relational anchor and required a real column rather than a JSONB convention.

### 3. Current row counts and current task shape

Discovery result before migration 016:

1. `seam.projects` row count = `1`
2. `seam.tasks` row count = `15`
3. `seam.apparatus` row count = `184`
4. `seam.scopes` row count = `0`
5. `seam.tasks` currently includes `status` and `workpackage_id` in addition to `id`, `created_at`, `updated_at`, and `data`

Conclusion:

The packet had to preserve unchanged-row-count proof and document the current task schema truth instead of repeating earlier shorthand.

### 4. Current grant posture before migration 016

Discovery result before migration 016:

1. `pm` and `operations` had grant coverage on `seam.scopes` only.
2. `seam.projects`, `seam.tasks`, and `seam.apparatus` did not yet carry the expected operational write posture.

Conclusion:

The missing operational-table grants were a real structural blocker and part of the minimum supplement.

## Implementation Executed

### 1. Migration 016

Implemented surface:

1. `apps/mutation-seam/migrations/016_seam_apparatus_scope_id_and_operational_grants.sql`

What the migration does:

1. Adds nullable `seam.apparatus.scope_id TEXT`.
2. Adds foreign key `apparatus_scope_id_fkey` to `seam.scopes(id)`.
3. Adds index `apparatus_scope_id_idx`.
4. Grants `SELECT`, `INSERT`, and `UPDATE` on `seam.projects`, `seam.tasks`, and `seam.apparatus` to `pm` and `operations`.
5. Revokes all access on those three tables from `anon` and `authenticated`.

Production application result:

1. Migration 016 was applied live through the governed administrative Postgres session in this workspace.
2. The live application returned `MIGRATION_016_STATUS applied`.

### 2. Verification surface

Implemented surface:

1. `apps/mutation-seam/scripts/lane_500_migration_016/run_migration_016_verification.py`
2. `apps/mutation-seam/scripts/lane_500_migration_016/README.md`
3. `apps/mutation-seam/scripts/lane_500_migration_016/output/migration_016_verification_20260521T040158Z.json`

Verification result:

1. `overall_status = passed`
2. `seam.apparatus.scope_id` exists as nullable `TEXT`
3. `apparatus_scope_id_fkey` targets `seam.scopes(id)`
4. `apparatus_scope_id_idx` exists
5. `pm` and `operations` each have `USAGE` on `seam` plus `SELECT`, `INSERT`, and `UPDATE` on `seam.projects`, `seam.tasks`, and `seam.apparatus`
6. `anon` and `authenticated` do not retain those privileges
7. seam totals remain `projects=1`, `tasks=15`, `apparatus=184`, and `scopes=0`
8. all `184` current `seam.apparatus.scope_id` values remain `NULL`

## Boundaries Preserved

This packet does not admit:

1. any business-row insert, update, or delete
2. any `scope_id` backfill
3. any JSONB normalization
4. any route or persistence-module change
5. any auth-role-definition change
6. any first-write admission phrase
7. any autonomous AI business-state mutation

## Final Verdict

Migration 016 is closed and live as a structural supplement.

The production schema and grant floor now match the minimum relational posture required for later onboarding redesign, but the original Lane 500 onboarding lane remains separately blocked until source/export governance and existing-row reconciliation are handled in a later packet.