#!/usr/bin/env python3
"""Managed-prod acceptance shim for the records lane -- GO #2 "prod-compatible dormant
acceptance" (operator-ratified 2026-07-07).

WHY THIS EXISTS: run_validation.py's tier5/6/7 impersonate roles with
SET SESSION AUTHORIZATION, which Postgres gates on the LOGIN role being a superuser.
Managed Supabase `postgres` is rolsuper=false, so those tiers 42501 false-RED on prod
(a substrate mismatch, not a posture failure). This shim reproduces the acceptance on
the managed substrate in three buckets:

  BUCKET 1 - STATIC / READ-ONLY invariants, FULL STRENGTH. Reuses run_validation's OWN
             SQL constants (imported, not re-transcribed) plus the branch-proof INV
             forms; pure introspection, no impersonation. Autocommit.
  BUCKET 2 - BEHAVIORAL via SET ROLE + transient `grant <role> to postgres with set true`
             (Gate-A: postgres is the creator, holds admin_option), run in ONE
             transaction that is ALWAYS rolled back, then a fresh-connection residue
             assert (0 non-exempt membership edges). Scoped HONESTLY: proves grant/RLS
             behaviour ONLY.
  BUCKET 3 - SESSION_USER semantics (actor_role := session_user attribution, positive
             assert_serving_identity requiring session_user=current_user, direct-login
             runtime) are CARRIED from the Phase-3B branch proof and NOT re-proved here.
             SET ROLE leaves session_user=postgres, so it cannot honestly prove them.
             Deferred until a real direct-login consumer is minted. No temp creds.

Managed-substrate note: on non-super createrole postgres, PG16+ auto-creates a creator
membership edge (postgres -> each app role, admin_option=true set_option=false
inherit_option=false). The branch-proof INV7 treats exactly these as exempt; this shim
does the same (asserts 0 NON-exempt edges), NOT run_validation's raw MEMBERSHIP_EDGES==0
(which is correct only on a superuser-applied local DB with no creator edges).

Value-silent: DSN from injected env, never echoed. Exit 0 = all PASS; nonzero = any FAIL.
"""
import os
import sys

RECORDS_DIR = "/home/olares/code/apex/apex-power-ops-platform/infra/database/migrations/records"
sys.path.insert(0, RECORDS_DIR)
import run_validation as rv  # noqa: E402  (reuse its VERIFIED SQL constants + role lists)

# Reused module-level constants (single source of truth, imported):
REF, WP, V7_VIEWS = rv.REF, rv.WP, rv.V7_VIEWS
OWNER_ONLY, DATA_API_ROLES = rv.OWNER_ONLY, rv.DATA_API_ROLES   # anon/authenticated/service_role
SERVING = ["records_api", "records_intake_writer", "records_auditor"]
APP_ROLES_6 = ["records_owner", "records_fn_owner", "records_reclaim_owner",
               "records_api", "records_intake_writer", "records_auditor"]
NOLOGIN_ROLES = {"records_owner", "records_fn_owner", "records_reclaim_owner"}
LOGIN_ROLES = {"records_api", "records_intake_writer", "records_auditor"}  # pre-GO#3 posture

# --- TRANSCRIBED (value-equivalent; both review engines confirmed content-identical) from
#     run_validation.tier7_serving @ b8df9e3d. expected_ops + GRANTED_COLS are local to that
#     function (not importable); comments/indentation differ, dict + return values match. ---
def expected_ops(role, obj):
    if role == "records_api":
        return {"SELECT"} if obj in REF + WP + V7_VIEWS else set()
    if role == "records_intake_writer":
        return {"SELECT"} if obj in REF + WP else set()
    if role == "records_auditor":
        return {"SELECT"} if obj == "audit_log" else set()
    return set()

