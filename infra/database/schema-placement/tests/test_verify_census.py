"""Offline tests for the census-acceptance gate (verify_census.py).

A GREEN baseline (a genuine, signed, in-scope raw census with zero-width windows + not_observed
overlays PASSES — unlike preapply), plus the operator's adversarial cases: wrong scope, wrong bundle
hash, wrong repo SHA, mixed-schema output, query failure, missing signature, wrong key.
"""

import contextlib
import copy
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect_disposition as cds  # noqa: E402
import disposition_provenance as dp  # noqa: E402
import disposition_signing as ds  # noqa: E402
import verify_census as vc  # noqa: E402

QB = cds.query_bundle_sha256()
PROJECT = "fxoyniqnrlkxfligbxmg"
SHA = "8a4c37fc"
MARKERS = ["anon", "authenticated", "service_role"]
EXPECT = dict(expect_project_ref=PROJECT, expect_database="postgres", expect_schemas=["public"],
              expect_repo_sha=SHA, require_role_markers=MARKERS)


def _ephemeral_keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    pub_pem = priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, priv_pem, pub_pem


def _rel(schema="public", name="v_x"):
    return {"object_id": f"{schema}.{name}", "schema": schema, "name": name, "relkind": "v",
            "owner": {"state": "observed", "value": "postgres"}, "rls_enabled": {"state": "observed", "value": False},
            "is_security_definer_view": {"state": "observed", "value": True},
            "in_data_api_exposed_schema": {"state": "not_observed", "detail": "overlay"},
            "anon_effective_privs": {"state": "observed", "value": ["SELECT"]},
            "authenticated_effective_privs": {"state": "observed", "value": ["SELECT"]},
            "inbound_fk_count": {"state": "observed", "value": 0}, "outbound_fk_count": {"state": "observed", "value": 0},
            "dependent_objects": {"state": "observed", "value": []},
            "row_estimate": {"state": "not_applicable", "detail": "view"},
            "advisor_findings": {"state": "not_observed", "detail": "overlay"},
            "consumer_evidence": {"observation_window": {"started_at": "2026-07-11T00:00:00Z", "ended_at": "2026-07-11T00:00:00Z"},
                                  "database_deps": {"state": "observed", "found_consumers": 0, "ref": "query:dependents-v2"},
                                  "static_repo": {"state": "not_observed", "found_consumers": None, "ref": None, "detail": "overlay"},
                                  "runtime_logs": {"state": "not_observed", "found_consumers": None, "ref": None, "detail": "overlay"},
                                  "external_clients": {"state": "not_observed", "found_consumers": None, "ref": None, "detail": "overlay"},
                                  "operator_declaration": {"state": "not_observed", "found_consumers": None, "ref": None, "detail": "overlay"}}}


def _snap(relations=None, repo_sha=SHA, schemas=("public",)):
    rels = relations if relations is not None else [_rel()]
    return {"kind": "evidence_snapshot", "project_ref": PROJECT, "observed_at": "2026-07-11T00:00:00Z",
            "repo_sha": repo_sha, "collector_version": "0.1.0", "query_bundle_sha256": QB,
            "relation_count": len(rels), "catalog_relation_count": len(rels),
            "collection_scope": {"schemas": sorted(schemas), "expected_database": "postgres",
                                 "required_role_markers": list(MARKERS), "repo_sha": repo_sha,
                                 "query_bundle_sha256": QB, "collector_version": "0.1.0"},
            "target_identity": {"current_database": "postgres", "current_user": "authenticator",
                                "server_version": "PostgreSQL 16.13", "transaction_read_only": True,
                                "expected_database": "postgres", "platform_role_markers": list(MARKERS), "guard_passed": True},
            "relations": rels}


def _codes(snapshot, **over):
    ex = dict(EXPECT); ex.update(over)
    return [d.code for d in vc.check_census(snapshot, **ex)]


# ---- pure check_census =====================================================
def test_green_baseline_accepts():
    # a raw census with zero-width windows + not_observed overlays is ACCEPTED here (would fail preapply)
    assert _codes(_snap()) == []


def test_wrong_scope_CN005():
    assert "CN005" in _codes(_snap(), expect_schemas=["ops"])


def test_wrong_bundle_CN006():
    s = _snap(); s["query_bundle_sha256"] = "b" * 64
    assert "CN006" in _codes(s)


def test_wrong_repo_sha_CN007():
    assert "CN007" in _codes(_snap(), expect_repo_sha="deadbee")


