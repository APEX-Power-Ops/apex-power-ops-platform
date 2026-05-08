# Olares Developer Host Cutover Milestone 1 Acceptance Checklist

Date: 2026-05-05
Status: Executed Milestone 1 audit baseline with closeout-routing context
Scope: auditable acceptance checklist for Milestone 1 host residency baseline

Closeout interpretation note:

Milestone 1 host residency is already closed. This checklist remains the audit baseline for what had to be proven, but it is no longer a live gate for opening the cutover lane.

Current routing:

1. use `PROJECT_STATUS.md` for the current residue-retirement lane and latest completed packets,
2. use `docs\architecture\OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-PLAN-2026-05-05.md` for the recorded milestone baseline,
3. use `ops/agents/handoffs/2026-05-05-olares-dev-residency-002-canonical-host-residency-and-toolchain-revalidation-handoff.md` for the actual Milestone 1 evidence record.

## Purpose

This checklist records how Milestone 1 of the Olares developer-host cutover was
to be assessed.

Milestone 1 is the host residency baseline.

It closes only when path authority, secrets and mutable-state boundaries, and
reconnect behavior are all proven on the Olares host rather than assumed from
prior Phase 5 work.

## Authority

This checklist depends on:

1. `docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-PLAN-2026-05-05.md`
2. `docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-TECHNICAL-PLAN-2026-05-05.md`
3. `ops/agents/packets/draft/2026-05-05-olares-dev-residency-001-developer-host-cutover-preflight-and-execution-planning.json`
4. `ops/agents/handoffs/2026-05-05-olares-dev-residency-001-developer-host-cutover-preflight-and-execution-planning-handoff.md`
5. `plan/infrastructure-olares-full-implementation-roadmap-1.md`

## How To Use This Checklist

For each item below, record one of:

1. `pass`
2. `fail`
3. `not assessed`

Milestone 1 closed only if every required item passed and no failure trigger was
hit.

## Required Acceptance Items

### A. Host Path Authority

1. Evidence proves the authoritative host parent-root mirror is `~/code/apex`.
2. Evidence proves the active host implementation surface is `~/code/apex/apex-power-ops-platform`.
3. The execution record shows `git rev-parse --show-toplevel` resolving to `/home/olares/code/apex` from the active implementation lane.
4. Operator-facing documentation and packet surfaces point active host work at `~/code/apex`, not the old clone.

### B. Old Clone Demotion

5. `/home/olares/src/apex-power-ops-platform` is explicitly recorded as historical evidence only.
6. No active validation or mutation step for Milestone 1 is executed from `/home/olares/src/apex-power-ops-platform`.
7. Any comparison against the old clone is read-only and framed as preservation evidence rather than active workspace use.

### C. Secrets And Mutable State Boundaries

8. Required secret-bearing material is stored outside the git workspace under a host-local boundary such as `~/apex-secrets`.
9. Required mutable development or application state is stored outside the git workspace under a host-local boundary such as `~/apex-data`.
10. Recovery or bounded host-side backup material is stored under a documented host-local boundary such as `~/apex-backups`.
11. No required secret, mutable runtime state, or recovery artifact exists only on the field laptop.

### D. Restart And Reconnect Repeatability

12. An approved reconnect path to Olares is proven and recorded, using private-mesh SSH, VS Code Remote-SSH, browser-terminal fallback, or another already-approved private path.
13. The execution record proves the host workspace can be re-entered after disconnect or restart without relying on undocumented laptop-local state.
14. The execution record captures the exact target path and reconnect method used for the proof.

### E. Program Boundary Integrity

15. The Milestone 1 proof does not reopen feature delivery, public ingress widening, AI-services expansion, Gitea transition, or canonical-hosting transition.
16. The Milestone 1 proof does not silently re-establish the laptop as the durable runtime anchor.

## Failure Triggers

Milestone 1 fails immediately if any of the following is true:

1. active work is routed to `/home/olares/src/apex-power-ops-platform`
2. required secrets or mutable state are stored inside the git workspace
3. required secrets or mutable state exist only on the laptop
4. reconnect or restart success depends on undocumented operator memory rather than repo-visible evidence
5. the proof requires public ingress widening, code-hosting transition, or unrelated runtime churn

## Required Evidence Shape

The execution artifact for this checklist should capture at minimum:

1. the exact host path used for the proof
2. the exact reconnect method used for the proof
3. path-authority evidence showing the correct git top-level
4. boundary evidence for secrets, mutable state, and recovery paths
5. an explicit statement that the old clone remained observe-only
6. a pass or fail verdict for each required item above

## Exit Condition

Milestone 1 closes only when:

1. all sixteen required acceptance items are marked `pass`
2. no failure trigger fired during execution, and
3. the result is published as repo-visible evidence rather than left only in terminal history