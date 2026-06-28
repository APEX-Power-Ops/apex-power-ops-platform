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
        cur.execute(f'SELECT * FROM access_raw."{atbl}"')
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
        d4vals = {}
        if has_d4:
            for acc_col, pg_col in _D4_ACCESS_TO_PG:
                v = row.get(acc_col)
                d4vals[pg_col] = v
                if v is not None:
                    d4_nonnull[pg_col] += 1
            if any(v is not None for v in d4vals.values()):
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

        # Per style-table checksum + reconciliation
        style_tables = [m["access_table"] for m in MANIFEST.values()]
        table_checksums = {}
        for tbl in style_tables:
            cur.execute(
                "SELECT checksum FROM access_meta.tables "
                "WHERE run_id=%s AND table_name=%s",
                (run_id, tbl),
            )
            trow = cur.fetchone()
            checksum = trow[0] if trow is not None else None

            cur.execute(
                "SELECT matches FROM access_validation.checksum_reconciliation "
                "WHERE run_id=%s AND table_name=%s",
                (run_id, tbl),
            )
            rrow = cur.fetchone()
            matches = rrow[0] if rrow is not None else None

            table_checksums[tbl] = {"checksum": checksum, "matches": matches}

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
