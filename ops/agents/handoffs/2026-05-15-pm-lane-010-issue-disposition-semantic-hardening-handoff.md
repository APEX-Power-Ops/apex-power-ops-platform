# PM Lane 010 Handoff - Issue Disposition Semantic Hardening

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-010`
Scope: PM runtime Class C issue-disposition hardening

## Summary

This tranche hardens the existing `/api/v1/mutations/issues` Class C PM disposition seam. It does not create a new mutation route; it tightens the semantics of already-admitted issue actions.

The shared validator now covers:

1. `return_to_lead`,
2. `resolve_escalated`,
3. `re_escalate`.

No backend service, endpoint, SQL, schema, auth, ingress, assignment, schedule, Operations Visibility, or autonomous AI mutation authority was added.

## Backend Changes

`apps/mutation-seam/app/services/mutation_pipeline.py` now requires explicit PM issue-disposition semantics:

1. `return_to_lead` requires source status `escalated`, target status `in_review`, actor project scope, and non-empty PM reason.
2. `resolve_escalated` requires source status `escalated`, target status `resolved`, actor project scope, and non-empty PM reason.
3. `re_escalate` requires source status `in_review`, target status `escalated`, actor project scope, and non-empty PM reason.

This closes the prior gap where sibling PM issue actions could travel through the generic lifecycle path without an explicit target status.

## Caller Alignment

Existing callers were aligned to the tightened contract:

1. `apps/mutation-seam/validate.py` now sends a PM reason for the resolve-escalated harness step.
2. `apps/operations-web/app/pm-review/approval/page.tsx` now sends `payload.status=escalated` for `re_escalate`.
3. `apps/operations-web/public/pm-review/approval-surface.html` now sends `payload.status=escalated` for `re_escalate`.
4. `apps/operations-web/public/integration-dashboard/index.html` now sends a PM reason for the resolve-escalated demo step.

## Delegation And Orchestration Notes

Two read-only scouts reviewed the next-move selection:

1. Frontend/package scout `019e2c63-f15f-7b31-98fd-bcee35d52175` recommended first attempting the Lane 009 hosted read-only proof and preserving the existing smoke path.
2. Backend/domain scout `019e2c64-2217-75f2-a1ce-bdf6b125b719` identified the safest product tranche as PM escalated-issue disposition hardening inside the existing Class C issue seam.

Codex attempted the Lane 009 hosted smoke first. That proof did not pass, and no hosted pass is claimed:

```text
PM_LIVE_DATA_STEP mutation-seam https://mutation-seam.apexpowerops.com/
PM_LIVE_DATA_FATAL mutation seam schedule projects returned HTTP 500
```

Follow-up read-only probes showed:

1. `GET https://mutation-seam.apexpowerops.com/health` -> `200`,
2. `GET https://mutation-seam.apexpowerops.com/api/v1/schedule/projects` -> `500`,
3. `GET https://mutation-seam.apexpowerops.com/api/v1/reads/approval-queue` -> `200`,
4. `GET https://mutation-seam.apexpowerops.com/api/v1/reads/pm-workfront` -> `404`,
5. `GET https://mutation-seam.apexpowerops.com/api/v1/reads/decision-history?entity_id=__pm_workfront_smoke_noop__&limit=25` -> `200`.

The repo-owned deployed seam smoke also failed read-only with `RESULT FAIL`: `schedule_projects`, `schedule_drivers`, `schedule_tracer`, and `schedule_variance` each returned `500`.

This indicates the public hosted seam is stale or failing relative to the current PM lane stack. The tranche therefore proceeds as local product hardening plus truthful deployment-blocker evidence.

## Files Changed

Backend/domain:

1. `apps/mutation-seam/app/services/mutation_pipeline.py`
2. `apps/mutation-seam/tests/test_pm_issue_disposition.py`
3. `apps/mutation-seam/tests/test_pipeline_integration.py`
4. `apps/mutation-seam/validate.py`

Existing frontend/static callers:

1. `apps/operations-web/app/pm-review/approval/page.tsx`
2. `apps/operations-web/public/pm-review/approval-surface.html`
3. `apps/operations-web/public/integration-dashboard/index.html`

Packet and status:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-010-issue-disposition-semantic-hardening.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-010-issue-disposition-semantic-hardening-handoff.md`

## Validation

Local validation:

```powershell
$env:SEAM_STORE_BACKEND='memory'
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_issue_disposition.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pipeline_integration.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" -q
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/app/services/mutation_pipeline.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/validate.py"
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.approval-context.smoke.spec.ts
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts
```

Results:

1. Focused mutation-seam PM suite passed `26 passed`.
2. `py_compile` passed for the changed mutation-seam modules.
3. Deployed mutation-seam smoke failed read-only with `RESULT FAIL` because public hosted schedule reads returned `500`; this is recorded as deployment drift, not a product-code pass.
4. Operations-web typecheck passed.
5. Operations-web production build passed.
6. Approval-context Playwright smoke passed `2 passed`.
7. PM workfront Playwright smoke passed `1 passed`.

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

Recommended next move: publish this head, allow or trigger hosted mutation-seam and operations-web deployment from the new clean-main head, then rerun the read-only hosted `smoke:pm-live-data` proof. If the public seam still returns `schedule/projects=500` or `pm-workfront=404`, open a bounded hosted-deployment remediation packet before claiming live PM proof.
