"""Offline tests for the census-acceptance gate (verify_census.py).

A GREEN baseline (a genuine, signed, in-scope raw census with zero-width windows + not_observed
overlays PASSES — unlike preapply), plus the operator's adversarial cases: wrong scope, wrong bundle
hash, wrong repo SHA, mixed-schema output, query failure, missing signature, wrong key.
"""

import copy
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect_disposition as cds  # noqa: E402
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
            "relation_count": len(rels),
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


# ---- main() with real signatures ===========================================
def _write_signed(snapshot, d, priv, pub_pem):
    snap_bytes = json.dumps(snapshot, indent=2, sort_keys=True).encode("utf-8")
    snap_path = os.path.join(d, "prod.json")
    with open(snap_path, "wb") as fh:
        fh.write(snap_bytes)
    sig_path = snap_path + ".sig"
    with open(sig_path, "w", encoding="utf-8") as fh:
        json.dump(ds.build_sig_sidecar(snap_bytes, priv), fh)
    pub_path = os.path.join(d, "verify.pub")
    with open(pub_path, "wb") as fh:
        fh.write(pub_pem)
    return snap_path, sig_path, pub_path


def _argv(snap_path, sig_path, pub_path):
    return ["--snapshot", snap_path, "--snapshot-sig", sig_path, "--verify-key", pub_path,
            "--expect-project-ref", PROJECT, "--expect-database", "postgres", "--expect-schemas", "public",
            "--expect-repo-sha", SHA, "--require-role-markers", ",".join(MARKERS)]


def test_main_green_e2e():
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, pub = _write_signed(_snap(), d, priv, pub_pem)
        assert vc.main(_argv(sp, sig, pub)) == 0


def test_main_tampered_snapshot_CN001():
    priv, _pp, pub_pem = _ephemeral_keypair()
    with tempfile.TemporaryDirectory() as d:
        sp, sig, pub = _write_signed(_snap(), d, priv, pub_pem)
        with open(sp, "ab") as fh:
            fh.write(b" ")  # tamper after signing
        assert vc.main(_argv(sp, sig, pub)) == 1


def test_main_wrong_key_CN001():
    priv, _pp, _pub = _ephemeral_keypair()
    _priv2, _pp2, other_pub = _ephemeral_keypair()  # verify against a DIFFERENT key
    with tempfile.TemporaryDirectory() as d:
        sp, sig, pub = _write_signed(_snap(), d, priv, other_pub)
        assert vc.main(_argv(sp, sig, pub)) == 1


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
    ("main_green_e2e", test_main_green_e2e),
    ("main_tampered_snapshot_CN001", test_main_tampered_snapshot_CN001),
    ("main_wrong_key_CN001", test_main_wrong_key_CN001),
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
