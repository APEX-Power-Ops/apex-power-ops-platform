-- =============================================================================
-- Reverse of 005. Drops the run/job columns (run cols first, then job cols so the
-- 'kind' column is gone before its type), then the job_kind_enum type.
-- The 'awaiting_promotion' value added to job_status_enum is LEFT IN PLACE:
-- Postgres has no DROP VALUE; removing it would require a full type rebuild.
-- It is harmless (unused) — documented deviation from "each file reverses cleanly".
-- =============================================================================
ALTER TABLE jobs.run
  DROP COLUMN IF EXISTS diff_stat,
  DROP COLUMN IF EXISTS branch,
  DROP COLUMN IF EXISTS worktree_path,
  DROP COLUMN IF EXISTS heartbeat_at,
  DROP COLUMN IF EXISTS lease_expires_at;

ALTER TABLE jobs.job
  DROP COLUMN IF EXISTS base_ref,
  DROP COLUMN IF EXISTS max_attempts,
  DROP COLUMN IF EXISTS kind;

DROP TYPE IF EXISTS jobs.job_kind_enum;
