"""Schema-level contract tests for the disposition ledger (schema-placement).

Proves the technical-authority adversarial cases FAIL and a positive fixture for every
action_class PASSES. Cross-document / time / context checks belong to check_disposition.py.

Run: uv run --project infra/database/schema-placement \
       python infra/database/schema-placement/tests/test_disposition_schema.py
"""

import copy
import json
import os

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "disposition.schema.json")


def _schema():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _validator():
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


V = _validator()
SHA64 = "a" * 64


def _obs(value):
    return {"state": "observed", "value": value}


def _na(detail="not applicable for this relation"):
    return {"state": "not_applicable", "detail": detail}


def _cdim(n=0):
    return {"state": "observed", "found_consumers": n, "ref": "sha:8a4c37fc"}


def _cdim_missing(state="not_observed", detail="not wired yet"):
    return {"state": state, "found_consumers": None, "ref": None, "detail": detail}


def _consumer_evidence():
    return {
        "observation_window": {"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-10T00:00:00Z"},
        "static_repo": _cdim(0),
        "database_deps": _cdim(0),
        "runtime_logs": _cdim_missing("not_observed", "runtime log access not wired"),
        "external_clients": _cdim_missing("not_applicable", "no external client dimension"),
        "operator_declaration": _cdim_missing("not_observed", "pending operator declaration"),
    }


def _relation(oid="public.v_projects_full", schema="public", name="v_projects_full", relkind="v"):
    return {
        "object_id": oid, "schema": schema, "name": name, "relkind": relkind,
        "owner": _obs("postgres"),
        "rls_enabled": _obs(False),
        "is_security_definer_view": _obs(True),
        "in_data_api_exposed_schema": _obs(True),
        "anon_effective_privs": _obs(["SELECT"]),
        "authenticated_effective_privs": _obs(["SELECT"]),
        "inbound_fk_count": _obs(0),
        "outbound_fk_count": _obs(0),
        "dependent_objects": _obs([
            {"object_type": "function", "identity": "public.handle_new_user()", "direction": "inbound", "evidence_type": "pg_depend", "evidence_ref": "query:dependency-closure-v1", "dependency_role": "external_consumer"},
            {"object_type": "trigger", "identity": "public.projects.trg_audit", "direction": "inbound", "evidence_type": "pg_depend", "evidence_ref": "query:dependency-closure-v1", "dependency_role": "attached_object"},
            {"object_type": "policy", "identity": "public.mcp_task_packets.service_all", "direction": "inbound", "evidence_type": "pg_depend", "evidence_ref": "query:dependency-closure-v1", "dependency_role": "attached_object"},
        ]),
        "row_estimate": _na("view — no row estimate"),
        "advisor_findings": _obs(["security_definer_view"]),
        "consumer_evidence": _consumer_evidence(),
    }


def _target_identity():
    return {"current_database": "postgres", "current_user": "authenticator", "server_version": "PostgreSQL 16.13",
            "server_version_num": 160013, "transaction_read_only": True, "expected_database": "postgres",
            "platform_role_markers": ["anon", "authenticated", "service_role"], "guard_passed": True}


def _collection_scope():
    return {"schemas": ["public"], "expected_database": "postgres", "required_role_markers": ["anon", "authenticated", "service_role"], "repo_sha": "8a4c37fc", "query_bundle_sha256": SHA64, "collector_version": "0.1.0"}


def _valid_snapshot(relations=None):
    rels = relations if relations is not None else [_relation()]
    return {"kind": "evidence_snapshot", "project_ref": "fxoyniqnrlkxfligbxmg", "observed_at": "2026-07-10T20:00:00Z", "repo_sha": "8a4c37fc", "collector_version": "0.1.0", "query_bundle_sha256": SHA64, "relation_count": len(rels), "collection_scope": _collection_scope(), "target_identity": _target_identity(), "relations": rels}


def _exit():
    return {"metric": "calls", "source": "pg_stat_statements", "operator": "<=", "threshold": 0, "window_hours": 720, "minimum_samples": 30}


def _row_proposed():
    return {"decision_id": "D-0001", "source_objects": ["public.v_projects_full"], "meaning_disposition": "unresolved", "action_class": "harden", "decision_status": "proposed"}


def _row_harden():
    return {"decision_id": "D-harden-1", "source_objects": ["public.v_scope_financials"], "meaning_disposition": "preserve", "action_class": "harden", "decision_status": "accepted", "exposure_policy": "service_only", "consumer_disposition": "no_consumer", "evidence_refs": ["evidence/prod-2026-07-10.json#v_scope_financials"], "technical_authority_approval": "TA-2026-07-10-001"}


