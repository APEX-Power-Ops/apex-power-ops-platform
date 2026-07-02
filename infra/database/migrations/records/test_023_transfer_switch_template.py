"""TDD - records Chip 2c: Automatic Transfer Switch datasheet (NETA 7.22.3).

First of the slice-3 coverage-backlog families (the Prime catalog has an ATS datasheet; records did not).
The asset-class leaf 'ats' already exists (Chip 2-shell). NETA 7.22.3 = 11 VM + 8 electrical = 19 ATS
items; the field_schema must cover all of them (coverage invariant). Capture = field + cover_attach (no
instrument bridge / standard import format for ATS). NETA-derived; R-A = neta_table (IR -> 100.1) + mfr.

RED until gen_transfer_switch_template.py emits 023_transfer_switch_template.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --no-project --directory infra/database/migrations/records --with "psycopg[binary]" --with pytest pytest test_023_transfer_switch_template.py
"""
import json
import os
import subprocess

import psycopg
import pytest

import _dbtest

HERE = os.path.dirname(os.path.abspath(__file__))
DSN = _dbtest.dsn()
JSON = _dbtest.neta_json()
CODE = "ats_transfer_switch_v1"
SEC = "7.22.3"


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


@pytest.fixture(scope="module")
def conn():
    _psql("023_transfer_switch_template_down.sql")
    _psql("023_transfer_switch_template.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _schema(conn):
    row = conn.execute(
        "select neta_section, field_schema, "
        "(select class_code from records.asset_classes a where a.asset_class_id = t.asset_class_id) "
        "from records.form_templates t where template_code = %s and is_current", (CODE,)
    ).fetchone()
    assert row, f"{CODE} not found"
    sec, fs, leaf = row
    return sec, (json.loads(fs) if isinstance(fs, str) else fs), leaf


def _required():
    d = json.load(open(JSON, encoding="utf-8"))
    e = next(x for x in d["equipment"] if x.get("section") == SEC)
    ats = e.get("ats_data") or {}
    vm = ats.get("visual_mechanical") or []
    el = ats.get("electrical_tests") or []
    return ({f"{SEC}.A.{i + 1}" for i in range(len(vm))}
            | {f"{SEC}.B.{i + 1}" for i in range(len(el))})


def test_template_bound(conn):
    sec, _, leaf = _schema(conn)
    assert sec == SEC, f"neta_section {sec} != {SEC}"
    assert leaf == "ats", f"bound to {leaf}, expected leaf 'ats'"


def test_coverage_invariant(conn):
    _, fs, _ = _schema(conn)
    covered = set()
    for s in fs["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = _required()
    assert not (required - covered), f"coverage gap: {sorted(required - covered)}"
    phantom = {r for r in covered if r.startswith(SEC + ".")} - required
    assert not phantom, f"phantom refs: {sorted(phantom)}"
    assert len(required) == 19, f"expected 19 NETA items, got {len(required)}"


def test_structure_and_capture(conn):
    _, fs, _ = _schema(conn)
    keys = [s["key"] for s in fs["sections"]]
    for k in ("identification", "visual_mechanical", "insulation_resistance",
              "contact_resistance", "transfer_operation", "attachments"):
        assert k in keys, f"missing section {k}"
    assert len(keys) == len(set(keys)), "duplicate section keys"
    cap = fs.get("capture", {})
    assert cap.get("default") == "field" and "cover_attach" in cap.get("modes", []), "capture block"


def test_ascii_only(conn):
    _, fs, _ = _schema(conn)
    blob = json.dumps(fs, ensure_ascii=False)
    assert blob.isascii(), "field_schema must be ASCII-only (NETA trap)"


def test_reversibility(conn):
    _psql("023_transfer_switch_template_down.sql")
    with psycopg.connect(DSN) as c:
        row = c.execute("select 1 from records.form_templates where template_code = %s and is_current",
                        (CODE,)).fetchone()
        assert row is None, "down must remove the template"
    _psql("023_transfer_switch_template_down.sql")
    _psql("023_transfer_switch_template.sql")
