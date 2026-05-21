# PM Lane 420 Production Financial Table Schema Floor Closeout Handoff

Date: 2026-05-20

## Scope

Bounded live-schema remediation for the existing Lane 420 hosted smoke blocker on production Supabase.

This closeout covers only the missing four-table financial schema floor and the read-only verifier grant needed for the existing hosted smoke runner.

No route implementation changes were deployed from this handoff, and no production business rows were inserted.

## Repo Changes

1. Added executable migration [apps/mutation-seam/migrations/013_pm_lane_411_financial_tables.sql](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/migrations/013_pm_lane_411_financial_tables.sql).
2. Updated [PROJECT_STATUS.md](c:/APEX%20Platform/apex-power-ops-platform/PROJECT_STATUS.md) with the live schema-floor and passing hosted-smoke result.

## Production Facts Applied

1. Production base key shapes were verified before DDL application:
   - `seam.projects.id` is `TEXT`
   - `seam.apparatus.id` is `TEXT`
   - `public.scopes.id` is `UUID`
2. The four required tables were created live in schema `seam`:
   - `seam.project_contract_snapshots`
   - `seam.scope_labor_details`
   - `seam.apparatus_financials`
   - `seam.apparatus_revenue_events`
3. The required enum types were created live:
   - `seam.scope_labor_category`
   - `seam.apparatus_revenue_event_kind`
4. Insert-only triggers, RLS, and `anon`/`authenticated` revokes were applied live.
5. The existing read-only verifier role `lane_420_rowcount_reader` received `SELECT` on the four new tables so the hosted smoke could complete read-only row-count proof through the transaction pooler.

## Live Validation Commands

Hosted smoke rerun:

```powershell
# Provision the verified read-only transaction-pooler DSN from the secure operator boundary.
$env:LANE_420_DRY_RUN_FLAG_OBSERVATION='unset'
.\.venv\Scripts\python.exe apps/mutation-seam/scripts/lane_420_hosted_smoke/run_lane_420_hosted_smoke.py
```

## Live Validation Results

1. Supabase SQL editor returned `Success. No rows returned` for the schema-floor DDL.
2. Supabase verification confirmed all four required tables now resolve in production.
3. Hosted smoke rerun returned:
   - `LANE_420_SMOKE_STATUS passed`
   - `LANE_420_SMOKE_OUTPUT C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\scripts\lane_420_hosted_smoke\output\smoke_run_20260520T235801Z.json`
4. The passing artifact records:
   - `overall_status = passed`
   - `dry_run_flag_observation = unset`
   - both Lane 412 routes present in OpenAPI
   - PM and Operations success paths passed
   - task lead and field tech rejection paths passed
   - before and after row counts available with zero deltas across all four financial tables

## Final Verdict

PM Lane 420 is no longer blocked on missing production schema.

The live four-table financial schema floor now exists in production, the read-only verifier can truthfully count those tables, and the authoritative hosted rerun passed at [apps/mutation-seam/scripts/lane_420_hosted_smoke/output/smoke_run_20260520T235801Z.json](c:/APEX%20Platform/apex-power-ops-platform/apps/mutation-seam/scripts/lane_420_hosted_smoke/output/smoke_run_20260520T235801Z.json).

## Guardrails Preserved

1. No production business-row insert or update was performed.
2. No live import-contract-support write path was exercised against the database.
3. No route-path or auth-contract change was deployed from this closeout.
4. No secret value was added to repo files.
5. No new service, DNS, auth, or ingress surface was created.
6. No autonomous AI business-state mutation was admitted.