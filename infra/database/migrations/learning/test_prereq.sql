-- Throwaway learning_test bootstrap. Minimal stand-ins for the baseline tables the learning
-- migrations reference (the real learning_dev has the full frozen baseline). Idempotent so the
-- migration- and package-test fixtures can apply it repeatedly.
create table if not exists public.user_profiles (
  id    uuid primary key default gen_random_uuid(),
  email text not null default 'seed@example.com'
);
create table if not exists public.study_content (
  id    uuid primary key default gen_random_uuid(),
  title text
);
insert into public.user_profiles (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'tech1@example.com')
  on conflict (id) do nothing;
insert into public.study_content (id, title) values
  ('00000000-0000-0000-0000-000000000010', 'Seed content')
  on conflict (id) do nothing;
