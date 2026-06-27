# Access Fidelity Harness - Phase 1 (Preserving + Validation) - Design Spec (Rev 2)

Status: DESIGN (brainstorming output, pre-plan). Author: CC. Date: 2026-06-26.
Lane: `tcc/access-fidelity-harness` (off main). Repo home: `infra/database/access-harness/`. Dev-only; merge operator-gated.
**Rev 2** folds an engine-diverse review (Codex `apex-jobs review-run` + a 5-lens Claude panel that empirically probed the live `.accdb` and the host `tcc`): 5 critical + 11 important + 8 minor, all build-blocking-or-real. The conceptual frame (1:1 mirror, no-FK, descriptive-only, freeze/provenance) survived; the metadata-extraction path and the entire anti-join were re-specified. Changelog at the end.

## Goal

A **repeatable** harness that mirrors the Access source (`D:\TCC_NEW.accdb`, 239.3 MB, 79 user tables) into the existing local Postgres `tcc_fidelity_staging` under three disciplined new schemas - `access_raw`, `access_meta`, `access_validation` - **preserving structure, recording provenance, and validating fidelity, with ZERO behavioral interpretation**. Phase 1 is preserving + validation only; the functional `tcc.*` rebuild is deferred to Phase 2.

Replaces the one-off `_phase2_load` (which mirrored only the ETU side into ~20 bare `public.Dat*`/`Manufacturers` tables + `public._phase2_load_manifest`; e.g. `public."DatStyle"`=2,094 exact) with a universal, provenance-complete harness over all 79 tables.

## Proven feasibility + hard ground facts (probed this session)

- Data SELECT path works: `pyodbc` + 64-bit `Microsoft Access Driver (*.mdb, *.accdb)`, run via `uv run --no-project --with pyodbc`. `SELECT TOP 1 *` + `cursor.description` returned all 26 columns of `Breaker_TMTFrameSizes` with types. The DATA path is sound.
- **Broken catalog methods (verified live, build-blocking):** `cursor.columns()` raises `UnicodeDecodeError` (illegal UTF-16 surrogate) on **33/79 tables including every acceptance table** (all `Breaker_TMT*`, all 3 style tables, `Dat*`, `EMT_*`, `Relay*`). `cursor.primaryKeys()` / `cursor.foreignKeys()` raise `IM001` (unsupported) on every table. **Only `cursor.statistics()` works** among catalog methods. => column metadata MUST come from `cursor.description` + ACE OLE DB; PK from `cursor.statistics()`; FK/index from ACE OLE DB.
- **OLE DB needs COM:** ACE `adSchemaProcedures` (22) + `adSchemaViews` (11) return full saved-query SQL with NO `MSysObjects` grant (which is permission-blocked). But `OpenSchema` is a COM call requiring `pywin32` - an undeclared dependency. `adSchemaTables` returns 103 objects = 79 `TABLE` + 8 `ACCESS TABLE` + 5 `SYSTEM TABLE` + 11 `VIEW`; "79 user tables" = the `TABLE_TYPE='TABLE'` subset only.
- **F-79-03 Step 1 (done):** live Access `COUNT(*)` == G1 Master Reference exactly -> H3 stale-ref REFUTED; tcc shortfalls real (frames -169 etc.). These are COUNT deltas, NOT validated row anti-joins.
- **tcc re-keying (verified on `tcc_breaker_viewer_20260625`):** `tcc.tmt_frames.id` is a **dense re-sequenced surrogate (1..42082)** that does NOT preserve Access `Breaker_TMTFrameSizes.ID`. The Access frame->tcc bridge survives only through `tcc.brk_*_styles.source_id` (= Access `Breaker*Styles.ID`). Real tcc table names: `tmt_frames/tmt_amps/tmt_settings/tmt_curves/tmt_thermal_adj`; real columns differ from Access (`tmt_amps.rating` not `TripAmp`; `tmt_curves.time_sec`/`current_amp` not `Time`/`Amps`; `tmt_frames.size` varchar vs Access `FrameSize` float).
- **Access PKs are not the surrogates:** `Breaker_TMTFrameSizes` declared PK = composite `(StyleID, FrameDesc)`; `ID` is a separate autonumber unique index (sparse, max 73,351 for 42,238 rows).
- **Key quality varies:** `Breaker_TMTFrameAmps (FrameSizeID, TripAmp)` IS unique (67,206=67,206); `Breaker_TMTFrameCurves (FrameSizeID, Class, Time, Amps)` is NOT (27,730 dup-key rows) and is float-typed; `tmt_thermal_adj` has no per-row natural key.

