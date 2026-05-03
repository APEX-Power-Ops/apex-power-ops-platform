# TCC Runtime 015 Runtime-Contract Trio Kickoff Handoff

Date: 2026-04-26
Packet: `2026-04-26-tcc-runtime-015`
Status: **Part 1 PASS 2026-04-26 (TASK-011 / TASK-012 part 1 / TASK-013 part 1); Part 2 deferred to atomic-swap prep**
Authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-access-workflow-fidelity-1.md`
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`

## Outcome

This handoff records the runtime-contract trio after part-1 closure on 2026-04-26. TASK-011 is resolved for the runtime-contract lane: the sensor-context route exposes canonical delay-routing aliases and decoded names for the legacy `DS3_SEC3_I2T` and `DS1GF_SEC3_I2T` storage fields, `DLL_SEMANTIC_FINDINGS.md` and `DLL_END_TO_END_MAPPING.md` now carry RESOLVED disposition stamps, and the storage-column rename is explicitly deferred to Phase 5 Tier A. TASK-012 part 1 is resolved in Python via focused STPU override tests anchored on rebuilt-v2 values. TASK-013 part 1 is resolved by inheriting the linked-selection contract from the 2026-03-24 selection-model packet and surfacing degraded plug mismatch as a user-visible diagnostic warning. The remaining macro-phase is atomic-swap prep: TASK-013 part 2 for truthful rebuilt-state split-anchor fixture re-keying, then atomic swap / runtime rebind, then TASK-012 part 2 for the SQL RPC override path and post-cutover loader transition on the post-swap canonical surface, then Phase 4 acceptance.

## Packet Scope

Per the authority plan, this packet lane covers the three runtime-contract tasks that were authorized together and are now closed for part 1:

1. `TASK-011` — normalize `DS3_SEC3_I2T` and `DS1GF_SEC3_I2T` handling as delay-routing codes rather than boolean I2T flags.
2. `TASK-012` — verify and implement `DatSection3STOvr` handling.
3. `TASK-013` — define and implement the ETU linked-selection contract, narrow resolved breaker/trip-unit identity honestly, and downgrade degraded plug mismatch from synthetic routing behavior to diagnostic-only behavior.

## Current Evidence

### Authorization state

- `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE3-RUNTIME-EVIDENCE-AND-DOCS-2026-04-26.md` records TASK-008 PASS, TASK-009 PASS, and TASK-010 PASS.
- The same authority slice explicitly leaves TASK-011, TASK-012, and TASK-013 as the next authorized runtime lane.
- Atomic swap / final Phase 4 acceptance remains blocked on closure of this trio.

### Runtime-contract part-1 validation

Focused validation passed after the route test harness was corrected to stop preferring live Data API reads. Combined regression now closes the part-1 packet surface:

```text
tests/test_neta_plot_tcc.py
tests/test_sensor_context_route.py
tests/test_etu_delay_routing.py
tests/test_stpu_override_enforcement.py

59 passed, 0 failed
```

### Environment hazard discovered during validation

`NETA_PREFER_DATA_API_READS=1` can silently bypass the fake DB test seam and force `/api/v1/neta/context/{sensor_id}` through live Data API reads. The first TASK-011 pytest failure was caused by that env path, not by the alias logic. The route test now explicitly disables that preference so fixture-backed assertions hit the intended seam.

## Surfaces Changed In Part 1

`source-domains/tcc_v5_backend/services/neta/schemas.py`

- `SensorCalcContext` now carries canonical alias fields:
  - `stpu_delay_calc_code`
  - `gfpu_delay_calc_code`
  - `stpu_delay_calc_name`
  - `gfpu_delay_calc_name`
- Legacy fields `stpu_i2t` and `gfpu_i2t` remain present for compatibility, but comments now reflect that they store delay-routing codes, not simple booleans.

`source-domains/tcc_v5_backend/services/neta/router.py`

- `get_sensor_context` now copies legacy delay-routing codes into canonical aliases and derives readable names via `delay_calc_name(...)` before constructing `SensorCalcContext`.

`source-domains/tcc_v5_backend/tests/test_sensor_context_route.py`

- Fake context payload extended to include delay-routing-code examples.
- Assertions added for both legacy fields and canonical alias/name fields.
- Test harness now disables Data API preference during this test.

