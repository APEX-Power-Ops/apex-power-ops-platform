# Access Fidelity Harness - Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable harness that mirrors `D:\TCC_NEW.accdb` (79 user tables) into local Postgres `tcc_fidelity_staging` under `access_raw` / `access_meta` / `access_validation` schemas, preserving structure + provenance and validating fidelity, with ZERO behavioral interpretation. First acceptance slice = F-79-03 evidence (breaker/TMT).

**Architecture:** Python (uv) extraction (`pyodbc` data + `pywin32` ACE OLE DB metadata) -> local PG. Three schemas + a `tcc_snapshot` bridge schema. Anti-joins run LOCAL-to-local after pulling tcc key-sets read-only over the mesh. All metadata sourced from `cursor.description`/`cursor.statistics()`/ACE `adSchema*` (the broken `cursor.columns/primaryKeys/foreignKeys` are forbidden).

**Tech Stack:** Python 3.12, uv, pyodbc, pywin32, psycopg[binary], pytest. Local PG18 (127.0.0.1:5432, db `tcc_fidelity_staging`). Built/run on THIS Windows machine (the `.accdb` + local PG live here), not the Olares host.

**Spec:** `docs/superpowers/specs/2026-06-26-access-fidelity-harness-phase-1-design.md` @ Rev 2 (`4f248aa3`).

## Global Constraints

Every task implicitly includes these (exact values from the spec + operator-ratified decisions):

- **HR1 - no behavioral interpretation.** `access_validation.*` columns restricted to a permitted shape allow-list (counts, deltas, hashes, key-tuples, set-membership, load-process states). A test denylist REJECTS interpretive column names (`status`/`expected`/`correct`/`category`/`verdict`/`is_gap`/`correct?`). `access_meta.tables.status` = closed enum `{inventoried_only, extracting, loaded, checksummed, failed}` only. `tcc_build_kind` is operator-authored data the harness JOINs to (values `{1:1_load, computed, derived, none}`), NEVER computed by the harness. No "apples-to-oranges"/"gap"/"correct" language in any `access_validation` row.
- **HR2 - goldens opt-in + fail-closed.** A saved query executes for a golden ONLY if: (a) name in `access_meta.golden_allowlist` AND (b) type==`SELECT` verified from the ACE rowset AND (c) verified param count==0 AND (d) connection opened read-only AND (e) a statement guard accepts only a single `SELECT`. `is_parameterless`/`golden_eligible` are advisory hints, never the gate. Golden DIFF deferred to Phase 2; Phase 1 CAPTURES the Access-side result set only.
- **Forbidden extraction methods:** `cursor.columns()`, `cursor.primaryKeys()`, `cursor.foreignKeys()` (verified broken on this driver). Use `cursor.description` (columns), `cursor.statistics()` (PK/unique indexes), ACE OLE DB `adSchemaColumns/Indexes/ForeignKeys/Procedures/Views` (FK/index/rich-column/queries).
- **Table set:** `TABLE_TYPE='TABLE'` only (the 79); exclude `ACCESS TABLE`/`SYSTEM TABLE`/`VIEW`.
- **Freeze (mandatory):** copy to `D:\_access_frozen\TCC_NEW_<mtime>_<sha8>.accdb` (create dir; skip-copy if target sha exists); record sha256/size/mtime/source_path/frozen_copy_path/extracted_at/driver_name(`SQL_DRIVER_NAME`)/dbms_version(`SQL_DBMS_VER`)/read_only in `extraction_run`. Extract from the FROZEN copy read-only (`ReadOnly=1`).
- **Idempotency:** every `access_meta.*`/`access_validation.*` row carries `run_id` (FK -> `extraction_run`); per-table TRUNCATE+reload of `access_raw` inside a txn; single-writer advisory lock; retain ALL runs + a `latest` view.
- **Anti-join keying:** style-mediated only - Access frame `StyleID` -> `brk_{class}_styles.source_id` -> `brk_{class}_styles.id` -> `tmt_frames.breaker_style_id`, then natural attributes. Direct surrogate `Breaker_TMTFrameSizes.ID` <-> `tcc.tmt_frames.id` is FORBIDDEN (red-team test, Task 8). Key-uniqueness hard gate: set-diff if unique, multiset (per-key COUNT) diff if not. `computed`/`derived` tables (curves/thermal_adj) = count/shape only.
- **Real tcc names:** `tcc.tmt_frames(id surrogate, breaker_style_id, size)`, `tmt_amps(frame_id, rating)`, `tmt_settings(frame_id,...)`, `tmt_curves(frame_id, class, time_sec, current_amp)`, `tmt_thermal_adj(id, frame_id, adjustment)`, `brk_{mccb,iccb,pcb}_styles(id, source_id, breaker_id, frame, standard)`. `tmt_curves`+`tmt_thermal_adj` are `computed`/`derived` build kinds.
- **Decisions (operator-ratified):** golden diff deferred to Phase 2 (D1); `_phase2` `public.Dat*` drop is a SEPARATE gated cleanup task, NOT in the first build, allowed only after access_raw parity + replacement manifest exist (D2); retain-all-runs + latest view (D3); NO `source_id` added to governed `tcc.tmt_frames` (D4 - frame identity resolved by style+attributes only).
- ASCII-only in all files. Commit identity `jasonlswenson-sys <jasonlswenson@gmail.com>`. Merge operator-gated.

