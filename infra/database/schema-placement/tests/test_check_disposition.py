"""Semantic-gate tests for check_disposition.py (offline, --now injected).

A GREEN preapply baseline per action class (harden/promote/compat/archive/delete/retain), each
with an accepted manifest + cluster approval, an accepted entity_map, fully-resolved consumer
evidence, and a manifest/snapshot path binding; plus one negative per SP0xx code, and unit
tests for the dup-key loaders (YAML+JSON) and the path-safety helper.
"""

import copy
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_disposition as cd  # noqa: E402
import disposition_signing as ds  # noqa: E402
import contextlib  # noqa: E402
import disposition_provenance as dp  # noqa: E402
import disposition_trust as dt  # noqa: E402
import yaml  # noqa: E402


def _stub_dp(head, clean=True):
    saved = (dp.git_head_sha, dp.git_worktree_clean)
    dp.git_head_sha = lambda *a: head
    dp.git_worktree_clean = lambda *a: clean
    return saved


def _restore_dp(saved):
    dp.git_head_sha, dp.git_worktree_clean = saved


def _ephemeral_keypair():
    """A throwaway Ed25519 keypair for signature tests — the PRODUCTION key is generated out-of-band
    and held in Infisical (operator custody); the checker/collector never embed a real key."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    pub_pem = priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, priv_pem, pub_pem

NOW = cd.parse_dt("2026-07-10T21:00:00Z")
VALIDATOR = cd._validator()

_ROOT = tempfile.mkdtemp(prefix="sp01_evidence_")
for _fn in ("prod.json", "prod2.json", "backup.sha256"):
    with open(os.path.join(_ROOT, _fn), "w", encoding="utf-8") as _fh:
        _fh.write("{}")
with open(os.path.join(_ROOT, "empty.sha256"), "w", encoding="utf-8") as _fh:
    _fh.write("")  # zero-byte recovery artifact (Claude R2 negative)
# structured recovery-artifact evidence (correction tranche): a real backup file + its true sha256, and a restore-validation log
_RECOVERY_BYTES = b"BACKUP: public._scratch_defunct @ 2026-07-09T00:00:00Z"
with open(os.path.join(_ROOT, "recovery.tar"), "wb") as _fh:
    _fh.write(_RECOVERY_BYTES)
with open(os.path.join(_ROOT, "restore-ok.log"), "w", encoding="utf-8") as _fh:
    _fh.write("restore validated OK 2026-07-09")
RECOVERY_SHA = hashlib.sha256(_RECOVERY_BYTES).hexdigest()
EMPTY_SHA = hashlib.sha256(b"").hexdigest()
# a symlink aliasing the backup under a different name — the operator's alias false-green (samefile)
try:
    os.symlink(os.path.join(_ROOT, "recovery.tar"), os.path.join(_ROOT, "restore-alias.log"))
except (OSError, NotImplementedError):
    pass  # symlink may be unavailable off the Linux host; the negative then resolves to a missing file (still SP014)
ROOTS = [_ROOT]
SNAP_PATH = os.path.join(_ROOT, "prod.json")


def _recovery_artifact(artifact_path="recovery.tar", sha256=None, restore_validation_ref="restore-ok.log", captured_at="2026-07-09T00:00:00Z"):
    return {"artifact_path": artifact_path, "sha256": sha256 or RECOVERY_SHA, "captured_at": captured_at, "restore_validation_ref": restore_validation_ref}


def _obs(v):
    return {"state": "observed", "value": v}


def _na(detail="n/a"):
    return {"state": "not_applicable", "detail": detail}


def _odim(n=0):
    return {"state": "observed", "found_consumers": n, "ref": "sha:x"}


def _consumer(static_n=0):
    return {"observation_window": {"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-10T00:00:00Z"},
            "static_repo": _odim(static_n), "database_deps": _odim(0), "runtime_logs": _odim(0),
            "external_clients": _odim(0), "operator_declaration": _odim(0)}


def _rel(oid, schema, name, relkind="v", static_n=0):
    return {"object_id": oid, "schema": schema, "name": name, "relkind": relkind,
            "owner": _obs("postgres"), "rls_enabled": _obs(False), "is_security_definer_view": _obs(True),
            "in_data_api_exposed_schema": _obs(True), "anon_effective_privs": _obs(["SELECT"]),
            "authenticated_effective_privs": _obs(["SELECT"]), "inbound_fk_count": _obs(0), "outbound_fk_count": _obs(0),
            "dependent_objects": _obs([]), "row_estimate": _na("view"), "advisor_findings": _obs(["security_definer_view"]),
            "consumer_evidence": _consumer(static_n)}


def _target_identity():
    return {"current_database": "postgres", "current_user": "authenticator", "server_version": "PostgreSQL 16.13",
            "server_version_num": 160013, "transaction_read_only": True, "expected_database": "postgres",
            "platform_role_markers": ["anon", "authenticated", "service_role"], "guard_passed": True}


def _collection_scope():
    return {"schemas": ["public"], "expected_database": "postgres", "required_role_markers": ["anon", "authenticated", "service_role"],
            "repo_sha": "8a4c37fc", "query_bundle_sha256": "a" * 64, "collector_version": "0.1.0"}


def _snapshot(rels):
    return {"kind": "evidence_snapshot", "project_ref": "fxoyniqnrlkxfligbxmg", "observed_at": "2026-07-10T20:00:00Z",
            "repo_sha": "8a4c37fc", "collector_version": "0.1.0", "query_bundle_sha256": "a" * 64,
            "relation_count": len(rels), "catalog_relation_count": len(rels), "collection_scope": _collection_scope(), "target_identity": _target_identity(), "relations": rels}


def _entity_map():
    return {"kind": "entity_map", "approval": "accepted", "approval_ref": "TA-map-1",
            "physical_schemas": [{"name": "ops", "status": "accepted", "approval_ref": "PR#86"}, {"name": "archive", "status": "accepted", "approval_ref": "8a4c37fc"}],
            "entities": [{"entity_id": "work.project", "database_layer": "apex_core", "logical_domain": "work", "physical_schema": "ops", "decision_status": "accepted", "source_refs": ["s"]}]}


def _exit(threshold=0):
    return {"metric": "calls", "source": "pg_stat_statements", "operator": "<=", "threshold": threshold, "window_hours": 720, "minimum_samples": 30}


def _manifest(action, ids, req=("is_security_definer_view", "in_data_api_exposed_schema"), snap="prod.json", status="accepted", ta="TA-cluster-1"):
    return {"kind": "cluster_manifest", "cluster_id": "c-001", "status": status, "action_class": action,
            "decision_ids": list(ids), "evidence_snapshot": snap, "max_staleness_hours": 24,
            "minimum_consumer_window_hours": 24, "required_observations": list(req), "technical_authority_approval": ta}


def _decs(rows):
    return {"kind": "decisions_file", "rows": rows}


# ---- GREEN baselines per action class --------------------------------------
def harden_bundle():
    d = {"decision_id": "D-h1", "source_objects": ["public.v_scope_financials"], "meaning_disposition": "preserve", "action_class": "harden", "decision_status": "accepted", "exposure_policy": "service_only", "consumer_disposition": "no_consumer", "evidence_refs": ["query:x"], "technical_authority_approval": "TA-1"}
    return _snapshot([_rel("public.v_scope_financials", "public", "v_scope_financials")]), _decs([d]), _entity_map(), _manifest("harden", ["D-h1"]), SNAP_PATH


def promote_bundle():
    d = {"decision_id": "D-p1", "source_objects": ["public.projects"], "target_objects": ["ops.project"], "meaning_disposition": "preserve", "action_class": "promote", "decision_status": "accepted", "target_entity": "work.project", "target_schema": "ops", "consumer_disposition": "has_consumers", "exposure_policy": "api_facade", "compatibility_contract": {"required": True, "mechanism": "v", "exit_condition": _exit(), "telemetry_ref": "telemetry:x"}, "transform": {"source_def": "a", "target_def": "b", "transform_logic": "c", "validation_report": "query:v", "rollback_story": "r"}, "evidence_refs": ["query:x"], "technical_authority_approval": "TA-2"}
    return _snapshot([_rel("public.projects", "public", "projects", "r", static_n=5)]), _decs([d]), _entity_map(), _manifest("promote", ["D-p1"]), SNAP_PATH


def compat_bundle():
    d = {"decision_id": "D-c1", "source_objects": ["ops.project"], "target_objects": ["public.projects_compat_v"], "target_schema": "public", "meaning_disposition": "preserve", "action_class": "compat", "decision_status": "accepted", "consumer_disposition": "has_consumers", "compatibility_contract": {"required": True, "mechanism": "v", "exit_condition": _exit(), "telemetry_ref": "telemetry:x"}, "evidence_refs": ["query:x"], "technical_authority_approval": "TA-3"}
    return _snapshot([_rel("ops.project", "ops", "project", "r", static_n=1)]), _decs([d]), _entity_map(), _manifest("compat", ["D-c1"]), SNAP_PATH


def archive_bundle():
    d = {"decision_id": "D-a1", "source_objects": ["public._009_rollback_snapshot"], "target_objects": ["archive._009_rollback_snapshot"], "meaning_disposition": "retire", "action_class": "archive", "decision_status": "accepted", "target_schema": "archive", "consumer_disposition": "no_consumer", "evidence_refs": ["query:x"], "technical_authority_approval": "TA-4"}
    return _snapshot([_rel("public._009_rollback_snapshot", "public", "_009_rollback_snapshot", "r")]), _decs([d]), _entity_map(), _manifest("archive", ["D-a1"]), SNAP_PATH


def delete_bundle():
    r = _rel("public._scratch_defunct", "public", "_scratch_defunct", "r")
    r["consumer_evidence"]["observation_window"] = {"started_at": "2026-06-05T00:00:00Z", "ended_at": "2026-07-09T00:00:00Z"}  # 34d >= 30d destructive floor
    d = {"decision_id": "D-d1", "source_objects": ["public._scratch_defunct"], "meaning_disposition": "retire", "action_class": "delete", "decision_status": "accepted", "consumer_disposition": "no_consumer", "retention_disposition": {"policy": "delete_after", "recovery_proof": _recovery_artifact()}, "evidence_refs": ["query:x"], "technical_authority_approval": "TA-5"}
    return _snapshot([r]), _decs([d]), _entity_map(), _manifest("delete", ["D-d1"]), SNAP_PATH


def retain_bundle():
    d = {"decision_id": "D-r1", "source_objects": ["public.audit_log"], "meaning_disposition": "preserve", "action_class": "retain", "decision_status": "accepted", "retention_disposition": {"policy": "retain", "recovery_proof": None}}
    return _snapshot([_rel("public.audit_log", "public", "audit_log", "r")]), _decs([d]), _entity_map(), _manifest("retain", ["D-r1"]), SNAP_PATH


BASELINES = {"harden": harden_bundle, "promote": promote_bundle, "compat": compat_bundle, "archive": archive_bundle, "delete": delete_bundle, "retain": retain_bundle}


def codes(bundle, now=NOW, expect_project_ref="fxoyniqnrlkxfligbxmg"):
    snap, dec, em, man, sp = bundle
    return [d.code for d in cd.run(snap, dec, em, man, now, "preapply", ROOTS, VALIDATOR, sp, expect_project_ref)]


def _mut(builder, fn):
    b = list(copy.deepcopy(x) if not isinstance(x, str) else x for x in builder())
    fn(b[0], b[1], b[2], b[3])
    return tuple(b)


# ---- pytest: green baselines ----------------------------------------------
def test_all_baselines_green():
    for name, b in BASELINES.items():
        assert codes(b()) == [], f"{name} baseline not green: {codes(b())}"


# ---- negatives, one per code ----------------------------------------------
def _dup_rel(s, d, e, m):
    r2 = copy.deepcopy(s["relations"][0]); r2["consumer_evidence"]["static_repo"]["ref"] = "sha:other"
    s["relations"].append(r2); s["relation_count"] = 2


# label -> (builder, mutation, expected_code); multiple labels may reproduce one code.
NEG = {
    "SP002": (harden_bundle, lambda s, d, e, m: s.update(relation_count=99), "SP002"),
    "SP003": (harden_bundle, _dup_rel, "SP003"),
    "SP004": (harden_bundle, lambda s, d, e, m: s["relations"][0].update(name="wrong"), "SP004"),
    "SP005": (harden_bundle, lambda s, d, e, m: m.update(action_class="promote"), "SP005"),
    "SP006": (harden_bundle, lambda s, d, e, m: m["decision_ids"].append("D-nope"), "SP006"),
    "SP007": (harden_bundle, lambda s, d, e, m: d["rows"][0].update(source_objects=["public.ghost"]), "SP007"),
    "SP008": (harden_bundle, lambda s, d, e, m: s.update(observed_at="2026-07-10T23:00:00Z"), "SP008"),
    "SP009": (harden_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"]["observation_window"].update(ended_at="2026-07-11T00:00:00Z"), "SP009"),
    "SP009_zero_window": (harden_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"]["observation_window"].update(ended_at="2026-07-01T00:00:00Z"), "SP009"),
    "SP010": (harden_bundle, lambda s, d, e, m: s["relations"][0].update(is_security_definer_view={"state": "stale", "detail": "c"}), "SP010"),
    "SP011": (promote_bundle, lambda s, d, e, m: d["rows"][0].update(target_entity="work.ghost"), "SP011"),
    "SP012": (promote_bundle, lambda s, d, e, m: d["rows"][0].update(target_schema="ghost"), "SP012"),
    "SP013": (harden_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"]["static_repo"].update(found_consumers=7), "SP013"),
    "SP014": (harden_bundle, lambda s, d, e, m: d["rows"][0]["evidence_refs"].append("../../etc/passwd"), "SP014"),
    "SP014_manifest_scheme": (harden_bundle, lambda s, d, e, m: m.update(evidence_snapshot="query:not-a-file"), "SP014"),
    "SP014_nested_missing": (promote_bundle, lambda s, d, e, m: d["rows"][0]["transform"].update(validation_report="evidence/missing.json"), "SP014"),
    "SP015": (promote_bundle, lambda s, d, e, m: d["rows"][0]["compatibility_contract"]["exit_condition"].update(threshold=float("inf")), "SP015"),
    "SP016": (harden_bundle, lambda s, d, e, m: d["rows"][0].update(decision_status="proposed"), "SP016"),
    "SP017": (harden_bundle, lambda s, d, e, m: m.update(decision_ids=["D-x", "D-y"]), "SP017"),
    "SP018": (harden_bundle, lambda s, d, e, m: m.update(status="proposed", technical_authority_approval=None), "SP018"),
    "SP019": (promote_bundle, lambda s, d, e, m: e.update(approval="proposed"), "SP019"),
    "SP020": (harden_bundle, lambda s, d, e, m: d["rows"].append(dict(d["rows"][0], source_objects=["public.v_scope_financials"])), "SP020"),
    "SP021": (harden_bundle, lambda s, d, e, m: m.update(evidence_snapshot="prod2.json"), "SP021"),
    "SP022": (harden_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"]["operator_declaration"].update(state="not_observed", found_consumers=None, ref=None, detail="pending"), "SP022"),
    "SP022_has_consumers_unresolved": (promote_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"]["external_clients"].update(state="not_observed", found_consumers=None, ref=None, detail="pending"), "SP022"),
    "SP023": (promote_bundle, lambda s, d, e, m: d["rows"][0].update(target_schema="archive"), "SP023"),
    "SP025_wrong_destination": (promote_bundle, lambda s, d, e, m: d["rows"][0].update(target_objects=["public.wrong_destination"]), "SP025"),
    "SP022_database_deps_na": (harden_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"].update(database_deps={"state": "not_applicable", "found_consumers": None, "ref": None, "detail": "neutralized"}), "SP022"),
    "SP014_delete_scheme_recovery": (delete_bundle, lambda s, d, e, m: d["rows"][0]["retention_disposition"]["recovery_proof"].update(artifact_path="urn:not-a-real-backup"), "SP014"),
    "SP014_delete_sha_mismatch": (delete_bundle, lambda s, d, e, m: d["rows"][0]["retention_disposition"]["recovery_proof"].update(sha256="b" * 64), "SP014"),  # correction tranche: artifact bytes must hash to the declared sha256
    "SP014_delete_restore_ref_missing": (delete_bundle, lambda s, d, e, m: d["rows"][0]["retention_disposition"]["recovery_proof"].update(restore_validation_ref="evidence/nope.log"), "SP014"),  # restore-validation proof must resolve
    "SP027_delete_static_na": (delete_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"]["static_repo"].update(state="not_applicable", found_consumers=None, ref=None, detail="waived"), "SP027"),  # delete floor: no not_applicable waiver
    "SP027_delete_short_window": (delete_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"]["observation_window"].update(started_at="2026-07-01T00:00:00Z"), "SP027"),  # < 30 days
    "SP027_delete_external_na_exposed": (delete_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"]["external_clients"].update(state="not_applicable", found_consumers=None, ref=None, detail="n/a"), "SP027"),  # external na while API-exposed
    "SP014_delete_rvr_equals_artifact": (delete_bundle, lambda s, d, e, m: d["rows"][0]["retention_disposition"]["recovery_proof"].update(restore_validation_ref="recovery.tar"), "SP014"),  # F2: restore proof must be DISTINCT from the backup
    "SP014_delete_rvr_symlink_alias": (delete_bundle, lambda s, d, e, m: d["rows"][0]["retention_disposition"]["recovery_proof"].update(restore_validation_ref="restore-alias.log"), "SP014"),  # operator finding: a differently-named symlink to the backup is the SAME file (os.path.samefile)
    "SP014_delete_rvr_empty": (delete_bundle, lambda s, d, e, m: d["rows"][0]["retention_disposition"]["recovery_proof"].update(restore_validation_ref="empty.sha256"), "SP014"),  # F2: restore proof must be non-empty
    "SP015_required_false_infinite_window": (harden_bundle, lambda s, d, e, m: d["rows"][0].update(compatibility_contract={"required": False, "mechanism": None, "exit_condition": {"metric": "calls", "source": "pg_stat_statements", "operator": "<=", "threshold": 0, "window_hours": float("inf"), "minimum_samples": 30}, "telemetry_ref": None}), "SP015"),  # F8: finiteness checked even when required=false
    "SP012_compat_unapproved_schema": (compat_bundle, lambda s, d, e, m: d["rows"][0].update(target_schema="evil", target_objects=["evil.some_view"]), "SP012"),  # Codex R2: compat must target public
    "SP010_consumer_evidence_required": (compat_bundle, lambda s, d, e, m: (m["required_observations"].append("consumer_evidence"), s["relations"][0]["consumer_evidence"]["runtime_logs"].update(state="not_observed", found_consumers=None, ref=None, detail="pending")), "SP010"),  # Codex R2
    "SP015_nonfinite_staleness": (harden_bundle, lambda s, d, e, m: m.update(max_staleness_hours=float("nan")), "SP015"),  # Codex R2
    "SP015_compat_window_infinite": (promote_bundle, lambda s, d, e, m: d["rows"][0]["compatibility_contract"]["exit_condition"].update(window_hours=float("inf")), "SP015"),  # correction tranche: compat exit window must be finite (schema exclusiveMinimum lets +inf through)
    "SP014_delete_empty_recovery": (delete_bundle, lambda s, d, e, m: d["rows"][0]["retention_disposition"]["recovery_proof"].update(artifact_path="empty.sha256"), "SP014"),  # Claude R2: zero-byte artifact
    "SP022_compat_unresolved_consumer": (compat_bundle, lambda s, d, e, m: s["relations"][0]["consumer_evidence"]["database_deps"].update(state="not_observed", found_consumers=None, ref=None, detail="pending"), "SP022"),  # correction tranche: accepted compat must carry OBSERVED consumer evidence, independent of manifest required_observations
}


def test_negatives_one_per_code():
    for label, (builder, fn, code) in NEG.items():
        got = codes(_mut(builder, fn))
        assert code in got, f"{label}: {code} not raised; got {got}"


def test_sp008_stale():
    assert "SP008" in codes(harden_bundle(), now=cd.parse_dt("2026-07-20T21:00:00Z"))


def test_sp024_project_mismatch():
    assert "SP024" in codes(harden_bundle(), expect_project_ref="wrong-project-ref")


def test_sp024_missing_expect():
    assert "SP024" in codes(harden_bundle(), expect_project_ref=None)


def test_sp024_missing_target_identity():
    # schema now REQUIRES target_identity -> its removal is a hard SP001 gate at the boundary
    b = _mut(harden_bundle, lambda s, d, e, m: s.pop("target_identity", None))
    assert "SP001" in codes(b)


def _sp024_mismatch():
    return "SP024" in codes(harden_bundle(), expect_project_ref="wrong-project-ref")


def _sp024_missing_expect():
    return "SP024" in codes(harden_bundle(), expect_project_ref=None)


def _sp024_missing_ti():
    return "SP001" in codes(_mut(harden_bundle, lambda s, d, e, m: s.pop("target_identity", None)))


def _receipt_pure():
    # the gate receipt pins the bytes the apply runner must rehash before executing SQL (TOCTOU):
    # the four CLI docs by path, plus every resolved decision-referenced evidence file.
    snap, dec, em, man, _sp = delete_bundle()
    with tempfile.TemporaryDirectory() as d:
        doc_bytes, paths = {}, {}
        for nm, doc in (("snapshot", snap), ("decisions", dec), ("entity_map", em), ("manifest", man)):
            paths[nm] = os.path.join(d, nm + ".json")
            doc_bytes[nm] = json.dumps(doc).encode("utf-8")
            with open(paths[nm], "wb") as fh:
                fh.write(doc_bytes[nm])
        # Codex P1b regression: corrupt the on-disk snapshot AFTER the validated bytes were captured;
        # the receipt must hash the IN-HAND (validated) bytes, NOT a re-read of the tampered file.
        with open(paths["snapshot"], "ab") as fh:
            fh.write(b"TAMPER-AFTER-VALIDATION")
        rec = cd.build_receipt(mode="preapply", now_iso="2026-07-10T21:00:00Z", expect_project_ref="fxoyniqnrlkxfligbxmg",
                               doc_bytes=doc_bytes, doc_paths=paths, signer={"key_id": "k", "spki_sha256": "00" * 32, "pem_sha256": "11" * 32},
                               snapshot_signature_sha256="22" * 32, gate_repo_sha=None, checkout_bound=False,
                               production_eligible=False, roots=ROOTS, decisions=dec)
        with open(paths["snapshot"], "rb") as fh:
            tampered_sha = hashlib.sha256(fh.read()).hexdigest()
        ev = {e["ref"]: e["sha256"] for e in rec["evidence"]}
        return (rec["gate"] == "green"
                and rec["inputs"]["snapshot"]["sha256"] == hashlib.sha256(doc_bytes["snapshot"]).hexdigest()  # follows validated bytes
                and rec["inputs"]["snapshot"]["sha256"] != tampered_sha        # NOT the tampered re-read
                and ev.get("recovery.tar") == RECOVERY_SHA        # the backup bytes are pinned
                and "restore-ok.log" in ev)                       # and the restore-validation proof


def test_gate_receipt_pure():
    assert _receipt_pure()


def _delete_external_na_unexposed():
    # the ONE allowed external_clients waiver: not_applicable when API exposure is OBSERVED false
    b = _mut(delete_bundle, lambda s, d, e, m: (
        s["relations"][0].__setitem__("in_data_api_exposed_schema", {"state": "observed", "value": False}),
        s["relations"][0]["consumer_evidence"]["external_clients"].update(state="not_applicable", found_consumers=None, ref=None, detail="not API-exposed")))
    return codes(b) == []


def test_delete_external_na_when_unexposed():
    assert _delete_external_na_unexposed()


def _sig_roundtrip():
    priv, _priv_pem, pub_pem = _ephemeral_keypair()
    pub = ds.load_public_key_pem(pub_pem)
    msg = b'{"kind":"evidence_snapshot","project_ref":"fxoyniqnrlkxfligbxmg"}'
    sidecar = ds.build_sig_sidecar(msg, priv)
    ok, _r = ds.verify_sidecar(msg, sidecar, pub)
    tampered, _r2 = ds.verify_sidecar(msg + b" ", sidecar, pub)          # payload changed
    _p2, _pp2, pub2_pem = _ephemeral_keypair()
    wrongkey, _r3 = ds.verify_sidecar(msg, sidecar, ds.load_public_key_pem(pub2_pem))  # different key
    return ok and not tampered and not wrongkey


def test_signature_roundtrip():
    assert _sig_roundtrip()


KEY_ID = "test-ed25519"


@contextlib.contextmanager
def _trusted(key_id, fingerprint):
    prev = dict(dt.TRUSTED_SIGNERS)
    dt.TRUSTED_SIGNERS[key_id] = fingerprint
    try:
        yield
    finally:
        dt.TRUSTED_SIGNERS.clear()
        dt.TRUSTED_SIGNERS.update(prev)


def _fp(pub_pem):
    return ds.public_key_fingerprint(ds.load_public_key_pem(pub_pem))


def _preapply_base(d):
    """Write a GREEN harden bundle's decisions/entity_map/manifest into dir d; return (base_argv, snap).
    The manifest's evidence_snapshot is set to 'snap.json' — the basename _preapply_signed_paths writes —
    so it resolves within --root d (SP021). The snapshot itself is passed via --snapshot separately."""
    snap, dec, em, man, _sp = harden_bundle()
    man = copy.deepcopy(man)
    man["evidence_snapshot"] = "snap.json"
    for nm, doc in (("dec.json", dec), ("em.json", em), ("man.json", man)):
        with open(os.path.join(d, nm), "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
    base = ["--decisions", os.path.join(d, "dec.json"), "--entity-map", os.path.join(d, "em.json"),
            "--manifest", os.path.join(d, "man.json"), "--now", "2026-07-10T21:00:00Z", "--root", d,
            "--expect-project-ref", "fxoyniqnrlkxfligbxmg"]
    return base, snap


def _preapply_signed_paths(d, snap):
    priv, _pp, pub_pem = _ephemeral_keypair()
    snap_bytes = json.dumps(snap, indent=2, sort_keys=True).encode("utf-8")
    snap_path = os.path.join(d, "snap.json")
    with open(snap_path, "wb") as fh:
        fh.write(snap_bytes)
    sig_path = snap_path + ".sig"
    with open(sig_path, "w", encoding="utf-8") as fh:
        json.dump(ds.build_sig_sidecar(snap_bytes, priv), fh)
    keys_dir = os.path.join(d, "keys")
    os.makedirs(keys_dir, exist_ok=True)
    with open(os.path.join(keys_dir, KEY_ID + ".pub.pem"), "wb") as fh:
        fh.write(pub_pem)
    return snap_path, sig_path, keys_dir, _fp(pub_pem)


def _preapply_anchor_green():
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, fp = _preapply_signed_paths(d, snap)
        receipt_path = os.path.join(d, "receipt.json")
        with _trusted(KEY_ID, fp):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path,
                                 "--key-id", KEY_ID, "--keys-dir", keys_dir, "--allow-unbound-checkout", "--receipt-out", receipt_path])
        if rc != 0:
            return False
        rec = json.load(open(receipt_path, encoding="utf-8"))
        return (rec["gate"] == "green" and rec["signer"]["key_id"] == KEY_ID and rec["signer"]["spki_sha256"] == fp
                and "verify_key" not in json.dumps(rec)
                and rec["snapshot_signature_sha256"] == hashlib.sha256(open(sig_path, "rb").read()).hexdigest())


def test_preapply_anchor_green():
    assert _preapply_anchor_green()


# The SP026 negatives assert the SP026 CODE (not just rc). When Task 7 inserts the SP028 gate BEFORE
# the SP026 gate, a flag-less run would block on SP028 and turn these RED — forcing Task 7 to add
# --allow-unbound-checkout here so execution still reaches the SP026 path (guard against silent masking).
def _preapply_missing_key_blocks():
    import io
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, _kd, _fp2 = _preapply_signed_paths(d, snap)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path, "--allow-unbound-checkout"])  # no --key-id
        return rc == 1 and "SP026" in buf.getvalue()


def test_preapply_missing_key_blocks():
    assert _preapply_missing_key_blocks()


def _preapply_unknown_key_blocks():
    import io
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, _fp2 = _preapply_signed_paths(d, snap)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path,
                                 "--key-id", "not-a-signer", "--keys-dir", keys_dir, "--allow-unbound-checkout"])
        return rc == 1 and "SP026" in buf.getvalue()


def test_preapply_unknown_key_blocks():
    assert _preapply_unknown_key_blocks()


def _sig_gate_e2e():
    """End-to-end SP026: a green harden bundle passes ONLY with a valid signature resolved through the
    TRUSTED_SIGNERS anchor; a missing --key-id or a tampered snapshot blocks with the SP026 code (exit 1).
    Proves the checker verifies before trusting the snapshot."""
    import io
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, fp = _preapply_signed_paths(d, snap)
        receipt_path = os.path.join(d, "receipt.json")
        with _trusted(KEY_ID, fp):
            green = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path,
                                    "--key-id", KEY_ID, "--keys-dir", keys_dir, "--allow-unbound-checkout", "--receipt-out", receipt_path]) == 0
            green = green and os.path.isfile(receipt_path) and json.load(open(receipt_path, encoding="utf-8"))["gate"] == "green"  # receipt emitted on GREEN
            mbuf = io.StringIO()
            with contextlib.redirect_stdout(mbuf):
                mrc = cd.main(base + ["--snapshot", snap_path, "--allow-unbound-checkout"])                 # no sig/key supplied
            missing = mrc == 1 and "SP026" in mbuf.getvalue()
            with open(snap_path, "ab") as fh:
                fh.write(b" ")                                                  # tamper the signed bytes
            tbuf = io.StringIO()
            with contextlib.redirect_stdout(tbuf):
                trc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path,
                                      "--key-id", KEY_ID, "--keys-dir", keys_dir, "--allow-unbound-checkout"])
            tampered = trc == 1 and "SP026" in tbuf.getvalue()
        return green and missing and tampered


def test_signature_gate_end_to_end():
    assert _sig_gate_e2e()


def _sidecar_bytes_agree():
    priv, _pp, pub_pem = _ephemeral_keypair()
    pub = ds.load_public_key_pem(pub_pem)
    msg = b'{"kind":"evidence_snapshot"}'
    sidecar_bytes = json.dumps(ds.build_sig_sidecar(msg, priv)).encode("utf-8")
    ok, _ = ds.verify_sidecar_bytes_with_key(msg, sidecar_bytes, pub)
    return ok is True


def _sidecar_bytes_bad_json_fails_closed():
    _priv, _pp, pub_pem = _ephemeral_keypair()
    pub = ds.load_public_key_pem(pub_pem)
    ok, reason = ds.verify_sidecar_bytes_with_key(b"msg", b"{not json", pub)
    return ok is False and "sidecar" in reason


def test_wrong_kind_document_rejected():
    # a decisions_file passed in the --snapshot slot must be SP001-rejected, not crash mid-check
    snap, dec, em, man, sp = harden_bundle()
    got = [d.code for d in cd.run(dec, dec, em, man, NOW, "preapply", ROOTS, VALIDATOR, sp, "fxoyniqnrlkxfligbxmg")]
    assert "SP001" in got


def _wrong_kind():
    snap, dec, em, man, sp = harden_bundle()
    return "SP001" in [d.code for d in cd.run(dec, dec, em, man, NOW, "preapply", ROOTS, VALIDATOR, sp, "fxoyniqnrlkxfligbxmg")]


# ---- unit: dup-key loaders + path safety -----------------------------------
def test_dup_key_yaml_rejected():
    try:
        yaml.load("k: 1\nk: 2\n", Loader=cd.NoDupSafeLoader)
        raise AssertionError("YAML dup not rejected")
    except yaml.YAMLError:
        pass


def test_dup_key_json_rejected():
    try:
        cd.json.loads('{"k":1,"k":2}', object_pairs_hook=cd._reject_dup_json_pairs)
        raise AssertionError("JSON dup not rejected")
    except ValueError:
        pass


def test_path_safety():
    assert cd.resolve_within_roots("prod.json", ROOTS)[0] is not None
    assert cd.resolve_within_roots("../escape.json", ROOTS)[0] is None
    assert cd.resolve_within_roots("nonexist.json", ROOTS)[0] is None
    assert not cd.is_path_ref("query:x")
    assert cd.is_path_ref("evidence/p.json")
    assert cd.is_path_ref("C:\\Windows\\x")  # not an allowlisted scheme -> treated as path


def _yaml_dup():
    try:
        yaml.load("k: 1\nk: 2\n", Loader=cd.NoDupSafeLoader)
        return False
    except yaml.YAMLError:
        return True


def _json_dup():
    try:
        cd.json.loads('{"k":1,"k":2}', object_pairs_hook=cd._reject_dup_json_pairs)
        return False
    except ValueError:
        return True


def _path():
    return (cd.resolve_within_roots("prod.json", ROOTS)[0] is not None
            and cd.resolve_within_roots("../escape.json", ROOTS)[0] is None
            and not cd.is_path_ref("query:x") and cd.is_path_ref("C:\\x"))


def _checkout_matrix():
    g = cd._checkout_gate
    r = []
    r.append(g(None, False, False)[0] is False)                       # (0,0,0) SP028
    r.append(g(None, False, True) == (True, False, False, None, None))  # (0,0,1) authoring
    saved = _stub_dp("deadbeef", clean=True)
    try:
        r.append(g("deadbeef", True, False)[:4] == (True, True, True, "deadbeef"))  # (1,1,0) bound
        r.append(g("cafef00d", True, False)[0] is False)              # wrong gate sha -> SP028
        _restore_dp(saved); saved = _stub_dp("deadbeef", clean=False)
        r.append(g("deadbeef", True, False)[0] is False)              # dirty -> SP028
        _restore_dp(saved); saved = _stub_dp(None, clean=True)
        r.append(g("deadbeef", True, False)[0] is False)              # undeterminable HEAD (git_head_sha->None) -> SP028
    finally:
        _restore_dp(saved)
    r.append(g("deadbeef", False, False)[0] is False)                 # (1,0,0) SP028
    r.append(g(None, True, False)[0] is False)                        # (0,1,0) SP028
    r.append(g("deadbeef", True, True)[0] is False)                   # (1,1,1) SP028
    r.append(g("deadbeef", False, True)[0] is False)                  # (1,0,1) SP028
    r.append(g(None, True, True)[0] is False)                         # (0,1,1) SP028
    return all(r)


def test_checkout_matrix():
    assert _checkout_matrix()


def _neither_flag_blocks_sp028():
    import io
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, fp = _preapply_signed_paths(d, snap)
        buf = io.StringIO()
        with _trusted(KEY_ID, fp), contextlib.redirect_stdout(buf):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path, "--key-id", KEY_ID, "--keys-dir", keys_dir])
    return rc == 1 and "SP028" in buf.getvalue()


def test_neither_flag_blocks_sp028():
    assert _neither_flag_blocks_sp028()


def _sp028_precedes_doc_read():
    # a nonexistent snapshot/decisions path + no checkout flags must fail SP028 (rc 1), NOT SP000 (rc 2):
    # the gate refuses before any document read.
    import io
    with tempfile.TemporaryDirectory() as d:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cd.main(["--snapshot", os.path.join(d, "nope.json"), "--decisions", os.path.join(d, "nope.json"),
                          "--entity-map", os.path.join(d, "nope.json"), "--manifest", os.path.join(d, "nope.json"),
                          "--now", "2026-07-10T21:00:00Z", "--root", d, "--expect-project-ref", "fxoyniqnrlkxfligbxmg"])
    return rc == 1 and "SP028" in buf.getvalue()


def test_sp028_precedes_doc_read():
    assert _sp028_precedes_doc_read()


def _authoring_banner_and_receipt():
    import io
    banner = "=== DISPOSITION GATE (preapply): GREEN — AUTHORING ONLY; CHECKOUT UNBOUND ==="  # exact literal (em-dash)
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, fp = _preapply_signed_paths(d, snap)
        receipt_path = os.path.join(d, "receipt.json")
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with _trusted(KEY_ID, fp), contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path, "--key-id", KEY_ID,
                                 "--keys-dir", keys_dir, "--allow-unbound-checkout", "--receipt-out", receipt_path])
        out, err = out_buf.getvalue(), err_buf.getvalue()
        rec = json.load(open(receipt_path, encoding="utf-8"))
    return (rc == 0 and banner in out and "WARNING: unbound checkout" in err
            and rec["checkout_bound"] is False and rec["production_eligible"] is False and rec["gate_repo_sha"] is None)


def test_authoring_banner_and_receipt():
    assert _authoring_banner_and_receipt()


def _bound_green_receipt():
    import io
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, fp = _preapply_signed_paths(d, snap)
        receipt_path = os.path.join(d, "receipt.json")
        saved = _stub_dp("deadbeef", clean=True)
        buf = io.StringIO()
        try:
            with _trusted(KEY_ID, fp), contextlib.redirect_stdout(buf):
                rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path, "--key-id", KEY_ID,
                                     "--keys-dir", keys_dir, "--expect-gate-repo-sha", "deadbeef",
                                     "--require-clean-checkout", "--receipt-out", receipt_path])
            out = buf.getvalue()
            rec = json.load(open(receipt_path, encoding="utf-8"))
        finally:
            _restore_dp(saved)
    return (rc == 0 and "AUTHORING ONLY" not in out and rec["checkout_bound"] is True
            and rec["production_eligible"] is True and rec["gate_repo_sha"] == "deadbeef")


def test_bound_green_receipt():
    assert _bound_green_receipt()


def _verify_key_flag_rejected():
    import io
    err = io.StringIO()
    argv = ["--snapshot", "s", "--decisions", "d", "--entity-map", "e", "--manifest", "m",
            "--now", "2026-07-10T21:00:00Z", "--root", "r", "--verify-key", "x"]
    try:
        with contextlib.redirect_stderr(err):
            cd.main(argv)
        return False  # argparse should have exited before returning
    except SystemExit as exc:
        return exc.code == 2 and "unrecognized arguments: --verify-key" in err.getvalue()


def test_verify_key_flag_rejected():
    assert _verify_key_flag_rejected()


def _sp009_provenance_conditional():
    # An overlay-derived window with ended_at AFTER observed_at PASSES SP009 iff the object_id is in
    # derived_window_object_ids; with the marker removed it fails via the original bound.
    snap, dec, em, man, sp = harden_bundle()
    r = snap["relations"][0]
    r["consumer_evidence"]["observation_window"] = {"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-20T00:00:00Z"}  # ended > observed_at
    oid = r["object_id"]
    with_marker = [d.code for d in cd.run(snap, dec, em, man, NOW, "preapply", ROOTS, VALIDATOR, sp,
                                          "fxoyniqnrlkxfligbxmg", derived_window_object_ids={oid})]
    without = [d.code for d in cd.run(snap, dec, em, man, NOW, "preapply", ROOTS, VALIDATOR, sp,
                                      "fxoyniqnrlkxfligbxmg", derived_window_object_ids=None)]
    return "SP009" not in with_marker and "SP009" in without


if __name__ == "__main__":
    ok = True
    print("== green baselines ==")
    for name, b in BASELINES.items():
        c = codes(b()); good = (c == []); ok = ok and good
        print(f"  {'ok  ' if good else 'FAIL'}: {name}" + ("" if good else f" -> {c}"))
    print(f"== negatives ({len(NEG)}) ==")
    for label, (builder, fn, code) in NEG.items():
        try:
            got = codes(_mut(builder, fn)); hit = code in got
        except Exception as exc:  # noqa: BLE001
            got, hit = f"EXC {exc}", False
        ok = ok and hit
        print(f"  {'ok  ' if hit else 'FAIL'}: {label}" + ("" if hit else f" -> {got}"))
    print("== units ==")
    for name, fn in [
        ("sp008_stale", lambda: "SP008" in codes(harden_bundle(), now=cd.parse_dt("2026-07-20T21:00:00Z"))),
        ("sp024_project_mismatch", _sp024_mismatch),
        ("sp024_missing_expect", _sp024_missing_expect),
        ("sp024_missing_target_identity", _sp024_missing_ti),
        ("delete_external_na_when_unexposed", _delete_external_na_unexposed),
        ("gate_receipt_pure", _receipt_pure),
        # F7 obsolete under SP026: the receipt binds snapshot_signature_sha256 from in-hand sig bytes; there is no second read to guard.
        ("signature_roundtrip", _sig_roundtrip),
        ("signature_gate_end_to_end", _sig_gate_e2e),
        ("preapply_anchor_green", _preapply_anchor_green),
        ("preapply_missing_key_blocks", _preapply_missing_key_blocks),
        ("preapply_unknown_key_blocks", _preapply_unknown_key_blocks),
        ("verify_sidecar_bytes_ok", _sidecar_bytes_agree),
        ("verify_sidecar_bytes_bad_json", _sidecar_bytes_bad_json_fails_closed),
        ("wrong_kind_document", _wrong_kind),
        ("dup_yaml", lambda: _yaml_dup()),
        ("dup_json", lambda: _json_dup()),
        ("path_safety", lambda: _path()),
        ("checkout_matrix", _checkout_matrix),
        ("neither_flag_blocks_sp028", _neither_flag_blocks_sp028),
        ("sp028_precedes_doc_read", _sp028_precedes_doc_read),
        ("authoring_banner_and_receipt", _authoring_banner_and_receipt),
        ("bound_green_receipt", _bound_green_receipt),
        ("verify_key_flag_rejected", _verify_key_flag_rejected),
        ("sp009_provenance_conditional", _sp009_provenance_conditional),
    ]:
        try:
            r = bool(fn())
        except Exception as exc:  # noqa: BLE001
            r = False; name = f"{name} (EXC {exc})"
        ok = ok and r
        print(f"  {'ok  ' if r else 'FAIL'}: {name}")
    print("\n=== CHECKER SEMANTIC SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
