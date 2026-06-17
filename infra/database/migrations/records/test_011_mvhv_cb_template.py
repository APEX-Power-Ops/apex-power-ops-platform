"""TDD - Records Chip 2b: the MV/HV circuit-breaker composite datasheet template.

Applies 011 (the ats_mvhv_cb_v1 form_templates seed) to records_dev and asserts the
field_schema contract + the NETA coverage invariant across ALL FOUR interrupting-medium
procedures + the operator's blessed decisions.

THE coverage invariant: every records.neta_test_items row for the four cb_mvhv procedures
(7.6.1.3 air, 7.6.2 oil, 7.6.3 vacuum, 7.6.4 SF6; standard='ats', category in
visual_mechanical|electrical) maps to a control that cites it - i.e. its canonical ref is
in the union of the sections' `neta_covers`. No silent drops; nothing fabricated.

R-A (operator-confirmed for MV/HV): MV/HV breakers have NO integral trip curve, so the
acceptance windows are sourced from NETA tables + mfr-published data, NOT lvbreakertcc.
tolerance_source.engine must be in {neta_table, mfr} - never 'tcc'.

Assumes records_dev has Chip 1 + 2a (neta_*) + 2-shell (asset_classes) + 2-backfill applied.
RED until gen_mv_cb_template.py emits 011_mvhv_cb_datasheet_template.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_011_mvhv_cb_template.py
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

TEMPLATE_CODE = "ats_mvhv_cb_v1"
PRIMARY_SECTION = "7.6.1.3"
MEDIA_SECTIONS = ["7.6.1.3", "7.6.2", "7.6.3", "7.6.4"]
EXPECTED_SECTIONS = {
    "nameplate", "visual_mechanical", "operation_counter", "contact_timing",
    "insulation_resistance", "contact_resistance", "dielectric_withstand",
    "power_factor", "pickup_coils", "insulating_liquid", "sf6_gas",
    "auxiliary", "instrument_transformers", "test_equipment", "comments_deficiencies",
}
MEDIA = {"air", "oil", "vacuum", "sf6"}


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
    _psql("011_mvhv_cb_datasheet_template_down.sql")   # reset (idempotent)
    _psql("011_mvhv_cb_datasheet_template.sql")


@pytest.fixture(scope="module")
def conn():
    _apply()
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _schema(conn):
    row = conn.execute(
        "select field_schema from records.form_templates "
        "where template_code = %s and is_current", (TEMPLATE_CODE,)
    ).fetchone()
    assert row is not None, f"template {TEMPLATE_CODE} not found / not current"
    fs = row[0]
    return json.loads(fs) if isinstance(fs, str) else fs


def _sections(conn):
    return {s["key"]: s for s in _schema(conn)["sections"]}


def _columns(section):
    return {c["tag"] for c in section.get("table", {}).get("columns", [])}


def _rows(section):
    return {r["key"]: r for r in section.get("table", {}).get("row_dim", {}).get("rows", [])}


def _required_neta_refs(conn):
    rows = conn.execute(
        "select p.section, ti.category, ti.item_number from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = any(%s) and ti.standard = 'ats' "
        "and ti.category in ('visual_mechanical','electrical')", (MEDIA_SECTIONS,)
    ).fetchall()
    out = set()
    for sec, cat, num in rows:
        letter = "A" if cat == "visual_mechanical" else "B"
        out.add(f"{sec}.{letter}.{num}")
    return out


def _covered_refs(conn):
    covered = set()
    for s in _schema(conn)["sections"]:
        covered |= set(s.get("neta_covers", []))
    return covered


def _all_tolerance_sources(conn):
    out = []
    for s in _schema(conn)["sections"]:
        for f in s.get("fields", []):
            if f.get("tolerance_source"):
                out.append(f["tolerance_source"])
        for c in s.get("table", {}).get("columns", []):
            if c.get("tolerance_source"):
                out.append(c["tolerance_source"])
    return out


# ---- template identity / contract shape ----

def test_template_exists_and_bound(conn):
    row = conn.execute(
        "select t.form_type, t.neta_standard, t.neta_section, t.is_current, t.version, "
        "a.class_code from records.form_templates t "
        "left join records.asset_classes a on a.asset_class_id = t.asset_class_id "
        "where t.template_code = %s and t.is_current", (TEMPLATE_CODE,)
    ).fetchone()
    assert row is not None, "ats_mvhv_cb_v1 current template missing"
    form_type, std, section, is_current, version, class_code = row
    assert form_type == "neta_datasheet"
    assert std == "ats"
    assert section == PRIMARY_SECTION
    assert is_current is True and version == 1
    assert class_code == "cb_mvhv", f"template must bind to cb_mvhv leaf, got {class_code}"


def test_field_schema_shape(conn):
    fs = _schema(conn)
    assert fs.get("version") == 1
    assert fs.get("family") == "mvhv_circuit_breaker"
    assert isinstance(fs.get("selections"), list) and fs["selections"]
    assert isinstance(fs.get("sections"), list) and fs["sections"]


def test_interrupting_medium_selector(conn):
    sel = {s["tag"]: s for s in _schema(conn)["selections"]}
    assert "interrupting_medium" in sel, "the composite needs an interrupting_medium selector"
    assert set(sel["interrupting_medium"]["options"]) == MEDIA
    assert sel["interrupting_medium"].get("ties_to") == "equipment_model"


def test_sections_present(conn):
    assert set(_sections(conn).keys()) == EXPECTED_SECTIONS


# ---- THE coverage invariant (union across all 4 media) ----

def test_neta_coverage_invariant(conn):
    required = _required_neta_refs(conn)
    covered = _covered_refs(conn)
    missing = required - covered
    assert not missing, f"NETA cb_mvhv items with no field (silent drop): {sorted(missing)}"


def test_coverage_required_is_full(conn):
    # air 19+10, oil 19+14, vac 16+13, sf6 18+13 = 122 prescribed ATS items
    assert len(_required_neta_refs(conn)) == 122


def test_no_phantom_coverage(conn):
    required = _required_neta_refs(conn)
    covered = _covered_refs(conn)
    prefixes = tuple(s + "." for s in MEDIA_SECTIONS)
    phantom = {r for r in covered if r.startswith(prefixes)} - required
    assert not phantom, f"neta_covers cite non-existent items: {sorted(phantom)}"


# ---- the blessed structure: medium-gated deltas ----

def test_air_only_deltas_gated(conn):
    rows = _rows(_sections(conn)["visual_mechanical"])
    for k in ("arc_chutes", "puffer"):
        assert k in rows, f"missing air VM item {k}"
        vis = rows[k].get("visible_if", "")
        assert "air" in vis and "oil" not in vis and "sf6" not in vis, f"{k} must gate to air"


def test_oil_only_deltas_gated(conn):
    rows = _rows(_sections(conn)["visual_mechanical"])
    assert "oil_level" in rows
    vis = rows["oil_level"].get("visible_if", "")
    assert "oil" in vis and "air" not in vis


def test_vacuum_only_deltas_gated(conn):
    rows = _rows(_sections(conn)["visual_mechanical"])
    assert "contact_gap" in rows
    vis = rows["contact_gap"].get("visible_if", "")
    assert "vacuum" in vis and "air" not in vis


def test_sf6_gas_section_gated(conn):
    sec = _sections(conn)["sf6_gas"]
    vis = sec.get("visible_if", "")
    assert "sf6" in vis and "air" not in vis, "sf6_gas section must gate to sf6"


def test_insulating_liquid_section_gated(conn):
    sec = _sections(conn)["insulating_liquid"]
    vis = sec.get("visible_if", "")
    assert "oil" in vis and "vacuum" not in vis, "insulating_liquid section must gate to oil"


def test_dielectric_vacuum_integrity_rows(conn):
    # MAC + vacuum-bottle integrity ride in the dielectric section, gated to vacuum
    rows = _rows(_sections(conn)["dielectric_withstand"])
    for k in ("vac_bottle", "mac"):
        assert k in rows, f"missing vacuum dielectric row {k}"
        assert "vacuum" in rows[k].get("visible_if", ""), f"{k} must gate to vacuum"


# ---- R-A: tolerance-source is NETA-table + mfr, NEVER lvbreakertcc ----

def test_ra_tolerance_source_engines(conn):
    srcs = _all_tolerance_sources(conn)
    assert srcs, "expected declared tolerance_source bindings"
    engines = {s.get("engine") for s in srcs}
    assert engines <= {"neta_table", "mfr"}, f"MV/HV must not source tcc; got {engines}"
    assert "tcc" not in engines, "MV/HV breaker has no integral trip curve - no tcc source"


def test_ra_neta_table_bindings(conn):
    secs = _sections(conn)
    # IR -> 100.1, dielectric -> 100.19, pickup -> 100.20 all declare a neta_table source
    def src_tables(section_key):
        s = secs[section_key]
        cols = s.get("table", {}).get("columns", []) + s.get("fields", [])
        return {c["tolerance_source"]["table"]
                for c in cols
                if c.get("tolerance_source", {}).get("engine") == "neta_table"
                and "table" in c["tolerance_source"]}
    assert "100.1" in src_tables("insulation_resistance")
    assert "100.19" in src_tables("dielectric_withstand")
    assert "100.20" in src_tables("pickup_coils")


def test_ra_mfr_slot_present(conn):
    # contact resistance + contact timing declare the mfr engine (the future mfr-layer slot)
    srcs = _all_tolerance_sources(conn)
    mfr = [s for s in srcs if s.get("engine") == "mfr"]
    assert mfr, "contact resistance/timing must declare an mfr tolerance_source"


def test_ra_no_prefilled_windows(conn):
    # windows resolve at provisioning (Chip 5); the template never pre-fills a value
    for s in _schema(conn)["sections"]:
        for c in s.get("table", {}).get("columns", []):
            if c.get("tolerance_source"):
                assert "value" not in c, f"{c['tag']} must not pre-fill a window value"


# ---- R-C: asset vs submission data_source ----

def test_rc_nameplate_inherited(conn):
    np = _sections(conn)["nameplate"]
    inherited = [f for f in np["fields"] if f.get("data_source") == "inherited"]
    assert len(inherited) >= 8, "R-C: nameplate identity should inherit from the asset"


def test_rc_readings_are_data(conn):
    ir = _sections(conn)["insulation_resistance"]
    reading = next(c for c in ir["table"]["columns"] if c["tag"] == "reading_mohm")
    assert reading["data_source"] == "data", "R-C: test readings are per-visit data"


# ---- instrument-transformer 7.10 borrow: covered as a cross-reference, not breaker fields ----

def test_instrument_transformer_xref(conn):
    sec = _sections(conn)["instrument_transformers"]
    covered = set(sec.get("neta_covers", []))
    # the IT item exists in oil/vac/sf6 (not air) and must be covered (no silent drop)
    assert covered, "instrument_transformers section must cover the 7.10 borrow items"
    assert all(r.startswith(("7.6.2.", "7.6.3.", "7.6.4.")) for r in covered)


def test_reversibility(conn):
    _psql("011_mvhv_cb_datasheet_template_down.sql")
    with psycopg.connect(DSN) as c:
        gone = c.execute(
            "select count(*) from records.form_templates where template_code = %s",
            (TEMPLATE_CODE,)
        ).fetchone()[0]
        assert gone == 0, "down migration should remove the template"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
