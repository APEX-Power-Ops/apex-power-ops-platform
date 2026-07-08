# ops Supabase-Compat -- G1: coexistence + managed-down branch proof (evidence)

Date: 2026-07-08. Lane `ops/supabase-compat`. Closes the two open gates from the P3 readiness
packet (`OPS-SUPABASE-COMPAT-P3-SERVING-DSN-AND-READINESS-2026-07-08.md`, sections 2 + 3):
**coexistence with the co-tenant surface ops 012 touches**, and the **managed `012_down`** proof.
Companion: the P2/P4 core branch proof (`OPS-SUPABASE-COMPAT-BRANCH-PROOF-2026-07-08.md`).

Executed on a THROWAWAY Supabase preview branch of governed prod (`fxoyniqnrlkxfligbxmg`),
created + torn down within the session. Prod was NEVER a mutation target: every SQL call used the
branch's own `project_ref`; the branch was identity-guarded; teardown left prod byte-identical.
Value-silent throughout (the authorized Supabase MCP `execute_sql` holds branch auth; no
DSN/password was ever constructed or echoed).

## Branch identity + substrate (guard)
- Branch `project_ref` = `bekeknmknsgedrxvhlgc` (id `1eb7de6d-...`); parent `fxoyniqnrlkxfligbxmg`
  (DISTINCT -> not prod). Status `MIGRATIONS_FAILED` / `preview_project_status ACTIVE_HEALTHY` --
  the same benign parent-replay-stops-at-111 behavior P2 recorded (the DB is up + usable).
- Applier: `current_user=postgres`, **`rolsuper=FALSE`** (the authentic managed non-super applier),
  `rolcreaterole=TRUE`, `db=postgres`. `supabase_migrations` count = **111** (!= prod 198).
- Clean start: `ops/core/work/records` ABSENT; `ops_roles=0`, `records_roles=0`.

## Coexistence synthesis (Option B -- minimal faithful, matched to the prod precheck)
Before ops 001-012, synthesized EXACTLY the co-tenant surface ops 012 touches, matched to prod:
- `create schema work` (empty -- prod `work` has 0 tables) PLUS a stress `work.g1_stress` table
  granting `select,insert,update,delete` to PUBLIC -- the exact condition that would have
  false-failed the OLD `has_table_privilege` work assert (adversarial F1). Confirmed:
  `work_present=t`, `work_tables=1`, `work_public_dml=t`.
- 6 `records_*` roles created NOLOGIN with the EXACT prod names (`records_api`, `records_auditor`,
  `records_fn_owner`, `records_intake_writer`, `records_owner`, `records_reclaim_owner`).
  Confirmed: `records_roles=6`, `records_all_nologin=t`.

