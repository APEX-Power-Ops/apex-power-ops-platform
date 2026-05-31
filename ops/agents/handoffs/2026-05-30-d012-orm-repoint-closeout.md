# Decision-012 ORM Repoint Closeout

Dispatch: `2026-05-30-cc-d012-orm-repoint`
Result: PASS
Date: 2026-05-31

## Summary

Completed the code-only ORM/runtime repoint from retired bare TCC names to schema-qualified `tcc.*` names. No database DDL, view recreation, or migration SQL was run.

Two runtime surfaces needed the repoint:

- `aafcc2f0 api: repoint tcc orm models to tcc schema`
- `ddaffbed api: repoint calc engine tcc consumers to tcc schema`

The second commit was required because hosted `/api/v1/neta/evaluate` imports active curve-generation code from `packages/calc-engine/src/apex_calc_engine`, which still carried its own old ORM/raw-SQL references after the API model copy was fixed.

No revert was needed.

## Enumeration And Repoint

API ORM models repointed in `apps/control-plane-api/models/`:

- `breakers.py`: `BrkICCB -> tcc.brk_iccb`, `BrkMCCB -> tcc.brk_mccb`, `BrkPCB -> tcc.brk_pcb`, `BrkICCBStyle -> tcc.brk_iccb_styles`, `BrkMCCBStyle -> tcc.brk_mccb_styles`, `BrkPCBStyle -> tcc.brk_pcb_styles`
- `reference.py`: `Manufacturer -> tcc.manufacturers`, `TripType -> tcc.trip_types`, `TripStyle -> tcc.trip_styles`
- `tmt.py`: `TMTFrame -> tcc.tmt_frames`, `TMTAmp -> tcc.tmt_amps`, `TMTCurve -> tcc.tmt_curves`, `TMTSetting -> tcc.tmt_settings`, `TMTThermalAdj -> tcc.tmt_thermal_adj`
- `etu_core.py`: `ETUPlug -> tcc.etu_plugs`, `ETUSensor -> tcc.etu_sensors`
- `etu_pickups.py`: `ETULTPUPickup -> tcc.etu_ltpu_pickups`, `ETULTPUMultiplier -> tcc.etu_ltpu_multipliers`, `ETUSTPUPickup -> tcc.etu_stpu_pickups`, `ETUInstPickup -> tcc.etu_inst_pickups`, `ETUGFPUPickup -> tcc.etu_gfpu_pickups`
- `etu_bands.py`: `ETULTDBand -> tcc.etu_ltd_bands`, `ETUSTDBand -> tcc.etu_std_bands`, `ETUGFDBand -> tcc.etu_gfd_bands`
- `etu_curves.py`: `ETUInstCurve -> tcc.etu_inst_curves`, `ETUSensorParam -> tcc.etu_sensor_params`, `ETULTDParam -> tcc.etu_ltd_params`, `ETUSTPUOverride -> tcc.etu_stpu_overrides`, `ETUSensorMaint -> tcc.etu_sensor_maint`
- `etu_equations.py`: `ETUSTDEquation -> tcc.etu_std_equations`, `ETUGFDEquation -> tcc.etu_gfd_equations`
- `user.py`: ETU FK strings now target `tcc.etu_*`; public `tcc_test_plans` / `tcc_test_results` table names were left unchanged.
- `__init__.py` and `services/neta/schemas.py`: comment/docstring hygiene only.

Calc-engine runtime copy repointed in `packages/calc-engine/src/apex_calc_engine/`:

- Models mirror the API ORM repoint for `reference.py`, `tmt.py`, `etu_core.py`, `etu_pickups.py`, `etu_bands.py`, `etu_curves.py`, and `etu_equations.py`.
- `models/user.py`: ETU FK strings now target `tcc.etu_*`; public `tcc_test_plans` / `tcc_test_results` table names were left unchanged.
- Direct calc-engine SQL now targets `tcc.*` in `services/calc_engine/etu_pickup.py`, `etu_ltd.py`, and `etu_curves.py`.
- `services/calc_engine/etu_delay_routing.py` and `tmt_curves.py` received comment/docstring hygiene for the renamed tables.

Each repointed model now uses the canonical bare table name plus `schema='tcc'`, and FK strings use `tcc.<table>.<column>`.

## Scope Checks

- `apps/control-plane-api/models/work.py` and `work_enums.py` carried no old TCC catalog names requiring this packet.
- Relay ORM/raw-SQL was intentionally left out of scope. The remaining `work.tcc_relay_*` FK strings in the calc-engine relay models are work-schema relay tables, not retired TCC catalog back-compat names.
- `apps/control-plane-api/migrations/*.py` were not touched. `rg "migrations\\." apps/control-plane-api -g '*.py'` found no runtime app imports; only `apps/control-plane-api/tests/test_full_access_emt_import.py` imports a migration helper.

## Local Validation

- Mapper configuration with API and calc-engine models loaded together:
  - `PYTHONPATH=../../packages/calc-engine/src:. .venv/bin/python - <<'PY' ... configure_mappers() ... PY`
  - PASS: `mapper_configuration_ok`
- Local-live ETU SQL parity against patched local API on `127.0.0.1:8027`:
  - PASS: `live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0`
- Focused API tests:
  - `50 passed, 1 warning in 0.78s`
- Calc-engine tests:
  - `45 passed, 1 skipped`
- `git diff --check`: PASS before the calc-engine commit.

## Hosted Gate

Hosted surface: `https://control.apexpowerops.com`

Render/autodeploy confirmation: after `ddaffbed` was pushed, hosted ETU parity moved from warning count 3/2 during deploy catch-up to warning count 0 at `2026-05-31 11:23 UTC`.

Post-deploy checks:

| Check | Result |
| --- | --- |
| `scripts/probe_live_etu_sql_parity.py` | PASS, 3 seeded scenarios, evaluate warnings: 0 |
| Affected ETU sensors `25`, `26`, `17892` | PASS via parity probe; settings/evaluate returned 200 and no `UndefinedTable` warnings |
| `scripts/probe_live_relay_sql_parity.py` | PASS, 6 seeded scenarios; families `bsl`, `iec`, `meq`, `pcd`, `swz`, `tcp`; warnings: 0; failures: 0 |
| `/api/v1/neta/catalog/status` | 200, manufacturers: 63, sensors: 17831 |
| `/api/v1/neta/etu/search?q=chint&limit=3` | 200, total count: 5, returned: 3 |
| `/api/v1/neta/tmt/facets` | 200, total matching frames: 40264 |
| `/api/v1/neta/emt/facets` | 200, total matching frames: 805 |
| `/api/v1/neta/settings/29442` | 200, `sensor_id=29442` |
| `/api/v1/neta/context/29442` | 200, `manufacturer=Chint`, `trip_type=NA`, `style=NA1` |
| `/api/v1/neta/etu/breaker-cascade?sensor_id=29442` | 200, `scope.sensor_id=29442`, first manufacturer `Chint` |
| `/api/v1/neta/relay/sections?supported_only=true&limit=3` | 200, count: 3 |

Decision-012 is complete end-to-end for the catalog repoint/drop lane: the catalog is physically unified in `tcc.*`, and the active raw-SQL plus ORM consumer surfaces exercised by the hosted gate no longer depend on the retired bare TCC catalog names.