def _row_promote():
    return {"decision_id": "D-promote-1", "source_objects": ["public.projects"], "target_objects": ["ops.project"], "meaning_disposition": "preserve", "action_class": "promote", "decision_status": "accepted", "target_entity": "work.project", "target_schema": "ops", "consumer_disposition": "has_consumers", "exposure_policy": "api_facade", "compatibility_contract": {"required": True, "mechanism": "public view over ops.project", "exit_condition": _exit(), "telemetry_ref": "telemetry/projects.json"}, "transform": {"source_def": "public.projects", "target_def": "ops.project", "transform_logic": "1:1 column map", "validation_report": "evidence/xform-projects.json", "rollback_story": "swap compat view back"}, "technical_authority_approval": "TA-2026-07-10-002"}


def _row_compat():
    return {"decision_id": "D-compat-1", "source_objects": ["ops.project"], "target_objects": ["public.projects_compat_v"], "target_schema": "public", "meaning_disposition": "preserve", "action_class": "compat", "decision_status": "accepted", "consumer_disposition": "has_consumers", "compatibility_contract": {"required": True, "mechanism": "public view over ops.project", "exit_condition": _exit(), "telemetry_ref": "telemetry/compat-projects.json"}, "technical_authority_approval": "TA-2026-07-10-003"}


def _row_archive():
    return {"decision_id": "D-archive-1", "source_objects": ["public._009_rollback_snapshot"], "target_objects": ["archive._009_rollback_snapshot"], "meaning_disposition": "retire", "action_class": "archive", "decision_status": "accepted", "target_schema": "archive", "consumer_disposition": "no_consumer", "technical_authority_approval": "TA-2026-07-10-004"}


def _recovery_artifact():
    return {"artifact_path": "evidence/backup-2026-07-10.tar", "sha256": "a" * 64, "captured_at": "2026-07-09T00:00:00Z", "restore_validation_ref": "evidence/restore-check-2026-07-09.log"}


def _row_delete():
    return {"decision_id": "D-delete-1", "source_objects": ["public._scratch_defunct"], "meaning_disposition": "retire", "action_class": "delete", "decision_status": "accepted", "consumer_disposition": "no_consumer", "retention_disposition": {"policy": "delete_after", "recovery_proof": _recovery_artifact()}, "technical_authority_approval": "TA-2026-07-10-005"}


def _row_retain():
    return {"decision_id": "D-retain-1", "source_objects": ["public.audit_log"], "meaning_disposition": "preserve", "action_class": "retain", "decision_status": "accepted", "retention_disposition": {"policy": "retain", "recovery_proof": None}}


def _valid_decisions(rows):
    return {"kind": "decisions_file", "version": "0.1.0", "rows": rows}


def _valid_manifest():
    return {"kind": "cluster_manifest", "cluster_id": "definer-views-001", "title": "First definer-view tranche", "status": "proposed", "action_class": "harden", "decision_ids": ["D-harden-1", "D-harden-2"], "evidence_snapshot": "docs/operations/schema-placement/evidence/prod-2026-07-10.json", "max_staleness_hours": 24, "required_observations": ["is_security_definer_view", "anon_effective_privs", "in_data_api_exposed_schema", "consumer_evidence"], "technical_authority_approval": None}


def _valid_entity_map():
    return {"kind": "entity_map", "approval": "proposed", "approval_ref": None, "physical_schemas": [{"name": "ops", "status": "accepted", "approval_ref": "PR#79-#86"}, {"name": "core", "status": "accepted", "approval_ref": "39214fa3"}, {"name": "archive", "status": "accepted", "approval_ref": "8a4c37fc"}, {"name": "records", "status": "proposed", "approval_ref": None}], "entities": [{"entity_id": "work.project", "database_layer": "apex_core", "logical_domain": "work", "physical_schema": "ops", "decision_status": "proposed", "source_refs": ["strategy:§5"]}]}


# ---- NEGATIVES -------------------------------------------------------------
def _neg_observed_without_value():
    s = _valid_snapshot(); s["relations"][0]["owner"] = {"state": "observed"}; return s


def _neg_relation_without_facts():
    s = _valid_snapshot(); s["relations"][0] = {"object_id": "public.x", "schema": "public", "name": "x", "relkind": "r"}; return s


def _neg_accepted_promote_without_target():
    return _valid_decisions([{"decision_id": "D-x", "source_objects": ["public.projects"], "meaning_disposition": "preserve", "action_class": "promote", "decision_status": "accepted"}])


