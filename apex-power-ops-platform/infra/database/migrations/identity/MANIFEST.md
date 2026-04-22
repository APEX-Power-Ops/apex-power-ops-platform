# Identity Domain SQL Migration Manifest
## Packet: 2026-04-14-pm-schema-012b
## Target: Local PostgreSQL staging database `apex_pm_stage`

## Execution Order

Execute these files in strict sequential order against the target database:

| Order | File | Contents | Dependencies |
| --- | --- | --- | --- |
| 1 | `001_identity_schema.sql` | `identity` schema creation | None |
| 2 | `002_identity_tables.sql` | 3 core tables with PKs, internal FK, UNIQUE constraints | Requires 001 (schema) |
| 3 | `003_identity_triggers.sql` | `updated_at` auto-maintenance trigger function + 3 triggers | Requires 002 (tables) |

## Quick Execution

```bash
# Execute in order against the existing staging database
psql -d apex_pm_stage -f 001_identity_schema.sql
psql -d apex_pm_stage -f 002_identity_tables.sql
psql -d apex_pm_stage -f 003_identity_triggers.sql
```

## Object Summary

| Category | Count | Details |
| --- | --- | --- |
| Schema | 1 | `identity` |
| Enum types | 0 | None required for minimum design |
| Tables | 3 | users, employees, crews |
| Internal FKs | 1 | employees.user_id -> users |
| UNIQUE constraints | 3 | users.email, employees.employee_code, crews.crew_code |
| Trigger functions | 1 | identity.fn_set_updated_at |
| Triggers | 3 | updated_at on all 3 tables |

## Relationship to PM/Work Domain

This identity bundle does NOT activate any PM/work foreign keys. The six deferred FK columns in `work.work_packages`, `work.assignments`, `work.execution_issues`, and `work.progress_snapshots` remain as bare UUID columns. FK activation is deferred to packet 012d after seed-data population (012c).

| Deferred PM/Work FK | Target | Activation Packet |
| --- | --- | --- |
| `work.work_packages.assigned_crew_id` | `identity.crews` | 012d |
| `work.assignments.employee_id` | `identity.employees` | 012d |
| `work.assignments.crew_id` | `identity.crews` | 012d |
| `work.execution_issues.reported_by` | `identity.users` | 012d |
| `work.execution_issues.assigned_to` | `identity.users` | 012d |
| `work.progress_snapshots.approved_by` | `identity.users` | 012d |

## Clean Rebuild (identity only)

```bash
# Drop identity schema and recreate
psql -d apex_pm_stage -c "DROP SCHEMA IF EXISTS identity CASCADE;"
psql -d apex_pm_stage -f 001_identity_schema.sql
psql -d apex_pm_stage -f 002_identity_tables.sql
psql -d apex_pm_stage -f 003_identity_triggers.sql
```
