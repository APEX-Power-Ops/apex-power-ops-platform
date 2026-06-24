-- ---- T6: drop the read views (first in down order) ------------------------
drop view if exists ops.v_completion_recognition_rollup;
drop view if exists ops.v_completion_recognition_worklist;

-- ============================================================================
-- DOWN — ops migration 009 recognition bridge. Undoes ONLY 009 (leaves 001-008
-- intact). FULLY IDEMPOTENT: every block uses `if exists` / `create or replace`, so
-- running this down TWICE in a row is a clean no-op (proven by
-- test_down_is_idempotent_double_down). Built incrementally across T0..T6: each task
-- PREPENDS its teardown so the down runs in reverse dependency order. Final order
-- (T6 top -> T0 bottom): drop views; drop completion guard; drop attestation-
-- immutability trigger/fn; create-or-replace the two 005 fns VERBATIM; drop the
-- trace column; drop revoke fn; drop attest fn; drop completion_attestation.
-- ============================================================================

-- ---- T5: restore the two Chip-3 functions to their VERBATIM 005-up bodies ---
-- (005-down DROPs these; there is no body to "restore," so the 005-up bodies are
--  EMBEDDED here verbatim — preserving the FIX-A/FIX-B null-safety + serialization.
--  A pg_get_functiondef source-diff test (T5) proves byte-equality, normalized.)
-- PROVENANCE: the two function bodies below are a VERBATIM copy of
--   infra/database/migrations/ops/005_recognition_ledger.sql (the SOURCE OF TRUTH).
--   Do NOT hand-edit them here — edit 005 and re-copy. The drift guard is
--   test_down_restores_005_function_bodies_byte_for_byte in test_009_recognition_bridge.py
--   (pg_get_functiondef source-diff), which FAILS if these drift from the 005-up defs.
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

alter table ops.revenue_recognition_event drop column if exists completion_attestation_id;

-- ---- T4: drop revoke function ---------------------------------------------
drop function if exists ops.revoke_completion_attestation(uuid,uuid,text) cascade;

-- ---- T3: drop attest function ---------------------------------------------
drop function if exists ops.attest_apparatus_complete(uuid,uuid,text) cascade;

-- ---- T2: drop completion guard trigger + function -------------------------
drop trigger if exists apparatus_completion_guard on ops.apparatus;
drop function if exists ops.trg_apparatus_completion_guard() cascade;

-- ---- T1: drop attestation-immutability trigger + function ------------------
drop trigger if exists completion_attestation_immutable on ops.completion_attestation;
drop function if exists ops.trg_completion_attestation_immutable() cascade;

-- ---- T0: drop the completion attestation table -----------------------------
drop table if exists ops.completion_attestation cascade;
