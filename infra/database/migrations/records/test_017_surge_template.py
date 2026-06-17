"""TDD - Records Chip 2b: the Surge-Protection datasheets (LV SPD + MV/HV arrester).

Operator ruling (2026-06-17): SPLIT the single `surge_arrester` leaf into two, because NETA 7.19
is two genuinely different apparatus. So this chip ALSO does a small taxonomy split:
  - NEW leaf `spd_lv` (Surge Protective Device, Low-Voltage) under the `surge_protection` parent.
  - relink: 7.19.1 now belongs to `spd_lv` (primary); the stale `surge_arrester`->7.19.1 link removed.
Then two leaf-bound single-procedure sheets:
  - ats_lv_spd_v1        -> spd_lv;         NETA 7.19.1 (LV SPD);            8 ATS (6 VM + 2 elec).
  - ats_mvhv_arrester_v1 -> surge_arrester; NETA 7.19.2 (MV/HV arrester);  12 ATS (8 VM + 4 elec).

NOT PowerDB-anchored (no surge form in the corpus) -> NETA-derived. R-A: LV SPD has no NETA
measurement table -> `mfr` (grounding connection per 7.13); MV/HV arrester IR -> Table 100.1
(`neta_table`) + watts-loss -> `mfr`. Never tcc. Capture = field + cover_attach (no arrester bridge).

RED until gen_surge_template.py emits 017_surge_templates.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_017_surge_template.py
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

LV_CODE, LV_LEAF, LV_SEC = "ats_lv_spd_v1", "spd_lv", "7.19.1"
MV_CODE, MV_LEAF, MV_SEC = "ats_mvhv_arrester_v1", "surge_arrester", "7.19.2"
# (code, leaf, section, n_items, n_sections)
SHEETS = [(LV_CODE, LV_LEAF, LV_SEC, 8, 7), (MV_CODE, MV_LEAF, MV_SEC, 12, 9)]

EXPECTED_SECTIONS = {
    LV_CODE: {"nameplate", "visual_mechanical", "functional_status", "grounding",
              "test_equipment", "comments_deficiencies", "attachments"},
    MV_CODE: {"nameplate", "visual_mechanical", "bolted_resistance", "insulation_resistance",
              "grounding", "watts_loss", "test_equipment", "comments_deficiencies", "attachments"},
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
    _psql("017_surge_templates_down.sql")
    _psql("017_surge_templates.sql")


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


# ---- taxonomy split -------------------------------------------------------------

def test_spd_lv_leaf_added(conn):
    row = conn.execute(
        "select p.class_code from records.asset_classes a "
        "left join records.asset_classes p on p.asset_class_id = a.parent_class_id "
        "where a.class_code = %s", (LV_LEAF,)
    ).fetchone()
    assert row is not None, "spd_lv leaf must exist"
    assert row[0] == "surge_protection", "spd_lv must hang under the surge_protection parent"


def test_acnp_relink(conn):
    def link(leaf, section):
        return conn.execute(
            "select acnp.is_primary from records.asset_class_neta_procedure acnp "
            "join records.asset_classes a using (asset_class_id) "
            "join records.neta_procedures p using (neta_procedure_id) "
            "where a.class_code = %s and p.section = %s", (leaf, section)
        ).fetchone()
    assert link("spd_lv", "7.19.1") == (True,), "spd_lv must primary-own 7.19.1"
    assert link("surge_arrester", "7.19.1") is None, "the stale surge_arrester->7.19.1 link must be removed"
    assert link("surge_arrester", "7.19.2") == (True,), "surge_arrester keeps 7.19.2 (primary)"


# ---- the two sheets -------------------------------------------------------------

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


def test_lv_mfr_slot(conn):
    mfr = [s for s in _tolerance_sources(conn, LV_CODE) if s.get("engine") == "mfr"]
    assert mfr, "LV SPD must declare an mfr tolerance_source (grounding connection per 7.13)"


def test_mv_ir_table_100_1(conn):
    tables = {s["table"] for s in _tolerance_sources(conn, MV_CODE)
              if s.get("engine") == "neta_table" and "table" in s}
    assert "100.1" in tables, "MV/HV arrester IR must cite Table 100.1"
    mfr = [s for s in _tolerance_sources(conn, MV_CODE) if s.get("engine") == "mfr"]
    assert mfr, "MV/HV arrester must declare an mfr tolerance_source (watts-loss)"


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
        assert {"field", "cover_attach"} <= modes, f"{code} capture modes {modes}"
        assert "instrument_import" not in modes, f"{code} has no arrester bridge -> no instrument_import"
        assert cap.get("default") == "field"
        imp = [s for s in _schema(conn, code)["sections"] if s.get("capture_mode") == "instrument_import"]
        assert not imp, f"{code} should have no instrument_import section"


def test_cover_attach_section(conn):
    for code, _, _, _, _ in SHEETS:
        att = _sections(conn, code)["attachments"]
        assert att.get("kind") == "attachment" and att.get("capture_mode") == "cover_attach"
        assert "attachment" in {f.get("value_kind") for f in att.get("fields", [])}
        assert not att.get("neta_covers")


def test_mv_arrester_battery(conn):
    secs = set(_sections(conn, MV_CODE))
    for k in ("bolted_resistance", "insulation_resistance", "watts_loss"):
        assert k in secs, f"MV/HV arrester must have the {k} section"
    # LV SPD does not carry the arrester electrical battery
    assert "watts_loss" not in set(_sections(conn, LV_CODE))


def test_reversibility(conn):
    _psql("017_surge_templates_down.sql")
    with psycopg.connect(DSN) as c:
        for code, _, _, _, _ in SHEETS:
            gone = c.execute(
                "select count(*) from records.form_templates where template_code = %s", (code,)
            ).fetchone()[0]
            assert gone == 0, f"down should remove {code}"
        # the split is reversed: spd_lv gone, surge_arrester->7.19.1 restored
        leaf = c.execute("select count(*) from records.asset_classes where class_code = 'spd_lv'").fetchone()[0]
        assert leaf == 0, "down should remove the spd_lv leaf"
        restored = c.execute(
            "select count(*) from records.asset_class_neta_procedure acnp "
            "join records.asset_classes a using (asset_class_id) "
            "join records.neta_procedures p using (neta_procedure_id) "
            "where a.class_code = 'surge_arrester' and p.section = '7.19.1'"
        ).fetchone()[0]
        assert restored == 1, "down should restore surge_arrester->7.19.1"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
