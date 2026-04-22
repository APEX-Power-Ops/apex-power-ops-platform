-- =============================================================================
-- 008_work_identity_fk_activation.sql
-- PM Schema Packet 012d — Activate 6 Deferred Identity Foreign Keys
-- =============================================================================
-- Activates the six cross-schema FK constraints from work.work_packages,
-- work.assignments, work.execution_issues, and work.progress_snapshots
-- into the identity schema tables created by packet 012b and populated by
-- packet 012c.
--
-- Prerequisites:
--   - identity schema exists with 3 tables (users, employees, crews)
--   - seed data covers all non-NULL employee_id/crew_id/user_id values in work tables
--   - all 3 coverage verification queries from packet 012a §5.4 return zero
--     orphaned rows
--
-- Constraints activated (6 total):
--   work.work_packages     → identity.crews     (assigned_crew_id, nullable)
--   work.assignments       → identity.employees (employee_id, nullable)
--   work.assignments       → identity.crews     (crew_id, nullable)
--   work.execution_issues  → identity.users     (reported_by, nullable)
--   work.execution_issues  → identity.users     (assigned_to, nullable)
--   work.progress_snapshots → identity.users    (approved_by, nullable)
-- =============================================================================

-- ---------- work.work_packages → identity.crews ----------
ALTER TABLE work.work_packages
  ADD CONSTRAINT fk_work_packages_assigned_crew
  FOREIGN KEY (assigned_crew_id) REFERENCES identity.crews (crew_id);

-- ---------- work.assignments → identity.employees ----------
ALTER TABLE work.assignments
  ADD CONSTRAINT fk_assignments_employee
  FOREIGN KEY (employee_id) REFERENCES identity.employees (employee_id);

-- ---------- work.assignments → identity.crews ----------
ALTER TABLE work.assignments
  ADD CONSTRAINT fk_assignments_crew
  FOREIGN KEY (crew_id) REFERENCES identity.crews (crew_id);

-- ---------- work.execution_issues → identity.users (reported_by) ----------
ALTER TABLE work.execution_issues
  ADD CONSTRAINT fk_execution_issues_reported_by
  FOREIGN KEY (reported_by) REFERENCES identity.users (user_id);

-- ---------- work.execution_issues → identity.users (assigned_to) ----------
ALTER TABLE work.execution_issues
  ADD CONSTRAINT fk_execution_issues_assigned_to
  FOREIGN KEY (assigned_to) REFERENCES identity.users (user_id);

-- ---------- work.progress_snapshots → identity.users (approved_by) ----------
ALTER TABLE work.progress_snapshots
  ADD CONSTRAINT fk_progress_snapshots_approved_by
  FOREIGN KEY (approved_by) REFERENCES identity.users (user_id);
