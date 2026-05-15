# PM Lane 004 Handoff - Workfront Read-Only Lenses And Disposition History

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-004`
Scope: PM runtime product lane with read-only triage lenses and disposition context

## Summary

This tranche keeps the PM workfront inside the existing read projection while making the queue more operationally useful for PM triage.

The route still uses:

```text
GET /api/v1/reads/pm-workfront
```

No new read endpoint, mutation endpoint, service, SQL, schema, auth, ingress, assignment, schedule, Operations Visibility, or autonomous AI mutation authority was added.

## Backend Changes

`apps/mutation-seam` now enriches the existing PM workfront read model with:

1. top-level `lenses` counts for all, blocked, needs PM disposition, returned to lead, stale blockers, and unassigned rows,
2. row-level `lens_tags` computed from existing readiness, blocking issue, ownership, PM follow-up, and audit context,
3. row-level `last_pm_decision` context derived from existing audit rows for PM disposition actions,
4. continued `summary` readiness counts for frontend compatibility.

The read router passes the existing store audit log into the PM workfront projection. The projection keeps the audit payload compact by surfacing only the latest decision fields needed for queue context.

## Frontend Changes

`/pm-review/workfront` now exposes read-only lens controls for:

1. `All`,
2. `Blocked`,
3. `Needs PM disposition`,
4. `Returned to lead`,
5. `Stale blockers`,
6. `Unassigned`,
7. existing readiness filters.

Expanded rows now show returned-to-lead review context and the latest PM disposition without creating a new action path. The existing `Return to lead` button remains the only PM-clicked mutation on the route, and it remains gated to returnable escalated issues.

## Delegation And Orchestration Notes

Two read-only scouts reviewed the slice before closeout:

1. Backend scout `019e2c3d-c2a9-75f0-80d4-f09ff919d91d` recommended enriching the existing `/api/v1/reads/pm-workfront` projection only, with no new endpoint, schema, store contract, or mutation authority.
2. Frontend scout `019e2c3d-dd1a-7bb0-b814-64c4ad83948a` recommended read-only lens labels, disposition-history wording, and Playwright assertions proving no mutation occurs when advisory context is opened.

Codex retained coordinator, reviewer, release-gate, and executor authority for implementation, validation, packet authorship, and closeout.

## Files Changed

Backend:

1. `apps/mutation-seam/app/pm_workfront_read_model.py`
2. `apps/mutation-seam/app/routers/reads.py`
3. `apps/mutation-seam/tests/test_pm_workfront_read_model.py`

Frontend:

1. `apps/operations-web/app/pm-review/workfront/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`

Packet and status:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-004-workfront-read-only-lenses-and-disposition-history.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-004-workfront-read-only-lenses-and-disposition-history-handoff.md`

## Validation

Focused backend validation:

```powershell
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_issue_disposition.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pipeline_integration.py" -q
```

Result: `14 passed` with existing Pydantic v2 deprecation warnings.

Frontend validation:

```powershell
corepack pnpm build
corepack pnpm typecheck
corepack pnpm exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts
```

Results:

1. `next build` passed and prerendered `/pm-review/workfront`.
2. `tsc --noEmit` passed.
3. Focused Playwright smoke passed `1 passed`; it asserts no mutation occurs on advisory draft open, lens counts transition after return-to-lead, returned-to-lead disposition history is visible, stale-blocker filtering updates, and the unchanged PM-clicked Class C `return_to_lead` request remains intact.

## Guardrails Preserved

1. No SQL or schema migration.
2. No new service admission.
3. No auth or ingress widening.
4. No assignment mutation.
5. No schedule mutation.
6. No Operations Visibility reopening.
7. No autonomous AI business-state mutation.
8. No new mutation endpoint.
9. No new read endpoint.

## Next Bounded Move

The next PM product slice should stay read-first. Recommended next options:

1. add a read-only PM decision-history drawer or inline timeline backed by the existing decision-history read surface after timestamp-shape hardening, or
2. add a PM lane packet for Supabase parity inspection of the workfront/disposition fields before claiming live database parity for returned-to-lead history.
