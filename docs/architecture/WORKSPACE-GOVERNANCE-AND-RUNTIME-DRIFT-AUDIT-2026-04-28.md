---
goal: Workspace Governance And Runtime Drift Audit For Post-Rehome Lane Alignment
version: 1.0
date_created: 2026-04-28
last_updated: 2026-04-28
owner: Platform Governance / Workspace Architecture
status: Historical audit packet
tags: [workspace, governance, audit, re-home, runtime, canary]
---

# Historical Workspace Governance And Runtime Drift Audit

Historical audit note:

This packet preserves one bounded post-rehome audit proposal from before the later standalone repo cutover and authority normalization work. It is not the current packet frontier for repo-structure or Olares operator decisions.

Current routing:

1. use `../../PROJECT_STATUS.md` for the current residue-retirement frontier and packet ledger,
2. use `APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` plus `APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md` for the current repo-structure and lane-routing contract,
3. use this audit only when the earlier workspace-governance drift hypothesis or its original evidence set need to be reconstructed historically.

## Executive Summary

This packet defined one bounded authority lane after the closed TCC Phase 5
Tier B consumer-need ruling and the then-newly visible platform-root drift signals.

At that time, the next governed move was not a default TCC Slice 3 measurement packet.
The stronger current problem was workspace-governance and runtime-proof drift
inside `C:/APEX Platform/apex-power-ops-platform`.

What is already true:

1. the TCC lane is currently in a clean HOLD state, with no qualifying current
   or near-term consumer found for either Tier B derived view
2. the TCC umbrella packet already states that any future Slice 3 move requires
   a separately authored measurement packet
3. new platform-root authority and canary surfaces have appeared since that TCC
   closure state was reconciled
4. those new platform-root surfaces introduce file-backed questions about
   whether the lane map, ownership map, package map, and runtime-proof map are
   still aligned

What this packet was for:

1. inspect governance surfaces that define the active platform lane map
2. inspect moved-subfolder or re-home lineage where runtime evidence now points
   across lane boundaries
3. inspect workflow and repo-drift risk introduced by new local authority docs,
   Python-tooling normalization, and committed canary actual outputs
4. return one exact ruling saying whether the drift is only documentation drift,
   or whether a narrower follow-on implementation or governance packet is needed

This packet did not authorize TCC runtime work, TCC Slice 3 implementation,
package activation by narrative, or repo-wide restructuring.

## Scope Lock

In scope:

1. `docs/authority/README.md` and the newly added local authority document set
2. `pyproject.toml`, `apps/control-plane-api/requirements-dev.txt`, and
   `apps/mutation-seam/pyproject.toml` / `QUICKSTART.md` as evidence of active
   Python governance change
3. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
4. `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md`
5. `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`
6. `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md`
7. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
8. `tests/canary/**/actual/*` as runtime-proof surfaces
9. active lane relationships among `apps/mutation-seam`, `packages/forms-engine`,
   and `packages/p6-ingest`

Out of scope:

1. reopening the closed TCC consumer-need packet
2. authoring a TCC Slice 3 measurement target
3. runtime code moves between lanes
4. new package scaffolding or package promotion by assumption
5. deploy-worktree reconciliation
6. broad parent-root publication work

## Confirmed Drift Signals

The packet is justified because the following file-backed drift signals now
exist simultaneously:

1. `docs/authority/README.md` still states that the strategic authority stack
   has not moved yet, but it now also names active local authority documents in
   the bootstrap root.
2. Root and lane-local Python governance changed materially toward Ruff-first
   tooling and `.venv`-first bootstrap flows, but that change has not yet been
   reconciled against the broader workspace-governance surfaces.
3. New committed canary actual outputs now prove live runtime contracts for
   `forms-engine`, `p6-ingest`, and MCP endpoints inside `tests/canary/`.
4. The `p6-ingest` runtime canary records fixture lineage from
   `apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer`.
5. The current workspace-governance docs call out `packages/calc-engine` and
   `packages/forms-engine` as active governed package lanes, but they do not
   presently describe `packages/p6-ingest` as part of the active lane map.
6. `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md` names ownership for
   `packages/calc-engine`, `packages/forms-engine`, and `packages/api-contracts`,
   but not for `packages/p6-ingest`.

These signals are enough to justify an audit packet even before any code or doc
repair is authorized.

## Decision Boundary

This packet must answer the following questions exactly:

1. Are the new local authority docs merely additive, or do they create an
   unresolved cutover contradiction with the current authority bridge?
2. Are the new Python governance changes aligned with the current workspace lane
   map and package/app posture, or do they overstate what has actually been
   normalized?
3. Are the new canary actual outputs acting only as bounded runtime evidence,
   or are they exposing unresolved lane-boundary drift?
4. Is `p6-ingest` intentionally still dependent on `apps/mutation-seam` fixture
   lineage, or is that dependency an undocumented re-home gap?
5. Is the package and ownership map still truthful if `packages/p6-ingest`
   remains absent from the current governance surfaces?

