-- ============================================================================
-- learning migration 001 DOWN -- reverse 001_person_bridge.sql. Drops the bridge column
-- (and its partial-unique index, which the column drop removes). Requires public.user_profiles
-- to exist (the real learning_dev baseline / the test prereq).
-- ============================================================================
drop index if exists public.uq_user_profiles_employee_id;
alter table public.user_profiles drop column if exists employee_id;
