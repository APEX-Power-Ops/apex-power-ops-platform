# Records Supabase-Compat Adaptation - Design Spec (rev 4, IRP-folded)

*2026-07-04. Lane: records/supabase-compat. Off `origin/main @ 3f3ebe46`.*
*rev 2 folded the dual-engine IRP (Claude 5-agent grounded audit + Codex cross-engine) + operator ratifications; rev 3 folds the Codex stability-pass P1s (046 in the NOSUPERUSER drop; SET ROLE under INHERIT FALSE; per-migration owner authority); rev 4 folds the operator plan-audits: the `ALTER ... OWNER TO` transfer runs AS the object's CURRENT owner (not while SET-ROLE'd into the target), with the 048 cross-role grant and the reverse/down transfers (046_down A->postgres, 048_down B->A) plus the `grant postgres to <custom>` permission probe; temp schema CREATE belongs to the NEW/receiving owner; the B3 applier-privilege probe is a scratch-WRITE needing its own scratch-write GO.*

## Goal

Adapt records migrations `045-049` (and their `_down` counterparts, and two prod-apply-packet
corrections) so the Gate-5 security layer APPLIES on Supabase's NON-superuser managed `postgres`,
preserving the IDENTICAL Gate-5 guarantees, proven under Supabase's actual managed-Postgres privilege
envelope, so the full records stack `001-049` can be re-attempted on governed prod as a SEPARATE,
operator-gated act.

## Background / root cause (IRP-confirmed)

The 2026-07-04 prod-apply applied `001-044` cleanly, then `045_records_security_rls.sql:21` failed:
`permission denied to alter role - Only roles with the SUPERUSER attribute may alter roles with the
SUPERUSER attribute` (on `alter role records_api ... nosuperuser ...`). Managed Supabase `postgres` is
`rolsuper=false`. 045 self-wrapped -> rolled back atomically; `001-044` were reverted to greenfield.
Root cause + reusable lesson: `feedback_supabase_prod_superuser_fidelity`.

The dual-engine IRP established this is NOT a single-statement fix but a **THREE-stop failure plus a
second incompatibility class**:
- **Stop 1 (045):** `alter role` on `records_api` / `records_intake_writer` (and 047 on
  `records_fn_owner` / `records_auditor`) needs superuser to touch SUPERUSER/BYPASSRLS/REPLICATION.
- **Stop 2 (046):** `alter table|view|sequence|function|schema ... owner to records_owner` needs the
  applier to be a member (with `SET`) of `records_owner`; no `GRANT records_owner TO postgres` exists.
- **Stop 3 (048):** the same ownership wall against a DIFFERENT role, `records_fn_owner`
  (`alter table records.audit_log owner to records_fn_owner`; `alter function fn_audit_capture ...`).
