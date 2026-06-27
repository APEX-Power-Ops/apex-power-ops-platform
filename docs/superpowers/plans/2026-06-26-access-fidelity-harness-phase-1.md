# Access Fidelity Harness - Phase 1 Implementation Plan (Rev 2.1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable harness that mirrors `D:\TCC_NEW.accdb` into local Postgres `tcc_fidelity_staging` under `access_raw` / `access_meta` / `access_validation` schemas, preserving structure + provenance and validating fidelity, with ZERO behavioral interpretation. **Phase 1 INVENTORIES all 79 tables into `access_meta`, but DATA-MIRRORS only the breaker/TMT slice (5 TMT tables + 3 style parents) into `access_raw`; the other ~59 tables are inventory-only (`load_state='inventoried_only'`) - their data load is a later phase, NOT this build.** First acceptance slice = F-79-03 evidence (breaker/TMT).

**Architecture:** Python (uv) extraction (`pyodbc` data + `pywin32` ACE OLE DB metadata) -> local PG. Three schemas + a `tcc_snapshot` bridge schema. Anti-joins run LOCAL-to-local after pulling tcc key-sets read-only over the mesh. All metadata from `cursor.description`/`cursor.statistics()`/ACE `adSchema*` (the broken `cursor.columns/primaryKeys/foreignKeys` are forbidden by design).

**Tech Stack:** Python 3.12, uv, pyodbc, pywin32, psycopg[binary], pytest. Local PG18 (127.0.0.1:5432). **Build + tests run on THIS Windows machine** (the `.accdb` + local PG live here), NOT the Olares host.

**Spec:** `docs/superpowers/specs/2026-06-26-access-fidelity-harness-phase-1-design.md` @ Rev 2 (`4f248aa3`).

## Global Constraints

