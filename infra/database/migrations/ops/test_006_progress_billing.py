"""ops Chip 4 -- progress billing: invariants + reversibility (TDD). Throwaway ops_test ONLY."""
import os, pathlib, uuid
from decimal import Decimal
import psycopg, pytest

DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} sslmode=disable")
HERE = pathlib.Path(__file__).parent
UP1, DOWN1 = HERE/"001_identity_skeleton.sql", HERE/"001_identity_skeleton_down.sql"
UP2, UP4, UP5 = HERE/"002_quote_model.sql", HERE/"004_person_anchor.sql", HERE/"005_recognition_ledger.sql"
UP6, DOWN6 = HERE/"006_progress_billing.sql", HERE/"006_progress_billing_down.sql"

def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))

def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    _exec_file(DOWN1)
    for f in (UP1, UP2, UP4, UP5, UP6): _exec_file(f)
    yield
    _exec_file(DOWN1)

@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try: yield c
        finally: c.rollback()

def _set_ctx(c):
    """Mark the txn as inside a billing function so the mutation gate (Task 2) permits raw DML in tests."""
    c.execute("select set_config('ops.billing_ctx','1',true)")

def _seed_recognizable(c, *, pct=0, quoted_hours=5, quoted_revenue=500, status="Complete", is_active=True):
    """project->scope->scope_quote(blended_rate=100, frozen)->apparatus->person. retainage_pct=pct.
    Returns dict(project, scope, apparatus, person)."""
    pid = c.execute("insert into ops.projects (project_number,project_name,is_active,status,retainage_pct) "
                    "values (%s,'t',true,'Active',%s) returning id",
                    (f"P-{uuid.uuid4().hex[:8]}", pct)).fetchone()[0]
    sid = c.execute("insert into ops.scopes (project_id,scope_name,is_active,status) "
                    "values (%s,'s',true,'In Progress') returning id", (pid,)).fetchone()[0]
    c.execute("insert into ops.scope_quote (scope_id,onsite_labor,unit_multiplier,pct_adjust,total_quoted_hours) "
              "values (%s,1000,1,1,10)", (sid,))
    c.execute("update ops.scope_quote set is_frozen=true, frozen_at=now() where scope_id=%s", (sid,))
    aid = c.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,is_active,assessment,"
                    "quoted_hours,quoted_revenue) values (%s,'A-1',%s,%s,'Pass',%s,%s) returning id",
                    (sid, status, is_active, quoted_hours, quoted_revenue)).fetchone()[0]
    person = c.execute("insert into ops.persons (display_name) values ('Lead') returning person_id").fetchone()[0]
    return {"project": pid, "scope": sid, "apparatus": aid, "person": person}

def _recognize(c, s):
    """Recognize the seeded apparatus via the Chip 3 gated function (provided clearances). Returns event id."""
    return c.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
                     (s["apparatus"], s["person"])).fetchone()[0]


# ---- Task 1: schema structure ----

def test_tables_exist(conn):
    for t in ("billing_application", "billing_application_line", "billing_application_draft"):
        assert conn.execute("select to_regclass(%s)", (f"ops.{t}",)).fetchone()[0] is not None

def test_enum_exists(conn):
    labels = conn.execute(
        "select array_agg(e.enumlabel order by e.enumsortorder) from pg_enum e "
        "join pg_type t on t.oid=e.enumtypid join pg_namespace n on n.oid=t.typnamespace "
        "where n.nspname='ops' and t.typname='billing_application_status'").fetchone()[0]
    assert labels == ["issued", "voided"]

def test_retainage_pct_column_exists(conn):
    col = conn.execute(
        "select data_type, column_default from information_schema.columns "
        "where table_schema='ops' and table_name='projects' and column_name='retainage_pct'").fetchone()
    assert col is not None
    assert col[0] == "numeric"

def test_retainage_pct_bounds(conn):
    s = _seed_recognizable(conn)
    # pct=0 is valid (seeded above); pct >= 1 violates the CHECK
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("update ops.projects set retainage_pct=1.0 where id=%s", (s["project"],))

