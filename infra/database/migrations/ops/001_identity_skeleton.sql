-- ============================================================================
-- ops Chip 1 — identity skeleton (projects / scopes / apparatus / tasks)
-- Lane SSoT:  reference/ops/00-MASTER-INDEX.md
-- Spec:       reference/ops/01-CHIP1-IDENTITY-SPEC.md
-- Dev DB:     ops_dev (local PG). Nothing applied to prod.
-- Model:      public.* conceptual PM core (workbook-verified, SSoT §5a) + seam disciplines.
-- Enums seeded faithfully from the live public.* enums (pulled 2026-06-15).
-- Assumes a clean ops schema (the down migration drops it; the test runs down first).
-- ============================================================================

create schema if not exists ops;

-- ---- enums (values verbatim from live public.* ) ---------------------------
create type ops.project_status        as enum ('Draft','Quoted','Won','Active','On Hold','Complete','Cancelled');
create type ops.scope_status          as enum ('Not Started','In Progress','On Hold','Complete','Cancelled');
create type ops.scope_type            as enum ('ATS','SWGR','XFMR','PDC','MCC','CB','RELAY','CABLE','BATT','UPS','GEN','VFD','CAP','GND','OTHER');
create type ops.apparatus_status      as enum ('Not Started','In Progress','Pending Review','Complete','Cancelled');
create type ops.apparatus_assessment  as enum ('Pass','Fail','Marginal','Needs Repair','Deferred','Not Tested','Acceptable','Non-Serviceable','Minor Deficiency');
create type ops.apparatus_availability as enum ('Ready','On Hold','Not Available');
create type ops.task_status           as enum ('Not Started','In Progress','On Hold','Complete','Cancelled');

-- ---- projects --------------------------------------------------------------
create table ops.projects (
  id                        uuid primary key default gen_random_uuid(),
  project_number            varchar not null unique,
  project_name              varchar not null,
  status                    ops.project_status not null default 'Draft',
  project_type              varchar,
  business_unit             varchar,
  quote_date                date,
  quote_revision            varchar,
  start_date                date,
  end_date                  date,
  contract_value            numeric,                 -- = Sum of scope P4 (set by intake; Chip 2)
  po_number                 varchar,
  project_lead              varchar,
  estimator                 varchar,
  description               text,
  notes                     text,
  total_apparatus_count     int default 0,
  completed_apparatus_count int default 0,
  percent_complete          numeric default 0,
  date_due                  date,
  -- soft refs (D-010 seam; org tables land in a later chip)
  client_ref                uuid,
  site_ref                  uuid,
  location_ref              uuid,
  -- cheap seams + provenance (MASTER §6)
  tenant_id                 uuid,
  source                    text,
  provenance_status         text not null default 'draft',
  legacy_source_id          text,
  created_by                uuid,                    -- -> auth.users (soft; auth schema not on ops_dev)
  updated_by                uuid,
  is_active                 boolean not null default true,
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now()
);

-- ---- scopes ----------------------------------------------------------------
create table ops.scopes (
  id                        uuid primary key default gen_random_uuid(),
  project_id                uuid not null references ops.projects(id) on delete cascade,
  scope_number              varchar,
  scope_name                varchar not null,
  scope_type                ops.scope_type,
  status                    ops.scope_status not null default 'Not Started',
  percent_complete          numeric default 0,
  planned_start             date,
  planned_end               date,
  actual_start              date,
  actual_end                date,
  date_due                  date,
  total_apparatus_count     int default 0,
  completed_apparatus_count int default 0,
  sort_order                int,
  notes                     text,
  client_ref                uuid,
  site_ref                  uuid,
  -- hours / revenue / 4-category / blended rate land in Chip 2-3 (NOT here)
  tenant_id                 uuid,
  source                    text,
  provenance_status         text not null default 'draft',
  legacy_source_id          text,
  created_by                uuid,
  updated_by                uuid,
  is_active                 boolean not null default true,
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now()
);