- **HR1 - no behavioral interpretation.** `access_validation.*` columns restricted to a permitted shape allow-list (counts, deltas, hashes, key-tuples, set-membership, load-process states). A test denylist REJECTS interpretive column names (`status`/`expected`/`correct`/`category`/`verdict`/`is_gap`). The single canonical load-process column is **`access_meta.tables.load_state`** = closed enum `{inventoried_only, extracting, loaded, checksummed, failed}` (there is NO `status` column anywhere). `tcc_build_kind` is operator-authored data the harness JOINs to (`{1:1_load, computed, derived, none}`), NEVER computed by the harness. No "apples-to-oranges"/"gap"/"correct" language in any `access_validation` row.
- **HR2 - goldens opt-in + fail-closed.** A saved query executes for a golden ONLY if: (a) name in `golden_allowlist` AND (b) type==`SELECT` verified from the ACE rowset AND (c) verified param count==0 AND (d) the **passed-in connection is verified read-only** AND (e) a statement guard accepts only a single `SELECT` (one optional trailing `;` tolerated; any additional statement rejected). `is_parameterless`/`golden_eligible` are advisory hints, never the gate. Golden DIFF deferred to Phase 2; Phase 1 CAPTURES the Access-side result set only.
- **Forbidden extraction methods (by design, enforced by test):** `cursor.columns()`, `cursor.primaryKeys()`, `cursor.foreignKeys()`. A monkeypatch/source-scan test FAILS if any harness module calls them (not merely "the driver crashes" - the ban is permanent even if a future driver stops crashing). Use `cursor.description` (columns), `cursor.statistics()` (PK/unique indexes), ACE `adSchemaColumns/Indexes/ForeignKeys/Procedures/Views`.
- **Forbidden anti-join keys (red-team, enforced by test):** ANY direct Access-surrogate -> `tcc.tmt_frames.id` pairing is forbidden, including the frame `Breaker_TMTFrameSizes.ID` AND every child `*.FrameSizeID` (`Breaker_TMTFrameAmps/Settings/Curves/ThermalTripAdj`). tcc frame ids are resequenced; only the style-mediated chain is sanctioned: Access `StyleID` -> `brk_{class}_styles.source_id` -> `brk_{class}_styles.id` -> `tmt_frames.breaker_style_id`, then natural attributes within the resolved frame. Key-uniqueness hard gate: set-diff if unique, multiset (per-key COUNT) if not. `computed`/`derived` tables (curves/thermal_adj) = count/shape only.
- **Test isolation (hard fence):** destructive schema tests (which CREATE/DROP `access_raw`/`access_meta`/`access_validation`/`tcc_snapshot`) run ONLY against a SEPARATE `tcc_fidelity_test` database, hard-guarded by `current_database() = 'tcc_fidelity_test'` (raise/skip otherwise). NEVER against the real `tcc_fidelity_staging` (which holds the live `public.Dat*` staging).
- **Freeze (mandatory):** copy to `D:\_access_frozen\TCC_NEW_<mtime>_<sha8>.accdb` (create dir; skip-copy if target sha exists); record sha256/size/mtime/source_path/frozen_copy_path/extracted_at/driver_name(`SQL_DRIVER_NAME`)/dbms_version(`SQL_DBMS_VER`)/read_only in `extraction_run`. Extract from the FROZEN copy read-only (`ReadOnly=1`).
- **Idempotency:** every `access_meta.*`/`access_validation.*` row carries `run_id` (FK -> `extraction_run`); per-table TRUNCATE+reload of `access_raw` in a txn; single-writer advisory lock; retain ALL runs + a `latest` view.
- **Real tcc names:** `tmt_frames(id surrogate, breaker_style_id, size)`, `tmt_amps(frame_id, rating)`, `tmt_settings(frame_id,...)`, `tmt_curves(frame_id, class, time_sec, current_amp)`, `tmt_thermal_adj(id, frame_id, adjustment)`, `brk_{mccb,iccb,pcb}_styles(id, source_id, breaker_id, frame, standard)`. `tmt_curves`+`tmt_thermal_adj` are `computed`/`derived`.
- **Decisions (operator-ratified):** golden diff deferred to Phase 2 / capture-only (D1); `_phase2` `public.Dat*` drop is a SEPARATE gated cleanup task, NOT in this build (D2); retain-all-runs + latest view (D3); NO `source_id` added to governed `tcc.tmt_frames` (D4 - frames resolved by style+attributes only).
- ASCII-only in all files. Commit identity `jasonlswenson-sys <jasonlswenson@gmail.com>`. Merge operator-gated.

## File Structure

`infra/database/access-harness/`: `pyproject.toml` (pyodbc, pywin32, psycopg[binary], pytest); `access_harness/{__init__,config,freeze,typemap,extract,load,inventory,checksum,snapshot_tcc,projection,validate,golden,hr1_guard,cli}.py`; `sql/001_schemas.sql`; `tests/` (unit synthetic + integration frozen-`.accdb`/mesh skip-guarded); `README.md`.

---

### Task 0: Scaffold + schemas + test-DB fence + PG provisioning

**Files:** Create `pyproject.toml`, `access_harness/{__init__,config}.py`, `sql/001_schemas.sql`; Test `tests/conftest.py`, `tests/test_schema_apply.py`

**Interfaces:** Produces `config.pg_dsn()` (local harness DSN, from env `ACCESS_HARNESS_PG_DSN`), `config.test_pg_dsn()` (points at `tcc_fidelity_test`), `config.frozen_dir()`, `config.apply_sql(conn, path)`; pytest fixture `pg` (connection to `tcc_fidelity_test`).