- **Second class (H2, 045):** RLS policies bound to custom cluster roles (`for select to records_api,
  records_intake_writer`); 045's own header self-warns it is "NOT Supabase-apply-ready (TO <app-role>
  policies need role-rebind to authenticated)". Whether managed `postgres` accepts `CREATE POLICY ...
  TO <custom role>` is un-probed.

A 045-only patch regresses at 046, then 048, then policy DDL. The fix must cover the whole envelope.

## Grounding facts (established this session; primary-source verified at `3f3ebe46`)

1. prod `postgres`: `rolsuper=false`; `rolcreaterole=true`, `rolbypassrls=true`, `rolreplication=true`,
   `rolcanlogin=true`; admin_option member of admin/anon/authenticated/authenticator/service_role/pm/
   operations/field_tech/task_lead/etc. What `postgres` HOLDS is known; what it can SET on other roles
   under Supabase's managed layer is UNPROVEN (Phase 0 is the authority).
2. **Creator-admin edge (PG16+):** a non-superuser `CREATEROLE` role that runs `CREATE ROLE x` receives
   an AUTOMATIC membership grant of `x` back to itself with `ADMIN TRUE, SET FALSE, INHERIT FALSE`, and
   the creator CANNOT remove/alter that bootstrap grant. This is an **authority edge, not benign
   residue**: `ADMIN OPTION` lets the creator later re-grant `x` to itself (or anyone) `WITH SET
   TRUE`/`INHERIT TRUE`. If Supabase PG17 behaves this way, strict "zero membership edges" is NOT
   achievable when `postgres` creates the records roles. UNVERIFIED on the target - Phase 0 decides.
3. Custom non-login roles already exist on this Supabase prod (creation empirically works). `service_role`
   is `rolbypassrls=true` and `postgres` is its admin-member (a bypass-role reachable by grant).
4. On a Supabase BRANCH, objects applied by managed migrations/branch-restore MAY be owned by
   `supabase_admin` (not `postgres`); 046 assumes `postgres` ownership. UNVERIFIED - Phase 0 inventories.
5. Data-API exposed-schemas is PostgREST platform config, set by NO statement in `001-049`; a migration
   apply can neither set nor prove it. Must be verified via the API/management surface + HTTP probes.

## Frame and non-goals

- **Frame:** privilege adaptation ONLY. NOT a Gate-5 security-model rethink. Scope covers ALL FIVE
  records roles (`records_api`, `records_intake_writer`, `records_owner`, `records_fn_owner`,
  `records_auditor`) and BOTH ownership planes (046 -> `records_owner`, 048 -> `records_fn_owner`),
  UP and DOWN paths, plus the policy-binding surface.
- **Non-goals:** (a) no prod apply in this lane - re-apply is Phase 4, separate + operator-gated;
  (b) no faked `supabase_migrations` history; (c) no reliance on the local approximation alone - the
  Supabase branch is the authoritative fidelity gate; (d) NO silent switch of policy targets to
  `authenticated` and NO silent acceptance of admin-only membership residue (both route to the
  Decision Gates).

## Gate-5 guarantees to preserve (invariants)

1. Serving roles `records_api`, `records_intake_writer`: `rolbypassrls=false`, `rolsuper=false`.
2. Owner roles `records_owner`, `records_fn_owner`: NOLOGIN, non-super, non-bypass; own EVERY records
   object (15 tables + views + sequences + functions + schema; audit objects owned by `records_fn_owner`).
3. `records_auditor`: LOGIN, non-super, non-bypass, no replication/createdb/createrole; audit-log READ
   reachability only. (Added per IRP M1/M3 - it was omitted from rev 1.)
4. FORCE ROW LEVEL SECURITY on all base tables + `audit_log` (owner bound by RLS).
5. `fn_audit_capture` SECURITY DEFINER, owned by `records_fn_owner`, search_path pinned, NO PUBLIC EXECUTE.
6. Audit posture: append-only `audit_log`; `trg_audit` on exactly the writer-grant table set;
   `actor_role=session_user`.
7. Data API exclusion: records not in the exposed-schemas list AND zero USAGE on schema records + zero
   object/routine/default-ACL privilege to anon/authenticated/service_role/PUBLIC.
8. **Membership invariant (EFFECTIVE, not point-in-time):** no direct OR indirect membership path with
   `SET TRUE` or `INHERIT TRUE` from any records role to a privileged/bypass/Data-API role (e.g.
   `service_role`), and no residual usable membership into the owner roles. Asserted as an EFFECTIVE
   reachability check, re-run at prod preflight AND post-apply drift - never described as a one-time
   guarantee. (Reframed per IRP C4; the literal "zero edges" form is subject to Decision Gate A.)

## DECISION GATES (must be explicit before writing-plans; both are hard stops)

### Gate A - Membership-invariant achievability (the C3 gate)

Phase 0 decides whether `postgres`-created records roles can satisfy invariant 8 with a CLEAN zero-edge
teardown.

```
IF clean zero-edge cleanup is provable on the branch:
    use in-migration role creation + temporary SET-membership choreography (Design A3).
IF an unavoidable creator-admin edge remains (per grounding fact 2):
    EITHER use a PRE-PROVISIONED-role path (roles minted out-of-band so `postgres` is never the
            creator, so no bootstrap self-grant exists),
    OR STOP for an explicit operator design decision before weakening the invariant.
NO implementation may silently reinterpret zero-membership residue as acceptable admin-only residue.
Admin-only residue is a standing AUTHORITY edge (re-grantable to SET/INHERIT), not equivalent to zero.
```

### Gate B - Policy-role binding (the H2 gate)

Phase 0/3 must prove the exact behavior of `CREATE POLICY ... TO <custom cluster role>` (e.g.
`TO records_api`) on managed Supabase.

```
IF managed `postgres` accepts policies bound to the custom serving roles:
    KEEP `TO records_api, records_intake_writer` (correct for Gate 9's DIRECT-DSN serving model -
    serving connects AS records_api, NOT via PostgREST/authenticated). Reconcile 045's stale
    "rebind to authenticated" header (it predates the direct-DSN decision) as a documentation fix.
