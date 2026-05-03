# TCC Relay Tranche 4 Read-Only Control-Plane API Adoption Execution Handoff

Date: 2026-04-30
Status: Pre-execution boundary for the next relay slice
Authority: `Platform-Authority/TCC-RELAY-TRANCHE-4-READ-ONLY-CONTROL-PLANE-API-ADOPTION-EXECUTION-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
Prior tranche closure: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-3-shared-calc-substrate-enablement-execution-completion-handoff.md`
External reviewed packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

---

## Objective

Carry the relay lane from internal shared calc enablement into the smallest
approved control-plane contract slice.

Only read-only NETA router endpoints, relay response schemas, route tests, and
shared-calc consumption are in scope.

---

## Mandatory Read Set

Read these surfaces before touching the control-plane API:

1. `Platform-Authority/TCC-RELAY-RUNTIME-ADOPTION-SCOPING-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-TRANCHE-4-READ-ONLY-CONTROL-PLANE-API-ADOPTION-EXECUTION-PACKET-2026-04-30.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-3-shared-calc-substrate-enablement-execution-completion-handoff.md`
5. `apex-power-ops-platform/apps/control-plane-api/main.py`
6. `apex-power-ops-platform/apps/control-plane-api/services/neta/router.py`
7. `apex-power-ops-platform/apps/control-plane-api/services/neta/schemas.py`
8. `apex-power-ops-platform/apps/control-plane-api/tests/test_neta_tmt_routes.py`
9. `apex-power-ops-platform/apps/control-plane-api/tests/test_neta_emt_routes.py`

---

## Canonical Scope Boundary

The next implementation move is limited to:

1. one bounded relay route surface under `apps/control-plane-api/services/neta/router.py`,
2. one bounded relay schema surface under `apps/control-plane-api/services/neta/schemas.py`,
3. focused relay route tests under `apps/control-plane-api/tests/`.

And to read-only API consumers only.

---

## Explicitly Blocked In This Slice

Do not open:

1. browser code,
2. write paths,
3. deferred enrichment runtime support,
4. inline relay math that bypasses the shared calc package,
5. display-name-only curve identity,
6. analytical substitution of vendor-tabulated curves.

---

## Expected Outcome From This Handoff

If followed correctly, the next repo-native move will produce one bounded
read-only relay API slice inside the existing NETA router, with search,
context, settings, and preview contracts that consume the governed shared
calc package, surface provenance and storage-family identity, preserve
explicit unsupported-family behavior, and leave browser and write surfaces
closed.