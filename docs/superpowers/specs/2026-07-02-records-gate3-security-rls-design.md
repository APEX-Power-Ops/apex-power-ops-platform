# Records Gate 3 — Security / RLS Design

**Date:** 2026-07-02  ·  **Rev 3** (folds the Claude+Codex IRP: membership hardening all-directions, savepoint discipline, CI full-ladder, serving-identity AC, full writer-column enumeration, multi-base-table view proof, factual fixes)
**Lane:** `records/gate3-security-rls` (worktree `/home/olares/code/apex/apex-records-gate3`)
**Dev DB:** `records_dev` (local PG17 cluster over mesh); disposable `records_val_*` for validation
**Prod target:** governed Supabase `fxoyniqnrlkxfligbxmg` — reviewable SQL first, NOT applied in this lane
**Migration:** `045_records_security_rls.sql` (+ `_down`)
**Authority / precedents:** `reference/records/CURRENT-STATE.md` "Next Gates" #3; the merged ops role-boundary lane `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (PR #55/#56); the Gate-2 harness (`run_validation.py`, `_dbtest.py`); the identity contract; Supabase RLS / function-privilege / view-security docs (D3).
**Status:** DRAFT (post-IRP rev 3) for operator ratification. No code built; no DB state touched.

> **Reviewer note (grounding).** The canonical tree is the **host** at `/home/olares/code/apex/apex-power-ops-platform`, `main 90ccf864` — where migrations 043/044, ops-012, `run_validation.py`, `_dbtest.py`, and `records-ci.yml` all live and were verified. The **local Windows checkouts are divergent** (`records/chip10-import`, tops out at mig 042) and must not be used to audit this spec. All §0 posture claims were checked against **live `records_dev` (PG 17.10)** and the host repo.

---

## 0. Context & grounding (verified 2026-07-02 against live records_dev + host repo)

- `records` schema: **15 tables + 2 views**, all owned by `postgres` (superuser). **RLS 0%** (0 enabled, 0 forced, 0 policies). Grants **owner-only** (zero to PUBLIC/anon/any login role). Schema ACL `NULL`.
- Views `v_asset_test_history`, `v_pm_due` are **not** `security_invoker` (would bypass base-table RLS once exposed). Each has **three** base tables (below).
- One function only: `records.fn_set_updated_at()` (trigger helper, SECURITY INVOKER, owner `postgres`, `proacl IS NULL` → carries the **default PUBLIC EXECUTE**).
- Only plausible scoping columns (`form_submissions.project_ref`, `pm_events.project_ref`, `assets.site_ref`/`client_ref`) are **nullable soft UUIDs, no FK**. **No tenant/org/customer/created_by/reviewer/approver column anywhere.** Person identity is a cross-DB contract-FK (`persons.employee_ref → public.employees.id`, never a DB FK).

**Core problem.** Fail-closed today only by grant-absence, not by design; the instant serving is granted anything, that role sees every row. Gate 3 removes that cliff, reusing the ops-012 pattern and adding the RLS backstop ops chose not to build.

---

## 1. Goal & non-goals

**Goal.** (a) least-privilege app roles with an explicit, fully-enumerated column-scoped grant matrix and **no membership-escalation path in either direction**; (b) RLS `ENABLE`d on every `records.*` table (deny-by-default backstop), `USING (true)` reads for reference/catalog, **role-scoped** policies for write-path; (c) `security_invoker` on both views; (d) PUBLIC hygiene over tables **and routines**; all self-asserted in-migration and independently proven by a new harness tier under a **faithful non-superuser identity** (`SET SESSION AUTHORIZATION`), on a disposable DB, reversibly, not applied to prod.

**Non-goals.** Row-level tenant isolation (role/operation backstop only; row predicates deferred); audit-log table + review/approval workflow (Gate 5 — Gate 3 establishes only the identity hook + the reserved-column boundary); SECURITY DEFINER function layer / reviewer role (Gate 5); Value Model V2; source-content policy (Gate 9); offline/PowerSync (Gate 6); API/UI; prod Supabase apply; soft-FK activation (Chip 8).

---

## 2. Ratified decisions

