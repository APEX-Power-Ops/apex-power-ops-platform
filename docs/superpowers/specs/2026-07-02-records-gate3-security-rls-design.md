# Records Gate 3 — Security / RLS Design

**Date:** 2026-07-02  ·  **Rev 2** (folds operator review: role-membership hardening, PUBLIC routine EXECUTE hygiene, SET SESSION AUTHORIZATION faithful proofs, DP9 rogue-view proof; D2=A ratified)
**Lane:** `records/gate3-security-rls` (worktree `/home/olares/code/apex/apex-records-gate3`)
**Dev DB:** `records_dev` (local PG17 cluster over mesh); disposable `records_val_*` for validation
**Prod target:** governed Supabase `fxoyniqnrlkxfligbxmg` — reviewable SQL first, NOT applied in this lane
**Migration:** `045_records_security_rls.sql` (+ `_down`)
**Authority / precedents:** `reference/records/CURRENT-STATE.md` "Next Gates" #3; the merged ops role-boundary lane `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (PR #55/#56); the Gate-2 validation harness (`run_validation.py`, `_dbtest.py`); the identity contract `.claude/PLATFORM/INTEGRATION_BACKBONE_IDENTITY_CONTRACT_2026-06-20.md`; Supabase RLS / function-privilege / view-security docs (D3 alignment).
**Status:** DRAFT for the Deep IRP pass, then operator ratification. No code built; no DB state touched.

---

## 0. Context & grounding (verified 2026-07-02)

Every claim below was checked against the live `records_dev` schema and the repo at `main 90ccf864`.

**Current posture (live probe):**
- `records` schema holds **15 tables + 2 views**, all owned by `postgres` (superuser).
- **RLS coverage is 0%** — 0 tables `ENABLE`d, 0 `FORCE`d, **0 policies**.
- **Grants are owner-only.** Sole grantee across all tables/views is `postgres`. Zero grants to `PUBLIC`/`anon`/`authenticated` or any login role. The `records` schema ACL is `NULL` (no `USAGE` to `PUBLIC`).
- The two views (`v_asset_test_history`, `v_pm_due`) are **not** `security_invoker` → they run as their superuser definer and would bypass base-table RLS once exposed.
- Only one function exists: `records.fn_set_updated_at()` (trigger helper, SECURITY INVOKER). **No SECURITY DEFINER surface.** Its `proacl` is `NULL` → it carries the **default PUBLIC EXECUTE** (see HIGH-2 / §3.4).
- The only plausible scoping columns (`form_submissions.project_ref`, `pm_events.project_ref`, `assets.site_ref`/`client_ref`) are **nullable soft UUIDs with no FK**. **No `tenant`/`org`/`customer`/`created_by`/`reviewer`/`approver` column exists anywhere.** Person identity is a **cross-DB contract-FK** (`persons.employee_ref → public.employees.id`, reconciliation-validated, never a DB FK).

**The core problem.** The schema is fail-*closed today, but only by grant-absence, not by design.* No least-privilege role model, no RLS backstop. The instant serving is granted anything, that role sees **every row** — nothing sits behind the grant. Gate 3 removes that cliff.

