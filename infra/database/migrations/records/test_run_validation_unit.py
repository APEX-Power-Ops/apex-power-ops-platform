"""Unit tests for run_validation pure functions. No database required.
No 3-digit prefix => excluded from the migration walk by construction."""
import os
import re

import pytest

import run_validation as rv


def _mk(tmp_path, names):
    for n in names:
        (tmp_path / n).write_text("-- x", encoding="utf-8")
    return str(tmp_path)


def test_enumerate_stack_happy(tmp_path):
    d = _mk(tmp_path, [
        "001_a.sql", "001_a_down.sql", "002_b.sql", "003_c.sql",
        "test_001_a.py", "test_003_c.py", "test__helper.py", "conftest.py",
    ])
    migs, tests = rv.enumerate_stack(d)
    assert migs == [(1, "001_a.sql"), (2, "002_b.sql"), (3, "003_c.sql")]
    assert tests == {1: "test_001_a.py", 3: "test_003_c.py"}


def test_enumerate_stack_gap_fails(tmp_path):
    d = _mk(tmp_path, ["001_a.sql", "003_c.sql"])
    with pytest.raises(rv.HarnessError, match="gap"):
        rv.enumerate_stack(d)


def test_enumerate_stack_orphan_test_fails(tmp_path):
    d = _mk(tmp_path, ["001_a.sql", "test_002_ghost.py"])
    with pytest.raises(rv.HarnessError, match="orphan"):
        rv.enumerate_stack(d)


def test_derive_child_dsn_swaps_only_dbname():
    child = rv.derive_child_dsn(
        "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=x sslmode=disable",
        "records_val_x",
    )
    assert "dbname=records_val_x" in child
    assert "host=127.0.0.1" in child and "user=postgres" in child
    assert "password=x" in child and "dbname=postgres" not in child


def test_enumerate_stack_missing_first_fails(tmp_path):
    d = _mk(tmp_path, ["002_b.sql", "003_c.sql"])
    with pytest.raises(rv.HarnessError, match="start at 001"):
        rv.enumerate_stack(d)


def test_derive_child_dsn_ignores_dbname_inside_password():
    child = rv.derive_child_dsn(
        "host=h port=1 dbname=postgres user=u password=xdbname=evil", "records_val_x"
    )
    assert "dbname=records_val_x" in child
    assert "password=xdbname=evil" in child


def test_check_admin_dsn_requires_postgres_db():
    rv.check_admin_dsn("host=h port=1 dbname=postgres user=u")
    with pytest.raises(rv.HarnessError, match="maintenance"):
        rv.check_admin_dsn("host=h port=1 dbname=records_dev user=u")
    with pytest.raises(rv.HarnessError, match="maintenance"):
        rv.check_admin_dsn("host=h port=1 dbname=ops_dev user=u")


def test_val_name_shape_and_assert():
    n = rv.make_val_name()
    assert re.fullmatch(r"records_val_\d{8}T\d{6}_\d+", n)
    rv.assert_val_name(n)
    for bad in ("records_dev", "postgres", "records_val", "x_records_val_1"):
        with pytest.raises(rv.HarnessError):
            rv.assert_val_name(bad)


def test_parse_tiers_default_and_valid():
    assert rv.parse_tiers("") == {0, 1, 2, 3, 4, 5, 6, 7}
    assert rv.parse_tiers("3,4") == {3, 4}
    assert rv.parse_tiers("5") == {5}
    assert rv.parse_tiers("3,5") == {3, 5}
    assert rv.parse_tiers("6") == {6}
    assert rv.parse_tiers("7") == {7}
    assert rv.parse_tiers("5,6") == {5, 6}
    assert rv.parse_tiers("0,1,2,3,4,5,6,7") == {0, 1, 2, 3, 4, 5, 6, 7}


def test_parse_tiers_rejects_unknown():
    with pytest.raises(rv.HarnessError, match="valid: 0-7"):
        rv.parse_tiers("9")
    with pytest.raises(rv.HarnessError, match="valid: 0-7"):
        rv.parse_tiers("8")
    with pytest.raises(rv.HarnessError, match="tiers 0-7"):
        rv.parse_tiers("x")


def test_summary_formats_all_statuses():
    tiers = [rv.Tier("0-syntax", "PASS", ""), rv.Tier("3-migrations", "FAIL", "boom"),
             rv.Tier("4-import-db", "SKIP", "tier 3 failed")]
    out = rv.summary(tiers)
    assert "0-syntax" in out and "PASS" in out and "FAIL" in out and "SKIP" in out


# snapshot_roles default must track all NINE cluster-level roles the harness may
# create: the 6 Gate-5 roles (walk-created records_owner/records_fn_owner/records_auditor
# + records_reclaim_owner from 046 leak past a disposable-DB drop) PLUS the 3 Data-API
# stubs tier7 creates (anon/authenticated/service_role). The finally-block drops exactly
# the roles absent pre-run; drop-if-exists no-ops on any stub tier7 did not create, so
# tracking all 9 is safe for tiers 0-6 (Codex P2-1; Gate 9 F2; whole-branch fix D).
GATE5_ROLES = (
    "records_api", "records_intake_writer",
    "records_owner", "records_fn_owner", "records_auditor",
    "records_reclaim_owner",
)
DATA_API_STUBS = ("anon", "authenticated", "service_role")
ALL_TRACKED_ROLES = GATE5_ROLES + DATA_API_STUBS


def test_snapshot_roles_default_tracks_all_nine():
    import inspect
    default = inspect.signature(rv.snapshot_roles).parameters["names"].default
    assert tuple(default) == ALL_TRACKED_ROLES


