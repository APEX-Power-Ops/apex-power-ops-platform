"""TDD - Records Chip 2b: the Rotating-Machinery datasheets (NETA 7.15).

Three leaf-bound single-procedure sheets (clean recipe, one leaf per procedure; the largest family):
  - ats_induction_motor_v1    -> rm_induction;   7.15.1 (AC induction);   27 ATS (11 VM + 16 elec).
  - ats_synchronous_machine_v1-> rm_synchronous; 7.15.2 (synchronous);    37 ATS (11 VM + 26 elec).
  - ats_dc_machine_v1         -> rm_dc;          7.15.3 (DC machines);    20 ATS (10 VM + 10 elec).

NOT PowerDB-anchored (no motor form in the corpus) -> NETA-derived. R-A: rotating machinery tests to
IEEE 43 (IR/PI) / NEMA MG 1 (hipot) / mfr data, not a NETA acceptance table -> `mfr` only (torque ->
Table 100.12 stays a VM acceptance basis). Never tcc. Capture = field + cover_attach (no motor bridge;
the emerging DTAX winding-resistance work is not wired here).

Coverage invariant: per sheet, union of section neta_covers == all the procedure's ATS items.

RED until gen_motor_template.py emits 018_motor_templates.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_018_motor_template.py
"""
import json
import os
import subprocess

import psycopg
import pytest

import _dbtest

HERE = os.path.dirname(os.path.abspath(__file__))
DSN = _dbtest.dsn()

IND_CODE, SYN_CODE, DC_CODE = "ats_induction_motor_v1", "ats_synchronous_machine_v1", "ats_dc_machine_v1"
# (code, leaf, section, n_items, n_sections)
SHEETS = [
    (IND_CODE, "rm_induction", "7.15.1", 27, 14),
    (SYN_CODE, "rm_synchronous", "7.15.2", 37, 15),
    (DC_CODE, "rm_dc", "7.15.3", 20, 11),
]

COMMON = {"nameplate", "visual_mechanical", "test_equipment", "comments_deficiencies", "attachments"}
EXPECTED_SECTIONS = {
    IND_CODE: COMMON | {"bolted_resistance", "insulation_resistance", "dielectric_withstand",
                        "winding_resistance", "power_factor", "surge_comparison",
                        "protective_devices", "auxiliary", "running_tests"},
    SYN_CODE: COMMON | {"bolted_resistance", "insulation_resistance", "dielectric_withstand",
                        "winding_resistance", "power_factor", "surge_comparison", "field_excitation",
                        "protective_devices", "auxiliary", "running_tests"},
    DC_CODE: COMMON | {"bolted_resistance", "insulation_resistance", "dielectric_withstand",
                       "field_excitation", "running_tests", "protective_devices"},
}


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


def _apply():
    _psql("018_motor_templates_down.sql")
    _psql("018_motor_templates.sql")


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
    # rotating machinery: IR/PI per IEEE 43 -> mfr basis (no NETA IR table for motors).
    for code, _, _, _, _ in SHEETS:
        mfr = [s for s in _tolerance_sources(conn, code) if s.get("engine") == "mfr"]
        assert mfr, f"{code} must declare an mfr tolerance_source (IR per IEEE 43)"


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


def test_insulation_resistance_ieee43(conn):
    # every motor sheet has an IR section that is the mfr/IEEE-43 acceptance slot.
    for code, _, _, _, _ in SHEETS:
        ir = _sections(conn, code)["insulation_resistance"]
        engines = {c.get("tolerance_source", {}).get("engine") for c in _controls(ir)}
        assert "mfr" in engines, f"{code} IR section must carry the mfr (IEEE 43) tolerance_source"


def test_synchronous_field_excitation(conn):
    # the synchronous + DC machines carry the field/excitation battery; induction does not.
    assert "field_excitation" in set(_sections(conn, SYN_CODE))
    assert "field_excitation" in set(_sections(conn, DC_CODE))
    assert "field_excitation" not in set(_sections(conn, IND_CODE))


def test_reversibility(conn):
    _psql("018_motor_templates_down.sql")
    with psycopg.connect(DSN) as c:
        for code, _, _, _, _ in SHEETS:
            gone = c.execute(
                "select count(*) from records.form_templates where template_code = %s", (code,)
            ).fetchone()[0]
            assert gone == 0, f"down should remove {code}"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
