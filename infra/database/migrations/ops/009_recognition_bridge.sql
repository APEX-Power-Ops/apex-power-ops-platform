-- ============================================================================
-- ops migration 009 — recognition bridge (completion attestation -> recognize).
-- Built INCREMENTALLY across plan tasks T0..T6; each task appends one block to
-- THIS file and the matching teardown to 009_recognition_bridge_down.sql.
-- Dev DB: ops_dev / ops_test. Nothing applied to prod (blocked behind the §5.11
-- ops_app role-boundary RELEASE GATE). Builds on 001-008.
-- ============================================================================

-- ---- T0: completion attestation table + one-active-per-apparatus index -----
create table ops.completion_attestation (
  id            uuid primary key default gen_random_uuid(),
  apparatus_id  uuid not null references ops.apparatus(id),
  attested_by   uuid not null references ops.persons(person_id),
  reason        text not null check (btrim(reason) <> ''),
  provenance    text not null default 'pm_recognition_attestation'
                  check (provenance in ('pm_recognition_attestation')),
  prior_status  ops.apparatus_status not null,
  attested_at   timestamptz not null default now(),
  revoked_at    timestamptz,
  revoked_by    uuid references ops.persons(person_id),
  revoke_reason text
);
create unique index uq_completion_attestation_active
  on ops.completion_attestation (apparatus_id) where revoked_at is null;
comment on table ops.completion_attestation is
  'Governed PM attestation that an apparatus is testing-complete FOR RECOGNITION. NOT production truth, NOT customer-facing. Sole sanctioned writer of ops.apparatus.status=Complete for approved apparatus. A future production-tracking authority supersedes via provenance=production_tracking.';

-- ---- T1: attestation immutability (append-only completion proof) -----------
create function ops.trg_completion_attestation_immutable() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then raise exception 'ops.completion_attestation is append-only (DELETE blocked)'; end if;
  if new.id is distinct from old.id or new.apparatus_id is distinct from old.apparatus_id
     or new.attested_by is distinct from old.attested_by or new.reason is distinct from old.reason
     or new.provenance is distinct from old.provenance or new.prior_status is distinct from old.prior_status
     or new.attested_at is distinct from old.attested_at then
    raise exception 'ops.completion_attestation core fields are immutable (id %)', old.id;
  end if;
  -- the ONLY permitted UPDATE is a single, well-formed revoke transition:
  -- all revoke fields NULL -> all populated together (revoked_at + revoked_by + non-blank revoke_reason).
  if old.revoked_at is not null or old.revoked_by is not null or old.revoke_reason is not null then
    raise exception 'ops.completion_attestation % already revoked (immutable)', old.id;
  end if;
  if not (new.revoked_at is not null and new.revoked_by is not null
          and btrim(coalesce(new.revoke_reason,'')) <> '') then
    raise exception 'ops.completion_attestation %: only a complete revoke is permitted (revoked_at + revoked_by + non-blank reason set together)', old.id;
  end if;
  return new;
end; $$;
create trigger completion_attestation_immutable before update or delete on ops.completion_attestation
  for each row execute function ops.trg_completion_attestation_immutable();

-- ---- T2: completion guard — predicate-transition aware (governed-complete) --
create function ops.trg_apparatus_completion_guard() returns trigger language plpgsql as $$
declare
  new_g boolean := (new.status='Complete' and new.provenance_status='approved');
  old_g boolean;
begin
  if tg_op = 'INSERT' then
    if new_g and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may be entered only via attest', new.id;
    end if;
  else  -- UPDATE
    old_g := (old.status='Complete' and old.provenance_status='approved');
    if (new_g is distinct from old_g) and current_setting('ops.completion_ctx', true) is distinct from '1' then
      raise exception 'apparatus %: governed-complete may change only via attest/revoke', new.id;
    end if;
  end if;
  return new;
end; $$;
create trigger apparatus_completion_guard before insert or update on ops.apparatus
  for each row execute function ops.trg_apparatus_completion_guard();

