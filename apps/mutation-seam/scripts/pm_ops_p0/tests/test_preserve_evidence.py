"""Offline tests for pm_ops_p0.preserve_evidence.

No database is contacted. Every refusal path is exercised BEFORE any connect,
so feeding an unbound DSN is safe. Custody permissions, the SHA-256 manifest,
argument parsing, value-silence, and SQL parity are all checked offline.

Runnable under pytest OR directly:  python tests/test_preserve_evidence.py
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pm_ops_p0.preserve_evidence as pe  # noqa: E402

REF = "fxoyniqnrlkxfligbxmg"


def _run_main(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pe.main(argv)
    return rc, buf.getvalue()


# ----------------------------------------------------------------- arg parsing


def test_parser_requires_expect_project_ref():
    try:
        pe.build_parser().parse_args(["--dsn-env", "SOME_VAR"])
    except SystemExit as exc:
        assert exc.code != 0
    else:  # pragma: no cover
        raise AssertionError("--expect-project-ref must be required")


def test_parser_requires_dsn_env():
    try:
        pe.build_parser().parse_args(["--expect-project-ref", REF])
    except SystemExit as exc:
        assert exc.code != 0
    else:  # pragma: no cover
        raise AssertionError("--dsn-env must be required")


# --------------------------------------------------------------- refusal paths


def test_main_refuses_unexpected_project_ref():
    rc, out = _run_main(
        ["--expect-project-ref", "someotherproject", "--dsn-env", "UNSET_X"]
    )
    assert rc != 0
    assert "unexpected_project_ref" in out
    assert "RESULT FAIL" in out


def test_main_refuses_unset_dsn_env():
    os.environ.pop("PM_OPS_P0_TEST_DSN", None)
    rc, out = _run_main(
        ["--expect-project-ref", REF, "--dsn-env", "PM_OPS_P0_TEST_DSN"]
    )
    assert rc != 0
    assert "dsn_unset" in out


def test_main_refuses_unbound_dsn_value_silently():
    secret_host = "evil.attacker.example"
    secret_pw = "SuperSecretPw999"
    os.environ["PM_OPS_P0_TEST_DSN"] = (
        f"host={secret_host} user=sneaky password={secret_pw} dbname=postgres"
    )
    try:
        rc, out = _run_main(
            ["--expect-project-ref", REF, "--dsn-env", "PM_OPS_P0_TEST_DSN"]
        )
    finally:
        os.environ.pop("PM_OPS_P0_TEST_DSN", None)
    assert rc != 0
    # bind_target rejects BEFORE any connect; the DSN never leaks
    assert secret_host not in out
    assert secret_pw not in out
    assert "sneaky" not in out
    assert "not_bound" in out  # a stable bind reject code


# -------------------------------------------------------------------- custody


def test_write_custody_permissions_and_manifest():
    base = Path(tempfile.mkdtemp(prefix="p0a-custody-"))
    try:
        artifacts = {
            "acl.txt": "projects rls=false\n",
            "counts.json": '{"projects": 0}\n',
        }
        run_dir = pe.write_custody(base, artifacts, clock="2026-07-14T00-00-00Z")
        assert run_dir.parent == base
        # run dir is 0700
        assert stat.S_IMODE(run_dir.stat().st_mode) == 0o700
        manifest = run_dir / pe.MANIFEST_NAME
        assert manifest.exists()
        manifest_text = manifest.read_text()
        for name, content in artifacts.items():
            f = run_dir / name
            assert f.exists()
            # each artifact file is 0400
            assert stat.S_IMODE(f.stat().st_mode) == 0o400
            digest = hashlib.sha256(content.encode()).hexdigest()
            assert digest in manifest_text
            assert name in manifest_text
        # manifest itself is 0400
        assert stat.S_IMODE(manifest.stat().st_mode) == 0o400
    finally:
        # restore write perms so cleanup can remove 0400 files
        for p in base.rglob("*"):
            with contextlib.suppress(OSError):
                p.chmod(0o600)
        shutil.rmtree(base, ignore_errors=True)


def test_write_custody_no_clobber():
    base = Path(tempfile.mkdtemp(prefix="p0a-custody-"))
    try:
        pe.write_custody(base, {"a.txt": "x\n"}, clock="2026-07-14T00-00-00Z")
        raised = False
        try:
            pe.write_custody(base, {"a.txt": "y\n"}, clock="2026-07-14T00-00-00Z")
        except FileExistsError:
            raised = True
        assert raised, "custody must not clobber an existing run directory"
    finally:
        for p in base.rglob("*"):
            with contextlib.suppress(OSError):
                p.chmod(0o600)
        shutil.rmtree(base, ignore_errors=True)


# ------------------------------------------------------------------ SQL parity


def test_p0a_sql_is_guarded_read_only():
    sql = pe.p0a_sql_text()
    assert "REPEATABLE READ, READ ONLY" in sql
    assert "transaction_read_only" in sql
    assert "P0-A refused" in sql  # the fail-closed guard raises
    for tbl in ("projects", "scopes", "tasks", "apparatus"):
        assert f"public.{tbl}" in sql
    assert "approve_apparatus_completion" in sql  # RPC fingerprint
    assert sql.strip().endswith("COMMIT;") or "\nCOMMIT;" in sql


def test_p0a_sql_effective_privilege_principal_set():
    sql = pe.p0a_sql_text()
    assert "has_table_privilege" in sql
    for principal in ("anon", "authenticated", "public", "apex_tcc_runtime"):
        assert f"'{principal}'" in sql
    for priv in (
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "TRUNCATE",
        "REFERENCES",
        "TRIGGER",
        "MAINTAIN",
    ):
        assert f"'{priv}'" in sql


def test_p0a_sql_secdef_fail_closed_or_of_three():
    sql = pe.p0a_sql_text()
    assert "prosecdef" in sql
    assert "depends_on_targets" in sql
    assert "name_refs_targets" in sql
    assert "has_dynamic_sql" in sql
    assert "in_scope_failclosed" in sql


def test_p0a_sql_default_acl_tables_and_functions():
    sql = pe.p0a_sql_text()
    assert "pg_default_acl" in sql
    assert "'r'" in sql and "'f'" in sql  # both objtypes


# --------------------------------------------- live-path choreography (mocked)


class _FakeCursor:
    def __init__(self, recorder):
        self._recorder = recorder
        self.description = None

    def execute(self, sql):
        self._recorder.append(sql)

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def __init__(self, host, user, recorder):
        self.info = type("Info", (), {"host": host, "user": user, "hostaddr": ""})()
        self._recorder = recorder

    def cursor(self):
        return _FakeCursor(self._recorder)

    def close(self):
        pass


def test_collect_evidence_choreography_and_env_scrub():
    import pm_ops_p0.binding as binding
    import psycopg

    recorder: list[str] = []
    env_at_connect: dict[str, object] = {}

    def fake_connect(**kwargs):
        for k in binding.PG_ENV_OVERRIDES:
            env_at_connect[k] = os.environ.get(k)
        return _FakeConn(kwargs["host"], kwargs["user"], recorder)

    orig = psycopg.connect
    psycopg.connect = fake_connect
    os.environ["PGHOST"] = "leak.example"
    try:
        dsn = f"host=db.{REF}.supabase.co user=postgres password=pw dbname=postgres"
        artifacts = pe.collect_evidence(dsn, REF)
    finally:
        psycopg.connect = orig
        os.environ.pop("PGHOST", None)

    # exact guarded read-only choreography
    expected = (
        [pe._BEGIN, pe._GUARD] + [sql for _, sql in pe._EVIDENCE_STEPS] + [pe._COMMIT]
    )
    assert recorder == expected
    # PG* overrides were scrubbed at the moment of connect
    assert env_at_connect.get("PGHOST") is None
    assert "00_p0a_snapshot.sql" in artifacts


def test_collect_evidence_rejects_wrong_host_before_any_query():
    import psycopg

    recorder: list[str] = []

    def fake_connect(**kwargs):
        return _FakeConn("evil.attacker.example", "postgres", recorder)

    orig = psycopg.connect
    psycopg.connect = fake_connect
    try:
        raised = False
        try:
            pe.collect_evidence(
                f"host=db.{REF}.supabase.co user=postgres dbname=postgres", REF
            )
        except pe.TargetBindingError as exc:
            raised = True
            assert exc.code == "connection_host_mismatch", exc.code
    finally:
        psycopg.connect = orig
    assert raised
    assert recorder == []  # the post-connect re-check gates BEFORE any query runs


def test_main_value_silent_when_collection_raises():
    import logging

    sentinel = "leaky-host-9.9.9.9.internal"

    def boom(dsn, expect_ref):
        raise RuntimeError(f"could not connect to {sentinel}:5432")

    records: list[str] = []

    class _Cap(logging.Handler):
        def emit(self, record):
            records.append(self.format(record))

    handler = _Cap()
    handler.setFormatter(logging.Formatter("%(message)s"))
    orig_collect = pe.collect_evidence
    pe.collect_evidence = boom
    pe.log.addHandler(handler)
    pe.log.setLevel(logging.DEBUG)
    os.environ["PM_OPS_P0_TEST_DSN"] = "host=whatever user=x dbname=postgres"
    try:
        rc, out = _run_main(
            ["--expect-project-ref", REF, "--dsn-env", "PM_OPS_P0_TEST_DSN"]
        )
    finally:
        pe.collect_evidence = orig_collect
        pe.log.removeHandler(handler)
        os.environ.pop("PM_OPS_P0_TEST_DSN", None)
    assert rc != 0
    assert "connection_or_query_failed" in out
    # the raw driver message (which can carry host/IP) never reaches stdout or logs
    assert sentinel not in out
    assert all(sentinel not in m for m in records)


# ------------------------------------------------------------------- runner


def _run() -> int:
    funcs = [
        v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)
    ]
    failures = 0
    for fn in funcs:
        try:
            fn()
            print(f"[PASS] {fn.__name__}")
        except Exception as exc:  # noqa: BLE001 - test runner
            failures += 1
            print(f"[FAIL] {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(funcs) - failures}/{len(funcs)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
