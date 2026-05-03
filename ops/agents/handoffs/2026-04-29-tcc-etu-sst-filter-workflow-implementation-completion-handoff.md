# TCC ETU / SST Filter-Workflow Implementation — Completion Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-etu-sst-filter-workflow-implementation`
Status: **Closed PASS — bounded cascade-terminal invalidation slice landed inside contract; no parity claim made**

Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-FILTER-WORKFLOW-IMPLEMENTATION-2026-04-29.md`
Execution handoff: `ops/agents/handoffs/2026-04-29-tcc-etu-sst-filter-workflow-implementation-handoff.md`
Workflow audit anchor: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-FILTER-WORKFLOW-IMPLEMENTATION-EVIDENCE-2026-04-29.md`

---

## Summary

The bounded ETU / SST filter-workflow implementation slice executed end to
end. The truthful result on disk is that the cascade-terminal invalidation
gap identified by the 2026-04-29 EasyPower audit (Gap 2 / Gap 3 — plug
edge of `mfr → type → style → sensor → curve / plug`) is now closed.

Frontend-only change. No backend, schema, or calc-engine work was
performed. No widening into TMT, EMT, or other settings inputs. No parity
claim is made.

A focused executable validation step was run and PASSES. The two
analogous prior cascade-invalidation tests still PASS.

---

## What Was Already In Compliance

Surface discovery confirmed that several pieces of the audited contract
were already satisfied before this slice (full enumeration in the
evidence document). Highlights:

1. Backend `/api/v1/neta/cascade` already cross-filters the
   manufacturer / type / style / sensor chain via `vw_trip_unit_cascade`.
2. Frontend `syncSelectOptions` already preserves a previous selection
   only when still valid in the new option list — matches EasyPower
   `dvlSSTPopulateSensorCombo` semantics.
3. Plug values already arrive only via `/api/v1/neta/settings/{sensor_id}`,
   the runtime equivalent of the audit's exact-SQL anchor
   `SELECT PlugVal FROM DatPlugs WHERE SensorID = ?`.
4. Curves are already not exposed as a top-level user selector; they are
   generated at calculate-time keyed against the resolved sensor record.
5. Sensor-change invalidation of stale execution sections already worked
   via `clearEtuExecutionState`.

The only uncovered link in the audited cascade chain was the **plug
terminal** — changing plug after a calculate / evaluate / TCC-plot left
those sections visible even though the results were computed against the
previous plug rating.

---

## What Changed

### Files modified

1. `tcc_v5_backend/demo/neta_tcc.html`
   - Added `clearEtuStaleExecutionResults` helper (≈14 lines, near line
     1052) — hides only the execution-result sections (calc, eval, TCC)
     and disables export / save-result, leaving identity, settings panel,
     cascade, and active plan untouched.
   - Added one change listener:
     `$('set-plug').addEventListener('change', clearEtuStaleExecutionResults);`
     near line 1161.
2. `tcc_v5_backend/tests/test_demo_browser.py`
   - Added `test_etu_plug_change_clears_stale_execution_sections`
     (≈260 lines, modeled on the existing
     `test_etu_upstream_sensor_change_clears_stale_execution_sections`).

No other files were touched.

### Why plug-only and not all settings inputs

The audit's Gap 2 explicitly enumerates the cascade chain as
**manufacturer → type → style → sensor → curve / plug**. Plug is named as
the cascade terminal because EasyPower fetches it from a catalog
(`DatPlugs`) keyed against resolved sensor identity. The other settings
inputs (LTPU, STD, INST, GFPU, etc.) are operator-tuned setpoints, not
cascade-catalog options. Treating them as part of the cascade would
overstate the audit's scope.

This is recorded so a future widener has the contract reasoning, not just
the code.

---

## Focused Validation Step

```
cd /c/APEX\ Platform/source-domains/tcc_v5_backend
.venv/Scripts/pytest.exe \
  tests/test_demo_browser.py::TestDemoBrowserWorkflow::test_etu_plug_change_clears_stale_execution_sections -v
```

Result: `1 passed, 1 warning in 9.97s`.

The new test drives a real Chromium browser through:

