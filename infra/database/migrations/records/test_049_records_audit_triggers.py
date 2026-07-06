import os
import sys

import psycopg
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dbtest  # noqa: E402

MIG = "049_records_audit_triggers.sql"
DOWN = "049_records_audit_triggers_down.sql"

# The writer-grant set (records_intake_writer INSERT/UPDATE). 049 attaches
# trg_audit to EXACTLY these and to nothing else (not audit_log, which would
# recurse, nor neta_table_source_links, which is owner-only, D7).
#
# VISIBILITY-INDEPENDENT ORACLE (D5-B): derive the writer-grant table set from
# the RAW catalog ACLs - pg_class.relacl (table-level) AND pg_attribute.attacl
# (column-level, which is how 045 records the writer's INSERT/UPDATE: the grants
# are COLUMN-scoped, so a relacl-only read would yield 0) - via aclexplode. The
# ORIGINAL 049 (and the pre-fix test) derived this from
# information_schema.role_column_grants, which is CURRENT-USER-VISIBILITY scoped:
# a low-visibility running role sees 0 rows -> 0 triggers -> got==want==0 GREEN
# with audit SILENTLY DISABLED. aclexplode over catalog ACL columns is readable
# by ANY role (not visibility-filtered), so this yields the TRUE writer-grant set.
# The migration 049 uses this SAME derivation for both its create loop and its
# terminal want-count; the test asserts want > 0 so a regression to a visibility-
# scoped oracle FAILS LOUD instead of silent-greening.
WANT_TRIGGER_COUNT = (
    "select count(*) from ("
    "  select distinct c.relname"
    "    from pg_class c"
    "    join pg_namespace ns on ns.oid = c.relnamespace"
    "    left join lateral aclexplode(c.relacl) ra on true"
    "    left join lateral ("
    "      select a.privilege_type as ptype, a.grantee as gtee"
    "        from pg_attribute att, lateral aclexplode(att.attacl) a"
    "       where att.attrelid = c.oid and att.attnum > 0 and not att.attisdropped"
    "    ) ca on true"
    "   where ns.nspname = 'records' and c.relkind = 'r'"
    "     and c.relname not in ('audit_log','neta_table_source_links')"
    "     and ("
    "       (ra.grantee = 'records_intake_writer'::regrole and ra.privilege_type in ('INSERT','UPDATE'))"
    "       or (ca.gtee = 'records_intake_writer'::regrole and ca.ptype in ('INSERT','UPDATE'))"
    "     )"
    ") s"
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
# records_owner must hold NO EXECUTE on fn_audit_capture at rest: 049 grants it a
# TRANSIENT EXECUTE only for CREATE-TRIGGER time and revokes it afterward (the
# trigger keeps firing without it). A leaked grant is a residue failure.
OWNER_HAS_FN_EXECUTE = (
    "select count(*) from pg_proc p, "
    "  lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
    "where p.pronamespace=(select oid from pg_namespace where nspname='records') "
    "  and p.proname='fn_audit_capture' "
    "  and a.grantee='records_owner'::regrole and a.privilege_type='EXECUTE'"
)
# temp-authority residue (046 [4] / 048 form): no NON-admin role holds a USABLE
# (set/inherit) membership INTO records_owner or records_fn_owner (postgres EXEMPT).
TEMP_AUTHORITY_RESIDUE = (
    "select count(*) from pg_auth_members am "
    "join pg_roles ow on ow.oid=am.roleid and ow.rolname in ('records_owner','records_fn_owner') "
    "join pg_roles m on m.oid=am.member "
    "where (am.set_option or am.inherit_option) and m.oid <> 'postgres'::regrole"
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
    # SELF-ORACLE GUARD (D5-B): the visibility-independent set is NON-EMPTY. A
    # regression to a visibility-scoped oracle (role_column_grants) that yields 0
    # under a low-visibility running role would fail HERE instead of silent-greening.
    assert want > 0, "writer-grant table set is empty - audit would be SILENTLY DISABLED"
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


# --------------------------------------------------------------------------------------
# SUPABASE-COMPAT green-proof (Task 2.5). Self-driving on RECORDS_PG_ADMIN_DSN: it builds
# a disposable DB, applies 001-044 + adapted 045 + 046 + 047 + 048 + 049 through the
# NON-super applier, and asserts the adapted 049 SUCCEEDS with the applied posture:
# trg_audit on EXACTLY the writer-grant set (visibility-independent oracle), none on
# audit_log/neta_table_source_links, want > 0 (the self-oracle floor), records_owner
# holds NO leftover EXECUTE on fn_audit_capture (the transient CREATE-TRIGGER grant is
# revoked), and the temp-authority residue clean (no usable non-admin membership into an
# owner role). It then ALSO drives the WHOLE committed 049_..._down.sql through the SAME
# non-super applier and asserts every trigger is dropped. This is the green mirror of
# test_supabase_compat_redproof.py; 049's compat proof exercises the FULL set-role-owner
# CREATE/DROP TRIGGER + transient-EXECUTE choreography locally, because by 049 the target
# tables are records_owner-owned even locally. It is a LOCAL APPROXIMATION (a real
# Supabase branch is the fidelity authority, Phase 3).
# --------------------------------------------------------------------------------------
import run_validation as rv  # noqa: E402

_ADMIN = os.environ.get("RECORDS_PG_ADMIN_DSN")

compat = pytest.mark.skipif(
    not _ADMIN, reason="RECORDS_PG_ADMIN_DSN not set - non-super compat green-proof skipped"
)

# Cluster-level roles the compat proof may leave behind (aborted prior run). Drop the
# password-less, orphaned set before/after each module run so the proof is idempotent;
# password-carrying roles are LEFT IN PLACE (DEV-7 safety).
_DISPOSABLE_ROLES = (
    "records_api", "records_intake_writer", "records_owner", "records_reclaim_owner",
    "records_fn_owner", "records_auditor",
)


def _drop_disposable_roles():
    with psycopg.connect(_ADMIN, autocommit=True) as c:
        for role in _DISPOSABLE_ROLES:
            if not c.execute("select 1 from pg_roles where rolname=%s", (role,)).fetchone():
                continue
            haspw = c.execute(
                "select rolpassword is not null from pg_authid where rolname=%s", (role,)
            ).fetchone()[0]
            if haspw:
                continue  # out-of-band password: never drop (DEV-7 discipline)
            try:
                c.execute(f'drop owned by "{role}"')
                c.execute(f'drop role "{role}"')
            except psycopg.errors.DependentObjectsStillExist:
                pass  # cross-DB dependency: leave in place


@pytest.fixture(scope="module")
def compat_child():
    """Disposable DB with 001-044 + adapted 045/046/047/048/049 applied AS the non-super
    applier; yields (admin_child_dsn, applier_apply_dsn): the ADMIN child DSN for catalog
    introspection, and the non-super APPLIER's own apply DSN so a test can drive further
    SQL (e.g. 049_down) through the SAME non-super identity that applied 049 UP - the
    identity whose transient owner-role memberships are exactly what Task 2.5's set-role-
    owner choreography establishes and revokes. The fixture succeeding IS the green proof
    that adapted 049 applies under the non-super applier. Value-silent."""
    if not _ADMIN:
        pytest.skip("RECORDS_PG_ADMIN_DSN not set")
    rv.check_admin_dsn(_ADMIN)
    _drop_disposable_roles()  # clean any orphaned cluster-level roles before applying
    val = rv.make_val_name()
    rv.assert_val_name(val)
    applier = rv.make_local_applier(_ADMIN, rv.LOCAL_APPLIER_ENVELOPE)
    rv.assert_applier_name(applier.role)
    with psycopg.connect(_ADMIN, autocommit=True) as c:
        c.execute(f'create database "{val}"')
    try:
        with psycopg.connect(_ADMIN, autocommit=True) as c:
            c.execute(applier.create_sql)
            c.execute(f'grant create on database "{val}" to "{applier.role}"')
        apply_dsn = rv.derive_child_dsn(applier.dsn, val)
        migs, _ = rv.enumerate_stack(rv.HERE)
        for num, fname in migs:
            if num > 49:
                break
            rv._apply_as_applier(fname, apply_dsn)  # 001-044, adapted 045-049; each succeeds
        yield rv.RedactedDsn(rv.derive_child_dsn(_ADMIN, val)), rv.RedactedDsn(apply_dsn)
    finally:
        with psycopg.connect(_ADMIN, autocommit=True) as c:
            c.execute(f'drop database if exists "{val}" with (force)')
            c.execute(applier.drop_sql)
        _drop_disposable_roles()  # do not leave orphaned cluster-level roles behind


@compat
def test_compat_adapted_049_applies_under_non_super(compat_child):
    # Reaching here means adapted 049 applied AS the non-super applier without raising -
    # the CREATE TRIGGER under SET ROLE records_owner + transient EXECUTE grant from
    # records_fn_owner + the visibility-independent oracle under the non-super applier is
    # green.
    admin_dsn, apply_dsn = compat_child
    assert admin_dsn and apply_dsn


@compat
def test_compat_trigger_set_equals_writer_grant_set(compat_child):
    # trg_audit on EXACTLY the visibility-independent writer-grant set; want > 0 (the
    # self-oracle floor - a regression to a visibility-scoped oracle would collapse this
    # to 0 and FAIL here, not silent-green); none on audit_log/neta_table_source_links.
    admin_dsn, _apply_dsn = compat_child
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        want = c.execute(WANT_TRIGGER_COUNT).fetchone()[0]
        assert want > 0, "writer-grant table set is empty - audit would be SILENTLY DISABLED"
        assert want == 6, f"expected 6 writer-grant tables, got {want}"
        got = c.execute(GOT_TRIGGER_COUNT).fetchone()[0]
        assert got == want, f"trigger count {got} <> writer-grant table count {want}"
        assert c.execute(FORBIDDEN_TRIGGER).fetchone()[0] == 0, \
            "trg_audit must be ABSENT from audit_log and neta_table_source_links"
        assert c.execute(BAD_TRIGGER_DEFS).fetchone()[0] == 0, \
            "every trg_audit must fire AFTER I/U/D FOR EACH ROW via fn_audit_capture"


@compat
def test_compat_owner_execute_and_temp_authority_residue_clean(compat_child):
    # residue: records_owner holds NO EXECUTE on fn_audit_capture at rest (the transient
    # CREATE-TRIGGER grant issued BY records_fn_owner was revoked), and no NON-admin role
    # holds a usable (set/inherit) membership into records_owner/records_fn_owner (the two
    # transient memberships were revoked; postgres is EXEMPT).
    admin_dsn, _apply_dsn = compat_child
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        assert c.execute(OWNER_HAS_FN_EXECUTE).fetchone()[0] == 0, \
            "records_owner retains EXECUTE on fn_audit_capture (transient grant leaked)"
        n = c.execute(TEMP_AUTHORITY_RESIDUE).fetchone()[0]
        assert n == 0, f"{n} usable non-admin membership edge(s) into an owner role survived 049 UP"


@compat
def test_compat_049_down_full_file_applies_under_non_super(compat_child):
    # Task 2.5 FULL-FILE RED/GREEN proof: applies the WHOLE committed
    # 049_records_audit_triggers_down.sql AS THE SAME NON-SUPER APPLIER that applied
    # 001-049 UP, then asserts every trg_audit trigger is DROPPED. This is the strongest
    # local proof - the entire file, single BEGIN...COMMIT, under the true non-super
    # applier - the analog of 047_down's / 048_down's full-file proof.
    #
    # The 42501 this catches: `drop trigger` on records_owner-owned tables needs table
    # OWNERSHIP, so 049_down must SET ROLE records_owner (via a transient WITH SET grant).
    # Reverting that turns this RED (the whole file is one transaction, so any failure
    # rolls back everything). Driven via rv._apply_as_applier (whole file from disk under
    # the applier DSN, mirroring the compat fixture's own UP applies) - NOT via
    # _dbtest.run_psql on RECORDS_DEV_DSN, which runs as the walk's trusted superuser child
    # DB and would mask the bug.
    admin_dsn, apply_dsn = compat_child
    rv._apply_as_applier(DOWN, apply_dsn)  # raises ApplierApplyError on a 42501 regression
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        assert c.execute(GOT_TRIGGER_COUNT).fetchone()[0] == 0, \
            "all trg_audit triggers must be DROPPED by 049_down under the non-super applier"
        # records_owner must be RETAINED (049_down does not drop roles; 046_down owns that).
        assert c.execute(
            "select count(*) from pg_roles where rolname='records_owner'"
        ).fetchone()[0] == 1, "records_owner must be RETAINED (046_down owns its drop)"
