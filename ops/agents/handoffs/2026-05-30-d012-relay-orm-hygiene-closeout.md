# Decision-012 Relay ORM Hygiene Closeout

Dispatch: `2026-05-30-cc-d012-relay-orm-hygiene`
Result: PASS
Date: 2026-05-31

## Summary

Completed the code-only relay ORM hygiene pass. No database DDL, view recreation, or migration SQL was run.

Commits:

- `665e066d claim: 2026-05-30-cc-d012-relay-orm-hygiene by codex`
- `b45257b2 api: repoint relay orm models to tcc schema`

No revert was needed.

## Relay ORM Repoint

`packages/calc-engine/src/apex_calc_engine/models/relay.py` declared 16 relay ORM classes. All were repointed from `work.tcc_relay_*` back-compat names to canonical `tcc.relay_*` names:

- `RelayTDSection -> tcc.relay_td_sections`
- `RelayCurveIEC -> tcc.relay_curves_iec`, FK `tcc.relay_td_sections.relay_td_section_id`
- `RelayCurveSWZ -> tcc.relay_curves_swz`, FK `tcc.relay_td_sections.relay_td_section_id`
- `RelayCurveBSL -> tcc.relay_curves_bsl`, FK `tcc.relay_td_sections.relay_td_section_id`
- `RelayCurveMEQ -> tcc.relay_curves_meq`, FK `tcc.relay_td_sections.relay_td_section_id`
- `RelayCurvePCD -> tcc.relay_curves_pcd`, FK `tcc.relay_td_sections.relay_td_section_id`
- `RelayCurveLRM -> tcc.relay_curves_lrm`, FK `tcc.relay_td_sections.relay_td_section_id`
- `RelayCurveRXD -> tcc.relay_curves_rxd`, FK `tcc.relay_td_sections.relay_td_section_id`
- `RelayCurveEGC -> tcc.relay_curves_egc`, FK `tcc.relay_td_sections.relay_td_section_id`
- `RelayCurveTCP -> tcc.relay_curves_tcp`, FK `tcc.relay_td_sections.relay_td_section_id`
- `RelayCurveRowIEC -> tcc.relay_curve_rows_iec`, FK `tcc.relay_curves_iec.relay_curve_iec_id`
- `RelayCurveRowSWZ -> tcc.relay_curve_rows_swz`, FK `tcc.relay_curves_swz.relay_curve_swz_id`
- `RelayCurveRowBSL -> tcc.relay_curve_rows_bsl`, FK `tcc.relay_curves_bsl.relay_curve_bsl_id`
- `RelayCurveRowMEQ -> tcc.relay_curve_rows_meq`, FK `tcc.relay_curves_meq.relay_curve_meq_id`
- `RelayCurveRowPCD -> tcc.relay_curve_rows_pcd`, FK `tcc.relay_curves_pcd.relay_curve_pcd_id`
- `RelayCurvePointTCP -> tcc.relay_curve_points_tcp`, FK `tcc.relay_curves_tcp.relay_curve_tcp_id`

Each repointed class now uses the canonical bare table name plus `__table_args__ = {'schema': 'tcc'}`. Existing relationship names stayed unchanged.

`apex_calc_engine.services.calc_engine.relay_dispatch` still imports cleanly after the repoint.

## Zero-Stale-Refs Sweep

Active-code sweep scope:

- `apps/control-plane-api/services`
- `apps/control-plane-api/models`
- `apps/control-plane-api/config.py`
- `apps/control-plane-api/main.py`
- `packages/calc-engine/src`

Excluded as directed: migrations, `_archive`, `__pycache__`, and historical one-off scripts.

Sweep command for retired names, excluding retained non-catalog `tcc_test_*` user tables:

```bash
rg -n "tcc_relay|work\.tcc_relay|public\.tcc_|__tablename__\s*=\s*'tcc_(?!test_)|ForeignKey\('(?:work\.|public\.)?tcc_(?!test_)|FROM\s+(?:work\.|public\.)?tcc_(?!test_)|JOIN\s+(?:work\.|public\.)?tcc_(?!test_)|table_name\s*=\s*'tcc_(?!test_)" apps/control-plane-api/services apps/control-plane-api/models apps/control-plane-api/config.py apps/control-plane-api/main.py packages/calc-engine/src -g '*.py' -g '!**/__pycache__/**' -g '!**/_archive/**' --pcre2
```

Result: `0` active runtime references to retired `public.tcc_*`, `work.tcc_relay_*`, old bare ORM names, old FK strings, or old raw-SQL table names.

Remaining active `tcc_*` tokens were classified as non-retired:

- `tcc_test_plans` / `tcc_test_results`: retained public user test tables in API/user models, calc-engine user models, `main.py`, and `services/neta/plans.py`
- `tcc_number`: ordinary catalog field name, not a table reference
- `tcc_v5_backend`: provenance/docstring text, not a retired table/view reference

Historical migration and handoff artifacts still contain old names by design, especially relay tranche migrations under `infra/database/migrations/work/010_tcc_relay_tables.sql` and `012_tcc_relay_staged_population.sql`; those are not active runtime code and were left unchanged.

## Local Validation

- Mapper/import validation:
  - PASS: `mapper_configuration_ok`
  - PASS: `relay_dispatch_import_ok`
- Calc-engine tests:
  - PASS: `45 passed, 1 skipped`
- Relay route contract tests:
  - PASS: `14 passed, 1 warning`
- `git diff --check`:
  - PASS

## Hosted Sanity

Hosted surface: `https://control.apexpowerops.com`

Autodeploy/deploy confirmation: after `b45257b2` was pushed, all hosted no-regression gates below passed.

| Check | Result |
| --- | --- |
| `scripts/probe_live_relay_sql_parity.py` | PASS, 6 seeded scenarios; families `bsl`, `iec`, `meq`, `pcd`, `swz`, `tcp`; warnings: 0; failures: 0 |
| `GET /api/v1/neta/relay/sections?supported_only=true&limit=3` | 200, count: 3 |
| `POST /api/v1/neta/relay/plot-tcc {"td_section_source_id":5075,"current_multiples":[2.0,10.0]}` | 200, `status=supported`, curves: 1, points: 2 |
| `scripts/probe_live_etu_sql_parity.py` | PASS, 3 seeded scenarios, evaluate warnings: 0 |
| `GET /api/v1/neta/catalog/status` | 200, manufacturers: 63, sensors: 17831 |

Decision-012 is closed: `tcc.*` is the sole active TCC catalog surface, and active code no longer references retired TCC catalog/view/table names.
