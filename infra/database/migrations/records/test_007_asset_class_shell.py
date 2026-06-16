"""TDD — Records Chip 2-shell: asset_class family taxonomy (records.asset_classes).

Applies 007 (the 2-level family shell seed) to local records_dev and asserts:
  * 27 NETA-category PARENTS (19 active + 8 future/inactive) + 36 practical LEAF classes = 63
  * 2 levels only (every leaf hangs off a top-level parent — no third level)
  * the NETA anchor is REAL: the parent neta_category set == records.neta_procedures.category set
  * leaves carry no neta_category (resolved via parent — not denormalized)
  * grain spot-checks (breakers 2, instrument-transformers 3, switchgear 5)
  * Safety/JHA is NOT an asset_class (it's form_type=jha)
  * a future parent (ev_charging) is inactive + childless
  * reversibility leaves the Chip-1 records.asset_classes table intact

Assumes records_dev already has Chip-1 (asset_classes) + Chip-2a (neta_procedures) applied.
RED until gen_shell_seed.py emits 007_asset_class_shell.sql. Run:
  $env:PGPASSWORD='...'; uv run --with "psycopg[binary]" --with pytest pytest test_007_asset_class_shell.py
DSN pins records_dev explicitly because ambient PGHOST/PGUSER point at Supabase prod.
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
    _psql("007_asset_class_shell_down.sql")   # reset (idempotent)
    _psql("007_asset_class_shell.sql")


@pytest.fixture(scope="module")
def conn():
    _apply()
    # autocommit so read queries don't hold ACCESS SHARE locks open against the down/up DML
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _scalar(conn, sql, params=None):
    return conn.execute(sql, params).fetchone()[0]


def _codes(conn, sql, params=None):
    return {r[0] for r in conn.execute(sql, params).fetchall()}


def test_parent_and_leaf_counts(conn):
    parents = _scalar(conn, "select count(*) from records.asset_classes where parent_class_id is null")
    leaves = _scalar(conn, "select count(*) from records.asset_classes where parent_class_id is not null")
    assert parents == 27, f"expected 27 NETA-category parents, got {parents}"
    assert leaves == 36, f"expected 36 leaf classes, got {leaves}"


def test_active_inactive_split(conn):
    active_parents = _scalar(conn,
        "select count(*) from records.asset_classes where parent_class_id is null and is_active")
    inactive_parents = _scalar(conn,
        "select count(*) from records.asset_classes where parent_class_id is null and not is_active")
    assert active_parents == 19, f"expected 19 active parents, got {active_parents}"
    assert inactive_parents == 8, f"expected 8 future/inactive parents, got {inactive_parents}"
    inactive_leaves = _scalar(conn,
        "select count(*) from records.asset_classes where parent_class_id is not null and not is_active")
    assert inactive_leaves == 0, "all leaf classes should be active"


def test_two_levels_only(conn):
    # every leaf's parent must itself be a top-level parent (no third level)
    bad = _scalar(conn,
        "select count(*) from records.asset_classes c "
        "join records.asset_classes p on p.asset_class_id = c.parent_class_id "
        "where c.parent_class_id is not null and p.parent_class_id is not null")
    assert bad == 0, f"{bad} leaves hang off a non-top-level parent (>2 levels)"


def test_neta_anchor_is_real(conn):
    # parents carry a neta_category; the set must EXACTLY match the loaded NETA taxonomy
    parent_cats = _codes(conn,
        "select neta_category from records.asset_classes where parent_class_id is null")
    neta_cats = _codes(conn, "select distinct category from records.neta_procedures")
    assert None not in parent_cats, "every parent must carry a neta_category anchor"
    assert parent_cats == neta_cats, (
        f"parent neta_category set != NETA procedure categories; "
        f"only-in-shell={parent_cats - neta_cats}, only-in-neta={neta_cats - parent_cats}")


def test_leaves_have_no_neta_category(conn):
    # leaves resolve category via the parent — they don't denormalize it
    n = _scalar(conn,
        "select count(*) from records.asset_classes "
        "where parent_class_id is not null and neta_category is not null")
    assert n == 0, f"{n} leaves carry a denormalized neta_category"


def test_breaker_grain(conn):
    kids = _codes(conn,
        "select c.class_code from records.asset_classes c "
        "join records.asset_classes p on p.asset_class_id = c.parent_class_id "
        "where p.class_code = 'circuit_breakers'")
    assert kids == {"cb_lv", "cb_mvhv"}, f"breaker leaves = {kids}"
    assert _scalar(conn,
        "select is_active from records.asset_classes where class_code='circuit_breakers'") is True


def test_instrument_transformer_split(conn):
    kids = _codes(conn,
        "select c.class_code from records.asset_classes c "
        "join records.asset_classes p on p.asset_class_id = c.parent_class_id "
        "where p.class_code = 'instrument_transformers'")
    assert kids == {"it_ct", "it_vt", "it_cvt"}, f"instrument-transformer leaves = {kids}"


def test_switchgear_five(conn):
    n = _scalar(conn,
        "select count(*) from records.asset_classes c "
        "join records.asset_classes p on p.asset_class_id = c.parent_class_id "
        "where p.class_code = 'switchgear'")
    assert n == 5, f"expected 5 switchgear leaves, got {n}"


def test_future_parent_inactive_and_childless(conn):
    row = conn.execute(
        "select a.is_active, "
        "(select count(*) from records.asset_classes c where c.parent_class_id = a.asset_class_id) "
        "from records.asset_classes a where a.class_code = 'ev_charging'").fetchone()
    assert row is not None, "ev_charging future parent missing"
    assert row[0] is False, "ev_charging should be inactive"
    assert row[1] == 0, "future parents carry no leaves yet"


def test_safety_is_not_an_asset_class(conn):
    n = _scalar(conn,
        "select count(*) from records.asset_classes where class_code in ('safety', 'jha')")
    assert n == 0, "Safety/JHA is a form_type, not an asset_class"


def test_reversibility_leaves_table_intact(conn):
    _psql("007_asset_class_shell_down.sql")
    with psycopg.connect(DSN) as c:
        gone = _scalar(c,
            "select count(*) from records.asset_classes "
            "where class_code in ('circuit_breakers', 'cb_lv', 'ev_charging')")
        assert gone == 0, "down should remove shell rows at both levels"
        exists = _scalar(c,
            "select count(*) from information_schema.tables "
            "where table_schema='records' and table_name='asset_classes'")
        assert exists == 1, "Chip-1 records.asset_classes table must survive the shell down"
    _apply()  # restore