The output must publish one exact next-step ruling:

1. doc-only reconciliation packet,
2. bounded lane-ownership reconciliation packet,
3. bounded moved-subfolder or re-home implementation packet, or
4. explicit no-action beyond recording the drift as acceptable current posture.

## Mandatory Read Set

Open these files before the first substantive audit action:

1. `docs/authority/README.md`
2. `docs/authority/PYTHON-FRAMEWORK-GUIDELINES-2026-04-27.md`
3. `pyproject.toml`
4. `apps/control-plane-api/requirements-dev.txt`
5. `apps/mutation-seam/pyproject.toml`
6. `apps/mutation-seam/QUICKSTART.md`
7. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
8. `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md`
9. `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`
10. `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md`
11. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
12. `tests/canary/p6-ingest-dev-runtime/actual/health.json`
13. `tests/canary/p6-ingest-dev-runtime/actual/summary.json`
14. `tests/canary/forms-engine-dev-runtime/actual/health.json`
15. `tests/canary/mcp-contract/actual/mcp-tool-lists.json`

## First Audit Anchors

Start from the owning governance surfaces and the runtime proofs rather than
from broad repo exploration.

### Governance anchors

1. `docs/authority/README.md`
2. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
3. `docs/architecture/WORKSPACE-LANE-NORMALIZATION-CHECKLIST-2026-04-22.md`
4. `.github/WORKSPACE-OWNERSHIP-APPROVAL-MAP.md`

Local hypothesis for the first slice:

- the workspace-governance map is lagging behind real runtime and package
  surfaces, and the next honest work is an audit and classification pass rather
  than another implementation packet in an unrelated lane.

Cheapest falsifying check:

- verify whether the changed authority, ownership, and lane-status docs already
  account for the newly visible runtime surfaces and package lanes. If they do,
  this packet can collapse to a smaller doc-only status note.

### Runtime-proof anchors

1. `tests/canary/p6-ingest-dev-runtime/actual/health.json`
2. `tests/canary/forms-engine-dev-runtime/actual/health.json`
3. `tests/canary/mcp-contract/actual/mcp-tool-lists.json`

Local hypothesis for the runtime slice:

- the canary outputs are not just generic proof artifacts; they are exposing
  real lane-boundary questions, especially where `p6-ingest` runtime proof is
  still rooted in `apps/mutation-seam` fixture lineage.

Cheapest falsifying check:

- determine whether that cross-lane lineage is already explicitly governed. If
  it is, the remaining issue is documentation completeness. If it is not, a
  narrower moved-subfolder or lane-reconciliation follow-on is justified.

## Execution Order

### 1. Reconfirm the boundary

Required outcomes:

1. the TCC next-step lane is confirmed not to be automatically reopened here
2. the packet is confirmed to be platform-root audit only
3. the changed platform surfaces are confirmed to be file-backed and current

### 2. Audit authority and ownership surfaces

Required outcomes:

1. local authority-doc posture is classified as additive, contradictory, or in
   partial cutover
2. package and lane maps are checked against the actual directory and runtime
   proof surfaces
3. ownership-map omissions, if any, are named exactly

Execution rules:

1. do not change lane state by assumption during the audit
2. distinguish missing documentation from missing governed ownership
3. prefer exact file-backed contradictions over broad narrative statements

### 3. Audit moved-subfolder and runtime-proof lineage

Required outcomes:

1. any runtime proof that crosses governed lane boundaries is named exactly
2. intentional lineage reuse is separated from accidental drift
3. the `p6-ingest` fixture lineage posture is classified explicitly

Execution rules:

1. do not move or rename files in this packet
2. do not treat committed canary actuals as self-justifying governance truth
3. preserve the distinction between runtime proof, source lineage, and lane
   ownership

### 4. Publish the next-step ruling

Required outcomes:

1. one exact drift classification is published for each major surface:
   authority, Python tooling, package map, canary runtime proofs
2. one exact follow-on packet type is named, or the packet explicitly states
   that no further action is required
3. the ruling stays narrower than repo-wide restructuring

## Hard Limits

1. no TCC packet reopening inside this audit
2. no runtime code edits, subfolder moves, or package scaffolding changes
3. no ownership-map edits unless the audit proves a correction is purely
   mechanical and needs no new governance decision
4. no canary artifact deletion or regeneration in this packet
5. no deploy-worktree, hosting cutover, or parent-root publication widening

## Expected Deliverables

Return all of the following:

1. exact governance surfaces checked
2. exact moved-subfolder or cross-lane lineage surfaces checked
3. exact contradictions or omissions found
4. exact doc-only reconciliations made, if any
5. one explicit next-step ruling with packet type and reason

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| Authority bridge vs local authority-doc posture classified exactly | PASS | Pending |
| Python governance changes reconciled against lane map truthfully | PASS | Pending |
| `p6-ingest` lane and ownership posture classified exactly | PASS | Pending |
| Cross-lane runtime-proof lineage classified exactly | PASS | Pending |
| One explicit next-step ruling published | PASS | Pending |