def test_retainage_pct_negative_rejected(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("update ops.projects set retainage_pct=-0.001 where id=%s", (s["project"],))

def test_retainage_pct_below_one_accepted(conn):
    s = _seed_recognizable(conn)
    conn.execute("update ops.projects set retainage_pct=0.10000 where id=%s", (s["project"],))
    val = conn.execute("select retainage_pct from ops.projects where id=%s", (s["project"],)).fetchone()[0]
    assert val == Decimal("0.10000")

def test_withheld_cap_check(conn):
    _set_ctx(conn)
    s = _seed_recognizable(conn); _recognize(conn, s)
    # raw header with withheld > positive_gross must violate ck_billapp_withheld_cap
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into ops.billing_application "
            "(project_id,application_no,status,period_through,external_invoice_ref,"
            "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
            "values (%s,1,'issued',current_date,'INV',5,500,500,600,-100,%s)",
            (s["project"], s["person"]))

def test_billapp_ref_nonblank_check(conn):
    _set_ctx(conn)
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into ops.billing_application "
            "(project_id,application_no,status,period_through,external_invoice_ref,"
            "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
            "values (%s,1,'issued',current_date,'   ',5,500,500,0,500,%s)",
            (s["project"], s["person"]))

def test_billapp_void_shape_check(conn):
    _set_ctx(conn)
    s = _seed_recognizable(conn)
    # voided status but missing voided_at/voided_by/void_reason
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into ops.billing_application "
            "(project_id,application_no,status,period_through,external_invoice_ref,"
            "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
            "values (%s,1,'voided',current_date,'INV-VOID',5,500,500,0,500,%s)",
            (s["project"], s["person"]))

def test_billapp_net_check(conn):
    _set_ctx(conn)
    s = _seed_recognizable(conn)
    # net_invoiced arithmetic wrong: 500 - 0 + 0 + 0 != 400
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into ops.billing_application "
            "(project_id,application_no,status,period_through,external_invoice_ref,"
            "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
            "values (%s,1,'issued',current_date,'INV-BAD-NET',5,500,500,0,400,%s)",
            (s["project"], s["person"]))

def test_billapp_retainage_nonneg_check(conn):
    _set_ctx(conn)
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into ops.billing_application "
            "(project_id,application_no,status,period_through,external_invoice_ref,"
            "billable_hours,gross_amount,positive_gross,retainage_withheld,retainage_released,net_invoiced,actor_person_id) "
            "values (%s,1,'issued',current_date,'INV-NEG-WH',5,500,500,-10,0,510,%s)",
            (s["project"], s["person"]))

def test_uq_billapp_issued_ref(conn):
    """Two issued apps on the same project with the same invoice ref are rejected."""
    _set_ctx(conn)
    s = _seed_recognizable(conn)
    conn.execute(
        "insert into ops.billing_application "
        "(project_id,application_no,status,period_through,external_invoice_ref,"
        "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV-DUP',5,500,500,0,500,%s)",
        (s["project"], s["person"]))
    with pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute(
            "insert into ops.billing_application "
            "(project_id,application_no,status,period_through,external_invoice_ref,"
            "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
            "values (%s,2,'issued',current_date,'inv-dup',5,500,500,0,500,%s)",
            (s["project"], s["person"]))

def test_uq_billline_active_event(conn):
    """A second active line for the same recognition event is rejected."""
    _set_ctx(conn)
    s = _seed_recognizable(conn); eid = _recognize(conn, s)
    # insert a valid billing_application first
    app_id = conn.execute(
        "insert into ops.billing_application "
        "(project_id,application_no,status,period_through,external_invoice_ref,"
        "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV-LINE-UQ',5,500,500,0,500,%s) returning id",
        (s["project"], s["person"])).fetchone()[0]
    conn.execute(
        "insert into ops.billing_application_line "
        "(application_id,recognition_event_id,event_type,apparatus_id,scope_id,project_id,amount,billable_hours) "
        "values (%s,%s,'recognized',%s,%s,%s,500,5)",
        (app_id, eid, s["apparatus"], s["scope"], s["project"]))
    with pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute(
            "insert into ops.billing_application_line "
            "(application_id,recognition_event_id,event_type,apparatus_id,scope_id,project_id,amount,billable_hours) "
            "values (%s,%s,'recognized',%s,%s,%s,500,5)",
            (app_id, eid, s["apparatus"], s["scope"], s["project"]))

