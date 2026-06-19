import psycopg

from ops_intake.extract import extract_workbook
from ops_intake.load import load_payload


def test_load_then_idempotent(mini_workbook, clean_ops):  # clean_ops (conftest) truncates + returns dsn
    p = extract_workbook(mini_workbook)
    r1 = load_payload(p, clean_ops)
    assert r1.projects == 1 and r1.scopes == 1 and r1.lines == 2 and r1.apparatus == 5  # 2 + 3 QTY-expanded
    with psycopg.connect(clean_ops) as c:
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 5
        assert c.execute("select count(*) from ops.scope_quote_line").fetchone()[0] == 2
        (cv,) = c.execute("select contract_value from ops.projects").fetchone()
        assert float(cv) == 1000.0
    # idempotent: re-loading the same payload changes no row counts
    load_payload(p, clean_ops)
    with psycopg.connect(clean_ops) as c:
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 5
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 1
