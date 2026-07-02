import hashlib
import json
import psycopg
from ops_intake.envelope import create_run, get_run


def _bytes(mini_workbook):
    return mini_workbook.read_bytes()


def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(
            "insert into ops.persons (display_name) values (%s) returning person_id",
            ("PM",),
        ).fetchone()[0]


def test_create_run_persists_envelope_only(mini_workbook, clean_ops, admin_dsn):
    dsn = clean_ops
    who = _person(admin_dsn)
    out = create_run(
        dsn,
        uploaded_by=who,
        filename="mini.xlsm",
        raw_bytes=_bytes(mini_workbook),
        content_type="xlsm",
    )
    assert out["status"] == "parsed" and out["conflict_kind"] == "none"
    assert out["source_format"] == "decomposed_scope_sheet"
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.intake_runs").fetchone()[0] == 1
        assert c.execute("select count(*) from ops.intake_source_files").fetchone()[0] == 1
        for t in ("projects", "scopes", "tasks", "apparatus", "scope_quote", "scope_quote_line"):
            assert c.execute(
                "select count(*) from ops.{}".format(t)
            ).fetchone()[0] == 0, t
        (sha,) = c.execute("select sha256 from ops.intake_source_files").fetchone()
        assert sha == hashlib.sha256(_bytes(mini_workbook)).hexdigest()


def test_second_active_upload_supersedes(mini_workbook, clean_ops, admin_dsn):
    dsn = clean_ops
    who = _person(admin_dsn)
    r1 = create_run(
        dsn,
        uploaded_by=who,
        filename="m.xlsm",
        raw_bytes=_bytes(mini_workbook),
        content_type="xlsm",
    )
    r2 = create_run(
        dsn,
        uploaded_by=who,
        filename="m.xlsm",
        raw_bytes=_bytes(mini_workbook),
        content_type="xlsm",
    )
    with psycopg.connect(dsn) as c:
        assert (
            c.execute(
                "select status from ops.intake_runs where id=%s", (r1["run_id"],)
            ).fetchone()[0]
            == "superseded"
        )
        assert (
            c.execute(
                "select status from ops.intake_runs where id=%s", (r2["run_id"],)
            ).fetchone()[0]
            == "parsed"
        )


def test_dsn_guard_blocks_non_ops_test():
    import pytest
    from conftest import _require_ops_test

    with pytest.raises(AssertionError):
        _require_ops_test(
            "host=127.0.0.1 port=5432 dbname=ops_dev user=postgres sslmode=disable"
        )


# ---------------------------------------------------------------------------
# Task 9 tests
# ---------------------------------------------------------------------------

import pytest
from dataclasses import asdict
from ops_intake.extract import extract_workbook
from ops_intake.envelope import (create_run, patch_review,
                                 _assert_no_cross_scope_move, _assert_review_within_allowlist)


def test_patch_bumps_version_and_revalidates(mini_workbook, clean_ops, admin_dsn):
    dsn = clean_ops; who = _person(admin_dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    rp = r["review_payload"]; rp["scopes"][0]["lines"][0]["hrs_per_unit"] = 3.0
    out = patch_review(dsn, r["run_id"], review_payload=rp)
    assert out["review_payload_version"] == 2


def test_real_payload_lines_carry_line_uid(mini_workbook):
    p = asdict(extract_workbook(mini_workbook))
    assert all(l.get("line_uid") for s in p["scopes"] for l in s["lines"])


def test_cross_scope_move_rejected():
    canon = {"scopes": [{"scope_name": "A", "lines": [{"line_uid": "A:row1"}]},
                        {"scope_name": "B", "lines": []}]}
    moved = {"scopes": [{"scope_name": "A", "lines": []},
                        {"scope_name": "B", "lines": [{"line_uid": "A:row1"}]}]}
    with pytest.raises(ValueError):
        _assert_no_cross_scope_move(canon, moved)


def test_within_scope_regroup_ok():
    canon = {"scopes": [{"scope_name": "A", "lines": [{"line_uid": "A:row1", "section": "old"}]}]}
    same  = {"scopes": [{"scope_name": "A", "lines": [{"line_uid": "A:row1", "section": "NEW TASK"}]}]}
    _assert_no_cross_scope_move(canon, same)


def _canon():
    return {"project": {"project_number": "P1"},
            "scopes": [{"scope_name": "A",
                        "quote": {"onsite_labor": 1000, "offsite_labor": 0, "travel": 0, "outside_services": 0,
                                  "unit_multiplier": 1, "pct_adjust": 1, "total_quoted_hours": 7},
                        "lines": [{"line_uid": "A:row1", "qty": 1, "apparatus_type": "X", "line_number": 1,
                                   "test_standard": "ATS", "hrs_per_unit": 2.0, "section": "old"},
                                  {"line_uid": "A:row2", "qty": 5, "apparatus_type": "Y", "line_number": 2,
                                   "test_standard": "ATS", "hrs_per_unit": 1.0, "section": "old"}]}]}


def test_allowlist_blocks_qty_and_dollar_tamper():
    bad = _canon(); bad["scopes"][0]["lines"][0]["qty"] = 99
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), bad)
    bad2 = _canon(); bad2["scopes"][0]["quote"]["onsite_labor"] = 5000
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), bad2)


