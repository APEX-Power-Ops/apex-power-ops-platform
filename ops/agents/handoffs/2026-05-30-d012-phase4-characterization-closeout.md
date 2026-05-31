# Decision-012 Phase 4 Characterization Closeout

Dispatch: `2026-05-30-cc-d012-phase4-characterization`
Executor: Codex
Date: 2026-05-31
Status: Complete. Read-only characterization only; no DDL, repoints, drops, or app edits.

## Claim And Method

- Claim commit pushed: `5e13403f` (`claim: 2026-05-30-cc-d012-phase4-characterization by codex`)
- Live credential value was not printed.
- All live DB inspection used `BEGIN READ ONLY`, catalog/body `SELECT`s, and `ROLLBACK`.
- Repo changes in this executor are limited to this closeout plus the inbox lifecycle move.

## 1. Back-Compat View Drop-Set

Live catalog contains the expected 60 old-name back-compat views: 39 in `public`, 21 in `work`. `pg_depend` found zero external object dependencies on the 60 views after excluding each view's own rewrite/type internals.

However, body scans found two functions still text-reference nine `public.tcc_*` views. Those must be repointed in 4a before the 4b view drop.

| Old view | Target base table | Remaining DB body refs |
| --- | --- | --- |
| `public.tcc_brk_iccb` | `tcc.brk_iccb` | none |
| `public.tcc_brk_iccb_styles` | `tcc.brk_iccb_styles` | none |
| `public.tcc_brk_mccb` | `tcc.brk_mccb` | none |
| `public.tcc_brk_mccb_styles` | `tcc.brk_mccb_styles` | none |
| `public.tcc_brk_pcb` | `tcc.brk_pcb` | none |
| `public.tcc_brk_pcb_styles` | `tcc.brk_pcb_styles` | none |
| `public.tcc_emt` | `tcc.emt` | none |
| `public.tcc_emt_band_names` | `tcc.emt_band_names` | none |
| `public.tcc_emt_curves` | `tcc.emt_curves` | none |
| `public.tcc_emt_frame_amps` | `tcc.emt_frame_amps` | none |
| `public.tcc_emt_frames` | `tcc.emt_frames` | none |
| `public.tcc_emt_pickups` | `tcc.emt_pickups` | none |
| `public.tcc_emt_sections` | `tcc.emt_sections` | none |
| `public.tcc_etu_gfd_bands` | `tcc.etu_gfd_bands` | none |
| `public.tcc_etu_gfd_equations` | `tcc.etu_gfd_equations` | none |
| `public.tcc_etu_gfpu_pickups` | `tcc.etu_gfpu_pickups` | `public.fn_sensor_available_settings(...)` |
| `public.tcc_etu_inst_curves` | `tcc.etu_inst_curves` | none |
| `public.tcc_etu_inst_pickups` | `tcc.etu_inst_pickups` | `public.fn_sensor_available_settings(...)` |
| `public.tcc_etu_ltd_bands` | `tcc.etu_ltd_bands` | `public.fn_sensor_available_settings(...)` |
| `public.tcc_etu_ltd_params` | `tcc.etu_ltd_params` | none |
| `public.tcc_etu_ltpu_multipliers` | `tcc.etu_ltpu_multipliers` | `public.fn_sensor_available_settings(...)` |
| `public.tcc_etu_ltpu_pickups` | `tcc.etu_ltpu_pickups` | `public.fn_sensor_available_settings(...)` |
| `public.tcc_etu_plugs` | `tcc.etu_plugs` | `public.fn_sensor_available_settings(...)` |
| `public.tcc_etu_sensor_maint` | `tcc.etu_sensor_maint` | none |
| `public.tcc_etu_sensor_params` | `tcc.etu_sensor_params` | none |
| `public.tcc_etu_sensors` | `tcc.etu_sensors` | `public.fn_sensor_available_settings(...)` |
| `public.tcc_etu_settings` | `tcc.etu_settings` | none |
| `public.tcc_etu_std_bands` | `tcc.etu_std_bands` | none |
| `public.tcc_etu_std_equations` | `tcc.etu_std_equations` | none |
| `public.tcc_etu_stpu_overrides` | `tcc.etu_stpu_overrides` | `public.fn_calculate_test_currents(...)` |
| `public.tcc_etu_stpu_pickups` | `tcc.etu_stpu_pickups` | `public.fn_sensor_available_settings(...)` |
| `public.tcc_manufacturers` | `tcc.manufacturers` | none |
| `public.tcc_tmt_amps` | `tcc.tmt_amps` | none |
| `public.tcc_tmt_curves` | `tcc.tmt_curves` | none |
| `public.tcc_tmt_frames` | `tcc.tmt_frames` | none |
| `public.tcc_tmt_settings` | `tcc.tmt_settings` | none |
| `public.tcc_tmt_thermal_adj` | `tcc.tmt_thermal_adj` | none |
| `public.tcc_trip_styles` | `tcc.trip_styles` | none |
| `public.tcc_trip_types` | `tcc.trip_types` | none |
| `work.tcc_relay_curve_points_tcp` | `tcc.relay_curve_points_tcp` | none |
| `work.tcc_relay_curve_rows_bsl` | `tcc.relay_curve_rows_bsl` | none |
| `work.tcc_relay_curve_rows_iec` | `tcc.relay_curve_rows_iec` | none |
| `work.tcc_relay_curve_rows_meq` | `tcc.relay_curve_rows_meq` | none |
| `work.tcc_relay_curve_rows_pcd` | `tcc.relay_curve_rows_pcd` | none |
| `work.tcc_relay_curve_rows_swz` | `tcc.relay_curve_rows_swz` | none |
| `work.tcc_relay_curves_bsl` | `tcc.relay_curves_bsl` | none |
| `work.tcc_relay_curves_egc` | `tcc.relay_curves_egc` | none |
| `work.tcc_relay_curves_iec` | `tcc.relay_curves_iec` | none |
| `work.tcc_relay_curves_lrm` | `tcc.relay_curves_lrm` | none |
| `work.tcc_relay_curves_meq` | `tcc.relay_curves_meq` | none |
| `work.tcc_relay_curves_pcd` | `tcc.relay_curves_pcd` | none |
| `work.tcc_relay_curves_rxd` | `tcc.relay_curves_rxd` | none |
| `work.tcc_relay_curves_swz` | `tcc.relay_curves_swz` | none |
| `work.tcc_relay_curves_tcp` | `tcc.relay_curves_tcp` | none |
| `work.tcc_relay_devices` | `tcc.relay_devices` | none |
| `work.tcc_relay_discrete_values` | `tcc.relay_discrete_values` | none |
| `work.tcc_relay_line_sections` | `tcc.relay_line_sections` | none |
| `work.tcc_relay_ranges` | `tcc.relay_ranges` | none |
| `work.tcc_relay_td_sections` | `tcc.relay_td_sections` | none |
| `work.tcc_relays` | `tcc.relays` | none |

