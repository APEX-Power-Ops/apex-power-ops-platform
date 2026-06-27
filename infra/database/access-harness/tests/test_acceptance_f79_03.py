"""Task 11 -- the F-79-03 acceptance: the breaker/TMT slice END-TO-END, live.

This is the culmination integration test.  It runs the breaker/TMT slice via
access_harness.cli.run_all against:
  * the REAL frozen copy of D:\\TCC_NEW.accdb (ACE / pyodbc, Windows-only),
  * the governed host tcc.* over the LarePass mesh (read-only), and
  * a LOCAL Postgres (tcc_fidelity_test),
then asserts the STRUCTURAL F-79-03 evidence with ZERO behavioral interpretation
(HR1).  It RECORDS the actual deltas (it does NOT hard-code -169/-246/-58); it
only asserts INTERNAL CONSISTENCY + structural shape.

SKIP-WITH-REASON (never a silent no-op) when a prerequisite is absent:
  * ACCESS_HARNESS_SUPERUSER_DSN unset, or it does not resolve to a reachable
    tcc_fidelity_test;
  * D:\\TCC_NEW.accdb missing (or not on Windows / no ACE driver);
  * TCC_BREAKER_RO_PW unset or the host tcc is unreachable.
On THIS build machine all three are present, so the acceptance RUNS.

HONEST SCOPE (see C:\\Users\\jjswe\\.sdd\\reports\\access-harness-task-11-report.md):
The achievable, honest Phase-1 F-79-03 evidence is the access-vs-tcc COUNT
reconciliation, the cleanly-keyable STYLE-PROVENANCE anti-join, the numeric-
normalised amps rating-value anti-join, the count-only curves/thermal evidence,
the recorded STYLE-RESOLUTION AMBIGUITY (the implicit-class overlap), the
red-team guard, and HR1.  The row-level FRAME-resolved anti-join is DEFERRED:
tcc.tmt_frames.id is re-sequenced and tcc `size` is a computed representation
that does not equal the Access FrameDesc, so a frame correspondence cannot be
honestly built; the ambiguity is recorded as a count, never fabricated.
"""
import os
import pathlib
import tempfile

import psycopg
import pytest

from access_harness import cli
from access_harness import config as _config
from access_harness.hr1_guard import assert_no_interpretive_columns
from access_harness.projection import (
    ForbiddenKeyError,
    ProjectionMap,
    assert_key_allowed,
)
from access_harness.snapshot_tcc import host_tcc_conn

ACCDB = r"D:\TCC_NEW.accdb"
_SCHEMAS = ["access_raw", "access_meta", "access_validation", "tcc_snapshot"]
_SQL = pathlib.Path(__file__).parent.parent / "sql" / "001_schemas.sql"

# Enumeration cap mirrored from validate.ENUMERATION_CAP (asserted, not imported,
# so a drift in the cap is caught here too).
_CAP = 1000


# ---------------------------------------------------------------------------
# Prerequisite probes -- each returns (ok: bool, reason: str).
# ---------------------------------------------------------------------------

def _dsn_reason():
    if not os.environ.get("ACCESS_HARNESS_SUPERUSER_DSN"):
        return False, "ACCESS_HARNESS_SUPERUSER_DSN unset"
    try:
        conn = psycopg.connect(_config.test_pg_dsn(), autocommit=True, connect_timeout=5)
    except Exception as exc:  # noqa: BLE001
        return False, f"tcc_fidelity_test unreachable: {exc!r}"
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            (db,) = cur.fetchone()
        if db != "tcc_fidelity_test":
            return False, f"DSN resolved to {db!r}, not tcc_fidelity_test"
    finally:
        conn.close()
    return True, ""


def _accdb_reason():
    if not pathlib.Path(ACCDB).exists():
        return False, f"{ACCDB} not present"
    try:
        import pyodbc  # noqa: F401
    except Exception:  # noqa: BLE001
        return False, "pyodbc not importable (non-Windows / no ACE driver)"
    return True, ""


def _host_reason():
    if not os.environ.get("TCC_BREAKER_RO_PW"):
        return False, "TCC_BREAKER_RO_PW unset"
    try:
        conn = host_tcc_conn()
    except Exception as exc:  # noqa: BLE001
        return False, f"host tcc unreachable: {exc!r}"
    try:
        conn.close()
    except Exception:  # noqa: BLE001
        pass
    return True, ""


