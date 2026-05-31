# Decision-012 Phase 2 EXPAND Retry Closeout

Dispatch: `2026-05-30-cc-d012-phase2-expand-retry`
Executor: Codex
Date: 2026-05-31
Status: Rolled back after post-commit relay parity gate failed. Prod is restored to pre-Phase-2 state.

## Claim

- Claim commit pushed: `33e4a0c2` (`claim: 2026-05-30-cc-d012-phase2-expand-retry by codex`)
- Predecessor was already done: `2026-05-30-cc-d012-phase2-expand`
- Live credential value was not printed.

## Dry-Run

Isolation used:

- on-prod dry-run
- authored UP SQL from `infra/database/migrations/tcc/001_tcc_schema_expand.sql`
- final `COMMIT;` transformed to `ROLLBACK;` only in the execution stream
- `psql -v ON_ERROR_STOP=1 -X`

Result: PASS. The revised UP ran through the two-phase manufacturer remap, `CREATE SCHEMA tcc`, the 60 table moves, back-compat views, final guards, and then rolled back.

Dry-run remap notices:

```text
NOTICE:  remap tcc_brk_iccb: 29 row(s) translated via temp space
NOTICE:  remap tcc_brk_mccb: 599 row(s) translated via temp space
NOTICE:  remap tcc_brk_pcb: 157 row(s) translated via temp space
NOTICE:  remap tcc_emt: 174 row(s) translated via temp space
NOTICE:  remap tcc_trip_types: 559 row(s) translated via temp space
ROLLBACK
```

## Real UP

Result: COMMITTED. The authored UP applied cleanly against prod.

Commit-run remap notices:

```text
NOTICE:  remap tcc_brk_iccb: 29 row(s) translated via temp space
NOTICE:  remap tcc_brk_mccb: 599 row(s) translated via temp space
NOTICE:  remap tcc_brk_pcb: 157 row(s) translated via temp space
NOTICE:  remap tcc_emt: 174 row(s) translated via temp space
NOTICE:  remap tcc_trip_types: 559 row(s) translated via temp space
COMMIT
```

## Post-Commit Gate

The gate found a relay compatibility failure, so the DOWN migration was run as required.

| Check | Result |
| --- | --- |
| ETU parity | PASS: `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0` |
| Relay parity | FAIL: `POST /api/v1/neta/relay/plot-tcc returned HTTP 503: {'detail': 'relay catalog unavailable: work-schema tables not present'}` |
| Breaker catalog/status | PASS: HTTP 200, `{"catalog":"live","manufacturer_count":63,"sensor_count":17831}` |
| Relay sections | FAIL: HTTP 503 |

New surprise: the route relay guard checks `sqlalchemy_inspect(bind).get_table_names(schema="work")` in `apps/control-plane-api/services/neta/router.py`. SQLAlchemy inspector table names do not include views, so replacing `work.tcc_relay_*` base tables with back-compat views left direct SQL viable but made `_ensure_relay_catalog_available` return 503. This is why the migration SQL final guard passed while the hosted route gate failed.

## DOWN / Rollback

DOWN migration was required and was run from `infra/database/migrations/tcc/001_tcc_schema_expand_down.sql`.

Result: COMMITTED.

Reverse remap notices:

```text
NOTICE:  reverse-remap tcc_brk_iccb: 29 row(s) translated via temp space
NOTICE:  reverse-remap tcc_brk_mccb: 599 row(s) translated via temp space
NOTICE:  reverse-remap tcc_brk_pcb: 157 row(s) translated via temp space
NOTICE:  reverse-remap tcc_emt: 174 row(s) translated via temp space
NOTICE:  reverse-remap tcc_trip_types: 559 row(s) translated via temp space
DROP SCHEMA
COMMIT
```

## Post-Rollback Confirmation

| Check | Result |
| --- | --- |
| `tcc` schema exists | `false` |
| Manufacturer FK targets | restored to `public.tcc_manufacturers_pre_rebuild` for ICCB/MCCB/PCB/EMT/trip types |
| Work relay guard names | restored as `BASE TABLE` entries |
| ETU parity | PASS: `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0` |
| Relay parity | PASS: `RESULT PASS: live relay SQL parity holds across 6 seeded scenario(s); families: bsl, iec, meq, pcd, swz, tcp; warnings: 0; failures: 0` |
| Breaker catalog/status | PASS: HTTP 200, `{"catalog":"live","manufacturer_count":63,"sensor_count":17831}` |
| Relay sections | PASS: HTTP 200, `count: 3` with real section rows |

## Boundary

No route, probe, test, schema, migration, package, or lockfile files were changed by this executor. The revised SQL artifacts remain exactly as pulled.
