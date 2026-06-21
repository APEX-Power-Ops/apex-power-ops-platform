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
    # recognition is stamped now(); a period_through FIRMLY in the past excludes it DETERMINISTICALLY
    # (current_date-1 is flaky near the Phoenix-midnight boundary -- audit finding).
    with pytest.raises(psycopg.errors.RaiseException):
        _issue(conn, s["project"], s["person"], period="'2000-01-01'::date")


def test_monotonic_period_rejected(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-1'", period="current_date")
    a2 = conn.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,is_active,assessment,"
        "quoted_hours,quoted_revenue) values (%s,'A-2','Complete',true,'Pass',5,500) returning id",(s["scope"],)).fetchone()[0]
    conn.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(a2,s["person"]))
    with pytest.raises(psycopg.errors.RaiseException):   # earlier period than a prior issued app
        _issue(conn, s["project"], s["person"], ref="'INV-2'", period="current_date - 5")


def test_exclude_holds_apparatus_back(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException):   # exclude the only recognized apparatus -> nothing to bill
        conn.execute("select ops.record_billing_application(%s,%s,current_date,'INV',array[%s]::uuid[],0)",
                     (s["project"], s["person"], s["apparatus"]))


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
    # DEFERRED-CONSTRAINT TEST IDIOM (audit fix): do the mismatched inserts in THIS conn's txn, then fire the
    # deferred constraint NOW with `set constraints all immediate`. This (a) avoids the savepoint false-green
    # (`with conn.transaction()` is a SAVEPOINT, and deferred constraints fire at top-level COMMIT, not savepoint
    # release) and (b) needs no separate committed connection, so the fixture rollback cleans up -- no ops_test leak.
    _set_ctx(conn); s = _seed_recognizable(conn); ev = _recognize(conn, s)
    app = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,999,999,999,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
        "apparatus_id,scope_id,project_id,amount,billable_hours) values (%s,%s,'recognized',%s,%s,%s,500,5)",
        (app, ev, s["apparatus"], s["scope"], s["project"]))
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("set constraints all immediate")   # header gross 999 != Sigma lines 500 -> fires now


def test_line_withheld_must_match_pct(conn):   # audit: §8.4 positive-branch withheld validation (Task-4 gap)
    _set_ctx(conn); s = _seed_recognizable(conn, pct=Decimal("0.10")); ev = _recognize(conn, s)
    app = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,50,450,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):   # withheld 0 but pct=0.10 on amount 500 -> must be 50.00
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
            "apparatus_id,scope_id,project_id,amount,billable_hours,retainage_withheld) values (%s,%s,'recognized',%s,%s,%s,500,5,0)",
            (app, ev, s["apparatus"], s["scope"], s["project"]))


def test_positive_line_after_reversal_rejected(conn):  # audit: §8.4 branch eligibility (gate-bypassed)
    _set_ctx(conn); s = _seed_recognizable(conn); ev = _recognize(conn, s)
    conn.execute("select ops.reverse_recognition(%s,%s,'x')", (ev, s["person"]))   # event now reversed
    app = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):   # positive line for a now-reversed recognition
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
            "apparatus_id,scope_id,project_id,amount,billable_hours) values (%s,%s,'recognized',%s,%s,%s,500,5)",
            (app, ev, s["apparatus"], s["scope"], s["project"]))


# ---- Task 5: line-grain retainage withholding + explicit capped draw ----

def test_withholding_line_grain(conn):
    s = _seed_recognizable(conn, pct=Decimal("0.10"), quoted_revenue=500); _recognize(conn, s)
    app = _issue(conn, s["project"], s["person"])
    h = conn.execute("select retainage_withheld,net_invoiced from ops.billing_application where id=%s",(app,)).fetchone()
    assert h[0] == Decimal("50.00") and h[1] == Decimal("450.00")  # 500*0.10 withheld; net 450
    ln = conn.execute("select retainage_withheld from ops.billing_application_line where application_id=%s",(app,)).fetchone()
    assert ln[0] == Decimal("50.00")


