# TCC ETU Stage 1 Slice Beta Breaker-Half UI And Invalidation — Execution Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-etu-stage1-slice-beta-breaker-half-ui-and-invalidation`
Status: **Closed PASS — 2026-04-29.** Slice β (frontend-only ETU breaker-half UI + cross-half advisory + step-indicator extension) lands inside contract. Three new selectors (`sel-brk-class / sel-brk-name / sel-brk-style`) consume `GET /api/v1/neta/etu/breaker-cascade` (Slice α endpoint). Client-side downstream invalidation within breaker-half + Slice-γ-boundary cross-half advisory + extended guided-step indicator (3 breaker-half + 4 trip-unit). No backend changes; no cross-half SQL wiring (Slice γ held); no DDL; no calc-engine touch; no TMT/EMT widening; no parity claim. Focused validation: 19/19 new + 32/32 adjacent ETU regression = 51/51 PASS in 1.82s. Implementation evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-BETA-BREAKER-HALF-UI-AND-INVALIDATION-IMPLEMENTATION-EVIDENCE-2026-04-29.md`. Completion handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-beta-breaker-half-ui-and-invalidation-completion-handoff.md`.

Original status (preserved): Ready for execution.
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-BETA-BREAKER-HALF-UI-AND-INVALIDATION-2026-04-29.md`
Primary contract authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-DLL-AUTHORITY-REVISION-2026-04-29.md`
Primary scoping authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-RULING-2026-04-29.md`
Alpha completion authority: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-alpha-breaker-cascade-backend-completion-handoff.md`

---

## Objective

Execute Slice beta only: add ETU-side breaker-half selectors and client-side
invalidation behavior against the already-landed read-only breaker-cascade
backend.

This handoff authorizes only the frontend-only slice scoped by the 2026-04-29
scoping ruling and unlocked by the Slice alpha closeout. It does not authorize
Slice gamma, backend cross-half wiring, schema migration, calc-engine work,
TMT/EMT widening, or parity claims.

---

## Confirmed Entry Gate

The packet is authorized because the required upstream state is already present
on disk:

1. the ETU DLL-authority revision remains active,
2. the ETU contract-reconciliation scoping lane is closed PASS,
3. Slice alpha is closed PASS,
4. the ETU breaker-cascade endpoint already exists,
5. no newer accepted artifact is present to supersede Slice beta.

If any of those statements fails when execution begins, stop and return a
blocker report rather than widening the lane implicitly.

---

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-STAGE1-SLICE-BETA-BREAKER-HALF-UI-AND-INVALIDATION-2026-04-29.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-DLL-AUTHORITY-REVISION-2026-04-29.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-RULING-2026-04-29.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
5. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-stage1-slice-alpha-breaker-cascade-backend-completion-handoff.md`
6. `source-domains/tcc_v5_backend/demo/neta_tcc.html`
7. `source-domains/tcc_v5_backend/tests/test_etu_guided_step_indicator.py`
8. `source-domains/tcc_v5_backend/tests/test_etu_breaker_context_provenance.py`
9. `source-domains/tcc_v5_backend/tests/test_etu_breaker_cascade.py`
10. `source-domains/tcc_v5_backend/services/neta/router.py`

---

## First-Code And First-Validation Anchors

Start from the ETU demo and adjacent UI validation surfaces rather than mapping
broader backend code paths.

First anchors:

1. `source-domains/tcc_v5_backend/demo/neta_tcc.html`
2. `source-domains/tcc_v5_backend/tests/test_etu_guided_step_indicator.py`
3. `source-domains/tcc_v5_backend/tests/test_etu_breaker_context_provenance.py`

Local hypothesis:

- a frontend-only selector/invalidation layer can consume the alpha endpoint
  honestly without requiring backend cross-half SQL.

Cheapest falsifying check:

- after the first substantive UI edit, run the narrowest UI-focused validation
  slice before touching authority docs or any backend surface.

---

## Execution Order

### 1. Reconfirm the boundary

Required outcomes:

1. Slice beta remains the only authorized packet in this handoff.
2. Slice gamma remains excluded.
3. No newer artifact has already executed or superseded the slice.

### 2. Implement the bounded UI slice

Required outcomes:

1. one ETU-side breaker-half selector flow exists,
2. the UI reads `GET /api/v1/neta/etu/breaker-cascade`,
3. the UI invalidates breaker-half and trip-unit-half state truthfully.

Execution rules:

1. do not add backend cross-half SQL,
2. do not add DDL,
3. do not widen into TMT or EMT UI,
4. do not claim parity.

### 3. Validate behavior narrowly

Required outcomes:

1. focused UI validation passes,
2. the existing alpha endpoint behavior remains unchanged,
3. the invalidation behavior is explicit rather than implicit.

### 4. Reconcile authority surfaces minimally

Required outcomes:

1. one implementation-evidence note is written,
2. one completion handoff is written,
3. Slice gamma remains explicitly conditional.

---

## Hard Limits

1. No backend cross-half breaker-to-trip-unit SQL wiring.
2. No schema migration or DDL.
3. No calc-engine, settings-route, calculate, evaluate, or plot changes.
4. No TMT or EMT lane edits.
5. No fabricated parity or backend capability claim.
6. No reopening of any closed ETU/SST trio, Phase 3/4/5, TASK-C, DEC-021, or
   TASK-E lane.

---

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. exact files changed,
2. exact UI and any minimal supporting surfaces updated,
3. exact tests run and results,
4. exact evidence artifact path,
5. exact completion handoff path,
6. exact downstream statement preserving Slice gamma as the separately governed
   next conditional slice.