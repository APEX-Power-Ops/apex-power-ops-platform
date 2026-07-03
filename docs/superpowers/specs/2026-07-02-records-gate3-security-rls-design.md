# Records Gate 3 — Security / RLS Design

**Date:** 2026-07-02
**Lane:** `records/gate3-security-rls` (worktree `/home/olares/code/apex/apex-records-gate3`)
**Dev DB:** `records_dev` (local PG17 cluster over mesh); disposable `records_val_*` for validation
**Prod target:** governed Supabase `fxoyniqnrlkxfligbxmg` — reviewable SQL first, NOT applied in this lane
**Migration:** `045_records_security_rls.sql` (+ `_down`)
**Authority / precedents:** `reference/records/CURRENT-STATE.md` "Next Gates" #3; the merged ops role-boundary lane `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (PR #55/#56); the Gate-2 validation harness (`infra/database/migrations/records/run_validation.py`, `_dbtest.py`); the identity contract `.claude/PLATFORM/INTEGRATION_BACKBONE_IDENTITY_CONTRACT_2026-06-20.md`.
**Status:** DRAFT for operator review. No code built; no DB state touched.

---

## 0. Context & grounding (verified 2026-07-02)

Every claim below was checked against the live `records_dev` schema and the repo at `main 90ccf864`.

**Current posture (live probe):**
- `records` schema holds **15 tables + 2 views**, all owned by `postgres` (superuser).
- **RLS coverage is 0%** — 0 tables `ENABLE`d, 0 `FORCE`d, **0 policies**.
- **Grants are owner-only.** The sole grantee across all tables/views is `postgres`. Zero grants to `PUBLIC`/`anon`/`authenticated` or any login role. The `records` schema ACL is `NULL` (no `USAGE` to `PUBLIC`).
- The two views (`v_asset_test_history`, `v_pm_due`) are **not** `security_invoker` → they run as their superuser definer and would bypass base-table RLS once exposed.
- Only one function exists: `records.fn_set_updated_at()` (trigger helper, SECURITY INVOKER). **No SECURITY DEFINER surface.**
- The only plausible scoping columns (`form_submissions.project_ref`, `pm_events.project_ref`, `assets.site_ref`/`client_ref`) are **nullable soft UUIDs with no FK** (activation is a later punch-list chip). **No `tenant`/`org`/`customer`/`created_by`/`reviewer`/`approver` column exists anywhere.** Person identity is a **cross-DB contract-FK** (`persons.employee_ref → public.employees.id`, reconciliation-validated, never a DB FK).

**The core problem.** The schema is fail-*closed today, but only by grant-absence, not by design.* There is no least-privilege role model and no RLS backstop. The instant the serving runtime is granted anything, that role sees **every row** — nothing sits behind the grant. Gate 3 removes that cliff.

