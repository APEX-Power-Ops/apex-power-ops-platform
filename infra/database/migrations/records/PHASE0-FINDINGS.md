# PHASE 0 FINDINGS - Records Supabase-Compat capability probe

**Branch:** `rdmxqwkrcebdhalodcgi` (name `compat-phase0`, parent `fxoyniqnrlkxfligbxmg`, org `xeabvbahdqwhidenufsh`), created 2026-07-06.
**Branch env:** PostgreSQL `17.6`; connected role `postgres` with `rolsuper = false` (non-superuser managed `postgres`, faithfully reproducing prod). Fresh-branch schemas = `{auth, public, storage}`; `records` schema absent (records is harness-tracked, not in `supabase_migrations`).
**Transport:** All capability probes ran via the authorized MCP `execute_sql(project_id=<branch_ref>)` as the non-super `postgres`, using session-local plpgsql `EXCEPTION`-capture harnesses (each probe self-contained: unique scratch roles/objects + teardown; per-statement SQLSTATE captured). This is the plan-permitted route for "controlled, savepoint-isolated capability probes." The host-`psql`-over-branch-DSN stack apply (Task 0.1) and the `supabase_probe.py` DSN self-proof (Task 0.7) are PENDING a working branch DSN (see "Branch DSN status").
**Residue:** Every probe tore down its scratch roles/objects (verified `schema:0; roles=none` per probe). The whole branch is deleted at Phase-0 end (ultimate cleanup). Nothing in this lane touched prod.

**AMENDED 2026-07-06:** A mandatory IRP cross-engine audit (Codex exit 0 + Claude completeness) + gap-closure probes (P0.8a-c) extended and refined these verdicts. See "## IRP CROSS-ENGINE AUDIT + GAP CLOSURE" - read it before parameterizing Phase 2 (it adds D1-D6: the choreography is proven technique NOT shipped code, the assert refinement extends to 045+047, 049 needs SET-ROLE + an oracle fix, and postgres BYPASSES FORCE RLS).

**AMENDED AGAIN 2026-07-06 v2 (post-operator-review):** Phase 0 is **DISCOVERY COMPLETE, NOT a closed ops gate.** A hardened probe run on a second branch FLIPPED Gate A - the creator edge is **SELF-ESCALATABLE** (`postgres` uses its admin option to self-grant SET+INHERIT, then `SET ROLE` succeeds), so the earlier "accept admin-only edge (lean b)" is **WITHDRAWN**. `supabase_probe.py` was hardened (per-run suffix + no blind pre-drops; full-object-type ownership transfer table/view/seq/func/schema; DDL envelope under owner context; a baked-in `gate_a_escalation` hard-gate). See "## 2026-07-06 ADDENDUM v2" at the END - it supersedes the Gate A section below.

---

## Decision-variable summary (parameterizes Phase 2 / Task 2.0)

| Variable | Verdict | Phase-2 action |
|---|---|---|
| Object-ownership default | Objects created by non-super `postgres` are `postgres`-owned (schema, table, view, sequence, function) | 046 `postgres`-ownership assumption HOLDS; NO `supabase_admin`-owner flag |
| A2 role-attr settability | Only `NOSUPERUSER`/`SUPERUSER` unsettable (42501); `nobypassrls, noreplication, nocreatedb, nocreaterole, login/nologin` all settable | Drop only the `NOSUPERUSER` keyword + assert `rolsuper=false`; KEEP the rest |
| Gate A (creator edge) | **SELF-ESCALATABLE** - admin-only on creation, but `postgres` self-grants SET+INHERIT via its admin option -> `SET ROLE` SUCCEEDS (NOT "non-usable") | **HARD STOP at Task 2.0**: pre-provision roles OR operator explicitly exempts the trusted `postgres`/applier; the assert refinement is necessary-but-insufficient. See ADDENDUM v2 |
| Gate B (policy binding) | `CREATE POLICY ... TO <custom_role>` SUCCEEDS | Keep `TO records_api, records_intake_writer`; stale "authenticated" header = docs-only |
| Ownership choreography | Forward + cross-role + reverse B->A all proven | Copy-ready choreography below |
| 046_down reclaim-to-postgres | `grant postgres to <custom>` REJECTED (42501) | Down-parity ESCALATION at Task 2.0 |
| DDL envelope | All 045-049 command classes permitted (owner-transfer needs WITH SET) | No un-probed op class remains |

