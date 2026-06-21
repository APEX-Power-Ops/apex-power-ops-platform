"""ops Chip 3 — recognition ledger: invariants + reversibility (TDD).

Builds on Chips 1 (001), 2 (002), 4 (004). Run against a THROWAWAY ops_test (NOT ops_dev,
which holds the 5,344 Miner apparatus). The fixture chains 001->002->004->005 then down-nukes.

Run (host):
  OPS_DEV_PGPASSWORD=<host pw> \
  OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=<pw> sslmode=disable" \
    uv run --with "psycopg[binary]" --with pytest pytest test_005_recognition_ledger.py -q
"""
import os
import pathlib
import uuid
from decimal import Decimal

import psycopg
import pytest

DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} "
    "sslmode=disable"
)
HERE = pathlib.Path(__file__).parent
UP1, DOWN1 = HERE / "001_identity_skeleton.sql", HERE / "001_identity_skeleton_down.sql"
UP2 = HERE / "002_quote_model.sql"
UP4 = HERE / "004_person_anchor.sql"
UP5, DOWN5 = HERE / "005_recognition_ledger.sql", HERE / "005_recognition_ledger_down.sql"


def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    _exec_file(DOWN1)            # drop schema ops cascade -> clean slate
    _exec_file(UP1); _exec_file(UP2); _exec_file(UP4); _exec_file(UP5)
    yield
    _exec_file(DOWN1)


@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try:
            yield c
        finally:
            c.rollback()


def _seed_recognizable(c, *, status="Complete", is_active=True, frozen=True,
                       scope_active=True, scope_status="In Progress",
                       project_active=True, project_status="Active",
                       quoted_hours=5, quoted_revenue=500):
    """Seed project->scope->scope_quote(blended_rate=100)->apparatus->person. Returns the ids PLUS the
    frozen basis (frozen_at, blended_rate, quoted_hours, quoted_revenue) so raw-insert tests can build
    rows the Task-4 insert trigger accepts. Default basis: blended_rate=100, quoted_revenue=500. NB: the
    Task-5 freeze guard forbids un-freezing — never set is_frozen=false on a frozen seed; pass frozen=False
    or set quote/apparatus values via the params instead."""
    pid = c.execute("insert into ops.projects (project_number, project_name, is_active, status) "
                    "values (%s,'t',%s,%s) returning id",
                    (f"P-{uuid.uuid4().hex[:8]}", project_active, project_status)).fetchone()[0]
    sid = c.execute("insert into ops.scopes (project_id, scope_name, is_active, status) "
                    "values (%s,'s',%s,%s) returning id",
                    (pid, scope_active, scope_status)).fetchone()[0]
    # scope_quote: P3=1000 (onsite), M4=N4=1 -> P4=1000; total_quoted_hours=10 -> blended_rate=100
    c.execute("insert into ops.scope_quote (scope_id, onsite_labor, unit_multiplier, pct_adjust, total_quoted_hours) "
              "values (%s,1000,1,1,10)", (sid,))
    if frozen:
        c.execute("update ops.scope_quote set is_frozen=true, frozen_at=now() where scope_id=%s", (sid,))
    aid = c.execute("insert into ops.apparatus (scope_id, apparatus_designation, status, is_active, "
                    "assessment, quoted_hours, quoted_revenue) values (%s,'A-1',%s,%s,'Pass',%s,%s) returning id",
                    (sid, status, is_active, quoted_hours, quoted_revenue)).fetchone()[0]
    person = c.execute("insert into ops.persons (display_name) values ('Lead') returning person_id").fetchone()[0]
    fz, br = c.execute("select frozen_at, blended_rate from ops.scope_quote where scope_id=%s", (sid,)).fetchone()
    return {"project": pid, "scope": sid, "apparatus": aid, "person": person,
            "frozen_at": fz, "blended_rate": br, "quoted_hours": quoted_hours, "quoted_revenue": quoted_revenue}


def _insert_recognized(c, s, **over):
    """Raw-insert a recognized row consistent with seed s's frozen basis; `over` replaces fields to drive
    one specific CHECK/FK while leaving everything else valid (so the Task-4 trigger passes it through to
    the constraint under test). Returns the new event id when the insert succeeds."""
    cols = dict(apparatus_id=s["apparatus"], scope_id=s["scope"], project_id=s["project"],
                event_type="recognized", recognized_amount=s["quoted_revenue"],
                quoted_hours=s["quoted_hours"], blended_rate=s["blended_rate"],
                basis_frozen_at=s["frozen_at"], actor_person_id=s["person"],
                datasheet_clearance="not_applicable", datasheet_ref=None,
                cx_clearance="not_applicable", cx_ref=None)
    cols.update(over)
    keys = ", ".join(cols.keys()); ph = ", ".join(["%s"] * len(cols))
    return c.execute(f"insert into ops.revenue_recognition_event ({keys}) values ({ph}) returning id",
                     tuple(cols.values())).fetchone()[0]


