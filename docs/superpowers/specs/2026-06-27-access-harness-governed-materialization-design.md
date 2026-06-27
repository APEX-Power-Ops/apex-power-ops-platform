# Access Fidelity Harness - Governed Materialization + Per-Table Checksum (Path-A enablement)

**Date:** 2026-06-27
**Lane:** `tcc/access-fidelity-harness` (PR #42, rebased onto main `42669c85` as `7e71b734`)
**Status:** spec for operator spec-review gate (pre-plan)
**Builds on:** Phase 1 harness (`docs/superpowers/specs/2026-06-26-access-fidelity-harness-phase-1-design.md`)

## Why this slice exists (the corrected premise)

The earlier premise -- "the loader must be extended to carry the 3 breaker style parents"
-- is **stale**. Verified 2026-06-27 against the actual `7e71b734` code + a read-only Access
probe: `cli.SLICE_STYLE_TABLES` (`BreakerICCB/MCCB/PCBStyles`) has been in the data-loaded
slice since Task 11, and `_load_slice` loads each full-width via `column_meta` (all columns) +
`read_rows` (`SELECT *`). The probe confirmed `column_meta` returns every D4/D5 column on all
three tables with no C1 UnicodeDecodeError:

| table | cols | rows | D4 (TMT_*) | D5 blocks |
|---|---|---|---|---|
| BreakerICCBStyles | 68 | 608 | 10 | 52 |
| BreakerMCCBStyles | 68 | 10335 | 10 | 52 |
| BreakerPCBStyles | 76 | 3279 | 4 (SST only) | 66 |

So the **loader is complete**. The real Path-A prerequisite is not extraction scope -- it is
producing a **durable, provenance-stamped `access_raw` mirror** the 029/030 prod population SQL
can be generated FROM (operator decision D-C), in a dedicated governed DB (D-B), landed via a
fold-then-merge (D-A). Two genuine gaps block that today:

1. **No durable governed target.** Every harness run targets either the torn-down test DB
   (`tcc_fidelity_test`, dropped CASCADE by the conftest fixture) or whatever the base DSN names
   (currently `postgres`). There is no fenced, durable governed materialization.
2. **The per-table checksum is dormant.** `access_meta.tables.checksum`,
   `access_validation.checksum_reconciliation` (access/staging/matches), the `'checksummed'`
   load_state, and `checksum.table_checksum()` all EXIST but nothing in the pipeline populates
   them. `load_table` writes only `staging_row_count`; `inventory.populate_meta` only PRESERVES a
   checksum that was never written. D-C's "stamp table checksums" assumes a value the harness does
   not currently produce.

## Goal

Make the harness produce, on demand, a **durable provenance-stamped `access_raw` mirror** of the
breaker/TMT slice (incl. the 3 style parents with all D4/D5 columns) in a dedicated governed DB,
with a **recorded, access-vs-staging-validated per-table checksum** -- so the next slice (D-C) can
generate the 029/030 population SQL FROM governed `access_raw` with a complete, auditable
provenance header.

## Scope (in)

### Piece 1 - Governed-target affordance (D-B)
- `config.governed_pg_dsn()` -> derive `tcc_fidelity_governed` from the base DSN by swapping only
  the database path (byte-identical netloc), exactly mirroring `config.test_pg_dsn()`.
- A `--governed` flag on the `load`, `inventory`, and `run-all` subcommands that routes EVERY
  connection (autocommit + tx) through `governed_pg_dsn()` instead of `pg_dsn()`.
- A **hard fence**: assert `current_database() == 'tcc_fidelity_governed'` before any write when
  `--governed` is set (mirrors the conftest test fence; fail closed so a governed run can never
  write into `postgres`/`_test`/prod).
- Idempotent `config.ensure_database(admin_conn, dbname)` / a `provision-governed` preflight:
  `CREATE DATABASE tcc_fidelity_governed` if absent (checked via `pg_database`, run from an
  autocommit admin connection to the base DB; the base DSN is a cluster superuser). No-op if it
  exists. Never drops.

### Piece 2 - Per-table checksum wiring (the dormant-machinery gap)
- A new pipeline step (e.g. `validate.reconcile_checksums(pg_conn, data_conn, run_id,
  loaded_tables, col_types_by_table)`) that, for each LOADED table (skip count-only curves):
  - computes the **staging checksum** = `checksum.table_checksum(rows_from_access_raw, col_types)`,
  - computes the **access checksum** = `checksum.table_checksum(read_rows_from_access, col_types)`,
  - both sides use the SAME `col_types` from `extract.column_meta` (the Task-2 symmetric contract;
    access_raw is created in `column_meta` order, so `SELECT *` aligns positionally),
  - writes `access_meta.tables.checksum = <staging checksum>` and sets `load_state='checksummed'`,
  - upserts `access_validation.checksum_reconciliation (run_id, table_name, access_checksum,
    staging_checksum, matches)`.
- Wire this step into `run_all`, `cmd_load`, and `cmd_inventory` AFTER `_load_slice`.
- This is pure structural fidelity (a hash + a boolean) -- HR1-clean. It also turns the
  access-vs-staging checksum match into a real Phase-1 round-trip fidelity proof (today only the
  row COUNT is reconciled).

### Piece 3 - Style-parent validation coverage
- `reconcile_counts` already covers all loaded tables incl. the 3 style parents (access-vs-staging
  row count). Piece 2 adds the checksum reconciliation for them.
- Add `key_quality(... 'ID' ...)` on each `BreakerXXXStyles` (the integer `ID` is the keyable
  surrogate) so the style parents carry a recorded key-uniqueness row. `style_provenance_antijoin`
  already covers `BreakerXXXStyles.ID -> brk_xxx_styles.source_id`.

## Scope (out / deferred)

- **D-C population generator swap** -- the 029/030 SQL generated FROM governed `access_raw` with a
  provenance header (run_id + frozen sha256 + per-table checksum + row counts). Authored AFTER
  merge against the REAL governed materialization, not a transient/test run. (Next slice.)
- **031 view-transition** -- after populated data; carries the 028 `frame_counts` perf fix.
- **Type-drift verification** (`access_meta.columns.round_trip_verified`, `access_validation.type_drift`
  population) -- Phase 2.
- **Physical host snapshot of access_raw** -- NOT chosen (D-C = generate-SQL-from-governed).

## Provenance header contract (informs D-C, built next slice)
The governed run leaves, per style table, everything the population header must cite:
- from `access_meta.extraction_run`: `run_id`, `source_sha256`, `frozen_copy_path`, `source_size`,
  `source_mtime_utc`, `driver_name`, `dbms_version`.
- from `access_meta.tables`: `checksum` (the access_raw checksum), `access_row_count`,
  `staging_row_count`.
- from `access_validation.checksum_reconciliation`: `matches = true` (a generation precondition).

## HR1 fidelity
Every new value is structural -- a sha256 hash, a boolean `matches`, row counts, a key-uniqueness
boolean. No interpretation, no verdict columns. `checksum_reconciliation` already has exactly these
columns in `001_schemas.sql`; no schema migration is required.

## Global constraints (binding)
- ASCII-only in all user-facing copy and comments.
- Merge to main is OPERATOR-GATED; no prod writes; no promotion without an explicit go.
- Governed runs target `tcc_fidelity_governed` ONLY, enforced by the fence (fail closed).
- Access is read ONLY (read-only pyodbc against the frozen copy).
- Never echo secrets / DSNs / passwords.
- TDD on the test DB (`tcc_fidelity_test`); the governed DB is touched only by explicit
  `--governed` runs, never by the test suite.
- Commit identity `jasonlswenson-sys <jasonlswenson@gmail.com>`; commits end with the
  `Co-Authored-By: Claude Opus 4.8 (1M context)` trailer.
- No new third-party dependencies.

## Open decision for the operator (surfaced, with lean)
**The checksum gap (Piece 2).** D-C assumed table checksums are available; they are not computed
today. Options:
- **(a) Wire checksum + checksum_reconciliation into the governed run [LEAN].** The checksum
  becomes part of the provenance record, validated access-vs-staging, recorded under the run_id;
  lights up dormant Phase-1 fidelity machinery; the generator just reads it. ~one extra full read
  of the slice (curves excluded) -- seconds.
- (b) Compute the checksum ad-hoc at generation time in the D-C generator. Lighter now, but the
  checksum is not part of the governed materialization's provenance record and there is no
  access-vs-staging fidelity proof.

Lean (a): a governed mirror without a recorded, validated checksum is not fully "provenance-
stamped," which is the whole point of Path A.
