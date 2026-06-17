"""TDD - Records Chip 2b: the Instrument-Transformer datasheets (CT / VT / CVT).

Three leaf-bound single-procedure sheets (the clean recipe, like the cables):
  - ats_ct_v1  -> it_ct;  NETA 7.10.1 (Current Transformer);              18 ATS (9 VM + 9 elec).
  - ats_vt_v1  -> it_vt;  NETA 7.10.2 (Voltage / Potential Transformer);  18 ATS (11 VM + 7 elec).
  - ats_cvt_v1 -> it_cvt; NETA 7.10.3 (Coupling-Capacitor VT);            20 ATS (11 VM + 9 elec).

R-A: an instrument transformer has no integral trip curve, so tolerance_source.engine is
neta_table (IR -> Table 100.5, dielectric withstand -> Table 100.9, torque -> 100.12) or mfr
(PF/DF >= 15/38 kV per mfr data) - never tcc.

CAPTURE-MODE CONTRACT (NEW - IT is the first capture-mode-aware build, ratified post-235):
  Each template declares a template-level `capture` block {modes, default} and carries a standard
  `attachments` section (kind=attachment, capture_mode=cover_attach = Path 1: the datasheet is a
  cover for the mfr/OEM report). Instrument-fillable sections declare capture_mode=instrument_import
  + an `import` hint {tool, profile} naming the bridge (ct_analyzer / dtax / ptm) = Path 2. The
  harvested control `tag` is the Path-2 import target id. Importer execution = Chip 10 (deferred).

Coverage invariant: per sheet, the union of every section's neta_covers covers all ATS
visual_mechanical+electrical items of its procedure (no silent drops, no phantom refs).

RED until gen_it_template.py emits 015_it_datasheet_templates.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_015_it_template.py
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

CT_CODE = "ats_ct_v1"
VT_CODE = "ats_vt_v1"
CVT_CODE = "ats_cvt_v1"
# (code, leaf, section, n_items, n_sections)
SHEETS = [
    (CT_CODE, "it_ct", "7.10.1", 18, 12),
    (VT_CODE, "it_vt", "7.10.2", 18, 11),
    (CVT_CODE, "it_cvt", "7.10.3", 20, 12),
]

EXPECTED_SECTIONS = {
    CT_CODE: {
        "nameplate", "visual_mechanical", "insulation_resistance", "ratio_polarity",
        "excitation", "burden", "dielectric_withstand", "power_factor", "grounding",
        "test_equipment", "comments_deficiencies", "attachments",
    },
    VT_CODE: {
        "nameplate", "visual_mechanical", "insulation_resistance", "ratio_polarity",
        "burden", "dielectric_withstand", "power_factor", "grounding",
        "test_equipment", "comments_deficiencies", "attachments",
    },
    CVT_CODE: {
        "nameplate", "visual_mechanical", "bolted_resistance", "insulation_resistance",
        "ratio_polarity", "burden", "dielectric_withstand", "capacitance_pf", "grounding",
        "test_equipment", "comments_deficiencies", "attachments",
    },
}

KNOWN_IMPORT_TOOLS = {"ct_analyzer", "dtax", "ptm"}


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
    _psql("015_it_datasheet_templates_down.sql")
    _psql("015_it_datasheet_templates.sql")


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


def _controls(section):
    return list(section.get("fields", [])) + list(section.get("table", {}).get("columns", []))


def _tolerance_sources(conn, code):
    out = []
    for s in _schema(conn, code)["sections"]:
        for c in _controls(s):
            if c.get("tolerance_source"):
                out.append(c["tolerance_source"])
    return out


def test_three_templates_bound(conn):
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
        assert sec == section, f"{code} section {sec} != {section}"
        assert class_code == leaf, f"{code} must bind {leaf}, got {class_code}"


def test_schema_shape(conn):
    for code, _, _, _, _ in SHEETS:
        fs = _schema(conn, code)
        assert fs.get("version") == 1
        assert fs.get("family")
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
        assert engines <= {"neta_table", "mfr"}, f"{code} bad engines {engines}"
        assert "tcc" not in engines


def test_ra_neta_tables(conn):
    # IR cites Table 100.5; dielectric withstand cites Table 100.9.
    for code, _, _, _, _ in SHEETS:
        tables = {s["table"] for s in _tolerance_sources(conn, code)
                  if s.get("engine") == "neta_table" and "table" in s}
        assert "100.5" in tables, f"{code} IR must cite Table 100.5"
        assert "100.9" in tables, f"{code} dielectric must cite Table 100.9"


def test_ra_mfr_slot(conn):
    # power-factor / dissipation-factor is the mfr-tolerance slot on every IT sheet.
    for code, _, _, _, _ in SHEETS:
        mfr = [s for s in _tolerance_sources(conn, code) if s.get("engine") == "mfr"]
        assert mfr, f"{code} must declare an mfr tolerance_source (PF/DF)"


def test_no_prefilled_windows(conn):
    for code, _, _, _, _ in SHEETS:
        for s in _schema(conn, code)["sections"]:
            for c in _controls(s):
                if c.get("tolerance_source"):
                    assert "value" not in c, f"{code}.{c['tag']} must not pre-fill a window"


def test_nameplate_inherited(conn):
    for code, _, _, _, _ in SHEETS:
        np = _sections(conn, code)["nameplate"]
        inherited = [f for f in np["fields"] if f.get("data_source") == "inherited"]
        assert len(inherited) >= 5, f"{code} nameplate should inherit from the asset"


# ---- capture-mode contract (NEW) ------------------------------------------------

def test_capture_block(conn):
    for code, _, _, _, _ in SHEETS:
        cap = _schema(conn, code).get("capture")
        assert isinstance(cap, dict), f"{code} missing template capture block"
        modes = set(cap.get("modes", []))
        assert {"field", "instrument_import", "cover_attach"} <= modes, f"{code} capture modes {modes}"
        assert cap.get("default") == "field", f"{code} default capture mode must be field"


def test_cover_attach_section(conn):
    # Path 1: the datasheet doubles as a cover for the mfr/OEM report.
    for code, _, _, _, _ in SHEETS:
        att = _sections(conn, code)["attachments"]
        assert att.get("kind") == "attachment", f"{code} attachments must be kind=attachment"
        assert att.get("capture_mode") == "cover_attach", f"{code} attachments must be cover_attach"
        kinds = {f.get("value_kind") for f in att.get("fields", [])}
        assert "attachment" in kinds, f"{code} attachments must carry an attachment control"
        # the cover affordance is NOT a NETA test - it must not claim coverage
        assert not att.get("neta_covers"), f"{code} attachments must not claim NETA coverage"


def test_instrument_import_hints(conn):
    # Path 2: at least one section per sheet is an instrument_import target with a bridge hint.
    for code, _, _, _, _ in SHEETS:
        imp = [s for s in _schema(conn, code)["sections"]
               if s.get("capture_mode") == "instrument_import"]
        assert imp, f"{code} expected at least one instrument_import section"
        for s in imp:
            h = s.get("import")
            assert isinstance(h, dict) and h.get("tool") in KNOWN_IMPORT_TOOLS, \
                f"{code}.{s['key']} import hint {h} must name a known bridge tool"
            assert h.get("profile"), f"{code}.{s['key']} import hint must name a profile"


def test_ct_excitation_is_ct_analyzer(conn):
    exc = _sections(conn, CT_CODE)["excitation"]
    assert exc.get("capture_mode") == "instrument_import"
    assert exc["import"]["tool"] == "ct_analyzer", "CT excitation curve is the CT-Analyzer import"


def test_cvt_capacitance_battery(conn):
    # the CVT-specific battery: capacitance of capacitor sections + PF/DF.
    secs = set(_sections(conn, CVT_CODE))
    assert "capacitance_pf" in secs and "bolted_resistance" in secs
    # CT / VT do not carry the capacitance battery
    assert "capacitance_pf" not in set(_sections(conn, CT_CODE))
    assert "capacitance_pf" not in set(_sections(conn, VT_CODE))


def test_reversibility(conn):
    _psql("015_it_datasheet_templates_down.sql")
    with psycopg.connect(DSN) as c:
        for code, _, _, _, _ in SHEETS:
            gone = c.execute(
                "select count(*) from records.form_templates where template_code = %s", (code,)
            ).fetchone()[0]
            assert gone == 0, f"down migration should remove {code}"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
