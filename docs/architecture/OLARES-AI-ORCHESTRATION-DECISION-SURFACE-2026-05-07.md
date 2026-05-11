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
3. `../operations/OLARES-MVP-AI-ORCHESTRATION-STATUS-BRIEF-2026-05-10.md` for the compact five-part MVP and current AI-lane status readout,
4. `../../plan/OLARES-AI-ORCHESTRATION-EXECUTION-PLAN-2026-05-10.md` for the active phase order, execution sequence, and widening gate,
5. `../operations/OLARES-AI-PARALLEL-TASK-READINESS-CHECKLIST-2026-05-10.md` for the bounded next-step checklist toward controlled parallel task ability,
6. `control-plane-lineage/apex-resa/AI_ORCHESTRATION_PROTOCOL.md` as the broader protocol and future-bridge reference,
7. packet and handoff evidence under `ops/agents/` for bounded execution history.

Do not use parent-root `.claude/DECISION_LOG.md` as the preferred current authority surface once this file answers the question.

## Current Authority Order

1. this file for current Olares-first AI orchestration decisions,
2. `../authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md` for the bounded Codex first-pass scaffold boundary and parallel hardening split,
3. `OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md` for admitted-surface commands, trust boundaries, and verification posture,
4. `control-plane-lineage/apex-resa/AI_ORCHESTRATION_PROTOCOL.md` for protocol structure and future integration model,
5. historical packets and handoffs only for provenance.

## Workflow Definition

### Primary queue shape

1. `apex-jobs` is the operational run and promotion ledger for the current Olares-first slice.
2. packet and handoff governance remain the controlling work-queue shape.
3. `ai_tasks` remains a later integration surface rather than the admitted first-slice controller.

### Executor shape

1. one bounded executor is the default execution model for packet-scoped work,
2. a second executor may be admitted only for explicitly disjoint lanes with written ownership,
3. `ai_tasks` does not currently assign or arbitrate executor ownership,
4. publication and promotion remain governed outcomes rather than automatic executor powers.

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

Current executor admission:

- primary mutation and validation executor for the admitted lane
- may run alone or as the implementation owner in a two-executor packet

### Codex

Current decision:

- Codex is not part of the current runtime, promotion, or queue-control boundary for the first admitted AI slice.
- Codex is admitted only for bounded design and scaffold authoring under `docs/authority/OLARES-AI-BACKBONE-FRAMEWORK-2026-05-08.md` and its companion execution brief.
- That admission does not authorize Codex to widen the admitted MCP trio, take over `apex-jobs` promotion control, or imply `ai_tasks`, Ollama, Dify, n8n, or public-ingress rollout.

Current executor admission:

- may act as a secondary bounded executor only for scaffold, shell, or document-authoring lanes
- may not become the shared owner of mixed scaffold-plus-runtime mutation in the same packet without an explicit boundary change

### Human authority

Jason review or decision remains required for:

- priority shifts
- business logic changes
- auth or public-boundary changes
- new third-party account commitments
- any intentional scope widening beyond the currently authorized packet lane

## Parallel Task And Executor Rules

The current lane allows controlled parallel task paths, but only in a narrow executor-governed form.

### Allowed now

1. one executor completing a bounded packet end to end,
2. two executors running in parallel when ownership is explicitly split before execution,
3. scaffold-versus-hardening splits that preserve file ownership and validation order,
4. review or publication-prep handoff after one executor completes the mutation slice.

### Not allowed now

1. open-ended multi-executor source mutation across the same files,
2. `ai_tasks` as the live queue owner or arbitration surface,
3. more than two active executors in the same mutation lane by default,
4. executor-driven widening of auth, ingress, hosting, or business-logic scope.

### Required conditions for two-executor work

1. the packet or handoff names each executor and its owned surface,
2. one executor owns the final write for each touched file,
3. the narrow validation order is explicit before the first edit,
4. abort rules are written if the lanes begin to overlap,
5. repo-visible evidence still captures one coherent completion record.

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