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


_CORE_TAIL = ('"observation_window": {"started_at": "2026-07-11T00:00:00+00:00", '
             '"ended_at": "2026-07-12T00:00:00+00:00"}, "authority": "a", "collection_method": "m"')


def _input_duplicate_dimension_key_AO000():
    # Phase-4.1 item 2 (RED before the strict-parse fix): a duplicate top-level "dimension" key
    # is currently silently last-wins -- json.dump cannot express this, so the fixture is raw text.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        raw = ('{"dimension": "advisor_findings", "dimension": "in_data_api_exposed_schema", '
              '"assignments": [{"object_id": "public.t1", "value": {}}], ' + _CORE_TAIL + "}")
        open(p, "w").write(raw)
        return _err_code(ao.load_input_core, p) == "AO000"


def _input_duplicate_assignments_key_AO000():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        raw = ('{"dimension": "advisor_findings", '
              '"assignments": [{"object_id": "public.t1", "value": {}}], '
              '"assignments": [{"object_id": "public.t2", "value": {}}], ' + _CORE_TAIL + "}")
        open(p, "w").write(raw)
        return _err_code(ao.load_input_core, p) == "AO000"


def _input_duplicate_key_nested_any_depth_AO000():
    # "any depth": object_pairs_hook fires for every JSON object in the tree, not just the top
    # level -- prove it catches a duplicate INSIDE observation_window too.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        raw = ('{"dimension": "advisor_findings", '
              '"assignments": [{"object_id": "public.t1", "value": {}}], '
              '"observation_window": {"started_at": "2026-07-11T00:00:00+00:00", '
              '"started_at": "2026-07-11T01:00:00+00:00", "ended_at": "2026-07-12T00:00:00+00:00"}, '
              '"authority": "a", "collection_method": "m"}')
        open(p, "w").write(raw)
        return _err_code(ao.load_input_core, p) == "AO000"


def _input_nonfinite_value_AO000():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        raw = ('{"dimension": "advisor_findings", '
              '"assignments": [{"object_id": "public.t1", "value": NaN}], ' + _CORE_TAIL + "}")
        open(p, "w").write(raw)
        return _err_code(ao.load_input_core, p) == "AO000"


def _input_unknown_property_AO002():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        core = fx.overlay_core("advisor_findings", [{"object_id": "public.t1", "value": {}}])
        core["note"] = "not part of the contract"
        json.dump(core, open(p, "w"))
        return _err_code(ao.load_input_core, p) == "AO002"


def _input_optional_fields_still_allowed():
    # regression guard: operator_identity/attestation_ref are the two OPTIONAL allowed keys --
    # the unknown-property gate must not reject them.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        core = fx.overlay_core("advisor_findings", [{"object_id": "public.t1", "value": {}}])
        core["operator_identity"] = "jason"
        core["attestation_ref"] = "sig:abc"
        json.dump(core, open(p, "w"))
        loaded = ao.load_input_core(p)
        return loaded["operator_identity"] == "jason" and loaded["attestation_ref"] == "sig:abc"


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


def _custody_absolute_path_AO004():
    return _err_code(ao.read_source, None, "no artifact", "/etc/passwd") == "AO004"


def _custody_windows_drive_AO004():
    return _err_code(ao.read_source, None, "no artifact", "C:\\evidence\\out.log") == "AO004"


def _custody_relative_path_AO004():
    return _err_code(ao.read_source, None, "no artifact", "relative/path/to/file.log") == "AO004"


def _custody_traversal_AO004():
    return _err_code(ao.read_source, None, "no artifact", "vault:../secrets") == "AO004"


def _custody_backslash_AO004():
    return _err_code(ao.read_source, None, "no artifact", "vault:cus\\tody") == "AO004"


def _custody_whitespace_AO004():
    return _err_code(ao.read_source, None, "no artifact", "vault:custody ref") == "AO004"


def _custody_empty_string_AO004():
    return _err_code(ao.read_source, None, "no artifact", "   ") == "AO004"


def _custody_valid_uri_passes():
    data, reason, custody, ext = ao.read_source(None, "no artifact", "vault:padloc/item/xyz")
    return data is None and custody == "vault:padloc/item/xyz"


