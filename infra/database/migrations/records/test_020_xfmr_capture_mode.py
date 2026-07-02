"""TDD - Records Chip 10a (Phase 1): make the transformer templates capture-mode-aware.

The xfmr datasheets (migration 012) predate the capture-mode contract (introduced at IT / 015), so they
have capture=NULL and no instrument_import sections. The PTM import (Chip 10a) needs declared targets:
this migration adds the `capture` block + marks the four PTM-fillable sections
(turns_ratio / winding_resistance / power_factor / excitation_current) `instrument_import` with an
`import {tool: ptm, profile}` hint. Non-PTM sections (nameplate, visual_mechanical, ...) are untouched.

RED until gen_020_xfmr_capture_mode.py emits 020_xfmr_capture_mode.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --no-project --directory infra/database/migrations/records --with "psycopg[binary]" --with pytest pytest test_020_xfmr_capture_mode.py
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
PTM_SECTIONS = {"turns_ratio", "winding_resistance", "power_factor", "excitation_current"}


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


@pytest.fixture(scope="module")
def conn():
    _psql("020_xfmr_capture_mode_down.sql")
    _psql("020_xfmr_capture_mode.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _schema(conn, code):
    fs = conn.execute(
        "select field_schema from records.form_templates where template_code = %s and is_current",
        (code,)
    ).fetchone()[0]
    return json.loads(fs) if isinstance(fs, str) else fs


def test_capture_block_present(conn):
    for code in CODES:
        cap = _schema(conn, code).get("capture")
        assert cap is not None, f"{code} missing capture block"
        assert set(cap.get("modes", [])) >= {"field", "instrument_import", "cover_attach"}, code
        assert cap.get("default") == "field", code


def test_ptm_sections_marked(conn):
    for code in CODES:
        secs = {s["key"]: s for s in _schema(conn, code)["sections"]}
        for k in PTM_SECTIONS:
            assert secs[k].get("capture_mode") == "instrument_import", f"{code}.{k} not marked"
            imp = secs[k].get("import")
            assert imp and imp.get("tool") == "ptm" and imp.get("profile"), f"{code}.{k} import hint"


def test_non_ptm_sections_untouched(conn):
    for code in CODES:
        secs = {s["key"]: s for s in _schema(conn, code)["sections"]}
        assert secs["nameplate"].get("capture_mode") != "instrument_import", code
        assert "import" not in secs["nameplate"], code


def test_section_set_unchanged(conn):
    # the wiring must not add/drop/reorder sections - only annotate the four.
    for code in CODES:
        keys = [s["key"] for s in _schema(conn, code)["sections"]]
        assert PTM_SECTIONS <= set(keys), code
        assert len(keys) == len(set(keys)), f"{code} duplicate section keys"


def test_reversibility(conn):
    _psql("020_xfmr_capture_mode_down.sql")
    with psycopg.connect(DSN) as c:
        for code in CODES:
            sch = _schema(c, code)
            assert sch.get("capture") is None, f"{code} down must restore capture=null"
            secs = {s["key"]: s for s in sch["sections"]}
            for k in PTM_SECTIONS:
                assert secs[k].get("capture_mode") is None and "import" not in secs[k], f"{code}.{k} down strip"
    _psql("020_xfmr_capture_mode_down.sql")
    _psql("020_xfmr_capture_mode.sql")
