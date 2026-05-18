# PM Hosted Executor Closeout Template

Use this template when closing PM Lane 041A, PM Lane 041B, PM Lane 076-selected execution, PM Lane 308, or another hosted PM parity executor lane.

Do not paste secrets. Do not summarize a failed command as success. If a hosted credential, deployment action, or validation command is unavailable, say that directly.

## Header

Packet:

Executor:

Date:

Status:

Source repository:

Source branch:

Source commit tested:

Hosted surface:

## Scope Executed

Describe only the bounded scope actually executed.

Expected examples:

1. Vercel existing-project promotion for operations-web.
2. Render existing-service redeploy/classification for mutation-seam.
3. Read-only hosted proof without deployment.
4. PM Lane 138 approval-persistence hosted gate: apply only migration 003 and redeploy only the existing Render mutation-seam service.

## Changed Files

List all repo files changed by the executor.

If none:

```text
No repo files changed.
```

## Hosted Action Evidence

Record only non-secret hosted evidence.

For Vercel:

1. project name or label,
2. deployment id,
3. production alias,
4. source commit,
5. route build evidence for `/pm-review/import-approval-readiness`,
6. route build evidence for `/pm-review/import-intake`.

For Render:

1. service name,
2. repository and branch,
3. working directory,
4. deployment id or timestamp,
5. deployed commit,
6. non-secret env key presence,
7. build/start/health metadata,
8. log-backed blocker classification if validation remains red.

For PM Lane 308 actuals-route redeploy:

1. exact service name `apex-platform-mutation-seam`,
2. repository and branch,
3. working directory,
4. deployment id or timestamp,
5. deployed commit,
6. proof that OpenAPI now includes or still omits `/api/v1/mutations/temp-power-actuals-capture-reviews`,
7. proof that OpenAPI now includes or still omits `/api/v1/reads/temp-power-actuals-capture-review-status`,
8. exact result of the bounded hosted smoke using `--include-temp-power-actuals-review`,
9. whether custom domain and Render hostname matched or diverged after redeploy,
10. log-backed blocker classification if the actuals routes still remain absent.

For PM Lane 138 approval-persistence hosted gate:

1. exact migration file applied: `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql`,
2. schema proof tuple for the approval table and insert-only triggers,
3. existing Render service name `apex-platform-mutation-seam`,
4. confirmation that `SEAM_DATABASE_URL` was present without printing it,
5. OpenAPI proof for `POST /api/v1/mutations/project-import-approvals`,
6. OpenAPI proof for `GET /api/v1/reads/project-import-approval-status`.

## Validation Commands And Results

Paste each command exactly, then record the exact result.

Required for PM Lane 041A:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com
```

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Required for PM Lane 041B:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Required for PM Lane 308:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-temp-power-actuals-review
```

Optional disambiguation for PM Lane 308 only when the custom domain still appears stale:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://apex-platform-mutation-seam.onrender.com --include-temp-power-actuals-review
```

Required for PM Lane 138:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Both PM Lane 138 hosted smokes must prove the approval-status GET route and approval POST OpenAPI registration. They must not send a live approval POST or create an approval row.

## Final Verdict

Choose one:

```text
PASS
PARTIAL_PASS_WITH_REMAINING_BLOCKER
BLOCKED_CREDENTIAL_UNAVAILABLE
BLOCKED_HOSTED_METADATA_MISMATCH
BLOCKED_PRODUCT_CODE_ISSUE
BLOCKED_SCHEMA_OR_DSN_OR_PERMISSION
BLOCKED_OTHER
```

## Remaining Blocker Classification

If not `PASS`, classify the remaining blocker.

Allowed classifications:

1. Vercel auth unavailable,
2. Render auth unavailable,
3. stale deploy,
4. hosted metadata mismatch,
5. DSN issue,
6. schema issue,
7. permission issue,
8. runtime import/startup issue,
9. product-code issue,
10. route promotion incomplete,
11. actuals routes still absent after redeploy,
12. other deployment failure.

## Guardrails Confirmed

Confirm each item:

1. no new hosted service,
2. no DNS change,
3. no auth widening,
4. no ingress widening,
5. no secret value printed or committed,
6. no secret rotation,
7. no SQL write,
8. no schema migration,
9. no fixture replay,
10. no approval persistence,
11. no import mutation,
12. no assignment, schedule, status, issue, task, workpackage, project, or autonomous AI business-state mutation.

For PM Lane 138 only, replace items 7, 8, and 10 with these narrower confirmations:

1. only migration 003 was applied,
2. no SQL other than migration 003 was executed,
3. approval persistence was admitted only as the dedicated table/schema gate and no approval row was created,
4. no UI approval POST wiring, browser approval button, live POST smoke, project import, assignment, schedule, status, issue, task, workpackage, project, production tracking, or autonomous AI business-state mutation occurred.

## Coordinator Recommendation

Recommend exactly one next action:

```text
ACCEPT_AND_CLOSE
ACCEPT_PARTIAL_AND_RUN_OTHER_LANE
REDELEGATE_WITH_FIX
OPEN_PRODUCT_CODE_PACKET
OPEN_DEPLOYMENT_ACCESS_PACKET
STOP_FOR_STAKEHOLDER_EXCEPTION
```
