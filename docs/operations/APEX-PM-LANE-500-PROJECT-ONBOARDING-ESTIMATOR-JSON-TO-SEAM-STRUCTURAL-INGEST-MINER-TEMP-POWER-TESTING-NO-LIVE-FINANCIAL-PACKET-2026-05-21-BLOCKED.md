# APEX PM Lane 500 Project Onboarding - Estimator JSON To Seam Structural Ingest - Miner Temp Power Testing No-Live Financial Packet

Date: 2026-05-21

Status: Blocked and preserved as a truthful Phase 0 closeout

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_500_PROJECT_ONBOARDING_ESTIMATOR_JSON_TO_SEAM_STRUCTURAL_INGEST_BLOCKED_PHASE_0`

## Purpose

This packet preserves the truthful blocked state for the original PM Lane 500 onboarding objective: take the current estimator-side Temp Power planning/export material and drive it into the live `seam.*` structural surface as a governed onboarding path.

The lane does not proceed to business-row write design or first-write admission.

Instead, it records the exact Phase 0 blocker state and separates the minimum structural follow-on into migration 016 so later redesign work can start from a cleaner production floor.

## Blocked Outcome

Selected outcome:

`LANE_500_PROJECT_ONBOARDING_PHASE_0_BLOCKED_NO_LIVE`

Meaning:

1. The original onboarding lane remains blocked and no-live.
2. The blocked state is preserved as historical truth rather than softened into a partial-go narrative.
3. Migration 016 is treated as a separate structural supplement, not as completion of the onboarding lane.

## Phase 0 Recheck

### 1. Lane 421 predecessor state

Recheck result:

1. PM Lane 421 schema architecture correction was already live through migration 015.
2. `seam.scopes` exists and remains the correct operational scope anchor.
3. `seam.scope_labor_details.scope_id` and `seam.apparatus_revenue_events.scope_id` already target `seam.scopes(id)`.

Conclusion:

The original Lane 500 blocker is no longer the Lane 421 architecture defect. The remaining blocker set sits at the onboarding surface itself.

### 2. Current seam structural state for onboarding

Recheck result before migration 016:

1. `seam.projects` columns were `id`, `created_at`, `updated_at`, and `data`.
2. `seam.tasks` columns were `id`, `created_at`, `updated_at`, `data`, `status`, and `workpackage_id`.
3. `seam.apparatus` columns were only `id`, `created_at`, `updated_at`, and `data`.
4. `seam.apparatus` had no relational `scope_id` column.
5. Existing apparatus rows also had `0` populated `data->>'scope_id'` values.

Conclusion:

The earlier simplified statement that `seam.tasks` contained only `id/created_at/updated_at/data` is no longer current truth. The blocking apparatus gap remained real, but the task surface is richer than that earlier shorthand.

### 3. Current production row counts

Recheck result:

1. `seam.projects` row count = `1`
2. `seam.tasks` row count = `15`
3. `seam.apparatus` row count = `184`
4. `seam.scopes` row count = `0`

Conclusion:

Temp Power onboarding cannot be treated as a clean empty-surface import. Existing seam rows already exist and must be reconciled by any later admitted onboarding design.

### 4. Current grant posture before migration 016

Recheck result before migration 016:

1. `pm` and `operations` had only the earlier `seam.scopes` `SELECT` plus `INSERT` contract from migration 015.
2. `seam.projects`, `seam.tasks`, and `seam.apparatus` remained effectively admin-only for write posture.
3. `lane_420_rowcount_reader` still held the read-only verification grant posture on the earlier financial tables.

Conclusion:

Even if a later onboarding route had been otherwise ready, the operational table grant floor was still incomplete at the time of the blocked closeout.

### 5. Migration tracking state

Recheck result:

1. `supabase_migrations.schema_migrations` exists in the live project.
2. Migration 015 content is represented there under the live Supabase migration ledger.

Conclusion:

The current production schema floor is not speculative. Lane 500 Phase 0 recheck started from a live, tracked post-015 state.

## Blocking Facts Preserved

The onboarding lane remains blocked because the following are still true:

1. There is no governed current packet that truthfully turns the present estimator-side Temp Power export path into a production-safe onboarding source of record.
2. Existing Temp Power rows already occupy `seam.projects`, `seam.tasks`, and `seam.apparatus`, so later onboarding work must be explicit about reconciliation instead of pretending to do a first import.
3. The original structural defects on `seam.apparatus.scope_id` and operational-table grants needed to be corrected before any truthful redesign packet could continue.
4. No later packet has yet admitted route changes, business-row writes, or first-write execution for this onboarding family.

## What Migration 016 Does And Does Not Mean

Migration 016 is intentionally separate from this blocked closeout.

It does mean:

1. `seam.apparatus` now has a relational `scope_id` anchor.
2. `pm` and `operations` now have the missing `SELECT`, `INSERT`, and `UPDATE` posture on `seam.projects`, `seam.tasks`, and `seam.apparatus`.

It does not mean:

1. the estimator JSON onboarding lane is unblocked end-to-end
2. the workbook/export lineage is now governed
3. existing Temp Power seam rows have been reconciled
4. any business-row write or backfill has been admitted

## Boundaries Preserved

This blocked closeout admits no:

1. business-row insert, update, or delete
2. route or persistence-module implementation change
3. workbook macro execution or workbook writeback
4. first-write admission phrase
5. autonomous AI business-state mutation

## Next Truth

The next truthful move is not to resume the original onboarding lane as if Phase 0 passed.

The next truthful move is a later redesign packet that starts from the new migration 016 floor, explicitly chooses a governed source/export contract, and explicitly reconciles the already-present Temp Power seam rows before any write-admission discussion continues.