- [ ] **Step 1: Confirm the working local PG credential** for `tcc_fidelity_staging` (the `tcc-fidelity-staging` MCP connects; `apex_pm_stage_user` is superuser; `postgres` pw reportedly lost). Put the DSN in env `ACCESS_HARNESS_PG_DSN`; **create a separate empty `tcc_fidelity_test` database** for tests (env `ACCESS_HARNESS_TEST_PG_DSN`). Document both in README. No passwords in code.
- [ ] **Step 2: Write `sql/001_schemas.sql`** - 4 schemas + the fixed tables (full DDL): `extraction_run(run_id PK, source_path, frozen_copy_path, source_size, source_mtime_utc, source_sha256, extracted_at_utc, driver_name, dbms_version, read_only, harness_version)`; `tables(run_id, table_name, object_type, load_state text CHECK (load_state IN ('inventoried_only','extracting','loaded','checksummed','failed')), access_row_count, staging_row_count, checksum, has_usable_unique_key, tcc_build_kind text CHECK (tcc_build_kind IN ('1:1_load','computed','derived','none')), started_at, completed_at, PRIMARY KEY(run_id, table_name))`; `columns`, `primary_keys`, `indexes`, `relationships`, `queries`, `golden_allowlist`, `projection_map`, `tcc_snapshot`; the `access_validation.*` tables (`row_count_reconciliation`, `checksum_reconciliation`, `type_drift`, `key_quality`, `antijoin_vs_tcc`, `golden_capture`) - each with `run_id`. `latest_*` views (most-recent `run_id`).
- [ ] **Step 3: Write failing test** `test_schemas_and_core_tables_exist` - applies DDL to `tcc_fidelity_test`, asserts the 4 schemas + `extraction_run` + `antijoin_vs_tcc` exist.
- [ ] **Step 4: Run - FAIL.**
- [ ] **Step 5: Implement** `config.py` + `conftest.py` `pg` fixture with the **hard fence**: the fixture asserts `current_database() == 'tcc_fidelity_test'` before applying/dropping DDL (raise otherwise); never touches `tcc_fidelity_staging`. Re-run - PASS.
- [ ] **Step 6: Commit.**

---

### Task 1: Type mapping (pure logic)

**Files:** Create `access_harness/typemap.py`; Test `tests/test_typemap.py`
**Interfaces:** `map_description(desc_row) -> ColumnType`; `pg_ddl_type(ct) -> str`; `ColumnType{access_type, pg_type, nullable, size, precision, round_trippable}`.

- [ ] **Step 1: Failing tests** - `int`->`integer`, `float`->`double precision`, `str`->`text`, currency `decimal`->`numeric(19,4)`, `datetime`->`timestamp`, `bool`->`boolean`, `bytearray`->`bytea`, unknown->`text` with `round_trippable=False`:
```python
def test_float_maps_to_double_precision():
    ct = map_description(('Sec2InstClrTime', float, 0, 8, 53, 0, True))
    assert ct.pg_type == 'double precision' and ct.round_trippable is True
def test_unknown_type_falls_back_to_text():
    ct = map_description(('Weird', object, 0, 0, 0, 0, True))
    assert ct.pg_type == 'text' and ct.round_trippable is False
```
- [ ] **Step 2: FAIL. Step 3: Implement** (dict on pyodbc `description` type-codes + fallback; NO `cursor.columns`). **Step 4: PASS. Step 5: Commit.**

---

### Task 2: Full-row checksum + multiset diff (pure logic; CRITICAL - C4)

**Files:** Create `access_harness/checksum.py`; Test `tests/test_checksum.py`
**Interfaces:** `canonical_row(row, col_types) -> str` (NULL sentinel `\x00NULL`, floats -> `format(x,'.17g')`, fixed col order); `table_checksum(rows, col_types) -> str` (sha256 over rows sorted by `canonical_row`); `multiset_diff(left: Counter, right: Counter) -> dict`.

- [ ] **Step 1: Failing tests** (determinism is critical):
```python
def test_checksum_is_order_independent():
    assert table_checksum([(1,1.5),(2,2.5)], T) == table_checksum([(2,2.5),(1,1.5)], T)
def test_checksum_float_round_trip_byte_identical():
    assert canonical_row((0.1+0.2,), [FT]) == canonical_row((0.30000000000000004,), [FT])
def test_null_vs_empty_string_distinct():
    assert canonical_row((None,), [ST]) != canonical_row(('',), [ST])
def test_multiset_diff_per_key_counts():
    from collections import Counter
    assert multiset_diff(Counter({'k':3}), Counter({'k':1})) == {'k': {'access':3,'tcc':1,'delta':2}}
```
- [ ] **Step 2: FAIL. Step 3: Implement.** **Step 4: PASS. Step 5: Commit.**

