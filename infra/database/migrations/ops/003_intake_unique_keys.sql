-- ops migration 003 — unique keys for idempotent estimator intake (ops Chip 5).
-- Additive + reversible. Partial uniques: intake rows always carry legacy_source_id / line_number,
-- so these do not constrain any non-intake rows that leave those columns null.
create unique index if not exists uq_ops_scopes_intake
  on ops.scopes (project_id, legacy_source_id) where legacy_source_id is not null;

create unique index if not exists uq_ops_scope_quote_line_intake
  on ops.scope_quote_line (scope_id, line_number) where line_number is not null;

create unique index if not exists uq_ops_apparatus_intake
  on ops.apparatus (legacy_source_id) where legacy_source_id is not null;
