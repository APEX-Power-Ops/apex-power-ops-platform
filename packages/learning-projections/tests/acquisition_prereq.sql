-- Slice 2d fixture extension over the 2b mini-graph: bring user_profiles to learning_dev parity
-- (role / employee_id / study_preferences) and add the negative-control subjects. learning_test only.
alter table public.user_profiles add column if not exists role text default 'technician';
alter table public.user_profiles add column if not exists employee_id uuid;
alter table public.user_profiles add column if not exists study_preferences jsonb default '{}'::jsonb;

-- Negative controls: a leveled user with NO content-linked evidence, and a Level-I user (0 KSAs).
insert into public.user_profiles (id, email, target_certification_level, is_active) values
  ('a0000000-2d00-4000-8000-000000000002','neg-noevidence@learning.invalid','III', true),
  ('a0000000-2d00-4000-8000-000000000003','neg-leveli@learning.invalid','I', true)
on conflict (id) do nothing;
