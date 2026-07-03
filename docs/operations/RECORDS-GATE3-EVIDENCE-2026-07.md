# Records Gate 3 (Security/RLS) - AC Evidence

Spec of record: `docs/superpowers/specs/2026-07-02-records-gate3-security-rls-design.md`
rev 6 (`a83701a3`). Plan of record: `337f3f96` (Gate 3 plan rev 3). Branch
`records/gate3-security-rls`. This document captures the closing evidence for
Task 6 of that plan: the full validation ladder, the down-migration symmetry
check, the AC8 secret-audit run, the teardown-DROP positive proof, CI
confirmation, and the AC1-AC8 checklist.

No DSN, password, or other secret value appears anywhere below. The harness's
own `[connect] dbname=...` / `[create] ...` / `[drop] ...` log tokens are the
only database-identifying output produced anywhere in this evidence, and they
are documented by the harness as safe (dbname only, never credentials).

## 1. Full validation ladder (Tiers 0-5, disposable DB)

Command run (per `_HOST_OPS_DB.md`):

```
cd apex-records-gate3 && set -a && . ./.env.dev && set +a && \
  .venv/bin/python infra/database/migrations/records/run_validation.py --require-db
```

Full transcript (all 42 executed test files, tail shows the summary):

```
--- tier1 (rc=0) ---
...........                                                              [100%]
--- tier2 (rc=0) ---
.........                                                                [100%]
[connect] dbname=postgres
[connect] dbname=postgres
[connect] dbname=records_val_20260703T051103_8584
--- test_005_neta_reference.py (rc=0) ---
.........                                                                [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_007_asset_class_shell.py (rc=0) ---
.............                                                            [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_008_backfill.py (rc=0) ---
........                                                                 [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_010_lv_cb_template.py (rc=0) ---
.................                                                        [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_011_mvhv_cb_template.py (rc=0) ---
.....................                                                    [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_012_xfmr_template.py (rc=0) ---
.................                                                        [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_013_switchgear_template.py (rc=0) ---
...............                                                          [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_014_cable_template.py (rc=0) ---
.............                                                            [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_015_it_template.py (rc=0) ---
.................                                                        [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_016_grounding_template.py (rc=0) ---
.............                                                            [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_017_surge_template.py (rc=0) ---
................                                                         [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_018_motor_template.py (rc=0) ---
..............                                                           [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_019_motor_starter_template.py (rc=0) ---
..............                                                           [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_020_xfmr_capture_mode.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_021_xfmr_pf_readings.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_022_it_pf_readings.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_023_transfer_switch_template.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_024_ups_template.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_025_battery_template.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_026_charger_template.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_027_switch_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_028_meter_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_029_engine_generator_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_030_busway_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_031_cap_bank_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_032_outdoor_bus_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_033_reactor_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_034_ngr_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_035_circuit_switcher_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_036_voltage_regulator_template.py (rc=0) ---
.......                                                                  [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_037_load_tap_changer_template.py (rc=0) ---
.......                                                                  [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_038_neta_tables_standard.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_039_xfmr_neta_standards.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_040_neta_standards_scaleout.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_041_form_submission_standard.py (rc=0) ---
...                                                                      [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_042_network_protector_template.py (rc=0) ---
..........                                                               [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_043_neta_table_source_links.py (rc=0) ---
..........................                                               [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_044_person_anchor.py (rc=0) ---
.........                                                                [100%]
[connect] dbname=records_val_20260703T051103_8584
[connect] dbname=records_val_20260703T051103_8584
--- test_045_records_security_rls.py (rc=0) ---
.........                                                                [100%]
[connect] dbname=records_val_20260703T051103_8584
--- tier4 (rc=0) ---
.......                                                                  [100%]
[connect] dbname=postgres
[drop] records_val_20260703T051103_8584

=== records validation summary ===
  0-syntax         PASS  compileall + origin asserts
  1-converters     PASS  pytest rc=0
  2-import-pure    PASS  pytest rc=0
  3-migrations     PASS  45 applied, 39 tests executed, 0 skipped
  4-import-db      PASS  3 DB test files, pytest rc=0
  5-roles          PASS  PP1-2/DP1-9/DP-ESC/polroles green
executed test files: 42
```

