# Schema-Placement Packet 01 (RE-SCOPED, rev 2): Public Exposure Hardening + Scratch Relocate - Design Spec

- Date: 2026-07-10. Rev 2.1 = post technical-authority review (findings 1-5 folded in; see section 1b). GATE
  STATUS: APPROVED FOR READ-ONLY P0 ONLY; implementation/write gate HELD pending P0 evidence + exact-SQL review.
- Status: DRAFT design material. NOT implementation-ready until technical-authority approval is recorded
  (PLATFORM-DATA-AND-SCHEMA-STRATEGY-2026-04-12 section 1.1 Technical Authority Gate).
- Supersedes: v1 (BLOCKED by cross-engine IRP). Provenance: v1 + schema_placement_01_IRP_synthesis.md.
- Substrate: prod Supabase fxoyniqnrlkxfligbxmg (managed non-super postgres).
- Governing authority (current): APEX-PLATFORM-OPERATING-ARCHITECTURE-2026-06-18, section 2.4 - operator-only
  human authority gates for auth/ingress, schema mutation, production-write; section 3 (the ai_tasks first-slice
  prohibition is LIFTED, section-2 gates preserved -> ai_* work is admitted-but-gated, not forbidden); section 2.8
  schema-role identity invariant. The APEX-OPS-...-2026-05-15 protocol is SUPERSEDED (folded into the 2026-06-18
  doc); its old sections 7/8 are cited as provenance only. Technical Authority Gate: PLATFORM-DATA section 1.1.
- This packet requires operator gates on: (a) an auth/ingress change (REVOKE), (b) a schema mutation (CREATE
  SCHEMA + SET SCHEMA), (c) production-write. Each is a separate operator write-GO. Nothing else is admitted; no
  business-state mutation, no auth/ingress WIDENING, no controller-authority widening as a side effect.

---

## 1. Why this is a rewrite (IRP verdict) - unchanged from rev 1
Cross-engine IRP (Claude 8-agent grounded-audit + Codex, both prod+repo grounded) BLOCKED v1. The clean slice
collapsed from ~28 objects to 2 inert scratch tables. Decisive: mcp_* is a LIVE control-plane backend; ai_* is
wired to 10 anon/authenticated-EXECUTE INVOKER RPCs + an unqualified-insert trigger (a move breaks writes for
every caller); tcc_*_pre_rebuild is not dead archive (kept tcc_test_plans FKs into it, marked must_keep). The
urgent, non-breaking security fix is REVOKE + definer-view neutralization, no schema move. Record:
schema_placement_01_IRP_synthesis.md.

## 1a. What rev 2 changed (from the technical-authority review, each prod-verified)
- F1: `authenticated` access to mcp_* is an INTENTIONAL contract (migration 000008: 8 policies granting
  authenticated packet/artifact/priority reads + self-scoped queue/job + review-decision insert). Revoking it is
  a contract RETIREMENT, not automatically non-breaking. -> split 01b into 01b-core (anon, unambiguous) and
  01b-auth (authenticated, GATED). If retired, DROP the 8 authenticated policies + comments in the SAME txn (no
  dormant policies).
- F2 (verified on prod): `mcp_external_action_audits` (migration 000009) is NOT present on fxoyniqnrlkxfligbxmg -
  my `mcp%`-across-all-schemas query returns exactly 6 tables + 2 views. So 01b live scope = 6+2. But this is a
  repo<->prod DRIFT: 000009 is repo-defined + unapplied here, and creates the table with NO anon/auth revoke ->
  it would be BORN anon-exposed when applied. Forward-hardening item added (section 6a).
- F3 + F5 (verified on prod): `apex_tcc_runtime` (a plausible control-plane role) has rolbypassrls=FALSE and no
  role memberships; the app nonetheless reads the RLS-on mcp_* tables live (so it must effectively connect as a
  bypassrls role - postgres/service_role - OR apex_tcc_runtime is vestigial). Catalog inference cannot resolve
  this. Converting the 2 definer views to security_invoker is the ONLY 01b mechanism that could break the control
  plane, and its safety is unprovable without the deployed DSN. -> the 01b mechanism is PURE REVOKE (leave views
  SECURITY DEFINER; remove the anon grant -> 42501). security_invoker becomes OPTIONAL deferred defense-in-depth,
  gated on the F5 positive proof (section 6b).