`source-domains/tcc_v5_backend/FULL_MIGRATION_COLUMN_MAP.md`

- `DS3_SEC3_I2T -> stpu_i2t` and `DS1GF_SEC3_I2T -> gfpu_i2t` descriptions corrected from generic I2T-flag wording to delay-routing-code semantics.

`source-domains/tcc_v5_backend/DLL_SEMANTIC_FINDINGS.md`

- Section 1 and section 2 now carry RESOLVED disposition stamps recording TASK-011 runtime-contract closure and the explicit deferral of the storage rename to Phase 5 Tier A.

`source-domains/tcc_v5_backend/DLL_END_TO_END_MAPPING.md`

- The row table and open-action items table now record the runtime-contract disposition for TASK-011 and defer the column rename to Phase 5 Tier A instead of leaving the issue open-ended.

`source-domains/tcc_v5_backend/tests/test_stpu_override_enforcement.py`

- Five focused unit tests pin the Python `ETUPickupCalculator` STPU override branch to rebuilt-v2 values (`12000 A`, asymmetric tolerance, `0.025 / 0.067 s`) without widening implementation into the SQL RPC lane.

`source-domains/tcc_v5_backend/tests/test_neta_plot_tcc.py`

- A route-level degraded-plug test now proves that `services/neta/router.py::_generate_nominal_plot_curves` appends the user-visible warning `plug_rating mismatch: using nominal curves only` rather than only logging a structured diagnostic.

`source-domains/tcc_v5_backend/services/neta/router.py`

- `_generate_nominal_plot_curves` now surfaces degraded plug mismatch as a user-visible warning while leaving the route on nominal curves only.

`source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-TASK-012-STPU-OVERRIDE-EVIDENCE-2026-04-26.md`

- Evidence packet for TASK-012 part 1, documenting the verified Python override branch, rebuilt-v2 numeric anchors, and the deferred SQL RPC parity leg.

`source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-TASK-013-LINKED-ETU-SELECTION-EVIDENCE-2026-04-26.md`

- Evidence packet for TASK-013 part 1, documenting inherited linked-selection authority, degraded-plug diagnostic reclassification, and the deferred rebuilt-state fixture re-keying leg.

## Deferred Runtime Work

### TASK-011 follow-on

- No additional runtime-contract implementation remains open in part 1.
- Storage rename to `stpu_delay_calc_code` / `gfpu_delay_calc_code` remains intentionally deferred to Phase 5 Tier A so the validated rebuilt baseline is not blurred by early nomenclature refactoring.

### TASK-012 part 2

- Implement and validate the SQL RPC `fn_calculate_test_currents` override branch so the route/database path matches the now-proven Python `ETUPickupCalculator` behavior.
- Transition the override loader from the interim EAV shape to the post-cutover flat shape during atomic-swap prep.
- Keep proof anchored on rebuilt-valid fixtures, not pre-rebuild sensor IDs.

### TASK-013 part 2

- Complete full `6258` to truthful rebuilt-state split-anchor fixture re-keying with rebuilt-state golden values, replacing the current caveat-banner bridge.
- Preserve the linked-selection contract already inherited from the 2026-03-24 packet; do not reopen that model unless rebuilt-state fixture proof forces a narrower repair.
- Keep degraded plug mismatch in diagnostic-only mode while re-keying the golden surfaces.

## Fixture And Reference Gate

Sensor `6258` is absent from the rebuilt v2 corpus and cannot support rebuilt-state closure claims for TASK-011/012/013. The earlier single-anchor `11442` assumption is superseded by the Runtime 016 split-anchor decision: use SensorID `4604` for pickup/cascade proof, SensorID `4174` for IEEE-depth proof, and keep `test_calc_engine.py` as historical executable lineage rather than the active pytest proof lane. Before broadening validation, re-anchor stale `6258` surfaces, especially:

- `source-domains/tcc_v5_backend/test_calc_engine.py`
- `source-domains/tcc_v5_backend/packages/calc-engine/src/calc_engine/docs/CALC_ENGINE_SPEC.md`
- any remaining runtime docs or prompts still asserting rebuilt-state proof through `6258`