**What the ops lane already proved (reuse, don't reinvent):** ops migration 012 established a two-login-role + NOLOGIN-owner boundary with guarded idempotent role creation, unconditional flag correction, membership revocation, PUBLIC hygiene, column-scoped grants, in-migration posture asserts (the migration FAILS on drift), and a symmetric guarded down. Records mirrors that structure and **adds the RLS backstop that ops chose not to build.**

---

## 1. Goal & non-goals

**Goal.** Establish and prove the records security substrate: (a) least-privilege application roles with an explicit, column-scoped grant matrix; (b) RLS `ENABLE`d on every `records.*` table as a deny-by-default backstop, with `USING (true)` read policies for shared reference/catalog data and **role-scoped** policies for write-path data; (c) `security_invoker` on both views; (d) PUBLIC hygiene; all self-asserted in-migration and independently proven by a new harness tier under a non-superuser identity — on a disposable DB, reversibly, not applied to prod.

**Non-goals (explicit).**
- **Row-level tenant isolation.** This gate delivers a *role/operation* backstop, **not** row scoping. Interim write-path policies gate by *role*, not by row predicate. Real project/tenant row predicates depend on the tenancy model + soft-FK activation and are deferred (see §11, D1).
- **Audit-log table + review/approval workflow** — Gate 5 (Import Sessions). Gate 3 establishes only the identity *hook* (which role wrote; the `technician_person_id` linkage) and the *column boundary* that reserves review columns for that future flow.
- **SECURITY DEFINER function layer / reviewer role** — deferred to Gate 5 (no definer functions exist to own yet).
- Value Model V2; source-content serving policy (Gate 9); offline/PowerSync (Gate 6); any API/UI implementation; prod Supabase apply; soft-FK activation (punch-list Chip 8).

---

## 2. Ratified decisions

| # | Decision | Resolution |
|---|---|---|
| **D1** | RLS depth this gate | **A (amended).** RLS `ENABLE` on **all** `records.*` tables. Shared reference/catalog tables get broad `USING (true)` SELECT policies (backstop invariant holds without faking tenant-scope). Write-path tables get **role-scoped** policies (policy `TO <role>`), row predicates deferred. Framed as "role/operation backstop + least privilege," **not** row isolation. |
| **D2** | Object ownership | **A — keep `postgres` ownership** (see §2.1: recommendation shifted from the B lean on new evidence; flagged for final ratification). Record the caveat: with a superuser owner, `FORCE RLS` is inert on the owner path and superuser bypasses RLS — mitigated by the serving invariant "the serving runtime MUST connect only as the non-owner app roles, never as the owner/superuser." |
| **D3** | Supabase reconciliation | **A.** Generic Postgres roles now; document the mapping to Supabase `anon`/`authenticated`/`service_role`; write policies so their predicates can bind `auth.uid()`/`auth.jwt()` at the Supabase seam later. |
| **D4** | Gate 3 / Gate 5 boundary | **Confirmed.** Gate 3 = enforcement substrate + identity hook + non-superuser proof. Audit-log table + review/approval workflow = Gate 5. |
| **D5** | Role set | `records_api` (reader, LOGIN) + `records_intake_writer` (writer, LOGIN, column-scoped). `records_fn_owner` and a reviewer/approver role **deferred to Gate 5** (nothing to own / no review flow yet). |
| **D6** | Reference-table writes | Owner/seed-path (migrations) only; both app roles get SELECT. |
| **D7** | FORCE RLS scope | Under D2-A, `FORCE` is inert on the superuser owner. Do **not** rely on it; write-path protection comes from `ENABLE` RLS + role-scoped policies applied to the non-owner app roles. (If D2 flips to B, `FORCE` on write-path tables becomes load-bearing — see §2.1.) |
| **D8** | Harness + CI | Add a non-superuser role/denial **Tier 5** to `run_validation.py`; wire it into Records CI (push-only, per the Gate-2 D-CI pattern). |

### 2.1 D2 — recommendation shifted from the operator's B-lean (needs final ratification)

The operator leaned **B** (re-own `records.*` to a non-superuser `records_fn_owner` so `FORCE RLS` bites the owner) "if you can tolerate the migration complexity," and explicitly authorized A with the documented caveat. On grounding I recommend **A**, on three pieces of evidence the original framing did not weigh:

1. **Ops precedent.** The further-along ops lane keeps its tables `postgres`-owned and enforces least-privilege via grants (no table re-ownership). Re-owning tables is not the platform's least-privilege pattern here.
2. **Supabase serving is non-owner by construction.** Records' governed prod home is Supabase, where the serving runtime connects as `authenticated`/`anon` (via PostgREST), never as the table owner. RLS therefore enforces correctly on `postgres`-owned tables because the serving roles are non-owner. Re-owning tables to a custom role would *fight* Supabase tooling (which assumes `postgres` ownership) and create a dev↔prod ownership divergence.
3. **Every operator-required proof passes under A.** All app-role denial proofs, the column-scoped writer proofs, and the accidental-grant proof exercise **non-owner** roles via `SET ROLE`; RLS applies to them regardless of who owns the table. D2-B's only added protection is the owner path itself — which is inert on Supabase and redundant with the serving invariant.

**Net:** A gives the operator everything they asked for at lower complexity and better prod alignment; its sole cost is the owner/superuser-bypass caveat, closed by the documented serving invariant + the accidental-grant proof. **If the operator prefers B for defense-in-depth against a misconfigured owner-connection in bare-PG dev,** the migration gains an exhaustive `ALTER ... OWNER TO records_fn_owner` block over every table+view (with an in-migration completeness assert that zero `records.*` relations remain `postgres`-owned) + `FORCE` on write-path tables + a symmetric down; the harness and proofs are otherwise unchanged. This is the one open decision for the spec-review gate.

---

## 3. Role & grant contract

### 3.1 Roles (cluster-global; created guarded)

| Role | Login | Flags | Purpose | Supabase map (D3) |
|---|---|---|---|---|
| `records_api` | LOGIN | NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOREPLICATION | read-only serving surface | `authenticated` (read) |
| `records_intake_writer` | LOGIN | (same) | import/data-entry write surface, column-scoped | `authenticated` (write) / service path |

Passwords for the two LOGIN roles are set **out-of-band by the operator** (Vault-first, L6 custody) on `records_dev`/prod — **never in the migration**. In the disposable validation DB the roles are created password-less and exercised via `SET ROLE` (no login needed).

Creation pattern (ops-012 proven, idempotent across the shared cluster):
```sql
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_api') then create role records_api; end if;
  if not exists (select 1 from pg_roles where rolname='records_intake_writer') then create role records_intake_writer; end if;
end $$;
alter role records_api           with login nosuperuser nocreatedb nocreaterole nobypassrls noreplication;
alter role records_intake_writer with login nosuperuser nocreatedb nocreaterole nobypassrls noreplication;
```
Flags are corrected **unconditionally** (M3 pattern) and an in-migration posture assert FAILS the migration if any role holds a privileged flag.

### 3.2 Table classes

- **Reference / catalog (9):** `asset_classes`, `form_templates`, `pm_programs`, `neta_procedures`, `neta_test_items`, `neta_tables`, `asset_class_neta_procedure`, `neta_procedure_xref`, `neta_table_source_links`. Shared firm-internal catalog; both roles SELECT; writes owner/seed-only.
- **Write-path (6):** `assets`, `form_submissions`, `form_field_values`, `pm_schedules`, `pm_events`, `persons`. Writer gets column-scoped INSERT/UPDATE; reader SELECT.

### 3.3 Grant matrix (column-scoped per write-path table)

`records_api` = **SELECT on every table + both views**, nothing else.

`records_intake_writer` = SELECT on all tables + `USAGE` on the `records` schema, plus:

| Table | Writer INSERT columns | Writer UPDATE columns | **Reserved (NOT writer — future reviewer/adjudicator/Gate-5)** |
|---|---|---|---|
| `assets` | identity/nameplate/location/provenance cols | same subset + `last_tested_at` | `status`, `condition` (asset lifecycle/assessment) |
| `form_submissions` | template_id, asset_id, project_ref, work_package_ref, pm_event_id, overall_assessment, as_found_as_left, test_status_label, job_number, test_date, technician, ambient_temp_c, relative_humidity, test_equipment, summary_notes, neta_standard, source, provenance_status, legacy_source_id, technician_person_id, origin_device, client_rev, client_captured_at, synced_at | same data set | **`status`** (draft→reviewed→approved lifecycle), **`reviewed_by`** |
| `form_field_values` | all reading/acceptance/sync cols | same | — |
| `pm_schedules` | enrollment/next-due cols | same | — |
| `pm_events` | schedule/asset/status/outcome/sync cols | same | — |
| `persons` | `display_name`, `worker_class` | `display_name`, `worker_class` | **`employee_ref`**, **`match_adjudicated_by`**, **`match_adjudicated_at`**, **`match_confidence`** (human-adjudication only, contract C3) |

Notes:
- On INSERT, un-granted columns fall to their DEFAULT — so a writer inserting a submission **cannot set `status`; it defaults to `'draft'`.** This bakes the review boundary into the grant layer: the writer can only create drafts, never approve. Same for `assets.status`/`condition`, `persons.employee_ref` (stay NULL until adjudication).
- `updated_at` is trigger-maintained (`fn_set_updated_at`, INVOKER, mutates NEW only) — the writer needs **no** grant for it (a BEFORE-trigger NEW assignment is not a privilege-checked column write). Grant `updated_at` only if the app *explicitly* stamps it.
- Exact per-column lists are finalized against the live DDL in the plan; the reserved columns above are the load-bearing boundary and are asserted both in-migration (`has_column_privilege` negative asserts) and by Tier 5 denial proofs.

### 3.4 PUBLIC hygiene (portable subset of ops-012)
- `revoke create on schema public from public;`
- No `PUBLIC` `USAGE` on the `records` schema; grant `USAGE` explicitly to the two roles.
- Assert zero `PUBLIC` grants remain on any `records` table/routine (`aclexplode`, grantee `0`).
- **Database-level CONNECT hygiene** (`revoke connect on database ... from public`) is **Supabase-caveated** — Supabase manages database CONNECT; do not encode a database-CONNECT revoke that would fight the platform. Optional in bare-PG dev; noted, not required.

---

## 4. RLS model

1. **`ENABLE ROW LEVEL SECURITY` on all 15 `records.*` tables** (AC1). Under D2-A, `FORCE` is inert (superuser owner) and is not relied upon (D7).
2. **Reference/catalog tables:** one permissive policy `FOR SELECT TO records_api, records_intake_writer USING (true)`. No write policy for app roles (writes are owner/seed-only).
3. **Write-path tables (interim, role-scoped — the mechanism that makes the accidental-grant proof pass):**
   - `FOR SELECT TO records_api, records_intake_writer USING (true)`
   - `FOR INSERT TO records_intake_writer WITH CHECK (true)`
   - `FOR UPDATE TO records_intake_writer USING (true) WITH CHECK (true)` (column boundary enforced by the grant, not the policy)
   - **No policy names any other role.** A role not listed in any policy, with RLS enabled, gets **default-deny → 0 rows** even if mistakenly granted SELECT. This is the "role/operation backstop."
   - When row predicates land later, the `USING (true)` clauses become `USING (<project/tenant predicate>)` — bindable to `auth.uid()`/`auth.jwt()` at the Supabase seam (D3) — without changing the role wiring.
4. **Views:** `ALTER VIEW records.v_asset_test_history SET (security_invoker = true);` and same for `v_pm_due` (AC4). With `security_invoker` + base-table RLS, the view applies the *caller's* RLS instead of the definer's. Grant SELECT on both views to `records_api`.

---

## 5. Migration `045_records_security_rls.sql`

Structure mirrors ops-012 (sectioned, guarded, self-asserting, reversible):

1. **[1] Roles + flag hardening** — guarded create; unconditional `alter role ... nosuperuser ...`; posture assert (no privileged flags; both LOGIN).
2. **[2] PUBLIC hygiene** — `revoke create on schema public from public`; grant `usage on schema records` to both roles; posture assert (zero PUBLIC grants on `records.*`).
3. **[3] Grant matrix** — `records_api` SELECT-all; `records_intake_writer` column-scoped INSERT/UPDATE + SELECT-all per §3.3; positive + negative `has_column_privilege` asserts (writer holds the data columns; writer does **not** hold `form_submissions.status`/`reviewed_by`, `persons.employee_ref`/`match_*`, `assets.status`/`condition`; `records_api` holds no write privilege anywhere).
4. **[4] RLS** — `enable row level security` on all 15 tables; create the reference `USING(true)` policies and the write-path role-scoped policies (§4); assert every `records.*` table has `relrowsecurity = true`.
5. **[5] Views** — `security_invoker = true` on both; assert set; grant SELECT to `records_api`.
6. **[6] Final posture assert** — a consolidated block that re-verifies the whole boundary (roles, no-PUBLIC, RLS-on-all, invoker views, the reserved-column negatives) and RAISEs on any drift, so a bad apply fails loud *inside the migration* on `records_dev`/prod where pytest does not run.

Idempotency: guarded role creation; `enable row level security` / `create policy` guarded (`drop policy if exists` then create, or `if not exists` where supported). The migration is safe to re-apply and safe on a shared cluster.

**`045_..._down.sql`** (symmetric, guarded, ordered): drop policies → `disable row level security` on all tables → revert views to non-invoker → revoke the grants (database-scoped revokes for the LOGIN roles; **not** `DROP OWNED` for a login role — the ops-012 F-012-3 lesson: `DROP OWNED` strips shared-object CONNECT cluster-wide) → guarded `DROP ROLE` that **refuses** to drop a role holding an out-of-band password (`pg_authid.rolpassword IS NOT NULL`, the DEV-7 guard) or cross-DB dependencies. Restores the pre-045 posture; it is a ladder-symmetry artifact, not a security recommendation.

---

## 6. Harness — Tier 5 (roles / grants / denial)

Extends `run_validation.py`. Runs on the disposable `records_val_*` DB **after** Tier 3 has walked the schema through migration 045, **before** the `finally` drop. All proofs run on the maintenance (superuser) connection via `SET ROLE <role>` / `RESET ROLE` — no passwords, no separate logins.

**Seam edits (exact, from harness grounding):** extend `parse_tiers` valid set to `{0,1,2,3,4,5}` (×3 spots incl. the `unknown` subtraction and the error string); add `5` to `db_wanted = wanted & {3,4,5}`; add `tier5_roles(child_dsn, executed)` next to `tier4_import_db`, gated on Tier 3 having built the schema; return a `Tier("5-roles", PASS/FAIL, detail)` so `summary()`/exit-code machinery picks it up.

**Proofs (each a hard FAIL if the expectation is not met):**

*Positive (sanctioned path):*
- PP1 `set role records_api; select` from a write-path table + both views → succeeds.
- PP2 `set role records_intake_writer; insert` a submission (omitting `status`) → succeeds, row lands with `status='draft'`.

*Denial:*
- DP1 `set role records_api;` INSERT/UPDATE/DELETE on any write-path table → `insufficient_privilege`.
- DP2 `set role records_intake_writer;` `update form_submissions set status='approved'` → raises; `set reviewed_by=...` → raises (column-scoped grant).
- DP3 `set role records_intake_writer;` `update persons set employee_ref=...` / `set match_adjudicated_by=...` → raises.
- DP4 `set role records_intake_writer;` DDL (`drop table` / `alter table`) → raises.
- DP5 **accidental-grant proof (correction #4).** Inside a transaction/savepoint that is **rolled back**: `create role <run_scoped_rogue>; grant usage on schema records to rogue; grant select on records.form_submissions to rogue; set role rogue; select ...` → RLS returns **0 rows** (no policy names rogue → default-deny); attempted write → raises. `reset role; rollback` removes the rogue role + grant cleanly (CREATE ROLE/GRANT are transactional).
- DP6 **no-PUBLIC-grant assert:** `aclexplode` over `records.*` tables + routines, grantee `0` → zero rows.
- DP7 **RLS-enabled assert:** every `records.*` table `relrowsecurity = true` → else FAIL.
- DP8 **security_invoker assert:** both views have `security_invoker` on.
- DP9 **reader read-through-view respects invoker RLS:** `set role records_api; select` from `v_asset_test_history` returns only policy-permitted rows (proves the view is not definer-bypassing).

**Teardown (correction #2 + ops-012 guards), in the `finally` block, in order:**
1. `reset role`; close the disposable-DB connection.
2. `drop database ... with (force)` (existing behavior) — removes all per-DB grants.
3. Drop the two app roles **only if this run created them** (snapshot `records_api`/`records_intake_writer` existence *before* the walk) **and** they hold no out-of-band password (`pg_authid.rolpassword IS NULL`). This guarantees a validation run can **never** drop a real serving role that `records_dev`/prod provisioned. A run-scoped allowlist assertion guards any role name the harness drops.

Invariants preserved (Gate-2): `guard_target` records_dev refusal on every DSN; admin-dbname=`postgres`; `records_val_*` allowlist before CREATE/DROP; no hardcoded credentials; explicit `_child_env`; unmasked exit codes; `--require-db` turns SKIP into failure. **Concurrency assumption:** validation runs are serialized per cluster (CI runs one job; local one at a time); the fixed-name app roles are created idempotently and dropped only when this run created them — documented, not silently assumed.

---

## 7. Acceptance criteria

- **AC1** Every `records.*` table has RLS `ENABLE`d (0 without).
- **AC2** Zero `PUBLIC`/`anon` grants on any `records` table/routine; `records` schema has no PUBLIC `USAGE` (harness-asserted, DP6).
- **AC3** The least-privilege matrix is in place: `records_api` cannot write anywhere; `records_intake_writer` holds exactly the §3.3 columns and none of the reserved columns; both proven by in-migration asserts and Tier 5 denial proofs (DP1–DP4).
- **AC4** Both views are `security_invoker = true` (DP8) and read-through respects invoker RLS (DP9).
- **AC5** Non-superuser execution proven: the sanctioned read + write paths succeed under `SET ROLE` app roles (PP1–PP2), never as superuser.
- **AC6** Tier 5 runs on a disposable `records_val_*` DB only; `records_dev` appears in no connection; app roles dropped only when harness-created; all Gate-2 invariants intact; Records CI green.
- **AC7** `045` + `045_down` are reversible and reviewed; **not** applied to prod Supabase in this lane.

---

## 8. Denial + sanctioned-path proofs (summary)

Positive: PP1 (reader SELECT), PP2 (writer creates draft only). Denial: DP1 (reader no-write), DP2 (writer no status/reviewed_by), DP3 (writer no persons adjudication cols), DP4 (writer no DDL), DP5 (accidental-grant → RLS default-deny), DP6 (no-PUBLIC), DP7 (RLS-on-all), DP8 (invoker views), DP9 (view read-through). Two of these are the mandatory red proofs analogous to Gate-2: **DP2** (column boundary) and **DP5** (accidental-grant backstop).

---

## 9. CI

Extend `.github/workflows/records-ci.yml` to run `--only 5` (or the full ladder with `--require-db`) in the existing postgres-17 service job. Push-only trigger (already the Gate-2 posture). `persist-credentials: false` retained. Tier 5 needs only the maintenance role already provisioned for Tiers 3/4 — no new CI secret (roles are created by migration 045, exercised via `SET ROLE`).

---

## 10. Security & credential custody

- App-role passwords are operator-provisioned out-of-band, Vault-first; the AI never handles the values; the migration never contains a password.
- No DSN/password is ever echoed in code, logs, commits, or PR text.
- No test/script/runner connects to `records_dev` (Gate-2 `guard_target` invariant extends to every Tier 5 connection).
- The reserved-column boundary + the RLS default-deny are the two independent controls (defense-in-depth): a mistaken grant is caught by RLS (DP5), a mistaken policy is caught by the grant (DP2).

---

## 11. Risks / open questions

1. **D2 final call (§2.1)** — A recommended on evidence vs the B lean. The one decision to ratify before build.
2. **Owner-bypass caveat (under A)** — superuser/owner bypasses RLS; closed by the serving invariant "serving connects only as non-owner app roles." Must be stated in the migration header and the serving runbook.
3. **No row isolation** — until a tenancy model + soft-FK activation lands, any granted app role sees all firm rows. Correct for the single-firm operational model, but must be stated so the spec does not imply row scoping.
4. **Fixed-name cluster roles vs disposable-per-run DBs** — resolved by snapshot-and-drop-only-if-created + out-of-band-password guard (§6); assumes serialized validation runs per cluster.
5. **Supabase drift (D3)** — proving in bare-PG risks a semantic gap vs Supabase RLS (`auth.uid()`); mitigated by writing `USING (true)` interim policies that swap to `auth`-bound predicates at the seam. The full Supabase mapping (roles → `anon`/`authenticated`/`service_role`; database-CONNECT hygiene) is a separate reconciliation, not this gate.
6. **Import-path tests run as superuser (Tier 4)** — adding RLS must not break them (superuser bypasses); verify the records-import DB tests do not assume a specific owner or a non-RLS table.

---

## 12. Out of scope (restated)

Row-scoping backfill; soft-FK activation (Chip 8); audit-log table + review/approval workflow + reviewer/`records_fn_owner` roles (Gate 5); SECURITY DEFINER function layer; Supabase prod apply; source-content serving policy (Gate 9); offline/PowerSync (Gate 6); Value Model V2; API/UI implementation.
