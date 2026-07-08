# ops prod-apply packet -- G2 serving-credential prep + G3 prod apply (RUNBOOK)

Date: 2026-07-08. DOCS ONLY -- **no DB write, no serving-secret arming, no prod mutation is
performed by this packet.** It is the operator-ratifiable plan for putting the ops.* spine on
governed prod `fxoyniqnrlkxfligbxmg`, gated step-by-step. Supersedes the forward-gate section of
`docs/operations/OPS-SUPABASE-COMPAT-P3-SERVING-DSN-AND-READINESS-2026-07-08.md`.

## 0. Preconditions (what is already true / proven)
- The dual-substrate `012` adaptation + down are MERGED to `main` (PR #80, squash `9364a849`);
  `test_012` 23/23 on `ops_test`; dev path byte-equivalent.
- **G1 proved** on a throwaway managed non-super branch (evidence
  `docs/operations/OPS-SUPABASE-COMPAT-G1-COEXISTENCE-PROOF-2026-07-08.md`): 001-012 apply GREEN on
  a faithful coexistence surface; two-oracle boundary 7/7; advisors 0 ops ERROR; managed `012_down`
  (F2) + up->down->up; zero-residue; prod never written.
- **Read-only prod precheck** (P3 section 0): on prod today `work` schema is present with **0 tables**
  (012's work block is a trivial no-op), `records_*` = 6 roles **all NOLOGIN** (tolerated by the
  `[1a]` login sweep), `ops` ABSENT, `ops_*` roles ABSENT, prod mig 198. So the real prod co-tenant
  surface exactly matches what G1 synthesized -> G1 is a faithful predictor of the prod apply.
- Serving roles `ops_api` / `ops_intake_writer` are created **passwordless** by 012; the migration
  never mints a password.

## 1. G2-prep -- serving-credential preparation (NO DB write)
Storing a credential in Infisical and arming the Postgres role are DISTINCT actions (P3 section 1a);
G2 is split. This prep step is everything up to (but NOT including) the DB-side arming.

**G2-prep tasks (operator + AI, value-silent):**
1. Names + custody (fixed):
   - `OPS_API_DSN` -> role `ops_api` (control-plane recognition read + SECDEF-invoke path).
   - `OPS_INTAKE_WRITER_DSN` -> role `ops_intake_writer` (intake/materialization write path).
   - NEVER `postgres` (it is `rolbypassrls=TRUE` + the migration applier).
2. **OOB:** operator stores the intended `OPS_API_DSN` and `OPS_INTAKE_WRITER_DSN` in Infisical prod,
   value-silent. This is the credential of record; no password value is ever echoed, logged, or
   committed. Each DSN targets prod host, database `postgres`, its own role, its own SCRAM password.
3. **No DB write yet.** The roles do not exist on prod until G3 step 1; arming cannot run before
   they exist. G2-prep only stages the intended credentials + this runbook.

**Serving-arming SQL (authored here; EXECUTED only in G3 step 2, under an operator write GO):**
```
-- run as the prod migration admin (postgres), AFTER ops 012 has created the two roles.
-- <from-Infisical> = the SCRAM password pulled value-silently from Infisical prod; it is NEVER
-- written literally into this file, any migration, or any transcript.
alter role ops_api            password '<from-Infisical OPS_API_DSN>';
alter role ops_intake_writer  password '<from-Infisical OPS_INTAKE_WRITER_DSN>';
grant connect on database postgres to ops_api, ops_intake_writer;
```
Rationale (P3 F6): on the managed path 012 deliberately does NOT grant database CONNECT (it leaves
inherited PUBLIC CONNECT intact); serving must therefore hold an EXPLICIT CONNECT grant so it does
not depend on PUBLIC CONNECT persisting.

**Real-login round-trip checks (defined here; RUN in G3 step 3, value-silent):**
Connect AS each role via the Infisical DSN (the real login path -- NOT the SET-ROLE impersonation
G1 used) and assert the boundary BEHAVIORALLY. Reuse the two-oracle harness
`docs/operations/ops-role-pass-2026-07-08.py` (connect via the armed DSN). Assertions (assert on
precomputed booleans / name-lists, NEVER dump the env dict -- value-silent-tests discipline):
- `ops_intake_writer`: CAN write the intake surface (INSERT ops.intake_runs) AND CANNOT execute any
  of the 9 mutation fns.
- `ops_api`: CAN read its recognition views (v_completion_recognition_worklist/_rollup) AND invoke
  the 4 recognition SECDEF fns AND CANNOT fabricate (INSERT ops.apparatus/scopes) AND CANNOT execute
  any deferred billing fn.
- Both roles: `rolbypassrls=FALSE` on the live login.
- **STOP before execution.** G2-prep ends here.

## 2. G3 -- prod apply (the real prod write sequence; each step a separate operator GO)
Applies to governed prod `fxoyniqnrlkxfligbxmg`. Follows the established prod-apply discipline used
for the records 001-049 apply: SHA-pinned inputs, value-silent, per-step evidence
(pre-SHA / post-counts / post-posture / committed transcript), no admin-bypass.

1. **Apply ops 001-012 to prod.** Apply the canonical ladder (001-011 base with
   008=`008_core_equipment_models.sql`; the `ops_dev`-only `008_apply_preflight.sql` is excluded),
   then the dual-substrate `012` -- as managed non-super `postgres` via the authorized Supabase MCP
   (value-silent; no DSN handled). 012's in-migration asserts ([1a]/[2]/[2a]/[3a]/[5a]) are the
   apply-time gate; GREEN = boundary established. Coexistence behavior is exactly as G1 proved
   (empty work no-op; NOLOGIN records_* tolerated; PUBLIC CONNECT retained). Evidence: pre-SHA of
   each file, post fingerprint (11 views / 28 fns / 9 SECDEF owned by ops_fn_owner), advisors
   (expect 0 ops ERROR).
2. **DB-side serving arming.** Run the section-1 arming SQL (ALTER ROLE ... PASSWORD from Infisical;
   GRANT CONNECT) under this step's write GO. Value-silent (password flows Infisical -> the arming
   command, never echoed).