def _neg_empty_consumer_evidence():
    s = _valid_snapshot(); s["relations"][0]["consumer_evidence"] = {}; return s


def _neg_invalid_domain():
    m = _valid_entity_map(); m["entities"][0]["logical_domain"] = "finance"; return m


def _neg_duplicate_relations():
    r = _relation(); s = _valid_snapshot(relations=[r, copy.deepcopy(r)]); s["relation_count"] = 1; return s


def _neg_unsafe_delete():
    r = _row_delete(); r["consumer_disposition"] = "has_consumers"; r["retention_disposition"] = {"policy": "retain", "recovery_proof": None}; return _valid_decisions([r])


def _neg_empty_transform():
    r = _row_promote(); r["transform"] = {"source_def": "", "target_def": "", "transform_logic": "", "validation_report": "", "rollback_story": ""}; return _valid_decisions([r])


def _neg_entity_map_accepted_null_ref():
    m = _valid_entity_map(); m["approval"] = "accepted"; m["approval_ref"] = None; return m


def _neg_physical_schema_accepted_null_ref():
    m = _valid_entity_map(); m["physical_schemas"][3] = {"name": "records", "status": "accepted", "approval_ref": None}; return m


def _neg_empty_ta_ref_row():
    r = _row_harden(); r["technical_authority_approval"] = ""; return _valid_decisions([r])


def _neg_invalid_timestamp():
    s = _valid_snapshot(); s["observed_at"] = "not-a-date"; return s


def _neg_not_observed_with_value():
    s = _valid_snapshot(); s["relations"][0]["owner"] = {"state": "not_observed", "value": "postgres", "detail": "x"}; return s


def _neg_not_observed_without_detail():
    s = _valid_snapshot(); s["relations"][0]["owner"] = {"state": "not_observed"}; return s


def _neg_observed_consumer_null():
    s = _valid_snapshot(); s["relations"][0]["consumer_evidence"]["static_repo"] = {"state": "observed", "found_consumers": None, "ref": None}; return s


def _neg_compat_required_false():
    r = _row_compat(); r["compatibility_contract"] = {"required": False}; return _valid_decisions([r])


def _neg_cluster_accepted_null_ta():
    m = _valid_manifest(); m["status"] = "accepted"; m["technical_authority_approval"] = None; return m


def _neg_cluster_uses_objects():
    m = _valid_manifest(); del m["decision_ids"]; m["objects"] = ["public.v_scope_financials"]; return m


def _neg_promote_without_target_objects():
    r = _row_promote(); del r["target_objects"]; return _valid_decisions([r])


def _neg_harden_with_target_objects():
    r = _row_harden(); r["target_objects"] = ["ops.something"]; return _valid_decisions([r])


def _neg_typed_rls_yes():
    s = _valid_snapshot(); s["relations"][0]["rls_enabled"] = _obs("yes"); return s


def _neg_typed_row_estimate_array():
    s = _valid_snapshot(); s["relations"][0]["row_estimate"] = _obs([]); return s


def _neg_negative_fk():
    s = _valid_snapshot(); s["relations"][0]["inbound_fk_count"] = _obs(-1); return s


def _neg_bad_privilege():
    s = _valid_snapshot(); s["relations"][0]["anon_effective_privs"] = _obs(["BOGUS"]); return s


def _neg_retain_unconstrained():
    r = _row_retain(); r["meaning_disposition"] = "unresolved"; del r["retention_disposition"]; return _valid_decisions([r])


def _neg_archive_has_consumers():
    r = _row_archive(); r["consumer_disposition"] = "has_consumers"; return _valid_decisions([r])


def _neg_window_as_string():
    s = _valid_snapshot(); s["relations"][0]["consumer_evidence"]["observation_window"] = "2026-07-01/2026-07-10"; return s


def _neg_harden_without_consumer():
    r = _row_harden(); del r["consumer_disposition"]; del r["evidence_refs"]; return _valid_decisions([r])


def _neg_nonobserved_dim_missing_nulls():
    s = _valid_snapshot(); s["relations"][0]["consumer_evidence"]["runtime_logs"] = {"state": "not_observed", "detail": "x"}; return s


def _neg_maintain_privilege():
    s = _valid_snapshot(); s["relations"][0]["anon_effective_privs"] = _obs(["MAINTAIN"]); return s


def _neg_compat_zero_window():
    r = _row_compat(); r["compatibility_contract"]["exit_condition"]["window_hours"] = 0; return _valid_decisions([r])


def _neg_compat_zero_samples():
    r = _row_compat(); r["compatibility_contract"]["exit_condition"]["minimum_samples"] = 0; return _valid_decisions([r])