## 2. DB Body Repoint Targets

Function/procedure/view/matview/trigger/rule scan found exactly three 4a body targets. Constraint references to `_pre_rebuild` are handled in section 4.

| Object | Old refs | Repoint target |
| --- | --- | --- |
| `public.fn_calculate_test_currents(...)` | `public.tcc_etu_stpu_overrides` | `tcc.etu_stpu_overrides` |
| `public.fn_sensor_available_settings(p_sensor_id integer)` | `public.tcc_etu_gfpu_pickups`, `public.tcc_etu_inst_pickups`, `public.tcc_etu_ltd_bands`, `public.tcc_etu_ltpu_multipliers`, `public.tcc_etu_ltpu_pickups`, `public.tcc_etu_plugs`, `public.tcc_etu_sensors`, `public.tcc_etu_stpu_pickups`, plus one unqualified `tcc_etu_plugs` token | `tcc.etu_gfpu_pickups`, `tcc.etu_inst_pickups`, `tcc.etu_ltd_bands`, `tcc.etu_ltpu_multipliers`, `tcc.etu_ltpu_pickups`, `tcc.etu_plugs`, `tcc.etu_sensors`, `tcc.etu_stpu_pickups` |
| `public.vw_trip_unit_cascade` | `tcc_manufacturers_pre_rebuild` | remove the `_pre_rebuild` CTE and join `tcc.trip_types` directly by canonical `manufacturer_id` plus `name = ts.type` |

No old relay names were found in DB object bodies.

## 3. `vw_trip_unit_cascade` Deep-Dive

App usage: active routes still use `vw_trip_unit_cascade` in `apps/control-plane-api/services/neta/router.py` at lines 1647, 2849, 2926, 2943, 2964, 2988, 3008, 3039, 3084, and 3105. It is also mentioned in service docstrings. DB usage: no other DB function/view body references it, and `pg_depend` found only its own rewrite/type internals.

Current view shape:

- Rows: `17831`
- Distinct `manufacturer_id`: `63`
- Distinct `manufacturer_name`: `63`
- Exposes manufacturer columns from canonical `tcc.manufacturers`: `m.id AS manufacturer_id`, `m.mfr_name AS manufacturer_name`
- Uses `_pre_rebuild` only inside the `trip_type_v2` CTE:
  `tcc.trip_types -> tcc_manufacturers_pre_rebuild -> tcc.manufacturers`

Manufacturer exposure check: joining current view output back to canonical `tcc.manufacturers` by id/name produced zero manufacturer-name or id mismatches.

Trip-type behavior check against a direct canonical join:

