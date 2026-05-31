# Decision-012 Relay Guard View-Aware Closeout

Dispatch: `2026-05-30-cc-d012-relay-guard-view-aware`
Executor: Codex
Date: 2026-05-31
Status: Complete. Code patch pushed; live non-regression checks are green.

## Claim

- Claim commit pushed: `f991a2dc` (`claim: 2026-05-30-cc-d012-relay-guard-view-aware by codex`)
- Predecessor was already done: `2026-05-30-cc-d012-phase2-expand-retry`
- No DB DDL was run.
- Live credential value was not printed.

## Blast-Radius Grep

Searched `apps/control-plane-api` for table-only introspection patterns:

```text
get_table_names(
has_table(
information_schema.tables
table_type = 'BASE TABLE'
pg_tables
relkind = 'r'
```

Findings:

| Site | Pattern | Disposition |
| --- | --- | --- |
| `apps/control-plane-api/services/neta/router.py:343` | `inspector.get_table_names(schema="work")` | Relay hosted route gate. Patched in this dispatch. |
| `apps/control-plane-api/services/supabase_mcp_server.py:1038,1041` | `information_schema.tables` + `table_type = 'BASE TABLE'` | Supabase MCP table-summary helper, not a breaker/relay route gate. Left unchanged. |
| `apps/control-plane-api/config.py:99` | `inspector.get_table_names()` | Local diagnostic `test_connection()`, not a route gate. Left unchanged. |
| `apps/control-plane-api/scripts/check_schema_drift.py:43,79` | `get_table_names()`, `pg_tables` | Script-only schema drift check. Left unchanged. |
| `apps/control-plane-api/scripts/audit_etu_ground_variants.py:280` | `get_table_names()` | Script-only audit. Left unchanged. |
| `apps/control-plane-api/scripts/validate_lv_breaker_phase3_families.py:175` | `get_table_names()` | Script-only validator; already also collects `get_view_names()`. Left unchanged. |
| `apps/control-plane-api/scripts/inspect_live_schema.py:16,56` | `get_table_names()`, `pg_tables` | Script-only live inspector. Left unchanged. |
| `apps/control-plane-api/tests/test_neta_tmt_live_integration.py:45` | `get_table_names()` | Integration-test availability skip guard, not hosted route gate. Left unchanged. |
| `apps/control-plane-api/tests/test_neta_emt_live_integration.py:39` | `get_table_names()` | Integration-test availability skip guard, not hosted route gate. Left unchanged. |
| `apps/control-plane-api/tests/test_database.py:13,33,42` | `get_table_names()` | Database tests only. Left unchanged. |
| `apps/control-plane-api/supabase/migrations/20260528_000010_align_etu_runtime_contract.sql:25` | `information_schema.tables` | Migration artifact, not route code. Left unchanged. |
| `apps/control-plane-api/migrations/_archive/002_transfer_data.py:300` | `information_schema.tables` | Archived migration helper. Left unchanged. |

No other base-table-only hosted breaker or relay route gate was found.

## Diff Applied

Code commit pushed: `8fdc7fd7` (`fix: make relay catalog guard view-aware`)

Changed `_relay_work_schema_tables_available` to treat `work` views as valid relay catalog surfaces:

```python
existing = set(inspector.get_table_names(schema="work")) | set(inspector.get_view_names(schema="work"))
```

The `work` schema short-circuit and `except Exception: return False` behavior were left unchanged.

Focused tests added in `apps/control-plane-api/tests/test_neta_relay_routes.py`:

- base relay names as tables -> `True`
- relay names only as views -> `True`
- neither tables nor views -> `False`

## Test Result

Command:

```bash
cd apps/control-plane-api
PYTHONPATH=. .venv/bin/python -m pytest tests/test_neta_relay_routes.py -q
```

Result:

```text
14 passed, 1 warning in 0.55s
```

The warning was the existing Starlette/httpx deprecation warning.

## Deploy / Hosted Poll

Render deploy confirmation could not be independently SHA-confirmed from local context: no `RENDER_*` token was present and the hosted service does not expose a commit/build SHA endpoint. After pushing `8fdc7fd7`, I polled hosted health/readiness for a deploy window:

```text
poll 1 health:200 ready:200
poll 2 health:200 ready:200
poll 3 health:200 ready:200
poll 4 health:200 ready:200
poll 5 health:200 ready:200
poll 6 health:200 ready:200
last_health={"status":"ok"}
last_ready={"status":"ready","database":"connected","catalog_available":true}
```

## Live Non-Regression Checks

All checks were run against `https://control.apexpowerops.com` after the health/readiness poll.

| Check | Result |
| --- | --- |
| ETU parity | PASS: `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0` |
| Relay parity | PASS: `RESULT PASS: live relay SQL parity holds across 6 seeded scenario(s); families: bsl, iec, meq, pcd, swz, tcp; warnings: 0; failures: 0` |
| Breaker catalog/status | PASS: HTTP 200, `{"catalog":"live","manufacturer_count":63,"sensor_count":17831}` |
| Relay sections | PASS: HTTP 200, `count: 3` with real section rows |

## Boundary

Only `apps/control-plane-api/services/neta/router.py` and `apps/control-plane-api/tests/test_neta_relay_routes.py` were changed for the code patch. No migration SQL, route SQL repoint, DB DDL, package, lockfile, or generated output was changed by this executor.
