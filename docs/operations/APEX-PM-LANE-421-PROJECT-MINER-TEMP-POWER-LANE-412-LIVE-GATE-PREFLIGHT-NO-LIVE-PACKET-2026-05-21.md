# APEX PM Lane 421 - Project Miner Temp Power Lane 412 Live-Gate Preflight No-Live Packet

Date: 2026-05-21

Status: Blocked and not promoted

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_412_LIVE_GATE_PREFLIGHT_NO_LIVE`

## Purpose

PM Lane 421 is the final no-write preflight before any Lane 422 first-write packet can even be discussed for the Temp Power `project-import-contract-support` mutation family.

This packet had four bounded goals:

1. convert the Lane 411 Revision C PM-plus-Operations grant contract into executable live SQL
2. verify the production financial-table grant posture truthfully
3. fix the exact no-write admission-gate inputs for the Temp Power project
4. run the rollback-only five-target atomic probe if and only if a truthful Temp Power `public.scopes.id` anchor exists in production

## Selected Outcome

Selected outcome:

`LANE_412_LIVE_GATE_PREFLIGHT_BLOCKED_ON_MISSING_TEMP_POWER_PUBLIC_SCOPE_ANCHOR_NO_LIVE`

Meaning:

1. the grant contract is now applied live and verified true
2. the live Render env still shows `LANE_412_DRY_RUN_ENABLED` absent
3. the exact Temp Power project, candidate, digest, apparatus, and task anchors are now fixed
4. the project-specific rollback-only atomic probe remains blocked because production exposes no truthful Temp Power `public.scopes.id` anchor
5. the Lane 422 admission phrase is not minted in this packet

## Phase 0 Discovery

### 1. Executable grant surface

Discovery result:

1. the repo now carries executable migration `apps/mutation-seam/migrations/014_pm_lane_411_revision_c_role_contract_grants.sql`
2. the migration creates `pm` and `operations` when absent
3. the migration grants `USAGE` on schema `seam` plus `SELECT` and `INSERT` on the four financial tables to `pm` and `operations`
4. the migration preserves the deny posture for `anon` and `authenticated`
5. the migration preserves non-admission for `field_tech`, `field_lead`, and `task_lead` when those roles exist

Conclusion:

Lane 421 has a truthful executable SQL surface for the Lane 411 Revision C role contract.

### 2. Live grant verification

Discovery result:

1. the authenticated Supabase SQL editor applied migration 014 and returned `Success. No rows returned`
2. live role existence now resolves exactly to `anon`, `authenticated`, `operations`, and `pm`
3. `pm` has `USAGE` on schema `seam` and `SELECT` plus `INSERT` on all four financial tables
4. `operations` has the same `USAGE` plus `SELECT` and `INSERT` contract on all four financial tables
5. `anon` and `authenticated` are denied `SELECT` and `INSERT` across all four financial tables, including `seam.apparatus_revenue_events`
6. the field-facing roles remain absent in production today, so the deny posture remains satisfied by non-existence

Conclusion:

The Lane 411 Revision C PM-plus-Operations grant contract is now true in production.

### 3. Exact no-write gate inputs

Discovery result:

1. Lane 415 digest remains `1859896bcbac1220d21266b19603a12eae710a6e9fbf553c132b7028e417026d`
2. the exact project anchor remains `pm-import-project-miner-temp-power`
3. the exact candidate anchor remains `pm-import-candidate-miner-temp-power`
4. the exact apparatus anchor is now `pm-import-project-miner-temp-power-app-0001`
5. the exact task anchor is now `pm-import-project-miner-temp-power-task-0001`
6. the live task carries `data->>'scope_id' = null`

Conclusion:

The project-specific scope anchor is still unresolved in production.

### 4. Canonical scope-surface discovery

Discovery result:

1. `public.projects` exists and contains exactly one row
2. that row is a LASNAP sample project:
   - `id = 33333333-0000-0000-0000-000000000001`
   - `project_number = LASNAP16`
   - `project_name = LASNAP Foods - Annual Maintenance Testing 2016`
3. `public.scopes` exists and contains exactly four rows
4. all four scope rows belong to the same LASNAP sample project:
   - `44444444-0000-0000-0000-000000000001 / LASNAP16-01 / Main Substation Testing`
   - `44444444-0000-0000-0000-000000000002 / LASNAP16-02 / Transformer Testing`
   - `44444444-0000-0000-0000-000000000003 / LASNAP16-03 / MCC Testing Building A`
   - `44444444-0000-0000-0000-000000000004 / LASNAP16-04 / MCC Testing Building B`
5. no `public.projects` or `public.scopes` row representing Temp Power exists in production today

Conclusion:

Lane 421 cannot truthfully run the rollback-only five-target atomic probe against a Temp Power scope anchor, because production does not expose one.

## Implemented Artifact Surface

### 1. Repo-owned executable and rerunnable surfaces

Implemented surface:

1. `apps/mutation-seam/migrations/014_pm_lane_411_revision_c_role_contract_grants.sql`
2. `apps/mutation-seam/scripts/lane_421_grant_verification/run_lane_421_grant_verification.py`
3. `apps/mutation-seam/scripts/lane_421_grant_verification/run_lane_421_atomic_transaction_probe.py`
4. `apps/mutation-seam/scripts/lane_421_grant_verification/README.md`

### 2. Recorded Lane 421 JSON artifacts

Recorded artifacts:

1. `apps/mutation-seam/scripts/lane_421_grant_verification/output/grant_verification_live_sql_editor_20260521T011102Z.json`
2. `apps/mutation-seam/scripts/lane_421_grant_verification/output/atomic_transaction_probe_blocked_20260521T011102Z.json`

These artifacts truthfully distinguish the green grant proof from the blocked project-specific atomic probe.

## Validation

Live no-write validation completed through the authenticated Supabase SQL editor and authenticated Render inspection:

1. migration 014 applied with `Success. No rows returned`
2. grant matrices for `pm`, `operations`, `anon`, and `authenticated` were explicitly verified on the four-table financial surface
3. Render inspection confirmed `LANE_412_DRY_RUN_ENABLED` remains absent on the live mutation-seam service
4. live anchor discovery confirmed the Temp Power apparatus and task IDs, but also proved the task has no scope id and the canonical `public.projects` plus `public.scopes` surface contains only LASNAP sample rows

The local rerunnable Python verification scripts remain present and py-compile clean, but they were not executed in this packet because the workspace still lacks a privileged admin DSN.

## Admission Phrase Status

The exact Lane 422 first-write admission phrase is not minted here.

Reason:

Lane 421 is blocked before the project-specific rollback probe can pass truthfully, so a first-write phrase would overstate live readiness.

## Boundary

This packet does not admit:

1. any committed production business-row insert
2. any live execution of the five-target atomic probe with a fabricated or cross-project scope id
3. any route-path or auth-layer change
4. any first-write admission phrase
5. any Lane 422 advancement

## Next Truth

The next truthful follow-on is not a first write.

The next truthful follow-on is a bounded scope-anchor remediation or proof packet that does one of two things:

1. establishes a real Temp Power `public.projects` and `public.scopes` anchor in production through the governed upstream surface, or
2. proves a different canonical scope-anchor source for Temp Power without inventing one from the seam tables

Only after that anchor exists should Lane 421 rerun the rollback-only five-target atomic probe and, if it passes, mint the Lane 422 first-write admission phrase.