Until that re-anchor is complete, treat any successful check tied to `6258` as pre-rebuild historical evidence only.

## Hard Limits

- `D:\TCC_NEW.accdb` remains the sole behavioral authority.
- Do not reopen TASK-008/009/010 except to cite their evidence.
- Do not treat the currently deferred storage rename as part of the runtime-contract closure; that rename belongs to Phase 5 Tier A only.
- Do not implement Phase 5 normalization tables/views/materializations under this packet; only runtime-contract behavior and contract wording belong here.
- Do not use pre-rebuild sensor `6258` as rebuilt-state proof.

## Merge Gate

| Gate | Result |
|---|---|
| Runtime-contract trio handoff created | PASS |
| TASK-011 sensor-context alias slice implemented | PASS |
| Focused pytest for route + delay dispatch | PASS — 20 passed |
| Data API preference hazard identified and bounded in tests | PASS |
| TASK-011 sweep — DLL_SEMANTIC_FINDINGS.md / DLL_END_TO_END_MAPPING.md disposition stamps | PASS — RESOLVED stamps applied 2026-04-26 |
| TASK-012 part 1 — Python `ETUPickupCalculator` override branch verified | PASS — `tests/test_stpu_override_enforcement.py` 5/5 |
| TASK-012 part 2 — SQL RPC override + post-cutover loader | DEFERRED (atomic-swap prep) |
| TASK-013 part 1 — degraded-plug diagnostic surface | PASS — `tests/test_neta_plot_tcc.py::TestGoldenDegradedPlugMismatch` 2/2 |
| TASK-013 part 2 — full 6258 → split-anchor fixture re-keying | DEFERRED (atomic-swap prep) — caveat banners applied to spec / tests / docstrings |
| Combined regression: plot-tcc + sensor-context + delay-routing + stpu-override | PASS — 59/59 |
| 6258 rebuilt-state references re-anchored (caveat banners) | PASS |
| 6258 → split-anchor full golden re-keying | DEFERRED (atomic-swap prep) |
| Phase 4 runtime-contract trio closed (parts 1) | PASS — 2026-04-26 |
| Atomic swap | DEFERRED (next macro-phase) |

## Recommended Next Execution Order

1. Execute TASK-013 part 2 by re-keying rebuilt-state fixtures from `6258` to the approved split anchors and replacing caveat-banner bridges with rebuilt-state golden values.
2. Perform the atomic swap (`*_v2` to canonical) only after TASK-013 part 2 is closed truthfully.
3. Execute TASK-012 part 2 in the SQL RPC / post-cutover loader lane on the post-swap canonical runtime, using the already-proven Python STPU override behavior as the contract anchor.
4. Run Phase 4 acceptance evidence on the post-swap canonical surface.

## Frontier Disposition

The runtime-contract frontier's part-1 work is fully drained as of 2026-04-26.

- TASK-011: sensor-context alias slice + DLL_SEMANTIC_FINDINGS.md / DLL_END_TO_END_MAPPING.md disposition stamps PASS. Storage column rename to `*_delay_calc_code` deferred to Phase 5 Tier A.
- TASK-012: Python `ETUPickupCalculator` override branch verified PASS via 5 focused unit tests anchored on rebuilt-v2 numeric values. SQL RPC `fn_calculate_test_currents` override gap and post-cutover EAV→flat shape transition deferred to TASK-012 part 2 alongside atomic swap.
- TASK-013: linked-selection contract inherited from 2026-03-24 selection-model packet; degraded-plug reclassification implemented in `services/neta/router.py`; new diagnostic test PASS; combined regression 59/59. Full 6258 → split-anchor fixture re-keying deferred to atomic-swap prep (caveat banners applied to spec and test surfaces).

Atomic swap, TASK-012 part 2 (SQL RPC + post-cutover loader), TASK-013 part 2 (rebuilt-state fixture re-keying), and Phase 4 acceptance are the next authorized macro-phase frontiers.

Evidence:

- `Development/Platform/TCC/TCC-FIDELITY-PHASE3-TASK-012-STPU-OVERRIDE-EVIDENCE-2026-04-26.md`
- `Development/Platform/TCC/TCC-FIDELITY-PHASE3-TASK-013-LINKED-ETU-SELECTION-EVIDENCE-2026-04-26.md`