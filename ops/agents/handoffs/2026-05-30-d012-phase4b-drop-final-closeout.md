# Decision-012 Phase 4b Terminal Drop Closeout

Dispatch: `2026-05-30-cc-d012-phase4b-drop-final`
Executor: Codex
Date: 2026-05-31
Status: Terminal drop applied. Catalog cleanup succeeded. Post-drop gate surfaced one escalation item: ETU evaluate returns 3 curve-generation warnings from a hidden unqualified ORM reference to retired public TCC names.

## Claim

- Claim commit pushed: `8a3f1619` (`claim: 2026-05-30-cc-d012-phase4b-drop-final by codex`)
- Live credential value was not printed.
- Packet lifecycle followed claim-push before live verification or DDL.

## Final Pre-Drop Verification

Read-only checks immediately before authoring/applying the terminal migration:

| Check | Result |
| --- | ---: |
| Missing drop targets | 0 |
| Existing drop-set views | 60 |
| Existing drop-set tables | 11 |
| DB object body refs | 0 |
| External dependency refs | 0 |
| Safe table sequence couplings with kept dependents | 0 |
| `tcc.etu_sensor_maint_id_seq` owner | `tcc.etu_sensor_maint.id` |

Notes:

- DB body matching used identifier-boundary matching for bare old names to avoid prefix false positives such as `tcc_emt` inside `tcc_emt_frames`.
- Active runtime scan across `apps/control-plane-api/services`, `apps/control-plane-api/scripts`, `apps/control-plane-api/config.py`, and `apps/control-plane-api/main.py` returned 0 matches for the qualified old views, the 10 safe `_pre_rebuild` names, and `tcc_etu_sensor_maint_v2`.

## Migration

Authored and committed:

- `infra/database/migrations/tcc/004_phase4b_drop_backcompat.sql`
- Commit: `24d5608f` (`db: add phase4b terminal drop migration`)

The migration uses one transaction, temp target ledgers, pre-drop guards, `DROP VIEW ... RESTRICT` for 60 views, `DROP TABLE ... RESTRICT` for 11 tables, and a final must-keep/catalog guard. It has no data DOWN.

## Dry-Run

Dry-run replaced only the terminal `COMMIT` with a post-drop count check and `ROLLBACK`.

| Check | Result |
| --- | ---: |
| Drop targets remaining inside dry-run | 0 |
| Must-keep objects missing inside dry-run | 0 |
| `tcc` base tables inside dry-run | 60 |
| Transaction | rolled back |

All 60 `DROP VIEW ... RESTRICT` and 11 `DROP TABLE ... RESTRICT` statements completed with zero errors.

## Apply

Live apply completed with:

- pre-drop guard `DO`: PASS
- 60 `DROP VIEW ... RESTRICT`: PASS
- 11 `DROP TABLE ... RESTRICT`: PASS
- final guard `DO`: PASS
- `COMMIT`: PASS

## Post-Drop Gate

| Gate | Result |
| --- | --- |
| ETU parity | **ESCALATE**: probe exited 0 and settings parity passed across 3 scenarios, but evaluate warning count was `3` rather than expected `0`. |
| Relay parity | PASS: 6 seeded scenarios; families `bsl`, `iec`, `meq`, `pcd`, `swz`, `tcp`; warnings `0`; failures `0` |
| `GET /api/v1/neta/catalog/status` | PASS: HTTP `200`; `catalog=live`, `manufacturer_count=63`, `sensor_count=17831` |
| `GET /api/v1/neta/etu/search?q=chint&limit=3` | PASS: HTTP `200`; count `5`, returned `3` items |
| `GET /api/v1/neta/tmt/facets` | PASS: HTTP `200` |
| `GET /api/v1/neta/emt/facets` | PASS: HTTP `200` |
| `GET /api/v1/neta/settings/29442` | PASS: HTTP `200`; plug `1`, LTPU `6`, STPU `15`, INST `20`, GFPU `7` |
| `GET /api/v1/neta/context/29442` | PASS: HTTP `200`; Chint / `NA` |
| `GET /api/v1/neta/etu/breaker-cascade?sensor_id=29442` | PASS: HTTP `200`; scope includes `sensor_id=29442`, manufacturer Chint |
| `GET /api/v1/neta/relay/sections?supported_only=true&limit=3` | PASS: HTTP `200`; count `3`, first TD section `82782` |

ETU warning detail:

- Sensors affected in the probe: `25`, `26`, `17892`.
- Hosted API evaluate payloads now include `Curve generation unavailable: (psycopg2.errors.UndefinedTable) relation "tcc_etu_sensors" does not exist`.
- Likely hidden app source: legacy SQLAlchemy ORM models still declare unqualified old names, for example `apps/control-plane-api/models/etu_core.py:98` has `__tablename__ = 'tcc_etu_sensors'`, and related ETU curve/band models keep FKs like `ForeignKey('tcc_etu_sensors.id')`.
- This was not caught by the packet's active runtime scan because that scan targeted qualified `public.tcc_*` / `work.tcc_*` names and the safe table names. The post-drop warning proves there is still a bare-name ORM curve-generation consumer path.

## Catalog Confirmation

| Check | Result |
| --- | ---: |
| Drop-set views still present | 0 |
| Drop-set tables still present | 0 |
| Must-keep objects missing | 0 |
| `tcc` base tables present | 60 |

The 10 MUST-KEEP `_pre_rebuild` tables, `public.sops_v2`, `public.tcc_test_plans`, `public.tcc_test_results`, and `tcc.etu_sensor_maint_id_seq` remain present.

## Boundary And Escalation

- The terminal drop is committed; no rollback was attempted.
- No app code, package metadata, lockfile, or row data changes were made in this dispatch.
- Decision-012's catalog cleanup is physically complete, but the post-drop ETU evaluate warning gate is not fully green.
- Recommended next dispatch: repoint or retire the legacy ETU ORM curve-generation model path so hosted evaluate no longer queries bare retired names such as `tcc_etu_sensors`.
