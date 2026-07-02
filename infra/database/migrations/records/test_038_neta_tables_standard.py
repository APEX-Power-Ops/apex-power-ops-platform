"""TDD - records MTS-accommodation Chip A: standard-key records.neta_tables (mig 038).

The Chip-2a seed (006) loaded neta_tables deduped globally by table_number, so ATS-100.1
and MTS-100.1 collapsed into one row. This migration adds a `standard` column, swaps the
unique key to (standard, table_number), and reseeds BOTH standards verbatim from the two
per-standard extracts. The standard dimension is the foundation the ATS/MTS flag swaps.

RED until gen_038_neta_tables_standard.py emits 038_neta_tables_standard.sql. Run PER-CHIP:
  RECORDS_DEV_PGPASSWORD=... uv run --no-project --directory <records-dir> \
    --with "psycopg[binary]" --with pytest pytest test_038_neta_tables_standard.py -q
"""
import json
import os
import subprocess

import psycopg
import pytest

import _dbtest

HERE = os.path.dirname(os.path.abspath(__file__))
DSN = _dbtest.dsn()
DATA = _dbtest.neta_data_dir()


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


def _src(std):
    fn = "NETA-ATS-2025-tables-extracted.json" if std == "ats" else "NETA-MTS-2023-tables-extracted.json"
    d = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
    return d["tables"]


@pytest.fixture(scope="module")
def conn():
    _psql("038_neta_tables_standard_down.sql")
    _psql("038_neta_tables_standard.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def test_standard_column_exists(conn):
    row = conn.execute(
        "select 1 from information_schema.columns where table_schema='records' "
        "and table_name='neta_tables' and column_name='standard'"
    ).fetchone()
    assert row, "neta_tables.standard column missing"


def test_both_standards_seeded_to_source_counts(conn):
    got = dict(conn.execute(
        "select standard::text, count(*) from records.neta_tables group by standard"
    ).fetchall())
    assert got.get("ats") == len(_src("ats")), f"ats table count {got.get('ats')} != source {len(_src('ats'))}"
    assert got.get("mts") == len(_src("mts")), f"mts table count {got.get('mts')} != source {len(_src('mts'))}"


def test_total_rows_match_source(conn):
    def src_rows(std):
        return sum(len(t.get("data") or t.get("rows") or []) for t in _src(std).values())
    got = dict(conn.execute(
        "select standard::text, sum(jsonb_array_length(rows)) from records.neta_tables group by standard"
    ).fetchall())
    assert int(got["ats"]) == src_rows("ats"), f"ats rows {got['ats']} != source {src_rows('ats')}"
    assert int(got["mts"]) == src_rows("mts"), f"mts rows {got['mts']} != source {src_rows('mts')}"


def test_same_number_coexists_across_standards(conn):
    # 100.1 must now exist for BOTH standards (the dedupe collapse is gone)
    stds = {r[0] for r in conn.execute(
        "select standard::text from records.neta_tables where table_number='100.1'"
    ).fetchall()}
    assert stds == {"ats", "mts"}, f"100.1 standards present: {stds}"


def test_standard_dimension_is_meaningful(conn):
    # At least one shared table_number must carry DIFFERENT values per standard —
    # otherwise the standard split would be pointless. (e.g. oil limits: new vs service-aged.)
    diffs = conn.execute(
        "select count(*) from ("
        "  select table_number from records.neta_tables where standard='ats' "
        "  intersect select table_number from records.neta_tables where standard='mts') shared "
        "join lateral ("
        "  select (a.rows = m.rows) eq from records.neta_tables a, records.neta_tables m "
        "  where a.standard='ats' and m.standard='mts' "
        "  and a.table_number=shared.table_number and m.table_number=shared.table_number) d on true "
        "where d.eq = false"
    ).fetchone()[0]
    assert diffs > 0, "no shared table differs between ATS and MTS — standard split is inert"


def test_unique_is_standard_scoped(conn):
    # the (standard, table_number) unique exists; the old global one is gone
    cons = {r[0] for r in conn.execute(
        "select conname from pg_constraint where conrelid='records.neta_tables'::regclass and contype='u'"
    ).fetchall()}
    assert "uq_neta_tables_std_number" in cons, cons
    assert "uq_neta_tables_number" not in cons, cons