def test_billline_retainage_nonneg_check(conn):
    _set_ctx(conn)
    s = _seed_recognizable(conn); eid = _recognize(conn, s)
    app_id = conn.execute(
        "insert into ops.billing_application "
        "(project_id,application_no,status,period_through,external_invoice_ref,"
        "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV-LNEG',5,500,500,0,500,%s) returning id",
        (s["project"], s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into ops.billing_application_line "
            "(application_id,recognition_event_id,event_type,apparatus_id,scope_id,project_id,"
            "amount,billable_hours,retainage_withheld) "
            "values (%s,%s,'recognized',%s,%s,%s,500,5,-10)",
            (app_id, eid, s["apparatus"], s["scope"], s["project"]))

def test_draft_fk_to_project(conn):
    _set_ctx(conn)
    s = _seed_recognizable(conn)
    draft_id = conn.execute(
        "insert into ops.billing_application_draft "
        "(project_id,period_through,actor_person_id) values (%s,current_date,%s) returning id",
        (s["project"], s["person"])).fetchone()[0]
    assert draft_id is not None

def test_draft_rejects_bad_project_fk(conn):
    _set_ctx(conn)
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute(
            "insert into ops.billing_application_draft "
            "(project_id,period_through,actor_person_id) values (%s,current_date,%s)",
            (str(uuid.uuid4()), s["person"]))


# ---- Task 2: mutation gate + immutability triggers ----

def test_gate_blocks_unflagged_insert(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException):   # no _set_ctx -> gate rejects
        conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
                     "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
                     "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s)", (s["project"], s["person"]))

def test_header_delete_blocked_with_ctx(conn):
    _set_ctx(conn); s = _seed_recognizable(conn); _recognize(conn, s)
    aid = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("delete from ops.billing_application where id=%s", (aid,))

def test_illegal_header_update_blocked(conn):
    _set_ctx(conn); s = _seed_recognizable(conn); _recognize(conn, s)
    aid = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update ops.billing_application set gross_amount=999 where id=%s", (aid,))


def test_down_up_clean():
    """DOWN6 + UP6 round-trip: tables still resolve after reapplication."""
    _exec_file(DOWN6)
    assert _scalar("select to_regclass('ops.billing_application')") is None
    assert _scalar("select to_regclass('ops.billing_application_line')") is None
    assert _scalar("select to_regclass('ops.billing_application_draft')") is None
    # Chips 1/2/3/4 intact
    assert _scalar("select to_regclass('ops.revenue_recognition_event')") is not None
    assert _scalar("select to_regclass('ops.apparatus')") is not None
    # retainage_pct column gone after down
    col = _scalar(
        "select column_name from information_schema.columns "
        "where table_schema='ops' and table_name='projects' and column_name='retainage_pct'")
    assert col is None
    _exec_file(UP6)
    assert _scalar("select to_regclass('ops.billing_application')") is not None
    assert _scalar("select to_regclass('ops.billing_application_draft')") is not None
    col2 = _scalar(
        "select column_name from information_schema.columns "
        "where table_schema='ops' and table_name='projects' and column_name='retainage_pct'")
    assert col2 == "retainage_pct"


# ---- Task 3: record/issue positive-branch sweep + flag containment ----

def _issue(c, project, person, period="current_date", ref="'INV-1'", exclude="'{}'::uuid[]", draw=0):
    return c.execute(f"select ops.record_billing_application(%s,%s,{period},{ref},{exclude},{draw})",
                     (project, person)).fetchone()[0]


def test_single_apparatus_issue(conn):
    s = _seed_recognizable(conn, quoted_revenue=500, quoted_hours=5); _recognize(conn, s)
    app = _issue(conn, s["project"], s["person"])
    row = conn.execute("select status,application_no,gross_amount,positive_gross,billable_hours,net_invoiced "
                       "from ops.billing_application where id=%s", (app,)).fetchone()
    assert row[0] == "issued" and row[1] == 1
    assert row[2] == Decimal("500.00") and row[3] == Decimal("500.00")
    assert row[4] == Decimal("5.00") and row[5] == Decimal("500.00")
    assert conn.execute("select count(*) from ops.billing_application_line where application_id=%s",(app,)).fetchone()[0]==1


