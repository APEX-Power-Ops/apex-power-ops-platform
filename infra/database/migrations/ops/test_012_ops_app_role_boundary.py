# test_012_ops_app_role_boundary.py -- self-contained migration test (mirrors test_011's shape).
# Applies the FULL ladder 001..012 on ops_test, then proves the 012 posture: role flags,
# non-membership, PUBLIC hygiene, DEFINER/owner conversion, the column-scoped grant matrix,
# the boundary-denial proofs, H2, the FOR-UPDATE regressions, and reversibility.
#
# Denial proofs run via SET ROLE from the admin session: object-privilege checks use
# current_user, and superuser bypass is off after SET ROLE to a non-super role.
# NOTE: the SET ROLE *membership* denial itself cannot be proven from an admin session
# (SET ROLE permission is checked against session_user, which stays postgres); the
# real-login SET ROLE denial lives in packages/ops-intake/tests (writer/api DSNs).
# Here, non-membership is proven via pg_has_role.
import os, pathlib, uuid
import psycopg, pytest
from psycopg import errors
from psycopg.conninfo import conninfo_to_dict

HERE = pathlib.Path(__file__).resolve().parent

DSN = os.environ.get("OPS_DEV_ADMIN_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    "password={} sslmode=disable".format(
        os.environ.get("OPS_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", "")
    )
)
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "012 migration tests run on ops_test ONLY"

CHAIN = [
    "001_identity_skeleton.sql",
    "002_quote_model.sql",
    "003_intake_unique_keys.sql",
    "004_person_anchor.sql",
    "005_recognition_ledger.sql",
    "006_progress_billing.sql",
    "007_intake_envelope.sql",
    "008_core_equipment_models.sql",
    "009_recognition_bridge.sql",
    "010_native_envelope_intake.sql",
    "011_scope_quote_line_description.sql",
    "012_ops_app_role_boundary.sql",
]
DOWN012 = HERE / "012_ops_app_role_boundary_down.sql"
UP012 = HERE / "012_ops_app_role_boundary.sql"
DOWN011 = HERE / "011_scope_quote_line_description_down.sql"
DOWN010 = HERE / "010_native_envelope_intake_down.sql"
DOWN009 = HERE / "009_recognition_bridge_down.sql"
DOWN008 = HERE / "008_core_equipment_models_down.sql"
DOWN001 = HERE / "001_identity_skeleton_down.sql"