def test_pure_draw_app_issues(conn):
    s = _seed_recognizable(conn, pct=Decimal("0.10")); _recognize(conn, s); _issue(conn, s["project"], s["person"], ref="'INV-1'")
    # held_to_date is 50; a pure draw of 50 with empty sweep issues
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'", draw=50)
    assert conn.execute("select retainage_drawn,net_invoiced from ops.billing_application where id=%s",(app2,)).fetchone() == (Decimal("50.00"), Decimal("50.00"))


def test_over_draw_rejected(conn):
    s = _seed_recognizable(conn, pct=Decimal("0.10")); _recognize(conn, s); _issue(conn, s["project"], s["person"], ref="'INV-1'")
    with pytest.raises(psycopg.errors.RaiseException):
        _issue(conn, s["project"], s["person"], ref="'INV-2'", draw=999)


# ---- Task 6: credit branch + line-grain auto-release (canonical order) ----

def test_credit_returns_gross_plus_retainage(conn):
    s = _seed_recognizable(conn, pct=Decimal("0.10"), quoted_revenue=500); ev = _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-1'")              # bill: net 450, held 50
    conn.execute("select ops.reverse_recognition(%s,%s,'rework')", (ev, s["person"]))
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'")        # credit
    h = conn.execute("select gross_amount,retainage_released,net_invoiced from ops.billing_application where id=%s",(app2,)).fetchone()
    assert h == (Decimal("-500.00"), Decimal("50.00"), Decimal("-450.00"))  # net-credit = -(net originally billed)
    held = conn.execute("select coalesce(sum(retainage_withheld-retainage_released-retainage_drawn),0) "
                        "from ops.billing_application where project_id=%s and status='issued'",(s["project"],)).fetchone()[0]
    assert held == Decimal("0.00")


def test_pure_credit_app_issues(conn):   # C-1 fix: withheld cap=positive_gross, not LEAST(.,gross)
    s = _seed_recognizable(conn, pct=Decimal("0.10")); ev = _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-1'")
    conn.execute("select ops.reverse_recognition(%s,%s,'x')",(ev,s["person"]))
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'")
    assert conn.execute("select gross_amount from ops.billing_application where id=%s",(app2,)).fetchone()[0] < 0


def test_bill_draw_reverse_no_wedge(conn):  # C-2 fix
    s = _seed_recognizable(conn, pct=Decimal("0.10")); ev = _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-1'")               # held 50
    _issue(conn, s["project"], s["person"], ref="'INV-2'", draw=50)      # held 0
    conn.execute("select ops.reverse_recognition(%s,%s,'x')",(ev,s["person"]))
    app3 = _issue(conn, s["project"], s["person"], ref="'INV-3'")        # credit: released=LEAST(50,0)=0
    h = conn.execute("select retainage_released,net_invoiced from ops.billing_application where id=%s",(app3,)).fetchone()
    assert h == (Decimal("0.00"), Decimal("-500.00"))   # full gross credited; no wedge


def test_credit_amount_negative(conn):
    """§8.4: credit line amount must be < 0 -- trigger enforces this."""
    _set_ctx(conn); s = _seed_recognizable(conn, pct=Decimal("0.10")); ev = _recognize(conn, s)
    app1 = conn.execute(
        "insert into ops.billing_application "
        "(project_id,application_no,status,period_through,external_invoice_ref,"
        "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV-P',5,500,500,50,450,%s) returning id",
        (s["project"], s["person"])).fetchone()[0]
    conn.execute(
        "insert into ops.billing_application_line "
        "(application_id,recognition_event_id,event_type,apparatus_id,scope_id,project_id,"
        "amount,billable_hours,retainage_withheld,retainage_released) "
        "values (%s,%s,'recognized',%s,%s,%s,500,5,50,0)",
        (app1, ev, s["apparatus"], s["scope"], s["project"]))
    # Now reverse
    rev_ev = conn.execute("select ops.reverse_recognition(%s,%s,'test')", (ev, s["person"])).fetchone()[0]
    app2 = conn.execute(
        "insert into ops.billing_application "
        "(project_id,application_no,status,period_through,external_invoice_ref,"
        "billable_hours,gross_amount,positive_gross,retainage_withheld,retainage_released,net_invoiced,actor_person_id) "
        "values (%s,2,'issued',current_date,'INV-C',-5,-500,0,0,50,-450,%s) returning id",
        (s["project"], s["person"])).fetchone()[0]
    # Attempt a credit line with amount > 0 -- must be rejected by the trigger
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute(
            "insert into ops.billing_application_line "
            "(application_id,recognition_event_id,event_type,apparatus_id,scope_id,project_id,"
            "amount,billable_hours,retainage_withheld,retainage_released) "
            "values (%s,%s,'reversal',%s,%s,%s,500,-5,0,50)",
            (app2, rev_ev, s["apparatus"], s["scope"], s["project"]))


