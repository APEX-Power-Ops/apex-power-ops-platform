# ops Supabase-Compat -- Branch Proof (evidence)

Date: 2026-07-08. Lane `ops/supabase-compat` (Phase-0 `6eba8382`, P1 `437a6a10`, A2 fix
`c49cb1a0`). Companion design: `docs/superpowers/specs/2026-07-08-ops-supabase-compat-design.md`;
Phase-0: `docs/operations/OPS-SUPABASE-COMPAT-PHASE0-ENUMERATION-2026-07-08.md`. Precedent:
`docs/operations/RECORDS-SUPABASE-COMPAT-PHASE3B-BRANCH-PROOF-2026-07-07.md`.

Executed on a THROWAWAY Supabase preview branch of the governed prod project (parent
`fxoyniqnrlkxfligbxmg`), created and torn down within the session. Prod was NEVER a mutation
target: every SQL call used the branch's own `project_ref`, and the branch was identity-guarded
(`mig_count=111` != prod). Applied over the branch's managed non-super `postgres` via the
authorized Supabase MCP `execute_sql`. Value-silent throughout (the MCP handles auth; no
DSN/password was ever constructed or echoed).

## Branch identity + substrate
- Branch `project_ref`: `qiqktlrgewicglpziwsw` (branch id `ba6124c5-...`); parent
  `fxoyniqnrlkxfligbxmg`.
- Applier: `current_user=postgres`, `rolsuper=FALSE`, `rolcreaterole=TRUE` -- the authentic
  managed applier. `db=postgres`. Distinct IPv6 server from prod.
- Branch-identity guard: `supabase_migrations` count = **111** (parent-history replay stopped at
  111 on an unrelated pre-`records` migration -- the SAME benign behavior the records Phase-3B
  recorded). At 111 the branch has `public/seam/auth/...`; `records/tcc/work/schedule` are ABSENT.
- Matches prod on the axes that matter here: non-super `postgres`, `ops` absent,
  `public.employees` present. Coexistence caveat in Scope below.

## RED -- unadapted 012 (from main) must fail on non-super
Base ops `001-011` applied clean first (27 tables / 11 views / 28 fns / 0 ops roles). Then the
UNADAPTED main `012`:
- FAILED `sqlstate 42501` "permission denied to alter role" / DETAIL "Only roles with the
  SUPERUSER attribute may alter roles with the SUPERUSER attribute" -- at
  `alter role ops_intake_writer with login nosuperuser ... nobypassrls noreplication`.
- Residue after RED: `ops_roles=0`, `ops_tables=27` (whole script rolled back; base intact).
- Conclusion: the unadapted stack genuinely cannot apply as managed non-super `postgres`. Proven.

## GREEN v1 -- adapted 012, FIRST attempt: caught a real second-order defect
The first adapted `012` cleared A1 (role attrs) and A3 (skipped db-CONNECT) and did the applier
self-grant, then FAILED at section [3] `alter function ... owner to ops_fn_owner`:
`sqlstate 42501` "permission denied for schema ops". Root cause: Postgres requires the NEW
owning role to hold CREATE on the function's schema for a non-superuser to reassign ownership
(you cannot give an object to a role that could not have created it there). A2 granted the
applier SET-capable membership but never gave `ops_fn_owner` CREATE on schema `ops`. On dev
(superuser) the bypass masks this; on managed it is fatal. The apply halted; the script rolled
back clean (0 roles, 27 tables). This is exactly the false-green class the local-superuser
harness cannot see -- the reason the real-substrate proof was worth the spend.

## Fix + GREEN v2 -- adapted 012 (fixed) applies clean
Fix `c49cb1a0`: on the non-super path, GRANT `ops_fn_owner` TRANSIENT CREATE on schema `ops`
before the ownership loop, REVOKE it after. Durable posture stays USAGE-only (identical to the
superuser path, where the bypass needs neither). GREEN v2: applied clean; all in-migration
posture asserts ([1a][2a][3a][5a]) passed on the managed substrate. `test_012` re-run 23/23 on
`ops_test` (dev path unchanged; fix is `not v_super`-gated).

