# PM/Work Domain SQL Migration Manifest
## Packet: 2026-04-13-pm-schema-007
## Target: Local PostgreSQL staging database `apex_pm_stage`

## Execution Order

Execute these files in strict sequential order against the target database:

| Order | File | Contents | Dependencies |
| --- | --- | --- | --- |
| 1 | `001_work_enums.sql` | `work` schema creation + 16 enum types | None |
| 2 | `002_work_tables.sql` | 8 core tables with PKs, internal FKs, CHECK constraints, UNIQUE constraints | Requires 001 (enums) |
| 3 | `003_work_indexes.sql` | Performance indexes on all 8 tables | Requires 002 (tables) |
| 4 | `004_work_triggers_and_functions.sql` | `updated_at` auto-maintenance, lifecycle validation triggers, schedule priority function, progress rollup function | Requires 002 (tables) + 001 (enums) |
| 5 | `005_work_views.sql` | 5 operational views (v_p6_binding_status deferred) | Requires all prior files |
| 6 | `006_migration_infrastructure.sql` | Migration tracking tables | Requires 002 (tables) |
| 7 | `007_work_org_fk_activation.sql` | 6 cross-schema FK constraints (work→org) | Requires 002 (tables) + org schema (011b) + org seed data (011c) |
| 8 | `008_work_identity_fk_activation.sql` | 6 cross-schema FK constraints (work→identity) | Requires 002 (tables) + identity schema (012b) + identity seed data (012c) |
| 9 | `009_pm_idempotency_keys.sql` | Shared-infra `pm.idempotency_keys` durable POST idempotency store | Independent of `work.*`; requires only `gen_random_uuid()` support |
| 10 | `010_tcc_relay_tables.sql` | Tranche 1 relay substrate tables + 2 relay-local enums | Requires 001 (work schema + provenance enums) |
| 11 | `011_tcc_relay_indexes.sql` | Relay lookup and traversal indexes for the Tranche 1 substrate | Requires 010 (relay tables) |
| 12 | `012_tcc_relay_staged_population.sql` | Tranche 2 immutable-snapshot replay into the relay substrate with provenance preservation and TCP normalization | Requires 010/011 + source snapshot `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/` |

## Quick Execution

```bash
# Create the staging database
createdb apex_pm_stage

# Execute in order
psql -d apex_pm_stage -f 001_work_enums.sql
psql -d apex_pm_stage -f 002_work_tables.sql
psql -d apex_pm_stage -f 003_work_indexes.sql
psql -d apex_pm_stage -f 004_work_triggers_and_functions.sql
psql -d apex_pm_stage -f 005_work_views.sql
psql -d apex_pm_stage -f 006_migration_infrastructure.sql
psql -d apex_pm_stage -f 007_work_org_fk_activation.sql
psql -d apex_pm_stage -f 008_work_identity_fk_activation.sql
psql -d apex_pm_stage -f 009_pm_idempotency_keys.sql
psql -d apex_pm_stage -f 010_tcc_relay_tables.sql
psql -d apex_pm_stage -f 011_tcc_relay_indexes.sql
psql -d apex_pm_stage -f 012_tcc_relay_staged_population.sql
```

## Object Summary

| Category | Count | Details |
| --- | --- | --- |
| Schema | 1 | `work` |
| Enum types | 16 | provenance_source, provenance_status, project_status, wp_lifecycle, work_type, priority, billing_state, task_lifecycle, task_type, dependency_type, assignment_role, issue_type, severity, issue_status, resolution_type, snapshot_status |
| Tables | 8 | projects, wbs_nodes, work_packages, tasks, dependencies, assignments, execution_issues, progress_snapshots |
| Indexes | 16 | See 003 for full list |
| Trigger functions | 4 | fn_set_updated_at, fn_validate_wp_lifecycle, fn_validate_task_lifecycle, fn_is_valid_wp_transition + fn_is_valid_task_transition (helper functions) |
| Triggers | 10 | 8 updated_at triggers + 2 lifecycle validation triggers |
| Callable functions | 2 | fn_compute_schedule_priority, fn_compute_wp_progress |
| Views | 5 created, 1 deferred | v_work_package_status, v_task_schedule, v_wbs_hierarchy, v_execution_issue_dashboard, v_progress_current (v_p6_binding_status deferred) |

## Deferred Cross-Domain Dependencies

These are documented in full in 002_work_tables.sql header and the handoff note:

| Deferred item | Reason | Resolution path |
| --- | --- | --- |
| ~~FK → org.clients, org.sites, org.business_units, org.contracts~~ | ~~org schema does not exist~~ | **RESOLVED** by packet 011d (`007_work_org_fk_activation.sql`) |
| ~~FK → identity.users, identity.employees, identity.crews~~ | ~~identity schema does not exist~~ | **RESOLVED** by packet 012d (`008_work_identity_fk_activation.sql`) |
| FK → asset.asset_classes | asset schema does not exist | Add FK when asset domain is created |
| Audit triggers → audit.state_transition_events | audit schema does not exist | Add trigger when audit domain is created |
| v_p6_binding_status view | integration.p6_sync_log does not exist | Create view when integration domain is created |

## Clean Rebuild

```bash
dropdb apex_pm_stage
createdb apex_pm_stage
# Re-execute all 12 files in order
```

## Relay Tranche 1 Additions

Packet `2026-04-30-tcc-relay-tranche-1` adds the following bounded substrate:

| Category | Count | Details |
| --- | --- | --- |
| Enum types | 2 | `relay_range_parent_kind_enum`, `relay_voltage_restraint_kind_enum` |
| Tables | 21 | `tcc_relays`, `tcc_relay_devices`, `tcc_relay_line_sections`, `tcc_relay_td_sections`, `tcc_relay_ranges`, `tcc_relay_discrete_values`, 9 typed family parent tables, 5 typed curve-row tables, `tcc_relay_curve_points_tcp` |
| Indexes | 24 | Relay root/device/section/range indexes, 9 family-parent traversal indexes, TCP curve + point indexes |

Scope note:

- This tranche creates schema substrate only. No data loads, runtime functions, views, triggers, calc-engine surfaces, API surfaces, browser surfaces, or deferred relay enrichment tables are included here.

## Relay Tranche 2 Additions

Packet `2026-04-30-tcc-relay-tranche-2` adds the following bounded replay slice:

| Category | Count | Details |
| --- | --- | --- |
| Replay files | 1 | `012_tcc_relay_staged_population.sql` |
| Snapshot roots | 1 | `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/` |
| Admitted source CSVs | 22 | `Manufacturers`, `Relays`, `RelayDevices`, `RelayLineSection`, `RelayTDSection`, `RelayRanges`, `RelayDiscreteValues`, 9 family parent tables, 5 family child/point tables |

Scope note:

- This tranche replays one immutable relay snapshot into the existing shared-infra substrate, preserving source snapshot ids and rejecting orphan `RelayDevices` rows. It still does not open calc-engine, API, browser, or deferred enrichment surfaces.
