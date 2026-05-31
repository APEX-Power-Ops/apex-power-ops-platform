# Decision-012 Phase 2 EXPAND Re-Run Closeout

Dispatch: `2026-05-30-cc-d012-phase2-expand-rerun`
Executor: Codex
Date: 2026-05-31
Status: Complete. EXPAND is live behind back-compat views.

## Claim

- Claim commit pushed: `a86e38ac` (`claim: 2026-05-30-cc-d012-phase2-expand-rerun by codex`)
- Predecessor was already done: `2026-05-30-cc-d012-relay-guard-view-aware`
- No migration SQL or route/probe/test SQL was edited.
- Live credential value was not printed.

## Dry-Run

Isolation used:

- on-prod dry-run
- authored UP SQL from `infra/database/migrations/tcc/001_tcc_schema_expand.sql`
- final `COMMIT;` transformed to `ROLLBACK;` only in the execution stream
- `psql -v ON_ERROR_STOP=1 -X`

Result: PASS. The UP ran through two-phase remap, `CREATE SCHEMA tcc`, the 60 table moves, back-compat views, final guards, and then rolled back.

Dry-run remap notices:

```text
NOTICE:  remap tcc_brk_iccb: 29 row(s) translated via temp space
NOTICE:  remap tcc_brk_mccb: 599 row(s) translated via temp space
NOTICE:  remap tcc_brk_pcb: 157 row(s) translated via temp space
NOTICE:  remap tcc_emt: 174 row(s) translated via temp space
NOTICE:  remap tcc_trip_types: 559 row(s) translated via temp space
ROLLBACK
```

## Deploy Sanity

Immediately before the real UP, hosted relay sections returned HTTP 200 with real rows:

```text
GET https://control.apexpowerops.com/api/v1/neta/relay/sections?supported_only=true&limit=3
HTTP_STATUS:200
count: 3
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

All required post-commit checks passed. The 90s relay re-poll was not needed, and DOWN was not needed.

| Check | Result |
| --- | --- |
| ETU parity | PASS: `RESULT PASS: live ETU SQL settings parity holds across 3 seeded scenario(s); evaluate warnings: 0` |
| Relay parity | PASS: `RESULT PASS: live relay SQL parity holds across 6 seeded scenario(s); families: bsl, iec, meq, pcd, swz, tcp; warnings: 0; failures: 0` |
| Breaker catalog/status | PASS: HTTP 200, `{"catalog":"live","manufacturer_count":63,"sensor_count":17831}` |
| Relay sections | PASS: HTTP 200, `count: 3` with real section rows |

## Live State Confirmation

Read-only state confirmation after the gate:

| Surface | Result |
| --- | --- |
| `tcc` schema exists | `true` |
| `tcc` base tables | `60` |
| back-compat old-name views | `60` |
| `work.tcc_relay*` views | `21` |
| `public.tcc_*` carried views | `39` |
| `tcc.manufacturers` rows | `450` |

Manufacturer FK retarget confirmation:

| Source | Target |
| --- | --- |
| `tcc.brk_iccb(manufacturer_id)` | `tcc.manufacturers(id)` |
| `tcc.brk_mccb(manufacturer_id)` | `tcc.manufacturers(id)` |
| `tcc.brk_pcb(manufacturer_id)` | `tcc.manufacturers(id)` |
| `tcc.emt(manufacturer_id)` | `tcc.manufacturers(id)` |
| `tcc.trip_types(manufacturer_id)` | `tcc.manufacturers(id)` |

## Surprise / Follow-Up

No new surprise was found in this run. The relay guard view-aware patch was live enough for the post-commit relay route and relay parity checks to pass over the back-compat views.

Next lane: Decision-012 Phase 3 route SQL repoint and parity gate.

## Boundary

No route, probe, test, schema file, migration SQL, package, lockfile, or generated output file was changed by this executor. The only repo changes for this closeout are the inbox lifecycle rename and this handoff.