GRANTED_COLS = {
    "assets": ["asset_tag", "name", "asset_class_id", "parent_asset_id", "site_ref",
               "client_ref", "location_label", "region", "jobsite", "plant", "substation",
               "gps_lat", "gps_long", "manufacturer", "model", "serial_number",
               "rated_voltage", "rated_current", "year_manufactured", "last_tested_at",
               "apparatus_ref", "equipment_model_id", "source", "provenance_status",
               "legacy_source_id", "notes"],
    "form_submissions": ["template_id", "asset_id", "project_ref", "work_package_ref",
               "pm_event_id", "overall_assessment", "as_found_as_left", "test_status_label",
               "job_number", "test_date", "technician", "ambient_temp_c", "relative_humidity",
               "test_equipment", "summary_notes", "source", "provenance_status",
               "legacy_source_id", "origin_device", "client_rev", "client_captured_at",
               "synced_at", "neta_standard", "technician_person_id"],
    "form_field_values": ["form_submission_id", "field_key", "field_label", "test_group",
               "sequence_no", "value_kind", "value_numeric", "value_text", "value_boolean",
               "unit", "expected_value", "min_acceptable", "max_acceptable", "measured_at",
               "notes", "origin_device", "client_rev", "client_captured_at", "synced_at"],
    "pm_schedules": ["pm_program_id", "asset_id", "last_performed_at", "next_due_at",
               "is_active", "notes"],
    "pm_events": ["pm_schedule_id", "asset_id", "scheduled_for", "performed_at",
               "form_submission_id", "project_ref", "outcome", "notes", "origin_device",
               "client_rev", "client_captured_at", "synced_at"],
    "persons": ["display_name"]}


def _redact(s):
    """Scrub any password token from text before printing (reuse the harness regexes)."""
    s = rv._PW_RE.sub(r"\1***", s)
    s = rv._URI_PW_RE.sub(r"\1***\2", s)
    return s


fails = []


def ck(cond, label):
    if not cond:
        fails.append(label)