def _exec(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(pathlib.Path(path).read_text(encoding="utf-8"))


def _admin(autocommit=True):
    return psycopg.connect(DSN, autocommit=autocommit)


def _ops_schema_exists(conn) -> bool:
    return conn.execute(
        "select 1 from pg_catalog.pg_namespace where nspname='ops'"
    ).fetchone() is not None


def _clean_slate():
    """Drop all ops + core schemas so migrations apply cleanly on any ops_test state.
    012_down is guarded (to_regprocedure / pg_roles checks) so it is safe to run even
    when 012 was never applied."""
    with _admin() as c:
        if _ops_schema_exists(c):
            c.execute("delete from ops.intake_runs")  # 010 down data-loss guard
            _exec(DOWN012)
            _exec(DOWN011)
            _exec(DOWN010)
            _exec(DOWN009)
        _exec(DOWN008)
    _exec(DOWN001)


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    with _admin() as c:
        row = c.execute("select current_database()").fetchone()
        assert row[0] == "ops_test", "REFUSING DDL: current_database() != ops_test"
    _clean_slate()
    for f in CHAIN:
        _exec(HERE / f)
    yield
    _clean_slate()


# ---------- Task 1: roles ----------

def test_012_roles_exist_with_hardened_flags():
    with _admin() as c:
        for role, canlogin in (
            ("ops_intake_writer", True),
            ("ops_api", True),
            ("ops_fn_owner", False),
        ):
            row = c.execute(
                "select rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls,"
                " rolreplication from pg_roles where rolname=%s",
                (role,),
            ).fetchone()
            assert row is not None, role + " missing"
            assert row[0] is canlogin, role + " login flag wrong"
            assert row[1:] == (False, False, False, False, False), role + " has a privileged flag"


def test_012_no_login_role_is_member_of_fn_owner():
    with _admin() as c:
        for role in ("ops_intake_writer", "ops_api"):
            assert c.execute(
                "select pg_has_role(%s, 'ops_fn_owner', 'member')", (role,)
            ).fetchone()[0] is False, role + " can reach ops_fn_owner"
        # No non-superuser login role at all may be a member (superusers pass every
        # membership check by definition, so they are excluded from the sweep).
        bad = c.execute(
            "select rolname from pg_roles"
            " where rolcanlogin and not rolsuper"
            "   and pg_has_role(rolname, 'ops_fn_owner', 'member')"
        ).fetchall()
        assert bad == [], "login role(s) are members of ops_fn_owner: " + repr(bad)


# ---------- Task 2: PUBLIC hygiene ----------

def test_012_public_has_no_execute_on_ops_core_functions():
    with _admin() as c:
        n = c.execute(
            "select count(*) from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace"
            " where ns.nspname in ('ops','core')"
            "   and (p.proacl is null"
            "        or exists (select 1 from aclexplode(p.proacl) a"
            "                   where a.grantee = 0 and a.privilege_type = 'EXECUTE'))"
        ).fetchone()[0]
        assert n == 0, str(n) + " ops/core function(s) retain PUBLIC EXECUTE"


def test_012_public_connect_revoked_and_login_roles_connect():
    with _admin() as c:
        row = c.execute(
            "select datacl is null, exists (select 1 from aclexplode(coalesce(datacl,'{}'::aclitem[])) a"
            " where a.grantee = 0 and a.privilege_type = 'CONNECT')"
            " from pg_database where datname = current_database()"
        ).fetchone()
        assert row[0] is False, "datacl is NULL (default ACL includes PUBLIC CONNECT)"
        assert row[1] is False, "PUBLIC retains CONNECT"
        for role in ("ops_intake_writer", "ops_api"):
            assert c.execute(
                "select has_database_privilege(%s, current_database(), 'CONNECT')", (role,)
            ).fetchone()[0] is True, role + " lost CONNECT"
        assert c.execute(
            "select has_database_privilege('postgres', current_database(), 'CONNECT')"
        ).fetchone()[0] is True


def test_012_public_create_on_schema_public_revoked():
    with _admin() as c:
        row = c.execute(
            "select exists (select 1 from pg_namespace n,"
            " aclexplode(coalesce(n.nspacl,'{}'::aclitem[])) a"
            " where n.nspname='public' and a.grantee = 0 and a.privilege_type='CREATE')"
        ).fetchone()
        assert row[0] is False, "PUBLIC retains CREATE on schema public"


# ---------- Task 3: DEFINER conversion + owner ----------

SIGS = [
    "ops.attest_apparatus_complete(uuid,uuid,text)",
    "ops.revoke_completion_attestation(uuid,uuid,text)",
    "ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)",
    "ops.reverse_recognition(uuid,uuid,text)",
    "ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric)",
    "ops.issue_billing_application(uuid,uuid,text)",
    "ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric)",
    "ops.discard_draft_billing_application(uuid,uuid)",
    "ops.void_billing_application(uuid,uuid,text)",
]


def test_012_nine_fns_definer_owned_searchpath():
    with _admin() as c:
        for sig in SIGS:
            row = c.execute(
                "select p.prosecdef, p.proowner::regrole::text, p.proconfig"
                " from pg_proc p where p.oid = to_regprocedure(%s)",
                (sig,),
            ).fetchone()
            assert row is not None, sig + " missing"
            assert row[0] is True, sig + " is not SECURITY DEFINER"
            assert row[1] == "ops_fn_owner", sig + " owner is " + row[1]
            assert row[2] is not None and any(
                x.startswith("search_path=") and "ops" in x and "pg_temp" in x for x in row[2]
            ), sig + " search_path not pinned to ops, pg_temp"


def test_012_owner_grants_cover_fn_read_and_lock_surface():
    with _admin() as c:
        # SELECT surface (RV-1: the owner needs SELECT on every table its fn bodies read/join)
        for t in ("apparatus", "scopes", "completion_attestation", "revenue_recognition_event",
                  "scope_quote", "projects", "persons", "tasks",
                  "billing_application", "billing_application_line", "billing_application_draft"):
            assert c.execute(
                "select has_table_privilege('ops_fn_owner', %s, 'SELECT')", ("ops." + t,)
            ).fetchone()[0] is True, "ops_fn_owner missing SELECT on ops." + t
        # write/lock surface
        for t, priv in (
            ("apparatus", "UPDATE"),
            ("completion_attestation", "INSERT"), ("completion_attestation", "UPDATE"),
            ("revenue_recognition_event", "INSERT"), ("revenue_recognition_event", "UPDATE"),
            ("projects", "UPDATE"),
            ("billing_application", "INSERT"), ("billing_application", "UPDATE"), ("billing_application", "DELETE"),
            ("billing_application_line", "INSERT"), ("billing_application_line", "UPDATE"), ("billing_application_line", "DELETE"),
            ("billing_application_draft", "INSERT"), ("billing_application_draft", "UPDATE"), ("billing_application_draft", "DELETE"),
        ):
            assert c.execute(
                "select has_table_privilege('ops_fn_owner', %s, %s)", ("ops." + t, priv)
            ).fetchone()[0] is True, "ops_fn_owner missing " + priv + " on ops." + t
        assert c.execute(
            "select has_schema_privilege('ops_fn_owner', 'ops', 'USAGE')"
        ).fetchone()[0] is True


# ---------- Task 4: grant matrix + denial proofs ----------

PROJECTS_UPDATE_COLS = [
    "project_name", "status", "quote_revision", "contract_value", "description",
    "source_client_name", "source_site_name", "source_site_address", "source_site_city",
    "source_site_state", "source_site_zip", "source", "provenance_status", "updated_at",
]

APPARATUS_INSERT_COLS = [  # the 11 load.py columns, EXCLUDING status (D2)
    "scope_id", "task_id", "apparatus_designation", "apparatus_type", "equipment_model_ref",
    "drawing_reference", "quoted_hours", "quote_line_id", "source", "legacy_source_id",
    "provenance_status",
]

OPS_VIEWS = [
    "v_apparatus_quote", "v_apparatus_recognition", "v_billing_application_sov",
    "v_completion_recognition_rollup", "v_completion_recognition_worklist", "v_draft_preview",
    "v_project_billing", "v_project_recognition", "v_recognition_review_queue",
    "v_scope_recognition", "v_unbilled_recognition",
]


def _seed_min(c, project_number=None):
    """Admin setup DML: minimal project -> scope -> scope_quote -> apparatus('In Progress').
    Mirrors the eligible fixture in test_ops_recognition_routes.py."""
    pn = project_number or ("T012-" + uuid.uuid4().hex[:8])
    with c.cursor() as cur:
        cur.execute(
            "insert into ops.projects (project_number,project_name,status,provenance_status)"
            " values (%s,'P','Active','approved') returning id", (pn,))
        pid = cur.fetchone()[0]
        cur.execute(
            "insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
            " values (%s,'S','In Progress','approved','ops-intake') returning id", (pid,))
        sid = cur.fetchone()[0]
        cur.execute(
            "insert into ops.scope_quote (scope_id,onsite_labor,unit_multiplier,pct_adjust,"
            "total_quoted_hours,is_frozen,frozen_at) values (%s,1500,1,1,10,true,now())", (sid,))
        cur.execute(
            "insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,"
            "quoted_hours,quoted_revenue,source) values (%s,'A','In Progress','approved',10,1500,'ops-intake')"
            " returning id", (sid,))
        aid = cur.fetchone()[0]
    return pid, sid, aid


def _denied(sql, role, params=None, pre_sql=None):
    """Run sql AS role (SET ROLE from the admin session) inside a rolled-back txn;
    assert InsufficientPrivilege. Object-privilege checks use current_user, and
    superuser bypass is OFF after SET ROLE to a non-super role."""
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role " + role)
            if pre_sql:
                cur.execute(pre_sql)
            with pytest.raises(errors.InsufficientPrivilege):
                cur.execute(sql, params)
        c.rollback()


def test_012_writer_positive_matrix():
    with _admin() as c:
        for col in PROJECTS_UPDATE_COLS:
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.projects',%s,'UPDATE')", (col,)
            ).fetchone()[0] is True, "writer missing projects UPDATE(" + col + ")"
        for col in APPARATUS_INSERT_COLS:
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.apparatus',%s,'INSERT')", (col,)
            ).fetchone()[0] is True, "writer missing apparatus INSERT(" + col + ")"
        for col in ("quoted_revenue", "provenance_status", "updated_at"):
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.apparatus',%s,'UPDATE')", (col,)
            ).fetchone()[0] is True, "writer missing apparatus UPDATE(" + col + ")"
        for t, p in (("intake_runs", "INSERT"), ("intake_runs", "UPDATE"), ("intake_runs", "SELECT"),
                     ("intake_source_files", "INSERT"), ("intake_validation_findings", "INSERT"),
                     ("scopes", "INSERT"), ("scopes", "DELETE"), ("scope_quote", "INSERT"),
                     ("scope_quote_line", "INSERT"), ("tasks", "INSERT"), ("tasks", "UPDATE"),
                     ("revenue_recognition_event", "SELECT"), ("billing_application", "SELECT")):
            assert c.execute(
                "select has_table_privilege('ops_intake_writer', %s, %s)", ("ops." + t, p)
            ).fetchone()[0] is True, "writer missing " + p + " on ops." + t
        for col in ("total_quoted_hours", "is_frozen", "frozen_at"):
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.scope_quote',%s,'UPDATE')", (col,)
            ).fetchone()[0] is True
        for v in OPS_VIEWS:
            assert c.execute(
                "select has_table_privilege('ops_intake_writer', %s, 'SELECT')", ("ops." + v,)
            ).fetchone()[0] is True, "writer missing SELECT on ops." + v
        for t in ("core.v_equipment_models_resolved", "core.equipment_models"):
            assert c.execute(
                "select has_table_privilege('ops_intake_writer', %s, 'SELECT')", (t,)
            ).fetchone()[0] is True
        # F-012-1: the 010 partial-index predicate helper - writer holds EXECUTE, api does not
        assert c.execute(
            "select has_function_privilege('ops_intake_writer',"
            " 'ops._intake_source_format_text(ops.intake_source_format)'::regprocedure, 'EXECUTE')"
        ).fetchone()[0] is True
        assert c.execute(
            "select has_function_privilege('ops_api',"
            " 'ops._intake_source_format_text(ops.intake_source_format)'::regprocedure, 'EXECUTE')"
        ).fetchone()[0] is False


