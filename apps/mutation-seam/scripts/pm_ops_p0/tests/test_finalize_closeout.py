"""Offline tests for pm_ops_p0.finalize_closeout (review round 3, finding 5).

No database or network. A synthetic custody dir (script artifacts + manifest + operator
artifacts) and a closeout spec drive the fail-closed matrix: missing / duplicate category,
path traversal, non-regular artifact, unhashed / hash-mismatch script artifact, failed-HTTP
capture, and the no-clobber SHA-256 index. Runnable under pytest OR directly:

    python tests/test_finalize_closeout.py
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import stat
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pm_ops_p0.finalize_closeout as fc  # noqa: E402

CLOCK = "2026-07-14T00:00:00+00:00"

# script-captured artifacts (hashed into manifest.sha256 by preserve_evidence.write_custody)
SCRIPT_ARTS = {
    "00_provenance.json": b'{"artifact": "prov"}\n',
    "00_p0a_snapshot.sql": b"BEGIN;\n",
    "01_markers.txt": b"markers\n",
    "02_table_acl.txt": b"acl\n",
    "03_effective_privilege.txt": b"eff\n",
    "04_role_membership_closure.txt": b"closure\n",
    "05_counts.txt": b"counts\n",
    "06_default_acl.txt": b"default\n",
    "07_secdef_discovery.txt": b"secdef\n",
    "08_secdef_function_acl.txt": b"fnacl\n",
}
# operator/HTTP-captured artifacts (NOT in the script manifest; finalizer hashes them)
OPERATOR_ARTS = {
    "openapi_seam.json": b'{"openapi": "3.1.0", "paths": {}}\n',
    "reset_route.json": b'{"path": "/reset", "security": []}\n',
    "backend.json": b'{"backend": "render", "source": "config"}\n',
    "reset_logs.txt": b"POST /reset 200\n",
}


def _make_custody(tmp: Path) -> Path:
    custody = tmp / "run"
    custody.mkdir(parents=True)
    lines = []
    for name, data in SCRIPT_ARTS.items():
        (custody / name).write_bytes(data)
        lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
    for name, data in OPERATOR_ARTS.items():
        (custody / name).write_bytes(
            data
        )  # operator arts deliberately NOT in the manifest
    (custody / "manifest.sha256").write_text("\n".join(lines) + "\n")
    return custody


def _full_spec() -> dict:
    return {
        "categories": [
            {"category": 1, "source": "operator", "artifacts": ["openapi_seam.json"]},
            {"category": 2, "source": "operator", "artifacts": ["reset_route.json"]},
            {
                "category": 3,
                "source": "script",
                "artifacts": [
                    "03_effective_privilege.txt",
                    "04_role_membership_closure.txt",
                ],
            },
            {
                "category": 4,
                "source": "script",
                "artifacts": ["07_secdef_discovery.txt", "08_secdef_function_acl.txt"],
            },
            {"category": 5, "source": "script", "artifacts": ["05_counts.txt"]},
            {"category": 6, "source": "script", "artifacts": ["06_default_acl.txt"]},
            {"category": 7, "source": "operator", "artifacts": ["backend.json"]},
            {"category": 8, "source": "operator", "artifacts": ["reset_logs.txt"]},
            {
                "category": 9,
                "source": "script",
                "artifacts": [
                    "02_table_acl.txt",
                    "06_default_acl.txt",
                    "08_secdef_function_acl.txt",
                ],
            },
        ]
    }


def _write_spec(tmp: Path, spec: dict) -> Path:
    p = tmp / "spec.json"
    p.write_text(json.dumps(spec))
    return p


@contextlib.contextmanager
def _tmp():
    d = Path(tempfile.mkdtemp(prefix="p0a-closeout-"))
    try:
        yield d
    finally:
        for p in d.rglob("*"):
            with contextlib.suppress(OSError):
                p.chmod(0o600)
        shutil.rmtree(d, ignore_errors=True)


def _expect_closeout_error(spec: dict, code: str, *, custody_mutator=None) -> None:
    with _tmp() as tmp:
        custody = _make_custody(tmp)
        if custody_mutator is not None:
            custody_mutator(tmp, custody)
        spec_path = _write_spec(tmp, spec)
        out = custody / "closeout_index.json"
        try:
            fc.finalize(spec_path, custody, out, clock=CLOCK)
        except fc.CloseoutError as exc:
            assert exc.code == code, (exc.code, code)
            assert exc.code == str(exc)  # value-free stable code
            assert not out.exists()  # nothing published on failure
        else:  # pragma: no cover
            raise AssertionError(f"expected CloseoutError({code})")


# --------------------------------------------------------------- negative matrix


def test_finalize_missing_category_fails():
    spec = _full_spec()
    spec["categories"] = [c for c in spec["categories"] if c["category"] != 7]
    _expect_closeout_error(spec, "missing_category")


def test_finalize_duplicate_category_fails():
    spec = _full_spec()
    spec["categories"].append(
        {"category": 3, "source": "script", "artifacts": ["05_counts.txt"]}
    )
    _expect_closeout_error(spec, "duplicate_category")


def test_finalize_failed_http_artifact_fails():
    # a failed OpenAPI capture saved an HTML error page instead of JSON
    def mutate(tmp, custody):
        (custody / "openapi_seam.json").write_bytes(b"<html>502 Bad Gateway</html>\n")

    _expect_closeout_error(_full_spec(), "failed_http", custody_mutator=mutate)


def test_finalize_unhashed_script_artifact_fails():
    # a script-sourced artifact that is NOT covered by the evidence manifest
    def mutate(tmp, custody):
        (custody / "99_rogue.txt").write_bytes(b"rogue\n")

    spec = _full_spec()
    spec["categories"][4]["artifacts"].append("99_rogue.txt")  # category 5 (script)
    _expect_closeout_error(spec, "unhashed_artifact", custody_mutator=mutate)


def test_finalize_hash_mismatch_fails():
    # a script artifact whose bytes disagree with the recorded manifest hash (tampered)
    def mutate(tmp, custody):
        (custody / "05_counts.txt").write_bytes(b"TAMPERED\n")

    _expect_closeout_error(_full_spec(), "hash_mismatch", custody_mutator=mutate)


def test_finalize_path_traversal_rejected():
    def mutate(tmp, custody):
        (tmp / "evil.txt").write_bytes(b"evil\n")  # outside the custody dir

    spec = _full_spec()
    spec["categories"][6]["artifacts"] = ["../evil.txt"]  # category 7 (operator)
    _expect_closeout_error(spec, "artifact_path_escape", custody_mutator=mutate)


def test_finalize_non_regular_artifact_rejected():
    def mutate(tmp, custody):
        (custody / "a_dir").mkdir()

    spec = _full_spec()
    spec["categories"][6]["artifacts"] = ["a_dir"]  # category 7 (operator), a directory
    _expect_closeout_error(spec, "artifact_not_regular", custody_mutator=mutate)


def test_finalize_provenance_missing_fails():
    def mutate(tmp, custody):
        (custody / "00_provenance.json").unlink()  # governance anchor gone

    _expect_closeout_error(_full_spec(), "provenance_missing", custody_mutator=mutate)


# -------------------------------------------------------------- happy path + index


def test_finalize_index_binds_every_artifact_by_sha256():
    with _tmp() as tmp:
        custody = _make_custody(tmp)
        spec = _write_spec(tmp, _full_spec())
        out = custody / "closeout_index.json"
        run = fc.finalize(spec, custody, out, clock=CLOCK)
        assert run == out
        idx = json.loads(out.read_text())
        assert idx["all_categories_present"] is True
        assert idx["all_artifacts_hashed"] is True
        assert {c["category"] for c in idx["categories"]} == set(range(1, 10))
        # every listed artifact carries a matching SHA-256 + byte count
        for cat in idx["categories"]:
            for art in cat["artifacts"]:
                data = (custody / art["name"]).read_bytes()
                assert art["sha256"] == hashlib.sha256(data).hexdigest()
                assert art["bytes"] == len(data)
        # the index itself is published read-only
        assert stat.S_IMODE(out.stat().st_mode) == 0o400


def test_finalize_no_clobber():
    with _tmp() as tmp:
        custody = _make_custody(tmp)
        spec = _write_spec(tmp, _full_spec())
        out = custody / "closeout_index.json"
        fc.finalize(spec, custody, out, clock=CLOCK)
        raised = False
        try:
            fc.finalize(spec, custody, out, clock=CLOCK)
        except FileExistsError:
            raised = True
        assert raised, "closeout index must not be clobbered"


# ---------------------------------------------------------------- main() integration


def _run_main(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fc.main(argv)
    return rc, buf.getvalue()


def test_main_reports_pass_and_failure_codes():
    with _tmp() as tmp:
        custody = _make_custody(tmp)
        good = _write_spec(tmp, _full_spec())
        rc, out = _run_main(["--spec", str(good), "--custody-dir", str(custody)])
        assert rc == 0
        assert "RESULT PASS" in out
        assert (custody / "closeout_index.json").exists()

        bad_spec = _full_spec()
        bad_spec["categories"] = [
            c for c in bad_spec["categories"] if c["category"] != 2
        ]
        bad = tmp / "bad.json"
        bad.write_text(json.dumps(bad_spec))
        custody2 = _make_custody(tmp / "second")
        rc2, out2 = _run_main(["--spec", str(bad), "--custody-dir", str(custody2)])
        assert rc2 != 0
        assert "RESULT FAIL" in out2
        assert "missing_category" in out2


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
