"""TDD - records migration 043: records.neta_table_source_links (NETA ETT source-link companion).

A no-excerpt source-lineage companion for records.neta_tables. Schema only -- no seed.
This test is the dry-run gate (G3/G4) for the technical-authority-approved 043. It guards
the two amendments that must NOT regress:
  - Amendment 1: the records lane uses NO RLS/grants -> this table must keep RLS DISABLED.
  - Amendment 2: the bespoke vocab is CHECK-constrained text -> the four old enum TYPES
    must NOT exist.
Plus: FK (RESTRICT) to records.neta_tables, the path-safety / head / value CHECKs actually
reject bad input, the unique locator index, the updated_at trigger, idempotency, reversal.

Run PER-CHIP (never a bulk `pytest .` -- see the records MANIFEST). On the Olares host:
  RECORDS_DEV_PGPASSWORD=<host postgres pw> uv run --no-project \
    --with "psycopg[binary]" --with pytest pytest test_043_neta_table_source_links.py -q
"""
import os
import subprocess

import psycopg
import pytest

import _dbtest

HERE = os.path.dirname(os.path.abspath(__file__))
DSN = _dbtest.dsn()
UP = "043_neta_table_source_links.sql"
DOWN = "043_neta_table_source_links_down.sql"
TBL = "records.neta_table_source_links"

# A fully-valid metadata-only row (FK nullable -> neta_table_id None is valid).
BASE = dict(
    neta_table_id=None,
    standard="ats",
    table_number="100.1",
    source_repo_id="neta-ett-study-material",
    source_repo_head="7f162df1150912d8bbe5024aa352939db5663fa4",
    source_repo_dirty_count=17,
    source_surface="resources_references",
    source_family="ATS-2025",
    canonical_family="ATS_2025",
    source_path="references/ANSI-NETA-ATS-2025_tables appendix.xlsx",
    source_file="ANSI-NETA-ATS-2025_tables appendix.xlsx",
    source_owner="NETA",
    source_use_posture="metadata_only",
    locator_kind="filename",
    locator_value=None,
    lineage_confidence="medium",
    restricted_review_required=True,
    validation_status="candidate",
    review_notes=None,
)
COLS = list(BASE.keys())
_INSERT = (
    f"insert into {TBL} (" + ", ".join(COLS) + ") values (" + ", ".join(f"%({c})s" for c in COLS) + ")"
)


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


def _insert(conn, **over):
    conn.execute(_INSERT, {**BASE, **over})


@pytest.fixture(scope="module")
def conn():
    _psql(DOWN)   # idempotent clean (safe before up)
    _psql(UP)
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def test_table_and_columns(conn):
    cols = dict(conn.execute(
        "select column_name, data_type from information_schema.columns "
        "where table_schema='records' and table_name='neta_table_source_links'"
    ).fetchall())
    assert cols, "table not created"
    for c in ("neta_table_source_link_id", "neta_table_id", "standard", "table_number",
              "source_repo_head", "source_path", "source_file", "source_surface",
              "source_use_posture", "lineage_confidence", "validation_status",
              "review_notes", "created_at", "updated_at"):
        assert c in cols, f"missing column {c}"
    assert cols["neta_table_id"] == "uuid"
    assert cols["standard"] == "USER-DEFINED"          # records.neta_standard_enum
    assert cols["source_surface"] == "text"            # Amendment 2: text, not enum
    assert cols["validation_status"] == "text"
    assert cols["created_at"] == "timestamp with time zone"
    # Amendment 3: the speculative columns must be gone.
    assert "target_domain" not in cols, "Amendment 3: target_domain must be dropped"
    assert "source_checkout_role" not in cols, "Amendment 3: source_checkout_role must be dropped"


def test_fk_to_neta_tables_restrict(conn):
    row = conn.execute(
        "select confrelid::regclass::text, confdeltype from pg_constraint "
        "where conname='fk_neta_table_source_links_table'"
    ).fetchone()
    assert row, "FK constraint missing"
    assert row[0] == "records.neta_tables", f"FK targets {row[0]}"
    assert row[1] == "r", "FK must be ON DELETE RESTRICT"


def test_no_bespoke_enums(conn):
    n = conn.execute(
        "select count(*) from pg_type t join pg_namespace ns on ns.oid=t.typnamespace "
        "where ns.nspname='records' and t.typname = any(%s)",
        (["neta_source_surface_enum", "neta_source_use_posture_enum",
          "neta_lineage_confidence_enum", "neta_source_link_validation_status_enum"],),
    ).fetchone()[0]
    assert n == 0, "Amendment 2: bespoke vocab must be CHECK-constrained text, not enum types"


