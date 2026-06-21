-- ============================================================================
-- ops Chip 3 — recognition ledger (append-only revenue recognition on ops.*).
-- Builds on Chips 1/2/4. Dev DB: ops_dev / ops_test. Nothing applied to prod.
-- Law 3 firewall: recognized $ live ONLY here; frozen quote is read, never mutated.
-- Spec: docs/superpowers/specs/2026-06-21-ops-chip3-recognition-ledger-design.md
-- ============================================================================

create type ops.recognition_event_type as enum ('recognized','reversal');
create type ops.obligation_clearance  as enum ('provided','not_applicable');

create table ops.revenue_recognition_event (
  id                  uuid primary key default gen_random_uuid(),
  apparatus_id        uuid not null references ops.apparatus(id),
  scope_id            uuid not null references ops.scopes(id),
  project_id          uuid not null references ops.projects(id),
  event_type          ops.recognition_event_type not null,
  recognized_amount   numeric not null,                      -- signed; mirrors apparatus.quoted_revenue
  quoted_hours        numeric,                               -- basis snapshot (required on recognized)
  blended_rate        numeric,                               -- basis snapshot (required on recognized)
  basis_frozen_at     timestamptz,                           -- scope_quote.frozen_at (required on recognized)
  assessment          ops.apparatus_assessment,              -- stamped, non-gating
  actor_person_id     uuid not null references ops.persons(person_id),
  datasheet_clearance ops.obligation_clearance,
  datasheet_ref       text,
  cx_clearance        ops.obligation_clearance,
  cx_ref              text,
  reverses_event_id   uuid references ops.revenue_recognition_event(id),
  reason              text,
  recognized_at       timestamptz not null default now(),
  created_at          timestamptz not null default now(),
  constraint ck_revrec_event_shape check (
    case event_type
      when 'recognized' then
        recognized_amount > 0 and reverses_event_id is null
        and datasheet_clearance is not null and cx_clearance is not null
        and quoted_hours is not null and quoted_hours > 0
        and blended_rate is not null and basis_frozen_at is not null
      when 'reversal' then
        recognized_amount < 0 and reverses_event_id is not null
        and reason is not null and btrim(reason) <> ''
    end
  ),
  constraint ck_revrec_datasheet_ref check (
    datasheet_clearance is distinct from 'provided'
    or (datasheet_ref is not null and btrim(datasheet_ref) <> '')
  ),
  constraint ck_revrec_cx_ref check (
    cx_clearance is distinct from 'provided'
    or (cx_ref is not null and btrim(cx_ref) <> '')
  )
);
comment on table ops.revenue_recognition_event is
  'Append-only apparatus-grain recognized-revenue ledger (Chip 3). recognized + reversal as signed rows; net per apparatus = sum(recognized_amount). Law 3 firewall.';

-- append-only: block UPDATE/DELETE
create or replace function ops.trg_revrec_immutable() returns trigger language plpgsql as $$
begin
  raise exception 'ops.revenue_recognition_event is append-only (% blocked)', tg_op;
end;
$$;
create trigger revrec_immutable before update or delete on ops.revenue_recognition_event
  for each row execute function ops.trg_revrec_immutable();

create index ix_revrec_apparatus on ops.revenue_recognition_event(apparatus_id);
create index ix_revrec_scope     on ops.revenue_recognition_event(scope_id);
create index ix_revrec_project   on ops.revenue_recognition_event(project_id);
create unique index uq_revrec_one_reversal
  on ops.revenue_recognition_event(reverses_event_id) where event_type='reversal';
