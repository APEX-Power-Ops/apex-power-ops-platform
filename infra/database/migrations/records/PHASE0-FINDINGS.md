# PHASE 0 FINDINGS - Records Supabase-Compat capability probe

**Branch:** `rdmxqwkrcebdhalodcgi` (name `compat-phase0`, parent `fxoyniqnrlkxfligbxmg`, org `xeabvbahdqwhidenufsh`), created 2026-07-06.
**Branch env:** PostgreSQL `17.6`; connected role `postgres` with `rolsuper = false` (non-superuser managed `postgres`, faithfully reproducing prod). Fresh-branch schemas = `{auth, public, storage}`; `records` schema absent (records is harness-tracked, not in `supabase_migrations`).
**Transport:** All capability probes ran via the authorized MCP `execute_sql(project_id=<branch_ref>)` as the non-super `postgres`, using session-local plpgsql `EXCEPTION`-capture harnesses (each probe self-contained: unique scratch roles/objects + teardown; per-statement SQLSTATE captured). This is the plan-permitted route for "controlled, savepoint-isolated capability probes." The host-`psql`-over-branch-DSN stack apply (Task 0.1) and the `supabase_probe.py` DSN self-proof (Task 0.7) are PENDING a working branch DSN (see "Branch DSN status").
**Residue:** Every probe tore down its scratch roles/objects (verified `schema:0; roles=none` per probe). The whole branch is deleted at Phase-0 end (ultimate cleanup). Nothing in this lane touched prod.

---

## Decision-variable summary (parameterizes Phase 2 / Task 2.0)

| Variable | Verdict | Phase-2 action |
|---|---|---|
| Object-ownership default | Objects created by non-super `postgres` are `postgres`-owned (schema, table, view, sequence, function) | 046 `postgres`-ownership assumption HOLDS; NO `supabase_admin`-owner flag |
| A2 role-attr settability | Only `NOSUPERUSER`/`SUPERUSER` unsettable (42501); `nobypassrls, noreplication, nocreatedb, nocreaterole, login/nologin` all settable | Drop only the `NOSUPERUSER` keyword + assert `rolsuper=false`; KEEP the rest |
| Gate A (creator edge) | UNAVOIDABLE admin-only edge (un-removable, non-privilege-usable) | STOP/escalate at Task 2.0; refine 046 terminal assert (see below) |
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

**Verdict: GATE_A = unavoidable-edge (admin-only, non-privilege-usable). STOP/escalate at Task 2.0.**

On the managed branch, when the non-super `postgres` creates a role, an auto membership grant is created:

```
grantor = supabase_admin,  member = postgres,  admin_option = true,  set_option = FALSE,  inherit_option = FALSE
```

- The edge is **un-removable by `postgres`**: `revoke <role> from postgres` runs without error but is a no-op (edge persists - `postgres` is not the grantor); `revoke <role> from postgres granted by supabase_admin` FAILS `42501`; `revoke admin option for <role> from postgres` runs "ok" but does not change `admin_option` (no-op).
- The edge is **NOT privilege-usable**: `set_option = false` and `inherit_option = false` -> `postgres` cannot `SET ROLE` into the created role (`42501`) and does not inherit its privileges. It is a membership-management (ADMIN) residue only, not a privilege-escalation path.

**Impact on 046:** 046's terminal assert (`raise exception '... LOGIN role(s) are members of records_owner'`) checks mere membership. Because `postgres` (a LOGIN role) remains an un-removable member of every role it creates, that assert AS WRITTEN would trip. **Phase-2 refinement (046):** change the terminal check to flag only SET/INHERIT-USABLE membership by a LOGIN role - i.e. `WHERE (set_option OR inherit_option)` - not bare membership. This preserves invariant 8 (no LOGIN role holds a usable SET/INHERIT path into `records_owner`) while tolerating the admin-only edge.

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

## Branch DSN status (Tasks 0.1 / 0.7 - host psql)

Host->branch connectivity is PROVEN (Olares host reaches the branch over IPv6 and via the `aws-1-us-west-2` Supavisor pooler tenant). The operator-provisioned `SUPABASE_BRANCH_DSN` (Infisical `prod` env) targets the correct branch ref (`prod_ref_in_dsn=0`), but the **password is rejected on both the tenant-qualified pooler format and the direct format** -> the stored branch password does not match the branch's actual `postgres` password. Correct form: `postgres.rdmxqwkrcebdhalodcgi@aws-1-us-west-2.pooler.supabase.com:5432/postgres` (tenant-qualified pooler user) with the branch's real DB password (reset/reveal in the Supabase dashboard for the branch project). Until fixed, Task 0.1's full 001-044 stack apply + real-schema owner inventory and Task 0.7's DSN self-proof are pending; the object-ownership default (the decision-relevant part of 0.1) is already proven via the scratch-object probe above, and `supabase_probe.py` is validated via `execute_sql` transport.

---

## Status vs plan

- Task 0.2 (A2) - DONE. Task 0.3 (Gate A) - DONE (unavoidable-edge; escalate at 2.0). Task 0.4 (choreography) - DONE (forward+cross-role+reverse proven; 046_down reclaim BLOCKED -> escalate). Task 0.5 (Gate B) - DONE (keep). Task 0.6 (DDL envelope) - DONE. Object-ownership default (0.1 core) - DONE.
- Task 0.1 full stack apply + Task 0.7 DSN self-proof - PENDING branch DSN password fix.
- Phase 2 is decision-gated at Task 2.0 on: Gate A acceptance (lean b), the 046_down down-parity design, and the 046 terminal-assert refinement.
