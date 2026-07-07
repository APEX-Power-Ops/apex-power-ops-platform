-- 049_records_audit_triggers.sql - attach fn_audit_capture to exactly the
-- tables records_intake_writer may INSERT/UPDATE (the writer-grant set),
-- passing each table's single-column PK name. Excludes audit_log (recursion)
-- and neta_table_source_links (owner-only, D7).
--
-- SUPABASE-COMPAT (compat lane Task 2.5, plan REV 5 / Task-2.0 Step 3 + D5):
-- adapted to apply as the NON-SUPER managed postgres applier. Two D5 fixes:
--   * SELF-ORACLE (D5-B, load-bearing correctness): the ORIGINAL 049 derived BOTH
--     its trigger set AND its terminal `want` count from
--     information_schema.role_column_grants, which is CURRENT-USER-VISIBILITY
--     scoped (surfaces only grants the running role granted or received). Under a
--     low-visibility running role it yields 0 rows -> 0 triggers created ->
--     got==want==0 GREEN with AUDIT SILENTLY DISABLED (the exact D5 hazard). This
--     rewrite derives the writer-grant table set ONCE from the raw catalog ACLs -
--     pg_class.relacl (table-level) AND pg_attribute.attacl (column-level, which is
--     how 045 records the writer's INSERT/UPDATE - the grants are COLUMN-scoped, so
--     a relacl-only read would itself yield 0) - via aclexplode, filtered
--     grantee=records_intake_writer / privilege in (INSERT,UPDATE) / schema=records /
--     DISTINCT table / EXCLUDING audit_log + neta_table_source_links. aclexplode over
--     catalog ACL columns is readable by ANY role (NOT visibility-filtered), so this
--     yields the TRUE writer-grant set regardless of the running role. The SAME
--     derivation feeds the create loop and the `want` count (they are IDENTICAL by
--     construction), and a `want > 0` floor makes a regression to a 0-yielding
--     visibility-scoped oracle FAIL LOUD instead of silent-greening.
--   * CREATE TRIGGER under SET ROLE records_owner (D5-A): the target tables are
--     records_owner-owned; CREATE/DROP TRIGGER needs table OWNERSHIP -> bare
--     non-super postgres 42501s. records_owner ALSO needs EXECUTE on
--     records.fn_audit_capture() at CREATE-TRIGGER time (048 revoked PUBLIC execute;
--     only records_fn_owner holds it). So: temp authority = grant records_owner +
--     records_fn_owner to the applier WITH SET (INHERIT/ADMIN false); a TRANSIENT
--     `grant execute on function records.fn_audit_capture() to records_owner` issued
--     BY the function owner records_fn_owner (under SET ROLE records_fn_owner); then
--     SET ROLE records_owner, run the create-trigger loop over the visibility-
--     independent set, RESET ROLE; then REVOKE the transient EXECUTE grant (the
--     trigger keeps firing after creation - trigger execution does NOT re-check the
--     creator's EXECUTE at fire time). Revoke ALL temp memberships before the
--     terminal asserts. The terminal asserts (pg_trigger/pg_class/pg_namespace joins
--     by nspname/relname - NO records.*::regclass casts) need no schema USAGE, so
--     they run as plain non-super postgres AFTER reset + revoke. A temp-authority
--     residue assert (046 [4] / 048 form) closes out.
BEGIN;
SET client_encoding TO 'UTF8';

-- [t0] re-establish 049's OWN transient authority (048 revoked its own). The applier
-- takes WITH SET into records_owner (to CREATE/DROP triggers on the owner-owned
-- tables) and into records_fn_owner (to issue the transient EXECUTE grant AS the
-- function owner). Both INHERIT FALSE / ADMIN FALSE. All revoked in [t4].
do $$
begin
  execute format('grant records_owner to %I with set true, inherit false, admin false', current_user);
  execute format('grant records_fn_owner to %I with set true, inherit false, admin false', current_user);
end $$;

-- [t1] the TRANSIENT EXECUTE grant, issued BY the function owner records_fn_owner.
-- records_owner needs EXECUTE on fn_audit_capture at CREATE-TRIGGER time (a trigger's
-- function must be executable by the creating role when the trigger is created). 048
-- revoked PUBLIC execute and the function is owned by records_fn_owner, so ONLY the
-- owner can grant it - hence SET ROLE records_fn_owner to issue the grant (a non-owner
-- GRANT only WARNs/no-ops). REVOKED in [t3] once the triggers exist.
do $$
begin
  set role records_fn_owner;
  grant execute on function records.fn_audit_capture() to records_owner;
  reset role;
end $$;

-- [t2] create the triggers UNDER the table owner records_owner (CREATE TRIGGER needs
-- table ownership). The writer-grant table set is derived ONCE, visibility-INDEPENDENT,
-- from the raw catalog ACLs (relacl + attacl via aclexplode) - NOT from
-- information_schema.role_column_grants (D5-B). aclexplode on catalog ACL columns is
-- readable by any role, so the set is the TRUE writer-grant set regardless of the
-- SET-ROLE'd identity. A `want = 0` floor here is fail-closed: a real records
-- deployment HAS writer tables, so an empty set is itself a failure (the silent-
-- disable hazard turned into a loud raise).
do $$
declare
  t         record;
  pk_col    text;
  npk       int;
  want      int;
begin
  set role records_owner;

  -- (0) fail-closed floor on the visibility-independent writer-grant set.
  select count(*) into want from (
    select distinct c.relname
      from pg_class c
      join pg_namespace ns on ns.oid = c.relnamespace
      left join lateral aclexplode(c.relacl) ra on true
      left join lateral (
        select a.privilege_type as ptype, a.grantee as gtee
          from pg_attribute att,
               lateral aclexplode(att.attacl) a
         where att.attrelid = c.oid and att.attnum > 0 and not att.attisdropped
      ) ca on true
     where ns.nspname = 'records'
       and c.relkind = 'r'
       and c.relname not in ('audit_log','neta_table_source_links')
       and (
         (ra.grantee = 'records_intake_writer'::regrole and ra.privilege_type in ('INSERT','UPDATE'))
         or (ca.gtee = 'records_intake_writer'::regrole and ca.ptype in ('INSERT','UPDATE'))
       )
  ) s;
  if want = 0 then
    raise exception '049: writer-grant table set is EMPTY (visibility-independent oracle yielded 0 - audit would be SILENTLY DISABLED)';
  end if;

  -- (1) create trg_audit on EXACTLY that set (same derivation as the floor above).
  for t in
    select distinct c.relname as table_name
      from pg_class c
      join pg_namespace ns on ns.oid = c.relnamespace
      left join lateral aclexplode(c.relacl) ra on true
      left join lateral (
        select a.privilege_type as ptype, a.grantee as gtee
          from pg_attribute att,
               lateral aclexplode(att.attacl) a
         where att.attrelid = c.oid and att.attnum > 0 and not att.attisdropped
      ) ca on true
     where ns.nspname = 'records'
       and c.relkind = 'r'
       and c.relname not in ('audit_log','neta_table_source_links')
       and (
         (ra.grantee = 'records_intake_writer'::regrole and ra.privilege_type in ('INSERT','UPDATE'))
         or (ca.gtee = 'records_intake_writer'::regrole and ca.ptype in ('INSERT','UPDATE'))
       )
  loop
    -- single-column PK name for this table
    select count(*) into npk
      from pg_index i join pg_class c on c.oid=i.indrelid
      join pg_namespace ns on ns.oid=c.relnamespace
     where ns.nspname='records' and c.relname=t.table_name and i.indisprimary;
    if npk <> 1 then raise exception '049: %.% has no single primary key', 'records', t.table_name; end if;
    select a.attname into pk_col
      from pg_index i join pg_class c on c.oid=i.indrelid
      join pg_namespace ns on ns.oid=c.relnamespace
      join pg_attribute a on a.attrelid=c.oid and a.attnum = any(i.indkey)
     where ns.nspname='records' and c.relname=t.table_name and i.indisprimary
       and array_length(i.indkey,1)=1;
    execute format('drop trigger if exists trg_audit on records.%I', t.table_name);
    execute format(
      'create trigger trg_audit after insert or update or delete on records.%I '
      'for each row execute function records.fn_audit_capture(%L)', t.table_name, pk_col);
  end loop;

  reset role;
end $$;

-- [t3] revoke the transient EXECUTE grant to records_owner, issued AS the function
-- owner records_fn_owner. The triggers keep firing without it (trigger execution does
-- not re-check the creator's EXECUTE at fire time; the definer function runs as its
-- own owner). After this, records_owner holds NO privilege on fn_audit_capture.
do $$
begin
  set role records_fn_owner;
  revoke execute on function records.fn_audit_capture() from records_owner;
  reset role;
end $$;

-- [t4] revoke the two temp memberships taken in [t0] (records_owner, records_fn_owner)
-- BEFORE the terminal asserts. revoke-if-exists is safe unconditionally.
do $$
begin
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_owner from %I', current_user);
  end if;
  if exists (select 1 from pg_auth_members am
               join pg_roles ow on ow.oid=am.roleid and ow.rolname='records_fn_owner'
               join pg_roles m on m.oid=am.member and m.rolname=current_user) then
    execute format('revoke records_fn_owner from %I', current_user);
  end if;
end $$;

-- assert: trigger set == writer-grant set; no trigger on audit_log or source_links.
-- Derived visibility-INDEPENDENTLY (same relacl+attacl aclexplode as the create loop),
-- so `want` cannot silently collapse to 0. These are catalog reads by nspname/relname
-- (NO records.*::regclass cast), so they need no schema USAGE and run as plain
-- non-super postgres after [t3]/[t4].
do $$
declare got int; want int;
begin
  select count(*) into want from (
    select distinct c.relname
      from pg_class c
      join pg_namespace ns on ns.oid = c.relnamespace
      left join lateral aclexplode(c.relacl) ra on true
      left join lateral (
        select a.privilege_type as ptype, a.grantee as gtee
          from pg_attribute att,
               lateral aclexplode(att.attacl) a
         where att.attrelid = c.oid and att.attnum > 0 and not att.attisdropped
      ) ca on true
     where ns.nspname = 'records'
       and c.relkind = 'r'
       and c.relname not in ('audit_log','neta_table_source_links')
       and (
         (ra.grantee = 'records_intake_writer'::regrole and ra.privilege_type in ('INSERT','UPDATE'))
         or (ca.gtee = 'records_intake_writer'::regrole and ca.ptype in ('INSERT','UPDATE'))
       )
  ) s;
  if want = 0 then raise exception '049: writer-grant table set is EMPTY at terminal assert (audit SILENTLY DISABLED)'; end if;
  select count(*) into got from pg_trigger tg join pg_class c on c.oid=tg.tgrelid
    join pg_namespace ns on ns.oid=c.relnamespace
   where ns.nspname='records' and tg.tgname='trg_audit' and not tg.tgisinternal;
  if got <> want then raise exception '049: trigger count % <> writer-grant table count %', got, want; end if;
  if exists (select 1 from pg_trigger tg join pg_class c on c.oid=tg.tgrelid
             join pg_namespace ns on ns.oid=c.relnamespace
             where ns.nspname='records' and c.relname in ('audit_log','neta_table_source_links')
               and tg.tgname='trg_audit')
    then raise exception '049: trg_audit present on audit_log or source_links'; end if;
end $$;

-- temp-authority residue assert (046 [4] / 048 form): no NON-admin role holds a USABLE
-- (set_option OR inherit_option) membership INTO records_owner or records_fn_owner; and
-- records_owner holds NO EXECUTE on fn_audit_capture (the transient grant was revoked).
-- The two transient memberships (applier->records_owner, applier->records_fn_owner) and
-- the transient EXECUTE grant were revoked in [t3]/[t4]; the trusted postgres applier is
-- EXEMPT (member <> postgres) and admin-only creator edges (set=inherit=false) are not
-- flagged. A surviving SET/INHERIT edge from a non-admin role would be a real escalation.
do $$
declare n int; e int;
begin
  select count(*) into n from pg_auth_members am
     join pg_roles ow on ow.oid=am.roleid and ow.rolname in ('records_owner','records_fn_owner')
     join pg_roles m on m.oid=am.member
   where (am.set_option or am.inherit_option)
     and m.oid <> 'postgres'::regrole;
  if n>0 then raise exception '049: % non-admin role(s) hold a usable membership into an owner role (escalation path)', n; end if;
  select count(*) into e
    from pg_proc p, lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
   where p.pronamespace = (select oid from pg_namespace where nspname='records')
     and p.proname = 'fn_audit_capture'
     and a.grantee = 'records_owner'::regrole and a.privilege_type = 'EXECUTE';
  if e>0 then raise exception '049: records_owner retains EXECUTE on fn_audit_capture (transient grant not revoked)'; end if;
end $$;

COMMIT;
