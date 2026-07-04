# Records Gate 9 - Supabase Serving: AC1-AC12 Evidence

Status: gate green. Lane: records/gate9-supabase-serving. Repo:
apex-records-gate9. HEAD at evidence time: 5bea009a (tree clean before and
after this run). Evidence captured: 2026-07-04 (UTC).

This document is the closing evidence record for Task 6 of the Gate 9 plan:
it runs the complete validation gate, proves the residue is clean (delta
form), and maps every acceptance criterion in
`docs/superpowers/specs/2026-07-03-records-gate9-supabase-serving-design.md`
(section 9) to its exact proof.

All commands below are value-silent: no DSN, password, or credential value
appears in this document or in the gate/residue output that produced it.

## 1. Gate command and result (tiers 0-7, DB-free + DB-required)

Command (run on the canonical host repo, `.env.dev` sourced into the shell,
never echoed):

```
cd apex-records-gate9 && set -a; . ./.env.dev; set +a && \
  ./.venv/bin/python -m pytest infra/database/migrations/records/test__dbtest_helper.py \
     infra/database/migrations/records/test_run_validation_unit.py \
     infra/database/migrations/records/test_serving_identity_unit.py \
     reference/records/test_serving_contract.py -q && \
  bash infra/database/migrations/records/test_secret_audit_ac8.sh && \
  ./.venv/bin/python infra/database/migrations/records/run_validation.py --require-db
```

### 1a. DB-free pytest (harness unit tests + contract tests)

```
........................................                                 [100%]
```

40 tests collected, 40 passed, 0 failed, 0 skipped. Exit code: 0.

Files covered: `test__dbtest_helper.py` (guard/DSN/neta-data-dir helpers),
`test_run_validation_unit.py` (stack enumeration, DSN derivation, val-name
shape, tier-parsing, summary formatting, role-snapshot logic),
`test_serving_identity_unit.py` (assert_serving_identity pass/fail modes -
always runs, no DB needed), `reference/records/test_serving_contract.py`
(SERVING_CONTRACT v2 shape, ASCII-only, dormant Check-3 assertion).

### 1b. secret-audit Check 3 fixture (AC9 armed-detector proof)

```
RESULT: AC8 fixture test PASSED
```

(File is named `test_secret_audit_ac8.sh` from an earlier AC-numbering pass
in this lane; the assertion it proves against the current spec numbering is
AC9 - secret-audit Check 3 arming. See section 3, AC9 row.) Exit code: 0.
All fixture assertions - including every `value-silent: ...` line - passed;
no planted secret value (owner/service_role/sb_secret_*/URL-form password)
appeared in captured Check 3 output.

### 1c. run_validation.py --require-db (tiers 0-7, live disposable DB)

```
=== records validation summary ===
  0-syntax         PASS  compileall + origin asserts
  1-converters     PASS  pytest rc=0
  2-import-pure    PASS  pytest rc=0
  3-migrations     PASS  49 applied, 43 tests executed, 0 skipped
  4-import-db      PASS  3 DB test files, pytest rc=0
  5-roles          PASS  PP1-2/DP1-9/DP-ESC/polroles green
  6-posture        PASS  ownership/roles/definer-allowlist/no-membership/trigger-set/isolation/FORCE-RLS green
  7-serving        PASS  Option-B serving matrix proven exhaustively (AC1-AC10)
executed test files: 46
```

Exit code: 0. **8 of 8 tiers PASS, 0 SKIP, 0 FAIL.** The disposable database
(`records_val_20260704T041003_31368`) was created, walked through all 49
migrations, exercised, and dropped in the same run; the run's own teardown
log shows the drop and the six roles it created for the walk
(`records_owner`, `records_fn_owner`, `records_auditor`, `anon`,
`authenticated`, `service_role`) each individually dropped via `[drop-role]`
(passwordless stubs only - a role carrying a password would be retained and
flagged `[keep-role]`; none were).

## 2. Residue check (delta form - rev-5 P2-2 shape)

The gate's own teardown already drops what it creates. This section is an
independent, external verification: snapshot cluster-level roles and
`records_val_*` databases immediately before and after the gate run, and
assert the sets are identical (no new role, no new val-DB left behind by
THIS run), while disclosing any pre-existing `records_val_*` database that
predates this lane.

Snapshot query (value-silent; connects via the admin DSN already in the
sourced environment, prints only role/db names):

```
select rolname from pg_roles where rolname = any(ARRAY[
  'records_api','records_intake_writer','records_owner','records_fn_owner',
  'records_auditor','anon','authenticated','service_role']);
select datname from pg_database where datname like 'records_val_%';
```

### Before the gate run

```
ROLES: ['records_api', 'records_intake_writer']
VALDBS: ['records_val_repro_48838']
```

### After the gate run

```
ROLES: ['records_api', 'records_intake_writer']
VALDBS: ['records_val_repro_48838']
```

### Delta verdict

