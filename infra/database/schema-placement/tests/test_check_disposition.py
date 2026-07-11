"""Semantic-gate tests for check_disposition.py (offline, --now injected).

A GREEN preapply baseline per action class (harden/promote/compat/archive/delete/retain), each
with an accepted manifest + cluster approval, an accepted entity_map, fully-resolved consumer
evidence, and a manifest/snapshot path binding; plus one negative per SP0xx code, and unit
tests for the dup-key loaders (YAML+JSON) and the path-safety helper.
"""

import copy
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_disposition as cd  # noqa: E402
import yaml  # noqa: E402

NOW = cd.parse_dt("2026-07-10T21:00:00Z")
VALIDATOR = cd._validator()

_ROOT = tempfile.mkdtemp(prefix="sp01_evidence_")
for _fn in ("prod.json", "prod2.json", "backup.sha256"):
    with open(os.path.join(_ROOT, _fn), "w", encoding="utf-8") as _fh:
        _fh.write("{}")
with open(os.path.join(_ROOT, "empty.sha256"), "w", encoding="utf-8") as _fh:
    _fh.write("")  # zero-byte recovery artifact (Claude R2 negative)
ROOTS = [_ROOT]
SNAP_PATH = os.path.join(_ROOT, "prod.json")


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


def _snapshot(rels):
    return {"kind": "evidence_snapshot", "project_ref": "fxoyniqnrlkxfligbxmg", "observed_at": "2026-07-10T20:00:00Z",
            "repo_sha": "8a4c37fc", "collector_version": "0.1.0", "query_bundle_sha256": "a" * 64,
            "relation_count": len(rels), "target_identity": _target_identity(), "relations": rels}


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
    d = {"decision_id": "D-c1", "source_objects": ["ops.project"], "target_objects": ["public.projects_compat_v"], "target_schema": "public", "meaning_disposition": "preserve", "action_class": "compat", "decision_status": "accepted", "compatibility_contract": {"required": True, "mechanism": "v", "exit_condition": _exit(), "telemetry_ref": "telemetry:x"}, "evidence_refs": ["query:x"], "technical_authority_approval": "TA-3"}
    return _snapshot([_rel("ops.project", "ops", "project", "r")]), _decs([d]), _entity_map(), _manifest("compat", ["D-c1"]), SNAP_PATH


def archive_bundle():
    d = {"decision_id": "D-a1", "source_objects": ["public._009_rollback_snapshot"], "target_objects": ["archive._009_rollback_snapshot"], "meaning_disposition": "retire", "action_class": "archive", "decision_status": "accepted", "target_schema": "archive", "consumer_disposition": "no_consumer", "evidence_refs": ["query:x"], "technical_authority_approval": "TA-4"}
    return _snapshot([_rel("public._009_rollback_snapshot", "public", "_009_rollback_snapshot", "r")]), _decs([d]), _entity_map(), _manifest("archive", ["D-a1"]), SNAP_PATH


def delete_bundle():
    d = {"decision_id": "D-d1", "source_objects": ["public._scratch_defunct"], "meaning_disposition": "retire", "action_class": "delete", "decision_status": "accepted", "consumer_disposition": "no_consumer", "retention_disposition": {"policy": "delete_after", "recovery_proof": "backup.sha256"}, "evidence_refs": ["query:x"], "technical_authority_approval": "TA-5"}
    return _snapshot([_rel("public._scratch_defunct", "public", "_scratch_defunct", "r")]), _decs([d]), _entity_map(), _manifest("delete", ["D-d1"]), SNAP_PATH


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
    "SP014_delete_scheme_recovery": (delete_bundle, lambda s, d, e, m: d["rows"][0]["retention_disposition"].update(recovery_proof="urn:not-a-real-backup"), "SP014"),
    "SP012_compat_unapproved_schema": (compat_bundle, lambda s, d, e, m: d["rows"][0].update(target_schema="evil", target_objects=["evil.some_view"]), "SP012"),  # Codex R2: compat must target public
    "SP010_consumer_evidence_required": (compat_bundle, lambda s, d, e, m: (m["required_observations"].append("consumer_evidence"), s["relations"][0]["consumer_evidence"]["runtime_logs"].update(state="not_observed", found_consumers=None, ref=None, detail="pending")), "SP010"),  # Codex R2
    "SP015_nonfinite_staleness": (harden_bundle, lambda s, d, e, m: m.update(max_staleness_hours=float("nan")), "SP015"),  # Codex R2
    "SP014_delete_empty_recovery": (delete_bundle, lambda s, d, e, m: d["rows"][0]["retention_disposition"].update(recovery_proof="empty.sha256"), "SP014"),  # Claude R2: zero-byte artifact
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
        ("wrong_kind_document", _wrong_kind),
        ("dup_yaml", lambda: _yaml_dup()),
        ("dup_json", lambda: _json_dup()),
        ("path_safety", lambda: _path()),
    ]:
        try:
            r = bool(fn())
        except Exception as exc:  # noqa: BLE001
            r = False; name = f"{name} (EXC {exc})"
        ok = ok and r
        print(f"  {'ok  ' if r else 'FAIL'}: {name}")
    print("\n=== CHECKER SEMANTIC SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
