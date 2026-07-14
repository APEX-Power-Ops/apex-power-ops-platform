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
