"""TDD — Records Chip 2a NETA reference layer (records.neta_*).

Applies 005 (tables) + 006 (seed, generated from the NETA master JSON) to the local
records_dev database and asserts the load is ACCURATE against ANSI/NETA ATS-2025:
the full 72-procedure set, the LV power breaker's item counts, the acceptance tables,
and reversibility that leaves the Chip-1 records.* tables intact.

RED until 006_neta_reference_seed.sql exists. Run:
  $env:PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_005_neta_reference.py
DSN pins records_dev explicitly because ambient PGHOST/PGUSER point at Supabase prod.
"""
import os
import subprocess

import psycopg
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", r"C:\Program Files\PostgreSQL\18\bin\psql.exe")
# Pin the LOCAL password — do NOT fall through to ambient PGPASSWORD (it points at
# Supabase prod in this shell's profile).
PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = os.environ.get("RECORDS_DEV_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"
)


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
    _psql("005_neta_reference_tables_down.sql")   # reset (idempotent)
    _psql("005_neta_reference_tables.sql")
    _psql("006_neta_reference_seed.sql")


@pytest.fixture(scope="module")
def conn():
    _apply()
    # autocommit so read queries don't hold ACCESS SHARE locks open — otherwise the
    # reversibility test's DROP (via psql) blocks on this fixture's own connection.
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _scalar(conn, sql, params=None):
    return conn.execute(sql, params).fetchone()[0]


def test_all_72_procedures(conn):
    assert _scalar(conn, "select count(*) from records.neta_procedures") == 72


def test_lv_power_breaker_present(conn):
    row = conn.execute(
        "select name, has_ats, has_mts from records.neta_procedures where section = %s",
        ("7.6.1.2",),
    ).fetchone()
    assert row is not None, "LV power breaker procedure 7.6.1.2 missing"
    assert "Low-Voltage, Power" in row[0]
    assert row[1] is True  # has_ats


def test_lv_ats_visual_mechanical_count(conn):
    n = _scalar(conn,
        "select count(*) from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section='7.6.1.2' and ti.standard='ats' and ti.category='visual_mechanical'")
    assert n == 16, f"expected 16 ATS visual-mechanical items, got {n}"


def test_lv_ats_electrical_count(conn):
    n = _scalar(conn,
        "select count(*) from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section='7.6.1.2' and ti.standard='ats' and ti.category='electrical'")
    assert n == 9, f"expected 9 ATS electrical items, got {n}"


def test_lv_table_refs(conn):
    refs = _scalar(conn,
        "select ats_table_refs from records.neta_procedures where section='7.6.1.2'")
    assert "100.1" in refs and "100.8" in refs, f"LV ats_table_refs = {refs}"


def test_acceptance_tables_loaded(conn):
    total = _scalar(conn, "select count(*) from records.neta_tables")
    assert total >= 40, f"expected the full NETA table set, got {total}"
    # Table 100.1 — insulation-resistance acceptance values (the IR field basis)
    t1 = conn.execute(
        "select title, headers, jsonb_array_length(rows) from records.neta_tables "
        "where table_number='100.1'").fetchone()
    assert t1 is not None, "Table 100.1 missing"
    assert t1[2] >= 6, f"Table 100.1 should carry its rows, got {t1[2]}"
    # parent/child structure preserved
    parent = _scalar(conn,
        "select parent_table_number from records.neta_tables where table_number='100.12.1'")
    assert parent == "100.12"


def test_no_placeholder_descriptions(conn):
    # the crossref mis-seed emitted bare flag words ('required'/'optional') as descriptions
    bad = _scalar(conn,
        "select count(*) from records.neta_test_items "
        "where lower(btrim(description)) in ('required','optional','n/a','')")
    assert bad == 0, f"{bad} test items have placeholder descriptions (crossref mis-seed)"


def test_mcc_crossref_items(conn):
    # MCC procedures are crossref-only: their real content is the 'Refer to Section'
    # composition pointers, carried as category='crossref' items (not garbage).
    for section in ("7.16.2.1", "7.16.2.2"):
        n = _scalar(conn,
            "select count(*) from records.neta_test_items ti "
            "join records.neta_procedures p using (neta_procedure_id) "
            "where p.section=%s and ti.standard='ats' and ti.category='crossref'", (section,))
        assert n == 4, f"{section} should carry 4 ATS crossref items, got {n}"
    first = conn.execute(
        "select description from records.neta_test_items ti "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section='7.16.2.1' and ti.category='crossref' and ti.standard='ats' "
        "and ti.item_number='1'").fetchone()
    assert first and "Refer to Section 7.1" in first[0], f"crossref content wrong: {first}"


def test_reversibility_leaves_chip1_intact(conn):
    # down removes only the 2a objects; the Chip-1 tables survive
    _psql("005_neta_reference_tables_down.sql")
    with psycopg.connect(DSN) as c:
        gone = _scalar(c,
            "select count(*) from information_schema.tables "
            "where table_schema='records' and table_name like 'neta_%'")
        assert gone == 0, "neta_* tables should be dropped by the down migration"
        assets = _scalar(c,
            "select count(*) from information_schema.tables "
            "where table_schema='records' and table_name='assets'")
        assert assets == 1, "Chip-1 records.assets must survive the 2a down"
    _apply()  # restore for any subsequent run