---

## A2 - role-attribute settability (resolves A2)

Probe: create `probe_attr NOLOGIN` (non-super `postgres`), then each `ALTER ROLE` individually inside a savepoint.

| Clause | Result | Phase-2 decision |
|---|---|---|
| `NOSUPERUSER` | FAIL `42501` | DROP keyword (role is already non-super by default); add `rolsuper=false` assert |
| `SUPERUSER` (escalation) | FAIL `42501` | n/a - confirms non-super `postgres` cannot escalate (prod-match) |
| `NOBYPASSRLS` | ok (settable) | KEEP |
| `NOREPLICATION` | ok (settable) | KEEP |
| `NOCREATEDB` | ok (settable) | KEEP |
| `NOCREATEROLE` | ok (settable) | KEEP |
| `LOGIN` / `NOLOGIN` | ok (settable) | KEEP |

Note: positive `BYPASSRLS`/`REPLICATION` grants also succeeded, but the migrations set the `NO*` forms, so this is immaterial (recorded for completeness). Only the `SUPERUSER` bit is gated. `final_flags` after the sequence: `super=false, bypassrls=true, repl=true, createdb=false, createrole=false, login=true` (reflects the last grant tested per attribute).

Evidence: `create=ok;nosuperuser=FAIL:42501;nobypassrls=ok;noreplication=ok;nocreatedb=ok;nocreaterole=ok;login=ok;superuser=FAIL:42501;bypassrls_grant=ok;replication_grant=ok;`

---

## Gate A - CREATEROLE self-grant + membership revoke (resolves Decision Gate A)

**Verdict (CORRECTED 2026-07-06 v2): GATE_A = SELF-ESCALATABLE creator edge. HARD STOP at Task 2.0.** The auto-edge is admin-only ON CREATION, but `postgres` can USE its admin option to self-grant SET+INHERIT and then `SET ROLE` into the role - so it is NOT "non-usable." The "## 2026-07-06 ADDENDUM v2" section (escalation proof) SUPERSEDES the "admin-only, non-usable" characterization in the rest of this section.

On the managed branch, when the non-super `postgres` creates a role, an auto membership grant is created:

```
grantor = supabase_admin,  member = postgres,  admin_option = true,  set_option = FALSE,  inherit_option = FALSE
```

- The edge is **un-removable by `postgres`**: `revoke <role> from postgres` runs without error but is a no-op (edge persists - `postgres` is not the grantor); `revoke <role> from postgres granted by supabase_admin` FAILS `42501`; `revoke admin option for <role> from postgres` runs "ok" but does not change `admin_option` (no-op).
- The edge is **admin-only ON CREATION** (`set_option = false`, `inherit_option = false` -> `postgres` cannot IMMEDIATELY `SET ROLE` into it), **BUT it is SELF-ESCALATABLE (CORRECTED v2):** because `postgres` holds `admin_option`, it can `GRANT <role> TO postgres WITH SET TRUE` (and `INHERIT TRUE`), which ADDS a second membership row (`grantor=postgres, set=true, inherit=true`) after which `SET ROLE` SUCCEEDS. So it is a latent privilege-escalation path, NOT a benign residue. Proof in "## 2026-07-06 ADDENDUM v2".

**Impact on 046:** 046's terminal assert (`raise exception '... LOGIN role(s) are members of records_owner'`) checks mere membership. Because `postgres` (a LOGIN role) remains an un-removable member of every role it creates, that assert AS WRITTEN would trip. **Phase-2 refinement (046):** change the terminal check to flag only SET/INHERIT-USABLE membership by a LOGIN role - i.e. `WHERE (set_option OR inherit_option)` - not bare membership. Per the v2 self-escalation finding, that refinement is NECESSARY BUT NOT SUFFICIENT: `postgres` can make `set_option=true` at will via its admin option, so no in-migration assert can constrain `postgres`. Invariant-8 isolation of `postgres` from `records_owner` is achievable ONLY by pre-provisioning the roles (so `postgres` is never their creator/admin) OR by an explicit operator decision that the trusted `postgres`/applier is exempt from invariant 8. See ADDENDUM v2.

