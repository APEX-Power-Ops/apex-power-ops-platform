# Records Gate 5 - Serving Security (Ownership Posture + Audit Substrate + Serving Contract)

**Status:** DRAFT for operator review (rev 1, 2026-07-03).
**Lane:** `records/gate5-serving-security` off `main @ 03f6c339` (post Gate-3 PR #62).
**Predecessor:** Gate 3 security/RLS (migration `045`; roles `records_api` reader + `records_intake_writer` writer; RLS on all 15 tables; `security_invoker` views; `neta_table_source_links` owner-only). Gate 3 self-admitted its safety rests on an unenforced invariant: *serving connects only as the non-owner app roles, never as owner/postgres*.

**Goal (one sentence):** Convert the Gate-3 backstop from *safe by custody* toward *safe by enforcement* - move records objects off the superuser owner so RLS actually binds the owner, add a metadata-minimal DB-trigger audit trail that makes even owner/direct-SQL mutations visible, and hand Gate 9 a machine-readable serving contract - without building the serving runtime.

**Architecture (2-3 sentences):** Two sequenced authoritative-migration slabs plus a documentation artifact. **5A (ownership posture, mig 046):** reassign every `records.*` object from the superuser `postgres` to a NOLOGIN/NOSUPERUSER/NOBYPASSRLS `records_owner`, then `FORCE ROW LEVEL SECURITY` on all 15 tables so RLS binds the owner too. **5B (audit substrate, migs 047-049):** a `records_fn_owner`-owned `SECURITY DEFINER` capture function feeding an append-only, metadata-minimal `records.audit_log` via AFTER-row triggers on the 6 writable tables, readable only by a new read-only `records_auditor`. Plus a checked-in **serving contract** (role -> Supabase boundary + DSN-form inventory) that makes Gate 9 a mechanical rebind. The Check-3 detector stays **dormant** (no serving config exists to arm it against); the runtime startup-identity assertion and comprehensive DSN parser are deferred to the serving-runtime brainstorm / Gate 9, where real config files will exist to test against.

**Tech Stack:** PostgreSQL 17 (dev), Python + psycopg test harness (`run_validation.py` disposable-DB walk), bash `secret-audit.sh` tripwire. Same toolchain and discipline as Gate 3.

---

## Global Constraints

Every task inherits these (values verbatim from the lane's established discipline):

- **Authoritative migrations, not deltas.** Any grant/role/ownership change REVOKEs/normalizes first, then applies, with **in-migration posture asserts** (`raise exception` on any violated invariant). Mirror the 045 revoke-first + exactness-assert pattern.
- **Reversible `_down` for every migration**, mirroring its up in reverse dependency order; symmetry proven on a disposable DB.
- **ASCII-only added lines** (no U+2014 em-dashes etc.).
- **Tests run against a DISPOSABLE dev DB only** (`records_val_*` / `records_spike_*` generated names); **NEVER `records_dev`** (the harness `guard_target` refuses it) and **NEVER prod Supabase** (Gate-3 AC7 stands - nothing in this gate is applied to prod).
- **App-role passwords are operator-provisioned out-of-band, Vault-first.** No migration sets a password. New roles created here (`records_owner`, `records_fn_owner`) are **NOLOGIN** by construction (they are never connection identities); `records_auditor` is LOGIN and its password is provisioned out-of-band.
- **Value-silent detectors.** Any secret/DSN tripwire prints `file:line + rule name` only, never a value.
- **`TO <named-role>` policy idiom** on every new policy, so Gate 9's rebind to Supabase boundaries stays a mechanical find/replace.
- **Audit is metadata-minimal by default** (operator ruling, 2026-07-03): audit rows carry table, pk, operation, actor/session identity, txid, timestamp, changed-column NAMES, and a row HASH - **NOT full before/after row values**. Full row images require explicit operator ratification (audit logs are themselves a leakage surface).
- **Honest scope claim.** This gate closes the NON-superuser-owner RLS-bypass. It does NOT close `postgres`-superuser or Supabase `service_role` bypass - those remain custody + detector + a startup-identity assertion deferred to the first real serving process. The gate's writeup must say "much safer + detectable," never "safe by enforcement" unqualified.

---

## Feasibility grounding (pre-build spike, 2026-07-03)

A throwaway spike built the full 001-045 schema on a disposable DB and proved the 5A mechanism empirically (Appendix A). Verified: all 15 tables + 2 views + 1 function + the `records` schema are owned by `postgres` (`superuser=true, bypassrls=true`); zero sequences (uuid PKs). Explicit per-object `ALTER OWNER` to a non-superuser `records_owner` reassigns all 18 objects + schema + function with **0 stragglers** and reverses with **0 stragglers**. On a FORCEd `neta_tables` (88 rows): superuser sees 88, `records_owner` sees **0**, `records_api` sees 88 (its policy); the unFORCEd contrast table lets the owner see all rows; an owner-path INSERT is **blocked by RLS**. Verdict: **GO** - feasible, clean, reversible.

Two consequences the spike surfaced (folded into the decisions below): (1) ownership hygiene is an **ongoing invariant** - future migrations run as `postgres` and would create superuser-owned objects again, so a drift tripwire is required, not just a one-time move; (2) the `records_owner` must **never be a DML identity** (FORCE RLS blocks its writes), lightly tensioning Gate-3 D9's "maintenance/owner path" for bulk import.

---

## Decisions

| # | Decision | Ruling |
|---|----------|--------|
| G5-D1 | Owner-path treatment | **Move all `records.*` objects to a non-superuser/non-BYPASSRLS `records_owner` + FORCE RLS** (mig 046). Operator-ratified in-DB hardening path. Residual `postgres`-superuser / `service_role` bypass stays custody + detector + startup-assertion (deferred). |
| G5-D2 | `records_owner` shape | **NOLOGIN, NOSUPERUSER, NOBYPASSRLS.** It is purely the object owner, never a connection or DML identity - so by construction it can never be a serving identity, and FORCE RLS makes any hypothetical owner-path DML deny-by-default. |
| G5-D3 | FORCE RLS scope | **All 15 records tables.** Reference tables keep their `USING(true)` read policies `TO` the app roles (app reads unaffected); the owner now sees 0 without a policy (correct - owner is not a serving identity). `neta_table_source_links` stays deny-by-default (no policy) so FORCE makes even the owner denied. Migrations run as `postgres` (superuser bypasses FORCE - verified), so migration DDL/DML is unaffected. |
| G5-D4 | Ongoing ownership hygiene | **A harness posture assert (Tier 6) that FAILS if any `records.*` table/view/matview/sequence/function is owned by a role with `rolsuper` OR `rolbypassrls`.** Catches future-migration drift. Plus a migration-authoring discipline note (new records objects `ALTER OWNER TO records_owner`). |
| G5-D5 | Audit mechanism | **DB triggers.** AFTER INSERT/UPDATE/DELETE FOR EACH ROW on the 6 writable operational tables, calling ONE shared `records.fn_audit_capture()`. All four design lenses converged here: there is no app layer, the write path is a DB-role identity over a direct DSN, so triggers are the only chokepoint a future/forgotten connector cannot bypass. Reuses the `records.fn_set_updated_at` (mig 004) shared-function precedent. |
| G5-D6 | Audit content | **Metadata-minimal (operator ruling).** Columns: `audit_id` (bigint identity PK), `event_at` (`clock_timestamp()`), `action` (insert/update/delete CHECK), `table_name`, `row_pk` (text), `db_role` (`current_user`), `session_role` (`session_user`), `is_superuser` (bool snapshot), `txid` (`txid_current()`), `application_name`, `client_addr` (`inet_client_addr()`), `changed_columns` (text[] of NAMES, UPDATE only), `row_hash` (md5 of the row image), `app_actor` (nullable, from `SET LOCAL records.app_actor`). **NO `before_row`/`after_row` value images.** Rationale: forensic value (who changed which columns of which row, when, to what hash) with zero value leakage; the audit table is itself a lower-privilege surface. |
| G5-D7 | source_links audit | **EXCLUDE `neta_table_source_links` from audit triggers in Gate 5**, and assert the exclusion (its trigger set is empty). Rationale: it is owner-only (no app-role writes), so its only mutations are the custody-controlled owner/superuser path; excluding it guarantees no lineage metadata (not even a hash) enters a lower-privilege table. Revisit with a column-allowlist when a reviewer workflow actually mutates its lifecycle (later gate). |
| G5-D8 | `records_auditor` role | **LOGIN, read-only** (the D5 reviewer's read half): SELECT on `records.audit_log` + SELECT on the operational tables for correlation; NO write anywhere. Proven via session-authorization tests so it is not unexercised. The approver/write capability + review decision table + workflow are **deferred** with the review workflow (later gate). |
| G5-D9 | audit_log RLS/grants | RLS enabled; **SELECT policy `TO records_auditor` only; INSERT policy `TO records_fn_owner`** (so the definer function can write); **NO grant or policy to `records_api`/`records_intake_writer`** (serving roles can neither read nor rewrite their own audit trail); append-only (no UPDATE/DELETE policy for anyone). `audit_log` owned by `records_fn_owner`. |
| G5-D10 | Definer-function safety | `records.fn_audit_capture()` is **SECURITY DEFINER, owned by `records_fn_owner` (NOLOGIN/NOSUPERUSER/NOBYPASSRLS), `SET search_path = pg_catalog, records` pinned**. In-migration: `ALTER FUNCTION ... OWNER TO records_fn_owner` explicitly + assert `pg_proc.proowner = records_fn_owner` + assert the owner's `rolbypassrls=false` + assert `proconfig` pins search_path. A test inserts-as-writer and asserts the audit row LANDS (proves the INSERT-policy coupling) AND asserts the function is NOT `postgres`-owned (the exact false-green class the operator caught in Gate 3: a postgres-owned definer works via BYPASSRLS and masks a missing policy). |
| G5-D11 | Serving contract | A checked-in **machine-readable** artifact (`reference/records/SERVING_CONTRACT.yaml` + a companion `.md`) enumerating each records role -> intended Supabase boundary + the 045/046 policy names bound to it + write scope, PLUS a DSN-form inventory the eventual serving config is expected to use. Gate 9 consumes it mechanically. **Check-3 stays dormant** (`RECORDS_SERVING_GLOBS` unset) - an honest SKIP, not an armed-but-empty PASS. |
| G5-D12 | Tier-6 posture assert | Value-silent in-DB posture check (harness Tier 6): `records_owner`, `records_fn_owner`, `records_auditor` are all `rolsuper=false AND rolbypassrls=false`; and (ties to G5-D4) no `records.*` object is owned by a super/bypassrls role. This is the in-DB half of the identity invariant that ships regardless of a serving consumer. |

---

## Migration + harness shape

Authoritative migrations `046-049`, each with a reversible `_down`, following the 045 idiom. All applied only to disposable dev DBs in this gate.

- **`046_records_ownership.sql`** - create `records_owner` (NOLOGIN NOSUPERUSER NOBYPASSRLS, guarded `if not exists`); deterministic explicit `ALTER OWNER` of every `records.*` table/view/matview/sequence/function + the schema to `records_owner` (a `do`-block enumerating `pg_class`/`pg_proc`, NOT `REASSIGN OWNED BY postgres` which would move the whole cluster); `ALTER TABLE ... FORCE ROW LEVEL SECURITY` on all 15 tables; in-migration asserts: (a) 0 records objects not owned by `records_owner`; (b) `records_owner` is non-super/non-bypassrls; (c) all 15 tables `relforcerowsecurity=true`. `046_down`: `NO FORCE` on the 15; reassign every object back to the prior owner; guarded `DROP ROLE records_owner` (after reassign; DROP-hook: the down is a `.sql` applied via `psql -f`).
- **`047_records_audit_roles.sql`** - `records_fn_owner` (NOLOGIN NOSUPERUSER NOBYPASSRLS) + `records_auditor` (LOGIN, password out-of-band). Authoritative revoke-first grants + exactness asserts (auditor has NO write on any operational table; auditor has SELECT on the operational tables + will get SELECT on audit_log in 048). Both-direction membership hardening as in 045. `047_down` guarded role drops.
- **`048_records_audit_log.sql`** - `records.audit_log` (owned by `records_fn_owner`); BRIN index on `event_at`, btree on `(table_name, row_pk)`; partition-key + retention posture in a table COMMENT (no partition machinery - deferred); RLS enabled; SELECT policy `TO records_auditor`, INSERT policy `TO records_fn_owner`; NO app-role grant/policy; `records.fn_audit_capture()` SECURITY DEFINER owned by `records_fn_owner` with pinned search_path; asserts per G5-D10. `048_down` drops function + table + policies.
- **`049_records_audit_triggers.sql`** - AFTER INSERT/UPDATE/DELETE FOR EACH ROW trigger on each of the 6 writable tables -> `fn_audit_capture()`; assert the records trigger set for this function is EXACTLY those 6 (not `audit_log` itself - recursion guard; not `source_links` - G5-D7). `049_down` drops the 6 triggers.
- **Harness (`run_validation.py`)** - extend to a **Tier 6** (ownership + audit posture) proving: all records objects owned by non-super/non-bypassrls `records_owner`; FORCE RLS teeth (owner sees 0 without a policy on a seeded table; app role sees rows; owner-path write blocked); audit INSERT-as-writer lands exactly one metadata-minimal row (asserts NO value-image columns exist); auditor can SELECT audit_log; `records_api`/`records_intake_writer` CANNOT read audit_log; `source_links` has no audit trigger; the definer function is `records_fn_owner`-owned and search_path-pinned; the Tier-6 posture asserts (G5-D12). Plus `parse_tiers` extended to `{0..6}` with the full-set guard. Unit tests for `parse_tiers`.
- **Serving contract** - `reference/records/SERVING_CONTRACT.{yaml,md}` per G5-D11. No code consumes it in this gate.
- **CI** - `records-ci.yml` `--require-db` already runs the full ladder; extend the tier set to include Tier 6 (a one-line flag change or none if `--require-db` runs all tiers). The AC8 fixture step stays.

---

## Acceptance Criteria

- **AC1 (ownership).** After 046, every `records.*` table/view/matview/sequence/function + the schema is owned by `records_owner`; `046_down` restores the prior owner. Reversible, 0 stragglers each direction (test).
- **AC2 (FORCE teeth).** All 15 tables `FORCE ROW LEVEL SECURITY`; a non-superuser owner sees 0 rows on a seeded table with no owner policy; app roles see their policy rows; an owner-path INSERT is RLS-blocked (test).
- **AC3 (ownership hygiene).** A harness posture assert FAILS if any `records.*` object is owned by a `rolsuper` OR `rolbypassrls` role (test plants a superuser-owned object -> assert fails; clean tree -> passes).
- **AC4 (audit capture).** `records.audit_log` is append-only; AFTER-row triggers exist on exactly the 6 writable tables (not audit_log, not source_links); each writer INSERT/UPDATE/DELETE yields exactly one audit row with correct action/db_role/txid (test).
- **AC5 (metadata-minimal).** Audit rows carry only metadata + `changed_columns` NAMES + `row_hash`; the table has NO `before_row`/`after_row` value-image column, and no audit row contains a source data value (test asserts the column set and inspects a captured row).
- **AC6 (definer safety / false-green guard).** `fn_audit_capture` is SECURITY DEFINER owned by `records_fn_owner` (non-bypassrls), search_path pinned; INSERT-as-writer LANDS an audit row (policy coupling proven); the function is NOT `postgres`-owned (test asserts `proowner` + `rolbypassrls=false` + `proconfig`).
- **AC7 (audit isolation).** `records.audit_log` is readable by `records_auditor` and NOT readable or writable by `records_api`/`records_intake_writer` (test via session authorization).
- **AC8 (Tier-6 posture).** Value-silent: `records_owner`/`records_fn_owner`/`records_auditor` are non-super + non-bypassrls (test).
- **AC9 (serving contract).** `SERVING_CONTRACT.{yaml,md}` present + machine-readable (role -> boundary -> policy names + DSN-form inventory); Check-3 remains dormant (honest SKIP), NOT armed (test/inspection).
- **AC10 (discipline).** Every migration has a reversible `_down` (symmetry proven); ASCII-only added lines; all tests on disposable DBs; nothing applied to prod Supabase.

---

## Non-goals (explicitly deferred)

- **Serving runtime** (tablet entry UI, scripted pass/fail calc, PDF report-gen) - separate flagship product arc.
- **Thin real serving consumer** + a live `assert_serving_identity()` **startup guard** + **arming Check-3** + **broadening the DSN parser** - all need real serving config files, which are born with the runtime / Gate 9. Gate 5 hands them the contract + audit schema + Check-4 as ready inputs.
- **Full object-ownership migration enforcement beyond the drift assert** (e.g., event triggers auto-reowning new objects) - the Tier-6 assert + authoring discipline suffice for now.
- **Tamper-evident audit** (hash-chaining / WORM / cluster `pgaudit`) - Gate 5 audit is detective-only and truncatable by a superuser; stated plainly, deferred to a later hardening gate.
- **Retention/partitioning automation** - declare partition key + retention posture in a comment only.
- **SECURITY DEFINER write-mediation layer** (definer-owned insert/update wrappers) - Gate 5's only definer function is audit capture.
- **Reviewer approval-WRITE + decision table + workflow UI** - Gate 5 ships the read-only `records_auditor` role only.
- **Gate 9** - rebinding the `TO <app-role>` policies to authenticated/anon/service, and the `source_links` content-serving policy.

---

## Re-audit gate (spec 5.3-equivalent, before merge)

Mandatory, mirroring Gate 3: whole-branch Claude review (5-dimension workflow, adversarial refute-stage) **+ Codex cross-engine** via `apex-jobs review-run --review-head records/gate5-serving-security --base-ref main --json`. Concentrate the adversarial lens on:
1. **The definer-owner false-green** (G5-D10/AC6): can a postgres-owned `fn_audit_capture` slip through and mask a missing INSERT policy? Verify the `proowner` + `rolbypassrls` + insert-as-writer-lands asserts actually fail on the bad build (plant-the-bad-state test, per the Gate-3 fresh-state-bias lesson).
2. **Ownership-drift**: does the Tier-6 hygiene assert actually fail when a new object is superuser-owned (plant a superuser-owned records object -> assert must fail)?
3. **Metadata-minimal**: is there ANY path by which a source data value (not just a hash/column-name) reaches `audit_log`? Especially the `row_hash` derivation and `changed_columns`.
4. **source_links exclusion**: proven no trigger fires on `neta_table_source_links`.
5. **Reversibility**: 046-049 `_down` symmetry (re-owner back, NO FORCE, drop roles guarded, DROP OWNED guard); no orphaned owned objects block a role drop.
6. **No `TO PUBLIC`** on any new policy; `polroles` explicit; Check-3 still dormant (not accidentally armed).

Fold all findings; operator ratifies before merge. Not applied to prod Supabase.

---

## Appendix A - Ownership spike results (2026-07-03, disposable DB)

```
[INV] relkind=r count=15 owner(s)=postgres
[INV] relkind=v count=2 owner(s)=postgres
[INV] schema owner=postgres ; distinct object owners=['postgres']
[INV] owner-role postgres: superuser=True bypassrls=True canlogin=True
[INV] function fn_set_updated_at owner=postgres
[BASE] superuser counts: {seeded_ref_a(neta_tables):88, seeded_ref_b(neta_procedures):72, assets:0, source_links:0}
[REOWN] explicit ALTER OWNER done: {table:15, view:2, sequence:0, function:1, schema:1}
[REOWN] objects NOT owned by records_owner after reassign: 0 (expect 0)
[TEETH] neta_tables FORCED: superuser=88  records_owner=0 (want 0)  records_api=88
[TEETH] neta_procedures UNFORCED: records_owner=72 (owner bypasses RLS when not forced)
[STALE] owner-path write on forced neta_tables -> INSERT BLOCKED (violates RLS policy)
[DOWN] objects NOT back to postgres after reverse: 0 (expect 0)
VERDICT: GO - feasible, clean, reversible.
```