def _neg_dependency_missing_evidence():
    s = _valid_snapshot(); s["relations"][0]["dependent_objects"] = _obs([{"object_type": "function", "identity": "public.f()", "direction": "inbound", "evidence_type": "pg_depend"}]); return s


def _neg_snapshot_without_target_identity():
    s = _valid_snapshot(); del s["target_identity"]; return s


def _neg_delete_null_retention():  # null-vacuity bypass (finding #1)
    r = _row_delete(); r["retention_disposition"] = None; return _valid_decisions([r])


def _neg_retain_null_retention():
    r = _row_retain(); r["retention_disposition"] = None; return _valid_decisions([r])


def _neg_compat_null_contract():
    r = _row_compat(); r["compatibility_contract"] = None; return _valid_decisions([r])


def _neg_compat_missing_target_schema():  # compat now requires target_schema (finding #4)
    r = _row_compat(); del r["target_schema"]; return _valid_decisions([r])


def _neg_promote_has_consumers_null_compat():  # Codex R2: has_consumers promote needs a real compat
    r = _row_promote(); r["compatibility_contract"] = None; return _valid_decisions([r])


def _neg_promote_null_exposure():  # Claude R2 adversarial: promote must declare a non-null exposure posture
    r = _row_promote(); r["exposure_policy"] = None; return _valid_decisions([r])


def _neg_dependency_missing_role():  # correction tranche: every stored edge must carry dependency_role
    s = _valid_snapshot()
    s["relations"][0]["dependent_objects"] = _obs([{"object_type": "view", "identity": "public.v_x", "direction": "inbound", "evidence_type": "pg_depend", "evidence_ref": "query:x"}])
    return s


def _neg_dependency_bad_role():  # dependency_role is a closed enum
    s = _valid_snapshot()
    s["relations"][0]["dependent_objects"] = _obs([{"object_type": "view", "identity": "public.v_x", "direction": "inbound", "evidence_type": "pg_depend", "evidence_ref": "query:x", "dependency_role": "consumer"}])
    return s


def _neg_compat_missing_consumer_disposition():  # correction tranche: accepted compat must assert has_consumers
    r = _row_compat(); del r["consumer_disposition"]; return _valid_decisions([r])


def _neg_compat_no_consumer():  # a no_consumer compat is contradictory (no facade needed) -> must stay proposed
    r = _row_compat(); r["consumer_disposition"] = "no_consumer"; return _valid_decisions([r])


def _neg_delete_string_recovery():  # correction tranche: delete recovery_proof must be a structured artifact, not a bare path
    r = _row_delete(); r["retention_disposition"]["recovery_proof"] = "evidence/backup.sha256"; return _valid_decisions([r])


def _neg_delete_recovery_missing_sha():  # the recovery artifact must carry the sha256 of the backup bytes
    r = _row_delete(); del r["retention_disposition"]["recovery_proof"]["sha256"]; return _valid_decisions([r])


def _neg_calendar_invalid_observed_at():  # F1: date-time format (rfc3339-validator) rejects calendar-invalid values the regex admits
    s = _valid_snapshot(); s["observed_at"] = "2026-13-45T25:61:61Z"; return s


def _neg_snapshot_without_collection_scope():  # census-enablement: the signed snapshot must bind its query scope
    s = _valid_snapshot(); del s["collection_scope"]; return s


