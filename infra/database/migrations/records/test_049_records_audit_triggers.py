import os
import sys

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dbtest  # noqa: E402

MIG = "049_records_audit_triggers.sql"
DOWN = "049_records_audit_triggers_down.sql"

# The writer-grant set (records_intake_writer INSERT/UPDATE). 049 attaches
# trg_audit to EXACTLY these and to nothing else (not audit_log, which would
# recurse, nor neta_table_source_links, which is owner-only, D7).
WANT_TRIGGER_COUNT = (
    "select count(distinct table_name) from information_schema.role_column_grants "
    "where grantee='records_intake_writer' and table_schema='records' "
    "  and privilege_type in ('INSERT','UPDATE')"
)
GOT_TRIGGER_COUNT = (
    "select count(*) from pg_trigger tg join pg_class c on c.oid=tg.tgrelid "
    "  join pg_namespace ns on ns.oid=c.relnamespace "
    "where ns.nspname='records' and tg.tgname='trg_audit' and not tg.tgisinternal"
)
# trg_audit must be ABSENT from these two tables.
FORBIDDEN_TRIGGER = (
    "select count(*) from pg_trigger tg join pg_class c on c.oid=tg.tgrelid "
    "  join pg_namespace ns on ns.oid=c.relnamespace "
    "where ns.nspname='records' and tg.tgname='trg_audit' and not tg.tgisinternal "
    "  and c.relname in ('audit_log','neta_table_source_links')"
)
# every trg_audit trigger fires AFTER I/U/D FOR EACH ROW via fn_audit_capture.
# Assert on catalog columns (formatting-independent): tgtype bit layout is
# ROW(1) + INSERT(4) + DELETE(8) + UPDATE(16) = 29 for an AFTER (BEFORE bit 2
# clear), FOR EACH ROW, INSERT-OR-UPDATE-OR-DELETE trigger; tgfoid is the
# shared capture function.
BAD_TRIGGER_DEFS = (
    "select count(*) from pg_trigger tg join pg_class c on c.oid=tg.tgrelid "
    "  join pg_namespace ns on ns.oid=c.relnamespace "
    "where ns.nspname='records' and tg.tgname='trg_audit' and not tg.tgisinternal "
    "  and (tg.tgtype <> 29 "
    "       or tg.tgfoid <> 'records.fn_audit_capture()'::regprocedure)"
)
# trg_audit exists on the persons write-path table (our fixture target).
PERSONS_HAS_TRIGGER = (
    "select count(*) from pg_trigger tg join pg_class c on c.oid=tg.tgrelid "
    "  join pg_namespace ns on ns.oid=c.relnamespace "
    "where ns.nspname='records' and c.relname='persons' "
    "  and tg.tgname='trg_audit' and not tg.tgisinternal"
)


def _q(dsn, sql):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(sql).fetchall()


