"""D4/D5 governed-generation (Phase 2 / D-C).

Reads governed access_raw (tcc_fidelity_governed), runs six fail-closed pre-emit
gates, and emits provenance-stamped, row-level-guarded 029/030 data SQL.

Consumer of the harness; carries raw D4/D5 verbatim (policy a -- no behavioral
interpretation; HR1 spirit preserved).

Public API (Task 1 -- manifest + gates)
---------------------------------------
GenerationRefused(Exception)
    Raised by any gate that refuses. Generation must not proceed.

MANIFEST: dict[str, dict]
    Per breaker class (ICCB/MCCB/PCB): access_table, pg_table, has_d4,
    d4_cols, d5_block_cols (dict of block-name -> list of verbatim Access
    column names), and derived required_cols (sorted unique of
    ID + InstOvrAmps + d4_cols + all d5 block cols).

assert_governed_source(conn)
    Gate 1: refuse unless current_database() == 'tcc_fidelity_governed'.
    Converts config.assert_current_database RuntimeError -> GenerationRefused.

select_run_id(conn, requested) -> str
    Gate 2: if requested is given, it must exist in access_meta.extraction_run
    (else refuse); if omitted, return the sole run (refuse if not exactly one).

assert_style_evidence(conn, run_id)
    Gates 3-6 for ALL three style tables:
    - Gate 3 (materialized_owner): access_meta.materialized_owner
      (layer='access_raw', table_name) must have run_id == selected run_id.
    - Gate 4 (reconciliation): access_validation.checksum_reconciliation.matches
      must be True for (run_id, table).
    - Gate 5 (key_quality): access_validation.key_quality.is_unique must be True
      for (run_id, table).
    - Gate 6 (manifest columns, EXACT not prefix): every column in required_cols
      must exist in access_raw.<access_table> (information_schema.columns).

Public API (Task 2 -- governed reader + transform + report)
-----------------------------------------------------------
read_class(conn, cls) -> dict
    Read access_raw."<access_table>" via psycopg, apply the VERBATIM transform
    from the dry-run generator (using MANIFEST d5_block_cols for exact per-class
    block membership -- NOT str.startswith prefixes), and return:
      {
        "d4_rows": [(source_id, {pg_col: value}), ...],
        "d5_rows": [(source_id, {block_name: {col: value} or None}), ...],
        "counts": {
          "total_styles": int,
          "d4_update_count": int,
          "d5_insert_count": int,
          "real_override_count": int,     -- InstOvrAmps > 0 (metric only, no row filter)
          "rating_only_count": int,
          "d4_nonnull_per_col": {pg_col: int} or None,
          "d5_block_present_counts": {block_name: int},
          "samples": [up to 3 sample dicts],
        }
      }

build_report(conn, run_id, generated_at=None) -> dict
    Return provenance + per-class counts for a generation run:
      {
        "provenance": {run_id, source_sha256, frozen_copy_path, driver_name,
                       dbms_version, read_only, snapshot_id, host, db_name,
                       role, table_checksums, generator_version,
                       generated_at (if passed)},
        "classes": {cls: counts_dict, ...},
      }
    generated_at is NOT stamped internally -- pass it in or omit.

Public API (Task 3 -- SQL emitters + generate orchestrator)
-----------------------------------------------------------
emit_029(class_reads, report) -> str
    Emit provenance-stamped, row-level-guarded UPDATE SQL targeting
    tcc.brk_<class>_styles (D4 tmt_* columns).  ICCB + MCCB only.
    Contains stage table, INSERT chunks, DO-guard block, UPDATE, post-write
    assertion, wrapped in BEGIN/COMMIT.

emit_030(class_reads, report) -> str
    Emit provenance-stamped, row-level-guarded INSERT SQL targeting
    tcc.brk_style_native_overrides (D5 JSONB blocks).  All three classes.
    ON CONFLICT ... DO UPDATE (idempotent).

generate(conn, requested_run_id, out_dir, generated_at=None) -> dict
    Full orchestrator: gates -> read -> report -> merge counts -> write files.
    Writes 029_d4_data.sql, 030_d5_data.sql, generation_report.json.
    Returns summary dict with paths + per-class counts.
"""
from access_harness.config import GOVERNED_DB, assert_current_database


class GenerationRefused(Exception):
    """A fail-closed pre-emit gate refused. Generation must not proceed."""


# ---------------------------------------------------------------------------
# Column lists (verbatim Access column names, pinned from governed access_raw
# 2026-06-27). ASCII-only -- no em-dashes or smart quotes.
# ---------------------------------------------------------------------------

_INST = [
    "InstOvrAmps", "InstOvrMinTolerance", "InstOvrMaxTolerance",
    "InstOvrClrDelayTime", "InstOvrClrRadius", "InstOvrOpnDelayTime",
    "InstOvrOpnRadius", "InstOvrNoteText", "InstOvrClrCurve", "InstOvrClrChar",
    "InstOvrCurveCalcClr", "InstOvrClrEnteredAt", "InstOvrOpenCurve",
    "InstOvrOpenChar", "InstOvrCurveCalcOpen", "InstOvrOpenEnteredAt",
]

_NINST = [
    "NInstOvrAmps", "NInstOvrMinTolerance", "NInstOvrMaxTolerance",
    "NInstOvrClrDelayTime", "NInstOvrClrRadius", "NInstOvrOpnDelayTime",
    "NInstOvrOpnRadius", "NInstOvrClrCurve", "NInstOvrClrChar",
    "NInstOvrCurveCalcClr", "NInstOvrClrEnteredAt", "NInstOvrOpenCurve",
    "NInstOvrOpenChar", "NInstOvrCurveCalcOpen", "NInstOvrOpenEnteredAt",
]

_BRK = [
    "BrkTimesMechOpening50", "BrkTimesMechOpening60",
    "BrkTimesSTDelayBand50", "BrkTimesSTDelayBand60",
]

# r_int / r_iec base columns (ICCB + MCCB)
_RINT_BASE = [
    "r_int_inst_240", "r_int_inst_480", "r_int_inst_600",
    "r_int_series_240", "r_int_series_480", "r_int_series_600",
]
# PCB has 3 extra r_int_ninst_* columns
_RINT_PCB = _RINT_BASE + [
    "r_int_ninst_240", "r_int_ninst_480", "r_int_ninst_600",
]

