"""TDD - Records Chip 2b: the switchgear + panelboard datasheets.

Applies 013 (two form_templates: ats_switchgear_v1, ats_panelboard_v1) to records_dev.

Switchgear has a structure the breaker/transformer chips did not: FOUR leaves share NETA
7.1.1 (LV switchboard / MV metal-clad / pad-mount / VFI), and panelboard is its own 7.1.2.
So:
  - ats_switchgear_v1 covers 7.1.1 (35 ATS), with an assembly_type selector for the 4 types,
    and is bound to the PARENT `switchgear` node (the 7.1.1 procedure's home) - because four
    leaves share the procedure, it cannot 1:1-bind to a leaf the way prior sheets did.
  - ats_panelboard_v1 covers 7.1.2 (14 ATS), leaf-bound to `swgr_panelboard`.

R-A: a switchgear assembly has no integral trip curve, so tolerance_source.engine is
neta_table (IR 100.1, dielectric 100.2, torque 100.12) or mfr (bolted-connection resistance) -
never tcc. The IT (7.10) / surge-arrester (7.19) / ground (7.13) / metering (7.11) items are
cross-ref borrows covered, not fabricated.

RED until gen_switchgear_template.py emits 013_switchgear_templates.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_013_switchgear_template.py
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

SWGR_CODE = "ats_switchgear_v1"
PANEL_CODE = "ats_panelboard_v1"
SWGR_SECTION = "7.1.1"
PANEL_SECTION = "7.1.2"

EXPECTED_SWGR_SECTIONS = {
    "nameplate", "visual_mechanical", "insulation_resistance", "dielectric_withstand",
    "bolted_resistance", "instrument_transformers", "metering", "ground_resistance",
    "functional", "surge_arresters", "partial_discharge",
    "test_equipment", "comments_deficiencies",
}
EXPECTED_PANEL_SECTIONS = {
    "nameplate", "visual_mechanical", "insulation_resistance", "ground_resistance",
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
    _psql("013_switchgear_templates_down.sql")
    _psql("013_switchgear_templates.sql")


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
        letter = "A" if cat == "visual_mechanical" else "B"
        out.add(f"{section}.{letter}.{num}")
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


# ---- identity / binding (incl. the parent-binding novelty) ----

def test_switchgear_parent_bound(conn):
    row = conn.execute(
        "select t.form_type, t.neta_standard, t.neta_section, t.version, "
        "a.class_code, a.parent_class_id from records.form_templates t "
        "left join records.asset_classes a on a.asset_class_id = t.asset_class_id "
        "where t.template_code = %s and t.is_current", (SWGR_CODE,)
    ).fetchone()
    assert row is not None, "ats_switchgear_v1 missing"
    form_type, std, section, version, class_code, parent_id = row
    assert form_type == "neta_datasheet" and std == "ats" and version == 1
    assert section == SWGR_SECTION
    assert class_code == "switchgear", f"switchgear sheet must bind the parent node, got {class_code}"
    assert parent_id is None, "the switchgear sheet binds the PARENT (4 leaves share 7.1.1)"


def test_panelboard_leaf_bound(conn):
    row = conn.execute(
        "select t.neta_section, a.class_code, a.parent_class_id from records.form_templates t "
        "left join records.asset_classes a on a.asset_class_id = t.asset_class_id "
        "where t.template_code = %s and t.is_current", (PANEL_CODE,)
    ).fetchone()
    assert row is not None, "ats_panelboard_v1 missing"
    section, class_code, parent_id = row
    assert section == PANEL_SECTION
    assert class_code == "swgr_panelboard", f"panelboard must bind its leaf, got {class_code}"
    assert parent_id is not None, "swgr_panelboard is a leaf"


def test_schema_shape(conn):
    for code, fam in ((SWGR_CODE, "switchgear_assembly"), (PANEL_CODE, "panelboard_assembly")):
        fs = _schema(conn, code)
        assert fs.get("version") == 1
        assert fs.get("family") == fam
        assert isinstance(fs.get("selections"), list)
        assert isinstance(fs.get("sections"), list) and fs["sections"]


def test_assembly_type_selector(conn):
    sel = {s["tag"]: s for s in _schema(conn, SWGR_CODE)["selections"]}
    assert "assembly_type" in sel, "switchgear needs an assembly_type selector"
    assert set(sel["assembly_type"]["options"]) == {
        "lv_switchboard", "mv_metalclad", "padmount", "vfi"}


def test_sections_present(conn):
    assert set(_sections(conn, SWGR_CODE)) == EXPECTED_SWGR_SECTIONS
    assert set(_sections(conn, PANEL_CODE)) == EXPECTED_PANEL_SECTIONS


# ---- coverage invariant per sheet ----

def test_switchgear_coverage(conn):
    required = _required_neta_refs(conn, SWGR_SECTION)
    covered = _covered_refs(conn, SWGR_CODE)
    assert required - covered == set(), f"switchgear silent drops: {sorted(required - covered)}"
    assert len(required) == 35


def test_panelboard_coverage(conn):
    required = _required_neta_refs(conn, PANEL_SECTION)
    covered = _covered_refs(conn, PANEL_CODE)
    assert required - covered == set(), f"panelboard silent drops: {sorted(required - covered)}"
    assert len(required) == 14


def test_no_phantom(conn):
    for code, section in ((SWGR_CODE, SWGR_SECTION), (PANEL_CODE, PANEL_SECTION)):
        required = _required_neta_refs(conn, section)
        covered = _covered_refs(conn, code)
        phantom = {r for r in covered if r.startswith(section + ".")} - required
        assert not phantom, f"{code} phantom refs: {sorted(phantom)}"


# ---- R-A: neta_table + mfr, never tcc ----

def test_ra_engines(conn):
    for code in (SWGR_CODE, PANEL_CODE):
        engines = {s.get("engine") for s in _tolerance_sources(conn, code)}
        assert engines, f"{code} expected declared tolerance_source bindings"
        assert engines <= {"neta_table", "mfr"}, f"{code} bad engines {engines}"
        assert "tcc" not in engines


def test_ra_table_bindings(conn):
    # switchgear: IR -> 100.1, dielectric -> 100.2
    secs = _sections(conn, SWGR_CODE)

    def src_tables(section_key):
        s = secs[section_key]
        cols = s.get("table", {}).get("columns", []) + s.get("fields", [])
        return {c["tolerance_source"]["table"] for c in cols
                if c.get("tolerance_source", {}).get("engine") == "neta_table"
                and "table" in c["tolerance_source"]}
    assert "100.1" in src_tables("insulation_resistance")
    assert "100.2" in src_tables("dielectric_withstand")


def test_ra_mfr_slot(conn):
    # the switchgear sheet's bolted-connection resistance is the mfr slot; panelboard (7.1.2)
    # has only IR + ground-resistance (no mfr-measured electrical value - its bolted
    # connections are the VM torque row), so the mfr slot applies to switchgear only.
    mfr = [s for s in _tolerance_sources(conn, SWGR_CODE) if s.get("engine") == "mfr"]
    assert mfr, "switchgear must declare an mfr tolerance_source (bolted-connection resistance)"


def test_no_prefilled_windows(conn):
    for code in (SWGR_CODE, PANEL_CODE):
        for s in _schema(conn, code)["sections"]:
            for c in s.get("table", {}).get("columns", []):
                if c.get("tolerance_source"):
                    assert "value" not in c, f"{code}.{c['tag']} must not pre-fill a window"


# ---- cross-ref borrows (IT 7.10 / SA 7.19 / ground 7.13 / metering 7.11) ----

def test_switchgear_borrows_covered(conn):
    secs = _sections(conn, SWGR_CODE)
    for sk in ("instrument_transformers", "metering", "ground_resistance", "surge_arresters"):
        cov = set(secs[sk].get("neta_covers", []))
        assert cov and all(r.startswith("7.1.1.") for r in cov), f"{sk} must cover 7.1.1 borrow items"


# ---- R-C ----

def test_rc_nameplate_inherited(conn):
    for code in (SWGR_CODE, PANEL_CODE):
        np = _sections(conn, code)["nameplate"]
        inherited = [f for f in np["fields"] if f.get("data_source") == "inherited"]
        assert len(inherited) >= 6, f"{code} nameplate should inherit from the asset"


def test_reversibility(conn):
    _psql("013_switchgear_templates_down.sql")
    with psycopg.connect(DSN) as c:
        for code in (SWGR_CODE, PANEL_CODE):
            gone = c.execute(
                "select count(*) from records.form_templates where template_code = %s", (code,)
            ).fetchone()[0]
            assert gone == 0, f"down migration should remove {code}"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
