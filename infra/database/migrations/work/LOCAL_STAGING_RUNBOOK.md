# PM/Work Domain — Local PostgreSQL Staging Runbook
## Packet: 2026-04-13-pm-schema-007
## Authority: PM-SCHEMA-V2-LOCAL-POSTGRES-STAGING-DESIGN-2026-04-13.md

## Prerequisites

1. PostgreSQL 14+ installed locally
2. `psql` CLI available on PATH
3. A database superuser or role with `CREATE DATABASE` and `CREATE SCHEMA` privileges

## 1. Create The Staging Database

```bash
createdb apex_pm_stage
```

The staging database is disposable and resettable. It contains only the PM/work domain schema.

## 2. Execute The SQL Bundle

Run from the `infra/database/migrations/work/` directory in strict manifest order:

```bash
cd "c:/APEX Platform/apex-power-ops-platform/infra/database/migrations/work"

psql -d apex_pm_stage -f 001_work_enums.sql
psql -d apex_pm_stage -f 002_work_tables.sql
psql -d apex_pm_stage -f 003_work_indexes.sql
psql -d apex_pm_stage -f 004_work_triggers_and_functions.sql
psql -d apex_pm_stage -f 005_work_views.sql
```

All five files should execute without errors. If any file fails, fix the SQL and rebuild from scratch (see §7).

## 3. Validate Schema Objects Exist

```sql
-- Connect
psql -d apex_pm_stage

-- Check schema
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'work';

-- Check enum types (expect 16)
SELECT typname FROM pg_type
WHERE typnamespace = 'work'::regnamespace AND typtype = 'e'
ORDER BY typname;

-- Check tables (expect 8)
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'work' AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Check views (expect 5)
SELECT table_name FROM information_schema.views
WHERE table_schema = 'work'
ORDER BY table_name;

-- Check indexes (expect 16 script-defined idx_* indexes + PK/UNIQUE auto-indexes)
SELECT indexname FROM pg_indexes WHERE schemaname = 'work' ORDER BY indexname;

-- Check triggers
SELECT trigger_name, event_object_table
FROM information_schema.triggers
WHERE trigger_schema = 'work'
ORDER BY event_object_table, trigger_name;
```

## 4. Validate Constraints

```sql
-- 4.1 CHECK constraints work
-- Projects: end > start
INSERT INTO work.projects (project_code, title, client_id, site_id,
    planned_start_at, planned_end_at)
VALUES ('TEST-CHECK-1', 'Check Test', gen_random_uuid(), gen_random_uuid(),
    '2026-06-01', '2026-05-01');
-- Expected: FAILS with ck_projects_planned_dates violation

-- 4.2 UNIQUE constraints work
INSERT INTO work.projects (project_code, title, client_id, site_id)
VALUES ('PROJ-001', 'First', gen_random_uuid(), gen_random_uuid());
INSERT INTO work.projects (project_code, title, client_id, site_id)
VALUES ('PROJ-001', 'Duplicate', gen_random_uuid(), gen_random_uuid());
-- Expected: FAILS with uq_projects_project_code violation

-- 4.3 FK constraints work
INSERT INTO work.work_packages (project_id, work_package_code, title,
    work_type, client_id, site_id)
VALUES (gen_random_uuid(), 'WP-001', 'Bad FK', 'testing',
    gen_random_uuid(), gen_random_uuid());
-- Expected: FAILS with fk_work_packages_project violation

-- 4.4 Assignments at-least-one-parent CHECK
INSERT INTO work.assignments (assignment_role) VALUES ('primary');
-- Expected: FAILS with ck_assignments_at_least_one_parent

-- 4.5 P6 nullable bindings
INSERT INTO work.projects (project_code, title, client_id, site_id)
VALUES ('PROJ-P6NULL', 'P6 Null Test', gen_random_uuid(), gen_random_uuid());
-- Expected: SUCCEEDS with all p6_* columns as NULL
```

## 5. Validate Triggers And Functions

```sql
-- 5.1 updated_at trigger
INSERT INTO work.projects (project_code, title, client_id, site_id)
VALUES ('PROJ-TRG', 'Trigger Test', gen_random_uuid(), gen_random_uuid());

SELECT created_at, updated_at FROM work.projects WHERE project_code = 'PROJ-TRG';
-- Expected: created_at ≈ updated_at ≈ now()

UPDATE work.projects SET title = 'Updated Title' WHERE project_code = 'PROJ-TRG';
SELECT created_at, updated_at FROM work.projects WHERE project_code = 'PROJ-TRG';
-- Expected: updated_at > created_at, created_at unchanged

-- 5.2 Lifecycle validation (logs NOTICE, does not block)
-- First create a valid project and work package
INSERT INTO work.projects (project_id, project_code, title, client_id, site_id)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'PROJ-LC', 'Lifecycle Test',
    gen_random_uuid(), gen_random_uuid());

INSERT INTO work.work_packages (project_id, work_package_code, title,
    work_type, client_id, site_id)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'WP-LC', 'Lifecycle WP',
    'testing', gen_random_uuid(), gen_random_uuid());
-- lifecycle_state defaults to 'draft'

-- Valid transition: draft → planned
UPDATE work.work_packages SET lifecycle_state = 'planned'
WHERE work_package_code = 'WP-LC';
-- Expected: succeeds silently

-- Invalid transition: planned → complete (skips states)
UPDATE work.work_packages SET lifecycle_state = 'complete'
WHERE work_package_code = 'WP-LC';
-- Expected: succeeds BUT raises a NOTICE about lifecycle violation

-- 5.3 Schedule priority function
SELECT work.fn_compute_schedule_priority(0);     -- Expected: 'critical'
SELECT work.fn_compute_schedule_priority(40);    -- Expected: 'high'
SELECT work.fn_compute_schedule_priority(100);   -- Expected: 'normal'
SELECT work.fn_compute_schedule_priority(200);   -- Expected: 'low'
SELECT work.fn_compute_schedule_priority(NULL);  -- Expected: NULL
```

## 6. Validate Views

```sql
-- Views should be queryable even with no data (return empty result sets)
SELECT * FROM work.v_work_package_status LIMIT 0;
SELECT * FROM work.v_task_schedule LIMIT 0;
SELECT * FROM work.v_wbs_hierarchy LIMIT 0;
SELECT * FROM work.v_execution_issue_dashboard LIMIT 0;
SELECT * FROM work.v_progress_current LIMIT 0;

-- With test data, verify derived columns compute correctly
-- (Use the test project/WP created in §5 above)
SELECT
    work_package_code,
    lifecycle_state,
    is_overdue,
    is_at_risk,
    is_blocked_by_issue,
    active_issue_count,
    task_completion_percent,
    project_title
FROM work.v_work_package_status
WHERE work_package_code = 'WP-LC';
```

## 7. Clean Rebuild Procedure

If any step fails or you need a fresh start:

```bash
dropdb apex_pm_stage
createdb apex_pm_stage
# Re-execute all 5 files in order
```

Rules:
- The staging DB is disposable — never patch manually, always rebuild from SQL files
- Fix defects in the SQL migration files, not by manual database edits
- The SQL files in `infra/database/migrations/work/` are the source of truth

## 8. Environment Variables (Optional)

If your local setup needs explicit connection info:

```bash
export PM_STAGE_DATABASE_URL="postgresql://localhost/apex_pm_stage"
```

This is an implementation/admin env var — do not put it in app runtime config.
