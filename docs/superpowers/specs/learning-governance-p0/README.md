# Learning Governance P0 Design Packet

Status: OPERATOR-DIRECTED DESIGN - NOT IMPLEMENTED

Authority:

- operator GO `LEARNING-GOVERNANCE-P0-DESIGN ONLY`;
- operator direction dated 2026-07-14 adopting the staged product intent,
  recommended authorities, delegated Program Manager, separate primary Codex
  executor, and checkpointed continuous-goal model.

Baseline: `origin/main` at `cf1c72f370e4922b8fdad4b691f7ad9d89258109`

## Purpose

This packet designs a durable control plane for learning-program goals,
authority, evidence, decisions, and roadmap state. It records the operator's
product-intent and delegation decisions while preserving the current Level II
Electrical Theory pilot hold. It replaces chat-only coordination with a
proposed governed model that a separate primary executor can follow and a
delegated Program Manager can review.

## Hard Boundaries

This packet may read repository authority and existing control metadata and may
produce design documents. It does not authorize:

- source-body or draft-body inspection;
- learner-facing content authoring;
- learner-data access or writes;
- database or API access;
- schema, checker, registry, or application implementation;
- import, render, deployment, release, or production action;
- clearing `ET-PILOT-HOLD`;
- expansion beyond ET-010 through ET-014;
- activation of ET-017 or ET-028.

## Packet Index

1. `2026-07-14-learning-governance-control-plane-design.md`
2. `PROGRAM-CHARTER-DRAFT.md`
3. `ROLE-AND-DECISION-RIGHTS-DRAFT.md`
4. `GOAL-REGISTRY-AND-STATE-MACHINE-DRAFT.md`
5. `EVIDENCE-AND-DECISION-BINDING-DRAFT.md`
6. `CHECKER-AND-ADVERSARIAL-TEST-DESIGN.md`
7. `LEVEL-II-G2-STATE-MIGRATION-MAP.md`
8. `SLICE2D-CONTRACT-RECONCILIATION-FOLLOW-UP.md`
9. `APPOINTMENTS-AND-DELEGATIONS.md`
10. `PROGRAM-MANAGER-OPERATING-INSTRUCTIONS.md`
11. `PRIMARY-EXECUTOR-OPERATING-INSTRUCTIONS.md`
12. `CONTINUOUS-GOAL-LOOP.md`
13. `ROADMAP-AND-CURRENT-GOALS.md`
14. `PROGRAM-MANAGER-ACTION-QUEUE.md`
15. `RIGHTS-AUTHORITY-AND-SOURCE-EVIDENCE.md`
16. `goals/README.md`
17. `goals/LEARN-GOV-P0-001.md`
18. `goals/LEARN-GOV-P1-CHECKER-001.md`
19. `goals/LEARN-RIGHTS-DECISIONS-001.md`
20. `goals/LEARN-SME-APPOINTMENT-001.md`
21. `goals/LEVEL-II-ET-PILOT-001.md`
22. `reviews/LEARN-GOV-P0-001-CP4-CP5-REVIEW-2026-07-14.md`
23. `templates/GOAL-CHARTER-TEMPLATE.md`
24. `templates/EXECUTION-CHECKPOINT-TEMPLATE.md`
25. `templates/PROGRAM-MANAGER-REVIEW-TEMPLATE.md`
26. `templates/DECISION-RECORD-TEMPLATE.md`
27. `templates/GOAL-CLOSEOUT-TEMPLATE.md`

## Review Gate

The staged product intent and role mechanisms named in this packet are
operator-directed. The control-plane implementation, individual goal
appointments, source decisions, SME decisions, learner-data work, content work,
and release decisions remain separately gated. No implementation plan may
treat a placeholder, recommendation, or missing decision as accepted authority.
