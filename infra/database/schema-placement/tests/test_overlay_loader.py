"""Loader tests for disposition_overlay.py (Tasks 2-8). Offline; throwaway fixture keys only.

Runner: uv run --project . --locked python tests/test_overlay_loader.py
"""
import copy
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # tests/ dir, to reuse the real helpers
import disposition_overlay as ov  # noqa: E402
import disposition_signing as _ds  # noqa: E402
import test_check_disposition as tcd  # noqa: E402 -- reuse the SCHEMA-VALID snapshot/rel helpers (audit F5)

# Canonical, mutually-coherent fixture clock (audit F5). base census observed_at == tcd._snapshot's;
# NOW is after it; the default overlay captured_at and window sit inside [.., NOW] with
# base_observed_at IN the default window (ended_at == base_observed_at), so the default derivation is
# valid and every timestamp is internally consistent.
CENSUS_OBSERVED_AT = "2026-07-10T20:00:00Z"    # == tcd._snapshot observed_at (base_observed_at)
NOW_ISO = "2026-07-11T00:00:00Z"
DEF_CAPTURED = "2026-07-10T21:00:00Z"          # <= NOW, >= every default window ended_at
DEF_WIN = {"started_at": "2026-06-05T00:00:00Z", "ended_at": CENSUS_OBSERVED_AT}  # ~35d; ended == base_observed_at
_CONTRACT = ov.load_overlay_contract()


def _ephemeral_keypair():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign(obj, priv):
    body = _canon(obj)
    sidecar = json.dumps(_ds.build_sig_sidecar(body, priv)).encode("utf-8")
    return body, sidecar


def _no_bool():
    return {"state": "not_observed", "detail": "pending"}


def _no_ci():
    return {"state": "not_observed", "found_consumers": None, "ref": None, "detail": "pending"}


def _zero_census(oids):
    """A fully SCHEMA-VALID census built from tcd._snapshot/_rel (all required top-level fields:
    repo_sha, collector_version, query_bundle_sha256, catalog_relation_count, collection_scope,
    target_identity, ...), forced to the canonical zero-width consumer window + all six overlay dims
    not_observed. database_deps stays observed (NOT an overlay target). Reuses the real helpers (F5)."""
    rels = []
    for oid in oids:
        schema, name = oid.split(".", 1)
        r = tcd._rel(oid, schema, name, "v")
        r["in_data_api_exposed_schema"] = _no_bool()
        r["advisor_findings"] = _no_bool()
        ce = r["consumer_evidence"]
        ce["observation_window"] = {"started_at": CENSUS_OBSERVED_AT, "ended_at": CENSUS_OBSERVED_AT}
        for dim in ("static_repo", "runtime_logs", "external_clients", "operator_declaration"):
            ce[dim] = _no_ci()
        # database_deps stays observed (tcd._rel set it observed) — not an overlay target
        rels.append(r)
    return tcd._snapshot(rels)  # sets observed_at == CENSUS_OBSERVED_AT + all required snapshot fields


def _overlay(dimension, source_type, assignments, census_bytes=None, **overrides):
    """A well-formed overlay bound to census_bytes. Default source_hash/producing_repo_sha are NON-null
    with NO *_not_applicable_reason (IFF-valid, audit F9); dimensions needing null+reason override both."""
    doc = {"kind": "evidence_overlay", "overlay_version": "1",
           "dimension": dimension, "source_type": source_type,
           "authority": "test", "collection_method": "test", "source_locator": "test:x",
           "source_hash": "e" * 64,
           "base_snapshot_sha256": hashlib.sha256(census_bytes).hexdigest() if census_bytes else "a" * 64,
           "disposition_schema_sha256": _CONTRACT.disp_sha256, "overlay_schema_sha256": _CONTRACT.overlay_sha256,
           "project_ref": "fxoyniqnrlkxfligbxmg",
           "captured_at": DEF_CAPTURED, "observation_window": dict(DEF_WIN),
           "producing_repo_sha": "d" * 40,
           "assignments": assignments}
    doc.update(overrides)
    return doc


def _codes(diags):
    return sorted({c for c, _l, _m in diags})


# ---- Task 2: signature + binding ----
def _tampered_byte_fails_OV001():
    priv, pub = _ephemeral_keypair()
    body, sig = _sign(_overlay("consumer_evidence.static_repo", "repository_scan",
                               [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}]), priv)
    tampered = bytearray(body); tampered[10] ^= 0x01
    ok, _r = ov.verify_overlay(bytes(tampered), sig, pub)
    return ok is False


def _good_signature_verifies():
    priv, pub = _ephemeral_keypair()
    body, sig = _sign(_overlay("consumer_evidence.static_repo", "repository_scan",
                               [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}]), priv)
    ok, _r = ov.verify_overlay(body, sig, pub)
    return ok is True


def _base_hash_mismatch_OV002():
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    doc["base_snapshot_sha256"] = "f" * 64  # not the census hash
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=doc["disposition_schema_sha256"], on_disk_overlay_sha=doc["overlay_schema_sha256"])
    return "OV002" in _codes(diags)


def _project_mismatch_OV003():
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb, project_ref="other-project")
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=doc["disposition_schema_sha256"], on_disk_overlay_sha=doc["overlay_schema_sha256"])
    return "OV003" in _codes(diags)


def _schema_drift_OV020():
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb, disposition_schema_sha256="0" * 64)
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=_CONTRACT.disp_sha256, on_disk_overlay_sha=_CONTRACT.overlay_sha256)
    return "OV020" in _codes(diags)


def _schema_drift_overlay_branch_OV020():
    # The overlay_schema_sha256 half of OV020 must fire independently of the disposition half
    # (regression: the disp-branch test alone left this half unexercised).
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb, overlay_schema_sha256="0" * 64)
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=_CONTRACT.disp_sha256, on_disk_overlay_sha=_CONTRACT.overlay_sha256)
    return "OV020" in _codes(diags)


def _project_mismatch_census_vs_expect_OV003():
    # OV003 is a THREE-way equality: a doc whose project_ref matches the census must STILL be rejected
    # when census_project_ref != expect_project_ref (the --expect-project-ref axis, not just the doc's).
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb)  # doc.project_ref == census_project_ref == fxoyniqnrlkxfligbxmg
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="a-different-expected-ref",
                             on_disk_disp_sha=_CONTRACT.disp_sha256, on_disk_overlay_sha=_CONTRACT.overlay_sha256)
    return "OV003" in _codes(diags)


def _check_binding_clean_no_diags():
    # The POSITIVE side of the fail-closed contract: a correctly-bound overlay yields NO diagnostics.
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb)
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=_CONTRACT.disp_sha256, on_disk_overlay_sha=_CONTRACT.overlay_sha256)
    return diags == []


def _parse_overlay_rejects_duplicate_keys():
    # A JSON body with a repeated object key must raise ValueError (parser-confusion guard, fail-closed).
    try:
        ov.parse_overlay(b'{"kind": "evidence_overlay", "kind": "sneaky"}')
        return False  # must have raised
    except ValueError:
        return True
    except Exception:
        return False


def _parse_overlay_rejects_nonfinite():
    # NaN / Infinity / -Infinity JSON constants must raise ValueError (Python json accepts them by default).
    for body in (b'{"x": NaN}', b'{"x": Infinity}', b'{"x": -Infinity}'):
        try:
            ov.parse_overlay(body)
            return False  # must have raised
        except ValueError:
            continue
        except Exception:
            return False
    return True


