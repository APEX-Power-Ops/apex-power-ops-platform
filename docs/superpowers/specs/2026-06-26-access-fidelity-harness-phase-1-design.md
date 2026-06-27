# Access Fidelity Harness - Phase 1 (Preserving + Validation) - Design Spec

Status: DESIGN (brainstorming output, pre-plan). Author: CC. Date: 2026-06-26.
Lane: `tcc/access-fidelity-harness` (off main). Repo home: `infra/database/access-harness/`. Dev-only; merge operator-gated.
Operator-ratified decisions + two hard requirements folded in (2026-06-26).
Feeds: writing-plans -> SDD build. First build slice = F-79-03 evidence.

## Goal

A **repeatable** harness that mirrors the Access source (`D:\TCC_NEW.accdb`, 239.3 MB, 79 user tables) into the existing local Postgres `tcc_fidelity_staging` under three disciplined new schemas - `access_raw`, `access_meta`, `access_validation` - **preserving structure, recording provenance, and validating fidelity, with ZERO behavioral interpretation**. Phase 1 is preserving + validation only; the functional `tcc.*` rebuild is deferred to a later phase.

This replaces the one-off `_phase2_load` (which faithfully mirrored only the ETU `Dat*` side - 21 tables, e.g. `DatStyle`=2,094 exact) with a universal, provenance-complete harness covering all 79 tables.

## Proven feasibility (this session)

- Extraction works: `pyodbc` + 64-bit driver `Microsoft Access Driver (*.mdb, *.accdb)` (also ACE.OLEDB.16.0/12.0 present), run ephemerally via `uv run --no-project --with pyodbc`. The probe read all five `Breaker_TMT*` counts + the 26-column `Breaker_TMTFrameSizes` schema, read-only, from the live file.
- F-79-03 Step 1 already executed by the probe: **live Access counts == G1 Master Reference exactly** (H3 stale-ref REFUTED); `tcc` shortfalls are real (frames -169, amps -246, settings -58, curves -4,433, thermal_adj -7,170).
- Constraint found: `MSysObjects` is permission-blocked ("no read permission"); saved-query SQL inventory must use the ACE OLEDB schema rowset (`adSchemaProcedures`/`adSchemaViews`) or an operator-side grant, not the system tables directly.

## Scope

- **Tables: ALL 79 Access user tables.** The inventory/checksum/manifest machinery is **universal from day one** - no special-casing - to avoid building a one-family harness.
- **First acceptance milestone (the first build slice): breaker/TMT + parents**, aimed at F-79-03 evidence: `Breaker_TMTFrameSizes`, `Breaker_TMTFrameAmps`, `Breaker_TMTFrameSettings`, `Breaker_TMTFrameCurves`, `Breaker_TMTThermalTripAdj`, and parents `BreakerICCBStyles`/`BreakerMCCBStyles`/`BreakerPCBStyles`.
- **Out of scope (Phase 2+):** the functional `tcc.*` projection rebuild; Access saved-query -> PG view translation; forms/reports/VBA/macros reimplementation; crosstab/action queries.

## The two hard requirements (load-bearing)

**HR1 - No behavioral interpretation in Phase 1.** The harness MAY report deltas, anti-joins, missing rows, type drift, and query-output differences. It MUST NOT decide whether any delta is "correct." Every `access_validation` artifact is descriptive evidence; classification (loader gap / expected exclusion / projection artifact / ...) is operator authority. No row, view, or report in this harness emits a verdict column.

**HR2 - Query goldens are opt-in.** Phase 1 inventories saved-query **SQL text for all queries** (`access_meta.queries`), but **executes only a curated allow-list** of read-only SELECT queries as goldens (`access_meta.golden_allowlist` -> results into `access_validation`). Access queries can hide parameters, UI dependencies, VBA, and dialect quirks, so no query is executed for a golden unless explicitly allow-listed and confirmed parameterless/read-only.

## Architecture