# r_iec base columns (ICCB + MCCB, 11 voltage levels)
_RIEC_BASE = [
    "r_iec_inst_220", "r_iec_inst_230", "r_iec_inst_240",
    "r_iec_inst_380", "r_iec_inst_400", "r_iec_inst_415",
    "r_iec_inst_440", "r_iec_inst_500", "r_iec_inst_550",
    "r_iec_inst_690", "r_iec_inst_1000",
]
# PCB has 11 extra r_iec_ninst_* columns
_RIEC_PCB = _RIEC_BASE + [
    "r_iec_ninst_220", "r_iec_ninst_230", "r_iec_ninst_240",
    "r_iec_ninst_380", "r_iec_ninst_400", "r_iec_ninst_415",
    "r_iec_ninst_440", "r_iec_ninst_500", "r_iec_ninst_550",
    "r_iec_ninst_690", "r_iec_ninst_1000",
]

# D4 columns (ICCB + MCCB only; PCB has none)
_D4 = [
    "TMT_TCCNumber", "TMT_Notes", "TMT_TripPlug",
    "TMT_BreakerType", "TMT_ThermalMagnetic", "TMT_Thermal",
]


def _d5_blocks(rint, riec):
    """Build the d5_block_cols dict for a given class."""
    return {
        "inst_override": _INST,
        "ninst_override": _NINST,
        "brk_times": _BRK,
        "r_int": rint,
        "r_iec": riec,
    }


# ---------------------------------------------------------------------------
# MANIFEST -- per breaker class constant
# ---------------------------------------------------------------------------

MANIFEST = {
    "ICCB": {
        "access_table": "BreakerICCBStyles",
        "pg_table": "brk_iccb_styles",
        "has_d4": True,
        "d4_cols": _D4,
        "d5_block_cols": _d5_blocks(_RINT_BASE, _RIEC_BASE),
    },
    "MCCB": {
        "access_table": "BreakerMCCBStyles",
        "pg_table": "brk_mccb_styles",
        "has_d4": True,
        "d4_cols": _D4,
        "d5_block_cols": _d5_blocks(_RINT_BASE, _RIEC_BASE),
    },
    "PCB": {
        "access_table": "BreakerPCBStyles",
        "pg_table": "brk_pcb_styles",
        "has_d4": False,
        "d4_cols": [],
        "d5_block_cols": _d5_blocks(_RINT_PCB, _RIEC_PCB),
    },
}

# Derive required_cols for each class: sorted unique of
# ID + InstOvrAmps + d4_cols + all d5 block cols.
for _cls, _m in MANIFEST.items():
    _req = ["ID", "InstOvrAmps"] + list(_m["d4_cols"])
    for _grp in _m["d5_block_cols"].values():
        _req += _grp
    _m["required_cols"] = sorted(set(_req))


# ---------------------------------------------------------------------------
# Gate 1: assert_governed_source
# ---------------------------------------------------------------------------

def assert_governed_source(conn):
    """Gate 1: refuse unless connected to tcc_fidelity_governed.

    Reuses config.assert_current_database and converts its RuntimeError
    into GenerationRefused so callers see a single exception type.
    """
    try:
        assert_current_database(conn, GOVERNED_DB)
    except RuntimeError as exc:
        raise GenerationRefused(str(exc)) from exc


# ---------------------------------------------------------------------------
# Gate 2: select_run_id
# ---------------------------------------------------------------------------

def select_run_id(conn, requested):
    """Gate 2: resolve the run_id to use for generation.

    If `requested` is given, it must exist in access_meta.extraction_run;
    refuse if absent.
    If `requested` is None/empty, return the sole run_id; refuse if there
    is not exactly one row (ambiguous or empty).

    Returns the resolved run_id string.
    """
    with conn.cursor() as cur:
        if requested:
            cur.execute(
                "SELECT 1 FROM access_meta.extraction_run WHERE run_id=%s",
                (requested,),
            )
            if cur.fetchone() is None:
                raise GenerationRefused(
                    f"run_id {requested!r} not found in extraction_run"
                )
            return requested
        # No run_id requested -- default to the sole run.
        cur.execute("SELECT run_id FROM access_meta.extraction_run")
        rows = [r[0] for r in cur.fetchall()]
    if len(rows) != 1:
        raise GenerationRefused(
            f"run_id is ambiguous: {len(rows)} runs in extraction_run; "
            "pass an explicit run_id"
        )
    return rows[0]


# ---------------------------------------------------------------------------
# Gates 3-6: assert_style_evidence
# ---------------------------------------------------------------------------

def assert_style_evidence(conn, run_id):
    """Gates 3-6 for all 3 style tables.

    Gate 3 (materialized_owner): access_meta.materialized_owner
        (layer='access_raw', table_name) must have run_id == the selected
        run_id. This is the load-bearing gate: access_raw is
        latest-materialized while evidence is kept by run_id, so an older
        run_id could otherwise pass historical checksum/key-quality while
        reading newer table contents.

    Gate 4 (reconciliation): access_validation.checksum_reconciliation.matches
        must be True for (run_id, table).

    Gate 5 (key_quality): access_validation.key_quality.is_unique must be True
        for (run_id, table).

    Gate 6 (manifest columns, EXACT not prefix): every column in required_cols
        must exist in access_raw.<access_table> (information_schema.columns).
        Refuse listing the missing column(s).

    Raises GenerationRefused on any gate violation.
    """
    with conn.cursor() as cur:
        for cls, m in MANIFEST.items():
            t = m["access_table"]

            # Gate 3: materialized_owner
            cur.execute(
                "SELECT run_id FROM access_meta.materialized_owner "
                "WHERE layer='access_raw' AND table_name=%s",
                (t,),
            )
            row = cur.fetchone()
            owner = row[0] if row is not None else None
            if owner != run_id:
                raise GenerationRefused(
                    f"materialized_owner for {t} is {owner!r}, "
                    f"expected {run_id!r}"
                )

            # Gate 4: checksum reconciliation
            cur.execute(
                "SELECT matches FROM access_validation.checksum_reconciliation "
                "WHERE run_id=%s AND table_name=%s",
                (run_id, t),
            )
            row = cur.fetchone()
            matches = row[0] if row is not None else None
            if matches is not True:
                raise GenerationRefused(
                    f"checksum reconciliation for {t} did not match "
                    f"(run_id={run_id!r}, matches={matches!r})"
                )

            # Gate 5: key quality
            cur.execute(
                "SELECT is_unique FROM access_validation.key_quality "
                "WHERE run_id=%s AND table_name=%s",
                (run_id, t),
            )
            row = cur.fetchone()
            is_unique = row[0] if row is not None else None
            if is_unique is not True:
                raise GenerationRefused(
                    f"key_quality for {t} is not unique "
                    f"(run_id={run_id!r}, is_unique={is_unique!r})"
                )

            # Gate 6: manifest columns present (exact, not prefix)
            cur.execute(
                "SELECT column_name "
                "FROM information_schema.columns "
                "WHERE table_schema='access_raw' AND table_name=%s",
                (t,),
            )
            present = {r[0] for r in cur.fetchall()}
            missing = [c for c in m["required_cols"] if c not in present]
            if missing:
                raise GenerationRefused(
                    f"{t} is missing required column(s): {missing}"
                )


