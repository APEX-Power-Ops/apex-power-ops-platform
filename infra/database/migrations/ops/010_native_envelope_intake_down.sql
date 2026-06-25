-- ops migration 010 DOWN. Reverses the columns/indexes; rebuilds the enum WITHOUT 'native'.
-- Refuses if any native run exists (an enum value cannot be dropped while in use, and silently
-- dropping native runs would be data loss).
-- Idempotent: uses ::text cast in the data-loss guard (valid in DO blocks); enum rebuild is
-- guarded so a repeat call is a safe no-op.

do $$
begin
  -- data-loss guard: refuse if any native rows exist.
  -- cast via text so we do not USE the enum value in a context that requires it to be visible.
  if exists (select 1 from ops.intake_runs where source_format::text = 'native') then
    raise exception 'refusing 010 down: native intake_runs exist (drop them first)';
  end if;
end $$;

drop index if exists ops.uq_intake_runs_proj_quote_version_native;
-- uq_intake_runs_content_hash_native is NOT dropped here: it was never created (C6-RESOLVED).
drop function if exists ops._intake_source_format_text(ops.intake_source_format) cascade;

-- restore the 007 trigger body (drop the 010 identity-col checks)
create or replace function ops.trg_intake_run_immutable() returns trigger language plpgsql as $$
begin
  if (new.approved_by is null) <> (new.approved_at is null) then
    raise exception 'intake_runs: approved_by and approved_at must be set together';
  end if;
  if (new.status = 'approved') <> (new.approved_by is not null) then
    raise exception 'intake_runs: status=approved iff approved_by is set';
  end if;
  if tg_op = 'UPDATE' then
    if new.canonical_payload_json   is distinct from old.canonical_payload_json
       or new.source_format         is distinct from old.source_format
       or new.payload_schema_version is distinct from old.payload_schema_version
       or new.parser_version         is distinct from old.parser_version
       or new.uploaded_by            is distinct from old.uploaded_by
       or new.project_number         is distinct from old.project_number then
      raise exception 'intake_runs provenance fields are immutable (run %)', old.id;
    end if;
    if old.approved_by is not null and new.approved_by is distinct from old.approved_by then
      raise exception 'intake_runs.approved_by is set-once (run %)', old.id;
    end if;
    if old.approved_at is not null and new.approved_at is distinct from old.approved_at then
      raise exception 'intake_runs.approved_at is set-once (run %)', old.id;
    end if;
    new.updated_at := now();
  end if;
  return new;
end $$;

alter table ops.intake_runs
  drop column if exists estimate_envelope_json,
  drop column if exists source_revision_id,
  drop column if exists source_draft_id,
  drop column if exists content_hash,
  drop column if exists quote_version,
  drop column if exists envelope_id;

-- rebuild the enum without 'native' (no DROP VALUE in Postgres)
-- guard via EXECUTE inside DO block so DDL runs conditionally (idempotent on repeat calls)
do $$
begin
  if exists (
    select 1 from pg_enum e join pg_type t on t.oid = e.enumtypid
    where t.typname = 'intake_source_format' and e.enumlabel = 'native'
  ) then
    execute 'alter type ops.intake_source_format rename to intake_source_format_old';
    execute $q$create type ops.intake_source_format as enum ('decomposed_scope_sheet','flat_quote','unsupported')$q$;
    execute 'alter table ops.intake_runs alter column source_format type ops.intake_source_format using source_format::text::ops.intake_source_format';
    execute 'drop type ops.intake_source_format_old';
  end if;
end $$;
