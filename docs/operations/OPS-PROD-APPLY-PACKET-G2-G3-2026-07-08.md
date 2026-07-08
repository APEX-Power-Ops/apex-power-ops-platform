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

**Serving-arming SQL + execution mechanism (authored here; EXECUTED only in G3 step 2, under an operator write GO):**
The role password is the SCRAM PASSWORD COMPONENT PARSED FROM the Infisical DSN -- NOT the full DSN
string used as the password. Store the two components as their own value-silent variables
(`OPS_API_PASSWORD`, `OPS_INTAKE_WRITER_PASSWORD`), each = only the password field parsed from the
corresponding `OPS_*_DSN`. The password value is NEVER written literally into this file, any
migration, any command line, or any transcript.

Execution is value-silent and MANDATORY: run as the prod admin `postgres` via a host `psql` path
with BOUND variables so no literal password appears on any command line or in any log -- explicitly
NOT via MCP `execute_sql` / `apply_migration` (which would place the literal password inside a
VISIBLE tool-call argument). Passwords are injected from Infisical into the process env for the
single call and never echoed; capture + classify stderr and never dump it (psql parse/auth errors
can echo connection-string fragments). Illustrative shape (values from injected env; run only AFTER
ops 012 has created the two passwordless roles):

    psql "<postgres admin conninfo -- value-silent, never echoed>" -v ON_ERROR_STOP=1 \
      -v ops_api_pw="$OPS_API_PASSWORD" -v ops_intake_pw="$OPS_INTAKE_WRITER_PASSWORD" \
      -f arm_serving.sql   # 0600 temp, shredded after; stderr captured + redacted, never printed

    -- arm_serving.sql (:'x' single-quote-escapes the bound value; no literal password in the file):
    --   alter role ops_api            password :'ops_api_pw';
    --   alter role ops_intake_writer  password :'ops_intake_pw';
    --   grant connect on database postgres to ops_api, ops_intake_writer;

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
- **Target guard (MANDATORY, checked BEFORE the harness runs):** each DSN used for these real-login
  checks MUST resolve to prod host `fxoyniqnrlkxfligbxmg` (`db.fxoyniqnrlkxfligbxmg.supabase.co` /
  its pooler), database `postgres`, with login user EXACTLY `ops_api` or `ops_intake_writer`.
  Assert host + db + user up front and REFUSE to run if the DSN resolves to `ops_test`/dev, any
  other database, or any other user -- a value-silent misfire against a non-prod target must be
  impossible by construction.
- **STOP before execution.** G2-prep ends here.

## 2. G3 -- prod apply (the real prod write sequence; each step a separate operator GO)
Applies to governed prod `fxoyniqnrlkxfligbxmg`. Follows the established prod-apply discipline used
for the records 001-049 apply: SHA-pinned inputs, value-silent, per-step evidence
(pre-SHA / post-counts / post-posture / committed transcript), no admin-bypass.

0. **Pre-write drift gate (read-only, MANDATORY -- STOP on ANY drift).** The section-0 precheck
   records prod state at authoring time; it must be RE-CONFIRMED on a fresh read-only connection
   immediately before any write, because prod can move between authoring and apply. Re-confirm:
   (a) target project ref is `fxoyniqnrlkxfligbxmg` (NOT a preview branch, NOT dev);
   (b) applier is managed non-super `postgres` (`rolsuper=false`) and `current_database()='postgres'`;
   (c) `ops` schema ABSENT and `ops_*` roles ABSENT (this packet is a first apply, not a re-apply);
   (d) `work` schema still has 0 tables, OR any present `work` relations are explicitly reviewed +
   accepted as coexistence-safe (012 grants no ops role a work privilege on either path);
   (e) the 6 `records_*` roles still ALL NOLOGIN;
   (f) `supabase_migrations` count + a schema posture snapshot match the recorded prod baseline;
   (g) the 12 input files' sha256 match the SHA-pinned manifest for this apply.
   ANY mismatch -> STOP + report, do not write.

1. **Apply ops 001-012 to prod.** Apply the canonical ladder (001-011 base with
   008=`008_core_equipment_models.sql`; the `ops_dev`-only `008_apply_preflight.sql` is excluded),
   then the dual-substrate `012` -- as managed non-super `postgres` via the authorized Supabase MCP
   (value-silent; no DSN handled). 012's in-migration asserts ([1a]/[2]/[2a]/[3a]/[5a]) are the
   apply-time gate; GREEN = boundary established. Coexistence behavior is exactly as G1 proved
   (empty work no-op; NOLOGIN records_* tolerated; PUBLIC CONNECT retained). Evidence: pre-SHA of
   each file, post fingerprint (11 views / 28 fns / 9 SECDEF owned by ops_fn_owner), advisors
   (expect 0 ops ERROR).
   **Migration-history posture (explicit):** applying via MCP `execute_sql` deliberately writes NO
   `supabase_migrations` rows (the ops ladder uses its own numbering, separate from the Supabase
   001-198 scheme; mixing them is undesirable). Acceptance is therefore EVIDENCE / MANIFEST-governed
   -- the 012 in-migration asserts, the committed per-step transcript, and the ops `MANIFEST.md` are
   the authoritative record of what was applied -- NOT migration-history-governed. This is
   consistent with the records evidence-governed prod-apply posture. (If history-tracking is ever
   wanted, `apply_migration` is the alternative, at the cost of mixing numbering schemes -- out of
   scope for this packet.)
2. **DB-side serving arming.** Run the section-1 arming SQL via the section-1 value-silent `psql`
   bound-variable mechanism (passwords = the components parsed from the Infisical DSNs, injected
   from Infisical, `:'...'`-bound, never echoed; NOT MCP `execute_sql`) under this step's write GO.
   Includes the explicit `GRANT CONNECT ON DATABASE postgres TO ops_api, ops_intake_writer`.
3. **Verify the Infisical DSN login round-trip.** Run the section-1 round-trip checks (INCLUDING the
   mandatory target guard: each DSN resolves to prod host `fxoyniqnrlkxfligbxmg`, database
   `postgres`, user exactly `ops_api` / `ops_intake_writer` -- never `ops_test`/dev) connecting AS
   each role via the armed Infisical DSNs. Value-silent; assert on precomputed booleans.
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
