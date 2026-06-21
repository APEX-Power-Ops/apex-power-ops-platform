drop trigger if exists trg_intake_run_immutable on ops.intake_runs;
drop function if exists ops.trg_intake_run_immutable();
drop table if exists ops.intake_validation_findings;
drop table if exists ops.intake_source_files;
drop table if exists ops.intake_runs;
drop type if exists ops.intake_source_format;
drop type if exists ops.intake_conflict_kind;
drop type if exists ops.intake_run_status;
