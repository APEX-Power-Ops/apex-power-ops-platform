# PM Lane 036 Handoff - Hosted PM Intake UI Promotion And Render Parity Blocker

Date: 2026-05-15
Status: Complete
Scope: Vercel-hosted PM intake UI proof plus Render backend parity blocker

## Executive Summary

PM Lane 036 makes the new Project Miner Temp Power intake review pages visible on the production operations-web URL:

1. `https://operations.apexpowerops.com/pm-review/import-candidate`
2. `https://operations.apexpowerops.com/pm-review/import-admission-plan`

It also adds repeatable hosted smoke coverage that separates frontend route proof from backend Render parity proof. The current truthful verdict is:

`operations-web hosted route parity is live; hosted PM intake live-data parity is blocked by stale Render mutation-seam deployment and missing Render-authenticated redeploy/log inspection access.`

## What Changed

Deployment/tooling:

1. Added repo-root `.vercelignore` so root-invoked operations-web deploys exclude docs, ops, backend services, private infra, caches, and local residue while preserving the configured `apps/operations-web` Vercel root directory.
2. Extended `apps/operations-web/scripts/smoke-hosted-routes.mjs` to cover `/pm-review/import-candidate` and `/pm-review/import-admission-plan`.
3. Hardened the hosted route smoke parser so pnpm's `--` separator is accepted.
4. Added `apps/operations-web/scripts/smoke-pm-intake-hosted.mjs`.
5. Added `smoke:pm-intake-hosted` to `apps/operations-web/package.json`.

Documentation:

1. Updated `PROJECT_STATUS.md`.
2. Updated `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`.
3. Updated `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`.
4. Updated `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`.

## Vercel Production Proof

Vercel identity:

`jasonlswenson-sys`

Final production deployment:

`dpl_GhaHP7v2QPA8SKDC7t7yU5PzNfCt`

Production alias:

`https://operations.apexpowerops.com`

Inspect URL:

`https://vercel.com/jasonlswenson-sys-projects/apex-operations-web/GhaHP7v2QPA8SKDC7t7yU5PzNfCt`

The final deploy used the tightened `.vercelignore` and uploaded `14.0KB`. The Vercel build listed both routes:

1. `/pm-review/import-candidate`
2. `/pm-review/import-admission-plan`

The initial Vercel publish from repo root proved the routes but uploaded the broader repo. That deployment was superseded by the final scoped deployment above. An intermediate overly strict `.vercelignore` attempt failed because it hid the configured `apps/operations-web` root directory from Vercel; the final denylist preserves that root and is now the repo-owned deployment hygiene guard.

## Hosted Validation

Commands run from `C:/APEX Platform/apex-power-ops-platform` unless noted.

```powershell
node --check apps/operations-web/scripts/smoke-pm-intake-hosted.mjs
```

Result:

passed

```powershell
node --check apps/operations-web/scripts/smoke-hosted-routes.mjs
```

Result:

passed

```powershell
corepack pnpm --filter @apex/operations-web typecheck
```

Result:

passed

```powershell
corepack pnpm --filter @apex/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com
```

Result:

`SMOKE_SUMMARY failed=0 passed=10 base_url=https://operations.apexpowerops.com/`

```powershell
corepack pnpm --filter @apex/operations-web smoke:pm-intake-hosted -- --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com
```

Result:

1. UI import candidate route passed.
2. UI import admission plan route passed.
3. Mutation-seam health passed.
4. Mutation-seam OpenAPI failed because the new PM intake paths are missing.
5. `GET /api/v1/reads/project-import-candidate` failed with `404`.
6. `GET /api/v1/reads/project-import-admission-plan` failed with `404`.

Summary:

`PM_INTAKE_HOSTED_SUMMARY failed=3 operations_web_base_url=https://operations.apexpowerops.com/ mutation_seam_base_url=https://mutation-seam.apexpowerops.com/`

```powershell
.venv/Scripts/python.exe apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com
```

Result:

1. health passed with `200`,
2. root passed with `200`,
3. approval queue passed with `200`,
4. schedule projects, drivers, tracer, and variance failed with `500`.

```powershell
.venv/Scripts/python.exe -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-036-hosted-pm-intake-parity.json', encoding='utf-8')); print('packet-json-ok')"
```

Result:

`packet-json-ok`

Scoped `git diff --check` passed for the Lane 036 file set.

## Render Blocker

Render auth/token/service metadata are unavailable in the current Codex workspace. No `RENDER_*` environment variables surfaced, and no `render` CLI command was available.

Because of that, this lane did not attempt to:

1. trigger a Render redeploy,
2. inspect Render logs,
3. inspect Render env posture,
4. repair Render service metadata.

The next backend parity lane needs Render-authenticated access to redeploy `apex-platform-mutation-seam`, confirm the deployed commit, inspect logs, and rerun the PM intake hosted smoke until the new read endpoints are present.

## Orchestration Notes

An internal read-only sidecar scout checked the hosted-parity options while the coordinator continued direct execution. The scout recommended exactly this closeout boundary: Vercel-only promotion or verification is safe; full hosted PM parity cannot be claimed without Render access.

The coordinator retained final write ownership and did not delegate code edits.

## Guardrails Preserved

This packet does not authorize:

1. Render deployment from this workspace,
2. Render metadata repair,
3. SQL or schema migration,
4. live database write,
5. production import,
6. approval persistence,
7. workbook writeback,
8. workbook macro execution,
9. service admission,
10. auth or ingress widening,
11. package dependency addition,
12. server-side PM note persistence,
13. candidate edit persistence,
14. import mutation,
15. assignment mutation,
16. schedule mutation,
17. status mutation,
18. autonomous AI business-state mutation.

## Recommended Next Packet

PM Lane 037 should be a Render-authenticated mutation-seam hosted parity packet.

Required scope:

1. confirm Render service `apex-platform-mutation-seam` target commit,
2. trigger or verify redeploy of current `clean-main`,
3. inspect logs for import-candidate/admission-plan route registration,
4. rerun hosted PM intake smoke,
5. rerun deployed mutation-seam smoke,
6. record whether schedule read `500` failures are resolved or need a separate schedule parity packet.

Only after Render exposes the new read endpoints should the PM lane claim hosted live-data proof for the intake pages.
