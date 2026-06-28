# D4/D5 Governed Generation (Phase 2 / D-C) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A generator that reads breaker style D4/D5 from the governed `access_raw`
(`tcc_fidelity_governed`), runs six fail-closed pre-emit gates, and emits provenance-stamped,
row-level-guarded `029_d4_data.sql` + `030_d5_data.sql` (+ `generation_report.json`) -- replacing the
Path-B direct-Access dry-run generator. Build-only; NO prod apply.

**Architecture:** A new module in the access-harness package (for harness config/fence + psycopg +
pytest reuse) that is a downstream CONSUMER of the governed mirror. It carries raw D4/D5 verbatim
(policy (a); no behavioral interpretation -- HR1 spirit preserved). The transform is copied verbatim
from the Codex-converged dry-run generator; only the source (governed access_raw), the provenance
header, the six gates, and the temp-stage row-level apply pattern are new. Generated SQL artifacts land
in the breaker-sandbox dir.

**Tech Stack:** Python 3.12 / uv / psycopg 3 (existing harness deps -- NO new deps). Postgres
`tcc_fidelity_governed` (read) + `tcc_fidelity_test` (TDD target) + a host clone off
`tcc_breaker_baseline_20260625` (live dry-run, controller-run).

## Global Constraints
- ASCII-only in AUTHORED SQL / comments / copy (no em-dashes or smart quotes; use `--` and `->`).
  NOTE (Rev 2.1, cross-engine review): VERBATIM SOURCE DATA literals carried from Access (e.g. TMT_Notes
  may contain (c)/(r)/degree/+- and smart quotes) are NOT subject to this -- they are emitted verbatim as
  UTF-8 (the generator sets `client_encoding='UTF8'`). Escaping or stripping source data would be a
  source-fidelity violation; the prod tcc DB is UTF-8.
- Commit identity `jasonlswenson-sys <jasonlswenson@gmail.com>`; every commit ends with
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- NO new dependencies. NO prod apply of 029/030 in this slice (build + dry-run + review only).
- TDD on `tcc_fidelity_test`; the normal suite must NEVER touch `tcc_fidelity_governed` (read-only,
  live-acceptance only, skip without DSN).
- Single writer = the Windows worktree `C:\dev\apex-access-harness`; do NOT push/merge from subagents.
- The transform (D4 6-col map, D5 5-block map, policy (a) real-override metric `InstOvrAmps > 0` as a
  REPORT metric only -- never a filter) is copied VERBATIM from
  `infra/database/sandbox/breaker/d4d5-population-dryrun/dry_run_direct_access_population_generator.py`.
- The exact per-class column manifest is Appendix A of the spec
  (`docs/superpowers/specs/2026-06-27-d4d5-governed-generation-design.md`), pinned from live
  `access_raw`.

## File Structure
- Create: `infra/database/access-harness/access_harness/d4d5_governed_generation.py`
  -- the manifest constant, the six gates (`GenerationRefused`), the reader+transform, the SQL emitter.
- Modify: `infra/database/access-harness/access_harness/cli.py`
  -- add a `generate-d4d5` subcommand (fenced; routes the governed DSN; `--run-id` optional; `--out-dir`).
- Create: `infra/database/access-harness/tests/test_d4d5_governed_generation.py`
  -- gate unit tests (TDD on `tcc_fidelity_test`), emit-shape tests, and the live governed-vs-direct
  parity regression (skips without DSN/Access).
- Output (generated; committed AFTER the dry-run validates): under
  `infra/database/sandbox/breaker/d4d5-governed-generation/` -- `029_d4_data.sql`, `030_d5_data.sql`,
  `generation_report.json`, `README.md`.

---

### Task 1: Manifest + the six fail-closed pre-emit gates

**Files:**
- Create: `infra/database/access-harness/access_harness/d4d5_governed_generation.py`
- Test: `infra/database/access-harness/tests/test_d4d5_governed_generation.py`

