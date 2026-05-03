# TCC ETU Stage 1 Slice Alpha Breaker-Cascade Backend — Execution Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-etu-stage1-slice-alpha-breaker-cascade-backend`
Status: **Closed PASS — 2026-04-29.** Slice α (read-only ETU-distinct breaker-half cascade backend) lands inside contract. New endpoint `GET /api/v1/neta/etu/breaker-cascade` mirrors the EasyPower DLL `FindMatchingBreakerStyles` (DeviceLibrary.cs:403) join shape via `UNION ALL` across ICCB / MCCB / PCB inside CTE `etu_breaker_combined` over existing `tcc_brk_*` tables. No HTML, no DDL, no cross-half wiring (Slice γ held), no frontend (Slice β held), no parity claim. Focused validation: 8/8 new + 24/24 adjacent ETU regression = 32/32 PASS in 3.57s. Implementation evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-IMPLEMENTATION-EVIDENCE-2026-04-29.md`. Completion handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-alpha-breaker-cascade-backend-completion-handoff.md`.

Original status (preserved): Ready for execution.
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-2026-04-29.md`
Primary contract authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-DLL-AUTHORITY-REVISION-2026-04-29.md`
Primary scoping authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-RULING-2026-04-29.md`

---

## Objective

Execute Slice alpha only: add the ETU lane's missing Stage 1 read-only
breaker-cascade backend over the existing `tcc_brk_*` tables.

This handoff authorizes only the bounded backend-support slice scoped by the
2026-04-29 scoping ruling. It does not authorize Slice beta, Slice gamma,
frontend work, cross-half wiring, schema migration, calc-engine work, TMT/EMT
widening, or parity claims.

---

## Confirmed Entry Gate

The packet is authorized because the required upstream state is already present
on disk:

1. the ETU DLL-authority revision remains active,
2. the ETU contract-reconciliation scoping lane is closed PASS,
3. the scoping ruling states that Slice alpha is the first later execution
   packet,
4. the scoping completion handoff repeats the same downstream ruling,
5. no newer accepted artifact is present to supersede Slice alpha.

If any of those statements fails when execution begins, stop and return a
blocker report rather than widening the lane implicitly.

---

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-2026-04-29.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-DLL-AUTHORITY-REVISION-2026-04-29.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-RULING-2026-04-29.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
5. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-contract-reconciliation-runtime-gap-scoping-completion-handoff.md`
6. `source-domains/neta-ett-study-material/Development/DLL_END_TO_END_MAPPING.md`
7. `source-domains/neta-ett-study-material/Development/DLL_SEMANTIC_FINDINGS.md`
8. `source-domains/tcc_v5_backend/IMPLEMENTATION_STATUS.md`
9. `source-domains/tcc_v5_backend/services/neta/router.py`
10. `source-domains/tcc_v5_backend/services/neta/schemas.py`
11. `source-domains/tcc_v5_backend/tests/test_cascade_route.py`

---

## First-Code And First-Validation Anchors

Start from the nearest ETU route and schema surfaces rather than browsing the
whole repo.

First anchors:

1. `source-domains/tcc_v5_backend/services/neta/router.py`
2. `source-domains/tcc_v5_backend/services/neta/schemas.py`
3. `source-domains/tcc_v5_backend/tests/test_cascade_route.py`

Local hypothesis:

- a read-only ETU breaker-cascade endpoint can restore Stage 1 honestly with no
  frontend changes and no cross-half wiring if it stays rooted on existing
  breaker tables and returns only breaker-half identity surfaces.

Cheapest falsifying check:

- after the first substantive route/schema edit, run the narrowest focused
  breaker-cascade tests before touching any wider runtime or authority surface.

---

## Execution Order

### 1. Reconfirm the boundary

Required outcomes:

1. Slice alpha remains the only authorized packet in this handoff.
2. Slice beta and Slice gamma remain excluded.
3. No newer artifact has already executed or superseded the slice.

### 2. Implement the bounded backend slice

Required outcomes:

1. one ETU-specific read-only breaker-cascade endpoint exists,
2. one matching schema set exists,
3. the route reads existing `tcc_brk_*` and `tcc_manufacturers` tables only.

Execution rules:

1. do not reuse TMT browse helpers for ETU,
2. do not add frontend work,
3. do not add DDL or migrations,
4. do not wire breaker-half filters into trip-unit-half filters.

### 3. Validate behavior narrowly

Required outcomes:

1. focused endpoint tests pass,
2. empty-state behavior is explicit,
3. at least one filter-happy-path proof and one upstream-scope proof exist.

### 4. Reconcile authority surfaces minimally

Required outcomes:

1. one implementation-evidence note is written,
2. one completion handoff is written,
3. Slice beta and Slice gamma remain explicitly conditional follow-ons.

---

## Hard Limits

1. No HTML or other frontend changes.
2. No cross-half breaker-to-trip-unit wiring.
3. No schema migration or DDL.
4. No reuse of TMT browse helpers as the ETU implementation surface.
5. No calc-engine, settings-route, calculate, evaluate, or plot changes.
6. No TMT or EMT lane edits.
7. No fabricated breaker hierarchy or parity claim.
8. No reopening of any closed ETU/SST trio, Phase 3/4/5, TASK-C, DEC-021, or
   TASK-E lane.

---

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. exact files changed,
2. exact route and schema surfaces added or updated,
3. exact tests run and results,
4. exact evidence artifact path,
5. exact completion handoff path,
6. exact downstream statement preserving Slice beta and Slice gamma as
   separately governed follow-ons.