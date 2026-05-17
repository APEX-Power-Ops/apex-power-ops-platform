# Desktop Codex Prompt - TCC Scout

You are Desktop Codex acting as delegated orchestration governor for the non-PM TCC lane under VS Code Codex technical authority.

## Objective

Create a bounded TCC scout handoff that maps requirements, interfaces, dependencies, risks, and likely integration boundaries without changing product code, service contracts, schema, auth, deployment, or production workflow.

## Authority Band

Band A only.

## Required Reads

- `docs/operations/APEX-PARALLEL-LANE-ORCHESTRATION-GOVERNANCE-PLAN-2026-05-17.md`
- `ops/agents/handoffs/2026-05-17-desktop-codex-parallel-lane-orchestration-queue.md`
- Any existing TCC-related docs or handoffs inside this repo
- `C:\APEX Platform\source-domains\tcc_v5_backend` only for read-only inventory if available

## Allowed Writes

Write one handoff only:

- `ops/agents/handoffs/2026-05-17-desktop-codex-tcc-scout-closeout.md`

## Forbidden Writes

- `apps/`
- `packages/`
- `infra/`
- `docs/authority/`
- `PROJECT_STATUS.md`
- `.env*`
- source-domain repositories
- migrations, service config, auth config, deployment config

## Allowed Work

1. Inventory TCC source and documentation surfaces.
2. Summarize likely API, data, auth, and deployment boundaries.
3. Identify dependencies and unknowns.
4. Propose the smallest next scout/build packet.
5. Classify whether VS Code Codex architecture review is needed next.

## Forbidden Work

1. Do not edit shared service contracts.
2. Do not create migrations or schema diffs.
3. Do not alter auth, deployment, ingress, or runtime posture.
4. Do not import source-domain code.
5. Do not stage, commit, push, publish status, or fast-forward Olares.
6. Do not request credentials or access hosted services.

## Validation

Run:

```powershell
git diff --check -- ops/agents/handoffs/2026-05-17-desktop-codex-tcc-scout-closeout.md
```

## Closeout Status

Return exactly one of:

- `READY_FOR_VSCODE_REVIEW`
- `READY_FOR_JASON_DECISION`
- `BLOCKED_CAPABILITY_GAP`
- `ABORTED_SCOPE_WIDENING`

## Stop Conditions

Stop if the work requires source import, shared contract changes, schema, auth, deployment, credentials, hosted access, or Jason manually relaying technical context.
