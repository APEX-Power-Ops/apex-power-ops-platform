"""End-to-end on the NEW envelope path: create_run -> approve_run on the real Rev10
estimator, then reconcile. Skips unless MINER_WORKBOOK is set (real_workbook fixture).

Migrated from the old direct-load e2e: the catalog assertion is now NEGATIVE --
intake leaves ops.standard_hours empty (D4: the catalog is a seed, never written by
intake).
"""
import psycopg

from ops_intake.envelope import create_run
from ops_intake.approve import approve_run


def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(
            "insert into ops.persons (display_name) values ('Lead') returning person_id"
        ).fetchone()[0]


def test_e2e_miner_full_load(real_workbook, clean_ops, admin_dsn):
    dsn = clean_ops
    who = _person(admin_dsn)
    r = create_run(dsn, uploaded_by=who, filename="rev10.xlsm",
                   raw_bytes=real_workbook.read_bytes(), content_type="xlsm")
    out = approve_run(dsn, r["run_id"], approved_by=who)
    assert out["outcome"] == "approved"
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 9  # 7 MV + 2 chiller
        nlines = c.execute("select count(*) from ops.scope_quote_line").fetchone()[0]
        napp = c.execute("select count(*) from ops.apparatus").fetchone()[0]
        assert nlines >= 100  # ~118 valid apparatus lines in Rev10
        assert napp >= 2 * nlines  # QTY-expansion happened
        (cv,) = c.execute("select contract_value from ops.projects").fetchone()
        assert abs(float(cv) - 4692078.98) < 1.0
        # Sum apparatus quoted_revenue (frozen) == Sum MV-scope adjusted_total (P4); chillers excluded.
        (mv_p4,) = c.execute(
            "select round(coalesce(sum(adjusted_total), 0), 2) from ops.scope_quote "
            "where provenance_status <> 'estimate'"
        ).fetchone()
        (app_rev,) = c.execute(
            "select round(coalesce(sum(quoted_revenue), 0), 2) from ops.apparatus"
        ).fetchone()
        assert abs(float(app_rev) - float(mv_p4)) < 10.0, (app_rev, mv_p4)  # cumulative cent-rounding
    # Codex-P2b: standard_hours - D4 "no catalog write" - the writer holds NO grant on this
    # table at all (spec S5: dropped over-grant), so this verification read runs as admin,
    # not the writer (mirrors test_approve_envelope.py's test_approve_materializes_tasks_and_freezes).
    with psycopg.connect(admin_dsn) as c:
        assert c.execute("select count(*) from ops.standard_hours").fetchone()[0] == 0  # D4: no catalog write