def _parse_overlay_accepts_valid_body():
    # Non-vacuity guard for the two reject tests: a well-formed overlay body parses to a dict.
    census_bytes = _canon(_zero_census(["public.v"]))
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=census_bytes)
    parsed = ov.parse_overlay(_canon(doc))
    return isinstance(parsed, dict) and parsed.get("kind") == "evidence_overlay"


_CASES = [
    ("tampered_byte_fails_OV001", _tampered_byte_fails_OV001),
    ("good_signature_verifies", _good_signature_verifies),
    ("base_hash_mismatch_OV002", _base_hash_mismatch_OV002),
    ("project_mismatch_OV003", _project_mismatch_OV003),
    ("schema_drift_OV020", _schema_drift_OV020),
    ("schema_drift_overlay_branch_OV020", _schema_drift_overlay_branch_OV020),
    ("project_mismatch_census_vs_expect_OV003", _project_mismatch_census_vs_expect_OV003),
    ("check_binding_clean_no_diags", _check_binding_clean_no_diags),
    ("parse_overlay_rejects_duplicate_keys", _parse_overlay_rejects_duplicate_keys),
    ("parse_overlay_rejects_nonfinite", _parse_overlay_rejects_nonfinite),
    ("parse_overlay_accepts_valid_body", _parse_overlay_accepts_valid_body),
]


def _rel_index(census):
    return {r["object_id"]: r for r in census["relations"]}


# ---- Task 3: target / conflict / base-window ----
def _dimension_not_permitted_OV004():
    census = _zero_census(["public.v"])
    doc = _overlay("database_deps", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return "OV004" in _codes(ov.check_target(doc, _rel_index(census)))


def _unknown_object_id_OV005():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.absent", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return "OV005" in _codes(ov.check_target(doc, _rel_index(census)))


def _non_not_observed_target_OV006():
    census = _zero_census(["public.v"])
    census["relations"][0]["consumer_evidence"]["static_repo"] = {"state": "query_failed", "found_consumers": None, "ref": None, "detail": "err"}
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return "OV006" in _codes(ov.check_target(doc, _rel_index(census)))


def _source_type_mismatch_OV013():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "runtime_logs",  # wrong source_type for dimension
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return "OV013" in _codes(ov.check_target(doc, _rel_index(census)))


def _operator_declaration_missing_provenance_OV014():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.operator_declaration", "operator_declaration",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 1, "ref": "sha:att1"}}],
                   producing_repo_sha=None, producing_repo_sha_not_applicable_reason="operator attestation")  # forbidden dim -> null+reason (isolates OV014)
    doc.pop("operator_identity", None); doc.pop("attestation_ref", None)
    return "OV014" in _codes(ov.check_target(doc, _rel_index(census)))


def _validate_overlay_unresolvable_maps_to_OV008():
    # audit round-3 F4: an unseeded $ref hit during validation must be CAUGHT by validate_overlay and
    # mapped to a coded OV008 (never an uncaught referencing.Unresolvable, never a network fetch).
    from jsonschema import Draft202012Validator
    from referencing import Registry
    bogus = Draft202012Validator({"$ref": "https://unseeded.example/nope.json#/$defs/x"}, registry=Registry())
    return _codes(ov.validate_overlay({"dimension": "x", "any": 1}, bogus)) == ["OV008"]


def _validate_overlay_calendar_invalid_datetime_OV008():
    # Global-constraint emphasis: a calendar-invalid datetime (Feb 30) is a coded OV008 via the REAL
    # contract overlay_validator's FormatChecker — not an uncaught exception, not silently accepted
    # (the sibling regex pattern alone would NOT catch this; the format check does).
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   captured_at="2026-02-30T00:00:00Z")
    return _codes(ov.validate_overlay(doc, _CONTRACT.overlay_validator)) == ["OV008"]


def _producing_repo_sha_forbidden_nonnull_OV012():
    census = _zero_census(["public.v"])  # advisor_findings is FORBIDDEN: a non-null producing_repo_sha rejects
    doc = _overlay("advisor_findings", "advisor_api",
                   [{"object_id": "public.v", "value": {"state": "observed", "value": ["security_definer_view"]}}])  # default producing_repo_sha="d"*40
    return "OV012" in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_forbidden_null_reason_ok():
    census = _zero_census(["public.v"])
    doc = _overlay("advisor_findings", "advisor_api",
                   [{"object_id": "public.v", "value": {"state": "observed", "value": ["x"]}}],
                   producing_repo_sha=None, producing_repo_sha_not_applicable_reason="advisor API pull")
    return "OV012" not in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_conditional_nonnull_ok():
    census = _zero_census(["public.v"])  # external_clients is CONDITIONAL: non-null (no reason) is allowed
    doc = _overlay("consumer_evidence.external_clients", "external_client_inventory",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "sha:e1"}}])
    return "OV012" not in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_conditional_null_reason_ok():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.external_clients", "external_client_inventory",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "sha:e1"}}],
                   producing_repo_sha=None, producing_repo_sha_not_applicable_reason="no producing repo")
    return "OV012" not in _codes(ov.check_target(doc, _rel_index(census)))


def _source_hash_null_without_reason_OV019():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   source_hash=None); doc.pop("source_hash_not_applicable_reason", None)
    return "OV019" in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_absent_OV012():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",  # this dimension requires producing_repo_sha
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   producing_repo_sha=None); doc.pop("producing_repo_sha_not_applicable_reason", None)
    return "OV012" in _codes(ov.check_target(doc, _rel_index(census)))


def _duplicate_pair_within_and_across_OV007():
    # identical (dimension, object_id) twice, even with identical values, must reject
    keys = [("consumer_evidence.static_repo", "public.v"), ("consumer_evidence.static_repo", "public.v")]
    return "OV007" in _codes(ov.check_conflict(keys))


def _base_nonzero_window_OV021_with_zero_overlays():
    census = _zero_census(["public.v"])
    census["relations"][0]["consumer_evidence"]["observation_window"] = {"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-09T00:00:00Z"}
    return "OV021" in _codes(ov.precheck_base_window(census))


def _base_canonical_window_passes_OV021():
    census = _zero_census(["public.v"])  # already {observed_at, observed_at}
    return ov.precheck_base_window(census) == []


NOW_DT = ov._parse_iso(NOW_ISO)


# ---- Task 3: per-overlay window (OV009) + IFF null-reason (F9) ----
def _window_started_after_ended_OV009():
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   observation_window={"started_at": "2026-07-10T00:00:00Z", "ended_at": "2026-06-01T00:00:00Z"})
    return "OV009" in _codes(ov.check_observation_window(doc, NOW_DT))


def _window_ended_after_captured_OV009():
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   captured_at="2026-07-08T00:00:00Z", observation_window={"started_at": "2026-06-05T00:00:00Z", "ended_at": "2026-07-09T00:00:00Z"})
    return "OV009" in _codes(ov.check_observation_window(doc, NOW_DT))


def _window_future_ended_OV009():
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   captured_at="2026-07-20T00:00:00Z", observation_window={"started_at": "2026-06-05T00:00:00Z", "ended_at": "2026-07-15T00:00:00Z"})  # ended after NOW
    return "OV009" in _codes(ov.check_observation_window(doc, NOW_DT))


