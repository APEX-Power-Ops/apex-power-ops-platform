import hashlib
import psycopg
from ops_intake.envelope import create_run, get_run


def _bytes(mini_workbook):
    return mini_workbook.read_bytes()


def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(
            "insert into ops.persons (display_name) values (%s) returning person_id",
            ("PM",),
        ).fetchone()[0]


def test_create_run_persists_envelope_only(mini_workbook, clean_ops):
    dsn = clean_ops
    who = _person(dsn)
    out = create_run(
        dsn,
        uploaded_by=who,
        filename="mini.xlsm",
        raw_bytes=_bytes(mini_workbook),
        content_type="xlsm",
    )
    assert out["status"] == "parsed" and out["conflict_kind"] == "none"
    assert out["source_format"] == "decomposed_scope_sheet"
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.intake_runs").fetchone()[0] == 1
        assert c.execute("select count(*) from ops.intake_source_files").fetchone()[0] == 1
        for t in ("projects", "scopes", "tasks", "apparatus", "scope_quote", "scope_quote_line"):
            assert c.execute(
                "select count(*) from ops.{}".format(t)
            ).fetchone()[0] == 0, t
        (sha,) = c.execute("select sha256 from ops.intake_source_files").fetchone()
        assert sha == hashlib.sha256(_bytes(mini_workbook)).hexdigest()


def test_second_active_upload_supersedes(mini_workbook, clean_ops):
    dsn = clean_ops
    who = _person(dsn)
    r1 = create_run(
        dsn,
        uploaded_by=who,
        filename="m.xlsm",
        raw_bytes=_bytes(mini_workbook),
        content_type="xlsm",
    )
    r2 = create_run(
        dsn,
        uploaded_by=who,
        filename="m.xlsm",
        raw_bytes=_bytes(mini_workbook),
        content_type="xlsm",
    )
    with psycopg.connect(dsn) as c:
        assert (
            c.execute(
                "select status from ops.intake_runs where id=%s", (r1["run_id"],)
            ).fetchone()[0]
            == "superseded"
        )
        assert (
            c.execute(
                "select status from ops.intake_runs where id=%s", (r2["run_id"],)
            ).fetchone()[0]
            == "parsed"
        )


def test_dsn_guard_blocks_non_ops_test():
    import pytest
    from conftest import _require_ops_test

    with pytest.raises(AssertionError):
        _require_ops_test(
            "host=127.0.0.1 port=5432 dbname=ops_dev user=postgres sslmode=disable"
        )