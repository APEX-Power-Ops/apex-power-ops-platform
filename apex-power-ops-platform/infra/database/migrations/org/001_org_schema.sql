-- =============================================================================
-- Org Domain -- Schema Creation
-- Packet: 2026-04-14-pm-schema-011b
-- Authority: 2026-04-14-pm-schema-011a-org-domain-schema-design-handoff.md
-- Landing Lane: infra/database/migrations/org/
--
-- This file creates only the org schema namespace.
-- No enums are required for the minimum org design.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS org;

COMMENT ON SCHEMA org IS
    'Organization domain: clients, sites, business units, and contracts. '
    'Minimum shared-infra schema required to support PM/work foreign key activation.';
