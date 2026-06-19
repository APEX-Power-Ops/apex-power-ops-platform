"""End-to-end: load the real Rev10 estimator into ops_dev and reconcile. Skips unless MINER_WORKBOOK set."""
import psycopg

from ops_intake.extract import extract_workbook
from ops_intake.load import load_payload


def test_e2e_miner_full_load(real_workbook, clean_ops):
    dsn = clean_ops
    p = extract_workbook(real_workbook)
    res = load_payload(p, dsn, approve=True)
    assert res.projects == 1
    assert res.scopes == 9  # 7 MV + 2 chiller
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 9
        nlines = c.execute("select count(*) from ops.scope_quote_line").fetchone()[0]
        napp = c.execute("select count(*) from ops.apparatus").fetchone()[0]
        assert nlines >= 100  # ~118 valid apparatus lines in Rev10 (reconciliation is the real invariant)
        assert napp >= 2 * nlines  # QTY-expansion happened
        assert c.execute("select count(*) from ops.standard_hours").fetchone()[0] >= 20  # catalog loaded
        (cv,) = c.execute("select contract_value from ops.projects").fetchone()
        assert abs(float(cv) - 4692078.98) < 1.0
        # Σ apparatus quoted_revenue (frozen) == Σ MV-scope adjusted_total (P4); chillers excluded (no apparatus)
        (mv_p4,) = c.execute(
            "select round(coalesce(sum(adjusted_total), 0), 2) from ops.scope_quote "
            "where provenance_status <> 'estimate'"
        ).fetchone()
        (app_rev,) = c.execute(
            "select round(coalesce(sum(quoted_revenue), 0), 2) from ops.apparatus"
        ).fetchone()
        assert abs(float(app_rev) - float(mv_p4)) < 10.0, (app_rev, mv_p4)  # cumulative cent-rounding
    # idempotent: a second approve-load changes no apparatus count
    load_payload(p, dsn, approve=True)
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == napp
