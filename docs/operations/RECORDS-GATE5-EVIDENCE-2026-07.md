# Records Gate 5 - Serving Security Evidence Record

**Gate:** Gate 5 (ownership posture + audit substrate + serving contract), NETA-records lane.
**Spec:** `docs/superpowers/specs/2026-07-03-records-gate5-serving-security-design.md`
**Scope:** migrations 046-049 (Gate 5A ownership, Gate 5B audit substrate), harness Tier 6
(durable posture proofs), and the checked-in serving contract for Gate 9.

This document maps each acceptance criterion (AC1-AC11) to the real, committed artifact
that satisfies it, and reproduces the specific transcripts an adversarial reviewer would
ask for: the false-green negative controls, the actor-attribution proof, the
down/up-reversibility evidence, the honest-scope callout, and the DEV-7 auditor-retain
behavior. All evidence below is drawn from the actual files on `main` at the commits
listed, plus one live harness run captured on 2026-07-03.

## Commit inventory

| Migration / artifact | Commit | Subject |
| --- | --- | --- |
| 046 (ownership posture) | `048d50ce` | feat(records): 046 ownership posture - records_owner + FORCE RLS (Gate 5A) |
| 047 (audit roles) | `719e2a3c` | feat(records): 047 audit roles - records_fn_owner + records_auditor (Gate 5B) |
| 048 (audit_log + definer) | `303261bc` | feat(records): 048 audit_log (FORCE-RLS) + fn_audit_capture definer + fn_owner allowlist (Gate 5B) |
| 049 (audit triggers) | `10c04a6a` | feat(records): 049 audit triggers on the writer-grant set (Gate 5B) |
| Tier 6 + MANIFEST | `2eff8c30` | feat(records): Tier 6 ownership+audit posture proofs + parse_tiers {0..6} + MANIFEST (Gate 5) |
| Serving contract | `62f682d6` | docs(records): serving contract for Gate 9 (Gate 5) |
| Serving contract fixup | `94aea7d2` | docs(records): serving contract - fix app-served table count 15->14 (T6 review Minor) |

All seven commits are on `main` (`ee163d14`..`94aea7d2` covers the full Gate 5 spec+plan+build
arc); `git log --oneline main..HEAD` on the build worktree shows zero unmerged Gate 5 work.

## AC1-AC11 -> satisfying artifact

