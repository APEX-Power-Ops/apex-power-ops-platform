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
--     Task 4 extended with §8.3 header insert-integrity logic)
-- before insert or update or delete on ops.billing_application
create or replace function ops.trg_billapp_immutable()
returns trigger language plpgsql as $$
declare
  v_max_period   date;
  v_held_to_date numeric(14,2);
begin
  -- 8.0 gate: every mutation trigger checks the billing-context flag first
  if current_setting('ops.billing_ctx', true) is distinct from '1' then
    raise exception 'ops billing tables are function-only (set ops.billing_ctx)';
  end if;

  -- §8.3 INSERT integrity (serialize + validate header invariants)
  if tg_op = 'INSERT' then
    -- Serialize concurrent inserters: project FOR UPDATE
    perform 1 from ops.projects where id = new.project_id for update;

    -- Note: external_invoice_ref non-blank is enforced by ck_billapp_ref_nonblank CHECK constraint;
    -- we do NOT duplicate it here to avoid shadowing the expected CheckViolation error class.

    -- application_no must equal max(existing)+1 for this project
    -- (the project lock above serializes this read)
    declare
      v_next_no int;
    begin
      select coalesce(max(application_no), 0) + 1
        into v_next_no
        from ops.billing_application
       where project_id = new.project_id;
      if new.application_no <> v_next_no then
        raise exception 'application_no must be % for project % (got %)',
                        v_next_no, new.project_id, new.application_no;
      end if;
    end;

    -- period_through must be >= every issued app period_through for this project
    select max(period_through)
      into v_max_period
      from ops.billing_application
     where project_id = new.project_id
       and status = 'issued';
    if v_max_period is not null and new.period_through < v_max_period then
      raise exception 'period_through % is not monotonically increasing (max existing: %)',
                      new.period_through, v_max_period;
    end if;

    -- retainage_drawn upper-bound: must not exceed held_to_date
    -- held_to_date = sum(withheld - released - drawn) over issued apps for this project
    select coalesce(sum(retainage_withheld - retainage_released - retainage_drawn), 0)
      into v_held_to_date
      from ops.billing_application
     where project_id = new.project_id
       and status = 'issued';
    if new.retainage_drawn > v_held_to_date then
      raise exception 'retainage_drawn (%) exceeds held_to_date (%) for project %',
                      new.retainage_drawn, v_held_to_date, new.project_id;
    end if;

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
--     Task 4 extended with §8.4 line insert-integrity logic)
-- before insert or update or delete on ops.billing_application_line
create or replace function ops.trg_billline_immutable()
returns trigger language plpgsql as $$
declare
  v_event        record;
  v_app_project  uuid;
  v_expected_amt numeric(14,2);
  v_expected_hrs numeric(14,2);
  v_orig_line    record;
