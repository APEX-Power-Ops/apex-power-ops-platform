# PM Lane 076 Copy/Paste Prompt - Hosted PM Intake Parity Executor Dispatch Binder

You are executing PM Lane 076 for Apex Power Ops as an authenticated hosted parity executor.

Repository:

```text
C:\APEX Platform\apex-power-ops-platform
```

Current source floor:

```text
clean-main e89cabb7a1226ceeb3a431b25147d889402ea1a3
```

Preferred executor for this run:

```text
Desktop Codex, using whichever authenticated Vercel and/or Render credential surface is available in that application.
```

Authoritative dispatch packet:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-15-pm-lane-076-hosted-pm-intake-parity-executor-dispatch-refresh.json
```

Authoritative dispatch handoff:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-076-hosted-pm-intake-parity-executor-dispatch-refresh-handoff.md
```

Closeout template:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\templates\pm-hosted-executor-closeout-template.md
```

## First Step

Inspect your available hosted credential surface:

1. If you have authenticated Vercel access for the existing operations-web project, execute PM Lane 041A.
2. If you have authenticated Render access for the existing `apex-platform-mutation-seam` service, execute PM Lane 041B.
3. If you have both, you may execute both lanes and return two closeouts.
4. If you have neither, stop and create a credential-unavailable closeout using the template.

Do not ask Jason to relay technical details that are already in the repo handoffs.
Do not edit local PM Lane 120 files; the coordinator is continuing local PM work separately while this hosted parity lane runs.

## Lane 041A - Vercel Operations-Web Promotion

Read:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-041a-vercel-operations-web-promotion-handoff.md
```

Goal:

```text
Promote current clean-main to the existing operations-web production alias so these routes are hosted:
https://operations.apexpowerops.com/pm-review/import-approval-readiness
https://operations.apexpowerops.com/pm-review/import-intake
```

Use the existing Vercel project and existing production alias only.

Required validation:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com
```

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Closeout path:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-041a-vercel-operations-web-promotion-closeout-handoff.md
```

## Lane 041B - Render Mutation-Seam Redeploy Or Classification

Read:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification-handoff.md
```

Goal:

```text
Redeploy the existing Render service apex-platform-mutation-seam from current clean-main or classify why hosted PM intake reads remain missing.
```

Target reads:

```text
https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-candidate
https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-admission-plan
https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-approval-contract
https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-approval-storage-plan
```

Use the existing Render service only.

Required validation:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Closeout path:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification-closeout-handoff.md
```

## Hard Guardrails

Do not:

1. create a new Vercel project,
2. create a new Render service,
3. change DNS,
4. widen auth or ingress,
5. disclose or rotate secrets,
6. run SQL writes,
7. migrate schema,
8. replay fixtures,
9. change product code unless the coordinator opens a new packet,
10. add backend endpoints,
11. persist approval,
12. import project rows,
13. run workbook macros,
14. write back to workbooks,
15. mutate assignments, schedules, statuses, issues, tasks, workpackages, projects, apparatus, field records, production tracking, or autonomous AI business state.

## Closeout Rules

Use the hosted executor closeout template exactly.

Record:

1. selected lane,
2. source branch and commit tested,
3. non-secret hosted action evidence,
4. exact validation commands and results,
5. final verdict,
6. remaining blocker classification if any,
7. guardrail confirmations,
8. one coordinator recommendation.

Commit and push only scoped closeout/status updates. Preserve unrelated working-tree residue. Do not use destructive git commands.
