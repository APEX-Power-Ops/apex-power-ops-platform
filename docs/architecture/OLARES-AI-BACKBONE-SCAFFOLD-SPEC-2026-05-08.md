# Olares AI Backbone Scaffold Specification

Date: 2026-05-08
Status: Active bounded implementation specification
Scope: exact first-pass design and scaffold outputs for the admitted Olares AI backbone

## Purpose

This specification translates the current authority stack into a concrete scaffold plan.

It is intentionally narrower than a general implementation roadmap.

Use it to drive a first-pass design and scaffold session that prepares the admitted backbone surfaces without widening runtime, trust, or hosting boundaries.

## First-Pass Outcome

The first pass is complete when the repo has a coherent shell for the admitted backbone, not when the whole AI platform is complete.

Expected first-pass outcome:

1. the minimal MCP trio surfaces are structurally consistent,
2. compose and env contracts are scaffolded or normalized,
3. Claude and Codex session wiring is documented against the same boundary,
4. the first staging-shell chart surface is scaffolded,
5. canary and promotion guardrail expectations are written down where implementation can follow.

## Allowed Output Classes

### A. MCP trio scaffold alignment

Allowed outputs:

1. README and contract files for `services/mcp/apex-fs/`, `services/mcp/apex-db/`, and `services/mcp/apex-jobs/`,
2. non-destructive skeleton alignment for package metadata, startup surfaces, env variable expectations, and health-check descriptions,
3. test-shell or fixture-shell surfaces that validate the admitted trio contract without adding new service families.

### B. Dev-zone scaffold surfaces

Allowed outputs:

1. `infra/compose.dev.yml` normalization or scaffold completion for admitted surfaces,
2. `.env.dev.template` contract completion,
3. comments or contract notes that make sandbox-only posture explicit.

### C. Session and operator wiring

Allowed outputs:

1. `docs/operations/OLARES-VSCODE-BUILD-SESSION-PROMPT.md`,
2. `docs/operations/CODEX-AI-BACKBONE-FIRST-PASS-EXECUTION-BRIEF-2026-05-08.md`,
3. bounded repo-owned backbone briefing notes under `docs/operations/`,
4. current authority references that keep the admitted backbone wiring explicit.

### D. Staging-shell scaffold

Allowed outputs:

1. `infra/olares/forms-engine/Chart.yaml`,
2. `infra/olares/forms-engine/OlaresManifest.yaml`,
3. chart README or values skeleton,
4. OIDC, middleware, and `env=host` expectations written as shell-level contract, not claimed runtime proof.

### E. Guardrail shell surfaces

Allowed outputs:

1. `tests/canary/` scaffold additions,
2. `tools/` scripts or stubs that enforce admitted contract checks,
3. doc-visible evidence paths and expected validation commands.

## Explicit Non-Goals For This Spec

The first pass must not:

1. add new orchestration services beyond the admitted trio,
2. implement `ai_tasks` as the active queue owner,
3. install or configure new Olares services,
4. widen public or authenticated exposure,
5. change business workflows in `apps/`,
6. claim complete staging graduation.

## Acceptance Criteria

The first pass should satisfy all of the following:

1. every new scaffold file names its boundary and deferred work honestly,
2. every new runtime-facing shell still routes trust and promotion through `apex-jobs`,
3. the admitted trio remains the only MCP family in scope,
4. the staging shell stays forms-engine-first,
5. the validation path is focused on diff hygiene, contract checks, and the smallest executable assertions available.

## Suggested Execution Order

1. align or document the three MCP services,
2. align compose and env contracts,
3. align `.claude` and session-brief surfaces,
4. scaffold the forms-engine chart shell,
5. write canary and hardening hooks,
6. stop before widening into runtime rollout.

## Follow-On After The First Pass

After the first scaffold pass, the next truthful lanes are:

1. execute the adjacent backbone hardening slice,
2. implement the smallest missing contract surfaces exposed by the scaffold diff,
3. validate one bounded shell path locally,
4. admit any broader orchestration expansion only through a separate decision packet.