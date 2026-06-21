-- Slice 2d rehearsal cohort provisioning. Idempotent. Synthetic handles only -- NO PII.
-- Reversal is NON-DESTRUCTIVE (see slice2d_retire_cohort.sql): set is_active=false, NEVER delete
-- (a delete cascades into the append-only learning_events ledger and trips its immutability trigger).
-- Preflight is SELF-SUFFICIENT + idempotent: it creates the certification_level enum and every column
-- this script writes IF MISSING. This is a full no-op on learning_dev (all objects already exist) and
-- bootstraps the minimal learning_test capture fixture (which has only id/email/employee_id).
-- DB-IDENTITY GUARD: refuse to run anywhere but learning_dev/learning_test -- a copied command
-- cannot write outside the lane even if pointed at the wrong connection.
do $$ begin
  if current_database() not in ('learning_dev','learning_test') then
    raise exception 'Slice 2d provisioning refuses to run on %; expected learning_dev/learning_test', current_database();
  end if;
end $$;
do $$ begin
  if not exists (select 1 from pg_type where typname = 'certification_level') then
    create type certification_level as enum ('I','II','III','IV');
  end if;
end $$;
alter table public.user_profiles add column if not exists full_name text;
alter table public.user_profiles add column if not exists role text default 'technician';
alter table public.user_profiles add column if not exists target_certification_level  certification_level;
alter table public.user_profiles add column if not exists current_certification_level certification_level;
alter table public.user_profiles add column if not exists is_active boolean default true;
alter table public.user_profiles add column if not exists employee_id uuid;
alter table public.user_profiles add column if not exists study_preferences jsonb default '{}'::jsonb;

insert into public.user_profiles
  (id, email, full_name, role, target_certification_level, current_certification_level,
   is_active, employee_id, study_preferences)
values
  ('a0000000-2d00-4000-8000-000000000001', 'rehearsal-01@learning.invalid', 'Rehearsal Tech 01',
   'technician', 'III', null, true, null,
   '{"data_fidelity":"rehearsal","acquisition_run_id":"slice2d-rehearsal-01"}'::jsonb)
on conflict (id) do update
  set full_name = excluded.full_name,
      role = excluded.role,
      target_certification_level = excluded.target_certification_level,
      is_active = true,
      study_preferences = excluded.study_preferences;
