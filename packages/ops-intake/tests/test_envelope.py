import hashlib
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


def test_create_run_persists_envelope_only(mini_workbook, clean_ops):
    dsn = clean_ops
    who = _person(dsn)
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


def test_second_active_upload_supersedes(mini_workbook, clean_ops):
    dsn = clean_ops
    who = _person(dsn)
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


def test_patch_bumps_version_and_revalidates(mini_workbook, clean_ops):
    dsn = clean_ops; who = _person(dsn)
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