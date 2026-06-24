-- ops migration 010 -- Native estimator EstimateEnvelope intake (catalog-only v1). Additive + reversible. Dev-only.
-- Adds the 'native' source_format, the envelope identity provenance columns, the raw-envelope sidecar,
-- the write-once trigger extension, and the native-only partial-unique indexes. NO source_kind (C1).

alter type ops.intake_source_format add value if not exists 'native';

alter table ops.intake_runs
  add column if not exists envelope_id           text,
  add column if not exists quote_version          integer,
  add column if not exists content_hash           text,
  add column if not exists source_draft_id        text,
  add column if not exists source_revision_id     text,
  add column if not exists estimate_envelope_json jsonb;

-- C4: the new identity/provenance cols are write-once (extend the existing immutability trigger).
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
       or new.project_number         is distinct from old.project_number
       or new.envelope_id            is distinct from old.envelope_id            -- 010 (write-once)
       or new.quote_version          is distinct from old.quote_version          -- 010
       or new.content_hash           is distinct from old.content_hash           -- 010
       or new.source_draft_id        is distinct from old.source_draft_id        -- 010
       or new.source_revision_id     is distinct from old.source_revision_id     -- 010
       or new.estimate_envelope_json is distinct from old.estimate_envelope_json -- 010
    then
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

-- R1-1: partial index predicates must use an IMMUTABLE expression. A bare enum::text cast is not
-- considered IMMUTABLE by PostgreSQL in index predicates, so we define a thin IMMUTABLE wrapper
-- function. This also avoids using the 'native' enum literal in the same connection.execute() call
-- that adds the value (the function compares text, not enum, so no enum-value restriction applies).
create or replace function ops._intake_source_format_text(v ops.intake_source_format)
  returns text language sql immutable strict as $$select v::text$$;

-- C4: idempotency — one native run per compiled-envelope content_hash.
create unique index if not exists uq_intake_runs_content_hash_native
  on ops.intake_runs (content_hash)
  where ops._intake_source_format_text(source_format) = 'native' and content_hash is not null;

-- C4: one native run per (project_number, quote_version); supersede = a new quote_version.
create unique index if not exists uq_intake_runs_proj_quote_version_native
  on ops.intake_runs (project_number, quote_version)
  where ops._intake_source_format_text(source_format) = 'native' and quote_version is not null;