def bucket1_static(dsn):
    """Read-only introspection. Full-strength invariants; no impersonation."""
    import psycopg
    n0 = len(fails)
    ro = psycopg.connect(dsn, autocommit=True)
    try:
        # (a) no records object owned by a super/bypassrls role (reuse rv constant).
        ck(ro.execute(rv.OWNED_BY_SUPER_OR_BYPASS).fetchone()[0] == 0,
           "1a: a records object is owned by a super/bypassrls role")

        # (b) role flags + login posture for all 6 records roles.
        rows = ro.execute(
            "select rolname, rolsuper, rolbypassrls, rolcanlogin, rolcreatedb, "
            "rolcreaterole, rolreplication from pg_roles where rolname = any(%s)",
            (APP_ROLES_6,)).fetchall()
        seen = {r[0] for r in rows}
        ck(seen == set(APP_ROLES_6), "1b: not all 6 records roles present: missing %s"
           % sorted(set(APP_ROLES_6) - seen))
        for name, su, brls, canlogin, cdb, crole, crepl in rows:
            ck(not su, "1b: %s is superuser" % name)
            ck(not brls, "1b: %s has BYPASSRLS" % name)
            ck(not (cdb or crole or crepl), "1b: %s has createdb/createrole/replication" % name)
            want_login = name in LOGIN_ROLES
            ck(canlogin == want_login, "1b: %s canlogin=%s want=%s" % (name, canlogin, want_login))

        # (c) INV7 membership edges (managed form): the ONLY edges touching an app role
        # are the exempt postgres creator edges (member=postgres, admin, NOT set, NOT
        # inherit). Assert 0 NON-exempt edges (either direction); record exempt count.
        non_exempt = ro.execute(
            "select count(*) from pg_auth_members am "
            "where (am.roleid in (select oid from pg_roles where rolname=any(%s)) "
            "    or am.member in (select oid from pg_roles where rolname=any(%s))) "
            "  and not ("
            "     am.member = 'postgres'::regrole "
            "     and am.roleid in (select oid from pg_roles where rolname=any(%s)) "
            "     and am.admin_option and not am.set_option and not am.inherit_option)",
            (APP_ROLES_6, APP_ROLES_6, APP_ROLES_6)).fetchone()[0]
        ck(non_exempt == 0, "1c: %d NON-exempt membership edge(s) touch an app role" % non_exempt)
        exempt = ro.execute(
            "select count(*) from pg_auth_members am "
            "where am.member='postgres'::regrole "
            "  and am.roleid in (select oid from pg_roles where rolname=any(%s)) "
            "  and am.admin_option and not am.set_option and not am.inherit_option",
            (APP_ROLES_6,)).fetchone()[0]
        ck(exempt == 6, "1c: exempt postgres creator edges=%d want=6" % exempt)

        # (d) ownership (INV8): schema + tables/views owned by records_owner except
        # audit_log (records_fn_owner); functions split.
        so = ro.execute("select pg_get_userbyid(nspowner) from pg_namespace where nspname='records'").fetchone()[0]
        ck(so == "records_owner", "1d: schema owner %s != records_owner" % so)
        bad_owned = ro.execute(
            "select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace "
            "where n.nspname='records' and c.relkind in ('r','v') and c.relname<>'audit_log' "
            "  and pg_get_userbyid(c.relowner) <> 'records_owner'").fetchone()[0]
        ck(bad_owned == 0, "1d: %d records table/view(s) not owned by records_owner" % bad_owned)
        alo = ro.execute("select pg_get_userbyid(relowner) from pg_class c join pg_namespace n on "
                         "n.oid=c.relnamespace where n.nspname='records' and c.relname='audit_log'").fetchone()[0]
        ck(alo == "records_fn_owner", "1d: audit_log owner %s != records_fn_owner" % alo)
        fao = ro.execute("select pg_get_userbyid(proowner) from pg_proc p join pg_namespace n on "
                         "n.oid=p.pronamespace where n.nspname='records' and p.proname='fn_audit_capture'").fetchone()[0]
        ck(fao == "records_fn_owner", "1d: fn_audit_capture owner %s != records_fn_owner" % fao)

        # (e) RLS + FORCE RLS on every records base table (INV1/INV2).
        norls = ro.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace "
                           "where n.nspname='records' and c.relkind='r' and not c.relrowsecurity").fetchone()[0]
        noforce = ro.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace "
                             "where n.nspname='records' and c.relkind='r' and not c.relforcerowsecurity").fetchone()[0]
        ck(norls == 0, "1e: %d records base table(s) with RLS disabled" % norls)
        ck(noforce == 0, "1e: %d records base table(s) without FORCE RLS" % noforce)

        # (f) policy coverage (INV3): every base table policy-covered EXCEPT
        # neta_table_source_links (deny-all by design: RLS+FORCE, no policy, owner-only).
        uncovered = ro.execute(
            "select coalesce(array_agg(c.relname order by c.relname), array[]::text[]) "
            "from pg_class c join pg_namespace n on n.oid=c.relnamespace "
            "where n.nspname='records' and c.relkind='r' "
            "  and c.relname <> 'neta_table_source_links' "
            "  and not exists (select 1 from pg_policies p where p.schemaname='records' and p.tablename=c.relname)"
        ).fetchone()[0]
        ck(uncovered == [], "1f: base table(s) without a policy: %s" % uncovered)
        sl_pol = ro.execute("select count(*) from pg_policies where schemaname='records' "
                            "and tablename='neta_table_source_links'").fetchone()[0]
        ck(sl_pol == 0, "1f: neta_table_source_links has a policy (want deny-all/none)")
        al_pol = ro.execute("select count(*) from pg_policies where schemaname='records' "
                            "and tablename='audit_log' and policyname='p_audit_log_ins'").fetchone()[0]
        ck(al_pol == 1, "1f: audit_log INSERT policy p_audit_log_ins missing")
        # no records policy TO PUBLIC.
        ck(ro.execute("select count(*) from pg_policies where schemaname='records' "
                      "and (roles is null or 'public' = any(roles))").fetchone()[0] == 0,
           "1f: a records policy is TO PUBLIC")

        # (g) function posture: fn_audit_capture meta + 048 exact allowlist.
        owner, secdef, sp_pinned, pub_exec = ro.execute(rv.FN_CAPTURE_META).fetchone()
        ck(owner == "records_fn_owner", "1g: fn_audit_capture owner %s" % owner)
        ck(secdef, "1g: fn_audit_capture not SECURITY DEFINER")
        ck(sp_pinned, "1g: fn_audit_capture search_path not pinned")
        ck(not pub_exec, "1g: fn_audit_capture has PUBLIC EXECUTE")
        # no PUBLIC EXECUTE on ANY records routine.
        ck(ro.execute("select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace, "
                      "lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
                      "where ns.nspname='records' and a.grantee=0 and a.privilege_type='EXECUTE'").fetchone()[0] == 0,
           "1g: PUBLIC holds EXECUTE on a records routine")
        try:
            ro.execute(rv.FN_OWNER_ALLOWLIST)   # RAISEs on any allowlist violation
        except psycopg.errors.RaiseException as e:
            fails.append("1g allowlist: %s" % str(e).strip().splitlines()[0])

        # (h) trigger coverage: trg_audit set == writer-grant table set (INV6/049).
        want = ro.execute(rv.TRG_WANT).fetchone()[0]
        got = ro.execute(rv.TRG_GOT).fetchone()[0]
        ck(got == want, "1h: trg_audit count %s != writer-grant table count %s" % (got, want))

        # (i) EXHAUSTIVE table-level ACL exactness: role x object x op == expected_ops.
        allobjs = REF + WP + V7_VIEWS + OWNER_ONLY
        for role in SERVING + DATA_API_ROLES:
            for obj in allobjs:
                exp = expected_ops(role, obj)
                for op in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                    got_p = ro.execute("select has_table_privilege(%s,%s,%s)",
                                       (role, "records." + obj, op)).fetchone()[0]
                    ck(got_p == (op in exp), "1i-acl-%s-%s-%s-want-%s" % (role, obj, op, op in exp))
        # schema USAGE: serving yes, Data-API no.
        for role in SERVING:
            ck(ro.execute("select has_schema_privilege(%s,'records','USAGE')", (role,)).fetchone()[0],
               "1i-usage-missing-" + role)
        for role in DATA_API_ROLES:
            ck(not ro.execute("select has_schema_privilege(%s,'records','USAGE')", (role,)).fetchone()[0],
               "1i-usage-LEAK-" + role)

        # (j) column-scope exactness (AC5): per granted column == GRANTED_COLS; boundary.
        for tbl in WP:
            cols = [r[0] for r in ro.execute("select column_name from information_schema.columns "
                    "where table_schema='records' and table_name=%s", (tbl,)).fetchall()]
            granted = set(GRANTED_COLS[tbl])
            for col in cols:
                for op in ("INSERT", "UPDATE"):
                    hp = ro.execute("select has_column_privilege('records_intake_writer',%s,%s,%s)",
                                    ("records." + tbl, col, op)).fetchone()[0]
                    ck(hp == (col in granted), "1j-col-%s.%s-%s-want-%s" % (tbl, col, op, col in granted))
            for op in ("INSERT", "UPDATE"):
                ck(ro.execute("select has_any_column_privilege('records_intake_writer',%s,%s)",
                              ("records." + tbl, op)).fetchone()[0], "1j-anycol-writer-missing-%s-%s" % (op, tbl))
            for role in ["records_api", "records_auditor"] + DATA_API_ROLES:
                for op in ("INSERT", "UPDATE"):
                    ck(not ro.execute("select has_any_column_privilege(%s,%s,%s)",
                                      (role, "records." + tbl, op)).fetchone()[0],
                       "1j-anycol-write-LEAK-%s-%s-%s" % (role, tbl, op))

        # (k) column-ACL exactness via aclexplode: EXACTLY the writer's INSERT/UPDATE on
        # granted WP columns; nothing else, no PUBLIC (grantee 0).
        actual = {(r[0], r[1], r[2], r[3]) for r in ro.execute("""
            select c.relname, a.attname,
                   case when acl.grantee=0 then 'PUBLIC' else acl.grantee::regrole::text end,
                   acl.privilege_type
            from pg_attribute a join pg_class c on c.oid=a.attrelid
            join pg_namespace n on n.oid=c.relnamespace
            cross join lateral aclexplode(a.attacl) acl
            where n.nspname='records' and a.attnum>0 and a.attacl is not null""").fetchall()}
        expected = set()
        for _t, _cs in GRANTED_COLS.items():
            for _c in _cs:
                expected.add((_t, _c, "records_intake_writer", "INSERT"))
                expected.add((_t, _c, "records_intake_writer", "UPDATE"))
        ck(actual == expected, "1k-colacl-exactness extra=%r missing=%r"
           % (sorted(actual - expected)[:6], sorted(expected - actual)[:6]))

        # (l) Data-API exclusion GRANT gate: PUBLIC holds nothing on records
        # (schema nspacl, relacl, attacl grantee 0).
        ck(ro.execute("select count(*) from pg_namespace n, lateral aclexplode(n.nspacl) a "
                      "where n.nspname='records' and a.grantee=0").fetchone()[0] == 0,
           "1l-public-schema-usage")
        ck(ro.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace, "
                      "lateral aclexplode(c.relacl) a where n.nspname='records' and a.grantee=0").fetchone()[0] == 0,
           "1l-public-object-grant")

        # (m) views are security_invoker=true (RLS-bypass guard; tier5 DP8). Read-only.
        for v in V7_VIEWS:
            opts = ro.execute("select reloptions from pg_class c join pg_namespace n on "
                              "n.oid=c.relnamespace where n.nspname='records' and c.relname=%s", (v,)).fetchone()[0]
            ok = bool(opts) and any(o.startswith("security_invoker=") and o.split("=")[1] in ("true", "on", "1")
                                    for o in opts)
            ck(ok, "1m: %s is not security_invoker=true (view would bypass RLS)" % v)

        # (n) service_role IS BYPASSRLS -- the premise that makes 'no records grant' a real
        # grant-layer block of a bypass-capable role (tier7 AC2).
        srb = ro.execute("select rolbypassrls from pg_roles where rolname='service_role'").fetchone()
        ck(srb is not None and srb[0] is True,
           "1n: service_role is not BYPASSRLS (grant-layer exclusion premise void)")

        # (o) records_auditor named in NO records policy outside audit_log (tier6 6g).
        ck(ro.execute("select count(*) from pg_policies where schemaname='records' "
                      "and tablename<>'audit_log' and 'records_auditor' = any(roles)").fetchone()[0] == 0,
           "1o: records_auditor named in a policy outside audit_log")
    finally:
        ro.close()
    return len(fails) == n0


