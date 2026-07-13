"""Offline suite for author_overlay.py (overlay author/sign CLI). Script __main__ runner."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _overlay_pub_fixtures as fx  # noqa: E402
import author_overlay as ao  # noqa: E402

_CASES = []


def _err_code(fn, *a, **k):
    try:
        fn(*a, **k)
        return None
    except ao.AuthorError as exc:
        return exc.code


def _input_unreadable_AO000():
    return _err_code(ao.load_input_core, os.path.join(tempfile.gettempdir(), "no-such-dir-xyz", "core.json")) == "AO000"


def _input_not_object_AO002():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        open(p, "w").write("[1,2]")
        return _err_code(ao.load_input_core, p) == "AO002"


def _input_missing_field_AO002():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        json.dump({"dimension": "advisor_findings"}, open(p, "w"))
        return _err_code(ao.load_input_core, p) == "AO002"


def _input_bad_dimension_AO002():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        core = fx.overlay_core("advisor_findings", [{"object_id": "public.t1", "value": {}}])
        core["dimension"] = "not_a_dimension"
        json.dump(core, open(p, "w"))
        return _err_code(ao.load_input_core, p) == "AO002"


def _input_empty_assignments_AO002():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        core = fx.overlay_core("advisor_findings", [{"object_id": "public.t1", "value": {}}])
        core["assignments"] = []
        json.dump(core, open(p, "w"))
        return _err_code(ao.load_input_core, p) == "AO002"


def _input_valid_core_loads():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        core = fx.overlay_core("advisor_findings", [{"object_id": "public.t1", "value": {}}])
        json.dump(core, open(p, "w"))
        return ao.load_input_core(p)["dimension"] == "advisor_findings"


SHA = "c" * 40


def _producing_required_uses_gate_sha():
    return ao.compute_producing("consumer_evidence.static_repo", SHA, None) == (SHA, None)


def _producing_required_rejects_reason_AO002():
    return _err_code(ao.compute_producing, "in_data_api_exposed_schema", SHA, "why") == "AO002"


def _producing_forbidden_needs_reason_AO002():
    return _err_code(ao.compute_producing, "advisor_findings", SHA, None) == "AO002"


def _producing_forbidden_null_plus_reason():
    return ao.compute_producing("consumer_evidence.runtime_logs", SHA, "logs are not a repo") == (None, "logs are not a repo")


def _producing_conditional_both_shapes():
    a = ao.compute_producing("consumer_evidence.external_clients", SHA, None) == (SHA, None)
    b = ao.compute_producing("consumer_evidence.external_clients", SHA, "no repo inventory") == (None, "no repo inventory")
    return a and b


def _source_both_supplied_AO004():
    return _err_code(ao.read_source, "/tmp/x", "reason", "custody:ref") == "AO004"


def _source_neither_supplied_AO004():
    return _err_code(ao.read_source, None, None, None) == "AO004"


def _source_custody_without_reason_AO004():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "s.txt")
        open(p, "w").write("x")
        return _err_code(ao.read_source, p, None, "custody:ref") == "AO004"


def _source_reason_without_custody_AO004():
    return _err_code(ao.read_source, None, "api snapshot", None) == "AO004"


def _source_unreadable_AO009_value_silent():
    try:
        ao.read_source(os.path.join(tempfile.gettempdir(), "no-such-dir-xyz", "evidence.log"), None, None)
        return False
    except ao.AuthorError as exc:
        return exc.code == "AO009" and "FileNotFoundError" in exc.message


def _source_file_read_and_ext():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "advisor.json")
        open(p, "wb").write(b'{"advisor": []}')
        data, reason, custody, ext = ao.read_source(p, None, None)
        return data == b'{"advisor": []}' and reason is None and custody is None and ext == ".json"


def _source_na_path():
    data, reason, custody, ext = ao.read_source(None, "no artifact for this source", "vault:custody/2026-07")
    return data is None and reason == "no artifact for this source" and custody == "vault:custody/2026-07" and ext is None


_CASES += [
    ("input_unreadable_AO000", _input_unreadable_AO000),
    ("input_not_object_AO002", _input_not_object_AO002),
    ("input_missing_field_AO002", _input_missing_field_AO002),
    ("input_bad_dimension_AO002", _input_bad_dimension_AO002),
    ("input_empty_assignments_AO002", _input_empty_assignments_AO002),
    ("input_valid_core_loads", _input_valid_core_loads),
    ("producing_required_uses_gate_sha", _producing_required_uses_gate_sha),
    ("producing_required_rejects_reason_AO002", _producing_required_rejects_reason_AO002),
    ("producing_forbidden_needs_reason_AO002", _producing_forbidden_needs_reason_AO002),
    ("producing_forbidden_null_plus_reason", _producing_forbidden_null_plus_reason),
    ("producing_conditional_both_shapes", _producing_conditional_both_shapes),
    ("source_both_supplied_AO004", _source_both_supplied_AO004),
    ("source_neither_supplied_AO004", _source_neither_supplied_AO004),
    ("source_custody_without_reason_AO004", _source_custody_without_reason_AO004),
    ("source_reason_without_custody_AO004", _source_reason_without_custody_AO004),
    ("source_unreadable_AO009_value_silent", _source_unreadable_AO009_value_silent),
    ("source_file_read_and_ext", _source_file_read_and_ext),
    ("source_na_path", _source_na_path),
]

import hashlib  # noqa: E402

import disposition_overlay as dov  # noqa: E402

NOW = dov._parse_iso("2026-07-12T12:00:00+00:00")


def _assembled(dimension="in_data_api_exposed_schema", value=None, window=None,
               captured="2026-07-12T06:00:00+00:00", oids=("public.t1", "public.t2"),
               assignments=None):
    census = fx.acceptance_census(list(oids))
    census_bytes = fx.canon(census)
    census_sha = hashlib.sha256(census_bytes).hexdigest()
    contract = dov.load_overlay_contract()
    core = fx.overlay_core(
        dimension,
        assignments or [{"object_id": "public.t1", "value": value or {"state": "observed", "value": False}}],
        window=window)
    doc = ao.assemble_overlay(core, census=census, census_sha256=census_sha, contract=contract,
                              producing=("d" * 40, None), source_hash="e" * 64,
                              source_hash_reason=None, source_locator="evidence/source/x.source.json",
                              captured_at_iso=captured)
    return ao._canon(doc), census, census_sha, contract


def _validate(message, census, census_sha, contract):
    return ao.validate_assembled(message, census=census, census_bytes_sha=census_sha,
                                 contract=contract, expect_project_ref=fx.PROJECT_REF, now=NOW)


def _assembled_clean_validates():
    m, c, s, k = _assembled()
    return _validate(m, c, s, k) == []


def _bad_window_yields_OV009():
    m, c, s, k = _assembled(window={"started_at": "2026-07-12T00:00:00+00:00",
                                    "ended_at": "2026-07-11T00:00:00+00:00"})
    return any(d[0] == "OV009" for d in _validate(m, c, s, k))


def _future_captured_yields_OV010():
    m, c, s, k = _assembled(captured="2027-01-01T00:00:00+00:00")
    return any(d[0] == "OV010" for d in _validate(m, c, s, k))


def _unknown_object_yields_OV005():
    m, c, s, k = _assembled(oids=("public.t1",),
                            assignments=[{"object_id": "public.nope",
                                          "value": {"state": "observed", "value": False}}])
    return any(d[0] == "OV005" for d in _validate(m, c, s, k))


def _intra_duplicate_yields_OV007():
    a = {"object_id": "public.t1", "value": {"state": "observed", "value": False}}
    m, c, s, k = _assembled(assignments=[a, dict(a)])
    return any(d[0] == "OV007" for d in _validate(m, c, s, k))


def _wrong_value_shape_yields_OV008_only():
    # advisor_findings requires observed_advisor_array; an observed_bool must FAIL schema and
    # SHORT-CIRCUIT (no binding/target diags on a schema-invalid doc).
    m, c, s, k = _assembled(dimension="advisor_findings", value={"state": "observed", "value": True})
    # producing: advisor is FORBIDDEN -- rebuild with null+reason so ONLY the value shape is wrong.
    census = fx.acceptance_census(["public.t1"])
    census_bytes = fx.canon(census); census_sha = hashlib.sha256(census_bytes).hexdigest()
    contract = dov.load_overlay_contract()
    core = fx.overlay_core("advisor_findings",
                           [{"object_id": "public.t1", "value": {"state": "observed", "value": True}}])
    doc = ao.assemble_overlay(core, census=census, census_sha256=census_sha, contract=contract,
                              producing=(None, "advisor API snapshot"),
                              source_hash="e" * 64, source_hash_reason=None,
                              source_locator="evidence/source/x.source.json",
                              captured_at_iso="2026-07-12T06:00:00+00:00")
    diags = _validate(ao._canon(doc), census, census_sha, contract)
    return diags and all(d[0] == "OV008" for d in diags)


def _na_reason_fields_assemble_green():
    census = fx.acceptance_census(["public.t1"])
    census_bytes = fx.canon(census); census_sha = hashlib.sha256(census_bytes).hexdigest()
    contract = dov.load_overlay_contract()
    core = fx.overlay_core("advisor_findings",
                           [{"object_id": "public.t1", "value": {"state": "observed", "value": ["lint:ok"]}}])
    doc = ao.assemble_overlay(core, census=census, census_sha256=census_sha, contract=contract,
                              producing=(None, "advisor API snapshot, not a repo"),
                              source_hash=None, source_hash_reason="no committed artifact",
                              source_locator="vault:custody/2026-07",
                              captured_at_iso="2026-07-12T06:00:00+00:00")
    ok_fields = (doc["producing_repo_sha"] is None
                 and doc["producing_repo_sha_not_applicable_reason"] == "advisor API snapshot, not a repo"
                 and doc["source_hash"] is None
                 and doc["source_hash_not_applicable_reason"] == "no committed artifact")
    return ok_fields and _validate(ao._canon(doc), census, census_sha, contract) == []


_CASES += [
    ("assembled_clean_validates", _assembled_clean_validates),
    ("bad_window_yields_OV009", _bad_window_yields_OV009),
    ("future_captured_yields_OV010", _future_captured_yields_OV010),
    ("unknown_object_yields_OV005", _unknown_object_yields_OV005),
    ("intra_duplicate_yields_OV007", _intra_duplicate_yields_OV007),
    ("wrong_value_shape_yields_OV008_only", _wrong_value_shape_yields_OV008_only),
    ("na_reason_fields_assemble_green", _na_reason_fields_assemble_green),
]

import disposition_signing as ds  # noqa: E402
import disposition_trust as dt  # noqa: E402


def _signer_and_census(tmpdir, priv=None, pub=None):
    priv2, pub2 = fx.keypair()
    priv, pub = priv or priv2, pub or pub2
    keys_dir = fx.write_keys_dir(tmpdir, pub)
    with fx.trusted(fx.KEY_ID, fx.spki_fp(pub)):
        signer, reason = dt.resolve_pinned_key(keys_dir, fx.KEY_ID)
    assert signer is not None, reason
    census = fx.acceptance_census(["public.t1"])
    census_bytes = fx.canon(census)
    sig_bytes = fx.sidecar_bytes_for(census_bytes, priv)
    return signer, census, census_bytes, sig_bytes, priv


def _census_accepts_green():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, sb, _ = _signer_and_census(d)
        got = ao.accept_census(cb, sb, signer=signer, expects=fx.acceptance_expects(census))
        return got["project_ref"] == fx.PROJECT_REF


def _tampered_census_AO001():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, sb, _ = _signer_and_census(d)
        bad = cb[:-2] + b" }"
        return _err_code(ao.accept_census, bad, sb, signer=signer,
                         expects=fx.acceptance_expects(census)) == "AO001"


def _foreign_signed_census_AO001():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, _sb, _ = _signer_and_census(d)
        foreign_priv, _fp = fx.keypair()
        foreign_sig = fx.sidecar_bytes_for(cb, foreign_priv)
        return _err_code(ao.accept_census, cb, foreign_sig, signer=signer,
                         expects=fx.acceptance_expects(census)) == "AO001"


def _project_mismatch_AO003():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, sb, _ = _signer_and_census(d)
        expects = fx.acceptance_expects(census)
        expects["project_ref"] = "otherproject"
        return _err_code(ao.accept_census, cb, sb, signer=signer, expects=expects) == "AO003"


def _out_of_scope_census_AO011():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, sb, _ = _signer_and_census(d)
        expects = fx.acceptance_expects(census)
        expects["schemas"] = ["public", "extra_schema"]  # CN005 inside check_census
        return _err_code(ao.accept_census, cb, sb, signer=signer, expects=expects) == "AO011"


def _key_env_unset_AO007():
    os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
    with tempfile.TemporaryDirectory() as d:
        signer, *_ = _signer_and_census(d)
        return _err_code(ao.load_signing_key, "TEST_SIGNING_KEY_XYZ", signer) == "AO007"


def _key_invalid_pem_AO007_value_silent():
    os.environ["TEST_SIGNING_KEY_XYZ"] = "not-a-pem"
    try:
        with tempfile.TemporaryDirectory() as d:
            signer, *_ = _signer_and_census(d)
            try:
                ao.load_signing_key("TEST_SIGNING_KEY_XYZ", signer)
                return False
            except ao.AuthorError as exc:
                return exc.code == "AO007" and "not-a-pem" not in str(exc)
    finally:
        os.environ.pop("TEST_SIGNING_KEY_XYZ", None)


def _key_wrong_signer_AO007():
    wrong_priv, _ = fx.keypair()  # valid Ed25519 key, NOT the pinned signer
    os.environ["TEST_SIGNING_KEY_XYZ"] = fx.priv_pem(wrong_priv)
    try:
        with tempfile.TemporaryDirectory() as d:
            signer, *_ = _signer_and_census(d)
            try:
                ao.load_signing_key("TEST_SIGNING_KEY_XYZ", signer)
                return False
            except ao.AuthorError as exc:
                return exc.code == "AO007" and "wrong signer" in exc.message
    finally:
        os.environ.pop("TEST_SIGNING_KEY_XYZ", None)


def _key_parity_green_and_sidecar_verifies():
    with tempfile.TemporaryDirectory() as d:
        signer, _census, cb, _sb, priv = _signer_and_census(d)
        os.environ["TEST_SIGNING_KEY_XYZ"] = fx.priv_pem(priv)
        try:
            key = ao.load_signing_key("TEST_SIGNING_KEY_XYZ", signer)
            sidecar = ao.build_and_check_sidecar(b"message-bytes", key, signer)
            ok, _ = ds.verify_sidecar_bytes_with_key(b"message-bytes", sidecar, signer.public_key)
            return ok
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)


def _sidecar_inmemory_failure_AO012():
    # Matrix row "in-memory sidecar fails to verify": force the verify step to report failure
    # (a broken/mismatched signer path) and prove the author raises AO012 BEFORE any publish.
    with tempfile.TemporaryDirectory() as d:
        signer, _census, _cb, _sb, priv = _signer_and_census(d)
        orig = ds.verify_sidecar_bytes_with_key
        ds.verify_sidecar_bytes_with_key = lambda *_a, **_k: (False, "forced failure (test)")
        try:
            code = _err_code(ao.build_and_check_sidecar, b"message-bytes", priv, signer)
        finally:
            ds.verify_sidecar_bytes_with_key = orig
        return code == "AO012"


_CASES += [
    ("census_accepts_green", _census_accepts_green),
    ("tampered_census_AO001", _tampered_census_AO001),
    ("foreign_signed_census_AO001", _foreign_signed_census_AO001),
    ("project_mismatch_AO003", _project_mismatch_AO003),
    ("out_of_scope_census_AO011", _out_of_scope_census_AO011),
    ("key_env_unset_AO007", _key_env_unset_AO007),
    ("key_invalid_pem_AO007_value_silent", _key_invalid_pem_AO007_value_silent),
    ("key_wrong_signer_AO007", _key_wrong_signer_AO007),
    ("key_parity_green_and_sidecar_verifies", _key_parity_green_and_sidecar_verifies),
    ("sidecar_inmemory_failure_AO012", _sidecar_inmemory_failure_AO012),
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
    print("\n=== AUTHOR OVERLAY SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
