# Workspace Governance And Runtime Drift Audit Handoff

Date: 2026-04-28
Packet: `2026-04-28-workspace-governance-and-runtime-drift-audit`
Status: **Ready for execution**
Authority: `docs/architecture/WORKSPACE-GOVERNANCE-AND-RUNTIME-DRIFT-AUDIT-2026-04-28.md`
Project: `C:/APEX Platform/apex-power-ops-platform` workspace governance and
runtime-proof reconciliation lane

## Objective

This handoff delegates the next bounded authority slice after the TCC consumer-
need packet closed PASS and the platform-root drift signals surfaced.

Execute only this audit lane:

1. verify whether the new local authority docs create only additive local
   guidance or a real cutover contradiction,
2. verify whether the new Python governance changes are aligned with the current
   lane map,
3. verify whether the newly committed canary actual outputs expose unresolved
   cross-lane or moved-subfolder lineage drift,
4. classify the current `p6-ingest` lane posture exactly,
5. return one exact next-step ruling naming the smallest truthful follow-on.

This handoff does not authorize TCC work, code motion, package activation by
assumption, or broad repo restructuring.

## Confirmed Entry Gate

The packet is authorized because the following statements are already true on
disk:

1. the closed TCC consumer-need packet preserved HOLD on both Tier B views and
   left TCC Slice 3 separately gated on a future measurement packet
2. new local authority docs now exist under `docs/authority/`
3. root and lane-local Python governance changed materially toward Ruff-first
   tooling and `.venv`-first local bootstrap
4. new canary actual outputs now exist for `forms-engine`, `p6-ingest`, and MCP
   runtime contracts
5. the current workspace governance surfaces do not obviously reconcile all of
   those new signals yet

If any one of those statements fails when execution begins, stop and return a
blocker report instead of broadening into a different lane.

## Mandatory Read Set

Open these files before the first substantive action:

1. `docs/architecture/WORKSPACE-GOVERNANCE-AND-RUNTIME-DRIFT-AUDIT-2026-04-28.md`
2. `docs/authority/README.md`
3. `docs/authority/PYTHON-FRAMEWORK-GUIDELINES-2026-04-27.md`
4. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
5. `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md`
6. `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`
7. `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md`
8. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
9. `tests/canary/p6-ingest-dev-runtime/actual/health.json`
10. `tests/canary/p6-ingest-dev-runtime/actual/summary.json`
11. `tests/canary/forms-engine-dev-runtime/actual/health.json`
12. `tests/canary/mcp-contract/actual/mcp-tool-lists.json`

## First Anchors

Start from the current lane-status and ownership docs plus the canary runtime
proofs rather than re-exploring the whole repo.

### Governance anchors

1. `docs/authority/README.md`
2. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
3. `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`
4. `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md`

Local hypothesis for the first slice:

- current governance is lagging the live runtime and package evidence, so the
  next honest move is classification and reconciliation, not a fresh feature
  packet in another lane.

Cheapest falsifying check:

- verify whether those governance surfaces already describe the newly visible
  runtime and package state exactly. If they do, do not widen the packet.

### Runtime-proof anchors

1. `tests/canary/p6-ingest-dev-runtime/actual/health.json`
2. `tests/canary/forms-engine-dev-runtime/actual/health.json`
3. `tests/canary/mcp-contract/actual/mcp-tool-lists.json`

Local hypothesis for the runtime slice:

- the committed canary outputs are exposing real lane-boundary questions, with
  the strongest signal currently on the `p6-ingest` runtime proof path.

Cheapest falsifying check:

- determine whether the recorded runtime lineage is already explicitly governed.
  If yes, this is mainly doc drift. If no, a narrower follow-on packet is needed.

## Execution Order

### 1. Reconfirm the boundary

Required outcomes:

1. TCC remains out of scope
2. no code or package move is implied by this packet
3. the audit remains platform-root only

### 2. Audit governance and ownership surfaces

Required outcomes:

1. classify authority-bridge posture exactly
2. classify package-map and ownership-map coverage exactly
3. record any omissions or contradictions with exact file references

### 3. Audit runtime-proof and moved-subfolder lineage

Required outcomes:

1. classify each cross-lane runtime proof exactly
2. determine whether `p6-ingest` fixture lineage is governed, tolerated drift,
   or ungoverned drift
3. distinguish runtime proof from lane ownership and source lineage

### 4. Publish the next-step ruling

Required outcomes:

1. one exact drift classification per major surface
2. one exact smallest follow-on packet or no-action ruling
3. no widening into repo-wide re-architecture

## Hard Limits

1. no TCC reopening
2. no file moves or package activation edits
3. no canary regeneration or deletion
4. no deploy-worktree or publication-boundary widening

## Expected Deliverables Back To Copilot

Return all of the following:

1. exact governance surfaces checked
2. exact runtime-proof surfaces checked
3. exact contradictions or omissions found
4. exact doc-only reconciliations made, if any
5. one explicit next-step ruling

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| Authority posture classified exactly | PASS | Pending |
| Ownership and lane-map posture classified exactly | PASS | Pending |
| Cross-lane runtime-proof posture classified exactly | PASS | Pending |
| `p6-ingest` follow-on ruling stated exactly | PASS | Pending |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Execute a
bounded audit and classification pass only. If the packet proves only doc drift,
return the smallest doc-only follow-on. If it proves a real lane-boundary gap,
name the exact next packet needed and stop there.