## Scope

- **Tables: ALL 79 Access user tables** (`TABLE_TYPE='TABLE'` only; exclude system/access/view objects). **Inventory/checksum machinery universal from day one.**
- **First acceptance milestone (first build slice): breaker/TMT + 3 style parents**, aimed at F-79-03 evidence.
- **Out of scope (Phase 2+):** functional `tcc.*` rebuild; saved-query -> PG view translation; golden DIFF execution (Phase 1 only CAPTURES goldens, see HR2); forms/reports/VBA; crosstab/action queries.

## The two hard requirements (load-bearing)

**HR1 - No behavioral interpretation in Phase 1.** The harness reports deltas/anti-joins/missing-rows/type-drift/query-output differences; it MUST NOT decide whether any delta is "correct." Enforced **structurally**, not by prose:
- `access_validation.*` columns are restricted to a permitted shape allow-list (counts, deltas, hashes, key tuples, set-membership, load-process states). A test denylist rejects interpretive column names (`status`/`expected`/`correct`/`category`/`verdict`/`is_gap`...).
- `access_meta.tables.load_state` (the single canonical load-process column; there is NO `status` column) is a closed enum of LOAD-PROCESS states only (`inventoried_only`/`extracting`/`loaded`/`checksummed`/`failed`) - never a fidelity judgment.
- The `lineage` / `tcc_build_kind` value is **operator-authored data the harness JOINs to** (from a documented mapping in `access_meta`), never computed by the harness. No "apples-to-oranges"/"NOT a gap" language anywhere in `access_validation`.

**HR2 - Query goldens are opt-in AND fail-closed.** Phase 1 inventories saved-query SQL for ALL queries (`access_meta.queries`), and CAPTURES (not diffs) golden result sets ONLY for an allow-listed set. Execution gate is fail-closed multi-factor **at run time**: a query executes only if (a) name in `access_meta.golden_allowlist`, AND (b) type == `SELECT` verified from the ACE rowset, AND (c) verified parameter count == 0, AND (d) the connection is opened read-only AND a statement guard rejects anything that is not a single `SELECT`. Allow-list membership is necessary, NOT sufficient. `is_parameterless`/`golden_eligible` are advisory hints only; the authoritative signal is a run-time `golden_exec_guard_passed`. The golden DIFF vs `access_raw` is **deferred to Phase 2** (no PG-side query exists in Phase 1 since query translation is Phase 2); Phase 1 stores the Access-side golden result set as a provenance-stamped reference snapshot.

## Architecture

Three new schemas in `tcc_fidelity_staging` (PG18, local). The existing `public.Dat*` + `public._phase2_load_manifest` are LEFT INTACT (see Supersede below).

### `access_raw.*` - structural data mirror (1:1)
One table per Access user table (`TABLE_TYPE='TABLE'`), named faithfully (e.g. `access_raw."Breaker_TMTFrameSizes"`). Columns + types from `cursor.description` of a probe `SELECT * WHERE 1=0` (+ ACE `adSchemaColumns` for null/size richness) - NOT `cursor.columns()`. No cleaning/renaming; no FK enforcement (orphans must survive). Memo/long-text -> `text`. Decode policy `errors='surrogatepass'` for the lone-surrogate text the catalog exposed.

