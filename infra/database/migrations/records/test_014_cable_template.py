"""TDD - Records Chip 2b: the cable datasheets (LV + MV/HV).

Two leaf-bound single-procedure sheets (the clean recipe, like the breakers):
  - ats_lv_cable_v1   -> cable_lv;  NETA 7.3.2 (LV, 600 V max); 11 ATS.
  - ats_mvhv_cable_v1 -> cable_mv;  NETA 7.3.3 (MV/HV); 18 ATS - adds the shielded-cable
    HV battery (shield continuity, TDR, jacket integrity, dielectric withstand, tan-delta, PD).

R-A: a cable has no integral trip curve, so tolerance_source.engine is neta_table (MV IR ->
Table 100.1, tan-delta -> Table 100.6.6, torque -> 100.12) or mfr (LV IR comparison, MV
dielectric withstand) - never tcc.

RED until gen_cable_template.py emits 014_cable_templates.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_014_cable_template.py
"""
import json
import os
import subprocess

import psycopg
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", r"C:\Program Files\PostgreSQL\18\bin\psql.exe")
PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = os.environ.get("RECORDS_DEV_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"
)

LV_CODE = "ats_lv_cable_v1"
MV_CODE = "ats_mvhv_cable_v1"
LV_SECTION = "7.3.2"
MV_SECTION = "7.3.3"

EXPECTED_LV_SECTIONS = {
    "nameplate", "visual_mechanical", "insulation_resistance", "continuity",
    "test_equipment", "comments_deficiencies",
}
EXPECTED_MV_SECTIONS = {
    "nameplate", "visual_mechanical", "insulation_resistance", "shield_continuity",
    "tdr", "jacket_integrity", "dielectric_withstand", "tan_delta", "partial_discharge",
    "test_equipment", "comments_deficiencies",
}


def _psql(fname):
    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "postgres", "-d", "records_dev",
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}")


def _apply():
    _psql("014_cable_templates_down.sql")
    _psql("014_cable_templates.sql")


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


def _required_neta_refs(conn, section):
    rows = conn.execute(
        "select ti.category, ti.item_number from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = %s and ti.standard = 'ats' "
        "and ti.category in ('visual_mechanical','electrical')", (section,)
    ).fetchall()
    out = set()
    for cat, num in rows:
        out.add(f"{section}.{'A' if cat == 'visual_mechanical' else 'B'}.{num}")
    return out


def _covered_refs(conn, code):
    covered = set()
    for s in _schema(conn, code)["sections"]:
        covered |= set(s.get("neta_covers", []))
    return covered


def _tolerance_sources(conn, code):
    out = []
    for s in _schema(conn, code)["sections"]:
        for f in s.get("fields", []):
            if f.get("tolerance_source"):
                out.append(f["tolerance_source"])
        for c in s.get("table", {}).get("columns", []):
            if c.get("tolerance_source"):
                out.append(c["tolerance_source"])
    return out


def test_both_templates_bound(conn):
    for code, leaf, section in ((LV_CODE, "cable_lv", LV_SECTION), (MV_CODE, "cable_mv", MV_SECTION)):
        row = conn.execute(
            "select t.form_type, t.neta_standard, t.neta_section, t.version, a.class_code "
            "from records.form_templates t "
            "left join records.asset_classes a on a.asset_class_id = t.asset_class_id "
            "where t.template_code = %s and t.is_current", (code,)
        ).fetchone()
        assert row is not None, f"{code} missing"
        form_type, std, sec, version, class_code = row
        assert form_type == "neta_datasheet" and std == "ats" and version == 1
        assert sec == section
        assert class_code == leaf, f"{code} must bind {leaf}, got {class_code}"


def test_schema_shape(conn):
    for code, fam in ((LV_CODE, "lv_cable"), (MV_CODE, "mvhv_cable")):
        fs = _schema(conn, code)
        assert fs.get("version") == 1
        assert fs.get("family") == fam
        assert isinstance(fs.get("selections"), list)
        assert isinstance(fs.get("sections"), list) and fs["sections"]


