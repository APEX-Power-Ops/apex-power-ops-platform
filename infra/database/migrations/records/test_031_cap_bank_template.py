"""TDD - records Chip 2c: Capacitor Bank datasheet (NETA 7.20.1).

Slice-3 coverage backlog. Leaf 'cap_bank' already exists (Chip 2-shell). NETA 7.20.1 = 7 VM + 4
electrical = 11 items. R-A = neta_table (IR->100.1) + mfr (capacitance / discharge-R / bolted).
Capture = field + cover_attach.

RED until gen_cap_bank_template.py emits 031_cap_bank_template.sql. Run PER-CHIP.
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
CODE = "ats_cap_bank_v1"
SEC = "7.20.1"


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


@pytest.fixture(scope="module")
def conn():
    _psql("031_cap_bank_template_down.sql")
    _psql("031_cap_bank_template.sql")
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
    assert sec == SEC and leaf == "cap_bank", f"{sec}/{leaf}"


def test_coverage_invariant(conn):
    _, fs, _ = _schema(conn)
    covered = set()
    for s in fs["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = _required()
    assert not (required - covered), f"coverage gap: {sorted(required - covered)}"
    assert not ({r for r in covered if r.startswith(SEC + ".")} - required), "phantom"
    assert len(required) == 11, f"expected 11, got {len(required)}"


def test_structure_and_capture(conn):
    _, fs, _ = _schema(conn)
    keys = [s["key"] for s in fs["sections"]]
    for k in ("identification", "visual_mechanical", "insulation_resistance", "capacitance",
              "discharge_resistors", "attachments"):
        assert k in keys, f"missing section {k}"
    assert len(keys) == len(set(keys)), "duplicate keys"
    cap = fs.get("capture", {})
    assert cap.get("default") == "field" and "cover_attach" in cap.get("modes", [])


def test_ir_acceptance_is_neta_table(conn):
    _, fs, _ = _schema(conn)
    ir = next(s for s in fs["sections"] if s["key"] == "insulation_resistance")
    one_min = next(c for c in ir["table"]["columns"] if c["tag"] == "one_min_mohm")
    assert one_min.get("tolerance_source", {}).get("table") == "100.1"


def test_ascii_only(conn):
    _, fs, _ = _schema(conn)
    assert json.dumps(fs, ensure_ascii=False).isascii(), "field_schema must be ASCII-only"


def test_reversibility(conn):
    _psql("031_cap_bank_template_down.sql")
    with psycopg.connect(DSN) as c:
        assert c.execute("select 1 from records.form_templates where template_code=%s and is_current",
                         (CODE,)).fetchone() is None, "down must remove the template"
    _psql("031_cap_bank_template_down.sql")
    _psql("031_cap_bank_template.sql")