-- ---- tasks (work-grouping layer; before apparatus for the FK) ---------------
create table ops.tasks (
  id                        uuid primary key default gen_random_uuid(),
  scope_id                  uuid not null references ops.scopes(id) on delete cascade,
  parent_task_id            uuid references ops.tasks(id) on delete set null,
  task_number               varchar,
  task_name                 varchar not null,
  task_type                 varchar,
  status                    ops.task_status not null default 'Not Started',
  percent_complete          numeric default 0,
  estimated_hours           numeric,
  actual_hours              numeric,
  planned_start             date,
  planned_end               date,
  actual_start              date,
  actual_end                date,
  date_due                  date,
  apparatus_count           int default 0,
  sort_order                int,
  description               text,
  notes                     text,
  tenant_id                 uuid,
  source                    text,
  provenance_status         text not null default 'draft',
  legacy_source_id          text,
  created_by                uuid,
  updated_by                uuid,
  is_active                 boolean not null default true,
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now()
);

-- ---- apparatus (THE recognition unit) --------------------------------------
create table ops.apparatus (
  id                        uuid primary key default gen_random_uuid(),
  scope_id                  uuid not null references ops.scopes(id) on delete cascade,  -- Law 1: FIXED binding
  task_id                   uuid references ops.tasks(id) on delete set null,
  apparatus_designation     varchar not null,
  apparatus_name            varchar,
  apparatus_type            varchar,                 -- -> std-hours catalog key (Chip 2)
  manufacturer              varchar,
  model                     varchar,
  serial_number             varchar,
  status                    ops.apparatus_status not null default 'Not Started',
  assessment                ops.apparatus_assessment,
  availability              ops.apparatus_availability,
  percent_complete          numeric default 0,
  anticipated_start         date,
  actual_start              date,
  actual_end                date,
  date_due                  date,
  building                  varchar,
  floor                     varchar,
  room                      varchar,
  drawing_reference         varchar,
  datasheet_complete        boolean default false,
  sort_order                int,
  priority                  int,
  notes                     text,
  tech_notes                text,
  -- Law 5: soft core seam (hard FK to core.equipment_models at co-location)
  equipment_model_ref       uuid,
  -- Law 3 (recognition firewall): NO actual_revenue here; quoted_hours/quoted_revenue land in Chip 2.
  -- cheap seams + provenance (MASTER §6)
  tenant_id                 uuid,
  source                    text,
  provenance_status         text not null default 'draft',
  legacy_source_id          text,
  -- offline-sync reserves (MASTER §6; PowerSync wiring deferred)
  origin_device             text,
  client_rev                bigint,
  client_captured_at        timestamptz,
  synced_at                 timestamptz,
  -- audit (-> auth.users; soft uuid)
  created_by                uuid,
  updated_by                uuid,
  submitted_by              uuid,
  approved_by               uuid,
  is_active                 boolean not null default true,
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now()
);

-- Law 1: apparatus cannot move between scopes (the revenue-recognition anchor is fixed).
create or replace function ops.guard_apparatus_scope_immutable()
returns trigger language plpgsql as $$
begin
  if new.scope_id is distinct from old.scope_id then
    raise exception
      'ops.apparatus.scope_id is immutable (FIXED scope->apparatus binding, SSoT Law 1): % -> %',
      old.scope_id, new.scope_id;
  end if;
  return new;
end;
$$;

create trigger trg_apparatus_scope_immutable
  before update on ops.apparatus
  for each row execute function ops.guard_apparatus_scope_immutable();

-- ---- indexes (FK-supporting) ----------------------------------------------
create index ix_ops_scopes_project   on ops.scopes(project_id);
create index ix_ops_tasks_scope      on ops.tasks(scope_id);
create index ix_ops_tasks_parent     on ops.tasks(parent_task_id);
create index ix_ops_apparatus_scope  on ops.apparatus(scope_id);
create index ix_ops_apparatus_task   on ops.apparatus(task_id);

-- ---- self-documenting comments (the load-bearing laws) ---------------------
comment on schema ops is 'Operations (PM) lane — identity spine. SSoT: reference/ops/00-MASTER-INDEX.md';
comment on column ops.apparatus.scope_id is 'FIXED scope->apparatus binding (SSoT Law 1) — NOT NULL + immutable (trigger). Revenue-recognition anchor.';
comment on column ops.apparatus.equipment_model_ref is 'Soft seam to core.equipment_models (SSoT Law 5); hard FK at co-location.';
comment on table ops.apparatus is 'The recognition unit (operator ruling D-OPS-8). Revenue recognized when each apparatus is complete; recognized $ live in the Chip 3 event ledger, never as a column here (Law 3).';
