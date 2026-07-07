# Records Supabase-Compat -- Phase 3B Branch Proof (evidence)

Date: 2026-07-07. Branch under test: records/supabase-compat @ HEAD c892c164.
Executed on a throwaway Supabase preview branch of the governed prod project
(parent fxoyniqnrlkxfligbxmg), created and torn down within the session. Prod
was never a mutation target; every write phase guarded on the branch identity
(supabase_migrations count = 111) so prod (~200) could not be hit. Applied over
the branch's DIRECT connection as the real managed non-super `postgres` (the
authentic applier identity; rolbypassrls=true confirmed). Value-silent
throughout (password injected via Infisical prod env, never echoed).

## Environment
- Branch parent-migration replay stopped at 111/~200 on an UNRELATED tcc
  migration (20260601191219 d1_sst_bridge_add_cols_and_staging). Per-migration
  replay is transactional -> branch cleanly at 111. `public.employees` present
  (records/044 FK target); `records` schema absent at start. Not a records
  concern; recorded for completeness.

## Phase A -- base 001-044
- All 44 base files applied byte-exact from git: 44/44 OK.
- Post-base: 15 records tables, RLS=0, policies=0, records roles=0,
  schema owner=postgres (the FRESH case for 045's owner pre-check).

## Phase B -- RED (unadapted 045 from main)
- psql exit 3. ERROR: 42501: permission denied to alter role.
  DETAIL: "Only roles with the SUPERUSER attribute may alter roles with the
  SUPERUSER attribute." (the `alter role ... nosuperuser` at line 21).
- Residue check after failure: tables=15 roles=0 rls=0 policies=0 == pristine
  base. The BEGIN..COMMIT transaction rolled back completely; no residue.
- Conclusion: the UNADAPTED stack genuinely cannot apply as the managed
  non-super postgres.

## Phase C -- GREEN (adapted 045-049 from HEAD c892c164)
- All 5 adapted migrations applied: OK.
- Posture: RLS 16/16, FORCE 16/16, policies=28, records roles=6,
  schema_owner=records_owner (046 transferred from postgres), audit_log present,
  fn_audit_capture present, audit_triggers=6.

## Phase E -- Gate-5 invariants (all verified)
- INV1 RLS enabled: 16/16 tables.
- INV2 FORCE RLS: 16/16 tables.
- INV3 policies: 15 tables policy-covered; neta_table_source_links is
  RLS+FORCE+no-policy+owner-only-grant = deny-all by design (D10 "not served").
- INV4 no PUBLIC: 0 object grants to PUBLIC, 0 schema USAGE to PUBLIC.
- INV5 grant allowlist: NONE outside {records_api, records_intake_writer,
  records_auditor, records_owner, records_fn_owner}. Matrix is least-privilege
  (api=SELECT on served tables; auditor=SELECT audit_log; intake_writer=column
  INSERT/UPDATE; fn_owner=audit writer; owner=owner).
- INV6 audit infra: audit_log RLS+FORCE, fn_audit_capture present, 6 triggers.
- INV7 D-A: 0 usable app-role membership edges. Only edges are the 6 exempt
  postgres creator edges (set=false, inherit=false, admin=true) -- the ratified
  trusted-applier posture (postgres would have to self-grant to escalate).
- INV8 ownership: schema + 15 tables/views owned by records_owner; audit_log
  owned by records_fn_owner BY DESIGN (048: FORCE-RLS on the definer's own table
  so the INSERT policy is not a no-op); functions split (fn_set_updated_at ->
  records_owner, fn_audit_capture -> records_fn_owner).

## Phase D -- D4 DML negative control
- Bypass asymmetry: postgres=true; records_api/records_intake_writer/
  records_auditor=false.
- Negative (RLS/grant enforced against non-bypass roles):
  * records_api INSERT assets -> BLOCKED (permission denied).
  * records_api SELECT audit_log -> BLOCKED (permission denied).
- Positive (intended paths):
  * records_intake_writer INSERT assets -> ALLOWED; fired the audit trigger.
  * records_api SELECT assets -> ALLOWED (via policy).
  * records_auditor SELECT audit_log -> ALLOWED (1 audit row from the writer's
    insert -> the SECURITY DEFINER capture path works end-to-end).
- D4 core: postgres SELECT audit_log -> ALLOWED (BYPASS). This is the reason the
  serving DSN role must be the non-bypass records_api, never postgres.
- Role impersonation used a transient postgres self-grant of SET (Gate-A
  trusted-applier property); revoked after. INV7 recheck post-cleanup = 0.

## Advisors (Supabase security)
- No records-schema ERROR. records-relevant: 1 INFO (source_links deny-all,
  intended) + 1 WARN (function_search_path_mutable on the BASE fn_set_updated_at,
  pre-existing/out-of-lane-scope; the SECURITY DEFINER fn_audit_capture is NOT
  flagged -> it already pins search_path). The 87 ERROR / 55 WARN are all against
  the inherited parent schema (public/tcc/...), pre-existing prod, out of scope.

## Teardown
- delete_branch -> success. list_branches -> only main remains. Zero residue.

## Session incident (recorded)
- A value-silence slip (`${VAR:-NO}` instead of `${VAR:+yes}`) printed the prod
  DSN incl. password to the transcript. Flagged immediately; operator rotated
  BOTH the prod DB password and the branch password, updated Infisical
  (SUPABASE_PROD_DSN) and added SUPABASE_BRANCH_PW. Remediation complete.

## Verdict
UNADAPTED = RED (42501), ADAPTED = GREEN, all 7 invariants + D4 verified on the
REAL managed non-super postgres, zero-residue teardown. The compat lane's
adaptation is proven on the authoritative substrate.