## Posture (first-hand, post-GREEN)
- 3 ops roles: `ops_api` (login, non-super, non-bypass), `ops_intake_writer` (login, non-super,
  non-bypass), `ops_fn_owner` (NOLOGIN, non-super, non-bypass).
- 9 mutation fns SECURITY DEFINER + owned by `ops_fn_owner`.
- `ops_fn_owner`: CREATE on schema ops = **FALSE** (transient CREATE cleaned up); USAGE = **TRUE**.
- PUBLIC retains DB CONNECT = **TRUE** (A3: the managed path left the database-level ACL
  untouched; the boundary is schema-scoped).
- ops/core functions retaining PUBLIC EXECUTE = **0** (PUBLIC EXECUTE hygiene applied
  schema-scoped, not database-scoped).
- applier (`postgres`) is a member of `ops_fn_owner` = TRUE (the ratified trusted-applier edge, D8-2).

## Boundary -- two oracles agree (no false green)
Catalog oracle (`has_*_privilege` as the connected role): api reads worklist TRUE; api INSERT
apparatus FALSE; writer INSERT intake_runs TRUE; writer EXECUTE attest FALSE -- as intended.
Behavioral oracle / DML negative control (transient `postgres` self-grant of SET -> `set role`
-> attempt in-role -> classify SQLSTATE -> reset) -- **7/7 PASS**:

| probe | expect | observed |
|---|---|---|
| W1 writer INSERT ops.intake_runs | REACHED | REACHED |
| W2 writer INSERT ops.revenue_recognition_event | ACL_DENY | ACL_DENY |
| W3 writer EXECUTE ops.attest_apparatus_complete | ACL_DENY | ACL_DENY |
| A1 api SELECT ops.v_completion_recognition_worklist | REACHED | REACHED |
| A2 api INSERT ops.apparatus (fabricate) | ACL_DENY | ACL_DENY |
| A3 api EXECUTE ops.attest_apparatus_complete | REACHED | REACHED |
| A4 api EXECUTE ops.record_billing_application (deferred) | ACL_DENY | ACL_DENY |

Bypass asymmetry: `postgres rolbypassrls=TRUE`; `ops_api`/`ops_intake_writer`=FALSE -> the
serving DSN role must be a non-bypass login role, NEVER `postgres`.

## Advisors (Supabase security) -- classified
162 lints total (87 ERROR / 73 WARN / 2 INFO). ops/core-relevant: **19, ALL WARN
`function_search_path_mutable`**, and ALL on BASE (non-SECDEF) ops functions (`trg_*` triggers,
guards, `_intake_source_format_text`, `maintain_scope_quote_hours`). **ZERO ops/core ERROR.**
The 9 SECURITY DEFINER mutation fns `012` owns are NOT flagged -> `012`'s `search_path` pinning
works. The 87 ERROR + remaining WARN are all against the inherited parent schema
(`public/seam/...`), pre-existing prod, out of scope. The 19 base-fn WARNs are a pre-existing
base-migration property (not a `012` boundary concern; low risk -- invoker fns) -> a candidate
FUTURE hardening (pin `search_path` on base ops fns), out of D8 scope.

## Teardown -- zero residue
`delete_branch(ba6124c5-...)` -> success. `list_branches` -> only `main`. Prod
`fxoyniqnrlkxfligbxmg` never received a single write.

## Scope / caveats (honest)
- Coexistence NOT fully exercised: at branch `mig=111`, `records_*`/`tcc`/`work`/`schedule` are
  absent, so (a) the A7 `work.*` presence-gated block was a no-op and (b) `ops` was not proved
  alongside the `records_*` roles that coexist on prod. A7's managed behavior (the `v_super`-gated
  `work`-PUBLIC revoke is skipped; the ops-scoped `work` revokes are no-ops on fresh roles) is
  verified by reasoning + the presence gate, NOT by an on-branch run. The prod-apply packet must
  re-run the identity + boundary checks on the full-coexistence prod substrate.
