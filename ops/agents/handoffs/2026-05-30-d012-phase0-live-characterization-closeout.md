# Decision-012 Phase 0 Live Characterization Closeout

Dispatch: `2026-05-30-cc-d012-phase0-live-characterization`
Executor: Codex
Date: 2026-05-31
Status: Complete - read-only characterization only; no DDL, writes, schema/data/route/test changes.

## Claim

- Claim commit pushed: `a514cc2a` (`claim: 2026-05-30-cc-d012-phase0-live-characterization by codex`)
- Predecessor was already done: `2026-05-30-cc-hosted-breaker-resource-explorer`
- Live access used the read-only pooler DSN exported by the canonical secret file; no DSN value was printed.
- The plan file named in the packet, `apex-ops-substrate/.claude/PLATFORM/DECISION_012_TCC_SCHEMA_UNIFICATION_PLAN_2026-05-30.md`, was not present under `/home/olares/code/apex` on this host.

## Deliverable A - Live Inventory

### Public `tcc_*` Generations

Live has `62` `public.tcc_*` base tables:

| Generation | Tables | Total rows |
| --- | ---: | ---: |
| base | 41 | 2,570,467 |
| `_pre_rebuild` | 20 | 1,138,846 |
| `_v2` | 1 | 2,572 |

Full inventory:

| Generation | Table | Rows |
| --- | --- | ---: |
| base | `tcc_brk_iccb` | 29 |
| base | `tcc_brk_iccb_styles` | 608 |
| base | `tcc_brk_mccb` | 599 |
| base | `tcc_brk_mccb_styles` | 10,335 |
| base | `tcc_brk_pcb` | 157 |
| base | `tcc_brk_pcb_styles` | 3,279 |
| base | `tcc_emt` | 174 |
| base | `tcc_emt_band_names` | 2,971 |
| base | `tcc_emt_curves` | 40,735 |
| base | `tcc_emt_frame_amps` | 1,691 |
| base | `tcc_emt_frames` | 805 |
| base | `tcc_emt_pickups` | 6,587 |
| base | `tcc_emt_sections` | 1,765 |
| base | `tcc_etu_gfd_bands` | 72,464 |
| `_pre_rebuild` | `tcc_etu_gfd_bands_pre_rebuild` | 72,464 |
| base | `tcc_etu_gfd_equations` | 8,550 |
| `_pre_rebuild` | `tcc_etu_gfd_equations_pre_rebuild` | 8,550 |
| base | `tcc_etu_gfpu_pickups` | 65,871 |
| `_pre_rebuild` | `tcc_etu_gfpu_pickups_pre_rebuild` | 65,871 |
| base | `tcc_etu_inst_curves` | 94,873 |
| `_pre_rebuild` | `tcc_etu_inst_curves_pre_rebuild` | 94,873 |
| base | `tcc_etu_inst_pickups` | 152,449 |
| `_pre_rebuild` | `tcc_etu_inst_pickups_pre_rebuild` | 152,449 |
| base | `tcc_etu_ltd_bands` | 158,074 |
| `_pre_rebuild` | `tcc_etu_ltd_bands_pre_rebuild` | 158,074 |
| base | `tcc_etu_ltd_params` | 3,919 |
| `_pre_rebuild` | `tcc_etu_ltd_params_pre_rebuild` | 3,919 |
| base | `tcc_etu_ltpu_multipliers` | 4,832 |
| `_pre_rebuild` | `tcc_etu_ltpu_multipliers_pre_rebuild` | 4,832 |
| base | `tcc_etu_ltpu_pickups` | 128,718 |
| `_pre_rebuild` | `tcc_etu_ltpu_pickups_pre_rebuild` | 128,718 |
| base | `tcc_etu_plugs` | 49,901 |
| `_pre_rebuild` | `tcc_etu_plugs_pre_rebuild` | 19,122 |
| base | `tcc_etu_sensor_maint` | 2,572 |
| `_pre_rebuild` | `tcc_etu_sensor_maint_pre_rebuild` | 2,572 |
| `_v2` | `tcc_etu_sensor_maint_v2` | 2,572 |
| base | `tcc_etu_sensor_params` | 136,384 |
| `_pre_rebuild` | `tcc_etu_sensor_params_pre_rebuild` | 136,384 |
| base | `tcc_etu_sensors` | 17,831 |
| `_pre_rebuild` | `tcc_etu_sensors_pre_rebuild` | 11,442 |
| base | `tcc_etu_settings` | 3,514 |
| `_pre_rebuild` | `tcc_etu_settings_pre_rebuild` | 0 |
| base | `tcc_etu_std_bands` | 139,643 |
| `_pre_rebuild` | `tcc_etu_std_bands_pre_rebuild` | 139,643 |
| base | `tcc_etu_std_equations` | 22,620 |
| `_pre_rebuild` | `tcc_etu_std_equations_pre_rebuild` | 22,620 |
| base | `tcc_etu_stpu_overrides` | 3 |
| `_pre_rebuild` | `tcc_etu_stpu_overrides_pre_rebuild` | 15 |
| base | `tcc_etu_stpu_pickups` | 114,754 |
| `_pre_rebuild` | `tcc_etu_stpu_pickups_pre_rebuild` | 114,754 |
| base | `tcc_manufacturers` | 450 |
| `_pre_rebuild` | `tcc_manufacturers_pre_rebuild` | 450 |
| base | `tcc_test_plans` | 0 |
| base | `tcc_test_results` | 0 |
| base | `tcc_tmt_amps` | 66,960 |
| base | `tcc_tmt_curves` | 1,139,025 |
| base | `tcc_tmt_frames` | 42,069 |
| base | `tcc_tmt_settings` | 57,983 |
| base | `tcc_tmt_thermal_adj` | 14,620 |
| base | `tcc_trip_styles` | 2,094 |
| `_pre_rebuild` | `tcc_trip_styles_pre_rebuild` | 2,094 |
| base | `tcc_trip_types` | 559 |

