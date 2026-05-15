# PM Lane 006 Handoff - Workfront Read-Only Decision-History Panel

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-006`
Scope: PM runtime frontend read lane over the normalized decision-history seam

## Summary

This tranche adds a lazy, read-only disposition-history panel inside the existing PM workfront row expansion.

The panel reuses the existing normalized read seam:

```text
GET /api/v1/reads/decision-history
```

No backend endpoint, mutation endpoint, service, SQL, schema, auth, ingress, assignment, schedule, Operations Visibility, or autonomous AI mutation authority was added.

## Frontend Changes

`/pm-review/workfront` now includes a scoped `Disposition history` region in the expanded row panel.

The history panel:

1. loads only when PM clicks `View history` or `Refresh history`,
2. filters the returned history locally by `primary_blocking_issue_id`, `returnable_issue_id`, `last_pm_decision.entity_id`, and `blocking_issues[].id`,
3. shows the PM action, status transition, timestamp, actor role, and PM reason,
4. clears stale history rows on fetch failure,
5. keeps explicit copy that the panel is read-only and `Return to lead` is the only mutation action on the surface.

## Delegation And Orchestration Notes

Two read-only scouts reviewed the slice before closeout:

1. Backend scout `019e2c49-3714-7390-b4e0-6341b56ebd9b` recommended reusing the existing normalized `/api/v1/reads/decision-history` contract, filtering by issue IDs client-side, and avoiding reliance on `entity_type` or full audit payload internals.
2. Frontend scout `019e2c49-37bf-7f52-a855-63f62203a3b4` recommended the inline per-row panel, lazy loading, read-only copy, `last_pm_decision.entity_id` filtering, stale-history clearing, and scoped Playwright assertions.

Codex retained coordinator, reviewer, release-gate, and executor authority for implementation, validation, packet authorship, and closeout.

## Files Changed

Frontend:

1. `apps/operations-web/app/pm-review/workfront/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`

Packet and status:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-006-workfront-read-only-decision-history-panel.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-006-workfront-read-only-decision-history-panel-handoff.md`

## Validation

Frontend validation:

```powershell
corepack pnpm build
corepack pnpm typecheck
corepack pnpm exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts
```

Results:

1. `next build` passed and prerendered `/pm-review/workfront`.
2. `tsc --noEmit` passed.
3. Focused Playwright smoke passed `1 passed`; it asserts lazy decision-history loading, scoped history rendering, unrelated history exclusion, no mutation from history open, and the unchanged PM-clicked Class C `return_to_lead` request.

Focused backend validation:

```powershell
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_issue_disposition.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pipeline_integration.py" -q
```

Result: `15 passed` with existing Pydantic v2 deprecation warnings.

## Guardrails Preserved

1. No SQL or schema migration.
2. No backend endpoint change.
3. No new service admission.
4. No auth or ingress widening.
5. No assignment mutation.
6. No schedule mutation.
7. No Operations Visibility reopening.
8. No autonomous AI business-state mutation.
9. No new mutation endpoint.

## Next Bounded Move

The next PM product slice should stay non-destructive. Recommended options:

1. a non-mutating Supabase parity inspection packet for `seam.audit_log` and issue JSON overflow fields before live-history claims, or
2. optional query narrowing on the existing decision-history read endpoint, preserving the default full-history behavior and adding only bounded `entity_id` plus capped `limit` parameters.
