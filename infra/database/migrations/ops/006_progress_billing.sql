-- ============================================================================
-- UP -- ops Chip 4 progress billing scaffold.
-- Adds: retainage_pct column on projects; billing_application_status enum;
--       billing_application, billing_application_line, billing_application_draft tables;
--       indexes uq_billapp_issued_ref, uq_billline_active_event + supporting indexes.
-- Triggers/functions/views added by Tasks 2-9.
-- ============================================================================

-- 6a. retainage_pct on projects
alter table ops.projects
  add column retainage_pct numeric(6,5) not null default 0
    check (retainage_pct >= 0 and retainage_pct < 1);

-- 6b. status enum (no draft -- drafts are a separate table)
create type ops.billing_application_status as enum ('issued','voided');

-- 6c. billing_application (the financial record -- always issued | voided)
create table ops.billing_application (
  id                    uuid primary key default gen_random_uuid(),
  project_id            uuid not null references ops.projects(id),
  application_no        int  not null,
  status                ops.billing_application_status not null default 'issued',
  period_through        date not null,
  external_invoice_ref  text not null,
  billable_hours        numeric(14,2) not null,
  gross_amount          numeric(14,2) not null,
  positive_gross        numeric(14,2) not null,
  retainage_withheld    numeric(14,2) not null default 0,
  retainage_released    numeric(14,2) not null default 0,
  retainage_drawn       numeric(14,2) not null default 0,
  net_invoiced          numeric(14,2) not null,
  actor_person_id       uuid not null references ops.persons(person_id),
  issued_at             timestamptz not null default now(),
  voided_at             timestamptz,
  voided_by             uuid references ops.persons(person_id),
  void_reason           text,
  created_at            timestamptz not null default now(),

  constraint uq_billapp_project_no unique (project_id, application_no),
  constraint ck_billapp_ref_nonblank check (btrim(external_invoice_ref) <> ''),
  constraint ck_billapp_void_shape check (
    status <> 'voided'
    or (voided_at is not null and voided_by is not null
        and void_reason is not null and btrim(void_reason) <> '')),
  constraint ck_billapp_retainage_nonneg check (
    retainage_withheld >= 0 and retainage_released >= 0 and retainage_drawn >= 0),
  constraint ck_billapp_withheld_cap check (retainage_withheld <= positive_gross),
  constraint ck_billapp_net check (
    net_invoiced = gross_amount - retainage_withheld + retainage_released + retainage_drawn)
);

-- no two ISSUED apps may record the same RESA invoice ref for a project (voided refs may be re-used)
create unique index uq_billapp_issued_ref
  on ops.billing_application (project_id, lower(btrim(external_invoice_ref))) where status = 'issued';

-- 6d. billing_application_line (membership marker + line-grain retainage)
create table ops.billing_application_line (
  id                   uuid primary key default gen_random_uuid(),
  application_id       uuid not null references ops.billing_application(id),
  recognition_event_id uuid not null references ops.revenue_recognition_event(id),
  event_type           ops.recognition_event_type not null,
  apparatus_id         uuid not null references ops.apparatus(id),
  scope_id             uuid not null references ops.scopes(id),
  project_id           uuid not null references ops.projects(id),
  amount               numeric(14,2) not null,
  billable_hours       numeric(14,2) not null,
  retainage_withheld   numeric(14,2) not null default 0,
  retainage_released   numeric(14,2) not null default 0,
  is_voided            boolean not null default false,
  created_at           timestamptz not null default now(),
  constraint ck_billline_retainage_nonneg check (retainage_withheld >= 0 and retainage_released >= 0)
);

create unique index uq_billline_active_event
  on ops.billing_application_line (recognition_event_id) where is_voided = false;

create index ix_billline_app on ops.billing_application_line(application_id);
create index ix_billline_apparatus on ops.billing_application_line(apparatus_id);
create index ix_billline_scope on ops.billing_application_line(scope_id);

-- 6e. billing_application_draft (saved intent -- NOT a financial record)
create table ops.billing_application_draft (
  id                       uuid primary key default gen_random_uuid(),
  project_id               uuid not null references ops.projects(id),
  period_through           date not null,
  exclude_apparatus_ids    uuid[] not null default '{}',
  retainage_draw_request   numeric(14,2) not null default 0,
  external_invoice_ref     text,
  actor_person_id          uuid not null references ops.persons(person_id),
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);

-- ============================================================================
-- Task 2: function-only mutation gate + immutability triggers (sec 8.0/8.1/8.2)
-- ============================================================================