**Interfaces:**
- Produces: `GenerationRefused(Exception)`; `MANIFEST: dict[str, dict]` (per-class: `access_table`,
  `pg_table`, `has_d4`, `d4_cols`, `d5_block_cols`, `required_cols`); `select_run_id(conn, requested) ->
  str`; `assert_governed_source(conn)`; `assert_style_evidence(conn, run_id)` (runs the
  materialized_owner + reconciliation + key_quality + manifest-column gates for all 3 style tables).

- [ ] **Step 1: Write the failing gate tests**

```python
# tests/test_d4d5_governed_generation.py
import psycopg, pytest
from access_harness import config
from access_harness import d4d5_governed_generation as gen

STYLE_TABLES = ("BreakerICCBStyles", "BreakerMCCBStyles", "BreakerPCBStyles")

def _test_conn():
    dsn = config.test_pg_dsn()
    return psycopg.connect(dsn)

def test_assert_governed_source_refuses_non_governed():
    # tcc_fidelity_test is NOT tcc_fidelity_governed -> must refuse
    with _test_conn() as conn:
        with pytest.raises(gen.GenerationRefused, match="tcc_fidelity_governed"):
            gen.assert_governed_source(conn)

def test_select_run_id_refuses_when_absent(seeded_test_db):
    with _test_conn() as conn:
        with pytest.raises(gen.GenerationRefused, match="run_id"):
            gen.select_run_id(conn, "does-not-exist")

def test_materialized_owner_mismatch_refuses(seeded_test_db):
    # seeded_test_db materializes owner=run B for a style table but we ask for run A
    with _test_conn() as conn:
        with pytest.raises(gen.GenerationRefused, match="materialized_owner"):
            gen.assert_style_evidence(conn, run_id="runA")

def test_reconciliation_false_refuses(seeded_test_db):
    with _test_conn() as conn:
        with pytest.raises(gen.GenerationRefused, match="reconcil"):
            gen.assert_style_evidence(conn, run_id="run_recon_false")

def test_key_quality_not_unique_refuses(seeded_test_db):
    with _test_conn() as conn:
        with pytest.raises(gen.GenerationRefused, match="key_quality|unique"):
            gen.assert_style_evidence(conn, run_id="run_key_dupe")

def test_missing_manifest_column_refuses(seeded_test_db):
    with _test_conn() as conn:
        with pytest.raises(gen.GenerationRefused, match="column"):
            gen.assert_style_evidence(conn, run_id="run_missing_col")

def test_clean_run_passes(seeded_test_db):
    with _test_conn() as conn:
        gen.assert_governed_source  # callable
        gen.assert_style_evidence(conn, run_id="run_clean")  # no raise
```

A `seeded_test_db` fixture creates the minimal `access_meta`/`access_validation`/`access_raw` rows on
`tcc_fidelity_test` for each named scenario (clean, recon_false, key_dupe, missing_col, owner-mismatch).
The fixture creates only the columns the gates read; build it in the test module.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_d4d5_governed_generation.py -k gate -v`
Expected: FAIL (module / functions not defined).

- [ ] **Step 3: Implement the manifest + gates**

```python
# access_harness/d4d5_governed_generation.py
"""D4/D5 governed-generation (Phase 2 / D-C). Reads governed access_raw, emits provenance-stamped,
row-level-guarded 029/030 data SQL. Consumer of the harness; carries raw D4/D5 verbatim (policy a)."""
from access_harness.config import GOVERNED_DB, assert_current_database

class GenerationRefused(Exception):
    """A fail-closed pre-emit gate refused. Generation must not proceed."""

_INST = ["InstOvrAmps","InstOvrMinTolerance","InstOvrMaxTolerance","InstOvrClrDelayTime",
    "InstOvrClrRadius","InstOvrOpnDelayTime","InstOvrOpnRadius","InstOvrNoteText","InstOvrClrCurve",
    "InstOvrClrChar","InstOvrCurveCalcClr","InstOvrClrEnteredAt","InstOvrOpenCurve","InstOvrOpenChar",
    "InstOvrCurveCalcOpen","InstOvrOpenEnteredAt"]
