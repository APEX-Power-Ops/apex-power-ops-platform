-- ============================================================================
-- APEX Packet 020c — Persisted schedule baseline DDL and loader lane
-- Migration: 002_schedule_baseline.sql
-- Created:   2026-04-17
-- ============================================================================
-- Lands the bounded persisted baseline lane authorized by packet 020a
-- (field authority) and packet 020b (XER mapping authority). This migration
-- extends the `schedule` schema only.
--
-- Scope
--   * Adds baseline columns to `schedule.tasks`:
--       baseline_start_at, baseline_end_at, baseline_name, baseline_source,
--       baselined_at, baseline_event_id
--   * Creates `schedule.baseline_events` as the integration ledger for
--     baselining events (one row per authorized baselining action).
--   * Adds supporting indexes and CHECK constraints.
--
-- Out of scope (per packet 020c prompt + write_scope)
--   * WorkPackage baseline. `schedule.*` has no workpackages table today;
--     landing WP baseline requires a separate authority decision on its
--     physical home and is deferred to a later packet.
--   * Any bridge route changes. No GET endpoint reads these columns yet.
--   * Any UI / Gantt render changes.
--   * Any touch on `seam.*`, `work.*`, `org.*`, `identity.*`.
--
-- Re-runnability
--   * Every DDL statement uses IF NOT EXISTS. Safe to re-apply.
--   * The migration does NOT populate baseline data; the loader (packet 020c
--     loader extension) does that, and only from authorized baseline sources
--     per 020b §3-§5.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- schedule.baseline_events — integration ledger for baselining events
-- ---------------------------------------------------------------------------
-- One row per authorized baselining action. A baselining action can be:
--   * 'p6_import'       — baseline truth landed from a P6 XER whose
--                         PROJBASELINE row linked a baseline project to
--                         the live project (per 020b §3).
--   * 'internal_capture' — baseline truth captured by an authorized RESA
--                         actor at a declared baselining event (per 020a
--                         §3.6). Implementation of that path is a future
--                         packet; the event row is supported here.
--   * 'rebaseline'      — a subsequent authorized re-baselining event
--                         whose non-NULL overwrite behavior must honor
--                         020b §5.3.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS schedule.baseline_events (
    id                     TEXT PRIMARY KEY,          -- e.g. "blev-<iso8601>-<uuid>"
    schedule_project_id    TEXT NOT NULL REFERENCES schedule.projects(id) ON DELETE CASCADE,
    baseline_source        TEXT NOT NULL,
    baseline_name          TEXT NOT NULL,             -- P6 PROJBASELINE label or RESA-internal label
    p6_baseline_proj_id    TEXT,                      -- set only when baseline_source='p6_import'
    source_file            TEXT,
    captured_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    captured_by_actor_id   TEXT,                      -- nullable: null for p6_import, required by app logic for internal_capture
    status                 TEXT NOT NULL DEFAULT 'in_progress',
    stats                  JSONB NOT NULL DEFAULT '{}'::jsonb,  -- e.g. {matched_tasks: n, unmatched_baseline_tasks: n}
    error_text             TEXT,
    CONSTRAINT baseline_events_source_valid
        CHECK (baseline_source IN ('p6_import', 'internal_capture', 'rebaseline')),
    CONSTRAINT baseline_events_status_valid
        CHECK (status IN ('in_progress', 'success', 'failed')),
    CONSTRAINT baseline_events_p6_proj_only_when_p6
        CHECK (
            (baseline_source = 'p6_import' AND p6_baseline_proj_id IS NOT NULL)
            OR (baseline_source <> 'p6_import')
        )
);

CREATE INDEX IF NOT EXISTS idx_sched_baseline_events_proj
    ON schedule.baseline_events (schedule_project_id);
CREATE INDEX IF NOT EXISTS idx_sched_baseline_events_source
    ON schedule.baseline_events (baseline_source);