### `access_meta.*` - structural inventory + provenance (every row carries `run_id`)
- `extraction_run` - `run_id` (PK), `source_path`, `frozen_copy_path`, `source_size`, `source_mtime_utc`, `source_sha256`, `extracted_at_utc`, `driver_name` (from `SQL_DRIVER_NAME` = `ACEODBC.DLL`), `dbms_version` (from `SQL_DBMS_VER`), `read_only`, `harness_version`.
- `tcc_snapshot` - one row per tcc-side capture: `snapshot_id`, host, db name, captured_at, role, per-table tcc counts (+ optional tcc-side checksum). The mutable comparand's provenance (C2/I10).
- `tables` - `run_id`, name, object_type, `load_state` enum (`inventoried_only`/`loaded`/`failed`), `access_row_count`, `staging_row_count`, `checksum`, `has_usable_unique_key` (bool), `tcc_build_kind` (operator-authored: `1:1_load`/`computed`/`derived`/`none`), timing.
- `columns` - `run_id`, table, name, ordinal, access_type (from `cursor.description`/ACE), mapped_pg_type, nullable, size/precision, `round_trip_verified`.
- `primary_keys` - `run_id`, table, declared PK columns (from `cursor.statistics()` PrimaryKey index), + separately any unique indexes (for surrogate detection).
- `indexes`, `relationships` - from ACE `adSchemaIndexes` / `adSchemaForeignKeys` (PRIMARY path; SQLForeignKeys is unsupported). Per-kind `coverage_source` recorded so an empty set is not read as "no declared RI."
- `queries` - `run_id`, name, type, `sql_text`, `sql_text_complete` (bool), `inventory_source`, `is_parameterless` (advisory). UNION of `adSchemaProcedures` (22) + `adSchemaViews` (11) = 33.
- `golden_allowlist` - operator-curated query names (the ONLY execution key).
- `projection_map` - operator/build-authored Access->tcc table+column name + type-alignment map for the anti-join (I2).

### `access_validation.*` - fidelity reports (descriptive only; every row carries `run_id` + applicable `snapshot_id`)
- `row_count_reconciliation` - per loaded table: access vs staging count + delta. (Necessary, not sufficient.)
- `checksum_reconciliation` - per loaded table: **FULL-ROW** deterministic checksum (all columns, canonical normalization: floats->fixed-precision text, NULL sentinel, fixed column order), ordered by a guaranteed-deterministic ordering; never by a candidate natural key. Match/mismatch + which side.
- `type_drift` - columns that don't round-trip cleanly; the exact coercion; `not_comparable_coerced` flag (no match/mismatch verdict on those).
- `key_quality` - per table: candidate keys tested for uniqueness on the Access side; non-unique keys recorded as a hazard (gates the anti-join method).
- `antijoin_vs_tcc` - for `1:1_load` tables with a `projection_map` entry: resolved via the **style-mediated bridge** (Access frame `StyleID` -> `BreakerXXXStyles.ID` == tcc `brk_*_styles.source_id` -> `brk_*_styles.id` -> `tmt_frames.breaker_style_id`), then compared at the resolved grain on natural attributes (NOT raw `id` EXCEPT). Set-diff when the key is unique; **multiset/bag (per-key COUNT) diff when not**. `computed`/`derived` tables (curves, thermal_adj) get a count/shape summary + `row_antijoin_not_applicable`, never a 1.14M-row noise EXCEPT.
- `golden_capture` - the captured Access-side golden result sets for allow-listed queries (reference snapshots; diff deferred to Phase 2).

All `access_validation` rows are evidence. None carries a verdict (HR1).

## Cross-instance bridge (the missing component - C2)