## File Structure

`infra/database/access-harness/`
- `pyproject.toml` - uv project (pyodbc, pywin32, psycopg[binary], pytest)
- `access_harness/__init__.py`
- `access_harness/config.py` - PG connection (local), Access frozen-dir, env/Vault host conn for snapshot
- `access_harness/freeze.py` - copy+hash+dedup; `extraction_run` row
- `access_harness/typemap.py` - Access/ODBC `cursor.description` -> PG type + drift
- `access_harness/extract.py` - corrected metadata + data readers (pyodbc + pywin32 ACE)
- `access_harness/load.py` - access_raw DDL-gen + TRUNCATE/reload + load_state + advisory lock
- `access_harness/inventory.py` - populate `access_meta.*`
- `access_harness/checksum.py` - full-row deterministic checksum + multiset diff
- `access_harness/snapshot_tcc.py` - mesh read-only -> `tcc_snapshot.*` + provenance
- `access_harness/projection.py` - Access->tcc `projection_map` + the FORBIDDEN-key guard
- `access_harness/validate.py` - reconciliation + style-mediated anti-join -> `access_validation.*`
- `access_harness/golden.py` - saved-query inventory + HR2 fail-closed capture
- `access_harness/hr1_guard.py` - `access_validation` column-shape allow-list + interpretive denylist
- `access_harness/cli.py` - subcommands
- `sql/001_schemas.sql` - `access_meta.*`, `access_validation.*`, `tcc_snapshot.*` DDL + `latest` views
- `tests/` - unit (synthetic) + integration (frozen `.accdb`, skip-guarded)
- `README.md` - runbook

---

### Task 0: Scaffold + schemas + PG/connection provisioning

**Files:**
- Create: `infra/database/access-harness/pyproject.toml`, `access_harness/__init__.py`, `access_harness/config.py`, `sql/001_schemas.sql`
- Test: `tests/test_schema_apply.py`, `tests/conftest.py`

**Interfaces:**
- Produces: `config.pg_dsn()` -> str (local harness DSN); `config.frozen_dir()` -> Path; `config.apply_sql(conn, path)`; pytest fixture `pg` (a connection to a throwaway test schema set).

- [ ] **Step 1: Confirm the local PG credential.** The harness needs a working `tcc_fidelity_staging` login. The `tcc-fidelity-staging` MCP already connects, and `apex_pm_stage_user` is a superuser (the `postgres` pw is reportedly lost). Determine the working DSN (env var `ACCESS_HARNESS_PG_DSN`); document in README. Do NOT hardcode a password in code.
- [ ] **Step 2: Write the schema DDL** (`sql/001_schemas.sql`): create schemas `access_raw`, `access_meta`, `access_validation`, `tcc_snapshot`. Create fixed tables (full DDL): `access_meta.extraction_run(run_id text PK, source_path text, frozen_copy_path text, source_size bigint, source_mtime_utc timestamptz, source_sha256 text, extracted_at_utc timestamptz, driver_name text, dbms_version text, read_only bool, harness_version text)`; `access_meta.tables(run_id text, table_name text, object_type text, load_state text CHECK (load_state in ('inventoried_only','extracting','loaded','checksummed','failed')), access_row_count bigint, staging_row_count bigint, checksum text, has_usable_unique_key bool, tcc_build_kind text CHECK (tcc_build_kind in ('1:1_load','computed','derived','none')) , started_at timestamptz, completed_at timestamptz, PRIMARY KEY(run_id, table_name))`; `access_meta.columns`, `primary_keys`, `indexes`, `relationships`, `queries`, `golden_allowlist`, `projection_map`, `tcc_snapshot` (per spec), and the `access_validation.*` tables (`row_count_reconciliation`, `checksum_reconciliation`, `type_drift`, `key_quality`, `antijoin_vs_tcc`, `golden_capture`) - every table includes `run_id`. Add `latest_*` views (most-recent `run_id`).
- [ ] **Step 3: Write the failing test** `tests/test_schema_apply.py::test_schemas_and_core_tables_exist` - applies `001_schemas.sql` to the test DB, asserts the 4 schemas + `access_meta.extraction_run` + `access_validation.antijoin_vs_tcc` exist.
- [ ] **Step 4: Run it - FAIL** (`uv run pytest tests/test_schema_apply.py -v`).
- [ ] **Step 5: Implement** `config.py` (DSN from env, `apply_sql`) + `conftest.py` `pg` fixture (applies DDL to a test schema set, rolls back/drops after). Re-run - PASS.
- [ ] **Step 6: Commit.**