### Target Schema

`tcc` schema does not exist live.

### Relay Work Inventory

Live relay tables in `work`:

| Table | Rows |
| --- | ---: |
| `work.tcc_relays` | 1,442 |
| `work.tcc_relay_devices` | 6,850 |
| `work.tcc_relay_line_sections` | 23,387 |
| `work.tcc_relay_td_sections` | 6,635 |
| `work.tcc_relay_ranges` | 34,213 |
| `work.tcc_relay_discrete_values` | 38,679 |
| `work.tcc_relay_curves_tcp` | 16,183 |
| `work.tcc_relay_curve_points_tcp` | 1,570,700 |
| `work.tcc_relay_curves_iec` | 981 |
| `work.tcc_relay_curve_rows_iec` | 4,114 |
| `work.tcc_relay_curves_meq` | 333 |
| `work.tcc_relay_curve_rows_meq` | 1,600 |
| `work.tcc_relay_curves_bsl` | 491 |
| `work.tcc_relay_curve_rows_bsl` | 3,695 |
| `work.tcc_relay_curves_swz` | 950 |
| `work.tcc_relay_curve_rows_swz` | 5,688 |
| `work.tcc_relay_curves_pcd` | 52 |
| `work.tcc_relay_curve_rows_pcd` | 424 |
| `work.tcc_relay_curves_lrm` | 13 |
| `work.tcc_relay_curves_rxd` | 26 |
| `work.tcc_relay_curves_egc` | 0 |

G-3 cross-check holds for the headline counts: relays `1,442`, devices `6,850`, ranges `34,213`, TCP points `1,570,700`.

### FK Landmine

The breaker manufacturer FKs still target `public.tcc_manufacturers_pre_rebuild`, while route SQL joins `public.tcc_manufacturers`.

| Source table | FK target for `manufacturer_id` | Route join target |
| --- | --- | --- |
| `tcc_brk_iccb` | `tcc_manufacturers_pre_rebuild(id)` | `tcc_manufacturers` |
| `tcc_brk_mccb` | `tcc_manufacturers_pre_rebuild(id)` | `tcc_manufacturers` |
| `tcc_brk_pcb` | `tcc_manufacturers_pre_rebuild(id)` | `tcc_manufacturers` |
| `tcc_emt` | `tcc_manufacturers_pre_rebuild(id)` | `tcc_manufacturers` |

Additional live check:

| Source table | Rows | Missing in `tcc_manufacturers` | Missing in `tcc_manufacturers_pre_rebuild` |
| --- | ---: | ---: | ---: |
| `tcc_brk_iccb` | 29 | 0 | 0 |
| `tcc_brk_mccb` | 599 | 5 | 0 |
| `tcc_brk_pcb` | 157 | 1 | 0 |
| `tcc_emt` | 174 | 0 | 0 |
| `tcc_trip_types` | 559 | 1 | 0 |

The missing base-manufacturer rows all use `manufacturer_id = 262` (`5` MCCB rows, `1` PCB row, `1` trip-type row). A Phase-1 design that rewires FKs to base `tcc_manufacturers` must either carry/repair manufacturer `262` in base or deliberately omit/remap those rows. Preserving live FK semantics means preserving the `_pre_rebuild` target for those FKs.

### Base TCC FK Map

There are `61` FKs on base `public.tcc_*` source tables. Source-table FKs that target `_pre_rebuild` are part of the live state, not a typo in this closeout.