A new `snapshot_tcc` CLI step: connect read-only over the mesh (role `tcc_breaker_ro`, host `apex-dev-pg` `tcc_breaker_viewer_*`, connection string from env/Vault) and pull the needed `tcc.*` key-sets/counts into local `tcc_snapshot.*` inside `tcc_fidelity_staging`, recording `tcc_snapshot` provenance. ALL `EXCEPT`/anti-joins then run LOCAL-to-local (`access_raw` vs `tcc_snapshot`). No anti-join depends on an MCP at runtime.

## Style-mediated frame resolution (the missing component - C3)

The only provenance-honest Access->tcc frame mapping (tcc re-sequenced `id`, dropped Access `FrameSizeID`):
`access_raw.Breaker_TMTFrameSizes.StyleID` -> (== `brk_{class}_styles.source_id`) -> `brk_{class}_styles.id` -> `tmt_frames.breaker_style_id`, then match frames within a style on natural attributes (`FrameDesc`/`FrameSize` <-> tcc frame attrs via `projection_map`). Per-row frame identity is NOT recoverable as an `id` anti-join under Phase-1 tcc keying; this is stated as a limitation (or Phase 2 adds `source_id` to `tmt_frames`). Children resolve inside the resolved frame bucket on their natural attributes.

## Freeze / integrity (mandatory)

Copy `.accdb` -> hashed frozen snapshot `D:\_access_frozen\TCC_NEW_<mtime>_<sha8>.accdb` (create the dir; hash-then-skip-copy if the target sha already exists). Record sha256/size/mtime/source_path/frozen_copy_path/extracted_at/driver_name/dbms_version/read_only in `extraction_run`. Extract from the FROZEN copy read-only (`ReadOnly=1`). Same-sha re-run reproducible.

## Idempotency + error model (the missing model - I5, completeness-critic 5/6/9)

- **Write idempotency:** per table, TRUNCATE+reload inside a transaction (stable schema); every `access_meta.*`/`access_validation.*` row carries `run_id`; decide retain-history vs latest-only at build (lean: retain, latest view). Distinct from reproducible-read.
- **Single-writer:** only one harness run may target the staging schemas at once (advisory lock).
- **Partial-failure/quarantine:** a table that fails extraction (e.g. a future catalog crash, a mid-load error) is recorded `load_state='failed'` with the error; the run continues; failed tables never emit false drift.
- **Driver-capability preflight:** before trusting any metadata source, a probe asserts it returns rows on a real frozen table (guards the C1 class of failure).

## Extraction tooling

Python 3.12 + `pyodbc` (data) + **`pywin32`** (ACE OLE DB `OpenSchema` for columns/PK-richness/indexes/FKs/saved-queries) + a PG driver (psycopg). uv-managed. Connection (data): `DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=<frozen>;ReadOnly=1;`. Metadata sources: `cursor.description` (columns), `cursor.statistics()` (PK/unique indexes), ACE `adSchemaColumns/Indexes/ForeignKeys/Procedures/Views`. Relationship/index completeness via ACE is an explicit, recorded sub-risk (declared RI also lives in the blocked MSys family).

## Type mapping

Driven from observed `cursor.description` across all 79 tables (not an a-priori list). Documented Access/ODBC->PG map (`COUNTER`->`integer`, `LONG`->`integer`, `DOUBLE`/`SINGLE`->`double precision`/`real`, `CURRENCY`->`numeric(19,4)`, `DATETIME`->`timestamp`, `BIT`->`boolean`, `VARCHAR`/`LONGCHAR`->`text`, `GUID`->`uuid` only when values validate else `text`). Non-clean -> `text`, recorded in `type_drift` with `round_trip_verified` (HR1: reported, not "fixed").

## Component / file structure (for writing-plans)

`infra/database/access-harness/`: `pyproject.toml` (pyodbc, pywin32, psycopg); `access_harness/{freeze,extract,typemap,load,inventory,checksum,snapshot_tcc,validate,golden,cli}.py`; `sql/` (DDL for the 3 schemas + `tcc_snapshot`); `README.md`. CLI subcommands: `freeze`, `extract`, `load`, `inventory`, `snapshot-tcc`, `validate`, `golden-capture`, `run-all`.

