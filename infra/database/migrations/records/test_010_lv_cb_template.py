"""TDD — Records Chip 2b: the LV circuit-breaker composite datasheet template.

Applies 010 (the ats_lv_cb_v1 form_templates seed) to records_dev and asserts the
field_schema contract + the NETA 7.6.1.2 coverage invariant + the operator's blessed
decisions (R-A/R-B/R-C + the 5 red-line leans).

THE coverage invariant: every records.neta_test_items row for the Power procedure
(7.6.1.2, standard='ats', category in visual_mechanical|electrical) maps to a control
that cites it — i.e. its canonical ref is in the union of the sections' `neta_covers`.
No silent drops; nothing fabricated.

Assumes records_dev has Chip 1 + 2a (neta_*) + 2-shell (asset_classes) + 2-backfill applied.
RED until gen_lv_cb_template.py emits 010_lv_cb_datasheet_template.sql. Run:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_010_lv_cb_template.py
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

TEMPLATE_CODE = "ats_lv_cb_v1"
POWER_SECTION = "7.6.1.2"
EXPECTED_SECTIONS = {
    "nameplate", "visual_mechanical", "operation_counter", "settings_lsig",
    "insulation_resistance", "contact_resistance", "primary_injection",
    "secondary_injection", "auxiliary", "test_equipment", "comments_deficiencies",
}
IR_ROWS = {
    "pole_1_2", "pole_2_3", "pole_1_3", "pole_to_ground_closed",
    "across_open_pole", "control_wiring", "line_to_load",
}
LSIG = {"long", "short", "instantaneous", "ground"}


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
    _psql("010_lv_cb_datasheet_template_down.sql")   # reset (idempotent)
    _psql("010_lv_cb_datasheet_template.sql")


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


def _row_keys(section):
    return {r["key"] for r in section.get("table", {}).get("row_dim", {}).get("rows", [])}


def _required_neta_refs(conn):
    rows = conn.execute(
        "select ti.category, ti.item_number from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = %s and ti.standard = 'ats' "
        "and ti.category in ('visual_mechanical','electrical')", (POWER_SECTION,)
    ).fetchall()
    out = set()
    for cat, num in rows:
        letter = "A" if cat == "visual_mechanical" else "B"
        out.add(f"{POWER_SECTION}.{letter}.{num}")
    return out


def _covered_refs(conn):
    covered = set()
    for s in _schema(conn)["sections"]:
        covered |= set(s.get("neta_covers", []))
    return covered


# ---- template identity / contract shape ----

def test_template_exists_and_bound(conn):
    row = conn.execute(
        "select t.form_type, t.neta_standard, t.neta_section, t.is_current, t.version, "
        "a.class_code from records.form_templates t "
        "left join records.asset_classes a on a.asset_class_id = t.asset_class_id "
        "where t.template_code = %s and t.is_current", (TEMPLATE_CODE,)
    ).fetchone()
    assert row is not None, "ats_lv_cb_v1 current template missing"
    form_type, std, section, is_current, version, class_code = row
    assert form_type == "neta_datasheet"
    assert std == "ats"
    assert section == POWER_SECTION
    assert is_current is True and version == 1
    assert class_code == "cb_lv", f"template must bind to cb_lv leaf, got {class_code}"


def test_field_schema_shape(conn):
    fs = _schema(conn)
    assert fs.get("version") == 1
    assert fs.get("family") == "lv_circuit_breaker"
    assert isinstance(fs.get("selections"), list) and fs["selections"]
    assert isinstance(fs.get("sections"), list) and fs["sections"]


def test_construction_type_selector(conn):
    sel = {s["tag"]: s for s in _schema(conn)["selections"]}
    assert "construction_type" in sel, "the composite needs a construction_type selector"
    assert set(sel["construction_type"]["options"]) == {"power", "insulated_case", "molded_case"}
    assert sel["construction_type"].get("ties_to") == "equipment_model"


def test_sections_present(conn):
    assert set(_sections(conn).keys()) == EXPECTED_SECTIONS


# ---- THE coverage invariant ----

def test_neta_coverage_invariant(conn):
    required = _required_neta_refs(conn)
    covered = _covered_refs(conn)
    missing = required - covered
    assert not missing, f"NETA 7.6.1.2 items with no field (silent drop): {sorted(missing)}"


def test_coverage_required_is_full(conn):
    # sanity: the Power procedure really has 16 VM + 9 electrical = 25 prescribed items
    assert len(_required_neta_refs(conn)) == 25


def test_no_phantom_coverage(conn):
    # every neta_covers ref must be a real Power-procedure item (no fabricated refs)
    required = _required_neta_refs(conn)
    covered = _covered_refs(conn)
    phantom = {r for r in covered if r.startswith(POWER_SECTION + ".")} - required
    assert not phantom, f"neta_covers cite non-existent items: {sorted(phantom)}"


# ---- the 5 blessed decisions ----

def test_rb_all_16_vm_items(conn):
    covered = _covered_refs(conn)
    vm = {r for r in covered if r.startswith(POWER_SECTION + ".A.")}
    assert len(vm) == 16, f"R-B: expected all 16 VM items covered, got {sorted(vm)}"


def test_decision2_settings_pickup_and_factor(conn):
    cols = _columns(_sections(conn)["settings_lsig"])
    for c in ("af_pickup", "af_factor", "af_delay", "af_curve",
              "al_pickup", "al_factor", "al_delay", "al_curve"):
        assert c in cols, f"settings_lsig missing column {c}"
    assert _row_keys(_sections(conn)["settings_lsig"]) == LSIG


def test_decision3_ir_rows(conn):
    assert _row_keys(_sections(conn)["insulation_resistance"]) == IR_ROWS


def test_decision4_primary_injection_per_pole(conn):
    pi = _sections(conn)["primary_injection"]
    assert pi.get("per_pole") is True, "decision 4: capture trip time per pole"
    assert _row_keys(pi) == LSIG


def test_decision5_voltage_drop(conn):
    assert "voltage_drop" in _columns(_sections(conn)["primary_injection"])


# ---- R-A: tolerance-source binding (declared, resolved at provisioning) ----

def test_ra_tolerance_source_binding(conn):
    pi = _sections(conn)["primary_injection"]
    cols = {c["tag"]: c for c in pi["table"]["columns"]}
    for tag in ("min_time", "max_time"):
        ts = cols[tag].get("tolerance_source")
        assert ts and ts.get("engine") == "tcc", f"{tag} must declare a tcc tolerance_source"
    # the template carries NO fabricated window value (resolved at provisioning, Chip 5)
    for tag in ("min_time", "max_time"):
        assert "value" not in cols[tag], "windows must not be pre-filled in the template"


# ---- R-C: asset vs submission data_source ----

def test_rc_nameplate_inherited(conn):
    np = _sections(conn)["nameplate"]
    inherited = [f for f in np["fields"] if f.get("data_source") == "inherited"]
    assert len(inherited) >= 8, "R-C: nameplate identity should inherit from the asset"


def test_rc_readings_are_data(conn):
    pi = _sections(conn)["primary_injection"]
    reading = next(c for c in pi["table"]["columns"] if c["tag"] == "pickup_amps")
    assert reading["data_source"] == "data", "R-C: test readings are per-visit data"


# ---- drawout gating (the composite deltas) ----

def test_drawout_gating(conn):
    vm = _sections(conn)["visual_mechanical"]
    rows = {r["key"]: r for r in vm["table"]["row_dim"]["rows"]}
    for k in ("vm_racking_mechanism", "vm_cell_fit_element_align", "vm_arc_chutes"):
        assert "visible_if" in rows[k], f"{k} must be gated to drawout breakers"
        assert "molded_case" not in rows[k]["visible_if"]


def test_reversibility(conn):
    _psql("010_lv_cb_datasheet_template_down.sql")
    with psycopg.connect(DSN) as c:
        gone = c.execute(
            "select count(*) from records.form_templates where template_code = %s",
            (TEMPLATE_CODE,)
        ).fetchone()[0]
        assert gone == 0, "down migration should remove the template"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
