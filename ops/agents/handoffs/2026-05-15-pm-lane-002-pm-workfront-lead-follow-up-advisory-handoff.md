# PM Lane 002 Handoff - PM Workfront Lead Follow-Up Advisory

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-002`
Scope: PM runtime product lane with advisory-only AI orchestration proof

## Summary

This tranche advances the PM workfront from passive readiness triage to an advisory-only PM-to-lead follow-up draft loop.

The mutation seam now enriches `/api/v1/reads/pm-workfront` rows with:

1. primary blocking issue ID,
2. blocking issue summaries,
3. row-level `ai_advisory` metadata,
4. deterministic lead follow-up brief text,
5. explicit `mutation_authority: not_admitted`.

Operations Web now lets a PM reveal a row-level lead follow-up draft from `/pm-review/workfront`. The UI does not call any mutation route, does not assign work, does not change issue status, and does not send an autonomous AI action.

## Delegation And Orchestration Notes

Two read-only explorer delegates reviewed the next slice before implementation:

1. Backend explorer `019e2c2c-25c7-7242-8401-c0a10ff44ead` recommended reusing the existing issue return-to-lead authority only as a bounded path and flagged scope risks around permissive issue payloads and project-scope enforcement.
2. Frontend explorer `019e2c2c-3c1b-7c21-a299-c70b88893ed1` recommended the safer first UI pass: deterministic PM-to-lead follow-up drafts with a Playwright mutation-route trap proving the route remains advisory-only.

Codex retained coordinator, reviewer, release-gate, and executor authority for integration, validation, packet authorship, and closeout.

## Files Changed

Backend:

1. `apps/mutation-seam/app/pm_workfront_read_model.py`
2. `apps/mutation-seam/tests/test_pm_workfront_read_model.py`

Frontend:

1. `apps/operations-web/app/pm-review/workfront/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`

Packet and status:

1. `PROJECT_STATUS.md`
2. `ops/agents/packets/draft/2026-05-15-pm-lane-002-pm-workfront-lead-follow-up-advisory.json`
3. `ops/agents/handoffs/2026-05-15-pm-lane-002-pm-workfront-lead-follow-up-advisory-handoff.md`

## Validation

Focused backend validation:

```powershell
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" -q
```

Result: `1 passed` with existing Pydantic v2 deprecation warnings.

Frontend validation:

```powershell
corepack pnpm build
corepack pnpm typecheck
corepack pnpm exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts
```

Results:

1. `next build` passed and prerendered `/pm-review/workfront`.
2. `tsc --noEmit` passed.
3. Focused Playwright smoke passed `1 passed`; the spec traps `**/api/v1/mutations/**` and asserts no mutation call occurs when the lead follow-up draft is opened.

## Guardrails Preserved

1. No SQL or schema migration.
2. No new service admission.
3. No auth or ingress widening.
4. No assignment mutation.
5. No issue status mutation from the PM workfront route.
6. No schedule mutation.
7. No Operations Visibility reopening.
8. No autonomous AI business-state mutation.

## Next Bounded Move

The next PM product slice can either:

1. keep the workfront advisory-only and add PM review sorting or filtered workfront lenses, or
2. admit one explicit user-initiated PM issue disposition loop from the workfront by reusing the existing Class C issue mutation path, with tests that prove idempotency, audit logging, role guard behavior, and no assignment authority widening.