---

### Task 3: Metadata + data extraction (Access-touching; CRITICAL - C1) + forbidden-method enforcement (O4)

**Files:** Create `access_harness/extract.py`; Test `tests/test_extract_integration.py` (skip-guarded), `tests/test_forbidden_methods.py`
**Interfaces:** `connect_data(frozen_path)` (`ReadOnly=1`); `list_user_tables(conn)` (ACE `adSchemaTables`, `TABLE_TYPE='TABLE'`); `column_meta(conn, table)` (probe `SELECT * WHERE 1=0` + `cursor.description`, `errors='surrogatepass'`); `primary_key(conn, table)` (`cursor.statistics()` PrimaryKey index); `foreign_keys/indexes(conn_ace, table)` + `saved_queries(conn_ace)` (ACE OpenSchema; `adSchemaProcedures` UNION `adSchemaViews` = 33); `driver_info(conn)` (`SQL_DRIVER_NAME`,`SQL_DBMS_VER`); `read_rows(conn, table)`.

- [ ] **Step 1a: Write the DESIGN-ENFORCEMENT test** (`test_forbidden_methods.py`, runs everywhere, no driver needed) - the load-bearing O4 test:
```python
def test_harness_never_calls_forbidden_catalog_methods(monkeypatch):
    import pyodbc
    for m in ('columns', 'primaryKeys', 'foreignKeys'):
        def boom(*a, _m=m, **k): raise AssertionError(f'forbidden cursor.{_m}() called')
        monkeypatch.setattr(pyodbc.Cursor, m, boom, raising=False)
    # exercise the metadata path against a fixture/probe; must NOT trip the boom
    # (plus a static scan: assert 'cursor.columns(' etc. absent from access_harness/*.py source)
```
- [ ] **Step 1b: Write the integration tests** (`test_extract_integration.py`, skip if frozen file/driver absent; the freeze in Task 4 supplies it - for this task point at a pre-frozen copy):
```python
def test_cursor_columns_known_broken_on_this_driver(conn):  # documents the driver fact
    with pytest.raises(Exception): conn.cursor().columns(table='Breaker_TMTFrameSizes').fetchall()
def test_column_meta_returns_26(conn): assert len(column_meta(conn,'Breaker_TMTFrameSizes')) == 26
def test_primary_key_is_composite(conn): assert primary_key(conn,'Breaker_TMTFrameSizes') == ['StyleID','FrameDesc']
def test_list_user_tables_is_79(conn): assert len(list_user_tables(conn)) == 79
def test_saved_queries_total_33(conn_ace): assert len(saved_queries(conn_ace)) == 33
```
- [ ] **Step 2: FAIL.** **Step 3: Implement** with ONLY allowed methods + `pywin32` ADODB `OpenSchema`; record per-kind `coverage_source`. **Step 4: PASS** (enforcement everywhere; integration against the real file). **Step 5: Commit.**

---

### Task 4: Freeze + extraction_run (Access-touching)

**Files:** Create `access_harness/freeze.py`; Test `tests/test_freeze.py`
**Interfaces:** `freeze(source, dest_dir) -> FrozenSource`; `record_extraction_run(pg, frozen, driver_info) -> run_id`.

- [ ] **Step 1: Failing tests** - sha determinism; skip-copy on identical sha; `extraction_run` carries all provenance incl. `driver_name`/`dbms_version` (use a tiny temp binary for pure logic; real `.accdb` exercised in Task 11).
- [ ] **Step 2: FAIL. Step 3: Implement** (`shutil.copy2`, streamed `hashlib.sha256`, dir create, `<mtime>_<sha8>` name). **Step 4: PASS. Step 5: Commit.**

---