---

### Task 1: Type mapping (pure logic)

**Files:** Create `access_harness/typemap.py`; Test `tests/test_typemap.py`

**Interfaces:**
- Produces: `map_description(desc_row: tuple) -> ColumnType` (from a `cursor.description` 7-tuple: name, type_code, display_size, internal_size, precision, scale, null_ok); `pg_ddl_type(ct: ColumnType) -> str`; `ColumnType` carries `access_type`, `pg_type`, `nullable`, `size`, `precision`, `round_trippable: bool`.

- [ ] **Step 1: Write failing tests** covering: `int`->`integer`, `float`->`double precision`, `str`(short)->`text`, `decimal`->`numeric(19,4)` (currency), `datetime`->`timestamp`, `bool`->`boolean`, `bytearray`->`bytea`, and an unmapped/odd type -> `text` with `round_trippable=False`. Example:
```python
def test_float_maps_to_double_precision():
    ct = map_description(('Sec2InstClrTime', float, 0, 8, 53, 0, True))
    assert ct.pg_type == 'double precision' and ct.round_trippable is True

def test_unknown_type_falls_back_to_text_not_round_trippable():
    ct = map_description(('Weird', object, 0, 0, 0, 0, True))
    assert ct.pg_type == 'text' and ct.round_trippable is False
```
- [ ] **Step 2: Run - FAIL.**
- [ ] **Step 3: Implement** `typemap.py` (a `dict` keyed on Python type-codes pyodbc returns in `description`, plus the fallback). No `cursor.columns()` anywhere.
- [ ] **Step 4: Run - PASS.**
- [ ] **Step 5: Commit.**

---

### Task 2: Full-row checksum + multiset diff (pure logic; CRITICAL - C4)

**Files:** Create `access_harness/checksum.py`; Test `tests/test_checksum.py`

**Interfaces:**
- Produces: `canonical_row(row: tuple, col_types: list[ColumnType]) -> str` (NULL sentinel `\x00NULL`, floats -> `repr`-stable fixed-precision text, fixed column order); `table_checksum(rows: Iterable[tuple], col_types) -> str` (sha256 over rows sorted by `canonical_row`); `multiset_diff(left: Counter, right: Counter) -> dict` (per-key count deltas).

- [ ] **Step 1: Write failing tests** - CRITICAL determinism cases:
```python
def test_checksum_is_order_independent():
    a = [(1, 1.5), (2, 2.5)]; b = [(2, 2.5), (1, 1.5)]
    assert table_checksum(a, T) == table_checksum(b, T)

def test_checksum_float_round_trip_byte_identical():
    # the SAME float read twice (Access->py vs py->PG->py) must hash equal
    assert canonical_row((0.1+0.2,), [FT]) == canonical_row((0.30000000000000004,), [FT])

def test_checksum_distinguishes_null_from_empty_string():
    assert canonical_row((None,), [ST]) != canonical_row(('',), [ST])

def test_multiset_diff_reports_per_key_counts():
    from collections import Counter
    d = multiset_diff(Counter({'k': 3}), Counter({'k': 1}))
    assert d == {'k': {'access': 3, 'tcc': 1, 'delta': 2}}
```
- [ ] **Step 2: Run - FAIL.**
- [ ] **Step 3: Implement** `checksum.py` (float canonicalization via fixed `repr`/`format(x, '.17g')`; NULL sentinel; sort then sha256; multiset via `Counter`).
- [ ] **Step 4: Run - PASS.**
- [ ] **Step 5: Commit.**