| Metric | Count |
| --- | ---: |
| Rows compared | 17831 |
| `trip_type_id` differences | 396 |
| `trip_type_name` differences | 396 |
| Current null, direct canonical found | 396 |
| Current found, direct canonical null | 0 |

Sample current-vs-canonical differences:

| Sensor | Manufacturer | Current trip type | Direct canonical trip type |
| ---: | --- | --- | --- |
| 29442 | Chint | `NULL` | `531 / NA` |
| 29443 | Chint | `NULL` | `531 / NA` |
| 30770 | Hager | `NULL` | `534 / H250` |
| 30775 | Hager | `NULL` | `535 / H400` |

Underlying id-space sample:

| Trip type | Current `trip_types.manufacturer_id` | Canonical name by current id | Pre-rebuild name by same id | Canonical id by pre-rebuild name |
| --- | ---: | --- | --- | ---: |
| `531 / NA` | 264 | Chint | Argus | 266 |
| `534 / H250` | 292 | Hager | Proteus | 296 |
| `537 / STU` | 304 | LG Industrial | AEI | 308 |
| `538 / Electronic Trip` | 317 | MEM | Crown Electric | 321 |

Recommendation: **repoint-to-canonical, do not drop**. The app still consumes this view, and direct canonical repoint is a behavior fix: it preserves canonical manufacturer columns and restores 396 missing trip-type associations currently hidden by the stale `_pre_rebuild` id/name bridge.

## 4. `_pre_rebuild` Disposition

There are 20 live `public.*_pre_rebuild` tables. `public.tcc_test_plans` has 0 rows but still has eight FKs into ETU `_pre_rebuild` tables; `public.tcc_test_results` has 0 rows and FK only to `public.tcc_test_plans`.

| Table | Rows | Inbound FK summary | Disposition |
| --- | ---: | --- | --- |
| `public.tcc_etu_gfd_bands_pre_rebuild` | 72464 | `tcc_test_plans_gfd_band_id_fkey` | MUST-KEEP |
| `public.tcc_etu_gfd_equations_pre_rebuild` | 8550 | none | SAFE-TO-DROP |
| `public.tcc_etu_gfpu_pickups_pre_rebuild` | 65871 | `tcc_test_plans_gfpu_pickup_id_fkey` | MUST-KEEP |
| `public.tcc_etu_inst_curves_pre_rebuild` | 94873 | none | SAFE-TO-DROP |
| `public.tcc_etu_inst_pickups_pre_rebuild` | 152449 | `tcc_test_plans_inst_pickup_id_fkey` | MUST-KEEP |
| `public.tcc_etu_ltd_bands_pre_rebuild` | 158074 | `tcc_test_plans_ltd_band_id_fkey` | MUST-KEEP |
| `public.tcc_etu_ltd_params_pre_rebuild` | 3919 | none | SAFE-TO-DROP |
| `public.tcc_etu_ltpu_multipliers_pre_rebuild` | 4832 | none | SAFE-TO-DROP |
| `public.tcc_etu_ltpu_pickups_pre_rebuild` | 128718 | `tcc_test_plans_ltpu_pickup_id_fkey` | MUST-KEEP |
| `public.tcc_etu_plugs_pre_rebuild` | 19122 | none; outbound FK to `tcc_trip_styles_pre_rebuild` | SAFE-TO-DROP |
| `public.tcc_etu_sensor_maint_pre_rebuild` | 2572 | none | SAFE-TO-DROP |
| `public.tcc_etu_sensor_params_pre_rebuild` | 136384 | none | SAFE-TO-DROP |
| `public.tcc_etu_sensors_pre_rebuild` | 11442 | `tcc_test_plans_sensor_id_fkey`, plus inbound FKs from ETU pre-rebuild child tables | MUST-KEEP |
| `public.tcc_etu_settings_pre_rebuild` | 0 | none | SAFE-TO-DROP |
| `public.tcc_etu_std_bands_pre_rebuild` | 139643 | `tcc_test_plans_std_band_id_fkey` | MUST-KEEP |
| `public.tcc_etu_std_equations_pre_rebuild` | 22620 | none | SAFE-TO-DROP |
| `public.tcc_etu_stpu_overrides_pre_rebuild` | 15 | none | SAFE-TO-DROP |
| `public.tcc_etu_stpu_pickups_pre_rebuild` | 114754 | `tcc_test_plans_stpu_pickup_id_fkey` | MUST-KEEP |
| `public.tcc_manufacturers_pre_rebuild` | 450 | needed by `tcc_trip_styles_pre_rebuild`; also current `vw_trip_unit_cascade` until 4a | MUST-KEEP |
| `public.tcc_trip_styles_pre_rebuild` | 2094 | needed by `tcc_etu_sensors_pre_rebuild`; inbound from `tcc_etu_plugs_pre_rebuild` too | MUST-KEEP |

