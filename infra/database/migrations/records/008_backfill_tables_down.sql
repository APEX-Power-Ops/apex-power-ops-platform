-- Reverse 008_backfill_tables.sql (drop links + xref + the kind enum).
BEGIN;

DROP TABLE IF EXISTS records.asset_class_neta_procedure;
DROP TABLE IF EXISTS records.neta_procedure_xref;
DROP TYPE IF EXISTS records.neta_xref_kind_enum;

COMMIT;