| AC | Requirement (abridged) | Migration / test / tier | Evidence |
| --- | --- | --- | --- |
| AC1 | Ownership + reversible: every `records.*` object + schema owned by `records_owner` after 046; `046_down` reassigns to `postgres`, `DROP OWNED` + `DROP ROLE` succeeds, RAISES if the role survives. | `046_records_ownership.sql` / `046_records_ownership_down.sql` / `test_046_records_ownership.py` | `test_046` asserts the three-catalog `OWNED_NE` count is 0 for `records_owner` post-up, runs `046_down`, re-asserts the same count is 0 for `postgres`, asserts `records_owner` is gone from `pg_roles` (count 0), then re-applies 046 and leaves it applied. See "Down-reversibility evidence" below for the RAISE-on-survival guard text. |
| AC2 | FORCE teeth: all 15 tables `FORCE ROW LEVEL SECURITY`; non-superuser owner sees 0 rows on a seeded table with no owner policy; app roles see their rows; owner-path INSERT is RLS-blocked. | `046_records_ownership.sql` / `test_046` | `test_046` asserts `relforcerowsecurity` count of non-FORCE tables is 0, then proves the teeth live: `SET SESSION AUTHORIZATION records_owner` on `records.neta_tables` returns 0 rows while `records_api` returns the full `base` count via the same connection. Tier 6(a) re-proves zero-stragglers on every CI run (see below). |
| AC3 | Ownership-drift: Tier-6 assert FAILS when any `records.*` object is owned by a `rolsuper` OR `rolbypassrls` role. | Tier 6(a), `run_validation.py` `OWNED_BY_SUPER_OR_BYPASS` | The query unions `pg_class` (relkind r/v/m/S) + `pg_proc` + `pg_namespace`, each joined to `pg_roles` and filtered on `rolsuper OR rolbypassrls`; Tier 6 fails with `"6a: a records object is owned by a super/bypassrls role"` if the union is non-zero. This is the identical three-catalog union used in 046's own asserts (see "three-catalog" note under AC1/AC4 mapping). |
| AC4 | Audit capture: triggers on exactly the writer-grant table set (derived, not hardcoded); not on `audit_log`/`source_links`; writer INSERT+UPDATE each yield one row; DELETE coverage exercised via superuser DELETE (writer has no DELETE per Gate 3), row_pk non-null. | `049_records_audit_triggers.sql` / `test_049_records_audit_triggers.py` / Tier 6(e) | `test_049` derives `WANT_TRIGGER_COUNT` from `information_schema.role_column_grants` for `records_intake_writer` INSERT/UPDATE (not a hardcoded list) == 6 (`assets, form_submissions, form_field_values, pm_schedules, pm_events, persons`), asserts `GOT_TRIGGER_COUNT` (real `trg_audit` triggers) matches, and asserts `FORBIDDEN_TRIGGER` (audit_log, neta_table_source_links) == 0. The superuser UPDATE+DELETE block (`by_action["delete"]`) asserts `d_pk == str(pk)` (row_pk non-null on DELETE) and `d_actor == admin_login`, `d_is_su is True`. Tier 6(e) re-derives the same want/got pair on the final migrated DB every CI run. |
| AC5 | Metadata-minimal: `audit_log` has NO before/after value-image column AND NO content `row_hash`; `actor_role` = mutating session identity; no audit row contains an operational data value. | `048_records_audit_log.sql` (table DDL) / `test_048_records_audit_log.py` | 048's `audit_log` DDL carries only `audit_id, table_name, pk_name, row_pk, action, actor_role, definer_role, actor_is_superuser, changed_columns (name array), txid, occurred_at, app_actor` - no `old_row`/`new_row`/`row_hash` column exists in the DDL. `test_049`'s UPDATE proof asserts `u_changed == ["display_name"]` (column NAMES, not values), and no assertion anywhere reads a captured value payload, because none is stored. |
| AC6 | Definer false-green guard: `fn_audit_capture` is SECURITY DEFINER owned by `records_fn_owner`; three asserts (proowner, owner non-bypass/non-super, insert-as-writer lands) in one path; negative control (drop INSERT policy -> capture RAISES); function not `postgres`-owned. | `048_records_audit_log.sql` / `test_048_records_audit_log.py` / Tier 6(c)/(h) | See "False-green negative-control evidence" below - reproduced in full from the actual test and Tier 6 code. |
| AC7 | Audit isolation: `records_auditor` (via SET ROLE) reads `audit_log`; `records_api`/`records_intake_writer` can neither read nor write it; `records_auditor` has no grant/policy on `neta_table_source_links` or any operational/reference table. | `047_records_audit_roles.sql` / `048_records_audit_log.sql` / Tier 6(f)/(g) | Tier 6(f): `SET ROLE records_auditor` then `SELECT count(*) FROM records.audit_log` succeeds; the same statement under `SET SESSION AUTHORIZATION records_api` and `records_intake_writer` raises and is caught (denial confirmed for both). Tier 6(g): zero rows from `information_schema.role_table_grants` / `role_column_grants` for `records_auditor` outside `audit_log`, and zero `pg_policies` rows naming `records_auditor` outside `audit_log`. |
| AC8 | Tier-6 posture: three roles non-super/non-bypassrls; `fn_audit_capture` prosecdef+proconfig durable re-check; `SET ROLE` into owner roles denied from app/rogue roles. | Tier 6(b)/(c)/(d) | Tier 6(b) checks `rolsuper`, `rolbypassrls`, `rolcanlogin` (against an explicit `want_login` map), `rolcreatedb`, `rolcreaterole`, `rolreplication` for all three of `records_owner`/`records_fn_owner`/`records_auditor`. Tier 6(c) re-checks `FN_CAPTURE_META` (owner, `prosecdef`, `search_path` pinned via `proconfig`, zero PUBLIC EXECUTE via `aclexplode`) plus the full 048 exact-allowlist DO block. Tier 6(d) denies `SET ROLE records_owner`/`records_fn_owner` from `records_api` and from a freshly created rogue login role (`expect_raise` savepoint pattern), and separately asserts zero `pg_auth_members` edges touching any of the three roles in either direction (membership-drift durability, item AC8 "no membership"). |
| AC9 | Serving contract: `SERVING_CONTRACT.{yaml,md}` present + machine-readable; every connecting role has a `supabase_target`; every NOLOGIN owner flagged `connects:false`/owner-only/no-DSN; Check-3 stays a dormant, honest SKIP (not armed). | `reference/records/SERVING_CONTRACT.yaml` / `reference/records/SERVING_CONTRACT.md` (commit `62f682d6`, fixed up in `94aea7d2`) | The YAML classifies `records_api`/`records_intake_writer`/`records_auditor` as `connects: true` with a `supabase_target`, and `records_owner`/`records_fn_owner` as `connects: false` (owner-only, no DSN). `RECORDS_SERVING_GLOBS` is unset by design, so Check-3 records an honest SKIP rather than a false PASS with nothing armed - the fixup commit corrected the app-served table count (15->14) caught in T6 review. |
| AC10 | Discipline: every migration has a reversible `_down` (symmetry proven, fail-loud on role survival); ASCII-only added lines; all tests on disposable DBs; nothing applied to prod Supabase. | 046-049 `*_down.sql` / `test_046`-`test_049` / this doc's ASCII check | See "Down-reversibility evidence" and the ASCII-check section below. All four migrations were validated exclusively against `records_val_20260703T200558_7343`, a harness-created disposable DB dropped at the end of the run (see captured transcript below); `RECORDS_PG_ADMIN_DSN` in `.env.dev` never points at `records_dev` or a Supabase project, and the harness's `guard_target()`/`assert_val_name()` refuse `records_dev` and any non-`records_val_*` name by construction. |
| AC11 | Actor attribution: writer INSERT records `actor_role=records_intake_writer` + `definer_role=records_fn_owner` (not the definer as actor); superuser/direct-SQL mutation records `actor_role`=session login + `actor_is_superuser=true`; writer path exercised via `SET SESSION AUTHORIZATION` (not `SET ROLE`). | `test_049_records_audit_triggers.py` | See "Actor-attribution evidence" below - reproduced verbatim from the test. |