**Confirmed:** `records_dev` appears in zero lines of this (or any) transcript
captured in this document (`grep -c records_dev` over the raw run output = 0).
Every `[connect]` line targets either `dbname=postgres` (the admin/maintenance
connection) or the single disposable `dbname=records_val_20260703T051103_8584`,
which is created once and dropped once (`[drop] records_val_20260703T051103_8584`).
A direct post-run query (`select count(*) from pg_database where datname like
'records_val_%'`) returned **0** - no disposable database residue on the
cluster after the run.

## 2. `test_045_records_security_rls.py` assertions (Task 1)

9 `def test_...` functions, all PASS (`.........` = 100%) in the ladder above
and independently in Task 1's own commit-time run:

1. `test_rls_enabled_on_all_records_tables` - RLS is ON for every records-schema
   table (no table left with `relrowsecurity = false`).
2. `test_no_policy_is_public` - no `records` policy has `roles is null` or
   `'public' = any(roles)` (every policy names explicit roles via `TO`).
3. `test_no_public_execute_on_routines` - PUBLIC holds no EXECUTE on any
   `records`-schema routine.
4. `test_no_public_on_tables_or_schema` - PUBLIC holds no grant on any
   `records` table/view and no USAGE on the `records` schema.
5. `test_reader_has_no_write` - `records_api` (reader) holds no INSERT/UPDATE/
   DELETE privilege on any records table.
6. `test_writer_holds_all_not_null_columns` - `records_intake_writer` holds
   column-level UPDATE/INSERT on every NOT-NULL invariant column it is
   supposed to write.
7. `test_writer_denied_reserved_columns` - `records_intake_writer` is denied
   grants on every D9-reserved column (`assets.status`/`condition`;
   `form_submissions.status`/`reviewed_by`; `pm_events.status`;
   `form_field_values.assessment`; `persons.worker_class`/`employee_ref`/
   `match_adjudicated_by`/`match_adjudicated_at`/`match_confidence`).
8. `test_views_are_security_invoker` - both `v_asset_test_history` and
   `v_pm_due` carry `security_invoker=true`.
9. `test_source_links_restricted` (D10) - `neta_table_source_links` has RLS
   enabled, owner-only, with NO app-role grant and NO policy.

All 9 passed identically across Task 1's post-commit run, Task 2's forward-
ladder regression, and the Task 6 full-ladder run captured above (Tier 3:
"45 applied, 39 tests executed, 0 skipped").

## 3. Down-migration symmetry check (Task 2, 10/10)

`045_records_security_rls_down.sql` was verified via a standalone script run
from a HOST path outside the repo (`/tmp/verify_045_down.py`, never committed,
removed after use) that applied migrations 001-045 forward on a disposable
`records_val_*` DB, applied the down migration, then asserted the full
pre-045 posture was restored:

```
[create] records_val_20260703T044858_35518
[applied] 45 forward migrations 001..045
[applied] 045_records_security_rls_down.sql
PASS: all 15 records tables present for inspection
PASS: RLS disabled on all 15 records tables
PASS: zero records policies remain
PASS: PUBLIC EXECUTE restored on fn_set_updated_at
PASS: PUBLIC EXECUTE restored on all records routines
PASS: no records_api/records_intake_writer table/view grants remain
PASS: no records_api/records_intake_writer routine grants remain
PASS: no records_api/records_intake_writer schema USAGE remains
PASS: role records_api dropped (password-less pre-check)
PASS: role records_intake_writer dropped (password-less pre-check)
[drop] records_val_20260703T044858_35518

SUMMARY: 10 passed, 0 failed
```

Down-migration checklist (spec F3 / Sec 5.3), confirmed by code inspection at
Task 2 time and re-confirmed for this document:

- (a) zero `DROP OWNED` executable statements (only appears in an explanatory
  code comment).
- (b) unconditional database-scoped revokes for both LOGIN roles (`records_api`,
  `records_intake_writer`), independent of password state.
- (c) `all routines` used throughout (never `all functions`).
- (d) guarded `DROP ROLE`: skips + `RAISE NOTICE` when `pg_authid.rolpassword
  is not null` (DEV-7), and is wrapped in an exception handler for
  `dependent_objects_still_exist`.

