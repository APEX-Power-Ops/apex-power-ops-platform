-- ============================================================================
-- ops Chip 2 — quote model (standard-hours catalog + quote lines + scope quote
--                            + apparatus quote columns).  Builds on Chip 1.
-- Lane SSoT: reference/ops/00-MASTER-INDEX.md  ·  Spec: reference/ops/02-CHIP2-QUOTE-MODEL-SPEC.md
-- Dev DB: ops_dev. Nothing applied to prod.
-- Encodes the workbook-verified revenue model (SSoT §5/§5a):
--   per-project hours are first-class (catalog = default only); accounting enforced
--   by generated columns + a J3 roll-up trigger so it can't drift.
-- ============================================================================

create type ops.test_standard as enum ('ATS','MTS');   -- acceptance vs maintenance

-- ---- standard-hours catalog (universal DEFAULT; Resources-candidate) --------
create table ops.standard_hours (
  id              uuid primary key default gen_random_uuid(),
  apparatus_type  varchar not null,
  test_standard   ops.test_standard not null,
  default_hours   numeric not null,
  neta_section    varchar,
  category        varchar,
  is_active       boolean not null default true,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (apparatus_type, test_standard)
);
comment on table ops.standard_hours is
  'Universal DEFAULT standard hours per apparatus_type x test_standard (SSoT §5a). A SEED only — it never binds a quote; per-project hours live on ops.scope_quote_line. Resources-lane candidate.';

-- ---- quote line (the Estimator line; HOME of per-project hours) -------------
create table ops.scope_quote_line (
  id                    uuid primary key default gen_random_uuid(),
  scope_id              uuid not null references ops.scopes(id) on delete cascade,
  apparatus_type        varchar not null,
  test_standard         ops.test_standard,
  qty                   int not null default 1,
  hrs_per_unit          numeric not null,                 -- per-project; seeded from catalog, OVERRIDABLE
  line_hours            numeric generated always as (qty * hrs_per_unit) stored,
  catalog_default_hours numeric,                           -- the catalog seed (override provenance)
  designation           varchar,
  line_number           int,
  notes                 text,
  provenance_status     text not null default 'draft',
  source                text,
  legacy_source_id      text,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);
comment on column ops.scope_quote_line.hrs_per_unit is
  'Per-project hours/unit. Seeded from ops.standard_hours.default_hours but freely overridable per project (operator ruling 2026-06-15). This is the binding value, not the catalog.';

-- ---- scope quote (1:1 scope; frozen at approval) ---------------------------
create table ops.scope_quote (
  scope_id           uuid primary key references ops.scopes(id) on delete cascade,
  -- the 4 tracked revenue categories (operator: D-OPS-9)
  onsite_labor       numeric not null default 0,
  offsite_labor      numeric not null default 0,
  travel             numeric not null default 0,
  outside_services   numeric not null default 0,
  unit_multiplier    numeric not null default 1,           -- M4
  pct_adjust         numeric not null default 1,           -- N4
  total_quoted_hours numeric not null default 0,           -- J3 (maintained by trigger = Sum line_hours)
  -- derived (generated from base columns only)
  unadjusted_total   numeric generated always as
                       (onsite_labor + offsite_labor + travel + outside_services) stored,                 -- P3
  adjusted_total     numeric generated always as
                       ((onsite_labor + offsite_labor + travel + outside_services) * unit_multiplier * pct_adjust) stored,  -- P4
  blended_rate       numeric generated always as
                       (((onsite_labor + offsite_labor + travel + outside_services) * unit_multiplier * pct_adjust)
                         / nullif(total_quoted_hours, 0)) stored,                                          -- P4 / J3
  is_frozen          boolean not null default false,
  frozen_at          timestamptz,
  provenance_status  text not null default 'draft',
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);
comment on column ops.scope_quote.blended_rate is
  'Single blended $/app-hour = P4 / J3 (operator D-OPS-4). Generated; absorbs all adders + external costs.';

-- J3 roll-up: keep scope_quote.total_quoted_hours = Sum(scope_quote_line.line_hours).
create or replace function ops.maintain_scope_quote_hours()
returns trigger language plpgsql as $$
begin
  if tg_op in ('UPDATE','DELETE') and old.scope_id is not null then
    update ops.scope_quote
       set total_quoted_hours = coalesce(
             (select sum(line_hours) from ops.scope_quote_line where scope_id = old.scope_id), 0)
     where scope_id = old.scope_id;
  end if;
  if tg_op in ('INSERT','UPDATE') and new.scope_id is not null then
    update ops.scope_quote
       set total_quoted_hours = coalesce(
             (select sum(line_hours) from ops.scope_quote_line where scope_id = new.scope_id), 0)
     where scope_id = new.scope_id;
  end if;
  return null;
end;
$$;

create trigger trg_scope_quote_line_hours
  after insert or update or delete on ops.scope_quote_line
  for each row execute function ops.maintain_scope_quote_hours();

-- ---- apparatus quote columns (the Chip 1 deferrals) ------------------------
alter table ops.apparatus
  add column quoted_hours   numeric,                        -- inherited from its line (frozen)
  add column quoted_revenue numeric,                        -- frozen snapshot (populated at approval)
  add column quote_line_id  uuid references ops.scope_quote_line(id) on delete set null;

-- ---- live quote-revenue view (serving + verification) ----------------------
create view ops.v_apparatus_quote as
select a.id           as apparatus_id,
       a.scope_id     as scope_id,
       a.quoted_hours as quoted_hours,
       sq.blended_rate as blended_rate,
       (a.quoted_hours * sq.blended_rate) as quoted_revenue
from ops.apparatus a
join ops.scope_quote sq on sq.scope_id = a.scope_id;

-- ---- indexes ---------------------------------------------------------------
create index ix_ops_scope_quote_line_scope on ops.scope_quote_line(scope_id);
create index ix_ops_apparatus_quote_line   on ops.apparatus(quote_line_id);
