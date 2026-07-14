"""Offline tests for pm_ops_p0.preserve_evidence.

No database is contacted. Every refusal path is exercised BEFORE any connect,
so feeding an unbound DSN is safe. Governance provenance, custody permissions +
atomic publish, the SHA-256 manifest, argument parsing, value-silence, the DB
role guard, and SQL parity are all checked offline (git + live connect are stubbed).

Runnable under pytest OR directly:  python tests/test_preserve_evidence.py
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pm_ops_p0.preserve_evidence as pe  # noqa: E402

REF = "fxoyniqnrlkxfligbxmg"
SHA = "0123456789abcdef0123456789abcdef01234567"
CLOCK = "2026-07-14T00-00-00Z"


def _run_main(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pe.main(argv)
    return rc, buf.getvalue()


@contextlib.contextmanager
def _patched_repo(sha=SHA, clean=True, on_main=True):
    """Inject a controlled git state so main()'s governance gate is offline-testable."""
    orig_root, orig_state = pe._repo_root, pe._repo_git_state
    pe._repo_root = lambda: Path("/fake/repo")
    pe._repo_git_state = lambda root: (sha, clean, on_main)
    try:
        yield sha
    finally:
        pe._repo_root, pe._repo_git_state = orig_root, orig_state


# ----------------------------------------------------------------- arg parsing


def test_parser_requires_expect_project_ref():
    try:
        pe.build_parser().parse_args(["--dsn-env", "V", "--expect-repo-sha", SHA])
    except SystemExit as exc:
        assert exc.code != 0
    else:  # pragma: no cover
        raise AssertionError("--expect-project-ref must be required")


def test_parser_requires_dsn_env():
    try:
        pe.build_parser().parse_args(
            ["--expect-project-ref", REF, "--expect-repo-sha", SHA]
        )
    except SystemExit as exc:
        assert exc.code != 0
    else:  # pragma: no cover
        raise AssertionError("--dsn-env must be required")


def test_parser_requires_expect_repo_sha():
    try:
        pe.build_parser().parse_args(["--expect-project-ref", REF, "--dsn-env", "V"])
    except SystemExit as exc:
        assert exc.code != 0
    else:  # pragma: no cover
        raise AssertionError("--expect-repo-sha must be required")


# --------------------------------------------------------------- refusal paths


def test_main_refuses_unexpected_project_ref():
    # ref check precedes the repo gate, so no repo patch is needed
    rc, out = _run_main(
        [
            "--expect-project-ref",
            "someotherproject",
            "--dsn-env",
            "UNSET_X",
            "--expect-repo-sha",
            SHA,
        ]
    )
    assert rc != 0
    assert "unexpected_project_ref" in out
    assert "RESULT FAIL" in out


def test_main_refuses_unset_dsn_env():
    os.environ.pop("PM_OPS_P0_TEST_DSN", None)
    rc, out = _run_main(
        [
            "--expect-project-ref",
            REF,
            "--dsn-env",
            "PM_OPS_P0_TEST_DSN",
            "--expect-repo-sha",
            SHA,
        ]
    )
    assert rc != 0
    assert "dsn_unset" in out


def test_main_refuses_repo_dirty():
    os.environ["PM_OPS_P0_TEST_DSN"] = (
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres"
    )
    try:
        with _patched_repo(clean=False):
            rc, out = _run_main(
                [
                    "--expect-project-ref",
                    REF,
                    "--dsn-env",
                    "PM_OPS_P0_TEST_DSN",
                    "--expect-repo-sha",
                    SHA,
                ]
            )
    finally:
        os.environ.pop("PM_OPS_P0_TEST_DSN", None)
    assert rc != 0
    assert "repo_dirty" in out


def test_main_refuses_repo_sha_mismatch():
    os.environ["PM_OPS_P0_TEST_DSN"] = (
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres"
    )
    try:
        with _patched_repo(sha="aaaa1111"):
            rc, out = _run_main(
                [
                    "--expect-project-ref",
                    REF,
                    "--dsn-env",
                    "PM_OPS_P0_TEST_DSN",
                    "--expect-repo-sha",
                    "bbbb2222",
                ]
            )
    finally:
        os.environ.pop("PM_OPS_P0_TEST_DSN", None)
    assert rc != 0
    assert "repo_sha_mismatch" in out


def test_main_refuses_repo_not_on_main():
    os.environ["PM_OPS_P0_TEST_DSN"] = (
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres"
    )
    try:
        with _patched_repo(on_main=False):
            rc, out = _run_main(
                [
                    "--expect-project-ref",
                    REF,
                    "--dsn-env",
                    "PM_OPS_P0_TEST_DSN",
                    "--expect-repo-sha",
                    SHA,
                ]
            )
    finally:
        os.environ.pop("PM_OPS_P0_TEST_DSN", None)
    assert rc != 0
    assert "repo_not_on_main" in out