def test_sub_cent_credit_skipped(conn):
    """A credit line with amount=0 (round(recognized_amount,2)=0) is rejected by §8.4 trigger.
    Sub-cent reversal events cannot produce valid credit lines -- the amount<0 check enforces this."""
    _set_ctx(conn); s = _seed_recognizable(conn, pct=Decimal("0.10")); ev = _recognize(conn, s)
    # Bill the positive event
    app1 = conn.execute(
        "insert into ops.billing_application "
        "(project_id,application_no,status,period_through,external_invoice_ref,"
        "billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV-P',5,500,500,50,450,%s) returning id",
        (s["project"], s["person"])).fetchone()[0]
    conn.execute(
        "insert into ops.billing_application_line "
        "(application_id,recognition_event_id,event_type,apparatus_id,scope_id,project_id,"
        "amount,billable_hours,retainage_withheld,retainage_released) "
        "values (%s,%s,'recognized',%s,%s,%s,500,5,50,0)",
        (app1, ev, s["apparatus"], s["scope"], s["project"]))
    rev_ev = conn.execute("select ops.reverse_recognition(%s,%s,'sub-cent-test')", (ev, s["person"])).fetchone()[0]
    # Attempt a credit line with amount=0.00 -- trigger must reject (credit amount must be < 0, not zero)
    app2 = conn.execute(
        "insert into ops.billing_application "
        "(project_id,application_no,status,period_through,external_invoice_ref,"
        "billable_hours,gross_amount,positive_gross,retainage_withheld,retainage_released,net_invoiced,actor_person_id) "
        "values (%s,2,'issued',current_date,'INV-SC',0,0,0,0,0,0,%s) returning id",
        (s["project"], s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        # amount=0.00 for a reversal line -- trigger rejects (must be < 0)
        conn.execute(
            "insert into ops.billing_application_line "
            "(application_id,recognition_event_id,event_type,apparatus_id,scope_id,project_id,"
            "amount,billable_hours,retainage_withheld,retainage_released) "
            "values (%s,%s,'reversal',%s,%s,%s,0.00,-5,0,0)",
            (app2, rev_ev, s["apparatus"], s["scope"], s["project"]))


def test_credit_non_excludable(conn):
    """exclude[] does NOT suppress a credit for an already-billed-then-reversed apparatus."""
    s = _seed_recognizable(conn, pct=Decimal("0.10"), quoted_revenue=500); ev = _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-1'")
    conn.execute("select ops.reverse_recognition(%s,%s,'test')", (ev, s["person"]))
    # Issue with exclude=[apparatus] -- credit should still sweep (credits are non-excludable)
    app2 = conn.execute(
        "select ops.record_billing_application(%s,%s,current_date,'INV-2',array[%s]::uuid[],0)",
        (s["project"], s["person"], s["apparatus"])).fetchone()[0]
    row = conn.execute("select gross_amount from ops.billing_application where id=%s", (app2,)).fetchone()
    assert row[0] < 0  # credit swept despite apparatus being in exclude[]


# ---- Task 7: void_billing_application + void-dependency guard + line-cascade ----

def test_void_green_path(conn):
    """Legal issued->voided under ctx: status flips, lines cascade to is_voided=true."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    app = _issue(conn, s["project"], s["person"])
    conn.execute("select ops.void_billing_application(%s,%s,'mis-invoiced')", (app, s["person"]))
    hdr = conn.execute("select status,voided_at,voided_by,void_reason from ops.billing_application where id=%s",
                       (app,)).fetchone()
    assert hdr[0] == "voided"
    assert hdr[1] is not None
    assert hdr[2] == s["person"]
    assert hdr[3] == "mis-invoiced"
    # All lines must be voided
    lines_voided = conn.execute(
        "select bool_and(is_voided) from ops.billing_application_line where application_id=%s",
        (app,)).fetchone()[0]
    assert lines_voided is True


def test_void_releases_events_to_unbilled(conn):
    """After voiding, the event's active line is gone; a second issue can sweep it again."""
    s = _seed_recognizable(conn); ev = _recognize(conn, s)
    app = _issue(conn, s["project"], s["person"])
    conn.execute("select ops.void_billing_application(%s,%s,'mis-invoiced')", (app, s["person"]))
    assert conn.execute(
        "select status from ops.billing_application where id=%s", (app,)).fetchone()[0] == "voided"
    assert conn.execute(
        "select bool_and(is_voided) from ops.billing_application_line where application_id=%s",
        (app,)).fetchone()[0] is True
    # Event is re-billable: a new issue must succeed
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'")
    assert app2 is not None


def test_void_blocked_by_standing_credit(conn):
    """Cannot void app1 when another issued app holds a standing credit against app1's lines."""
    s = _seed_recognizable(conn); ev = _recognize(conn, s)
    app1 = _issue(conn, s["project"], s["person"], ref="'INV-1'")
    # Reverse the recognized event so a credit becomes available
    conn.execute("select ops.reverse_recognition(%s,%s,'x')", (ev, s["person"]))
    # Issue app2 which picks up the standing credit (credit line points at app1's positive event)
    _issue(conn, s["project"], s["person"], ref="'INV-2'")
    # Now try to void app1 -- the standing-credit guard must reject
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("select ops.void_billing_application(%s,%s,'late')", (app1, s["person"]))


def test_void_blocked_when_held_would_go_negative(conn):
    """Voiding a withholding app that was already drawn from makes held go negative.
    The §8.5 deferred held>=0 check catches this (fired by set constraints all immediate)."""
    s = _seed_recognizable(conn, pct=Decimal("0.10"), quoted_revenue=500); _recognize(conn, s)
    app1 = _issue(conn, s["project"], s["person"], ref="'INV-1'")  # held=50
    # Draw all held retainage via a pure-draw app
    _issue(conn, s["project"], s["person"], ref="'INV-2'", draw=50)  # held now 0
    # Void app1 (which had withheld=50): held would become -50 for the project
    # The deferred constraint (held>=0) should fire
    conn.execute("select ops.void_billing_application(%s,%s,'wrong')", (app1, s["person"]))
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("set constraints all immediate")


def test_application_no_burned_after_void(conn):
    """application_no is burned on void: the next issued app gets no=2, not no=1 reused."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    app1 = _issue(conn, s["project"], s["person"], ref="'INV-1'")
    no1 = conn.execute("select application_no from ops.billing_application where id=%s", (app1,)).fetchone()[0]
    assert no1 == 1
    conn.execute("select ops.void_billing_application(%s,%s,'void-for-test')", (app1, s["person"]))
    # Seed a new recognizable apparatus in same project so there is something to bill
    a2 = conn.execute(
        "insert into ops.apparatus (scope_id,apparatus_designation,status,is_active,assessment,"
        "quoted_hours,quoted_revenue) values (%s,'A-2','Complete',true,'Pass',5,500) returning id",
        (s["scope"],)).fetchone()[0]
    conn.execute(
        "select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
        (a2, s["person"]))
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'")
    no2 = conn.execute("select application_no from ops.billing_application where id=%s", (app2,)).fetchone()[0]
    assert no2 == 2  # burned; not reused


def test_dup_ref_blocked(conn):
    """uq_billapp_issued_ref: two simultaneously issued apps with the same ref are blocked."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-DUP'")
    # Seed a second recognizable apparatus to give something to bill
    a2 = conn.execute(
        "insert into ops.apparatus (scope_id,apparatus_designation,status,is_active,assessment,"
        "quoted_hours,quoted_revenue) values (%s,'A-2','Complete',true,'Pass',5,500) returning id",
        (s["scope"],)).fetchone()[0]
    conn.execute(
        "select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
        (a2, s["person"]))
    with pytest.raises(psycopg.errors.UniqueViolation):
        _issue(conn, s["project"], s["person"], ref="'INV-DUP'")


def test_ref_reusable_after_void(conn):
    """After voiding app1 with ref='INV-REUSE', a new issued app can reuse the same ref."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    app1 = _issue(conn, s["project"], s["person"], ref="'INV-REUSE'")
    conn.execute("select ops.void_billing_application(%s,%s,'void-for-reuse')", (app1, s["person"]))
    # Seed a new apparatus to bill
    a2 = conn.execute(
        "insert into ops.apparatus (scope_id,apparatus_designation,status,is_active,assessment,"
        "quoted_hours,quoted_revenue) values (%s,'A-2','Complete',true,'Pass',5,500) returning id",
        (s["scope"],)).fetchone()[0]
    conn.execute(
        "select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
        (a2, s["person"]))
    # Re-use the same ref -- must succeed since app1 is now voided
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-REUSE'")
    assert app2 is not None


# ---- Task 8: draft = intent (record->draft, issue-from-draft, discard) ----

def test_draft_saved_then_issued_fresh(conn):
    """record with null ref saves a draft (no billing_application row); 3-param issue promotes it."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    d = conn.execute("select ops.record_billing_application(%s,%s,current_date,null,'{}'::uuid[],0)",
                     (s["project"], s["person"])).fetchone()[0]
    # Draft row exists; no issued application yet
    assert conn.execute("select count(*) from ops.billing_application_draft where id=%s", (d,)).fetchone()[0] == 1
    assert conn.execute("select count(*) from ops.billing_application where project_id=%s", (s["project"],)).fetchone()[0] == 0
    # Promote via 3-param overload: fresh sweep is re-derived at issue time
    app = conn.execute("select ops.issue_billing_application(%s,%s,'INV-1')", (d, s["person"])).fetchone()[0]
    assert conn.execute("select status from ops.billing_application where id=%s", (app,)).fetchone()[0] == "issued"
    # Draft is consumed (deleted) after promotion
    assert conn.execute("select count(*) from ops.billing_application_draft where id=%s", (d,)).fetchone()[0] == 0