---

### Task 3: Metadata + data extraction (Access-touching; CRITICAL - C1/I1)

**Files:** Create `access_harness/extract.py`; Test `tests/test_extract_integration.py` (skip-guarded)

**Interfaces:**
- Produces: `connect_data(frozen_path) -> pyodbc.Connection` (`ReadOnly=1`); `list_user_tables(conn) -> list[str]` (ACE `adSchemaTables`, `TABLE_TYPE='TABLE'` only); `column_meta(conn, table) -> list[ColumnType]` (via `SELECT * WHERE 1=0` + `cursor.description`, `decode errors=surrogatepass`); `primary_key(conn, table) -> list[str]` (via `cursor.statistics()` PrimaryKey index); `foreign_keys(conn_ace, table)`/`indexes(conn_ace, table)` (ACE OpenSchema); `saved_queries(conn_ace) -> list[Query]` (ACE `adSchemaProcedures` UNION `adSchemaViews`, 33); `driver_info(conn) -> (name, dbms_ver)` (`getinfo(SQL_DRIVER_NAME)`, `getinfo(SQL_DBMS_VER)`); `read_rows(conn, table) -> Iterator[tuple]`.

- [ ] **Step 1: Write the driver-capability + red-team tests** (`tests/test_extract_integration.py`, skip if frozen file/driver absent):
```python
def test_cursor_columns_is_forbidden_and_known_broken(conn):
    # locks in C1: the broken method MUST raise on an acceptance table
    with pytest.raises(Exception):
        conn.cursor().columns(table='Breaker_TMTFrameSizes').fetchall()

def test_column_meta_uses_description_and_returns_26(conn):
    cols = column_meta(conn, 'Breaker_TMTFrameSizes')
    assert len(cols) == 26  # proven by the probe

def test_primary_key_is_composite_styleid_framedesc(conn):
    assert primary_key(conn, 'Breaker_TMTFrameSizes') == ['StyleID', 'FrameDesc']

def test_list_user_tables_is_79(conn):
    assert len(list_user_tables(conn)) == 79

def test_saved_queries_total_33(conn_ace):
    assert len(saved_queries(conn_ace)) == 33
```
- [ ] **Step 2: Run - FAIL/skip** (confirm not silently skipping: the frozen file must exist - Task 4 freezes it; for this task, point at `D:\TCC_NEW.accdb` read-only or a pre-frozen copy).
- [ ] **Step 3: Implement** `extract.py` using ONLY the allowed methods + `pywin32` `win32com.client.Dispatch('ADODB.Connection')` for `OpenSchema`. Record per-metadata-kind `coverage_source`.
- [ ] **Step 4: Run - PASS** (against the real file).
- [ ] **Step 5: Commit.**

---

### Task 4: Freeze + extraction_run (Access-touching)

**Files:** Create `access_harness/freeze.py`; Test `tests/test_freeze.py`

**Interfaces:** Produces `freeze(source: Path, dest_dir: Path) -> FrozenSource` (sha256/size/mtime/frozen_path; skip-copy if target exists); `record_extraction_run(pg, frozen, driver_info) -> run_id`.

- [ ] **Step 1: Failing tests** - hash determinism, skip-copy on identical sha, `extraction_run` row has all required provenance fields incl. `driver_name`/`dbms_version`. (Use a tiny temp binary as the "source" for the pure freeze logic; the real `.accdb` is exercised in Task 9.)
- [ ] **Step 2: Run - FAIL.** **Step 3: Implement** (`shutil.copy2`, `hashlib.sha256` streamed, dir create, `<mtime>_<sha8>` name). **Step 4: PASS.** **Step 5: Commit.**

---

### Task 5: access_raw load (TRUNCATE/reload + load_state + single-writer)

**Files:** Create `access_harness/load.py`; Test `tests/test_load.py`

**Interfaces:** Produces `create_access_raw_table(pg, table, col_types)`; `load_table(pg, conn_access, table, run_id) -> int` (TRUNCATE+reload in a txn; returns staging count; on error sets `load_state='failed'` and re-raises-or-quarantines per `continue_on_error`); `with single_writer(pg):` advisory-lock context.

- [ ] **Step 1: Failing tests** (unit, synthetic PG + a fake row source): re-running `load_table` twice yields the SAME row count (idempotent, not doubled); a failing row source marks `load_state='failed'` and does not partially commit; `single_writer` blocks a second concurrent acquire.
- [ ] **Step 2: FAIL. Step 3: Implement** (DDL from `typemap.pg_ddl_type`; `pg_advisory_xact_lock`; per-table txn). **Step 4: PASS. Step 5: Commit.**