| Source | Target |
| --- | --- |
| `tcc_brk_iccb(manufacturer_id)` | `tcc_manufacturers_pre_rebuild(id)` |
| `tcc_brk_iccb_styles(breaker_id)` | `tcc_brk_iccb(id)` |
| `tcc_brk_mccb(manufacturer_id)` | `tcc_manufacturers_pre_rebuild(id)` |
| `tcc_brk_mccb_styles(breaker_id)` | `tcc_brk_mccb(id)` |
| `tcc_brk_pcb(manufacturer_id)` | `tcc_manufacturers_pre_rebuild(id)` |
| `tcc_brk_pcb_styles(breaker_id)` | `tcc_brk_pcb(id)` |
| `tcc_emt(manufacturer_id)` | `tcc_manufacturers_pre_rebuild(id)` |
| `tcc_emt_band_names(section_id)` | `tcc_emt_sections(id)` |
| `tcc_emt_curves(band_id)` | `tcc_emt_band_names(id)` |
| `tcc_emt_frame_amps(frame_id)` | `tcc_emt_frames(id)` |
| `tcc_emt_frames(emt_id)` | `tcc_emt(id)` |
| `tcc_emt_pickups(section_id)` | `tcc_emt_sections(id)` |
| `tcc_emt_sections(frame_id)` | `tcc_emt_frames(id)` |
| `tcc_etu_gfd_bands(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_gfd_equations(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_gfpu_pickups(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_inst_curves(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_inst_pickups(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_ltd_bands(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_ltd_params(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_ltpu_multipliers(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_ltpu_pickups(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_plugs(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_sensor_maint(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_sensor_params(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_sensors(trip_style_id)` | `tcc_trip_styles(id)` |
| `tcc_etu_settings(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_std_bands(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_std_equations(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_stpu_overrides(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_etu_stpu_pickups(sensor_id)` | `tcc_etu_sensors(id)` |
| `tcc_test_plans(sensor_id)` | `tcc_etu_sensors_pre_rebuild(id)` |
| `tcc_test_plans(ltpu_pickup_id)` | `tcc_etu_ltpu_pickups_pre_rebuild(id)` |
| `tcc_test_plans(ltd_band_id)` | `tcc_etu_ltd_bands_pre_rebuild(id)` |
| `tcc_test_plans(stpu_pickup_id)` | `tcc_etu_stpu_pickups_pre_rebuild(id)` |
| `tcc_test_plans(std_band_id)` | `tcc_etu_std_bands_pre_rebuild(id)` |
| `tcc_test_plans(inst_pickup_id)` | `tcc_etu_inst_pickups_pre_rebuild(id)` |
| `tcc_test_plans(gfpu_pickup_id)` | `tcc_etu_gfpu_pickups_pre_rebuild(id)` |
| `tcc_test_plans(gfd_band_id)` | `tcc_etu_gfd_bands_pre_rebuild(id)` |
| `tcc_test_plans(user_id)` | `auth.users(id)` |
| `tcc_test_results(plan_id)` | `tcc_test_plans(id)` |
| `tcc_tmt_amps(frame_id)` | `tcc_tmt_frames(id)` |
| `tcc_tmt_curves(frame_id)` | `tcc_tmt_frames(id)` |
| `tcc_tmt_settings(frame_id)` | `tcc_tmt_frames(id)` |
| `tcc_tmt_thermal_adj(frame_id)` | `tcc_tmt_frames(id)` |
| `tcc_trip_styles(mfg_id)` | `tcc_manufacturers(id)` |
| `tcc_trip_types(manufacturer_id)` | `tcc_manufacturers_pre_rebuild(id)` |

Some source/target pairs have duplicate live constraints with different constraint names, notably the ETU child tables with both legacy and `_v2`-named FK constraints. The total FK count is therefore higher than the unique source-target pair count shown above.

Exact FK constraints:

