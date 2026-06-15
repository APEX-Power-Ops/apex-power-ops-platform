-- ============================================================================
-- DOWN — ops Chip 2 quote model. Undoes ONLY Chip 2 (leaves the Chip 1 identity
-- skeleton intact). Idempotent (IF EXISTS) so the test can run it on any state.
-- Order: view -> apparatus columns (the FK to scope_quote_line) -> scope_quote
--        -> scope_quote_line (cascade drops the trigger) -> function -> catalog -> enum.
-- ============================================================================
drop view if exists ops.v_apparatus_quote;

alter table if exists ops.apparatus
  drop column if exists quote_line_id,
  drop column if exists quoted_revenue,
  drop column if exists quoted_hours;

drop table if exists ops.scope_quote;
drop table if exists ops.scope_quote_line cascade;
drop function if exists ops.maintain_scope_quote_hours() cascade;
drop table if exists ops.standard_hours;
drop type if exists ops.test_standard;