### Task 5: access_raw load (TRUNCATE/reload + load_state + single-writer)

**Files:** Create `access_harness/load.py`; Test `tests/test_load.py`
**Interfaces:** `create_access_raw_table(pg, table, col_types)`; `load_table(pg, row_source, table, run_id, continue_on_error=False) -> int`; `single_writer(pg)` context (advisory lock).

- [ ] **Step 1: Failing tests** (unit, synthetic): double `load_table` -> same count (idempotent, not doubled); a failing row source sets `load_state='failed'`, no partial commit; `single_writer` blocks a 2nd concurrent acquire.
- [ ] **Step 2: FAIL. Step 3: Implement** (DDL via `typemap.pg_ddl_type`; `pg_advisory_xact_lock`; per-table txn; `load_state` transitions). **Step 4: PASS. Step 5: Commit.**

---

### Task 6: Inventory population + HR1 guard

**Files:** Create `access_harness/inventory.py`, `access_harness/hr1_guard.py`; Test `tests/test_inventory.py`, `tests/test_hr1_guard.py`
**Interfaces:** `populate_meta(pg, conn_access, run_id, tables)` (all `access_meta.*` with `run_id`; unloaded tables get `load_state='inventoried_only'`); `assert_no_interpretive_columns(pg)` -> violations.

- [ ] **Step 1: Failing tests** - `primary_keys` row `(StyleID, FrameDesc)` for frames; `columns` count 26; the ~59 non-slice tables recorded `inventoried_only`; **HR1 guard**: a column named `is_gap`/`correct`/`verdict` injected into an `access_validation` table is DETECTED (guard fails); legitimate count/delta/hash columns pass.
- [ ] **Step 2: FAIL. Step 3: Implement.** **Step 4: PASS. Step 5: Commit.**

---

### Task 7: snapshot_tcc bridge (CRITICAL - C2)

**Files:** Create `access_harness/snapshot_tcc.py`; Test `tests/test_snapshot_tcc.py` (integration, skip if mesh DSN unset)
**Interfaces:** `snapshot_tcc(pg_local, host_dsn, tables) -> snapshot_id` (host read-only as `tcc_breaker_ro`, copy key-sets/counts into `tcc_snapshot.*`, record `tcc_snapshot` provenance).

- [ ] **Step 1: Failing tests** - `tcc_snapshot.tmt_frames` populated from host; provenance row carries host/db/captured_at/counts; the host connection is opened READ-ONLY. Skip if `ACCESS_HARNESS_TCC_HOST_DSN` unset.
- [ ] **Step 2: FAIL. Step 3: Implement** (`default_transaction_read_only`; psycopg COPY host->local). **Step 4: PASS. Step 5: Commit.**

---

### Task 8: projection_map + FORBIDDEN-key guard (CRITICAL - C3 + operator/Codex red-team)

**Files:** Create `access_harness/projection.py`; Test `tests/test_projection.py`
**Interfaces:** `ProjectionMap.for_table(name)` (tcc table, column map, resolution chain, key list, `tcc_build_kind`); `resolve_frame_join(pm, breaker_class) -> JoinPlan` (class-specific style chain); `assert_key_allowed(pm, access_col, tcc_col)` -> raises `ForbiddenKeyError` for ANY Access-surrogate -> `tmt_frames.id` pairing (frame `ID` OR child `FrameSizeID`).

