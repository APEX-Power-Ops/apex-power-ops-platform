# Codex AI Backbone First-Pass Execution Brief

Date: 2026-05-08
Status: Active bounded execution brief
Scope: Codex-only first-pass design and scaffold authoring for the admitted Olares AI backbone

## Role

You are Codex operating as a bounded scaffold author, not as the runtime or promotion controller.

Your job is to design and scaffold the first 20-30% of the admitted AI backbone without widening the admitted runtime, queue, network, or hosting boundary.

## Read First

1. `docs/architecture/OLARES-AI-ORCHESTRATION-DECISION-SURFACE-2026-05-07.md`
2. `docs/authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md`
3. `docs/architecture/OLARES-AI-BACKBONE-SCAFFOLD-SPEC-2026-05-08.md`
4. `docs/architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md`
5. `docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`

## Primary Objective

Produce the first-pass scaffold for the admitted backbone around:

1. `services/mcp/apex-fs/`
2. `services/mcp/apex-db/`
3. `services/mcp/apex-jobs/`
4. `infra/compose.dev.yml`
5. `.env.dev.template`
6. `docs/operations/OLARES-VSCODE-BUILD-SESSION-PROMPT.md`
7. `docs/architecture/OLARES-AI-BACKBONE-SCAFFOLD-SPEC-2026-05-08.md`
8. `infra/olares/forms-engine/`
9. `tests/canary/`
10. bounded supporting docs under `docs/`

## Hard Constraints

You must not:

1. add new MCP services,
2. promote `ai_tasks` into the active queue controller,
3. install or assume Ollama, Dify, n8n, Open WebUI, or Qdrant,
4. widen public ingress or auth scope,
5. change Supabase schema or business logic in `apps/`,
6. claim completion beyond scaffold readiness.

## Allowed Work

You may:

1. scaffold directories, metadata, and config shells,
2. write README and contract files,
3. add skeleton compose and chart definitions,
4. add bounded contract tests or canary stubs,
5. normalize developer-facing configuration where the authority docs already admit it.

## Required Output Shape

Every scaffolded surface should make these points obvious:

1. what it owns,
2. what it depends on,
3. what remains deferred,
4. what validation is expected,
5. whether it is sandbox-only, host-only, or not yet execution-complete.

## Parallel Coordination Rule

Assume a parallel hardening lane may be authoring docs or tests around:

1. `apex-jobs` env tagging,
2. promotion refusal and positive-gate helper-backed proof,
3. provenance metadata,
4. MCP boundary rules,
5. canary evidence requirements.

Do not take ownership of those hardening semantics beyond the minimum documentation needed for your scaffold outputs.

## Current Alignment Note

Packet `2026-05-13-olares-dev-residency-786` is the current completed first coordinator-owned two-lane rehearsal floor.

Packet `2026-05-13-olares-dev-residency-791` is the current helper-backed positive-gate promotion proof floor.

Treat both as preserved hardening inputs when authoring scaffold outputs; do not restate them as unresolved or future-first proof work.

## Done Definition

Your first pass is done when:

1. the admitted backbone surfaces have coherent scaffold structure,
2. the repo has a usable shell for later implementation,
3. the boundary remains narrow and truthful,
4. no file implies a wider orchestration rollout than the authority stack admits.