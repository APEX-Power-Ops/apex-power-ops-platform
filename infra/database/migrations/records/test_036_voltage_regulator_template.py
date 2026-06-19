"""TDD - records Chip 2c: Step Voltage Regulator datasheet (NETA 7.12.1.1).

Slice-3 coverage backlog. Leaf 'voltage_regulator' already exists (Chip 2-shell). NETA 7.12.1.1 =
15 VM + 16 electrical = 31 items (the largest Chip 2c family). NETA dup-lists leakage reactance in
BOTH the VM (A.6) and electrical (B.7) lists - one leakage_reactance section covers both. R-A =
neta_table (IR->100.5) + mfr (winding-R / PF/DF / turns-ratio / reactance) + standard-basis liquid.
Capture = field + cover_attach.

RED until gen_voltage_regulator_template.py emits 036_voltage_regulator_template.sql. Run PER-CHIP.
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
JSON = os.environ.get("NETA_JSON") or (
    r"C:\Users\jjswe\OneDrive\Documents\GitHub\neta-ett-study-material"
    r"\Development\NETA-Data\NETA-Master-Equipment-Table-Enhanced.json"
)
CODE = "ats_voltage_regulator_v1"
SEC = "7.12.1.1"


def _psql(fname):
    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "postgres", "-d", "records_dev",
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}")


@pytest.fixture(scope="module")
def conn():
    _psql("036_voltage_regulator_template_down.sql")
    _psql("036_voltage_regulator_template.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _schema(conn):
    row = conn.execute(
        "select neta_section, field_schema, "
        "(select class_code from records.asset_classes a where a.asset_class_id = t.asset_class_id) "
        "from records.form_templates t where template_code = %s and is_current", (CODE,)
    ).fetchone()
    assert row, f"{CODE} not found"
    sec, fs, leaf = row
    return sec, (json.loads(fs) if isinstance(fs, str) else fs), leaf


def _required():
    d = json.load(open(JSON, encoding="utf-8"))
    e = next(x for x in d["equipment"] if x.get("section") == SEC)
    ats = e.get("ats_data") or {}
    vm = ats.get("visual_mechanical") or []
    el = ats.get("electrical_tests") or []
    return ({f"{SEC}.A.{i + 1}" for i in range(len(vm))}
            | {f"{SEC}.B.{i + 1}" for i in range(len(el))})


def test_template_bound(conn):
    sec, _, leaf = _schema(conn)
    assert sec == SEC and leaf == "voltage_regulator", f"{sec}/{leaf}"


def test_coverage_invariant(conn):
    _, fs, _ = _schema(conn)
    covered = set()
    for s in fs["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = _required()
    assert not (required - covered), f"coverage gap: {sorted(required - covered)}"
    assert not ({r for r in covered if r.startswith(SEC + ".")} - required), "phantom"
    assert len(required) == 31, f"expected 31, got {len(required)}"


def test_leakage_reactance_covers_both_vm_and_electrical(conn):
    """The single leakage_reactance section must satisfy NETA's dup-listed A.6 + B.7."""
    _, fs, _ = _schema(conn)
    lr = next(s for s in fs["sections"] if s["key"] == "leakage_reactance")
    assert {f"{SEC}.A.6", f"{SEC}.B.7"} <= set(lr.get("neta_covers", []))


def test_structure_and_capture(conn):
    _, fs, _ = _schema(conn)
    keys = [s["key"] for s in fs["sections"]]
    for k in ("identification", "visual_mechanical", "insulation_resistance", "turns_ratio",
              "winding_resistance", "control_functions", "insulating_liquid", "attachments"):
        assert k in keys, f"missing section {k}"
    assert len(keys) == len(set(keys)), "duplicate keys"
    cap = fs.get("capture", {})
    assert cap.get("default") == "field" and "cover_attach" in cap.get("modes", [])


def test_ir_acceptance_is_neta_table_100_5(conn):
    """Regulator winding IR resolves to NETA Table 100.5 (transformer-class IR)."""
    _, fs, _ = _schema(conn)
    ir = next(s for s in fs["sections"] if s["key"] == "insulation_resistance")
    r60 = next(c for c in ir["fields"] if c["tag"] == "ir_60s_mohm")
    assert r60.get("tolerance_source", {}).get("table") == "100.5"


def test_ascii_only(conn):
    _, fs, _ = _schema(conn)
    assert json.dumps(fs, ensure_ascii=False).isascii(), "field_schema must be ASCII-only"


def test_reversibility(conn):
    _psql("036_voltage_regulator_template_down.sql")
    with psycopg.connect(DSN) as c:
        assert c.execute("select 1 from records.form_templates where template_code=%s and is_current",
                         (CODE,)).fetchone() is None, "down must remove the template"
    _psql("036_voltage_regulator_template_down.sql")
    _psql("036_voltage_regulator_template.sql")
