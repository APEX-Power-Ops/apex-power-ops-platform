# ops Supabase-Compat -- P3: Serving-DSN contract + prod-apply readiness packet

Date: 2026-07-08. Lane `ops/supabase-compat`. DOCS ONLY -- no serving-secret arming, no branch
spend, no prod write, no PR/merge. Companion: the branch-proof evidence
`docs/operations/OPS-SUPABASE-COMPAT-BRANCH-PROOF-2026-07-08.md` (ratified as proving the CORE
managed non-super adaptation, NOT coexistence / managed-down / serving path).

## 0. Read-only prod precheck (this session, no write) -- what coexistence actually is
Against prod `fxoyniqnrlkxfligbxmg` (read-only):
- Schemas present: `records, schedule, seam, tcc, work` (ops/core ABSENT). `prod_mig_count=198`.
- **`work` schema present but has 0 tables / 0 views** (0 relations with PUBLIC DML; 0 with any
  ACL). -> ops 012's `work.*` presence-gated block is a TRIVIAL NO-OP on current prod (the
  `to_regnamespace('work') is not null` path runs but iterates zero relations).
- `records_*` roles: 6, **all NOLOGIN** -> excluded from every `rolcanlogin`-scoped `[1a]` sweep.
- `ops_*` roles: absent. ops 012 references NO other co-tenant schema (not records/tcc/seam/schedule).

**Consequence:** the real co-tenant surface ops 012 touches on prod = an EMPTY `work` schema +
NOLOGIN cluster roles. That is a small, enumerable surface -- not the full records/tcc datasets.

## 1. Serving-DSN contract (prod)
- **Two distinct serving credentials**, one per login role, never shared:
  - `OPS_API_DSN` -> role `ops_api` (the control-plane API's recognition read + SECDEF-invoke path).
  - `OPS_INTAKE_WRITER_DSN` -> role `ops_intake_writer` (the intake/materialization write path).
- **Never `postgres`.** `postgres` has `rolbypassrls=TRUE` and is the migration applier; the
  serving path must use the non-bypass login roles so the grant matrix + RLS-if-any are enforced.
- **Passwords are Vault/Infisical-first, NEVER minted in SQL.** 012 creates the two roles
  passwordless (`create role ... ` + attribute correction only); the operator sets each role's
  SCRAM password OUT-OF-BAND (Infisical prod), and the AI verifies the round-trip value-silently.
  No migration, doc, or transcript ever contains a role password.
- **Explicit `GRANT CONNECT` is part of serving-arming (F6).** On the managed path 012
  deliberately does NOT grant database CONNECT (it leaves inherited PUBLIC CONNECT untouched).
  Arming MUST therefore `GRANT CONNECT ON DATABASE postgres TO ops_api, ops_intake_writer`
  explicitly, so serving does NOT depend on PUBLIC CONNECT persisting. If PUBLIC CONNECT is ever
  revoked on prod, explicitly-granted serving roles keep working.
- **No reliance on inherited PUBLIC CONNECT after arming** -- the explicit grant above is the
  standing guarantee.
- **Arming round-trip (value-silent):** connect as each role and assert the boundary behaviorally
  -- `ops_intake_writer` CAN write the intake surface + CANNOT execute any mutation fn;
  `ops_api` CAN read its recognition views + invoke the 4 recognition SECDEF fns + CANNOT
  fabricate (INSERT apparatus/scopes) or execute deferred billing. Reuse the two-oracle method
  from `docs/operations/ops-role-pass-2026-07-08.py` (connect AS the role via the armed DSN --
  the real login path, not the SET-ROLE impersonation the branch used).

## 2. Coexistence proof method (accounts for the 111-replay fidelity gap)
The Supabase preview-branch replay stops at `supabase_migrations=111` (blocked at #112, a tcc
migration) and prod is at 198 -- so "create a fresh branch" reliably yields a branch WITHOUT
records/tcc/work + their roles. "Fresh branch" must NOT be allowed to silently mean "branch
missing the co-tenant state we meant to test." Three options were considered:

- **Option A -- true coexistence branch:** make the branch actually contain records/tcc/work.
  REJECTED for this gate: requires either fixing the #112 replay blocker (a tcc-lane concern, out
  of D8 scope) or manually replaying the full records/tcc/work ladders on the branch (large, and
  ops 012 does not interact with their contents).
