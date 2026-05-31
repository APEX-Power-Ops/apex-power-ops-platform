# Decision-012 Phase 3 Relay Repoint Closeout

Dispatch: `2026-05-30-cc-d012-phase3-relay-repoint`
Executor: Codex
Date: 2026-05-31
Status: Complete. Relay app SQL and guard are repointed to `tcc.*`; Phase 3 app repoint is complete.

## Claim

- Claim commit pushed: `642d99cb` (`claim: 2026-05-30-cc-d012-phase3-relay-repoint by codex`)
- Repoint commit pushed: `f8ed805a` (`fix: repoint relay SQL to tcc schema`)
- Predecessor was already done: `2026-05-30-cc-d012-phase3-breaker-repoint`
- Live credential value was not printed.
- No DB DDL, migrations, function bodies, or views were changed.

## Enumeration

Exact pre-change scan at the claim commit found 42 old relay table tokens across the enumerated control-plane Python surface (`services/neta`, `scripts`, and `tests`).

| Table | Total | Files |
| --- | ---: | --- |
| `tcc_relays` | 3 | `apps/control-plane-api/services/neta/router.py`: 3 |
| `tcc_relay_devices` | 3 | `apps/control-plane-api/services/neta/router.py`: 3 |
| `tcc_relay_line_sections` | 5 | `apps/control-plane-api/services/neta/router.py`: 5 |
| `tcc_relay_td_sections` | 6 | `apps/control-plane-api/scripts/probe_live_relay_sql_parity.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 4 |
| `tcc_relay_ranges` | 3 | `apps/control-plane-api/services/neta/router.py`: 3 |
| `tcc_relay_discrete_values` | 1 | `apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_relay_curves_iec` | 2 | `apps/control-plane-api/services/neta/router.py`: 2 |
| `tcc_relay_curves_swz` | 1 | `apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_relay_curves_bsl` | 1 | `apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_relay_curves_meq` | 1 | `apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_relay_curves_pcd` | 1 | `apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_relay_curves_tcp` | 4 | `apps/control-plane-api/scripts/probe_live_relay_sql_parity.py`: 1<br>`apps/control-plane-api/services/neta/router.py`: 3 |
| `tcc_relay_curve_rows_iec` | 2 | `apps/control-plane-api/services/neta/router.py`: 2 |
| `tcc_relay_curve_rows_swz` | 1 | `apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_relay_curve_rows_bsl` | 1 | `apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_relay_curve_rows_meq` | 1 | `apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_relay_curve_rows_pcd` | 1 | `apps/control-plane-api/services/neta/router.py`: 1 |
| `tcc_relay_curve_points_tcp` | 5 | `apps/control-plane-api/scripts/probe_live_relay_sql_parity.py`: 2<br>`apps/control-plane-api/services/neta/router.py`: 3 |

Zero occurrences in current app SQL: `tcc_relay_curves_lrm`, `tcc_relay_curves_rxd`, `tcc_relay_curves_egc`.

The guard list, guard schema, guard detail message, route SQL, analytical family config, relay parity probe SQL, and relay guard tests were all accounted for. No breaker refs were touched. Post-change grep found no `work.tcc_relay*`, bare old relay table tokens, `schema="work"`, `_RELAY_WORK_SCHEMA_TABLES`, or `work-schema` text under the control-plane Python relay surface.

## Atomic Diff Summary

| Area | Change |
| --- | --- |
| Route SQL | `work.tcc_relay_*` / `work.tcc_relays` -> `tcc.relay_*` / `tcc.relays` |
| Analytical config | family parent/row table names now use `tcc.relay_curves_*` and `tcc.relay_curve_rows_*` |
| Guard list | `_RELAY_WORK_SCHEMA_TABLES` -> `_RELAY_TCC_SCHEMA_TABLES`, with all 21 relay table names in dropped-prefix form |
| Guard schema | inspector checks `schema="tcc"` for tables/views |
| Guard detail | `work-schema` wording -> `tcc-schema` wording |
| Probe/tests | relay parity SQL and guard assertions updated to `tcc` |

Live read-only schema confirmation before push: `schema_tcc=true`, `expected_count=21`, `missing=[]`.

## Local Validation

| Check | Result |
| --- | --- |
| Relay route/live integration pytest slice | PASS: `15 passed, 1 warning in 8.13s` |
| Py compile for edited route/probe/tests | PASS |

Focused pytest command:

```bash
cd apps/control-plane-api
PYTHONPATH=. .venv/bin/python -m pytest \
  tests/test_neta_relay_routes.py \
  tests/test_neta_relay_live_integration.py \
  -q
```

## Deploy Confirmation

Pushed `f8ed805a` to `main`. Hosted readiness was polled six times after the push:

- `/health`: HTTP 200, `{"status":"ok"}`
- `/health/ready`: HTTP 200, `{"status":"ready","database":"connected","catalog_available":true}`

## Post-Deploy Gate

All required post-deploy checks passed. Revert was not needed.

| Check | Result |
| --- | --- |
| Relay parity | PASS: `RESULT PASS: live relay SQL parity holds across 6 seeded scenario(s); families: bsl, iec, meq, pcd, swz, tcp; warnings: 0; failures: 0` |
| Relay sections | PASS: HTTP 200, `count=100` for `supported_only=true&limit=100` |
| Relay context/settings/plot round trip | PASS: selected `td_section_source_id=5075`, context HTTP 200, settings HTTP 200 with `preview_options=3`, plot HTTP 200 with 1 curve and 2 points |
| ETU parity | PASS: `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0` |
| Breaker catalog/status | PASS: HTTP 200, `manufacturer_count=63`, `sensor_count=17831` |

Note: the first `limit=3` relay section returned by search had no preview options, so the round-trip gate scanned supported sections and used the first section with curve data. The successful section was the second scanned section.

## Phase 4 DB Object List

Read-only scan used `pg_get_functiondef` for ordinary functions/procedures and `pg_views.definition` for views. No DB function or view body referenced old relay names (`work.tcc_relay_*`, `work.tcc_relays`, bare `tcc_relay_*`, or bare `tcc_relays`).

Relay-side Phase 4 DB-object prerequisite set: none found.

Breaker-side Phase 4 prerequisite set from the prior closeout still stands: `fn_calculate_test_currents`, `fn_sensor_available_settings`, and `vw_trip_unit_cascade`.

## Boundary

This phase was code-only. It did not touch DB DDL, migration SQL, breaker SQL, back-compat views, function bodies, package manifests, lockfiles, generated output, or unrelated dirty files.