# ---------------------------------------------------------------------------
# D4 column name map: Access column name -> pg column name
# (ICCB/MCCB only; PCB has no D4).
# Order matches _D4 list above.
# ---------------------------------------------------------------------------

_D4_ACCESS_TO_PG = [
    ("TMT_TCCNumber",       "tmt_tcc_number"),
    ("TMT_Notes",           "tmt_notes"),
    ("TMT_TripPlug",        "tmt_trip_plug"),
    ("TMT_BreakerType",     "tmt_breaker_type"),
    ("TMT_ThermalMagnetic", "tmt_thermal_magnetic"),
    ("TMT_Thermal",         "tmt_thermal"),
]

# Generator version constant (stamped in build_report provenance).
_GENERATOR_VERSION = "0.2.0"


# ---------------------------------------------------------------------------
# Task 2: read_class
# ---------------------------------------------------------------------------

def read_class(conn, cls):
    """Read access_raw."<access_table>" and apply the verbatim D4/D5 transform.

    Source: governed access_raw via psycopg (double-precision InstOvrAmps).
    Transform: VERBATIM copy of the dry-run generator loop, substituting:
      - pyodbc cursor -> psycopg cursor
      - BLOCK_PREFIX startswith predicates -> MANIFEST[cls]["d5_block_cols"]
        exact column lists (so PCB ninst cols are included and a vanished col
        is NOT silently absorbed)
    Policy (a): InstOvrAmps > 0 is a REPORT METRIC ONLY -- never a row filter.

    Returns:
        {
          "d4_rows": [(source_id, {pg_col: access_value}), ...],
          "d5_rows": [(source_id, {block_name: {access_col: value} or None}), ...],
          "counts": {
            "total_styles": int,
            "d4_update_count": int,
            "d5_insert_count": int,
            "real_override_count": int,
            "rating_only_count": int,
            "d4_nonnull_per_col": {pg_col: int} or None,
            "d5_block_present_counts": {block_name: int},
            "samples": [up to 3 sample dicts],
          }
        }
    """
    m = MANIFEST[cls]
    atbl = m["access_table"]
    has_d4 = m["has_d4"]
    block_cols = m["d5_block_cols"]   # {block_name: [col, ...]} -- exact lists

    with conn.cursor() as cur:
        cur.execute(f'SELECT * FROM access_raw."{atbl}" ORDER BY "ID"')
        col_names = [d.name for d in cur.description]
        rows = [dict(zip(col_names, r)) for r in cur.fetchall()]

    d4_rows = []
    d4_nonnull = {pg: 0 for _, pg in _D4_ACCESS_TO_PG} if has_d4 else None
    d5_rows = []
    block_present = {b: 0 for b in block_cols}
    real_override = 0
    rating_only = 0
    samples = []

    for row in rows:
        sid = row["ID"]

        # -- D4 (ICCB/MCCB only) --
        # PATCH 1: stage EVERY style row for D4 classes (source-faithful idempotency).
        # A rerun must be able to clear stale values that were set by a previous run,
        # so all-null-D4 rows are included.  The "any non-null" filter has been removed.
        d4vals = {}
        if has_d4:
            for acc_col, pg_col in _D4_ACCESS_TO_PG:
                v = row.get(acc_col)
                d4vals[pg_col] = v
                if v is not None:
                    d4_nonnull[pg_col] += 1
            d4_rows.append((sid, d4vals))

        # -- D5 blocks -- use MANIFEST exact col lists (NOT startswith) --
        blocks = {}
        for bname, bcols in block_cols.items():
            blk = {c: row[c] for c in bcols if row.get(c) is not None}
            blocks[bname] = blk if blk else None
            if blk:
                block_present[bname] += 1

        # -- Real-override discriminator (policy a: metric only, never a filter) --
        inst_amps = row.get("InstOvrAmps")
        # Defensive coerce: access_raw stores double precision but an anomalous
        # text value must not crash the metric (the metric never drops a row).
        try:
            inst_amps_f = float(inst_amps) if inst_amps is not None else None
        except (TypeError, ValueError):
            inst_amps_f = None
        is_real = inst_amps_f is not None and inst_amps_f > 0
        has_rating = blocks.get("r_int") is not None or blocks.get("r_iec") is not None

        if is_real:
            real_override += 1
        elif has_rating:
            rating_only += 1

        # -- D5 row: any block non-null --
        if any(b is not None for b in blocks.values()):
            d5_rows.append((sid, blocks))
            if len(samples) < 3:
                samples.append({
                    "source_id": sid,
                    "d4": {pg: d4vals.get(pg) for _, pg in _D4_ACCESS_TO_PG} if has_d4 else None,
                    "d5_blocks_present": [b for b in block_cols if blocks.get(b) is not None],
                    "inst_override_keys": list(blocks["inst_override"].keys()) if blocks.get("inst_override") else [],
                    "r_int": blocks.get("r_int"),
                })

    return {
        "d4_rows": d4_rows,
        "d5_rows": d5_rows,
        "counts": {
            "total_styles": len(rows),
            "d4_update_count": len(d4_rows) if has_d4 else 0,
            "d5_insert_count": len(d5_rows),
            "real_override_count": real_override,
            "rating_only_count": rating_only,
            "d4_nonnull_per_col": d4_nonnull,
            "d5_block_present_counts": block_present,
            "samples": samples,
        },
    }