## False-green negative-control evidence (AC6)

Two independent negative controls exist, at two different points in the stack, both proving
the same claim: **the audit row lands because of the `INSERT ... TO records_fn_owner` policy,
not because the definer or its owner bypasses RLS.**

**`test_048_records_audit_log.py` (per-migration, point-in-time):**
```
115:    # (3) NEGATIVE CONTROL (savepoint discipline) ---------------------------
117:    # inside a savepoint, re-fire the insert -> RLS rejects it (42501); then
118:    # rollback to the savepoint (which un-drops the policy). If the policy were
124:            cur.execute("savepoint s")
125:            cur.execute("drop policy p_audit_log_ins on records.audit_log")
126:            raised = False
130:                raised = True
131:                # SQLSTATE 42501, message mentions the RLS policy violation.
132:                assert e.sqlstate == "42501"
134:            assert raised, (
135:                "negative control FAILED: insert succeeded with the INSERT "
141:            cur.execute("rollback to savepoint s")
```
With `p_audit_log_ins` dropped inside a savepoint, the definer-path INSERT into `audit_log`
is rejected with SQLSTATE `42501` (RLS violation) rather than silently succeeding - proof
that `records_fn_owner` (the function's owner) does not bypass FORCE RLS on its own table.
The savepoint rollback restores the policy with zero residue.

**Tier 6(h) (durable, every-CI-run, exercised via a real writer-table INSERT once 049's
triggers exist):**
```python
cur.execute("savepoint h")
cur.execute("drop policy p_audit_log_ins on records.audit_log")
cur.execute("set session authorization records_intake_writer")
raised = False
try:
    cur.execute("insert into records.persons (display_name) values ('t6-forcerls-probe')")
except psycopg.errors.InsufficientPrivilege as e:
    raised = True
    if e.sqlstate != "42501" or "row-level security policy" not in str(e):
        fails.append(f"6h: capture raised but not the expected RLS violation: {e}")
except psycopg.errors.Error as e:
    raised = True
    fails.append(f"6h: capture raised an unexpected error (not 42501 RLS): {e}")
if not raised:
    fails.append("6h: writer insert SUCCEEDED with p_audit_log_ins dropped "
                 "(FORCE-RLS no-op / owner bypass - audit_log admission is not policy-gated)")
cur.execute("rollback to savepoint h")   # aborts the txn + un-drops the policy
```
Tier 6(h) fires the *trigger* path (a real `records_intake_writer` INSERT into
`records.persons`, which carries `trg_audit`) rather than calling the definer function
directly - a trigger function cannot be invoked without `TG_OP`/`NEW`/`OLD` context, so this
is the only way to exercise it end-to-end. The comment states the failure mode explicitly:
if FORCE RLS were a no-op or the owner bypassed it, the insert would **succeed**, and the
`if not raised` branch is exactly the false-green trap this control is built to catch. Both
controls returned PASS in the 2026-07-03 run (see captured transcript below - `6-posture
... FORCE-RLS green`).

## Actor-attribution evidence (AC11)

From `test_049_records_audit_triggers.py`, the writer path (`SET SESSION AUTHORIZATION`,
not `SET ROLE`, per the spec's explicit requirement that `SET ROLE` would leave
`session_user=postgres` and falsely attribute the row):

```python
cur.execute("set session authorization records_intake_writer")
cur.execute(
    "insert into records.persons (display_name) values ('audit-writer-fixture') "
    "returning person_id"
)
...
assert actor_role == "records_intake_writer"   # session_user, not the definer
assert definer_role == "records_fn_owner"       # current_user = the definer owner
assert is_su is False             # the writer is a non-superuser login
```

And the superuser / direct-SQL path (no `SET` at all - proving direct admin writes are not
invisible to the trail):

```python
admin_login = cur.execute("select session_user").fetchone()[0]
admin_is_su = cur.execute(
    "select rolsuper from pg_roles where rolname=session_user"
).fetchone()[0]
assert admin_is_su is True, "walk admin must be a superuser for this proof"
...
u_action, u_actor, u_is_su, u_pk, u_changed = by_action["update"]
assert u_actor == admin_login          # direct-SQL actor = the admin login
assert u_is_su is True                 # captured as superuser
...
d_action, d_actor, d_is_su, d_pk, d_changed = by_action["delete"]
assert d_actor == admin_login
assert d_is_su is True
assert d_pk == str(pk)                 # row_pk non-null on delete
```

This is the exact contrast the AC demands: the writer row's `actor_role` is the writer
(`records_intake_writer`) with `definer_role` separately recording the SECURITY DEFINER
owner (`records_fn_owner`) - the definer is never mistaken for the actor - while the
superuser row's `actor_role` is the admin login itself with `actor_is_superuser=true`,
so a direct-SQL superuser mutation is captured, not silently missed.

## Down-reversibility evidence (AC1, AC10)

Every one of 046-049 is proven reversible by its own test, following the identical
runner contract (rev-3 correction 3): the harness applies migration NNN, then the test
asserts the applied-NNN posture, runs `NNN_down`, asserts the reversed/pre-state, re-runs
`NNN` (up), and leaves the DB at applied-NNN - never re-applying NNN first, never leaving
it reversed. `test_046_records_ownership.py` is representative:

```python
def test_046_applied_then_down_up():
    dsn = _dbtest.dsn()
    # (1) applied posture: everything records_owner-owned across all catalogs
    assert _q(dsn, OWNED_NE % ("records_owner", "records_owner", "records_owner"))[0][0] == 0
    ...
    # (2) DOWN -> reversed to the postgres pre-state (all catalogs) + role dropped
    _dbtest.run_psql(DOWN, dsn)
    assert _q(dsn, OWNED_NE % ("postgres", "postgres", "postgres"))[0][0] == 0
    assert _q(dsn, "select count(*) from pg_roles where rolname='records_owner'")[0][0] == 0
    # (3) UP -> re-apply 046 and LEAVE it applied
    _dbtest.run_psql(MIG, dsn)
    assert _q(dsn, OWNED_NE % ("records_owner", "records_owner", "records_owner"))[0][0] == 0
```

`OWNED_NE` is the same three-catalog union (`pg_class` + `pg_proc` + `pg_namespace`) used
throughout 046/Tier 6, so ownership reversal is proven, not merely table-existence.

**Fingerprint stability (harness-level, all of 003-049 including 046-049):** the Tier-3
walk (`run_validation.py::tier3_walk`) takes a schema-only catalog `_fingerprint()` of the
`records` schema immediately before and after each `test_NNN` runs, and fails the whole
tier with `"{tf} PASSED but did not restore its migration (schema fingerprint moved)"` if
they differ - this is what proves each test's down->up round-trip left the schema exactly
where the walk expects it, independent of and in addition to each test's own explicit
assertions. All four Gate-5 migration tests passed this check in the captured run below
(`3-migrations PASS 49 applied, 43 tests executed, 0 skipped`).

Every migration's `_down` also fails loud rather than swallowing survival:
`046_records_ownership_down.sql` / `047_records_audit_roles_down.sql` reassign or drop the
owner roles and RAISE if `DROP ROLE` leaves the role in place (mirroring 045's revoke-first
+ exactness-assert pattern) - the one deliberate, documented exception being the DEV-7
guard on the LOGIN role `records_auditor`, below.

## DEV-7 auditor-retain note (AC10)

`records_auditor` is the one password-bearing LOGIN role in the Gate-5 role set, and its
`_down` migration cannot apply the same "RAISE if it survives" rule as the two NOLOGIN
owner roles, because dropping a password-bearing role out from under a live credential
would be destructive in a way a re-run migration should not silently do. From
`047_records_audit_roles_down.sql`:

```sql
25:-- records_auditor: LOGIN, password provisioned out-of-band -> DEV-7 guard,
27:-- explicit DB-scoped revokes, then DROP ROLE ONLY if it is passwordless
28:-- (harness / disposable-DB case); RETAIN with a NOTICE if password-bearing.
37:  select (rolpassword is not null) into has_pw from pg_authid where rolname='records_auditor';
39:    raise notice '047_down: records_auditor is password-bearing; RETAINED (DEV-7 guard).';
```

The down migration always revokes `records_auditor`'s grants first (both directions, all
DB-scoped privileges), regardless of password state - the isolation posture is fully
undone either way. It then checks `pg_authid.rolpassword`: if the role is passwordless
(the harness-created disposable-DB case, where 047 provisions no password), `DROP ROLE`
proceeds and the down is exact-symmetric like the other two roles. If the role carries a
password (the real out-of-band-provisioned case on a persistent cluster), the role is
**retained** with an explicit `RAISE NOTICE`, never silently dropped and never silently
kept without a trace in the migration output. This is a deliberate, narrow exception to
the "down RAISES on survival" rule, scoped to exactly the one LOGIN/password-bearing role,
and it is stated as such in the constraints inherited by every task in this gate.