def _all_prereqs():
    """Return (ok, reason) -- ok only when ALL prerequisites are present."""
    for probe in (_dsn_reason, _accdb_reason, _host_reason):
        ok, reason = probe()
        if not ok:
            return False, reason
    return True, ""


# ---------------------------------------------------------------------------
# Module-scoped live run: run-all ONCE, assert many facets.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def live_run():
    """Run the breaker/TMT slice end-to-end ONCE against tcc_fidelity_test.

    Skips WITH A CLEAR REASON if any prerequisite is absent.  Builds a clean
    schema set (hard-fenced to tcc_fidelity_test), runs cli.run_all (curves
    count-only), and yields {'dsn', 'run_id', 'snapshot_id', 'loaded',
    'all_tables'}.  Schemas are dropped on teardown.
    """
    ok, reason = _all_prereqs()
    if not ok:
        pytest.skip(f"F-79-03 acceptance prerequisite absent: {reason}")

    dsn = _config.test_pg_dsn()

    # HARD FENCE + clean schema set.
    setup = psycopg.connect(dsn, autocommit=True)
    try:
        with setup.cursor() as cur:
            cur.execute("SELECT current_database()")
            (db,) = cur.fetchone()
            if db != "tcc_fidelity_test":
                raise RuntimeError(
                    f"HARD FENCE VIOLATION: connected to {db!r}, not "
                    "tcc_fidelity_test"
                )
            for s in _SCHEMAS:
                cur.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")
            for s in _SCHEMAS:
                cur.execute(f"CREATE SCHEMA {s}")
            cur.execute(_SQL.read_text(encoding="utf-8"))
    finally:
        setup.close()

    frozen_dir = pathlib.Path(tempfile.mkdtemp(prefix="harness_frozen_"))

    pg_auto = psycopg.connect(dsn, autocommit=True)
    pg_tx = psycopg.connect(dsn, autocommit=False)
    try:
        result = cli.run_all(
            pg_auto, pg_tx, ACCDB, frozen_dir, with_curves=False
        )
    finally:
        pg_tx.close()
        pg_auto.close()

    result["dsn"] = dsn
    yield result

    # Teardown: drop schemas.
    teardown = psycopg.connect(dsn, autocommit=True)
    try:
        with teardown.cursor() as cur:
            for s in _SCHEMAS:
                cur.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")
    finally:
        teardown.close()


@pytest.fixture
def pg_conn(live_run):
    """A fresh autocommit connection to the run's DB for read-back assertions."""
    conn = psycopg.connect(live_run["dsn"], autocommit=True)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Style-parent coverage helper (Task 3).
# ---------------------------------------------------------------------------

def _assert_style_parent_coverage(pg_conn, run_id):
    """The 3 style parents must carry a recorded checksum (load_state checksummed),
    a checksum_reconciliation row, and a key_quality row after run_all."""
    styles = ("BreakerICCBStyles", "BreakerMCCBStyles", "BreakerPCBStyles")
    for tbl in styles:
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT checksum, load_state FROM access_meta.tables "
                "WHERE run_id=%s AND table_name=%s", (run_id, tbl))
            ck, state = cur.fetchone()
            assert ck is not None, f"{tbl}: no recorded checksum"
            assert state == "checksummed", f"{tbl}: load_state={state!r}"
            cur.execute(
                "SELECT matches FROM access_validation.checksum_reconciliation "
                "WHERE run_id=%s AND table_name=%s", (run_id, tbl))
            recon = cur.fetchone()
            assert recon is not None, f"{tbl}: no checksum_reconciliation row"
            # Fidelity expectation: the style parents round-trip faithfully
            # (int/text/float/smallint columns). A False here is a GENUINE
            # fidelity finding to surface, not to suppress.
            assert recon[0] is True, (
                f"{tbl}: access-vs-staging checksum MISMATCH (matches=False) -- "
                "investigate the round-trip before generating population SQL")
            cur.execute(
                "SELECT is_unique FROM access_validation.key_quality "
                "WHERE run_id=%s AND table_name=%s", (run_id, tbl))
            kq = cur.fetchone()
            assert kq is not None, f"{tbl}: no key_quality row"


