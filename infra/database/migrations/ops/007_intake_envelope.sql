-- ops migration 007 -- Estimator intake envelope (Chip 5). Additive + reversible. Dev-only.
-- Builds on 001-006. The operational ops.* substrate is written ONLY by approve_run (the package);
-- this migration adds the audit/lifecycle envelope + guards + minimal source columns.

create type ops.intake_run_status   as enum ('parsed','reviewing','approved','rejected','revision_blocked','superseded');
create type ops.intake_conflict_kind as enum ('none','frozen','recognized','billed');
create type ops.intake_source_format as enum ('decomposed_scope_sheet','flat_quote','unsupported');

create table ops.intake_runs (
  id                     uuid primary key default gen_random_uuid(),
  project_number         text not null,
  project_id             uuid references ops.projects(id),
  source_format          ops.intake_source_format not null,
  status                 ops.intake_run_status not null default 'parsed',
  conflict_kind          ops.intake_conflict_kind not null default 'none',
  payload_schema_version text not null,
  parser_version         text not null,
  canonical_payload_json jsonb not null,
  review_payload_json    jsonb not null,
  review_payload_version int  not null default 1,
  uploaded_by            uuid not null references ops.persons(person_id),
  uploaded_at            timestamptz not null default now(),
  approved_by            uuid references ops.persons(person_id),
  approved_at            timestamptz,
  rejected_reason        text,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);

create table ops.intake_source_files (
  id           uuid primary key default gen_random_uuid(),
  run_id       uuid not null references ops.intake_runs(id) on delete cascade,
  filename     text not null,
  content_type text not null check (content_type in ('xlsm','json')),
  byte_size    bigint not null check (byte_size > 0 and byte_size <= 26214400),  -- 25 MB audit-envelope cap
  sha256       text not null,
  raw_bytes    bytea not null check (octet_length(raw_bytes) = byte_size),       -- stored artifact integrity
  created_at   timestamptz not null default now()
);

create table ops.intake_validation_findings (
  id                uuid primary key default gen_random_uuid(),
  run_id            uuid not null references ops.intake_runs(id) on delete cascade,
  payload_version   int  not null,
  severity          text not null check (severity in ('blocking','fidelity','info')),
  code              text not null,
  ok                boolean not null,
  message           text not null default '',     -- PM-safe: NO dollar values
  diagnostic_detail text,                          -- finance-only; never returned to the PM surface
  created_at        timestamptz not null default now()
);
create index ix_intake_findings_run on ops.intake_validation_findings (run_id, payload_version);
create index ix_intake_source_files_run on ops.intake_source_files (run_id);

-- one approvable active run per project_number (supersede lifecycle backstop)
create unique index uq_intake_one_active on ops.intake_runs (project_number)
  where status in ('parsed','reviewing');

-- write-once provenance fields on intake_runs
create or replace function ops.trg_intake_run_immutable() returns trigger language plpgsql as $$
begin
  -- approval shape (INSERT *and* UPDATE): by/at set together; status='approved' IFF approved_by set
  -- (blocks a direct insert of status='approved' with null actor, and approval fields on a non-approved row).
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
       or new.project_number         is distinct from old.project_number then   -- project_number write-once
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
create trigger trg_intake_run_immutable before insert or update on ops.intake_runs
  for each row execute function ops.trg_intake_run_immutable();

-- D1: apparatus.task_id must reference a task in the SAME scope.
create or replace function ops.trg_apparatus_task_same_scope() returns trigger language plpgsql as $$
declare v_task_scope uuid;
begin
  if new.task_id is not null then
    select scope_id into v_task_scope from ops.tasks where id = new.task_id;
    if v_task_scope is null or v_task_scope <> new.scope_id then
      raise exception 'apparatus % task_id must be a task in scope % (got task scope %)',
        coalesce(new.apparatus_designation,'?'), new.scope_id, v_task_scope;
    end if;
  end if;
  return new;
end $$;
create trigger trg_apparatus_task_same_scope before insert or update on ops.apparatus
  for each row execute function ops.trg_apparatus_task_same_scope();

-- D1: tasks.scope_id is immutable once the row exists.
create or replace function ops.trg_task_scope_immutable() returns trigger language plpgsql as $$
begin
  if new.scope_id is distinct from old.scope_id then
    raise exception 'ops.tasks.scope_id is immutable (task %)', old.id;
  end if;
  return new;
end $$;
create trigger trg_task_scope_immutable before update on ops.tasks
  for each row execute function ops.trg_task_scope_immutable();

-- Intake idempotency for tasks (003 covered scopes/lines/apparatus but not tasks). Section is the stable key.
create unique index uq_ops_tasks_intake on ops.tasks (scope_id, legacy_source_id)
  where legacy_source_id is not null;

-- D2: minimal source-derived project columns (NOT canonical CRM).
alter table ops.projects
  add column if not exists source_client_name   text,
  add column if not exists source_site_name     text,
  add column if not exists source_site_address  text,
  add column if not exists source_site_city     text,
  add column if not exists source_site_state    text,
  add column if not exists source_site_zip      text;