Three new schemas in `tcc_fidelity_staging` (PG18, local, 127.0.0.1:5432). The existing `_phase2_*` artifacts are LEFT INTACT until the new manifest supersedes them.

### `access_raw.*` - structural data mirror (1:1)
- One table per Access user table, named faithfully (e.g. `access_raw."Breaker_TMTFrameSizes"`), columns + types mapped faithfully from the Access/ODBC type metadata (see Type mapping below). No cleaning, no renaming, no FK enforcement at load (RI is recorded in `access_meta`, not imposed - orphans must survive for fidelity, per the T7/tmt_curves orphan precedent).
- Memo/long-text columns preserved as `text` (note: the memo-field count-inflation trap is a CSV artifact only; `COUNT(*)` via ODBC is authoritative and used everywhere).

### `access_meta.*` - structural inventory + provenance
- `access_meta.extraction_run` - one row per harness run: `run_id`, `source_path`, `frozen_copy_path`, `source_size`, `source_mtime_utc`, `source_sha256`, `extracted_at_utc`, `driver_name`, `driver_version`, `read_only` (bool), `harness_version`.
- `access_meta.tables` - per table: name, Access object type, `access_row_count`, `staging_row_count`, `checksum`, status, timing (supersedes `_phase2_load_manifest`).
- `access_meta.columns` - per column: table, name, ordinal, Access type, mapped PG type, nullable, size/precision.
- `access_meta.primary_keys`, `access_meta.indexes`, `access_meta.relationships` - PKs, indexes, and declared relationships (via ODBC catalog functions / ACE OLEDB schema rowsets `adSchemaPrimaryKeys`/`adSchemaIndexes`/`adSchemaForeignKeys`).
- `access_meta.queries` - saved-query inventory: name, type (SELECT/crosstab/action/...), `sql_text`, `is_parameterless` (best-effort), `golden_eligible` (bool). Source: ACE OLEDB schema rowset or operator grant (MSysObjects blocked).
- `access_meta.golden_allowlist` - the curated opt-in list of query names to execute as goldens (HR2).

### `access_validation.*` - fidelity reports (descriptive only, HR1)
- `access_validation.row_count_reconciliation` - per table: `access_row_count`, `staging_row_count`, delta. (Note: count parity is necessary, not sufficient.)
- `access_validation.checksum_reconciliation` - per table: deterministic checksum (ordered hash of rows by PK/natural key) on the Access side vs the `access_raw` side; match/mismatch.
- `access_validation.type_drift` - columns whose Access type does not round-trip cleanly to the mapped PG type.
- `access_validation.antijoin_vs_tcc` - for tables that map to governed/sandbox `tcc.*`: bidirectional set difference (`access_raw EXCEPT tcc` and `tcc EXCEPT access_raw`), keyed correctly (frames on `ID`<->`id`; children frame-grain count then natural key, per the F-79-03 runbook - amps `(FrameSizeID, TripAmp)`, curves `(FrameSizeID, Class, Time, Amps)`, settings/thermal natural key confirmed at build). Carries a `lineage` tag (`1:1_load` / `computed` / `derived`) so curves/thermal_adj are flagged as apples-to-oranges comparands, NOT asserted as gaps.
- `access_validation.golden_diff` - for allow-listed queries: Access result set vs the equivalent `access_raw` query; row/value differences.

All `access_validation` rows are evidence. None carries a verdict (HR1).

## Freeze / integrity (mandatory)

Before extraction, the harness:
1. Copies `D:\TCC_NEW.accdb` to a frozen, hashed snapshot under a configured archive dir (e.g. `D:\_access_frozen\TCC_NEW_<mtime>_<sha8>.accdb`).
2. Computes + records `source_sha256`, `source_size`, `source_mtime_utc`, `source_path`, `frozen_copy_path`, `extracted_at_utc`, `driver_name` + `driver_version`, `read_only=true` into `access_meta.extraction_run`.
3. Extracts from the FROZEN copy, read-only (`ReadOnly=1`).
The live file is never modified. A re-run against the same frozen sha is reproducible.