- **Option B -- minimal faithful synthesis (CHOSEN):** on a fresh branch, before applying ops
  001-012, synthesize EXACTLY the co-tenant surface ops 012 touches, matched to the prod precheck:
  1. `create schema work;` (empty -- matches prod's 0-table `work`). This exercises the
     `to_regnamespace('work') is not null` TRUE path (with zero relations) that the first branch
     proof could NOT (work was ABSENT there).
  2. Belt-and-suspenders stress case: also create ONE `work.<t>` table and
     `grant select,insert,update,delete on work.<t> to public;` -- the exact condition that would
     have false-failed the OLD `has_table_privilege` assert. Prove the NEW direct-ACE assert does
     NOT abort (it tolerates PUBLIC-inherited grants), then optionally drop the table so the
     empty-`work` case is also covered.
  3. `create role records_api nologin; ...` for the 6 `records_*` names as NOLOGIN -- prove the
     `[1a]` login sweep tolerates NOLOGIN co-tenant roles.
  Then apply ops 001-012, run identity + two-oracle boundary + advisors, and the managed down
  (section 3), and delete the branch zero-residue.
  **Scope honesty:** Option B proves ops 012 coexists with the SURFACE it touches (empty work +
  NOLOGIN roles). It does NOT (and need not) prove interaction with records/tcc DATA or RLS --
  ops 012 references none of it.
- **Option C -- prod read-only precheck + no-op guarantees (fallback/complement):** the section-0
  precheck already establishes work is empty + records roles are NOLOGIN on prod. If branch
  synthesis is ever blocked, this precheck + the direct-ACE/`v_super` no-op guarantees are the
  minimum bar; but Option B is the primary method because it actually EXECUTES 012 against the
  synthesized surface.

## 3. Managed 012_down proof (open gate -- not paperwork)
`012_down` has NEVER run on a managed non-super substrate (the branch proof deleted the branch
rather than running the down; the `test_012` reversibility runs on ops_test where `postgres` is a
superuser). Before the down is accepted as prod rollback posture, on the Option-B coexistence
branch, AFTER a GREEN apply:
- Run `012_down` as the managed non-super `postgres`.
- Assert: the 9 fns are reassigned to `postgres` (via the kept `ops_fn_owner` membership + postgres
  owning schema ops); `drop owned by ops_fn_owner` succeeds as a non-super member; `ops_fn_owner`
  drops (NOLOGIN, no deps after reassignment); the two LOGIN roles are LEFT IN PLACE (managed
  branch of [d4]: no `pg_authid` read); the `work`/database grants are `v_super`-gated and skipped;
  NO superuser-only statement executes.
- Assert coherent end state + zero unexpected residue; then a re-apply (up) to prove up->down->up
  reversibility on the managed substrate.

## 4. Prod-apply readiness gate sequence (each gate stops for operator GO)
- **G1 (branch, cost):** Option-B coexistence branch -> apply ops 001-012 -> identity + two-oracle
  boundary + advisors -> managed `012_down` proof -> up->down->up -> delete branch, zero residue.
  Closes the coexistence + managed-down gates. Commit a G1 evidence record.
- **G2 (serving arming, OOB secret):** operator sets `ops_api` / `ops_intake_writer` SCRAM
  passwords in Infisical prod; apply `GRANT CONNECT` to both; AI verifies the real-login round-trip
  value-silently. NB: role creation + CONNECT grant happen at prod-apply time (G3); the PASSWORD is
  the only OOB step.
- **G3 (prod apply, write):** GO-sequenced apply of ops 001-012 to prod `fxoyniqnrlkxfligbxmg`
  (evidence per step: pre-SHA / post-counts / post-posture / committed transcript), then the G2
  round-trip against live prod.

## 5. Merge timing
Do NOT merge `ops/supabase-compat` to main yet. Land the P3 docs first (this file), then decide
whether the migration-adaptation PR merges BEFORE or AFTER G1 (coexistence + managed-down). The
adaptation is dev-green + core-proven; the open gates are prod-substrate, so an early merge is
defensible ONLY if the PR body is explicit that prod-apply remains gated behind G1-G3.