# ---------------------------------------------------------------------------
# Task 2: build_report
# ---------------------------------------------------------------------------

def build_report(conn, run_id, generated_at=None):
    """Build a provenance + counts report for a governed generation run.

    Reads from:
      - access_meta.extraction_run (run_id, source_sha256, frozen_copy_path,
        driver_name, dbms_version, read_only)
      - access_meta.tcc_snapshot (snapshot_id, host, db_name, role for run_id)
      - access_meta.tables.checksum per style table
      - access_validation.checksum_reconciliation.matches per style table

    generated_at: if provided (a datetime or ISO string), it is included in the
    provenance block. NOT generated internally -- the controller stamps it.

    Returns:
        {
          "provenance": {
            "run_id": str,
            "source_sha256": str or None,
            "frozen_copy_path": str or None,
            "driver_name": str or None,
            "dbms_version": str or None,
            "read_only": bool or None,
            "snapshot_id": str or None,
            "host": str or None,
            "db_name": str or None,
            "role": str or None,
            "table_checksums": {table_name: {"checksum": str, "matches": bool}},
            "generator_version": str,
            # "generated_at": ... (only if generated_at parameter is not None)
          },
          "classes": {cls: counts_dict, ...},
        }
    """
    with conn.cursor() as cur:
        # extraction_run
        cur.execute(
            "SELECT source_sha256, frozen_copy_path, driver_name, dbms_version, read_only "
            "FROM access_meta.extraction_run WHERE run_id=%s",
            (run_id,),
        )
        er = cur.fetchone()
        if er is not None:
            source_sha256, frozen_copy_path, driver_name, dbms_version, read_only = er
        else:
            source_sha256 = frozen_copy_path = driver_name = dbms_version = read_only = None

        # tcc_snapshot (keyed by snapshot_id PK; linked via run_id FK)
        cur.execute(
            "SELECT snapshot_id, host, db_name, role "
            "FROM access_meta.tcc_snapshot WHERE run_id=%s LIMIT 1",
            (run_id,),
        )
        snap = cur.fetchone()
        if snap is not None:
            snapshot_id, snap_host, snap_db, snap_role = snap
        else:
            snapshot_id = snap_host = snap_db = snap_role = None

        # Per style-table checksum + reconciliation + source row_count (PATCH 2)
        style_tables = [m["access_table"] for m in MANIFEST.values()]
        table_checksums = {}
        # Check once whether access_meta.tables has a row_count column.
        cur.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='access_meta' AND table_name='tables' "
            "AND column_name='row_count' LIMIT 1"
        )
        _has_row_count_col = cur.fetchone() is not None
        for tbl in style_tables:
            if _has_row_count_col:
                cur.execute(
                    "SELECT checksum, row_count FROM access_meta.tables "
                    "WHERE run_id=%s AND table_name=%s",
                    (run_id, tbl),
                )
                trow = cur.fetchone()
                checksum = trow[0] if trow is not None else None
                row_count = trow[1] if trow is not None else None
            else:
                cur.execute(
                    "SELECT checksum FROM access_meta.tables "
                    "WHERE run_id=%s AND table_name=%s",
                    (run_id, tbl),
                )
                trow = cur.fetchone()
                checksum = trow[0] if trow is not None else None
                # Fallback: count directly from access_raw
                try:
                    cur.execute(
                        'SELECT count(*) FROM access_raw."%s"' % tbl
                    )
                    rcount_row = cur.fetchone()
                    row_count = rcount_row[0] if rcount_row is not None else None
                except Exception:  # noqa: BLE001
                    row_count = None

            cur.execute(
                "SELECT matches FROM access_validation.checksum_reconciliation "
                "WHERE run_id=%s AND table_name=%s",
                (run_id, tbl),
            )
            rrow = cur.fetchone()
            matches = rrow[0] if rrow is not None else None

            table_checksums[tbl] = {"checksum": checksum, "matches": matches, "row_count": row_count}

    provenance = {
        "run_id": run_id,
        "source_sha256": source_sha256,
        "frozen_copy_path": frozen_copy_path,
        "driver_name": driver_name,
        "dbms_version": dbms_version,
        "read_only": read_only,
        "snapshot_id": snapshot_id,
        "host": snap_host,
        "db_name": snap_db,
        "role": snap_role,
        "table_checksums": table_checksums,
        "generator_version": _GENERATOR_VERSION,
    }
    if generated_at is not None:
        provenance["generated_at"] = generated_at

    return {
        "provenance": provenance,
        "classes": {},   # caller populates by calling read_class per cls
    }


# ---------------------------------------------------------------------------
# Task 3 -- Literal helpers (verbatim from dry-run generator, same escaping).
# ---------------------------------------------------------------------------

import json as _json
import decimal as _decimal
import datetime as _datetime


def _jdefault(o):
    if isinstance(o, _decimal.Decimal):
        return float(o)
    if isinstance(o, (bytes, bytearray)):
        return o.hex()
    if isinstance(o, (_datetime.datetime, _datetime.date, _datetime.time)):
        return o.isoformat()
    return str(o)


def _lit_text(v):
    """Escape a text value as a SQL literal or NULL."""
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def _lit_int(v):
    """Emit a smallint/integer literal or NULL."""
    if v is None:
        return "NULL"
    return str(int(v))


def _sql_jsonb(d):
    """Emit a JSONB literal cast or NULL (empty dict -> NULL)."""
    if not d:
        return "NULL"
    return "'" + _json.dumps(d, default=_jdefault, ensure_ascii=False).replace("'", "''") + "'::jsonb"


# ---------------------------------------------------------------------------
# Task 3 -- Provenance comment header builder (shared by emit_029 + emit_030).
# ---------------------------------------------------------------------------

_CHUNK = 500