## Testing

- TDD on pure logic (type mapping, full-row checksum determinism incl. a FLOAT round-trip fixture proving byte-identical both sides, multiset diff, projection-map application, HR2 statement-guard) with synthetic fixtures.
- A **driver-capability probe test** asserting each chosen metadata source returns rows on the frozen file (locks in C1).
- The breaker/TMT acceptance test asserts the **ENUMERATED missing keys** (specific resolved frames / child natural keys), NOT the net count delta (a net delta is reproducible by an offsetting bug). Explicit skip-with-reason when the driver/frozen file is absent.

## First build slice (F-79-03 acceptance)

1. Three schemas + universal `access_meta`/`access_validation` machinery + the HR1 structural guards.
2. Freeze + extract (via the corrected metadata path) + load breaker/TMT + 3 style parents into `access_raw`.
3. Inventory ALL 79 tables into `access_meta` (columns/PK/indexes/relationships/queries; data load for the other 59 = `inventoried_only`).
4. `snapshot_tcc` the TMT/style key-sets into `tcc_snapshot`.
5. `antijoin_vs_tcc` for the TMT tables via the style-mediated bridge + verified `projection_map`, key-quality-gated.
Acceptance: the report ENUMERATES the specific missing resolved frames / child rows for the operator's H1/H2/H4 verdict - reproducing the -169/-246/-58 deltas as a consequence of enumerated rows, with curves/thermal_adj count-only (lineage-gated) - WITHOUT the harness classifying them (HR1).

## Provenance

Every `access_raw` table + `access_validation` report ties to an `extraction_run` (sha-pinned frozen source) AND, for anti-joins, a `tcc_snapshot` id. Phase 2 promotions will trace to `access_raw` or an allow-listed query.

## Supersede / retirement of `_phase2` (I9)

Real artifacts: ~20 `public.Dat*`/`Manufacturers` tables + `public._phase2_load_manifest`. After the universal load proves `access_raw` mirror + checksum parity for those tables, **drop the `public.Dat*` set** (preferred) so there is one copy; until then they remain a frozen comparand. Decision recorded; not auto-dropped.

## Rev 2 changelog (what the review changed)

- Metadata path re-specified: `cursor.description`+ACE (not `cursor.columns`), `cursor.statistics()` PKs, ACE FKs; `pywin32` added (C1/I1/I6/M1/M8).
- Anti-join fully reworked: cross-instance `snapshot_tcc` bridge (C2); style-mediated `source_id` resolution (C3); full-row checksum + key-uniqueness gate + multiset fallback (C4); verified Access->tcc `projection_map` with real names/types (I2); thermal_adj count-only (I7); two-sided provenance (I10).
- HR1 hardened to structural guards + operator-authored `tcc_build_kind` (I3/I4).
- HR2 hardened to a fail-closed run-time multi-factor gate; golden DIFF deferred to Phase 2, capture-only in Phase 1 (C5/M6/M7).
- Added `run_id` everywhere, TRUNCATE+reload idempotency, single-writer, partial-failure/quarantine, driver-capability preflight (I5/I8 + completeness-critic).
- `TABLE_TYPE='TABLE'` filter, freeze dedup, observed-driven type map, real `_phase2` naming + retirement (I9/M2/M3/M4/M5).

## Open decisions surfaced by the rework (operator call)

1. Golden DIFF: capture-only in Phase 1, defer diff to Phase 2 (lean) vs store curated PG-side SQL now to diff in Phase 1.
2. `_phase2` `public.Dat*`: drop after parity proven (lean) vs keep permanently as a frozen comparand.
3. Run history: retain all runs with a latest-view (lean) vs latest-only.
4. C3 frame identity: accept "no row-level ID anti-join in Phase 1, resolve by style+attributes" (lean) vs add `source_id` to `tmt_frames` (touches Phase 2 / governed schema).