-- 8.1 Header immutability + void cascade (also carries §8.0 gate for INSERT path;
--     Task 3 will extend this function with insert-integrity logic)
-- before insert or update or delete on ops.billing_application
create or replace function ops.trg_billapp_immutable()
returns trigger language plpgsql as $$
begin
  -- 8.0 gate: every mutation trigger checks the billing-context flag first
  if current_setting('ops.billing_ctx', true) is distinct from '1' then
    raise exception 'ops billing tables are function-only (set ops.billing_ctx)';
  end if;

  -- INSERT: gate only (Task 3 adds insert-integrity logic here)
  if tg_op = 'INSERT' then
    return new;
  end if;

  -- DELETE is never permitted on billing_application
  if tg_op = 'DELETE' then
    raise exception 'billing_application rows are immutable -- DELETE is not permitted';
  end if;

  -- UPDATE: only issued->voided transition writing exactly status/voided_at/voided_by/void_reason
  if tg_op = 'UPDATE' then
    if not (
      old.status = 'issued'
      and new.status = 'voided'
      and new.project_id              = old.project_id
      and new.application_no          = old.application_no
      and new.period_through          = old.period_through
      and new.external_invoice_ref    = old.external_invoice_ref
      and new.billable_hours          = old.billable_hours
      and new.gross_amount            = old.gross_amount
      and new.positive_gross          = old.positive_gross
      and new.retainage_withheld      = old.retainage_withheld
      and new.retainage_released      = old.retainage_released
      and new.retainage_drawn         = old.retainage_drawn
      and new.net_invoiced            = old.net_invoiced
      and new.actor_person_id         = old.actor_person_id
      and new.issued_at               = old.issued_at
      and new.created_at              = old.created_at
      and new.voided_at    is not null
      and new.voided_by    is not null
      and new.void_reason  is not null
    ) then
      raise exception 'billing_application is immutable -- only issued->voided transition is permitted '
                      '(fields: status, voided_at, voided_by, void_reason)';
    end if;

    -- cascade the line-void: all active lines for this application become voided
    update ops.billing_application_line
       set is_voided = true
     where application_id = old.id
       and is_voided = false;
  end if;

  return new;
end;
$$;

create trigger trg_billapp_immutable
  before insert or update or delete on ops.billing_application
  for each row execute function ops.trg_billapp_immutable();

-- 8.2 Line immutability (also carries §8.0 gate for INSERT path;
--     Task 4 will extend this function with insert-integrity logic)
-- before insert or update or delete on ops.billing_application_line
create or replace function ops.trg_billline_immutable()
returns trigger language plpgsql as $$
begin
  -- 8.0 gate
  if current_setting('ops.billing_ctx', true) is distinct from '1' then
    raise exception 'ops billing tables are function-only (set ops.billing_ctx)';
  end if;

  -- INSERT: gate only (Task 4 adds insert-integrity logic here)
  if tg_op = 'INSERT' then
    return new;
  end if;

  -- DELETE is never permitted
  if tg_op = 'DELETE' then
    raise exception 'billing_application_line rows are immutable -- DELETE is not permitted';
  end if;

  -- UPDATE: only is_voided false->true
  if tg_op = 'UPDATE' then
    if not (old.is_voided = false and new.is_voided = true
            and new.application_id       = old.application_id
            and new.recognition_event_id = old.recognition_event_id
            and new.event_type           = old.event_type
            and new.apparatus_id         = old.apparatus_id
            and new.scope_id             = old.scope_id
            and new.project_id           = old.project_id
            and new.amount               = old.amount
            and new.billable_hours       = old.billable_hours
            and new.retainage_withheld   = old.retainage_withheld
            and new.retainage_released   = old.retainage_released
            and new.created_at           = old.created_at) then
      raise exception 'billing_application_line is immutable -- only is_voided false->true is permitted';
    end if;
  end if;

  return new;
end;
$$;

create trigger trg_billline_immutable
  before insert or update or delete on ops.billing_application_line
  for each row execute function ops.trg_billline_immutable();

-- 8.0 Draft gate (insert/update/delete on billing_application_draft: gate only)
create or replace function ops.trg_billdraft_gate()
returns trigger language plpgsql as $$
begin
  if current_setting('ops.billing_ctx', true) is distinct from '1' then
    raise exception 'ops billing tables are function-only (set ops.billing_ctx)';
  end if;
  return new;
end;
$$;

create trigger trg_billdraft_gate
  before insert or update or delete on ops.billing_application_draft
  for each row execute function ops.trg_billdraft_gate();