NEGATIVES = {
    "01_observed_without_value": _neg_observed_without_value,
    "02_relation_without_facts": _neg_relation_without_facts,
    "03_accepted_promote_without_target": _neg_accepted_promote_without_target,
    "04_empty_consumer_evidence": _neg_empty_consumer_evidence,
    "05_invalid_domain": _neg_invalid_domain,
    "06_duplicate_relations": _neg_duplicate_relations,
    "07_unsafe_delete": _neg_unsafe_delete,
    "08_empty_transform": _neg_empty_transform,
    "09_entity_map_accepted_null_ref": _neg_entity_map_accepted_null_ref,
    "10_physical_schema_accepted_null_ref": _neg_physical_schema_accepted_null_ref,
    "11_empty_ta_ref_row": _neg_empty_ta_ref_row,
    "12_invalid_timestamp": _neg_invalid_timestamp,
    "13_not_observed_with_value": _neg_not_observed_with_value,
    "14_not_observed_without_detail": _neg_not_observed_without_detail,
    "15_observed_consumer_null": _neg_observed_consumer_null,
    "16_compat_required_false": _neg_compat_required_false,
    "17_cluster_accepted_null_ta": _neg_cluster_accepted_null_ta,
    "18_cluster_uses_objects": _neg_cluster_uses_objects,
    "19_promote_without_target_objects": _neg_promote_without_target_objects,
    "20_harden_with_target_objects": _neg_harden_with_target_objects,
    "21_typed_rls_yes": _neg_typed_rls_yes,
    "22_typed_row_estimate_array": _neg_typed_row_estimate_array,
    "23_negative_fk": _neg_negative_fk,
    "24_bad_privilege": _neg_bad_privilege,
    "25_retain_unconstrained": _neg_retain_unconstrained,
    "26_archive_has_consumers": _neg_archive_has_consumers,
    "27_window_as_string": _neg_window_as_string,
    "28_harden_without_consumer": _neg_harden_without_consumer,
    "29_nonobserved_dim_missing_nulls": _neg_nonobserved_dim_missing_nulls,
    "30_maintain_privilege": _neg_maintain_privilege,
    "31_compat_zero_window": _neg_compat_zero_window,
    "32_compat_zero_samples": _neg_compat_zero_samples,
    "33_dependency_missing_evidence": _neg_dependency_missing_evidence,
    "34_snapshot_without_target_identity": _neg_snapshot_without_target_identity,
    "35_delete_null_retention": _neg_delete_null_retention,
    "36_retain_null_retention": _neg_retain_null_retention,
    "37_compat_null_contract": _neg_compat_null_contract,
    "38_compat_missing_target_schema": _neg_compat_missing_target_schema,
    "39_promote_has_consumers_null_compat": _neg_promote_has_consumers_null_compat,
    "40_promote_null_exposure": _neg_promote_null_exposure,
    "41_dependency_missing_role": _neg_dependency_missing_role,
    "42_dependency_bad_role": _neg_dependency_bad_role,
    "43_compat_missing_consumer_disposition": _neg_compat_missing_consumer_disposition,
    "44_compat_no_consumer": _neg_compat_no_consumer,
    "45_delete_string_recovery": _neg_delete_string_recovery,
    "46_delete_recovery_missing_sha": _neg_delete_recovery_missing_sha,
    "47_calendar_invalid_observed_at": _neg_calendar_invalid_observed_at,
    "48_snapshot_without_collection_scope": _neg_snapshot_without_collection_scope,
}

POSITIVES = {
    "snapshot": _valid_snapshot(),
    "manifest_proposed": _valid_manifest(),
    "manifest_accepted": {**_valid_manifest(), "status": "accepted", "technical_authority_approval": "TA-cluster-001"},
    "entity_map": _valid_entity_map(),
    "decisions_proposed": _valid_decisions([_row_proposed()]),
    "row_harden": _valid_decisions([_row_harden()]),
    "row_promote": _valid_decisions([_row_promote()]),
    "row_compat": _valid_decisions([_row_compat()]),
    "row_archive": _valid_decisions([_row_archive()]),
    "row_delete": _valid_decisions([_row_delete()]),
    "row_retain": _valid_decisions([_row_retain()]),
}


def test_schema_is_valid_draft202012():
    Draft202012Validator.check_schema(_schema())


def test_negatives_all_fail():
    for name, build in NEGATIVES.items():
        assert not V.is_valid(build()), f"NEGATIVE {name} unexpectedly PASSED"


def test_positives_all_pass():
    for name, doc in POSITIVES.items():
        errs = sorted(V.iter_errors(doc), key=lambda e: str(e.path))
        assert not errs, f"POSITIVE {name} FAILED: {[e.message for e in errs][:3]}"


if __name__ == "__main__":
    ok = True
    print("== schema meta-validation ==")
    try:
        Draft202012Validator.check_schema(_schema()); print("  ok:   valid Draft 2020-12")
    except Exception as exc:  # noqa: BLE001
        ok = False; print(f"  FAIL: {exc}")
    print(f"== negatives (must FAIL): {len(NEGATIVES)} ==")
    for name, build in NEGATIVES.items():
        bad = not V.is_valid(build()); ok = ok and bad
        print(f"  {'ok  ' if bad else 'FAIL'}: neg {name} -> {'rejected' if bad else 'ACCEPTED (bug)'}")
    print(f"== positives (must PASS): {len(POSITIVES)} ==")
    for name, doc in POSITIVES.items():
        errs = sorted(V.iter_errors(doc), key=lambda e: str(e.path)); good = not errs; ok = ok and good
        print(f"  {'ok  ' if good else 'FAIL'}: pos {name}" + ("" if good else f" -> {errs[0].message}"))
    print("\n=== SCHEMA CONTRACT: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