def test_sections_present(conn):
    assert set(_sections(conn, LV_CODE)) == EXPECTED_LV_SECTIONS
    assert set(_sections(conn, MV_CODE)) == EXPECTED_MV_SECTIONS


def test_lv_coverage(conn):
    required = _required_neta_refs(conn, LV_SECTION)
    covered = _covered_refs(conn, LV_CODE)
    assert required - covered == set(), f"LV cable silent drops: {sorted(required - covered)}"
    assert len(required) == 11


def test_mv_coverage(conn):
    required = _required_neta_refs(conn, MV_SECTION)
    covered = _covered_refs(conn, MV_CODE)
    assert required - covered == set(), f"MV cable silent drops: {sorted(required - covered)}"
    assert len(required) == 18


def test_no_phantom(conn):
    for code, section in ((LV_CODE, LV_SECTION), (MV_CODE, MV_SECTION)):
        required = _required_neta_refs(conn, section)
        covered = _covered_refs(conn, code)
        phantom = {r for r in covered if r.startswith(section + ".")} - required
        assert not phantom, f"{code} phantom refs: {sorted(phantom)}"


def test_mv_hv_battery_sections(conn):
    # the MV/HV-specific shielded-cable battery
    secs = set(_sections(conn, MV_CODE))
    for k in ("shield_continuity", "tdr", "jacket_integrity", "dielectric_withstand",
              "tan_delta", "partial_discharge"):
        assert k in secs, f"MV cable must have the {k} section"
    # LV (600 V) does not carry the HV battery
    lv = set(_sections(conn, LV_CODE))
    assert "tan_delta" not in lv and "dielectric_withstand" not in lv


def test_ra_engines(conn):
    for code in (LV_CODE, MV_CODE):
        engines = {s.get("engine") for s in _tolerance_sources(conn, code)}
        assert engines, f"{code} expected declared tolerance_source bindings"
        assert engines <= {"neta_table", "mfr"}, f"{code} bad engines {engines}"
        assert "tcc" not in engines


def test_ra_mv_ir_table_100_1(conn):
    ir = _sections(conn, MV_CODE)["insulation_resistance"]
    cols = ir.get("table", {}).get("columns", []) + ir.get("fields", [])
    tables = {c["tolerance_source"]["table"] for c in cols
              if c.get("tolerance_source", {}).get("engine") == "neta_table"
              and "table" in c["tolerance_source"]}
    assert "100.1" in tables, "MV cable IR must cite Table 100.1"


def test_ra_mfr_slot(conn):
    for code in (LV_CODE, MV_CODE):
        mfr = [s for s in _tolerance_sources(conn, code) if s.get("engine") == "mfr"]
        assert mfr, f"{code} must declare an mfr tolerance_source"


def test_no_prefilled_windows(conn):
    for code in (LV_CODE, MV_CODE):
        for s in _schema(conn, code)["sections"]:
            for c in s.get("table", {}).get("columns", []):
                if c.get("tolerance_source"):
                    assert "value" not in c, f"{code}.{c['tag']} must not pre-fill a window"


def test_rc_nameplate_inherited(conn):
    for code in (LV_CODE, MV_CODE):
        np = _sections(conn, code)["nameplate"]
        inherited = [f for f in np["fields"] if f.get("data_source") == "inherited"]
        assert len(inherited) >= 5, f"{code} nameplate should inherit from the asset"


def test_reversibility(conn):
    _psql("014_cable_templates_down.sql")
    with psycopg.connect(DSN) as c:
        for code in (LV_CODE, MV_CODE):
            gone = c.execute(
                "select count(*) from records.form_templates where template_code = %s", (code,)
            ).fetchone()[0]
            assert gone == 0, f"down migration should remove {code}"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
