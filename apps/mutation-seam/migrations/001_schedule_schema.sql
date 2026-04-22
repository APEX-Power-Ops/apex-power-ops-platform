-- ============================================================================
-- APEX Packet UI-002a — P6 schedule-context read bridge
-- Migration: 001_schedule_schema.sql
-- Created:   2026-04-17
-- ============================================================================
-- Creates a parallel `schedule` schema that lands P6-derived planning context
-- alongside the governed `seam` schema created in packet UI-001e.
--
-- Design posture:
--   * Read-only from the application's perspective. The mutation seam does NOT
--     write to `schedule.*`; writes happen only via the out-of-band P6 import
--     loader (apps/mutation-seam/app/schedule/loader.py).
--   * No foreign keys into `seam.*`, `work.*`, `org.*`, or `identity.*`. The
--     link from `schedule.tasks.scope_id` -> `seam.tasks.id` is a soft text
--     reference resolved in the bridge layer at read time. This preserves the
--     PM/work domain as canonical owner of execution truth per the UI Source-
--     Of-Truth memo §3 (WBS is planning support, not authority).
--   * TEXT primary keys for consistency with the seam prototype.
--   * P6 identifiers kept as first-class columns for round-trip with XER.
--
-- Re-runnable: every CREATE uses IF NOT EXISTS so this migration is safe to
-- re-apply. Use DROP SCHEMA schedule CASCADE to reset in a dev environment.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS schedule;

