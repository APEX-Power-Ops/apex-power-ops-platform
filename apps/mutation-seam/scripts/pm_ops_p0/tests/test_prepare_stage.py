"""Offline tests for pm_ops_p0.prepare_stage — the secret-free two-stage prepare (RI2-3 F1).

The core property: the staged package bytes come from the PINNED COMMIT OBJECT via
``git cat-file``, so a repo-controlled clean filter, ``update-index --assume-unchanged``,
an ignored ``.pyc``, or a modified worktree verifier CANNOT change what gets staged — the
exact bypasses the old self-verifying-worktree model allowed. Real temp git repos with a
local bare origin; no DSN, no network. Runnable under pytest OR directly.
"""

from __future__ import annotations

import contextlib
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pm_ops_p0.prepare_stage as ps  # noqa: E402

PKG_REL = ps.PACKAGE_REL  # apps/mutation-seam/scripts/pm_ops_p0
GENUINE = {
    "__init__.py": b'"""genuine init"""\n',
    "binding.py": b"GENUINE = True\ndef connect_bound():\n    return 'genuine'\n",
    "finalize_closeout.py": b"GENUINE_FINALIZE = True\n",
    "preserve_evidence.py": b"GENUINE_VERIFIER = True\n",
}


def _git(cwd: Path, *args: str, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=check
    )


def _make_repo(tmp: Path) -> tuple[Path, str]:
    """A work repo with the package committed at PKG_REL on main, pushed to a bare origin."""
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
    pkg = work / PKG_REL
    pkg.mkdir(parents=True)
    for name, data in GENUINE.items():
        (pkg / name).write_bytes(data)
    _git(work, "add", "-A")
    _git(work, "commit", "--quiet", "-m", "c1")
    _git(work, "remote", "add", "origin", str(origin))
    _git(work, "push", "--quiet", "origin", "main")
    _git(work, "fetch", "--quiet", "origin")
    return work, _git(work, "rev-parse", "HEAD").stdout.strip()


@contextlib.contextmanager
def _patched_root(work: Path):
    orig = ps._repo_root
    ps._repo_root = lambda: work
    try:
        yield
    finally:
        ps._repo_root = orig


def _make_bundle(tmp: Path) -> tuple[str, str, str]:
    bundle = tmp / "bundle"
    bundle.mkdir()
    data = b"# fake psycopg placeholder\n"
    (bundle / "psycopg").mkdir()
    (bundle / "psycopg" / "__init__.py").write_bytes(data)
    man = tmp / "bundle.sha256"
    man.write_bytes(
        f"{hashlib.sha256(data).hexdigest()}  psycopg/__init__.py\n".encode()
    )
    return str(bundle), str(man), hashlib.sha256(man.read_bytes()).hexdigest()


def _prepare(
    tmp: Path, work: Path, sha: str, stage_name="stage"
) -> tuple[int, str, Path]:
    bundle, man, man_sha = _make_bundle(tmp)
    stage = tmp / stage_name
    with _patched_root(work):
        try:
            digest = ps.prepare(
                expect_repo_sha=sha,
                stage_dir=str(stage),
                dependency_bundle=bundle,
                bundle_manifest=man,
                expect_bundle_manifest_sha256=man_sha,
            )
        except ps.PrepareRefusal as exc:
            return 1, exc.code, stage
    return 0, digest, stage


@contextlib.contextmanager
def _tmp():
    d = Path(tempfile.mkdtemp(prefix="p0a-prepare-"))
    try:
        yield d
    finally:
        for p in d.rglob("*"):
            with contextlib.suppress(OSError):
                p.chmod(0o700)
        shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------------ happy path


def test_prepare_stages_pinned_modules_and_freezes():
    with _tmp() as tmp:
        work, sha = _make_repo(tmp)
        rc, digest, stage = _prepare(tmp, work, sha)
        assert rc == 0, digest
        for name, data in GENUINE.items():
            assert (stage / "pm_ops_p0" / name).read_bytes() == data
        # no tests/, no __pycache__, no README/requirements staged
        assert not (stage / "pm_ops_p0" / "tests").exists()
        assert (stage / "deps" / "psycopg" / "__init__.py").exists()
        prov = (stage / ps.STAGE_PROVENANCE_NAME).read_text()
        assert sha in prov
        assert (stage / ps.STAGE_DIGEST_NAME).read_text().strip() == digest
        # digest is a pure function of the staged module hashes
        shas = {n: hashlib.sha256(d).hexdigest() for n, d in GENUINE.items()}
        assert ps.compute_stage_digest(shas) == digest


# ----------------------------------------------- the static-plant bypasses (F1)


def test_assume_unchanged_modified_binding_still_stages_pinned_bytes():
    # git update-index --assume-unchanged hides a modified tracked file from status, so the
    # old worktree-reading verifier would pass "pristine" AND read the tampered bytes. cat-file
    # extraction from the pinned commit ignores the worktree entirely.
    with _tmp() as tmp:
        work, sha = _make_repo(tmp)
        (work / PKG_REL / "binding.py").write_bytes(b"MALICIOUS = __import__('os')\n")
        _git(work, "update-index", "--assume-unchanged", f"{PKG_REL}/binding.py")
        rc, digest, stage = _prepare(tmp, work, sha)
        assert rc == 0, digest  # governance still passes (assume-unchanged hides it)
        assert (stage / "pm_ops_p0" / "binding.py").read_bytes() == GENUINE[
            "binding.py"
        ]
        assert b"MALICIOUS" not in (stage / "pm_ops_p0" / "binding.py").read_bytes()