- [ ] **Step 1: Write the RED-TEAM tests** (operator + Codex P1):
```python
def test_direct_frame_surrogate_id_forbidden():
    with pytest.raises(ForbiddenKeyError):
        assert_key_allowed(ProjectionMap.for_table('Breaker_TMTFrameSizes'), 'Breaker_TMTFrameSizes.ID', 'tmt_frames.id')
def test_direct_child_framesizeid_also_forbidden():   # Codex P1
    for t in ('Breaker_TMTFrameAmps','Breaker_TMTFrameSettings','Breaker_TMTFrameCurves','Breaker_TMTThermalTripAdj'):
        with pytest.raises(ForbiddenKeyError):
            assert_key_allowed(ProjectionMap.for_table(t), f'{t}.FrameSizeID', 'tmt_frames.id')
def test_style_mediated_chain_is_class_specific():    # Codex P2
    plan = resolve_frame_join(ProjectionMap.for_table('Breaker_TMTFrameSizes'), 'MCCB')
    assert plan.chain == ['StyleID','brk_mccb_styles.source_id','brk_mccb_styles.id','tmt_frames.breaker_style_id']
def test_real_tcc_column_names():
    assert ProjectionMap.for_table('Breaker_TMTFrameAmps').col_map['TripAmp'] == 'rating'
```
- [ ] **Step 2: FAIL. Step 3: Implement** the projection map (real names) + the forbidden-key set (any `*.ID`/`*.FrameSizeID -> tmt_frames.id`) + class-specific chains for MCCB/ICCB/PCB. **Step 4: PASS. Step 5: Commit.**

---

### Task 9: validate - reconciliation + style-mediated anti-join (synthetic exact-delta tests; O3)

**Files:** Create `access_harness/validate.py`; Test `tests/test_validate.py`
**Interfaces:** `reconcile_counts/checksums(pg, run_id)`; `key_quality(pg, conn_access, table)`; `antijoin_vs_tcc(pg, run_id, snapshot_id, pm)` -> `access_validation` rows (set-diff if unique; multiset if not; count/shape only when `tcc_build_kind in ('computed','derived')`).

- [ ] **Step 1: Failing tests** (unit, **synthetic access_raw + tcc_snapshot fixtures in `tcc_fidelity_test`** with KNOWN, PINNED contents so EXACT deltas are asserted deterministically): an amps fixture missing 2 known `(resolved_frame, rating)` rows -> the anti-join ENUMERATES exactly those 2 keys (assert the exact set, not a count); a `computed` curves fixture -> a count/shape row with `row_antijoin_not_applicable`, NO row EXCEPT; a non-unique key fixture -> multiset path; `key_quality` records `has_usable_unique_key=false` for the non-unique fixture.
- [ ] **Step 2: FAIL. Step 3: Implement.** **Step 4: PASS. Step 5: Commit.**

---

### Task 10: golden capture (HR2 fail-closed; CRITICAL - C5 + Codex P2 x2)

**Files:** Create `access_harness/golden.py`; Test `tests/test_golden.py`
**Interfaces:** `statement_is_single_select(sql) -> bool` (tolerates ONE optional trailing `;`, rejects additional statements); `golden_exec_guard(query, allowlist, conn_access) -> bool` (5-factor incl. **verifying `conn_access` is read-only**); `capture_golden(conn_access, query)`.

- [ ] **Step 1: Write the fail-closed tests** (incl. Codex P2 fixes):
```python
def test_guard_rejects_action_and_multistatement():
    for sql in ('UPDATE t SET x=1','DELETE FROM t','SELECT * INTO u FROM t','SELECT 1; DROP TABLE t'):
        assert statement_is_single_select(sql) is False
def test_guard_tolerates_one_trailing_semicolon():   # Codex P2
    assert statement_is_single_select('SELECT a, b FROM MyQuery;') is True
def test_name_not_in_allowlist_rejected_even_if_clean_select(ro_conn):
    assert golden_exec_guard(Query('NotListed','SELECT 1',type='SELECT',params=0), allowlist={'OK'}, conn_access=ro_conn) is False
def test_writable_connection_rejected(rw_conn):       # Codex P2 read-only factor
    assert golden_exec_guard(Query('OK','SELECT 1',type='SELECT',params=0), allowlist={'OK'}, conn_access=rw_conn) is False
def test_clean_allowlisted_parameterless_select_passes(ro_conn):
    assert golden_exec_guard(Query('OK','SELECT 1',type='SELECT',params=0), allowlist={'OK'}, conn_access=ro_conn) is True
```
- [ ] **Step 2: FAIL. Step 3: Implement** (first-keyword + reject `INTO`/extra `;`/params; require ACE type==SELECT + 0 params + allowlist + `conn_access` read-only verified). **Step 4: PASS. Step 5: Commit.**

