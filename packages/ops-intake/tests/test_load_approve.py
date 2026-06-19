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


def test_approve_is_scoped_to_its_project(mini_workbook, clean_ops):
    """A second, unrelated project in the same DB must be untouched by this project's approve."""
    dsn = clean_ops
    with psycopg.connect(dsn, autocommit=True) as c:
        pid = c.execute(
            "insert into ops.projects (project_number, project_name) values ('OTHER-1','Other') returning id"
        ).fetchone()[0]
        sid = c.execute(
            "insert into ops.scopes (project_id, scope_name) values (%s,'Other Scope') returning id", (pid,)
        ).fetchone()[0]
        c.execute("insert into ops.scope_quote (scope_id, onsite_labor, total_quoted_hours) values (%s,500,10)", (sid,))
        c.execute("insert into ops.apparatus (scope_id, apparatus_designation, quoted_hours) values (%s,'X',5)", (sid,))

    load_payload(extract_workbook(mini_workbook), dsn, approve=True)  # approves MINER-PHX-AB-MV only

    with psycopg.connect(dsn) as c:
        frozen = c.execute(
            "select bool_or(sq.is_frozen) from ops.scope_quote sq join ops.scopes s on s.id=sq.scope_id "
            "join ops.projects p on p.id=s.project_id where p.project_number='OTHER-1'"
        ).fetchone()[0]
        assert frozen is False  # the other project was NOT frozen
        rev = c.execute(
            "select a.quoted_revenue from ops.apparatus a join ops.scopes s on s.id=a.scope_id "
            "join ops.projects p on p.id=s.project_id where p.project_number='OTHER-1'"
        ).fetchone()[0]
        assert rev is None  # the other project's apparatus revenue was NOT stamped
