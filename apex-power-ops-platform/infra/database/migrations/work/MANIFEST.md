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
# Re-execute all 5 files in order
```