def test_main_refuses_unbound_dsn_value_silently():
    secret_host = "evil.attacker.example"
    secret_pw = "SuperSecretPw999"
    os.environ["PM_OPS_P0_TEST_DSN"] = (
        f"host={secret_host} user=sneaky password={secret_pw} dbname=postgres"
    )
    try:
        with _patched_repo():  # clean, matching sha, on main -> reaches bind
            rc, out = _run_main(
                [
                    "--expect-project-ref",
                    REF,
                    "--dsn-env",
                    "PM_OPS_P0_TEST_DSN",
                    "--expect-repo-sha",
                    SHA,
                ]
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
        run_dir = pe.write_custody(base, artifacts, clock=CLOCK)
        assert run_dir.parent == base
        assert stat.S_IMODE(run_dir.stat().st_mode) == 0o700
        manifest = run_dir / pe.MANIFEST_NAME
        assert manifest.exists()
        manifest_text = manifest.read_text()
        for name, content in artifacts.items():
            f = run_dir / name
            assert f.exists()
            assert stat.S_IMODE(f.stat().st_mode) == 0o400
            digest = hashlib.sha256(content.encode()).hexdigest()
            assert digest in manifest_text
            assert name in manifest_text
        assert stat.S_IMODE(manifest.stat().st_mode) == 0o400
    finally:
        for p in base.rglob("*"):
            with contextlib.suppress(OSError):
                p.chmod(0o600)
        shutil.rmtree(base, ignore_errors=True)


def test_write_custody_no_clobber():
    base = Path(tempfile.mkdtemp(prefix="p0a-custody-"))
    try:
        pe.write_custody(base, {"a.txt": "x\n"}, clock=CLOCK)
        raised = False
        try:
            pe.write_custody(base, {"a.txt": "y\n"}, clock=CLOCK)
        except FileExistsError:
            raised = True
        assert raised, "custody must not clobber an existing run directory"
    finally:
        for p in base.rglob("*"):
            with contextlib.suppress(OSError):
                p.chmod(0o600)
        shutil.rmtree(base, ignore_errors=True)


def test_write_custody_atomic_publish_leaves_no_partial():
    base = Path(tempfile.mkdtemp(prefix="p0a-custody-"))
    try:
        run_dir = pe.write_custody(base, {"a.txt": "x\n"}, clock=CLOCK)
        assert run_dir.exists()
        assert list(base.glob(".partial-*")) == []  # staging dir was renamed away
    finally:
        for p in base.rglob("*"):
            with contextlib.suppress(OSError):
                p.chmod(0o600)
        shutil.rmtree(base, ignore_errors=True)


def test_write_custody_writes_full_large_artifact():
    # guards against a short-write truncation while the manifest records the full hash
    base = Path(tempfile.mkdtemp(prefix="p0a-custody-"))
    try:
        big = ("row\t" * 100 + "\n") * 20000  # several MB, may span multiple writes
        run_dir = pe.write_custody(base, {"big.txt": big}, clock=CLOCK)
        written = (run_dir / "big.txt").read_bytes()
        assert written == big.encode()  # no truncation
        manifest = (run_dir / pe.MANIFEST_NAME).read_text()
        assert hashlib.sha256(big.encode()).hexdigest() in manifest
    finally:
        for p in base.rglob("*"):
            with contextlib.suppress(OSError):
                p.chmod(0o600)
        shutil.rmtree(base, ignore_errors=True)


# ---------------------------------------------------------------- provenance


def test_build_provenance_records_governance_fields():
    prov = pe.build_provenance(
        repo_sha="abc123",
        repo_clean=True,
        on_main=True,
        expect_repo_sha="abc123",
        expect_project_ref=REF,
        expect_db_role="postgres",
        dsn_env="SUPABASE_PROD_DSN",
        started_at="2026-07-14T00:00:00+00:00",
        finished_at="2026-07-14T00:00:05+00:00",
    )
    rec = json.loads(prov)
    assert rec["repo_sha"] == "abc123"
    assert rec["expected_project_ref"] == REF
    assert rec["expected_db_role"] == "postgres"
    assert rec["dsn_env_var_name"] == "SUPABASE_PROD_DSN"  # NAME only, never a value
    assert rec["repo_tracked_tree_clean"] is True
    assert rec["repo_head_merged_to_origin_main"] is True
    assert isinstance(rec["libpq_version"], int)
    assert set(rec["tool_source_sha256"]) == {"binding.py", "preserve_evidence.py"}
    here = Path(pe.__file__).resolve().parent
    for name in ("binding.py", "preserve_evidence.py"):
        expected = hashlib.sha256((here / name).read_bytes()).hexdigest()
        assert rec["tool_source_sha256"][name] == expected
    assert (
        rec["query_bundle_sha256"]
        == hashlib.sha256(pe.query_bundle_text().encode()).hexdigest()
    )


# ------------------------------------------------------------------ SQL parity


def test_p0a_sql_is_guarded_read_only():
    sql = pe.p0a_sql_text()
    assert "REPEATABLE READ, READ ONLY" in sql
    assert "transaction_read_only" in sql
    assert "P0-A refused" in sql
    for tbl in ("projects", "scopes", "tasks", "apparatus"):
        assert f"public.{tbl}" in sql
    assert "approve_apparatus_completion" in sql
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
    assert "'r'" in sql and "'f'" in sql


def test_p0a_sql_exact_function_acl_capture():
    # review finding 1: exact rollback source (raw proacl + exploded grants)
    sql = pe.p0a_sql_text()
    assert "proacl" in sql
    assert "aclexplode" in sql
    assert "grantee" in sql
    assert "grantor" in sql
    assert "is_grantable" in sql


def test_query_bundle_covers_role_guard_and_all_steps():
    bundle = pe.query_bundle_text()
    assert pe._ROLE_CHECK_SQL in bundle
    for _, step_sql in pe._EVIDENCE_STEPS:
        assert step_sql in bundle


# --------------------------------------------- live-path choreography (mocked)


class _FakeCursor:
    def __init__(self, recorder, role_ok):
        self._recorder = recorder
        self._role_ok = role_ok
        self.description = None

    def execute(self, sql, params=None):
        self._recorder.append(sql)

    def fetchone(self):
        return (self._role_ok,)

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    def __init__(self, host, user, recorder, role_ok=True):
        self.info = type("Info", (), {"host": host, "user": user, "hostaddr": ""})()
        self._recorder = recorder
        self._role_ok = role_ok

    def cursor(self):
        return _FakeCursor(self._recorder, self._role_ok)

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
        return _FakeConn(kwargs["host"], kwargs["user"], recorder, role_ok=True)

    orig = psycopg.connect
    psycopg.connect = fake_connect
    os.environ["PGHOST"] = "leak.example"
    try:
        dsn = f"host=db.{REF}.supabase.co user=postgres password=pw dbname=postgres"
        artifacts = pe.collect_evidence(dsn, REF, expect_role="postgres")
    finally:
        psycopg.connect = orig
        os.environ.pop("PGHOST", None)

    expected = (
        [pe._BEGIN, pe._GUARD, pe._ROLE_CHECK_SQL]
        + [sql for _, sql in pe._EVIDENCE_STEPS]
        + [pe._COMMIT]
    )
    assert recorder == expected
    assert env_at_connect.get("PGHOST") is None  # PG* scrubbed at connect time
    assert pe.SNAPSHOT_NAME in artifacts
    assert "08_secdef_function_acl.txt" in artifacts  # finding 1 artifact present


def test_collect_evidence_refuses_wrong_db_role_before_evidence():
    import psycopg

    recorder: list[str] = []

    def fake_connect(**kwargs):
        return _FakeConn(f"db.{REF}.supabase.co", "postgres", recorder, role_ok=False)

    orig = psycopg.connect
    psycopg.connect = fake_connect
    try:
        raised = False
        try:
            pe.collect_evidence(
                f"host=db.{REF}.supabase.co user=postgres dbname=postgres",
                REF,
                expect_role="postgres",
            )
        except pe.EvidenceRefusal as exc:
            raised = True
            assert exc.code == "db_role_mismatch", exc.code
    finally:
        psycopg.connect = orig
    assert raised
    # the role guard runs (BEGIN, GUARD, role-check) but NO evidence query is captured
    assert recorder == [pe._BEGIN, pe._GUARD, pe._ROLE_CHECK_SQL]


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

    def boom(dsn, expect_ref, *, expect_role="postgres"):
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
    os.environ["PM_OPS_P0_TEST_DSN"] = (
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres"
    )
    try:
        with _patched_repo():
            rc, out = _run_main(
                [
                    "--expect-project-ref",
                    REF,
                    "--dsn-env",
                    "PM_OPS_P0_TEST_DSN",
                    "--expect-repo-sha",
                    SHA,
                ]
            )
    finally:
        pe.collect_evidence = orig_collect
        pe.log.removeHandler(handler)
        os.environ.pop("PM_OPS_P0_TEST_DSN", None)
    assert rc != 0
    assert "connection_or_query_failed" in out
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
