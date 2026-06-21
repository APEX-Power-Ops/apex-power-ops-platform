import json

import psycopg

from ops_intake.cli import main


def test_cli_extract(mini_workbook, tmp_path):
    out = tmp_path / "p.json"
    rc = main(["extract", str(mini_workbook), "--out", str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["project"]["contract_value"] == 1000.0
    assert len(data["scopes"]) == 1
    assert data["scopes"][0]["scope_name"] == "A1) MV - Test"


def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(
            "insert into ops.persons (display_name) values (%s) returning person_id",
            ("CLI-PM",),
        ).fetchone()[0]


def test_cli_intake(mini_workbook, clean_ops):
    dsn = clean_ops
    who = _person(dsn)
    rc = main(["intake", str(mini_workbook), "--dsn", dsn, "--uploaded-by", str(who)])
    assert rc == 0
    with psycopg.connect(dsn) as c:
        row = c.execute(
            "select status from ops.intake_runs order by created_at desc limit 1"
        ).fetchone()
    assert row is not None
    assert row[0] == "parsed"
