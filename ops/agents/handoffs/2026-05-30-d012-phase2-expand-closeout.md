# Decision-012 Phase 2 EXPAND Closeout

Dispatch: `2026-05-30-cc-d012-phase2-expand`
Executor: Codex
Date: 2026-05-31
Status: Stopped at validation. The UP migration was not committed to prod.

## Claim

- Claim commit pushed: `c32729a0` (`claim: 2026-05-30-cc-d012-phase2-expand by codex`)
- Predecessor was already done: `2026-05-30-cc-d012-phase0-live-characterization`
- Live credential value was not printed.

## Isolation Used

No Supabase test branch was available from local context, so the packet fallback was used:

- on-prod dry-run
- authored UP SQL from `infra/database/migrations/tcc/001_tcc_schema_expand.sql`
- final `COMMIT;` transformed to `ROLLBACK;` only in the execution stream
- `psql -v ON_ERROR_STOP=1 -X`

## Dry-Run Result

The dry-run failed during the D2 manufacturer remap, before `CREATE SCHEMA tcc` and before any table moves.

Observed output:

```text
BEGIN
DO
CREATE TABLE
INSERT 0 60
DO
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
NOTICE:  remap tcc_brk_iccb: 0 row(s) retargeted
ERROR:  duplicate key value violates unique constraint "tcc_brk_mccb_manufacturer_id_name_key"
DETAIL:  Key (manufacturer_id, name)=(292, MCB [IEC]) already exists.
CONTEXT:  SQL statement "
      UPDATE public.tcc_brk_mccb b
         SET manufacturer_id = c.id
        FROM public.tcc_manufacturers_pre_rebuild p
        JOIN public.tcc_manufacturers c ON c.mfr_name = p.name
       WHERE p.id = b.manufacturer_id
         AND c.id <> b.manufacturer_id
    "
PL/pgSQL function inline_code_block line 7 at EXECUTE
```

`psql` exited non-zero. Per the packet guardrail, I stopped here and did not edit the migration to force it through.

## Read-Only Evidence After Stop

Read-only confirmation after the failed dry-run:

- `tcc` schema exists: `false`
- original manufacturer FK targets are still present on:
  - `public.tcc_brk_iccb -> public.tcc_manufacturers_pre_rebuild`
  - `public.tcc_brk_mccb -> public.tcc_manufacturers_pre_rebuild`
  - `public.tcc_brk_pcb -> public.tcc_manufacturers_pre_rebuild`
  - `public.tcc_emt -> public.tcc_manufacturers_pre_rebuild`
  - `public.tcc_trip_types -> public.tcc_manufacturers_pre_rebuild`

Read-only collision evidence for `tcc_brk_mccb`:

| id | current manufacturer_id | name | pre-rebuild name | mapped canonical id | mapped canonical name | current canonical name |
| ---: | ---: | --- | --- | ---: | --- | --- |
| 401 | 288 | `MCB [IEC]` | `Hager` | 292 | `Hager` | `EPEL` |
| 565 | 292 | `MCB [IEC]` | `Proteus` | 296 | `Proteus` | `Hager` |

Inference from the live evidence: the single-table remap updates rows under a unique key on `(manufacturer_id, name)`. Row `401` wants to move to manufacturer `292` while row `565` still occupies `(292, 'MCB [IEC]')` before its own remap to `296`, so the non-deferrable uniqueness check blocks the statement even though the final mapped state may not contain that duplicate.

## Commit / Post-Commit Gate

- Real UP commit: not attempted because validation failed.
- ETU parity post-commit check: skipped; there was no commit.
- Relay parity post-commit check: skipped; there was no commit.
- Breaker catalog/status smoke: skipped; there was no commit.
- Relay sections smoke: skipped; there was no commit.
- DOWN migration: not needed; no UP commit occurred and the failed dry-run rolled back on disconnect.

## Boundary

No route, probe, test, schema, migration, package, or lockfile changes were made. The authored SQL artifacts remain exactly as pulled.
