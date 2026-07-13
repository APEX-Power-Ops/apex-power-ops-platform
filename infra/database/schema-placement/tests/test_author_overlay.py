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