def test_mixed_schema_CN012():
    # a relation outside the snapshot's own declared scope
    s = _snap(relations=[_rel(), _rel(schema="ops", name="secret")])
    assert "CN012" in _codes(s)


def test_query_failure_CN011():
    s = _snap()
    s["relations"][0]["anon_effective_privs"] = {"state": "query_failed", "detail": "privileges query failed"}
    assert "CN011" in _codes(s)


def test_query_failure_database_deps_CN011():
    s = _snap()
    s["relations"][0]["consumer_evidence"]["database_deps"] = {"state": "query_failed", "found_consumers": None, "ref": None, "detail": "dependents failed"}
    assert "CN011" in _codes(s)


def test_project_mismatch_CN003():
    assert "CN003" in _codes(_snap(), expect_project_ref="wrong-ref")


def test_database_mismatch_CN004():
    assert "CN004" in _codes(_snap(), expect_database="dev_db")


def test_role_markers_CN008():
    s = _snap(); s["target_identity"]["platform_role_markers"] = ["anon"]
    assert "CN008" in _codes(s)


def test_relation_count_CN009():
    s = _snap(); s["relation_count"] = 99
    assert "CN009" in _codes(s)


def test_empty_census_CN014():
    s = _snap(relations=[]); s["relation_count"] = 0
    assert "CN014" in _codes(s)


def test_duplicate_object_id_CN015():
    r1 = _rel(name="v_dup")
    r2 = _rel(name="v_dup"); r2["owner"] = {"state": "observed", "value": "other"}  # same identity, differing record
    assert "CN015" in _codes(_snap(relations=[r1, r2]))


def test_ti_expected_database_CN004():
    s = _snap(); s["target_identity"]["expected_database"] = "dev_db"
    assert "CN004" in _codes(s)


def test_internal_inconsistency_CN016():
    s = _snap(); s["collector_version"] = "9.9.9"  # top-level disagrees with collection_scope
    assert "CN016" in _codes(s)


def test_count_mismatch_CN009():
    s = _snap(); s["catalog_relation_count"] = 99  # independent DB count disagrees with the emitted list
    assert "CN009" in _codes(s)


# ---- main() with real signatures ===========================================
KEY_ID = "test-ed25519"
PROD_KEY_ID = "prod-disposition-ed25519-2026-07"


@contextlib.contextmanager
def _trusted(key_id, fingerprint):
    """Temporarily pin a signer id -> SPKI fingerprint in the reviewed source-constant anchor, so an
    ephemeral test key is treated as an authorized signer. Restores the real anchor afterward. Works
    under both pytest and the __main__ runner (no fixtures)."""
    prev = dict(vc.TRUSTED_SIGNERS)
    vc.TRUSTED_SIGNERS[key_id] = fingerprint
    try:
        yield
    finally:
        vc.TRUSTED_SIGNERS.clear()
        vc.TRUSTED_SIGNERS.update(prev)


def _fp(pub_pem):
    return ds.public_key_fingerprint(ds.load_public_key_pem(pub_pem))


def _write_signed(snapshot, d, priv, pub_pem, fingerprint=None, key_id=KEY_ID):
    snap_bytes = json.dumps(snapshot, indent=2, sort_keys=True).encode("utf-8")
    snap_path = os.path.join(d, "prod.json")
    with open(snap_path, "wb") as fh:
        fh.write(snap_bytes)
    sig_path = snap_path + ".sig"
    with open(sig_path, "w", encoding="utf-8") as fh:
        json.dump(ds.build_sig_sidecar(snap_bytes, priv), fh)
    keys_dir = os.path.join(d, "keys")
    os.makedirs(keys_dir, exist_ok=True)
    with open(os.path.join(keys_dir, key_id + ".pub.pem"), "wb") as fh:
        fh.write(pub_pem)
    # The sibling .spki-sha256 is INERT under the source-constant anchor (the trust anchor is
    # vc.TRUSTED_SIGNERS, not this file); it is written only to prove a caller-supplied sibling
    # fingerprint grants no trust.
    fp = fingerprint if fingerprint is not None else ds.public_key_fingerprint(ds.load_public_key_pem(pub_pem))
    with open(os.path.join(keys_dir, key_id + ".spki-sha256"), "w", encoding="utf-8") as fh:
        fh.write(fp + "\n")
    return snap_path, sig_path, keys_dir