def test_allowlist_blocks_multiplier_and_j3_tamper():
    for field in ("unit_multiplier", "pct_adjust", "total_quoted_hours"):
        bad = _canon(); bad["scopes"][0]["quote"][field] = 9
        with pytest.raises(ValueError):
            _assert_review_within_allowlist(_canon(), bad)


def test_allowlist_blocks_same_scope_content_swap():
    swap = _canon(); a, b = swap["scopes"][0]["lines"]
    a["qty"], b["qty"] = b["qty"], a["qty"]
    a["apparatus_type"], b["apparatus_type"] = b["apparatus_type"], a["apparatus_type"]
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), swap)


def test_allowlist_blocks_added_or_duplicated_line():
    add = _canon(); add["scopes"][0]["lines"].append({"line_uid": "A:row3", "qty": 1})
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), add)
    dup = _canon(); dup["scopes"][0]["lines"].append({**_canon()["scopes"][0]["lines"][0]})
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), dup)


def test_allowlist_allows_section_and_hours_edit():
    ok = _canon(); ok["scopes"][0]["lines"][0]["section"] = "NEW"; ok["scopes"][0]["lines"][0]["hrs_per_unit"] = 3.5
    _assert_review_within_allowlist(_canon(), ok)


def test_allowlist_blocks_identity_and_structural_tamper():
    bad_pn = _canon(); bad_pn["project"]["project_number"] = "P9"
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), bad_pn)
    for field, val in [("apparatus_type", "Z"), ("test_standard", "MTS"), ("line_number", 99)]:
        bad = _canon(); bad["scopes"][0]["lines"][0][field] = val
        with pytest.raises(ValueError):
            _assert_review_within_allowlist(_canon(), bad)
    deleted = _canon(); deleted["scopes"][0]["lines"].pop()
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), deleted)


def test_get_run_returns_only_current_version_findings(mini_workbook, clean_ops, admin_dsn):
    """get_run must return ONLY current-version findings; a stale prior-version blocker (one the PM
    resolved in a later revision) must NOT keep the UI Approve button disabled (operator defect I2)."""
    dsn = clean_ops
    who = _person(admin_dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm",
                   raw_bytes=_bytes(mini_workbook), content_type="xlsm")
    rid = r["run_id"]
    # Inject a STALE v1 blocking finding directly (simulating a blocker resolved by a later patch).
    # Writer holds INSERT on intake_validation_findings (load.py writes findings) - stays on dsn.
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(
            "insert into ops.intake_validation_findings "
            "(run_id, payload_version, severity, code, ok, message) "
            "values (%s, 1, 'blocking', 'stale_v1', false, 'old blocker')",
            (rid,),
        )
    # A valid (identity) edit bumps the run to review_payload_version 2 and writes fresh v2 findings.
    patch_review(dsn, rid, review_payload=r["review_payload"])
    out = get_run(dsn, rid)
    assert out["review_payload_version"] == 2
    # The stale v1 blocker must NOT be returned (get_run filters to the current version).
    assert all(f["code"] != "stale_v1" for f in out["findings"]), out["findings"]


