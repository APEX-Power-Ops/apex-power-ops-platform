# ops Supabase-Compat -- Design (D8 prod-substrate proof)

Date: 2026-07-08. Lane: `ops/supabase-compat`.
Companion Phase-0 record: `docs/operations/OPS-SUPABASE-COMPAT-PHASE0-ENUMERATION-2026-07-08.md`.
Direct precedent (same governed project, same non-super postgres):
`docs/superpowers/specs/2026-07-04-records-supabase-compat-design.md` (design) and
`docs/operations/RECORDS-SUPABASE-COMPAT-PHASE3B-BRANCH-PROOF-2026-07-07.md` (proven RED->GREEN
branch proof).

## Goal
Prove that ops migrations 001-012 apply cleanly, and that the 012 role boundary holds, on the
managed non-super `postgres` of the governed prod project `fxoyniqnrlkxfligbxmg` -- WITHOUT
mutating prod -- and define the serving-DSN contract. Prod apply and the real serving-DSN
round-trip are a SEPARATE later operator-gated packet.

## Non-goals
- No prod apply of any ops migration.
- No real serving-DSN provisioning / round-trip (contract only in this lane).
- No records-lane changes.

## Substrate (from Phase-0)
Applier `postgres` is non-super (createrole/createdb/bypassrls). `ops` and ops_* roles are
absent on prod. The DB is SHARED (records/tcc/seam/work/public coexist). This is why the
dedicated-DB assumptions in 012 (database-level CONNECT hygiene; superuser attribute writes;
free ownership transfer) must be adapted -- see Phase-0 deltas A1-A7.

## Approach -- reuse the records branch-proof method
Vehicle: a throwaway Supabase preview branch of the prod project, created + torn down within
the session, every write phase guarded on branch identity so prod cannot be a mutation target.
Applied over the branch's DIRECT connection as the real managed non-super `postgres`.
Value-silent throughout: DSN injected via Infisical, never echoed; `${VAR:+ok}` only (carry the
records Phase-3B value-silence incident lesson -- a `${VAR:-NO}` slip once printed the prod DSN).

Phases:
0. (DONE) Phase-0 read-only enumeration -> the A1-A7 adaptation list.
1. Adapt 012 (this lane, no cost): apply A1-A4 in-migration and A5 in the down as a
   DUAL-SUBSTRATE file -- keep the `ops_dev`/`ops_test` behavior green while adding a
   non-super / shared-DB path. Re-run `test_012` on `ops_test`/`ops_dev` locally to prove no
   dev regression BEFORE spending a branch.
2. Branch proof (needs `create_branch` -- COST GATE, operator GO):
   - A. base: apply ops 001-011 byte-exact -> expect clean (postgres-owned).
   - B. RED: apply UNADAPTED 012 -> expect failure on the first superuser-only op
        (A1 `alter role`, or A3 database CONNECT), zero residue (BEGIN..COMMIT rollback).
   - C. GREEN: apply ADAPTED 012 -> expect clean.
   - D. boundary: run the adapted acceptance harness against the branch as
        ops_api / ops_intake_writer -> the 18/18 two-oracle analog holds on the real
        substrate; DML negative control (bypass asymmetry; blocked vs intended paths through
        the SECURITY DEFINER funnel).
   - E. advisors (security) -> classify ops findings (A6 expected: RLS-off ops relations, by
        design) vs inherited-parent noise (public/tcc/... pre-existing, out of scope).
   - F. `delete_branch` -> zero residue; `list_branches` shows only main.
3. Serving-DSN contract (no secret in this lane): specify the two serving roles as
   schema-scoped LOGIN roles on the single prod DB. The control-plane API connects as
   `ops_api` (NEVER `postgres` -- postgres has BYPASSRLS and would bypass the boundary);
   intake connects as `ops_intake_writer`. Arming = the operator sets each role password OOB
   in Infisical; the AI verifies the round-trip value-silently in the LATER packet.
4. Package evidence + IRP cross-engine (Codex) -> operator ratifies -> later prod-apply packet.

## Acceptance harness adaptation (ops semantics)
The records harness proved Gate-5 (RLS/FORCE/policies/audit). ops has a DIFFERENT boundary: no
RLS/Data-API surface; the guarantee is the 3-role least-privilege split + the SECURITY DEFINER
mutation funnel. Reuse the two-oracle method from `docs/operations/ops-role-pass-2026-07-08.py`
verbatim (behavioral rolled-back-txn SQLSTATE classification + catalog-exact `has_*_privilege`),
retargeted to the branch DB via the in-process dbname override. ops-specific negative controls:
`ops_api` cannot INSERT apparatus/scopes (fabrication), cannot write recognition tables, cannot
EXECUTE billing fns; `ops_intake_writer` cannot EXECUTE any mutation fn; the elevated write
happens ONLY through the definer funnel. Positive: writer writes the intake surface; api reads
its recognition views + invokes the recognition definer fn.

## Open decisions (operator -- at spec review, before the COST GATE)
- **D8-1 (A6 RLS posture)**: confirm ops relations are NOT Data-API-served and therefore do
  NOT get FORCE-RLS in this lane (served via the control-plane API as the `ops_api` login
  role). Lean: CONFIRM -- ops is not a PostgREST/anon surface; RLS adds no boundary the grant
  matrix lacks, and forcing it now is scope creep. If ops is ever Data-API-exposed, that is its
  own lane.
- **D8-2 (A2 edge disposition)**: after ownership transfer, KEEP postgres's ops_fn_owner
  membership as the ratified trusted-applier edge vs REVOKE it. Lean: KEEP (matches records
  INV7 exempt edges; revoking may block later idempotent re-apply).
- **D8-3 (A3 confirmation)**: ratify dropping the database-level CONNECT hygiene entirely in
  favor of schema-scoped USAGE on the shared DB. Lean: CONFIRM (mandatory -- the dedicated-DB
  block is unsafe on the shared prod DB).
- **D8-4 (adapted-012 shape)**: a SINGLE dual-substrate 012 with capability guards (detect
  non-super applier / shared DB and take the schema-scoped path; else the dedicated-DB path)
  vs a separate `012-managed` variant. Lean: SINGLE FILE with guards -- one source of truth;
  `ops_dev`/`ops_test` stay byte-green, prod uses the same asserted boundary.

## Gates (STOP points)
- `create_branch` (Supabase cost) -> explicit operator cost/status GO.
- serving-DSN arming (OOB secret custody) -> later packet.
- prod apply -> later packet.

## Definition of done (this lane)
Adapted dual-substrate 012 (dev-green + branch-green); a committed branch-proof evidence record
(RED 42501 / GREEN / boundary 18/18 analog / DML negative control / advisors classified /
zero-residue teardown); the serving-DSN contract; Codex cross-engine folded; operator
ratification. Then the prod-apply packet opens as a separate gated lane.