IF managed `postgres` REJECTS custom-role-bound policies:
    STOP for a design decision. Do NOT silently switch policy targets to `authenticated` - that would
    change the serving model and is an operator call.
```

## Design

### A. Adaptation of 045-049 (Phase-0-conditional, all five roles, up + down)

- **A1.** Drop explicit `NOSUPERUSER` immediately (certain: you cannot set an attribute you lack;
  `CREATE ROLE` defaults non-super). Applies to ALL THREE role-defining migrations: 045 (records_api,
  records_intake_writer), **046 (records_owner - `046:33/37`)**, and 047 (records_fn_owner,
  records_auditor). A2's attribute gating covers the same three files - NOT 045/047 only (omitting 046
  would re-create the 045-only-patch failure at 046's own `alter role records_owner ... nosuperuser`).
- **A2.** Keep `NOBYPASSRLS` / `NOREPLICATION` / `NOCREATEDB` / `NOCREATEROLE` ONLY IF Phase 0 proves
  managed `postgres` can set those negative/default attributes. If any is rejected, REMOVE the clause
  and preserve the guarantee via post-create/post-alter ASSERTIONS that fail loudly on forbidden state
  (`rolsuper=false`, `rolbypassrls=false`, `rolreplication=false`, `rolcreatedb=false`,
  `rolcreaterole=false`). Keep `LOGIN`/`NOLOGIN`.
- **A3.** Ownership transfer, BOTH planes (046 -> `records_owner`, 048 -> `records_fn_owner`):
  temporary membership choreography, gated by Decision Gate A. Exact shape:
  - `GRANT <owner_role> TO postgres WITH SET TRUE, INHERIT FALSE, ADMIN FALSE` (or the branch-proven
    equivalent) - and any temporary schema/DB `CREATE` the NEW/receiving owner (NOT `postgres`) needs to
    receive ownership;
  - the `ALTER ... OWNER TO <owner_role>` transfer itself runs AS the object's CURRENT owner (which holds
    the `WITH SET` grant), NOT while `SET ROLE`d into `<owner_role>` - the target does not yet own the
    object, so a set-role'd transfer is rejected;
  - **owner-only DDL runs under an explicit `SET ROLE <owner_role>` ... `RESET ROLE` bracket, NOT by
    holding membership alone.** Because the membership is `INHERIT FALSE`, `postgres` does not passively
    hold the owner's privileges - so 046's post-transfer `FORCE ROW LEVEL SECURITY` and 048's
    audit-object RLS/policy/grant work must execute AS the owner (the `SET TRUE` membership is precisely
    what enables the `SET ROLE`). `INHERIT FALSE` is deliberate - passive inheritance would hand
    `postgres` the owner's privileges standing, the opposite of the invariant;
  - the temp authority remains live through **ALL owner-only DDL in that migration**, and the `REVOKE`
    (with a matching `RESET ROLE`) fires **AFTER** all owner-only DDL and **BEFORE** the migration's own
    terminal self-check (046 ends its `BEGIN...COMMIT` with `raise exception '... LOGIN role(s) are
    members of records_owner'`; `postgres` is LOGIN, so a still-live temp grant self-aborts the
    migration). The splice point is stated exactly in each migration, not abstractly;
  - **temp authority is PER-MIGRATION** - each migration re-establishes what IT needs (046 revokes its
    own at its boundary, so 048/049 cannot rely on 046's grant): 048 creates `audit_log` IN the
    now-`records_owner`-owned `records` schema, so it needs temporary `records_owner` / schema-`CREATE`
    authority (via `SET ROLE`) IN ADDITION to `records_fn_owner` for the audit objects' ownership - the
    transfer of `audit_log` from its creator `records_owner` to `records_fn_owner` runs AS the current
    owner `records_owner`, which must hold `WITH SET` membership in `records_fn_owner`
    (`grant records_fn_owner to records_owner with set`); 049
    needs trigger/table/function authority on the `records_owner`-owned tables. NO temp authority is
    carried across a migration boundary; each migration asserts its temp authority + membership clean at
    its own end.
- **A4. Effective-membership + temp-authority residue asserts.** After each migration: assert invariant
  8 (no direct/indirect SET/INHERIT path to a bypass/Data-API role; no usable membership into the owner
  roles), AND assert every temporary `CREATE`/`TRIGGER`/`EXECUTE`/schema/database/membership authority
  granted only to complete ownership/audit DDL is REMOVED - or proven un-removable, which routes to
  Gate A. The assertion is EFFECTIVE (re-grantable admin edges are flagged), not a bare `pg_auth_members`
  row count.
- **A5. Down-migration parity (`045_down` .. `049_down`).** The reversals that reassign ownership back
  to `postgres`, drop the owner/serving/audit roles, or reverse audit objects carry the SAME choreography
  (temp membership through all owner-only reverse-DDL, revoke before any terminal assert) and the SAME
  residue asserts. The reverse runs AS the then-current owner: `048_down` (`records_fn_owner` ->
  `records_owner`) and `046_down` (`records_owner` -> `postgres`); the reclaim-to-`postgres` direction
  requires the current owner hold `WITH SET` membership in `postgres` (`grant postgres to <owner> with
  set`). Phase 0 probes BOTH reverse directions AND whether managed Supabase permits granting the
  `postgres` role to a custom role - if rejected, the down path escalates for an alternate design (see
  Error handling). Phase 2 adapts downs in lockstep; Phase 3 exercises down->up cycles on both surfaces.
- **A6. Policy binding (Gate B).** Keep `TO records_api, records_intake_writer` pending Gate B; the
  045 header "rebind to authenticated" note is reconciled per Gate B's outcome, never blindly followed.
- Everything else (grants, RLS enable, triggers) unchanged, but Phase 0 confirms each op class applies
  under the branch role (nothing is assumed "free" post-ownership-move).

### B. Validation machinery

- **B1. Local `--apply-as-non-superuser` mode** in `run_validation.py`: create a local applier role
  matching the branch-observed managed-postgres capability envelope as closely as local Postgres permits
  (do NOT predeclare it `CREATEROLE+BYPASSRLS+REPLICATION` unless Phase 0 confirms). Apply the stack AS
  it - a PERMANENT CI tripwire. Named to signal it APPROXIMATES, not IS, Supabase. Its RED proof must
  assert the failing migration + statement + SQLSTATE + error class (a real non-super applier that
  REACHES the role-attr `ALTER`, not one that dies earlier at `CREATE ROLE`).
- **B2. Real Supabase-branch proof (authoritative):** `create_branch` -> apply adapted `001-049` ->
  verify invariants 1-8 -> `delete_branch` -> prove zero residue. Invariant 7's exposed-schemas part is
  verified via the Supabase API/management surface + HTTP negative probes (anon/authenticated/service
  keys) + a `pg_default_acl` future-grant assertion - NOT via migration SQL alone.
- **B3. Executable applier-privilege probe (reusable).** A single executable that, given a target DSN,
  tests the exact privilege classes that failed or may fail: role attribute sets, role creation,
  membership grant/revoke WITH SET, ownership transfer (table/view/seq/function/schema; forward +
  cross-role + reverse-to-postgres, the last probing whether `grant postgres to <custom>` is permitted),
  policy creation `TO <custom role>`, RLS enable + FORCE RLS, trigger + function ownership, and clean
  teardown. It performs scratch WRITES (savepoint/transaction-wrapped + value-silent). Run on the branch
  in Phase 0 (to design), AND as the Phase-4 prod-apply PRECONDITION (an executable go/no-go gate, not
  prose) - see its scratch-write GO caveat under Packet corrections.

## Phases (non-circular)

- **Phase 0 - branch capability probe (AUTHORITATIVE).** `create_branch` -> apply `001-044` -> inventory
  ACTUAL owners of schema/tables/views/sequences/functions/indexes/identity-sequences (flag any
  `supabase_admin`); capture `server_version`, the createrole-self-grant behavior (`pg_auth_members`
  immediately after each `CREATE ROLE` + prove/disprove `REVOKE` removes the edge -> Gate A), and
  `pg_event_trigger`; run the B3 full-envelope capability probe (one minimal object per exact command
  class, INCLUDING `CREATE POLICY ... TO <custom role>` -> Gate B). Output parameterizes Phase 2 and
  resolves Gate A + Gate B. No adapted migrations here.
- **Phase 1 - local non-super mode + RED-PROOF (B1).** Build the mode; prove current unadapted `045-049`
  FAIL under it at the right migration/statement/SQLSTATE.
- **Phase 2 - implement the adaptation** (Design A, all five roles, both ownership planes, up + down),
  parameterized by Phase 0 and the resolved gates.
- **Phase 3 - GREEN proofs.** Adapted stack passes locally under `--apply-as-non-superuser`; adapted
  `001-049` + `045_down..049_down` down->up cycles apply on a real Supabase branch; invariants 1-8
  verified (invariant 7 via API + HTTP + default-ACL); branch teardown proves zero residue.
- **Phase 4 (SEPARATE, operator-gated) - re-attempt prod apply.** PRECONDITIONS: (a) prod in a KNOWN
  state - confirmed re-verified greenfield (as left 2026-07-04) OR an explicit operator-approved
  fix-forward from a documented partial state; never assumed ambient; AND (b) the B3 executable
  applier-privilege probe passes against the prod target. Its own go/no-go + operator GO, like 2026-07-04.

## Acceptance criteria

Operator-authored (verbatim): (1) current `045-049` FAIL in the non-super mode for the same class;
(2) adapted `045-049` PASS locally under the non-super applier; (3) adapted `001-049` PASS on a real
throwaway Supabase branch; (4) branch cleanup proves no role/schema/ACL/ownership/migration residue;
(5) preserve the Gate-5 guarantees (invariants 1-8); (6) do not rely on local approximation alone.
IRP-added: (7) the fix covers all five roles + both ownership planes + up/down; (8) Gate A and Gate B
are resolved by branch proof, not assumption; (9) down->up cycles pass on both surfaces; (10) the
red-proof asserts the exact SQLSTATE/error class; (11) invariant 7 is verified via platform surface,
not migration SQL.

## Packet corrections (separate artifact: `RECORDS-GATE9-PROD-APPLY-PACKET.md`)

Folded from IRP C2/M4/M5 - applied when Phase 4 is prepared (the packet is a committed doc, edited then):
- Add an EXECUTABLE applier-privilege precondition (the B3 probe) to Section 1 (the gate absent on
  2026-07-04). Because the probe performs scratch WRITES (creates + tears down scratch roles/objects,
  transactionally + value-silently), it requires its OWN operator-approved scratch-write GO, distinct
  from and PRIOR TO the migration write GO - it is NOT run "before any GO".
- Make transaction atomicity SOURCE-owned: wrap the six unwrapped up-migrations (`001-005`, `008`) in
  `BEGIN;/COMMIT;` at source, OR have the packet state exactly which layer owns wrapping per file - do
  not let a hand-added `-1` in operator memory be the safety mechanism.
- Reconcile the "0 of 198" figure (Section, line ~14) against the real `001-049` (49 up-migrations / 96
  files).
- Reconcile 045's "NOT Supabase-apply-ready" self-warning with the packet's straight-apply direction.

## Error handling / escalation

- Gate A unavoidable-edge -> pre-provisioned-role path OR operator design decision (never silent accept).
- Gate B custom-role-policy rejection -> operator design decision (never silent switch to `authenticated`).
- If Phase 0 shows ownership transfer needs MORE than temp membership (e.g. temp CREATE, or a
  `supabase_admin`-owned object with no `postgres` transfer path), revise before Phase 2, or ESCALATE.
- If the reclaim-to-`postgres` reverse transfer requires granting the `postgres` role to a custom role and
  managed Supabase rejects it, the down migrations escalate for an alternate down design (drop-and-recreate,
  or a dedicated reclaim owner) - never leave the down silently non-reversible.
- Every branch is throwaway; nothing mutates prod in this lane; cleanup + residue proof mandatory;
  value-silent throughout (no DSN/password printed).

## Testing

- RED proof (local + branch): unadapted `045-049` fail at the exact statement/SQLSTATE/error class.
- GREEN proof (local + branch): adapted stack passes; invariants 1-8 verified (7 via API + HTTP + default-ACL).
- DOWN->UP cycle proof (local + branch): adapted downs reverse cleanly (ownership back to postgres, roles
  dropped, temp-authority + membership residue asserted clean), then re-apply.
- Residue proof on branch teardown (roles / schema / ACL / ownership / migration / exposed-schema all clean).
- B3 executable applier-privilege probe green on the target before Phase 4.

## Open questions the branch probe must settle (operator-flagged + IRP)

1. Gate A: does managed PG17 impose the un-removable creator-admin edge? (Determines in-migration vs
   pre-provisioned roles.)
2. Gate B: does managed `postgres` accept `CREATE POLICY ... TO <custom role>`?
3. Can `postgres` set the residual role attributes (A2), or must they fall to assertion-only?
4. Are branch-applied `001-044` objects `postgres`-owned or `supabase_admin`-owned? (046 precondition.)
5. Does temp SET-membership suffice for ownership transfer, or is temp CREATE also required?
