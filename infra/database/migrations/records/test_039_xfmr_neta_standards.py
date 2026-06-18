"""TDD - records MTS-accommodation Chip B PILOT: ats_liquid_xfmr_v1 standard-aware (mig 039).

Proves the ATS/MTS flag mechanism on ONE sheet before the 33-sheet scale-out:
  * field_schema.neta_standards = ["ats","mts"]
  * each section.neta_covers : flat list -> {"ats":[...], "mts":[...]}  (per-standard coverage)
  * the NETA coverage invariant runs PER STANDARD against the seeded neta_test_items
    (ATS 39 items + MTS 34 items for 7.2.2 — both fully covered, no phantom)
  * acceptance (Table 100.5) resolves against the standard-keyed neta_tables (mig 038)

RED until gen_039_xfmr_neta_standards.py emits 039_xfmr_neta_standards_pilot.sql. Run PER-CHIP:
  RECORDS_DEV_PGPASSWORD=... uv run --no-project --with "psycopg[binary]" --with pytest \
    pytest test_039_xfmr_neta_standards.py -q
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
CODE = "ats_liquid_xfmr_v1"
SEC = "7.2.2"
# pre-039 baseline for the liquid sheet: 012 (fresh) -> 020 (capture) -> 021 (PF readings)
PREREQ = [
    "012_xfmr_datasheet_templates_down.sql", "012_xfmr_datasheet_templates.sql",
    "020_xfmr_capture_mode.sql", "021_xfmr_pf_readings.sql",
]


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
    for f in PREREQ:
        _psql(f)
    _psql("039_xfmr_neta_standards_pilot.sql")


@pytest.fixture(scope="module")
def conn():
    _apply()
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _schema(conn):
    fs = conn.execute(
        "select field_schema from records.form_templates where template_code=%s and is_current",
        (CODE,)
    ).fetchone()[0]
    return json.loads(fs) if isinstance(fs, str) else fs


def _required(conn, std):
    rows = conn.execute(
        "select ti.category, ti.item_number from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section=%s and ti.standard=%s "
        "and ti.category in ('visual_mechanical','electrical')", (SEC, std)
    ).fetchall()
    out = set()
    for cat, num in rows:
        out.add(f"{SEC}.{'A' if cat == 'visual_mechanical' else 'B'}.{num}")
    return out


def _covered(conn, std):
    cov = set()
    for s in _schema(conn)["sections"]:
        nc = s.get("neta_covers") or {}
        if isinstance(nc, dict):
            cov |= set(nc.get(std, []))
    return cov


def test_neta_standards_declared(conn):
    assert _schema(conn).get("neta_standards") == ["ats", "mts"]


def test_neta_covers_is_standard_map(conn):
    for s in _schema(conn)["sections"]:
        nc = s.get("neta_covers")
        assert isinstance(nc, dict) and {"ats", "mts"} <= set(nc), \
            f"{s['key']}: neta_covers must be an {{ats,mts}} map, got {type(nc).__name__}"
        assert s.get("standards") == ["ats", "mts"], f"{s['key']} missing standards tag"


def test_per_standard_coverage_invariant(conn):
    for std, n in (("ats", 39), ("mts", 34)):
        req = _required(conn, std)
        cov = _covered(conn, std)
        assert len(req) == n, f"{std} expected {n} required refs, got {len(req)}"
        assert req - cov == set(), f"{std} silent drops: {sorted(req - cov)}"
        phantom = {r for r in cov if r.startswith(SEC + ".")} - req
        assert not phantom, f"{std} phantom refs: {sorted(phantom)}"


def test_ats_coverage_unregressed(conn):
    # the ATS coverage that 012 established must survive the patch untouched
    assert _required(conn, "ats") - _covered(conn, "ats") == set()


def test_acceptance_resolves_per_standard(conn):
    # IR still cites Table 100.5; both standards' 100.5 now exist in neta_tables (mig 038)
    ir = next(s for s in _schema(conn)["sections"] if s["key"] == "insulation_resistance")
    tables = {c.get("tolerance_source", {}).get("table")
              for c in ir.get("table", {}).get("columns", [])}
    assert "100.5" in tables, f"IR must cite Table 100.5, got {tables}"
    stds = {r[0] for r in conn.execute(
        "select standard::text from records.neta_tables where table_number='100.5'").fetchall()}
    assert stds == {"ats", "mts"}, f"100.5 must exist for both standards, got {stds}"


def test_reversibility(conn):
    _psql("039_xfmr_neta_standards_pilot_down.sql")
    with psycopg.connect(DSN) as c:
        fs = c.execute(
            "select field_schema from records.form_templates where template_code=%s and is_current",
            (CODE,)
        ).fetchone()[0]
        fs = json.loads(fs) if isinstance(fs, str) else fs
        assert "neta_standards" not in fs, "down must remove neta_standards"
        assert isinstance(fs["sections"][1].get("neta_covers"), list), \
            "down must restore flat neta_covers list"
    _apply()
