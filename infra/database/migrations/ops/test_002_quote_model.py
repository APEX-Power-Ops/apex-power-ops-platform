"""Chip 2 — ops quote model: generated-column accounting + trigger + reversibility (TDD).

Builds on Chip 1 (001). Run with the local-PG password in env:
    $env:PGPASSWORD="..."; uv run --with "psycopg[binary]" --with pytest pytest <thisfile> -v

Asserts (SSoT §5/§5a, Chip 2 spec):
  - standard_hours catalog + scope_quote_line + scope_quote + apparatus quote cols + view exist
  - line_hours = qty * hrs_per_unit  (generated)
  - P3 = sum(4 categories); P4 = P3 * M4 * N4; blended = P4 / J3  (generated)
  - J3 trigger: inserting a line updates scope_quote.total_quoted_hours
  - catalog default != binding: overriding a line's hrs_per_unit leaves the catalog row untouched
  - revenue identity: sum(v_apparatus_quote.quoted_revenue) per scope == P4
  - reversibility: 002 down leaves Chip 1 intact; 002 up restores
"""
import os
import pathlib
import uuid
from decimal import Decimal

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

# This environment's shell exports ambient PGHOST/PGUSER/PGDATABASE pointing at Supabase;
# pin the local ops_test connection explicitly (password only from env).
DSN = os.environ.get("OPS_DEV_ADMIN_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
    "sslmode=disable"
)
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "002 migration tests run on ops_test ONLY"

HERE = pathlib.Path(__file__).parent
UP1 = HERE / "001_identity_skeleton.sql"
DOWN1 = HERE / "001_identity_skeleton_down.sql"
UP2 = HERE / "002_quote_model.sql"
DOWN2 = HERE / "002_quote_model_down.sql"


def _exec_file(path: pathlib.Path) -> None:
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    _exec_file(DOWN1)   # drop schema ops cascade -> nukes chip1 + chip2 (clean slate)
    _exec_file(UP1)     # chip 1
    _exec_file(UP2)     # chip 2 (RED here until the migration exists)
    yield
    _exec_file(DOWN1)


@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try:
            yield c
        finally:
            c.rollback()


def _mk_scope(c) -> str:
    pid = c.execute(
        "insert into ops.projects (project_number, project_name) values (%s, 't') returning id",
        (f"P-{uuid.uuid4().hex[:8]}",),
    ).fetchone()[0]
    return c.execute(
        "insert into ops.scopes (project_id, scope_name) values (%s, 's') returning id",
        (pid,),
    ).fetchone()[0]


# ---- structural ----

def test_catalog_and_quote_tables_exist():
    with psycopg.connect(DSN, autocommit=True) as c:
        t = {r[0] for r in c.execute(
            "select table_name from information_schema.tables where table_schema='ops'"
        )}
    assert {"standard_hours", "scope_quote_line", "scope_quote"} <= t


def test_test_standard_enum_exists():
    labels = {r[0] for r in _query(
        "select e.enumlabel from pg_enum e join pg_type t on t.oid=e.enumtypid "
        "join pg_namespace n on n.oid=t.typnamespace where n.nspname='ops' and t.typname='test_standard'"
    )}
    assert labels == {"ATS", "MTS"}


def test_apparatus_quote_columns_and_view():
    with psycopg.connect(DSN, autocommit=True) as c:
        cols = {r[0] for r in c.execute(
            "select column_name from information_schema.columns "
            "where table_schema='ops' and table_name='apparatus'"
        )}
        views = {r[0] for r in c.execute(
            "select table_name from information_schema.views where table_schema='ops'"
        )}
    assert {"quoted_hours", "quoted_revenue", "quote_line_id"} <= cols
    assert "v_apparatus_quote" in views


# ---- generated columns ----

def test_line_hours_generated(conn):
    sid = _mk_scope(conn)
    h = conn.execute(
        "insert into ops.scope_quote_line (scope_id, apparatus_type, qty, hrs_per_unit) "
        "values (%s, 'X', 3, 2.5) returning line_hours",
        (sid,),
    ).fetchone()[0]
    assert h == Decimal("7.5")


def test_scope_quote_generated(conn):
    sid = _mk_scope(conn)
    row = conn.execute(
        "insert into ops.scope_quote "
        "(scope_id, onsite_labor, offsite_labor, travel, outside_services, "
        " unit_multiplier, pct_adjust, total_quoted_hours) "
        "values (%s, 100, 20, 30, 50, 1.0, 1.10, 8) "
        "returning unadjusted_total, adjusted_total, blended_rate",
        (sid,),
    ).fetchone()
    p3, p4, blended = row
    assert p3 == Decimal("200")                 # 100+20+30+50
    assert p4 == Decimal("220.000")             # 200 * 1.0 * 1.10
    assert blended == Decimal("27.5")           # 220 / 8