| # | Decision | Resolution |
|---|---|---|
| **D1** | RLS depth | **A (amended).** RLS on all tables; `USING(true)` reads for reference/catalog; write-path role-scoped policies (`TO <role>`); row predicates deferred. "Role/operation backstop," not row isolation. |
| **D2** | Object ownership | **A — keep `postgres` ownership. RATIFIED.** Caveat + F6 residual: `FORCE` inert on superuser owner; the owner/superuser path is not RLS-guarded — closed by the **serving invariant** + **AC8** custody control (§7), not by in-DB enforcement. |
| **D3** | Supabase | **A.** Generic PG roles now; documented mapping to `anon`/`authenticated`/`service_role`; predicates bindable to `auth.uid()`/`auth.jwt()` at the seam. |
| **D4** | Gate 3/5 boundary | **Confirmed.** Enforcement substrate + identity hook + non-superuser proof here; audit-log + review workflow = Gate 5. |
| **D5** | Role set | `records_api` (reader) + `records_intake_writer` (writer, column-scoped). `records_fn_owner` + reviewer/approver deferred to Gate 5. |
| **D6** | Reference writes | Owner/seed only; both roles SELECT. |
| **D7** | FORCE RLS | Inert under D2-A; not relied on. |
| **D8** | Harness + CI | Non-superuser Tier 5; CI runs the **full ladder with `--require-db`** (not `--only 5`). |

---

## 3. Role & grant contract

### 3.1 Roles + membership hardening (both directions)

| Role | Login | Flags | Purpose | Supabase (D3) |
|---|---|---|---|---|
| `records_api` | LOGIN | NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOREPLICATION | read-only serving | `authenticated` (read) |
| `records_intake_writer` | LOGIN | (same) | import/data-entry, column-scoped | `authenticated` (write)/service |

Passwords set **out-of-band by the operator** (Vault-first) on `records_dev`/prod; never in the migration. In the disposable validation DB the roles are password-less and exercised via `SET SESSION AUTHORIZATION`.

```sql
do $$
begin
  if not exists (select 1 from pg_roles where rolname='records_api') then create role records_api; end if;
  if not exists (select 1 from pg_roles where rolname='records_intake_writer') then create role records_intake_writer; end if;
end $$;
alter role records_api           with login nosuperuser nocreatedb nocreaterole nobypassrls noreplication;
alter role records_intake_writer with login nosuperuser nocreatedb nocreaterole nobypassrls noreplication;

-- HIGH-1 + Codex-C1: NOSUPERUSER/NOBYPASSRLS does NOT stop a preexisting MEMBER from SET ROLE
-- escalation. On the shared cluster, dynamically revoke EVERY membership in BOTH directions for
-- the two app roles (outbound: our role is a member of X; inbound: X is a member of our role).
do $$
declare m record;
begin
  for m in
    select granted.rolname as granted_role, member.rolname as member_role
    from pg_auth_members am
    join pg_roles granted on granted.oid = am.roleid
    join pg_roles member  on member.oid  = am.member
    where granted.rolname in ('records_api','records_intake_writer')
       or member.rolname  in ('records_api','records_intake_writer')
  loop
    execute format('revoke %I from %I', m.granted_role, m.member_role);
  end loop;
end $$;
```
Posture assert (FAILS the migration on drift): no privileged flags; both LOGIN; **zero `pg_auth_members` rows where either app role is `roleid` OR `member`** (no inbound, no outbound membership).

### 3.2 Table classes

- **Reference / catalog (9):** `asset_classes`, `form_templates`, `pm_programs`, `neta_procedures`, `neta_test_items`, `neta_tables`, `asset_class_neta_procedure`, `neta_procedure_xref`, `neta_table_source_links`. Both roles SELECT; writes owner/seed-only.
- **Write-path (6):** `assets`, `form_submissions`, `form_field_values`, `pm_schedules`, `pm_events`, `persons`. Writer column-scoped INSERT/UPDATE; reader SELECT.

### 3.3 Grant matrix (fully enumerated — closes the NOT-NULL INSERT-break risk)

`records_api` = **SELECT on every table + both views**, nothing else.