| Constraint | Source | Target | ON DELETE | ON UPDATE |
| --- | --- | --- | --- | --- |
| `tcc_brk_iccb_manufacturer_id_fkey` | `tcc_brk_iccb(manufacturer_id)` | `public.tcc_manufacturers_pre_rebuild(id)` | CASCADE | NO ACTION |
| `tcc_brk_iccb_styles_breaker_id_fkey` | `tcc_brk_iccb_styles(breaker_id)` | `public.tcc_brk_iccb(id)` | CASCADE | NO ACTION |
| `tcc_brk_mccb_manufacturer_id_fkey` | `tcc_brk_mccb(manufacturer_id)` | `public.tcc_manufacturers_pre_rebuild(id)` | CASCADE | NO ACTION |
| `tcc_brk_mccb_styles_breaker_id_fkey` | `tcc_brk_mccb_styles(breaker_id)` | `public.tcc_brk_mccb(id)` | CASCADE | NO ACTION |
| `tcc_brk_pcb_manufacturer_id_fkey` | `tcc_brk_pcb(manufacturer_id)` | `public.tcc_manufacturers_pre_rebuild(id)` | CASCADE | NO ACTION |
| `tcc_brk_pcb_styles_breaker_id_fkey` | `tcc_brk_pcb_styles(breaker_id)` | `public.tcc_brk_pcb(id)` | CASCADE | NO ACTION |
| `tcc_emt_manufacturer_id_fkey` | `tcc_emt(manufacturer_id)` | `public.tcc_manufacturers_pre_rebuild(id)` | CASCADE | NO ACTION |
| `tcc_emt_band_names_section_id_fkey` | `tcc_emt_band_names(section_id)` | `public.tcc_emt_sections(id)` | CASCADE | NO ACTION |
| `tcc_emt_curves_band_id_fkey` | `tcc_emt_curves(band_id)` | `public.tcc_emt_band_names(id)` | CASCADE | NO ACTION |
| `tcc_emt_frame_amps_frame_id_fkey` | `tcc_emt_frame_amps(frame_id)` | `public.tcc_emt_frames(id)` | CASCADE | NO ACTION |
| `tcc_emt_frames_emt_id_fkey` | `tcc_emt_frames(emt_id)` | `public.tcc_emt(id)` | CASCADE | NO ACTION |
| `tcc_emt_pickups_section_id_fkey` | `tcc_emt_pickups(section_id)` | `public.tcc_emt_sections(id)` | CASCADE | NO ACTION |
| `tcc_emt_sections_frame_id_fkey` | `tcc_emt_sections(frame_id)` | `public.tcc_emt_frames(id)` | CASCADE | NO ACTION |
| `tcc_etu_gfd_bands_sensor_fk` | `tcc_etu_gfd_bands(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_gfd_bands_v2_sensor_id_fkey` | `tcc_etu_gfd_bands(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_gfd_equations_sensor_fk` | `tcc_etu_gfd_equations(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_gfd_equations_v2_sensor_id_fkey` | `tcc_etu_gfd_equations(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_gfpu_pickups_sensor_fk` | `tcc_etu_gfpu_pickups(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_gfpu_pickups_v2_sensor_id_fkey` | `tcc_etu_gfpu_pickups(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_inst_curves_sensor_fk` | `tcc_etu_inst_curves(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_inst_curves_v2_sensor_id_fkey` | `tcc_etu_inst_curves(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_inst_pickups_sensor_fk` | `tcc_etu_inst_pickups(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_inst_pickups_v2_sensor_id_fkey` | `tcc_etu_inst_pickups(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_ltd_bands_sensor_fk` | `tcc_etu_ltd_bands(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_ltd_bands_v2_sensor_id_fkey` | `tcc_etu_ltd_bands(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_ltd_params_sensor_fk` | `tcc_etu_ltd_params(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_ltd_params_v2_sensor_id_fkey` | `tcc_etu_ltd_params(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_ltpu_multipliers_sensor_fk` | `tcc_etu_ltpu_multipliers(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_ltpu_multipliers_v2_sensor_id_fkey` | `tcc_etu_ltpu_multipliers(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_ltpu_pickups_sensor_fk` | `tcc_etu_ltpu_pickups(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_ltpu_pickups_v2_sensor_id_fkey` | `tcc_etu_ltpu_pickups(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_plugs_sensor_fk` | `tcc_etu_plugs(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_plugs_sensor_id_fkey` | `tcc_etu_plugs(sensor_id)` | `public.tcc_etu_sensors(id)` | CASCADE | NO ACTION |
| `tcc_etu_sensor_maint_sensor_fk` | `tcc_etu_sensor_maint(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_sensor_params_sensor_fk` | `tcc_etu_sensor_params(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_sensor_params_v2_sensor_id_fkey` | `tcc_etu_sensor_params(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_sensors_trip_style_fk` | `tcc_etu_sensors(trip_style_id)` | `public.tcc_trip_styles(id)` | NO ACTION | NO ACTION |
| `tcc_etu_settings_sensor_fk` | `tcc_etu_settings(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_std_bands_sensor_fk` | `tcc_etu_std_bands(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_std_bands_v2_sensor_id_fkey` | `tcc_etu_std_bands(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_std_equations_sensor_fk` | `tcc_etu_std_equations(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_std_equations_v2_sensor_id_fkey` | `tcc_etu_std_equations(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_stpu_overrides_sensor_fk` | `tcc_etu_stpu_overrides(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_stpu_pickups_sensor_fk` | `tcc_etu_stpu_pickups(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_etu_stpu_pickups_v2_sensor_id_fkey` | `tcc_etu_stpu_pickups(sensor_id)` | `public.tcc_etu_sensors(id)` | NO ACTION | NO ACTION |
| `tcc_test_plans_gfd_band_id_fkey` | `tcc_test_plans(gfd_band_id)` | `public.tcc_etu_gfd_bands_pre_rebuild(id)` | NO ACTION | NO ACTION |
| `tcc_test_plans_gfpu_pickup_id_fkey` | `tcc_test_plans(gfpu_pickup_id)` | `public.tcc_etu_gfpu_pickups_pre_rebuild(id)` | NO ACTION | NO ACTION |
| `tcc_test_plans_inst_pickup_id_fkey` | `tcc_test_plans(inst_pickup_id)` | `public.tcc_etu_inst_pickups_pre_rebuild(id)` | NO ACTION | NO ACTION |
| `tcc_test_plans_ltd_band_id_fkey` | `tcc_test_plans(ltd_band_id)` | `public.tcc_etu_ltd_bands_pre_rebuild(id)` | NO ACTION | NO ACTION |
| `tcc_test_plans_ltpu_pickup_id_fkey` | `tcc_test_plans(ltpu_pickup_id)` | `public.tcc_etu_ltpu_pickups_pre_rebuild(id)` | NO ACTION | NO ACTION |
| `tcc_test_plans_sensor_id_fkey` | `tcc_test_plans(sensor_id)` | `public.tcc_etu_sensors_pre_rebuild(id)` | NO ACTION | NO ACTION |
| `tcc_test_plans_std_band_id_fkey` | `tcc_test_plans(std_band_id)` | `public.tcc_etu_std_bands_pre_rebuild(id)` | NO ACTION | NO ACTION |
| `tcc_test_plans_stpu_pickup_id_fkey` | `tcc_test_plans(stpu_pickup_id)` | `public.tcc_etu_stpu_pickups_pre_rebuild(id)` | NO ACTION | NO ACTION |
| `tcc_test_plans_user_id_fkey` | `tcc_test_plans(user_id)` | `auth.users(id)` | CASCADE | NO ACTION |
| `tcc_test_results_plan_id_fkey` | `tcc_test_results(plan_id)` | `public.tcc_test_plans(id)` | CASCADE | NO ACTION |
| `tcc_tmt_amps_frame_id_fkey` | `tcc_tmt_amps(frame_id)` | `public.tcc_tmt_frames(id)` | CASCADE | NO ACTION |
| `tcc_tmt_curves_frame_id_fkey` | `tcc_tmt_curves(frame_id)` | `public.tcc_tmt_frames(id)` | CASCADE | NO ACTION |
| `tcc_tmt_settings_frame_id_fkey` | `tcc_tmt_settings(frame_id)` | `public.tcc_tmt_frames(id)` | CASCADE | NO ACTION |
| `tcc_tmt_thermal_adj_frame_id_fkey` | `tcc_tmt_thermal_adj(frame_id)` | `public.tcc_tmt_frames(id)` | CASCADE | NO ACTION |
| `tcc_trip_styles_v2_mfg_id_fkey` | `tcc_trip_styles(mfg_id)` | `public.tcc_manufacturers(id)` | NO ACTION | NO ACTION |
| `tcc_trip_types_manufacturer_id_fkey` | `tcc_trip_types(manufacturer_id)` | `public.tcc_manufacturers_pre_rebuild(id)` | CASCADE | NO ACTION |

