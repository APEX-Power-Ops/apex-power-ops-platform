# PM Lane 008 Handoff - Decision-History Query Narrowing

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-008`
Scope: PM runtime read-seam narrowing and workfront history-panel efficiency

## Summary

This tranche adds bounded query narrowing to the existing PM decision-history read seam and updates the PM workfront history panel to use it.

The route remains:

```text
GET /api/v1/reads/decision-history
```

No new endpoint, mutation endpoint, service, SQL, schema, auth, ingress, assignment, schedule, Operations Visibility, or autonomous AI mutation authority was added.

## Backend Changes

`/api/v1/reads/decision-history` now supports:

1. repeated `entity_id` query params, for example `?entity_id=issue-002&entity_id=task-001`,
2. optional `limit` with `ge=1` validation,
3. silent `limit` capping at `100`,
4. unchanged full-history behavior when no params are supplied.

Filtering occurs before sorting. The existing Lane 005 timestamp normalization and newest-first sort remain the ordering contract, and the limit is applied after sorting.

## Frontend Changes

The PM workfront decision-history panel now requests only row-relevant history:

```text
/api/v1/reads/decision-history?entity_id=<row issue id>&limit=25
```

The panel still loads lazily and keeps its local row-history filter as a defensive guard. Rows without decision entity IDs mark history as loaded-empty and do not fall back to full-history reads.

## Delegation And Orchestration Notes

Two read-only scouts reviewed the slice before closeout:

1. Backend scout `019e2c52-c2a8-7251-aa65-f13181bdd1ba` recommended repeated `entity_id` params, no-param backward compatibility, a named cap constant, silent `min(limit, 100)`, and tests for repeated params plus limit validation.
2. Frontend scout `019e2c52-c35e-7933-8022-01f7bf502cd5` recommended `URLSearchParams`, `limit=25`, a no-ID guard to avoid full-history fallback, query-string route matching, and preserving the existing return-to-lead mutation assertion.

Codex retained coordinator, reviewer, release-gate, and executor authority for implementation, validation, packet authorship, and closeout.

## Files Changed

Backend:

1. `apps/mutation-seam/app/routers/reads.py`
2. `apps/mutation-seam/tests/test_pipeline_integration.py`

Frontend:

1. `apps/operations-web/app/pm-review/workfront/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`

Packet and status:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-008-decision-history-query-narrowing.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-008-decision-history-query-narrowing-handoff.md`

## Validation

Focused backend validation:

```powershell
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_issue_disposition.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pipeline_integration.py" -q
```

Result: `16 passed` with existing Pydantic v2 deprecation warnings.

Frontend validation:

```powershell
corepack pnpm build
corepack pnpm typecheck
corepack pnpm exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts
```

Results:

1. `next build` passed and prerendered `/pm-review/workfront`.
2. `tsc --noEmit` passed.
3. Focused Playwright smoke passed `1 passed`; it asserts row-scoped decision-history requests use `entity_id=issue-200` and `limit=25`, history open performs no mutation, unrelated history stays hidden, and the PM-clicked Class C `return_to_lead` request remains unchanged.

## Guardrails Preserved

1. No SQL or schema migration.
2. No live database write.
3. No new endpoint.
4. No new service admission.
5. No auth or ingress widening.
6. No assignment mutation.
7. No schedule mutation.
8. No Operations Visibility reopening.
9. No autonomous AI business-state mutation.
10. No new mutation endpoint.

## Next Bounded Move

Recommended next move: add a non-mutating PM workfront route smoke against the hosted/read-only environment if a stable hosted route is available, or prepare a staging-only governed return-to-lead proof packet that can produce one real audit row without touching production data.