- The two managed hazards `012` must survive are BOTH now proven handled on the real substrate:
  (1) the NOSUPERUSER/NOBYPASSRLS ALTER ROLE clause (A1); (2) the owner-reassignment CREATE
  requirement (A2, caught + fixed here). No further managed blind spot surfaced past section [3].
- Serving path NOT exercised: the ops roles are passwordless on the branch; the behavioral oracle
  impersonated via `SET ROLE` (trusted-applier), not a real login. The real serving-DSN
  round-trip is the later operator-gated packet.

## Verdict
UNADAPTED = RED (42501). ADAPTED = GREEN on the real managed non-super `postgres`, with a real
defect caught + fixed mid-proof. Boundary holds under two agreeing oracles; advisors show zero
`ops` ERROR; zero-residue teardown; prod untouched. The dual-substrate `012` is proven on the
authoritative substrate for the CORE non-super adaptation. Forward gate for the prod-apply
packet: full-coexistence re-run + serving-DSN arming (detailed below).

## P4 -- Cross-engine review folded (Codex + adversarial Claude)
Two independent reviews of the adaptation + this evidence:
- **Codex** (`apex-jobs review-run`, dispatch `review-95425a07`): one [P2] -- the DOWN `[d5]`
  work-PUBLIC grant was not superuser-gated (asymmetric with the up). FIXED (`df51f3a4`).
- **Adversarial Claude** (refute-mode): no CRITICAL/HIGH; the core UP adaptation is sound.
  - **F1 (MED)**: the up `[2a]` work assert used `has_table_privilege`, which returns true for a
    privilege inherited via a grant to PUBLIC -> on the managed path (work-PUBLIC ACL untouched)
    it would false-fail and ABORT the apply if any work table grants DML to PUBLIC. FIXED
    `df51f3a4` (DIRECT-ACE check; validated on ops_dev, work present, ops roles have no direct
    work grant).
  - **F2 (MED)**: the managed DOWN has never run on a real non-super substrate (coverage gap, not
    a proven bug) -> FORWARD GATE.
  - **F3 (LOW)** = Codex [P2]; **F4 (LOW)** work warning-noise -> both FIXED `df51f3a4` (the
    managed path now issues ZERO statements against the co-tenant work schema).
  - **F5 (LOW)**: the static CONNECT-guard test uses a 500-char proximity heuristic (current file
    correct) -> noted, no change.
  - **F6 (LOW)**: managed serving roles reach the DB via inherited PUBLIC CONNECT (no explicit
    grant) -> SERVING-DSN GATE.
- Could NOT be refuted by either engine: A2 transient-CREATE sound; D8-2 trusted-applier edge
  grants no serving-role escalation (serving roles are revoked + asserted non-member); A3 truly
  blocks database-level ACL mutation on the managed path; login sweeps safe under coexistence
  (`records_*` are NOLOGIN); ASCII clean; value-silent.

## Forward gate (updated) -- required before any prod apply
1. Create a FRESH branch on the full-coexistence substrate (records/tcc/work + their roles
   present) and exercise the `[2a]` work DIRECT-ACE assert + the `v_super`-gated work paths on a
   work-present DB.
2. Prove the managed `012_down` on that coexistence branch (F2) before treating it as the prod
   rollback.
3. Serving-DSN arming: create `ops_api` / `ops_intake_writer` passwords OOB (Infisical) and GRANT
   explicit CONNECT on the prod DB to both -- do NOT rely on inherited PUBLIC CONNECT (F6).
4. Re-run identity + two-oracle boundary + advisors on the coexistence substrate; zero-residue.
5. Pre-check (belt-and-suspenders): verify on prod that no `work.*` relation grants DML DIRECTLY
   to the ops roles (the direct-ACE assert already tolerates PUBLIC grants).
