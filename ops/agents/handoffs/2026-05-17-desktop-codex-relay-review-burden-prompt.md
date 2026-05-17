# Desktop Codex Prompt - Relay Review-Burden Scout

You are Desktop Codex acting as delegated orchestration governor for the non-PM Relay lane under VS Code Codex technical authority.

## Objective

Create a bounded Relay lane handoff that evaluates how Desktop Codex can reduce Jason's AI-to-AI relay burden and VS Code Codex interruption load without admitting autonomous runtime, new MCP services, hosted changes, credentials, or business-state mutation.

## Authority Band

Band A/B only.

## Required Reads

- `docs/operations/APEX-PARALLEL-LANE-ORCHESTRATION-GOVERNANCE-PLAN-2026-05-17.md`
- `ops/agents/handoffs/2026-05-17-desktop-codex-parallel-lane-orchestration-queue.md`
- Recent Desktop Codex executor handoffs in `ops/agents/handoffs/`
- Existing PM lane relay-reduction docs in `docs/operations/`

## Allowed Writes

Write one handoff only:

- `ops/agents/handoffs/2026-05-17-desktop-codex-relay-review-burden-closeout.md`

## Forbidden Writes

- `apps/`
- `packages/`
- `infra/`
- `docs/authority/`
- `PROJECT_STATUS.md`
- `.env*`
- packet JSON unless separately admitted
- MCP, Olares, Render, Vercel, Supabase, or runtime config

## Allowed Work

1. Identify where Jason currently acts as the relay between agents.
2. Identify where VS Code Codex review is being requested too early.
3. Propose summary shapes that make sidecar output decision-ready.
4. Recommend one small next packet for orchestration efficiency.
5. Classify capability gaps honestly.

## Forbidden Work

1. Do not admit autonomous queue ownership.
2. Do not add or configure MCP services.
3. Do not change Olares runtime or hosted services.
4. Do not touch credentials.
5. Do not alter PM business state.
6. Do not stage, commit, push, publish status, or fast-forward Olares.

## Validation

Run:

```powershell
git diff --check -- ops/agents/handoffs/2026-05-17-desktop-codex-relay-review-burden-closeout.md
```

## Closeout Status

Return exactly one of:

- `READY_FOR_VSCODE_REVIEW`
- `READY_FOR_JASON_DECISION`
- `BLOCKED_CAPABILITY_GAP`
- `ABORTED_SCOPE_WIDENING`

## Stop Conditions

Stop if the work requires autonomous runtime, MCP admission, Olares changes, credentials, production services, PM business-state changes, or Jason manually relaying raw technical context.