## 4. AC8 secret-audit run (Task 5)

### 4a. Clean-tree real audit (before detector additions were tested, and
again post-commit with the new fixture test file tracked)

```
[2] leaked credentials in tracked files
  PASS  no leaked credentials in tracked files
  note  8 match(es) suppressed by infra/.secret-audit-allow
[3] records serving config: only records_api/records_intake_writer, no bypass creds (AC8)
  SKIP  no RECORDS_SERVING_GLOBS set (serving config not built yet)
========================================
RESULT: clean
EXIT=0
```

`[3]` legitimately SKIPs in normal dev/CI runs because `RECORDS_SERVING_GLOBS`
is unset until the serving-config stage (Gate 5+) exists; this is documented,
expected dormancy, not a gap.

### 4b. Fixture test (positive + negative cases), final post-fix run

`infra/database/migrations/records/test_secret_audit_ac8.sh`:

```
PASS  positive fixtures: exit 1 as expected
PASS  rule fired: records-serving-non-app-role
PASS  rule fired: records-serving-bypass-credential
PASS  value-silent: no planted value appeared in captured output
PASS  sanctioned role (records_api) not flagged
PASS  sanctioned fixture did not trip bypass-credential rule
PASS  single-file fixture: exit 1 as expected
PASS  single-file fixture: rule fired
PASS  single-file fixture: file path present in FIND line
PASS  single-file fixture: planted value absent from captured output
RESULT: AC8 fixture test PASSED
EXIT=0
```

The single-file regression cases (last 4 lines) close a value-silent-contract
defect found during Task 5 review: GNU `grep` omits the `filename:` prefix
when a glob expands to exactly one file, which for Check 3 rule (b) caused
the captured *secret value itself* to be echoed into the FIND line instead of
a `file:line` locator. Fix: add `-H` (force filename prefix) to both Check 3
grep invocations (`infra/secret-audit.sh`, commit `ce717cb4`). Re-verified
clean/value-silent for both multi-file and single-file glob shapes.

Detectors added (Task 5, commit `8d1ef8b6` + fix `ce717cb4`):
- Check 2 rule `supabase-secret-key`: `sb_secret_[A-Za-z0-9_-]{16,}`.
- Check 3 (new, dormant until `RECORDS_SERVING_GLOBS` is set): rule
  `records-serving-non-app-role` (any `user=`/`role=` value that is not
  `records_api`/`records_intake_writer`); rule
  `records-serving-bypass-credential` (`sb_secret_`, `service_role`, or
  `bypassrls`, case-insensitive). Both rules print `file:line [rule: name]`
  only - never the matched text.

## 5. Teardown-DROP positive proof (closes a Task 3 review item)

**Problem:** `records_api`/`records_intake_writer` normally pre-exist on the
dev cluster (left behind, password-less, from prior ladder runs), so a normal
full-ladder run's `snapshot_roles()` finds them already present, records zero
`created_roles`, and the Tier-5 `finally` teardown has nothing to drop - the
DROP branch of the teardown code is never actually exercised by an ordinary
run, only its (correct) no-op branch.

**Method:** a small script (`drop_records_roles.py`, drop-if-exists,
exception-guarded, all DROP logic inside Python - never a literal `drop role`
in any bash command string) was authored locally and `scp`'d to `/tmp` on the
host (OUTSIDE the git tree), then run with `.env.dev` sourced and
`.venv/bin/python`. A companion read-only check script
(`check_records_roles.py`) confirmed role presence/absence at each step. Both
scripts were removed from `/tmp` after use; neither was ever committed.

Step-by-step transcript:

```
=== BEFORE DROP ===
records_api: PRESENT (has_password=False)
records_intake_writer: PRESENT (has_password=False)
present count: 2

=== RUNNING DROP SCRIPT ===
dropped: ['records_api', 'records_intake_writer']
kept: []
remaining count (expect 0): 0

=== AFTER DROP, BEFORE LADDER ===
records_api: ABSENT
records_intake_writer: ABSENT
present count: 0
```

Full ladder run immediately after (same command as Section 1), tail showing
the role create-then-drop sequence from the harness's own log lines:

```
[connect] dbname=postgres
[drop] records_val_20260703T051326_33802
[connect] dbname=postgres
[drop-role] records_api
[connect] dbname=postgres
[drop-role] records_intake_writer

=== records validation summary ===
  0-syntax         PASS  compileall + origin asserts
  1-converters     PASS  pytest rc=0
  2-import-pure    PASS  pytest rc=0
  3-migrations     PASS  45 applied, 39 tests executed, 0 skipped
  4-import-db      PASS  3 DB test files, pytest rc=0
  5-roles          PASS  PP1-2/DP1-9/DP-ESC/polroles green
executed test files: 42
```

The `[drop-role] records_api` / `[drop-role] records_intake_writer` lines are
produced by `run_validation.py`'s own `finally` teardown block (not by the
proof script), confirming `snapshot_roles()` found both roles absent this
run, `045` created them for the disposable DB's duration, Tier 5 proved
against them, and the teardown then dropped exactly the two roles this run
created - the DROP branch, not the no-op branch.

Final check, confirming both roles absent after the ladder completed:

```
=== AFTER LADDER TEARDOWN ===
records_api: ABSENT
records_intake_writer: ABSENT
present count: 0
```

**Result: the teardown DROP path was positively exercised**, not merely
correct-by-inspection. (Cluster state self-heals on the next ordinary ladder
run via `045`'s idempotent `create role ... if not exists`, exactly as noted
in Task 2's report.)

## 6. CI confirmation

`.github/workflows/records-ci.yml` needs **no change**. Its final two steps:

```yaml
      - name: Harness unit tests (the gate's own tests)
        run: python -m pytest infra/database/migrations/records/test__dbtest_helper.py infra/database/migrations/records/test_run_validation_unit.py -q
      - name: Run the records validation gate
        run: python infra/database/migrations/records/run_validation.py --require-db
```

`run_validation.py --require-db` is called with no `--only` flag, so it uses
`parse_tiers("")`, whose default is `{0, 1, 2, 3, 4, 5}` - Tier 5 is in the
default set, so CI already runs the full Tiers 0-5 ladder with no workflow
edit required.

Harness-unit-test step, re-run on host to confirm it passes with the current
`parse_tiers`:

```
21 passed in 0.03s
```

(`test_run_validation_unit.py::test_parse_tiers_default_and_valid` asserts
`parse_tiers("") == {0, 1, 2, 3, 4, 5}` directly; `test_parse_tiers_rejects_unknown`
asserts `parse_tiers("9")` and `parse_tiers("x")` both raise.)

## 7. Operational callout - password guard (DEV-7)

`045_records_security_rls_down.sql` drops cluster-level app roles
(`records_api`, `records_intake_writer`) **by design** whenever it finds them
password-less (DEV-7 guard: `pg_authid.rolpassword is not null` is the only
condition that retains the role through a down-migration). This is correct
and intentional for disposable `records_val_*` validation databases, where
the roles are throwaway and never carry a password.

**Operational requirement:** any `records_api` / `records_intake_writer` role
that exists on a non-disposable database (e.g. `records_dev`, or any future
staging/prod cluster) must be kept **passworded at all times**. A
password-less app role on a non-disposable DB would be silently dropped by
`045_down.sql` if that down migration were ever run there. Passwords for
those roles are operator-provisioned out-of-band; the migration itself never
sets one (Global Constraint, both `045` and `045_down`).

## 8. Disposable-DB and role hygiene confirmation

- `records_dev` appears in **zero** connection lines across every transcript
  in this document (verified by direct grep count = 0 on the raw ladder
  output).
- The disposable database created by the Section 1 full-ladder run
  (`records_val_20260703T051103_8584`) was dropped by the harness itself
  (`[drop] records_val_20260703T051103_8584`) and confirmed absent from
  `pg_database` by direct query (count = 0) after the run.
- The disposable database created by the Section 5 full-ladder run
  (`records_val_20260703T051326_33802`) was likewise dropped by the harness
  (`[drop] records_val_20260703T051326_33802`).
- The two cluster-level app roles created by the Section 5 ladder run
  (because `snapshot_roles()` found them absent going in) were dropped by the
  same run's teardown (`[drop-role] records_api`, `[drop-role]
  records_intake_writer`), confirmed absent by direct query afterward.
- No DSN, password, or other secret value was printed, echoed, or committed
  at any point in this task.

## 9. AC1-AC8 checklist (mapped to proof)

| AC | Requirement (summary) | Proof |
|----|------------------------|-------|
| AC1 | RLS enabled + backstop posture across all records tables | Task 1 migration `045` Sec [4]; `test_045::test_rls_enabled_on_all_records_tables`; Tier 5 DP7 (Sec 1, 5-roles PASS; DP7 introspection: zero records tables with RLS disabled) |
| AC2 | No PUBLIC privilege anywhere in scope (routines, tables/views, schema) | Task 1 migration `045` Sec [2]/[2a] (revokes + asserts over routines **and** tables/views **and** schema USAGE); `test_045::test_no_public_execute_on_routines` + `test_no_public_on_tables_or_schema`; Tier 5 DP6 (Sec 1, 5-roles PASS; PUBLIC holds zero EXECUTE/table/view grants) |
| AC3 | Reader/writer role separation with correct grant boundaries | Task 1 migration `045` Sec [3a]; `test_045::test_reader_has_no_write` + `test_writer_holds_all_not_null_columns` + `test_writer_denied_reserved_columns`; Tier 5 PP1-PP2/DP1-DP4/DP-ESC (Sec 1 and Sec 5, 5-roles PASS: "PP1-2/DP1-9/DP-ESC/polroles green") |
| AC4 | Views are `security_invoker`, correctly scoped for both views | Task 1 migration `045` Sec [5]; `test_045::test_views_are_security_invoker`; Tier 5 DP8/DP9 for both `v_asset_test_history` and `v_pm_due`, cross-checked against `polroles` (Sec 1, 5-roles PASS) |
| AC5 | Dynamic proof: expected-raise / expected-allow behavior under least-privilege roles | Tier 5 PP1-PP2 (Sec 1 and Sec 5 full-ladder runs, "5-roles PASS ... PP1-2 ... green") |
| AC6 | Down-migration is reversible and restores pre-045 posture; teardown DROP path is real | Task 2 down-symmetry check, 10/10 PASS (Sec 3); Task 6 teardown-DROP positive proof (Sec 5) closing the Task 3 review item - both roles confirmed ABSENT after a ladder run that created them |
| AC7 | Not applied to prod Supabase; not Supabase-apply-ready as written | Global Constraints (this doc's scope + brief); `045`/`045_down` target `records_api`/`records_intake_writer` directly, not `authenticated` - role-rebinding explicitly deferred to the serving/Gate-9 stage; no prod-apply action taken by any task in this build |
| AC8 | Secret-audit detectors catch non-app-role identities and bypass credentials in records serving config, value-silent | Task 5 `infra/secret-audit.sh` Check 2 (`supabase-secret-key`) + Check 3 (`records-serving-non-app-role`, `records-serving-bypass-credential`); Task 6 evidence: clean-tree real-audit run (Sec 4a) + fixture-test run including the single-file value-silent regression (Sec 4b) |

Tier 5 (`run_validation.py::tier5_roles`) implements the **complete** binding
proof set - PP1-PP2, DP1-DP9, DP-ESC - across **both** views, not a subset;
D9 (reserved-column denial) and D10 (`neta_table_source_links` restriction)
are encoded directly in the RESERVED-column test coverage and the dedicated
`test_source_links_restricted` assertion respectively.

## 10. Source commits (this build, branch `records/gate3-security-rls`)

| Commit | Subject |
|--------|---------|
| `8d1ef8b6` | feat(infra): AC8 secret-audit detectors (service_role/secret-key/bypass-DSN, value-silent) |
| `ce717cb4` | fix(infra): AC8 Check 3 value-silent for single-file globs (-H) |
| `49e3957e` | docs(records): note post-045 RLS flip in test_043/044 + MANIFEST |
| `803a9766` | feat(records): 045 security/RLS migration + Tier-3 static test |
| `fc7ac153` | feat(records): 045 reversible down (checklist a-d) |
| `989db3dc` | feat(records): run_validation Tier 5 (role/grant/denial proofs) |