def test_012_negative_matrix_the_boundary():
    with _admin() as c:
        # D2: no status privilege anywhere on a login role
        for role in ("ops_intake_writer", "ops_api"):
            for priv in ("INSERT", "UPDATE"):
                assert c.execute(
                    "select has_column_privilege(%s,'ops.apparatus','status',%s)", (role, priv)
                ).fetchone()[0] is False, role + " holds apparatus.status " + priv
        # writer: no source/scope_id UPDATE on apparatus, no DELETE on apparatus
        for col in ("source", "scope_id"):
            assert c.execute(
                "select has_column_privilege('ops_intake_writer','ops.apparatus',%s,'UPDATE')", (col,)
            ).fetchone()[0] is False
        # forge-closure: api has NO table DML; writer has NO ledger/attestation/billing DML
        for t in ("apparatus", "scopes", "projects", "intake_runs"):
            for p in ("INSERT", "UPDATE", "DELETE"):
                assert c.execute(
                    "select has_table_privilege('ops_api', %s, %s)", ("ops." + t, p)
                ).fetchone()[0] is False, "ops_api holds " + p + " on ops." + t
        for role in ("ops_intake_writer", "ops_api"):
            for t in ("revenue_recognition_event", "completion_attestation",
                      "billing_application", "billing_application_line", "billing_application_draft"):
                for p in ("INSERT", "UPDATE", "DELETE"):
                    assert c.execute(
                        "select has_table_privilege(%s, %s, %s)", (role, "ops." + t, p)
                    ).fetchone()[0] is False, role + " holds " + p + " on ops." + t
            for t in ("projects", "apparatus", "tasks", "scope_quote", "scope_quote_line"):
                assert c.execute(
                    "select has_table_privilege(%s, %s, 'DELETE')", (role, "ops." + t)
                ).fetchone()[0] is False, role + " holds DELETE on ops." + t
        # writer: no EXECUTE on any of the 9; api: EXECUTE on exactly the 4 recognition fns
        for sig in SIGS:
            assert c.execute(
                "select has_function_privilege('ops_intake_writer', to_regprocedure(%s), 'EXECUTE')", (sig,)
            ).fetchone()[0] is False, "writer can EXECUTE " + sig
        for sig in SIGS[:4]:
            assert c.execute(
                "select has_function_privilege('ops_api', to_regprocedure(%s), 'EXECUTE')", (sig,)
            ).fetchone()[0] is True, "api missing EXECUTE on " + sig
        for sig in SIGS[4:]:
            assert c.execute(
                "select has_function_privilege('ops_api', to_regprocedure(%s), 'EXECUTE')", (sig,)
            ).fetchone()[0] is False, "api can EXECUTE deferred billing fn " + sig