---

### Task 6: Inventory population + HR1 guard

**Files:** Create `access_harness/inventory.py`, `access_harness/hr1_guard.py`; Test `tests/test_inventory.py`, `tests/test_hr1_guard.py`

**Interfaces:** Produces `populate_meta(pg, conn_access, run_id, tables)` (tables/columns/primary_keys/indexes/relationships/queries with `run_id`); `assert_no_interpretive_columns(pg)` (scans `access_validation` columns vs the denylist) returning violations.

- [ ] **Step 1: Failing tests** - `populate_meta` writes a `primary_keys` row `(StyleID, FrameDesc)` for frames; `columns` count == 26 for frames; **HR1 guard test**: injecting a column named `is_gap`/`correct`/`verdict` into an `access_validation` table is DETECTED and the guard fails; the legitimate columns (counts/deltas/hashes) pass.
- [ ] **Step 2: FAIL. Step 3: Implement.** **Step 4: PASS. Step 5: Commit.**

---

### Task 7: snapshot_tcc bridge (CRITICAL - C2)

**Files:** Create `access_harness/snapshot_tcc.py`; Test `tests/test_snapshot_tcc.py` (integration, skip-guarded on mesh)

**Interfaces:** Produces `snapshot_tcc(pg_local, host_dsn, tables) -> snapshot_id` (connect host read-only as `tcc_breaker_ro`, copy key-sets/counts into `tcc_snapshot.*`, record `access_meta.tcc_snapshot` provenance: host, db, captured_at, per-table counts).

- [ ] **Step 1: Failing tests** - the local `tcc_snapshot.tmt_frames` is populated from the host and `tcc_snapshot` provenance row carries host/db/captured_at/counts; assert the host connection is opened READ-ONLY (role `tcc_breaker_ro`). Skip if `ACCESS_HARNESS_TCC_HOST_DSN` unset.
- [ ] **Step 2: FAIL. Step 3: Implement** (host conn from env; `default_transaction_read_only`; psycopg COPY into local). **Step 4: PASS. Step 5: Commit.**

---

### Task 8: projection_map + the FORBIDDEN-key guard (CRITICAL - C3 + operator red-team)

**Files:** Create `access_harness/projection.py`; Test `tests/test_projection.py`

**Interfaces:** Produces `ProjectionMap` (per Access table: tcc table, column map, the resolution chain, key list, `tcc_build_kind`); `resolve_frame_join(pm) -> JoinPlan` (style-mediated chain); `assert_key_allowed(pm, access_col, tcc_col)` -> raises `ForbiddenKeyError` for any direct `Breaker_TMTFrameSizes.ID <-> tmt_frames.id` pairing.

- [ ] **Step 1: Write the RED-TEAM test** (operator requirement):
```python
def test_direct_surrogate_id_frame_join_is_forbidden():
    pm = ProjectionMap.for_table('Breaker_TMTFrameSizes')
    with pytest.raises(ForbiddenKeyError):
        assert_key_allowed(pm, 'Breaker_TMTFrameSizes.ID', 'tmt_frames.id')

def test_style_mediated_chain_is_the_sanctioned_path():
    plan = resolve_frame_join(ProjectionMap.for_table('Breaker_TMTFrameSizes'))
    assert plan.chain == ['StyleID', 'brk_styles.source_id', 'brk_styles.id', 'tmt_frames.breaker_style_id']

def test_real_tcc_column_names(pm):
    assert pm.for_table('Breaker_TMTFrameAmps').col_map['TripAmp'] == 'rating'  # not 'TripAmp'
```
- [ ] **Step 2: FAIL. Step 3: Implement** the projection map (real names from the spec) + the forbidden-key set (any `*.ID -> tmt_frames.id` frame pairing). **Step 4: PASS. Step 5: Commit.**

---

### Task 9: validate - reconciliation + style-mediated anti-join

**Files:** Create `access_harness/validate.py`; Test `tests/test_validate.py`

**Interfaces:** Produces `reconcile_counts/checksums(pg, run_id)`; `key_quality(pg, conn_access, table)` (uniqueness gate); `antijoin_vs_tcc(pg, run_id, snapshot_id, pm)` -> rows into `access_validation` (set-diff if key unique; multiset if not; count/shape only when `tcc_build_kind in ('computed','derived')`).

