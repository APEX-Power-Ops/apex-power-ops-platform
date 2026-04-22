-- =============================================================================
-- Identity Domain -- Core Tables
-- Packet: 2026-04-14-pm-schema-012b
-- Authority: 2026-04-14-pm-schema-012a-identity-domain-schema-design-handoff.md §3
-- Landing Lane: infra/database/migrations/identity/
--
-- Dependency order:
--   users -> employees (employees.user_id FK -> users)
--   crews (standalone)
--
-- These tables define the minimum identity entities required to support
-- deferred PM/work foreign keys:
--   work.execution_issues.reported_by   -> identity.users
--   work.execution_issues.assigned_to   -> identity.users
--   work.progress_snapshots.approved_by -> identity.users
--   work.assignments.employee_id        -> identity.employees
--   work.work_packages.assigned_crew_id -> identity.crews
--   work.assignments.crew_id            -> identity.crews
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. users — platform actors for workflow actions
-- ---------------------------------------------------------------------------

CREATE TABLE identity.users (
    user_id         uuid            NOT NULL DEFAULT gen_random_uuid(),
    email           text            NOT NULL,
    display_name    text            NOT NULL,
    is_active       boolean         NOT NULL DEFAULT true,
    created_at      timestamptz     NOT NULL DEFAULT now(),
    updated_at      timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT uq_users_email UNIQUE (email)
);

COMMENT ON TABLE identity.users IS
    'Platform user identity. Referenced by execution_issues (reported_by, assigned_to) '
    'and progress_snapshots (approved_by). Minimum viable actor record for PM/work workflows.';

-- ---------------------------------------------------------------------------
-- 2. employees — field workers assigned to work packages and tasks
-- ---------------------------------------------------------------------------

CREATE TABLE identity.employees (
    employee_id     uuid            NOT NULL DEFAULT gen_random_uuid(),
    user_id         uuid            NULL,
    employee_code   text            NOT NULL,
    first_name      text            NOT NULL,
    last_name       text            NOT NULL,
    job_title       text            NULL,
    is_active       boolean         NOT NULL DEFAULT true,
    created_at      timestamptz     NOT NULL DEFAULT now(),
    updated_at      timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_employees PRIMARY KEY (employee_id),
    CONSTRAINT uq_employees_employee_code UNIQUE (employee_code),
    CONSTRAINT fk_employees_user
        FOREIGN KEY (user_id) REFERENCES identity.users (user_id)
);

COMMENT ON TABLE identity.employees IS
    'Field worker identity for labor assignments. Referenced by work.assignments.employee_id. '
    'Nullable user_id allows employees without platform login accounts.';
COMMENT ON COLUMN identity.employees.user_id IS
    'Links employee to platform user account. Nullable — not every field worker has system access.';
COMMENT ON COLUMN identity.employees.employee_code IS
    'Badge number or HR identifier. Natural key for external system matching.';

-- ---------------------------------------------------------------------------
-- 3. crews — named work groups for crew-level assignment
-- ---------------------------------------------------------------------------

CREATE TABLE identity.crews (
    crew_id         uuid            NOT NULL DEFAULT gen_random_uuid(),
    crew_code       text            NOT NULL,
    name            text            NOT NULL,
    is_active       boolean         NOT NULL DEFAULT true,
    created_at      timestamptz     NOT NULL DEFAULT now(),
    updated_at      timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_crews PRIMARY KEY (crew_id),
    CONSTRAINT uq_crews_crew_code UNIQUE (crew_code)
);

COMMENT ON TABLE identity.crews IS
    'Named work crew for crew-level assignment. Referenced by work.work_packages.assigned_crew_id '
    'and work.assignments.crew_id. Crew membership derived from work.assignments records.';
