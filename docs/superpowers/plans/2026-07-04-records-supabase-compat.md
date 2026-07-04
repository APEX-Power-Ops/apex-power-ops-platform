# Records Supabase-Compat Adaptation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make records migrations `045-049` (up + down) apply on Supabase's non-superuser managed `postgres`, preserving the Gate-5 guarantees, proven on a throwaway Supabase branch.

**Architecture:** A branch capability probe (Phase 0) empirically resolves two decision gates and the exact privilege choreography; a permanent `--apply-as-non-superuser` harness mode (Phase 1) makes the class CI-catchable; the migration adaptations (Phase 2) are authored FROM the Phase-0 findings; green/branch proofs (Phase 3) verify all invariants; packet corrections (Phase 4-prep) close the go/no-go gaps. Phase 2 is decision-gated on Phase 0 - its exact per-migration SQL is finalized at Task 2.0 from the recorded Phase-0 artifact, not guessed.

**Tech Stack:** PostgreSQL 17 (Supabase managed), the authorized Supabase MCP (`create_branch`/`delete_branch`/`execute_sql` for read/probe only), value-silent host `psql` over the branch DSN (stack apply), `run_validation.py` + `_dbtest.py` (Python/psycopg/psql harness), host worktree `/home/olares/code/apex/apex-records-supabase-compat` (branch `records/supabase-compat`).

**Revision:** rev 2 - folds the operator plan-audit (2026-07-04): P1 corrected ownership-transfer choreography (transfer AS the current owner, not while `SET ROLE`d into the target; 046 + 048 cross-role); P1 removed `apply_migration` (host `psql` only, no history rows); P2 per-probe unique scratch roles + teardown; P2 the applier-privilege probe is a scratch-write needing its own GO. Phase 0 is a single operator-gated run; Phase 2 does not fan out until Task 2.0 clears Gate A, Gate B, and the choreography.

## Global Constraints (verbatim from spec + lane discipline)

