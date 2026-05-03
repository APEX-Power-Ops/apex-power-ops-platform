# `packages/p6-ingest` Lane-Ownership Reconciliation Handoff

Date: 2026-04-29
Packet: `2026-04-29-p6-ingest-lane-ownership-reconciliation`
Status: **Executed / closed**
Authority: `docs/architecture/WORKSPACE-P6-INGEST-LANE-OWNERSHIP-RECONCILIATION-2026-04-29.md`
Completion handoff: `ops/agents/handoffs/2026-04-29-p6-ingest-lane-ownership-reconciliation-completion-handoff.md`
Project: `C:/APEX Platform/apex-power-ops-platform` bounded lane-governance
reconciliation for `packages/p6-ingest`

## Objective

Execute only the bounded reconciliation authorized by the completed workspace
governance and runtime drift audit.

The execution must do exactly five things:

1. absorb `packages/p6-ingest` into the active lane-governance surfaces,
2. add explicit ownership and approval routing for `packages/p6-ingest/`,
3. add `packages/p6-ingest` to the Pattern 1 examples in the Python framework
   standard,
4. publish one explicit ruling for the runtime fixture lineage between
   `packages/p6-ingest` and
   `apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer`,
5. return a completion handoff that names any residual out-of-scope drift

This handoff does not authorize code changes, fixture motion, canary reruns,
parent-root publication, or unrelated doc cleanup.

## Execution Result

This handoff has been executed and is now historical control context.

Closed outcome:

1. all five required governance edits landed
2. the fixture-lineage ruling was published as governed cross-lane reuse
3. the completion record now lives in
   `ops/agents/handoffs/2026-04-29-p6-ingest-lane-ownership-reconciliation-completion-handoff.md`
4. no hard-limit breach occurred during execution

## Confirmed Entry Gate

The packet is authorized because the completed audit already established all of
the following on disk:

1. `packages/p6-ingest` is a real package-shaped lane under `packages/`
2. the Olares roadmap already records `p6-ingest` host-installed proof as
   closed
3. MCP runtime evidence already exposes the `apex-p6` endpoint
4. `p6-ingest` canary runtime evidence already resolves through the
   mutation-seam fixture path
5. the active lane-governance, ownership, and Python-framework surfaces omit
   `packages/p6-ingest`
6. no governance surface yet classifies the current fixture-lineage posture

If any of those six statements fails on re-read, stop and return a blocker
instead of broadening the packet.

## Mandatory Read Set

Open these files before the first substantive edit:

1. `docs/architecture/WORKSPACE-P6-INGEST-LANE-OWNERSHIP-RECONCILIATION-2026-04-29.md`
2. `docs/architecture/WORKSPACE-GOVERNANCE-AND-RUNTIME-DRIFT-AUDIT-2026-04-28.md`
3. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
4. `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md`
5. `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`
6. `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md`
7. `docs/authority/PYTHON-FRAMEWORK-GUIDELINES-2026-04-27.md`
8. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
9. `tests/canary/p6-ingest-dev-runtime/actual/health.json`
10. `tests/canary/p6-ingest-dev-runtime/actual/summary.json`
11. `tests/canary/mcp-contract/actual/mcp-tool-lists.json`
12. `apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.README.md`
13. `apps/mutation-seam/app/schedule/fixtures/BASELINE_XER_FIXTURE_CONTRACT.md`

## First Anchors

Start from the active lane-governance docs plus the exact fixture path already
named in runtime proof.

### Governance anchors

1. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
2. `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md`
3. `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`
4. `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md`
5. `docs/authority/PYTHON-FRAMEWORK-GUIDELINES-2026-04-27.md`

Local hypothesis for the first slice:

- the core gap is omission, so a narrow governance edit pass should fully close
  the lane-classification problem without touching implementation code.

Cheapest falsifying check:

- if any governing doc already classifies `packages/p6-ingest` under a
  conflicting lane state, stop and return the contradiction before editing.

### Fixture-lineage anchors

1. `tests/canary/p6-ingest-dev-runtime/actual/health.json`
2. `tests/canary/p6-ingest-dev-runtime/actual/summary.json`
3. `apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer`
4. `apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.README.md`

Local hypothesis for the lineage slice:

- the current fixture dependency can be governed explicitly now, and any actual
  re-home decision can remain a later packet if needed.

Cheapest falsifying check:

- if the fixture-side docs prohibit shared-package reuse, do not ratify reuse;
  publish only the scheduled later re-home ruling.

## Execution Order

### 1. Reconfirm packet limits

Required outcomes:

1. the packet remains doc-governance only
2. TCC remains out of scope
3. no fixture motion is implied

### 2. Reconcile active lane-governance surfaces

Required outcomes:

1. `packages/p6-ingest` appears in the active lane-governance docs
2. wording stays parallel to other active shared-package lanes
3. no unrelated lane states are changed

### 3. Reconcile ownership routing

Required outcomes:

1. `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md` gains a
   `packages/p6-ingest/` row
2. the primary steward lane is `shared-packages`
3. `runtime-apps` remains a secondary concern when behavior changes affect
   active consumers

### 4. Reconcile Python framework examples

Required outcomes:

1. the Pattern 1 examples name `apex-power-ops-platform/packages/p6-ingest`
2. the packet does not widen into general Python bootstrap cleanup

### 5. Publish the fixture-lineage ruling

Required outcomes:

1. one explicit statement classifies the current lineage posture
2. the statement chooses either governed cross-lane reuse or scheduled later
   re-home
3. no file motion is performed

### 6. Publish completion handoff

Required outcomes:

1. exact files edited are listed
2. the lineage ruling is restated exactly
3. residual out-of-scope drift is separated from this packet

## Hard Limits

1. no code edits in `packages/p6-ingest/` or `apps/mutation-seam/`
2. no canary regeneration or deletion
3. no edits to `apps/mutation-seam/QUICKSTART.md`
4. no parent-root publication work
5. no topology rewrite beyond `packages/p6-ingest`

## Expected Deliverables Back To Copilot

Return all of the following:

1. exact governance files updated
2. exact ownership routing added
3. exact Pattern 1 example reconciliation made
4. one explicit fixture-lineage ruling
5. one list of residual out-of-scope items, if any

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| Active lane-governance surfaces absorb `packages/p6-ingest` exactly | PASS | PASS |
| Ownership routing for `packages/p6-ingest/` is explicit | PASS | PASS |
| Python framework examples absorb `packages/p6-ingest` cleanly | PASS | PASS |
| Fixture-lineage posture is ruled without file motion | PASS | PASS |
| Residual drift remains bounded out of scope | PASS | PASS |

## Operator Note

This is a reconciliation packet, not an implementation packet. If the current
fixture lineage cannot be governed as-is, record the later re-home requirement
and stop. Do not move fixtures or widen into package refactoring inside this
lane.