`records_intake_writer` = `USAGE` on schema `records` + SELECT on all tables, plus a column-scoped INSERT/UPDATE per write-path table governed by this **RULE**:

> **Writer column set = (all columns of the table) − (reserved columns below) − (auto-populated columns: the `gen_random_uuid()` PK, `created_at`, `updated_at`).**
> All reserved columns carry a DEFAULT (or are nullable), so an INSERT that omits them succeeds; every NOT-NULL/no-default column is non-reserved and therefore **in** the writer grant.

**Reserved (NOT writer — future reviewer/adjudicator/Gate-5), per table:**

| Table | Reserved columns | Why |
|---|---|---|
| `assets` | `status`, `condition` | asset lifecycle/assessment; both **NOT NULL with sentinel defaults** (`status`→`'unknown'`, `condition`→`'not_assessed'`) — they never become NULL, they default to the sentinel |
| `form_submissions` | `status`, `reviewed_by` | review lifecycle (see enum note) + review attribution |
| `persons` | `employee_ref`, `match_adjudicated_by`, `match_adjudicated_at`, `match_confidence` | human-adjudication only (contract C3); these **are** nullable and stay NULL until adjudication |
| `form_field_values` | — | none |
| `pm_schedules` | — | none |
| `pm_events` | — | none |

**Build-time invariant (F7).** These **11 NOT-NULL/no-default columns** MUST appear in the writer INSERT grant (an in-migration `has_column_privilege` assert enforces it, so a missing grant fails loud instead of breaking a real import): `assets.asset_tag`, `assets.name`; `form_submissions.template_id`, `form_submissions.asset_id`; `form_field_values.form_submission_id`, `form_field_values.field_key`; `pm_schedules.pm_program_id`, `pm_schedules.asset_id`; `pm_events.pm_schedule_id`, `pm_events.asset_id`; `persons.display_name`. (None are reserved → all covered by the RULE.)

**`form_submissions.status` enum note (F11).** The reserved `status` is `records.form_status_enum` = `draft, in_progress, complete, reviewed, approved, superseded, voided` (**7 states**, not "draft→reviewed→approved"). The writer is denied the **whole column**; on INSERT it defaults to `'draft'` (writer creates drafts only). Gate 5's reviewer role will govern the `reviewed`/`approved`/`superseded`/`voided` transitions; this boundary is what reserves them.

Notes: `updated_at` is trigger-maintained (INVOKER, mutates NEW only) — no writer grant needed (a BEFORE-trigger NEW write is not privilege-checked; verified). The plan enumerates the exact per-column lists table-by-table; the RULE + the 11-column invariant guarantee no INSERT can fail on a missing grant.