def test_blended_rate_null_when_zero_hours(conn):
    sid = _mk_scope(conn)
    blended = conn.execute(
        "insert into ops.scope_quote (scope_id, onsite_labor, total_quoted_hours) "
        "values (%s, 100, 0) returning blended_rate",
        (sid,),
    ).fetchone()[0]
    assert blended is None


# ---- trigger ----

def test_j3_trigger_maintains_total_hours(conn):
    sid = _mk_scope(conn)
    conn.execute("insert into ops.scope_quote (scope_id) values (%s)", (sid,))
    conn.execute("insert into ops.scope_quote_line (scope_id, apparatus_type, qty, hrs_per_unit) values (%s,'A',2,5)", (sid,))
    conn.execute("insert into ops.scope_quote_line (scope_id, apparatus_type, qty, hrs_per_unit) values (%s,'B',1,6)", (sid,))
    j3 = conn.execute("select total_quoted_hours from ops.scope_quote where scope_id=%s", (sid,)).fetchone()[0]
    assert j3 == Decimal("16")   # 2*5 + 1*6


# ---- catalog default != binding ----

def test_catalog_default_is_not_binding(conn):
    conn.execute(
        "insert into ops.standard_hours (apparatus_type, test_standard, default_hours) values ('Widget','ATS',4)"
    )
    sid = _mk_scope(conn)
    # estimator overrides per project: 9 hrs, not the catalog's 4
    conn.execute(
        "insert into ops.scope_quote_line (scope_id, apparatus_type, test_standard, qty, hrs_per_unit, catalog_default_hours) "
        "values (%s,'Widget','ATS',1,9,4)",
        (sid,),
    )
    catalog = conn.execute(
        "select default_hours from ops.standard_hours where apparatus_type='Widget' and test_standard='ATS'"
    ).fetchone()[0]
    assert catalog == Decimal("4")   # untouched by the per-project override


# ---- revenue identity ----

def test_apparatus_revenue_sums_to_p4(conn):
    sid = _mk_scope(conn)
    # scope_quote: P3=1600 (all onsite), M4=N4=1 -> P4=1600; J3 maintained by lines
    conn.execute(
        "insert into ops.scope_quote (scope_id, onsite_labor, unit_multiplier, pct_adjust) values (%s,1600,1,1)",
        (sid,),
    )
    l1 = conn.execute("insert into ops.scope_quote_line (scope_id,apparatus_type,qty,hrs_per_unit) values (%s,'A',2,5) returning id", (sid,)).fetchone()[0]
    l2 = conn.execute("insert into ops.scope_quote_line (scope_id,apparatus_type,qty,hrs_per_unit) values (%s,'B',1,6) returning id", (sid,)).fetchone()[0]
    # J3 now 16 -> blended = 1600/16 = 100
    blended = conn.execute("select blended_rate from ops.scope_quote where scope_id=%s", (sid,)).fetchone()[0]
    assert blended == Decimal("100")
    # explode apparatus, each inheriting its line's hrs
    for (desig, hrs, lid) in [("A1", 5, l1), ("A2", 5, l1), ("B1", 6, l2)]:
        conn.execute(
            "insert into ops.apparatus (scope_id, apparatus_designation, quoted_hours, quote_line_id) values (%s,%s,%s,%s)",
            (sid, desig, hrs, lid),
        )
    total = conn.execute(
        "select sum(quoted_revenue) from ops.v_apparatus_quote where scope_id=%s", (sid,)
    ).fetchone()[0]
    assert total == Decimal("1600")   # (5+5+6) * 100 == P4


# ---- reversibility (Chip 2 down leaves Chip 1 intact) ----

def test_chip2_reversible_without_dropping_chip1():
    _exec_file(DOWN2)
    with psycopg.connect(DSN, autocommit=True) as c:
        ops_tables = {r[0] for r in c.execute(
            "select table_name from information_schema.tables where table_schema='ops'"
        )}
    assert "scope_quote" not in ops_tables        # chip 2 gone
    assert {"projects", "apparatus"} <= ops_tables  # chip 1 intact
    _exec_file(UP2)
    assert _scalar("select 1 from information_schema.tables where table_schema='ops' and table_name='scope_quote'") == 1


# small helper
def _query(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        return c.execute(sql, params).fetchall()