_CASES += [
    ("input_unreadable_AO000", _input_unreadable_AO000),
    ("input_not_object_AO002", _input_not_object_AO002),
    ("input_missing_field_AO002", _input_missing_field_AO002),
    ("input_bad_dimension_AO002", _input_bad_dimension_AO002),
    ("input_empty_assignments_AO002", _input_empty_assignments_AO002),
    ("input_valid_core_loads", _input_valid_core_loads),
    ("input_duplicate_dimension_key_AO000", _input_duplicate_dimension_key_AO000),
    ("input_duplicate_assignments_key_AO000", _input_duplicate_assignments_key_AO000),
    ("input_duplicate_key_nested_any_depth_AO000", _input_duplicate_key_nested_any_depth_AO000),
    ("input_nonfinite_value_AO000", _input_nonfinite_value_AO000),
    ("input_unknown_property_AO002", _input_unknown_property_AO002),
    ("input_optional_fields_still_allowed", _input_optional_fields_still_allowed),
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
    ("custody_absolute_path_AO004", _custody_absolute_path_AO004),
    ("custody_windows_drive_AO004", _custody_windows_drive_AO004),
    ("custody_relative_path_AO004", _custody_relative_path_AO004),
    ("custody_traversal_AO004", _custody_traversal_AO004),
    ("custody_backslash_AO004", _custody_backslash_AO004),
    ("custody_whitespace_AO004", _custody_whitespace_AO004),
    ("custody_empty_string_AO004", _custody_empty_string_AO004),
    ("custody_valid_uri_passes", _custody_valid_uri_passes),
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

import contextlib  # noqa: E402
import io  # noqa: E402

import disposition_provenance as dp  # noqa: E402

GATE_SHA = "f" * 40


@contextlib.contextmanager
def _provenance(head=GATE_SHA, clean=True):
    orig_head, orig_clean = dp.git_head_sha, dp.git_worktree_clean
    dp.git_head_sha = lambda _d: head
    dp.git_worktree_clean = lambda _d: clean
    try:
        yield
    finally:
        dp.git_head_sha, dp.git_worktree_clean = orig_head, orig_clean


def _noclobber_refuses_existing():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.json")
        open(p, "wb").write(b"old")
        try:
            ao._write_bytes_atomic_noclobber(p, b"new")
            return False
        except FileExistsError:
            return open(p, "rb").read() == b"old" and not [f for f in os.listdir(d) if f.startswith(".")]


def _publish_set_partial_failure_AO008():
    # sidecar target pre-exists: source publishes, sidecar refuses -> AO008; overlay NEVER written;
    # no temp residue anywhere (the finally-unlink).
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "source", "r.source.txt")
        sig = os.path.join(d, "o.json.sig")
        ovl = os.path.join(d, "o.json")
        open(sig, "wb").write(b"squatter")
        code = _err_code(ao.publish_set, [(src, b"S"), (sig, b"G"), (ovl, b"O")])
        residue = [f for f in os.listdir(d) if f.startswith(".")]
        return (code == "AO008" and os.path.exists(src) and not os.path.exists(ovl)
                and open(sig, "rb").read() == b"squatter" and not residue)


def _canonical_names_counter():
    with tempfile.TemporaryDirectory() as d:
        from datetime import datetime, timezone
        dt_ = datetime(2026, 7, 12, 6, 0, 0, tzinfo=timezone.utc)
        first = ao.canonical_names("consumer_evidence.static_repo", "ab" * 32, dt_, d, ".txt")
        base = "overlay-consumer_evidence_static_repo-abababababab-20260712T060000Z"
        if os.path.basename(first["overlay"]) != base + ".json":
            return False
        if first["locator"] != "evidence/source/" + base + ".source.txt":
            return False
        open(first["overlay"], "wb").write(b"x")  # occupy -> next call must pick -01
        second = ao.canonical_names("consumer_evidence.static_repo", "ab" * 32, dt_, d, ".txt")
        return os.path.basename(second["overlay"]) == base + "-01.json"


