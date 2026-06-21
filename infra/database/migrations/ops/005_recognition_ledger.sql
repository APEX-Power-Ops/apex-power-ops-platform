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

-- ---- gated recognition primitive -------------------------------------------
create or replace function ops.approve_and_recognize(
  p_apparatus_id        uuid,
  p_actor_person_id     uuid,
  p_datasheet_clearance ops.obligation_clearance,
  p_datasheet_ref       text,
  p_cx_clearance        ops.obligation_clearance,
  p_cx_ref              text
) returns uuid language plpgsql as $$
declare a record; sq record; v_net numeric; v_id uuid;
begin
  select a2.scope_id, a2.status, a2.is_active, a2.quoted_hours, a2.quoted_revenue, a2.assessment,
         s.project_id, s.is_active as scope_active, s.status as scope_status,
         p.is_active as project_active, p.status as project_status
    into a
    from ops.apparatus a2
    join ops.scopes s   on s.id = a2.scope_id
    join ops.projects p on p.id = s.project_id
   where a2.id = p_apparatus_id
   for update of a2;                                 -- row lock serializes concurrent approvals
  if not found then raise exception 'apparatus % not found', p_apparatus_id; end if;
  if a.status <> 'Complete' then
    raise exception 'apparatus % not testing-complete (status=%)', p_apparatus_id, a.status;
  end if;
  if not (a.is_active and a.scope_active and a.project_active
          and a.scope_status <> 'Cancelled' and a.project_status <> 'Cancelled') then
    raise exception 'apparatus % inactive/cancelled chain cannot recognize', p_apparatus_id;
  end if;
  select sq2.is_frozen, sq2.frozen_at, sq2.blended_rate into sq
    from ops.scope_quote sq2 where sq2.scope_id = a.scope_id;
  if not found or not sq.is_frozen or sq.frozen_at is null then
    raise exception 'scope % quote basis not frozen', a.scope_id;
  end if;
  if a.quoted_hours is null or a.quoted_hours <= 0
     or a.quoted_revenue is null or a.quoted_revenue <= 0 then
    raise exception 'apparatus % invalid quote basis', p_apparatus_id;
  end if;
  if p_datasheet_clearance is null or p_cx_clearance is null then
    raise exception 'both datasheet and cx clearances required';
  end if;
  select coalesce(sum(recognized_amount),0) into v_net
    from ops.revenue_recognition_event where apparatus_id = p_apparatus_id;
  if v_net > 0 then raise exception 'apparatus % already recognized', p_apparatus_id; end if;
  insert into ops.revenue_recognition_event
    (apparatus_id, scope_id, project_id, event_type, recognized_amount,
     quoted_hours, blended_rate, basis_frozen_at, assessment, actor_person_id,
     datasheet_clearance, datasheet_ref, cx_clearance, cx_ref)
  values
    (p_apparatus_id, a.scope_id, a.project_id, 'recognized', a.quoted_revenue,
     a.quoted_hours, sq.blended_rate, sq.frozen_at, a.assessment, p_actor_person_id,
     p_datasheet_clearance, p_datasheet_ref, p_cx_clearance, p_cx_ref)
  returning id into v_id;
  return v_id;
end;
$$;

-- ---- reversal primitive ----------------------------------------------------
create or replace function ops.reverse_recognition(
  p_event_id uuid, p_actor_person_id uuid, p_reason text
) returns uuid language plpgsql as $$
declare e record; v_id uuid;
begin
  if p_reason is null or btrim(p_reason) = '' then raise exception 'reason required for reversal'; end if;
  select apparatus_id, scope_id, project_id, event_type, recognized_amount into e
    from ops.revenue_recognition_event where id = p_event_id for update;
  if not found then raise exception 'event % not found', p_event_id; end if;
  if e.event_type <> 'recognized' then
    raise exception 'can only reverse a recognized event (% is %)', p_event_id, e.event_type;
  end if;
  perform 1 from ops.apparatus where id = e.apparatus_id for update;   -- coordinate with approve
  if exists (select 1 from ops.revenue_recognition_event where reverses_event_id = p_event_id) then
    raise exception 'event % already reversed', p_event_id;
  end if;
  insert into ops.revenue_recognition_event
    (apparatus_id, scope_id, project_id, event_type, recognized_amount,
     actor_person_id, reverses_event_id, reason)
  values
    (e.apparatus_id, e.scope_id, e.project_id, 'reversal', -e.recognized_amount,
     p_actor_person_id, p_event_id, p_reason)
  returning id into v_id;
  return v_id;