# ---- Task 1: structure + CHECKs + append-only ----
# These raw-insert negative tests build a basis-consistent row via _insert_recognized and override ONE
# field, so the Task-4 insert trigger (added later) passes the row through to the constraint under test.

def test_event_table_and_enums_exist():
    assert _scalar("select to_regclass('ops.revenue_recognition_event') is not null") is True
    labels = _scalar(
        "select array_agg(e.enumlabel order by e.enumsortorder) from pg_enum e join pg_type t on t.oid=e.enumtypid "
        "join pg_namespace n on n.oid=t.typnamespace where n.nspname='ops' and t.typname='obligation_clearance'")
    assert labels == ["provided", "not_applicable"]


def test_actor_fk_targets_persons(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _insert_recognized(conn, s, actor_person_id=str(uuid.uuid4()))


def test_recognized_requires_both_clearances(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.CheckViolation):       # cx_clearance NULL on a recognized row
        _insert_recognized(conn, s, datasheet_clearance="provided", datasheet_ref="FS-1", cx_clearance=None)


def test_clearance_ref_coherence(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.CheckViolation):       # provided + blank ref
        _insert_recognized(conn, s, datasheet_clearance="provided", datasheet_ref="   ")


def test_append_only_blocks_update_and_delete(conn):
    s = _seed_recognizable(conn)
    eid = _insert_recognized(conn, s)
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update ops.revenue_recognition_event set reason='x' where id=%s", (eid,))
    conn.rollback()
    # Re-seed after rollback: the prior seed and event were rolled back with the failed UPDATE.
    s = _seed_recognizable(conn)
    eid = _insert_recognized(conn, s)
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("delete from ops.revenue_recognition_event where id=%s", (eid,))


# ---- Task 2: approve_and_recognize ----

def _recognize(c, s, ds=("not_applicable", None), cx=("not_applicable", None)):
    return c.execute("select ops.approve_and_recognize(%s,%s,%s,%s,%s,%s)",
                     (s["apparatus"], s["person"], ds[0], ds[1], cx[0], cx[1])).fetchone()[0]


def test_recognize_happy_path(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s, ds=("provided", "FS-1"), cx=("provided", "CX-1"))
    row = conn.execute("select event_type, recognized_amount, quoted_hours, blended_rate, basis_frozen_at, "
                       "actor_person_id from ops.revenue_recognition_event where id=%s", (eid,)).fetchone()
    assert row[0] == "recognized"
    assert row[1] == Decimal("500") and row[2] == Decimal("5") and row[3] == Decimal("100")
    assert row[4] is not None and row[5] == s["person"]
    net = conn.execute("select sum(recognized_amount) from ops.revenue_recognition_event where apparatus_id=%s",
                       (s["apparatus"],)).fetchone()[0]
    assert net == Decimal("500")


def test_recognize_requires_complete(conn):
    s = _seed_recognizable(conn, status="In Progress")
    with pytest.raises(psycopg.errors.RaiseException, match="not testing-complete"):
        _recognize(conn, s)


def test_recognize_assessment_independent(conn):
    s = _seed_recognizable(conn)
    conn.execute("update ops.apparatus set assessment='Fail' where id=%s", (s["apparatus"],))
    eid = _recognize(conn, s)
    assert eid is not None


def test_recognize_requires_frozen_basis(conn):
    s = _seed_recognizable(conn, frozen=False)
    with pytest.raises(psycopg.errors.RaiseException, match="not frozen"):
        _recognize(conn, s)


def test_recognize_requires_valid_quote(conn):
    s = _seed_recognizable(conn, quoted_revenue=None)   # frozen basis, but apparatus has no quoted_revenue
    with pytest.raises(psycopg.errors.RaiseException, match="invalid quote basis"):
        _recognize(conn, s)


def test_recognize_requires_both_clearances_fn(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.RaiseException, match="clearances required"):
        conn.execute("select ops.approve_and_recognize(%s,%s,null,null,%s,%s)",
                     (s["apparatus"], s["person"], "not_applicable", None))


def test_recognize_active_row_gate(conn):
    s = _seed_recognizable(conn, scope_status="Cancelled")
    with pytest.raises(psycopg.errors.RaiseException, match="inactive/cancelled"):
        _recognize(conn, s)


def test_recognize_actor_fk(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute("select ops.approve_and_recognize(%s,%s,%s,%s,%s,%s)",
                     (s["apparatus"], str(uuid.uuid4()), "not_applicable", None, "not_applicable", None))


def test_recognize_idempotent(conn):
    s = _seed_recognizable(conn)
    _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="already recognized"):
        _recognize(conn, s)


# ---- Task 3: reverse_recognition ----

def test_reversal_then_rerecognize(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s)
    rid = conn.execute("select ops.reverse_recognition(%s,%s,%s)", (eid, s["person"], "rework")).fetchone()[0]
    net = conn.execute("select coalesce(sum(recognized_amount),0) from ops.revenue_recognition_event "
                       "where apparatus_id=%s", (s["apparatus"],)).fetchone()[0]
    assert net == Decimal("0")
    rev = conn.execute("select event_type, recognized_amount, reverses_event_id from "
                       "ops.revenue_recognition_event where id=%s", (rid,)).fetchone()
    assert rev[0] == "reversal" and rev[1] == Decimal("-500") and rev[2] == eid
    eid2 = _recognize(conn, s)   # re-recognition allowed at net 0
    assert eid2 is not None


def test_reversal_requires_reason(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="reason required"):
        conn.execute("select ops.reverse_recognition(%s,%s,%s)", (eid, s["person"], "   "))


def test_one_reversal_per_event(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s)
    conn.execute("select ops.reverse_recognition(%s,%s,%s)", (eid, s["person"], "first"))
    with pytest.raises(psycopg.errors.RaiseException, match="already reversed"):
        conn.execute("select ops.reverse_recognition(%s,%s,%s)", (eid, s["person"], "second"))


# ---- Task 4: insert-invariant trigger ----

def _base_recognized_cols(s):
    return ("apparatus_id, scope_id, project_id, event_type, recognized_amount, quoted_hours, blended_rate, "
            "basis_frozen_at, actor_person_id, datasheet_clearance, cx_clearance")


def test_insert_lineage_mismatch(conn):
    s = _seed_recognizable(conn)
    other_scope = _seed_recognizable(conn)["scope"]
    with pytest.raises(psycopg.errors.RaiseException, match="lineage"):
        conn.execute(
            f"insert into ops.revenue_recognition_event ({_base_recognized_cols(s)}) "
            "values (%s,%s,%s,'recognized',500,5,100,now(),%s,'not_applicable','not_applicable')",
            (s["apparatus"], other_scope, s["project"], s["person"]))   # scope_id != apparatus lineage


def test_insert_recognized_requires_complete(conn):
    s = _seed_recognizable(conn, status="In Progress")
    with pytest.raises(psycopg.errors.RaiseException, match="non-complete"):
        conn.execute(
            f"insert into ops.revenue_recognition_event ({_base_recognized_cols(s)}) "
            "values (%s,%s,%s,'recognized',500,5,100,now(),%s,'not_applicable','not_applicable')",
            (s["apparatus"], s["scope"], s["project"], s["person"]))


def test_insert_recognized_amount_must_match_quote(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.RaiseException, match="quoted_revenue"):
        conn.execute(
            f"insert into ops.revenue_recognition_event ({_base_recognized_cols(s)}) "
            "values (%s,%s,%s,'recognized',499,5,100,now(),%s,'not_applicable','not_applicable')",  # 499 != 500
            (s["apparatus"], s["scope"], s["project"], s["person"]))


def test_insert_recognized_snapshot_must_match(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.RaiseException, match="snapshot"):
        conn.execute(
            f"insert into ops.revenue_recognition_event ({_base_recognized_cols(s)}) "
            "values (%s,%s,%s,'recognized',500,5,999,now(),%s,'not_applicable','not_applicable')",  # blended 999 != 100
            (s["apparatus"], s["scope"], s["project"], s["person"]))


def test_insert_reversal_amount_must_equal_negative_original(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="reversal amount"):
        conn.execute(
            "insert into ops.revenue_recognition_event "
            "(apparatus_id, scope_id, project_id, event_type, recognized_amount, actor_person_id, reverses_event_id, reason) "
            "values (%s,%s,%s,'reversal',-499,%s,%s,'bad')",   # -499 != -500
            (s["apparatus"], s["scope"], s["project"], s["person"], eid))