3. **Verify the Infisical DSN login round-trip.** Run the section-1 round-trip checks connecting AS
   `ops_api` / `ops_intake_writer` via the armed Infisical DSNs. Value-silent; assert on precomputed
   booleans.
4. **Run the boundary harness + advisors on prod.** Two-oracle boundary (catalog + real-login
   behavioral) + `get_advisors` (classify ops/core; expect 0 ops ERROR, the 19 base-fn
   search_path WARNs = pre-existing, tracked as `task_7dd40f4f`).
5. **Commit evidence.** Per-step transcript (pre-SHA / post-counts / post-posture / round-trip
   result) committed to `main` as the prod-apply record, mirroring the records
   `PROD_APPLY_EVIDENCE.md` standard.

## 3. Rollback posture (proven)
`012_down` is now F2-proven on a real managed non-super substrate (G1): it reassigns the 9 fns to
postgres + SECURITY INVOKER, drops the NOLOGIN `ops_fn_owner`, LEAVES the password-bearing login
roles in place (so an armed serving password survives a rollback), restores PUBLIC EXECUTE, touches
no co-tenant object, and executes no superuser-only statement; up->down->up is reversible. A prod
rollback would run `012_down` as postgres, then (if fully reverting) the 001-011 downs in reverse.

## 4. Guardrails (binding)
- Value-silent throughout: never echo a password/DSN value; classify SQLSTATE, never dump env.
- Passwords Vault/Infisical-first; never minted in SQL; never literal in any file/transcript.
- No admin-bypass on any merge; ASCII-only added lines; host-canonical single-writer over mesh.
- Each G3 step is a SEPARATE operator write GO. STOP between steps with evidence.
