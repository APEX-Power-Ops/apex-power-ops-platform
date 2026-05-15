# PM Lane 009 Handoff - Read-Only Live Workfront Smoke Extension

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-009`
Scope: PM runtime read-only hosted/live smoke extension

## Summary

This tranche extends the existing `smoke:pm-live-data` path so deployment-time PM proof now covers the workfront read model and narrowed decision-history read.

It does not add a new script entrypoint. It extends the existing smoke lane:

```text
corepack pnpm smoke:pm-live-data
```

No backend endpoint, mutation endpoint, service, SQL, schema, auth, ingress, assignment, schedule, Operations Visibility, or autonomous AI mutation authority was added.

## Smoke Runner Changes

`apps/operations-web/scripts/smoke-pm-live-data.mjs` now checks:

1. `GET /api/v1/reads/pm-workfront`,
2. PM workfront `rows` shape,
3. non-negative `summary.total_count`,
4. `advisory.mode: read_only`,
5. `advisory.ai_mutation_authority: not_admitted`,
6. row-scoped `GET /api/v1/reads/decision-history?entity_id=...&limit=25`,
7. no-op narrowed decision-history read when no workfront issue IDs exist, without falling back to full history.

Empty decision history remains a pass, preserving the PM Lane 007 `PASS_WITH_EMPTY_LIVE_HISTORY` verdict.

## Browser Smoke Changes

`apps/operations-web/tests/browser-shell.pm-live-data.smoke.spec.ts` now verifies the same PM workfront and row-scoped decision-history reads through operations-web same-origin ingress.

It also installs a mutation sentinel for:

```text
/api/v1/mutations/**
```

The test never clicks `Return to lead` and asserts no mutation request occurs.

## Delegation And Orchestration Notes

Two read-only scouts reviewed the slice before closeout:

1. Backend/live-smoke scout `019e2c59-1e3a-7d72-86c2-e8a7637bd302` recommended extending the existing `smoke:pm-live-data` path, asserting PM workfront read-only posture, keeping history row-scoped and capped, and preserving empty-history truth.
2. Frontend/package scout `019e2c59-1e79-7560-8cf2-f7a7f84e187b` recommended no new package script, same-origin Playwright/API checks, a mutation sentinel, and no full-history fallback when workfront rows have no issue IDs.

Codex retained coordinator, reviewer, release-gate, and executor authority for implementation, validation, packet authorship, and closeout.

## Files Changed

Frontend smoke tooling:

1. `apps/operations-web/scripts/smoke-pm-live-data.mjs`
2. `apps/operations-web/tests/browser-shell.pm-live-data.smoke.spec.ts`

Packet and status:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-009-read-only-live-workfront-smoke-extension.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-009-read-only-live-workfront-smoke-extension-handoff.md`

## Validation

Local validation:

```powershell
node --check scripts/smoke-pm-live-data.mjs
corepack pnpm typecheck
corepack pnpm build
corepack pnpm exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts
node scripts/smoke-pm-live-data.mjs --help
```

Results:

1. Node syntax check passed.
2. `tsc --noEmit` passed after build-generated Next types were present.
3. `next build` passed and prerendered `/pm-review/workfront`.
4. Focused mocked PM workfront Playwright smoke passed `1 passed`.
5. Smoke runner help path printed usage successfully.

The actual hosted smoke command was not run against `https://operations.apexpowerops.com` in this local turn because the current clean-main change must first be deployed there. The intended deployment-time command is:

```powershell
$env:OPERATIONS_WEB_BASE_URL='https://operations.apexpowerops.com'
$env:MUTATION_SEAM_BASE_URL='https://mutation-seam.apexpowerops.com'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:pm-live-data
```

## Guardrails Preserved

1. No SQL or schema migration.
2. No live database write.
3. No new endpoint.
4. No new package script.
5. No new service admission.
6. No auth or ingress widening.
7. No assignment mutation.
8. No schedule mutation.
9. No Operations Visibility reopening.
10. No autonomous AI business-state mutation.
11. No new mutation endpoint.

## Next Bounded Move

Recommended next move: deploy or promote operations-web from the new clean-main head, then run the hosted `smoke:pm-live-data` proof against `https://operations.apexpowerops.com` and `https://mutation-seam.apexpowerops.com` without performing any mutation.
