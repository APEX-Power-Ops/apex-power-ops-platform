# PM Hosted Executor Closeout Template

Use this template when closing PM Lane 041A, PM Lane 041B, or another hosted PM parity executor lane.

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
11. other deployment failure.

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