def _in_data_api_overlay_window_is_checked_OV009():
    # The Data-API-exposure overlay (observed_bool, NOT a consumer contributor) still passes OV009 (F2).
    doc = _overlay("in_data_api_exposed_schema", "platform_config",
                   [{"object_id": "public.v", "value": {"state": "observed", "value": False}}],
                   observation_window={"started_at": "2026-07-10T00:00:00Z", "ended_at": "2026-06-01T00:00:00Z"})
    return "OV009" in _codes(ov.check_observation_window(doc, NOW_DT))


def _valid_window_passes_OV009():
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return ov.check_observation_window(doc, NOW_DT) == []


def _source_hash_reason_with_nonnull_OV019():
    # IFF (F9): a reason supplied ALONGSIDE a non-null source_hash is also rejected.
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   source_hash="e" * 64, source_hash_not_applicable_reason="should not be here")
    return "OV019" in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_reason_with_nonnull_OV012():
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   producing_repo_sha="d" * 40, producing_repo_sha_not_applicable_reason="should not be here")
    return "OV012" in _codes(ov.check_target(doc, _rel_index(census)))


def _malformed_window_null_timestamp_OV009():
    # Fail-closed (round-3 review): a null / non-string window timestamp must be a coded OV009,
    # never an uncaught AttributeError from _parse_iso's .replace().
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   observation_window={"started_at": None, "ended_at": "2026-07-09T00:00:00Z"})
    return "OV009" in _codes(ov.check_observation_window(doc, NOW_DT))


def _validate_overlay_clean_no_diags():
    # Happy-path guard: a fully valid overlay yields NO OV008 (guards against a spurious-reject regression).
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    return ov.validate_overlay(doc, _CONTRACT.overlay_validator) == []


def _check_conflict_distinct_no_diags():
    # Mutation guard: distinct (dimension, object_id) keys yield NO OV007 (kills an `n >= 1` flag-everything bug).
    keys = [("consumer_evidence.static_repo", "public.v"),
            ("consumer_evidence.runtime_logs", "public.v"),
            ("consumer_evidence.static_repo", "public.w")]
    return ov.check_conflict(keys) == []


def _producing_repo_sha_forbidden_null_without_reason_OV012():
    # FORBIDDEN dim (advisor_findings): null producing_repo_sha WITHOUT a reason must reject (matrix completeness).
    census = _zero_census(["public.v"])
    doc = _overlay("advisor_findings", "advisor_api",
                   [{"object_id": "public.v", "value": {"state": "observed", "value": ["x"]}}],
                   producing_repo_sha=None)
    doc.pop("producing_repo_sha_not_applicable_reason", None)
    return "OV012" in _codes(ov.check_target(doc, _rel_index(census)))


def _producing_repo_sha_conditional_null_without_reason_OV012():
    # CONDITIONAL dim (external_clients): null producing_repo_sha WITHOUT a reason must reject (matrix completeness).
    census = _zero_census(["public.v"])
    doc = _overlay("consumer_evidence.external_clients", "external_client_inventory",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "sha:e1"}}],
                   producing_repo_sha=None)
    doc.pop("producing_repo_sha_not_applicable_reason", None)
    return "OV012" in _codes(ov.check_target(doc, _rel_index(census)))


_CASES += [
    ("dimension_not_permitted_OV004", _dimension_not_permitted_OV004),
    ("unknown_object_id_OV005", _unknown_object_id_OV005),
    ("non_not_observed_target_OV006", _non_not_observed_target_OV006),
    ("source_type_mismatch_OV013", _source_type_mismatch_OV013),
    ("operator_declaration_missing_provenance_OV014", _operator_declaration_missing_provenance_OV014),
    ("source_hash_null_without_reason_OV019", _source_hash_null_without_reason_OV019),
    ("producing_repo_sha_absent_OV012", _producing_repo_sha_absent_OV012),
    ("source_hash_reason_with_nonnull_OV019", _source_hash_reason_with_nonnull_OV019),
    ("producing_repo_sha_reason_with_nonnull_OV012", _producing_repo_sha_reason_with_nonnull_OV012),
    ("producing_repo_sha_forbidden_nonnull_OV012", _producing_repo_sha_forbidden_nonnull_OV012),
    ("producing_repo_sha_forbidden_null_reason_ok", _producing_repo_sha_forbidden_null_reason_ok),
    ("producing_repo_sha_conditional_nonnull_ok", _producing_repo_sha_conditional_nonnull_ok),
    ("producing_repo_sha_conditional_null_reason_ok", _producing_repo_sha_conditional_null_reason_ok),
    ("validate_overlay_unresolvable_maps_to_OV008", _validate_overlay_unresolvable_maps_to_OV008),
    ("validate_overlay_calendar_invalid_datetime_OV008", _validate_overlay_calendar_invalid_datetime_OV008),
    ("duplicate_pair_within_and_across_OV007", _duplicate_pair_within_and_across_OV007),
    ("window_started_after_ended_OV009", _window_started_after_ended_OV009),
    ("window_ended_after_captured_OV009", _window_ended_after_captured_OV009),
    ("window_future_ended_OV009", _window_future_ended_OV009),
    ("in_data_api_overlay_window_is_checked_OV009", _in_data_api_overlay_window_is_checked_OV009),
    ("valid_window_passes_OV009", _valid_window_passes_OV009),
    ("base_nonzero_window_OV021_with_zero_overlays", _base_nonzero_window_OV021_with_zero_overlays),
    ("base_canonical_window_passes_OV021", _base_canonical_window_passes_OV021),
    ("malformed_window_null_timestamp_OV009", _malformed_window_null_timestamp_OV009),
    ("validate_overlay_clean_no_diags", _validate_overlay_clean_no_diags),
    ("check_conflict_distinct_no_diags", _check_conflict_distinct_no_diags),
    ("producing_repo_sha_forbidden_null_without_reason_OV012", _producing_repo_sha_forbidden_null_without_reason_OV012),
    ("producing_repo_sha_conditional_null_without_reason_OV012", _producing_repo_sha_conditional_null_without_reason_OV012),
]

# ---- Task 4: time derivation (derive_windows) ----
def _pdt(s):
    return ov._parse_iso(s)


BASE = _pdt(CENSUS_OBSERVED_AT)          # 2026-07-10T20:00:00Z (base_observed_at)
NOW = _pdt(NOW_ISO)                      # 2026-07-11T00:00:00Z


def _contrib_map(*entries):
    """Build a LOCAL {oid: [(started, ended, captured), ...]} contributor map (audit #9: passed as a
    separate arg to derive_windows — NEVER stashed on the effective snapshot)."""
    m = {}
    for oid, started, ended, captured in entries:
        m.setdefault(oid, []).append((_pdt(started), _pdt(ended), _pdt(captured)))
    return m


def _derive(eff, contrib, max_age=8760):
    return ov.derive_windows(eff, cluster_src_oids=set(contrib) or {"public.v"}, contrib_by_oid=contrib,
                             now=NOW, base_observed_at=BASE, max_consumer_evidence_age_hours=max_age)


def _fresh_window_derives_ok():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED))
    diags, derived = _derive(eff, contrib)
    return diags == [] and "public.v" in derived


