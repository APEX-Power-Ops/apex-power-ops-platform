-- ============================================================================
-- DOWN — ops Chip 3 recognition ledger. Undoes ONLY Chip 3 (leaves Chips 1/2/4
-- intact). Idempotent (IF EXISTS). Order: views -> parent-table guards -> the two
-- recognition functions -> event table (cascade drops its triggers) -> enums.
-- ============================================================================
drop view if exists ops.v_project_recognition;
drop view if exists ops.v_scope_recognition;
drop view if exists ops.v_apparatus_recognition;
drop view if exists ops.v_recognition_review_queue;

drop trigger if exists apparatus_protect_recognition on ops.apparatus;
drop trigger if exists apparatus_freeze_guard        on ops.apparatus;
drop trigger if exists scope_protect_recognition     on ops.scopes;
drop trigger if exists project_protect_recognition   on ops.projects;
drop trigger if exists scope_quote_freeze_guard      on ops.scope_quote;
drop function if exists ops.trg_apparatus_protect_recognition() cascade;
drop function if exists ops.trg_apparatus_freeze_guard()        cascade;
drop function if exists ops.trg_scope_protect_recognition()     cascade;
drop function if exists ops.trg_project_protect_recognition()   cascade;
drop function if exists ops.trg_scope_quote_freeze_guard()      cascade;

drop function if exists ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text) cascade;
drop function if exists ops.reverse_recognition(uuid,uuid,text) cascade;

drop table if exists ops.revenue_recognition_event cascade;
drop function if exists ops.trg_revrec_immutable() cascade;
drop function if exists ops.trg_revrec_insert_integrity() cascade;

drop type if exists ops.obligation_clearance;
drop type if exists ops.recognition_event_type;
