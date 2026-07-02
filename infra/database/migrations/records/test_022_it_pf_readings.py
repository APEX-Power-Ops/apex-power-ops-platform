"""TDD - Records reconcile slice 2 / D-R1 generalized: complete the IT PF/DF sections.

The IT templates (015) were built capture-aware, so their PF/DF sections already hold test_kv / pf_pct /
watts (+ capacitance on CT/CVT). But they lack the charging current (mA) and the temperature-corrected PF
that a field Doble PF/DF test records and that the DTAX TX_PFDF import carries - the same Doble field set
characterized from Prime 56900 in slice 1. This migration adds current_ma + pf_corrected_pct to all three
IT PF/DF sections (ct.power_factor, vt.power_factor, cvt.capacitance_pf), plus cap_pf to vt.power_factor
(CT/CVT already capture capacitance; VT did not). Additive; import marks preserved.

RED until gen_022_it_pf_readings.py emits 022_it_pf_readings.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --no-project --directory infra/database/migrations/records --with "psycopg[binary]" --with pytest pytest test_022_it_pf_readings.py
"""
import json
import os
import subprocess

import psycopg
import pytest

import _dbtest

HERE = os.path.dirname(os.path.abspath(__file__))
DSN = _dbtest.dsn()
# code -> (PF/DF section key, expects cap_pf added)
PF = {"ats_ct_v1": ("power_factor", False), "ats_vt_v1": ("power_factor", True),
      "ats_cvt_v1": ("capacitance_pf", False)}
UNIVERSAL = {"current_ma": "mA", "pf_corrected_pct": "pct"}  # added to all three


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


@pytest.fixture(scope="module")
def conn():
    _psql("022_it_pf_readings_down.sql")
    _psql("022_it_pf_readings.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _entries(conn, code, key):
    """Return {tag: entry} for a section regardless of fields- vs table-kind, plus (section, schema)."""
    fs = conn.execute(
        "select field_schema from records.form_templates where template_code = %s and is_current",
        (code,)
    ).fetchone()[0]
    fs = json.loads(fs) if isinstance(fs, str) else fs
    s = next(x for x in fs["sections"] if x["key"] == key)
    lst = s.get("fields") or s.get("table", {}).get("columns") or []
    return {e["tag"]: e for e in lst}, s, fs


def test_universal_readings_added(conn):
    for code, (key, _) in PF.items():
        ent, _, _ = _entries(conn, code, key)
        for tag, unit in UNIVERSAL.items():
            assert tag in ent, f"{code}.{key} missing {tag}"
            assert ent[tag].get("unit") == unit, f"{code}.{tag} unit={ent[tag].get('unit')} != {unit}"
            assert ent[tag].get("value_kind") == "numeric", f"{code}.{tag} not numeric"
        assert ent["pf_corrected_pct"].get("data_source") == "calc", f"{code} corrected PF must be calc"


def test_vt_capacitance_added(conn):
    ent, _, _ = _entries(conn, "ats_vt_v1", "power_factor")
    assert "cap_pf" in ent, "vt.power_factor still missing capacitance"
    assert ent["cap_pf"].get("unit") == "pF", "vt cap_pf unit"


def test_existing_fields_intact(conn):
    base = {"ats_ct_v1": {"test_kv", "pf_pct", "watts", "cap_pf"},
            "ats_vt_v1": {"test_kv", "pf_pct", "watts"},
            "ats_cvt_v1": {"test_kv", "measured_cap_pf", "pf_pct", "watts"}}
    for code, (key, _) in PF.items():
        ent, _, _ = _entries(conn, code, key)
        assert base[code] <= set(ent), f"{code}.{key} lost an existing field"


def test_import_marks_preserved(conn):
    # the read-live-snapshot must not clobber the 015 capture-mode wiring.
    for code in PF:
        _, _, fs = _entries(conn, code, PF[code][0])
        assert fs.get("capture", {}).get("default") == "field", f"{code} capture block lost"
    _, s_vt, _ = _entries(conn, "ats_vt_v1", "power_factor")
    assert s_vt.get("import", {}).get("tool") == "dtax", "vt.power_factor dtax import hint lost"
    _, s_cvt, _ = _entries(conn, "ats_cvt_v1", "capacitance_pf")
    assert s_cvt.get("import", {}).get("tool") == "dtax", "cvt.capacitance_pf dtax import hint lost"
    _, s_exc, _ = _entries(conn, "ats_ct_v1", "excitation")
    assert s_exc.get("import", {}).get("tool") == "ct_analyzer", "ct.excitation ct_analyzer hint lost"


def test_reversibility(conn):
    _psql("022_it_pf_readings_down.sql")
    with psycopg.connect(DSN) as c:
        for code, (key, _) in PF.items():
            ent, _, fs = _entries(c, code, key)
            assert not (set(UNIVERSAL) & set(ent)), f"{code}.{key} down must strip current_ma/pf_corrected_pct"
            assert fs.get("capture", {}).get("default") == "field", f"{code} down must not touch capture"
        ent_vt, _, _ = _entries(c, "ats_vt_v1", "power_factor")
        assert "cap_pf" not in ent_vt, "down must strip the cap_pf added to VT"
        # CT keeps its NATIVE cap_pf (the down must not over-strip)
        ent_ct, _, _ = _entries(c, "ats_ct_v1", "power_factor")
        assert "cap_pf" in ent_ct, "down must keep CT's native cap_pf"
    _psql("022_it_pf_readings_down.sql")
    _psql("022_it_pf_readings.sql")
