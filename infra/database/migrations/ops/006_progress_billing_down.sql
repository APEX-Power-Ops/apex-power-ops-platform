-- DOWN -- ops Chip 4 progress billing. Undoes ONLY Chip 4 (leaves Chips 1/2/3 intact). Idempotent.

-- Drop views first (depend on tables + functions below)
drop view if exists ops.v_project_billing;
drop view if exists ops.v_billing_application_sov;
drop view if exists ops.v_draft_preview;
drop view if exists ops.v_unbilled_recognition;

-- Drop triggers explicitly before the functions they reference (belt-and-suspenders; tables cascade
-- triggers on DROP TABLE, but explicit drops here ensure a clean partial-state re-run path).
-- Constraint triggers on billing_application (header consistency + immutability)
drop trigger if exists trg_billing_consistency_header on ops.billing_application;
drop trigger if exists trg_billapp_immutable          on ops.billing_application;

-- Constraint trigger on billing_application_line (line consistency + immutability)
drop trigger if exists trg_billing_consistency_line on ops.billing_application_line;
drop trigger if exists trg_billline_immutable       on ops.billing_application_line;

-- Gate trigger on billing_application_draft
drop trigger if exists trg_billdraft_gate on ops.billing_application_draft;

-- Drop trigger functions (cascade to any remaining trigger references just in case)
drop function if exists ops.trg_billing_consistency() cascade;
drop function if exists ops.trg_billapp_immutable()   cascade;
drop function if exists ops.trg_billline_immutable()  cascade;
drop function if exists ops.trg_billdraft_gate()      cascade;

-- Drop the five Chip-4 functions (by exact signature; cascade handles any stale refs)
-- 6-param issue (the main billing engine)
drop function if exists ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric) cascade;
-- 3-param issue (promote-from-draft overload)
drop function if exists ops.issue_billing_application(uuid,uuid,text) cascade;
-- record (draft/issue router)
drop function if exists ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric) cascade;
-- discard draft
drop function if exists ops.discard_draft_billing_application(uuid,uuid) cascade;
-- void
drop function if exists ops.void_billing_application(uuid,uuid,text) cascade;

-- Drop tables in reverse-dependency order (line references application; draft is independent)
drop table if exists ops.billing_application_line  cascade;
drop table if exists ops.billing_application       cascade;
drop table if exists ops.billing_application_draft cascade;

-- Drop the enum (no table depends on it once tables are gone)
drop type if exists ops.billing_application_status;

-- Drop the retainage_pct column added to ops.projects
alter table if exists ops.projects drop column if exists retainage_pct;