**Task 2.0 operator decision (hard stop):**
- (a) pre-provisioned-role path (roles minted out-of-band by `supabase_admin`/dashboard so `postgres` is never the creator, avoiding the edge), OR
- (b) explicit operator acceptance of the admin-only residue.
- **Lean: (b)** - the residue is provably non-usable (no SET/INHERIT; `SET ROLE` blocked) and inherent to Supabase's CREATEROLE model; (a) adds out-of-band role provisioning outside the migration. Operator decides.

---

## Gate B - custom-role policy binding (resolves Decision Gate B)

**Verdict: GATE_B = keep `TO <custom role>`. Clean GO.**

`CREATE POLICY p_probe ON <rls table> FOR SELECT TO <custom_role> USING (true)` SUCCEEDS as the non-super `postgres`. Policies may target `records_api` / `records_intake_writer` directly. The stale "rebind to authenticated" header in 045 is reconciled as documentation only (no functional change; no silent switch to `authenticated`).

Evidence: `create_role=ok;create_schema=ok;create_table=ok;enable_rls=ok;create_policy_to_custom=ok;`

---

## Ownership-transfer choreography (Task 0.4) - copy-ready

Proven red/green. Key rules confirmed on managed Supabase:

1. **RED (wrong pattern) fails.** `set role <target>; alter <obj> owner to <target>` -> FAIL `42501` (the target does not yet own the object). Confirms the corrected rule.
2. **Forward transfer runs AS the current owner** holding `WITH SET` membership in the new owner. `grant <new_owner> to <current_owner> with set true, inherit false, admin false` first; then `alter <obj> owner to <new_owner>` executed AS the current owner (e.g. `postgres` for 046). Do NOT `set role` into the target for the transfer.
3. **Receiving owner needs CREATE on the object's schema** (PG16+ rule) - CONFIRMED REQUIRED (`needed_create_on_schema = yes` for both forward and cross-role). Grant `grant create on schema <s> to <new_owner>` before the transfer; the receiving owner also needs `USAGE` on the schema for later operations.
4. **Transfer the schema owner LAST** (after its contained objects), or the object transfers lose schema CREATE.
5. **Owner-only ops run under `set role <new_owner>` AFTER the transfer** - `alter table ... force row level security` under `set role <new_owner>` SUCCEEDS (validates the `INHERIT FALSE` + `SET ROLE` design; `INHERIT FALSE` membership alone does not confer owner authority).
6. **Cross-role forward (048: A -> B)**: `grant B to A with set true`; receiver B needs CREATE+USAGE on the schema; `set role A; alter <obj> owner to B; reset role`; then `revoke B from A`. PROVEN.
7. **Reverse B -> A (048_down)**: `grant A to B with set true`; B needs `USAGE` on the (A-owned) schema; `set role B; alter <obj> owner to A; reset role`; then `revoke A from B`. PROVEN.
8. **Cyclic-membership constraint**: `grant B to A with set` and `grant A to B with set` are MUTUALLY EXCLUSIVE (Postgres rejects mutual membership, SQLSTATE `0LP01`). The forward (up) and reverse (down) SET-grants must be granted-then-revoked PER PHASE, never held simultaneously - which matches up vs down running at different times.

Forward evidence: `grant_a_to_pg_set=ok;RED_as_target=FAIL:42501;fwd_t_after_screate=ok;fwd_v=ok;fwd_sq=ok;fwd_f=ok;fwd_schema=ok;owner_only_forcerls=ok;grant_b_to_a_set=ok;cross_t_after_screate=ok;` Reverse evidence: `create_t_as_a=ok;fwd_a_to_b=ok;rev_b_to_a=ok;` (all residue clean).

### 046_down reclaim-to-`postgres` - BLOCKED (down-parity escalation)

