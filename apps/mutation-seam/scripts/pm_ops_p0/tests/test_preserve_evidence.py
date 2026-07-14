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
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pm_ops_p0.preserve_evidence as pe  # noqa: E402

REF = "fxoyniqnrlkxfligbxmg"
SHA = "0123456789abcdef0123456789abcdef01234567"
CLOCK = "2026-07-14T00-00-00Z"

_SAME = (
    object()
)  # sentinel: origin/main sha defaults to HEAD sha (a merged-tip checkout)


# the three dependency-bundle args are argparse-required; governance refusals fire before
# the bundle is ever validated, so refusal tests can pass throwaway values. Collect-reaching
# tests stub _bootstrap_dependency_bundle to "" (-> the ambient offline psycopg via
# _load_binding(None)); see _patched_repo.
_BUNDLE_ARGS = [
    "--dependency-bundle",
    "/nonexistent-bundle",
    "--bundle-manifest",
    "/nonexistent-manifest",
    "--expect-bundle-manifest-sha256",
    "0" * 64,
]


def _run_main(argv: list[str]) -> tuple[int, str]:
    if "--dependency-bundle" not in argv:
        argv = [*argv, *_BUNDLE_ARGS]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pe.main(argv)
    return rc, buf.getvalue()


@contextlib.contextmanager
def _patched_repo(sha=SHA, clean=True, origin_main_sha=_SAME):
    """Inject a controlled git state so main()'s governance gate is offline-testable.

    The 3rd element is the freshly-fetched origin/main sha (str or None), matching the
    real ``_repo_git_state`` contract; it defaults to the HEAD sha (HEAD == origin/main).
    Also stubs the dependency-bundle bootstrap to "" so a governance-cleared run reaches
    the binding via the ambient offline psycopg (``_load_binding(None)``) instead of
    verifying a real bundle.
    """
    oms = sha if origin_main_sha is _SAME else origin_main_sha
    orig_root, orig_state, orig_boot = (
        pe._repo_root,
        pe._repo_git_state,
        pe._bootstrap_dependency_bundle,
    )
    pe._repo_root = lambda: Path("/fake/repo")
    pe._repo_git_state = lambda root: (sha, clean, oms)
    pe._bootstrap_dependency_bundle = lambda *a, **k: ""
    try:
        yield sha
    finally:
        pe._repo_root, pe._repo_git_state, pe._bootstrap_dependency_bundle = (
            orig_root,
            orig_state,
            orig_boot,
        )


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run git in `cwd`, raising with captured output on failure (test helper)."""
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True
    )


def _make_repo_with_remote(tmp: Path) -> tuple[Path, Path, str]:
    """Build a real work repo with one commit on `main` pushed to a local bare origin.

    Returns (work_dir, origin_bare_dir, head_sha) with HEAD == origin/main. Offline: the
    remote is a local bare repo (no network), so the real ``_repo_git_state`` fetch runs.
    """
    origin = tmp / "origin.git"
    work = tmp / "work"
    subprocess.run(
        ["git", "init", "--quiet", "--bare", str(origin)],
        check=True,
        capture_output=True,
    )
    work.mkdir()
    _git(work, "init", "--quiet")
    _git(work, "config", "user.email", "t@example.invalid")
    _git(work, "config", "user.name", "T")
    _git(work, "config", "commit.gpgsign", "false")
    _git(work, "checkout", "--quiet", "-b", "main")
    (work / "f.txt").write_text("1\n")
    _git(work, "add", "-A")
    _git(work, "commit", "--quiet", "-m", "c1")
    _git(work, "remote", "add", "origin", str(origin))
    _git(work, "push", "--quiet", "origin", "main")
    _git(work, "fetch", "--quiet", "origin")  # populate refs/remotes/origin/main
    return work, origin, _git(work, "rev-parse", "HEAD").stdout.strip()


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


def test_parser_requires_dependency_bundle_args():
    # RI2 finding 1: all three bundle args are required — psycopg is loaded ONLY from a
    # verified hash-pinned bundle under -S, never the interpreter's site startup.
    full = [
        "--expect-project-ref",
        REF,
        "--dsn-env",
        "V",
        "--expect-repo-sha",
        SHA,
        "--dependency-bundle",
        "/b",
        "--bundle-manifest",
        "/m",
        "--expect-bundle-manifest-sha256",
        "0" * 64,
    ]
    pe.build_parser().parse_args(full)  # complete set parses
    for missing in (
        "--dependency-bundle",
        "--bundle-manifest",
        "--expect-bundle-manifest-sha256",
    ):
        args = list(full)
        i = args.index(missing)
        del args[i : i + 2]
        try:
            pe.build_parser().parse_args(args)
        except SystemExit as exc:
            assert exc.code != 0
        else:  # pragma: no cover
            raise AssertionError(f"{missing} must be required")


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


def test_main_refuses_head_not_origin_main():
    # HEAD == --expect-repo-sha but != origin/main (a stale/ancestor or self-attested
    # checkout an ancestor test would have passed) -> refuse (finding 2, equality).
    os.environ["PM_OPS_P0_TEST_DSN"] = (
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres"
    )
    try:
        with _patched_repo(origin_main_sha="ffff0000ffff0000ffff0000ffff0000ffff0000"):
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
    assert "repo_head_not_origin_main" in out


def test_main_refuses_when_origin_main_unresolvable():
    # fail closed: cannot verify the merged guarantee -> refuse (review Codex-P2)
    os.environ["PM_OPS_P0_TEST_DSN"] = (
        f"host=db.{REF}.supabase.co user=postgres dbname=postgres"
    )
    try:
        with _patched_repo(origin_main_sha=None):
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
    assert "origin_main_unresolvable" in out


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


# ---------------------------------------------- runtime integrity (round 3)


def test_expect_db_role_flag_is_rejected():
    # finding 3: the admin DB role is SOURCE-PINNED, not a caller-selectable option
    try:
        pe.build_parser().parse_args(
            [
                "--expect-project-ref",
                REF,
                "--dsn-env",
                "V",
                "--expect-repo-sha",
                SHA,
                "--expect-db-role",
                "authenticator",
            ]
        )
    except SystemExit as exc:
        assert exc.code != 0
    else:  # pragma: no cover
        raise AssertionError("--expect-db-role must not be an accepted option")


def test_untracked_import_shadow_rejected_before_binding_import():
    # finding 1: an untracked shadow module makes the tree non-pristine, so main() refuses
    # (repo_dirty) BEFORE collect_evidence() -- where pm_ops_p0.binding/psycopg is imported.
    tmp = Path(tempfile.mkdtemp(prefix="p0a-ri-shadow-"))
    try:
        work, _origin, head = _make_repo_with_remote(tmp)
        # a planted import-shadow is UNTRACKED; if imported it would run this
        (work / "psycopg.py").write_text("raise RuntimeError('shadow executed')\n")
        reached = {"collect": False}

        def spy_collect(dsn, expect_ref, *, connect_bound=None):
            reached["collect"] = True  # only reachable past the deferred binding import
            raise AssertionError("collect_evidence must not run for an untracked tree")

        orig_root, orig_collect = pe._repo_root, pe.collect_evidence
        pe._repo_root = lambda: work
        pe.collect_evidence = spy_collect
        os.environ["PM_OPS_P0_TEST_DSN"] = (
            f"host=db.{REF}.supabase.co user=postgres dbname=postgres"
        )
        try:
            rc, out = _run_main(
                [
                    "--expect-project-ref",
                    REF,
                    "--dsn-env",
                    "PM_OPS_P0_TEST_DSN",
                    "--expect-repo-sha",
                    head,
                ]
            )
        finally:
            pe._repo_root, pe.collect_evidence = orig_root, orig_collect
            os.environ.pop("PM_OPS_P0_TEST_DSN", None)
        assert rc != 0
        assert "repo_dirty" in out  # untracked shadow -> non-pristine -> refused
        assert reached["collect"] is False  # refused before the deferred binding import
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_historical_ancestor_of_origin_main_rejected():
    # finding 2: HEAD is an ANCESTOR of origin/main but not equal -> refuse (equality, not
    # ancestor). A `merge-base --is-ancestor` test would have passed this stale checkout.
    tmp = Path(tempfile.mkdtemp(prefix="p0a-ri-ancestor-"))
    try:
        work, _origin, head1 = _make_repo_with_remote(tmp)
        (work / "f.txt").write_text("2\n")
        _git(work, "add", "-A")
        _git(work, "commit", "--quiet", "-m", "c2")
        _git(work, "push", "--quiet", "origin", "main")  # origin/main advances to head2
        _git(work, "reset", "--quiet", "--hard", head1)  # HEAD back to the ancestor
        orig_root = pe._repo_root
        pe._repo_root = lambda: work
        os.environ["PM_OPS_P0_TEST_DSN"] = (
            f"host=db.{REF}.supabase.co user=postgres dbname=postgres"
        )
        try:
            rc, out = _run_main(
                [
                    "--expect-project-ref",
                    REF,
                    "--dsn-env",
                    "PM_OPS_P0_TEST_DSN",
                    "--expect-repo-sha",
                    head1,
                ]
            )
        finally:
            pe._repo_root = orig_root
            os.environ.pop("PM_OPS_P0_TEST_DSN", None)
        assert rc != 0
        assert "repo_head_not_origin_main" in out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_head_equals_origin_main_clears_the_gate():
    # finding 2 (positive): a pristine checkout at HEAD == origin/main == --expect-repo-sha
    # clears the gate and reaches collect_evidence (stubbed short of any real connect).
    tmp = Path(tempfile.mkdtemp(prefix="p0a-ri-pass-"))
    try:
        work, _origin, head = _make_repo_with_remote(tmp)
        reached = {"collect": False}

        def spy_collect(dsn, expect_ref, *, connect_bound=None):
            reached["collect"] = True
            raise pe.EvidenceRefusal("stub_gate_cleared")

        orig_root, orig_collect, orig_boot = (
            pe._repo_root,
            pe.collect_evidence,
            pe._bootstrap_dependency_bundle,
        )
        pe._repo_root = lambda: work
        pe.collect_evidence = spy_collect
        pe._bootstrap_dependency_bundle = lambda *a, **k: ""  # ambient offline psycopg
        os.environ["PM_OPS_P0_TEST_DSN"] = (
            f"host=db.{REF}.supabase.co user=postgres dbname=postgres"
        )
        try:
            rc, out = _run_main(
                [
                    "--expect-project-ref",
                    REF,
                    "--dsn-env",
                    "PM_OPS_P0_TEST_DSN",
                    "--expect-repo-sha",
                    head,
                ]
            )
        finally:
            pe._repo_root, pe.collect_evidence, pe._bootstrap_dependency_bundle = (
                orig_root,
                orig_collect,
                orig_boot,
            )
            os.environ.pop("PM_OPS_P0_TEST_DSN", None)
        assert rc != 0
        assert reached["collect"] is True  # governance gate cleared
        assert "stub_gate_cleared" in out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_runbook_uses_child_only_infisical_injection():
    # finding 4: the runbook injects the DSN into the CHILD process via inject.sh and
    # never exports a literal secret into the operator shell.
    root = Path(__file__).resolve().parents[5]
    runbook = root / "docs" / "superpowers" / "specs" / "pm-ops-p0" / "P0A_RUNBOOK.md"
    text = runbook.read_text()
    assert "infra/infisical/inject.sh prod --" in text
    assert "--dsn-env" in text
    assert "export SUPABASE_PROD_DSN" not in text  # no literal secret export
    assert "--expect-db-role" not in text  # removed, source-pinned (finding 3)


def test_config_hidden_untracked_shadow_still_rejected():
    # lens-A A1: a hostile repo-local .git/config `showUntrackedFiles=no` must NOT hide a
    # planted untracked shadow from the pristine check (the tool forces --untracked-files=all).
    tmp = Path(tempfile.mkdtemp(prefix="p0a-ri-cfg-"))
    try:
        work, _origin, _head = _make_repo_with_remote(tmp)
        _git(
            work, "config", "status.showUntrackedFiles", "no"
        )  # attacker hides untracked
        (work / "psycopg.py").write_text(
            "raise RuntimeError('shadow')\n"
        )  # untracked shadow
        _sha, pristine, _oms = pe._repo_git_state(work)
        assert (
            pristine is False
        )  # forced -uall + pinned config defeats the hostile config
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_assert_trusted_location_belt():
    # lens-A A2 / Codex-c5,c8 P1: only a path UNDER a real interpreter/venv install dir is
    # trusted -- a repo-tree shadow AND a decoy merely CONTAINING "site-packages" are refused.
    import sysconfig

    for bad in (
        "/home/olares/code/apex/apex-power-ops-platform"
        "/apps/mutation-seam/scripts/psycopg.py",
        "/tmp/site-packages/psycopg.py",  # contains the token but is NOT a real install dir
        "",
    ):
        raised = False
        try:
            pe._assert_trusted_location(bad)
        except pe.EvidenceRefusal as exc:
            raised = True
            assert exc.code == "untrusted_binding_source", exc.code
        assert raised, bad
    # the ACTUAL interpreter site-packages location is accepted
    real = os.path.join(sysconfig.get_paths()["purelib"], "psycopg", "__init__.py")
    pe._assert_trusted_location(real)  # under the real venv -> no raise


def test_git_env_scrubs_injected_secrets_and_redirects():
    # Codex-c6 P1: no injected app secret reaches git. Codex-c7 P1: no GIT_*/XDG_*
    # repo/config redirection var is forwarded (they are honored over `-C`).
    injected = {
        "SUPABASE_PROD_DSN": "postgresql://secret-should-not-reach-git",
        "DISPOSITION_SIGNING_KEY": "topsecret-should-not-reach-git",
        "GIT_DIR": "/tmp/attacker/.git",
        "GIT_WORK_TREE": "/tmp/attacker",
        "GIT_CONFIG_GLOBAL": "/tmp/attacker/gitconfig",
        "XDG_CONFIG_HOME": "/tmp/attacker/.config",
    }
    saved = {k: os.environ.get(k) for k in injected}
    os.environ.update(injected)
    try:
        env = pe._git_env()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    # neither secrets nor GIT_*/XDG_* redirection vars are forwarded ...
    for k in (
        "SUPABASE_PROD_DSN",
        "DISPOSITION_SIGNING_KEY",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "XDG_CONFIG_HOME",
    ):
        assert k not in env, k
    # ... and the attacker's GIT_CONFIG_GLOBAL value is REPLACED with our safe /dev/null pin
    # (present with our value, never the injected one; RI2 lens-A F1).
    assert env.get("GIT_CONFIG_GLOBAL") == "/dev/null"
    assert "/tmp/attacker/gitconfig" not in env.values()
    assert "PATH" in env  # git still receives what it legitimately needs
    # RI2 lens-A F1: global/system gitconfig is pinned to /dev/null so it cannot inject
    # hooks/fsmonitor/credential-helpers into the preflight.
    assert env.get("GIT_CONFIG_GLOBAL") == "/dev/null"
    assert env.get("GIT_CONFIG_SYSTEM") == "/dev/null"


def test_git_hardening_flags_disable_config_execution():
    # RI2 lens-A F1: every git call forces the code-execution knobs OFF via command-line -c
    joined = " ".join(pe._GIT_HARDENING)
    assert "core.fsmonitor=false" in joined
    assert "core.hooksPath=/dev/null" in joined
    assert "credential.helper=" in joined
    assert "protocol.ext.allow=never" in joined


def test_git_preflight_neutralizes_repo_local_fsmonitor():
    # RI2 lens-A F1 (behavioral): a repo-local core.fsmonitor is arbitrary code git runs
    # during `git status`. The preflight's `-c core.fsmonitor=false` (command-line, outranks
    # repo config) must prevent it from executing at all.
    tmp = Path(tempfile.mkdtemp(prefix="p0a-ri-fsmon-"))
    try:
        work, _origin, _head = _make_repo_with_remote(tmp)
        marker = tmp / "FSMONITOR_RAN"
        hook = work / "evil_fsmonitor.sh"
        hook.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 1\n')
        hook.chmod(0o755)
        # a repo-LOCAL config setting fsmonitor to the hook (untracked config, invisible to
        # `git status`); git would invoke it during status absent the hardening.
        _git(work, "config", "core.fsmonitor", str(hook))
        pe._repo_git_state(work)  # runs the hardened `git status`
        assert not marker.exists(), (
            "repo-local core.fsmonitor executed despite -c override"
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_isolation_gate():
    # RI2 finding 1: -I alone does NOT imply -S, so site still runs and executes an
    # editable-install .pth BEFORE the gate (with the injected DSN present). The CLI now
    # requires python -I -S (isolated AND no-site); any weaker interpreter is refused.
    assert pe._isolation_gate(True, True) is None  # -I -S -> proceed
    for isolated, no_site in ((True, False), (False, True), (False, False)):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = pe._isolation_gate(isolated, no_site)
        out = buf.getvalue()
        assert rc == 1, (isolated, no_site)
        assert "interpreter_not_isolated_no_site" in out
        assert "RESULT FAIL" in out


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
        repo_pristine=True,
        on_main=True,
        origin_main_sha="abc123",
        expect_repo_sha="abc123",
        expect_project_ref=REF,
        expect_db_role="postgres",
        dsn_env="SUPABASE_PROD_DSN",
        dependency_bundle_manifest_sha256="d" * 64,
        started_at="2026-07-14T00:00:00+00:00",
        finished_at="2026-07-14T00:00:05+00:00",
    )
    rec = json.loads(prov)
    assert rec["schema_version"] == 3  # RI2: bundle-bearing provenance schema
    assert rec["repo_sha"] == "abc123"
    assert rec["expected_project_ref"] == REF
    assert rec["expected_db_role"] == "postgres"
    assert rec["dsn_env_var_name"] == "SUPABASE_PROD_DSN"  # NAME only, never a value
    assert (
        rec["dependency_bundle_manifest_sha256"] == "d" * 64
    )  # bundle bound to evidence
    assert rec["repo_tree_pristine"] is True
    assert (
        rec["origin_main_sha"] == "abc123"
    )  # HEAD == origin/main == expect (finding 2)
    assert rec["repo_head_equals_origin_main"] is True
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
        artifacts = pe.collect_evidence(dsn, REF)
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
    import pm_ops_p0.binding as binding
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
        except binding.TargetBindingError as exc:  # deferred import -> catch on binding
            raised = True
            assert exc.code == "connection_host_mismatch", exc.code
    finally:
        psycopg.connect = orig
    assert raised
    assert recorder == []  # the post-connect re-check gates BEFORE any query runs


def test_main_value_silent_when_collection_raises():
    import logging

    sentinel = "leaky-host-9.9.9.9.internal"

    def boom(dsn, expect_ref, *, connect_bound=None):
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