_NINST = ["NInstOvrAmps","NInstOvrMinTolerance","NInstOvrMaxTolerance","NInstOvrClrDelayTime",
    "NInstOvrClrRadius","NInstOvrOpnDelayTime","NInstOvrOpnRadius","NInstOvrClrCurve","NInstOvrClrChar",
    "NInstOvrCurveCalcClr","NInstOvrClrEnteredAt","NInstOvrOpenCurve","NInstOvrOpenChar",
    "NInstOvrCurveCalcOpen","NInstOvrOpenEnteredAt"]
_BRK = ["BrkTimesMechOpening50","BrkTimesMechOpening60","BrkTimesSTDelayBand50","BrkTimesSTDelayBand60"]
_RINT_BASE = ["r_int_inst_240","r_int_inst_480","r_int_inst_600","r_int_series_240","r_int_series_480","r_int_series_600"]
_RINT_PCB  = _RINT_BASE + ["r_int_ninst_240","r_int_ninst_480","r_int_ninst_600"]
_RIEC_BASE = ["r_iec_inst_220","r_iec_inst_230","r_iec_inst_240","r_iec_inst_380","r_iec_inst_400",
    "r_iec_inst_415","r_iec_inst_440","r_iec_inst_500","r_iec_inst_550","r_iec_inst_690","r_iec_inst_1000"]
_RIEC_PCB  = _RIEC_BASE + ["r_iec_ninst_220","r_iec_ninst_230","r_iec_ninst_240","r_iec_ninst_380",
    "r_iec_ninst_400","r_iec_ninst_415","r_iec_ninst_440","r_iec_ninst_500","r_iec_ninst_550",
    "r_iec_ninst_690","r_iec_ninst_1000"]
_D4 = ["TMT_TCCNumber","TMT_Notes","TMT_TripPlug","TMT_BreakerType","TMT_ThermalMagnetic","TMT_Thermal"]

def _blocks(rint, riec):
    return {"inst_override": _INST, "ninst_override": _NINST, "brk_times": _BRK, "r_int": rint, "r_iec": riec}

MANIFEST = {
    "ICCB": {"access_table": "BreakerICCBStyles", "pg_table": "brk_iccb_styles", "has_d4": True,
             "d4_cols": _D4, "d5_block_cols": _blocks(_RINT_BASE, _RIEC_BASE)},
    "MCCB": {"access_table": "BreakerMCCBStyles", "pg_table": "brk_mccb_styles", "has_d4": True,
             "d4_cols": _D4, "d5_block_cols": _blocks(_RINT_BASE, _RIEC_BASE)},
    "PCB":  {"access_table": "BreakerPCBStyles",  "pg_table": "brk_pcb_styles",  "has_d4": False,
             "d4_cols": [], "d5_block_cols": _blocks(_RINT_PCB, _RIEC_PCB)},
}
for _c, _m in MANIFEST.items():
    _req = ["ID", "InstOvrAmps"] + list(_m["d4_cols"])
    for _grp in _m["d5_block_cols"].values():
        _req += _grp
    _m["required_cols"] = sorted(set(_req))

def assert_governed_source(conn):
    """Gate 1: refuse unless connected to tcc_fidelity_governed."""
    try:
        assert_current_database(conn, GOVERNED_DB)
    except RuntimeError as e:
        raise GenerationRefused(str(e))

def select_run_id(conn, requested):
    """Gate 2: explicit run_id if present in extraction_run; else the sole run; refuse if absent/ambiguous."""
    with conn.cursor() as cur:
        if requested:
            cur.execute("SELECT 1 FROM access_meta.extraction_run WHERE run_id=%s", (requested,))
            if cur.fetchone() is None:
                raise GenerationRefused(f"run_id {requested!r} not found in extraction_run")
            return requested
        cur.execute("SELECT run_id FROM access_meta.extraction_run")
        rows = [r[0] for r in cur.fetchall()]
    if len(rows) != 1:
        raise GenerationRefused(f"run_id is ambiguous: {len(rows)} runs in extraction_run; pass --run-id")
    return rows[0]