- F4: REVOKE targets PUBLIC + anon + authenticated (not only direct ACL entries); assert EFFECTIVE privilege via
  has_table_privilege (accounts for PUBLIC + membership), not relacl inspection. (Verified: PUBLIC has no direct
  grant; anon/authenticated/service_role/apex_tcc_runtime do; the last two are PRESERVED.)
- F6: `ai_knowledge` EXCLUDED from 01a (repo provenance flags it as deployed orchestration state; 0 rows/0 db-deps
  do not prove 0 external callers) -> deferred to 01c with the rest of ai_*.
- F7: P0 is READ-ONLY catalog inspection only. No trial ALTER+ROLLBACK (acquires locks / is a prod write) - DDL
  capability is exercised only under the P1 write-GO.
- Operator call: `_009_rollback_snapshot` + `_phase3_load_manifest` = retain-and-relocate to `archive`, APPROVED.
  Do NOT describe `_009` as retired / retention-resolved; retention remains a SEPARATE open decision
  (reference/tcc/G2-RULES-GUIDE.md:95). "retention accepted" is removed as an 01a precondition.

## 1b. Rev 2.1 deltas (technical-authority findings 1-5; APPROVED FOR READ-ONLY P0)
1b.1 Authenticated-consumer branch has TWO mandatory outcomes (not "01b-auth or nothing"):
  - No authenticated Data-API consumer -> execute 01b-auth: REVOKE authenticated + DROP the 8 authenticated
    policies + update comments.
  - A consumer exists -> 01b-auth cannot merely defer. The 2 summary views are SECURITY DEFINER over self-scoped
    RLS tables (mcp_job_run_summary_v joins requested_by-scoped rows), so any authenticated user reading them sees
    CROSS-USER rows (definer bypasses the per-user policy). In that branch section 6b becomes MANDATORY: prove the
    runtime role, then convert the views to security_invoker OR move the consumer behind the control-plane API.
    Packet 01 is NOT "fully closed" while authenticated cross-user view exposure remains.
  Operator evidence (2026-07-10): NO repo-visible authenticated Data-API consumer (control-plane uses direct SQL;
  no .from('mcp_*') / /rest/v1/mcp_* callsite; the 000008 policies prove intended capability, not current use).
  P0 combines this with PostgREST access history + an explicit operator declaration; absent any known external
  signed-in client, the recommendation is 01b-auth RETIREMENT.
1b.2 Mechanically-separate tranche ACLs + exact post-states (supersedes any "FROM PUBLIC, anon, authenticated"
  phrasing for 01b-core):
  - 01b-core: REVOKE ... FROM PUBLIC, anon ONLY. authenticated behavior must match its captured baseline (untouched).
  - 01b-auth: REVOKE ... FROM authenticated + DROP the 8 auth policies + update comments.
  - After core: anon -> PostgREST 42501 (Postgres error code; HTTP 401/403); authenticated UNCHANGED.
  - After auth: BOTH roles -> 42501.
1b.3 Forward hardening = an EXECUTABLE idempotent canonical migration (not a doc note). 01b's prod-write IS
  delivered as a NEW idempotent migration in the control-plane migrations lane
  (apps/control-plane-api/supabase/migrations/, per its README) that conditionally hardens: the 6 current tables;
  the 2 views; AND mcp_external_action_audits guarded by `to_regclass('public.mcp_external_action_audits') IS NOT
  NULL`. Do NOT rewrite migration 000009 unless P0 proves it is unapplied in EVERY governed environment; a later
  idempotent migration is safer + drift-resistant (also fixes the born-exposed bootstrap on next apply).
1b.4 Durable drift assertion: extend apps/control-plane-api/scripts/check_schema_drift.py with a focused ACL/view-
  posture check over the 6-or-7 tables + 2 views (assert anon has NO effective privilege; authenticated per the
  chosen 01b-auth outcome). Prevents a future grant silently undoing the pure-REVOKE boundary. Packet deliverable.
1b.5 Advisor residual allowlist: record the EXACT two accepted security_definer_view objects
  {public.mcp_job_run_summary_v, public.mcp_task_packet_summary_v}, expected count = 2. Acceptance FAILS on any
  ADDITIONAL security_definer_view finding OR any renewed effective anon privilege. (If the 1b.1 consumer-exists
  branch converts the views to invoker, the expected count becomes 0.)

