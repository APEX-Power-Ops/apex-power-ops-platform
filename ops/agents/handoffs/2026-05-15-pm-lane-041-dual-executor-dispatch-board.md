# PM Lane 041 Dual Executor Dispatch Board

Date: 2026-05-15
Status: Ready for authenticated hosted executors
Coordinator: Codex, repo technical authority and PM lane coordinator

## Purpose

This board removes Jason from the AI-to-AI relay loop for the hosted parity step. It points each executor at one bounded handoff and keeps the coordinator decision visible in the repo.

## Current Dispatch Wrapper

PM Lane 076 is the current top-level copy/paste wrapper for this board after the local PM intake workbench through PM Lane 119:

```text
ops/agents/handoffs/2026-05-15-pm-lane-076-hosted-pm-intake-parity-executor-copy-paste-prompt.md
```

Current source floor:

```text
clean-main e89cabb7a1226ceeb3a431b25147d889402ea1a3
```

Use Lane 076 when assigning the hosted parity step to Desktop Codex, Claude Code, or another authenticated executor so the executor can select Vercel, Render, both, or credential-unavailable closeout without Jason relaying packet context manually.

## Dispatch Map

| Lane | Owner Surface | Handoff | Goal | Status |
| --- | --- | --- | --- | --- |
| 041A | Vercel-authenticated executor | `ops/agents/handoffs/2026-05-15-pm-lane-041a-vercel-operations-web-promotion-handoff.md` | Promote current operations-web so `/pm-review/import-approval-readiness` and `/pm-review/import-intake` are hosted | ready |
| 041B | Render-authenticated executor | `ops/agents/handoffs/2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification-handoff.md` | Redeploy existing mutation-seam or classify PM intake read blocker | ready |

## Current Hosted Split

1. `https://operations.apexpowerops.com/pm-review/import-candidate` passes.
2. `https://operations.apexpowerops.com/pm-review/import-admission-plan` passes.
3. `https://operations.apexpowerops.com/pm-review/import-approval-readiness` returns `404`.
4. `https://operations.apexpowerops.com/pm-review/import-intake` returns `404`.
5. `https://mutation-seam.apexpowerops.com/health` returns `200`.
6. Hosted mutation-seam OpenAPI is missing all four current PM intake reads.
7. Hosted mutation-seam returns `404` for all four current PM intake reads.
8. Hosted mutation-seam schedule reads still return `500`.

## Sequencing

The two executor lanes are independent enough to run in parallel.

If only one hosted credential surface is available:

1. run 041A alone if Vercel access is available,
2. run 041B alone if Render access is available,
3. record the unavailable surface explicitly instead of blocking silently.

Full PM intake hosted parity requires both:

1. operations-web serving the Lane 040 route and the Lane 043 workbench route,
2. mutation-seam serving the four current PM intake reads.

## Coordinator Acceptance

Coordinator accepts the hosted parity step only when one of these is true:

1. paired hosted PM intake smoke is green, or
2. remaining red checks are precisely classified with owner, blocker type, and next packet recommendation.

Each executor must return a completed closeout handoff using:

```text
ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md
```

Expected closeout paths:

```text
ops/agents/handoffs/2026-05-15-pm-lane-041a-vercel-operations-web-promotion-closeout-handoff.md
ops/agents/handoffs/2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification-closeout-handoff.md
```

## Guardrails

No lane may:

1. create a new hosted service,
2. change DNS,
3. widen auth or ingress,
4. print or rotate secrets,
5. run SQL writes,
6. migrate schema,
7. replay fixtures,
8. persist approval,
9. import project rows,
10. mutate assignment, schedule, status, issue, task, workpackage, project, or autonomous AI business state.