`grant postgres to <custom_role> with set true` is REJECTED (`42501`) on managed Supabase. Therefore the `records_owner -> postgres` reclaim that a literal 046_down needs is **not achievable**: neither `set role records_owner; alter ... owner to postgres` (records_owner cannot be granted SET membership in `postgres`) nor a `postgres`-executed transfer (postgres cannot `SET ROLE` into records_owner; its edge is set=false) works.

**Available option-space (for Task 2.0):** cross-role transfer to ANY custom role IS proven (finding 6/7). So a viable down design is to reclaim ownership to a **dedicated custom reclaim-owner** (not `postgres`), or to drop-and-recreate, or to accept that down does not restore `postgres`-ownership. **This is an operator design decision at Task 2.0** (down-parity), not resolvable by choreography alone.

---

## DDL envelope (Task 0.6)

All command classes 045-049 use are permitted for the non-super `postgres` (savepoint-isolated, torn down):

`revoke create on schema public from public = ok; enable row level security = ok; force row level security = ok; create policy = ok; drop policy = ok; alter view set (security_invoker=true) = ok; create index = ok; create or replace function (security definer) = ok; revoke execute ... from public = ok; create trigger = ok;`

`alter function ... owner to <role>` returned `42501` ONLY because no `WITH SET` grant to the target existed at that point; with the choreography's `grant <owner> to postgres with set` it succeeds (see choreography). No un-probed op class remains.

**Managed event triggers visible** (none block our DDL): `issue_graphql_placeholder(sql_drop)`, `pgrst_ddl_watch(ddl_command_end)`, `pgrst_drop_watch(sql_drop)`, `issue_pg_cron_access(ddl_command_end)`, `issue_pg_net_access(ddl_command_end)`, `issue_pg_graphql_access(ddl_command_end)`.

---

## Branch DSN status (Tasks 0.1 / 0.7 - host psql) - RESOLVED

Host->branch connectivity is PROVEN (Olares host reaches the branch over IPv6 and via the `aws-1-us-west-2` Supavisor pooler tenant). The branch has its OWN DB password (distinct from prod, not exposed by MCP `create_branch`/`get_project`). The operator provisioned the branch DB password out-of-band into Infisical `prod` (`SUPABASE_BRANCH_PW`); the working connection is the tenant-qualified pooler user `postgres.rdmxqwkrcebdhalodcgi@aws-1-us-west-2.pooler.supabase.com:5432/postgres` (plain `postgres` on the pooler fails - Supavisor needs the tenant suffix; a hand-built URI also risks silent truncation on un-percent-encoded special chars, so the raw password + discrete `PG*` args is the robust value-silent path). With that, Task 0.1 (001-044 apply + real-schema owner inventory) and Task 0.7 (`supabase_probe.py` DSN self-proof) both completed - see "Status vs plan".

---

## Status vs plan

- Task 0.2 (A2) - DONE. Task 0.3 (Gate A) - DONE (unavoidable-edge; escalate at 2.0). Task 0.4 (choreography) - DONE (forward+cross-role+reverse proven; 046_down reclaim BLOCKED -> escalate). Task 0.5 (Gate B) - DONE (keep). Task 0.6 (DDL envelope) - DONE. Object-ownership default (0.1 core) - DONE.
- Task 0.1 full stack apply + Task 0.7 DSN self-proof - DONE 2026-07-06 (host `psql` over the branch DSN, once the operator provisioned the branch DB password). Task 0.1: records 001-044 applied GREEN (44/44); real-schema owner inventory = `schema_owner=postgres`, `distinct_owners=postgres`, `supabase_admin_owned_objs=0`. Task 0.7: `supabase_probe.py` self-proof PASS (all 6 classes match this baseline, exit 0).
- Branch TEARDOWN 2026-07-06: `delete_branch` succeeded; only `main` remains. Pre-teardown scratch-residue = `roles: none, schemas: none`. Zero prod impact throughout. **Phase 0 DISCOVERY COMPLETE** (not a closed ops gate; a v2 branch later flipped Gate A - see ADDENDUM v2).
- Phase 2 is decision-gated at Task 2.0 on: Gate A acceptance (lean b), the 046_down down-parity design, and the assert refinement (045+046+047 per D3).

