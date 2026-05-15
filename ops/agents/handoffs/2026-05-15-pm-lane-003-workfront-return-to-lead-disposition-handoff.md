# PM Lane 003 Handoff - Workfront Return-To-Lead Disposition

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-003`
Scope: PM runtime product lane with user-initiated Class C issue disposition

## Summary

This tranche turns the PM workfront from advisory-only follow-up drafting into one explicit, PM-clicked issue disposition loop.

The route still uses the existing governed seam:

```text
POST /api/v1/mutations/issues
action_type: return_to_lead
mutation_class: C
payload.status: in_review
```

No new endpoint, service, SQL, schema, auth, ingress, assignment, schedule, or autonomous AI mutation authority was added.

## Backend Changes

`apps/mutation-seam` now hardens `return_to_lead` beyond the generic issue transition table:

1. actor project scope must include the issue `project_id`,
2. the issue must currently be `escalated`,
3. payload `status` must be exactly `in_review`,
4. the PM disposition reason must be non-empty.

The PM workfront read model now also surfaces:

1. `returnable_issue_id`,
2. `latest_pm_followup_note`,
3. `latest_pm_followup_sent_at`,
4. returned follow-up evidence inside each blocking issue summary.

## Frontend Changes

`/pm-review/workfront` now enables `Return to lead` only for rows with an escalated issue. Opening the advisory draft still performs no mutation. Clicking `Return to lead` sends a PM-authenticated Class C issue mutation and then refreshes the workfront.

The UI copy preserves the human-action boundary:

1. `This records a PM disposition through the governed seam. AI advisory remains draft-only.`
2. `PM returned this issue to lead review.`

## Delegation And Orchestration Notes

Two read-only scouts reviewed the slice before closeout:

1. Backend scout `019e2c33-2bb3-7fc1-ab6f-c0de91afb300` recommended keeping the existing issue route while adding semantic validation for scope, escalated source state, target status, reason, idempotency, and audit.
2. Frontend scout `019e2c33-44bc-7113-8379-5e80e67c8709` recommended gating the UI to escalated issues, using `Return to lead` wording, asserting the PM token and request body, and proving no mutation fires merely from opening the advisory panel.

Codex retained coordinator, reviewer, release-gate, and executor authority for implementation, validation, packet authorship, and closeout.

## Files Changed

Backend:

1. `apps/mutation-seam/app/services/mutation_pipeline.py`
2. `apps/mutation-seam/app/pm_workfront_read_model.py`
3. `apps/mutation-seam/tests/test_pm_issue_disposition.py`
4. `apps/mutation-seam/tests/test_pm_workfront_read_model.py`
5. `apps/mutation-seam/tests/test_pipeline_integration.py`

Frontend:

1. `apps/operations-web/app/pm-review/workfront/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`

Packet and status:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-003-workfront-return-to-lead-disposition.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-003-workfront-return-to-lead-disposition-handoff.md`

## Validation

Focused backend validation:

```powershell
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_issue_disposition.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pipeline_integration.py" -q
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
3. Focused Playwright smoke passed `1 passed`; it asserts no mutation occurs on advisory draft open, then asserts the exact PM-clicked Class C `return_to_lead` request body, PM bearer token payload, client timestamp, and post-action workfront refresh.

## Guardrails Preserved

1. No SQL or schema migration.
2. No new service admission.
3. No auth or ingress widening.
4. No assignment mutation.
5. No schedule mutation.
6. No Operations Visibility reopening.
7. No autonomous AI business-state mutation.
8. No new mutation endpoint.

## Next Bounded Move

The next PM product slice should stay in one of two lanes:

1. add PM workfront operational lenses for returned-to-lead, stale blockers, and unassigned readiness without new mutation authority, or
2. add live workfront decision history context beside each returned issue, still read-only, so PM can see the last disposition without leaving the queue.