## Honest-scope + residual-superuser/service_role callout (G5-D1, AC2/AC3)

Verbatim from the spec (`docs/superpowers/specs/2026-07-03-records-gate5-serving-security-design.md`):

> **Honest scope claim.** This gate closes the NON-superuser-owner RLS-bypass. It does NOT
> close `postgres`-superuser or Supabase `service_role` bypass - those remain custody +
> detector + a startup-identity assertion deferred to the first real serving process. The
> gate's writeup must say "much safer + detectable," never "safe by enforcement" unqualified.

Concretely: 046 moves every `records.*` object off the `postgres` superuser onto
`records_owner` (non-super, non-bypassrls) and turns on `FORCE ROW LEVEL SECURITY` on all
15 tables, which is what makes an owner-path bypass (the vulnerability this gate targets)
structurally impossible for `records_owner` - proven by AC2/AC3/Tier-6(a). But:

- **`postgres` superuser** still bypasses RLS entirely by Postgres design (superuser status,
  not ownership, is what FORCE RLS cannot touch) - migrations themselves run as `postgres`
  for exactly this reason (G5-D3: "Migrations run as postgres (superuser bypasses FORCE -
  verified), so migration DDL/DML is unaffected").
- **Supabase `service_role`** is a bypass-capable role in Supabase's own Postgres
  configuration, outside this gate's migration surface entirely.

