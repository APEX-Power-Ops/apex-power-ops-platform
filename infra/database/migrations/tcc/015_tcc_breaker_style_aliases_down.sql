-- Down migration record for 015_tcc_breaker_style_aliases.sql.
-- Do not run against prod unless explicitly retiring the governed alias table.
drop table if exists tcc.breaker_style_aliases;
