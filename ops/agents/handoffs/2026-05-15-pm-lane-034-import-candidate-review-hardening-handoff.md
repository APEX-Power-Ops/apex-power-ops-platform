# PM Lane 034 Handoff - Import Candidate Review Hardening

Date: 2026-05-15
Status: Complete
Scope: Project Miner Temp Power read-only import-candidate review hardening

## Executive Summary

PM Lane 034 hardens `/pm-review/import-candidate` so the Project Miner Temp Power review route is more useful for day-to-day PM intake review before any import mutation exists.

The tranche keeps the same boundary as PM Lane 033:

`GET /api/v1/reads/project-import-candidate`

No approval, import, assignment, schedule, status, workbook macro, workbook writeback, Supabase write, Render deployment, Vercel promotion, or autonomous AI business-state mutation is admitted.

## What Changed

Backend read model:

1. `apps/mutation-seam/app/project_import_candidate.py` now adds `source_freshness`.
2. The freshness strategy is `path_size_mtime_fingerprint`.
3. Each source file reports source id, label, path, found flag, size, modified time, stat fingerprint, and freshness status.
4. The candidate reports an aggregate source fingerprint and review action.

Frontend review route:

1. `apps/operations-web/app/pm-review/import-candidate/page.tsx` now renders source freshness.
2. Warning review supports severity filters and warning-code filtering.
3. The page can export browser-only JSON containing the current candidate and local PM draft notes.
4. PM questions draft is retained only in browser storage.

Focused proof:

1. `apps/mutation-seam/tests/test_project_import_candidate.py` asserts source freshness metadata while preserving `mutation_authority: not_admitted`.
2. `apps/operations-web/tests/browser-shell.pm-import-candidate.smoke.spec.ts` asserts filters, source freshness, JSON download, local draft restoration after reload, absent Approve/Import buttons, and zero mutation requests.

## Orchestration Notes

The coordinator used an internal read-only sidecar scout for PM Lane 034. The scout recommended the same bounded hardening shape:

1. source freshness panel,
2. warning filters,
3. JSON export,
4. local-only PM notes/questions.

The coordinator retained write ownership, integrated the recommendation, validated the tranche, and closed the sidecar. No external executor write result was accepted into the repo for this packet.

## Validation

Commands run from `C:/APEX Platform/apex-power-ops-platform` unless noted:

```powershell
.venv/Scripts/python.exe -m pytest apps/mutation-seam/tests/test_project_import_candidate.py
```

Result:

`2 passed`

```powershell
corepack pnpm --filter @apex/operations-web typecheck
```

Result:

passed

```powershell
corepack pnpm --filter @apex/operations-web build
```

Result:

passed and listed `/pm-review/import-candidate`

```powershell
corepack pnpm exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts
```

Run from:

`C:/APEX Platform/apex-power-ops-platform/apps/operations-web`

Result:

`1 passed`

The first focused browser-smoke run exposed a strict-mode duplicate text assertion after the warning-code dropdown was added. The assertion was scoped to the warning-review section and rerun successfully.

Additional visual proof:

The Browser plugin opened the route at:

`http://host.docker.internal:3031/pm-review/import-candidate`

against a current local API/UI pair:

1. current mutation seam on `127.0.0.1:8011`,
2. current operations-web production server on `127.0.0.1:3031`,
3. `MUTATION_SEAM_BASE_URL=http://127.0.0.1:8011`.

## Guardrails Preserved

This packet does not authorize:

1. SQL or schema migration,
2. live database write,
3. production import,
4. workbook writeback,
5. workbook macro execution,
6. Render deployment,
7. Vercel promotion,
8. service admission,
9. auth or ingress widening,
10. package dependency addition,
11. approval persistence,
12. server-side PM note persistence,
13. candidate edit persistence,
14. import mutation,
15. assignment mutation,
16. schedule mutation,
17. status mutation,
18. autonomous AI business-state mutation.

## Current Review Surface

Local review URL while the temporary servers are running:

`http://127.0.0.1:3031/pm-review/import-candidate`

User-facing hosted route remains:

`https://operations.apexpowerops.com/pm-review/import-candidate`

Hosted proof still depends on the separate Render mutation-seam parity lane.

## Recommended Next Packet

PM Lane 035 should prepare the first human-approved import-admission design without implementing the write yet.

Recommended scope:

1. define the approval record shape,
2. define import idempotency keys,
3. define preview-to-import diff checks,
4. define rollback/no-go checks,
5. keep SQL/import mutation unadmitted until Jason approves a specific candidate and the hosted seam parity gap is closed or explicitly bypassed for local-only rehearsal.
