# Decision-012 Phase 3 Breaker Repoint Closeout

Dispatch: `2026-05-30-cc-d012-phase3-breaker-repoint`
Executor: Codex
Date: 2026-05-31
Status: Complete. Breaker app SQL is repointed to `tcc.*`; relay was left untouched.

## Claim

- Claim commit pushed: `3055589a` (`claim: 2026-05-30-cc-d012-phase3-breaker-repoint by codex`)
- Repoint commit pushed: `70c7127a` (`fix: repoint breaker SQL to tcc schema`)
- Predecessor was already done: `2026-05-30-cc-d012-phase2-expand-rerun`
- Live credential value was not printed.
- No DB DDL, migrations, function bodies, or views were changed.

## Enumeration

Exact pre-change scan at the claim commit found 218 old breaker table tokens across the enumerated control-plane Python surface (`services/neta`, `scripts`, and `tests`). Of those, 189 were in the files edited by this phase and are now zero in those edited files.

| Table | Total | Files |
| --- | ---: | --- |
| `tcc_brk_iccb` | 4 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 1<br>`apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_brk_iccb_styles` | 4 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 1<br>`apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_brk_mccb` | 4 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 1<br>`apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_brk_mccb_styles` | 4 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 1<br>`apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_brk_pcb` | 4 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 1<br>`apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_brk_pcb_styles` | 4 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 1<br>`apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_emt` | 17 | `apps/control-plane-api/scripts/check_schema_drift.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 13<br>`apps/control-plane-api/tests/test_neta_emt_live_integration.py`: 1 |
| `tcc_emt_band_names` | 11 | `apps/control-plane-api/scripts/check_schema_drift.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 7<br>`apps/control-plane-api/tests/test_neta_emt_live_integration.py`: 1 |
| `tcc_emt_curves` | 10 | `apps/control-plane-api/scripts/check_schema_drift.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 6<br>`apps/control-plane-api/tests/test_neta_emt_live_integration.py`: 1 |
| `tcc_emt_frame_amps` | 11 | `apps/control-plane-api/scripts/check_schema_drift.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 7<br>`apps/control-plane-api/tests/test_neta_emt_live_integration.py`: 1 |
| `tcc_emt_frames` | 14 | `apps/control-plane-api/scripts/check_schema_drift.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 10<br>`apps/control-plane-api/tests/test_neta_emt_live_integration.py`: 1 |
| `tcc_emt_pickups` | 10 | `apps/control-plane-api/scripts/check_schema_drift.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 6<br>`apps/control-plane-api/tests/test_neta_emt_live_integration.py`: 1 |
| `tcc_emt_sections` | 12 | `apps/control-plane-api/scripts/check_schema_drift.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 8<br>`apps/control-plane-api/tests/test_neta_emt_live_integration.py`: 1 |
| `tcc_etu_gfd_bands` | 10 | `apps/control-plane-api/services/neta/router.py`: 7<br>`apps/control-plane-api/tests/test_neta_plot_tcc.py`: 2<br>`apps/control-plane-api/tests/test_settings_route.py`: 1 |
| `tcc_etu_gfpu_pickups` | 4 | `apps/control-plane-api/scripts/audit_etu_ground_variants.py`: 1<br>`apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_settings_route.py`: 1 |
| `tcc_etu_inst_pickups` | 3 | `apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_settings_route.py`: 1 |
| `tcc_etu_ltd_bands` | 10 | `apps/control-plane-api/services/neta/router.py`: 7<br>`apps/control-plane-api/tests/test_neta_plot_tcc.py`: 2<br>`apps/control-plane-api/tests/test_settings_route.py`: 1 |
| `tcc_etu_ltpu_multipliers` | 3 | `apps/control-plane-api/services/neta/router.py`: 1<br>`apps/control-plane-api/services/neta/schemas.py`: 1<br>`apps/control-plane-api/tests/test_settings_route.py`: 1 |
| `tcc_etu_ltpu_pickups` | 3 | `apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_settings_route.py`: 1 |
| `tcc_etu_plugs` | 9 | `apps/control-plane-api/scripts/audit_etu_ground_variants.py`: 1<br>`apps/control-plane-api/services/neta/router.py`: 4<br>`apps/control-plane-api/tests/test_cascade_route.py`: 3<br>`apps/control-plane-api/tests/test_settings_route.py`: 1 |
| `tcc_etu_sensor_maint` | 8 | `apps/control-plane-api/scripts/audit_etu_ground_variants.py`: 3<br>`apps/control-plane-api/scripts/probe_maint_reduction_evidence.py`: 2<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/schemas.py`: 1 |
| `tcc_etu_sensors` | 6 | `apps/control-plane-api/scripts/audit_etu_ground_variants.py`: 3<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_etu_settings` | 1 | `apps/control-plane-api/scripts/check_schema_drift.py`: 1 |
| `tcc_etu_std_bands` | 10 | `apps/control-plane-api/services/neta/router.py`: 7<br>`apps/control-plane-api/tests/test_neta_plot_tcc.py`: 2<br>`apps/control-plane-api/tests/test_settings_route.py`: 1 |
| `tcc_etu_stpu_pickups` | 3 | `apps/control-plane-api/services/neta/router.py`: 2<br>`apps/control-plane-api/tests/test_settings_route.py`: 1 |
| `tcc_manufacturers` | 10 | `apps/control-plane-api/scripts/audit_etu_ground_variants.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 6<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_tmt_amps` | 6 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 3<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_tmt_curves` | 3 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_tmt_frames` | 8 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 4<br>`apps/control-plane-api/services/neta/router.py`: 3<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_tmt_settings` | 3 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_tmt_thermal_adj` | 3 | `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2<br>`apps/control-plane-api/tests/test_neta_tmt_live_integration.py`: 1 |
| `tcc_trip_styles` | 3 | `apps/control-plane-api/scripts/audit_etu_ground_variants.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2 |
| `tcc_trip_types` | 3 | `apps/control-plane-api/scripts/audit_etu_ground_variants.py`: 1<br>`apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py`: 2 |

Zero occurrences in the enumerated app SQL surface: `tcc_etu_gfd_equations`, `tcc_etu_inst_curves`, `tcc_etu_ltd_params`, `tcc_etu_sensor_params`, `tcc_etu_std_equations`, `tcc_etu_stpu_overrides`.

No ambiguous SQL table hits were found. Relay references (`work.tcc_relay_*`, `tcc_relay_*`) and non-table tokens such as route fields were left untouched.

The post-change app scan still shows only non-runtime/table-list/comment old tokens in `check_schema_drift.py`, the live integration availability lists, and two comments/docstrings in `schemas.py`.

## Diff Summary

| File | Exact old table refs before | Exact old table refs after |
| --- | ---: | ---: |
| `apps/control-plane-api/services/neta/router.py` | 116 | 0 |
| `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py` | 42 | 0 |
| `apps/control-plane-api/scripts/audit_etu_ground_variants.py` | 11 | 0 |
| `apps/control-plane-api/scripts/probe_maint_reduction_evidence.py` | 2 | 0 |
| `apps/control-plane-api/tests/test_cascade_route.py` | 3 | 0 |
| `apps/control-plane-api/tests/test_settings_route.py` | 9 | 0 |
| `apps/control-plane-api/tests/test_neta_plot_tcc.py` | 6 | 0 |

Also adjusted `_get_table_columns()` in `router.py` so schema-qualified names such as `tcc.etu_sensors` query `information_schema.columns` with both schema and table name.

## Local Validation

| Check | Result |
| --- | --- |
| Focused pytest slice | PASS: `73 passed, 1 warning in 0.84s` |
| Py compile for edited route/tests/scripts | PASS |
| `scripts/probe_maint_reduction_evidence.py` | PASS: `total_rows=2572`, reduction/key counts all `0` |
| `scripts/validate_lv_breaker_phase3_families.py` | PASS: `result=PASS` |

Focused pytest command:

```bash
cd apps/control-plane-api
PYTHONPATH=. .venv/bin/python -m pytest \
  tests/test_cascade_route.py \
  tests/test_settings_route.py \
  tests/test_neta_plot_tcc.py \
  tests/test_etu_search_route.py \
  tests/test_etu_breaker_cascade_route.py \
  tests/test_neta_tmt_routes.py \
  tests/test_neta_tmt_facets_route.py \
  tests/test_neta_emt_routes.py \
  tests/test_neta_emt_facets_route.py \
  -q
