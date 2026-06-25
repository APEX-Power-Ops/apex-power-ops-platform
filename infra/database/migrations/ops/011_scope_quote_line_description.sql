-- 011_scope_quote_line_description.sql
-- Additive: line-level free-text `description` on ops.scope_quote_line.
-- `designation` (varchar) and `notes` (text) already exist from 002 — this adds the THIRD
-- distinct grid column. Reversible. Chips 1-10 survive DOWN. Nothing to prod (ops_app gate).
alter table ops.scope_quote_line
  add column if not exists description text;