def test_012_denial_a_forged_complete_insert():
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    # M6: every column here EXCEPT status is in the writer's 11-column INSERT grant, so
    # `status` is the SOLE unauthorized column - the denial proves the D2 boundary itself,
    # not an incidental grant gap (quoted_revenue was masking it: it is UPDATE-only).
    forged = ("insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,source)"
              " values (%s,'F','Complete','approved','ops-intake')")
    _denied(forged, "ops_intake_writer", params=(sid,))
    # MANDATORY (D2): STILL denied after SET ops.completion_ctx='1' (the column-privilege
    # check fires BEFORE the completion guard, so the GUC cannot help).
    _denied(forged, "ops_intake_writer", params=(sid,), pre_sql="set local ops.completion_ctx='1'")


def test_012_denial_b_writer_status_update():
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    _denied("update ops.apparatus set status='Complete' where id=%s", "ops_intake_writer", params=(aid,))


def test_012_denial_c_writer_cannot_execute_recognition():
    x = str(uuid.uuid4())
    _denied("select ops.attest_apparatus_complete(%s::uuid,%s::uuid,'x')", "ops_intake_writer", params=(x, x))
    _denied(
        "select ops.approve_and_recognize(%s::uuid,%s::uuid,"
        "'not_applicable'::ops.obligation_clearance,null,'not_applicable'::ops.obligation_clearance,null)",
        "ops_intake_writer", params=(x, x))