## 2. Program framing + this packet's place - unchanged
Security-led public lockdown + canonical promotion. North-star = 62 public ERROR advisor findings -> 0. THIS
packet delivers ONLY 01a + 01b-core (01b-auth is gated) and does not claim the north-star. Deferred: 01c (ai_*),
01d (tcc topology), Buckets 3/4/5, task_7dd40f4f.

## 3. Scope (on prod fxoyniqnrlkxfligbxmg, verified 2026-07-10)
IN:
- 01b-core (PRIMARY, urgent, unambiguous, non-breaking): REVOKE ALL on the 6 mcp_* tables + 2 summary views FROM
  PUBLIC, anon. Closes the anon view-leak (the sole anon vector) + the dormant anon table grants. No contract
  retired; no view semantic change; control-plane roles (postgres/service_role/apex_tcc_runtime) untouched.
- 01b-auth (GATED): REVOKE authenticated on the same 8 objects + DROP the 8 authenticated policies + update
  comments, in one txn - ONLY after the P0 gate proves no legitimate authenticated Data-API consumer OR the
  operator explicitly approves retiring the authenticated read/insert contract.
- 01a (tiny): relocate `_009_rollback_snapshot` + `_phase3_load_manifest` to a new private `archive` schema.
OUT (deferred, section 6): 01c (ai_* incl. ai_knowledge), 01d (tcc_test_plans/tcc_test_results + tcc_*_pre_rebuild),
Buckets 3/4/5, task_7dd40f4f, mcp_* SCHEMA relocation, the optional security_invoker DiD (section 6b).

## 4. 01b design - public exposure hardening (PRIMARY; PURE REVOKE, no view ALTER, no code change)
Target (verified present on prod): 6 tables (mcp_job_runs, mcp_lane_priorities, mcp_local_action_queue,
mcp_review_decisions, mcp_task_packets, mcp_validation_artifacts) + 2 views (mcp_job_run_summary_v,
mcp_task_packet_summary_v). Verified: RLS ON on all 6 tables, no policy admits anon; the sole anon leak WITHIN THE mcp_* CLUSTER is the 2
SECURITY DEFINER summary views (bypass RLS -> ~17 rows to anon). NOTE (review F1): project-wide, prod has 31 anon-
reachable public SECURITY DEFINER views; this packet closes anon on ONLY these 2 - the other 29 (incl.
financial/ops: v_scope_financials, v_projects_full, v_master_operations, v_tcc_*) remain OPEN + OUT OF SCOPE (section 8). relacl grants: postgres, anon, authenticated,
service_role, apex_tcc_runtime; PUBLIC has no direct grant.

### 01b-core (anon) - the admitted auth/ingress change, with validation
Action: REVOKE ALL ON <the 6 tables + 2 views> FROM PUBLIC, anon. (Preserve postgres, service_role,
apex_tcc_runtime.) No ALTER VIEW; views stay SECURITY DEFINER so the control-plane's definer-reads are unchanged.
Result: anon SELECT on the views -> 42501 permission-denied (leak closed); anon table grants removed (were already
RLS-blocked; removes the dormant relacl that would re-expose on any future RLS change).
Precondition (P0, read-only): confirm no legitimate anon Data-API consumer (grep already shows only the
control-plane via privileged direct SQL; anon is not a control-plane connection role).

### 01b-auth (authenticated) - GATED contract change
The 8 policies in migration 000008 are an INTENTIONAL authenticated contract (packet/artifact/priority reads;
self-scoped queue/job; review-decision insert). Gate (one of):
(a) P0 proves no legitimate authenticated Data-API consumer remains, OR (b) operator explicitly approves retiring
the contract. If proceeding: in ONE txn - REVOKE ALL ... FROM authenticated on the 8 objects + DROP the 8
authenticated policies (mcp_task_packets_auth_read, mcp_review_decisions_auth_read,
mcp_review_decisions_auth_insert_self, mcp_local_action_queue_auth_read_own, mcp_local_action_queue_auth_insert_own,
mcp_job_runs_auth_read_requested, mcp_validation_artifacts_auth_read, mcp_lane_priorities_auth_read) + update the
table comments to record the retirement. Do NOT leave the policies dormant after the grant is revoked (an accidental
future re-grant would silently reopen the surface). The service_role_all policies stay.