---

## IRP CROSS-ENGINE AUDIT + GAP CLOSURE (2026-07-06)

A mandatory adversarial cross-engine audit (workflow `wd0q6ie2g`: Claude completeness lens + Codex exit 0 + synthesis; the correctness agent dropped mid-response on a connection error, its ground covered by the Codex pass) of these findings vs the ACTUAL 045-049 migration bodies surfaced coverage gaps and amendments. All were closed empirically on the same branch (probes P0.8a-c, residue clean each). The earlier per-variable verdicts stand except where amended here.

### Root-cause framing (both engines converged)

Migrations 045-049 were authored for a SUPERUSER executor: 046's header says "Runs as the superuser admin; superuser bypasses FORCE" and 045 says "D2-A: tables stay postgres-owned; FORCE RLS inert on the superuser owner." Prod/branch `postgres` is NON-super AND still `rolbypassrls=true`. Adapting to the non-super executor IS Phase 2's job; the amendments below make its parameters precise.

### Gate-A edge shape - REPRODUCIBILITY CONFIRMED (closes the load-bearing flag)

P0.8a created 3 fresh postgres-owned roles: EACH auto-edge = `supabase_admin -> postgres, admin=true, set=false, inherit=false`, and `postgres` could NOT `SET ROLE` into any (42501). The false/false shape is reproducible for postgres-CREATEd roles, so the `WHERE (set_option OR inherit_option)` assert refinement is SAFE. (SEEDED postgres memberships carry set/inherit=true - a DIFFERENT code path; the migrations CREATE their roles, so the CREATE-path false/false shape governs.)

### D1 - the proven choreography is TECHNIQUE, not yet SHIPPED CODE (HIGH)

The ownership choreography above is proven-viable, but the CURRENT 046/048/049 (and 046_down/045_down) bodies do NOT encode it - 046 [2] is a bare `alter ... owner to records_owner` loop with NO `grant records_owner to postgres with set` and NO `grant create on schema` (exactly the RED pattern proven to fail 42501). This is EXACTLY the Phase-2 rewrite (Tasks 2.2/2.4/2.5); "copy-ready" means copy-ready TECHNIQUE to encode, NOT that a literal apply of the shipped bodies passes. DO NOT apply 045-049 as-is to a managed branch.

### D3 - assert-refinement scope EXTENDS to 045 + 047 (not just 046) (HIGH)

The un-removable creator edge (postgres is an admin member of every role it creates; `revoke ... from postgres` is a silent no-op) trips the zero-membership asserts in THREE files:
- 045 [1] "an app role retains a role membership (escalation path)" - bare membership touching records_api/records_intake_writer in EITHER direction -> trips.
- 046 [4] "LOGIN role(s) are members of records_owner" -> trips (already noted).
- 047 (final) "membership edge(s) touch an audit role" -> trips.
Phase-2 PARAMETER: apply the `WHERE (set_option OR inherit_option)` refinement (usable-membership only) to the asserts in 045 (Task 2.1), 046 (Task 2.2), AND 047 (Task 2.3). Keep the both-direction `revoke` loops (harmless) but do not rely on them.

### D5 - 049 CREATE TRIGGER must run under SET ROLE records_owner + fix the self-oracle (HIGH/MED)

P0.8b (faithful 049 model: table owned by OWNER, trigger fn owned by a DIFFERENT role FN with EXECUTE granted to OWNER):
- `create trigger ... as bare postgres` (non-owner) -> FAIL 42501.
- `set role OWNER; create trigger ...; reset role` -> OK.
Phase-2 PARAMETER (Task 2.5): 049 MUST create each trigger under `set role records_owner` (the table owner), with EXECUTE on `fn_audit_capture` reachable to records_owner. A bare-postgres 049 fails 42501.
Additionally (Codex): 049 derives its trigger SET and its terminal count oracle BOTH from `information_schema.role_column_grants`, which is visibility-filtered to the current role as grantor/grantee. If 049 ever runs as a role lacking that visibility it yields 0 rows -> 0 triggers -> got==want==0 GREEN with audit SILENTLY DISABLED. Phase-2 PARAMETER: derive `want` INDEPENDENTLY of `role_column_grants` visibility (e.g. from the writer-grant table set directly) OR assert the running role is the grantor.