CREATE INDEX IF NOT EXISTS idx_sched_baseline_events_captured_at
    ON schedule.baseline_events (captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_sched_baseline_events_status
    ON schedule.baseline_events (status);

COMMENT ON TABLE schedule.baseline_events IS
    'Append-only ledger of authorized baselining events. One row per baselining action. Referenced by schedule.tasks.baseline_event_id.';
COMMENT ON COLUMN schedule.baseline_events.baseline_source IS
    '''p6_import'' | ''internal_capture'' | ''rebaseline'' — authorized by 020a §3.6 and 020b §3.';
COMMENT ON COLUMN schedule.baseline_events.p6_baseline_proj_id IS
    'PROJECT.proj_id of the baseline PROJECT in the XER, linked via PROJBASELINE. Required when baseline_source=''p6_import'' per 020b §3.3.';

-- ---------------------------------------------------------------------------
-- schedule.tasks — add baseline columns
-- ---------------------------------------------------------------------------
-- Shape per 020a §3.1 (Task promotion) and 020a §3.6 (provenance guidance).
-- All columns are nullable — NULL distinguishes "no baseline captured" from
-- "baselined to this value" (020a §3.4).
-- ---------------------------------------------------------------------------

ALTER TABLE schedule.tasks
    ADD COLUMN IF NOT EXISTS baseline_start_at   TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS baseline_end_at     TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS baseline_name       TEXT,
    ADD COLUMN IF NOT EXISTS baseline_source     TEXT,
    ADD COLUMN IF NOT EXISTS baselined_at        TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS baseline_event_id   TEXT;

-- FK to the event ledger. ON DELETE SET NULL: event purges don't delete
-- baseline dates, they just lose the event pointer. (The app/loader is
-- expected to keep baseline_event_id populated for all non-NULL baselines
-- it writes; this is a belt-and-suspenders rule.)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'schedule_tasks_baseline_event_fk'
    ) THEN
        ALTER TABLE schedule.tasks
            ADD CONSTRAINT schedule_tasks_baseline_event_fk
            FOREIGN KEY (baseline_event_id)
            REFERENCES schedule.baseline_events (id)
            ON DELETE SET NULL;
    END IF;
END$$;

-- CHECK: baseline_source whitelist mirrors baseline_events.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'schedule_tasks_baseline_source_valid'
    ) THEN
        ALTER TABLE schedule.tasks
            ADD CONSTRAINT schedule_tasks_baseline_source_valid
            CHECK (
                baseline_source IS NULL
                OR baseline_source IN ('p6_import', 'internal_capture', 'rebaseline')
            );
    END IF;
END$$;

-- CHECK: the three baseline fields move together. Either all of
-- (baseline_start_at, baseline_end_at, baseline_source, baselined_at) are
-- NULL or all non-NULL. baseline_name and baseline_event_id may be NULL
-- only in the legacy pre-ledger state (future packets MUST populate them;
-- this migration does not).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'schedule_tasks_baseline_coherent'
    ) THEN
        ALTER TABLE schedule.tasks
            ADD CONSTRAINT schedule_tasks_baseline_coherent
            CHECK (
                (baseline_start_at IS NULL AND baseline_end_at IS NULL
                    AND baseline_source IS NULL AND baselined_at IS NULL)
                OR (baseline_start_at IS NOT NULL AND baseline_end_at IS NOT NULL
                    AND baseline_source IS NOT NULL AND baselined_at IS NOT NULL)
            );
    END IF;
END$$;

-- CHECK: finish strictly after start.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'schedule_tasks_baseline_dates_ordered'
    ) THEN
        ALTER TABLE schedule.tasks
            ADD CONSTRAINT schedule_tasks_baseline_dates_ordered
            CHECK (
                baseline_start_at IS NULL
                OR baseline_end_at IS NULL
                OR baseline_end_at > baseline_start_at
            );
    END IF;
END$$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sched_tasks_baseline_event
    ON schedule.tasks (baseline_event_id)
    WHERE baseline_event_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sched_tasks_baseline_source
    ON schedule.tasks (baseline_source)
    WHERE baseline_source IS NOT NULL;

-- Comments
COMMENT ON COLUMN schedule.tasks.baseline_start_at IS
    'Frozen planned start at the baselining event. Per 020a §3.1 + §3.4: optional; written only by the authorized baselining path; NULL means no baseline captured.';
COMMENT ON COLUMN schedule.tasks.baseline_end_at IS
    'Frozen planned end at the baselining event.';
COMMENT ON COLUMN schedule.tasks.baseline_name IS
    'Human-readable baseline label (P6 PROJBASELINE.base_type_name or RESA-internal label per 020b §4.4).';
COMMENT ON COLUMN schedule.tasks.baseline_source IS
    '''p6_import'' | ''internal_capture'' | ''rebaseline''. Matches schedule.baseline_events.baseline_source.';
COMMENT ON COLUMN schedule.tasks.baselined_at IS
    'Timestamp of the baselining event. Distinct from last_imported_at (which updates on every planning-refresh import).';
COMMENT ON COLUMN schedule.tasks.baseline_event_id IS
    'Pointer into schedule.baseline_events for full provenance.';

-- ============================================================================
-- END of 002_schedule_baseline.sql
-- ============================================================================