begin
  -- 8.0 gate
  if current_setting('ops.billing_ctx', true) is distinct from '1' then
    raise exception 'ops billing tables are function-only (set ops.billing_ctx)';
  end if;

  -- §8.4 INSERT integrity (validate line against committed state)
  if tg_op = 'INSERT' then
    -- Event must exist and attributes must match
    select e.id, e.event_type, e.apparatus_id, e.scope_id, e.project_id,
           e.recognized_amount, e.quoted_hours, e.reverses_event_id
      into v_event
      from ops.revenue_recognition_event e
     where e.id = new.recognition_event_id;
    if not found then
      raise exception 'recognition_event_id % does not exist', new.recognition_event_id;
    end if;

    if new.event_type::text <> v_event.event_type::text then
      raise exception 'event_type mismatch: line has % but event has %',
                      new.event_type, v_event.event_type;
    end if;
    if new.apparatus_id <> v_event.apparatus_id then
      raise exception 'apparatus_id mismatch: line has % but event has %',
                      new.apparatus_id, v_event.apparatus_id;
    end if;
    if new.scope_id <> v_event.scope_id then
      raise exception 'scope_id mismatch: line has % but event has %',
                      new.scope_id, v_event.scope_id;
    end if;
    if new.project_id <> v_event.project_id then
      raise exception 'project_id mismatch: line has % but event has %',
                      new.project_id, v_event.project_id;
    end if;

    -- project_id must match the application header
    select project_id into v_app_project
      from ops.billing_application
     where id = new.application_id;
    if not found then
      raise exception 'application_id % does not exist', new.application_id;
    end if;
    if new.project_id <> v_app_project then
      raise exception 'line project_id (%) does not match application project_id (%)',
                      new.project_id, v_app_project;
    end if;

    -- Determine branch: positive (recognized) vs credit (reversal)
    if v_event.reverses_event_id is null then
      -- POSITIVE BRANCH
      -- amount = round(recognized_amount,2) and amount > 0
      v_expected_amt := round(v_event.recognized_amount, 2);
      if v_expected_amt <= 0 then
        raise exception 'positive line amount rounds to <=0 (event %); sub-cent rows must not consume the no-double-bill slot',
                        new.recognition_event_id;
      end if;
      if new.amount <> v_expected_amt then
        raise exception 'amount % does not equal round(recognized_amount,2)=% for event %',
                        new.amount, v_expected_amt, new.recognition_event_id;
      end if;
      if new.amount <= 0 then
        raise exception 'positive line amount must be > 0 (got %)', new.amount;
      end if;

      -- billable_hours = round(quoted_hours,2) for positive
      v_expected_hrs := round(v_event.quoted_hours, 2);
      if new.billable_hours <> v_expected_hrs then
        raise exception 'billable_hours % does not equal round(quoted_hours,2)=% for event %',
                        new.billable_hours, v_expected_hrs, new.recognition_event_id;
      end if;

      -- retainage_released must be 0 for positive line
      if new.retainage_released <> 0 then
        raise exception 'retainage_released must be 0 for a positive line (got %)', new.retainage_released;
      end if;

      -- branch eligibility: event must not be reversed
      if exists (
        select 1 from ops.revenue_recognition_event r
         where r.reverses_event_id = new.recognition_event_id
      ) then
        raise exception 'event % has been reversed -- cannot bill a reversed event',
                        new.recognition_event_id;
      end if;

    else
      -- CREDIT BRANCH (reversal event: reverses_event_id is not null)
      -- amount = -round(orig.recognized_amount,2) and amount < 0
      -- We need the original event for amount + hours
      declare
        v_orig_event record;
      begin
        select e2.recognized_amount, e2.quoted_hours
          into v_orig_event
          from ops.revenue_recognition_event e2
         where e2.id = v_event.reverses_event_id;
        if not found then
          raise exception 'original event % for reversal not found', v_event.reverses_event_id;
        end if;

        v_expected_amt := -round(v_orig_event.recognized_amount, 2);
        if new.amount <> v_expected_amt then
          raise exception 'credit line amount % does not equal -round(orig.recognized_amount,2)=% for reversal event %',
                          new.amount, v_expected_amt, new.recognition_event_id;
        end if;
        if new.amount >= 0 then
          raise exception 'credit line amount must be < 0 (got %)', new.amount;
        end if;

        -- billable_hours = -round(orig.quoted_hours,2) for credit
        v_expected_hrs := -round(v_orig_event.quoted_hours, 2);
        if new.billable_hours <> v_expected_hrs then
          raise exception 'credit billable_hours % does not equal -round(orig.quoted_hours,2)=% for event %',
                          new.billable_hours, v_expected_hrs, new.recognition_event_id;
        end if;
      end;

      -- retainage_released <= original active line retainage_withheld
      select bl.retainage_withheld
        into v_orig_line
        from ops.billing_application_line bl
        join ops.billing_application ba on ba.id = bl.application_id
       where bl.recognition_event_id = v_event.reverses_event_id
         and bl.is_voided = false
         and ba.status = 'issued'
       limit 1;
      if found and new.retainage_released > v_orig_line.retainage_withheld then
        raise exception 'retainage_released (%) exceeds original line retainage_withheld (%) for credit event %',
                        new.retainage_released, v_orig_line.retainage_withheld, new.recognition_event_id;
      end if;

      -- branch eligibility: original event must have an active issued line
      if not exists (
        select 1 from ops.billing_application_line bl
          join ops.billing_application ba on ba.id = bl.application_id
         where bl.recognition_event_id = v_event.reverses_event_id
           and bl.is_voided = false
           and ba.status = 'issued'
      ) then
        raise exception 'credit line: original event % has no active issued line (credit eligibility failed)',
                        v_event.reverses_event_id;
      end if;
    end if;

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

-- ============================================================================
-- Task 3: record_billing_application / issue_billing_application
--         Positive-branch sweep + Chip-3 event FOR UPDATE lock + flag containment.
--         No retainage math (pct=0 in seeds), no credits, no draft path yet.
-- ============================================================================