Both remain **custody-controlled** (who holds the superuser/service_role credential),
**detector-covered** (the dormant Check-3 in the serving contract is the future automated
tripwire), and **deferred to a startup-identity assertion** that the spec explicitly places
in the serving-runtime / Gate 9 work, because that assertion needs a real serving process
and real config files to run against - both of which are non-goals of this documentation-
and-migration-only gate. This is why the evidence in this document is stated as "closes
the non-superuser-owner bypass, does not claim superuser/service_role-proof," matching the
spec's required framing exactly.

## Captured harness transcript (2026-07-03, live run against a disposable DB)

Command: `set -a; . ./.env.dev; set +a; export PATH=$HOME/.local/bin:$PATH; .venv/bin/python
infra/database/migrations/records/run_validation.py --require-db`

```
[connect] dbname=records_val_20260703T200558_7343
--- test_046_records_ownership.py (rc=0) ---
.                                                                        [100%]
[connect] dbname=records_val_20260703T200558_7343
[connect] dbname=records_val_20260703T200558_7343
--- test_047_records_audit_roles.py (rc=0) ---
.                                                                        [100%]
[connect] dbname=records_val_20260703T200558_7343
[connect] dbname=records_val_20260703T200558_7343
--- test_048_records_audit_log.py (rc=0) ---
.                                                                        [100%]
[connect] dbname=records_val_20260703T200558_7343
[connect] dbname=records_val_20260703T200558_7343
--- test_049_records_audit_triggers.py (rc=0) ---
.                                                                        [100%]
[connect] dbname=records_val_20260703T200558_7343
--- tier4 (rc=0) ---
.......                                                                  [100%]
[connect] dbname=postgres
[drop] records_val_20260703T200558_7343

=== records validation summary ===
  0-syntax         PASS  compileall + origin asserts
  1-converters     PASS  pytest rc=0
  2-import-pure    PASS  pytest rc=0
  3-migrations     PASS  49 applied, 43 tests executed, 0 skipped
  4-import-db      PASS  3 DB test files, pytest rc=0
  5-roles          PASS  PP1-2/DP1-9/DP-ESC/polroles green
  6-posture        PASS  ownership/roles/definer-allowlist/no-membership/trigger-set/isolation/FORCE-RLS green
executed test files: 46
```