end;
$$;

-- ---- insert integrity: direct inserts cannot bypass the function gate -------
create or replace function ops.trg_revrec_insert_integrity() returns trigger language plpgsql as $$
declare v_scope uuid; a record; sq record; orig record;
begin
  -- lineage (all rows)
  select scope_id into v_scope from ops.apparatus where id = new.apparatus_id;
  if not found then raise exception 'apparatus % not found', new.apparatus_id; end if;
  if new.scope_id <> v_scope then raise exception 'scope_id lineage mismatch'; end if;
  if new.project_id <> (select project_id from ops.scopes where id = new.scope_id) then
    raise exception 'project_id lineage mismatch';
  end if;

  if new.event_type = 'recognized' then
    select a2.status, a2.is_active, a2.quoted_hours, a2.quoted_revenue,
           s.is_active as scope_active, s.status as scope_status,
           p.is_active as project_active, p.status as project_status
      into a
      from ops.apparatus a2 join ops.scopes s on s.id=a2.scope_id join ops.projects p on p.id=s.project_id
     where a2.id = new.apparatus_id
     for update of a2;                         -- FIX-A: lock serializes concurrent direct inserts
    if not (a.is_active and a.scope_active and a.project_active
            and a.scope_status <> 'Cancelled' and a.project_status <> 'Cancelled') then
      raise exception 'recognized row for inactive/cancelled chain';
    end if;
    if a.status <> 'Complete' then raise exception 'recognized row for non-complete apparatus'; end if;
    select is_frozen, frozen_at, blended_rate into sq from ops.scope_quote where scope_id = new.scope_id;
    if not found or not sq.is_frozen or sq.frozen_at is null then
      raise exception 'recognized row on unfrozen basis';
    end if;
    if new.recognized_amount is distinct from a.quoted_revenue then  -- FIX-B: null-safe comparison
      raise exception 'recognized_amount must equal apparatus.quoted_revenue';
    end if;
    if new.quoted_hours is distinct from a.quoted_hours
       or new.blended_rate is distinct from sq.blended_rate
       or new.basis_frozen_at is distinct from sq.frozen_at then
      raise exception 'recognized row snapshot does not match current basis';
    end if;
    -- FIX-A: idempotency gate — reject if apparatus already has an open net recognition
    -- (BEFORE INSERT fires before the new row exists, so sum reflects only prior rows)
    if (select coalesce(sum(recognized_amount),0)
          from ops.revenue_recognition_event where apparatus_id = new.apparatus_id) > 0 then
      raise exception 'apparatus % already has an open recognition', new.apparatus_id;
    end if;
  elsif new.event_type = 'reversal' then
    select apparatus_id, recognized_amount into orig
      from ops.revenue_recognition_event where id = new.reverses_event_id and event_type='recognized';
    if not found then raise exception 'reversal target is not a recognized event'; end if;
    if orig.apparatus_id <> new.apparatus_id then raise exception 'reversal apparatus mismatch'; end if;
    if new.recognized_amount <> -orig.recognized_amount then raise exception 'reversal amount must equal -(original)'; end if;
  end if;
  return new;
end;
$$;
create trigger revrec_insert_integrity before insert on ops.revenue_recognition_event
  for each row execute function ops.trg_revrec_insert_integrity();

-- ---- Component 4: recognition-protection guards (reverse-first) -------------
create or replace function ops.trg_apparatus_protect_recognition() returns trigger language plpgsql as $$
declare v_net numeric;
begin
  if (old.status='Complete' and new.status<>'Complete') or (old.is_active and not new.is_active) then
    select coalesce(sum(recognized_amount),0) into v_net
      from ops.revenue_recognition_event where apparatus_id = new.id;
    if v_net > 0 then raise exception 'apparatus % has open recognition; reverse first', new.id; end if;
  end if;
  return new;