-- 7b. issue_billing_application -- the core write path.
--     Signature: (p_project_id, p_actor_person_id, p_period_through, p_external_invoice_ref,
--                 p_exclude_apparatus, p_retainage_draw_request)
create or replace function ops.issue_billing_application(
  p_project_id             uuid,
  p_actor_person_id        uuid,
  p_period_through         date,
  p_external_invoice_ref   text,
  p_exclude_apparatus      uuid[]   default '{}',
  p_retainage_draw_request numeric  default 0
) returns uuid language plpgsql as $$
declare
  v_proj            record;
  v_retainage_pct   numeric;
  candidate_ids     uuid[];
  v_app_id          uuid;
  v_app_no          int;
  v_gross           numeric(14,2);
  v_positive_gross  numeric(14,2);
  v_billable_hours  numeric(14,2);
  v_withheld        numeric(14,2);
  v_released        numeric(14,2);
  v_net             numeric(14,2);
  v_cutoff          timestamptz;
  rec               record;
begin
  -- set the billing context flag so the mutation gate permits our inserts
  perform set_config('ops.billing_ctx', '1', true);

  -- 1. Lock the project (serialize Chip-4 vs Chip-4)
  select id, is_active, status, retainage_pct
    into v_proj
    from ops.projects
   where id = p_project_id
   for update;
  if not found then
    perform set_config('ops.billing_ctx', '0', true);
    raise exception 'project % not found', p_project_id;
  end if;
  if not v_proj.is_active or v_proj.status = 'Cancelled' then
    perform set_config('ops.billing_ctx', '0', true);
    raise exception 'project % is inactive or cancelled', p_project_id;
  end if;
  if p_external_invoice_ref is null or btrim(p_external_invoice_ref) = '' then
    perform set_config('ops.billing_ctx', '0', true);
    raise exception 'external_invoice_ref is required for issue';
  end if;

  v_retainage_pct := v_proj.retainage_pct;

  -- 2. Monotonic period: reject if any issued app has period_through > p_period_through
  if exists (
    select 1 from ops.billing_application
     where project_id = p_project_id
       and status = 'issued'
       and period_through > p_period_through
  ) then
    perform set_config('ops.billing_ctx', '0', true);
    raise exception 'period_through % is not monotonically increasing for project %',
                    p_period_through, p_project_id;
  end if;

  -- Phoenix cutoff: events with recognized_at < (period_through+1) day at America/Phoenix midnight
  v_cutoff := (p_period_through + 1)::timestamp at time zone 'America/Phoenix';

  -- 3. Preliminary positive sweep: recognized events not reversed, not already on an active line,
  --    within period cutoff, apparatus not excluded.
  select array_agg(e.id)
    into candidate_ids
    from ops.revenue_recognition_event e
   where e.project_id = p_project_id
     and e.event_type = 'recognized'
     and e.recognized_at < v_cutoff
     -- not reversed
     and not exists (
       select 1 from ops.revenue_recognition_event r
        where r.reverses_event_id = e.id
     )
     -- no active line (is_voided=false on an issued app)
     and not exists (
       select 1 from ops.billing_application_line bl
        join ops.billing_application ba on ba.id = bl.application_id
        where bl.recognition_event_id = e.id
          and bl.is_voided = false
          and ba.status = 'issued'
     )
     -- apparatus not excluded
     and (p_exclude_apparatus is null
          or cardinality(p_exclude_apparatus) = 0
          or e.apparatus_id <> all(p_exclude_apparatus));

  -- 4. Lock the candidate events to close the Chip-3 reversal race.
  --    Deterministic order avoids deadlock (conflicts with reverse_recognition FOR UPDATE).
  if candidate_ids is not null and cardinality(candidate_ids) > 0 then
    perform 1
      from ops.revenue_recognition_event
     where id = any(candidate_ids)
     order by id
     for update;

    -- Re-evaluate eligibility under the lock (a reversal that committed before the lock is now visible)
    select array_agg(e.id)
      into candidate_ids
      from ops.revenue_recognition_event e
     where e.id = any(candidate_ids)
       and not exists (
         select 1 from ops.revenue_recognition_event r
          where r.reverses_event_id = e.id
       )
       and not exists (
         select 1 from ops.billing_application_line bl
          join ops.billing_application ba on ba.id = bl.application_id
          where bl.recognition_event_id = e.id
            and bl.is_voided = false
            and ba.status = 'issued'
       );
  end if;

  -- 8. Nothing-to-bill check (positive branch only; draw cap is a later task)
  if (candidate_ids is null or cardinality(candidate_ids) = 0)
     and p_retainage_draw_request = 0 then
    perform set_config('ops.billing_ctx', '0', true);
    raise exception 'nothing to bill for project %', p_project_id;
  end if;

  -- 9. application_no (under project lock; burned forever)
  select coalesce(max(application_no), 0) + 1
    into v_app_no
    from ops.billing_application
   where project_id = p_project_id;

  -- 5. Build aggregate totals from positive lines (retainage is 0 for now; Task 5/6 fill the math)
  v_gross          := 0;
  v_positive_gross := 0;
  v_billable_hours := 0;
  v_withheld       := 0;
  v_released       := 0;

  if candidate_ids is not null then
    select coalesce(sum(round(e.recognized_amount, 2)), 0),
           coalesce(sum(round(e.recognized_amount, 2)), 0),
           coalesce(sum(round(e.quoted_hours, 2)), 0)
      into v_gross, v_positive_gross, v_billable_hours
      from ops.revenue_recognition_event e
     where e.id = any(candidate_ids);

    -- retainage withheld: round(amount*pct,2) per line then sum
    -- pct=0 in Task 3 seeds so this is 0; guard so it is a no-op when pct=0
    if v_retainage_pct > 0 then
      select coalesce(sum(round(round(e.recognized_amount, 2) * v_retainage_pct, 2)), 0)
        into v_withheld
        from ops.revenue_recognition_event e
       where e.id = any(candidate_ids);
    end if;
  end if;

  -- credit walk: no credits in Task 3 (Tasks 5/6 add the walk)
  -- v_released stays 0

  -- retainage draw: Task 6 caps this; for now just pass it through (pct=0 => withheld=0 => draw stays 0)
  v_net := v_gross - v_withheld + v_released + p_retainage_draw_request;

  -- 10. Insert header
  insert into ops.billing_application (
    project_id, application_no, status, period_through, external_invoice_ref,
    billable_hours, gross_amount, positive_gross,
    retainage_withheld, retainage_released, retainage_drawn,
    net_invoiced, actor_person_id
  ) values (
    p_project_id, v_app_no, 'issued', p_period_through, p_external_invoice_ref,
    v_billable_hours, v_gross, v_positive_gross,
    v_withheld, v_released, p_retainage_draw_request,
    v_net, p_actor_person_id
  ) returning id into v_app_id;

  -- Insert positive lines
  if candidate_ids is not null and cardinality(candidate_ids) > 0 then
    insert into ops.billing_application_line (
      application_id, recognition_event_id, event_type,
      apparatus_id, scope_id, project_id,
      amount, billable_hours,
      retainage_withheld, retainage_released
    )
    select
      v_app_id,
      e.id,
      'recognized'::ops.recognition_event_type,
      e.apparatus_id,
      e.scope_id,
      e.project_id,
      round(e.recognized_amount, 2),
      round(e.quoted_hours, 2),
      case when v_retainage_pct > 0 then round(round(e.recognized_amount, 2) * v_retainage_pct, 2) else 0 end,
      0
    from ops.revenue_recognition_event e
    where e.id = any(candidate_ids);
  end if;

  -- Reset flag before returning
  perform set_config('ops.billing_ctx', '0', true);
  return v_app_id;