-- ---------------------------------------------------------------------------
-- Projects: one row per imported P6 PROJECT entry.
-- data_date is the P6 status date at import time — every derived schedule
-- health signal (overdue, critical-path, slippage) is interpreted relative to
-- this date.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedule.projects (
    id                TEXT PRIMARY KEY,          -- e.g. "sched-proj-001"
    p6_project_id     TEXT NOT NULL UNIQUE,      -- XER proj_id, e.g. "123456"
    name              TEXT NOT NULL,
    scope_project_id  TEXT,                      -- soft link -> seam.projects.id
    data_date         TIMESTAMPTZ,               -- P6 status/data date
    planned_start     TIMESTAMPTZ,
    planned_finish    TIMESTAMPTZ,
    actual_start      TIMESTAMPTZ,
    actual_finish     TIMESTAMPTZ,
    must_finish_by    TIMESTAMPTZ,
    last_imported_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_file       TEXT,                      -- basename of XER file, or 'json-fixture'
    data              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_schedule_projects_p6_id
    ON schedule.projects (p6_project_id);
CREATE INDEX IF NOT EXISTS idx_schedule_projects_scope
    ON schedule.projects (scope_project_id);

COMMENT ON TABLE  schedule.projects IS
    'Imported P6 PROJECT rows. Read-only from the app; written only by the schedule loader.';
COMMENT ON COLUMN schedule.projects.scope_project_id IS
    'Soft text link to seam.projects.id. Not a FK — seam remains canonical.';

-- ---------------------------------------------------------------------------
-- WBS nodes: hierarchical planning structure from P6 PROJWBS.
-- Self-referencing parent_wbs_id models the tree; level/seq are convenience
-- fields for display ordering.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedule.wbs_nodes (
    id                TEXT PRIMARY KEY,          -- e.g. "sched-wbs-001"
    p6_wbs_id         TEXT NOT NULL UNIQUE,
    schedule_project_id TEXT NOT NULL REFERENCES schedule.projects(id) ON DELETE CASCADE,
    parent_wbs_id     TEXT,                      -- references schedule.wbs_nodes.id (self); no FK to keep load ordering simple
    name              TEXT NOT NULL,
    short_name        TEXT,
    seq               INTEGER,
    level             INTEGER,
    data              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_schedule_wbs_project
    ON schedule.wbs_nodes (schedule_project_id);
CREATE INDEX IF NOT EXISTS idx_schedule_wbs_parent
    ON schedule.wbs_nodes (parent_wbs_id);

COMMENT ON TABLE schedule.wbs_nodes IS
    'Imported P6 PROJWBS rows — planning support hierarchy, not execution authority.';

-- ---------------------------------------------------------------------------
-- Tasks: one row per imported P6 TASK. Holds planning dates, float, status
-- and critical-flag. scope_id is a soft link to seam.tasks.id; the bridge
-- uses it for joined reads but neither schema owns the other's truth.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedule.tasks (
    id                TEXT PRIMARY KEY,          -- e.g. "sched-task-001"
    p6_task_id        TEXT NOT NULL UNIQUE,
    schedule_project_id TEXT NOT NULL REFERENCES schedule.projects(id) ON DELETE CASCADE,
    schedule_wbs_id   TEXT REFERENCES schedule.wbs_nodes(id),
    scope_id          TEXT,                      -- soft link -> seam.tasks.id (PM/work canonical)
    p6_status         TEXT,                      -- raw XER status (TK_NotStart, TK_Active, TK_Complete)
    apex_status       TEXT,                      -- enum-translated (not_started | active | complete)
    task_code         TEXT,                      -- P6 activity ID (e.g. "A1010")
    task_name         TEXT NOT NULL,
    task_type         TEXT,                      -- TT_Task | TT_Mile | TT_FinMile | TT_LOE | TT_Rsrc
    duration_hours    NUMERIC(10, 2),
    planned_start     TIMESTAMPTZ,
    planned_finish    TIMESTAMPTZ,
    actual_start      TIMESTAMPTZ,
    actual_finish     TIMESTAMPTZ,
    total_float_hours NUMERIC(10, 2),
    free_float_hours  NUMERIC(10, 2),
    critical_flag     BOOLEAN NOT NULL DEFAULT FALSE,
    constraint_type   TEXT,                      -- CS_MEO, CS_MSO, etc.
    constraint_date   TIMESTAMPTZ,
    data              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_schedule_tasks_project
    ON schedule.tasks (schedule_project_id);
CREATE INDEX IF NOT EXISTS idx_schedule_tasks_wbs
    ON schedule.tasks (schedule_wbs_id);
CREATE INDEX IF NOT EXISTS idx_schedule_tasks_scope
    ON schedule.tasks (scope_id);
CREATE INDEX IF NOT EXISTS idx_schedule_tasks_status
    ON schedule.tasks (apex_status);
CREATE INDEX IF NOT EXISTS idx_schedule_tasks_critical
    ON schedule.tasks (critical_flag)
    WHERE critical_flag = TRUE;

COMMENT ON COLUMN schedule.tasks.apex_status IS
    'Enum-translated status per APEX_Schema_V2/P6_Enum_Alignment.md. Derived-only display states (overdue, at-risk) are NOT stored here — they are computed at read time.';
COMMENT ON COLUMN schedule.tasks.scope_id IS
    'Soft link to seam.tasks.id. PM/work domain remains canonical owner of execution truth.';

-- ---------------------------------------------------------------------------
-- Relationships: imported from P6 TASKPRED. FS/SS/FF/SF with lag.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedule.relationships (
    id                   TEXT PRIMARY KEY,       -- e.g. "sched-rel-001"
    p6_taskpred_id       TEXT NOT NULL UNIQUE,
    schedule_project_id  TEXT NOT NULL REFERENCES schedule.projects(id) ON DELETE CASCADE,
    predecessor_task_id  TEXT NOT NULL REFERENCES schedule.tasks(id) ON DELETE CASCADE,
    successor_task_id    TEXT NOT NULL REFERENCES schedule.tasks(id) ON DELETE CASCADE,
    rel_type             TEXT NOT NULL,          -- FS | SS | FF | SF
    lag_hours            NUMERIC(10, 2) NOT NULL DEFAULT 0,
    data                 JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT rel_type_valid CHECK (rel_type IN ('FS', 'SS', 'FF', 'SF')),
    CONSTRAINT no_self_reference CHECK (predecessor_task_id <> successor_task_id)
);

CREATE INDEX IF NOT EXISTS idx_schedule_rel_pred
    ON schedule.relationships (predecessor_task_id);
CREATE INDEX IF NOT EXISTS idx_schedule_rel_succ
    ON schedule.relationships (successor_task_id);
CREATE INDEX IF NOT EXISTS idx_schedule_rel_project
    ON schedule.relationships (schedule_project_id);

COMMENT ON TABLE schedule.relationships IS
    'Imported P6 TASKPRED rows. FS/SS/FF/SF with signed lag (negative = lead).';

-- ---------------------------------------------------------------------------
-- Sync log: append-only record of every import run. This is the integration
-- ledger — per the Source-Of-Truth memo §3, the UI may display sync status
-- but may NOT treat sync log entries as business-completion proof.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedule.sync_log (
    id                TEXT PRIMARY KEY,          -- e.g. "sync-<iso8601>-<uuid>"
    source_type       TEXT NOT NULL,             -- 'xer' | 'json-fixture'
    source_file       TEXT NOT NULL,
    data_date         TIMESTAMPTZ,               -- echoed from schedule.projects for quick filter
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at       TIMESTAMPTZ,
    status            TEXT NOT NULL DEFAULT 'in_progress', -- in_progress | success | failed
    stats             JSONB NOT NULL DEFAULT '{}'::jsonb,   -- {projects: n, wbs: n, tasks: n, relationships: n}
    error_text        TEXT,
    CONSTRAINT status_valid CHECK (status IN ('in_progress', 'success', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_schedule_sync_started
    ON schedule.sync_log (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_schedule_sync_status
    ON schedule.sync_log (status);

COMMENT ON TABLE schedule.sync_log IS
    'Integration ledger. UI may surface sync state but may not use it as completion proof.';

-- ============================================================================
-- END of 001_schedule_schema.sql
-- ============================================================================
