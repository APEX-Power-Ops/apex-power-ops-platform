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


def _qp(dsn, sql, params):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(sql, params).fetchall()


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

    # (3) SUPERUSER / DIRECT-SQL UPDATE + DELETE (CROSS-TRANSACTION) --------
    # As the admin superuser the walk connects as, direct DML also fires the
    # trigger. actor_role is that admin login (captured dynamically, never
    # hardcoded); actor_is_superuser is TRUE. This proves direct-SQL writes are
    # NOT invisible to the audit trail (the whole point of a trigger, not a
    # policy).
    #
    # The changed_columns proof MUST be cross-transaction. Within a single txn
    # now() is frozen, so records.persons.updated_at (maintained by the BEFORE
    # trigger fn_set_updated_at: NEW.updated_at := now()) never moves and the
    # updated_at exclusion is untestable -- the old single-txn proof passed
    # vacuously, WITH OR WITHOUT the FIX-2 filter. Here we (a) insert + COMMIT,
    # (b) BACKDATE updated_at by an hour + COMMIT so it is demonstrably old, then
    # (c) UPDATE display_name in a SEPARATE txn so the BEFORE trigger bumps
    # updated_at to a much newer now(). We assert BOTH that updated_at ACTUALLY
    # MOVED and that changed_columns == ['display_name'] with updated_at EXCLUDED.
    # Without FIX 2 the second assertion would be ['display_name','updated_at'],
    # so this proof is load-bearing. Cross-txn commits cannot rely on rollback,
    # so we clean up explicitly at the end (the admin superuser bypasses RLS +
    # the audit_log append-only policy and can DELETE from records.audit_log).
    admin_login = _q(dsn, "select session_user")[0][0]
    admin_is_su = _q(dsn, "select rolsuper from pg_roles where rolname=session_user")[0][0]
    assert admin_is_su is True, "walk admin must be a superuser for this proof"

    # txn 1: insert the fixture row and COMMIT.
    with psycopg.connect(dsn) as pc:
        with pc.cursor() as cur:
            cur.execute(
                "insert into records.persons (display_name) values ('audit-su-fixture') "
                "returning person_id"
            )
            pk = cur.fetchone()[0]
        pc.commit()
    try:
        # BACKDATE updated_at by an hour and COMMIT so the stored value is
        # demonstrably old. The BEFORE trigger fn_set_updated_at would clobber any
        # explicit updated_at back to now(), so disable ONLY that trigger for this
        # one setup statement (trg_audit stays live -> the backdate still audits,
        # which we prove below is filtered to NULL). Superuser can DISABLE TRIGGER.
        with psycopg.connect(dsn) as pc:
            with pc.cursor() as cur:
                cur.execute(
                    "alter table records.persons disable trigger trg_persons_updated_at"
                )
                cur.execute(
                    "update records.persons set updated_at = now() - interval '1 hour' "
                    "where person_id=%s",
                    (pk,),
                )
                cur.execute(
                    "alter table records.persons enable trigger trg_persons_updated_at"
                )
                cur.execute(
                    "select updated_at from records.persons where person_id=%s", (pk,)
                )
                backdated_at = cur.fetchone()[0]
            pc.commit()

        # txn 2 (SEPARATE): UPDATE a single caller-intent column. The BEFORE
        # trigger now fires and sets updated_at := now() (much newer than the
        # backdated value), so updated_at genuinely moves within this update.
        with psycopg.connect(dsn) as pc:
            with pc.cursor() as cur:
                cur.execute(
                    "update records.persons set display_name='audit-su-updated' "
                    "where person_id=%s",
                    (pk,),
                )
                cur.execute(
                    "select updated_at from records.persons where person_id=%s", (pk,)
                )
                new_updated_at = cur.fetchone()[0]
            pc.commit()

        # (a) updated_at ACTUALLY MOVED (~1 hour) -> the BEFORE trigger fired on
        # the display_name update, so a naive OLD/NEW diff WOULD include updated_at
        # absent the FIX-2 exclusion. This is what makes assertion (b) load-bearing.
        assert new_updated_at > backdated_at, (
            "updated_at must move on the cross-txn update (BEFORE trigger)"
        )

        # (b) the UPDATE audit rows, oldest first. There are TWO: the backdate
        # (updated_at-only) and the display_name update. Both attribute to the
        # admin superuser. FIX 2 excludes the trigger-maintained updated_at, so:
        #   - the backdate row's changed_columns is NULL (updated_at was its ONLY
        #     changed column, now filtered out -> empty agg -> NULL), and
        #   - the display_name row's changed_columns is exactly ['display_name'].
        # Without FIX 2 the backdate row would be ['updated_at'] and the
        # display_name row ['display_name','updated_at'] -- so both are proof.
        urows = _qp(
            dsn,
            "select actor_role, actor_is_superuser, row_pk, changed_columns "
            "from records.audit_log where table_name='persons' and action='update' "
            "  and row_pk=%s order by audit_id",
            (str(pk),),
        )
        assert len(urows) == 2, (
            f"expected two UPDATE audit rows (backdate + display_name), got {len(urows)}"
        )
        for u_actor, u_is_su, u_pk, _ in urows:
            assert u_actor == admin_login      # direct-SQL actor = the admin login
            assert u_is_su is True             # captured as superuser
            assert u_pk == str(pk)
        # backdate row (oldest): updated_at was the only change -> filtered -> NULL.
        assert urows[0][3] is None, (
            f"backdate update (updated_at-only) must yield NULL changed_columns after "
            f"the FIX-2 filter, got {urows[0][3]}"
        )
        # THE load-bearing assertion: the display_name update excludes updated_at.
        # Without the filter this would be ['display_name','updated_at'].
        assert urows[1][3] == ["display_name"], (
            f"changed_columns must exclude trigger-maintained updated_at, got {urows[1][3]}"
        )

        # txn 3 (SEPARATE): DELETE the fixture row and COMMIT -> one delete audit
        # row, row_pk non-null (from OLD), admin/superuser attribution.
        with psycopg.connect(dsn) as pc:
            with pc.cursor() as cur:
                cur.execute("delete from records.persons where person_id=%s", (pk,))
            pc.commit()

        drow = _qp(
            dsn,
            "select actor_role, actor_is_superuser, row_pk "
            "from records.audit_log where table_name='persons' and action='delete' "
            "  and row_pk=%s",
            (str(pk),),
        )
        assert len(drow) == 1, "exactly one DELETE audit row for the fixture pk"
        d_actor, d_is_su, d_pk = drow[0]
        assert d_actor == admin_login
        assert d_is_su is True
        assert d_pk == str(pk)                 # row_pk non-null on delete
    finally:
        # EXPLICIT cleanup: the committed persons row is already gone (deleted
        # above; if an assertion aborted before the delete, remove it now), then
        # delete ALL audit_log rows for this pk (insert+update+delete). The admin
        # superuser bypasses RLS + the append-only policy. Leave zero residue.
        with psycopg.connect(dsn) as pc:
            with pc.cursor() as cur:
                cur.execute("delete from records.persons where person_id=%s", (pk,))
                cur.execute(
                    "delete from records.audit_log where table_name='persons' and row_pk=%s",
                    (str(pk),),
                )
            pc.commit()

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

    # residue check: sections 2 and 4 ran inside rolled-back txns; the
    # cross-txn section 3 committed but cleaned up explicitly in its finally
    # block. So audit_log holds no persons rows from this test.
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
