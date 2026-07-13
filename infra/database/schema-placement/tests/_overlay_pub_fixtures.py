"""Shared synthetic fixtures for the overlay-publication suites (Tasks 2-9).

Synthetic Ed25519 keys ONLY -- the production signing key never appears in tests. The census
fixture is ACCEPTANCE-GRADE: it passes the full verify_census.check_census contract with the
expects returned by acceptance_expects(), and reuses test_overlay_loader._zero_census for the
schema-valid relation bodies (zero-width windows, six not_observed dims)."""
import contextlib
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import disposition_overlay as dov  # noqa: E402
import disposition_signing as ds  # noqa: E402
import disposition_trust as dt  # noqa: E402
import verify_census as vc  # noqa: E402
import test_overlay_loader as tol  # noqa: E402 -- reuse the proven schema-valid census builder

KEY_ID = "pub-test-ed25519"
PROJECT_REF = "fxoyniqnrlkxfligbxmg"
FAKE_REPO_SHA = "a" * 40
FAKE_QB = "b" * 64


def keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, pub_pem


def priv_pem(priv):
    from cryptography.hazmat.primitives import serialization
    return priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                              serialization.NoEncryption()).decode("utf-8")


def spki_fp(pub_pem):
    return ds.public_key_fingerprint(ds.load_public_key_pem(pub_pem))


def canon(obj) -> bytes:
    return json.dumps(obj, indent=2, sort_keys=True).encode("utf-8")


def sidecar_bytes_for(message: bytes, priv) -> bytes:
    return canon(ds.build_sig_sidecar(message, priv))


@contextlib.contextmanager
def trusted(key_id, fingerprint):
    prev = dict(dt.TRUSTED_SIGNERS)
    dt.TRUSTED_SIGNERS[key_id] = fingerprint
    try:
        yield
    finally:
        dt.TRUSTED_SIGNERS.clear()
        dt.TRUSTED_SIGNERS.update(prev)


def write_keys_dir(d, pub_pem, key_id=KEY_ID):
    keys_dir = os.path.join(d, "keys")
    os.makedirs(keys_dir, exist_ok=True)
    with open(os.path.join(keys_dir, key_id + ".pub.pem"), "wb") as fh:
        fh.write(pub_pem)
    return keys_dir


def acceptance_census(oids, *, repo_sha=FAKE_REPO_SHA, qb=FAKE_QB):
    """A census that passes the FULL check_census contract with acceptance_expects(census)."""
    c = tol._zero_census(oids)
    n = len(c["relations"])
    c.update({
        "project_ref": PROJECT_REF, "repo_sha": repo_sha, "query_bundle_sha256": qb,
        "collector_version": "0.1.0", "relation_count": n, "catalog_relation_count": n,
        "generator": "collect_disposition/0.1.0",
        "collection_scope": {
            "schemas": ["public"], "expected_database": "postgres",
            "required_role_markers": ["anon", "authenticated", "service_role"],
            "repo_sha": repo_sha, "query_bundle_sha256": qb, "collector_version": "0.1.0"},
        "target_identity": {
            "current_database": "postgres", "current_user": "postgres",
            "server_version": "PostgreSQL 17.6 (synthetic)", "server_version_num": 170006,
            "transaction_read_only": True, "expected_database": "postgres",
            "platform_role_markers": ["anon", "authenticated", "authenticator", "postgres", "service_role"],
            "guard_passed": True},
    })
    # NOTE: c["observed_at"] is NOT overridden -- _zero_census keys every zero-width consumer
    # window to its own observed_at (OV021 coherence).
    return c


def acceptance_expects(census):
    cs = census["collection_scope"]
    return {"project_ref": census["project_ref"], "database": cs["expected_database"],
            "schemas": list(cs["schemas"]), "census_repo_sha": cs["repo_sha"],
            "role_markers": list(cs["required_role_markers"]),
            "query_bundle_sha256": cs["query_bundle_sha256"]}


def overlay_core(dimension, assignments, window=None):
    return {"dimension": dimension, "assignments": assignments,
            "observation_window": window or {"started_at": "2026-07-11T00:00:00+00:00",
                                             "ended_at": "2026-07-12T00:00:00+00:00"},
            "authority": "synthetic-test-authority", "collection_method": "synthetic-test-method"}


def write_signed(dirpath, basename, obj, priv):
    obj_bytes = canon(obj)
    path = os.path.join(dirpath, basename)
    sig_path = path + ".sig"
    with open(path, "wb") as fh:
        fh.write(obj_bytes)
    sig_bytes = sidecar_bytes_for(obj_bytes, priv)
    with open(sig_path, "wb") as fh:
        fh.write(sig_bytes)
    return path, sig_path, obj_bytes, sig_bytes


if __name__ == "__main__":
    contract = dov.load_overlay_contract()
    census = acceptance_census(["public.t1", "public.t2"])
    schema_errs = list(contract.disposition_validator.iter_errors(census))
    exp = acceptance_expects(census)
    diags = vc.check_census(census, expect_project_ref=exp["project_ref"], expect_database=exp["database"],
                            expect_schemas=exp["schemas"], expect_repo_sha=exp["census_repo_sha"],
                            require_role_markers=exp["role_markers"],
                            expect_query_bundle_sha256=exp["query_bundle_sha256"])
    priv, pub = keypair()
    msg = canon(census)
    ok, reason = ds.verify_sidecar_bytes_with_key(msg, sidecar_bytes_for(msg, priv),
                                                  ds.load_public_key_pem(pub))
    good = not schema_errs and not diags and ok
    print(f"  {'ok  ' if not schema_errs else 'FAIL'}: census fixture schema-valid ({len(schema_errs)} errors)")
    for dg in diags[:10]:
        print("    ", dg.render())
    print(f"  {'ok  ' if not diags else 'FAIL'}: census fixture acceptance-green ({len(diags)} diags)")
    print(f"  {'ok  ' if ok else 'FAIL'}: sign/verify round-trip ({reason or 'ok'})")
    print("\n=== OVERLAY PUB FIXTURES: {} ===".format("ALL PASS" if good else "FAILURES PRESENT"))
    raise SystemExit(0 if good else 1)