def test_012_denial_d_api_cannot_fabricate():
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    _denied("insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
            " values (%s,'F','In Progress','approved','ops-intake')", "ops_api", params=(pid,))
    _denied("insert into ops.apparatus (scope_id,apparatus_designation) values (%s,'F')",
            "ops_api", params=(sid,))


def test_012_denial_f_ledger_inserts():
    x = str(uuid.uuid4())
    for role in ("ops_intake_writer", "ops_api"):
        _denied("insert into ops.revenue_recognition_event (apparatus_id) values (%s::uuid)",
                role, params=(x,))
        _denied("insert into ops.completion_attestation (apparatus_id) values (%s::uuid)",
                role, params=(x,))
        _denied("insert into ops.billing_application (project_id) values (%s::uuid)",
                role, params=(x,), pre_sql="set local ops.billing_ctx='1'")


def test_012_denial_g_delete_projects():
    _denied("delete from ops.projects", "ops_intake_writer")
    _denied("delete from ops.projects", "ops_api")


def test_012_for_update_probe_regression():
    """Task 0 probe as a permanent regression: column-scoped UPDATE satisfies the
    approve.py:237 apparatus lock and the approve.py:233 projects lock as the writer."""
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role ops_intake_writer")
            cur.execute(
                "select a.id from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                " where s.project_id = %s for update of a", (pid,))
            assert cur.fetchone() is not None
            cur.execute("select id from ops.projects where id = %s for update", (pid,))
            assert cur.fetchone() is not None
        c.rollback()


def test_012_for_update_two_session_concurrency():
    """Two-session interleave: writer A holds the apparatus row lock; writer B's NOWAIT
    lock attempt fails loud (proves the lock is really taken under column-scoped grants)."""
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    a = psycopg.connect(DSN, autocommit=False)
    b = psycopg.connect(DSN, autocommit=False)
    try:
        with a.cursor() as ca:
            ca.execute("set local role ops_intake_writer")
            ca.execute(
                "select a.id from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                " where s.project_id = %s for update of a", (pid,))
            assert ca.fetchone() is not None
            with b.cursor() as cb:
                cb.execute("set local role ops_intake_writer")
                with pytest.raises(errors.LockNotAvailable):
                    cb.execute(
                        "select a.id from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                        " where s.project_id = %s for update of a nowait", (pid,))
            b.rollback()
        a.rollback()
    finally:
        a.close()
        b.close()


# ---------- Task 5: H2 guard ----------

def _force_complete(aid):
    """Admin setup: flip an apparatus to Complete via the sanctioned ctx (setup DML tier).
    Uses its OWN autocommit=False connection so `set local` is inside a real transaction
    (on an autocommit connection SET LOCAL is inert); commit persists status='Complete'."""
    with _admin(autocommit=False) as c, c.cursor() as cur:
        cur.execute("set local ops.completion_ctx='1'")
        cur.execute("update ops.apparatus set status='Complete' where id=%s", (aid,))
        c.commit()


def test_012_h2_provenance_frozen_on_complete_regardless_of_guc():
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
    _force_complete(aid)
    upd = "update ops.apparatus set provenance_status='draft', updated_at=now() where id=%s"
    # proof (e): denied by the H2 guard even though the writer HOLDS the column privilege,
    # and even with the ctx GUC set. RaiseException (the guard), not InsufficientPrivilege.
    for pre in (None, "set local ops.completion_ctx='1'"):
        with _admin(autocommit=False) as c:
            with c.cursor() as cur:
                cur.execute("set local role ops_intake_writer")
                if pre:
                    cur.execute(pre)
                with pytest.raises(errors.RaiseException) as ei:
                    cur.execute(upd, (aid,))
                assert "provenance_status may not change while status" in str(ei.value)
            c.rollback()


def test_012_h2_breaks_no_sanctioned_path():
    """Writer provenance UPDATE on a NON-Complete row still works (the approve path),
    and attest/revoke (status-only writes) still work through the DEFINER fns."""
    with _admin() as c:
        pid, sid, aid = _seed_min(c)
        with c.cursor() as cur:
            cur.execute("insert into ops.persons (display_name) values ('PM') returning person_id")
            who = cur.fetchone()[0]
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role ops_intake_writer")
            cur.execute(
                "update ops.apparatus set provenance_status='approved', updated_at=now() where id=%s",
                (aid,))
        c.commit()
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role ops_api")
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'ok')", (aid, who))
            att = cur.fetchone()[0]
            cur.execute("select ops.revoke_completion_attestation(%s,%s,'undo')", (att, who))
        c.commit()


# ---------- Task 6: reversibility ----------

def test_012_reversible_round_trip():
    """down -> posture reverted; up -> posture restored. Leaves 012 APPLIED (chain teardown
    expects to run 012_down first via _clean_slate).

    DEV-7: the contract asserted here is POSTURE-RESTORED (grants revoked in this DB), NOT
    role-absence. Whether the login role OBJECT survives depends on whether a password was
    set out-of-band (rolpassword IS NOT NULL -> [d4] leaves it). During a test_012 run no
    password is set, so the role is dropped; after the Task-8 operator checkpoint it survives.
    Either way [d3] DROP OWNED revoked this DB's grants, which is what we assert. NEVER assert
    the role object is gone.

    EXECUTE check: post-down PUBLIC EXECUTE is restored by [d5], and has_function_privilege
    includes PUBLIC-derived privilege - so effective-privilege checks are meaningless for
    surviving roles. The contract is NO DIRECT ACE for ops_api on the fn."""
    _exec(DOWN012)
    with _admin() as c:
        # fns reverted to INVOKER + postgres-owned
        row = c.execute(
            "select p.prosecdef, p.proowner::regrole::text from pg_proc p"
            " where p.oid = to_regprocedure('ops.attest_apparatus_complete(uuid,uuid,text)')"
        ).fetchone()
        assert row == (False, "postgres"), "down did not revert DEFINER/owner"
        # PUBLIC EXECUTE restored on ops fns (pre-012 posture)
        n = c.execute(
            "select count(*) from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace"
            " where ns.nspname = 'ops'"
            "   and not (p.proacl is null"
            "        or exists (select 1 from aclexplode(p.proacl) a"
            "                   where a.grantee = 0 and a.privilege_type = 'EXECUTE'))"
        ).fetchone()[0]
        assert n == 0, "down did not restore PUBLIC EXECUTE"
        # DEV-7 posture contract: if a role object survives (password-bearing, or cross-DB
        # dependency), its grants in THIS db must be gone (DROP OWNED). If it was dropped,
        # there is nothing to check. Guard has_*_privilege on existence (it errors on a
        # missing role). ops_api must hold no DIRECT EXECUTE ACE on the recognition fns
        # ([d5] restores PUBLIC EXECUTE, so has_function_privilege would see PUBLIC-derived
        # privilege on a surviving role - check the proacl ACE directly instead).
        for role in ("ops_intake_writer", "ops_api"):
            if c.execute("select 1 from pg_roles where rolname=%s", (role,)).fetchone():
                assert c.execute(
                    "select bool_or(has_table_privilege(%s, c.oid, 'SELECT') or"
                    " has_table_privilege(%s, c.oid, 'INSERT') or has_table_privilege(%s, c.oid, 'UPDATE'))"
                    " from pg_class c join pg_namespace ns on ns.oid=c.relnamespace"
                    " where ns.nspname='ops' and c.relkind in ('r','p')", (role, role, role)
                ).fetchone()[0] in (False, None), "down left " + role + " grants behind"
        if c.execute("select 1 from pg_roles where rolname='ops_api'").fetchone():
            row = c.execute(
                "select exists (select 1 from pg_proc p,"
                " aclexplode(coalesce(p.proacl, '{}'::aclitem[])) a"
                " where p.oid = to_regprocedure('ops.attest_apparatus_complete(uuid,uuid,text)')"
                "   and a.grantee = 'ops_api'::regrole)"
            ).fetchone()
            assert row[0] is False, "down left a direct ops_api EXECUTE ACE behind"
    _exec(UP012)
    with _admin() as c:
        assert c.execute(
            "select p.prosecdef from pg_proc p"
            " where p.oid = to_regprocedure('ops.attest_apparatus_complete(uuid,uuid,text)')"
        ).fetchone()[0] is True, "re-up did not restore DEFINER"


def test_012_down_preserves_cross_database_connect():
    """F-012-3 regression: DROP OWNED BY a login role would revoke CONNECT cluster-wide.
    Grant the writer CONNECT on a sentinel database (postgres), run 012_down, and assert
    the sentinel CONNECT SURVIVES (proves down is database-scoped, not a cluster-wide
    DROP OWNED). Roles survive teardown here because DEV-7 preserves password-bearing roles."""
    with _admin() as c:
        if not c.execute(
            "select 1 from pg_roles where rolname='ops_intake_writer'"
        ).fetchone():
            pytest.skip("ops_intake_writer role absent")
        c.execute("grant connect on database postgres to ops_intake_writer")
    try:
        _exec(DOWN012)
        with _admin() as c:
            survived = c.execute(
                "select has_database_privilege('ops_intake_writer', 'postgres', 'CONNECT')"
            ).fetchone()[0]
        assert survived is True, "012_down stripped cross-database CONNECT (F-012-3 regression)"
    finally:
        with _admin() as c:
            c.execute("revoke connect on database postgres from ops_intake_writer")
        _exec(UP012)  # restore 012 for the remaining tests


# ---------- Task 7: load.py D2 ----------

def test_012_insert_apparatus_succeeds_as_writer():
    """The live intake INSERT path must work under the column-scoped matrix (AC5 shape:
    the writer creates apparatus through load.py's statement, status supplied by DEFAULT)."""
    import sys
    sys.path.insert(0, str(HERE.parents[3] / "packages/ops-intake/src"))
    from ops_intake.load import insert_apparatus
    with _admin() as c:
        pid, _sid0, _aid0 = _seed_min(c)
        with c.cursor() as cur:
            # _seed_min's scope carries a FROZEN ops.scope_quote row (is_frozen=true,
            # immutable by trg_scope_quote_freeze_guard - no admin bypass, even to unfreeze).
            # Inserting a scope_quote_line fires the line-hours maintenance trigger, which
            # UPDATEs total_quoted_hours on ops.scope_quote and would hit that guard. Use a
            # second, fresh scope (own, unfrozen scope_quote) for the line/task/apparatus
            # under test; _seed_min is still exercised for the pid/base-fixture shape.
            cur.execute(
                "insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
                " values (%s,'S2','In Progress','draft','ops-intake') returning id", (pid,))
            sid = cur.fetchone()[0]
            cur.execute(
                "insert into ops.scope_quote (scope_id,onsite_labor,unit_multiplier,pct_adjust,"
                "total_quoted_hours) values (%s,0,1,1,0)", (sid,))
            cur.execute(
                "insert into ops.tasks (scope_id, task_name) values (%s,'T') returning id", (sid,))
            tid = cur.fetchone()[0]
            cur.execute(
                "insert into ops.scope_quote_line (scope_id, apparatus_type, hrs_per_unit,"
                " line_number) values (%s,'XFMR',1,1) returning id", (sid,))
            qlid = cur.fetchone()[0]
            cur.execute("select id from core.equipment_models limit 1")
            em = cur.fetchone()
    emid = em[0] if em else None
    with _admin(autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("set local role ops_intake_writer")
            insert_apparatus(
                cur, sid, tid, qlid,
                legacy_source_id="T012:A-1", designation="A-1", apparatus_type="XFMR",
                drawing=None, quoted_hours=1, equipment_model_ref=emid,
            )
            cur.execute(
                "select status from ops.apparatus where legacy_source_id='T012:A-1'")
            assert cur.fetchone()[0] == "Not Started", "DEFAULT did not supply status"
        c.rollback()