# Stack-position assertion (mig 043/044): valid through mig 044; migration 045 (Gate 3) enables RLS by design. Run via the incremental runner, not standalone against a post-045 records_dev.
def test_rls_disabled(conn):
    rls = conn.execute(f"select relrowsecurity from pg_class where oid='{TBL}'::regclass").fetchone()[0]
    assert rls is False, "Amendment 1: records lane uses no RLS; this table must not enable it"


def test_unique_locator_index_present(conn):
    n = conn.execute(
        "select count(*) from pg_indexes where schemaname='records' "
        "and tablename='neta_table_source_links' and indexname=%s",
        ("uq_neta_table_source_links_source_locator",),
    ).fetchone()[0]
    assert n == 1, "unique locator index missing"


def test_valid_row_inserts(conn):
    _insert(conn, source_path="references/valid-ok.xlsx", locator_value="ok")
    got = conn.execute(
        f"select source_use_posture, lineage_confidence, validation_status, restricted_review_required "
        f"from {TBL} where source_path='references/valid-ok.xlsx'"
    ).fetchone()
    assert got == ("metadata_only", "medium", "candidate", True), got


def test_fk_behavior(conn):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _insert(conn, neta_table_id="00000000-0000-0000-0000-000000000000",
                source_path="references/fk-bad.xlsx", locator_value="fkbad")
    tid = conn.execute(
        "select neta_table_id from records.neta_tables where standard='ats' and table_number='100.1'"
    ).fetchone()[0]
    _insert(conn, neta_table_id=tid, source_path="references/fk-good.xlsx", locator_value="fkgood")
    assert conn.execute(
        f"select neta_table_id from {TBL} where source_path='references/fk-good.xlsx'"
    ).fetchone()[0] == tid


@pytest.mark.parametrize("case,over", [
    ("abs_drive",       {"source_path": "C:\\bad\\x.xlsx"}),
    ("abs_unix",        {"source_path": "/etc/passwd"}),
    ("traversal",       {"source_path": "a/../b.xlsx"}),
    ("dotenv",          {"source_path": "config/.env"}),
    ("dotgit",          {"source_path": ".git/config"}),
    ("file_with_slash", {"source_file": "sub/x.xlsx"}),
    ("head_nothex",     {"source_repo_head": "zzzznothex"}),
    ("head_short",      {"source_repo_head": "7f162df"}),
    ("neg_dirty",       {"source_repo_dirty_count": -1}),
    ("standard_ecs",    {"standard": "ecs"}),       # valid enum label, rejected by CHECK
    ("surface_bogus",   {"source_surface": "bogus"}),
    ("posture_bogus",   {"source_use_posture": "nope"}),
    ("confidence_bogus", {"lineage_confidence": "nope"}),
    ("status_bogus",    {"validation_status": "nope"}),
    ("review_too_long", {"review_notes": "x" * 2001}),
])
def test_check_constraints_reject(conn, case, over):
    # unique source_path / locator per case so the intended CHECK (not a unique clash) fires
    payload = {"source_path": f"references/ck-{case}.xlsx", "locator_value": case, **over}
    with pytest.raises(psycopg.errors.CheckViolation):
        _insert(conn, **payload)


def test_unique_locator_enforced(conn):
    _insert(conn, source_path="references/uniq.xlsx", locator_value="L1")
    with pytest.raises(psycopg.errors.UniqueViolation):
        _insert(conn, source_path="references/uniq.xlsx", locator_value="L1")


def test_updated_at_trigger(conn):
    assert conn.execute(
        "select 1 from pg_trigger where tgname='trg_neta_table_source_links_updated_at' "
        "and not tgisinternal"
    ).fetchone(), "updated_at trigger missing"
    _insert(conn, source_path="references/trg.xlsx", locator_value="T1")
    c_at, u_at = conn.execute(
        f"select created_at, updated_at from {TBL} where source_path='references/trg.xlsx'"
    ).fetchone()
    conn.execute(f"update {TBL} set review_notes='touched' where source_path='references/trg.xlsx'")
    u2 = conn.execute(
        f"select updated_at from {TBL} where source_path='references/trg.xlsx'"
    ).fetchone()[0]
    assert u2 > u_at >= c_at, "updated_at must advance on UPDATE"


def test_idempotent_up(conn):
    _psql(UP)  # CREATE ... IF NOT EXISTS + DROP/CREATE TRIGGER -> no error, no data loss
    assert conn.execute(f"select to_regclass('{TBL}') is not null").fetchone()[0]


def test_reversibility(conn):
    _psql(DOWN)
    with psycopg.connect(DSN) as c:
        assert c.execute(f"select to_regclass('{TBL}')").fetchone()[0] is None, "down must drop the table"
        assert c.execute("select to_regclass('records.neta_tables')").fetchone()[0] is not None, \
            "down must not touch records.neta_tables"
    _psql(DOWN)
    _psql(UP)