def test_draft_reserves_nothing(conn):
    """A saved draft does not create any billing_application_line -- it reserves nothing.
    The apparatus still appears on the unbilled set (confirmed via ops.v_unbilled_recognition)."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    conn.execute("select ops.record_billing_application(%s,%s,current_date,null,'{}'::uuid[],0)",
                 (s["project"], s["person"]))
    # Drafts reserve nothing -- apparatus must still appear in the unbilled view.
    unbilled_count = conn.execute(
        "select count(*) from ops.v_unbilled_recognition where apparatus_id=%s",
        (s["apparatus"],)).fetchone()[0]
    assert unbilled_count >= 1


def test_draft_discard(conn):
    """discard_draft_billing_application removes the draft row; no billing_application created."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    d = conn.execute("select ops.record_billing_application(%s,%s,current_date,null,'{}'::uuid[],0)",
                     (s["project"], s["person"])).fetchone()[0]
    assert conn.execute("select count(*) from ops.billing_application_draft where id=%s", (d,)).fetchone()[0] == 1
    conn.execute("select ops.discard_draft_billing_application(%s,%s)", (d, s["person"]))
    assert conn.execute("select count(*) from ops.billing_application_draft where id=%s", (d,)).fetchone()[0] == 0
    assert conn.execute("select count(*) from ops.billing_application where project_id=%s", (s["project"],)).fetchone()[0] == 0


