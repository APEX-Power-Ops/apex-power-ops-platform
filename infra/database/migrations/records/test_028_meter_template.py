"""TDD - records Chip 2c: Metering Device datasheet (NETA 7.11.2).

Slice-3 coverage backlog. Leaf 'meter' already exists (Chip 2-shell). NETA 7.11.2 (Microprocessor-
Based) = 10 VM + 3 electrical = 13 items. R-A = mfr (metering accuracy vs spec; no IR section).
Capture = field + cover_attach.

RED until gen_meter_template.py emits 028_meter_template.sql. Run PER-CHIP.
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
CODE = "ats_meter_v1"
SEC = "7.11.2"


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


@pytest.fixture(scope="module")
def conn():
    _psql("028_meter_template_down.sql")
    _psql("028_meter_template.sql")
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
    assert sec == SEC and leaf == "meter", f"{sec}/{leaf}"


def test_coverage_invariant(conn):
    _, fs, _ = _schema(conn)
    covered = set()
    for s in fs["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = _required()
    assert not (required - covered), f"coverage gap: {sorted(required - covered)}"
    assert not ({r for r in covered if r.startswith(SEC + ".")} - required), "phantom"
    assert len(required) == 13, f"expected 13, got {len(required)}"


def test_structure_and_capture(conn):
    _, fs, _ = _schema(conn)
    keys = [s["key"] for s in fs["sections"]]
    for k in ("identification", "visual_mechanical", "settings", "input_verification",
              "energized_check", "attachments"):
        assert k in keys, f"missing section {k}"
    assert len(keys) == len(set(keys)), "duplicate keys"
    cap = fs.get("capture", {})
    assert cap.get("default") == "field" and "cover_attach" in cap.get("modes", [])


def test_accuracy_acceptance_is_mfr(conn):
    """Metering accuracy resolves to mfr spec - never tcc/neta_table for a meter."""
    _, fs, _ = _schema(conn)
    iv = next(s for s in fs["sections"] if s["key"] == "input_verification")
    meas = next(c for c in iv["table"]["columns"] if c["tag"] == "measured")
    assert meas.get("tolerance_source", {}).get("engine") == "mfr"


def test_ascii_only(conn):
    _, fs, _ = _schema(conn)
    assert json.dumps(fs, ensure_ascii=False).isascii(), "field_schema must be ASCII-only"


def test_reversibility(conn):
    _psql("028_meter_template_down.sql")
    with psycopg.connect(DSN) as c:
        assert c.execute("select 1 from records.form_templates where template_code=%s and is_current",
                         (CODE,)).fetchone() is None, "down must remove the template"
    _psql("028_meter_template_down.sql")
    _psql("028_meter_template.sql")
