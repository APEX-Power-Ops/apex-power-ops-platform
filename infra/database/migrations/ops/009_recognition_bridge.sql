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
