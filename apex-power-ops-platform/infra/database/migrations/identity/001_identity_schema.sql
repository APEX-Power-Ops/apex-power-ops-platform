-- =============================================================================
-- Identity Domain -- Schema Creation
-- Packet: 2026-04-14-pm-schema-012b
-- Authority: 2026-04-14-pm-schema-012a-identity-domain-schema-design-handoff.md
-- Landing Lane: infra/database/migrations/identity/
--
-- This file creates only the identity schema namespace.
-- No enums are required for the minimum identity design.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS identity;

COMMENT ON SCHEMA identity IS
    'Identity domain: users, employees, and crews. '
    'Minimum shared-infra schema required to support PM/work identity foreign key activation.';
