# Decision-012 Phase 4b Drop Backcompat Closeout

Dispatch: `2026-05-30-cc-d012-phase4b-drop-backcompat`
Executor: Codex
Date: 2026-05-31
Status: Stopped at dry-run validation. The irreversible UP was not committed to prod.

## Claim

- Claim commit pushed: `19a56e03` (`claim: 2026-05-30-cc-d012-phase4b-drop-backcompat by codex`)
- Live credential value was not printed.
- Packet lifecycle was followed through claim-push before any live validation.

## Final Pre-Drop Verification

Live DB scan was read-only and used literal `position(...)` matching, not SQL `LIKE` wildcard matching.

| Check | Result |
| --- | ---: |
| Expected drop objects | 71 |
| Existing views before drop | 60 |
| Existing tables before drop | 11 |
| Missing targets | 0 |
| External dependency refs | 0 |
| DB body refs | 0 |

Notes:

- The dependency scan excluded PostgreSQL auto/internal ownership artifacts such as table-owned sequences and toast tables. Those are not external consumers.
- The DB body scan covered functions/procedures, views, matviews, triggers, and rules, excluding the target objects' own view/rule bodies.
- Active app/script consumer scan returned 0 matches for the safe `_pre_rebuild` names, `tcc_etu_sensor_maint_v2`, and the qualified `public.tcc_*` / `work.tcc_relay_*` old view names. Historical docs, tests, and migration archives were not treated as runtime consumers.

## Dry-Run Result

The terminal migration was authored locally with:

- one transaction
- pre-drop guard block
- `DROP VIEW ... RESTRICT` for the 60 old-name views
- `DROP TABLE ... RESTRICT` for the 10 safe `_pre_rebuild` tables and `public.tcc_etu_sensor_maint_v2`
- final must-keep guard
- no down migration

Dry-run method:

- streamed the migration to `psql`
- replaced the final `COMMIT;` only in the execution stream with catalog checks plus `ROLLBACK;`
- `psql -v ON_ERROR_STOP=1 -X`

The dry-run failed under `RESTRICT` before any commit:

```text
ERROR:  cannot drop table tcc_etu_sensor_maint_pre_rebuild because other objects depend on it
DETAIL:  default value for column id of table tcc.etu_sensor_maint depends on sequence tcc_etu_sensor_maint_id_seq
HINT:  Use DROP ... CASCADE to drop the dependent objects too.
```

Per the packet guardrail, I stopped and did not force the migration. The local migration artifact was removed and was not committed.

## Dependency Finding

Read-only follow-up showed that the old sequence is shared by the pre-rebuild table default and the canonical table default:

| Field | Result |
| --- | --- |
| Sequence | `public.tcc_etu_sensor_maint_id_seq` |
| `pg_get_serial_sequence('public.tcc_etu_sensor_maint_pre_rebuild', 'id')` | `public.tcc_etu_sensor_maint_id_seq` |
| `pg_get_serial_sequence('tcc.etu_sensor_maint', 'id')` | empty |

Sequence dependents:

| Dependent object | Referenced object | Deptype |
| --- | --- | --- |
| default value for column id of table `tcc_etu_sensor_maint_pre_rebuild` | sequence `tcc_etu_sensor_maint_id_seq` | `n` |
| default value for column id of table `tcc.etu_sensor_maint` | sequence `tcc_etu_sensor_maint_id_seq` | `n` |

Inference: dropping `public.tcc_etu_sensor_maint_pre_rebuild` would attempt to drop the sequence it owns, but canonical `tcc.etu_sensor_maint.id` still depends on that same sequence. This needs a separate authorized fix, likely to retarget or detach sequence ownership/defaults safely before re-running Phase 4b. No such fix was applied in this packet.

## Post-Stop Live Confirmation

After the failed dry-run, read-only confirmation showed the live DB remained unchanged:

| Check | Result |
| --- | ---: |
| Drop-set views still present | 60 |
| Drop-set tables still present | 11 |
| Must-keep objects missing | 0 |
| `tcc` base tables present | 60 |

## Commit / Post-Commit Gate

- Real UP commit: not attempted because dry-run validation failed.
- ETU parity post-commit check: skipped; there was no commit.
- Relay parity post-commit check: skipped; there was no commit.
- Hosted breaker/relay route checks: skipped; there was no commit.
- DOWN migration: not needed; no UP commit occurred and the failed dry-run rolled back on disconnect.

## Boundary

No live DDL was committed. No app code, probe code, package metadata, lockfile, or durable migration file changes were made.
