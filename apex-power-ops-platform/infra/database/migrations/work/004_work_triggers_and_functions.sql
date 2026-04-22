-- =============================================================================
-- PM/Work Domain — Triggers and Functions
-- Packet: 2026-04-13-pm-schema-007
-- Authority: PM-DOMAIN-IMPLEMENTATION-READY-SCHEMA-SPEC-2026-04-12.md §7
-- Landing Lane: infra/database/migrations/work/
--
-- DEFERRED ITEMS:
--   - Lifecycle audit event generation (§7.3): DEFERRED because
--     audit.state_transition_events does not yet exist. The trigger can be
--     added in a follow-up migration when the audit domain is available.
--     No PM/work schema changes are required to support it later.
--
--   - Lifecycle transition validation (§7.2): Implemented as a
--     NOTICE-logging trigger per the recommended approach (application-level
--     enforcement with database trigger that logs violations rather than
--     hard-blocking). This allows emergency overrides with audit trail.
--
--   - Progress percent rollup (§7.5): Implemented as a callable function,
--     not as an automatic trigger. Called on demand per spec.
--
--   - Snapshot superseding logic (§7.6): No trigger needed — the spec
--     says original snapshots retain their status. View layer handles
--     presentation of latest-for-period.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 7.1 updated_at Auto-Maintenance (reusable trigger function)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION work.fn_set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION work.fn_set_updated_at() IS
    'Reusable trigger function: sets updated_at = now() on every UPDATE. Spec §7.1.';

-- Apply to all PM/work tables
CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON work.projects
    FOR EACH ROW EXECUTE FUNCTION work.fn_set_updated_at();

CREATE TRIGGER trg_wbs_nodes_updated_at
    BEFORE UPDATE ON work.wbs_nodes
    FOR EACH ROW EXECUTE FUNCTION work.fn_set_updated_at();

CREATE TRIGGER trg_work_packages_updated_at
    BEFORE UPDATE ON work.work_packages
    FOR EACH ROW EXECUTE FUNCTION work.fn_set_updated_at();

CREATE TRIGGER trg_tasks_updated_at
    BEFORE UPDATE ON work.tasks
    FOR EACH ROW EXECUTE FUNCTION work.fn_set_updated_at();

CREATE TRIGGER trg_dependencies_updated_at
    BEFORE UPDATE ON work.dependencies
    FOR EACH ROW EXECUTE FUNCTION work.fn_set_updated_at();

CREATE TRIGGER trg_assignments_updated_at
    BEFORE UPDATE ON work.assignments
    FOR EACH ROW EXECUTE FUNCTION work.fn_set_updated_at();

CREATE TRIGGER trg_execution_issues_updated_at
    BEFORE UPDATE ON work.execution_issues
    FOR EACH ROW EXECUTE FUNCTION work.fn_set_updated_at();

CREATE TRIGGER trg_progress_snapshots_updated_at
    BEFORE UPDATE ON work.progress_snapshots
    FOR EACH ROW EXECUTE FUNCTION work.fn_set_updated_at();

-- ---------------------------------------------------------------------------
-- 7.2 Lifecycle Transition Validation (NOTICE-logging, not hard-blocking)
--
-- Allowed transitions are defined per Packet 002.
-- This trigger logs disallowed transitions as NOTICE rather than raising
-- an exception, allowing emergency overrides while preserving audit trail.
-- ---------------------------------------------------------------------------

-- Helper: returns true if a WP lifecycle transition is in the allowed set
CREATE OR REPLACE FUNCTION work.fn_is_valid_wp_transition(
    from_state work.wp_lifecycle_enum,
    to_state   work.wp_lifecycle_enum
)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT (from_state, to_state) IN (
        -- Packet 002 §4.3 allowed transitions
        ('draft',            'planned'),
        ('draft',            'cancelled'),
        ('planned',          'ready'),
        ('planned',          'draft'),
        ('planned',          'cancelled'),
        ('ready',            'active'),
        ('ready',            'planned'),
        ('ready',            'cancelled'),
        ('active',           'blocked'),
        ('active',           'awaiting_review'),
        ('active',           'cancelled'),
        ('blocked',          'active'),
        ('blocked',          'cancelled'),
        ('awaiting_review',  'complete'),
        ('awaiting_review',  'active'),
        ('complete',         'closed'),
        ('complete',         'active'),          -- reopening
        ('closed',           'active')           -- exceptional reopen
    );