### D4 - FORCE RLS enforces for non-bypass roles but `postgres` BYPASSES it (MED)

P0.8c (DML negative control: FORCE-RLS table, 3 rows, policy `TO reader USING(false)`):
- as `postgres` (rolbypassrls=true): sees 3 rows -> BYPASSES FORCE RLS.
- as the non-bypass OWNER under FORCE RLS with no permissive policy: sees 0 rows -> RLS binds the owner.
(The reader sub-test returned 42501 only because postgres lacked SET membership in the reader role - a probe limitation, not an enforcement result; the owner result already proves enforcement against a non-bypass principal.)
IMPLICATION: 046's FORCE-RLS objective is proven at the ENFORCEMENT level ONLY for non-bypass roles. Every operational `postgres`/`service_role` (BYPASSRLS) session bypasses records RLS regardless of FORCE - consistent with and DEPENDENT ON the Gate-9 Option-B serving premise (the serving DSN connects AS a NON-bypass role, `records_api`). Phase-2/3 PARAMETER (Task 3.3): add a DML negative-control assert (records RLS actually blocks a non-bypass role), not just catalog `relforcerowsecurity` state; confirm the serving DSN role is non-bypass.

### D6 - down-path positive PUBLIC/object grants on non-owned objects (P2)

`045_down [d3] grant execute on all routines in schema records to public` (and 048's positive schema/table grants) run while objects may be owned by records_owner/records_fn_owner. In P0.8b positive `grant usage`/`grant select` as `postgres` SUCCEEDED while postgres held set-membership in the owner, so these likely pass during the choreography window; the robust pattern is to issue them under `set role <current owner>`. Task-2.4/2.5/down PARAMETER: issue down-path and cross-owner PUBLIC/object grants under `set role` the current owner.

### Bottom line

The per-variable verdicts are sound; the audit ENRICHED the Phase-2 parameter set (D1 encode-choreography, D3 assert scope 045/046/047, D5 trigger-under-set-role + oracle fix, D4 enforcement + negative control, D6 grants-under-set-role) and CONFIRMED the load-bearing Gate-A shape. Task 2.0 must additionally: (i) resolve the executor-identity premise (superuser-authored vs non-super apply); (ii) rewrite 046/048/049 + downs to the choreography BEFORE any managed apply; (iii) extend the assert refinement to 045/047; (iv) fix the 049 oracle; (v) add the DML negative control + confirm non-bypass serving role; (vi) design 046_down reclaim to a dedicated custom reclaim-owner (postgres-reclaim is impossible). Cross-engine record: workflow `wd0q6ie2g`.

---

## 2026-07-06 ADDENDUM v2 - Gate A ESCALATION (verdict flip) + probe hardening

Prompted by an operator code-review verdict (CHANGES REQUESTED): Phase 0 is a strong DISCOVERY artifact but not a closed ops gate; the Gate-A "admin-only" claim was not fully proven, and `supabase_probe.py` under-covered the Phase-4 precondition. A second throwaway branch (`mfakxwgdugpzbdtqimdb`, DELETED zero-residue; identical env: PG 17.6, `postgres` non-super + `rolbypassrls=true`) resolved both. Supabase status was OPERATIONAL (the June-30 incident is fully resolved).

### GATE A ESCALATION - CONFIRMED (the "accept admin-only" lean is WITHDRAWN)

The scary path the earlier probe skipped: can `postgres`, holding ADMIN option on the auto-edge, self-grant SET/INHERIT? Probe result:
- `edge_on_create`: `supabase_admin->postgres, admin=true, set=false, inh=false`.
- `grant sp_esc to postgres with set true` -> **ACCEPTED**; `... with inherit true` -> **ACCEPTED**.
- `edge_after_selfgrant`: `supabase_admin:admin=true/set=false/inh=false ; postgres:admin=false/set=true/inh=true` (a SECOND row, grantor=`postgres`, SET+INHERIT true).
- `set role sp_esc` -> **SUCCESS_ESCALATED**.

So the creator edge is **self-escalatable to full SET+INHERIT membership**: `postgres` can become `records_owner`/`records_fn_owner` at will. It is NOT "admin-only, non-usable." Combined with `postgres` being `rolbypassrls=true`, the applier `postgres` is isolated from the owner roles by NOTHING in-migration.

**Task-2.0 Gate-A decision (HARD STOP) - the two real options:**
- (a) **Pre-provision the roles out-of-band** (minted by `supabase_admin`/dashboard so `postgres` is never their creator -> no admin edge -> no self-escalation). The only way to satisfy a STRICT invariant 8 (`postgres` cannot reach `records_owner`).
- (b) **Explicit operator decision that the trusted `postgres`/applier is EXEMPT** from invariant 8 (it is already `bypassrls`+`createrole`; the NON-admin app/serving roles - `records_api`/`service_role`/`authenticated`/`anon` - do NOT receive the auto-admin-edge, so THEY stay isolated). Under (b), restate invariant 8 to scope it to non-admin roles and document that `postgres` self-escalation is accepted.
- The `WHERE (set_option OR inherit_option)` assert refinement (D3) is NECESSARY for the non-admin roles BUT CANNOT constrain `postgres` (it self-escalates `set_option=true`), so it is not a mitigation for the `postgres` path. NO silent acceptance.

### supabase_probe.py hardening (P1-2 / P2-3 addressed)

- **Collision-safe naming:** every scratch role/object carries a per-run suffix (uuid, or `SUPABASE_PROBE_RUN` override); NO blind pre-drops - teardown drops ONLY the suffixed names created this run.
- **Full-object-type ownership transfer:** the choreography probe now transfers table + view + sequence + function + schema (was table-only), forward + owner-only-under-set-role + cross-role A->B + reverse B->A + `grant postgres to <custom>` (blocked). Validated on the v2 branch: `RED=FAIL:42501; fwd_table/view/seq/func/schema=ok; owner_only=ok; cross=ok; reverse=ok; grant_postgres_to_custom=REJECTED:42501` (residue clean).
- **DDL envelope under OWNER context:** new `ddl_envelope` class exercises revoke-public-create, enable/force RLS, create/drop policy, `security_invoker` set+reset, create index, SECURITY DEFINER function, revoke-execute-from-public, and the down-path positive `grant execute ... to public` - all under `set role <owner>`. Validated: all 14 = ok.
- **Baked `gate_a_escalation` HARD-GATE:** the probe now runs the self-escalation test and hard-fails (exit nonzero) if `SET ROLE` succeeds after self-grant. So on managed Supabase the probe correctly reports FAIL until Gate A is resolved (fail-closed) - by design, not a bug.

### Choreography detail (Phase-2 relevant): receiver schema-CREATE must be granted by the schema owner

A non-owner `GRANT create on schema ... to <receiver>` only WARNs and no-ops (it does not error), so the receiver silently lacks CREATE and the transfer fails `42501`. The receiver's schema `CREATE`/`USAGE` must be granted WHILE `postgres` still owns the schema, OR by the current schema owner under `set role`. (Relevant to 048: `records_fn_owner`'s CREATE on the `records` schema must be granted by `records_owner`, not by `postgres` after 046 moved the schema.)

### Status

Phase 0 = **DISCOVERY COMPLETE** (envelope characterized; hardened reusable probe committed) - NOT a closed ops gate. Do NOT start Phase 2 migration rewrites until Task 2.0 explicitly records: (1) Gate A - pre-provision vs exempt-`postgres`; (2) 046_down reclaim - dedicated reclaim-owner vs drop/recreate vs non-`postgres` target; (3) executor premise - non-super `postgres` path remains the intended model. Both branch DSNs in Infisical (`SUPABASE_BRANCH_PW`/`SUPABASE_BRANCH_DSN`) are stale (both branches deleted).