def bucket2_behavioral(dsn):
    """Grant/RLS/reachability behaviour via SET ROLE + transient `grant <role> to postgres with
    set true` (postgres is the app-role creator, holds admin_option). ALL records access goes
    THROUGH the app roles (bare postgres owns nothing in records + holds no grant; BYPASSRLS
    bypasses policies, NOT privileges). ONE rolled-back transaction for the proofs, then a
    fresh-connection residue verification (membership + per-run sentinel absence + audit row-PK sentinel).
    Proves grant/RLS behaviour ONLY -- session_user semantics are bucket 3 (deferred).

    NOT literally zero-residue: no ROW/grant residue survives (asserted below), but two effects are
    NOT rolled back -- (a) the audit_log.audit_id IDENTITY sequence advances (assets.asset_id +
    form_submissions.form_submission_id are UUID defaults, so they do NOT consume a sequence), and
    (b) rolled-back writes still create normal WAL / XID / dead-tuple storage churn. Both are the
    packet-ratified '(dynamic proofs) may momentarily advance sequences' cost (packet Sec 5), benign
    on the dormant zero-consumer substrate. v_pm_due reachability needs an owner-only pm_programs
    seed (infeasible on prod post-045): CARRIED from Phase-3B; bucket 1m/1i prove its guard statically."""
    import psycopg
    import uuid
    n0 = len(fails)
    tag = "zzb2_" + uuid.uuid4().hex     # per-run unique sentinel (full 128-bit)

    def expect_denied(cur, sql, label):
        cur.execute("savepoint s")
        try:
            cur.execute(sql)
            cur.execute("rollback to savepoint s")
            fails.append(label)
        except psycopg.errors.Error as e:
            cur.execute("rollback to savepoint s")
            if getattr(e, "sqlstate", None) != "42501":
                fails.append("%s-wrong-sqlstate(%s)" % (label, getattr(e, "sqlstate", None)))

    def membership_residue(where):
        # autocommit, pg_catalog only: 0 non-exempt edges + exactly 6 exempt creator edges.
        r = psycopg.connect(dsn, autocommit=True)
        try:
            ne = r.execute(
                "select count(*) from pg_auth_members am "
                "where (am.roleid in (select oid from pg_roles where rolname=any(%s)) "
                "    or am.member in (select oid from pg_roles where rolname=any(%s))) "
                "  and not (am.member='postgres'::regrole "
                "     and am.roleid in (select oid from pg_roles where rolname=any(%s)) "
                "     and am.admin_option and not am.set_option and not am.inherit_option)",
                (APP_ROLES_6, APP_ROLES_6, APP_ROLES_6)).fetchone()[0]
            ck(ne == 0, "2-RESIDUE-%s: %d non-exempt membership edge(s) (self-grant leaked!)" % (where, ne))
            ex = r.execute(
                "select count(*) from pg_auth_members am where am.member='postgres'::regrole "
                "and am.roleid in (select oid from pg_roles where rolname=any(%s)) "
                "and am.admin_option and not am.set_option and not am.inherit_option",
                (APP_ROLES_6,)).fetchone()[0]
            ck(ex == 6, "2-RESIDUE-%s: exempt creator edges=%d want=6 (creator edge damaged!)" % (where, ex))
        finally:
            r.close()

    conn = psycopg.connect(dsn)   # autocommit=False; the whole proof is rolled back.
    try:
        cur = conn.cursor()
        for r in SERVING:                        # transient SET self-grants on the 3 login roles
            cur.execute('grant "%s" to postgres with set true' % r)

        # records_api: reference reachability (read REF for FK parents); writes + audit denied.
        cur.execute("set role records_api")
        r_cid = cur.execute("select asset_class_id from records.asset_classes limit 1").fetchone()
        ck(r_cid is not None, "2-api-cannot-read-asset_classes (reference reachability)")
        r_tid = cur.execute("select template_id from records.form_templates limit 1").fetchone()
        ck(r_tid is not None, "2-api-cannot-read-form_templates (reference reachability)")
        for t in WP:
            expect_denied(cur, "insert into records.%s default values" % t, "2-api-write-%s" % t)
        expect_denied(cur, "select 1 from records.audit_log", "2-api-read-audit_log")
        cur.execute("reset role")
        if r_cid is None or r_tid is None:
            raise RuntimeError("2-precondition: no reference row visible to records_api for FK parents")
        cid, tid = r_cid[0], r_tid[0]

        # records_intake_writer: allowed write path (fires trg_audit); reserved-col + audit denied.
        cur.execute("set role records_intake_writer")
        aid = cur.execute("insert into records.assets(asset_tag,name,asset_class_id) values(%s,%s,%s) "
                          "returning asset_id", (tag, tag, cid)).fetchone()[0]        # write ALLOWED
        sid, st = cur.execute("insert into records.form_submissions(template_id,asset_id) values(%s,%s) "
                              "returning form_submission_id, status", (tid, aid)).fetchone()
        ck(st == "draft", "2-writer-insert-status-default (%r != draft)" % st)
        expect_denied(cur, "update records.form_submissions set status='approved' where false", "2-writer-reserved-col-status")
        expect_denied(cur, "update records.persons set worker_class='1099' where false", "2-writer-reserved-col-worker_class")
        expect_denied(cur, "select 1 from records.audit_log", "2-writer-read-audit_log")
        cur.execute("reset role")

        # records_api: RLS+grant+security_invoker REACHABILITY -- sentinel-qualified so a
        # pre-existing prod row cannot false-green it. Sees ITS OWN asset + the joined view row.
        cur.execute("set role records_api")
        na = cur.execute("select count(*) from records.assets where asset_tag=%s", (tag,)).fetchone()[0]
        ck(na >= 1, "2-api-reachability-assets (writer row not visible to records_api via RLS)")
        nv = cur.execute("select count(*) from records.v_asset_test_history where asset_tag=%s",
                         (tag,)).fetchone()[0]
        ck(nv >= 1, "2-api-reachability-v_asset_test_history (sentinel row not visible via security_invoker view)")
        cur.execute("reset role")

        # records_auditor: THIS run's trigger fired -- EXACT row-PK sentinel (table_name+row_pk for
        # our OWN asset + submission inserts; row_pk = to_jsonb(rec)->>pk_col per 048). Immune to any
        # pre-existing/concurrent audit rows. Operational read denied.
        cur.execute("set role records_auditor")
        n_aud_asset = cur.execute("select count(*) from records.audit_log "
                                  "where table_name='assets' and row_pk=%s and action='insert'",
                                  (str(aid),)).fetchone()[0]
        ck(n_aud_asset >= 1, "2-audit-trigger-assets (no audit row for the sentinel asset insert)")
        n_aud_fs = cur.execute("select count(*) from records.audit_log "
                               "where table_name='form_submissions' and row_pk=%s and action='insert'",
                               (str(sid),)).fetchone()[0]
        ck(n_aud_fs >= 1, "2-audit-trigger-form_submissions (no audit row for the sentinel submission insert)")
        expect_denied(cur, "select 1 from records.assets", "2-auditor-read-assets")
        cur.execute("reset role")

        # No explicit revoke: the whole txn is rolled back below (authoritative undo), restoring
        # each creator edge to its set=false exempt state (an explicit revoke would DELETE it).
    finally:
        conn.rollback()   # undoes self-grants + writer rows + audit rows (sequences DO advance)
        conn.close()

    # --- RESIDUE VERIFICATION ---
    # Phase A: bucket-2 self-grants fully undone (membership; pg_catalog only).
    membership_residue("A-post-proof")

    # Phase B: per-run sentinel ABSENCE on every touched table + exact audit row-PK absence, read
    # through the app roles in their OWN rolled-back txn (bare postgres cannot read records objects).
    conn2 = psycopg.connect(dsn)   # autocommit=False
    try:
        c2 = conn2.cursor()
        c2.execute('grant "records_api" to postgres with set true')
        c2.execute('grant "records_auditor" to postgres with set true')
        c2.execute("set role records_api")
        na2 = c2.execute("select count(*) from records.assets where asset_tag=%s", (tag,)).fetchone()[0]
        ck(na2 == 0, "2-RESIDUE-sentinel-assets: %d sentinel asset row(s) survived rollback" % na2)
        nfs2 = c2.execute("select count(*) from records.form_submissions fs "
                          "join records.assets a on a.asset_id=fs.asset_id "
                          "where a.asset_tag=%s", (tag,)).fetchone()[0]
        ck(nfs2 == 0, "2-RESIDUE-sentinel-form_submissions: %d survived rollback" % nfs2)
        c2.execute("reset role")
        c2.execute("set role records_auditor")
        a_left = c2.execute("select count(*) from records.audit_log "
                            "where (table_name='assets' and row_pk=%s) "
                            "   or (table_name='form_submissions' and row_pk=%s)",
                            (str(aid), str(sid))).fetchone()[0]
        ck(a_left == 0, "2-RESIDUE-audit_log: %d sentinel audit row(s) survived rollback" % a_left)
        c2.execute("reset role")
    finally:
        conn2.rollback()   # undo the phase-B transient self-grants
        conn2.close()

    # Phase C: reassert membership cleanup INCLUDING the phase-B reader's transient self-grants.
    membership_residue("C-post-residue-read")
    return len(fails) == n0


def main():
    dsn = os.environ.get("SUPABASE_PROD_DSN")
    if not dsn:
        print("ERROR: SUPABASE_PROD_DSN not injected")
        return 3
    try:
        b1 = bucket1_static(dsn)
    except Exception as e:
        fails.append("BUCKET1-exception: %s: %s" % (type(e).__name__, _redact(str(e))[:200]))
        b1 = False
    try:
        b2 = bucket2_behavioral(dsn)
    except Exception as e:
        fails.append("BUCKET2-exception: %s: %s" % (type(e).__name__, _redact(str(e))[:200]))
        b2 = False
    print("[%s] BUCKET1-static-invariants" % ("PASS" if b1 else "FAIL"))
    print("[%s] BUCKET2-behavioral-set-role" % ("PASS" if b2 else "FAIL"))
    print("[INFO] BUCKET3-session-user-semantics: CARRIED from Phase-3B branch proof "
          "(actor_role=session_user attribution; positive assert_serving_identity; "
          "direct-login runtime). NOT re-proved on prod (SET ROLE keeps session_user=postgres). "
          "Deferred until a real direct-login consumer is minted.")
    for f in fails:
        print("   - " + f)
    ok = not fails
    print("ADAPTED_ACCEPTANCE_OVERALL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