### 3.4 PUBLIC hygiene (tables **and routines**)
- `revoke create on schema public from public;` (database-scoped — affects only `records_dev`'s `public`, safe vs other lanes on the shared cluster).
- No `PUBLIC` `USAGE` on `records`; grant `USAGE` to the two roles.
- **`revoke execute on all routines in schema records from public;`** — `records.fn_set_updated_at()` has `proacl IS NULL` = implicit default PUBLIC EXECUTE, invisible to `aclexplode(proacl)` (false-green class).
- **Assert with the materialized default ACL** (a genuine strength — do NOT "simplify" this away): PUBLIC (grantee `0`) holds no EXECUTE on any `records` routine via `aclexplode(coalesce(p.proacl, acldefault('f', p.proowner)))` → zero rows; zero PUBLIC grants on any `records` table.
- Database-CONNECT hygiene is **Supabase-caveated** (Supabase manages it) — optional in bare-PG dev; not encoded.

---

## 4. RLS model

1. **`ENABLE ROW LEVEL SECURITY` on all 15 tables** (AC1). `FORCE` inert under D2-A (D7).
2. **Reference/catalog:** `FOR SELECT TO records_api, records_intake_writer USING (true)`; no write policy for app roles.
3. **Write-path (interim, role-scoped):** `FOR SELECT TO ... USING (true)`; `FOR INSERT TO records_intake_writer WITH CHECK (true)`; `FOR UPDATE TO records_intake_writer USING (true) WITH CHECK (true)` (column boundary enforced by the grant). **No policy names any other role → an unnamed role gets default-deny (0 rows)** even if mistakenly granted SELECT. When row predicates land, `USING (true)` → `USING (<predicate>)`, bindable to `auth.uid()` at the seam, without touching role wiring.
4. **Views (`security_invoker = true` on both):** `v_asset_test_history` (base tables **`assets`, `form_submissions`, `form_templates`**) and `v_pm_due` (base tables **`pm_schedules`, `assets`, `pm_programs`**). With `security_invoker`, the view applies the caller's RLS on all base tables. Grant SELECT on both views to `records_api`.

---

## 5. Migration `045_records_security_rls.sql`

Sectioned, guarded, self-asserting, reversible (mirrors ops-012):
1. **[1] Roles + flag + membership hardening** — guarded create; unconditional flags; **both-direction dynamic membership revoke** (§3.1); posture assert (flags; LOGIN; zero memberships either direction).
2. **[2] PUBLIC hygiene** — revoke CREATE on `public`; grant USAGE on `records`; **`revoke execute on all routines in schema records from public`**; `acldefault`-materialized assert.
3. **[3] Grant matrix** — `records_api` SELECT-all; `records_intake_writer` column-scoped per §3.3; positive `has_column_privilege` asserts for the 11 NOT-NULL columns; negative asserts for every reserved column + `records_api` no-write.
4. **[4] RLS** — enable on all 15; reference + write-path policies; assert `relrowsecurity` on all.
5. **[5] Views** — `security_invoker`; assert; grant SELECT to `records_api`.
6. **[6] Final consolidated posture assert** — re-verifies the whole boundary; RAISEs on drift (the only guard on `records_dev`/prod).

Idempotent (guarded create; `drop policy if exists` then create). **`045_..._down.sql`** (symmetric, guarded, ordered): drop policies → disable RLS → revert views → re-grant PUBLIC EXECUTE on routines → **database-scoped** grant revokes for the LOGIN roles (NOT `DROP OWNED` — ops-012 F-012-3: `DROP OWNED` strips shared-object CONNECT cluster-wide) → guarded `DROP ROLE` refusing any role with an out-of-band password (`pg_authid.rolpassword IS NOT NULL`, DEV-7) or cross-DB deps.

### 5.1 Post-045 lane-invariant flip
045 intentionally breaks the "records 001–044 = no RLS/grants" invariant. `test_043`/`test_044` assert RLS-disabled at *their* stack position (green under the Tier-3 incremental walk, which runs them pre-045); a **standalone** run against post-045 `records_dev` fails by design. Fix: comment-rescope in `test_043_*`/`test_044_*` + MANIFEST to "through mig 044; 045 enables RLS by design — use the incremental runner." (Verify the exact assertion lines on the host, not the stale local tree.)

### 5.2 Three verification layers
In-migration posture asserts (apply-time, the only prod guard) · `test_045` (Tier-3 static schema-shape introspection) · Tier 5 (dynamic SET-SESSION-AUTHORIZATION proofs, §6).

---

## 6. Harness — Tier 5 (roles / grants / denial)

Extends `run_validation.py`; runs on the disposable `records_val_*` DB after Tier 3 walks through 045, before the `finally` drop.

**Faithful identity.** Proofs use `SET SESSION AUTHORIZATION <role>` … `RESET SESSION AUTHORIZATION` (not `SET ROLE` from the superuser session — a superuser can `SET ROLE` to anything and cannot prove a membership-gated escalation is blocked).

**Savepoint discipline (Codex-C2 — mandatory).** After a permission error Postgres marks the transaction aborted until rolled back, so any expected-raise that runs inside an explicit transaction MUST be bracketed:
```
SAVEPOINT p; <expected-failing statement>;   -- on the caught error:
ROLLBACK TO SAVEPOINT p; RESET SESSION AUTHORIZATION;   -- then continue; outer ROLLBACK at the end
```
Without it, the `RESET`/cleanup after the caught error itself errors and turns a real denial into a harness failure.

**Seam edits:** `parse_tiers` valid set `{0,1,2,3,4,5}` (×3); `db_wanted = wanted & {3,4,5}`; `tier5_roles(child_dsn, executed)` next to `tier4_import_db`, gated on Tier 3; return `Tier("5-roles", PASS/FAIL, detail)`.

**Seed first (anti-false-green).** Before any "expect 0 rows" proof, seed ≥1 row in **each** target table (for a view, in **every** base table) so 0 rows proves RLS denial, not an empty table.

**Proofs (hard FAIL if unmet):**
- PP1 `set session authorization records_api;` SELECT a write-path table + both views → succeeds.
- PP2 `set session authorization records_intake_writer;` INSERT a submission (omit `status`) → succeeds, lands `status='draft'`.
- DP1 reader INSERT/UPDATE/DELETE on any write-path table → `insufficient_privilege`.
- DP2 writer `update form_submissions set status='approved'` → raises; `set reviewed_by=…` → raises.
- DP3 writer `update persons set employee_ref=…` / `set match_adjudicated_by=…` → raises.
- DP4 writer DDL (`drop`/`alter table`) → raises.
- **DP-ESC (C1):** (a) `set session authorization records_api; set role records_intake_writer;` → raises; mirror writer→reader. (b) **rogue-role proof:** create a run-scoped rogue role (member of nothing), `set session authorization rogue; set role records_api;` → raises, and `set role records_intake_writer;` → raises — no arbitrary role can assume the app roles.
- DP5 **accidental-grant** (rolled-back txn, savepoint-bracketed): create rogue; grant it USAGE + SELECT on `records.form_submissions`; `set session authorization rogue; select count(*) from records.form_submissions` → **0** (default-deny); attempted write (savepoint) → raises; rollback removes rogue.
- DP6 **no-PUBLIC:** `aclexplode(coalesce(proacl, acldefault('f', proowner)))` over routines + table ACLs, grantee `0` → zero rows.
- DP7 **RLS-enabled:** every `records.*` table `relrowsecurity = true`.
- DP8 **security_invoker:** both views set.
- DP9 **view-RLS proof (F9 — multi-base-table).** For `v_asset_test_history`, grant the rogue SELECT on the **view AND all three base tables** (`assets`, `form_submissions`, `form_templates`), seed a row in **each**, `set session authorization rogue; select count(*) from records.v_asset_test_history` → **0** (base-table RLS denies rogue on every base table incl. the reference table's `USING(true)`-but-role-scoped policy). Rolled-back. (Mirror for `v_pm_due` over `pm_schedules`/`assets`/`pm_programs`.) A 0-row result now proves invoker+RLS, not a missing grant.

**Teardown (`finally`, in order):** `reset session authorization` + close conn → `drop database … with (force)` → drop the two app roles **only if this run created them** (snapshot before the walk) **and** they hold no out-of-band password (`pg_authid.rolpassword IS NULL`), so a validation run can never drop a real serving role. Run-scoped allowlist guards any dropped name.

Gate-2 invariants preserved: `guard_target` records_dev refusal; admin-dbname=`postgres`; `records_val_*` allowlist; no hardcoded creds; `_child_env`; unmasked exit codes; `--require-db` turns SKIP into failure. **Concurrency:** validation runs serialized per cluster (fixed-name roles created idempotently, dropped only if this run created them) — documented.

---

## 7. Acceptance criteria

- **AC1** Every `records.*` table RLS-`ENABLE`d.
- **AC2** Zero PUBLIC/anon grants on any `records` table **or routine** (materialized-ACL assert, DP6); no PUBLIC `USAGE` on `records`.
- **AC3** Least-privilege matrix: `records_api` cannot write; `records_intake_writer` holds the §3.3 columns (incl. all 11 NOT-NULL) and none reserved; **no membership-escalation in either direction, and no arbitrary role can assume the app roles** (DP-ESC). In-migration asserts + DP1–DP4, DP-ESC.
- **AC4** Both views `security_invoker` (DP8); a rogue reading through each view is denied by **all** its base tables' RLS (DP9).
- **AC5** Non-superuser execution proven under `SET SESSION AUTHORIZATION` (PP1–PP2), never superuser-masked.
- **AC6** Tier 5 on a disposable `records_val_*` DB only; `records_dev` in no connection; roles dropped only if harness-created; Gate-2 invariants intact; Records CI green on the **full ladder with `--require-db`**.
- **AC7** `045` + `_down` reversible + reviewed; **not** applied to prod Supabase in this lane.
- **AC8 (F6 — serving-identity control).** The owner/superuser path is not RLS-guarded under D2-A, so it is closed by **custody, not by the migration**: the serving credential for `records_dev`/prod is provisioned **only** for the non-owner app roles (`records_api`/`records_intake_writer`); the owner/superuser DSN is **never** placed in the serving secret store — verified by the L6 secret-audit tripwire, not by 045. **Recorded serving-layer requirement** (implemented when the serving runtime is built, not in this gate): a startup assertion that `current_user` is one of the app roles and is `NOT rolsuper` / not the table owner. This makes the untested owner-path an *acknowledged, controlled* gap, not a silent assumption.

---

## 8. Proofs (summary)

Positive: PP1, PP2. Denial/escalation: DP1–DP4, **DP-ESC** (cross-pair + rogue-assumes-app-role), DP5 (accidental-grant), DP6 (no-PUBLIC incl. routines), DP7 (RLS-on-all), DP8 (invoker), DP9 (multi-base rogue-through-view). Mandatory red proofs (Gate-2 analog): **DP2** (column boundary), **DP5** (accidental-grant backstop), **DP-ESC** (escalation).

---

## 9. CI

**Codex-C3:** a fresh CI job cannot run `--only 5` — DB tiers require an explicit `--db-dsn` and Tier 5 is gated on Tier 3 building the disposable DB through 045. So Records CI runs the **full ladder with `--require-db`** (Tiers 0→5 in one invocation; Tier 3 builds the DB, Tier 5 proves the boundary) in the existing postgres-17 service job. `--only 5` is retained **only** as a pre-migrated `--db-dsn` debugging path. Push-only trigger + `persist-credentials: false` (already current on `main`). No new CI secret — roles are created by 045 and exercised via `SET SESSION AUTHORIZATION`.

---

## 10. Security & credential custody

App-role passwords operator-provisioned out-of-band, Vault-first; never in the migration; never echoed. No test/script/runner connects to `records_dev` (`guard_target`). **Four independent controls (defense-in-depth):** reserved-column grant boundary (DP2), RLS default-deny (DP5), no-membership-escalation both directions (DP-ESC), and serving-identity custody (AC8). A mistaken grant is caught by RLS; a mistaken policy by the grant; a mistaken membership by the escalation proof; a mistaken serving credential by the secret-audit.

---

## 11. Risks / open questions

1. **F6 owner-bypass residual (D2-A)** — the single path that breaks the model (connect as owner/superuser) is not RLS-guarded in-DB; closed by AC8 custody + the recorded serving-startup assertion. **If the operator wants an in-DB backstop instead, that is D2-B** (re-own tables to a non-super owner + `FORCE`) — a bounded delta, deferred unless ratified.
2. **No row isolation** — until tenancy + soft-FK activation, any granted app role sees all firm rows (correct for the single-firm model; stated so the spec does not imply row scoping).
3. **Fixed-name cluster roles vs disposable-per-run DBs** — snapshot-and-drop-only-if-created + password guard; assumes serialized validation runs per cluster.
4. **Supabase drift (D3)** — bare-PG proofs vs Supabase RLS (`auth.uid()`); mitigated by `USING(true)` interim policies swappable to `auth`-bound predicates. Full Supabase role/CONNECT mapping is a separate reconciliation (AC7 keeps it out of this lane).
5. **Tier-4 import tests run as superuser** — adding RLS must not break them (superuser bypasses); verify the records-import DB tests assume no specific owner / non-RLS table.
6. **`proacl IS NULL` false-green class** — closed by the `acldefault`-materialized assert; any future records function must re-run the routine REVOKE or [2] catches it.

---

## 12. Out of scope

Row-scoping backfill; soft-FK activation (Chip 8); audit-log + review/approval workflow + reviewer/`records_fn_owner` roles (Gate 5); SECURITY DEFINER function layer; Supabase prod apply; source-content policy (Gate 9); offline/PowerSync (Gate 6); Value Model V2; API/UI.
