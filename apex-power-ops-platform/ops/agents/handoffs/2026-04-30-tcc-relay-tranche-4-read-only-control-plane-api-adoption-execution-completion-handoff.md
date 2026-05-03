# TCC Relay Tranche 4 Read-Only Control-Plane API Adoption Execution — Completion Handoff

Date: 2026-04-30
Status: Closed PASS — Tranche 4 read-only control-plane API adoption

Authoring handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-4-read-only-control-plane-api-adoption-execution-handoff.md`
Authority packet: `Platform-Authority/TCC-RELAY-TRANCHE-4-READ-ONLY-CONTROL-PLANE-API-ADOPTION-EXECUTION-PACKET-2026-04-30.md`
Upstream tranche planner: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
Prior tranche closure: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-3-shared-calc-substrate-enablement-execution-completion-handoff.md`

---

## §1. Outcome

Relay Tranche 4 lands closed PASS in the mounted NETA control-plane API lane.

The relay API slice now exists under:

1. `apps/control-plane-api/services/neta/router.py`
2. `apps/control-plane-api/services/neta/schemas.py`
3. `apps/control-plane-api/tests/test_neta_relay_routes.py`
4. `apps/control-plane-api/tests/test_neta_relay_live_integration.py`

This tranche closes the bounded control-plane requirements fixed by the packet:

1. relay discovery is exposed through the already-mounted NETA router,
2. relay context and settings contracts are grounded in governed `work.tcc_relay*` surfaces,
3. preview endpoints consume the Tranche 3 shared calc package rather than duplicating evaluator logic inline,
4. provenance, family identity, storage-kind identity, and explicit unsupported outcomes are carried in the response surface,
5. writes, browser implementation, and deferred enrichment remain closed.

---

## §2. Required outputs delivered

| # | Required output | Path / artifact |
|---|---|---|
| 1 | Mounted relay read-only routes | `apps/control-plane-api/services/neta/router.py` |
| 2 | Relay request / response contracts | `apps/control-plane-api/services/neta/schemas.py` |
| 3 | Focused route contract validation | `apps/control-plane-api/tests/test_neta_relay_routes.py` |
| 4 | Conditional live integration validation | `apps/control-plane-api/tests/test_neta_relay_live_integration.py` |
| 5 | Completion handoff | this file |

---

## §3. Files changed

| # | Surface | Action |
|---|---|---|
| 1 | `apps/control-plane-api/services/neta/router.py` | Edited |
| 2 | `apps/control-plane-api/services/neta/schemas.py` | Edited |
| 3 | `apps/control-plane-api/tests/test_neta_relay_routes.py` | Added |
| 4 | `apps/control-plane-api/tests/test_neta_relay_live_integration.py` | Added |

**Untouched (intentional):**

1. `packages/calc-engine/` except as consumed shared substrate
2. `apps/operations-web/`
3. `infra/database/`
4. write-path and mutation surfaces
5. deferred relay enrichment tables and contracts

---

## §4. Verification

### Focused API checks

The bounded relay control-plane slice validated with the narrow route-scoped test lanes:

1. `pytest tests/test_neta_relay_routes.py -q` → PASS (`5 passed`)
2. `pytest tests/test_neta_relay_routes.py tests/test_neta_tmt_routes.py tests/test_neta_emt_routes.py -q` → PASS (`18 passed`)
3. `pytest tests/test_neta_relay_live_integration.py -q` → SKIP (`1 skipped`; active database lacked the governed relay work-schema surface for live proof)

### Diagnostics

No editor diagnostics remain in:

1. `apps/control-plane-api/services/neta/router.py`
2. `apps/control-plane-api/services/neta/schemas.py`
3. `apps/control-plane-api/tests/test_neta_relay_routes.py`
4. `apps/control-plane-api/tests/test_neta_relay_live_integration.py`

### Key validation facts

1. discovery, context, settings, and preview all remain read-only,
2. supported preview routes flow through `apex_calc_engine.services.calc_engine.relay_dispatch.evaluate_curve_definition`,
3. TCP preview stays point-backed and analytical families stay constant-backed,
4. unsupported families remain explicit rather than silently substituted,
5. adjacent existing NETA TMT and EMT route contracts still pass unchanged.

---

## §5. Acceptance criteria

1. ✅ Relay API introduction is confined to the authorized mounted NETA router, schema, and route-test surfaces.
2. ✅ The preview contract consumes the governed shared calc package rather than duplicating relay math inline.
3. ✅ Response contracts disclose family identity, storage-kind identity, and explicit unsupported posture.
4. ✅ Route behavior remains read-only.
5. ✅ Existing neighboring NETA route contracts remain green.
6. ✅ Browser and write surfaces remain closed.

---

## §6. Hard limits honored

1. ✅ No browser implementation.
2. ✅ No write or mutation workflow.
3. ✅ No database schema or replay edits.
4. ✅ No deferred relay enrichment runtime support.
5. ✅ No display-name-only curve identity.
6. ✅ No all-at-once multi-tranche relay launch.

---

## §7. Downstream statement — Tranche 5 remains separate

This handoff closes Tranche 4 only.

The next truthful move is a separately authored Tranche 5 browser and coordination adoption execution packet.

That next move must remain limited to:

1. `apps/operations-web/`,
2. relay browse / compare / preview browser consumers over the now-live read-only control-plane routes,
3. user-facing provenance and warning disclosures,
4. no write path and no optimizer or recommendation workflow.

---

## §8. Bottom line

The relay lane is now past shared-infra landing, staged replay, shared calc enablement, and bounded read-only control-plane adoption. One governed relay API slice now exists inside the mounted NETA router with read-only discovery, context, settings, and preview contracts that consume the shared calc package, expose provenance and storage-family identity, and preserve explicit unsupported behavior.

The next lane is no longer Tranche 4. It is the separately governed Tranche 5 browser and coordination adoption slice.