- **Host-canonical single-writer.** Author files locally (ASCII-checkable), `scp` to the compat worktree `/home/olares/code/apex/apex-records-supabase-compat`, run/commit host-side via `ssh olares-mesh`. NEVER touch the shipped `apex-records-gate9` worktree.
- **ASCII-only** added lines; **value-silent** (never print a DSN/password; use `${VAR:+ok}` not `${VAR:-...}`).
- **Disposable Supabase branches ONLY**; NOTHING in this lane mutates prod. Every branch is torn down with a zero-residue proof.
- **No `supabase_migrations` history rows** are written (records is harness-tracked). The branch stack apply uses ONLY value-silent host `psql` over the branch DSN; MCP `apply_migration` is FORBIDDEN in this lane (it writes a history row). MCP `execute_sql` is permitted ONLY for read-only inventory and the controlled, savepoint-isolated capability probes - never for the migration stack apply.
- **Phase 0 is the SOLE AUTHORITY** for what managed `postgres` can do; the design/plan author's memory never parameterizes Phase 2.
- **The Gate-5 invariants (1-8)** and **Decision Gate A** (membership achievability / creator-admin edge) and **Decision Gate B** (custom-role policy binding) are hard stops - resolved by branch proof, escalated to operator if unachievable, NEVER silently reinterpreted.
- **Commit trailer:** `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Serving model is DIRECT-DSN (serving connects AS `records_api`), NOT PostgREST/`authenticated`; policy targets stay `TO records_api, records_intake_writer` unless Gate B forces a stop.
- **Ownership-transfer rule (corrected).** `ALTER ... OWNER TO <new_owner>` ALWAYS runs AS the object's CURRENT owner, holding `WITH SET` membership in `<new_owner>` - NEVER while `SET ROLE`d into `<new_owner>` (that role does not yet own the object, so the transfer is rejected). Owner-only follow-ups (`FORCE ROW LEVEL SECURITY`, definer/RLS work) run under `SET ROLE <new_owner>` AFTER the transfer, because `INHERIT FALSE` membership does not by itself confer the owner's authority. For a cross-role transfer (048: a `records_owner`-owned object -> `records_fn_owner`), the executor is the current owner `records_owner`, which must hold `WITH SET` membership in `records_fn_owner`.
- **Phase 0 is a single controlled run.** Phase 0 executes as ONE operator-gated, single-agent run (no subagent fan-out); it is the sole branch spend. Phase 2 does NOT fan out until Task 2.0 has resolved Gate A, Gate B, AND the ownership choreography.

## Files

- Create: `infra/database/migrations/records/supabase_probe.py` - the reusable executable applier-privilege probe (Phase 0 + the Phase-4 prod precondition).
- Create: `infra/database/migrations/records/PHASE0-FINDINGS.md` - the recorded Phase-0 artifact (gate outcomes + the settable-attribute/ownership envelope) that parameterizes Phase 2.
- Modify: `infra/database/migrations/records/run_validation.py` - add the `--apply-as-non-superuser` mode.
- Modify: `infra/database/migrations/records/045_records_security_rls.sql` (+`_down`), `046_records_ownership.sql` (+`_down`), `047_records_audit_roles.sql` (+`_down`), `048_records_audit_log.sql` (+`_down`), `049_records_audit_triggers.sql` (+`_down`) - the adaptations.
- Modify: `infra/database/migrations/records/001..005,008_*.sql` - `BEGIN;/COMMIT;` source-wrap (Phase 4-prep).
- Modify: `docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md` - applier-privilege precondition + "198" reconcile (Phase 4-prep).
- Create: `docs/operations/RECORDS-SUPABASE-COMPAT-EVIDENCE-2026-07.md` - the branch red/green/residue evidence.

---

## PHASE 0 - Branch capability probe + gate resolution (fully concrete)

*Output: `PHASE0-FINDINGS.md` recording the resolved decision variables. This gates all of Phase 2.*

### Task 0.1: Provision a throwaway branch + apply 001-044 + inventory owners

**Files:** Create `infra/database/migrations/records/supabase_probe.py` (skeleton + branch lifecycle).

**Interfaces:**
- Produces: a branch `project_ref`, and an owner-inventory dict `{objkind: {owner: count}}` written to `PHASE0-FINDINGS.md`.

- [ ] **Step 1** - Via the authorized Supabase MCP, `create_branch` on project `fxoyniqnrlkxfligbxmg` (confirm cost first with `get_cost`/`confirm_cost`). Record the branch `project_ref`. Value-silent: never print the branch DSN.
- [ ] **Step 2** - Apply records `001-044` to the branch via value-silent host `psql` over the branch DSN ONLY. Obtain the branch DSN into a `0600` host env var, never echoed. NO MCP `apply_migration` (it writes a `supabase_migrations` history row). Use the conditional-`-1` rule proven 2026-07-04: `psql -v ON_ERROR_STOP=1 -q -f` per file, adding `-1` only for the six unwrapped files `001-005,008`. Stop-on-first-error.
- [ ] **Step 3** - Inventory ACTUAL owners: `select relkind, relowner::regrole, count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='records' group by 1,2` + the schema owner (`select nspowner::regrole from pg_namespace where nspname='records'`) + sequences/functions. **If any owner is `supabase_admin` (not `postgres`), FLAG it** - 046 assumes `postgres` ownership; record whether a `postgres -> records_owner` transfer path exists from a `supabase_admin`-owned object, or STOP (escalate per spec error-handling).
- [ ] **Step 4** - Write the owner inventory + `server_version` to `PHASE0-FINDINGS.md`. Commit `supabase_probe.py` + findings.
  Expected: `001-044` apply green on the branch; inventory recorded; if `supabase_admin` ownership appears, it is explicitly flagged (do not proceed silently).

### Task 0.2: Probe role-attribute settability (resolves A2)

- [ ] **Step 1** - As the branch `postgres`, first `create role probe_attr nologin` (unique to this probe). Then run each of `alter role probe_attr nosuperuser`, `... nobypassrls`, `... noreplication`, `... nocreatedb`, `... nocreaterole`, `... login` INDIVIDUALLY inside a savepoint, capturing per-statement success + SQLSTATE on failure.
- [ ] **Step 2** - Record in `PHASE0-FINDINGS.md` a table `attr -> {settable: bool, sqlstate}`. This resolves A2: for each residual clause, KEEP if settable else DROP+assert.
- [ ] **Step 3** - `drop role probe_attr` in a teardown/finally path (runs even if a step raised); assert clean.
  Expected: `nosuperuser` fails (SQLSTATE 42501) - matches prod. The rest recorded per-attribute (do NOT assume from `postgres`'s own held attributes).

### Task 0.3: Probe the CREATEROLE self-grant + membership revoke (resolves Decision Gate A)

- [ ] **Step 1** - As branch `postgres`: `create role probe_ga_owner nologin`; immediately `select grantor::regrole, member::regrole, admin_option, set_option, inherit_option from pg_auth_members where roleid = 'probe_ga_owner'::regrole` (capture the auto self-grant + its `ADMIN/SET/INHERIT` flags).
- [ ] **Step 2** - Attempt `revoke probe_ga_owner from postgres`; re-query `pg_auth_members`. Record whether the bootstrap edge is REMOVABLE.
- [ ] **Step 3** - Write the Gate-A resolution to `PHASE0-FINDINGS.md`:
  - `IF the self-grant is absent OR fully revocable -> GATE_A = clean-zero-edge` (Phase 2 uses in-migration creation + temp SET choreography).
  - `IF an un-removable ADMIN edge remains -> GATE_A = unavoidable-edge` -> Phase 2 Task 2.0 STOPS for the operator: choose (a) pre-provisioned-role path (roles minted out-of-band so `postgres` is never the creator) or (b) explicit operator acceptance of admin-only residue. NEVER silently accept.
- [ ] **Step 4 (teardown/finally)** - `drop role probe_ga_owner` (runs even if a step raised); assert clean.
  Expected: a recorded, unambiguous `GATE_A` verdict.

### Task 0.4: Probe the ownership-transfer choreography (red/green: wrong pattern fails, current-owner pattern works)

- [ ] **Step 1 (setup)** - As branch `postgres`: `create role probe_own_a nologin`; `create role probe_own_b nologin`; create a scratch schema `probe_s` (postgres-owned) with a scratch table/view/sequence/function. `grant probe_own_a to postgres with set true, inherit false, admin false`.
- [ ] **Step 2 (RED - wrong pattern MUST fail)** - In a savepoint: `set role probe_own_a; alter table probe_s.t owner to probe_own_a; reset role`. EXPECT failure - `probe_own_a` does not yet own `probe_s.t`, so transferring AS the target is rejected. Capture the SQLSTATE; roll back the savepoint.
- [ ] **Step 3 (GREEN - current-owner pattern MUST work)** - As `postgres` (the current owner, holding the `WITH SET` grant in `probe_own_a`): `alter table probe_s.t owner to probe_own_a` (and the view/sequence/function; transfer `alter schema probe_s owner to probe_own_a` LAST, or grant `postgres` temp `CREATE` on the schema first if object transfers need it - record which). EXPECT success. Then the owner-only op under the bracket: `set role probe_own_a; alter table probe_s.t force row level security; reset role`. EXPECT success (validates the A3 `INHERIT FALSE` + `SET ROLE` design).
- [ ] **Step 4 (cross-role transfer, for 048)** - `grant probe_own_b to probe_own_a with set true` (as postgres); `set role probe_own_a` (now the current owner of `probe_s.t`); `alter table probe_s.t owner to probe_own_b` - transfer AS the current owner `probe_own_a`, which holds the `WITH SET` grant in `probe_own_b`; `reset role`. EXPECT success. This proves 048's `records_owner -> records_fn_owner` path.
- [ ] **Step 5** - `revoke probe_own_a from postgres` (and `probe_own_b from probe_own_a`); confirm ownership SURVIVES the revoke; assert membership residue per Gate A.
- [ ] **Step 6 (teardown/finally)** - drop scratch objects + schema; `drop role probe_own_a`; `drop role probe_own_b`; assert clean. Record the working choreography (exact grant flags, temp-CREATE requirement, SET-ROLE requirement, the RED wrong-pattern SQLSTATE, and the cross-role A->B path) to `PHASE0-FINDINGS.md`.
  Expected: a proven, copy-ready ownership choreography (wrong pattern demonstrably fails; current-owner pattern demonstrably works; cross-role A->B proven), or an escalation if no `postgres`-reachable path works.

### Task 0.5: Probe custom-role policy binding (resolves Decision Gate B)

- [ ] **Step 1** - As branch `postgres`: `create role probe_pol_owner nologin` (unique to this probe); create a scratch schema `probe_pol_s` with an RLS-enabled table `probe_pol_s.t`. `create policy p_probe on probe_pol_s.t for select to probe_pol_owner using (true)`; capture success/SQLSTATE.
- [ ] **Step 2** - Write the Gate-B resolution: `IF accepted -> GATE_B = keep TO <custom role>` (reconcile 045's stale "rebind to authenticated" header as docs). `IF rejected -> GATE_B = STOP for operator design decision` (no silent switch to `authenticated`).
- [ ] **Step 3 (teardown/finally)** - drop the scratch table + schema and `drop role probe_pol_owner`; assert clean.
  Expected: a recorded, unambiguous `GATE_B` verdict.

### Task 0.6: Probe the remaining DDL envelope

- [ ] **Step 1** - As branch `postgres`, probe (savepoint-isolated, everything rolled back) the exact remaining command classes 045-049 use. Create a scratch role `probe_env_owner` + scratch schema `probe_env_s` inside the probe for the policy/owner-target ops, and drop them in the same savepoint rollback. Classes: `revoke create on schema public from public`; `alter table ... enable row level security`; `create/drop policy`; `alter view ... set (security_invoker=true)`; `create index`; `create or replace function`; `revoke ... from public` (PUBLIC EXECUTE); `create trigger`; `alter function ... owner to` (SECURITY DEFINER). Record each `{class -> ok|sqlstate}`.
- [ ] **Step 2** - Query `pg_event_trigger` (where visible) and record any managed-layer DDL guards. Write all to `PHASE0-FINDINGS.md`.
  Expected: the full-envelope capability table; no un-probed op class remains before Phase 2.

### Task 0.7: Finalize the reusable applier-privilege probe (B3) + branch teardown

**Files:** finalize `infra/database/migrations/records/supabase_probe.py`.

- [ ] **Step 1** - Consolidate Tasks 0.2-0.6 into `supabase_probe.py` as a single executable: given a target DSN, it exercises every privilege class (role attrs, role creation + self-grant check, membership grant/revoke WITH SET, ownership transfer table/view/seq/function/schema, the cross-role A->B transfer, `CREATE POLICY TO <role>`, RLS+FORCE RLS, trigger/function ownership, PUBLIC revoke) on scratch objects and tears them down, emitting a machine-readable pass/fail matrix + exit nonzero on any hard failure. This is REUSED as the Phase-4 prod precondition. Every scratch role/object it creates is savepoint/transaction-wrapped and torn down (zero residue on the target); output is value-silent (matrix + booleans only, never a DSN).
- [ ] **Step 2** - `delete_branch`; prove zero residue (no branch, and - since roles are cluster-level on the branch instance only - confirm the branch is gone). Record teardown in `PHASE0-FINDINGS.md`.
- [ ] **Step 3** - Commit `supabase_probe.py` + `PHASE0-FINDINGS.md`.
  Expected: a reusable probe + a complete findings artifact resolving A2, Gate A, Gate B, the ownership choreography, and the DDL envelope.

---

## PHASE 1 - Local `--apply-as-non-superuser` harness mode + red-proof

### Task 1.1: Add `--apply-as-non-superuser` to `run_validation.py`

**Files:** Modify `infra/database/migrations/records/run_validation.py`; Test `infra/database/migrations/records/test_run_validation_unit.py`.

**Interfaces:**
- Consumes: `RECORDS_PG_ADMIN_DSN` (existing); the Phase-0 capability envelope (to shape the applier role).
- Produces: a new CLI flag `--apply-as-non-superuser`; when set, tier 3's walk applies each migration through a freshly-created NON-superuser applier role (mirroring the branch-observed envelope as closely as local Postgres permits) instead of the admin session.

- [ ] **Step 1: failing test** - in `test_run_validation_unit.py`, assert `parse_args(["--apply-as-non-superuser"]).apply_as_non_superuser is True` and that a helper `make_local_applier(admin_dsn, envelope)` returns a DSN whose role is NOT rolsuper. (Envelope shape from `PHASE0-FINDINGS.md`: e.g. `createrole=true, bypassrls=<branch-observed>, replication=<branch-observed>`; do NOT hardcode CREATEROLE+BYPASSRLS+REPLICATION unless Phase 0 confirmed `postgres` uses them.)
- [ ] **Step 2** - Run it; expect FAIL (flag/function absent).
- [ ] **Step 3: implement** - add the argparse flag; add `make_local_applier` that CREATEs a disposable `records_val_applier_*` non-super role with the envelope attributes, returns a child DSN authenticating as it; wire tier3's `run_psql` to use the applier DSN when the flag is set; drop the applier role in teardown. Named to signal APPROXIMATION (a doc line: "local non-superuser mode APPROXIMATES Supabase; the branch is the fidelity authority").
- [ ] **Step 4** - Run tests; expect PASS. Commit.

### Task 1.2: Red-proof - unadapted 045-049 FAIL under the non-super mode at the exact class

**Files:** Test `infra/database/migrations/records/test_supabase_compat_redproof.py`.

- [ ] **Step 1: failing test** - assert that running tier3 with `--apply-as-non-superuser` on the UNADAPTED `045` raises, and the captured error names migration `045`, the `alter role` statement, and SQLSTATE `42501` (insufficient_privilege) - NOT a `CREATE ROLE` failure (which would be the wrong reason). Assert the applier role actually REACHED the `alter role` (i.e. `CREATE ROLE records_api` succeeded first).
- [ ] **Step 2** - Run it; expect FAIL (no red-proof asserts yet / mode may let it pass locally if the applier is over-privileged - if so, tighten the applier envelope until the red proof is honest).
- [ ] **Step 3: implement** - capture SQLSTATE + failing statement in the walk; assert the red-proof matches migration/statement/SQLSTATE.
- [ ] **Step 4** - Run; expect PASS (unadapted fails for the RIGHT reason). Commit.
  Note: this satisfies acceptance (1) + (10).

---

## PHASE 2 - Adapt 045-049 (up + down), decision-gated on Phase 0

### Task 2.0: Finalize Phase-2 parameters from `PHASE0-FINDINGS.md` (the re-plan checkpoint)

- [ ] **Step 1** - Read `PHASE0-FINDINGS.md`. Resolve, in writing (append to the findings file): (a) A2 per-attribute KEEP/DROP+assert list; (b) `GATE_A` verdict -> if `unavoidable-edge`, **STOP and escalate to the operator** (choose pre-provisioned-role path or explicit acceptance) before any 046 edit; (c) `GATE_B` verdict -> if `reject`, **STOP and escalate**; (d) the exact ownership choreography from Task 0.4 (grant flags, temp-CREATE requirement, SET-ROLE bracket, cross-role A->B), confirmed red/green proven - if Task 0.4 found no `postgres`-reachable path, **STOP and escalate**; (e) any `supabase_admin`-owner flag from 0.1.
- [ ] **Step 2** - Only if Gate A, Gate B, AND the ownership choreography all resolve to a GO path: proceed - single-agent, NO fan-out - to Tasks 2.1-2.5 with the finalized parameters. Otherwise halt the lane at the operator decision.
  Expected: a written parameter set; the remaining Phase-2 tasks are now fully determined.

### Task 2.1: Adapt `045` (up + down) - role attrs + policy binding

**Files:** Modify `045_records_security_rls.sql`, `045_records_security_rls_down.sql`; Test `test_045_records_security_rls.py`.

- [ ] **Step 1: test** - via `--apply-as-non-superuser`, applying adapted `045` SUCCEEDS; post-apply assert `records_api`/`records_intake_writer` are `rolsuper=false, rolbypassrls=false, rolcanlogin=true`; the reader-no-write / writer-no-delete asserts still hold; policies exist bound per `GATE_B`.
- [ ] **Step 2** - Run; expect FAIL (unadapted).
- [ ] **Step 3: implement** - in `045`: remove `nosuperuser` from lines 21-22 (certain); for the residual `nobypassrls/noreplication/nocreatedb/nocreaterole` apply the A2 KEEP/DROP+assert decision from Task 2.0 (if DROP: add a post-`alter` `do $$ begin if (select rolbypassrls or rolreplication or rolcreatedb or rolcreaterole from pg_roles where rolname='records_api') then raise exception '045: records_api forbidden attr'; end if; end $$;` block - exact per attribute per findings). Policy binding stays `TO records_api, records_intake_writer` per `GATE_B`; if `GATE_B=keep`, add a comment reconciling the stale header. Mirror the reverse in `045_down`.
- [ ] **Step 4** - Run; expect PASS under non-super mode. Commit.

### Task 2.2: Adapt `046` (up + down) - `records_owner` attrs + ownership choreography

**Files:** Modify `046_records_ownership.sql`, `046_records_ownership_down.sql`; Test `test_046_records_ownership.py`.

- [ ] **Step 1: test** - via `--apply-as-non-superuser`, adapted `046` SUCCEEDS; post-apply assert every `records.*` object + the schema are owned by `records_owner`; FORCE RLS on all base tables; `records_owner` is NOLOGIN/non-super/non-bypass; and invariant 8 (no usable membership residue: `postgres` holds no `SET`/`INHERIT` path into `records_owner`) - per Gate A.
- [ ] **Step 2** - Run; expect FAIL (unadapted 046 alter-roles + owner-to fail under non-super).
- [ ] **Step 3: implement** - in `046`: (i) remove `nosuperuser` from the `create/alter role records_owner` (33/37) + A2 residual decision + forbidden-attr assert; (ii) BEFORE the owner-to loop: `grant records_owner to postgres with set true, inherit false, admin false` (+ temp schema/DB CREATE if Task 0.4 found it needed); (iii) run the `owner to records_owner` loop AS `postgres` (the current owner, holding the `WITH SET` grant from (ii)) - do NOT `set role` for the transfer itself; transfer the schema owner LAST (or use the temp schema `CREATE` from (ii)) so the object transfers keep schema `CREATE`; THEN wrap ONLY the owner-only follow-ups (the `force row level security` loop and any other owner-only DDL) in `set role records_owner; ... reset role;` (per the corrected ownership-transfer rule - `INHERIT FALSE` membership does not by itself confer owner authority); (iv) `revoke records_owner from postgres` AFTER all owner-only DDL and BEFORE `046`'s terminal `raise exception '... LOGIN role(s) are members of records_owner'` (`:104-107`) - splice exactly there so the self-check sees zero LOGIN members; (v) add the effective-membership + temp-authority residue asserts. Mirror in `046_down` (re-own to `postgres` runs AS the current owner `records_owner`, so grant `records_owner to postgres with set` and `set role` to perform the reverse transfers per the same corrected rule).
- [ ] **Step 4** - Run; expect PASS. Commit.

### Task 2.3: Adapt `047` (up + down) - `records_fn_owner` + `records_auditor` attrs

**Files:** Modify `047_records_audit_roles.sql`, `047_records_audit_roles_down.sql`; Test `test_047_records_audit_roles.py`.

- [ ] **Step 1: test** - adapted `047` SUCCEEDS under non-super mode; assert `records_fn_owner` NOLOGIN/non-super/non-bypass and `records_auditor` LOGIN/non-super/non-bypass/no-repl/no-createdb/no-createrole/no-memberships (invariant 3).
- [ ] **Step 2** - Run; expect FAIL.
- [ ] **Step 3: implement** - remove `nosuperuser` from `047:8/11/15/16` + A2 residual decision + forbidden-attr asserts for BOTH roles. Mirror in `_down`.
- [ ] **Step 4** - Run; expect PASS. Commit.

### Task 2.4: Adapt `048` (up + down) - per-migration owner authority for audit objects

**Files:** Modify `048_records_audit_log.sql`, `048_records_audit_log_down.sql`; Test `test_048_records_audit_log.py`.

- [ ] **Step 1: test** - adapted `048` SUCCEEDS under non-super mode; assert `audit_log` + `fn_audit_capture` owned by `records_fn_owner`, `audit_log` FORCE RLS, `fn_audit_capture` SECURITY DEFINER with no PUBLIC EXECUTE; invariant 8 residue clean.
- [ ] **Step 2** - Run; expect FAIL (048 creates `audit_log` IN the now-`records_owner`-owned schema + `owner to records_fn_owner` - both fail under bare non-super `postgres`).
- [ ] **Step 3: implement** - per P1-c, 048 re-establishes ITS OWN temp authority (046 revoked its own): `grant records_owner to postgres with set true...` AND `grant records_fn_owner to postgres with set true...`, AND (for the cross-role transfer) `grant records_fn_owner to records_owner with set true` so the creating owner can transfer to the fn-owner. Then `set role records_owner`; CREATE `audit_log`/objects in the schema (they are now owned by `records_owner`); `alter table audit_log owner to records_fn_owner` - transfer AS the current owner `records_owner`, which holds the `WITH SET` grant in `records_fn_owner` (per the corrected ownership-transfer rule, NOT while set-role'd into `records_fn_owner`); `reset role`. Do the SECURITY DEFINER / FORCE RLS owner-only work under `set role records_fn_owner` (the new owner) AFTER the transfer; `reset role`. Revoke ALL temp grants (`records_owner`+`records_fn_owner` from `postgres`, and `records_fn_owner` from `records_owner`) BEFORE any terminal assert; assert residue clean. Mirror in `_down`.
- [ ] **Step 4** - Run; expect PASS. Commit.

### Task 2.5: Adapt `049` (up + down) - trigger authority

**Files:** Modify `049_records_audit_triggers.sql`, `049_records_audit_triggers_down.sql`; Test `test_049_records_audit_triggers.py`.

- [ ] **Step 1: test** - adapted `049` SUCCEEDS under non-super mode; assert `trg_audit` on exactly the writer-grant table set; none on `audit_log`/`neta_table_source_links`.
- [ ] **Step 2** - Run; expect FAIL (`create trigger` on `records_owner`-owned tables + `execute` on `records_fn_owner`-owned fn require authority bare `postgres` lacks).
- [ ] **Step 3: implement** - grant + `set role` to the role that owns the target tables (`records_owner`) with `execute` reachability on `fn_audit_capture` (or `set role records_fn_owner` as needed per Task 0.6's trigger-creation probe), create the triggers, reset, revoke, assert residue clean. Mirror in `_down`.
- [ ] **Step 4** - Run; expect PASS. Commit.

---

## PHASE 3 - Green proofs (local + branch)

### Task 3.1: Local full green under `--apply-as-non-superuser`

- [ ] **Step 1** - Run the full gate `run_validation.py --require-db --apply-as-non-superuser`; expect tiers 0-7 PASS with the ADAPTED 045-049 (the local approximation green).
- [ ] **Step 2** - Run down->up cycles for 045-049 under the non-super mode; expect clean reversal + re-apply. Commit any harness tweaks.
  Expected: acceptance (2) + (9-local).

### Task 3.2: Branch green - adapted 001-049 + down->up on a real Supabase branch

- [ ] **Step 1** - `create_branch`; apply adapted `001-049` via value-silent host `psql` over the branch DSN (conditional-`-1` rule; NO `apply_migration`); expect green end-to-end (the authoritative proof). Then run `045_down..049_down` -> re-apply cycle on the branch; expect clean.
- [ ] **Step 2** - Record the branch apply transcript to `RECORDS-SUPABASE-COMPAT-EVIDENCE-2026-07.md` (value-silent).
  Expected: acceptance (3) + (9-branch).

### Task 3.3: Invariant verification (1-8) on the branch

- [ ] **Step 1** - On the green branch, verify invariants 1-6 + 8 via SQL (role flags; ownership of all records objects; FORCE RLS; definer + no PUBLIC EXECUTE; trigger set; effective-membership reachability check with no direct/indirect SET/INHERIT path to a bypass/Data-API role).
- [ ] **Step 2** - Verify invariant 7 via the PLATFORM surface, not migration SQL: (a) the Supabase API exposed-schemas config does NOT include `records` (management/API surface); (b) HTTP negative probes with anon/authenticated/service keys against a records table return not-found/forbidden; (c) `select * from pg_default_acl` shows no future-object grants to anon/authenticated/service_role/PUBLIC for `postgres`/`records_owner`/`records_fn_owner`. Record all to evidence.
  Expected: acceptance (5) + (11).

### Task 3.4: Zero-residue teardown

- [ ] **Step 1** - `delete_branch`; confirm gone. Record teardown + a final residue statement (no branch, no leaked artifacts) to evidence. Commit evidence.
  Expected: acceptance (4).

---

## PHASE 4-prep - Packet corrections (staged; applied when Phase 4 is scheduled)

### Task 4.1: Add the executable applier-privilege precondition to the packet

**Files:** Modify `docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md` Section 1.

- [ ] **Step 1** - Add a Section-1 precondition that is HONEST that `supabase_probe.py` is a scratch-WRITE probe (it creates and tears down scratch roles/objects, transactionally and value-silently). Wording: "Applier-privilege precondition: `supabase_probe.py` MUST exit 0 (all privilege classes green) on the target BEFORE the migration write GO. Because it performs scratch writes, it requires its OWN operator-approved scratch-write GO, distinct from and PRIOR TO the migration write GO - it is NOT run 'before any GO'." Reference the Phase-0 probe. Commit.
  Note: the spec's B3 clause carries the same "before any GO" phrasing; flag to the operator that the spec line should mirror this scratch-write-GO correction (spec edit is out of scope for this plan-rev commit).

### Task 4.2: Source-own transaction atomicity for the six unwrapped up-migrations

**Files:** Modify `001,002,003,004,005,008_*.sql`; Test the existing per-file tests still pass.

- [ ] **Step 1** - Wrap each of `001-005,008` in a leading `BEGIN;` and trailing `COMMIT;` at source (so the packet no longer relies on a hand-added `-1`). Re-run the disposable gate (tiers 0-7) to confirm the wraps are inert on success. Update the packet Section 2 to state per-file wrapping is source-owned. Commit.
  Note: verify none of the six contain a statement that cannot run in a transaction (already confirmed 2026-07-04: none do).

### Task 4.3: Reconcile the "198" figure

**Files:** Modify `docs/operations/RECORDS-GATE9-PROD-APPLY-PACKET.md` (~line 14).

- [ ] **Step 1** - Replace "0 of 198 migrations" with the verified count ("0 of 49 up-migrations / 96 files"). Commit.

---

## Self-Review

**1. Spec coverage:** Phase 0 covers the branch probe + owner inventory + Gate A (0.3) + Gate B (0.5) + the reusable probe (0.7). Phase 1 covers the non-super mode (1.1) + SQLSTATE red-proof (1.2). Phase 2 covers all five roles (2.1 records_api/writer, 2.2 records_owner, 2.3 fn_owner/auditor) + both ownership planes (2.2/2.4) + policy binding (2.1) + up/down (each task) + the SET ROLE bracket (2.2/2.4/2.5) + per-migration authority (2.4/2.5) + splice-before-terminal-assert (2.2). Phase 3 covers local green (3.1) + branch green + down/up (3.2) + invariants incl. platform-verified 7 (3.3) + residue (3.4). Phase 4-prep covers the packet corrections. Decision Gates are hard stops at Task 2.0. No spec section is unmapped.

**2. Placeholder scan:** the Phase-2 conditionals are DECISION RULES keyed to the recorded `PHASE0-FINDINGS.md`, each with the exact edit for its branch or an explicit STOP->escalate - not "TODO"s. Task 2.0 is the honest re-plan checkpoint.

**3. Consistency:** role names (`records_api`, `records_intake_writer`, `records_owner`, `records_fn_owner`, `records_auditor`), the `PHASE0-FINDINGS.md` artifact, `supabase_probe.py`, and `--apply-as-non-superuser` are used consistently across tasks.

**4. Rev-2 fold check:** the corrected ownership-transfer rule (transfer AS the current owner; owner-only ops under `SET ROLE` after) is stated once in Global Constraints and applied consistently in Task 0.4 (red/green + cross-role), Task 2.2 (046), and Task 2.4 (048); no task still transfers ownership while `SET ROLE`d into the target. The stack apply is host `psql`-only in Tasks 0.1 and 3.2 (no `apply_migration` anywhere). Every Phase-0 probe (0.2-0.6) creates its own uniquely-named scratch role and tears it down. Task 0.4 is the sole owner of the ownership-choreography proof and Task 2.0 gates Phase 2 on it plus Gate A + Gate B with no fan-out.
