-- =============================================================================
-- Identity Domain -- Triggers
-- Packet: 2026-04-14-pm-schema-012b
-- Authority: 2026-04-14-pm-schema-012a-identity-domain-schema-design-handoff.md §3
-- Landing Lane: infra/database/migrations/identity/
--
-- Pattern: same reusable updated_at trigger as work.fn_set_updated_at()
-- and org.fn_set_updated_at() but scoped to the identity schema to
-- maintain domain isolation.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Reusable updated_at trigger function (identity-scoped)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION identity.fn_set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION identity.fn_set_updated_at() IS
    'Reusable trigger function: sets updated_at = now() on every UPDATE. '
    'Identity-domain counterpart of work.fn_set_updated_at() and org.fn_set_updated_at().';

-- ---------------------------------------------------------------------------
-- Apply to all identity tables
-- ---------------------------------------------------------------------------

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON identity.users
    FOR EACH ROW EXECUTE FUNCTION identity.fn_set_updated_at();

CREATE TRIGGER trg_employees_updated_at
    BEFORE UPDATE ON identity.employees
    FOR EACH ROW EXECUTE FUNCTION identity.fn_set_updated_at();

CREATE TRIGGER trg_crews_updated_at
    BEFORE UPDATE ON identity.crews
    FOR EACH ROW EXECUTE FUNCTION identity.fn_set_updated_at();