def test_draft_promote_blank_ref_rejected(conn):
    """Promoting a draft with a blank ref must raise an exception."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    d = conn.execute("select ops.record_billing_application(%s,%s,current_date,null,'{}'::uuid[],0)",
                     (s["project"], s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("select ops.issue_billing_application(%s,%s,'')", (d, s["person"]))


def test_draft_promote_nonexistent_id_rejected(conn):
    """Promoting a draft_id that does not exist must raise an exception."""
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("select ops.issue_billing_application(%s,%s,'INV-GHOST')",
                     (str(uuid.uuid4()), s["person"]))


# ---- Task 9: views (v_unbilled_recognition, v_draft_preview, v_billing_application_sov, v_project_billing) ----

def test_reconciliation_ties_to_cent(conn):
    """recognized_to_date == billed_gross_to_date + unbilled_recognized, cent-exact.
    Uses non-2dp quoted_revenue (333.335) to confirm round-per-event then sum avoids floating drift."""
    # quoted_revenue=333.335: round(333.335,2) = 333.34 (half-even) or 333.33 depending on DB;
    # the key is that recognized_to_date uses the SAME per-event rounding as the billing lines,
    # so the identity holds regardless of which way it rounds.
    s = _seed_recognizable(conn, quoted_revenue=Decimal("333.335"), quoted_hours=3)
    _recognize(conn, s)
    _issue(conn, s["project"], s["person"])
    r = conn.execute(
        "select recognized_to_date, billed_gross_to_date, unbilled_recognized "
        "from ops.v_project_billing where project_id=%s",
        (s["project"],)).fetchone()
    assert r is not None
    assert r[0] == r[1] + r[2]   # recognized == billed + unbilled, to the cent


def test_unbilled_view_matches_sweep(conn):
    """v_unbilled_recognition shows the apparatus before billing; disappears after issue."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    assert conn.execute(
        "select count(*) from ops.v_unbilled_recognition where apparatus_id=%s",
        (s["apparatus"],)).fetchone()[0] == 1
    _issue(conn, s["project"], s["person"])
    assert conn.execute(
        "select count(*) from ops.v_unbilled_recognition where apparatus_id=%s",
        (s["apparatus"],)).fetchone()[0] == 0