end;
$$;
create trigger apparatus_protect_recognition before update on ops.apparatus
  for each row execute function ops.trg_apparatus_protect_recognition();

create or replace function ops.trg_scope_protect_recognition() returns trigger language plpgsql as $$
declare v_net numeric;
begin
  if (old.is_active and not new.is_active) or (new.status='Cancelled' and old.status<>'Cancelled') then
    select coalesce(sum(recognized_amount),0) into v_net
      from ops.revenue_recognition_event where scope_id = new.id;
    if v_net > 0 then raise exception 'scope % has open recognition; reverse first', new.id; end if;
  end if;
  return new;
end;
$$;
create trigger scope_protect_recognition before update on ops.scopes
  for each row execute function ops.trg_scope_protect_recognition();

create or replace function ops.trg_project_protect_recognition() returns trigger language plpgsql as $$
declare v_net numeric;
begin
  if (old.is_active and not new.is_active) or (new.status='Cancelled' and old.status<>'Cancelled') then
    select coalesce(sum(recognized_amount),0) into v_net
      from ops.revenue_recognition_event where project_id = new.id;
    if v_net > 0 then raise exception 'project % has open recognition; reverse first', new.id; end if;
  end if;
  return new;
end;
$$;
create trigger project_protect_recognition before update on ops.projects
  for each row execute function ops.trg_project_protect_recognition();

-- ---- Component 5: frozen-basis immutability (completes the Chip 2 freeze) ---
create or replace function ops.trg_scope_quote_freeze_guard() returns trigger language plpgsql as $$
begin
  if old.is_frozen and (
       new.onsite_labor       is distinct from old.onsite_labor
    or new.offsite_labor      is distinct from old.offsite_labor
    or new.travel             is distinct from old.travel
    or new.outside_services   is distinct from old.outside_services
    or new.unit_multiplier    is distinct from old.unit_multiplier
    or new.pct_adjust         is distinct from old.pct_adjust
    or new.total_quoted_hours is distinct from old.total_quoted_hours
    or new.is_frozen          is distinct from old.is_frozen
    or new.frozen_at          is distinct from old.frozen_at) then
    raise exception 'frozen quote basis is immutable (scope %)', old.scope_id;
  end if;
  return new;
end;
$$;
create trigger scope_quote_freeze_guard before update on ops.scope_quote
  for each row execute function ops.trg_scope_quote_freeze_guard();

create or replace function ops.trg_apparatus_freeze_guard() returns trigger language plpgsql as $$
declare v_frozen boolean;
begin
  if new.quoted_hours   is distinct from old.quoted_hours
     or new.quoted_revenue is distinct from old.quoted_revenue
     or new.quote_line_id  is distinct from old.quote_line_id then
    select is_frozen into v_frozen from ops.scope_quote where scope_id = old.scope_id;
    if coalesce(v_frozen,false) then
      raise exception 'apparatus quote columns immutable once scope quote frozen (apparatus %)', old.id;
    end if;
  end if;
  return new;
end;
$$;
create trigger apparatus_freeze_guard before update on ops.apparatus
  for each row execute function ops.trg_apparatus_freeze_guard();

-- ---- Component 6: views ----------------------------------------------------
create view ops.v_recognition_review_queue as
select a.id as apparatus_id, a.apparatus_designation, a.scope_id, s.project_id,
       a.quoted_revenue, a.quoted_hours, a.date_due, a.assessment
from ops.apparatus a
join ops.scopes s   on s.id = a.scope_id
join ops.projects p on p.id = s.project_id
where a.status='Complete' and a.is_active and s.is_active and p.is_active
  and s.status <> 'Cancelled' and p.status <> 'Cancelled'
  and coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e
               where e.apparatus_id = a.id), 0) <= 0;

