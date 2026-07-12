"""Schema + offline-registry tests for overlay.schema.json (Task 1).

Proves per-dimension shape enforcement and that remote/unseeded $ref resolution is IMPOSSIBLE
(mapped to a coded OverlayRegistryError, never an uncaught referencing.Unresolvable) and that a
calendar-invalid datetime is a coded reject via FormatChecker (not a traceback).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import disposition_overlay as ov  # noqa: E402

VALIDATOR = ov.load_overlay_contract().overlay_validator


def _base_overlay(dimension, source_type, value):
    return {
        "kind": "evidence_overlay", "overlay_version": "1",
        "dimension": dimension, "source_type": source_type,
        "authority": "test", "collection_method": "test", "source_locator": "test:x",
        "source_hash": None, "source_hash_not_applicable_reason": "live pull",
        "base_snapshot_sha256": "a" * 64,
        "disposition_schema_sha256": "b" * 64, "overlay_schema_sha256": "c" * 64,
        "project_ref": "fxoyniqnrlkxfligbxmg",
        "captured_at": "2026-07-14T18:03:00+00:00",
        "observation_window": {"started_at": "2026-07-01T00:00:00Z", "ended_at": "2026-07-10T00:00:00Z"},
        "producing_repo_sha": None, "producing_repo_sha_not_applicable_reason": "n/a",
        "assignments": [{"object_id": "public.v_scope_financials", "value": value}],
    }


def _errs(doc):
    return [e.message for e in VALIDATOR.iter_errors(doc)]


def _valid_bool_overlay_accepted():
    doc = _base_overlay("in_data_api_exposed_schema", "platform_config", {"state": "observed", "value": False})
    doc["producing_repo_sha"] = "d" * 40  # required for this dimension
    return _errs(doc) == []


def _valid_consumer_overlay_accepted():
    doc = _base_overlay("consumer_evidence.static_repo", "repository_scan",
                        {"state": "observed", "found_consumers": 0, "ref": "scan:2026-07-14"})
    doc["source_hash"] = "e" * 64
    doc["producing_repo_sha"] = "d" * 40
    return _errs(doc) == []


def _source_type_mismatch_rejected():
    doc = _base_overlay("consumer_evidence.static_repo", "advisor_api",  # wrong source_type
                        {"state": "observed", "found_consumers": 0, "ref": "scan:x"})
    return _errs(doc) != []


def _wrong_value_shape_rejected():
    # a consumer_evidence_dim value under a bool dimension must fail
    doc = _base_overlay("in_data_api_exposed_schema", "platform_config",
                        {"state": "observed", "found_consumers": 0, "ref": "x"})
    return _errs(doc) != []


def _operator_declaration_requires_provenance():
    doc = _base_overlay("consumer_evidence.operator_declaration", "operator_declaration",
                        {"state": "observed", "found_consumers": 3, "ref": "att:2026-07-14"})
    # missing operator_identity / attestation_ref -> schema rejects
    return _errs(doc) != []


def _calendar_invalid_datetime_coded():
    doc = _base_overlay("consumer_evidence.static_repo", "repository_scan",
                        {"state": "observed", "found_consumers": 0, "ref": "scan:x"})
    doc["source_hash"] = "e" * 64
    doc["producing_repo_sha"] = "d" * 40
    doc["captured_at"] = "2026-13-40T99:99:99Z"  # pattern-plausible, calendar-invalid
    # FormatChecker must flag it as a coded schema error, NOT raise
    return _errs(doc) != []


def _unseeded_ref_raises_unresolvable_offline():
    # A registry with NO retrieve callback must FAIL CLOSED (raise referencing.Unresolvable) rather
    # than fetch when a schema $ref points at an UNSEEDED $id — proving remote resolution is impossible
    # and no network is attempted. (Task 3 additionally proves validate_overlay maps this to a coded OV008.)
    from jsonschema import Draft202012Validator
    from referencing import Registry
    from referencing.exceptions import Unresolvable
    bogus = Draft202012Validator({"$ref": "https://unseeded.example/nope.json#/$defs/x"}, registry=Registry())
    try:
        list(bogus.iter_errors({"any": 1}))
        return False  # must not silently pass
    except Unresolvable:
        return True   # fail-closed, offline, no fetch
    except Exception:
        return False  # any other exception (incl. a network error) is a failure


def _contract_hashes_match_on_disk_bytes():
    # The contract's schema SHA-256s must equal the on-disk bytes (read-once binding, audit F4).
    c = ov.load_overlay_contract()
    return (c.disp_sha256 == ov._sha256_hex(open(ov.DISPOSITION_SCHEMA_PATH, "rb").read())
            and c.overlay_sha256 == ov._sha256_hex(open(ov.OVERLAY_SCHEMA_PATH, "rb").read()))


def _malformed_schema_build_error_coded():
    # A jsonschema SchemaError raised by check_schema() inside load_overlay_contract() must map to a
    # coded OverlayRegistryError, never escape as an uncaught exception (fail-closed read-once contract;
    # round-6 F1 hardening — the except tuple must cover SchemaError, not just OSError/ValueError/KeyError).
    import tempfile
    orig = ov.OVERLAY_SCHEMA_PATH
    fd, tmp = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write('{"type": 123}')  # invalid: "type" must be string/array -> check_schema raises SchemaError
        ov.OVERLAY_SCHEMA_PATH = tmp
        try:
            ov.load_overlay_contract()
            return False  # must have raised
        except ov.OverlayRegistryError:
            return True
        except Exception:
            return False  # any uncaught/other-typed exception is a fail-closed violation
    finally:
        ov.OVERLAY_SCHEMA_PATH = orig
        os.unlink(tmp)


def _undeterminable_spec_build_error_coded():
    # A referencing CannotDetermineSpecification raised by Resource.from_contents() (a schema with no
    # determinable $schema dialect) must ALSO map to a coded OverlayRegistryError, not escape
    # (round-6 F1 hardening — referencing.exceptions.ReferencingError does not exist on the pinned
    # version, so the except tuple names CannotDetermineSpecification explicitly).
    import tempfile
    orig = ov.OVERLAY_SCHEMA_PATH
    fd, tmp = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write('{"$id": "https://overlay.local/undeterminable", "type": "object"}')  # valid schema, no $schema
        ov.OVERLAY_SCHEMA_PATH = tmp
        try:
            ov.load_overlay_contract()
            return False
        except ov.OverlayRegistryError:
            return True
        except Exception:
            return False
    finally:
        ov.OVERLAY_SCHEMA_PATH = orig
        os.unlink(tmp)


if __name__ == "__main__":
    ok = True
    for name, fn in [
        ("valid_bool_overlay_accepted", _valid_bool_overlay_accepted),
        ("valid_consumer_overlay_accepted", _valid_consumer_overlay_accepted),
        ("source_type_mismatch_rejected", _source_type_mismatch_rejected),
        ("wrong_value_shape_rejected", _wrong_value_shape_rejected),
        ("operator_declaration_requires_provenance", _operator_declaration_requires_provenance),
        ("calendar_invalid_datetime_coded", _calendar_invalid_datetime_coded),
        ("unseeded_ref_raises_unresolvable_offline", _unseeded_ref_raises_unresolvable_offline),
        ("contract_hashes_match_on_disk_bytes", _contract_hashes_match_on_disk_bytes),
        ("malformed_schema_build_error_coded", _malformed_schema_build_error_coded),
        ("undeterminable_spec_build_error_coded", _undeterminable_spec_build_error_coded),
    ]:
        try:
            r = bool(fn())
        except Exception as exc:  # noqa: BLE001
            r = False; name = f"{name} (EXC {exc})"
        ok = ok and r
        print(f"  {'ok  ' if r else 'FAIL'}: {name}")
    print("\n=== OVERLAY SCHEMA SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