1. Cascade narrowing `GE → MVT RMS-9 → ICCB → sensor 25`.
2. Pick `plug=800`, fill measured LTPU, click Calculate then TCC.
3. Assert `calc-section`, `eval-section`, `tcc-section` are visible.
4. Change `plug=600`.
5. Assert all three execution sections become hidden, `btn-export` and
   `btn-save-result` become disabled, and `sensor-summary` /
   `settings-section` / sensor selection / new plug selection remain
   intact.

### Regression check

Re-ran the analogous prior browser tests — both PASS:

- `test_etu_upstream_sensor_change_clears_stale_execution_sections`
- `test_etu_sensor_change_hides_non_applicable_rows_and_clears_stale_values`

Pre-existing live-data integration failures observed (unrelated to this
slice — backend SQL schema drift in
`fn_sensor_available_settings` returning HTTP 400
`column pl.trip_style_id does not exist`):

- `test_cascade_route.py` (4 failures)
- `test_demo_browser.py::test_preset_populates_cascade_dropdowns`

This slice did not touch any backend code, schema, or RPC. These failures
predate the change and are recorded as observed-but-unrelated.

---

## Acceptance Criteria Trace

| Criterion | Status |
|---|---|
| 1. ETU / SST lane behaves as dependency-aware cascade | PASS — already true; plug terminal now closes the chain. |
| 2. Upstream identity changes invalidate stale downstream selections | PASS — existing for mfr/type/style/sensor; new for plug. |
| 3. Curve and plug remain downstream of resolved ETU / SST identity | PASS — already in compliance; not regressed. |
| 4. Breaker context remains bounded additive context | PASS — no breaker-side hierarchy introduced. |
| 5. At least one focused executable validation step run | PASS — see above. |
| 6. Evidence and completion handoff map back to authority chain | PASS — both documents author audit and planning citations. |
| 7. No TMT or EMT widening | PASS — zero edits to TMT or EMT branches. |
| 8. No parity claim | PASS — explicitly disclaimed. |

---

## Decision Boundary Answers

The handoff's Decision Boundary asked four questions. They answer:

1. **Did the ETU / SST cascade-restoration slice land inside the accepted
   audit and ETU runtime-planning contract?** Yes.
2. **Were curve and plug restored as dependent downstream outputs rather
   than independent peers?** Yes — already in compliance; this slice
   strengthens the dependency edge by enforcing stale-result invalidation
   on plug change.
3. **Were TMT and EMT kept out of scope?** Yes — zero edits.
4. **Is the ETU / SST lane now ready for later separate parity or broader
   family-lane work, without claiming that parity now exists?** Yes —
   parity is explicitly not claimed; future audits remain separately
   authorizable.

---

## Out-Of-Scope Items Explicitly Not Touched

1. TMT cascade — no edits.
2. EMT cascade — no edits.
3. Schema or migrations — none.
4. Calc-engine or curve-formula semantics — none.
5. Backend router endpoints, schemas, or RPCs — none.
6. Parity acceptance — not claimed.
7. Full breaker-side runtime hierarchy — not introduced.
8. Plug-aware reverse filtering (audit §9) — explicitly deferred per
   the audit as "advanced compatibility behavior."
9. Other settings inputs (LTPU, STD, etc.) — explicitly outside the
   audit-named cascade chain.

---

## Exact Closure Ruling

The bounded ETU / SST cascade-restoration slice is closed PASS.

Recorded truths on disk:

1. The plug terminal of the audited cascade now invalidates stale
   downstream execution-result sections on change, satisfying audit Gap 2
   for the previously uncovered link.
2. The acceptance test
   `test_etu_plug_change_clears_stale_execution_sections` proves the new
   behavior end-to-end through a real browser.
3. No regressions in the analogous prior cascade-invalidation tests.
4. No backend, schema, or calc-engine work was done.
5. No parity claim is made.

The next honest move, if the user chooses to continue, remains the
bounded options the original audit document recommended:

- audit the current TCC front-end and backend endpoints against the
  seven required support surfaces listed by the audit, OR
- author a separately governed packet for the remaining gap surface
  (richer DAT-family SQL surfacing, plug-aware reverse filtering,
  broader breaker-half representation).

This completion handoff does not pre-authorize either move.