def test_create_run_json_intake(clean_ops, admin_dsn):
    """JSON upload (DataverseExport shape) creates a GOVERNED envelope, envelope-only; a malformed
    JSON yields a rejected envelope rather than a 500 (operator I3 -- JSON must be allowed)."""
    dsn = clean_ops
    who = _person(admin_dsn)
    doc = {
        "project": {"name": "JSON Proj", "projectNumber": "JSON-001"},
        "client": {"name": "Acme"},
        "site": {"city": "Mesa"},
        "scopes": [{
            "name": "S1", "scopeType": "ATS", "totalHours": "10", "multiplier": "1",
            "financials": {"onsiteLaborTotal": "1000", "offsiteLaborTotal": "0",
                           "travelTotal": "0", "outsideServicesTotal": "0"},
            "apparatus": [
                {"row": "8", "section": "SES-1", "quantity": "2",
                 "equipmentType": "Switchgear", "hoursPerUnit": "2.5"},
            ],
        }],
        "summary": {"grandTotal": "1000"},
    }
    raw = json.dumps(doc).encode("utf-8")
    out = create_run(dsn, uploaded_by=who, filename="export.json", raw_bytes=raw, content_type="json")
    assert out["status"] == "parsed"
    assert out["source_format"] == "decomposed_scope_sheet"
    with psycopg.connect(dsn) as c:
        (pn,) = c.execute(
            "select project_number from ops.intake_runs where id=%s", (out["run_id"],)
        ).fetchone()
        assert pn == "JSON-001"  # project identity comes from the JSON, not hard-coded
        for t in ("projects", "scopes", "tasks", "apparatus", "scope_quote", "scope_quote_line"):
            assert c.execute(f"select count(*) from ops.{t}").fetchone()[0] == 0, t  # envelope-only

    # Malformed JSON -> a GOVERNED rejected envelope (a persisted run + blocking finding), not a crash.
    bad = create_run(dsn, uploaded_by=who, filename="bad.json",
                     raw_bytes=b"{not valid json", content_type="json")
    assert bad["status"] == "rejected"
    assert any(f["code"] == "parse_error" and f["severity"] == "blocking" for f in bad["findings"])


def test_allowlist_error_message_is_value_free():
    """A guard rejection must NOT leak the quote dollar values in its message -- finance redaction
    applies to guard errors too (the API returns a generic 400, and the message itself is value-free).
    (Codex finding 1)"""
    import pytest
    bad = _canon()
    bad["scopes"][0]["quote"]["onsite_labor"] = 99999
    with pytest.raises(ValueError) as ei:
        _assert_review_within_allowlist(_canon(), bad)
    msg = str(ei.value)
    assert "$" not in msg
    assert "99999" not in msg and "1000" not in msg  # neither the review nor the canonical dollar value


def test_patch_review_on_inactive_run_raises_run_not_active(mini_workbook, clean_ops, admin_dsn):
    """patch_review on an approved (inactive) run raises RunNotActive (API maps to 409), re-checked
    under the run-row FOR UPDATE lock -- never a silent revert of an approved run. (Codex finding 2)"""
    import pytest
    from ops_intake.envelope import RunNotActive
    from ops_intake.approve import approve_run
    dsn = clean_ops
    who = _person(admin_dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm",
                   raw_bytes=_bytes(mini_workbook), content_type="xlsm")
    approve_run(dsn, r["run_id"], approved_by=who)  # -> status 'approved' (inactive)
    with pytest.raises(RunNotActive):
        patch_review(dsn, r["run_id"], review_payload=r["review_payload"])


def test_guard_messages_are_dollar_free_even_with_dollar_named_scope():
    """Guard errors must be value-free even when a scope is NAMED with a '$' (and the line_uid it
    prefixes inherits it). Finance redaction covers guard error messages across the WHOLE class of
    guards, not just the quote/line field guards. (Codex 2nd-round finding)"""
    import pytest
    SN = "Switchgear $1234"

    def _canon_dollar():
        return {"project": {"project_number": "P1"},
                "scopes": [{"scope_name": SN,
                            "quote": {"onsite_labor": 1000, "total_quoted_hours": 7},
                            "lines": [{"line_uid": SN + ":row1", "qty": 1, "apparatus_type": "X",
                                       "test_standard": "ATS", "line_number": 1, "section": "old"}]}]}

    # quote-field guard
    q = _canon_dollar(); q["scopes"][0]["quote"]["onsite_labor"] = 5000
    # pinned line-field guard
    ln = _canon_dollar(); ln["scopes"][0]["lines"][0]["qty"] = 99
    # cross-scope guard (move the $-named line's uid under a different scope)
    cs_c = {"scopes": [{"scope_name": SN, "lines": [{"line_uid": SN + ":row1"}]},
                       {"scope_name": "B", "lines": []}]}
    cs_r = {"scopes": [{"scope_name": SN, "lines": []},
                       {"scope_name": "B", "lines": [{"line_uid": SN + ":row1"}]}]}

    for canon, review, fn in [
        (_canon_dollar(), q, _assert_review_within_allowlist),
        (_canon_dollar(), ln, _assert_review_within_allowlist),
        (cs_c, cs_r, _assert_no_cross_scope_move),
    ]:
        with pytest.raises(ValueError) as ei:
            fn(canon, review)
        assert "$" not in str(ei.value), str(ei.value)  # no dollar char in ANY guard message