MUST-KEEP set:

`public.tcc_etu_gfd_bands_pre_rebuild`, `public.tcc_etu_gfpu_pickups_pre_rebuild`, `public.tcc_etu_inst_pickups_pre_rebuild`, `public.tcc_etu_ltd_bands_pre_rebuild`, `public.tcc_etu_ltpu_pickups_pre_rebuild`, `public.tcc_etu_sensors_pre_rebuild`, `public.tcc_etu_std_bands_pre_rebuild`, `public.tcc_etu_stpu_pickups_pre_rebuild`, `public.tcc_trip_styles_pre_rebuild`, `public.tcc_manufacturers_pre_rebuild`.

SAFE-TO-DROP set:

`public.tcc_etu_gfd_equations_pre_rebuild`, `public.tcc_etu_inst_curves_pre_rebuild`, `public.tcc_etu_ltd_params_pre_rebuild`, `public.tcc_etu_ltpu_multipliers_pre_rebuild`, `public.tcc_etu_plugs_pre_rebuild`, `public.tcc_etu_sensor_maint_pre_rebuild`, `public.tcc_etu_sensor_params_pre_rebuild`, `public.tcc_etu_settings_pre_rebuild`, `public.tcc_etu_std_equations_pre_rebuild`, `public.tcc_etu_stpu_overrides_pre_rebuild`.

## 5. `_v2` Disposition

All-schema `*_v2` scan found two tables:

| Table | Rows | References | Recommendation |
| --- | ---: | --- | --- |
| `public.sops_v2` | 0 | inbound FKs from `ahas`, `sop_apparatus_types`, `sop_task_steps`, and self-FK; outbound FKs to `employees` and self | Out of Decision-012 TCC scope; keep. |
| `public.tcc_etu_sensor_maint_v2` | 2572 | no inbound FKs; two outbound FKs to `tcc.etu_sensors`; no app refs; no function/view/matview/trigger/rule body refs | SAFE-TO-DROP in 4b. |

## 6. Proposed Phase-4 Execution Plan

4a, reversible:

1. Repoint `public.fn_calculate_test_currents(...)`: `public.tcc_etu_stpu_overrides` -> `tcc.etu_stpu_overrides`.
2. Repoint `public.fn_sensor_available_settings(integer)`: all old ETU availability table refs -> `tcc.*` targets listed in section 2.
3. Repoint `public.vw_trip_unit_cascade`: keep the view because app routes consume it, but remove the `_pre_rebuild` CTE and join `tcc.trip_types` directly by canonical `manufacturer_id` and `name = ts.type`. Treat the 396 restored trip-type associations as an intended behavior fix.
4. Gate 4a with ETU parity, breaker catalog/status, and route checks that exercise `vw_trip_unit_cascade`.

4b, irreversible:

1. Final pre-drop verification: re-run old body scan and confirm zero references to the 60 back-compat views and zero references to the SAFE-TO-DROP `_pre_rebuild`/`_v2` tables.
2. Drop all 60 back-compat views from section 1.
3. Drop SAFE-TO-DROP `_pre_rebuild` tables from section 4.
4. Drop `public.tcc_etu_sensor_maint_v2`.
5. Do not drop the MUST-KEEP `_pre_rebuild` tables unless Desktop authors a separate migration that retargets or removes the surviving `tcc_test_plans` FK chain.

Ordering constraints:

- 4a must precede the 60-view drop because two functions still reference old `public.tcc_*` views by body text.
- `vw_trip_unit_cascade` must be repointed before any attempt to drop `public.tcc_manufacturers_pre_rebuild`.
- The MUST-KEEP `_pre_rebuild` ancestry (`tcc_test_plans` -> ETU pre-rebuild target -> `tcc_etu_sensors_pre_rebuild` -> `tcc_trip_styles_pre_rebuild` -> `tcc_manufacturers_pre_rebuild`) blocks those drops under the current schema.

Flagged decisions:

- Desktop/operator should explicitly accept the `vw_trip_unit_cascade` behavior fix: 396 rows gain canonical trip-type ids/names that are currently null.
- `public.sops_v2` is a real non-TCC table with dependencies; leave it out of Decision-012 cleanup.

## Final Sets

4a repoint map: `fn_calculate_test_currents`, `fn_sensor_available_settings`, `vw_trip_unit_cascade`.

4b view drop-set: all 60 old-name views in section 1.

4b table drop-set: the 10 SAFE-TO-DROP `_pre_rebuild` tables in section 4 plus `public.tcc_etu_sensor_maint_v2`.

Do-not-drop set: the 10 MUST-KEEP `_pre_rebuild` tables in section 4 plus out-of-scope `public.sops_v2`.