exception when others then
  -- On any error: reset flag so it does not linger in explicit transactions.
  -- In a subtransaction (savepoint) the SET CONFIG with is_local=true is rolled back automatically,
  -- so this is belt-and-suspenders for top-level transactions.
  perform set_config('ops.billing_ctx', '0', true);
  raise;
end;
$$;

-- ============================================================================
-- Task 4: §8.5 Deferred consistency constraint trigger
--   Fires AFTER INSERT OR UPDATE on billing_application and billing_application_line,
--   DEFERRABLE INITIALLY DEFERRED (runs at COMMIT).
--   Does NOT check ops.billing_ctx -- the function has already reset it by COMMIT.
--   Asserts for each touched ISSUED application:
--     header.gross_amount        = sum(active lines amount where amount > 0 ... wait, spec says Sigma active)
--     header.positive_gross      = sum(active lines amount where amount > 0)
--     header.billable_hours      = sum(active lines billable_hours)
--     header.retainage_withheld  = sum(active lines retainage_withheld)
--     header.retainage_released  = sum(active lines retainage_released)
--   Asserts for each touched PROJECT:
--     sum(withheld - released - drawn) over issued apps >= 0  (held_to_date >= 0)
-- ============================================================================
create or replace function ops.trg_billing_consistency()
returns trigger language plpgsql as $$
declare
  v_app_id    uuid;
  v_proj_id   uuid;
  v_hdr       record;
  v_sum       record;
  v_held      numeric(14,2);
  touched_app_ids  uuid[];
  touched_proj_ids uuid[];
