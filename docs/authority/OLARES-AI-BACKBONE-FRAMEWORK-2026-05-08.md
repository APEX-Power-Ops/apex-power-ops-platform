# Olares AI Backbone Framework

Date: 2026-05-08
Status: Active repo-owned authority surface
Scope: bounded orchestration-backbone design, scaffold-authoring, and adjacent hardening rules for the Olares-first AI lane

## Purpose

This document is the current authority for the first bounded orchestration-backbone authoring lane.

It answers a narrower question than the general Olares workspace framework and AI orchestration decision surface:

1. what the admitted AI backbone actually is right now,
2. what Codex may do in a first 20-30% design and scaffold pass,
3. what must remain outside that pass,
4. which adjacent hardening slice may run in parallel without reopening broader orchestration expansion.

Use this file when the question is how to let Codex or another bounded authoring agent design and scaffold the backbone without accidentally admitting a wider runtime, queue, or hosting model.

## Authority Order For This Lane

Use this order when documents conflict for the bounded backbone lane:

1. `OLARES-AI-ORCHESTRATION-DECISION-SURFACE-2026-05-07.md`
2. this file
3. `../architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md`
4. `OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
5. `OLARES-BUILD-GUIDE.md`
6. `../../plan/infrastructure-olares-full-implementation-roadmap-1.md`
7. packet and handoff evidence under `ops/agents/`

## Current Backbone Definition

The admitted AI backbone is still intentionally small.

Its current controlling surfaces are:

1. `services/mcp/apex-fs/`
2. `services/mcp/apex-db/`
3. `services/mcp/apex-jobs/`
4. `tools/ai/run-minimal-mcp-trio.ps1`
5. `tools/ai/run-minimal-mcp-trio.sh`
6. `tools/ai/verify_minimal_mcp_trio.py`
7. `tools/ai/run-olares-hold-boundary-check.ps1`
8. `tools/ai/run-olares-hold-boundary-check.sh`
9. `tests/canary/mcp-contract/`
10. the `apex-jobs` env-tag and promotion gate behavior

This backbone is not a generic orchestration platform.

It is the currently admitted trust and control layer for:

1. bounded filesystem access,
2. bounded database read access,
3. run-ledger and promotion evidence,
4. truthful operator verification.

## First-Pass Codex Admission

Codex is admitted for first-pass design and scaffold authoring only.

That means Codex may:

1. author and refine directory-level scaffold docs,
2. scaffold non-destructive config and contract files,
3. write skeleton implementation surfaces that stay inside the already-admitted MCP trio and staging-shell boundary,
4. add doc-level and test-level contract wiring for the admitted backbone.

That does not mean Codex may:

1. redefine the runtime or promotion controller,
2. replace packet and handoff governance with autonomous queueing,
3. admit new orchestration services,
4. widen network exposure or auth posture,
5. imply that scaffolded surfaces are end-to-end complete.

## Codex-Allowed First-Pass Surfaces

The first 20-30% scaffold pass may touch only these surface classes unless a later packet widens scope:

1. `services/mcp/apex-fs/`, `services/mcp/apex-db/`, and `services/mcp/apex-jobs/` structure, README, env-contract, package metadata, and non-destructive skeleton wiring,
2. `.claude/CLAUDE.md`, `.claude/mcp.json`, and bounded subagent briefs,
3. `infra/compose.dev.yml` and `.env.dev.template` as scaffold and contract surfaces,
4. `infra/olares/charts/forms-engine/` as a shell-only staging chart boundary,
5. `tests/canary/` and `tools/` where the work is limited to admitted backbone contract checks,
6. repo-owned docs that describe the backbone, trust boundary, scaffold plan, and hardening split.

## Explicitly Forbidden In The First Pass

The first pass must not open any of the following:

1. `ai_tasks` admission or queue ownership,
2. Ollama, Open WebUI, Dify, n8n, Qdrant, or other broader AI-services rollout,
3. new MCP services beyond `apex-fs`, `apex-db`, and `apex-jobs`,
4. public ingress, canonical-hosting change, or auth-model change,
5. business-logic rewrites in `apps/` or schema mutation in Supabase,
6. any claim that staging or promotion proof exists without `env=host` evidence.

## Required Backbone Contracts

The first-pass scaffold must preserve these contracts:

1. every run that matters to completion still resolves through `apex-jobs`,
2. `env=sandbox|host` remains the controlling trust distinction,
3. promotion remains impossible without successful `env=host` evidence,
4. the minimal MCP trio remains operator-bounded and mesh-only,
5. canary and provenance surfaces remain repo-visible and reviewable.

## Parallel Hardening Split

The safe adjacent hardening lane may run in parallel with the Codex first pass.

That hardening lane is limited to authoring and tightening the contracts around:

1. `apex-jobs` env-tag semantics,
2. promotion-refusal behavior,
3. provenance metadata requirements,
4. MCP boundary and mount rules,
5. canary admission and evidence rules.

It must not refactor the same implementation files Codex is using for scaffold authoring unless the change is explicitly coordinated in the packet or handoff surface.

## Done Definition For The Framework Pack

This lane is successful when:

1. Codex has a written first-pass brief with explicit allowed and forbidden scope,
2. the repo has a scaffold specification that can be executed without re-arguing the boundary,
3. the adjacent hardening lane is named explicitly enough to run in parallel,
4. no new document implies broader orchestration-service admission than the current first slice allows.