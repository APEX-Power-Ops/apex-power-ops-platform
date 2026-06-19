-- Minimal public slice for hermetic recognized-revenue tests (DEV ONLY).
-- Apply to a dedicated test DB on host dev-pg, e.g.:
--   docker exec apex-dev-pg psql -U postgres -c "CREATE DATABASE revenue_recognition_test"
--   docker exec -i apex-dev-pg psql -U postgres -d revenue_recognition_test < infra/database/dev-fixtures/pm_public_slice.sql
DO $$ BEGIN
  CREATE TYPE public.apparatus_status AS ENUM ('Not Started','In Progress','Complete');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS public.projects (
  id uuid PRIMARY KEY,
  project_number text,
  project_name text,
  is_active boolean NOT NULL DEFAULT true
);
CREATE TABLE IF NOT EXISTS public.scopes (
  id uuid PRIMARY KEY,
  project_id uuid NOT NULL REFERENCES public.projects(id),
  scope_name text,
  is_active boolean NOT NULL DEFAULT true
);
CREATE TABLE IF NOT EXISTS public.apparatus (
  id uuid PRIMARY KEY,
  scope_id uuid NOT NULL REFERENCES public.scopes(id),
  status public.apparatus_status NOT NULL,
  quoted_revenue numeric NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true
);

TRUNCATE public.apparatus, public.scopes, public.projects CASCADE;

INSERT INTO public.projects (id, project_number, project_name, is_active) VALUES
  ('11111111-1111-1111-1111-111111111111','P-001','Test Project A', true);
INSERT INTO public.scopes (id, project_id, scope_name, is_active) VALUES
  ('22222222-2222-2222-2222-222222222221','11111111-1111-1111-1111-111111111111','Scope One', true),
  ('22222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111','Scope Two', true);
-- Scope One: 3 apparatus, 2 Complete  => quoted 6000, recognized 3000, 50.00%
-- Scope Two: 2 apparatus, 0 Complete  => quoted 5000, recognized 0, 0.00%
INSERT INTO public.apparatus (id, scope_id, status, quoted_revenue, is_active) VALUES
  ('33333333-3333-3333-3333-333333333301','22222222-2222-2222-2222-222222222221','Complete',1000,true),
  ('33333333-3333-3333-3333-333333333302','22222222-2222-2222-2222-222222222221','Complete',2000,true),
  ('33333333-3333-3333-3333-333333333303','22222222-2222-2222-2222-222222222221','In Progress',3000,true),
  ('33333333-3333-3333-3333-333333333304','22222222-2222-2222-2222-222222222222','In Progress',2500,true),
  ('33333333-3333-3333-3333-333333333305','22222222-2222-2222-2222-222222222222','Not Started',2500,true);