def test_nothing_to_bill_raises(conn):
    s = _seed_recognizable(conn)  # recognized NOTHING
    with pytest.raises(psycopg.errors.RaiseException):
        _issue(conn, s["project"], s["person"])


def test_period_cutoff_excludes_future_recognition(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    # period_through in the past (yesterday Phoenix) excludes today's recognition -> nothing to bill
    with pytest.raises(psycopg.errors.RaiseException):
        _issue(conn, s["project"], s["person"], period="current_date - 1")


def test_application_no_sequential(conn):
    s = _seed_recognizable(conn); _recognize(conn, s); _issue(conn, s["project"], s["person"], ref="'INV-1'")
    # second recognizable apparatus in same project
    a2 = conn.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,is_active,assessment,"
        "quoted_hours,quoted_revenue) values (%s,'A-2','Complete',true,'Pass',5,500) returning id",(s["scope"],)).fetchone()[0]
    conn.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(a2,s["person"]))
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'")
    assert conn.execute("select application_no from ops.billing_application where id=%s",(app2,)).fetchone()[0]==2


def test_flag_containment_success(conn):
    s = _seed_recognizable(conn); _recognize(conn, s); _issue(conn, s["project"], s["person"])
    # after the function returns it reset ops.billing_ctx -> a raw insert now is rejected
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
                     "apparatus_id,scope_id,project_id,amount,billable_hours) values "
                     "(gen_random_uuid(),gen_random_uuid(),'recognized',%s,%s,%s,1,1)",
                     (s["apparatus"], s["scope"], s["project"]))


def test_flag_containment_exception_savepoint(conn):
    s = _seed_recognizable(conn)  # nothing recognized -> issue raises
    conn.execute("savepoint sp")
    try: _issue(conn, s["project"], s["person"])
    except psycopg.errors.RaiseException: pass
    conn.execute("rollback to savepoint sp")
    with pytest.raises(psycopg.errors.RaiseException):  # flag cleared by subtxn rollback
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
                     "apparatus_id,scope_id,project_id,amount,billable_hours) values "
                     "(gen_random_uuid(),gen_random_uuid(),'recognized',%s,%s,%s,1,1)",(s["apparatus"],s["scope"],s["project"]))


# ---- Task 4: header + line insert-integrity + deferred header=sum-lines ----

def test_line_lineage_mismatch_rejected(conn):
    _set_ctx(conn); s = _seed_recognizable(conn); ev = _recognize(conn, s)
    other = _seed_recognizable(conn)
    app = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):  # scope_id of OTHER seed mismatches the event
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
            "apparatus_id,scope_id,project_id,amount,billable_hours) values (%s,%s,'recognized',%s,%s,%s,500,5)",
            (app, ev, s["apparatus"], other["scope"], s["project"]))


def test_header_neq_sum_lines_deferred_fires(conn):
    # an issued app with header gross != sum lines must fail at COMMIT.
    # Uses a fresh connection so conn.transaction() issues a real BEGIN/COMMIT
    # (the deferred constraint fires at COMMIT, not at savepoint release).
    # The seed is done on the main conn (rolled back at teardown; ops_test is throwaway),
    # but the failing billing inserts run on a fresh connection within a real txn block.
    s = _seed_recognizable(conn); ev = _recognize(conn, s)
    # Flush seed to ops_test (visible to other connections) -- ops_test is throwaway
    conn.commit()
    try:
        with psycopg.connect(DSN) as c2:
            with pytest.raises(psycopg.errors.RaiseException):
                with c2.transaction():
                    c2.execute("select set_config('ops.billing_ctx','1',true)")
                    app = c2.execute(
                        "insert into ops.billing_application (project_id,application_no,status,period_through,"
                        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
                        "values (%s,1,'issued',current_date,'INV',5,999,999,999,%s) returning id",
                        (s["project"],s["person"])).fetchone()[0]
                    c2.execute(
                        "insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
                        "apparatus_id,scope_id,project_id,amount,billable_hours) values (%s,%s,'recognized',%s,%s,%s,500,5)",
                        (app, ev, s["apparatus"], s["scope"], s["project"]))
    finally:
        # Rollback the seed data left on conn (ops_test is throwaway; belt+suspenders)
        conn.rollback()