**What the ops lane already proved (reuse, don't reinvent):** ops migration 012 established a two-login-role + NOLOGIN-owner boundary with guarded idempotent role creation, unconditional flag correction, **explicit membership revocation** (NOSUPERUSER/NOBYPASSRLS does NOT stop a preexisting member from `SET ROLE` escalation), PUBLIC hygiene including **`REVOKE EXECUTE ON ALL ROUTINES`** (a `proacl IS NULL` default-PUBLIC-EXECUTE is invisible to `aclexplode(proacl)`), column-scoped grants, in-migration posture asserts, and a symmetric guarded down. Records mirrors that structure and **adds the RLS backstop ops chose not to build.**

---

## 1. Goal & non-goals

**Goal.** Establish and prove the records security substrate: (a) least-privilege application roles with an explicit, column-scoped grant matrix and **no membership-escalation path**; (b) RLS `ENABLE`d on every `records.*` table as a deny-by-default backstop, with `USING (true)` read policies for shared reference/catalog data and **role-scoped** policies for write-path data; (c) `security_invoker` on both views; (d) PUBLIC hygiene over tables **and routines**; all self-asserted in-migration and independently proven by a new harness tier under a **faithful non-superuser identity** (`SET SESSION AUTHORIZATION`) — on a disposable DB, reversibly, not applied to prod.

**Non-goals (explicit).**
- **Row-level tenant isolation.** This gate delivers a *role/operation* backstop, **not** row scoping. Interim write-path policies gate by *role*, not by row predicate. Real predicates depend on the tenancy model + soft-FK activation and are deferred (§11, D1).
- **Audit-log table + review/approval workflow** — Gate 5. Gate 3 establishes only the identity *hook* (`technician_person_id`) and the *column boundary* reserving review columns for that future flow.
- **SECURITY DEFINER function layer / reviewer role** — Gate 5 (no definer functions exist to own yet).
- Value Model V2; source-content serving policy (Gate 9); offline/PowerSync (Gate 6); any API/UI; prod Supabase apply; soft-FK activation (punch-list Chip 8).

---

## 2. Ratified decisions

| # | Decision | Resolution |
|---|---|---|
| **D1** | RLS depth | **A (amended).** RLS `ENABLE` on **all** `records.*` tables. Reference/catalog get `USING (true)` SELECT policies. Write-path get **role-scoped** policies (policy `TO <role>`), row predicates deferred. Framed as "role/operation backstop + least privilege," **not** row isolation. |
| **D2** | Object ownership | **A — keep `postgres` ownership. RATIFIED 2026-07-02 (operator).** Caveat recorded: with a superuser owner, `FORCE RLS` is inert on the owner path and superuser bypasses RLS — closed by the **serving invariant**: "the serving runtime MUST connect only as the non-owner app roles, never as the owner/superuser." Rationale in §2.1. |
| **D3** | Supabase reconciliation | **A.** Generic Postgres roles now; document the mapping to Supabase `anon`/`authenticated`/`service_role`; write policies so predicates can bind `auth.uid()`/`auth.jwt()` at the Supabase seam later. Supabase docs confirm: RLS must be enabled for exposed schemas; PG15+ views need `security_invoker` to inherit caller RLS; privileged/service roles bypass RLS. |
| **D4** | Gate 3 / Gate 5 boundary | **Confirmed.** Gate 3 = enforcement substrate + identity hook + non-superuser proof. Audit-log + review/approval = Gate 5. |
| **D5** | Role set | `records_api` (reader, LOGIN) + `records_intake_writer` (writer, LOGIN, column-scoped). `records_fn_owner` and reviewer/approver roles **deferred to Gate 5**. |
| **D6** | Reference-table writes | Owner/seed-path (migrations) only; both app roles SELECT. |
| **D7** | FORCE RLS | Under D2-A, `FORCE` is inert on the superuser owner; not relied upon. Write-path protection = `ENABLE` RLS + role-scoped policies applied to the non-owner app roles. |
| **D8** | Harness + CI | Add a non-superuser role/denial **Tier 5**; wire into Records CI (push-only). |

### 2.1 D2 = A — rationale (ratified)

The operator leaned B (re-own tables to a non-super `records_fn_owner`) then ratified **A** on the grounding evidence: (1) the ops lane keeps tables `postgres`-owned; (2) records' prod home is **Supabase, where serving connects as non-owner roles by construction**, so RLS enforces correctly on `postgres`-owned tables and re-owning would fight Supabase tooling + create a dev↔prod ownership divergence; (3) **every operator-required proof passes under A** because they all exercise non-owner roles — B's only gain is owner-path protection, inert on Supabase and redundant with the serving invariant. Cost: the owner/superuser-bypass caveat, closed by the serving invariant + the accidental-grant proof (DP5).

---

## 3. Role & grant contract

### 3.1 Roles (cluster-global; created + hardened guarded)

| Role | Login | Flags | Purpose | Supabase map (D3) |
|---|---|---|---|---|
| `records_api` | LOGIN | NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOREPLICATION | read-only serving surface | `authenticated` (read) |
| `records_intake_writer` | LOGIN | (same) | import/data-entry write surface, column-scoped | `authenticated` (write) / service path |

Passwords set **out-of-band by the operator** (Vault-first, L6 custody) on `records_dev`/prod — never in the migration. In the disposable validation DB the roles are created password-less and exercised via `SET SESSION AUTHORIZATION` (no login needed).

Creation + **membership hardening** (ops-012 proven; the HIGH-1 fix):
```sql
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_api') then create role records_api; end if;
  if not exists (select 1 from pg_roles where rolname='records_intake_writer') then create role records_intake_writer; end if;
end $$;
alter role records_api           with login nosuperuser nocreatedb nocreaterole nobypassrls noreplication;
alter role records_intake_writer with login nosuperuser nocreatedb nocreaterole nobypassrls noreplication;

-- HIGH-1: NOSUPERUSER/NOBYPASSRLS does NOT stop a preexisting member from SET ROLE escalation.
-- Neither app role may be a member of the other, or of ANY other role.
revoke records_intake_writer from records_api;
revoke records_api from records_intake_writer;
```
Flags are corrected **unconditionally**. Posture assert (FAILS the migration on drift): no privileged flags; both LOGIN; **neither app role is a member of the other, and neither holds any role membership** (`pg_auth_members` join → zero rows for the two grantees; `pg_has_role(a,b,'member')` false both ways).

### 3.2 Table classes

- **Reference / catalog (9):** `asset_classes`, `form_templates`, `pm_programs`, `neta_procedures`, `neta_test_items`, `neta_tables`, `asset_class_neta_procedure`, `neta_procedure_xref`, `neta_table_source_links`. Shared firm-internal catalog; both roles SELECT; writes owner/seed-only.
- **Write-path (6):** `assets`, `form_submissions`, `form_field_values`, `pm_schedules`, `pm_events`, `persons`. Writer gets column-scoped INSERT/UPDATE; reader SELECT.

### 3.3 Grant matrix (column-scoped per write-path table)

`records_api` = **SELECT on every table + both views**, nothing else.

`records_intake_writer` = SELECT on all tables + `USAGE` on schema `records`, plus:

| Table | Writer INSERT columns | Writer UPDATE columns | **Reserved (NOT writer — future reviewer/adjudicator/Gate-5)** |
|---|---|---|---|
| `assets` | identity/nameplate/location/provenance cols | same subset + `last_tested_at` | `status`, `condition` |
| `form_submissions` | template_id, asset_id, project_ref, work_package_ref, pm_event_id, overall_assessment, as_found_as_left, test_status_label, job_number, test_date, technician, ambient_temp_c, relative_humidity, test_equipment, summary_notes, neta_standard, source, provenance_status, legacy_source_id, technician_person_id, origin_device, client_rev, client_captured_at, synced_at | same data set | **`status`** (draft→reviewed→approved), **`reviewed_by`** |
| `form_field_values` | all reading/acceptance/sync cols | same | — |
| `pm_schedules` | enrollment/next-due cols | same | — |
| `pm_events` | schedule/asset/status/outcome/sync cols | same | — |
| `persons` | `display_name`, `worker_class` | `display_name`, `worker_class` | **`employee_ref`**, **`match_adjudicated_by`**, **`match_adjudicated_at`**, **`match_confidence`** (human-adjudication only, contract C3) |

Notes:
- On INSERT, un-granted columns fall to DEFAULT — a writer inserting a submission **cannot set `status`; it defaults to `'draft'`.** The review boundary is baked into the grant layer: the writer creates drafts only, never approves. Same for `assets.status`/`condition`, `persons.employee_ref` (stay NULL until adjudication).
- `updated_at` is trigger-maintained (`fn_set_updated_at`, INVOKER, mutates NEW only) — a BEFORE-trigger NEW assignment is **not** a privilege-checked column write, so the writer needs **no** `updated_at` grant (verified: revoking PUBLIC EXECUTE on the trigger fn does not break writer-fired `updated_at`). Grant `updated_at` only if the app *explicitly* stamps it.
- Exact per-column lists are finalized against the live DDL in the plan; the reserved columns are the load-bearing boundary and are asserted in-migration (`has_column_privilege` negatives) and by Tier 5 (DP2/DP3).

### 3.4 PUBLIC hygiene (tables **and routines**)
- `revoke create on schema public from public;`
- No `PUBLIC` `USAGE` on `records`; grant `USAGE` explicitly to the two roles.
- **HIGH-2: `revoke execute on all routines in schema records from public;`** — `records.fn_set_updated_at()` has `proacl IS NULL` = implicit default PUBLIC EXECUTE, which `aclexplode(proacl)` reports as zero rows (false-green). Revoke it explicitly (matches ops-012 §[2]).
- **Assert with the materialized default ACL**, not raw `proacl`: PUBLIC (grantee `0`) holds no EXECUTE on any `records` routine via `aclexplode(coalesce(p.proacl, acldefault('f', p.proowner)))` → zero rows; and zero PUBLIC grants on any `records` table.
- **Database-level CONNECT hygiene** (`revoke connect on database ... from public`) is **Supabase-caveated** — Supabase manages database CONNECT; do not encode a database-CONNECT revoke that would fight the platform. Optional in bare-PG dev; noted, not required.

---

## 4. RLS model

1. **`ENABLE ROW LEVEL SECURITY` on all 15 `records.*` tables** (AC1). Under D2-A, `FORCE` is inert (superuser owner) and not relied upon (D7).
2. **Reference/catalog:** one permissive policy `FOR SELECT TO records_api, records_intake_writer USING (true)`. No write policy for app roles.
3. **Write-path (interim, role-scoped — the mechanism that makes DP5/DP9 pass):**
   - `FOR SELECT TO records_api, records_intake_writer USING (true)`
   - `FOR INSERT TO records_intake_writer WITH CHECK (true)`
   - `FOR UPDATE TO records_intake_writer USING (true) WITH CHECK (true)` (column boundary enforced by the grant)
   - **No policy names any other role.** A role not listed in any policy, with RLS enabled, gets **default-deny → 0 rows** even if mistakenly granted SELECT ("role/operation backstop"). When row predicates land, `USING (true)` becomes `USING (<project/tenant predicate>)` — bindable to `auth.uid()`/`auth.jwt()` at the Supabase seam — without touching role wiring.
4. **Views:** `ALTER VIEW records.v_asset_test_history SET (security_invoker = true);` and same for `v_pm_due` (AC4). Grant SELECT on both to `records_api`.

---

## 5. Migration `045_records_security_rls.sql`

Structure mirrors ops-012 (sectioned, guarded, self-asserting, reversible):

1. **[1] Roles + flag + membership hardening** — guarded create; unconditional flag `alter role`; revoke cross-membership; posture assert (no privileged flags; both LOGIN; no memberships / no escalation path).
2. **[2] PUBLIC hygiene** — `revoke create on schema public from public`; grant `usage on schema records` to both roles; **`revoke execute on all routines in schema records from public`**; posture assert via `acldefault`-materialized ACL (zero PUBLIC EXECUTE on routines; zero PUBLIC grants on tables).
3. **[3] Grant matrix** — `records_api` SELECT-all; `records_intake_writer` column-scoped INSERT/UPDATE + SELECT-all per §3.3; positive + negative `has_column_privilege` asserts (writer holds the data columns; NOT `form_submissions.status`/`reviewed_by`, `persons.employee_ref`/`match_*`, `assets.status`/`condition`; `records_api` holds no write privilege).
4. **[4] RLS** — `enable row level security` on all 15 tables; create reference `USING(true)` policies + write-path role-scoped policies (§4); assert every `records.*` table `relrowsecurity = true`.
5. **[5] Views** — `security_invoker = true` on both; assert; grant SELECT to `records_api`.
6. **[6] Final consolidated posture assert** — re-verifies the whole boundary (roles, no-membership, no-PUBLIC on tables+routines, RLS-on-all, invoker views, reserved-column negatives) and RAISEs on drift, so a bad apply fails loud **inside the migration** on `records_dev`/prod where pytest does not run.

Idempotency: guarded role creation; `drop policy if exists` then create; safe to re-apply and safe on a shared cluster.

**`045_..._down.sql`** (symmetric, guarded, ordered): drop policies → `disable row level security` → revert views to non-invoker → re-grant PUBLIC EXECUTE on routines (restore pre-045) → revoke the role grants (**database-scoped** revokes for the LOGIN roles — the ops-012 F-012-3 lesson: `DROP OWNED` strips shared-object CONNECT cluster-wide) → guarded `DROP ROLE` that **refuses** to drop a role holding an out-of-band password (`pg_authid.rolpassword IS NOT NULL`, the DEV-7 guard) or cross-DB dependencies. Restores the pre-045 posture; a ladder-symmetry artifact, not a security recommendation.

### 5.1 Post-045 lane-invariant flip (the LOW/MED fix)

Migration 045 **intentionally breaks** the "records 001–044 defines NO RLS/grants" lane invariant. `test_043` and `test_044` assert RLS-disabled at *their* stack position — correct and green under the Tier-3 incremental walk (they run pre-045), but a **standalone** run against a post-045 `records_dev` would fail by design. Fix: update the comments in `test_043_*`/`test_044_*` (and the MANIFEST 043/044 "NO RLS/grants" notes) to scope the assertion to "through migration 044; 045 enables RLS by design — use the incremental runner." No logic change; the walk stays authoritative.

### 5.2 Three verification layers (avoid duplication confusion)
- **In-migration posture asserts** (part of 045.sql) — self-verify at apply time; fail the migration on drift; the ONLY guard on `records_dev`/prod (pytest does not run there).
- **`test_045` (Tier-3 paired, static)** — schema-shape introspection at the 045 stack state: RLS flags, policy existence, grant matrix via `has_column_privilege`, `security_invoker` set, `acldefault`-materialized no-PUBLIC-EXECUTE.
- **Tier 5 (dynamic)** — the SET-SESSION-AUTHORIZATION denial/escalation/accidental-grant proofs on the fully-migrated DB (§6).

---

## 6. Harness — Tier 5 (roles / grants / denial)

Extends `run_validation.py`. Runs on the disposable `records_val_*` DB **after** Tier 3 walks through migration 045, **before** the `finally` drop.

**Faithful identity (the anti-superuser-masking fix).** Proofs use **`SET SESSION AUTHORIZATION <role>` … `RESET SESSION AUTHORIZATION`**, not `SET ROLE` from the superuser session: `SET ROLE` from a superuser can switch to *any* role and cannot prove a membership-gated escalation is blocked. `SET SESSION AUTHORIZATION` assumes the role's identity fully (grant/RLS/membership all evaluate as that role).

**Seam edits (from harness grounding):** `parse_tiers` valid set `{0,1,2,3,4,5}` (×3 incl. the `unknown` subtraction + error string); `db_wanted = wanted & {3,4,5}`; `tier5_roles(child_dsn, executed)` next to `tier4_import_db`, gated on Tier 3 having built the schema; return `Tier("5-roles", PASS/FAIL, detail)`.

**Seed first (anti-false-green):** before any "expect 0 rows" proof, ensure ≥1 row exists in the target write-path table (via PP2, or a superuser insert) so a 0-row result proves RLS denial rather than a vacuously empty table.

**Proofs (each a hard FAIL if the expectation is not met):**

*Positive:*
- PP1 `set session authorization records_api;` SELECT a write-path table + both views → succeeds. `reset session authorization`.
- PP2 `set session authorization records_intake_writer;` INSERT a submission (omitting `status`) → succeeds, lands `status='draft'`.

*Denial / escalation:*
- DP1 `set session authorization records_api;` INSERT/UPDATE/DELETE on any write-path table → `insufficient_privilege`.
- DP2 `set session authorization records_intake_writer;` `update form_submissions set status='approved'` → raises; `set reviewed_by=…` → raises (column grant).
- DP3 writer `update persons set employee_ref=…` / `set match_adjudicated_by=…` → raises.
- DP4 writer DDL (`drop table` / `alter table`) → raises.
- **DP-ESC (HIGH-1):** `set session authorization records_api; set role records_intake_writer;` → **raises** (records_api is not a member of the writer — no escalation path). Mirror for the writer→reader direction.
- DP5 **accidental-grant proof.** Inside a rolled-back transaction: `create role <run_scoped_rogue>; grant usage on schema records to rogue; grant select on records.form_submissions to rogue; set session authorization rogue; select count(*) from records.form_submissions` → **0** (no policy names rogue → default-deny); attempted write → raises. `reset session authorization; rollback` removes rogue + grant cleanly (CREATE ROLE/GRANT are transactional).
- DP6 **no-PUBLIC assert:** via `aclexplode(coalesce(proacl, acldefault('f', proowner)))` for routines + table ACLs, grantee `0` → zero EXECUTE/privilege rows.
- DP7 **RLS-enabled assert:** every `records.*` table `relrowsecurity = true`.
- DP8 **security_invoker assert:** both views have `security_invoker` on.
- DP9 **view-RLS proof (MED fix — proves invoker actually prevents definer bypass).** Inside a rolled-back transaction: `create role <rogue>; grant usage on schema records + select on records.v_asset_test_history AND its base tables to rogue; set session authorization rogue; select count(*) from records.v_asset_test_history` → **0** with `security_invoker` (base-table RLS denies rogue); a non-invoker view would leak as owner (>0). `rollback`.

**Teardown (correction #2 + ops-012 guards), in `finally`, in order:**
1. `reset session authorization`; close the disposable-DB connection.
2. `drop database … with (force)` — removes all per-DB grants.
3. Drop the two app roles **only if this run created them** (snapshot `records_api`/`records_intake_writer` existence *before* the walk) **and** they hold no out-of-band password (`pg_authid.rolpassword IS NULL`). A validation run can **never** drop a real serving role that `records_dev`/prod provisioned. Run-scoped allowlist assertion guards any dropped name.

Invariants preserved (Gate-2): `guard_target` records_dev refusal on every DSN; admin-dbname=`postgres`; `records_val_*` allowlist; no hardcoded credentials; explicit `_child_env`; unmasked exit codes; `--require-db` turns SKIP into failure. **Concurrency assumption:** validation runs are serialized per cluster; fixed-name app roles are created idempotently and dropped only when this run created them — documented, not silently assumed.

---

## 7. Acceptance criteria

- **AC1** Every `records.*` table has RLS `ENABLE`d (0 without).
- **AC2** Zero `PUBLIC`/`anon` grants on any `records` table **or routine** (materialized-ACL assert, DP6); `records` schema has no PUBLIC `USAGE`.
- **AC3** Least-privilege matrix in place: `records_api` cannot write anywhere; `records_intake_writer` holds exactly the §3.3 columns and none of the reserved columns; **neither app role can `SET ROLE`-escalate to the other** (DP-ESC). Proven by in-migration asserts + Tier 5 (DP1–DP4, DP-ESC).
- **AC4** Both views are `security_invoker = true` (DP8) and a rogue role reading through the view is denied by base-table RLS (DP9).
- **AC5** Non-superuser execution proven under `SET SESSION AUTHORIZATION` app roles (PP1–PP2), never masked by the superuser session.
- **AC6** Tier 5 runs on a disposable `records_val_*` DB only; `records_dev` appears in no connection; app roles dropped only when harness-created; Gate-2 invariants intact; Records CI green.
- **AC7** `045` + `045_down` are reversible and reviewed; **not** applied to prod Supabase in this lane.

---

## 8. Denial + sanctioned-path proofs (summary)

Positive: PP1 (reader SELECT), PP2 (writer creates draft only). Denial/escalation: DP1 (reader no-write), DP2 (writer no status/reviewed_by), DP3 (writer no persons adjudication cols), DP4 (writer no DDL), **DP-ESC (no SET-ROLE escalation)**, DP5 (accidental-grant → RLS default-deny), DP6 (no-PUBLIC incl. routines), DP7 (RLS-on-all), DP8 (invoker views), DP9 (rogue-through-view denied). Mandatory red proofs (Gate-2 analog): **DP2** (column boundary), **DP5** (accidental-grant backstop), **DP-ESC** (escalation).

---

## 9. CI

Extend `.github/workflows/records-ci.yml` to run `--only 5` (or the full ladder with `--require-db`) in the existing postgres-17 service job. Push-only trigger; `persist-credentials: false` retained. Tier 5 needs only the maintenance role already provisioned for Tiers 3/4 — no new CI secret (roles created by 045, exercised via `SET SESSION AUTHORIZATION`).

---

## 10. Security & credential custody

- App-role passwords are operator-provisioned out-of-band, Vault-first; the AI never handles the values; the migration never contains a password.
- No DSN/password echoed in code, logs, commits, or PR text.
- No test/script/runner connects to `records_dev` (`guard_target` extends to every Tier 5 connection).
- Three independent controls (defense-in-depth): the reserved-column grant boundary (DP2), the RLS default-deny (DP5), and the no-membership-escalation (DP-ESC). A mistaken grant is caught by RLS; a mistaken policy is caught by the grant; a mistaken membership is caught by the escalation proof.

---

## 11. Risks / open questions

1. **Owner-bypass caveat (D2-A)** — superuser/owner bypasses RLS; closed by the serving invariant "serving connects only as non-owner app roles." Stated in the migration header + the serving runbook.
2. **No row isolation** — until a tenancy model + soft-FK activation lands, any granted app role sees all firm rows. Correct for the single-firm model; stated so the spec does not imply row scoping.
3. **Fixed-name cluster roles vs disposable-per-run DBs** — resolved by snapshot-and-drop-only-if-created + out-of-band-password guard (§6); assumes serialized validation runs per cluster.
4. **Supabase drift (D3)** — proving in bare-PG risks a semantic gap vs Supabase RLS (`auth.uid()`); mitigated by `USING (true)` interim policies that swap to `auth`-bound predicates at the seam. Full Supabase mapping (roles → `anon`/`authenticated`/`service_role`; database-CONNECT hygiene) is a separate reconciliation, not this gate.
5. **Import-path tests run as superuser (Tier 4)** — adding RLS must not break them (superuser bypasses); verify the records-import DB tests do not assume a specific owner or a non-RLS table.
6. **`proacl IS NULL` false-green class** — closed by the `acldefault`-materialized assert (§3.4/DP6); any future records function must re-run the routine REVOKE or the [2] assert will catch it.

---

## 12. Out of scope (restated)

Row-scoping backfill; soft-FK activation (Chip 8); audit-log table + review/approval workflow + reviewer/`records_fn_owner` roles (Gate 5); SECURITY DEFINER function layer; Supabase prod apply; source-content serving policy (Gate 9); offline/PowerSync (Gate 6); Value Model V2; API/UI implementation.
