# PM Lane 136 - Import Candidate Approval Persistence Schema And Adapter Handoff

## Purpose

PM Lane 136 implements the first repo-local Project Miner import-candidate approval persistence path.

The lane admits only the dedicated approval-record storage boundary: `seam.pm_import_candidate_approvals`, an insert-only adapter, a PM-only mutation route, stable idempotent replay, one linked audit append per accepted insert, and table-backed readback classification. It does not import project/work rows and does not deploy or apply live SQL.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `25167ccbbbefaa2c46e201e031ed81d61569d10b`
- Prior lane: PM Lane 135, Current PM Next Actions and Guardrails Body Controls
- Hosted floor: PM Lane 041C accepted closed; hosted mutation-seam read surface and paired PM intake smoke were green before this local-only lane.
- Supabase guidance checked: Row Level Security docs confirm raw SQL-created tables should explicitly enable RLS and grant only needed roles.

## Implemented Scope

- Added `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql`.
- Added the dedicated `seam.pm_import_candidate_approvals` table definition with approval identity, replay identity, audit identity, PM decision payload, validation result, indexes, RLS, anon/authenticated revokes, and update/delete rejection triggers.
- Added `ApprovalPersistenceStore` for insert-only approval row writes and a transaction path that inserts the approval record plus linked audit row together for Supabase-backed storage.
- Added memory-store parity for `pm_import_candidate_approvals` so focused tests can run without touching live Supabase.
- Added `POST /api/v1/mutations/project-import-approvals` behind PM role, online source, Class C, deterministic entity ID, contract validation, and strict replay checks.
- Added stable idempotent replay behavior returning the original `mutation_id` and `audit_event_id`.
- Added readback classification for no record, current approved, stale, returned, and rejected approval records using the approval table as the source of current status.
- Hardened shared audit logging so existing mutation-pipeline writes preserve `entity_type`.
- Updated PM workflow/status docs and this packet/handoff.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/mutation-seam/app/audit/logger.py`
- `apps/mutation-seam/app/db/memory_store_original.py`
- `apps/mutation-seam/app/db/supabase_store.py`
- `apps/mutation-seam/app/main.py`
- `apps/mutation-seam/app/project_import_approval_persistence.py`
- `apps/mutation-seam/app/routers/project_import_approvals.py`
- `apps/mutation-seam/app/services/mutation_pipeline.py`
- `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql`
- `apps/mutation-seam/tests/conftest.py`
- `apps/mutation-seam/tests/test_pipeline_integration.py`
- `apps/mutation-seam/tests/test_project_import_approval_persistence.py`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-136-import-candidate-approval-persistence-schema-adapter.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-136-import-candidate-approval-persistence-schema-adapter-handoff.md`

## Not Allowed

- No live Supabase SQL application.
- No hosted Supabase row write.
- No Render, Vercel, or Olares deployment.
- No operations-web POST wiring, approval button, or hosted parity claim.
- No project import mutation.
- No project, workpackage, task, apparatus, issue, assignment, schedule, status, durable field record, production tracking, workbook, or import rows.
- No generic mutation-pipeline registration for `pm_import_candidate_approval`.
- No workbook macro execution or workbook writeback.
- No service creation, DNS/auth/ingress/secret change, fixture replay into live data, work authorization, field release, live work order creation, or autonomous AI business-state mutation.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile apps/mutation-seam/app/project_import_approval_persistence.py apps/mutation-seam/app/db/supabase_store.py apps/mutation-seam/app/audit/logger.py apps/mutation-seam/app/services/mutation_pipeline.py
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_project_import_approval_persistence.py apps/mutation-seam/tests/test_project_import_approval_contract.py apps/mutation-seam/tests/test_project_import_approval_storage_plan.py apps/mutation-seam/tests/test_project_import_admission_plan.py apps/mutation-seam/tests/test_project_import_candidate.py apps/mutation-seam/tests/test_pipeline_integration.py
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-136-import-candidate-approval-persistence-schema-adapter.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- `py_compile` passed for the touched backend modules.
- Focused backend tests passed with `32 passed, 21 warnings`.
- Packet JSON parse returned `packet-json-ok`.
- `git diff --check` passed.
- `git diff --cached --check` passed after scoped staging.

## Sidecar Result

The read-only sidecar audit found no blocking boundary findings. It confirmed the diff stays inside the dedicated approval table, PM-only route, stable replay, one-audit-append, no-import, no-frontend-POST, and no-live-deploy boundary.

The sidecar noted two low residual risks: shared audit plumbing and insert-only enforcement by convention. Both were addressed before closeout: existing mutation-pipeline tests now assert audit `entity_type`, and the approval migration includes DB update/delete rejection triggers.

## Next Recommended Lane

`PM Lane 137 - Approval Persistence Hosted Application Gate And Status Surfacing`

That next lane should be split into tightly bounded pieces: first a hosted application gate or executor handoff for applying only this migration and redeploying only the existing mutation-seam service, and separately a read-only status surface that exposes approval persistence state without adding a frontend approval POST. Project import, workpackage/task/apparatus writes, assignment, schedule, status, production tracking, workbook macros/writeback, and autonomous AI business-state mutation remain blocked.