def test_modified_worktree_verifier_does_not_reach_the_stage():
    # a modified preserve_evidence.py (the verifier itself), hidden by assume-unchanged, must
    # not be what capture later runs — the stage gets the pinned commit's verifier.
    with _tmp() as tmp:
        work, sha = _make_repo(tmp)
        (work / PKG_REL / "preserve_evidence.py").write_bytes(
            b"MALICIOUS_VERIFIER = 1\n"
        )
        _git(
            work,
            "update-index",
            "--assume-unchanged",
            f"{PKG_REL}/preserve_evidence.py",
        )
        rc, digest, stage = _prepare(tmp, work, sha)
        assert rc == 0, digest
        staged = (stage / "pm_ops_p0" / "preserve_evidence.py").read_bytes()
        assert staged == GENUINE["preserve_evidence.py"]
        assert b"MALICIOUS" not in staged


def test_clean_filter_divergence_trips_pristine_gate():
    # a repo-local clean filter (.git/info/attributes) that diverges binding.py makes it read
    # as modified: the pristine gate CATCHES it (repo_dirty) — defence in depth. (cat-file
    # immunity when the gate is bypassed is proven by the assume-unchanged tests above.)
    with _tmp() as tmp:
        work, sha = _make_repo(tmp)
        (work / ".git" / "info" / "attributes").write_text(
            f"{PKG_REL}/binding.py filter=evil\n"
        )
        _git(work, "config", "filter.evil.clean", "sed 's/GENUINE/MALICIOUS/'")
        rc, code, _ = _prepare(tmp, work, sha)
        assert rc == 1 and code == "repo_dirty", code


def test_clean_filter_with_assume_unchanged_still_stages_pinned_bytes():
    # combine the two: an identity-status clean filter can't diverge status, but even a
    # diverging filter hidden by assume-unchanged (so status is pristine) cannot change the
    # cat-file'd pinned bytes.
    with _tmp() as tmp:
        work, sha = _make_repo(tmp)
        (work / ".git" / "info" / "attributes").write_text(
            f"{PKG_REL}/binding.py filter=evil\n"
        )
        _git(work, "config", "filter.evil.clean", "sed 's/GENUINE/MALICIOUS/'")
        _git(work, "update-index", "--assume-unchanged", f"{PKG_REL}/binding.py")
        rc, digest, stage = _prepare(tmp, work, sha)
        assert rc == 0, digest
        assert (stage / "pm_ops_p0" / "binding.py").read_bytes() == GENUINE[
            "binding.py"
        ]


def test_ignored_pyc_is_not_staged():
    # an ignored, timestamp-valid __pycache__/*.pyc in the worktree is never staged (only the
    # top-level pinned .py modules are), so capture under -S can't load it.
    with _tmp() as tmp:
        work, sha = _make_repo(tmp)
        pycache = work / PKG_REL / "__pycache__"
        pycache.mkdir()
        (pycache / "binding.cpython-312.pyc").write_bytes(b"\x00malicious-bytecode\n")
        (work / PKG_REL / ".gitignore").write_text(
            "__pycache__/\n"
        )  # keep tree pristine
        _git(work, "add", f"{PKG_REL}/.gitignore")
        _git(work, "commit", "--quiet", "-m", "ignore pycache")
        _git(work, "push", "--quiet", "origin", "main")
        _git(work, "fetch", "--quiet", "origin")
        sha2 = _git(work, "rev-parse", "HEAD").stdout.strip()
        rc, digest, stage = _prepare(tmp, work, sha2)
        assert rc == 0, digest
        assert not (stage / "pm_ops_p0" / "__pycache__").exists()
        assert list((stage / "pm_ops_p0").glob("*.pyc")) == []


# ---------------------------------------------------------------- refusal paths


def test_repo_dirty_tracked_modification_refused():
    # a genuinely modified tracked file (NOT hidden by assume-unchanged) fails the pristine gate
    with _tmp() as tmp:
        work, sha = _make_repo(tmp)
        (work / PKG_REL / "binding.py").write_bytes(b"tracked change\n")
        rc, code, _ = _prepare(tmp, work, sha)
        assert rc == 1 and code == "repo_dirty", code


def test_sha_mismatch_refused():
    with _tmp() as tmp:
        work, _sha = _make_repo(tmp)
        rc, code, _ = _prepare(tmp, work, "0" * 40)
        assert rc == 1 and code == "repo_sha_mismatch", code


def test_stage_dir_exists_refused():
    with _tmp() as tmp:
        work, sha = _make_repo(tmp)
        (tmp / "stage").mkdir()
        rc, code, _ = _prepare(tmp, work, sha, stage_name="stage")
        assert rc == 1 and code == "stage_dir_exists", code


def test_bundle_manifest_untrusted_refused():
    with _tmp() as tmp:
        work, sha = _make_repo(tmp)
        bundle, man, _man_sha = _make_bundle(tmp)
        with _patched_root(work):
            try:
                ps.prepare(
                    expect_repo_sha=sha,
                    stage_dir=str(tmp / "stage"),
                    dependency_bundle=bundle,
                    bundle_manifest=man,
                    expect_bundle_manifest_sha256="0" * 64,
                )
            except ps.PrepareRefusal as exc:
                assert exc.code == "bundle_manifest_untrusted", exc.code
            else:  # pragma: no cover
                raise AssertionError("expected bundle_manifest_untrusted")


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
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[FAIL] {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(funcs) - failures}/{len(funcs)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
