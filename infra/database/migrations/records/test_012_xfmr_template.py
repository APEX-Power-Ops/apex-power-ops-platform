"""TDD - Records Chip 2b: the transformer composite datasheets (dry + liquid).

Applies 012 (two form_templates: ats_dry_xfmr_v1, ats_liquid_xfmr_v1) to records_dev and
asserts the field_schema contract + the NETA coverage invariant per sheet + the operator's
"fold 2W and 3W" ruling.

Two leaf-bound composites (matching cb_lv / cb_mvhv):
  - ats_dry_xfmr_v1  -> xfmr_dry; folds small (7.2.1.1) + large (7.2.1.2) via a dry_class
    selector; covers their UNION = 35 ATS items.
  - ats_liquid_xfmr_v1 -> xfmr_liquid; 7.2.2; 39 ATS items (incl. LTC/IT/surge-arrester
    cross-ref borrows to 7.12.3 / 7.10 / 7.19).
Both fold 2W/3W via a winding_config selector that gates the tertiary-winding measurement
rows (H-Y, X-Y, Y-G) - measurement granularity, not NETA coverage.

R-A (operator-confirmed for transformers): no integral trip curve, so tolerance_source.engine
is neta_table (IR 100.5, torque 100.12) or mfr (winding resistance, bushing PF, turns-ratio) -
never tcc. Oil/DGA acceptance is standard-basis (ASTM D923 / IEEE C57.104).

RED until gen_xfmr_template.py emits 012_xfmr_datasheet_templates.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_012_xfmr_template.py
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

DRY_CODE = "ats_dry_xfmr_v1"
LIQ_CODE = "ats_liquid_xfmr_v1"
DRY_SECTIONS_NETA = ["7.2.1.1", "7.2.1.2"]
LIQ_SECTIONS_NETA = ["7.2.2"]
DRY_PRIMARY = "7.2.1.1"
LIQ_PRIMARY = "7.2.2"

EXPECTED_DRY_SECTIONS = {
    "nameplate", "visual_mechanical", "insulation_resistance", "turns_ratio",
    "winding_resistance", "power_factor", "excitation_current", "dielectric_withstand",
    "bolted_resistance", "functional", "surge_arresters",
    "test_equipment", "comments_deficiencies",
}
EXPECTED_LIQ_SECTIONS = {
    "nameplate", "visual_mechanical", "insulation_resistance", "turns_ratio",
    "winding_resistance", "power_factor", "excitation_current", "advanced_diagnostics",
    "insulating_liquid", "gas_blanket", "load_tap_changer", "bolted_resistance",
    "auxiliary", "instrument_transformers", "surge_arresters",
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
    _psql("012_xfmr_datasheet_templates_down.sql")   # reset (idempotent)
    _psql("012_xfmr_datasheet_templates.sql")


@pytest.fixture(scope="module")
def conn():
    _apply()
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _schema(conn, code):
    row = conn.execute(
        "select field_schema from records.form_templates "
        "where template_code = %s and is_current", (code,)
    ).fetchone()
    assert row is not None, f"template {code} not found / not current"
    fs = row[0]
    return json.loads(fs) if isinstance(fs, str) else fs


def _sections(conn, code):
    return {s["key"]: s for s in _schema(conn, code)["sections"]}


def _rows(section):
    return {r["key"]: r for r in section.get("table", {}).get("row_dim", {}).get("rows", [])}


def _required_neta_refs(conn, neta_sections):
    rows = conn.execute(
        "select p.section, ti.category, ti.item_number from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = any(%s) and ti.standard = 'ats' "
        "and ti.category in ('visual_mechanical','electrical')", (neta_sections,)
    ).fetchall()
    out = set()
    for sec, cat, num in rows:
        letter = "A" if cat == "visual_mechanical" else "B"
        out.add(f"{sec}.{letter}.{num}")
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


# ---- identity / binding ----

def test_both_templates_bound(conn):
    for code, leaf, primary in ((DRY_CODE, "xfmr_dry", DRY_PRIMARY),
                                (LIQ_CODE, "xfmr_liquid", LIQ_PRIMARY)):
        row = conn.execute(
            "select t.form_type, t.neta_standard, t.neta_section, t.is_current, t.version, "
            "a.class_code from records.form_templates t "
            "left join records.asset_classes a on a.asset_class_id = t.asset_class_id "
            "where t.template_code = %s and t.is_current", (code,)
        ).fetchone()
        assert row is not None, f"{code} current template missing"
        form_type, std, section, is_current, version, class_code = row
        assert form_type == "neta_datasheet"
        assert std == "ats"
        assert section == primary, f"{code} neta_section {section} != {primary}"
        assert is_current is True and version == 1
        assert class_code == leaf, f"{code} must bind to {leaf}, got {class_code}"


def test_schema_shape(conn):
    for code, fam in ((DRY_CODE, "dry_transformer"), (LIQ_CODE, "liquid_transformer")):
        fs = _schema(conn, code)
        assert fs.get("version") == 1
        assert fs.get("family") == fam
        assert isinstance(fs.get("selections"), list) and fs["selections"]
        assert isinstance(fs.get("sections"), list) and fs["sections"]


def test_sections_present(conn):
    assert set(_sections(conn, DRY_CODE)) == EXPECTED_DRY_SECTIONS
    assert set(_sections(conn, LIQ_CODE)) == EXPECTED_LIQ_SECTIONS


# ---- the operator's fold: winding_config on BOTH; dry_class on dry ----

def test_winding_config_selector_on_both(conn):
    for code in (DRY_CODE, LIQ_CODE):
        sel = {s["tag"]: s for s in _schema(conn, code)["selections"]}
        assert "winding_config" in sel, f"{code} needs a winding_config selector"
        assert set(sel["winding_config"]["options"]) == {"two_winding", "three_winding"}


def test_dry_class_selector(conn):
    sel = {s["tag"]: s for s in _schema(conn, DRY_CODE)["selections"]}
    assert "dry_class" in sel, "dry sheet needs a small/large dry_class selector"
    assert set(sel["dry_class"]["options"]) == {"small", "large"}


def test_three_winding_rows_gated(conn):
    # IR + turns_ratio carry tertiary-winding rows gated to three_winding
    for code in (DRY_CODE, LIQ_CODE):
        for sec_key in ("insulation_resistance", "turns_ratio"):
            rows = _rows(_sections(conn, code)[sec_key])
            thirds = [k for k in rows if k in ("h_y", "x_y", "y_g")]
            assert thirds, f"{code}.{sec_key} must have tertiary-winding rows"
            for k in thirds:
                assert "three_winding" in rows[k].get("visible_if", ""), \
                    f"{code}.{sec_key}.{k} must gate to three_winding"


def test_dry_large_only_gated(conn):
    # excitation_current is a large-only dry section
    sec = _sections(conn, DRY_CODE)["excitation_current"]
    assert "large" in sec.get("visible_if", ""), "dry excitation must gate to large"


# ---- coverage invariant per sheet ----

def test_dry_coverage(conn):
    required = _required_neta_refs(conn, DRY_SECTIONS_NETA)
    covered = _covered_refs(conn, DRY_CODE)
    assert required - covered == set(), f"dry silent drops: {sorted(required - covered)}"
    assert len(required) == 35


def test_liquid_coverage(conn):
    required = _required_neta_refs(conn, LIQ_SECTIONS_NETA)
    covered = _covered_refs(conn, LIQ_CODE)
    assert required - covered == set(), f"liquid silent drops: {sorted(required - covered)}"
    assert len(required) == 39


def test_no_phantom(conn):
    for code, secs in ((DRY_CODE, DRY_SECTIONS_NETA), (LIQ_CODE, LIQ_SECTIONS_NETA)):
        required = _required_neta_refs(conn, secs)
        covered = _covered_refs(conn, code)
        prefixes = tuple(s + "." for s in secs)
        phantom = {r for r in covered if r.startswith(prefixes)} - required
        assert not phantom, f"{code} phantom refs: {sorted(phantom)}"


# ---- R-A: neta_table + mfr, never tcc ----

def test_ra_engines(conn):
    for code in (DRY_CODE, LIQ_CODE):
        engines = {s.get("engine") for s in _tolerance_sources(conn, code)}
        assert engines, f"{code} expected declared tolerance_source bindings"
        assert engines <= {"neta_table", "mfr"}, f"{code} bad engines {engines}"
        assert "tcc" not in engines


def test_ra_ir_table_100_5(conn):
    # the transformer IR basis is Table 100.5 (not 100.1)
    for code in (DRY_CODE, LIQ_CODE):
        ir = _sections(conn, code)["insulation_resistance"]
        cols = ir.get("table", {}).get("columns", [])
        tables = {c["tolerance_source"]["table"] for c in cols
                  if c.get("tolerance_source", {}).get("engine") == "neta_table"
                  and "table" in c["tolerance_source"]}
        assert "100.5" in tables, f"{code} IR must cite Table 100.5"


def test_ra_mfr_slot(conn):
    for code in (DRY_CODE, LIQ_CODE):
        mfr = [s for s in _tolerance_sources(conn, code) if s.get("engine") == "mfr"]
        assert mfr, f"{code} must declare an mfr tolerance_source (the future mfr-layer slot)"


def test_no_prefilled_windows(conn):
    for code in (DRY_CODE, LIQ_CODE):
        for s in _schema(conn, code)["sections"]:
            for c in s.get("table", {}).get("columns", []):
                if c.get("tolerance_source"):
                    assert "value" not in c, f"{code}.{c['tag']} must not pre-fill a window"


# ---- liquid cross-ref borrows (LTC 7.12.3, IT 7.10, surge 7.19) ----

def test_liquid_borrows_covered(conn):
    secs = _sections(conn, LIQ_CODE)
    it = set(secs["instrument_transformers"].get("neta_covers", []))
    assert it and all(r.startswith("7.2.2.") for r in it), "IT borrow must be covered under 7.2.2"
    # the LTC + surge sections exist as cross-references
    assert "load_tap_changer" in secs
    assert "surge_arresters" in secs


# ---- R-C ----

def test_rc_nameplate_inherited(conn):
    for code in (DRY_CODE, LIQ_CODE):
        np = _sections(conn, code)["nameplate"]
        inherited = [f for f in np["fields"] if f.get("data_source") == "inherited"]
        assert len(inherited) >= 8, f"{code} nameplate should inherit from the asset"


def test_reversibility(conn):
    _psql("012_xfmr_datasheet_templates_down.sql")
    with psycopg.connect(DSN) as c:
        for code in (DRY_CODE, LIQ_CODE):
            gone = c.execute(
                "select count(*) from records.form_templates where template_code = %s", (code,)
            ).fetchone()[0]
            assert gone == 0, f"down migration should remove {code}"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