The disposable database `records_val_20260703T200558_7343` was created by the harness
(`make_val_name()` / `assert_val_name()`), used exclusively for this run, and dropped at
the end (`[drop] records_val_20260703T200558_7343`) - no shared or persistent database
(`records_dev` or otherwise) was touched.

## CI wiring confirmation (Step 2)

`.github/workflows/records-ci.yml` runs the gate as:

```yaml
- name: Harness unit tests (the gate's own tests)
  run: python -m pytest infra/database/migrations/records/test__dbtest_helper.py infra/database/migrations/records/test_run_validation_unit.py -q
- name: AC8 secret-audit fixture test (records serving config)
  run: bash infra/database/migrations/records/test_secret_audit_ac8.sh
- name: Run the records validation gate
  run: python infra/database/migrations/records/run_validation.py --require-db
```

The final step invokes `run_validation.py --require-db` with **no `--only` flag**. In
`run_validation.py::parse_tiers`:

```python
def parse_tiers(only):
    """Validate --only. Unknown tiers must REFUSE - a typo like --only 9
    running zero tiers and exiting 0 would be a false-green gate."""
    if not only:
        return {0, 1, 2, 3, 4, 5, 6}
```

an empty/absent `--only` resolves to the full `{0, 1, 2, 3, 4, 5, 6}` tier set - so **Tier 6
(the Gate-5 durable ownership+audit posture proof) already runs on every CI invocation of
this workflow**, with no yaml edit required. The AC8 secret-audit fixture step
(`test_secret_audit_ac8.sh`) is untouched and remains a separate, preceding step in the
same job. No change was needed or made to `.github/workflows/records-ci.yml` for this task.

## Scope note

This document covers Tasks 1-6 (migrations 046-049, Tier 6, serving contract) as already
committed on `main`. No new migration, test, or CI change was introduced by this task -
this is a documentation-only evidence record plus a CI-wiring confirmation, per the Task 7
brief.