-- ---- T3: attest_apparatus_complete (sole sanctioned status=Complete writer) -
create function ops.attest_apparatus_complete(
  p_apparatus_id uuid, p_attested_by uuid, p_reason text
) returns uuid language plpgsql as $$
declare a record; sq record; v_prior ops.apparatus_status; v_id uuid;
begin
  if p_reason is null or btrim(p_reason) = '' then raise exception 'reason required'; end if;
  if not exists (select 1 from ops.persons where person_id = p_attested_by) then
    raise exception 'unknown actor %', p_attested_by;
  end if;
  select a2.scope_id, a2.status, a2.is_active, a2.provenance_status,
         a2.quoted_hours, a2.quoted_revenue,
         s.is_active as scope_active, s.status as scope_status,
         p.is_active as project_active, p.status as project_status
    into a
    from ops.apparatus a2
    join ops.scopes s   on s.id = a2.scope_id
    join ops.projects p on p.id = s.project_id
   where a2.id = p_apparatus_id
   for update of a2;
  if not found then raise exception 'apparatus % not found', p_apparatus_id; end if;
  if a.provenance_status <> 'approved' then
    raise exception 'apparatus % not approved (provenance_status=%)', p_apparatus_id, a.provenance_status;
  end if;
  if not (a.is_active and a.scope_active and a.project_active
          and a.scope_status <> 'Cancelled' and a.project_status <> 'Cancelled') then
    raise exception 'apparatus % inactive/cancelled chain cannot attest', p_apparatus_id;
  end if;
  if a.status in ('Complete','Cancelled') then
    raise exception 'apparatus % cannot attest from status %', p_apparatus_id, a.status;
  end if;
  select sq2.is_frozen, sq2.frozen_at into sq from ops.scope_quote sq2 where sq2.scope_id = a.scope_id;
  if not found or not sq.is_frozen or sq.frozen_at is null then
    raise exception 'scope % quote basis not frozen', a.scope_id;
  end if;
  if a.quoted_hours is null or a.quoted_hours <= 0
     or a.quoted_revenue is null or a.quoted_revenue <= 0 then
    raise exception 'apparatus % invalid quote basis', p_apparatus_id;
  end if;
  v_prior := a.status;
  perform set_config('ops.completion_ctx','1', true);
  update ops.apparatus set status='Complete', updated_at=now() where id=p_apparatus_id;
  perform set_config('ops.completion_ctx','0', true);
  insert into ops.completion_attestation (apparatus_id, attested_by, reason, prior_status)
    values (p_apparatus_id, p_attested_by, p_reason, v_prior)
    returning id into v_id;
  return v_id;
end; $$;

