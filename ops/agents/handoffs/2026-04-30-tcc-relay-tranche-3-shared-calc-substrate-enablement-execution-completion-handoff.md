# TCC Relay Tranche 3 Shared Calc Substrate Enablement Execution — Completion Handoff

Date: 2026-04-30
Status: Closed PASS — Tranche 3 shared calc substrate enablement

Authoring handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-3-shared-calc-substrate-enablement-execution-handoff.md`
Authority packet: `Platform-Authority/TCC-RELAY-TRANCHE-3-SHARED-CALC-SUBSTRATE-ENABLEMENT-EXECUTION-PACKET-2026-04-30.md`
Upstream tranche planner: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`

---

## §1. Outcome

Relay Tranche 3 lands **closed PASS** in the governed shared calc-package lane.

The relay calc substrate is now implemented under:

1. `packages/calc-engine/src/apex_calc_engine/models/relay.py`
2. `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_types.py`
3. `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_dispatch.py`
4. `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_iec.py`
5. `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_swz.py`
6. `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_bsl.py`
7. `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_meq.py`
8. `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_pcd.py`
9. `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_tcp.py`
10. `packages/calc-engine/tests/test_relay_golden_fixtures.py`
11. `packages/calc-engine/tests/fixtures/relay/`

This tranche also closes the bounded relay runtime requirements fixed by the
packet:

1. canonical family dispatch is rooted in `tcc_relay_td_sections.model_code`,
2. typed evaluator implementations exist for `iec`, `swz`, `bsl`, `meq`, `pcd`, and `tcp`,
3. TCP interpolation is sourced from normalized points rather than analytical substitution,
4. unsupported families `rxd`, `lrm`, and `egc` return explicit internal unsupported outcomes.

---

## §2. Required outputs delivered

| # | Required output | Path / artifact |
|---|---|---|
| 1 | Relay ORM read-model surface | `packages/calc-engine/src/apex_calc_engine/models/relay.py` |
| 2 | Shared relay dispatch and types | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_types.py`, `relay_dispatch.py` |
| 3 | Typed relay family evaluators | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_*.py` |
| 4 | Focused relay fixture lane | `packages/calc-engine/tests/fixtures/relay/golden_curves.json` |
| 5 | Focused package validation | `packages/calc-engine/tests/test_relay_golden_fixtures.py` |
| 6 | Completion handoff | this file |

---

## §3. Files changed

| # | Surface | Action |
|---|---|---|
| 1 | `packages/calc-engine/src/apex_calc_engine/models/relay.py` | Added |
| 2 | `packages/calc-engine/src/apex_calc_engine/models/__init__.py` | Edited |
| 3 | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_types.py` | Added |
| 4 | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_dispatch.py` | Added |
| 5 | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_iec.py` | Added |
| 6 | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_swz.py` | Added |
| 7 | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_bsl.py` | Added |
| 8 | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_meq.py` | Added |
| 9 | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_pcd.py` | Added |
| 10 | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/relay_family_tcp.py` | Added |
| 11 | `packages/calc-engine/src/apex_calc_engine/services/calc_engine/__init__.py` | Edited |
| 12 | `packages/calc-engine/tests/test_relay_golden_fixtures.py` | Added |
| 13 | `packages/calc-engine/tests/fixtures/relay/golden_curves.json` | Added |

**Untouched (intentional):**

1. `apps/control-plane-api/`
2. `apps/operations-web/`
3. `infra/database/migrations/`
4. write-path and mutation surfaces
5. deferred relay enrichment tables and browser consumers

---

## §4. Verification

### Focused package checks

The relay package slice validated with the narrow package-scoped pytest lane:

1. `pytest tests/test_relay_golden_fixtures.py -q` → PASS
2. `pytest tests/test_golden_fixtures.py tests/test_relay_golden_fixtures.py -q` → PASS (`1 skipped`, no relay failures)

### Key validation facts

1. supported relay families are covered by focused offline fixtures,
2. MEQ uses the decoded GE Multilin ANSI equation form,
3. TCP interpolation follows log-log segment interpolation over normalized points,
4. unsupported families remain explicit and non-silent,
5. touched package files are editor-clean.

---

## §5. Acceptance criteria

1. ✅ Relay calc introduction is confined to the shared package file surface.
2. ✅ Dispatch uses governed family identity and not display name alone.
3. ✅ Executable family evaluators exist for all admitted Tranche 3 families.
4. ✅ TCP evaluation uses normalized point data and not synthetic analytical substitution.
5. ✅ Unsupported families remain explicit.
6. ✅ No API or browser surface opened.

---

## §6. Hard limits honored

1. ✅ No control-plane API route implementation.
2. ✅ No browser or coordination implementation.
3. ✅ No write or mutation workflow.
4. ✅ No deferred relay enrichment runtime support.
5. ✅ No display-name-only curve identity.
6. ✅ No all-at-once multi-tranche relay launch.

---

## §7. Downstream statement — Tranche 4 remains separate

This handoff closes **Tranche 3 only**.

The next truthful move is a separately authored **Tranche 4 read-only
control-plane API adoption execution packet**.

That next move must remain limited to:

1. `apps/control-plane-api/`,
2. read-only relay catalog, context, settings, and preview contracts,
3. provenance-carrying API responses consuming the now-proven shared calc package,
4. no browser or write path.

---

## §8. Bottom line

The relay lane is now past shared-infra replay and past internal calc-package
enablement. One governed relay calc substrate now exists inside the shared
package with explicit family dispatch, typed evaluators, TCP interpolation,
focused golden-fixture proof, and continued closure of API and browser layers.

The next lane is no longer Tranche 3. It is the separately governed Tranche 4
read-only control-plane API adoption slice.