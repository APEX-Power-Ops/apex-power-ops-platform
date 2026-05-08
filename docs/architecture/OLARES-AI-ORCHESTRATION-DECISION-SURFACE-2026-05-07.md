# Olares AI Orchestration Decision Surface

Date: 2026-05-07
Status: Active repo-owned AI orchestration decision surface
Scope: current admitted AI workflow decisions for the Olares-first lane after extraction from parent-root `.claude/DECISION_LOG.md` Section 8

## Purpose

This document is the repo-owned current-truth decision surface for AI orchestration in the Olares-first lane.

It consolidates the surviving active decisions that had still been referenced through `.claude/DECISION_LOG.md`.

Use this file with:

1. `OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md` for operator commands and trust-boundary execution,
2. `../authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md` for the bounded backbone-design and scaffold-authoring rules,
3. `../../Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` as the broader protocol and future-bridge reference,
4. packet and handoff evidence under `ops/agents/` for bounded execution history.

Do not use parent-root `.claude/DECISION_LOG.md` as the preferred current authority surface once this file answers the question.

## Current Authority Order

1. this file for current Olares-first AI orchestration decisions,
2. `../authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md` for the bounded Codex first-pass scaffold boundary and parallel hardening split,
3. `OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md` for admitted-surface commands, trust boundaries, and verification posture,
4. `../../Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` for protocol structure and future integration model,
5. historical packets and handoffs only for provenance.

## Workflow Definition

### Primary queue shape

1. `apex-jobs` is the operational run and promotion ledger for the current Olares-first slice.
2. packet and handoff governance remain the controlling work-queue shape.
3. `ai_tasks` remains a later integration surface rather than the admitted first-slice controller.

### Valid task types

The current useful task types are:

- `decision`
- `document`
- `create`
- `enhance`
- `validate`
- `review`
- `publish`
- `deploy`
- `maintain`

### Priority model

The current priority set is:

- `critical`
- `high`
- `normal`
- `low`
- `background`

### Stuck threshold

Execution work is considered stuck when it has no new validation, ledger update, or handoff by the next working session.

`critical` work is stuck after 30 minutes without progress evidence.

## Agent Responsibilities

### Desktop Claude

Primary role:

- orchestration
- packet selection
- boundary decisions
- QC
- cross-surface reasoning

### VS Code Claude

Primary role:

- precision implementation
- validation
- file surgery
- bounded execution from the active workspace or host mirror

### Codex

Current decision:

- Codex is not part of the current runtime, promotion, or queue-control boundary for the first admitted AI slice.
- Codex is admitted only for bounded design and scaffold authoring under `docs/authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md` and its companion execution brief.
- That admission does not authorize Codex to widen the admitted MCP trio, take over `apex-jobs` promotion control, or imply `ai_tasks`, Ollama, Dify, n8n, or public-ingress rollout.

### Human authority

Jason review or decision remains required for:

- priority shifts
- business logic changes
- auth or public-boundary changes
- new third-party account commitments
- any intentional scope widening beyond the currently authorized packet lane

## Quality Gates

### Done definition

A task is done only when:

1. its scoped artifact exists,
2. the narrowest available validation has run,
3. the result is captured in repo-visible evidence or an equivalent ledger or handoff surface.

### Desktop Claude review gate

Desktop Claude review is required for:

- architecture changes
- protocol changes
- multi-file risky edits
- boundary changes
- work prepared for publication by another executor

### Jason review gate

Jason review is required for:

- business workflow decisions
- user-facing behavior changes that alter operating policy
- new external services or spending
- any auth or public-ingress change

## Interpretation Rules

1. The current Olares-first lane is intentionally bounded.
2. No current decision here silently admits broader AI-services expansion.
3. The admitted first slice is still Claude-first with the minimal MCP trio and `apex-jobs` ledger.
4. Codex first-pass work is limited to bounded backbone design and scaffold authoring under a written framework, not runtime or promotion control.
5. Historical `.claude/DECISION_LOG.md` content remains useful as provenance, not as the preferred current authority surface.