### Apparatus Anchor

Live apparatus evidence:

| Surface | Exists | Rows | PK |
| --- | --- | ---: | --- |
| `public.apparatus` | yes | 47 | `id` |
| `seam.apparatus` | yes | 184 | `id` |
| `seam.equipment_models` | no | n/a | n/a |
| `get_apparatus_resources(...)` | no | n/a | n/a |

Disposition: documented-deferred is recommended for Decision-010 anchoring in Phase 1. A full FK to `seam.equipment_models` is not feasible in live today because the table is absent, and the apparatus resource function is absent.

## Deliverable B - Repo Reference Enumeration

Exact table-name scan excluded dependency trees, generated Next output, agent packet/handoff history, archives, and local `output/`. It found `1,456` exact table-reference lines across `62` of `83` live table names.

Lane counts:

| Lane | Exact reference lines |
| --- | ---: |
| `control-plane-neta-router` | 146 |
| `control-plane-services` | 75 |
| `control-plane-scripts` | 79 |
| `control-plane-tests` | 37 |
| `control-plane-migrations` | 590 |
| `control-plane-models` | 91 |
| `calc-engine-src` | 204 |
| `calc-engine-tests` | 1 |
| `infra-database` | 192 |
| `docs` | 35 |
| `other` | 6 |

Top repoint/reference files:

