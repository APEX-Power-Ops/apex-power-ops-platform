# Records Gate 3 — Security / RLS Design

**Date:** 2026-07-02  ·  **Rev 6** (D9 + D10 RATIFIED; DP9 rogue `USAGE ON SCHEMA records` grant [P2]; AC2 narrowed to PUBLIC for this gate [P3])
**Lane:** `records/gate3-security-rls` (worktree `/home/olares/code/apex/apex-records-gate3`)
**Dev DB:** `records_dev` (local PG17 cluster over mesh); disposable `records_val_*` for validation
**Prod target:** governed Supabase `fxoyniqnrlkxfligbxmg` — reviewable SQL first, NOT applied in this lane
**Migration:** `045_records_security_rls.sql` (+ `_down`)
**Authority / precedents:** ops role-boundary `infra/database/migrations/ops/012_ops_app_role_boundary.sql` (PR #55/#56); Gate-2 harness (`run_validation.py`, `_dbtest.py`); the identity contract; Supabase RLS / function-privilege / API-key docs.
**Status:** APPROVED for writing-plans (2-round IRP + operator ratification of D9/D10, 2026-07-02). No code built; no DB state touched.

> **Reviewer note (grounding).** Canonical = **host** `/home/olares/code/apex/apex-power-ops-platform` `main 90ccf864`. **Local Windows checkouts are divergent** (top out at mig 042) — do not audit against them. §0 posture verified against **live `records_dev` (PG 17.10)** + the host repo.

---

## 0. Context & grounding (verified 2026-07-02)

- `records`: **15 tables + 2 views**, all owned by `postgres` (superuser). **RLS 0%**. Grants owner-only. Schema ACL `NULL`. **PUBLIC holds default CONNECT on `records_dev`** (`datacl IS NULL`) and default EXECUTE on the one function.
- Views not `security_invoker`; each is a **3-table JOIN**: `v_asset_test_history` = `assets`⋈`form_submissions`⋈`form_templates`; `v_pm_due` = `pm_schedules`⋈`assets`⋈`pm_programs`.
- One function: `records.fn_set_updated_at()` (INVOKER, owner `postgres`, `proacl IS NULL` → default PUBLIC EXECUTE).
- No tenant/org/customer scoping column; person identity is a cross-DB contract-FK. Only soft nullable `project_ref`/`site_ref`/`client_ref` (no FK).

**Core problem.** Fail-closed only by grant-absence, not design; first grant to any serving role exposes every row. Gate 3 installs the least-privilege + RLS backstop, mirroring ops-012.

---

## 1. Goal & non-goals

**Goal.** (a) least-privilege app roles, fully-enumerated column-scoped grants, no membership-escalation in either direction; (b) RLS on every table (deny-by-default), `USING(true)` reads for reference, role-scoped write-path policies; (c) `security_invoker` views; (d) PUBLIC hygiene over tables + routines; self-asserted in-migration and independently proven under a faithful non-superuser identity, on a disposable DB, reversibly, not applied to prod.

**Non-goals.** Row-level tenant isolation; audit-log + review/approval workflow (Gate 5); SECURITY DEFINER function layer / reviewer role (Gate 5); **source-content serving policy (Gate 9)**; Value Model V2; offline/PowerSync (Gate 6); API/UI; prod Supabase apply; soft-FK activation (Chip 8).

---

## 2. Decisions

| # | Decision | Resolution |
|---|---|---|
| D1 | RLS depth | **A (amended).** RLS on all; `USING(true)` reference reads; write-path role-scoped policies; row predicates deferred. Role/operation backstop, not row isolation. |
| D2 | Object ownership | **A — keep `postgres` ownership. RATIFIED.** Owner/superuser-bypass residual closed by the serving invariant + AC8 (custody), not in-DB. |
| D3 | Supabase | **A.** Generic PG roles now; mapping to `anon`/`authenticated`/`service_role` deferred; **045 is NOT Supabase-apply-ready as written** (see §11.4). |
| D4 | Gate 3/5 boundary | **Confirmed.** Substrate + identity hook + non-superuser proof here; audit-log + review workflow = Gate 5. |
| D5 | Role set | `records_api` (reader) + `records_intake_writer` (writer, column-scoped). `records_fn_owner` + reviewer/approver = Gate 5. |
| D6 | Reference writes | Owner/seed only; both roles SELECT (except the D10 restriction). |
| D7 | FORCE RLS | Inert under D2-A; not relied on. |
| D8 | Harness + CI | Non-superuser Tier 5; CI full ladder `--require-db`. |
| **D9** | **Reserved-column governance (F1) — RATIFIED** | Reserve `pm_events.status`, `form_field_values.assessment`, `persons.worker_class` from the writer (twins of already-reserved cols). Safe: bulk/historical import runs on the maintenance/owner path (Gate-2 Tier 4), not the app writer; `records_intake_writer` is forward serving-write only. DP2 covers all three. |
| **D10** | **`neta_table_source_links` exposure (F2) — RATIFIED** | RESTRICT — neither app role gets SELECT in Gate 3; RLS-enabled, owner-only; serving exposure deferred to Gate 9. |

---

## 3. Role & grant contract

### 3.1 Roles + membership hardening (both directions)

Two LOGIN roles: `records_api` (reader), `records_intake_writer` (writer), each NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOREPLICATION. Passwords out-of-band (Vault); never in the migration; password-less + `SET SESSION AUTHORIZATION` in the disposable DB.

Guarded create → unconditional flag correction → **dynamic revoke of every membership in BOTH directions** (any `pg_auth_members` row where an app role is `roleid` OR `member`) → posture assert (flags; LOGIN; zero memberships either way). **Ordering (F7): the membership-revoke DO block MUST run AFTER the guarded create** (else first apply errors on a missing role).

### 3.2 Table classes

- **Reference / catalog — SELECT to both roles (8):** `asset_classes`, `form_templates`, `pm_programs`, `neta_procedures`, `neta_test_items`, `neta_tables`, `asset_class_neta_procedure`, `neta_procedure_xref`.
- **Restricted — owner-only in Gate 3 (D10, F2):** `neta_table_source_links` — carries `source_owner`/`source_path`/`source_file`/`source_repo_*`/`review_notes`/`restricted_review_required` (default `true`); it is **source-provenance metadata, not catalog reference data**, and §12 defers source-content policy to Gate 9. RLS-enabled with no app-role SELECT policy; serving exposure decided at Gate 9.
- **Write-path (6):** `assets`, `form_submissions`, `form_field_values`, `pm_schedules`, `pm_events`, `persons`. Writer column-scoped INSERT/UPDATE; reader SELECT.

### 3.3 Grant matrix (fully enumerated)

`records_api` = **SELECT on the 8 reference tables + the 6 write-path tables + both views**, nothing else. **Not** `neta_table_source_links` (D10).

`records_intake_writer` = `USAGE` on `records` + SELECT on all tables (except `neta_table_source_links`, D10), plus column-scoped INSERT/UPDATE per write-path table by this **RULE**:

> **Writer column set = (all columns) − (reserved below) − (auto-populated: `gen_random_uuid()` PK, `created_at`, `updated_at`).**

**Reserved (NOT writer):**

| Table | Reserved | Status |
|---|---|---|
| `assets` | `status`, `condition` | ratified (D8) — NOT NULL sentinel defaults (`'unknown'`/`'not_assessed'`), never NULL |
| `form_submissions` | `status`, `reviewed_by` | ratified |
| `persons` | `employee_ref`, `match_adjudicated_by`, `match_adjudicated_at`, `match_confidence` | ratified (nullable; stay NULL until adjudication) |
| `pm_events` | **`status`** | ratified (D9) — twin of `form_submissions.status` |
| `form_field_values` | **`assessment`** | ratified (D9) — twin of `assets.condition` |
| `persons` | **`worker_class`** | ratified (D9) — HR classification; has a default, so explicitly reserved (outside the F7 NOT-NULL list) |

**Writer-dual-purpose resolution (why reserving is safe).** `records_intake_writer` is the **forward serving-write role** (creates drafts / new field data). **Bulk & historical import** (legacy PowerDB, Miner) that must preserve original `status`/lifecycle runs on the **maintenance/owner path** — as it does today in Gate-2 Tier 4 (superuser) — **not** the app writer. So reserving lifecycle/status columns from the writer preserves the review boundary without breaking historical-fidelity import. (D9 ratifies this framing.)

**Build-time invariant (F7).** The 11 NOT-NULL/no-default columns MUST be in the writer INSERT grant (`has_column_privilege` assert): `assets.asset_tag`/`name`; `form_submissions.template_id`/`asset_id`; `form_field_values.form_submission_id`/`field_key`; `pm_schedules.pm_program_id`/`asset_id`; `pm_events.pm_schedule_id`/`asset_id`; `persons.display_name`. (`worker_class` has a default → not in this list; its reservation is D9.)

**`form_submissions.status` enum** = `draft, in_progress, complete, reviewed, approved, superseded, voided` (7 states); writer denied the whole column → INSERT defaults to `'draft'`. Gate-5 reviewer governs the later transitions.

`updated_at` is trigger-maintained (no writer grant needed). The plan enumerates exact per-column lists; the RULE + 11-column invariant guarantee no INSERT fails on a missing grant.

### 3.4 PUBLIC hygiene (tables + routines)
- `revoke create on schema public from public;` — database-scoped (only `records_dev`'s `public`), safe on the shared cluster. **NO-OP vs the real starting state** (PG15+ default already lacks PUBLIC CREATE; `nspacl` shows PUBLIC holds only USAGE) — harmless; leaves no residue, so `_down` need not restore it (F7).
- Grant `USAGE on schema records` to both roles; no PUBLIC USAGE on `records`.
- **`revoke execute on all routines in schema records from public;`** — closes the `proacl IS NULL` implicit-PUBLIC-EXECUTE false-green.
- **Assert with the materialized default ACL** (a strength — do not "simplify" away): `aclexplode(coalesce(p.proacl, acldefault('f', p.proowner)))`, grantee `0` → zero EXECUTE; zero PUBLIC grants on any `records` table.
- **PUBLIC CONNECT is left in place** (records `datacl IS NULL`). This is **weaker CONNECT hygiene than ops-012** (which revokes PUBLIC CONNECT); records leans on the RLS default-deny as the sole gate for a PUBLIC-connected rogue. Accepted for Gate 3 (consistent with the Supabase model where CONNECT is managed out-of-DB); revisit if a non-Supabase shared-cluster serving path appears (§11.7).

---

## 4. RLS model

1. **`ENABLE ROW LEVEL SECURITY` on all 15 tables** (AC1). `FORCE` inert (D7).
2. **Reference/catalog (8):** `FOR SELECT TO records_api, records_intake_writer USING (true)`. **`neta_table_source_links`:** RLS enabled, **no app-role SELECT policy** (D10). No write policy for app roles anywhere in reference.
3. **Write-path (6, interim role-scoped):** `FOR SELECT TO records_api, records_intake_writer USING(true)`; `FOR INSERT TO records_intake_writer WITH CHECK(true)`; `FOR UPDATE TO records_intake_writer USING(true) WITH CHECK(true)` (column boundary via the grant). **Every policy names explicit roles via `TO` — never `TO PUBLIC`.** An unnamed role → default-deny (0 rows). Row predicates later swap `USING(true)` for `USING(<predicate>)`.
4. **Views (`security_invoker=true` on both):** applies the caller's RLS across all base tables. Grant SELECT on both views to `records_api`. **Invariant (F6):** a rogue absent from ANY base-table policy sees 0 rows (JOIN collapses) — sound only because the reference policy is role-scoped, so an in-migration assert enforces **every records policy has a non-PUBLIC `polroles`**.

---

## 5. Migration `045_records_security_rls.sql`

Sectioned/guarded/self-asserting/reversible (mirrors ops-012): [1] roles + flags + both-direction membership hardening (create BEFORE revoke) → [2] PUBLIC hygiene (revoke CREATE on public; USAGE on records; **revoke EXECUTE on all routines** from public; `acldefault` assert) → [3] grant matrix (column-scoped; positive 11-NOT-NULL + negative reserved-column asserts) → [4] RLS enable-all + policies (**assert every policy `polroles` is non-PUBLIC**, F6) → [5] `security_invoker` on both views → [6] consolidated posture assert (RAISEs on drift — the only guard on `records_dev`/prod).

Idempotent (guarded create; `drop policy if exists`).

**`045_..._down.sql` — build checklist (F3, mandatory at build-review):**
- **(a)** ZERO `DROP OWNED` statements — records has no NOLOGIN owner this gate; both app roles are LOGIN, and `DROP OWNED` on a LOGIN role strips shared `pg_database` CONNECT **cluster-wide** (ops-012 F-012-3). A `records_val_*` teardown running `_down` after 045 is applied on `records_dev` would otherwise strip live `records_api`/`records_intake_writer` CONNECT.
- **(b)** Database-scoped `revoke … on all tables/routines in schema records` + `revoke usage on schema records` for BOTH LOGIN roles, run **unconditionally** (posture restored even when the DEV-7 password guard retains the role object).
- **(c)** `all routines` (not `all functions`) in the PUBLIC-EXECUTE re-grant (future-procedure drift; ops-012 L3).
- **(d)** Guarded `DROP ROLE` refusing any role with an out-of-band password (`pg_authid.rolpassword IS NOT NULL`, DEV-7) or cross-DB deps.
- Consequence: `_down` is object-symmetric only on the password-less disposable DB; on `records_dev`/prod it revokes grants but retains the (password-carrying) role objects — intended.

### 5.1 Post-045 lane-invariant flip
045 breaks the "records 001–044 = no RLS/grants" invariant. Comment-rescope `test_043_*`/`test_044_*` + MANIFEST to "through mig 044; 045 enables RLS by design — use the incremental runner." **Verify the exact assertion lines on the host** (not the stale local tree).

### 5.2 Three verification layers
In-migration posture asserts (apply-time, the only prod guard) · `test_045` (Tier-3 static introspection) · Tier 5 (dynamic proofs, §6).

### 5.3 Built-file re-audit gate (F3/F5 — mandatory before merge)
Every down-reversibility/portability judgment here is made against spec prose + the ops-012 precedent; **the actual SQL does not exist yet.** The SDD whole-branch review MUST re-audit the built `045_up`/`_down`/Tier-5 against: the F3(a–d) checklist; the F6 `polroles`-non-PUBLIC preservation; and it MUST read `infra/secret-audit.sh` to confirm the AC8 tripwire actually detects `service_role`/secret-key/`BYPASSRLS` DSNs. This is the verification, not a formality.

---

## 6. Harness — Tier 5

Runs on the disposable DB after Tier 3 walks through 045, before the `finally` drop. Proofs use `SET SESSION AUTHORIZATION <role>` … `RESET SESSION AUTHORIZATION` (faithful; not superuser-masked). **Savepoint discipline (C2):** any expected-raise inside an explicit transaction is bracketed `SAVEPOINT p; …; ROLLBACK TO SAVEPOINT p; RESET SESSION AUTHORIZATION;` then outer `ROLLBACK`.

Seam edits: `parse_tiers` valid `{0..5}` (×3); `db_wanted = wanted & {3,4,5}`; `tier5_roles()` gated on Tier 3; return `Tier("5-roles", …)`.

**Proofs (hard FAIL if unmet):** PP1 reader SELECT ok; PP2 writer INSERT draft ok (`status='draft'`). DP1 reader no-write → raises. DP2 writer `form_submissions.status`/`reviewed_by`, **`pm_events.status`, `form_field_values.assessment`, `persons.worker_class`** (D9) → each raises. DP3 writer persons adjudication cols → raises. DP4 writer DDL → raises. DP-ESC (a) reader `set role writer` → raises + mirror; (b) rogue `set session authorization rogue; set role records_api/records_intake_writer` → raises. DP5 accidental-grant (rolled-back, savepoint): rogue SELECT on `form_submissions` → count 0; write → raises. DP6 no-PUBLIC via `acldefault`-materialized ACL → 0. DP7 RLS-enabled on all. DP8 both views `security_invoker`. **DP9 (F9+Codex-D1+F6, hardened):** for each view — (1) seed a **JOIN-satisfying** row set (matching `asset`+`submission`+`template`, resp. `schedule`+`asset`+`program`); (2) **positive control:** `set session authorization records_api; select count(*) from <view>` → **>0** (proves the join is non-empty); (3) grant the rogue **`USAGE ON SCHEMA records`** + SELECT on the view + all three base tables (mirror DP5 — there is no PUBLIC USAGE on `records`, so without the schema grant the query fails at schema access, not RLS, a false result); `set session authorization rogue; select count(*)` → **0** (base-table RLS denies); (4) **assert every records policy has a non-PUBLIC `polroles`** so a future `TO PUBLIC` "simplification" can't silently leak. Rolled-back.

**Teardown (`finally`, in order):** reset auth + close → `drop database … with (force)` → drop the two app roles **only if this run created them** (snapshot before the walk) **and** they hold no out-of-band password. Never drops a real serving role.

Gate-2 invariants preserved (`guard_target`, admin-dbname=`postgres`, `records_val_*` allowlist, no hardcoded creds, `_child_env`, unmasked exit codes). Concurrency: validation runs serialized per cluster.

---

## 7. Acceptance criteria

- **AC1** every table RLS-`ENABLE`d.
- **AC2** zero **PUBLIC** (grantee `0`) grants on any `records` table or routine (materialized-ACL assert); no PUBLIC USAGE on `records`. (No-direct-grant assertions for Supabase `anon`/`authenticated`/`service_role` — which do not exist on the dev cluster, and whose API reachability is grant-driven while `service_role`/secret keys bypass RLS — belong to the Supabase role-rebinding stage, §11.4, not this gate.)
- **AC3** matrix: `records_api` cannot write; `records_intake_writer` holds the §3.3 columns (incl. 11 NOT-NULL) and none reserved; no membership-escalation either direction; no arbitrary role can assume the app roles (DP-ESC).
- **AC4** both views `security_invoker`; a rogue is denied through each view by base-table RLS (DP9 with positive control); every records policy is role-scoped (`polroles` non-PUBLIC).
- **AC5** non-superuser execution proven under `SET SESSION AUTHORIZATION` (PP1–PP2).
- **AC6** Tier 5 on a disposable `records_val_*` DB only; `records_dev` in no connection; roles dropped only if harness-created; Gate-2 invariants intact; Records CI green on the full ladder `--require-db`.
- **AC7** `045` + `_down` reversible + reviewed (per the §5.3 re-audit gate); **not** applied to prod Supabase in this lane.
- **AC8 (serving-identity control).** Under D2-A the owner/superuser/BYPASSRLS path is closed by **custody, not the migration**: the records serving secret store contains **no owner/superuser DSN and no Supabase `service_role` / secret (service) key / any `BYPASSRLS` credential** (these bypass RLS by design → would defeat the backstop). **Concrete control:** `infra/secret-audit.sh` MUST detect any such credential in records serving config (the §5.3 gate verifies it does). Recorded serving-layer requirement: a startup assertion that `current_user` is an app role and is `NOT rolsuper AND NOT rolbypassrls` / not the table owner.

---

## 8. Proofs (summary)

PP1–PP2; DP1–DP4, DP-ESC, DP5, DP6, DP7, DP8, DP9. Mandatory red proofs: **DP2** (column boundary), **DP5** (accidental-grant), **DP-ESC** (escalation), **DP9** (view-through-RLS with positive control).

---

## 9. CI

Records CI runs the **full ladder with `--require-db`** (Tiers 0→5; Tier 3 builds the disposable DB, Tier 5 proves the boundary) in the postgres-17 service job. `--only 5` retained only as a pre-migrated `--db-dsn` debug path. Push-only + `persist-credentials: false` (current on `main`). No new CI secret.

---

## 10. Security & credential custody

Passwords out-of-band, Vault-first; never in the migration/logs. No test/runner connects to `records_dev`. **Five independent controls:** reserved-column grant boundary (DP2), RLS default-deny (DP5), no-membership-escalation both directions (DP-ESC), serving-identity custody (AC8/secret-audit), and role-scoped-policy invariant (DP9 `polroles`).

---

## 11. Risks / open questions

1. **F6 owner/BYPASSRLS residual (D2-A)** — closed by AC8 custody + the concrete `secret-audit.sh` control + the recorded serving-startup assertion; in-DB backstop (D2-B) deferred unless ratified.
2. **No row isolation** — any granted app role sees all firm rows (single-firm model).
3. **Fixed-name cluster roles vs disposable-per-run DBs** — snapshot-and-drop-only-if-created + password guard; serialized runs assumed.
4. **Supabase: 045 is NOT apply-ready as written.** Its policies bind `TO records_api`/`records_intake_writer` (LOGIN roles), but Supabase traffic runs as `authenticated`/`anon`/`service_role` (NOLOGIN group roles PostgREST SET-ROLEs into). A prod apply requires a **role-rebinding** (app roles → `authenticated`, or GRANT INTO), **not just a `USING(true)`→predicate swap** — a heavier delta, kept out of lane by AC7 and reconciled at the serving-layer/Gate-9 stage.
5. **Tier-4 import tests run as superuser** — adding RLS must not break them (superuser bypasses); verify no test assumes a specific owner / non-RLS table.
6. **`proacl IS NULL` false-green class** — closed by the `acldefault` assert.
7. **Weaker PUBLIC-CONNECT hygiene than ops-012** — accepted (§3.4), leaning on RLS default-deny; revisit for any non-Supabase shared-cluster serving path.

---

## 12. Out of scope

Row-scoping backfill; soft-FK activation (Chip 8); audit-log + review/approval workflow + reviewer/`records_fn_owner` roles (Gate 5); SECURITY DEFINER layer; Supabase prod apply; source-content policy (Gate 9); offline/PowerSync (Gate 6); Value Model V2; API/UI.

---

## 13. Governance decisions — RATIFIED 2026-07-02

**D9 — Reserved-column governance (F1).** Reserve `pm_events.status`, `form_field_values.assessment`, and `persons.worker_class` from `records_intake_writer`?
- *Diagnosis:* these are lifecycle/assessment/classification fields structurally identical to columns already reserved (`form_submissions.status`, `assets.condition`, the persons adjudication cols). Leaving them writer-writable lets the intake writer set PM-completion, per-field pass/fail, and W2/1099 classification with no reviewer boundary — the boundary this gate exists to build. `worker_class` has a default, so it slips past the F7 NOT-NULL enumeration into the writer grant unless explicitly reserved.
- *Framing:* reserving them is **safe** because bulk/historical import (which must preserve original status) runs on the **maintenance/owner path** (as Gate-2 Tier 4), not the app writer; `records_intake_writer` is the forward serving-write role.
- *Resolution (ratified):* **RESERVE all three**; DP2 covers them; the "historical import = owner path, app writer = forward draft-only" framing is confirmed.

**D10 — `neta_table_source_links` serving exposure (F2).** Restrict it from the app roles in Gate 3?
- *Diagnosis:* it is source-provenance metadata (`source_path`, `review_notes`, `restricted_review_required` default `true`), not catalog reference data; granting `records_api` (→ Supabase `authenticated`) SELECT now pre-empts the §12-deferred Gate-9 source-content policy.
- *Resolution (ratified):* **RESTRICT** — RLS-enabled, no app-role SELECT policy in Gate 3; serving exposure decided at Gate 9. Intake populates it via the owner/seed path.