def _argv(snap_path, sig_path, keys_dir, key_id=KEY_ID):
    return ["--snapshot", snap_path, "--snapshot-sig", sig_path, "--key-id", key_id, "--keys-dir", keys_dir,
            "--expect-project-ref", PROJECT, "--expect-database", "postgres", "--expect-schemas", "public",
            "--expect-repo-sha", SHA, "--require-role-markers", ",".join(MARKERS),
            "--expect-query-bundle-sha256", QB]


def test_main_green_e2e():
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        with _trusted(KEY_ID, _fp(pub_pem)):  # authorize the ephemeral test key in the source anchor
            assert vc.main(_argv(sp, sig, kd)) == 0


def test_main_tampered_snapshot_CN001():
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        with open(sp, "ab") as fh:
            fh.write(b" ")  # tamper after signing
        with _trusted(KEY_ID, _fp(pub_pem)):  # key is authorized; the SIGNATURE must fail (CN001)
            assert vc.main(_argv(sp, sig, kd)) == 1


def test_main_wrong_key_CN001():
    priv, _pp, _pub = _ephemeral_keypair()
    _priv2, _pp2, other_pub = _ephemeral_keypair()  # pinned key is a DIFFERENT (authorized) key
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, other_pub)  # signed by priv, pinned key = other
        with _trusted(KEY_ID, _fp(other_pub)):  # other_pub is the authorized signer; priv's sig fails
            assert vc.main(_argv(sp, sig, kd)) == 1


def test_main_fingerprint_mismatch_CN013():
    # the pinned SPKI fingerprint (source anchor) must match the supplied public key — a wrong pin fails closed
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        with _trusted(KEY_ID, "00" * 32):  # pinned fingerprint != the real pubkey's SPKI
            assert vc.main(_argv(sp, sig, kd)) == 1


def test_main_unknown_key_id_CN013():
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        assert vc.main(_argv(sp, sig, kd, key_id="does-not-exist")) == 1


def test_main_forged_keys_dir_rejected_CN013():
    # H1 (Codex PROVEN GREEN): a self-consistent forged keypair in a caller-controlled --keys-dir must
    # now be REJECTED. The trust anchor is the reviewed TRUSTED_SIGNERS source constant, NOT the sibling
    # fingerprint file — an ephemeral key whose SPKI is not pinned cannot validate a census.
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem)  # sibling fingerprint self-consistent
        assert vc.main(_argv(sp, sig, kd)) == 1  # KEY_ID is not an authorized signer


def test_main_forged_key_under_real_key_id_rejected_CN013():
    # H1: even using the REAL production key-id, a forged public key whose SPKI != the pinned constant
    # is rejected (the anchor is the source fingerprint, not the supplied key material).
    priv, _pp, pub_pem = _ephemeral_keypair()
    real_id = "prod-disposition-ed25519-2026-07"
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem, key_id=real_id)
        assert vc.main(_argv(sp, sig, kd, key_id=real_id)) == 1


def test_main_key_id_traversal_rejected_CN013():
    # H1/F3: a path-traversal / absolute key-id is refused even if it were (contrived) a trusted id —
    # key_id must be a bare identifier and the resolved key path must stay within keys_dir.
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        with _trusted("../evil", _fp(pub_pem)):
            assert vc.main(_argv(sp, sig, kd, key_id="../evil")) == 1


def test_resolve_pinned_key_returns_key_object():
    # H3: resolve_pinned_key returns a loaded public-key OBJECT (not a path), so the caller verifies the
    # signature against the exact key it fingerprint-checked (no verify-then-reopen TOCTOU).
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        _sp, _sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        with _trusted(KEY_ID, _fp(pub_pem)):
            key, reason = vc.resolve_pinned_key(kd, KEY_ID)
        assert reason == "" and key is not None
        assert not isinstance(key, (str, bytes, os.PathLike))
        assert hasattr(key, "public_bytes")  # an Ed25519 public key object


def test_verify_uses_pinned_key_object_after_file_swap():
    # H3 regression: swapping the on-disk pubkey AFTER resolve must not change verification — the pinned
    # key OBJECT is used, never re-read from disk.
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        with open(sp, "rb") as fh:
            snap_bytes = fh.read()
        with _trusted(KEY_ID, _fp(pub_pem)):
            key, reason = vc.resolve_pinned_key(kd, KEY_ID)
        assert reason == ""
        _p2, _pp2, other_pub = _ephemeral_keypair()
        with open(os.path.join(kd, KEY_ID + ".pub.pem"), "wb") as fh:
            fh.write(other_pub)  # swap the file to a DIFFERENT key after resolve
        ok, _r = ds.verify_detached_with_key(snap_bytes, sig, key)
        assert ok is True  # verified against the in-hand pinned object, unaffected by the swap


