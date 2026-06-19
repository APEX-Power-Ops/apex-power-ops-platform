-- =============================================================================
-- jobs 005 — durability + agent columns (requires 001-004). Additive: kind
-- defaults to 'command', so existing command jobs are untouched.
-- NOTE: ALTER TYPE ... ADD VALUE must NOT run inside an explicit txn block.
-- psql -f (no --single-transaction) autocommits each statement, and no later
-- statement in this file uses the new value, so this is safe as written.
-- =============================================================================

-- New job kind: command (today) vs agent (headless claude -p in a worktree).
CREATE TYPE jobs.job_kind_enum AS ENUM ('command', 'agent');

-- Post-run review pause, distinct from the pre-exec 'awaiting_approval'.
ALTER TYPE jobs.job_status_enum ADD VALUE IF NOT EXISTS 'awaiting_promotion';

ALTER TABLE jobs.job
  ADD COLUMN kind         jobs.job_kind_enum NOT NULL DEFAULT 'command',
  ADD COLUMN max_attempts int                NOT NULL DEFAULT 1,
  ADD COLUMN base_ref     text;   -- branch agent work merges into on promotion

ALTER TABLE jobs.run
  ADD COLUMN lease_expires_at timestamptz,   -- visibility timeout (crash recovery)
  ADD COLUMN heartbeat_at     timestamptz,   -- liveness during long agent runs
  ADD COLUMN worktree_path    text,          -- isolated worktree for an agent run
  ADD COLUMN branch           text,          -- job/<dispatch_id> branch
  ADD COLUMN diff_stat        text;          -- git diff --stat of the agent's work