| File | Lines |
| --- | ---: |
| `apps/control-plane-api/migrations/001_tcc_schema.sql` | 278 |
| `apps/control-plane-api/services/neta/router.py` | 146 |
| `infra/database/migrations/work/012_tcc_relay_staged_population.sql` | 87 |
| `infra/database/migrations/work/010_tcc_relay_tables.sql` | 58 |
| `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py` | 42 |
| `apps/control-plane-api/supabase/migrations/20260528_000010_align_etu_runtime_contract.sql` | 41 |
| `apps/control-plane-api/migrations/002_data_transfer.py` | 39 |
| `apps/control-plane-api/migrations/_archive/002_transfer_data.py` | 39 |
| `apps/control-plane-api/migrations/_verify_counts.py` | 38 |
| `packages/calc-engine/src/apex_calc_engine/services/calc_engine/NETA_TEST_PLAN_SPEC.md` | 37 |
| `apps/control-plane-api/services/calc_engine/NETA_TEST_PLAN_SPEC.md` | 37 |
| `apps/control-plane-api/migrations/full_access_import.py` | 36 |
| `apps/control-plane-api/migrations/004_emt_schema.sql` | 33 |
| `packages/calc-engine/src/apex_calc_engine/models/relay.py` | 31 |
| `docs/authority/CONTROL-PLANE-CALC-SCHEMA-MAPPING-2026-04-12.md` | 31 |

Active Phase-3 repoint surface (router/scripts/tests/plans) is `276` table-location references:

```text
tcc_brk_iccb -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:33; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:32; apps/control-plane-api/services/neta/router.py:1552,2043
tcc_brk_iccb_styles -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:36; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:35; apps/control-plane-api/services/neta/router.py:1553,2042
tcc_brk_mccb -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:34; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:33; apps/control-plane-api/services/neta/router.py:1564,2059
tcc_brk_mccb_styles -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:37; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:36; apps/control-plane-api/services/neta/router.py:1565,2058
tcc_brk_pcb -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:35; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:34; apps/control-plane-api/services/neta/router.py:1576,2075
tcc_brk_pcb_styles -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:38; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:37; apps/control-plane-api/services/neta/router.py:1577,2074
tcc_emt -> apps/control-plane-api/scripts/check_schema_drift.py:15; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:43,110; apps/control-plane-api/tests/test_neta_emt_live_integration.py:26; apps/control-plane-api/services/neta/router.py:2331,2349,2359,2360,2361,2362,2363,2364,2457,2505,2568,2765
tcc_emt_band_names -> apps/control-plane-api/scripts/check_schema_drift.py:16; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:47,114; apps/control-plane-api/tests/test_neta_emt_live_integration.py:30; apps/control-plane-api/services/neta/router.py:2336,2354,2393,2610,2681,2762
tcc_emt_curves -> apps/control-plane-api/scripts/check_schema_drift.py:17; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:49,116; apps/control-plane-api/tests/test_neta_emt_live_integration.py:32; apps/control-plane-api/services/neta/router.py:2337,2355,2399,2699,2786
tcc_emt_frame_amps -> apps/control-plane-api/scripts/check_schema_drift.py:18; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:45,112; apps/control-plane-api/tests/test_neta_emt_live_integration.py:28; apps/control-plane-api/services/neta/router.py:2333,2351,2372,2373,2461,2583
tcc_emt_frames -> apps/control-plane-api/scripts/check_schema_drift.py:19; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:44,111; apps/control-plane-api/tests/test_neta_emt_live_integration.py:27; apps/control-plane-api/services/neta/router.py:2332,2350,2367,2368,2369,2456,2504,2567,2764
tcc_emt_pickups -> apps/control-plane-api/scripts/check_schema_drift.py:20; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:48,115; apps/control-plane-api/tests/test_neta_emt_live_integration.py:31; apps/control-plane-api/services/neta/router.py:2335,2353,2388,2615,2665
tcc_emt_sections -> apps/control-plane-api/scripts/check_schema_drift.py:21; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:46,113; apps/control-plane-api/tests/test_neta_emt_live_integration.py:29; apps/control-plane-api/services/neta/router.py:2334,2352,2376,2466,2607,2649,2763
tcc_etu_gfd_bands -> apps/control-plane-api/tests/test_neta_plot_tcc.py:230,1165; apps/control-plane-api/tests/test_settings_route.py:104; apps/control-plane-api/services/neta/router.py:1146,1156,1350,1359,1377,2001,3362
tcc_etu_gfpu_pickups -> apps/control-plane-api/scripts/audit_etu_ground_variants.py:336; apps/control-plane-api/tests/test_settings_route.py:98; apps/control-plane-api/services/neta/router.py:130,1247
tcc_etu_inst_pickups -> apps/control-plane-api/tests/test_settings_route.py:96; apps/control-plane-api/services/neta/router.py:129,1246
tcc_etu_ltd_bands -> apps/control-plane-api/tests/test_neta_plot_tcc.py:222,1157; apps/control-plane-api/tests/test_settings_route.py:100; apps/control-plane-api/services/neta/router.py:1112,1122,1243,1278,1287,1305,1976
tcc_etu_ltpu_multipliers -> apps/control-plane-api/tests/test_settings_route.py:92; apps/control-plane-api/services/neta/router.py:1244
tcc_etu_ltpu_pickups -> apps/control-plane-api/tests/test_settings_route.py:90; apps/control-plane-api/services/neta/router.py:127,1242
tcc_etu_plugs -> apps/control-plane-api/scripts/audit_etu_ground_variants.py:346; apps/control-plane-api/tests/test_cascade_route.py:393,491,532; apps/control-plane-api/tests/test_settings_route.py:88; apps/control-plane-api/services/neta/router.py:1241,1651,1691,2993
tcc_etu_sensor_maint -> apps/control-plane-api/scripts/probe_maint_reduction_evidence.py:35,47; apps/control-plane-api/scripts/audit_etu_ground_variants.py:280,281,320; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:25,87
tcc_etu_sensor_params -> packages/calc-engine/tests/test_source_faithful_adapters.py:96
tcc_etu_sensors -> apps/control-plane-api/scripts/audit_etu_ground_variants.py:278,325,345; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:18,58; apps/control-plane-api/services/neta/router.py:1045
tcc_etu_settings -> apps/control-plane-api/scripts/check_schema_drift.py:22
tcc_etu_std_bands -> apps/control-plane-api/tests/test_neta_plot_tcc.py:226,1161; apps/control-plane-api/tests/test_settings_route.py:102; apps/control-plane-api/services/neta/router.py:1129,1139,1314,1323,1341,1982,3361
tcc_etu_stpu_pickups -> apps/control-plane-api/tests/test_settings_route.py:94; apps/control-plane-api/services/neta/router.py:128,1245
tcc_manufacturers -> apps/control-plane-api/scripts/audit_etu_ground_variants.py:328; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:21,39; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:38; apps/control-plane-api/services/neta/router.py:1554,1566,1578,2458,2569,2766
tcc_relay_curve_points_tcp -> apps/control-plane-api/scripts/probe_live_relay_sql_parity.py:247,277; apps/control-plane-api/services/neta/router.py:200,590,814
tcc_relay_curve_rows_bsl -> apps/control-plane-api/services/neta/router.py:174
tcc_relay_curve_rows_iec -> apps/control-plane-api/services/neta/router.py:162,198
tcc_relay_curve_rows_meq -> apps/control-plane-api/services/neta/router.py:168
tcc_relay_curve_rows_pcd -> apps/control-plane-api/services/neta/router.py:186
tcc_relay_curve_rows_swz -> apps/control-plane-api/services/neta/router.py:180
tcc_relay_curves_bsl -> apps/control-plane-api/services/neta/router.py:173
tcc_relay_curves_iec -> apps/control-plane-api/services/neta/router.py:161,197
tcc_relay_curves_meq -> apps/control-plane-api/services/neta/router.py:167
tcc_relay_curves_pcd -> apps/control-plane-api/services/neta/router.py:185
tcc_relay_curves_swz -> apps/control-plane-api/services/neta/router.py:179
tcc_relay_curves_tcp -> apps/control-plane-api/scripts/probe_live_relay_sql_parity.py:246; apps/control-plane-api/services/neta/router.py:199,606,815
tcc_relay_devices -> apps/control-plane-api/services/neta/router.py:193,403,703
tcc_relay_discrete_values -> apps/control-plane-api/services/neta/router.py:488
tcc_relay_line_sections -> apps/control-plane-api/services/neta/router.py:194,435,463,468,492
tcc_relay_ranges -> apps/control-plane-api/services/neta/router.py:196,462,487
tcc_relay_td_sections -> apps/control-plane-api/scripts/probe_live_relay_sql_parity.py:245,306; apps/control-plane-api/services/neta/router.py:195,402,464,702
tcc_relays -> apps/control-plane-api/services/neta/router.py:192,404,704
tcc_test_plans -> apps/control-plane-api/scripts/check_schema_drift.py:26,67,81,107,109; apps/control-plane-api/scripts/inspect_live_schema.py:37,57,67; apps/control-plane-api/services/neta/plans.py:16,38,313,376,424,456,509
tcc_test_results -> apps/control-plane-api/scripts/check_schema_drift.py:27,82; apps/control-plane-api/scripts/inspect_live_schema.py:47,57,67; apps/control-plane-api/services/neta/plans.py:39,452,500,540
tcc_tmt_amps -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:29,93; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:28; apps/control-plane-api/services/neta/router.py:2044,2060,2076
tcc_tmt_curves -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:31,95; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:30
tcc_tmt_frames -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:28,92,103,231; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:27; apps/control-plane-api/services/neta/router.py:2041,2057,2073
tcc_tmt_settings -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:30,94; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:29
tcc_tmt_thermal_adj -> apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:32,96; apps/control-plane-api/tests/test_neta_tmt_live_integration.py:31
tcc_trip_styles -> apps/control-plane-api/scripts/audit_etu_ground_variants.py:326; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:19,59
tcc_trip_types -> apps/control-plane-api/scripts/audit_etu_ground_variants.py:327; apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:20,60
```

Router-specific notes:

- `apps/control-plane-api/services/neta/router.py` has `146` exact table reference lines.
- `_PICKUP_TABLES` names the four ETU pickup tables.
- `_RELAY_ANALYTICAL_FAMILY_CONFIG` hardcodes `work.tcc_relay_curves_*` and `work.tcc_relay_curve_rows_*` for IEC/MEQ/BSL/SWZ/PCD.
- `_RELAY_WORK_SCHEMA_TABLES` guards only `tcc_relays`, `tcc_relay_devices`, `tcc_relay_line_sections`, `tcc_relay_td_sections`, `tcc_relay_ranges`, `tcc_relay_curves_iec`, `tcc_relay_curve_rows_iec`, `tcc_relay_curves_tcp`, and `tcc_relay_curve_points_tcp`.
- `_relay_work_schema_tables_available` checks the `work` schema and that table list; `_ensure_relay_catalog_available` returns `503` if unavailable.

Probe notes:

- `probe_live_relay_sql_parity.py` directly references `work.tcc_relay_td_sections`, `work.tcc_relay_curves_tcp`, `work.tcc_relay_curve_points_tcp`, plus dynamic `work.tcc_relay_curves_{family}` / `work.tcc_relay_curve_rows_{family}`.
- `probe_live_etu_sql_parity.py` does not directly reference TCC tables; it calls `fn_sensor_available_settings` and `fn_evaluate_test_results`.

Live indirect SQL objects also matter for Phase 3:

| Object | TCC/view/function dependencies |
| --- | --- |
| `vw_trip_unit_cascade` | `tcc_etu_sensors`, `tcc_manufacturers`, `tcc_manufacturers_pre_rebuild`, `tcc_trip_styles`, `tcc_trip_types` |
| `vw_sensor_calc_context` | `tcc_etu_sensor_maint`, `tcc_etu_sensors`, `tcc_manufacturers`, `tcc_trip_styles` |
| `fn_sensor_available_settings(integer)` | `public.tcc_etu_plugs`, `public.tcc_etu_sensors`, `public.tcc_etu_ltpu_pickups`, `public.tcc_etu_ltpu_multipliers`, `public.tcc_etu_stpu_pickups`, `public.tcc_etu_inst_pickups`, `public.tcc_etu_gfpu_pickups`, `public.tcc_etu_ltd_bands` |
| `fn_calculate_test_currents(...)` | `vw_sensor_calc_context`, `public.tcc_etu_stpu_overrides`, `fn_calc_etu_pickup_current`, `fn_etu_delay_calc_name` |
| `fn_evaluate_test_results(...)` | `vw_sensor_calc_context`, `fn_calc_etu_pickup_current` |

No direct `apps/mutation-seam` table consumer was found. `apps/operations-web` hits API routes only; its `tcc_number` field references are data field names, not table consumers.

## Deliverable C - Characterization Summary

Carry candidates:

- Base breaker/catalog tables: the `41` base `public.tcc_*` tables listed above.
- Relay catalog tables: the `21` `work.tcc_relays` / `work.tcc_relay_*` tables listed above.
- Do not assume `_pre_rebuild` is only archive residue: live FKs for breaker manufacturer tables, `tcc_trip_types`, and empty `tcc_test_plans` still target `_pre_rebuild` tables.
- `tcc_etu_sensor_maint_v2` is the only `_v2` table present live.

Surprises / phase-1 design flags:

1. `tcc` schema is clear; it does not exist live.
2. The plan path named by the dispatch was absent in this clone.
3. Breaker route SQL joins `tcc_manufacturers`, but breaker manufacturer FKs target `tcc_manufacturers_pre_rebuild`.
4. `manufacturer_id = 262` exists in `_pre_rebuild` and is referenced by MCCB/PCB/trip-type rows, but is absent from base `tcc_manufacturers`; this is the concrete landmine for any FK retarget to base.
5. `seam.equipment_models` and `get_apparatus_resources(...)` are absent live; apparatus anchoring should be documented-deferred unless Phase 1 first introduces the missing anchor surface.
6. Relay guard coverage is narrower than the full live relay table set. It checks the core published preview surface, not every populated relay table such as `tcc_relay_discrete_values`, all analytical family rows, unsupported family tables, or `tcc_relay_curves_*` beyond IEC/TCP.

## Verification

Read-only live SQL was executed inside explicit `BEGIN READ ONLY` transactions. Commands used only `SELECT` against catalog metadata and table counts.

Validation commands / checks:

- live `public.tcc_*` inventory, FK map, `work.tcc_relay*` inventory, `tcc` schema existence, and apparatus-anchor existence via SQLAlchemy read-only session
- exact repo table-reference scan with `rg`, excluding dependency/generated/agent-history noise
- direct route-source grep for manufacturer joins and relay guard/config references

No repo source code, tests, migrations, schemas, routes, data, or package/lockfile files were changed. Existing unrelated local residue (`pnpm-lock.yaml`, `output/`, and canary actual JSON files) was left untouched.