## Base ladder 001-011 applied (fidelity gate)
Applied ops `001-011` (008 = `008_core_equipment_models.sql`; the `ops_dev`-only
`008_apply_preflight.sql` is excluded from the gate) via `execute_sql`, in 4 parts, as the branch
non-super `postgres`. Fingerprint vs P2's recorded baseline:
- `ops_views=11` (== P2), `ops_fns=28` (== P2), **all 9 mutation-fn signatures resolve** (== P2),
  `core` table+view+`120` seed rows, `ops_roles=0`. `ops_tables=16` (== exactly what 001-011
  create; P2's "27" was a broader ops+core+inherited count basis). No `execute_sql` errored and
  no downstream reference failed -> no CREATE was dropped. Base transcription is faithful.
- Transcription note (honest): the base parts were ASCII-normalized on the host before apply
  (`iconv -c ... ascii//TRANSLIT`; the 52 non-ASCII chars are all comment/`COMMENT ON`-string
  glyphs -- code is byte-untouched, line counts identical). Behavior-identical; verified by the
  fingerprint + advisor set (below) both matching P2.

## 012 UP -- GREEN on the coexistence surface
Applied the canonical adapted `012` (sha `a31a65be...`) as managed non-super `postgres`. GREEN
(no error) -> every in-migration assert passed on the real substrate WITH the co-tenant surface
present:
- `[1a]` login sweep TOLERATED the 6 NOLOGIN `records_*` roles.
- `[2]` managed else-branch confirmed PUBLIC retains CONNECT. NB substrate variant: this branch's
  `datacl` is NON-null but carries an EXPLICIT PUBLIC CONNECT grant -> the else-branch's
  disjunction `(datacl is null) OR (explicit PUBLIC CONNECT)` held on its SECOND arm. P2's branch
  had a null `datacl`; 012 correctly handles both.
- `[2a]` DIRECT-ACE work assert TOLERATED the `work.g1_stress` PUBLIC DML (did not false-fail).
- `[3]` A2 ownership transfer succeeded (transient `ops_fn_owner` CREATE-on-`ops`).
Post-GREEN posture: 3 ops roles present; `secdef_owned_by_fnowner=9`; `fnowner_create_ops=false`
(transient CREATE cleaned -> durable USAGE-only); `fns_public_exec=0`; `applier_member_fnowner=t`
(D8-2 edge); serving roles `rolbypassrls=false`.
Co-tenant no-op proven: after 012, `work_public_dml_retained=t` (012 left the work-PUBLIC ACL
UNTOUCHED), `no_ops_direct_work_grant=t`, `records_all_nologin=t`.

## Boundary -- two oracles agree (no false green)
CATALOG oracle (`has_*_privilege`): api reads worklist=t / api INSERT apparatus=f / writer INSERT
intake=t / writer EXEC attest=f / api EXEC attest=t / api EXEC billing=f -- all match intent.
BEHAVIORAL oracle (transient SET-capable self-grant -> `set role` -> attempt -> classify SQLSTATE
[42501=ACL_DENY, else=REACHED] -> sentinel-rollback) -- **7/7 PASS**:

| probe | expect | observed |
|---|---|---|
| W1 writer INSERT ops.intake_runs | REACHED | REACHED |
| W2 writer INSERT ops.revenue_recognition_event | ACL_DENY | ACL_DENY |
| W3 writer EXECUTE ops.attest_apparatus_complete | ACL_DENY | ACL_DENY |
| A1 api SELECT ops.v_completion_recognition_worklist | REACHED | REACHED |
| A2 api INSERT ops.apparatus (fabricate) | ACL_DENY | ACL_DENY |
| A3 api EXECUTE ops.attest_apparatus_complete | REACHED | REACHED |
| A4 api EXECUTE ops.record_billing_application (deferred) | ACL_DENY | ACL_DENY |

Behavioral-oracle note: impersonation is via `SET ROLE` (trusted-applier), NOT a real login --
the real serving-DSN round-trip is G2. Probes wrote no data (all rolled back; ops.* all 0 rows
after cleanup). A managed-pooler quirk terminated the connection when the results were read from a
TEMP table + trailing SELECT in the same call; re-run via a permanent scratch table read in a
separate call succeeded (harness robustness note only -- no bearing on the classifications).

## Advisors (security) -- IDENTICAL to P2, boundary-clean
162 lints total (87 ERROR / 73 WARN / 2 INFO). ops/core = **19, ALL WARN
`function_search_path_mutable`, ZERO ops/core ERROR** -- all on BASE (non-SECDEF) ops functions;
the 9 SECDEF mutation fns 012 owns are NOT flagged (012's `search_path` pinning works). The 87
ERROR are all on the inherited parent schema (`public/seam/...`), pre-existing prod, out of scope.
Reproducing P2 exactly also cross-confirms base-ladder transcription fidelity. The 19 base-fn
WARNs = the already-spawned follow-up (`task_7dd40f4f`), out of D8 scope.

## Managed 012_down -- F2 GATE CLOSED (first run ever on a real non-super substrate)
Applied the canonical `012_down` (sha `c371f8a0...`) as managed non-super `postgres`. Clean (no
error -> no superuser-only statement executed). End-state asserts:
- `fns_postgres_owned_invoker=9` (all 9 reassigned to `postgres` + SECURITY INVOKER),
  `fns_still_search_path_pinned=0`.
- **`ops_fn_owner` DROPPED** (`drop owned by` + `drop role` succeed as a non-super MEMBER of the
  role it created); `ops_intake_writer` + `ops_api` LEFT IN PLACE (managed `[d4]`: no `pg_authid`
  read -> an out-of-band serving password would survive a rollback).
- `fns_public_exec_restored=28/28` (pre-012 PUBLIC EXECUTE restored on all ops/core fns).
- Serving roles lost ops USAGE (schema-scoped revoke worked): `writer/api ops USAGE=false`.
- Co-tenant surface UNTOUCHED by the down (v_super-gated): `work_public_dml_intact=t`,
  `records_all_nologin_intact=t`.

## up -> down -> up (managed reversibility)
Re-applied `012` UP over the down state. GREEN again -> the `[1] if not exists` role guards let it
re-run idempotently over the LEFT-IN-PLACE login roles (`ops_fn_owner` recreated). Re-up posture:
`reup_secdef_owned=9`, `reup_fnowner_exists=t`, `reup_fnowner_create=false`, `reup_fns_public_exec=0`,
boundary intact (api reads worklist=t / api INSERT apparatus=f / writer INSERT intake=t).

## Teardown -- zero residue
`delete_branch(1eb7de6d-...)` -> success. `list_branches` -> ONLY `main`. Prod
`fxoyniqnrlkxfligbxmg` re-checked: `prod_mig_count=198` (unchanged), `ops` ABSENT, `ops_roles=0`,
`records_roles=6` -- prod is byte-identical to before G1, never received a single write.

## Verdict + what this closes
- COEXISTENCE gate CLOSED: 012 applies GREEN + preserves the full boundary on a branch carrying the
  faithful co-tenant surface (empty `work` + PUBLIC-DML work table + 6 NOLOGIN `records_*`); the
  direct-ACE work assert tolerates PUBLIC DML; the login sweep tolerates NOLOGIN co-tenant roles;
  012 leaves the co-tenant surface untouched (no-op).
- MANAGED-DOWN gate CLOSED (F2): `012_down` runs coherently as non-super `postgres`, drops the
  NOLOGIN owner, preserves the password-bearing login roles, restores PUBLIC posture, touches no
  co-tenant object, and executes no superuser-only statement; up->down->up is reversible.
- The core adaptation was already cross-engine-reviewed (P4: Codex + adversarial Claude); G1 adds
  NO new migration code -- it is the branch-substrate execution of the ratified 012/012_down + the
  P3-ratified Option-B synthesis method.

## Still open (gated -- NOT proven here)
- G2 serving arming: real-login round-trip via armed `ops_api` / `ops_intake_writer` DSNs
  (OOB password + explicit `GRANT CONNECT`) -- the behavioral oracle used SET-ROLE, not a login.
- G3 prod apply: GO-sequenced apply to prod `fxoyniqnrlkxfligbxmg`.
- Merge timing (operator): run G1 before merge (ratified) -> this evidence supports the merge.