def test_049_applied_then_down_up():
    # Runner contract: 049 is ALREADY applied by the walk. Assert the applied
    # posture, exercise the actor-attribution capture, run DOWN then UP, and
    # LEAVE 049 applied (do NOT re-apply first, do NOT leave reversed). dsn()
    # reads RECORDS_DEV_DSN (the walk's disposable child DB), skips loudly if
    # absent, and refuses records_dev.
    dsn = _dbtest.dsn()

    # (1) STATIC POSTURE ----------------------------------------------------
    # trigger set == writer-grant set (exactly), and the triggers all fire
    # AFTER I/U/D FOR EACH ROW via fn_audit_capture.
    want = _q(dsn, WANT_TRIGGER_COUNT)[0][0]
    assert want == 6  # assets, form_submissions, form_field_values, pm_schedules, pm_events, persons
    assert _q(dsn, GOT_TRIGGER_COUNT)[0][0] == want
    # none on audit_log (recursion) or neta_table_source_links (owner-only).
    assert _q(dsn, FORBIDDEN_TRIGGER)[0][0] == 0
    # every trg_audit trigger has the expected shape.
    assert _q(dsn, BAD_TRIGGER_DEFS)[0][0] == 0
    # our fixture table (persons) is in the audited set.
    assert _q(dsn, PERSONS_HAS_TRIGGER)[0][0] == 1

    # (2) WRITER ATTRIBUTION (SET SESSION AUTHORIZATION, not SET ROLE) ------
    # persons is FK-independent (the person anchor), so a bare display_name
    # INSERT needs no fixture seeding. SET SESSION AUTHORIZATION makes
    # session_user the writer role -> fn_audit_capture records actor_role from
    # session_user. SET ROLE would leave session_user=postgres and FALSELY
    # attribute the row to the superuser. Everything runs inside ONE txn we
    # roll back, so both the persons row and the audit row leave zero residue.
    with psycopg.connect(dsn) as pc:
        with pc.cursor() as cur:
            cur.execute("set session authorization records_intake_writer")
            cur.execute(
                "insert into records.persons (display_name) values ('audit-writer-fixture') "
                "returning person_id"
            )
            pk = cur.fetchone()[0]
            # reset to the connecting (superuser) identity to READ audit_log
            # (records_intake_writer has no SELECT on audit_log).
            cur.execute("reset session authorization")
            cur.execute(
                "select action, table_name, row_pk, actor_role, definer_role, "
                "  actor_is_superuser, txid "
                "from records.audit_log where table_name='persons' and row_pk=%s",
                (str(pk),),
            )
            rows = cur.fetchall()
        assert len(rows) == 1, "writer INSERT must produce exactly one audit row"
        action, tbl, row_pk, actor_role, definer_role, is_su, txid = rows[0]
        assert action == "insert"
        assert tbl == "persons"
        assert row_pk == str(pk)          # row_pk non-null, equals the new PK
        assert actor_role == "records_intake_writer"   # session_user, not the definer
        assert definer_role == "records_fn_owner"       # current_user = the definer owner
        assert is_su is False             # the writer is a non-superuser login
        assert txid is not None
        pc.rollback()

    # (3) SUPERUSER / DIRECT-SQL UPDATE + DELETE (no SET) -------------------
    # As the admin superuser the walk connects as, direct DML also fires the
    # trigger. actor_role is that admin login (captured dynamically, never
    # hardcoded); actor_is_superuser is TRUE. This proves direct-SQL writes are
    # NOT invisible to the audit trail (the whole point of a trigger, not a
    # policy). Seed + mutate inside ONE txn, roll it all back.
    with psycopg.connect(dsn) as pc:
        with pc.cursor() as cur:
            admin_login = cur.execute("select session_user").fetchone()[0]
            admin_is_su = cur.execute(
                "select rolsuper from pg_roles where rolname=session_user"
            ).fetchone()[0]
            assert admin_is_su is True, "walk admin must be a superuser for this proof"
            # seed a row to mutate (as the admin; this INSERT also audits).
            cur.execute(
                "insert into records.persons (display_name) values ('audit-su-fixture') "
                "returning person_id"
            )
            pk = cur.fetchone()[0]
            # UPDATE a single column -> changed_columns must be exactly that set.
            cur.execute(
                "update records.persons set display_name='audit-su-updated' where person_id=%s",
                (pk,),
            )
            # DELETE -> one delete row, row_pk non-null (from OLD).
            cur.execute("delete from records.persons where person_id=%s", (pk,))

            cur.execute(
                "select action, actor_role, actor_is_superuser, row_pk, changed_columns "
                "from records.audit_log where table_name='persons' and row_pk=%s "
                "order by audit_id",
                (str(pk),),
            )
            rows = cur.fetchall()
        # three rows for this pk: insert (seed), update, delete.
        by_action = {r[0]: r for r in rows}
        assert set(by_action) == {"insert", "update", "delete"}, (
            f"expected insert/update/delete rows, got {sorted(by_action)}"
        )
        # UPDATE row: admin login, superuser, changed_columns == the changed set.
        u_action, u_actor, u_is_su, u_pk, u_changed = by_action["update"]
        assert u_actor == admin_login          # direct-SQL actor = the admin login
        assert u_is_su is True                 # captured as superuser
        assert u_pk == str(pk)
        assert u_changed == ["display_name"]   # exactly the one column that changed
        # DELETE row: admin login, superuser, row_pk non-null (from OLD).
        d_action, d_actor, d_is_su, d_pk, d_changed = by_action["delete"]
        assert d_actor == admin_login
        assert d_is_su is True
        assert d_pk == str(pk)                 # row_pk non-null on delete
        pc.rollback()

    # (4) app_actor (untrusted, bounded) -----------------------------------
    # records.app_actor='tech.42' -> captured verbatim. An over-long value
    # (>128) OR one outside the token charset is normalized to the sentinel
    # INVALID_APP_ACTOR (fn_audit_capture bounds untrusted free-text).
    # set_config(name,value,is_local=true) is the parameterizable form of
    # SET LOCAL (a plain SET cannot bind a $1 placeholder).
    with psycopg.connect(dsn) as pc:
        with pc.cursor() as cur:
            cur.execute("select set_config('records.app_actor', 'tech.42', true)")
            cur.execute(
                "insert into records.persons (display_name) values ('audit-appactor-ok') "
                "returning person_id"
            )
            pk_ok = cur.fetchone()[0]
            cur.execute(
                "select app_actor from records.audit_log where table_name='persons' and row_pk=%s",
                (str(pk_ok),),
            )
            assert cur.fetchone()[0] == "tech.42"
        pc.rollback()

    with psycopg.connect(dsn) as pc:
        with pc.cursor() as cur:
            # 200 'a' chars: over the 128-char bound -> sentinel.
            cur.execute("select set_config('records.app_actor', %s, true)", ("a" * 200,))
            cur.execute(
                "insert into records.persons (display_name) values ('audit-appactor-long') "
                "returning person_id"
            )
            pk_long = cur.fetchone()[0]
            # a value inside the length bound but outside the token charset
            # (space + '!') -> also the sentinel.
            cur.execute("select set_config('records.app_actor', %s, true)", ("bad actor!",))
            cur.execute(
                "insert into records.persons (display_name) values ('audit-appactor-charset') "
                "returning person_id"
            )
            pk_bad = cur.fetchone()[0]
            cur.execute(
                "select row_pk, app_actor from records.audit_log "
                "where table_name='persons' and row_pk = any(%s)",
                ([str(pk_long), str(pk_bad)],),
            )
            got = dict(cur.fetchall())
            assert got[str(pk_long)] == "INVALID_APP_ACTOR"   # over-long -> sentinel
            assert got[str(pk_bad)] == "INVALID_APP_ACTOR"    # bad charset -> sentinel
        pc.rollback()

    # residue check: every fixture ran inside a rolled-back txn, so audit_log
    # holds no persons rows from this test.
    assert _q(
        dsn, "select count(*) from records.audit_log where table_name='persons'"
    )[0][0] == 0

    # (5) DOWN -> every trg_audit trigger is gone (fingerprint captures
    # triggers, so this reversal is the reversibility teeth).
    assert _q(dsn, GOT_TRIGGER_COUNT)[0][0] == want
    _dbtest.run_psql(DOWN, dsn)
    assert _q(dsn, GOT_TRIGGER_COUNT)[0][0] == 0

    # (6) UP -> re-apply 049 and LEAVE it applied (fingerprint pre==post).
    _dbtest.run_psql(MIG, dsn)
    assert _q(dsn, GOT_TRIGGER_COUNT)[0][0] == want
    assert _q(dsn, FORBIDDEN_TRIGGER)[0][0] == 0
    assert _q(dsn, PERSONS_HAS_TRIGGER)[0][0] == 1
