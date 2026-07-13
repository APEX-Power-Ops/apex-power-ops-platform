"""Offline suite for verify_overlay_artifact.py. Script __main__ runner."""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _overlay_pub_fixtures as fx  # noqa: E402
import author_overlay as ao  # noqa: E402
import disposition_overlay as dov  # noqa: E402
import disposition_trust as dt  # noqa: E402
import verify_overlay_artifact as voa  # noqa: E402

_CASES = []
NOW = dov._parse_iso("2026-07-12T12:00:00+00:00")


def _ctx():
    priv, pub = fx.keypair()
    census = fx.acceptance_census(["public.t1", "public.t2"])
    census_bytes = fx.canon(census)
    contract = dov.load_overlay_contract()
    return priv, pub, census, census_bytes, contract


def _mk_overlay(census, census_bytes, contract, **kw):
    core = fx.overlay_core(kw.pop("dimension", "in_data_api_exposed_schema"),
                           kw.pop("assignments", [{"object_id": "public.t1",
                                                   "value": {"state": "observed", "value": False}}]),
                           window=kw.pop("window", None))
    doc = ao.assemble_overlay(core, census=census,
                              census_sha256=hashlib.sha256(census_bytes).hexdigest(), contract=contract,
                              producing=kw.pop("producing", ("d" * 40, None)),
                              source_hash=kw.pop("source_hash", "e" * 64),
                              source_hash_reason=kw.pop("source_hash_reason", None),
                              source_locator=kw.pop("source_locator", "evidence/source/x.source.json"),
                              captured_at_iso=kw.pop("captured", "2026-07-12T06:00:00+00:00"))
    doc.update(kw)  # raw overrides for tamper-shaped cases
    return doc


def _va(doc_or_bytes, census, census_bytes, contract):
    b = doc_or_bytes if isinstance(doc_or_bytes, bytes) else ao._canon(doc_or_bytes)
    return voa.verify_artifact(b, census=census,
                               census_bytes_sha=hashlib.sha256(census_bytes).hexdigest(),
                               contract=contract, expect_project_ref=fx.PROJECT_REF, now=NOW)


def _green_artifact_verifies():
    _p, _u, census, cb, k = _ctx()
    return _va(_mk_overlay(census, cb, k), census, cb, k) == []


def _signed_non_object_is_coded_OV008():
    _p, _u, census, cb, k = _ctx()
    diags = _va(fx.canon([1, 2, 3]), census, cb, k)  # a JSON array -- must NOT crash
    return diags and all(d[0] == "OV008" for d in diags)


def _wrong_base_hash_OV002():
    _p, _u, census, cb, k = _ctx()
    doc = _mk_overlay(census, cb, k, base_snapshot_sha256="0" * 64)
    return any(d[0] == "OV002" for d in _va(doc, census, cb, k))


def _schema_sha_drift_OV020():
    _p, _u, census, cb, k = _ctx()
    doc = _mk_overlay(census, cb, k, overlay_schema_sha256="0" * 64)
    return any(d[0] == "OV020" for d in _va(doc, census, cb, k))


def _future_captured_OV010():
    _p, _u, census, cb, k = _ctx()
    doc = _mk_overlay(census, cb, k, captured="2027-01-01T00:00:00+00:00")
    return any(d[0] == "OV010" for d in _va(doc, census, cb, k))


def _intra_dup_OV007():
    _p, _u, census, cb, k = _ctx()
    a = {"object_id": "public.t1", "value": {"state": "observed", "value": False}}
    doc = _mk_overlay(census, cb, k, assignments=[a, dict(a)])
    return any(d[0] == "OV007" for d in _va(doc, census, cb, k))


def _schema_invalid_short_circuits():
    _p, _u, census, cb, k = _ctx()
    doc = _mk_overlay(census, cb, k)
    del doc["authority"]  # schema-invalid -> OV008 only, nothing downstream
    diags = _va(doc, census, cb, k)
    return diags and all(d[0] == "OV008" for d in diags)


