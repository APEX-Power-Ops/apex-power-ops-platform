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
    "openapi_control.json": b'{"openapi": "3.1.0", "paths": {}}\n',
    "reset_route.json": b'{"path": "/reset", "method": "POST", "security": []}\n',
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
            {
                "category": 1,
                "source": "operator",
                "artifacts": ["openapi_seam.json", "openapi_control.json"],
            },
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


def test_finalize_category_source_downgrade_rejected():
    # Codex-xhigh P1: a DB category (3) marked "operator" would skip the manifest hash
    # binding; the source is pinned per category, so this is rejected.
    spec = _full_spec()
    spec["categories"][2]["source"] = "operator"  # category 3 is script-captured
    _expect_closeout_error(spec, "category_source_mismatch")


def test_finalize_failed_http_artifact_fails():
    # a failed OpenAPI capture saved an HTML error page instead of JSON
    def mutate(tmp, custody):
        (custody / "openapi_seam.json").write_bytes(b"<html>502 Bad Gateway</html>\n")

    _expect_closeout_error(_full_spec(), "failed_http", custody_mutator=mutate)


def test_finalize_unhashed_script_artifact_fails():
    # a script artifact present on disk but NOT covered by manifest.sha256 (tampered manifest):
    # the correct category-5 artifact set passes the pin, then the manifest binding fails.
    def mutate(tmp, custody):
        m = custody / "manifest.sha256"
        kept = [ln for ln in m.read_text().splitlines() if "05_counts.txt" not in ln]
        m.write_text("\n".join(kept) + "\n")

    _expect_closeout_error(_full_spec(), "unhashed_artifact", custody_mutator=mutate)


def test_finalize_wrong_script_artifact_for_category_rejected():
    # Codex-xhigh-final P1b: a manifest-present but wrong-for-the-category file is rejected
    spec = _full_spec()
    spec["categories"][2]["artifacts"] = [
        "05_counts.txt"
    ]  # category 3 must bind 03_/04_
    _expect_closeout_error(spec, "category_artifacts_mismatch")


def test_finalize_category2_partial_shape_fails():
    # Codex-xhigh-final P1a: the /reset path present but NO security state must fail
    # (the shape check requires ALL markers, not any single one)
    def mutate(tmp, custody):
        (custody / "reset_route.json").write_bytes(
            b'{"path": "/reset", "error": "unauthorized"}\n'
        )

    _expect_closeout_error(_full_spec(), "failed_http", custody_mutator=mutate)


def test_finalize_category1_requires_both_hosts():
    # Codex-c7 P1b: category 1 = deployed OpenAPI for BOTH hosts; a single doc is incomplete
    spec = _full_spec()
    spec["categories"][0]["artifacts"] = ["openapi_seam.json"]
    _expect_closeout_error(spec, "category_incomplete")


def test_finalize_duplicate_artifact_in_category_rejected():
    # Codex-c8 P2: the same file listed twice must not satisfy the multi-capture minimum
    spec = _full_spec()
    spec["categories"][0]["artifacts"] = ["openapi_seam.json", "openapi_seam.json"]
    _expect_closeout_error(spec, "duplicate_artifact")


def test_finalize_category2_wrong_route_fails():
    # Codex-c7 P2: a different route (/reset-status) must not satisfy the exact /reset evidence
    def mutate(tmp, custody):
        (custody / "reset_route.json").write_bytes(
            b'{"path": "/reset-status", "security": []}\n'
        )

    _expect_closeout_error(_full_spec(), "failed_http", custody_mutator=mutate)


def test_finalize_category2_missing_method_fails():
    # Codex-c9 P2: the exact /reset path with security but NO proven POST method must fail
    def mutate(tmp, custody):
        (custody / "reset_route.json").write_bytes(
            b'{"path": "/reset", "security": []}\n'
        )

    _expect_closeout_error(_full_spec(), "failed_http", custody_mutator=mutate)


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


def test_finalize_category2_json_error_body_fails():
    # lens-B A1: a failed /reset capture that saved a JSON error body (valid JSON, wrong
    # shape) must fail — category 2 previously accepted ANY well-formed JSON.
    def mutate(tmp, custody):
        (custody / "reset_route.json").write_bytes(b'{"error": "unauthorized"}\n')

    _expect_closeout_error(_full_spec(), "failed_http", custody_mutator=mutate)


def test_finalize_json_operator_artifact_must_parse():
    # lens-B A3: a JSON-named operator artifact (category 7) that is an HTML error page fails
    def mutate(tmp, custody):
        (custody / "backend.json").write_bytes(b"<html>502 Bad Gateway</html>\n")

    _expect_closeout_error(_full_spec(), "failed_json", custody_mutator=mutate)


def test_finalize_tampered_provenance_fails():
    # lens-B A2: provenance edited after the manifest was written -> content hash mismatch
    def mutate(tmp, custody):
        (custody / "00_provenance.json").write_bytes(b'{"artifact": "TAMPERED"}\n')

    _expect_closeout_error(_full_spec(), "hash_mismatch", custody_mutator=mutate)


def test_finalize_leaves_no_partial_on_success():
    # lens-B A6: the atomic publish removes its .partial staging file
    with _tmp() as tmp:
        custody = _make_custody(tmp)
        spec = _write_spec(tmp, _full_spec())
        out = custody / "closeout_index.json"
        fc.finalize(spec, custody, out, clock=CLOCK)
        assert out.exists()
        assert list(custody.glob("*.partial")) == []


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
        # the git/role attestation + the manifest binding the script artifacts are RECORDED
        prov = (custody / "00_provenance.json").read_bytes()
        assert idx["provenance"]["name"] == "00_provenance.json"
        assert idx["provenance"]["sha256"] == hashlib.sha256(prov).hexdigest()
        man = (custody / "manifest.sha256").read_bytes()
        assert idx["manifest_sha256"] == hashlib.sha256(man).hexdigest()
        # the index itself is published read-only
        assert stat.S_IMODE(out.stat().st_mode) == 0o400


def test_finalize_index_records_custody_relative_subpath():
    # Codex-c5 P2: an operator artifact in a subdir is recorded by its custody-relative
    # path, not a bare basename that could collide with a flat file of the same name.
    with _tmp() as tmp:
        custody = _make_custody(tmp)
        (custody / "captures").mkdir()
        (custody / "captures" / "openapi_seam.json").write_bytes(
            b'{"openapi": "3.1.0", "paths": {}}\n'
        )
        spec = _full_spec()
        spec["categories"][0]["artifacts"] = [
            "captures/openapi_seam.json",  # cat 1, in a subdir
            "openapi_control.json",  # + the second host (category 1 needs both)
        ]
        out = custody / "closeout_index.json"
        fc.finalize(_write_spec(tmp, spec), custody, out, clock=CLOCK)
        idx = json.loads(out.read_text())
        cat1 = next(c for c in idx["categories"] if c["category"] == 1)
        names = {a["name"] for a in cat1["artifacts"]}
        assert (
            "captures/openapi_seam.json" in names
        )  # recorded by its custody-relative path


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
