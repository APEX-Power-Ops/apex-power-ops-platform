"""TDD - Records reconcile slice 1 / D-R1: add the Doble raw-reading columns to power_factor.

Reconciliation against the Prime 56900 TWO-WINDING TRANSFORMER form (gold-standard Form_Controls.csv)
found our power_factor section captures only pf_pct/capacitance/temp - it cannot hold the raw Doble
readings (test kV, charging mA, watts) or the temperature-corrected PF that a field PF test records and
that a DTAX/PTM import carries. This migration adds test_kv / current_ma / watts / pf_corrected_pct to
the power_factor table on BOTH xfmr templates. Additive (no NETA-coverage change); capture-mode (020)
preserved (the read-live-snapshot mechanism re-emits the 012+020 state + these columns).

RED until gen_021_xfmr_pf_readings.py emits 021_xfmr_pf_readings.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --no-project --directory infra/database/migrations/records --with "psycopg[binary]" --with pytest pytest test_021_xfmr_pf_readings.py
"""
import json
import os
import subprocess

import psycopg
import pytest

import _dbtest

HERE = os.path.dirname(os.path.abspath(__file__))
DSN = _dbtest.dsn()
CODES = ["ats_liquid_xfmr_v1", "ats_dry_xfmr_v1"]
# new raw-reading columns -> expected unit
NEW_COLS = {"test_kv": "kV", "current_ma": "mA", "watts": "W", "pf_corrected_pct": "pct"}
BASE_COLS = {"pf_pct", "capacitance", "temp"}


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


@pytest.fixture(scope="module")
def conn():
    _psql("021_xfmr_pf_readings_down.sql")
    _psql("021_xfmr_pf_readings.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _pf(conn, code):
    fs = conn.execute(
        "select field_schema from records.form_templates where template_code = %s and is_current",
        (code,)
    ).fetchone()[0]
    fs = json.loads(fs) if isinstance(fs, str) else fs
    pf = next(s for s in fs["sections"] if s["key"] == "power_factor")
    return {c["tag"]: c for c in pf["table"]["columns"]}, fs


def test_raw_readings_added(conn):
    for code in CODES:
        cols, _ = _pf(conn, code)
        for tag, unit in NEW_COLS.items():
            assert tag in cols, f"{code}.power_factor missing {tag}"
            assert cols[tag].get("unit") == unit, f"{code}.{tag} unit={cols[tag].get('unit')} != {unit}"
            assert cols[tag].get("value_kind") == "numeric", f"{code}.{tag} not numeric"
        assert cols["pf_corrected_pct"].get("data_source") == "calc", f"{code} corrected PF must be calc"


def test_existing_pf_columns_intact(conn):
    for code in CODES:
        cols, _ = _pf(conn, code)
        assert BASE_COLS <= set(cols), f"{code} lost a base pf column"
        # pf_pct keeps its mfr tolerance_source (additive change must not touch it)
        assert cols["pf_pct"].get("tolerance_source", {}).get("engine") == "mfr", code


def test_capture_mode_preserved(conn):
    # the read-live-snapshot must NOT clobber the 020 capture-mode wiring.
    for code in CODES:
        _, fs = _pf(conn, code)
        assert fs.get("capture", {}).get("default") == "field", f"{code} capture block lost"
        pf = next(s for s in fs["sections"] if s["key"] == "power_factor")
        assert pf.get("capture_mode") == "instrument_import", f"{code} power_factor capture_mode lost"
        assert pf.get("import", {}).get("tool") == "ptm", f"{code} power_factor import hint lost"


def test_section_set_unchanged(conn):
    for code in CODES:
        _, fs = _pf(conn, code)
        keys = [s["key"] for s in fs["sections"]]
        assert len(keys) == len(set(keys)), f"{code} duplicate section keys"
        assert "power_factor" in keys, code


def test_reversibility(conn):
    _psql("021_xfmr_pf_readings_down.sql")
    with psycopg.connect(DSN) as c:
        for code in CODES:
            cols, fs = _pf(c, code)
            assert not (set(NEW_COLS) & set(cols)), f"{code} down must strip the raw-reading columns"
            assert BASE_COLS <= set(cols), f"{code} down must keep the base pf columns"
            # the 020 capture wiring survives a 021 down (surgical, power_factor-columns only)
            assert fs.get("capture", {}).get("default") == "field", f"{code} down must not touch capture"
    _psql("021_xfmr_pf_readings_down.sql")
    _psql("021_xfmr_pf_readings.sql")