def test_verify_detached_with_key_crypto_is_sole_gate():
    # F-1 guard (de3fa5de re-review): when the sidecar's public_key_sha256 is OMITTED or SPOOFED to
    # fp(pinned), the boundary that rejects a foreign signature is the FINAL crypto verify against the
    # PINNED key object. Locks the H1/H3 guarantee against a future refactor that conditions the crypto
    # verify behind the (skippable) fingerprint cross-check.
    K_priv, _kp, K_pub = _ephemeral_keypair()          # pinned key K
    A_priv, _ap, _A_pub = _ephemeral_keypair()          # attacker key A
    K_obj = ds.load_public_key_pem(K_pub)
    with tempfile.TemporaryDirectory() as d:
        msg = b'{"kind":"evidence_snapshot","n":1}'
        # (i) foreign signature (A) + fingerprint OMITTED -> cross-check skipped -> crypto REJECTS
        sc = ds.build_sig_sidecar(msg, A_priv); sc.pop("public_key_sha256")
        sig1 = os.path.join(d, "a.sig"); open(sig1, "w", encoding="utf-8").write(json.dumps(sc))
        assert ds.verify_detached_with_key(msg, sig1, K_obj)[0] is False
        # (ii) foreign signature (A) + fingerprint SPOOFED to fp(K) -> cross-check passes -> crypto REJECTS
        sc2 = ds.build_sig_sidecar(msg, A_priv); sc2["public_key_sha256"] = ds.public_key_fingerprint(K_obj)
        sig2 = os.path.join(d, "b.sig"); open(sig2, "w", encoding="utf-8").write(json.dumps(sc2))
        assert ds.verify_detached_with_key(msg, sig2, K_obj)[0] is False
        # (iii) genuine signature (K) + fingerprint OMITTED -> crypto verify against K ACCEPTS
        sc3 = ds.build_sig_sidecar(msg, K_priv); sc3.pop("public_key_sha256")
        sig3 = os.path.join(d, "c.sig"); open(sig3, "w", encoding="utf-8").write(json.dumps(sc3))
        assert ds.verify_detached_with_key(msg, sig3, K_obj)[0] is True


def test_committed_prod_key_resolves_and_no_private_material():
    # Finding #2: the COMMITTED production pubkey resolves through the REAL source anchor (no monkeypatch),
    # proving keys/<prod-id>.pub.pem matches the source-pinned TRUSTED_SIGNERS fingerprint; and keys/ holds
    # NO private-key material.
    assert PROD_KEY_ID in vc.TRUSTED_SIGNERS
    key, reason = vc.resolve_pinned_key(vc.DEFAULT_KEYS_DIR, PROD_KEY_ID)   # real TRUSTED_SIGNERS, real keys/
    assert reason == "" and key is not None and hasattr(key, "public_bytes")
    for root, _dirs, files in os.walk(vc.DEFAULT_KEYS_DIR):
        for fn in files:
            with open(os.path.join(root, fn), "rb") as fh:
                assert b"PRIVATE KEY" not in fh.read(), f"private key material found under keys/: {fn}"


def test_main_expect_query_bundle_required():
    # RR-2: --expect-query-bundle-sha256 is REQUIRED at the CLI (no self-referential default); argparse errors.
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        argv = ["--snapshot", sp, "--snapshot-sig", sig, "--key-id", KEY_ID, "--keys-dir", kd,
                "--expect-project-ref", PROJECT, "--expect-database", "postgres", "--expect-schemas", "public",
                "--expect-repo-sha", SHA, "--require-role-markers", ",".join(MARKERS)]  # NO --expect-query-bundle-sha256
        raised = False
        try:
            vc.main(argv)
        except SystemExit as exc:
            raised = (exc.code == 2)
        assert raised


def test_main_require_clean_checkout_preflight():
    # Finding #3: --require-clean-checkout binds the acceptance gate to reviewed source — fail-closed on a
    # dirty or mismatched verifier checkout, GREEN only when clean AND HEAD == --expect-repo-sha.
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        saved = (dp.git_head_sha, dp.git_worktree_clean)
        try:
            with _trusted(KEY_ID, _fp(pub_pem)):
                dp.git_head_sha = lambda *a: SHA; dp.git_worktree_clean = lambda *a: False   # dirty
                assert vc.main(_argv(sp, sig, kd) + ["--require-clean-checkout"]) == 1
                dp.git_head_sha = lambda *a: "deadbeef1234"; dp.git_worktree_clean = lambda *a: True  # wrong HEAD
                assert vc.main(_argv(sp, sig, kd) + ["--require-clean-checkout"]) == 1
                dp.git_head_sha = lambda *a: SHA; dp.git_worktree_clean = lambda *a: True    # clean + match
                assert vc.main(_argv(sp, sig, kd) + ["--require-clean-checkout"]) == 0
        finally:
            dp.git_head_sha, dp.git_worktree_clean = saved