# ---- main() e2e ----
def _files(d):
    priv, pub = fx.keypair()
    keys_dir = fx.write_keys_dir(d, pub)
    census = fx.acceptance_census(["public.t1"])
    cpath, cspath, cb, _ = fx.write_signed(d, "census-prod-fixture.json", census, priv)
    contract = dov.load_overlay_contract()
    doc = _mk_overlay(census, cb, contract,
                      assignments=[{"object_id": "public.t1", "value": {"state": "observed", "value": False}}])
    opath, ospath, _ob, _sb = fx.write_signed(d, "overlay-fixture.json", doc, priv)
    exp = fx.acceptance_expects(census)
    argv = ["--overlay", opath, "--overlay-sig", ospath, "--census", cpath, "--census-sig", cspath,
            "--key-id", fx.KEY_ID, "--keys-dir", keys_dir,
            "--expect-project-ref", exp["project_ref"], "--expect-database", exp["database"],
            "--expect-schemas", ",".join(exp["schemas"]), "--expect-census-repo-sha", exp["census_repo_sha"],
            "--require-role-markers", ",".join(exp["role_markers"]),
            "--expect-query-bundle-sha256", exp["query_bundle_sha256"]]
    return argv, pub, opath


def _run_main(argv, pub):
    out = io.StringIO()
    with fx.trusted(fx.KEY_ID, fx.spki_fp(pub)), contextlib.redirect_stdout(out):
        rc = voa.main(argv)
    return rc, out.getvalue()


def _main_green():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _files(d)
        rc, out = _run_main(argv, pub)
        return rc == 0 and "GREEN" in out


def _main_tampered_overlay_OV001():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, opath = _files(d)
        data = open(opath, "rb").read()
        open(opath, "wb").write(data[:-2] + b" }")
        rc, out = _run_main(argv, pub)
        return rc == 1 and "OV001" in out


def _main_tampered_census_OV001_census_locus():
    # Matrix row "tampered census bytes" at the VERIFIER: the census-side OV001 branch fires
    # with its own locus (distinct from the overlay-side OV001).
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _files(d)
        cpath = argv[argv.index("--census") + 1]
        data = open(cpath, "rb").read()
        open(cpath, "wb").write(data[:-2] + b" }")
        rc, out = _run_main(argv, pub)
        return rc == 1 and "OV001 census" in out


def _main_bad_census_scope_CN005():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _files(d)
        argv[argv.index("--expect-schemas") + 1] = "public,extra"
        rc, out = _run_main(argv, pub)
        return rc == 1 and "CN005" in out


def _main_unpinned_key_blocks():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _files(d)
        argv[argv.index("--key-id") + 1] = "unpinned-id"
        rc, out = _run_main(argv, pub)
        return rc == 1 and "authorized signer" in out


_CASES += [
    ("green_artifact_verifies", _green_artifact_verifies),
    ("signed_non_object_is_coded_OV008", _signed_non_object_is_coded_OV008),
    ("wrong_base_hash_OV002", _wrong_base_hash_OV002),
    ("schema_sha_drift_OV020", _schema_sha_drift_OV020),
    ("future_captured_OV010", _future_captured_OV010),
    ("intra_dup_OV007", _intra_dup_OV007),
    ("schema_invalid_short_circuits", _schema_invalid_short_circuits),
    ("main_green", _main_green),
    ("main_tampered_overlay_OV001", _main_tampered_overlay_OV001),
    ("main_tampered_census_OV001_census_locus", _main_tampered_census_OV001_census_locus),
    ("main_bad_census_scope_CN005", _main_bad_census_scope_CN005),
    ("main_unpinned_key_blocks", _main_unpinned_key_blocks),
]

if __name__ == "__main__":
    ok = True
    for name, fn in _CASES:
        try:
            r = bool(fn())
        except Exception as exc:  # noqa: BLE001
            r = False; name = f"{name} (EXC {exc})"
        ok = ok and r
        print(f"  {'ok  ' if r else 'FAIL'}: {name}")
    print("\n=== VERIFY OVERLAY ARTIFACT SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
