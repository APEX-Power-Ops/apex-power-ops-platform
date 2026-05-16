# PM Lane 044 Handoff - Hosted PM Intake Route Scope Refresh

Date: 2026-05-15
Status: Authored, read-only hosted proof refreshed
Scope: Add `/pm-review/import-intake` to hosted PM intake smoke and executor closeout requirements

## Executive Summary

PM Lane 044 updates the hosted parity and dual-executor stack after PM Lane 043 added the local Project Miner import-intake workbench:

```text
/pm-review/import-intake
```

This lane does not deploy. It updates the smoke scripts, 041/041A handoffs, dispatch board, closeout template, and status docs so authenticated Vercel and Render executors have current instructions.

## What Changed

Hosted smoke:

1. `apps/operations-web/scripts/smoke-hosted-routes.mjs`
2. `apps/operations-web/scripts/smoke-pm-intake-hosted.mjs`

Executor/governance surfaces:

1. `ops/agents/packets/draft/2026-05-15-pm-lane-041-hosted-pm-intake-parity-refresh.json`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-041a-vercel-operations-web-promotion.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-041-hosted-pm-intake-parity-refresh-handoff.md`
4. `ops/agents/handoffs/2026-05-15-pm-lane-041-dual-executor-dispatch-board.md`
5. `ops/agents/handoffs/2026-05-15-pm-lane-041a-vercel-operations-web-promotion-handoff.md`
6. `ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`

Docs/status:

1. `PROJECT_STATUS.md`
2. `apps/operations-web/DEPLOYMENT_VALIDATION.md`
3. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
4. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
5. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
6. `ops/agents/packets/draft/2026-05-15-pm-lane-044-hosted-intake-route-scope-refresh.json`

## Route Scope

The operations-web hosted parity lane now requires the existing Vercel project to serve both:

```text
/pm-review/import-approval-readiness
/pm-review/import-intake
```

The Render lane does not expand. `/pm-review/import-intake` consumes the same four current PM intake read seams already assigned to PM Lane 041B:

```text
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
```

## Read-Only Hosted Evidence

Hosted route smoke:

```powershell
corepack pnpm --dir apps/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com
```

Result:

```text
SMOKE_SUMMARY failed=2 passed=10
failed routes:
/pm-review/import-approval-readiness returned 404
/pm-review/import-intake returned 404
```

Hosted PM intake smoke:

```powershell
corepack pnpm --dir apps/operations-web smoke:pm-intake-hosted
```

Result:

```text
PM_INTAKE_HOSTED_SUMMARY failed=7
operations-web import candidate passed
operations-web import admission plan passed
operations-web import approval readiness returned 404
operations-web import intake workbench returned 404
mutation seam health passed
mutation seam OpenAPI is missing current PM intake reads
all four PM intake reads returned 404
```

This red state is expected until an authenticated Vercel executor promotes current operations-web and an authenticated Render executor redeploys or classifies mutation-seam.

## Sidecar Result

A read-only sidecar confirmed the minimum safe update set:

1. keep `/pm-review/import-intake` in both hosted smoke scripts,
2. update 041A Vercel packet and handoff,
3. update the parent 041 dispatch surfaces,
4. update the closeout template for both Vercel route proofs,
5. do not expand 041B backend scope.

No sidecar edits, staging, commits, deployments, live Supabase/Render/Vercel calls, or destructive actions occurred.

## Guardrails Preserved

This tranche does not authorize:

1. Vercel promotion from this unauthenticated workspace,
2. Render redeploy from this unauthenticated workspace,
3. new hosted service,
4. DNS change,
5. auth or ingress widening,
6. backend endpoint changes,
7. SQL write,
8. schema migration,
9. fixture replay,
10. approval persistence,
11. import mutation,
12. live database write,
13. workbook macro execution,
14. workbook writeback,
15. assignment mutation,
16. schedule mutation,
17. status mutation,
18. autonomous AI business-state mutation.

## Next Recommended Move

Execute the already-authored hosted lanes:

1. PM Lane 041A: Vercel-authenticated existing-project promotion for `/pm-review/import-approval-readiness` and `/pm-review/import-intake`.
2. PM Lane 041B: Render-authenticated existing-service redeploy or blocker classification for the four PM intake reads.

Do not begin approval persistence schema or adapter work until hosted parity is green or the remaining hosted blocker is precisely classified.
