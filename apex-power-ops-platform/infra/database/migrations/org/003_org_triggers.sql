-- =============================================================================
-- Org Domain -- Triggers
-- Packet: 2026-04-14-pm-schema-011b
-- Authority: 2026-04-14-pm-schema-011a-org-domain-schema-design-handoff.md §2
-- Landing Lane: infra/database/migrations/org/
--
-- Pattern: same reusable updated_at trigger as work.fn_set_updated_at()
-- but scoped to the org schema to maintain domain isolation.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Reusable updated_at trigger function (org-scoped)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION org.fn_set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION org.fn_set_updated_at() IS
    'Reusable trigger function: sets updated_at = now() on every UPDATE. '
    'Org-domain counterpart of work.fn_set_updated_at().';

-- ---------------------------------------------------------------------------
-- Apply to all org tables
-- ---------------------------------------------------------------------------

CREATE TRIGGER trg_clients_updated_at
    BEFORE UPDATE ON org.clients
    FOR EACH ROW EXECUTE FUNCTION org.fn_set_updated_at();

CREATE TRIGGER trg_sites_updated_at
    BEFORE UPDATE ON org.sites
    FOR EACH ROW EXECUTE FUNCTION org.fn_set_updated_at();

CREATE TRIGGER trg_business_units_updated_at
    BEFORE UPDATE ON org.business_units
    FOR EACH ROW EXECUTE FUNCTION org.fn_set_updated_at();

CREATE TRIGGER trg_contracts_updated_at
    BEFORE UPDATE ON org.contracts
    FOR EACH ROW EXECUTE FUNCTION org.fn_set_updated_at();
