-- =============================================================================
-- RESA Power Platform - Enum Refinements
-- =============================================================================
-- File: 09b_enum_updates.sql
-- Generated: 2025-12-11
-- Purpose: Align enum values with actual field usage
-- Run: Only if recreating enums (requires dropping/recreating)
-- =============================================================================

-- NOTE: PostgreSQL doesn't allow easy enum modification.
-- These are the RECOMMENDED values based on Excel tracker analysis.
-- To implement, you'd need to:
-- 1. Create new enum type
-- 2. Migrate data
-- 3. Drop old enum
-- 4. Rename new to old

-- =============================================================================
-- APPARATUS_ASSESSMENT - Current vs Recommended
-- =============================================================================
-- 
-- CURRENT ENUM:
--   'Pass', 'Fail', 'Marginal', 'Needs Repair', 'Deferred', 'Not Tested'
--
-- ACTUAL FIELD VALUES (from Excel):
--   'ACCEPTABLE', 'NON-SERVICEABLE', 'MINOR DEFICIENCY', '' (empty)
--
-- RECOMMENDED MAPPING:
--   ACCEPTABLE       -> Pass (or keep as Acceptable)
--   NON-SERVICEABLE  -> Fail (or keep as Non-Serviceable)
--   MINOR DEFICIENCY -> Marginal (or keep as Minor Deficiency)
--   (empty)          -> Not Tested

-- Option A: Add missing values to existing enum (Postgres 9.1+)
-- This is the least disruptive approach

DO $$ 
BEGIN
    -- Add field-actual values to apparatus_assessment if not exists
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'Acceptable' AND enumtypid = 'apparatus_assessment'::regtype) THEN
        ALTER TYPE apparatus_assessment ADD VALUE IF NOT EXISTS 'Acceptable';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'Non-Serviceable' AND enumtypid = 'apparatus_assessment'::regtype) THEN
        ALTER TYPE apparatus_assessment ADD VALUE IF NOT EXISTS 'Non-Serviceable';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'Minor Deficiency' AND enumtypid = 'apparatus_assessment'::regtype) THEN
        ALTER TYPE apparatus_assessment ADD VALUE IF NOT EXISTS 'Minor Deficiency';
    END IF;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- FULL ASSESSMENT REFERENCE
-- =============================================================================
-- After additions, the complete apparatus_assessment enum should be:
-- 
-- 'Pass'              - Generic pass (legacy)
-- 'Fail'              - Generic fail (legacy)
-- 'Marginal'          - Borderline pass (legacy)
-- 'Needs Repair'      - Requires work before serviceable
-- 'Deferred'          - Testing postponed
-- 'Not Tested'        - Not yet tested
-- 'Acceptable'        - NETA standard: meets requirements
-- 'Non-Serviceable'   - NETA standard: cannot be placed in service
-- 'Minor Deficiency'  - NETA standard: minor issues noted

-- =============================================================================
-- STATUS VALUE MAPPING
-- =============================================================================
-- Excel STATUS values vs our apparatus_status enum:
--
-- Excel Value      -> Database Value
-- 'COMPLETED'      -> 'Complete'
-- 'NOT STARTED'    -> 'Not Started'
-- 'IN PROGRESS'    -> 'In Progress'
-- ''(empty)        -> 'Not Started'
--
-- Our enum already supports these, just need case normalization on import

-- =============================================================================
-- IMPORT VALUE TRANSFORMATION NOTES
-- =============================================================================
-- When importing from Excel, the import function should transform:
--
-- STATUS:
--   UPPER('COMPLETED') -> 'Complete'
--   UPPER('NOT STARTED') -> 'Not Started'
--   UPPER('IN PROGRESS') -> 'In Progress'
--   empty -> 'Not Started'
--
-- AVAILABILITY:
--   'READY' -> 'Ready'
--   'ON HOLD' -> 'On Hold'
--   'NOT AVAILABLE' -> 'Not Available'
--   empty -> 'Not Available'
--
-- ASSESSMENT:
--   'ACCEPTABLE' -> 'Acceptable'
--   'NON-SERVICEABLE' -> 'Non-Serviceable'
--   'MINOR DEFICIENCY' -> 'Minor Deficiency'
--   empty -> NULL (not yet assessed)