```

## Deploy Confirmation

Pushed `70c7127a` to `main`. Render auto-deploy was confirmed by polling hosted readiness after the push:

- `/health`: HTTP 200, `{"status":"ok"}`
- `/health/ready`: HTTP 200, `{"status":"ready","database":"connected","catalog_available":true}`
- Six health/readiness polls stayed HTTP 200.

## Post-Deploy Gate

All required post-deploy checks passed. Revert was not needed.

| Check | Result |
| --- | --- |
| ETU parity | PASS: `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0` |
| Breaker catalog/status | PASS: HTTP 200, `manufacturer_count=63`, `sensor_count=17831` |
| ETU search | PASS: HTTP 200, `count=17831`, `limit=3` |
| TMT facets | PASS: HTTP 200, `total_matching_frames=40264` |
| EMT facets | PASS: HTTP 200, `total_matching_frames=805` |
| Relay parity | PASS: `RESULT PASS: live relay SQL parity holds across 6 seeded scenario(s); families: bsl, iec, meq, pcd, swz, tcp; warnings: 0; failures: 0` |
| Relay sections | PASS: HTTP 200, `count=3` |

## Phase 4 DB Object List

Read-only scan used `pg_get_functiondef` for ordinary functions/procedures and `pg_views.definition` for views. Direct old breaker table-name references remaining in DB object bodies:

| Object | Direct old refs |
| --- | --- |
| `public.fn_calculate_test_currents(p_sensor_id integer, p_plug_rating numeric, p_ltpu_setting numeric, p_ltd_multiplier numeric, p_stpu_setting numeric, p_std_multiplier numeric, p_inst_setting numeric, p_gfpu_setting numeric, p_gfd_multiplier numeric, p_multiplier_value numeric, p_c_factor numeric, p_maint_mode boolean)` | `tcc_etu_stpu_overrides` |
| `public.fn_sensor_available_settings(p_sensor_id integer)` | `tcc_etu_gfpu_pickups`, `tcc_etu_inst_pickups`, `tcc_etu_ltd_bands`, `tcc_etu_ltpu_multipliers`, `tcc_etu_ltpu_pickups`, `tcc_etu_plugs`, `tcc_etu_sensors`, `tcc_etu_stpu_pickups` |
| `public.vw_trip_unit_cascade` | `tcc_manufacturers_pre_rebuild` |

No direct old breaker table-name refs were found in `public.fn_evaluate_test_results` or `public.vw_sensor_calc_context` by this scan.

## Boundary

This phase was code-only. It did not touch DB DDL, migration SQL, relay SQL, back-compat views, function bodies, package manifests, lockfiles, generated output, or unrelated dirty files.
