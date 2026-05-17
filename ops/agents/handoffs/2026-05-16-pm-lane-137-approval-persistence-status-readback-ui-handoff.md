# PM Lane 137 - Approval Persistence Status Readback And UI Surfacing Handoff

## Purpose

PM Lane 137 makes the approval-persistence state visible without opening a browser write path.

The lane adds `GET /api/v1/reads/project-import-approval-status`, surfaces that status inside `/pm-review/import-intake`, and includes the readback in local exports. It does not approve a candidate, persist from the UI, import project rows, apply hosted SQL, or deploy hosted services.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `97a97b3554ec7d17b6f91a2e5f678e4677e114e5`
- Prior lane: PM Lane 136, Import Candidate Approval Persistence Schema And Adapter Implementation
- Hosted floor: PM Lane 041C accepted closed; hosted mutation-seam read surface and paired PM intake smoke were green before this local-only status-readback lane.

## Implemented Scope

- Added `GET /api/v1/reads/project-import-approval-status`.
- Extended approval status classification with read route, storage-source, approval-storage availability, and unavailable-storage classification.
- Preserved table-backed approval status as the current-status source; audit log remains evidence only.
- Added focused tests for missing record, current approved record, route readback, and storage-unavailable classification.
- Updated `/pm-review/import-intake` to fetch the new read seam alongside the existing candidate, admission-plan, approval-contract, and storage-plan reads.
- Added Approval Status Readback panels to the Admission and Approval Contract area and Approval Persistence Readiness area.
- Added readback metadata to the Approval Preview JSON, PM Brief export, and Executor Handoff export.
- Authored the next bounded hosted application gate prompt for a separate executor lane.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/mutation-seam/app/project_import_approval_persistence.py`
- `apps/mutation-seam/app/routers/reads.py`
- `apps/mutation-seam/tests/test_project_import_approval_persistence.py`
- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-137-approval-persistence-status-readback-ui.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-137-approval-persistence-status-readback-ui-handoff.md`
- `ops/agents/handoffs/2026-05-16-pm-lane-138-approval-persistence-hosted-application-gate-executor-copy-paste-prompt.md`

## Not Allowed

- No live Supabase SQL application.
- No hosted Supabase row write.
- No Render, Vercel, or Olares deployment.
- No operations-web approval button or approval POST wiring.
- No project import mutation.
- No project, workpackage, task, apparatus, issue, assignment, schedule, status, durable field record, production tracking, workbook, or import rows.
- No workbook macro execution or workbook writeback.
- No service creation, DNS/auth/ingress/secret change, fixture replay into live data, work authorization, field release, live work order creation, or autonomous AI business-state mutation.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_project_import_approval_persistence.py
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-137-approval-persistence-status-readback-ui.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- Focused backend approval-persistence tests passed with `9 passed`.
- `py_compile` passed for approval persistence and the reads router.
- `operations-web` typecheck passed.
- `operations-web` production build passed.
- Focused Playwright smoke `browser-shell.pm-import-intake.smoke.spec.ts` passed with `1 passed`.
- Packet JSON parse returned `packet-json-ok`.
- `git diff --check` passed.

## Sidecar Result

The read-only hosted-gate sidecar recommended `PM Lane 138 - Approval Persistence Hosted Application Gate`.

That executor lane should apply only `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql`, redeploy only the existing Render service `apex-platform-mutation-seam`, prove schema/trigger presence, prove hosted route registration, and rerun the hosted mutation-seam plus paired PM-intake smokes.

It must not add UI POST wiring, create approval records through a live smoke, import project/work rows, create services, rotate secrets unless the current DSN is broken, or store secret values in repo artifacts.

## Next Recommended Lane

`PM Lane 138 - Approval Persistence Hosted Application Gate`

That lane should be delegated only when the executor has authenticated access to Supabase/Render through the existing safe secret boundaries. It is a hosted application gate, not project import and not UI activation.