---

### Task 11: CLI + first-slice acceptance (F-79-03; O3 internal-consistency, not pinned numbers)

**Files:** Create `access_harness/cli.py`, `README.md`; Test `tests/test_acceptance_f79_03.py` (integration, skip-guarded on frozen file + mesh)
**Interfaces:** `cli` subcommands `freeze|extract|load|inventory|snapshot-tcc|validate|golden-capture|run-all`.

- [ ] **Step 1: Write the acceptance test** (skip-with-reason if frozen file/mesh absent - never silent no-op): `run-all` the breaker/TMT slice + 3 style parents; assert - (a) `access_raw` mirrors loaded with a recorded checksum; (b) the anti-join report **ENUMERATES a non-empty set of specific resolved missing frames/child rows** and is INTERNALLY CONSISTENT (the enumerated row count equals the reported delta for that table) - **NOT** a hard-coded `-169/-246/-58` (those live only as the EXACT-delta assertions in Task 9's pinned synthetic fixtures; live acceptance RECORDS the actual counts + the pinned `tcc_snapshot_id` into the report); (c) curves/thermal_adj are count-only (`row_antijoin_not_applicable`); (d) the `ForbiddenKeyError` path is exercised; (e) `assert_no_interpretive_columns` passes (no verdict columns); (f) a driver-capability preflight asserted.
- [ ] **Step 2: FAIL. Step 3: Implement** CLI + README runbook. **Step 4: PASS** (real frozen file + mesh). **Step 5: Commit.**

---

## Self-Review

- **Spec coverage:** schemas/run_id/idempotency/test-fence (T0); typemap (T1); checksum C4 (T2); corrected metadata C1 + forbidden-method enforcement O4 (T3); freeze (T4); load+load_state (T5); inventory+HR1+inventoried_only-for-59 O1 (T6); snapshot bridge C2 (T7); projection + frame+child forbidden-key C3/CX1 + class-specific CX2 (T8); anti-join + synthetic exact-delta O3 (T9); HR2 read-only+semicolon C5/CX3/CX4 (T10); acceptance internal-consistency O3 (T11).
- **Decisions honored:** golden diff deferred (T10); `_phase2` drop NOT in this plan (out of scope); retain-all+latest (T0); no governed-`tcc` change (T8). Scope: inventory-all-79 / data-load-TMT-only stated in Goal + T6.
- **Naming:** `load_state` is the single canonical column (no `status`) throughout.
- **Type consistency:** `ColumnType` (T1) -> typemap/load/checksum; `run_id` (T0/T4) -> all writes; `ProjectionMap`/`ForbiddenKeyError` (T8) -> validate (T9) + acceptance (T11); `golden_exec_guard(query, allowlist, conn_access)` signature consistent T10.

## Rev 2.1 changelog (review fixes)
Operator: O1 inventory-79/load-TMT scope; O2 `tcc_fidelity_test` hard fence; O3 exact-deltas synthetic / live = internal-consistency+recorded-counts; O4 forbidden-method enforcement test; O5 `load_state` single name. Codex (`review-e1aa45be`): CX1 child `FrameSizeID` also forbidden; CX2 class-specific `brk_{class}_styles` chain; CX3 read-only conn in golden guard; CX4 tolerate one trailing `;`.

## Execution Handoff
Recommended: **Subagent-Driven Development on THIS Windows machine** (the `.accdb` + local PG live here; Access/PG-touching tasks T3/T4/T7/T9/T11 cannot run on the Olares host). High-judgment: T2/T3/T8/T10 (strongest model); mechanical: T1/T4/T5. Pre-flight: verify the working tree is on `tcc/access-fidelity-harness @ <Rev2.1 tip>` and a `tcc_fidelity_test` DB exists before Task 0.