- [ ] **Step 1: Failing tests** (unit, synthetic access_raw + tcc_snapshot in test schemas): amps `(frame-resolved, rating)` unique -> set-diff enumerates missing keys; curves (`tcc_build_kind='computed'`) -> a count/shape row with `row_antijoin_not_applicable`, NO 1.14M-row EXCEPT; a non-unique key -> multiset path; `key_quality` records `has_usable_unique_key=false` for curves.
- [ ] **Step 2: FAIL. Step 3: Implement.** **Step 4: PASS. Step 5: Commit.**

---

### Task 10: golden capture (HR2 fail-closed)

**Files:** Create `access_harness/golden.py`; Test `tests/test_golden.py`

**Interfaces:** Produces `statement_is_single_select(sql) -> bool`; `golden_exec_guard(query, allowlist) -> bool` (the 5-factor gate); `capture_golden(conn_access, query) -> result snapshot`.

- [ ] **Step 1: Write the fail-closed tests** - the statement guard REJECTS `UPDATE`/`DELETE`/`INSERT`/`SELECT ... INTO`/`MAKE TABLE`/ multi-statement/ parameterized; a name NOT in the allowlist is rejected even if it is a clean SELECT; a clean allow-listed parameterless SELECT passes and captures rows; an allow-listed name whose ACE type != SELECT is rejected.
- [ ] **Step 2: FAIL. Step 3: Implement** (parse first keyword + reject `INTO`/`;`/params; require ACE type==SELECT + param count 0 + allowlist). **Step 4: PASS. Step 5: Commit.**

---

### Task 11: CLI + first-slice acceptance integration (F-79-03)

**Files:** Create `access_harness/cli.py`, `README.md`; Test `tests/test_acceptance_f79_03.py` (integration, skip-guarded)

**Interfaces:** `cli` subcommands `freeze|extract|load|inventory|snapshot-tcc|validate|golden-capture|run-all`.

- [ ] **Step 1: Write the acceptance test** (skip if frozen file / mesh absent) - `run-all` for the breaker/TMT slice + 3 style parents; assert: `access_raw` mirrors loaded with checksum recorded; `antijoin_vs_tcc` ENUMERATES specific missing resolved frames/child rows (NOT a net count - assert the enumerated set is non-empty AND its size reconciles to -169/-246/-58); curves/thermal_adj are count-only (`row_antijoin_not_applicable`); the red-team `ForbiddenKeyError` path is exercised; a driver-capability preflight asserted. NO verdict columns anywhere (run `assert_no_interpretive_columns`).
- [ ] **Step 2: FAIL. Step 3: Implement** the CLI wiring + README runbook. **Step 4: PASS** (against the real frozen file + mesh). **Step 5: Commit.**

---

## Self-Review

- **Spec coverage:** access_raw/meta/validation/tcc_snapshot (T0); freeze (T4); corrected metadata path C1 (T3); cross-instance bridge C2 (T7); style-mediated key C3 + red-team (T8); full-row checksum + multiset C4 (T2,T9); HR2 gate C5 (T10); HR1 guards (T6); run_id/idempotency/single-writer/partial-failure (T0,T5); projection_map real names I2 (T8); lineage operator-authored I3 (T0 enum + T9 gating); enumerated-keys acceptance I11 (T11). All Rev-2 criticals + importants mapped.
- **Decisions honored:** golden diff deferred (T10 capture-only); `_phase2` drop NOT in this plan (separate gated cleanup - explicitly out of scope here); retain-all + latest view (T0); no `source_id` on governed tcc (T8 resolves by style+attrs).
- **Type consistency:** `ColumnType` (T1) consumed by typemap/load/checksum; `run_id` threaded from `extraction_run` (T0/T4) through all writes; `ProjectionMap` (T8) consumed by validate (T9) + acceptance (T11).
- **Out of scope (Phase 2 / later):** golden DIFF, `tcc.*` functional rebuild, `public.Dat*` retirement (gated cleanup task), the other 59 tables' DATA load (inventory-only in Phase 1).

## Execution Handoff

Plan complete. Recommended: **Subagent-Driven Development** (fresh implementer + reviewer per task, on THIS Windows machine since the `.accdb` + local PG are local). Tasks 2/3/8/10 are the high-judgment ones (checksum determinism, the broken-method avoidance, the forbidden-key guard, the HR2 gate) - dispatch those on the strongest model; T1/T4/T5 are mechanical.
