# Records Validation Harness - Evidence Record (2026-07)

Lane: records/validation-harness. Spec: docs/superpowers/specs/2026-07-02-records-validation-harness-design.md (rev 3).

## AC1 - full host run (disposable DB only)

The full 5-tier run against a disposable records_val_* database on the canonical
host. The [connect] lines show only two dbnames throughout the run: postgres
(admin connections for CREATE/DROP) and the single disposable
records_val_20260702T213901_49578 (all test-tier connections). The final tier4
block issues [connect] dbname=postgres followed by [drop]
records_val_20260702T213901_49578, confirming the disposable database is
restored to nothing at the end of the run.

```
--- tier1 (rc=0) ---
...........                                                              [100%]
--- tier2 (rc=0) ---
.........                                                                [100%]
[connect] dbname=postgres
[connect] dbname=records_val_20260702T213901_49578
--- test_005_neta_reference.py (rc=0) ---
.........                                                                [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_007_asset_class_shell.py (rc=0) ---
.............                                                            [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_008_backfill.py (rc=0) ---
........                                                                 [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_010_lv_cb_template.py (rc=0) ---
.................                                                        [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_011_mvhv_cb_template.py (rc=0) ---
.....................                                                    [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_012_xfmr_template.py (rc=0) ---
.................                                                        [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_013_switchgear_template.py (rc=0) ---
...............                                                          [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_014_cable_template.py (rc=0) ---
.............                                                            [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_015_it_template.py (rc=0) ---
.................                                                        [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_016_grounding_template.py (rc=0) ---
.............                                                            [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_017_surge_template.py (rc=0) ---
................                                                         [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_018_motor_template.py (rc=0) ---
..............                                                           [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_019_motor_starter_template.py (rc=0) ---
..............                                                           [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_020_xfmr_capture_mode.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_021_xfmr_pf_readings.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_022_it_pf_readings.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_023_transfer_switch_template.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_024_ups_template.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_025_battery_template.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_026_charger_template.py (rc=0) ---
.....                                                                    [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_027_switch_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_028_meter_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_029_engine_generator_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_030_busway_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_031_cap_bank_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_032_outdoor_bus_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_033_reactor_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_034_ngr_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_035_circuit_switcher_template.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_036_voltage_regulator_template.py (rc=0) ---
.......                                                                  [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_037_load_tap_changer_template.py (rc=0) ---
.......                                                                  [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_038_neta_tables_standard.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_039_xfmr_neta_standards.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_040_neta_standards_scaleout.py (rc=0) ---
......                                                                   [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_041_form_submission_standard.py (rc=0) ---
...                                                                      [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_042_network_protector_template.py (rc=0) ---
..........                                                               [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_043_neta_table_source_links.py (rc=0) ---
..........................                                               [100%]
[connect] dbname=records_val_20260702T213901_49578
[connect] dbname=records_val_20260702T213901_49578
--- test_044_person_anchor.py (rc=0) ---
.........                                                                [100%]
[connect] dbname=records_val_20260702T213901_49578
--- tier4 (rc=0) ---
.......                                                                  [100%]
[connect] dbname=postgres
[drop] records_val_20260702T213901_49578

=== records validation summary ===
  0-syntax         PASS  compileall + origin asserts
  1-converters     PASS  pytest rc=0
  2-import-pure    PASS  pytest rc=0
  3-migrations     PASS  44 applied, 38 tests executed, 0 skipped
  4-import-db      PASS  3 DB test files, pytest rc=0
executed test files: 41
runner rc=0
```

## AC3 red proof 1 - withheld migration fails the completeness preflight

Scratch copy of the worktree at /tmp/rvh-redproof with
infra/database/migrations/records/031_cap_bank_template.sql removed (the
matching 031_cap_bank_template_down.sql was left in place). The Tier 3
completeness preflight detects the sequence gap and fails before any
CREATE DATABASE is attempted: rc=1, and a post-run check of the canonical
host (docker exec apex-dev-pg psql -U postgres -lqt | grep records_val)
returned zero rows, confirming no disposable database was created.

```
   Building records-import @ file:///tmp/rvh-redproof/packages/records-import
   Building power-test-converters @ file:///tmp/rvh-redproof/packages/power-test-converters
      Built power-test-converters @ file:///tmp/rvh-redproof/packages/power-test-converters
      Built records-import @ file:///tmp/rvh-redproof/packages/records-import
Installed 10 packages in 3ms
--- tier1 (rc=0) ---
...........                                                              [100%]
--- tier2 (rc=0) ---
.........                                                                [100%]

=== records validation summary ===
  0-syntax         PASS  compileall + origin asserts
  1-converters     PASS  pytest rc=0
  2-import-pure    PASS  pytest rc=0
  3-migrations     FAIL  migration sequence gap: missing [31]
executed test files: 0
rc=1
```

## AC3 red proof 2 - missing NETA_DATA_DIR fails loudly under --require-db

Run from the real worktree with NETA_DATA_DIR=/nonexistent-neta and
--require-db. The Tier 3 preflight fails naming the missing directory
before any database work begins: rc=1.

```
--- tier1 (rc=0) ---
...........                                                              [100%]
--- tier2 (rc=0) ---
.........                                                                [100%]

=== records validation summary ===
  0-syntax         PASS  compileall + origin asserts
  1-converters     PASS  pytest rc=0
  2-import-pure    PASS  pytest rc=0
  3-migrations     FAIL  NETA_DATA_DIR is not a directory: /nonexistent-neta (set NETA_DATA_DIR to the NETA extracts)
executed test files: 0
rc=1
```

## AC2 - CI run

<appended in the CI task: link to the green Actions run + the executed-counts lines>

## AC4 - fallback removal grep

<appended in the docs task>