-- ---- T4: revoke_completion_attestation (deadlock-safe: apparatus locked FIRST)
create function ops.revoke_completion_attestation(
  p_attestation_id uuid, p_revoked_by uuid, p_reason text
) returns uuid language plpgsql as $$
declare v_app uuid; v_att record; v_net numeric;
begin
  if p_reason is null or btrim(p_reason) = '' then raise exception 'reason required'; end if;
  if not exists (select 1 from ops.persons where person_id = p_revoked_by) then
    raise exception 'unknown actor %', p_revoked_by;
  end if;
  -- (2) resolve apparatus WITHOUT locking the attestation (taking the attestation
  --     lock first would invert approve_and_recognize's apparatus-first order -> deadlock).
  select apparatus_id into v_app from ops.completion_attestation
    where id = p_attestation_id and revoked_at is null;
  if not found then raise exception 'no active attestation %', p_attestation_id; end if;
  -- (3) lock the apparatus FIRST (D-OPS-12; matches approve_and_recognize 005:81).
  perform 1 from ops.apparatus where id = v_app for update;
  -- (4) re-select the active attestation FOR UPDATE + revalidate (a concurrent revoke
  --     may have won between steps 2-3).
  select id, apparatus_id, prior_status into v_att from ops.completion_attestation
    where id = p_attestation_id and revoked_at is null for update;
  if not found then raise exception 'attestation % no longer active', p_attestation_id; end if;
  if v_att.apparatus_id <> v_app then raise exception 'attestation apparatus mismatch'; end if;
  -- (5) net-recognition gate (deterministic under the apparatus lock).
  select coalesce(sum(recognized_amount),0) into v_net
    from ops.revenue_recognition_event where apparatus_id = v_app;
  if v_net > 0 then raise exception 'apparatus has open recognition; reverse first'; end if;
  -- (6-8) ctx -> restore prior_status -> mark revoked (immutability trigger permits this exact shape).
  perform set_config('ops.completion_ctx','1', true);
  update ops.apparatus set status=v_att.prior_status, updated_at=now() where id=v_app;
  perform set_config('ops.completion_ctx','0', true);
  update ops.completion_attestation
    set revoked_at=now(), revoked_by=p_revoked_by, revoke_reason=p_reason
    where id=p_attestation_id;
  return p_attestation_id;
end; $$;

-- ---- T5: firewall touch — recognition trace column + the two Chip-3 fns -----
alter table ops.revenue_recognition_event
  add column completion_attestation_id uuid references ops.completion_attestation(id);

create or replace function ops.approve_and_recognize(
  p_apparatus_id        uuid,
  p_actor_person_id     uuid,
  p_datasheet_clearance ops.obligation_clearance,
  p_datasheet_ref       text,
  p_cx_clearance        ops.obligation_clearance,
  p_cx_ref              text
) returns uuid language plpgsql as $$
declare a record; sq record; v_net numeric; v_id uuid; v_att uuid;   -- 009: v_att added
begin
  select a2.scope_id, a2.status, a2.is_active, a2.quoted_hours, a2.quoted_revenue, a2.assessment,
         s.project_id, s.is_active as scope_active, s.status as scope_status,
         p.is_active as project_active, p.status as project_status
    into a
    from ops.apparatus a2
    join ops.scopes s   on s.id = a2.scope_id
    join ops.projects p on p.id = s.project_id
   where a2.id = p_apparatus_id
   for update of a2;
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
  -- 009: resolve the active completion attestation (required for a recognized row).
  select id into v_att from ops.completion_attestation
    where apparatus_id = p_apparatus_id and revoked_at is null;
  if not found then raise exception 'apparatus % has no active completion attestation', p_apparatus_id; end if;
  insert into ops.revenue_recognition_event
    (apparatus_id, scope_id, project_id, event_type, recognized_amount,
     quoted_hours, blended_rate, basis_frozen_at, assessment, actor_person_id,
     datasheet_clearance, datasheet_ref, cx_clearance, cx_ref, completion_attestation_id)  -- 009: column
  values
    (p_apparatus_id, a.scope_id, a.project_id, 'recognized', a.quoted_revenue,
     a.quoted_hours, sq.blended_rate, sq.frozen_at, a.assessment, p_actor_person_id,
     p_datasheet_clearance, p_datasheet_ref, p_cx_clearance, p_cx_ref, v_att)            -- 009: value
  returning id into v_id;
  return v_id;
end;
$$;

create or replace function ops.trg_revrec_insert_integrity() returns trigger language plpgsql as $$
declare v_scope uuid; a record; sq record; orig record;
begin
  select scope_id into v_scope from ops.apparatus where id = new.apparatus_id;
  if not found then raise exception 'apparatus % not found', new.apparatus_id; end if;
  if new.scope_id <> v_scope then raise exception 'scope_id lineage mismatch'; end if;
  if new.project_id <> (select project_id from ops.scopes where id = new.scope_id) then
    raise exception 'project_id lineage mismatch';
  end if;

  if new.event_type = 'recognized' then
    -- 009: a recognized row MUST carry an active attestation for THIS apparatus.
    if new.completion_attestation_id is null then
      raise exception 'recognized row requires completion_attestation_id';
    end if;
    if not exists (select 1 from ops.completion_attestation
                   where id = new.completion_attestation_id
                     and revoked_at is null and apparatus_id = new.apparatus_id) then
      raise exception 'recognized row attestation invalid (revoked / wrong apparatus)';
    end if;
    select a2.status, a2.is_active, a2.quoted_hours, a2.quoted_revenue,
           s.is_active as scope_active, s.status as scope_status,
           p.is_active as project_active, p.status as project_status
      into a
      from ops.apparatus a2 join ops.scopes s on s.id=a2.scope_id join ops.projects p on p.id=s.project_id
     where a2.id = new.apparatus_id
     for update of a2;
    if not (a.is_active and a.scope_active and a.project_active
            and a.scope_status <> 'Cancelled' and a.project_status <> 'Cancelled') then
      raise exception 'recognized row for inactive/cancelled chain';
    end if;
    if a.status <> 'Complete' then raise exception 'recognized row for non-complete apparatus'; end if;
    select is_frozen, frozen_at, blended_rate into sq from ops.scope_quote where scope_id = new.scope_id;
    if not found or not sq.is_frozen or sq.frozen_at is null then
      raise exception 'recognized row on unfrozen basis';
    end if;
    if new.recognized_amount is distinct from a.quoted_revenue then
      raise exception 'recognized_amount must equal apparatus.quoted_revenue';
    end if;
    if new.quoted_hours is distinct from a.quoted_hours
       or new.blended_rate is distinct from sq.blended_rate
       or new.basis_frozen_at is distinct from sq.frozen_at then
      raise exception 'recognized row snapshot does not match current basis';
    end if;
    if (select coalesce(sum(recognized_amount),0)
          from ops.revenue_recognition_event where apparatus_id = new.apparatus_id) > 0 then
      raise exception 'apparatus % already has an open recognition', new.apparatus_id;
    end if;
  elsif new.event_type = 'reversal' then
    -- 009: reversal rows carry NO attestation (the trace is active-at-write on recognized only).
    if new.completion_attestation_id is not null then
      raise exception 'reversal row must not carry completion_attestation_id';
    end if;
    select apparatus_id, recognized_amount into orig
      from ops.revenue_recognition_event where id = new.reverses_event_id and event_type='recognized';
    if not found then raise exception 'reversal target is not a recognized event'; end if;
    if orig.apparatus_id <> new.apparatus_id then raise exception 'reversal apparatus mismatch'; end if;
    if new.recognized_amount <> -orig.recognized_amount then raise exception 'reversal amount must equal -(original)'; end if;
  end if;
  return new;
end;
$$;

-- ---- T6: read models — worklist + rollup ----------------------------------
create view ops.v_completion_recognition_worklist as
select a.id as apparatus_id, a.apparatus_designation, a.scope_id, s.project_id, p.project_number,
       a.status, a.quoted_hours, a.quoted_revenue,
       att.id as attestation_id, att.attested_by, att.attested_at, att.reason as attest_reason,
       ar.net_recognized, ar.is_recognized, ar.recognized_event_id,
       (a.status not in ('Complete','Cancelled') and att.id is null
         and a.quoted_hours > 0 and a.quoted_revenue > 0)                 as can_attest,
       (a.status = 'Complete' and att.id is not null
         and a.quoted_hours > 0 and a.quoted_revenue > 0
         and not ar.is_recognized)                                        as can_recognize,
       (att.id is not null and not ar.is_recognized)                      as can_revoke,
       ar.is_recognized                                                   as can_reverse
from ops.apparatus a
join ops.scopes s   on s.id = a.scope_id
join ops.projects p on p.id = s.project_id
join ops.scope_quote sq on sq.scope_id = a.scope_id
left join ops.completion_attestation att
  on att.apparatus_id = a.id and att.revoked_at is null
join ops.v_apparatus_recognition ar on ar.apparatus_id = a.id
where a.provenance_status = 'approved' and a.is_active
  and s.is_active and s.status <> 'Cancelled'
  and p.is_active and p.status <> 'Cancelled'
  and sq.is_frozen;

-- eligible_count + the row scope use the SAME eligibility predicate as
-- v_completion_recognition_worklist (provenance_status='approved' AND a.is_active
-- AND active non-cancelled scope/project chain AND sq.is_frozen). The outer WHERE
-- restricts the row set to eligible apparatus so recognized_total/recognized_count
-- and eligible_count all read the identical population the worklist exposes — an
-- unfrozen-basis or cancelled-scope apparatus is excluded from eligible_count.
create view ops.v_completion_recognition_rollup as
select p.project_number, s.id as scope_id, p.id as project_id,
       coalesce(sum(ar.net_recognized), 0)                          as recognized_total,
       count(*) filter (where ar.is_recognized)                      as recognized_count,
       count(*) filter (where a.provenance_status = 'approved'
                          and a.is_active
                          and s.is_active and s.status <> 'Cancelled'
                          and p.is_active and p.status <> 'Cancelled'
                          and sq.is_frozen)                          as eligible_count
from ops.apparatus a
join ops.scopes s   on s.id = a.scope_id
join ops.projects p on p.id = s.project_id
join ops.scope_quote sq on sq.scope_id = a.scope_id
join ops.v_apparatus_recognition ar on ar.apparatus_id = a.id
where a.provenance_status = 'approved' and a.is_active
  and s.is_active and s.status <> 'Cancelled'
  and p.is_active and p.status <> 'Cancelled'
  and sq.is_frozen
group by p.project_number, s.id, p.id;