def assert_style_evidence(conn, run_id):
    """Gates 3-6 for all 3 style tables: materialized_owner == run_id, reconciliation True,
    key_quality unique, manifest columns present. Refuse on any failure."""
    with conn.cursor() as cur:
        for cls, m in MANIFEST.items():
            t = m["access_table"]
            # Gate 3: materialized_owner
            cur.execute("SELECT run_id FROM access_meta.materialized_owner WHERE layer='access_raw' AND table_name=%s", (t,))
            row = cur.fetchone()
            if row is None or row[0] != run_id:
                raise GenerationRefused(f"materialized_owner for {t} is {row and row[0]!r}, expected {run_id!r}")
            # Gate 4: checksum reconciliation
            cur.execute("SELECT matches FROM access_validation.checksum_reconciliation WHERE run_id=%s AND table_name=%s", (run_id, t))
            row = cur.fetchone()
            if row is None or row[0] is not True:
                raise GenerationRefused(f"checksum reconciliation for {t} is not True (got {row and row[0]!r})")
            # Gate 5: key quality
            cur.execute("SELECT is_unique FROM access_validation.key_quality WHERE run_id=%s AND table_name=%s", (run_id, t))
            row = cur.fetchone()
            if row is None or row[0] is not True:
                raise GenerationRefused(f"key_quality for {t} is not unique (got {row and row[0]!r})")
            # Gate 6: manifest columns present (exact, not prefix)
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='access_raw' AND table_name=%s", (t,))
            present = {r[0] for r in cur.fetchall()}
            missing = [c for c in m["required_cols"] if c not in present]
            if missing:
                raise GenerationRefused(f"{t} missing required column(s): {missing}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_d4d5_governed_generation.py -k gate -v`
Expected: PASS (all gate scenarios).

- [ ] **Step 5: Commit**

```bash
git add access_harness/d4d5_governed_generation.py tests/test_d4d5_governed_generation.py
git commit -m "feat(d4d5-gen): manifest + six fail-closed pre-emit gates"
```

---

### Task 2: Reader + transform + report + governed-vs-direct parity regression

**Files:**
- Modify: `infra/database/access-harness/access_harness/d4d5_governed_generation.py`
- Test: `infra/database/access-harness/tests/test_d4d5_governed_generation.py`

**Interfaces:**
- Consumes: `MANIFEST`, the gates from Task 1.
- Produces: `read_class(conn, cls) -> dict` (returns `{d4_rows, d5_rows, counts}` for one class, applying
  the verbatim transform); `build_report(conn, run_id) -> dict` (provenance + per-class counts).

- [ ] **Step 1: Write the failing transform + parity tests**

```python
def test_read_class_counts_match_known(governed_conn):
    # live governed read; ICCB has 608 styles, MCCB 10335, PCB 3279
    r = gen.read_class(governed_conn, "ICCB")
    assert r["counts"]["total_styles"] == 608
    assert r["counts"]["d5_insert_count"] == 608  # one row per style (policy a)

def test_policy_a_metric_is_report_only(governed_conn):
    # rating_only rows are retained (NOT dropped); real_override is a separate count
    r = gen.read_class(governed_conn, "ICCB")
    assert r["counts"]["d5_insert_count"] == r["counts"]["real_override_count"] + r["counts"]["rating_only_count"] + r["counts"].get("neither_count", 0)
    assert r["counts"]["real_override_count"] == 241

@pytest.mark.live
def test_governed_vs_direct_parity(governed_conn, direct_frozen_accdb):
    # generate per-class counts from governed access_raw AND from the direct frozen Access read;
    # assert identical counts + identical representative JSON block shape.
    for cls in ("ICCB","MCCB","PCB"):
        g = gen.read_class(governed_conn, cls)["counts"]
        d = direct_counts(direct_frozen_accdb, cls)   # helper invoking the dry-run generator's logic
        assert g["total_styles"] == d["total_styles"]
        assert g["d5_insert_count"] == d["d5_insert_count"]
        assert g["real_override_count"] == d["real_override_count"]
        assert g["rating_only_count"] == d["rating_only_count"]
```

`governed_conn` is a fixture connecting to `config.governed_pg_dsn()` (skip if unset). `direct_frozen_accdb`
points at the frozen `.accdb` from `access_meta.extraction_run.frozen_copy_path`; `direct_counts` runs the
same block/metric logic over a pyodbc read (import or replicate the dry-run generator's per-class counters).

- [ ] **Step 2: Run to verify fail** -- `uv run pytest tests/test_d4d5_governed_generation.py -k "read_class or parity" -v` -> FAIL.

- [ ] **Step 3: Implement `read_class` + `build_report`**

Port the per-row loop from the dry-run generator VERBATIM (D4 non-null collection; D5 blocks via the
manifest's `d5_block_cols` per class; `is_real_override = InstOvrAmps is not None and float(InstOvrAmps) > 0`;
`has_rating = r_int or r_iec block non-empty`; `rating_only` when not real but rating present; one d5_row
per style with >=1 non-null block). Read rows with `SELECT * FROM access_raw."<access_table>"` (psycopg
returns dict-able rows via column names from `cur.description`). `build_report` adds the provenance block
read from `extraction_run` + `tcc_snapshot` + `access_meta.tables.checksum` +
`checksum_reconciliation.matches` for the run_id.

- [ ] **Step 4: Run to verify pass** -- same `-k` selector -> PASS (live tests skip without DSN/Access).

- [ ] **Step 5: Commit**

```bash
git add access_harness/d4d5_governed_generation.py tests/test_d4d5_governed_generation.py
git commit -m "feat(d4d5-gen): governed reader + transform + report + direct-parity regression"
```

---

### Task 3: SQL emitter (temp-stage + row-level guards + provenance header) + CLI

**Files:**
- Modify: `infra/database/access-harness/access_harness/d4d5_governed_generation.py`
- Modify: `infra/database/access-harness/access_harness/cli.py`
- Test: `infra/database/access-harness/tests/test_d4d5_governed_generation.py`

**Interfaces:**
- Consumes: Task 1 gates, Task 2 reader/report.
- Produces: `emit_029(class_reads, report) -> str`, `emit_030(class_reads, report) -> str`,
  `generate(conn, requested_run_id, out_dir) -> dict` (runs gates -> reads -> emits 3 files), and a
  `generate-d4d5` CLI subcommand.

- [ ] **Step 1: Write the failing emit tests**

```python
def test_emit_029_has_stage_and_rowlevel_guards():
    sql = gen.emit_029(SAMPLE_READS, SAMPLE_REPORT)
    assert "CREATE TEMP TABLE" in sql
    assert "BEGIN;" in sql and "COMMIT;" in sql
    assert "ON_ERROR_STOP" in sql
    assert "run_id" in sql and SAMPLE_REPORT["provenance"]["run_id"] in sql  # provenance header
    # row-level guards: stage count, dup-key, coverage anti-join, post-write count
    for needle in ("stage count", "duplicate", "anti-join", "rows updated"):
        assert needle.lower() in sql.lower()
    assert "%dryrun%" not in sql  # D1=A: no dry-run name lock on the prod artifact

def test_emit_030_has_class_coverage_and_upsert():
    sql = gen.emit_030(SAMPLE_READS, SAMPLE_REPORT)
    assert "ON CONFLICT (breaker_class, source_id) DO UPDATE" in sql
    assert "brk_style_native_overrides" in sql
    for needle in ("stage count", "duplicate", "anti-join", "inserted"):
        assert needle.lower() in sql.lower()

@pytest.mark.live
def test_generated_sql_applies_and_guards_fire_on_tcc_fidelity_test(...):
    # apply 029/030 DDL + the generated data SQL to a staging target on tcc_fidelity_test;
    # then tamper a stage row (orphan source_id) and assert the coverage anti-join RAISES.
```

- [ ] **Step 2: Run to verify fail** -> FAIL.

- [ ] **Step 3: Implement the emitters + CLI**

Each emitter builds: (a) the provenance comment header from `report["provenance"]`; (b)
`\set ON_ERROR_STOP on` + `BEGIN;`; (c) `CREATE TEMP TABLE stage_... ON COMMIT DROP` + chunked
`INSERT ... VALUES` of the staged rows (verbatim literal helpers from the dry-run generator:
`lit_text`/`lit_int`/`sql_jsonb`); (d) DO-block assertions IN-TX -- stage count == header count, no
duplicate key (`GROUP BY ... HAVING count(*)>1`), DDL present (target cols/table/PK exist), coverage
anti-join empty (`stage LEFT JOIN target ... WHERE target IS NULL` -> RAISE if any); (e) the write
(`UPDATE ... FROM stage` for 029; `INSERT ... SELECT FROM stage ON CONFLICT (breaker_class, source_id)
DO UPDATE` for 030); (f) a post-write count assertion (`GET DIAGNOSTICS` or a recount) == stage count;
(g) `COMMIT;`. `generate(conn, requested_run_id, out_dir)` calls `assert_governed_source` ->
`select_run_id` -> `assert_style_evidence` -> `read_class` x3 -> `build_report` -> writes the 3 files.
The CLI `generate-d4d5` subcommand routes the governed DSN, fences before the read, and accepts
`--run-id` + `--out-dir` (default `infra/database/sandbox/breaker/d4d5-governed-generation`).

- [ ] **Step 4: Run to verify pass** -> PASS (live apply-test skips without DSN).

- [ ] **Step 5: Commit**

```bash
git add access_harness/d4d5_governed_generation.py access_harness/cli.py tests/test_d4d5_governed_generation.py
git commit -m "feat(d4d5-gen): temp-stage row-level SQL emitter + generate-d4d5 CLI"
```

---

## After the tasks (controller-run, NOT a subagent task)
1. Run `generate-d4d5` against governed `access_raw` on Windows -> the 3 artifacts.
2. Fresh dated clone off `tcc_breaker_baseline_20260625` on host `apex-dev-pg` (NOT 79audit); apply 029
   DDL + 030 DDL + the generated 029/030 data SQL; verify counts 608/10335/3279 (D5 14222),
   partition real_override 241/129/317 (687) + rating_only 367/10204/2962 (13533) + neither 0/2/0 (2)
   = 14222 (all retained; rating_only = no real override AND rating present, neither = no override and no
   rating), all row-level guards pass, idempotent double-apply.
3. Commit the validated artifacts + a dry-run fidelity README under the sandbox dir.
4. Cross-engine: Codex `apex-jobs review-run` + opus whole-slice. Convergence-bounded.
5. STOP. No prod apply -- separate operator gos for 029 DDL -> governed 029 data -> 030 DDL ->
   governed 030 data, then author 031.

## Self-Review
- Spec coverage: gates 1-6 (Task 1), transform + policy (a) + parity (Task 2), temp-stage row-level
  emit + provenance + CLI (Task 3), dry-run + review + stop line (post-tasks). All spec sections mapped.
- Placeholder scan: the live-apply test body (Task 3 Step 1) is sketched; the implementer fills the
  apply/tamper detail against `tcc_fidelity_test` -- acceptable as a live-acceptance test, but name the
  covering DDL files and the tamper case explicitly when implementing.
- Type consistency: `read_class` returns `{d4_rows, d5_rows, counts}`; emitters consume that + `report`;
  CLI calls `generate()`. `GenerationRefused` is the single refusal type across all gates.
