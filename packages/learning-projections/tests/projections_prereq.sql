-- learning_test mini-graph for the projection-engine tests. Built fresh each session.
drop table if exists public.learning_events, public.content_concept_links,
  public.edition_ksa_map, public.ksas, public.concepts,
  public.study_content, public.user_profiles cascade;

do $$ begin
  if not exists (select 1 from pg_type where typname = 'certification_level') then
    create type certification_level as enum ('I','II','III','IV');
  end if;
end $$;

create table public.user_profiles (
  id uuid primary key,
  email text not null default 'seed@example.com',
  full_name text,
  target_certification_level  certification_level,
  current_certification_level certification_level,
  is_active boolean not null default true
);
create table public.study_content (
  id uuid primary key,
  title text,
  neta_section_primary text
);
create table public.concepts (
  concept_id text primary key,
  concept_description text
);
create table public.ksas (
  id uuid primary key default gen_random_uuid(),
  ksa_code varchar unique,
  certification_level certification_level
);
create table public.edition_ksa_map (
  id uuid primary key default gen_random_uuid(),
  concept_id text,
  ksa_code text,
  level text,
  edition text,
  is_active boolean not null default true
);
create table public.content_concept_links (
  id uuid primary key default gen_random_uuid(),
  content_id uuid,
  concept_id text
);

insert into public.user_profiles (id, email, target_certification_level, current_certification_level, is_active) values
  ('11111111-0000-0000-0000-000000000001','t1@x','II',  null, true),
  ('11111111-0000-0000-0000-000000000002','t2@x', null,'III', true),
  ('11111111-0000-0000-0000-000000000003','t3@x', null, null, true),
  ('11111111-0000-0000-0000-000000000004','t4@x','II',  null, true),
  ('11111111-0000-0000-0000-000000000009','t9@x','II',  null, false);

insert into public.study_content (id, title, neta_section_primary) values
  ('22222222-0000-0000-0000-000000000001','Content 1','7.1'),
  ('22222222-0000-0000-0000-000000000002','Content 2','7.2'),
  ('22222222-0000-0000-0000-000000000003','Content 3','7.3');

insert into public.concepts (concept_id, concept_description) values
  ('concept-1','Concept One'),('concept-2','Concept Two'),('concept-3','Concept Three');

insert into public.ksas (ksa_code, certification_level) values
  ('SA1','II'),('SA2','II'),('SA3','II'),('SA4','II'),
  ('SB1','III'),('SB2','III'),('SB3','III'),
  ('SC1','IV'),('SC2','IV');

insert into public.edition_ksa_map (concept_id, ksa_code, level, edition, is_active) values
  ('concept-1','SA1','II','2022', true),
  ('concept-1','SA1','II','2026', true),
  ('concept-1','SA2','II','2026', true),
  ('concept-2','SB1','III','2026', true),
  ('concept-2','SB2','III','2026', true),
  ('concept-2','SA3','II','2026', false),
  ('concept-3','ORPHAN1','II','2026', true);

insert into public.content_concept_links (content_id, concept_id) values
  ('22222222-0000-0000-0000-000000000001','concept-1'),
  ('22222222-0000-0000-0000-000000000001','concept-2'),
  ('22222222-0000-0000-0000-000000000002','concept-3'),
  ('22222222-0000-0000-0000-000000000003','concept-1');