create view ops.v_apparatus_recognition as
select a.id as apparatus_id, a.scope_id, a.status, a.quoted_revenue,
       coalesce(n.net, 0) as net_recognized,
       coalesce(n.net, 0) > 0 as is_recognized,
       r.id as recognized_event_id, r.actor_person_id, r.recognized_at,
       r.datasheet_clearance, r.datasheet_ref, r.cx_clearance, r.cx_ref,
       r.quoted_hours, r.blended_rate, r.basis_frozen_at
from ops.apparatus a
left join lateral (
  select sum(recognized_amount) as net from ops.revenue_recognition_event where apparatus_id = a.id
) n on true
left join lateral (
  select e.* from ops.revenue_recognition_event e
  where e.apparatus_id = a.id and e.event_type='recognized'
    and not exists (select 1 from ops.revenue_recognition_event x where x.reverses_event_id = e.id)
  order by e.recognized_at desc limit 1
) r on true;

create view ops.v_scope_recognition as
select s.id as scope_id, s.project_id,
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.scope_id=s.id),0) as recognized_total,
       coalesce((select sum(a.quoted_revenue) from ops.apparatus a where a.scope_id=s.id and a.is_active and a.status <> 'Cancelled'),0) as apparatus_ceiling,  -- FIX-C
       sq.adjusted_total as scope_adjusted_total,
       sq.adjusted_total
         - coalesce((select sum(a.quoted_revenue) from ops.apparatus a where a.scope_id=s.id and a.is_active and a.status <> 'Cancelled'),0) as residual,  -- FIX-C
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.scope_id=s.id),0)
         / NULLIF(coalesce((select sum(a.quoted_revenue) from ops.apparatus a where a.scope_id=s.id and a.is_active and a.status <> 'Cancelled'),0), 0) as pct_of_ceiling,  -- FIX-C
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.scope_id=s.id),0)
         / NULLIF(sq.adjusted_total, 0) as pct_of_scope
from ops.scopes s
join ops.projects p on p.id = s.project_id
left join ops.scope_quote sq on sq.scope_id = s.id
where s.is_active and s.status <> 'Cancelled' and p.is_active and p.status <> 'Cancelled';

create view ops.v_project_recognition as
select p.id as project_id,
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.project_id=p.id),0) as recognized_total,
       coalesce((select sum(a.quoted_revenue) from ops.apparatus a                              -- FIX-C: add scope+cancelled filters
                 join ops.scopes s on s.id=a.scope_id where s.project_id=p.id and a.is_active
                 and s.is_active and s.status <> 'Cancelled' and a.status <> 'Cancelled'),0) as apparatus_ceiling,
       coalesce((select sum(sq.adjusted_total) from ops.scope_quote sq
                 join ops.scopes s on s.id=sq.scope_id
                 where s.project_id=p.id and s.is_active and s.status <> 'Cancelled'),0) as scope_adjusted_total,
       coalesce((select sum(sq.adjusted_total) from ops.scope_quote sq
                 join ops.scopes s on s.id=sq.scope_id
                 where s.project_id=p.id and s.is_active and s.status <> 'Cancelled'),0)
         - coalesce((select sum(a.quoted_revenue) from ops.apparatus a                          -- FIX-C: add scope+cancelled filters
                     join ops.scopes s on s.id=a.scope_id where s.project_id=p.id and a.is_active
                     and s.is_active and s.status <> 'Cancelled' and a.status <> 'Cancelled'),0) as residual,
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.project_id=p.id),0)
         / NULLIF(coalesce((select sum(a.quoted_revenue) from ops.apparatus a                   -- FIX-C: add scope+cancelled filters
                            join ops.scopes s on s.id=a.scope_id where s.project_id=p.id and a.is_active
                            and s.is_active and s.status <> 'Cancelled' and a.status <> 'Cancelled'),0), 0) as pct_of_ceiling,
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.project_id=p.id),0)
         / NULLIF(coalesce((select sum(sq.adjusted_total) from ops.scope_quote sq
                            join ops.scopes s on s.id=sq.scope_id
                            where s.project_id=p.id and s.is_active and s.status <> 'Cancelled'),0), 0) as pct_of_scope
from ops.projects p
where p.is_active and p.status <> 'Cancelled';