def test_views_exist(conn):
    """All four Task 9 views are present in the ops schema."""
    for v in ("v_unbilled_recognition", "v_draft_preview", "v_billing_application_sov", "v_project_billing"):
        assert conn.execute("select to_regclass(%s)", (f"ops.{v}",)).fetchone()[0] is not None, f"missing view ops.{v}"


def test_sov_aggregates_by_scope(conn):
    """v_billing_application_sov groups lines by (application_id, scope_id)."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    app = _issue(conn, s["project"], s["person"])
    row = conn.execute(
        "select apparatus_count, amount from ops.v_billing_application_sov where application_id=%s",
        (app,)).fetchone()
    assert row is not None
    assert row[0] == 1
    assert row[1] == Decimal("500.00")


def test_draft_preview_shows_unbilled(conn):
    """v_draft_preview shows unbilled apparatus for a saved draft."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    d = conn.execute(
        "select ops.record_billing_application(%s,%s,current_date,null,'{}'::uuid[],0)",
        (s["project"], s["person"])).fetchone()[0]
    cnt = conn.execute(
        "select count(*) from ops.v_draft_preview where draft_id=%s",
        (d,)).fetchone()[0]
    assert cnt == 1


def test_project_billing_open_draft_count(conn):
    """v_project_billing.open_draft_count reflects saved drafts."""
    s = _seed_recognizable(conn); _recognize(conn, s)
    assert conn.execute(
        "select open_draft_count from ops.v_project_billing where project_id=%s",
        (s["project"],)).fetchone()[0] == 0
    conn.execute(
        "select ops.record_billing_application(%s,%s,current_date,null,'{}'::uuid[],0)",
        (s["project"], s["person"]))
    assert conn.execute(
        "select open_draft_count from ops.v_project_billing where project_id=%s",
        (s["project"],)).fetchone()[0] == 1
