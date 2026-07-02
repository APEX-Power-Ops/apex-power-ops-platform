"""TDD - Records Chip 2b: the Motor-Starter datasheets (NETA 7.16.1).

Two leaf-bound single-procedure sheets (the complete 7.16 procedures; the MCC leaves 7.16.2.x are
pure crossref -> deferred as asset-tree composition, not standalone sheets):
  - ats_lv_motor_starter_v1 -> motor_starter_lv; 7.16.1.1 (LV); 14 ATS (9 VM + 5 elec).
  - ats_mv_motor_starter_v1 -> motor_starter_mv; 7.16.1.2 (MV); 29 ATS (12 VM + 17 elec).

PowerDB-anchored to the RESA cover forms (31000 Motor Starter / 31300 MV Vacuum Motor Starter); NETA
stays the coverage authority. R-A: a starter has no integral trip curve -> tolerance_source.engine is
neta_table (IR -> Table 100.1) or mfr (motor-protection / dielectric per mfr data) - never tcc. No
starter instrument bridge wired -> capture = field + cover_attach (no instrument_import section).

Coverage invariant: per sheet, union of section neta_covers == all the procedure's ATS items.

RED until gen_motor_starter_template.py emits 019_motor_starter_templates.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_019_motor_starter_template.py
"""
import json
import os
import subprocess

import psycopg
import pytest

import _dbtest

HERE = os.path.dirname(os.path.abspath(__file__))
DSN = _dbtest.dsn()

LV_CODE, MV_CODE = "ats_lv_motor_starter_v1", "ats_mv_motor_starter_v1"
# (code, leaf, section, n_items, n_sections)
SHEETS = [
    (LV_CODE, "motor_starter_lv", "7.16.1.1", 14, 8),
    (MV_CODE, "motor_starter_mv", "7.16.1.2", 29, 12),
]

COMMON = {"nameplate", "visual_mechanical", "test_equipment", "comments_deficiencies", "attachments"}
EXPECTED_SECTIONS = {
    LV_CODE: COMMON | {"insulation_resistance", "protective_devices", "functional"},
    MV_CODE: COMMON | {"insulation_resistance", "vacuum_integrity", "dielectric_withstand",
                       "contact_resistance", "functional", "associated_devices", "auxiliary"},
}


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


def _apply():
    _psql("019_motor_starter_templates_down.sql")
    _psql("019_motor_starter_templates.sql")


@pytest.fixture(scope="module")
def conn():
    _apply()
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _schema(conn, code):
    row = conn.execute(
        "select field_schema from records.form_templates where template_code = %s and is_current",
        (code,)
    ).fetchone()
    assert row is not None, f"template {code} not found / not current"
    fs = row[0]
    return json.loads(fs) if isinstance(fs, str) else fs


def _sections(conn, code):
    return {s["key"]: s for s in _schema(conn, code)["sections"]}


def _controls(section):
    return list(section.get("fields", [])) + list(section.get("table", {}).get("columns", []))


def _required_neta_refs(conn, section):
    rows = conn.execute(
        "select ti.category, ti.item_number from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = %s and ti.standard = 'ats' "
        "and ti.category in ('visual_mechanical','electrical')", (section,)
    ).fetchall()
    return {f"{section}.{'A' if cat == 'visual_mechanical' else 'B'}.{num}" for cat, num in rows}


def _covered_refs(conn, code):
    covered = set()
    for s in _schema(conn, code)["sections"]:
        covered |= set(s.get("neta_covers", []))
    return covered


def _tolerance_sources(conn, code):
    out = []
    for s in _schema(conn, code)["sections"]:
        for c in _controls(s):
            if c.get("tolerance_source"):
                out.append(c["tolerance_source"])
    return out


def test_templates_bound(conn):
    for code, leaf, section, _, _ in SHEETS:
        row = conn.execute(
            "select t.form_type, t.neta_standard, t.neta_section, t.version, a.class_code "
            "from records.form_templates t "
            "left join records.asset_classes a on a.asset_class_id = t.asset_class_id "
            "where t.template_code = %s and t.is_current", (code,)
        ).fetchone()
        assert row is not None, f"{code} missing"
        form_type, std, sec, version, class_code = row
        assert form_type == "neta_datasheet" and std == "ats" and version == 1
        assert sec == section and class_code == leaf, f"{code} -> {class_code}/{sec}"