def _decade_old_window_OV016():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2016-06-01T00:00:00Z", "2016-07-01T00:00:00Z", "2016-07-02T00:00:00Z"))
    diags, _d = _derive(eff, contrib)
    return "OV016" in _codes(diags)


def _absent_maxage_is_OV016():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED))
    diags, _d = _derive(eff, contrib, max_age=None)
    return "OV016" in _codes(diags)


def _nonfinite_maxage_is_OV016():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED))
    diags, _d = _derive(eff, contrib, max_age=float("inf"))
    return "OV016" in _codes(diags)


def _base_outside_window_OV017():
    eff = _zero_census(["public.v"])  # base_observed_at = 07-10T20; window ends 07-05 < base
    contrib = _contrib_map(("public.v", "2026-06-01T00:00:00Z", "2026-07-05T00:00:00Z", "2026-07-06T00:00:00Z"))
    diags, _d = _derive(eff, contrib)
    return "OV017" in _codes(diags)


def _empty_contributors_OV018():
    eff = _zero_census(["public.v"])
    diags, _d = ov.derive_windows(eff, cluster_src_oids={"public.v"}, contrib_by_oid={}, now=NOW,
                                  base_observed_at=BASE, max_consumer_evidence_age_hours=8760)
    return "OV018" in _codes(diags)


def _empty_intersection_OV011():
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-07-08T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED),   # ended 07-10T20
                           ("public.v", "2026-06-05T00:00:00Z", "2026-07-05T00:00:00Z", "2026-07-06T00:00:00Z"))  # ended 07-05
    diags, _d = _derive(eff, contrib)  # S=max(07-08,06-05)=07-08 ; E=min(07-10T20,07-05)=07-05 ; S>E
    return "OV011" in _codes(diags)


def _duplicate_src_object_single_derivation():
    # object_id appears once in the set => derived exactly once; the derived marker is idempotent.
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED))
    diags, derived = _derive(eff, contrib)
    w = eff["relations"][0]["consumer_evidence"]["observation_window"]
    return diags == [] and list(derived) == ["public.v"] and w["started_at"] and w["ended_at"] and "_contrib_windows" not in eff


def _multi_contributor_intersection_exact_window():
    # Locks the CORE derivation math on the SUCCESS path across TWO contributors: S=max(started),
    # E=min(ended) => the intersection is written. A max<->min swap would change these exact values
    # (and here also trip E>min_captured), so this case catches a swap the reject-path tests cannot.
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-01T00:00:00Z", CENSUS_OBSERVED_AT, DEF_CAPTURED),          # ended = base
                           ("public.v", "2026-06-20T00:00:00Z", "2026-07-12T00:00:00Z", "2026-07-12T00:00:00Z"))
    diags, derived = _derive(eff, contrib)
    w = eff["relations"][0]["consumer_evidence"]["observation_window"]
    # S = max(06-01, 06-20) = 06-20 ; E = min(base=07-10T20, 07-12) = base
    return (diags == [] and "public.v" in derived
            and w["started_at"] == _pdt("2026-06-20T00:00:00Z").isoformat()
            and w["ended_at"] == BASE.isoformat())


def _future_ended_window_OV009():
    # The derive-time future-E OV009 branch: a contributor whose ended_at is after `now` is rejected
    # (captured_at set later so the E>min_captured branch does not pre-empt it).
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", "2026-07-15T00:00:00Z", "2026-07-16T00:00:00Z"))  # ended 07-15 > NOW 07-11
    diags, _d = _derive(eff, contrib)
    return "OV009" in _codes(diags)


def _ended_after_captured_defense_OV009():
    # The derive-time defense-assert OV009 branch: a contributor whose ended_at is after its own
    # captured_at is rejected (an inconsistency the per-overlay OV009 also catches upstream).
    eff = _zero_census(["public.v"])
    contrib = _contrib_map(("public.v", "2026-06-05T00:00:00Z", "2026-07-09T00:00:00Z", "2026-07-08T00:00:00Z"))  # ended 07-09 > captured 07-08
    diags, _d = _derive(eff, contrib)
    return "OV009" in _codes(diags)


_CASES += [
    ("fresh_window_derives_ok", _fresh_window_derives_ok),
    ("decade_old_window_OV016", _decade_old_window_OV016),
    ("absent_maxage_is_OV016", _absent_maxage_is_OV016),
    ("nonfinite_maxage_is_OV016", _nonfinite_maxage_is_OV016),
    ("base_outside_window_OV017", _base_outside_window_OV017),
    ("empty_contributors_OV018", _empty_contributors_OV018),
    ("empty_intersection_OV011", _empty_intersection_OV011),
    ("duplicate_src_object_single_derivation", _duplicate_src_object_single_derivation),
    ("multi_contributor_intersection_exact_window", _multi_contributor_intersection_exact_window),
    ("future_ended_window_OV009", _future_ended_window_OV009),
    ("ended_after_captured_defense_OV009", _ended_after_captured_defense_OV009),
]

# ---- Task 5: OV022 delete-floor coherence (T1/T2-scoped) ----
def _ov022_fires_when_window_not_covering():
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    # in_data_api overlay window starts AFTER S -> does NOT cover [S,E]
    inapi = {"public.v": (_pdt("2026-07-05T00:00:00Z"), _pdt("2026-07-10T20:00:00Z"))}
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids={"public.v"},
                                            in_data_api_windows=inapi, derived_windows={"public.v": (S, E)})
    return "OV022" in _codes(diags)


def _ov022_ok_when_window_covers():
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    inapi = {"public.v": (_pdt("2026-06-01T00:00:00Z"), _pdt("2026-07-15T00:00:00Z"))}  # covers [S,E]
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids={"public.v"},
                                            in_data_api_windows=inapi, derived_windows={"public.v": (S, E)})
    return diags == []


def _external_clients_observed_no_OV022():
    # external_clients OBSERVED -> the not_applicable waiver is not invoked -> OV022 not evaluated (T1)
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    inapi = {"public.v": (_pdt("2026-07-05T00:00:00Z"), _pdt("2026-07-08T00:00:00Z"))}  # narrow, would fail if evaluated
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids=set(),  # NOT not_applicable
                                            in_data_api_windows=inapi, derived_windows={"public.v": (S, E)})
    return diags == []


def _missing_in_data_api_no_OV022():
    # NO observed-false in_data_api overlay backs the waiver -> check_delete_floor_coherence emits NO
    # OV022 (it defers). The OVERALL routing for a missing overlay is OV015 (cluster-completeness) and,
    # for an observed-TRUE overlay, SP027 at the semantic gate — both exercised in Task 8 (audit F2).
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids={"public.v"},
                                            in_data_api_windows={}, derived_windows={"public.v": (S, E)})
    return "OV022" not in _codes(diags)


def _ov022_fires_when_ended_short():
    # Locks the ENDED half of the covering predicate (review-Important): api_started covers S but
    # api_ended < E => fires. A mutation dropping the `and api_e >= e` conjunct would survive without this.
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    inapi = {"public.v": (_pdt("2026-06-25T00:00:00Z"), _pdt("2026-07-08T00:00:00Z"))}  # started<=S, ended 07-08 < E
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids={"public.v"},
                                            in_data_api_windows=inapi, derived_windows={"public.v": (S, E)})
    return "OV022" in _codes(diags)