```
ROLE DELTA: EMPTY (no new role created by this run)
VALDB DELTA: EMPTY (0 new records_val_* DB leaked by this run)
PRE-EXISTING DISCLOSED: records_val_repro_48838 (stale, predates this lane, present before and after, untouched by this run)
```

`records_api` and `records_intake_writer` are long-lived, password-bearing
serving roles from earlier lane work (Gate 5) - present before this run,
unchanged after it, and out of scope for this run's create/drop cycle (the
gate's `[keep-role]` path exists precisely so a password-bearing role is
never dropped). `records_val_repro_48838` is a **known stale disposable
database that predates this lane**; it is disclosed here, not treated as a
failure, and this run neither created nor removed it, and did not touch
`records_dev` or any prod database.

## 3. AC1-AC12 to proof map

| AC | Requirement (abridged) | Exact proof |
|----|-------------------------|-------------|
| AC1 | Serving credentials are exactly the three contract roles; no owner/superuser/service_role/BYPASSRLS/sb_secret_* credential in any serving config. | `reference/records/test_serving_contract.py::test_every_connecting_role_has_direct_role_identity`, `::test_no_role_serves_via_authenticated_service_role_or_owner`, `::test_known_roles_present_with_expected_connect_posture` (DB-free, contract-level). Live: tier 7's exhaustive ACL matrix (`run_validation.py::tier7_serving`) drives only `records_api` / `records_intake_writer` / `records_auditor` against every object. |
| AC2 | records not exposed to Data API; no anon/authenticated/service_role/PUBLIC grant on any records object; a BYPASSRLS stub with no grant is still blocked at the grant layer. | Tier 7 (`tier7_serving`): PUBLIC-grant introspection (`7-public-schema-usage`, `7-public-object-grant`), the `DATA_API_ROLES` (`anon`/`authenticated`/`service_role`) rows of the exhaustive ACL matrix (`expected_ops` returns empty set for all three), schema-USAGE-leak check (`7-usage-leak-*`), and the live behavioral probe `7-service_role-grant-layer` (service_role is BYPASSRLS yet still denied `SELECT` on `records.assets` absent a grant - proves grants precede RLS). |
| AC3 | Only the sanctioned role DSNs reach the allowed objects; each role reaches exactly its contract scope and no more. | Tier 7's exhaustive `(role, object, op)` matrix (`expected_ops` + `want(hasp(...) == ...)` loop over `ALL_ROLES x allobjs x {SELECT,INSERT,UPDATE,DELETE}`) plus tier 5's dynamic proofs (`tier5_roles`: PP1/PP2/DP1-DP5/DP9 - reader can read but not write, writer can write only its column set, cross-role SET ROLE escalation denied). |
| AC4 | records_api reads exactly the 14 app-served tables and the 2 security-invoker views, writes nothing. | Tier 7 `expected_ops("records_api", obj)` = `{"SELECT"}` for `obj in REF + WP + V7_VIEWS` (14 tables + 2 views), empty otherwise; `7-anycol-write-leak-records_api-*` asserts no column-level write exists for records_api on any write-path table; tier 5 `DP1` (reader INSERT/UPDATE/DELETE all raise on all 6 write-path tables). |
| AC5 | records_intake_writer reads the 14 (not the 2 views) and inserts/updates only the column-scoped writer matrix on the 6 write-path tables; no DELETE. | Tier 7 column-ACL exactness block (`GRANTED_COLS` transcribed verbatim from migration 045, `has_column_privilege` per-column-per-op matrix `7-col-<table>.<col>-<op>-want-*`, plus the `aclexplode(pg_attribute.attacl)` full-scan `7-colacl-exactness` asserting the actual column-grant set equals the expected set exactly - catches both leaked and missing grants); `expected_ops("records_intake_writer", obj)` excludes the 2 views; tier 5 `DP2`/`DP3`/`DP4` (writer cannot update reserved/immutable columns, cannot DDL); no DELETE is proven by DELETE being absent from every `expected_ops` set for the writer (table-level DELETE is never granted). |
| AC6 | records_auditor reads audit_log only; cannot read operational/reference/view/source-link tables. | Tier 7 `expected_ops("records_auditor", obj)` = `{"SELECT"}` only for `obj == "audit_log"`, empty for every other object including `neta_table_source_links`; tier 6 posture check `6g` (`records_auditor` holds no table grant, no column grant, and is named in no policy outside `audit_log`). |
| AC7 | audit_log stays append-only; no serving grant or policy opens UPDATE/DELETE. | Tier 7 `expected_ops` never includes UPDATE/DELETE for `audit_log` under any role; tier 6 `6h` (FORCE-RLS negative control - drops `p_audit_log_ins`, proves the definer capture path RAISES 42501 rather than silently succeeding, i.e. audit_log admission is policy-gated, not owner-bypassed) plus `6c`/allowlist (`fn_audit_capture` is the sole SECURITY DEFINER writer, owned by `records_fn_owner`, no PUBLIC EXECUTE). |
| AC8 | neta_table_source_links remains closed to all three serving roles. | Tier 7: `neta_table_source_links` is in `OWNER_ONLY`; `expected_ops(role, "neta_table_source_links")` is the empty set for all of `records_api`/`records_intake_writer`/`records_auditor`, asserted via the same exhaustive `(role, obj, op)` matrix as every other object (`7-acl-*-neta_table_source_links-*-want-False`). |
| AC9 | secret-audit Check 3, once armed, allows exactly the three roles and fails on postgres/owner/service_role/sb_secret_*/BYPASSRLS across all DSN forms including Supavisor `[role].[project_ref]`; value-silent. | `infra/database/migrations/records/test_secret_audit_ac8.sh` (fixture-planted positive/negative cases across keyword-form, URL-form, and Supavisor dotted-user/uppercase-PGUSER forms; every planted secret value is built by runtime string concatenation so the tracked test file itself never carries a live signature; each `value-silent: ...` assertion confirms no planted value leaks into captured stdout+stderr). Result: `RESULT: AC8 fixture test PASSED` (see section 1b - the file's own name/header retain an earlier AC-numbering label; the assertion it proves against the current spec is AC9). |
| AC10 | Startup identity assertion proves session_user = current_user, both equal one sanctioned role, and that role is NOT rolsuper, NOT rolbypassrls, and not an owner role - so SET ROLE cannot false-green as sanctioned. | **Proven twice, by design:** (1) DB-free / always-runs: `infra/database/migrations/records/test_serving_identity_unit.py` (`test_pass_sanctioned`, `test_fail_set_role_masks_login`, `test_fail_superuser`, `test_fail_bypassrls`, `test_fail_owner_role`, `test_fail_unsanctioned` - exercises `assert_serving_identity` against fake connections, no DB required, runs in every DB-free pytest invocation). (2) Live, tier 7: `run_validation.py::_prove_serving_identity` (called from `tier7_serving`) - `SET SESSION AUTHORIZATION records_api` must NOT raise; `SET ROLE records_api` from the superuser session must RAISE (session_user != current_user, the exact masking case AC10 names); plain superuser session must RAISE; `SET SESSION AUTHORIZATION records_owner` (unsanctioned owner) must RAISE. All four live probes passed in this run's tier-7 PASS. |
| AC11 | Supabase security advisors run and are reviewed before any prod apply packet is accepted. | **Not proven by this dev-lane gate, by design** - AC11 is a prod-apply-time gate (design spec section 7, "Prod-variant apply packet"), and this lane performs no prod Supabase apply (see section 4 below). The requirement is carried forward, unexecuted, as a checklist item in the reviewed-but-not-applied prod-variant apply packet; it is discharged only when an operator runs the actual apply, not by this gate. |
| AC12 | SERVING_CONTRACT is revised to v2 with a direct-role/DSN serving identity (not `supabase_target: authenticated`); `test_serving_contract.py` fails if any connecting role's serving identity is authenticated, service_role, or an owner role. | `reference/records/test_serving_contract.py::test_yaml_parses_and_has_top_level_shape`, `::test_every_connecting_role_has_direct_role_identity`, `::test_no_role_serves_via_authenticated_service_role_or_owner`, `::test_every_non_connecting_role_is_owner_only_with_no_dsn`, `::test_known_roles_present_with_expected_connect_posture`, `::test_drm_boundary_keys_exist`, `::test_dsn_form_inventory_has_expected_shapes` (SERVING_CONTRACT v2 structural + identity-shape assertions - all in the DB-free suite, all green in section 1a). |

## 4. Honest-scope caveat (verbatim from the design spec, section 8)

> Gate 9 closes the non-superuser-owner RLS bypass for records serving only. The
> postgres superuser and the Supabase service_role can still bypass RLS; those
> remain custody-controlled (never minted as records serving credentials), covered
> by the secret-audit detector, and by the deferred startup assertion. Do not
> describe records serving as "safe by enforcement" without this qualification.

## 5. No prod apply in this lane

This lane performs no prod Supabase apply. All gate execution above (tiers
0-7, the secret-audit fixture, the DB-free pytest suite, and the residue
delta check) ran exclusively against a disposable `records_val_*` database
created and dropped within this run, on the dev admin connection. No
migration was applied to `records_dev` or any production Supabase project as
part of this evidence run. The prod-variant apply packet (design spec
section 7) is reviewed and produced by this lane but is explicitly deferred
to a separate, later, operator-run apply - it is not executed here, and AC11
(security advisor review) is discharged only at that later apply, not by
this gate.

## 6. Scope discipline

Only this evidence document was created by this task. No source, migration,
test, or contract file was modified to produce this gate result - the gate
was run as-is against the existing `5bea009a` tree, and the tree was
confirmed clean (`git status --porcelain` empty) both immediately before and
immediately after the gate run.
