# Learning Governance P0 Design Packet

Status: DESIGN ACCEPTED WITH CONDITIONS - NOT IMPLEMENTED

Authority:

- operator GO `LEARNING-GOVERNANCE-P0-DESIGN ONLY`;
- operator direction dated 2026-07-14 adopting the staged product intent,
  recommended authorities, delegated Program Manager, separate primary Codex
  executor, and checkpointed continuous-goal model;
- operator CP6 decision `LEARN-GOV-P0-CP6-2026-07-14`, accepting this governance
  design only while retaining every implementation and operational hold.

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
16. `SOURCE-ACCESS-AND-CUSTODY-MAP.md`
17. `decisions/LEARN-GOV-P0-001-CP6-2026-07-14.md`
18. `closeouts/LEARN-GOV-P0-001-CP7-2026-07-14.md`
19. `goals/README.md`
20. `goals/LEARN-GOV-P0-001.md`
21. `goals/LEARN-GOV-P1-CHECKER-001.md`
22. `goals/LEARN-RIGHTS-DECISIONS-001.md`
23. `goals/LEARN-SME-APPOINTMENT-001.md`
24. `goals/LEVEL-II-ET-PILOT-001.md`
25. `reviews/LEARN-GOV-P0-001-CP4-CP5-REVIEW-2026-07-14.md`
26. `reviews/LEARN-GOV-P0-001-REVIEWED-PACKET.sha256`
27. `closeouts/LEARN-GOV-P0-001-POST-CP6-PACKET.sha256`
28. `templates/GOAL-CHARTER-TEMPLATE.md`
29. `templates/EXECUTION-CHECKPOINT-TEMPLATE.md`
30. `templates/PROGRAM-MANAGER-REVIEW-TEMPLATE.md`
31. `templates/DECISION-RECORD-TEMPLATE.md`
32. `templates/GOAL-CLOSEOUT-TEMPLATE.md`

## Review Gate

The staged product intent and role mechanisms named in this packet are
operator-directed. The control-plane implementation, individual goal
appointments, source decisions, SME decisions, learner-data work, content work,
and release decisions remain separately gated. No implementation plan may
treat a placeholder, recommendation, or missing decision as accepted authority.
