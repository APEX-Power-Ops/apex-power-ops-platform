-- ============================================================================
-- External MCP Action Audit Table
-- ============================================================================
-- Purpose:
--   Preserve durable audit evidence for confirmed write actions executed through
--   dedicated external-system MCP connectors such as GitHub or future bounded
--   repository/platform integrations.
--
-- Policy posture:
--   - service_role keeps full access for backend writes and operator review
--   - authenticated clients do not read or write this table directly in the
--     first slice; the backend records audit rows server-side
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.mcp_external_action_audits (
    audit_id text PRIMARY KEY,
    connector text NOT NULL,
    tool_name text NOT NULL,
    actor_id text NOT NULL,
    actor_email text,
    owner text NOT NULL,
    repo text NOT NULL,
    target_type text,
    target_identifier text,
    request_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
    result_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_mcp_external_action_audits_connector_created_at
    ON public.mcp_external_action_audits (connector, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_mcp_external_action_audits_repo_created_at
    ON public.mcp_external_action_audits (owner, repo, created_at DESC);

ALTER TABLE public.mcp_external_action_audits ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mcp_external_action_audits_service_all ON public.mcp_external_action_audits;
CREATE POLICY mcp_external_action_audits_service_all
    ON public.mcp_external_action_audits
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE public.mcp_external_action_audits IS
    'Durable audit evidence for confirmed write actions executed through external dedicated MCP connectors.';