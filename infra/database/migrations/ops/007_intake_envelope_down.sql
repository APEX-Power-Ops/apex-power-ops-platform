drop trigger if exists trg_apparatus_task_same_scope on ops.apparatus;
drop function if exists ops.trg_apparatus_task_same_scope();
drop trigger if exists trg_task_scope_immutable on ops.tasks;
drop function if exists ops.trg_task_scope_immutable();
drop index if exists ops.uq_ops_tasks_intake;
alter table ops.projects
  drop column if exists source_client_name, drop column if exists source_site_name,
  drop column if exists source_site_address, drop column if exists source_site_city,
  drop column if exists source_site_state, drop column if exists source_site_zip;
drop trigger if exists trg_intake_run_immutable on ops.intake_runs;
drop function if exists ops.trg_intake_run_immutable();
drop table if exists ops.intake_validation_findings;
drop table if exists ops.intake_source_files;
drop index if exists ops.uq_intake_one_active;
drop table if exists ops.intake_runs;
drop type if exists ops.intake_source_format;
drop type if exists ops.intake_conflict_kind;
drop type if exists ops.intake_run_status;
