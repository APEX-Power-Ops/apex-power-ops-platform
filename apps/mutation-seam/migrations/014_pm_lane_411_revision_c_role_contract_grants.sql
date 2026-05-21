-- ============================================================================
-- APEX PM Lane 411 Revision C / Lane 421 — Canonical Role Grants
-- Migration: 014_pm_lane_411_revision_c_role_contract_grants.sql
-- Created:   2026-05-21
-- ============================================================================
-- Applies the first truthful executable grant surface for the Lane 411
-- financial tables after the Lane 420 schema floor established them live.
--
-- Scope
--   * Create the canonical pm and operations roles when absent.
--   * Grant schema usage needed for those roles on seam.
--   * Grant SELECT and INSERT on the four Lane 411 financial tables.
--   * Preserve the public-role deny posture for anon/authenticated.
--   * Preserve non-admission for field-facing roles.
--
-- Out of scope
--   * No business-row insert or update.
--   * No route or auth-layer implementation change.
--   * No apparatus status mutation, reporting, payroll, billing, invoice,
--     accounting, or external-finance output.
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pm') THEN
        CREATE ROLE pm NOLOGIN;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'operations') THEN
        CREATE ROLE operations NOLOGIN;
    END IF;
END;
$$;

GRANT USAGE ON SCHEMA seam TO pm, operations;

GRANT USAGE ON TYPE seam.scope_labor_category TO pm, operations;
GRANT USAGE ON TYPE seam.apparatus_revenue_event_kind TO pm, operations;

GRANT SELECT, INSERT ON TABLE seam.project_contract_snapshots TO pm, operations;
GRANT SELECT, INSERT ON TABLE seam.scope_labor_details TO pm, operations;
GRANT SELECT, INSERT ON TABLE seam.apparatus_financials TO pm, operations;
GRANT SELECT, INSERT ON TABLE seam.apparatus_revenue_events TO pm, operations;

REVOKE ALL ON TABLE seam.project_contract_snapshots FROM anon, authenticated;
REVOKE ALL ON TABLE seam.scope_labor_details FROM anon, authenticated;
REVOKE ALL ON TABLE seam.apparatus_financials FROM anon, authenticated;
REVOKE ALL ON TABLE seam.apparatus_revenue_events FROM anon, authenticated;

DO $$
DECLARE
    role_name TEXT;
BEGIN
    FOREACH role_name IN ARRAY ARRAY['field_tech', 'field_lead', 'task_lead']
    LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
            EXECUTE format('REVOKE ALL ON TABLE seam.project_contract_snapshots FROM %I', role_name);
            EXECUTE format('REVOKE ALL ON TABLE seam.scope_labor_details FROM %I', role_name);
            EXECUTE format('REVOKE ALL ON TABLE seam.apparatus_financials FROM %I', role_name);
            EXECUTE format('REVOKE ALL ON TABLE seam.apparatus_revenue_events FROM %I', role_name);
        END IF;
    END LOOP;
END;
$$;