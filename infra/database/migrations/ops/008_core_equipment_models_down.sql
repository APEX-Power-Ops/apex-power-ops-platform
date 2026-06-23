-- ============================================================================
-- ops Step 4a DOWN — revert 008. Drops only what 008 created. Chips 1–7 intact.
-- ============================================================================
alter table if exists ops.apparatus drop constraint if exists apparatus_equipment_model_ref_fkey;
drop view if exists core.v_equipment_models_resolved;
drop table if exists core.equipment_models;        -- self-FK rows go with it
drop type if exists core.unit_of_issue;
drop type if exists core.equipment_lifecycle;
drop schema if exists core;                         -- only if empty (it is)