def test_key_id_traversal_rejected_even_with_planted_key():
    # F-3 guard (de3fa5de re-review): plant a LOADABLE forged key at the traversal destination and trust
    # the traversal id, so the rejection MUST come from the sanitize/containment defenses (_KEY_ID_RE /
    # commonpath), NOT from a file-not-found. If both defenses were removed the planted key would load and
    # its SPKI would match the trusted fingerprint -> this test would then wrongly pass resolve.
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        _sp, _sig, kd = _write_signed(_snap(), d, priv, pub_pem)
        planted = os.path.join(os.path.dirname(kd), "evil.pub.pem")  # == kd/../evil.pub.pem
        with open(planted, "wb") as fh:
            fh.write(pub_pem)  # a loadable key whose SPKI == the trusted fingerprint below
        with _trusted("../evil", _fp(pub_pem)):
            key, reason = vc.resolve_pinned_key(kd, "../evil")
        assert key is None
        assert ("bare identifier" in reason) or ("escapes the keys directory" in reason)  # NOT "cannot load"


ALL = [
    ("green_baseline_accepts", test_green_baseline_accepts),
    ("wrong_scope_CN005", test_wrong_scope_CN005),
    ("wrong_bundle_CN006", test_wrong_bundle_CN006),
    ("wrong_repo_sha_CN007", test_wrong_repo_sha_CN007),
    ("mixed_schema_CN012", test_mixed_schema_CN012),
    ("query_failure_CN011", test_query_failure_CN011),
    ("query_failure_database_deps_CN011", test_query_failure_database_deps_CN011),
    ("project_mismatch_CN003", test_project_mismatch_CN003),
    ("database_mismatch_CN004", test_database_mismatch_CN004),
    ("role_markers_CN008", test_role_markers_CN008),
    ("relation_count_CN009", test_relation_count_CN009),
    ("empty_census_CN014", test_empty_census_CN014),
    ("duplicate_object_id_CN015", test_duplicate_object_id_CN015),
    ("ti_expected_database_CN004", test_ti_expected_database_CN004),
    ("internal_inconsistency_CN016", test_internal_inconsistency_CN016),
    ("count_mismatch_CN009", test_count_mismatch_CN009),
    ("main_green_e2e", test_main_green_e2e),
    ("main_tampered_snapshot_CN001", test_main_tampered_snapshot_CN001),
    ("main_wrong_key_CN001", test_main_wrong_key_CN001),
    ("main_fingerprint_mismatch_CN013", test_main_fingerprint_mismatch_CN013),
    ("main_unknown_key_id_CN013", test_main_unknown_key_id_CN013),
    ("main_forged_keys_dir_rejected_CN013", test_main_forged_keys_dir_rejected_CN013),
    ("main_forged_key_under_real_key_id_rejected_CN013", test_main_forged_key_under_real_key_id_rejected_CN013),
    ("main_key_id_traversal_rejected_CN013", test_main_key_id_traversal_rejected_CN013),
    ("resolve_pinned_key_returns_key_object", test_resolve_pinned_key_returns_key_object),
    ("verify_uses_pinned_key_object_after_file_swap", test_verify_uses_pinned_key_object_after_file_swap),
    ("verify_detached_with_key_crypto_is_sole_gate", test_verify_detached_with_key_crypto_is_sole_gate),
    ("key_id_traversal_rejected_even_with_planted_key", test_key_id_traversal_rejected_even_with_planted_key),
    ("committed_prod_key_resolves_and_no_private_material", test_committed_prod_key_resolves_and_no_private_material),
    ("main_expect_query_bundle_required", test_main_expect_query_bundle_required),
    ("main_require_clean_checkout_preflight", test_main_require_clean_checkout_preflight),
]


if __name__ == "__main__":
    ok = True
    for name, fn in ALL:
        try:
            fn()
            r = True
        except Exception as exc:  # noqa: BLE001
            r = False
            name = f"{name} ({type(exc).__name__}: {exc})"
        ok = ok and r
        print(f"  {'ok  ' if r else 'FAIL'}: {name}")
    print("\n=== CENSUS-ACCEPTANCE SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