# ---------------------------------------------------------------------------
# THE acceptance test.
# ---------------------------------------------------------------------------

def test_f79_03_pipeline_produces_structural_evidence(live_run, pg_conn):
    """run-all the slice; assert the structural F-79-03 evidence (HR1)."""
    run_id = live_run["run_id"]
    snapshot_id = live_run["snapshot_id"]

    # ------------------------------------------------------------------
    # 0. Slice loaded: Breaker_TMTFrameSizes is in access_raw with rows.
    #    (curves is count-only -- NOT data-loaded.)
    # ------------------------------------------------------------------
    assert "Breaker_TMTFrameSizes" in live_run["loaded"]
    assert "Breaker_TMTFrameCurves" not in live_run["loaded"], (
        "curves must be count-only (not data-loaded) by default"
    )
    with pg_conn.cursor() as cur:
        cur.execute('SELECT count(*) FROM access_raw."Breaker_TMTFrameSizes"')
        (frame_rows,) = cur.fetchone()
    assert frame_rows > 0, "Breaker_TMTFrameSizes must be loaded with rows"

    # Driver-capability preflight evidence: the extraction_run recorded a real
    # driver/version (the metadata path returned rows on the frozen file).
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT driver_name, dbms_version FROM access_meta.extraction_run "
            "WHERE run_id=%s",
            (run_id,),
        )
        drv = cur.fetchone()
    assert drv is not None and drv[0], "preflight must record a driver name"

    # Inventory covers ALL tables; the slice is loaded, the rest inventoried.
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT load_state, count(*) FROM access_meta.tables "
            "WHERE run_id=%s GROUP BY load_state",
            (run_id,),
        )
        states = dict(cur.fetchall())
    # After reconcile_checksums, loaded tables are upgraded to 'checksummed'.
    # Accept either state -- a run without reconcile_checksums (future test
    # fixture) may still carry 'loaded'.
    loaded_or_checksummed = (
        states.get("loaded", 0) + states.get("checksummed", 0)
    )
    assert loaded_or_checksummed == len(live_run["loaded"]), (
        f"loaded + checksummed count {loaded_or_checksummed} != "
        f"slice length {len(live_run['loaded'])}"
    )
    assert states.get("inventoried_only", 0) > 0, "the non-slice tables must be inventoried"
    assert sum(states.values()) == len(live_run["all_tables"])

    # ------------------------------------------------------------------
    # 1. access-vs-tcc COUNT reconciliation for ALL 5 TMT tables, NON-NULL
    #    deltas, internally consistent (delta == access - tcc).  RECORD actuals.
    # ------------------------------------------------------------------
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT access_table, access_row_count, tcc_row_count, delta "
            "FROM access_validation.tcc_count_reconciliation WHERE run_id=%s "
            "ORDER BY access_table",
            (run_id,),
        )
        recon = cur.fetchall()
    recon_tables = {r[0] for r in recon}
    assert recon_tables == {
        "Breaker_TMTFrameSizes",
        "Breaker_TMTFrameAmps",
        "Breaker_TMTFrameSettings",
        "Breaker_TMTFrameCurves",
        "Breaker_TMTThermalTripAdj",
    }, f"reconciliation must cover all 5 TMT tables, got {recon_tables}"
    actual_deltas = {}
    for access_table, acc, tcc, delta in recon:
        assert acc is not None, f"{access_table}: access count must be non-NULL"
        assert tcc is not None, f"{access_table}: tcc count must be non-NULL"
        assert delta is not None, f"{access_table}: delta must be non-NULL"
        assert delta == acc - tcc, (
            f"{access_table}: delta {delta} != access {acc} - tcc {tcc} "
            "(internal inconsistency)"
        )
        actual_deltas[access_table] = (acc, tcc, delta)
    print(f"\n[F-79-03] tcc_count_reconciliation deltas: {actual_deltas}")

    # ------------------------------------------------------------------
    # 2. The amps anti-join enumerates a NON-EMPTY missing set AND is internally
    #    consistent.  (Numeric-normalised rating-value key -- a frame-FREE key;
    #    the frame-resolved key is deferred, see report.)
    # ------------------------------------------------------------------
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT method, missing_in_tcc_count, extra_in_tcc_count, "
            "jsonb_typeof(enumerated_missing), row_antijoin_not_applicable "
            "FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table='Breaker_TMTFrameAmps'",
            (run_id,),
        )
        amps = cur.fetchone()
    assert amps is not None, "amps anti-join row must exist"
    method, missing_ct, extra_ct, enum_type, not_applicable = amps
    assert not_applicable is False, "amps row-anti-join IS applicable"
    assert missing_ct is not None and missing_ct > 0, (
        "amps missing_in_tcc_count must be a non-empty positive count"
    )
    # Enumeration is bounded; the FULL count lives in missing_in_tcc_count.
    if method == "setdiff":
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT jsonb_array_length(enumerated_missing) "
                "FROM access_validation.antijoin_vs_tcc "
                "WHERE run_id=%s AND access_table='Breaker_TMTFrameAmps'",
                (run_id,),
            )
            (enum_len,) = cur.fetchone()
    else:  # multiset -> jsonb object keyed per distinct positive-delta key
        assert method == "multiset"
        assert enum_type == "object"
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM access_validation.antijoin_vs_tcc, "
                "jsonb_object_keys(enumerated_missing) "
                "WHERE run_id=%s AND access_table='Breaker_TMTFrameAmps'",
                (run_id,),
            )
            (enum_len,) = cur.fetchone()
    assert enum_len > 0, "amps enumerated_missing must be non-empty"
    assert enum_len <= _CAP, (
        f"amps enumeration {enum_len} exceeds cap {_CAP}"
    )
    # Internal consistency: the amps table-level delta (access - tcc) must equal
    # the anti-join net (missing - extra) -- the same +N shortfall by both paths.
    acc_a, tcc_a, delta_a = actual_deltas["Breaker_TMTFrameAmps"]
    assert (missing_ct - extra_ct) == delta_a, (
        f"amps anti-join net {missing_ct - extra_ct} != count delta {delta_a}"
    )
    print(
        f"[F-79-03] amps anti-join: method={method} missing={missing_ct} "
        f"extra={extra_ct} enumerated={enum_len} (net == count delta {delta_a})"
    )

    # ------------------------------------------------------------------
    # 3. curves + thermal_adj are COUNT-ONLY: row_antijoin_not_applicable=True,
    #    NO enumerated rows (no 1.1M EXCEPT).
    # ------------------------------------------------------------------
    for tbl in ("Breaker_TMTFrameCurves", "Breaker_TMTThermalTripAdj"):
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT method, row_antijoin_not_applicable, enumerated_missing "
                "FROM access_validation.antijoin_vs_tcc "
                "WHERE run_id=%s AND access_table=%s",
                (run_id, tbl),
            )
            row = cur.fetchone()
        assert row is not None, f"{tbl} anti-join row must exist"
        method_c, not_applicable_c, enumerated_c = row
        assert method_c == "count_only", f"{tbl} must be count_only"
        assert not_applicable_c is True, f"{tbl} row_antijoin_not_applicable must be True"
        assert enumerated_c is None, f"{tbl} must NOT enumerate rows (count-only)"

    # ------------------------------------------------------------------
    # 4. Style-mediated frame resolution: the AMBIGUITY is recorded as counts.
    #    The class is implicit; some StyleIDs span >=2 Access style classes.
    #    We assert the counts are internally consistent and the ambiguity is
    #    a recorded structural fact (>0).  We do NOT pick a class.
    # ------------------------------------------------------------------
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT distinct_styleid_count, resolved_single_class_count, "
            "ambiguous_multi_class_count, unresolved_no_class_count, "
            "mccb_only_count, iccb_only_count, pcb_only_count "
            "FROM access_validation.style_resolution WHERE run_id=%s",
            (run_id,),
        )
        sr = cur.fetchone()
    assert sr is not None, "style_resolution row must exist"
    (distinct, single, ambiguous, none, mccb, iccb, pcb) = sr
    # partition consistency: single + ambiguous + none == distinct.
    assert single + ambiguous + none == distinct, (
        f"style partition inconsistent: {single}+{ambiguous}+{none} != {distinct}"
    )
    # single-class tally == sum of the per-class only-counts.
    assert mccb + iccb + pcb == single, (
        f"per-class single tally {mccb}+{iccb}+{pcb} != single {single}"
    )
    assert ambiguous > 0, (
        "the implicit-class AMBIGUITY must be RECORDED as a positive count "
        "(it is itself F-79-03 evidence)"
    )
    print(
        f"[F-79-03] style_resolution: distinct={distinct} single={single} "
        f"AMBIGUOUS={ambiguous} no_class={none} "
        f"(mccb={mccb} iccb={iccb} pcb={pcb})"
    )

    # ------------------------------------------------------------------
    # 4'. The cleanly-keyable STYLE-PROVENANCE anti-join: one row per class,
    #     Access ID <-> tcc source_id (the one cross-instance key that does NOT
    #     route through the re-sequenced tmt_frames.id surrogate).
    # ------------------------------------------------------------------
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT breaker_class, access_id_count, tcc_source_id_count, "
            "missing_in_tcc_count, extra_in_tcc_count "
            "FROM access_validation.style_provenance_antijoin WHERE run_id=%s "
            "ORDER BY breaker_class",
            (run_id,),
        )
        prov = cur.fetchall()
    prov_classes = {r[0] for r in prov}
    assert prov_classes == {"MCCB", "ICCB", "PCB"}, (
        f"style-provenance anti-join must cover all 3 classes, got {prov_classes}"
    )
    prov_actual = {}
    for bc, acc_n, tcc_n, miss, extra in prov:
        assert acc_n is not None and tcc_n is not None
        assert miss is not None and extra is not None
        prov_actual[bc] = (acc_n, tcc_n, miss, extra)
    print(f"[F-79-03] style_provenance_antijoin: {prov_actual}")

    # ------------------------------------------------------------------
    # 5. Red-team guard: a surrogate -> tmt_frames.id keying RAISES.
    # ------------------------------------------------------------------
    pm = ProjectionMap.for_table("Breaker_TMTFrameSizes")
    with pytest.raises(ForbiddenKeyError):
        assert_key_allowed(pm, "Breaker_TMTFrameSizes.ID", "tmt_frames.id")
    with pytest.raises(ForbiddenKeyError):
        # the codebase's own schema-qualified spelling must also trip the guard.
        assert_key_allowed(
            pm, "Breaker_TMTFrameAmps.FrameSizeID", "tcc.tmt_frames.id"
        )

    # ------------------------------------------------------------------
    # 6. HR1: no interpretive columns in access_validation after the run.
    # ------------------------------------------------------------------
    violations = assert_no_interpretive_columns(pg_conn)
    assert violations == [], f"HR1 violation -- interpretive columns: {violations}"

    # ------------------------------------------------------------------
    # 7. Style-parent checksum + key_quality coverage (Task 3).
    #    Each of the 3 BreakerXXXStyles tables must carry a recorded checksum
    #    (load_state='checksummed'), a checksum_reconciliation row with
    #    matches=True, and a key_quality row after run_all.
    # ------------------------------------------------------------------
    _assert_style_parent_coverage(pg_conn, run_id)


