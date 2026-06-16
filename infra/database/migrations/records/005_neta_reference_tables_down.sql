-- =============================================================================
-- DOWN — Records NETA Reference Layer (Chip 2a). Drops ONLY the 2a objects;
-- leaves the Chip 1 records.* tables (001–004) intact. Idempotent (IF EXISTS).
-- Order: child (test_items, FK) -> tables -> procedures -> category enum.
-- =============================================================================
DROP TABLE IF EXISTS records.neta_test_items;
DROP TABLE IF EXISTS records.neta_tables;
DROP TABLE IF EXISTS records.neta_procedures;
DROP TYPE  IF EXISTS records.neta_test_category_enum;
