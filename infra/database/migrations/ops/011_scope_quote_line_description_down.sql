-- 011_scope_quote_line_description_down.sql
-- Reverse of 011. Drops the description column (and any data in it — acceptable: dev/ops_test only).
alter table ops.scope_quote_line
  drop column if exists description;
