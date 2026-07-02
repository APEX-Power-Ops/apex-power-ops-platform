"""Migrated from the old direct-load test to the envelope flow.

Old `load_payload` is gone (approve_run is the sole domain writer). This keeps the
row-shape + re-approve idempotency coverage on the new path:
  create_run -> approve_run  (re-approve via a fresh run replaces in place).
"""
import psycopg

from ops_intake.envelope import create_run
from ops_intake.approve import approve_run


def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(
            "insert into ops.persons (display_name) values ('Lead') returning person_id"
        ).fetchone()[0]


def test_intake_materializes_expected_rows(mini_workbook, clean_ops, admin_dsn):
    dsn = clean_ops
    who = _person(admin_dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm",
                   raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    out = approve_run(dsn, r["run_id"], approved_by=who)
    assert out["outcome"] == "approved"
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.projects").fetchone()[0] == 1
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 1
        assert c.execute("select count(*) from ops.scope_quote_line").fetchone()[0] == 2
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 5  # 2 + 3 QTY-expanded
        (cv,) = c.execute("select contract_value from ops.projects").fetchone()
        assert float(cv) == 1000.0


def test_reapprove_is_full_replacement_not_growth(mini_workbook, clean_ops):
    """Re-materializing the same payload fully replaces -- row counts do not grow.

    (approve_run freezes, and a frozen quote is immutable by design, so the
    re-materialize idempotency is proved on the directly-unit-testable materialize.)
    """
    from ops_intake.approve import materialize
    from ops_intake.catalog import resolve_models
    from ops_intake.extract import extract_workbook
    import dataclasses

    dsn = clean_ops
    payload = dataclasses.asdict(extract_workbook(mini_workbook))
    pn = payload["project"]["project_number"]
    # collect all apparatus_type values from the payload to build the resolved map
    types = [line["apparatus_type"] for sc in payload.get("scopes", []) or []
             for line in (sc.get("lines", []) or []) if line.get("apparatus_type")]
    with psycopg.connect(dsn) as c:
        resolved = resolve_models(c.cursor(), types)
        materialize(c, pn, payload, resolved); c.commit()
        a1 = c.execute("select count(*) from ops.apparatus").fetchone()[0]
        materialize(c, pn, payload, resolved); c.commit()
        a2 = c.execute("select count(*) from ops.apparatus").fetchone()[0]
        assert a1 == 5 and a2 == 5
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 1
        assert c.execute("select count(*) from ops.scope_quote_line").fetchone()[0] == 2