## Extraction tooling

- Python (3.12) + `pyodbc`, uv-managed (proven). Connection: `DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=<frozen>;ReadOnly=1;`.
- Schema/index/relationship metadata via pyodbc catalog methods (`cursor.columns/primaryKeys/statistics/foreignKeys`) and/or ACE OLEDB schema rowsets where richer.
- Saved-query SQL via ACE OLEDB `adSchemaProcedures`/`adSchemaViews` (MSysObjects is permission-blocked - confirmed); if that path is insufficient, fall back to a one-time operator-side `GRANT SELECT ON MSysObjects` (documented, operator-run). Flagged as the one extraction sub-risk.

## Type mapping

A documented Access/ODBC -> PG type map (e.g. `COUNTER`->`integer`/PK, `LONG`->`integer`, `DOUBLE`/`SINGLE`->`double precision`/`real`, `CURRENCY`->`numeric(19,4)`, `DATETIME`->`timestamp`, `BIT`->`boolean`, `VARCHAR`/`LONGCHAR`(memo)->`text`, `GUID`->`uuid`/`text`). Any column that does not map cleanly is loaded as `text` and recorded in `access_validation.type_drift` (HR1: reported, not "fixed").

## Component / file structure (for writing-plans)

`infra/database/access-harness/`
- `pyproject.toml` (uv; deps pyodbc + a PG driver, e.g. psycopg)
- `access_harness/freeze.py` - copy + hash + record `extraction_run`
- `access_harness/extract.py` - read Access tables/data/schema/indexes/relationships/queries (pyodbc/ACE)
- `access_harness/typemap.py` - Access/ODBC -> PG type mapping + drift detection
- `access_harness/load.py` - create `access_raw` tables + bulk load (idempotent per run)
- `access_harness/inventory.py` - populate `access_meta.*`
- `access_harness/checksum.py` - deterministic per-table checksum (both sides)
- `access_harness/validate.py` - row-count/checksum/type-drift/anti-join/golden reports -> `access_validation.*`
- `access_harness/cli.py` - `freeze`, `extract`, `load`, `inventory`, `validate`, `run-all` subcommands
- `infra/database/access-harness/sql/` - DDL for the three schemas
- `infra/database/access-harness/README.md` - runbook

## Testing

- TDD on the PG-side + pure logic (type mapping, checksum determinism, anti-join keying, manifest writing) with synthetic fixtures - no Access dependency.
- An integration test against the FROZEN real `.accdb` for the breaker/TMT acceptance slice (the first milestone): mirror -> inventory -> validate -> the `antijoin_vs_tcc` report reproduces the probe's known deltas (frames -169 etc.). Mirrors the breaker-sandbox harness's synthetic-fixture-first + real-acceptance rigor.

## First build slice (F-79-03 acceptance)

1. Stand up the three schemas + the universal `access_meta`/`access_validation` machinery.
2. Freeze + extract + load the breaker/TMT tables + their 3 style parents into `access_raw`.
3. Inventory ALL 79 tables into `access_meta` (universal from day one; data load for the rest follows).
4. Produce `access_validation.antijoin_vs_tcc` for the TMT tables against governed/sandbox `tcc.*` (tcc id-sets via the breaker-viewer MCP / host), keyed per the F-79-03 runbook; lineage-tagged.
Acceptance: the anti-join report reproduces the probe deltas and enumerates the specific missing rows (frame IDs; child natural keys) for the operator's H1/H2/H4 verdict - WITHOUT the harness classifying them (HR1).

## Provenance

Every `access_raw` table + `access_validation` report traces to an `access_meta.extraction_run` (sha-pinned frozen source). When the functional `tcc.*` rebuild lands (Phase 2), each promoted object will trace back to `access_raw` or an allow-listed Access query.
