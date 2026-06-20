-- ============================================================================
-- learning migration 001 -- person bridge (public.user_profiles.employee_id).
-- Phase-5 additive identity slice / learning Slice 2a.
-- Authority: docs/superpowers/specs/2026-06-20-learning-slice2-capture-path-design.md;
--            .claude/PLATFORM/INTEGRATION_BACKBONE_IDENTITY_CONTRACT_2026-06-20.md (C1/D2).
-- Dev DB: learning_dev (apply is an operator-gated step; tests use learning_test). Nothing to prod.
-- Mirrors the column the prod migration additive_person_spine_prod already added to
-- public.user_profiles -- but here it is a cross-DB CONTRACT-FK to prod public.employees.id
-- (app-enforced, NO db FK: employees lives in a different database).
-- ============================================================================

alter table public.user_profiles
  add column if not exists employee_id uuid null;   -- contract-FK -> prod public.employees.id (NOT a db FK)

create unique index if not exists uq_user_profiles_employee_id
  on public.user_profiles (employee_id) where employee_id is not null;

comment on column public.user_profiles.employee_id is
  'Cross-DB contract-FK to prod public.employees.id; app-enforced, no DB FK (employees is a separate database). Learning Slice 2a.';
