-- =============================================================================
-- DOWN for 038_neta_tables_standard.sql — revert to global-dedupe neta_tables.
-- Drops the standard dimension; keeps the ATS rows under uq(table_number).
-- Tolerant of pre-038 state (no standard column) so the test fixture can run it first.
-- =============================================================================
BEGIN;
SET client_encoding TO 'UTF8';
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='records'
             AND table_name='neta_tables' AND column_name='standard') THEN
    ALTER TABLE records.neta_tables DROP CONSTRAINT IF EXISTS uq_neta_tables_std_number;
    DELETE FROM records.neta_tables WHERE standard = 'mts';
    ALTER TABLE records.neta_tables DROP COLUMN standard;
  END IF;
END $$;
ALTER TABLE records.neta_tables DROP CONSTRAINT IF EXISTS uq_neta_tables_number;
ALTER TABLE records.neta_tables ADD CONSTRAINT uq_neta_tables_number UNIQUE (table_number);
COMMIT;
