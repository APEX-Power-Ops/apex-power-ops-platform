# PM Lane 139 - Approval Persistence Hosted Gate Smoke And Closeout Contract Tightening Handoff

## Purpose

PM Lane 139 tightens the hosted application gate evidence for PM Lane 138 before a credentialed executor applies hosted migration 003.

The lane updates the standard hosted smokes so they verify the approval-status GET route and approval POST OpenAPI registration without sending a live approval POST. It also updates the hosted executor closeout template so PM Lane 138 can apply exactly migration 003 without conflicting with the older read-only hosted-parity guardrails.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `ba653cadb7d3b2f671ea757540879cce9873e142`
- Prior lane: PM Lane 137, Approval Persistence Status Readback And UI Surfacing
- Hosted gate prepared: PM Lane 138, Approval Persistence Hosted Application Gate

## Implemented Scope

- Extended `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --include-pm-intake` to require:
  - OpenAPI path registration for `GET /api/v1/reads/project-import-approval-status`,
  - OpenAPI path registration for `POST /api/v1/mutations/project-import-approvals`,
  - method-level proof for `GET` on the approval-status read,
  - method-level proof for `POST` on the approval mutation route,
  - hosted approval-status readback with approval storage available and no audit-log-only status dependency.
- Extended `apps/operations-web/scripts/smoke-pm-intake-hosted.mjs` with the same approval-status GET and approval POST OpenAPI registration proof.
- Preserved the live-safety boundary: the smokes do not send a live approval POST and do not create an approval row.
- Updated `ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md` with a PM Lane 138-specific migration-003 section.
- Updated the PM Lane 138 executor prompt so credentialed executors use the tightened hosted proof and closeout template.
- Updated PM lane status and operating docs to show the hosted-gate evidence contract.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
- `apps/operations-web/scripts/smoke-pm-intake-hosted.mjs`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`
- `ops/agents/handoffs/2026-05-16-pm-lane-138-approval-persistence-hosted-application-gate-executor-copy-paste-prompt.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-139-approval-persistence-hosted-gate-smoke-closeout-contract.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-139-approval-persistence-hosted-gate-smoke-closeout-contract-handoff.md`

## Not Allowed

- No live Supabase SQL application.
- No Render, Vercel, or Olares deployment.
- No secret access, secret print, secret rotation, or secret storage in repo.
- No live approval POST smoke or approval row creation.
- No operations-web approval button or frontend approval POST wiring.
- No project import mutation.
- No project, workpackage, task, apparatus, issue, assignment, schedule, status, durable field record, production tracking, workbook, or import rows.
- No workbook macro execution or workbook writeback.
- No service creation, DNS/auth/ingress change, fixture replay into live data, work authorization, field release, live work order creation, or autonomous AI business-state mutation.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --help
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node --check scripts/smoke-pm-intake-hosted.mjs
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-139-approval-persistence-hosted-gate-smoke-closeout-contract.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- `py_compile` passed for `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`.
- `smoke_deployed_mutation_seam.py --help` returned usage successfully.
- `node --check scripts/smoke-pm-intake-hosted.mjs` passed through `corepack pnpm --filter @apex/operations-web`.
- Packet JSON parse returned `packet-json-ok`.
- `rg` evidence check found approval-status GET, approval POST OpenAPI registration, migration-003 guardrails, and PM Lane 138/139 references across the scripts, template, prompt, packet, and handoff.
- `git diff --check` passed.
- `git diff --cached --check` passed after scoped staging.

## Sidecar Result

The read-only sidecar recommended this orchestration slice instead of more UI readback work. It found the UI readback covered, and identified the best no-credential accelerator as tightening the smoke/template evidence contract for the PM Lane 138 credentialed hosted gate.

## Next Recommended Lane

`PM Lane 138 - Approval Persistence Hosted Application Gate`

Run that lane only through an authenticated hosted executor with access to the approved non-git secret boundary and Render/Supabase sessions. It may apply only migration 003 and redeploy only the existing Render mutation-seam service. It must not send a live approval POST, create approval rows through smoke, import project rows, wire frontend approval controls, create services, expose secrets, or mutate production business state beyond the admitted schema gate.
