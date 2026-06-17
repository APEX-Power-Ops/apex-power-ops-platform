"""TDD - Records Chip 2b: the Grounding-System datasheet (NETA 7.13).

One leaf-bound single-procedure sheet (the smallest family): `ats_grounding_v1` -> grounding_system;
NETA 7.13 (Grounding Systems); 6 ATS (3 VM + 3 electrical).

NOT PowerDB-anchored (no grounding form in the RESA PowerDB corpus) -> NETA-derived field structure,
the same recipe the pre-IT families used. R-A: a grounding system has no integral trip curve and no
NETA IR/dielectric acceptance table, so tolerance_source.engine is `mfr` (ground resistance vs
design / IEEE 81 / NEC spec; bolted-connection resistance vs mfr) - never tcc, and (here) no neta_table
window (torque -> Table 100.12 stays an acceptance basis on the VM row).

Capture-mode: the universal `attachments` cover section (Path 1) applies (a ground-grid study / fall-
of-potential report can be attached); but there is NO instrument bridge for ground testers, so this
sheet's `capture.modes` = [field, cover_attach] (no instrument_import).

Coverage invariant: union of section neta_covers == all 7.13 ATS vm+electrical items (no drops/phantom).

RED until gen_grounding_template.py emits 016_grounding_template.sql. Run PER-CHIP:
  $env:RECORDS_DEV_PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_016_grounding_template.py
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

CODE = "ats_grounding_v1"
LEAF = "grounding_system"
SECTION = "7.13"

EXPECTED_SECTIONS = {
    "identification", "visual_mechanical", "bolted_resistance", "ground_resistance",
    "point_to_point", "test_equipment", "comments_deficiencies", "attachments",
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
    _psql("016_grounding_template_down.sql")
    _psql("016_grounding_template.sql")


@pytest.fixture(scope="module")
def conn():
    _apply()
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _schema(conn, code=CODE):
    row = conn.execute(
        "select field_schema from records.form_templates where template_code = %s and is_current",
        (code,)
    ).fetchone()
    assert row is not None, f"template {code} not found / not current"
    fs = row[0]
    return json.loads(fs) if isinstance(fs, str) else fs


def _sections(conn):
    return {s["key"]: s for s in _schema(conn)["sections"]}


def _controls(section):
    return list(section.get("fields", [])) + list(section.get("table", {}).get("columns", []))


def _required_neta_refs(conn, section=SECTION):
    rows = conn.execute(
        "select ti.category, ti.item_number from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = %s and ti.standard = 'ats' "
        "and ti.category in ('visual_mechanical','electrical')", (section,)
    ).fetchall()
    return {f"{section}.{'A' if cat == 'visual_mechanical' else 'B'}.{num}" for cat, num in rows}


def _covered_refs(conn):
    covered = set()
    for s in _schema(conn)["sections"]:
        covered |= set(s.get("neta_covers", []))
    return covered


def _tolerance_sources(conn):
    out = []
    for s in _schema(conn)["sections"]:
        for c in _controls(s):
            if c.get("tolerance_source"):
                out.append(c["tolerance_source"])
    return out


def test_template_bound(conn):
    row = conn.execute(
        "select t.form_type, t.neta_standard, t.neta_section, t.version, a.class_code "
        "from records.form_templates t "
        "left join records.asset_classes a on a.asset_class_id = t.asset_class_id "
        "where t.template_code = %s and t.is_current", (CODE,)
    ).fetchone()
    assert row is not None, f"{CODE} missing"
    form_type, std, sec, version, class_code = row
    assert form_type == "neta_datasheet" and std == "ats" and version == 1
    assert sec == SECTION
    assert class_code == LEAF, f"{CODE} must bind {LEAF}, got {class_code}"


def test_schema_shape(conn):
    fs = _schema(conn)
    assert fs.get("version") == 1
    assert fs.get("family") == "grounding"
    assert isinstance(fs.get("selections"), list)
    assert isinstance(fs.get("sections"), list) and fs["sections"]


def test_sections_present(conn):
    assert set(_sections(conn)) == EXPECTED_SECTIONS


def test_coverage_no_drops(conn):
    required = _required_neta_refs(conn)
    covered = _covered_refs(conn)
    assert required - covered == set(), f"grounding silent drops: {sorted(required - covered)}"
    assert len(required) == 6


def test_no_phantom(conn):
    required = _required_neta_refs(conn)
    covered = _covered_refs(conn)
    phantom = {r for r in covered if r.startswith(SECTION + ".")} - required
    assert not phantom, f"grounding phantom refs: {sorted(phantom)}"


def test_ra_engines(conn):
    engines = {s.get("engine") for s in _tolerance_sources(conn)}
    assert engines, "grounding expected declared tolerance_source bindings"
    assert engines <= {"neta_table", "mfr"}, f"grounding bad engines {engines}"
    assert "tcc" not in engines


def test_ra_mfr_slot(conn):
    # ground resistance + bolted-connection resistance compare vs design / IEEE 81 / mfr.
    mfr = [s for s in _tolerance_sources(conn) if s.get("engine") == "mfr"]
    assert mfr, "grounding must declare an mfr tolerance_source (ground resistance comparison)"


def test_no_prefilled_windows(conn):
    for s in _schema(conn)["sections"]:
        for c in _controls(s):
            if c.get("tolerance_source"):
                assert "value" not in c, f"grounding.{c['tag']} must not pre-fill a window"


def test_capture_block(conn):
    cap = _schema(conn).get("capture")
    assert isinstance(cap, dict), "grounding missing template capture block"
    modes = set(cap.get("modes", []))
    # cover_attach is universal; no instrument bridge exists for ground testers.
    assert {"field", "cover_attach"} <= modes, f"grounding capture modes {modes}"
    assert "instrument_import" not in modes, "grounding has no instrument bridge -> no instrument_import mode"
    assert cap.get("default") == "field"


def test_cover_attach_section(conn):
    att = _sections(conn)["attachments"]
    assert att.get("kind") == "attachment"
    assert att.get("capture_mode") == "cover_attach"
    kinds = {f.get("value_kind") for f in att.get("fields", [])}
    assert "attachment" in kinds
    assert not att.get("neta_covers"), "attachments must not claim NETA coverage"


def test_no_instrument_import_section(conn):
    imp = [s for s in _schema(conn)["sections"] if s.get("capture_mode") == "instrument_import"]
    assert not imp, "grounding has no instrument bridge; no section should be instrument_import"


def test_ground_resistance_section(conn):
    gr = _sections(conn)["ground_resistance"]
    cols = _controls(gr)
    tags = {c["tag"] for c in cols}
    assert "measured_ohms" in tags, "ground_resistance must measure ohms (fall-of-potential / IEEE 81)"


def test_reversibility(conn):
    _psql("016_grounding_template_down.sql")
    with psycopg.connect(DSN) as c:
        gone = c.execute(
            "select count(*) from records.form_templates where template_code = %s", (CODE,)
        ).fetchone()[0]
        assert gone == 0, f"down migration should remove {CODE}"
        procs = c.execute("select count(*) from records.neta_procedures").fetchone()[0]
        assert procs == 72, "2a procedures must survive the template down"
    _apply()
