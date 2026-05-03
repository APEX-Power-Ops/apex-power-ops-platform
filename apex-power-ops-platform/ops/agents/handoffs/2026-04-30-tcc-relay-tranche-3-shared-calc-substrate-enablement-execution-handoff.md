# TCC Relay Tranche 3 Shared Calc Substrate Enablement Execution Handoff

Date: 2026-04-30
Status: Pre-execution boundary for the next relay slice
Authority: `Platform-Authority/TCC-RELAY-TRANCHE-3-SHARED-CALC-SUBSTRATE-ENABLEMENT-EXECUTION-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
Prior tranche closure: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-2-staged-population-and-provenance-replay-execution-completion-handoff.md`
External reviewed packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

---

## Objective

Carry the relay lane from shared-infra replay into the smallest approved
runtime slice.

Only internal calc-package models, family dispatch, typed evaluators, TCP
interpolation, and package-scoped parity tests are in scope.

---

## Mandatory Read Set

Read these surfaces before touching the calc package:

1. `Platform-Authority/TCC-RELAY-RUNTIME-ADOPTION-SCOPING-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-TRANCHE-3-SHARED-CALC-SUBSTRATE-ENABLEMENT-EXECUTION-PACKET-2026-04-30.md`
4. `apex-power-ops-platform/packages/calc-engine/README.md`
5. `apex-power-ops-platform/packages/calc-engine/src/apex_calc_engine/services/calc_engine/CALC_ENGINE_SPEC.md`
6. `apex-power-ops-platform/packages/calc-engine/tests/test_golden_fixtures.py`

---

## Canonical Scope Boundary

The next implementation move is limited to:

1. one relay read-model surface under `packages/calc-engine/src/apex_calc_engine/models/`,
2. one bounded relay calc surface under `packages/calc-engine/src/apex_calc_engine/services/calc_engine/`,
3. one focused relay golden-fixture test surface under `packages/calc-engine/tests/`.

And to internal package consumers only.

---

## Explicitly Blocked In This Slice

Do not open:

1. API routes,
2. browser code,
3. write paths,
4. deferred enrichment runtime support,
5. display-name-only dispatch,
6. analytical substitution of vendor-tabulated curves.

---

## Expected Outcome From This Handoff

If followed correctly, the next repo-native move will produce one internal relay
calc substrate inside the shared package, with explicit family dispatch,
typed evaluator coverage for the admitted executable families, TCP
interpolation over the normalized point store, and focused package-level parity
tests while API and browser surfaces remain unopened.