def _main_env(d, *, dimension="consumer_evidence.static_repo", with_source=True):
    """Build a full green argv + env for main(); returns (argv, cleanup_ctx, signer_pub_fp)."""
    priv, pub = fx.keypair()
    keys_dir = fx.write_keys_dir(d, pub)
    census = fx.acceptance_census(["public.t1"])
    cpath, cs_path, _cb, _sb = fx.write_signed(d, "census-prod-fixture.json", census, priv)
    core = fx.overlay_core(dimension, [{"object_id": "public.t1",
                                        "value": {"state": "observed", "found_consumers": 0, "ref": "scan:t"}}])
    ipath = os.path.join(d, "core.json")
    json.dump(core, open(ipath, "w"))
    out_dir = os.path.join(d, "out")
    os.makedirs(out_dir, exist_ok=True)
    exp = fx.acceptance_expects(census)
    argv = ["--census", cpath, "--census-sig", cs_path, "--key-id", fx.KEY_ID, "--keys-dir", keys_dir,
            "--input", ipath, "--expect-gate-repo-sha", GATE_SHA,
            "--expect-project-ref", exp["project_ref"], "--expect-database", exp["database"],
            "--expect-schemas", ",".join(exp["schemas"]), "--expect-census-repo-sha", exp["census_repo_sha"],
            "--require-role-markers", ",".join(exp["role_markers"]),
            "--expect-query-bundle-sha256", exp["query_bundle_sha256"],
            "--out-dir", out_dir, "--signing-key-env", "TEST_SIGNING_KEY_XYZ"]
    if with_source:
        spath = os.path.join(d, "scan-output.txt")
        open(spath, "wb").write(b"public.t1: 0 refs\n")
        argv += ["--source-file", spath]
    os.environ["TEST_SIGNING_KEY_XYZ"] = fx.priv_pem(priv)
    return argv, pub, out_dir


def _run_main(argv, pub):
    err = io.StringIO()
    with fx.trusted(fx.KEY_ID, fx.spki_fp(pub)), contextlib.redirect_stderr(err):
        rc = ao.main(argv)
    return rc, err.getvalue()


def _main_green_publishes_triple():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, out_dir = _main_env(d)
        try:
            with _provenance():
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        if rc != 0:
            print("    stderr:", err)
            return False
        names = sorted(os.listdir(out_dir))
        overlays = [n for n in names if n.endswith(".json")]
        sigs = [n for n in names if n.endswith(".json.sig")]
        sources = os.listdir(os.path.join(out_dir, "source"))
        if not (len(overlays) == 1 and len(sigs) == 1 and len(sources) == 1):
            return False
        doc = json.load(open(os.path.join(out_dir, overlays[0])))
        return (doc["producing_repo_sha"] == GATE_SHA
                and doc["source_locator"] == "evidence/source/" + sources[0]
                and doc["source_hash"] is not None)


def _main_dirty_worktree_AO010_before_key():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _main_env(d)
        os.environ.pop("TEST_SIGNING_KEY_XYZ", None)  # key ABSENT: AO010 must fire first anyway
        with _provenance(clean=False):
            rc, err = _run_main(argv, pub)
        return rc == 2 and "AO010" in err and "AO007" not in err


def _main_wrong_head_AO010():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _main_env(d)
        try:
            with _provenance(head="0" * 40):
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        return rc == 2 and "AO010" in err


def _main_unpinned_key_id_AO013():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _main_env(d)
        argv[argv.index("--key-id") + 1] = "not-a-pinned-signer"
        try:
            with _provenance():
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        return rc == 2 and "AO013" in err


def _main_bad_assembly_refuses_to_sign_AO005():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, out_dir = _main_env(d)
        ipath = argv[argv.index("--input") + 1]
        core = json.load(open(ipath))
        core["observation_window"] = {"started_at": "2026-07-12T00:00:00+00:00",
                                      "ended_at": "2026-07-11T00:00:00+00:00"}  # OV009
        json.dump(core, open(ipath, "w"))
        try:
            with _provenance():
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        published = os.listdir(out_dir)
        published_src = os.listdir(os.path.join(out_dir, "source")) if os.path.isdir(os.path.join(out_dir, "source")) else []
        return rc == 2 and "OV009" in err and "AO005" in err and published == [] and published_src == []


def _main_value_silent_key_never_echoed():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _main_env(d)
        os.environ["TEST_SIGNING_KEY_XYZ"] = "-----BEGIN PRIVATE KEY-----\nGARBAGE\n-----END PRIVATE KEY-----"
        try:
            with _provenance():
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        return rc == 2 and "AO007" in err and "GARBAGE" not in err


_CASES += [
    ("noclobber_refuses_existing", _noclobber_refuses_existing),
    ("publish_set_partial_failure_AO008", _publish_set_partial_failure_AO008),
    ("canonical_names_counter", _canonical_names_counter),
    ("main_green_publishes_triple", _main_green_publishes_triple),
    ("main_dirty_worktree_AO010_before_key", _main_dirty_worktree_AO010_before_key),
    ("main_wrong_head_AO010", _main_wrong_head_AO010),
    ("main_unpinned_key_id_AO013", _main_unpinned_key_id_AO013),
    ("main_bad_assembly_refuses_to_sign_AO005", _main_bad_assembly_refuses_to_sign_AO005),
    ("main_value_silent_key_never_echoed", _main_value_silent_key_never_echoed),
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
