"""TDD — Records Chip 2-backfill: leaf<->NETA-procedure links + procedure xref graph.

Applies 008 (tables) + 009 (seed) to records_dev and asserts:
  * asset_class_neta_procedure — every active leaf linked; the approved grain
    (cb_lv->3, switch_disconnect->7, load_tap_changer->7.12.3, mcc_mv->7.16.2.2);
    exactly one is_primary per leaf; NO link to a RESERVED (0-item) procedure.
  * neta_procedure_xref — the 2 MCC crossref graphs (4 edges each) with resolution
    (7.5.1.1 resolves to a procedure; the category-level 7.1 stays unresolved);
    the in_accordance scrape (LTC 7.12.3 -> 7.2.2, resolved).
  * reversibility drops the backfill tables, leaving 2a procedures intact.

Assumes records_dev has Chip 1 + 2a (neta_procedures) + 2-shell (asset_classes) applied.
RED until gen_backfill_seed.py emits 009_backfill_seed.sql. Run:
  $env:PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_008_backfill.py
"""
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

RESERVED = ("7.10.4", "7.12.2", "7.18.3", "7.20.2", "7.3.1", "7.27", "7.30")


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
    _psql("008_backfill_tables_down.sql")   # reset (idempotent)
    _psql("008_backfill_tables.sql")
    _psql("009_backfill_seed.sql")


@pytest.fixture(scope="module")
def conn():
    _apply()
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _scalar(conn, sql, params=None):
    return conn.execute(sql, params).fetchone()[0]


def _secs(conn, code):
    return {r[0] for r in conn.execute(
        "select p.section from records.asset_class_neta_procedure l "
        "join records.asset_classes a using (asset_class_id) "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where a.class_code = %s", (code,)).fetchall()}


def test_every_active_leaf_linked(conn):
    unlinked = _scalar(conn,
        "select count(*) from records.asset_classes a where a.parent_class_id is not null "
        "and not exists (select 1 from records.asset_class_neta_procedure l "
        "where l.asset_class_id = a.asset_class_id)")
    assert unlinked == 0, f"{unlinked} leaves have no NETA procedure link"


def test_link_count(conn):
    n = _scalar(conn, "select count(*) from records.asset_class_neta_procedure")
    assert n == 61, f"expected 61 leaf->procedure links, got {n}"


def test_no_link_to_reserved(conn):
    bad = _scalar(conn,
        "select count(*) from records.asset_class_neta_procedure l "
        "join records.neta_procedures p using (neta_procedure_id) "
        "where p.section = any(%s)", (list(RESERVED),))
    assert bad == 0, f"{bad} links point at RESERVED procedures"


def test_one_primary_per_leaf(conn):
    bad = _scalar(conn,
        "select count(*) from (select asset_class_id, "
        "count(*) filter (where is_primary) as p "
        "from records.asset_class_neta_procedure group by asset_class_id) t where t.p <> 1")
    assert bad == 0, "every leaf must have exactly one primary procedure"


def test_grain_spotchecks(conn):
    assert _secs(conn, "cb_lv") == {"7.6.1.2", "7.6.1.1.1", "7.6.1.1.2"}
    assert len(_secs(conn, "switch_disconnect")) == 7
    assert _secs(conn, "load_tap_changer") == {"7.12.3"}
    assert _secs(conn, "mcc_mv") == {"7.16.2.2"}


def test_mcc_crossref_graph(conn):
    n = _scalar(conn,
        "select count(*) from records.neta_procedure_xref x "
        "join records.neta_procedures p on p.neta_procedure_id = x.from_procedure_id "
        "where p.section = '7.16.2.1' and x.ref_kind = 'crossref'")
    assert n == 4, f"7.16.2.1 should have 4 crossref edges, got {n}"
    # 7.5.1.1 is a real procedure -> resolved; the category-level 7.1 has no exact procedure -> NULL
    resolved = _scalar(conn,
        "select x.to_procedure_id is not null from records.neta_procedure_xref x "
        "join records.neta_procedures p on p.neta_procedure_id = x.from_procedure_id "
        "where p.section = '7.16.2.1' and x.to_section = '7.5.1.1'")
    assert resolved is True, "7.16.2.1 -> 7.5.1.1 should resolve to a procedure"
    unresolved = _scalar(conn,
        "select x.to_procedure_id is null from records.neta_procedure_xref x "
        "join records.neta_procedures p on p.neta_procedure_id = x.from_procedure_id "
        "where p.section = '7.16.2.1' and x.to_section = '7.1'")
    assert unresolved is True, "category-level 7.1 should stay unresolved"


def test_in_accordance_scrape(conn):
    # LTC borrows the transformer's insulation/PF methods -> 7.12.3 references 7.2.2
    row = conn.execute(
        "select x.to_procedure_id is not null from records.neta_procedure_xref x "
        "join records.neta_procedures p on p.neta_procedure_id = x.from_procedure_id "
        "where p.section = '7.12.3' and x.to_section = '7.2.2' and x.ref_kind = 'in_accordance'"
    ).fetchone()
    assert row is not None and row[0] is True, "LTC 7.12.3 -> 7.2.2 in_accordance edge missing/unresolved"
    total = _scalar(conn, "select count(*) from records.neta_procedure_xref where ref_kind = 'in_accordance'")
    assert total > 10, f"expected a pervasive in_accordance graph, got {total}"


def test_reversibility(conn):
    _psql("008_backfill_tables_down.sql")
    with psycopg.connect(DSN) as c:
        gone = _scalar(c,
            "select count(*) from information_schema.tables where table_schema='records' "
            "and table_name in ('asset_class_neta_procedure','neta_procedure_xref')")
        assert gone == 0, "backfill tables should be dropped by the down migration"
        procs = _scalar(c, "select count(*) from records.neta_procedures")
        assert procs == 72, "2a procedures must survive the backfill down"
    _apply()
