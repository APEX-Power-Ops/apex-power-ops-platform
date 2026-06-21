-- DOWN -- ops Chip 4 progress billing. Undoes ONLY Chip 4 (leaves Chips 1/2/3 intact). Idempotent.
drop view if exists ops.v_project_billing;
drop view if exists ops.v_billing_application_sov;
drop view if exists ops.v_draft_preview;
drop view if exists ops.v_unbilled_recognition;
-- Task 2: mutation gate + immutability trigger functions (drop before tables)
drop function if exists ops.trg_billapp_immutable() cascade;
drop function if exists ops.trg_billline_immutable() cascade;
drop function if exists ops.trg_billdraft_gate() cascade;
-- (further triggers + their functions dropped here once Tasks 3-9 add them; keep this list in sync)
drop function if exists ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric) cascade;
drop function if exists ops.issue_billing_application(uuid,uuid,date,text,uuid[],numeric) cascade;
drop function if exists ops.discard_draft_billing_application(uuid,uuid) cascade;
drop function if exists ops.void_billing_application(uuid,uuid,text) cascade;
drop table if exists ops.billing_application_line cascade;
drop table if exists ops.billing_application cascade;
drop table if exists ops.billing_application_draft cascade;
drop type if exists ops.billing_application_status;
alter table if exists ops.projects drop column if exists retainage_pct;