def _provenance_header(report):
    """Return a multi-line SQL comment block describing the generation provenance."""
    p = report["provenance"]
    lines = [
        "-- Generated by access_harness.d4d5_governed_generation v%s" % p.get("generator_version", "?"),
        "-- run_id:           %s" % p.get("run_id", "?"),
        "-- snapshot_id:      %s" % p.get("snapshot_id", "?"),
        "-- source_db:        %s" % p.get("db_name", "?"),
        "-- source_sha256:    %s" % p.get("source_sha256", "?"),
        "-- frozen_copy_path: %s" % p.get("frozen_copy_path", "?"),
        "-- driver:           %s" % p.get("driver_name", "?"),
    ]
    if p.get("generated_at") is not None:
        lines.append("-- generated_at:     %s" % p["generated_at"])
    # Per-table row_count + checksum (PATCH 2: row_count included per spec)
    for tbl, info in p.get("table_checksums", {}).items():
        lines.append(
            "-- table %s: checksum=%s matches=%s row_count=%s" % (
                tbl,
                info.get("checksum", "?"),
                info.get("matches", "?"),
                info.get("row_count", "?"),
            )
        )
    # Per-class counts from report["classes"] (if already merged)
    for cls, counts in report.get("classes", {}).items():
        if counts:
            lines.append(
                "-- class %s: d4_update_count=%s d5_insert_count=%s" % (
                    cls,
                    counts.get("d4_update_count", "?"),
                    counts.get("d5_insert_count", "?"),
                )
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Task 3 -- emit_029: D4 UPDATEs for ICCB + MCCB
# ---------------------------------------------------------------------------

def emit_029(class_reads, report):
    """Emit provenance-stamped, row-level-guarded D4 UPDATE SQL.

    Targets tcc.brk_<class>_styles (tmt_* columns) for ICCB and MCCB.
    Script is self-contained with BEGIN/COMMIT.  Uses a per-class temp stage
    table so all guards and the UPDATE live in one transaction.

    class_reads: {cls: read_class(...) result}
    report:      build_report(...) result (provenance already populated)

    Returns the SQL string.
    """
    parts = [_provenance_header(report)]
    parts.append("SET client_encoding='UTF8';")
    parts.append("SET standard_conforming_strings=on;")
    parts.append("BEGIN;")

    d4_classes = [cls for cls in ("ICCB", "MCCB") if MANIFEST[cls]["has_d4"]]

    for cls in d4_classes:
        pg_table = MANIFEST[cls]["pg_table"]
        stage = "stage_029_%s" % cls.lower()
        reads = class_reads[cls]
        d4_rows = reads["d4_rows"]
        d4_count = reads["counts"]["d4_update_count"]

        # Stage table (ON COMMIT DROP so it is automatically cleaned up)
        parts.append(
            "CREATE TEMP TABLE %(stage)s ("
            "source_id integer, "
            "tmt_tcc_number text, "
            "tmt_notes text, "
            "tmt_trip_plug smallint, "
            "tmt_breaker_type smallint, "
            "tmt_thermal_magnetic smallint, "
            "tmt_thermal smallint"
            ") ON COMMIT DROP;" % {"stage": stage}
        )

        # Chunked INSERT into stage
        if d4_rows:
            for i in range(0, len(d4_rows), _CHUNK):
                chunk = d4_rows[i:i + _CHUNK]
                val_strs = []
                for sid, d in chunk:
                    val_strs.append(
                        "(%s,%s,%s,%s,%s,%s,%s)" % (
                            int(sid),
                            _lit_text(d.get("tmt_tcc_number")),
                            _lit_text(d.get("tmt_notes")),
                            _lit_int(d.get("tmt_trip_plug")),
                            _lit_int(d.get("tmt_breaker_type")),
                            _lit_int(d.get("tmt_thermal_magnetic")),
                            _lit_int(d.get("tmt_thermal")),
                        )
                    )
                parts.append(
                    "INSERT INTO %s VALUES %s;" % (stage, ",".join(val_strs))
                )

        # DO-guard block: 4 guards
        parts.append(
            "DO $g$ DECLARE\n"
            "  v_stage_count integer;\n"
            "  v_dup_count integer;\n"
            "  v_col_count integer;\n"
            "  v_unmatched integer;\n"
            "  v_dup_target integer;\n"
            "BEGIN\n"
            "  -- Guard 1: stage row count == expected D4 count\n"
            "  SELECT count(*) INTO v_stage_count FROM %(stage)s;\n"
            "  IF v_stage_count <> %(d4_count)d THEN\n"
            "    RAISE EXCEPTION '029 guard [%(cls)s]: stage row count %% != expected %(d4_count)d', v_stage_count;\n"
            "  END IF;\n"
            "  -- Guard 2: no duplicate source_id in stage\n"
            "  SELECT count(*) INTO v_dup_count FROM (\n"
            "    SELECT source_id FROM %(stage)s GROUP BY source_id HAVING count(*) > 1\n"
            "  ) dups;\n"
            "  IF v_dup_count > 0 THEN\n"
            "    RAISE EXCEPTION '029 guard [%(cls)s]: %% duplicate source_id(s) in stage', v_dup_count;\n"
            "  END IF;\n"
            "  -- Guard 3: DDL present -- 6 tmt_* columns exist on tcc.%(pg_table)s\n"
            "  SELECT count(*) INTO v_col_count FROM information_schema.columns\n"
            "    WHERE table_schema='tcc' AND table_name=%(pg_table_lit)s\n"
            "      AND column_name IN ('tmt_tcc_number','tmt_notes','tmt_trip_plug',\n"
            "                          'tmt_breaker_type','tmt_thermal_magnetic','tmt_thermal');\n"
            "  IF v_col_count <> 6 THEN\n"
            "    RAISE EXCEPTION '029 guard [%(cls)s]: DDL missing -- only %% of 6 tmt_* columns present on tcc.%(pg_table)s', v_col_count;\n"
            "  END IF;\n"
            "  -- Guard 4: coverage anti-join -- every stage source_id matches exactly one target row\n"
            "  SELECT count(*) INTO v_unmatched\n"
            "    FROM %(stage)s st\n"
            "    LEFT JOIN tcc.%(pg_table)s t ON t.source_id = st.source_id\n"
            "    WHERE t.source_id IS NULL;\n"
            "  IF v_unmatched > 0 THEN\n"
            "    RAISE EXCEPTION '029 guard [%(cls)s]: %% stage source_id(s) have no match in tcc.%(pg_table)s (orphan rows)', v_unmatched;\n"
            "  END IF;\n"
            "  -- Guard 4b: source_id is unique in the target (no fan-out)\n"
            "  SELECT count(*) INTO v_dup_target FROM (\n"
            "    SELECT source_id FROM tcc.%(pg_table)s GROUP BY source_id HAVING count(*) > 1\n"
            "  ) dup_t;\n"
            "  IF v_dup_target > 0 THEN\n"
            "    RAISE EXCEPTION '029 guard [%(cls)s]: %% non-unique source_id(s) in tcc.%(pg_table)s -- UPDATE would fan-out', v_dup_target;\n"
            "  END IF;\n"
            "END $g$;" % {
                "stage": stage,
                "cls": cls,
                "d4_count": d4_count,
                "pg_table": pg_table,
                "pg_table_lit": _lit_text(pg_table),
            }
        )

        # UPDATE
        parts.append(
            "UPDATE tcc.%(pg_table)s s\n"
            "  SET tmt_tcc_number       = st.tmt_tcc_number,\n"
            "      tmt_notes            = st.tmt_notes,\n"
            "      tmt_trip_plug        = st.tmt_trip_plug,\n"
            "      tmt_breaker_type     = st.tmt_breaker_type,\n"
            "      tmt_thermal_magnetic = st.tmt_thermal_magnetic,\n"
            "      tmt_thermal          = st.tmt_thermal\n"
            "  FROM %(stage)s st\n"
            "  WHERE s.source_id = st.source_id;" % {
                "pg_table": pg_table,
                "stage": stage,
            }
        )

        # Post-write assertion: rows updated == stage count (via a matched-count query)
        parts.append(
            "DO $pw$ DECLARE v_updated integer; v_expected integer;\n"
            "BEGIN\n"
            "  SELECT count(*) INTO v_expected FROM %(stage)s;\n"
            "  SELECT count(*) INTO v_updated\n"
            "    FROM %(stage)s st\n"
            "    JOIN tcc.%(pg_table)s t ON t.source_id = st.source_id\n"
            "    WHERE t.tmt_tcc_number IS NOT DISTINCT FROM st.tmt_tcc_number\n"
            "      AND t.tmt_notes IS NOT DISTINCT FROM st.tmt_notes\n"
            "      AND t.tmt_trip_plug IS NOT DISTINCT FROM st.tmt_trip_plug\n"
            "      AND t.tmt_breaker_type IS NOT DISTINCT FROM st.tmt_breaker_type\n"
            "      AND t.tmt_thermal_magnetic IS NOT DISTINCT FROM st.tmt_thermal_magnetic\n"
            "      AND t.tmt_thermal IS NOT DISTINCT FROM st.tmt_thermal;\n"
            "  IF v_updated <> v_expected THEN\n"
            "    RAISE EXCEPTION '029 post-write [%(cls)s]: only %% of %% rows updated (values landed)', v_updated, v_expected;\n"
            "  END IF;\n"
            "END $pw$;" % {
                "stage": stage,
                "pg_table": pg_table,
                "cls": cls,
            }
        )

    parts.append("COMMIT;")
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Task 3 -- emit_030: D5 INSERTs into brk_style_native_overrides
# ---------------------------------------------------------------------------

def emit_030(class_reads, report):
    """Emit provenance-stamped, row-level-guarded D5 INSERT SQL.

    Targets tcc.brk_style_native_overrides (JSONB blocks).  All three classes.
    ON CONFLICT (breaker_class, source_id) DO UPDATE SET ... (idempotent).
    Script is self-contained with BEGIN/COMMIT.

    class_reads: {cls: read_class(...) result}
    report:      build_report(...) result (provenance already populated)

    Returns the SQL string.
    """
    parts = [_provenance_header(report)]
    parts.append("SET client_encoding='UTF8';")
    parts.append("SET standard_conforming_strings=on;")
    parts.append("BEGIN;")

    # Single stage table for all classes
    parts.append(
        "CREATE TEMP TABLE stage_030_d5 ("
        "breaker_class text, "
        "source_id integer, "
        "inst_override jsonb, "
        "ninst_override jsonb, "
        "brk_times jsonb, "
        "r_int jsonb, "
        "r_iec jsonb"
        ") ON COMMIT DROP;"
    )

    # Chunked INSERT from every class
    total_d5 = 0
    for cls in ("ICCB", "MCCB", "PCB"):
        reads = class_reads[cls]
        d5_rows = reads["d5_rows"]
        total_d5 += len(d5_rows)
        if d5_rows:
            for i in range(0, len(d5_rows), _CHUNK):
                chunk = d5_rows[i:i + _CHUNK]
                val_strs = []
                for sid, blocks in chunk:
                    val_strs.append(
                        "(%s,%d,%s,%s,%s,%s,%s)" % (
                            _lit_text(cls),
                            int(sid),
                            _sql_jsonb(blocks.get("inst_override")),
                            _sql_jsonb(blocks.get("ninst_override")),
                            _sql_jsonb(blocks.get("brk_times")),
                            _sql_jsonb(blocks.get("r_int")),
                            _sql_jsonb(blocks.get("r_iec")),
                        )
                    )
                parts.append(
                    "INSERT INTO stage_030_d5 VALUES %s;" % ",".join(val_strs)
                )

    # DO-guard block: 4 guards
    parts.append(
        "DO $g$ DECLARE\n"
        "  v_stage_count integer;\n"
        "  v_dup_count integer;\n"
        "  v_tbl_exists integer;\n"
        "  v_pk_cols integer;\n"
        "  v_unmatched integer;\n"
        "BEGIN\n"
        "  -- Guard 1: stage row count == expected D5 total\n"
        "  SELECT count(*) INTO v_stage_count FROM stage_030_d5;\n"
        "  IF v_stage_count <> %(total_d5)d THEN\n"
        "    RAISE EXCEPTION '030 guard: stage row count %% != expected %(total_d5)d', v_stage_count;\n"
        "  END IF;\n"
        "  -- Guard 2: no duplicate (breaker_class, source_id) in stage\n"
        "  SELECT count(*) INTO v_dup_count FROM (\n"
        "    SELECT breaker_class, source_id FROM stage_030_d5\n"
        "    GROUP BY breaker_class, source_id HAVING count(*) > 1\n"
        "  ) dups;\n"
        "  IF v_dup_count > 0 THEN\n"
        "    RAISE EXCEPTION '030 guard: %% duplicate (breaker_class, source_id) pair(s) in stage', v_dup_count;\n"
        "  END IF;\n"
        "  -- Guard 3: DDL present -- tcc.brk_style_native_overrides exists with PK (breaker_class, source_id)\n"
        "  SELECT count(*) INTO v_tbl_exists FROM information_schema.tables\n"
        "    WHERE table_schema='tcc' AND table_name='brk_style_native_overrides';\n"
        "  IF v_tbl_exists <> 1 THEN\n"
        "    RAISE EXCEPTION '030 guard: tcc.brk_style_native_overrides does not exist';\n"
        "  END IF;\n"
        "  -- PATCH 4: exact-2 PK guard matching the queued DDL (030_d5_native_overrides_sidetable.sql).\n"
        "  -- Step 1: total PK column count must be exactly 2.\n"
        "  SELECT count(*) INTO v_pk_cols\n"
        "    FROM information_schema.table_constraints tc\n"
        "    JOIN information_schema.key_column_usage kcu\n"
        "      ON kcu.constraint_schema = tc.constraint_schema\n"
        "      AND kcu.constraint_name = tc.constraint_name\n"
        "    WHERE tc.table_schema='tcc' AND tc.table_name='brk_style_native_overrides'\n"
        "      AND tc.constraint_type='PRIMARY KEY';\n"
        "  IF v_pk_cols <> 2 THEN\n"
        "    RAISE EXCEPTION '030 guard: PK has %% column(s), expected exactly 2 (breaker_class, source_id)', v_pk_cols;\n"
        "  END IF;\n"
        "  -- Step 2: membership check -- the 2 PK columns must be exactly (breaker_class, source_id).\n"
        "  IF (SELECT count(*) FROM information_schema.table_constraints tc\n"
        "        JOIN information_schema.key_column_usage kcu\n"
        "          ON kcu.constraint_schema = tc.constraint_schema\n"
        "          AND kcu.constraint_name = tc.constraint_name\n"
        "        WHERE tc.table_schema='tcc' AND tc.table_name='brk_style_native_overrides'\n"
        "          AND tc.constraint_type='PRIMARY KEY'\n"
        "          AND kcu.column_name IN ('breaker_class','source_id')) <> 2 THEN\n"
        "    RAISE EXCEPTION '030 guard: PK columns are not exactly (breaker_class, source_id)';\n"
        "  END IF;\n"
        "  -- Guard 4: coverage anti-join -- every stage (breaker_class, source_id)\n"
        "  --   must join its per-class style table source_id\n"
        "  SELECT count(*) INTO v_unmatched FROM (\n"
        "    SELECT st.breaker_class, st.source_id\n"
        "    FROM stage_030_d5 st\n"
        "    WHERE st.breaker_class = 'ICCB'\n"
        "      AND NOT EXISTS (SELECT 1 FROM tcc.brk_iccb_styles s WHERE s.source_id = st.source_id)\n"
        "    UNION ALL\n"
        "    SELECT st.breaker_class, st.source_id\n"
        "    FROM stage_030_d5 st\n"
        "    WHERE st.breaker_class = 'MCCB'\n"
        "      AND NOT EXISTS (SELECT 1 FROM tcc.brk_mccb_styles s WHERE s.source_id = st.source_id)\n"
        "    UNION ALL\n"
        "    SELECT st.breaker_class, st.source_id\n"
        "    FROM stage_030_d5 st\n"
        "    WHERE st.breaker_class = 'PCB'\n"
        "      AND NOT EXISTS (SELECT 1 FROM tcc.brk_pcb_styles s WHERE s.source_id = st.source_id)\n"
        "  ) unmatched;\n"
        "  IF v_unmatched > 0 THEN\n"
        "    RAISE EXCEPTION '030 guard: %% stage (breaker_class, source_id) pair(s) have no match in the per-class style table (orphan rows)', v_unmatched;\n"
        "  END IF;\n"
        "END $g$;" % {"total_d5": total_d5}
    )

    # Write: INSERT ... ON CONFLICT DO UPDATE
    parts.append(
        "INSERT INTO tcc.brk_style_native_overrides\n"
        "  (breaker_class, source_id, inst_override, ninst_override,\n"
        "   brk_times, r_int, r_iec, ovr_curves)\n"
        "SELECT breaker_class, source_id, inst_override, ninst_override,\n"
        "       brk_times, r_int, r_iec, NULL\n"
        "FROM stage_030_d5\n"
        "ON CONFLICT (breaker_class, source_id) DO UPDATE SET\n"
        "  inst_override  = EXCLUDED.inst_override,\n"
        "  ninst_override = EXCLUDED.ninst_override,\n"
        "  brk_times      = EXCLUDED.brk_times,\n"
        "  r_int          = EXCLUDED.r_int,\n"
        "  r_iec          = EXCLUDED.r_iec,\n"
        "  ovr_curves     = EXCLUDED.ovr_curves;"
    )

    # Post-write assertion: inserted+updated == stage count
    parts.append(
        "DO $pw$ DECLARE v_written integer; v_expected integer;\n"
        "BEGIN\n"
        "  SELECT count(*) INTO v_expected FROM stage_030_d5;\n"
        "  SELECT count(*) INTO v_written\n"
        "    FROM stage_030_d5 st\n"
        "    JOIN tcc.brk_style_native_overrides t\n"
        "      ON t.breaker_class = st.breaker_class AND t.source_id = st.source_id;\n"
        "  IF v_written <> v_expected THEN\n"
        "    -- single % below is a literal PL/pgSQL placeholder -- NOT a Python %-format target\n"
        "    RAISE EXCEPTION '030 post-write: only % of % rows present in target after INSERT', v_written, v_expected;\n"
        "  END IF;\n"
        "END $pw$;"
    )

    # PATCH 3: Post-write VALUE parity guard (in-tx, for the staged keyset).
    # Asserts each target row's payload equals the staged payload using
    # IS NOT DISTINCT FROM for the 5 JSONB blocks + ovr_curves IS NULL.
    # This is a regression tripwire for a future broken UPDATE clause; a
    # negative test is not cleanly constructible because ON CONFLICT DO UPDATE
    # always overwrites to the stage values -- asserting clean-pass is sufficient.
    parts.append(
        "DO $vp$ DECLARE v_mismatch integer;\n"
        "BEGIN\n"
        "  -- 030 value-parity guard: for each staged row, target payload must match stage.\n"
        "  -- Guards against a future broken UPDATE clause leaving stale JSONB.\n"
        "  SELECT count(*) INTO v_mismatch\n"
        "    FROM stage_030_d5 st\n"
        "    JOIN tcc.brk_style_native_overrides t\n"
        "      ON t.breaker_class = st.breaker_class AND t.source_id = st.source_id\n"
        "    WHERE NOT (\n"
        "          t.inst_override  IS NOT DISTINCT FROM st.inst_override\n"
        "      AND t.ninst_override IS NOT DISTINCT FROM st.ninst_override\n"
        "      AND t.brk_times      IS NOT DISTINCT FROM st.brk_times\n"
        "      AND t.r_int          IS NOT DISTINCT FROM st.r_int\n"
        "      AND t.r_iec          IS NOT DISTINCT FROM st.r_iec\n"
        "      AND t.ovr_curves IS NULL\n"
        "    );\n"
        "  IF v_mismatch > 0 THEN\n"
        "    -- single % below is a literal PL/pgSQL placeholder -- NOT a Python %-format target\n"
        "    RAISE EXCEPTION '030 value-parity: % staged row(s) have mismatched payload in target after INSERT', v_mismatch;\n"
        "  END IF;\n"
        "END $vp$;"
    )

    # Extra-row guard (post-write, in-tx): for each class the stage covers, the
    # count of tcc.brk_style_native_overrides rows for that class must EQUAL the
    # staged keyset count -- no target row for a staged class may be absent from
    # the stage (anti-join target LEFT JOIN stage WHERE stage IS NULL -> 0).
    # Scoped to classes this stage actually carries; classes not in the stage are ignored.
    parts.append(
        "DO $xr$ DECLARE v_extra integer;\n"
        "BEGIN\n"
        "  -- Extra-row guard: target must not contain (breaker_class, source_id) rows\n"
        "  -- that are absent from stage_030_d5 for any class the stage covers.\n"
        "  SELECT count(*) INTO v_extra\n"
        "    FROM tcc.brk_style_native_overrides t\n"
        "    -- Restrict to classes the stage carries (avoid flagging unrelated classes)\n"
        "    WHERE t.breaker_class IN (SELECT DISTINCT breaker_class FROM stage_030_d5)\n"
        "      AND NOT EXISTS (\n"
        "        SELECT 1 FROM stage_030_d5 st\n"
        "        WHERE st.breaker_class = t.breaker_class AND st.source_id = t.source_id\n"
        "      );\n"
        "  IF v_extra > 0 THEN\n"
        "    -- single % below is a literal PL/pgSQL placeholder -- NOT a Python %-format target\n"
        "    RAISE EXCEPTION '030 extra-row guard: % stale (breaker_class, source_id) row(s) in target outside the staged keyset -- polluted prior apply detected', v_extra;\n"
        "  END IF;\n"
        "END $xr$;"
    )

    parts.append("COMMIT;")
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Task 3 -- generate() orchestrator
# ---------------------------------------------------------------------------

import datetime as _dt
import json as _json_io
import pathlib as _pathlib


def generate(conn, requested_run_id, out_dir, generated_at=None):
    """Full orchestrator for the D4/D5 governed generation.

    Steps:
      1. assert_governed_source(conn)          -- Gate 1
      2. run_id = select_run_id(conn, ...)      -- Gate 2
      3. assert_style_evidence(conn, run_id)   -- Gates 3-6
      4. reads = {cls: read_class(conn, cls)}  -- read all 3 classes
      5. report = build_report(conn, run_id, generated_at)
      6. Merge per-class counts into report["classes"]
      7. Write 029_d4_data.sql, 030_d5_data.sql, generation_report.json
      8. Return summary dict

    Hardening (Task-2 Minor 1): the provenance header's run_id and sha256
    come from the SAME selected run_id that passed assert_style_evidence
    (build_report queries by run_id -- no separate latest-extraction call).

    generated_at: if None, stamped internally as UTC ISO string.

    Returns:
        {
          "run_id": str,
          "out_dir": str,
          "sql_029": str,    -- path to 029_d4_data.sql
          "sql_030": str,    -- path to 030_d5_data.sql
          "report_json": str, -- path to generation_report.json
          "classes": {cls: counts_dict, ...},
        }
    """
    # Gate 1
    assert_governed_source(conn)

    # Gate 2
    run_id = select_run_id(conn, requested_run_id)

    # Gates 3-6
    assert_style_evidence(conn, run_id)

    # Stamp generated_at if not provided
    if generated_at is None:
        generated_at = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Read all 3 classes
    reads = {cls: read_class(conn, cls) for cls in MANIFEST}

    # Build report (provenance comes from the SAME run_id -- Task-2 Minor 1 hardening)
    report = build_report(conn, run_id, generated_at=generated_at)

    # Merge per-class counts into report["classes"] (Task-2 Minor 2 closure)
    for cls, r in reads.items():
        report["classes"][cls] = r["counts"]

    # Emit SQL
    sql_029 = emit_029(reads, report)
    sql_030 = emit_030(reads, report)

    # Write output files
    out_path = _pathlib.Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    path_029 = out_path / "029_d4_data.sql"
    path_030 = out_path / "030_d5_data.sql"
    path_rpt = out_path / "generation_report.json"

    path_029.write_text(sql_029, encoding="utf-8")
    path_030.write_text(sql_030, encoding="utf-8")
    path_rpt.write_text(
        _json_io.dumps(report, indent=2, default=_jdefault, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "run_id": run_id,
        "out_dir": str(out_path),
        "sql_029": str(path_029),
        "sql_030": str(path_030),
        "report_json": str(path_rpt),
        "classes": report["classes"],
    }