# ---------------------------------------------------------------------------
# Skip-with-reason behaviour (no silent no-op).
# ---------------------------------------------------------------------------

def test_acceptance_skips_with_reason_when_prereqs_absent(monkeypatch):
    """With TCC_BREAKER_RO_PW forced absent, the HOST prereq probe yields a clear
    reason (so the acceptance SKIPS loudly for the host gap, never silently
    no-ops).

    We call the host-specific probe (_host_reason) DIRECTLY rather than
    _all_prereqs().  On a machine that is ALSO missing an earlier prerequisite
    (ACCESS_HARNESS_SUPERUSER_DSN or D:\\TCC_NEW.accdb), _all_prereqs() would
    short-circuit and return that earlier reason -- making this test assert the
    WRONG skip path.  _host_reason() proves the host-skip path regardless of
    other missing prerequisites (Codex P2 fix 4).
    """
    monkeypatch.delenv("TCC_BREAKER_RO_PW", raising=False)
    ok, reason = _host_reason()
    assert ok is False, "with TCC_BREAKER_RO_PW unset, the host prereq must be reported absent"
    assert reason and isinstance(reason, str), "skip reason must be non-empty"
    assert "TCC_BREAKER_RO_PW" in reason, (
        f"skip reason must name the missing prerequisite, got {reason!r}"
    )
