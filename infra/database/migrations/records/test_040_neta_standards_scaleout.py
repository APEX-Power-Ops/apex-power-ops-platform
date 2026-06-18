"""TDD - records MTS-accommodation Chip B SCALE-OUT: standard-aware datasheets (mig 040).

Generalizes the 039 pilot to every other datasheet. Asserts, for EACH sheet (except the
039-pilot liquid xfmr), the standard-aware v2 shape + the per-standard NETA coverage invariant:
for every standard the sheet declares, all that standard's VM+electrical items for the sheet's
NETA section(s) are covered (no silent drop) with no phantom refs. Placement is auto-authored;
this invariant is the correctness gate.

RED until gen_040_neta_standards_scaleout.py emits 040_neta_standards_scaleout.sql. Run PER-CHIP:
  RECORDS_DEV_PGPASSWORD=... uv run --no-project --with "psycopg[binary]" --with pytest \
    pytest test_040_neta_standards_scaleout.py -q
"""
import json
import os
import re
import subprocess

import psycopg
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", r"C:\Program Files\PostgreSQL\18\bin\psql.exe")
PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = os.environ.get("RECORDS_DEV_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"
)
PILOT = "ats_liquid_xfmr_v1"   # covered by test_039


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
    _psql("040_neta_standards_scaleout.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _sheets(conn):
    return [r[0] for r in conn.execute(
        "select template_code from records.form_templates "
        "where is_current and form_type='neta_datasheet' and template_code <> %s "
        "order by neta_section", (PILOT,)
    ).fetchall()]


def _schema(conn, code):
    fs = conn.execute(
        "select field_schema from records.form_templates where template_code=%s and is_current",
        (code,)
    ).fetchone()[0]
    return json.loads(fs) if isinstance(fs, str) else fs


def _parse_section(ref):
    m = re.match(r"^(.*)\.(?:A|B)\.\d+$", ref)
    return m.group(1) if m else None


def _sheet_sections(fs):
    secs = set()
    for s in fs["sections"]:
        nc = s.get("neta_covers") or {}
        refs = nc.get("ats", []) if isinstance(nc, dict) else nc
        for r in refs:
            ps = _parse_section(r)
            if ps:
                secs.add(ps)
    return sorted(secs)


def _required(conn, sections, std):
    if not sections:
        return set()
    rows = conn.execute(
        "select p.section, ti.category, ti.item_number from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = any(%s) and ti.standard=%s "
        "and ti.category in ('visual_mechanical','electrical')", (sections, std)
    ).fetchall()
    return {f"{sec}.{'A' if cat == 'visual_mechanical' else 'B'}.{num}" for sec, cat, num in rows}


def _covered(fs, std):
    cov = set()
    for s in fs["sections"]:
        nc = s.get("neta_covers") or {}
        if isinstance(nc, dict):
            cov |= set(nc.get(std, []))
    return cov


def test_all_sheets_standard_aware(conn):
    bad = []
    for code in _sheets(conn):
        fs = _schema(conn, code)
        if not fs.get("neta_standards"):
            bad.append(f"{code}: no neta_standards")
            continue
        for s in fs["sections"]:
            if not isinstance(s.get("neta_covers"), dict):
                bad.append(f"{code}.{s['key']}: neta_covers not a map")
    assert not bad, bad


def test_per_standard_coverage_invariant(conn):
    fails = []
    for code in _sheets(conn):
        fs = _schema(conn, code)
        sections = _sheet_sections(fs)
        for std in fs.get("neta_standards", []):
            req = _required(conn, sections, std)
            cov = _covered(fs, std)
            drops = req - cov
            phantom = {r for r in cov if any(r.startswith(s + ".") for s in sections)} - req
            if drops:
                fails.append(f"{code}/{std} SILENT DROPS {sorted(drops)[:4]}")
            if phantom:
                fails.append(f"{code}/{std} PHANTOM {sorted(phantom)[:4]}")
    assert not fails, "\n".join(fails)


def test_mts_declared_iff_mts_items_exist(conn):
    bad = []
    for code in _sheets(conn):
        fs = _schema(conn, code)
        sections = _sheet_sections(fs)
        has_mts = bool(_required(conn, sections, "mts"))
        decl = "mts" in fs.get("neta_standards", [])
        if has_mts != decl:
            bad.append(f"{code}: mts_items={has_mts} but declares={fs.get('neta_standards')}")
    assert not bad, bad


def test_panelboard_is_ats_only(conn):
    # 7.1.2 has no MTS analog (MTS folds panelboards into the switchgear section)
    fs = _schema(conn, "ats_panelboard_v1")
    assert fs["neta_standards"] == ["ats"], fs.get("neta_standards")
    assert _covered(fs, "mts") == set()


def test_ats_coverage_unregressed(conn):
    # the ATS coverage each sheet shipped with must survive the patch
    fails = []
    for code in _sheets(conn):
        fs = _schema(conn, code)
        sections = _sheet_sections(fs)
        if _required(conn, sections, "ats") - _covered(fs, "ats"):
            fails.append(code)
    assert not fails, f"ATS coverage regressed: {fails}"


def test_reversibility(conn):
    _psql("040_neta_standards_scaleout_down.sql")
    with psycopg.connect(DSN) as c:
        fs = _schema(c, "ats_busway_v1")
        assert "neta_standards" not in fs
        assert isinstance(fs["sections"][1].get("neta_covers"), list), "down must restore flat list"
    _psql("040_neta_standards_scaleout.sql")
