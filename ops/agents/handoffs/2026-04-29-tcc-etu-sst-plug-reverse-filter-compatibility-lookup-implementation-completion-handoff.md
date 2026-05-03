# TCC ETU / SST Plug Reverse-Filter Compatibility Lookup Implementation — Completion Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-etu-sst-plug-reverse-filter-compatibility-lookup-implementation`
Status: **Closed PASS — bounded mixed-surface implementation slice landed**

Authority task: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-PLUG-REVERSE-FILTER-COMPATIBILITY-LOOKUP-IMPLEMENTATION-2026-04-29.md`
Execution handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-sst-plug-reverse-filter-compatibility-lookup-implementation-handoff.md`
Scoping authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-REMAINING-GAP-SCOPING-RULING-2026-04-29.md`
Implementation evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-PLUG-REVERSE-FILTER-COMPATIBILITY-LOOKUP-IMPLEMENTATION-EVIDENCE-2026-04-29.md`

---

## Summary

Surface B of the 2026-04-29 remaining-gap scoping ruling landed as a bounded
ETU-only compatibility-validation control. One new backend route and one
small UI affordance answer the inverse of the existing forward plug filter:
"which sensors in the current upstream scope accept this plug rating?"

Plug remains downstream of upstream identity resolution. The route is **not**
wired into the cascade selector chain. The ruling's bounded-posture wording
is emitted as a server-side `advisory` string and rendered verbatim by the UI.

No schema, migration, calc-engine, TMT, or EMT change was made. No parity
claim is made.

---

## Files Touched

### Written

1. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-PLUG-REVERSE-FILTER-COMPATIBILITY-LOOKUP-IMPLEMENTATION-EVIDENCE-2026-04-29.md` — implementation evidence.
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-sst-plug-reverse-filter-compatibility-lookup-implementation-completion-handoff.md` — this handoff.
3. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-PLUG-REVERSE-FILTER-COMPATIBILITY-LOOKUP-IMPLEMENTATION-2026-04-29.md` — Status line + Completion Record append.

### Modified

4. `source-domains/tcc_v5_backend/services/neta/schemas.py` — added
   `SensorMatchingPlug` and `SensorsMatchingPlugResponse` Pydantic models.
5. `source-domains/tcc_v5_backend/services/neta/router.py` — schema imports
   plus `GET /api/v1/neta/etu/sensors-matching-plug` route.
6. `source-domains/tcc_v5_backend/demo/neta_tcc.html` — `#plug-compat-row`
   markup under `#etu-row-plug`, `selectedPlugValue` /
   `syncPlugCompatibilityControl` / `runPlugCompatibilityCheck` /
   `renderPlugCompatibilityResult` JS, change listener on `#set-plug`,
   click listener on `#btn-plug-compat-check`, and a `syncPlugCompatibility
   Control()` call inside `loadSettings(...)`.

### Created

7. `source-domains/tcc_v5_backend/tests/test_etu_plug_reverse_filter.py` —
   four pytest cases covering route contract, advisory wording, validation,
   and bound-parameter scope.

No schema migration was authored.

---

## Validation / Inspection Step Run

### A. SQL inspection — canonical join shape

Confirmed `tcc_etu_plugs ⨝ vw_trip_unit_cascade` returns exactly 4 sensors
for `plug_value=800, trip_style_id=3` (GE · MVT RMS-9 · ICCB family — sensor
descriptions `800`, `1000`, `1600`, `2000`). The `tcc_etu_plugs` table has
exactly three columns (`sensor_id`, `value`, `created_at`); the natural-key
join is unambiguous.

### B. Pytest — bounded contract validation

```
tests/test_etu_plug_reverse_filter.py::test_reverse_filter_returns_compatible_sensors_with_advisory PASSED
tests/test_etu_plug_reverse_filter.py::test_reverse_filter_empty_result_still_returns_advisory PASSED
tests/test_etu_plug_reverse_filter.py::test_reverse_filter_rejects_non_positive_plug_value PASSED
tests/test_etu_plug_reverse_filter.py::test_reverse_filter_passes_full_upstream_scope_to_sql PASSED
4 passed in 2.11s
```

### C. Adjacent regression — cascade route remains green

With `NETA_PREFER_DATA_API_READS=false` (the standard test posture):

```
tests/test_cascade_route.py::test_cascade_returns_cross_filtered_option_sets PASSED
tests/test_cascade_route.py::test_cascade_leaves_sensor_options_empty_until_style_selected PASSED
tests/test_cascade_route.py::test_cascade_sensor_filter_revalidates_exact_path PASSED
tests/test_cascade_route.py::test_cascade_surfaces_zero_match_empty_state PASSED
tests/test_etu_plug_reverse_filter.py::* PASSED (4)
8 passed in 1.35s
```

The `.env` default `NETA_PREFER_DATA_API_READS=true` is a pre-existing
environment-only issue that forces the cascade route into REST fallback in
fake-DB tests; it predates this slice and is unrelated.

---

## Acceptance Criteria Trace

| Criterion | Status |
|---|---|
| 1. A bounded plug-aware reverse-filter compatibility lookup exists for ETU/SST | PASS |
| 2. Plug remains downstream and is not promoted to an upstream selector | PASS |
| 3. The UI affordance is clearly compatibility-validation only | PASS — server-emitted advisory rendered verbatim, button title disclosure, no cascade dependency |
| 4. At least one focused executable validation step is run | PASS — 4 pytest + 1 SQL inspection |
| 5. No schema, TMT, EMT, or parity widening occurs | PASS |

---

## Out-Of-Scope Items Explicitly Not Touched

1. Plug promotion to an upstream cascade selector — explicitly excluded by
   ruling and by code structure (no cascade-selector dependency on the new
   route).
2. Schema or migration changes — none.
3. `fn_sensor_available_settings(sensor_id)` or other forward-filter SQL —
   unchanged.
4. Guided-selection step-indicator UI (Surface A + D) — separate slice.
5. Breaker-context provenance disclosure (Surface C) — separate slice.
6. TMT or EMT routes / UI — unchanged.
7. Parity claim against EasyPower — none.

---

## Exact Closure Ruling

Surface B is **closed PASS**. The bounded backend route plus the small
compatibility-validation UI affordance honor every scope-lock and
exclusion in the 2026-04-29 ruling:

1. Plug is not promoted to an upstream selector.
2. The route is mixed (one new BE + one small UI), not widened.
3. The audit-mandated bounded-posture wording is server-emitted as the
   `advisory` field and rendered verbatim by the UI.
4. No schema, calc-engine, TMT, EMT, or parity changes were made.

This handoff does not pre-authorize follow-on work on Surfaces A/D or C —
those remain separately governed packets per the ruling.

The user remains the next authorizing party for the remaining slices.