### 01b acceptance (both sub-lanes)
- REST re-probe with an anon key AND a real authenticated JWT (test auth user), value-silent, bodies discarded:
  every hardened object on the old public path -> NO row-bearing 200/206; prefer exact 42501 / 401 classification.
- Effective-privilege asserts: has_table_privilege('anon', obj, 'SELECT') = false (01b-core); and
  has_table_privilege('authenticated', obj, 'SELECT') = false (01b-auth, if taken). PUBLIC verified no-privilege.
- Control-plane smoke: 8 /api/v1/ops/* routes 200 + a control-plane mcp read/write path exercised green
  (proves the revoke did not touch the app's effective role).
- Advisor: the 2 `security_definer_view` findings do NOT auto-clear on a pure revoke (the views are still definer);
  they clear only if the optional invoker DiD (section 6b) is later applied. 01b-core's advisor win is the anon
  reachability closure, not the definer-view lint. State this honestly (do not claim the lint clears).

## 5. 01a design - scratch relocate (exactly 2 tables)
Target (verified inert on prod): `_009_rollback_snapshot` (11,442 rows), `_phase3_load_manifest` (40 rows). Both
RLS-off, anon-reachable, NO inbound/outbound FK, NO dependent view, NO function/trigger ref, NO publication/cron
membership, NO app-source hit, owned by postgres. This is retain-and-relocate; retention is a SEPARATE open
decision (not resolved here; see G2-RULES-GUIDE.md:95).
Target schema `archive`. Schema-role declaration (satisfies OPERATING-ARCHITECTURE section 2.8): `archive` holds
non-authoritative, superseded/inert artifacts; it carries NO apparatus/equipment-identity FK and requires none
(its contents are dead artifacts outside the canonical relationship graph). Declared-not-linked, per the invariant.
Actions (the admitted schema mutation, with validation): CREATE SCHEMA archive (owner postgres); REVOKE ALL ON
SCHEMA archive FROM PUBLIC; keep archive OFF the PostgREST exposed-schema list (this + the per-object REVOKE are
the mechanism; ALTER DEFAULT PRIVILEGES on a fresh schema is a belt-and-suspenders no-op, per IRP). Then per table,
in one txn: capture pre-ACL (relacl); ALTER TABLE public.<t> SET SCHEMA archive; REVOKE ALL ON archive.<t> FROM
PUBLIC, anon, authenticated (load-bearing: the anon relacl travels with SET SCHEMA); assert object in archive AND
has_table_privilege('anon',...,'SELECT')=false AND has_table_privilege('authenticated',...,'SELECT')=false.
Acceptance: old public path -> 404; Accept-Profile: archive -> 406; object in archive; anon+auth effective priv
false; advisor: the 2 `rls_disabled_in_public` findings for these tables clear.

## 6. Deferred packets (named; explicit entry criteria)
- 01c AI RPC lockdown (now includes ai_knowledge). ENTRY: prove whether external agents call the 10 ai_* RPCs at
  runtime via the anon/authenticated key (callers outside the repo). THEN fix TOGETHER: EXECUTE grants, function
  schema-qualification/search_path pin, and the log_task_status_change trigger qualification/pin, then optional
  relocate. GATED per OPERATING-ARCHITECTURE section 2.4 (auth/ingress + schema mutation are operator-only) and
  must not widen controller authority / admit new ownership as a side effect (old 05-15 section 8, provenance).
- 01d TCC topology/archive. ENTRY: settle tcc_test_plans/tcc_test_results disposition (both 0 rows, marked
  must_keep). Do NOT relocate the pre_rebuild FK targets ahead of the referencer's disposition.
- Buckets 3/4/5 + task_7dd40f4f: separate program packets.

### 6a. Forward-hardening = an EXECUTABLE idempotent canonical migration, a THIS-PACKET deliverable (per 1b.3; supersedes any "its own packet" wording below)
Migrations 000007 (`CREATE TABLE IF NOT EXISTS public.mcp_*`) and 000009 (`mcp_external_action_audits`, unapplied
on prod) create public.mcp_* objects that inherit the public default ACL (anon=arwdDxtm) - BORN anon-exposed, and
a re-run would recreate exposed shells if any mcp_* were ever moved. RECOMMENDATION (control-plane-side change,
its own packet): amend the bootstrap migrations to REVOKE anon/authenticated at creation, so the surface is not
re-opened on the next apply and the 7th table is not born exposed when 000009 lands here. Surfaced as a
capability/drift gap (OPERATING-ARCHITECTURE section 2.7), not silently worked around.

### 6b. security_invoker (DEFERRED by default; MANDATORY in the authenticated-consumer-exists branch per 1b.1; F5-gated)
Converting the 2 summary views to security_invoker is valuable DiD but is the only 01b mechanism that could break
the control-plane. It is DEFERRED until the F5 positive proof (below) shows the control-plane's effective role
reads both views correctly under invoker semantics. If proven safe, a follow-on applies ALTER VIEW ... SET
(security_invoker=true) (preserving the exact definition/identity) + asserts the reloption, and the advisor
`security_definer_view` findings then clear.

## 7. Phases (nothing executes until the Technical Authority Gate approval is recorded)
P0 - READ-ONLY verification (catalog inspection + value-silent DSN reads; NO DDL, NO trial ALTER):
1. anon consumer: confirm no legitimate anon Data-API consumer of mcp_* (grep + reasoning; anon is not a
   control-plane role).
2. authenticated consumer GATE: determine whether any legitimate authenticated Data-API consumer of mcp_* remains
   (repo/client grep + operator knowledge). Output: proceed-with-01b-auth vs operator-retirement-decision-needed.
3. F5 positive control-plane proof: connect via the ACTUAL deployed control-plane DSN (value-silent; never echo)
   and record: current_user, rolsuper, rolbypassrls, memberships; effective SELECT on every underlying relation;
   POSITIVE reads from the 6 base tables AND both summary views. This confirms 01b-core is non-breaking and informs
   the deferred 6b invoker decision.
4. non-super postgres DDL prerequisites (catalog only): confirm ownership of all 01a/01b objects + has-privilege
   for CREATE on the DB (has_database_privilege), and role attributes (rolcreaterole/rolbypassrls). Do NOT execute
   a trial CREATE/ALTER - that is exercised under the P1 write-GO.
5. rollback capture: pre-ACL (relacl) for every 01a/01b object; RLS/policy state (for 01b-auth policy restore).
   (No view drop in this packet -> no viewdef/owner/reloptions capture needed unless 6b is later taken.)
6. confirm PostgREST schema-cache reload path (NOTIFY pgrst,'reload schema') for the P2 REST asserts.
P1 - each admitted action a SEPARATE operator write-GO, value-silent, in-txn asserts, stop-on-first-failed-assert:
  P1.1 01b-core (anon revoke). P1.2 01b-auth (authenticated revoke + policy drop) IF gated-in. P1.3 01a (create
  archive + relocate 2 tables). Order: 01b-core first (urgent security), then 01b-auth (if approved), then 01a.
P2 - acceptance (section 9).

## 8. Success metric (honest, scoped)
- 01b-core: the 6 mcp_* tables + 2 views are NOT anon-reachable (anon revoked -> 42501; dormant anon grants gone);
  control-plane fully functional. NOTE: the 2 `security_definer_view` advisor findings do NOT clear on a pure
  revoke (deferred to 6b); the win is anon reachability closure.
- 01b-auth (if taken): authenticated over-read closed; the 8 authenticated policies dropped; contract retirement
  recorded.
- 01a: 2 inert scratch tables relocated to `archive` + de-exposed; their 2 `rls_disabled_in_public` findings clear.
- EXPLICITLY NOT claimed: ai_* anon-RPC surface remains open (01c); mcp_* not relocated; tcc untouched; the 7th
  audit table + bootstrap-born-exposed drift is flagged not fixed (6a); 62->0 is the program north-star.
- RESIDUAL ANON SURFACE (review F1, IMPORTANT): 29 OTHER public anon-reachable SECURITY DEFINER views (of 31 total;
  incl. financial/ops v_scope_financials, v_projects_full, v_master_operations, v_tcc_*) remain OPEN, pre-existing +
  untouched. This packet does NOT materially close the project-wide anon Data-API surface; recommend a separate,
  higher-priority definer-view-hardening packet before the broader north-star is claimed.

## 9. Acceptance oracle (corrected per F3/F4)
- REST probe with anon key AND a real authenticated JWT (value-silent; status/content-range/content-profile only):
  old public path for every hardened/relocated object; success = NO row-bearing 200/206; prefer 42501/401/404/406
  classification. Run NOTIFY pgrst,'reload schema' before the re-probe.
- Effective-privilege asserts (not relacl): has_table_privilege(anon, ...)=false everywhere; has_table_privilege(
  authenticated, ...)=false where 01b-auth taken and on the 2 relocated tables.
- /rpc/ characterization: the 10 ai_* RPCs remain anon-reachable after this packet - EXPECTED (01c scope), recorded
  not failed. This packet does not close the anon-RPC surface; say so.
- control-plane smoke: 8 ops routes 200 + a control-plane mcp read/write path green.
- advisor delta enumerated pre/post: 2 rls_disabled_in_public clear (01a); the 2 security_definer_view findings do
  NOT clear until 6b.

## 10. Governance / authority gates
- Technical Authority Gate (PLATFORM-DATA section 1.1): DESIGN MATERIAL until the technical authority (operator)
  records review + approval; SQL authoring + prod migration-path approval gated on that. This rev + the IRP are the
  review inputs.
- OPERATING-ARCHITECTURE section 2.4: auth/ingress (REVOKE), schema mutation (CREATE/SET SCHEMA), production-write
  are operator-only gates -> each admitted action is a separate operator write-GO with validation. Nothing else
  admitted; no auth/ingress WIDENING (this is narrowing), no controller/ownership widening, no business-state
  mutation. section 2.8 schema-role invariant honored (archive role declared, section 5).
- Execution: host-canonical single-writer (author local -> scp -> commit host-side); value-silent; a focused
  IRP/Codex re-review of the FINAL migration SQL before any prod write; governed merge (branch -> PR -> CI green ->
  squash --delete-branch, no admin-bypass); OPERATING-ARCHITECTURE section-9-style closeout (smallest validation
  first; update status/handoff only after green; staged pathspecs; scoped commit; restore host parity).

## 11. Rollback (explicit; never automatic re-exposure)
- 01b-core / 01b-auth: re-GRANT from the captured pre-ACL; 01b-auth also re-creates the 8 dropped policies from the
  captured definitions. Capture BEFORE change (P0.5).
- 01a: ALTER ... SET SCHEMA public + re-grant from captured relacl. (No view drop.)
- All rollback EXPLICIT + operator-gated; a failed in-txn assert aborts that txn (no partial state); recovery is a
  deliberate decision, never an auto re-grant that re-exposes data.

## 12. Global constraints + IRP framing corrections
- Value-silent always (no secrets/full DSNs incl. the P0.3 control-plane DSN; classify SQLSTATE; probe records
  status/headers/row-counts only, never bodies; anon key + test-user JWT only, never service_role in probes).
  ASCII-only added lines. Never sed-edit a credential file. No destructive data op.
- Corrected framings: mcp_* is RLS-ON. The 2 summary views stay SECURITY DEFINER in this packet (invoker DiD
  deferred, 6b). apex_tcc_runtime has no bypassrls (drove the pure-revoke mechanism). PUBLIC has no direct grant
  but is REVOKE-targeted defensively; effective-privilege asserts (has_table_privilege), not relacl. ADP on a fresh
  schema is a no-op; per-object REVOKE + off-exposed-list are the mechanism. `mcp_external_action_audits` absent on
  prod (6+2 live scope); its bootstrap-born-exposed drift flagged (6a).

## Appendix A - verified object inventory (prod fxoyniqnrlkxfligbxmg, 2026-07-10)
01b tables (6): mcp_job_runs, mcp_lane_priorities, mcp_local_action_queue, mcp_review_decisions, mcp_task_packets,
mcp_validation_artifacts. 01b views (2, SECURITY DEFINER): mcp_job_run_summary_v, mcp_task_packet_summary_v.
01a scratch (2): _009_rollback_snapshot, _phase3_load_manifest. All owned by postgres; relacl grantees {postgres,
anon, authenticated, service_role, apex_tcc_runtime}; PUBLIC none. NOT present on prod: mcp_external_action_audits
(repo migration 000009, unapplied). Deferred: ai_* (incl. ai_knowledge) -> 01c; tcc_*_pre_rebuild +
tcc_test_plans/tcc_test_results -> 01d.