def _ov022_ok_exact_boundary():
    # Locks the <= / >= boundary: an in_data_api window EXACTLY equal to [S,E] covers => no OV022.
    # A `<`-for-`<=` (or `>`-for-`>=`) off-by-one would spuriously fire here.
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    inapi = {"public.v": (S, E)}  # exact match on BOTH ends
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids={"public.v"}, external_na_oids={"public.v"},
                                            in_data_api_windows=inapi, derived_windows={"public.v": (S, E)})
    return diags == []


def _ov022_non_delete_oid_no_OV022():
    # T1 symmetry: an oid with external_clients=not_applicable but NOT a delete-conclusion source is
    # never evaluated (empty delete_src_oids ∩ external_na_oids), even with a deliberately non-covering window.
    eff = _zero_census(["public.v"])
    S, E = _pdt("2026-07-01T00:00:00Z"), _pdt("2026-07-10T20:00:00Z")
    inapi = {"public.v": (_pdt("2026-07-05T00:00:00Z"), _pdt("2026-07-08T00:00:00Z"))}  # non-covering, would fire if evaluated
    diags = ov.check_delete_floor_coherence(eff, delete_src_oids=set(), external_na_oids={"public.v"},
                                            in_data_api_windows=inapi, derived_windows={"public.v": (S, E)})
    return "OV022" not in _codes(diags)


_CASES += [
    ("ov022_fires_when_window_not_covering", _ov022_fires_when_window_not_covering),
    ("ov022_ok_when_window_covers", _ov022_ok_when_window_covers),
    ("external_clients_observed_no_OV022", _external_clients_observed_no_OV022),
    ("missing_in_data_api_no_OV022", _missing_in_data_api_no_OV022),
    ("ov022_fires_when_ended_short", _ov022_fires_when_ended_short),
    ("ov022_ok_exact_boundary", _ov022_ok_exact_boundary),
    ("ov022_non_delete_oid_no_OV022", _ov022_non_delete_oid_no_OV022),
]


# ---- Task 6: load_and_merge orchestration + effective-view integrity ----
class _FakeSigner:
    """Stands in for disposition_trust.ResolvedSigner (public_key + provenance for the receipt, F3)."""
    def __init__(self, pub):
        self.public_key = pub
        self.key_id = "test-signer"
        self.spki_sha256 = "f" * 64


def _decisions_manifest(oids, action="harden", conclusion="unresolved", required=None):
    # default conclusion 'unresolved' + empty required_observations => OV015 is NOT triggered, so these
    # merge-mechanics unit tests isolate the deepcopy/derivation/receipt behavior. (Full gate-required
    # coverage + OV015 are exercised in Task 8's e2e + Task 6's dedicated OV015 case below.)
    rows = [{"decision_id": "D1", "action_class": action, "decision_status": "accepted",
             "consumer_disposition": conclusion, "source_objects": list(oids)}]
    decisions = {"kind": "decisions_file", "rows": rows}
    manifest = {"kind": "cluster_manifest", "cluster_id": "c-001", "status": "accepted", "action_class": action,
                "decision_ids": ["D1"], "evidence_snapshot": "prod.json", "max_staleness_hours": 8760,
                "minimum_consumer_window_hours": 24, "required_observations": list(required or []),
                "technical_authority_approval": "TA-1"}
    return decisions, manifest


