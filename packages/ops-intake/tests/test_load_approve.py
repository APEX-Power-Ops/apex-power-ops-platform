import psycopg

from ops_intake.extract import extract_workbook
from ops_intake.load import load_payload


def test_approve_freezes(mini_workbook, clean_ops):
    dsn = clean_ops
    load_payload(extract_workbook(mini_workbook), dsn, approve=True)
    with psycopg.connect(dsn) as c:
        # 5 apparatus x 5h x blended_rate(1000/25=40) = 1000 == scope P4
        rev = c.execute("select coalesce(sum(quoted_revenue), 0) from ops.apparatus").fetchone()[0]
        assert abs(float(rev) - 1000.0) < 0.5
        assert c.execute("select bool_and(is_frozen) from ops.scope_quote").fetchone()[0] is True
        # every apparatus row carries a frozen revenue + approved provenance
        nulls = c.execute("select count(*) from ops.apparatus where quoted_revenue is null").fetchone()[0]
        assert nulls == 0