class _FakeConn:
    """Minimal _connect() stand-in: a context manager whose execute() returns an
    object with .fetchall(), echoing the pg_roles rows we seed. No database."""

    def __init__(self, present):
        self._present = present  # role names that already exist pre-run

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params):
        names = params[0]
        rows = [(n,) for n in names if n in self._present]
        return _FakeResult(rows)


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


def test_snapshot_roles_returns_absent_owner_auditor(monkeypatch):
    # The 2 app roles + 3 Data-API stubs pre-exist; only the 4 owner/auditor/reclaim roles
    # are absent -> snapshot_roles must return exactly those four, in names order (the ones
    # the walk creates and the finally-block must drop).
    present = {"records_api", "records_intake_writer", "anon", "authenticated", "service_role"}
    monkeypatch.setattr(rv, "_connect", lambda admin: _FakeConn(present))
    created = rv.snapshot_roles("host=h port=1 dbname=postgres user=u")
    assert created == ["records_owner", "records_fn_owner", "records_auditor", "records_reclaim_owner"]


def test_snapshot_roles_none_absent_returns_empty(monkeypatch):
    # All nine already exist pre-run -> nothing was created this run -> drop nothing.
    monkeypatch.setattr(rv, "_connect", lambda admin: _FakeConn(set(ALL_TRACKED_ROLES)))
    assert rv.snapshot_roles("host=h port=1 dbname=postgres user=u") == []


# --- Phase 1 (Supabase-compat): --apply-as-non-superuser local approximation -----
# PURE surface only (no DB). The behavioral proof that the applier reaches 045's
# `alter role` and fails 42501 lives in the DB-backed red-proof
# (test_supabase_compat_redproof.py). This mode APPROXIMATES Supabase managed
# `postgres` on a true-superuser local Postgres; it is NOT a Supabase-compat proof
# - Phase 0 (a real Supabase branch) is the fidelity authority.
ADMIN_DSN = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=x sslmode=disable"


def test_parse_args_apply_as_non_superuser_flag():
    assert rv.parse_args(["--apply-as-non-superuser"]).apply_as_non_superuser is True
    assert rv.parse_args([]).apply_as_non_superuser is False


def test_local_applier_envelope_mirrors_branch_observed_managed_postgres():
    # Phase-0-confirmed envelope (PHASE0-FINDINGS A2): the powerful-but-non-super admin
    # identity managed postgres actually is - non-super (superuser stays unsettable) plus
    # createrole + createdb + bypassrls + replication. Phase 2 needs the applier to HOLD
    # these so it can SET the app roles' NO forms (PG16+ requires holding an attr to set
    # its NO form on another role); only superuser stays False, preserving the 045
    # nosuperuser red-proof.
    env = rv.LOCAL_APPLIER_ENVELOPE
    assert env["superuser"] is False
    assert env["login"] is True
    assert env["createrole"] is True
    assert env["bypassrls"] is True
    assert env["replication"] is True
    assert env["createdb"] is True


def test_make_local_applier_returns_non_super_applier_dsn():
    res = rv.make_local_applier(ADMIN_DSN, rv.LOCAL_APPLIER_ENVELOPE)
    # a run-generated disposable applier role, NOT the superuser admin
    assert re.fullmatch(r"records_val_applier_\d{8}T\d{6}_\d+", res.role)
    rv.assert_applier_name(res.role)
    # DSN authenticates AS the applier (not postgres); host/port/dbname preserved
    assert f"user={res.role}" in res.dsn
    assert "user=postgres" not in res.dsn
    assert "host=127.0.0.1" in res.dsn and "dbname=postgres" in res.dsn
    # reuse the admin password token (never a fresh secret): applier auths cleanly
    assert "password=x" in res.dsn
    # DDL proves NON-superuser (the load-bearing constraint) AND reflects the branch-observed
    # envelope verbatim: createrole/createdb/bypassrls/replication HELD (so the applier can set
    # the app roles' NO forms), superuser NOT.
    cs = res.create_sql.lower()
    assert "nosuperuser" in cs
    assert "createrole" in cs and "nocreaterole" not in cs
    assert "createdb" in cs and "nocreatedb" not in cs
    assert "bypassrls" in cs and "nobypassrls" not in cs
    assert "replication" in cs and "noreplication" not in cs
    assert " login " in cs and "nologin" not in cs
    assert res.role in res.drop_sql and "drop role" in res.drop_sql.lower()


def test_assert_applier_name_rejects_foreign_names():
    rv.assert_applier_name(rv.make_local_applier(ADMIN_DSN, rv.LOCAL_APPLIER_ENVELOPE).role)
    for bad in ("postgres", "records_val_x", "records_api", "records_val_applier",
                "records_val_20260101T000000_1", "x_records_val_applier_20260101T000000_1"):
        with pytest.raises(rv.HarnessError):
            rv.assert_applier_name(bad)


def test_redacted_dsn_masks_password_keyword_form():
    real = "host=h password=FAKESECRET123 dbname=d"
    x = rv.RedactedDsn(real)
    # repr() is what pytest renders in a failing fixture's traceback - must be masked.
    assert "FAKESECRET123" not in repr(x)
    assert "***" in repr(x)
    # str() is what psycopg actually consumes to connect - must be the real, unmasked value.
    assert str(x) == real


def test_redacted_dsn_masks_password_uri_form():
    real = "postgresql://u:FAKESECRET123@h:5432/d"
    x = rv.RedactedDsn(real)
    assert "FAKESECRET123" not in repr(x)
    assert "***" in repr(x)
    assert str(x) == real


def test_redacted_dsn_is_str_subclass_usable_as_dsn():
    real = "host=h password=FAKESECRET123 dbname=d"
    x = rv.RedactedDsn(real)
    assert isinstance(x, str)
    # a bare str() equality / concatenation still behaves like a normal string
    assert x == real
    assert (x + "").startswith("host=h")