def _static_overlay(cb, oid="public.v", **overrides):
    return _overlay("consumer_evidence.static_repo", "repository_scan",
                    [{"object_id": oid, "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                    census_bytes=cb, **overrides)


def _merge(census, cb, overlays, decisions, manifest, signer, max_stale=8760):
    inputs = []
    for i, ov_doc in enumerate(overlays):
        ob, sig = _sign(ov_doc, signer[0])
        inputs.append((f"o{i}.json", f"o{i}.json.sig", ob, sig))
    return ov.load_and_merge(census=census, census_bytes=cb, overlay_inputs=inputs, manifest=manifest,
                             decisions=decisions, expect_project_ref="fxoyniqnrlkxfligbxmg", now=NOW,
                             max_consumer_evidence_age_hours=8760, max_staleness_hours=max_stale,
                             resolved_signer=signer[1], contract=_CONTRACT)


def _merge_deepcopy_unmutated():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    before = copy.deepcopy(census)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = _merge(census, cb, [_static_overlay(cb)], decisions, manifest, (priv, _FakeSigner(pub)))
    # base census object is unmutated; the effective view got a derived window (started_at moved off the
    # zero-width base); and no scratch contributor map leaked onto the effective snapshot (audit #9).
    w = res.effective_snapshot["relations"][0]["consumer_evidence"]["observation_window"]
    return (census == before and res.diagnostics == [] and w["started_at"] != CENSUS_OBSERVED_AT
            and "_contrib_windows" not in res.effective_snapshot)


def _stale_overlay_captured_at_OV010():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    # coherent window (ended <= captured, no OV009) but captured_at far older than max_staleness_hours
    o = _static_overlay(cb, captured_at="2020-01-05T00:00:00Z",
                        observation_window={"started_at": "2019-12-01T00:00:00Z", "ended_at": "2020-01-01T00:00:00Z"})
    decisions, manifest = _decisions_manifest(["public.v"])
    res = _merge(census, cb, [o], decisions, manifest, (priv, _FakeSigner(pub)), max_stale=24)
    return "OV010" in _codes(res.diagnostics)


def _future_captured_at_OV010():
    # OV010 future-captured branch (review Minor #3): an overlay captured_at AFTER `now` is rejected —
    # the stale test covers only the too-old branch. Window stays coherent (ended <= captured, <= now).
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    o = _static_overlay(cb, captured_at="2026-07-20T00:00:00Z")  # after NOW 2026-07-11; default window ends 07-10T20
    decisions, manifest = _decisions_manifest(["public.v"])
    res = _merge(census, cb, [o], decisions, manifest, (priv, _FakeSigner(pub)))
    return "OV010" in _codes(res.diagnostics)


def _effective_view_datetimes_are_iso():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = _merge(census, cb, [_static_overlay(cb)], decisions, manifest, (priv, _FakeSigner(pub)))
    w = res.effective_snapshot["relations"][0]["consumer_evidence"]["observation_window"]
    pat = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
    return res.diagnostics == [] and re.match(pat, w["started_at"]) and re.match(pat, w["ended_at"])


def _receipt_binds_sidecar_and_signer():
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = _merge(census, cb, [_static_overlay(cb)], decisions, manifest, (priv, _FakeSigner(pub)))
    e = res.receipt_overlays[0]
    return (res.diagnostics == [] and e["path"] == "o0.json" and e["sig_path"] == "o0.json.sig"
            and len(e["raw_sha256"]) == 64 and len(e["sig_sha256"]) == 64
            and e["signer"]["key_id"] == "test-signer" and e["signer"]["spki_sha256"] == "f" * 64
            and e["object_ids"] == ["public.v"] and e["dimension"] == "consumer_evidence.static_repo"
            and e["disposition_schema_sha256"] == _CONTRACT.disp_sha256)


def _ov015_missing_gate_required_dimension():
    # A resolved (no_consumer) conclusion forces every consumer contributor dim; supplying only
    # static_repo leaves runtime_logs/external_clients/operator_declaration unresolved -> OV015 (F7).
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    decisions, manifest = _decisions_manifest(["public.v"], conclusion="no_consumer")
    res = _merge(census, cb, [_static_overlay(cb)], decisions, manifest, (priv, _FakeSigner(pub)))
    return "OV015" in _codes(res.diagnostics)


def _signed_non_object_overlay_OV008():
    # a SIGNED JSON array (not an object) must be a coded OV008, never an uncaught AttributeError (F1).
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    body, sig = _sign(["not", "an", "object"], priv)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = ov.load_and_merge(census=census, census_bytes=cb, overlay_inputs=[("bad.json", "bad.json.sig", body, sig)],
                            manifest=manifest, decisions=decisions, expect_project_ref="fxoyniqnrlkxfligbxmg", now=NOW,
                            max_consumer_evidence_age_hours=8760, max_staleness_hours=8760,
                            resolved_signer=_FakeSigner(pub), contract=_CONTRACT)
    return "OV008" in _codes(res.diagnostics)  # reached here => no uncaught exception


def _signed_malformed_assignments_OV008():
    # a SIGNED object whose assignments is the wrong TYPE (not an array) -> schema OV008, no crash: the
    # short-circuit skips the assignment iteration that would otherwise iterate a string (F1).
    priv, pub = _ephemeral_keypair()
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _static_overlay(cb)
    doc["assignments"] = "not-an-array"
    body, sig = _sign(doc, priv)
    decisions, manifest = _decisions_manifest(["public.v"])
    res = ov.load_and_merge(census=census, census_bytes=cb, overlay_inputs=[("m.json", "m.json.sig", body, sig)],
                            manifest=manifest, decisions=decisions, expect_project_ref="fxoyniqnrlkxfligbxmg", now=NOW,
                            max_consumer_evidence_age_hours=8760, max_staleness_hours=8760,
                            resolved_signer=_FakeSigner(pub), contract=_CONTRACT)
    return "OV008" in _codes(res.diagnostics)


_CASES += [
    ("merge_deepcopy_unmutated", _merge_deepcopy_unmutated),
    ("stale_overlay_captured_at_OV010", _stale_overlay_captured_at_OV010),
    ("future_captured_at_OV010", _future_captured_at_OV010),
    ("effective_view_datetimes_are_iso", _effective_view_datetimes_are_iso),
    ("receipt_binds_sidecar_and_signer", _receipt_binds_sidecar_and_signer),
    ("ov015_missing_gate_required_dimension", _ov015_missing_gate_required_dimension),
    ("signed_non_object_overlay_OV008", _signed_non_object_overlay_OV008),
    ("signed_malformed_assignments_OV008", _signed_malformed_assignments_OV008),
]

# ---- Task 8: CLI wiring + end-to-end negatives + migrate main()-level baselines ----
import contextlib
import io
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_disposition as cd  # noqa: E402
import disposition_trust as dt  # noqa: E402


def _wb(path, b):
    with open(path, "wb") as fh:
        fh.write(b if isinstance(b, (bytes, bytearray)) else json.dumps(b).encode("utf-8"))
    return path


def _pin_signer(pub):
    """Monkeypatch the trust anchor so the throwaway key resolves as the pinned 'test-signer' (tests
    only). Returns the saved TRUSTED_SIGNERS to restore in a finally."""
    from cryptography.hazmat.primitives import serialization
    fp = hashlib.sha256(pub.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)).hexdigest()
    saved = dict(dt.TRUSTED_SIGNERS)
    dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS["test-signer"] = fp
    return saved


def _keys_dir(tmp, pub):
    from cryptography.hazmat.primitives import serialization
    kd = os.path.join(tmp, "keys"); os.makedirs(kd, exist_ok=True)
    _wb(os.path.join(kd, "test-signer.pub.pem"),
        pub.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    return kd


def _capture_main(argv):
    # Catch SystemExit so these tests start RED cleanly BEFORE implementation: an unknown --overlay /
    # --max-consumer-evidence-age-hours makes argparse call sys.exit(2) (a BaseException the runner's
    # `except Exception` would NOT catch), which would otherwise crash the whole suite instead of
    # reporting a per-test FAIL. After the CLI flags exist, cd.main returns an int normally.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc = cd.main(argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 2
    return rc, buf.getvalue()


def _harden_docs(oid):
    # disposition.schema.json pins an ACCEPTED harden decision's consumer_disposition to the resolved
    # enum {no_consumer, has_consumers} (a bare "unresolved" is a coded SP001 at the schema boundary,
    # not a semantic gate) -- so 'no_consumer' is used here, which makes SP022 force EVERY consumer dim
    # resolved on the effective view; required_observations additionally names in_data_api (a
    # permitted-overlay target, base not_observed) as a gate-required dim.
    d = {"decision_id": "D-h1", "source_objects": [oid], "meaning_disposition": "preserve",
         "action_class": "harden", "decision_status": "accepted", "exposure_policy": "service_only",
         "consumer_disposition": "no_consumer", "evidence_refs": ["query:x"], "technical_authority_approval": "TA-1"}
    manifest = {"kind": "cluster_manifest", "cluster_id": "c-001", "status": "accepted", "action_class": "harden",
                "decision_ids": ["D-h1"], "evidence_snapshot": "census.json", "max_staleness_hours": 8760,
                "minimum_consumer_window_hours": 24, "required_observations": ["in_data_api_exposed_schema"],
                "technical_authority_approval": "TA-1"}
    return tcd._decs([d]), manifest, tcd._entity_map()


def _base_argv(tmp, cpath, dpath, epath, mpath, pub):
    return ["--snapshot", cpath, "--snapshot-sig", cpath + ".sig", "--decisions", dpath,
            "--entity-map", epath, "--manifest", mpath, "--now", NOW_ISO, "--mode", "preapply",
            "--expect-project-ref", "fxoyniqnrlkxfligbxmg", "--key-id", "test-signer",
            "--keys-dir", _keys_dir(tmp, pub), "--allow-unbound-checkout",
            "--max-consumer-evidence-age-hours", "8760", "--root", tmp]


def _write_harden_case(priv, pub, census):
    tmp = tempfile.mkdtemp(prefix="ov_e2e_")
    cb = _canon(census)
    cpath = _wb(os.path.join(tmp, "census.json"), cb); _wb(cpath + ".sig", _sign(census, priv)[1])
    decisions, manifest, em = _harden_docs("public.v")
    dpath = _wb(os.path.join(tmp, "dec.json"), _canon(decisions))
    epath = _wb(os.path.join(tmp, "ent.json"), _canon(em))
    mpath = _wb(os.path.join(tmp, "man.json"), _canon(manifest))
    return tmp, cb, _base_argv(tmp, cpath, dpath, epath, mpath, pub)


def _e2e_red_then_green():
    priv, pub = _ephemeral_keypair(); saved = _pin_signer(pub); oid = "public.v"
    try:
        tmp, cb, base = _write_harden_case(priv, pub, _zero_census([oid]))
        rc_red, _o = _capture_main(base)                          # RED: zero overlays -> OV018/OV015
        # GREEN: in_data_api observed-false (gate-required) + the full consumer set (static_repo/
        # runtime_logs/external_clients/operator_declaration observed) — an accepted harden's
        # no_consumer conclusion forces every consumer dim resolved (SP022) on the effective view.
        # Consumer refs use the 'sha:' scheme so SP014 treats them as non-path (a bare id would be a path ref).
        ov_api = _overlay("in_data_api_exposed_schema", "platform_config",
                          [{"object_id": oid, "value": {"state": "observed", "value": False}}], census_bytes=cb)
        opts = []
        for i, o in enumerate([ov_api] + _harden_consumer_overlays(cb, oid)):
            p = os.path.join(tmp, f"ov{i}.json"); ob, sig = _sign(o, priv); _wb(p, ob); _wb(p + ".sig", sig); opts += ["--overlay", p]
        rpath = os.path.join(tmp, "receipt.json")
        rc_green, _o2 = _capture_main(base + opts + ["--receipt-out", rpath])
        receipt = json.load(open(rpath)) if os.path.exists(rpath) else {}
        return (rc_red == 1 and rc_green == 0 and receipt.get("evidence_ready") is True
                and receipt.get("execution_authorized") is False and "production_eligible" not in receipt)
    finally:
        dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS.update(saved)


def _e2e_ov021_via_main():
    priv, pub = _ephemeral_keypair(); saved = _pin_signer(pub); oid = "public.v"
    try:
        census = _zero_census([oid])
        census["relations"][0]["consumer_evidence"]["observation_window"] = {"started_at": "2026-06-05T00:00:00Z", "ended_at": CENSUS_OBSERVED_AT}
        _tmp, _cb, base = _write_harden_case(priv, pub, census)   # non-zero base window, zero overlays
        rc, out = _capture_main(base)
        return rc == 1 and "OV021" in out
    finally:
        dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS.update(saved)


# ---- delete/retain/SP018 e2e helpers + the six named tests (audit round-4 F2) ----
def _write_case(priv, pub, census, docs, extra_roots=()):
    """Generalizes _write_harden_case to any (decisions, manifest, entity_map) + extra --root dirs."""
    tmp = tempfile.mkdtemp(prefix="ov_e2e_")
    cb = _canon(census)
    cpath = _wb(os.path.join(tmp, "census.json"), cb); _wb(cpath + ".sig", _sign(census, priv)[1])
    decisions, manifest, em = docs
    dpath = _wb(os.path.join(tmp, "dec.json"), _canon(decisions))
    epath = _wb(os.path.join(tmp, "ent.json"), _canon(em))
    mpath = _wb(os.path.join(tmp, "man.json"), _canon(manifest))
    argv = _base_argv(tmp, cpath, dpath, epath, mpath, pub)
    for r in extra_roots:
        argv += ["--root", r]
    return tmp, cb, argv


def _add_overlays(tmp, priv, overlays):
    opts = []
    for i, o in enumerate(overlays):
        p = os.path.join(tmp, f"ov{i}.json"); ob, sig = _sign(o, priv); _wb(p, ob); _wb(p + ".sig", sig)
        opts += ["--overlay", p]
    return opts


def _consumer_overlay(dim, cb, ref, state="observed", **overrides):
    src = {"static_repo": "repository_scan", "runtime_logs": "runtime_logs",
           "external_clients": "external_client_inventory", "operator_declaration": "operator_declaration"}[dim]
    value = ({"state": "observed", "found_consumers": 0, "ref": ref} if state == "observed"
             else {"state": state, "found_consumers": None, "ref": None, "detail": "n/a"})
    return _overlay(f"consumer_evidence.{dim}", src, [{"object_id": "public.v", "value": value}], census_bytes=cb, **overrides)


def _in_data_api_overlay(cb, value, window=None):
    extra = {"observation_window": window} if window else {}
    return _overlay("in_data_api_exposed_schema", "platform_config",
                    [{"object_id": "public.v", "value": {"state": "observed", "value": value}}], census_bytes=cb, **extra)


def _harden_consumer_overlays(cb, oid="public.v"):
    """Full no_consumer resolution set for an accepted harden decision (disposition.schema.json pins
    consumer_disposition to no_consumer/has_consumers for accepted harden -- SP022 then requires EVERY
    consumer dim resolved on the effective view; unlike the delete floor, harden has no SP027
    not_applicable waiver, so external_clients is simply observed like the other three)."""
    return [
        _consumer_overlay("static_repo", cb, "sha:s1"),
        _consumer_overlay("runtime_logs", cb, "sha:r1", producing_repo_sha=None, producing_repo_sha_not_applicable_reason="runtime query"),
        _consumer_overlay("external_clients", cb, "sha:e1"),
        _consumer_overlay("operator_declaration", cb, "sha:o1", producing_repo_sha=None,
                          producing_repo_sha_not_applicable_reason="operator", operator_identity="op-1", attestation_ref="att-1"),
    ]


def _delete_consumer_overlays(cb):
    """The SP027/SP022 consumer set for a no_consumer delete: static_repo/runtime_logs/operator_declaration
    observed (windowed contributors) + external_clients not_applicable (invokes the SP027 waiver)."""
    return [
        _consumer_overlay("static_repo", cb, "sha:s1"),  # producing_repo_sha default "d"*40 (required category)
        _consumer_overlay("runtime_logs", cb, "sha:r1", producing_repo_sha=None, producing_repo_sha_not_applicable_reason="runtime query"),
        _consumer_overlay("operator_declaration", cb, "sha:o1", producing_repo_sha=None,
                          producing_repo_sha_not_applicable_reason="operator", operator_identity="op-1", attestation_ref="att-1"),
        _consumer_overlay("external_clients", cb, None, state="not_applicable",
                          producing_repo_sha=None, producing_repo_sha_not_applicable_reason="no external clients"),
    ]


def _delete_docs(oid):
    d = {"decision_id": "D-d1", "source_objects": [oid], "meaning_disposition": "retire",
         "action_class": "delete", "decision_status": "accepted", "consumer_disposition": "no_consumer",
         "retention_disposition": {"policy": "delete_after", "recovery_proof": tcd._recovery_artifact()},
         "evidence_refs": ["query:x"], "technical_authority_approval": "TA-5"}
    manifest = {"kind": "cluster_manifest", "cluster_id": "c-001", "status": "accepted", "action_class": "delete",
                "decision_ids": ["D-d1"], "evidence_snapshot": "census.json", "max_staleness_hours": 8760,
                "minimum_consumer_window_hours": 24, "required_observations": ["in_data_api_exposed_schema"],
                "technical_authority_approval": "TA-5"}
    return tcd._decs([d]), manifest, tcd._entity_map()


def _retain_docs(oid):
    d = {"decision_id": "D-r1", "source_objects": [oid], "meaning_disposition": "preserve",
         "action_class": "retain", "decision_status": "accepted", "consumer_disposition": "unresolved",
         "retention_disposition": {"policy": "retain", "recovery_proof": None},
         "evidence_refs": ["query:x"], "technical_authority_approval": "TA-r"}
    manifest = {"kind": "cluster_manifest", "cluster_id": "c-001", "status": "accepted", "action_class": "retain",
                "decision_ids": ["D-r1"], "evidence_snapshot": "census.json", "max_staleness_hours": 8760,
                "minimum_consumer_window_hours": 24, "required_observations": ["in_data_api_exposed_schema"],
                "technical_authority_approval": "TA-r"}
    return tcd._decs([d]), manifest, tcd._entity_map()


def _run_case(docs, build_overlays, receipt=False, extra_roots=()):
    """Write a case, sign the overlays build_overlays(cb) produces, run cd.main, return (rc, out, receipt_path_or_None)."""
    priv, pub = _ephemeral_keypair(); saved = _pin_signer(pub)
    try:
        tmp, cb, base = _write_case(priv, pub, _zero_census(["public.v"]), docs, extra_roots=extra_roots)
        argv = base + _add_overlays(tmp, priv, build_overlays(cb))
        rpath = None
        if receipt:
            rpath = os.path.join(tmp, "receipt.json"); argv += ["--receipt-out", rpath]
        rc, out = _capture_main(argv)
        return rc, out, (rpath if rpath and os.path.exists(rpath) else None)
    finally:
        dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS.update(saved)


def _e2e_delete_missing_in_data_api_OV015():
    rc, out, _r = _run_case(_delete_docs("public.v"), _delete_consumer_overlays, extra_roots=[tcd._ROOT])
    return rc == 1 and "OV015" in out


def _e2e_delete_true_in_data_api_SP027():
    rc, out, _r = _run_case(_delete_docs("public.v"),
                            lambda cb: _delete_consumer_overlays(cb) + [_in_data_api_overlay(cb, True)], extra_roots=[tcd._ROOT])
    return rc == 1 and "SP027" in out


def _e2e_delete_false_noncovering_OV022():
    narrow = {"started_at": "2026-06-20T00:00:00Z", "ended_at": CENSUS_OBSERVED_AT}  # starts after S=06-05 -> not covering
    rc, out, _r = _run_case(_delete_docs("public.v"),
                            lambda cb: _delete_consumer_overlays(cb) + [_in_data_api_overlay(cb, False, window=narrow)], extra_roots=[tcd._ROOT])
    return rc == 1 and "OV022" in out


def _e2e_retain_no_overlay_OV018():
    rc, out, _r = _run_case(_retain_docs("public.v"), lambda cb: [])   # retain source relation has no contributor
    return rc == 1 and "OV018" in out


def _e2e_retain_green():
    rc, out, _r = _run_case(_retain_docs("public.v"),
                            lambda cb: [_in_data_api_overlay(cb, False), _consumer_overlay("static_repo", cb, "sha:s1")])
    return rc == 0


def _e2e_unaccepted_manifest_SP018_no_receipt():
    # The overlay loader must reach a CLEAN merge (full no_consumer resolution + in_data_api) so the
    # manifest's not-accepted status is caught by run()'s SP018 (a semantic-gate code), not masked by
    # an earlier OV015/OV018 loader reject.
    decisions, manifest, em = _harden_docs("public.v")
    manifest["status"] = "proposed"; manifest["technical_authority_approval"] = None   # not accepted -> SP018
    rc, out, receipt = _run_case((decisions, manifest, em),
                                 lambda cb: [_in_data_api_overlay(cb, False)] + _harden_consumer_overlays(cb), receipt=True)
    return rc == 1 and "SP018" in out and receipt is None   # no receipt is written on a RED gate


def _e2e_signed_runtime_na_overlay_OV015_no_receipt():
    # gate-correction: a validly-SIGNED runtime_logs overlay authored not_applicable must be rejected at
    # the overlay layer (OV015) for a resolved harden conclusion, and emit NO receipt.
    priv, pub = _ephemeral_keypair(); saved = _pin_signer(pub); oid = "public.v"
    try:
        tmp, cb, base = _write_harden_case(priv, pub, _zero_census([oid]))
        overlays = [_in_data_api_overlay(cb, False),
                    _consumer_overlay("static_repo", cb, "sha:s1"),
                    _consumer_overlay("runtime_logs", cb, "sha:r1", state="not_applicable",
                                      producing_repo_sha=None, producing_repo_sha_not_applicable_reason="runtime query"),
                    _consumer_overlay("external_clients", cb, "sha:e1"),
                    _consumer_overlay("operator_declaration", cb, "sha:o1", producing_repo_sha=None,
                                      producing_repo_sha_not_applicable_reason="operator", operator_identity="op-1", attestation_ref="att-1")]
        opts = []
        for i, o in enumerate(overlays):
            p = os.path.join(tmp, f"ov{i}.json"); ob, sig = _sign(o, priv); _wb(p, ob); _wb(p + ".sig", sig); opts += ["--overlay", p]
        rpath = os.path.join(tmp, "receipt.json")
        rc, out = _capture_main(base + opts + ["--receipt-out", rpath])
        return rc == 1 and "OV015" in out and not os.path.exists(rpath)
    finally:
        dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS.update(saved)


def _e2e_base_census_runtime_na_OV015_no_receipt():
    # gate-correction: runtime_logs already not_applicable in the BASE census (no overlay) is likewise
    # rejected at the overlay layer (OV015) for a resolved harden conclusion, with NO receipt.
    priv, pub = _ephemeral_keypair(); saved = _pin_signer(pub); oid = "public.v"
    try:
        census = _zero_census([oid])
        census["relations"][0]["consumer_evidence"]["runtime_logs"] = {"state": "not_applicable", "found_consumers": None, "ref": None, "detail": "base n/a"}
        tmp, cb, base = _write_harden_case(priv, pub, census)
        overlays = [_in_data_api_overlay(cb, False),
                    _consumer_overlay("static_repo", cb, "sha:s1"),
                    _consumer_overlay("external_clients", cb, "sha:e1"),
                    _consumer_overlay("operator_declaration", cb, "sha:o1", producing_repo_sha=None,
                                      producing_repo_sha_not_applicable_reason="operator", operator_identity="op-1", attestation_ref="att-1")]
        opts = []
        for i, o in enumerate(overlays):
            p = os.path.join(tmp, f"ov{i}.json"); ob, sig = _sign(o, priv); _wb(p, ob); _wb(p + ".sig", sig); opts += ["--overlay", p]
        rpath = os.path.join(tmp, "receipt.json")
        rc, out = _capture_main(base + opts + ["--receipt-out", rpath])
        return rc == 1 and "OV015" in out and not os.path.exists(rpath)
    finally:
        dt.TRUSTED_SIGNERS.clear(); dt.TRUSTED_SIGNERS.update(saved)


_CASES += [
    ("e2e_red_then_green", _e2e_red_then_green),
    ("e2e_signed_runtime_na_overlay_OV015_no_receipt", _e2e_signed_runtime_na_overlay_OV015_no_receipt),
    ("e2e_base_census_runtime_na_OV015_no_receipt", _e2e_base_census_runtime_na_OV015_no_receipt),
    ("e2e_ov021_via_main", _e2e_ov021_via_main),
    ("e2e_delete_missing_in_data_api_OV015", _e2e_delete_missing_in_data_api_OV015),
    ("e2e_delete_true_in_data_api_SP027", _e2e_delete_true_in_data_api_SP027),
    ("e2e_delete_false_noncovering_OV022", _e2e_delete_false_noncovering_OV022),
    ("e2e_retain_no_overlay_OV018", _e2e_retain_no_overlay_OV018),
    ("e2e_retain_green", _e2e_retain_green),
    ("e2e_unaccepted_manifest_SP018_no_receipt", _e2e_unaccepted_manifest_SP018_no_receipt),
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
    print("\n=== OVERLAY LOADER SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