$$;

-- Helper: returns true if a task lifecycle transition is allowed
CREATE OR REPLACE FUNCTION work.fn_is_valid_task_transition(
    from_state work.task_lifecycle_enum,
    to_state   work.task_lifecycle_enum
)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT (from_state, to_state) IN (
        -- Packet 002 §5.3 allowed transitions
        ('not_started',      'ready'),
        ('not_started',      'cancelled'),
        ('ready',            'active'),
        ('ready',            'not_started'),
        ('ready',            'cancelled'),
        ('active',           'on_hold'),
        ('active',           'awaiting_review'),
        ('active',           'cancelled'),
        ('on_hold',          'active'),
        ('on_hold',          'cancelled'),
        ('awaiting_review',  'complete'),
        ('awaiting_review',  'active'),
        ('complete',         'active')           -- reopening
    );
$$;

-- WP lifecycle validation trigger
CREATE OR REPLACE FUNCTION work.fn_validate_wp_lifecycle()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.lifecycle_state IS DISTINCT FROM NEW.lifecycle_state THEN
        IF NOT work.fn_is_valid_wp_transition(OLD.lifecycle_state, NEW.lifecycle_state) THEN
            RAISE NOTICE 'LIFECYCLE_VIOLATION: work_packages id=% transition %→% is not in the allowed set. Proceeding (application-level enforcement expected).',
                NEW.work_package_id, OLD.lifecycle_state, NEW.lifecycle_state;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_work_packages_lifecycle
    BEFORE UPDATE ON work.work_packages
    FOR EACH ROW EXECUTE FUNCTION work.fn_validate_wp_lifecycle();

-- Task lifecycle validation trigger
CREATE OR REPLACE FUNCTION work.fn_validate_task_lifecycle()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.lifecycle_state IS DISTINCT FROM NEW.lifecycle_state THEN
        IF NOT work.fn_is_valid_task_transition(OLD.lifecycle_state, NEW.lifecycle_state) THEN
            RAISE NOTICE 'LIFECYCLE_VIOLATION: tasks id=% transition %→% is not in the allowed set. Proceeding (application-level enforcement expected).',
                NEW.task_id, OLD.lifecycle_state, NEW.lifecycle_state;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_tasks_lifecycle
    BEFORE UPDATE ON work.tasks
    FOR EACH ROW EXECUTE FUNCTION work.fn_validate_task_lifecycle();

-- ---------------------------------------------------------------------------
-- 7.4 Schedule Priority Computation (callable function, not stored)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION work.fn_compute_schedule_priority(
    p_total_float_hours numeric
)
RETURNS work.priority_enum
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT CASE
        WHEN p_total_float_hours IS NULL THEN NULL::work.priority_enum
        WHEN p_total_float_hours = 0     THEN 'critical'::work.priority_enum
        WHEN p_total_float_hours <= 80   THEN 'high'::work.priority_enum
        WHEN p_total_float_hours <= 160  THEN 'normal'::work.priority_enum
        ELSE 'low'::work.priority_enum
    END;
$$;

COMMENT ON FUNCTION work.fn_compute_schedule_priority(numeric) IS
    'Computes schedule priority from float thresholds (0/80/160 hours). Spec §7.4. Thresholds are Phase 1 defaults.';

-- ---------------------------------------------------------------------------
-- 7.5 Progress Percent Rollup (callable function, not automatic trigger)
--
-- Computes work-package progress from child task lifecycle states.
-- Uses a simple completed-tasks / total-tasks ratio for Phase 1.
-- Spec says this must never overwrite an approved ProgressSnapshot value.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION work.fn_compute_wp_progress(
    p_work_package_id uuid
)
RETURNS numeric(5,2)
LANGUAGE sql
STABLE
AS $$
    SELECT CASE
        WHEN COUNT(*) = 0 THEN NULL
        ELSE ROUND(
            100.0 * COUNT(*) FILTER (WHERE lifecycle_state IN ('complete', 'cancelled'))
            / COUNT(*),
            2
        )
    END
    FROM work.tasks
    WHERE work_package_id = p_work_package_id;
$$;

COMMENT ON FUNCTION work.fn_compute_wp_progress(uuid) IS
    'Computes work-package progress percent from child task completion. Callable on demand. Spec §7.5.';
