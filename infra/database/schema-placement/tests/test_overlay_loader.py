"""Loader tests for disposition_overlay.py (Tasks 2-8). Offline; throwaway fixture keys only.

Runner: uv run --project . --locked python tests/test_overlay_loader.py
"""
import copy
import hashlib
import json
import os
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