def test_schema_shape(conn):
    for code, _, _, _, _ in SHEETS:
        fs = _schema(conn, code)
        assert fs.get("version") == 1 and fs.get("family")
        assert isinstance(fs.get("selections"), list)
        assert isinstance(fs.get("sections"), list) and fs["sections"]


def test_sections_present(conn):
    for code, _, _, _, _ in SHEETS:
        assert set(_sections(conn, code)) == EXPECTED_SECTIONS[code], code


def test_section_count(conn):
    for code, _, _, _, n_sec in SHEETS:
        assert len(_schema(conn, code)["sections"]) == n_sec, code


def test_coverage_no_drops(conn):
    for code, _, section, n_items, _ in SHEETS:
        required = _required_neta_refs(conn, section)
        covered = _covered_refs(conn, code)
        assert required - covered == set(), f"{code} silent drops: {sorted(required - covered)}"
        assert len(required) == n_items, f"{code} expected {n_items}, got {len(required)}"


def test_no_phantom(conn):
    for code, _, section, _, _ in SHEETS:
        required = _required_neta_refs(conn, section)
        covered = _covered_refs(conn, code)
        phantom = {r for r in covered if r.startswith(section + ".")} - required
        assert not phantom, f"{code} phantom refs: {sorted(phantom)}"


def test_ra_engines(conn):
    for code, _, _, _, _ in SHEETS:
        engines = {s.get("engine") for s in _tolerance_sources(conn, code)}
        assert engines, f"{code} expected declared tolerance_source bindings"
        assert engines <= {"neta_table", "mfr"} and "tcc" not in engines, f"{code} bad engines {engines}"


def test_ra_mfr_slot(conn):
    # 7.16.1: motor-protection / dielectric tested to mfr published data -> an mfr basis exists.
    for code, _, _, _, _ in SHEETS:
        mfr = [s for s in _tolerance_sources(conn, code) if s.get("engine") == "mfr"]
        assert mfr, f"{code} must declare an mfr tolerance_source (motor protection / dielectric)"


def test_ir_neta_table_100_1(conn):
    # a starter has no trip curve: IR acceptance is NETA Table 100.1 (not IEEE 43 like rotating machinery).
    for code, _, _, _, _ in SHEETS:
        ir = _sections(conn, code)["insulation_resistance"]
        ts = [c.get("tolerance_source", {}) for c in _controls(ir) if c.get("tolerance_source")]
        assert any(t.get("engine") == "neta_table" and t.get("table") == "100.1" for t in ts), \
            f"{code} IR section must bind neta_table 100.1"


def test_no_prefilled_windows(conn):
    for code, _, _, _, _ in SHEETS:
        for s in _schema(conn, code)["sections"]:
            for c in _controls(s):
                if c.get("tolerance_source"):
                    assert "value" not in c, f"{code}.{c['tag']} must not pre-fill a window"


def test_capture_field_and_cover_only(conn):
    for code, _, _, _, _ in SHEETS:
        cap = _schema(conn, code).get("capture")
        assert isinstance(cap, dict), f"{code} missing capture block"
        modes = set(cap.get("modes", []))
        assert {"field", "cover_attach"} <= modes and "instrument_import" not in modes, f"{code} modes {modes}"
        assert cap.get("default") == "field"
        assert not [s for s in _schema(conn, code)["sections"] if s.get("capture_mode") == "instrument_import"]


def test_cover_attach_section(conn):
    for code, _, _, _, _ in SHEETS:
        att = _sections(conn, code)["attachments"]
        assert att.get("kind") == "attachment" and att.get("capture_mode") == "cover_attach"
        assert "attachment" in {f.get("value_kind") for f in att.get("fields", [])}
        assert not att.get("neta_covers")


def test_mv_only_vacuum_and_associated(conn):
    # the MV starter carries vacuum-integrity + contact/coil/fuse resistance + the xref associated-devices
    # group; the LV starter (no vacuum interrupter, fewer borrows) does not.
    mv, lv = set(_sections(conn, MV_CODE)), set(_sections(conn, LV_CODE))
    for k in ("vacuum_integrity", "contact_resistance", "associated_devices", "dielectric_withstand"):
        assert k in mv and k not in lv, k


def test_reversibility(conn):
    _psql("019_motor_starter_templates_down.sql")
    with psycopg.connect(DSN) as c:
        for code, _, _, _, _ in SHEETS:
            gone = c.execute(
                "select count(*) from records.form_templates where template_code = %s", (code,)
            ).fetchone()[0]
            assert gone == 0, f"down should remove {code}"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
