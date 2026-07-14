"""Offline tests for the preserve_evidence hash-pinned dependency-bundle bootstrap (RI2).

Under ``python -I -S`` the interpreter's site-packages are off ``sys.path``, so psycopg
cannot be imported via ``site`` startup (the ``.pth`` execution vector RI2 finding 1
removed). The operator instead supplies an immutable dependency bundle whose every file is
SHA-256-pinned in a manifest, the manifest's own SHA-256 attested out-of-band. These tests
drive that verification with SYNTHETIC bundles (no real psycopg needed): the
manifest-integrity, per-file hash, unlisted-member, symlink, escape, and missing-file
rejects, plus a positive load that imports a fake module from the verified bundle.

No database or network. Runnable under pytest OR directly:

    python tests/test_dependency_bundle.py
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pm_ops_p0.preserve_evidence as pe  # noqa: E402


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _make_bundle(root: Path, files: dict[str, bytes]) -> tuple[Path, Path, str]:
    """Create a synthetic bundle dir + a matching manifest; return (bundle, manifest, msha)."""
    bundle = root / "bundle"
    bundle.mkdir()
    lines = []
    for rel, data in files.items():
        p = bundle / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        lines.append(f"{_sha(data)}  {rel}")
    manifest = root / "bundle.sha256"
    manifest.write_bytes(("\n".join(lines) + "\n").encode())
    return bundle, manifest, _sha(manifest.read_bytes())


@contextlib.contextmanager
def _restore_syspath():
    saved_path, saved_dwb = list(sys.path), sys.dont_write_bytecode
    try:
        yield
    finally:
        sys.path[:] = saved_path
        sys.dont_write_bytecode = saved_dwb


def _expect_refusal(code: str, bundle: Path, manifest: Path, msha: str) -> None:
    with _restore_syspath():
        try:
            pe._bootstrap_dependency_bundle(str(bundle), str(manifest), msha)
        except pe.EvidenceRefusal as exc:
            assert exc.code == code, (exc.code, code)
            assert exc.code == str(exc)  # value-free stable code
            return
    raise AssertionError(f"expected EvidenceRefusal({code})")


# --------------------------------------------------------------- positive load


def test_bootstrap_accepts_clean_bundle_and_imports_from_it():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d, _restore_syspath():
        bundle, manifest, msha = _make_bundle(
            Path(d),
            {
                "fake_dep_ok/__init__.py": b"VALUE = 42\n",
                "fake_dep_ok/util.py": b"x = 1\n",
            },
        )
        base = pe._bootstrap_dependency_bundle(str(bundle), str(manifest), msha)
        try:
            assert base == os.path.realpath(bundle)
            assert sys.path[0] == base  # exposed at the FRONT
            assert (
                sys.dont_write_bytecode is True
            )  # no unlisted __pycache__ written back
            mod = importlib.import_module(
                "fake_dep_ok"
            )  # resolves from the verified bundle
            assert mod.VALUE == 42
            assert os.path.realpath(mod.__file__).startswith(base + os.sep)
        finally:
            sys.modules.pop("fake_dep_ok", None)
            sys.modules.pop("fake_dep_ok.util", None)


# ------------------------------------------------------------- manifest integrity


def test_bootstrap_rejects_untrusted_manifest_sha():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d:
        bundle, manifest, _msha = _make_bundle(Path(d), {"a.py": b"a\n"})
        _expect_refusal("bundle_manifest_untrusted", bundle, manifest, "0" * 64)


def test_bootstrap_rejects_unreadable_manifest():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d:
        bundle, _manifest, _msha = _make_bundle(Path(d), {"a.py": b"a\n"})
        missing = Path(d) / "nope.sha256"
        _expect_refusal("bundle_manifest_unreadable", bundle, missing, "0" * 64)


def test_bootstrap_rejects_empty_manifest():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d:
        root = Path(d)
        bundle = root / "bundle"
        bundle.mkdir()
        manifest = root / "empty.sha256"
        manifest.write_bytes(b"\n")
        _expect_refusal(
            "bundle_manifest_empty", bundle, manifest, _sha(manifest.read_bytes())
        )


def test_bootstrap_rejects_manifest_traversal_entry():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d:
        root = Path(d)
        bundle = root / "bundle"
        bundle.mkdir()
        manifest = root / "evil.sha256"
        manifest.write_bytes((f"{_sha(b'x')}  ../outside.py\n").encode())
        _expect_refusal(
            "bundle_manifest_malformed", bundle, manifest, _sha(manifest.read_bytes())
        )


# ------------------------------------------------------------- member integrity


def test_bootstrap_rejects_tampered_file():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d:
        bundle, manifest, msha = _make_bundle(Path(d), {"a.py": b"original\n"})
        (bundle / "a.py").write_bytes(
            b"TAMPERED\n"
        )  # bytes now disagree with the manifest
        _expect_refusal("bundle_hash_mismatch", bundle, manifest, msha)


def test_bootstrap_rejects_unlisted_extra_file():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d:
        bundle, manifest, msha = _make_bundle(Path(d), {"a.py": b"a\n"})
        (bundle / "evil.pth").write_bytes(b"import os\n")  # unlisted execution surface
        _expect_refusal("bundle_unlisted_file", bundle, manifest, msha)


def test_bootstrap_rejects_symlink_member():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d:
        bundle, manifest, msha = _make_bundle(Path(d), {"a.py": b"a\n"})
        outside = Path(d) / "outside.py"
        outside.write_bytes(b"import os\n")
        try:
            (bundle / "link.py").symlink_to(outside)
        except (
            OSError,
            NotImplementedError,
        ):  # pragma: no cover - platform w/o symlinks
            return
        _expect_refusal("bundle_unsafe_member", bundle, manifest, msha)


def test_bootstrap_rejects_missing_listed_file():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d:
        root = Path(d)
        bundle = root / "bundle"
        bundle.mkdir()
        (bundle / "a.py").write_bytes(b"a\n")
        # manifest lists a.py (present) AND b.py (never created) -> the listed file is missing
        sha_a, sha_b = _sha(b"a\n"), _sha(b"b\n")
        manifest = root / "b.sha256"
        manifest.write_bytes(f"{sha_a}  a.py\n{sha_b}  b.py\n".encode())
        _expect_refusal(
            "bundle_member_missing", bundle, manifest, _sha(manifest.read_bytes())
        )


def test_bootstrap_rejects_non_directory_bundle():
    with tempfile.TemporaryDirectory(prefix="p0a-bundle-") as d:
        root = Path(d)
        not_a_dir = root / "file.txt"
        not_a_dir.write_bytes(b"x\n")
        sha_a = _sha(b"a\n")
        manifest = root / "m.sha256"
        manifest.write_bytes(f"{sha_a}  a.py\n".encode())
        _expect_refusal(
            "bundle_dir_invalid", not_a_dir, manifest, _sha(manifest.read_bytes())
        )


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