begin
  -- Collect touched application_ids depending on which table fired
  if tg_table_name = 'billing_application' then
    -- header row: application_id is the row itself
    touched_app_ids  := array[new.id];
    touched_proj_ids := array[new.project_id];
  else
    -- line row: resolve application_id from the line
    touched_app_ids  := array[new.application_id];
    select project_id into v_proj_id
      from ops.billing_application where id = new.application_id;
    touched_proj_ids := array[v_proj_id];
  end if;

  -- Assert header = sum(active lines) for each touched ISSUED application
  foreach v_app_id in array touched_app_ids loop
    -- Only check issued apps (voided are exempt from header=sum-lines)
    select * into v_hdr
      from ops.billing_application
     where id = v_app_id and status = 'issued';
    if not found then
      continue;  -- voided or not found: skip
    end if;

    select
      coalesce(sum(amount), 0)                                  as gross_amount,
      coalesce(sum(amount) filter (where amount > 0), 0)        as positive_gross,
      coalesce(sum(billable_hours), 0)                          as billable_hours,
      coalesce(sum(retainage_withheld), 0)                      as retainage_withheld,
      coalesce(sum(retainage_released), 0)                      as retainage_released
      into v_sum
      from ops.billing_application_line
     where application_id = v_app_id
       and is_voided = false;

    if v_hdr.gross_amount <> v_sum.gross_amount then
      raise exception
        'billing consistency: app % gross_amount (%) != sum of active lines (%)',
        v_app_id, v_hdr.gross_amount, v_sum.gross_amount;
    end if;
    if v_hdr.positive_gross <> v_sum.positive_gross then
      raise exception
        'billing consistency: app % positive_gross (%) != sum of active positive lines (%)',
        v_app_id, v_hdr.positive_gross, v_sum.positive_gross;
    end if;
    if v_hdr.billable_hours <> v_sum.billable_hours then
      raise exception
        'billing consistency: app % billable_hours (%) != sum of active line hours (%)',
        v_app_id, v_hdr.billable_hours, v_sum.billable_hours;
    end if;
    if v_hdr.retainage_withheld <> v_sum.retainage_withheld then
      raise exception
        'billing consistency: app % retainage_withheld (%) != sum of active line retainage_withheld (%)',
        v_app_id, v_hdr.retainage_withheld, v_sum.retainage_withheld;
    end if;
    if v_hdr.retainage_released <> v_sum.retainage_released then
      raise exception
        'billing consistency: app % retainage_released (%) != sum of active line retainage_released (%)',
        v_app_id, v_hdr.retainage_released, v_sum.retainage_released;
    end if;
  end loop;

  -- Assert held_to_date >= 0 per touched project (over issued apps only)
  foreach v_proj_id in array touched_proj_ids loop
    select coalesce(sum(retainage_withheld - retainage_released - retainage_drawn), 0)
      into v_held
      from ops.billing_application
     where project_id = v_proj_id
       and status = 'issued';
    if v_held < 0 then
      raise exception
        'billing consistency: project % held_to_date is negative (%), retainage draw exceeds held',
        v_proj_id, v_held;
    end if;
  end loop;

  return new;
end;
$$;

-- Deferred constraint trigger on billing_application (header inserts/updates)
create constraint trigger trg_billing_consistency_header
  after insert or update on ops.billing_application
  deferrable initially deferred
  for each row execute function ops.trg_billing_consistency();

-- Deferred constraint trigger on billing_application_line (line inserts/updates)
create constraint trigger trg_billing_consistency_line
  after insert or update on ops.billing_application_line
  deferrable initially deferred
  for each row execute function ops.trg_billing_consistency();

-- ============================================================================
-- 7a. record_billing_application -- entry point.
--     With a non-blank ref: delegates to issue immediately.
--     With a null ref: draft path (Task 8); for now raise "draft not yet supported".
create or replace function ops.record_billing_application(
  p_project_id             uuid,
  p_actor_person_id        uuid,
  p_period_through         date,
  p_external_invoice_ref   text    default null,
  p_exclude_apparatus      uuid[]  default '{}',
  p_retainage_draw_request numeric default 0
) returns uuid language plpgsql as $$
begin
  if p_external_invoice_ref is not null and btrim(p_external_invoice_ref) <> '' then
    -- Issue path: delegate to issue_billing_application
    return ops.issue_billing_application(
      p_project_id,
      p_actor_person_id,
      p_period_through,
      p_external_invoice_ref,
      p_exclude_apparatus,
      p_retainage_draw_request
    );
  else
    -- Draft path: Task 8
    raise exception 'draft billing application not yet supported; provide external_invoice_ref to issue immediately';
  end if;
end;
$$;
