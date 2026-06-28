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
