-- =============================================================================
-- RESA AI ORCHESTRATION - DEPLOYMENT SCRIPT
-- Run this in Supabase SQL Editor to deploy orchestration layer
-- Created: December 24, 2025
-- =============================================================================

-- IMPORTANT: Run AFTER existing schema (01-09 files) is deployed

-- Check prerequisites
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'projects') THEN
        RAISE EXCEPTION 'Base schema not deployed. Run DEPLOY_SCHEMA.sql first.';
    END IF;
END $$;

-- =============================================================================
-- Include schema file
-- =============================================================================
\i schema/10_ai_orchestration.sql

-- =============================================================================
-- Include functions file
-- =============================================================================
\i schema/11_ai_orchestration_functions.sql

-- =============================================================================
-- Verify deployment
-- =============================================================================
DO $$
DECLARE
    v_table_count INTEGER;
    v_function_count INTEGER;
BEGIN
    -- Count new tables
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables 
    WHERE table_name IN (
        'ai_tasks', 'ai_agent_state', 'ai_task_history',
        'ai_knowledge', 'content_registry', 'ai_handoffs'
    );
    
    -- Count new functions
    SELECT COUNT(*) INTO v_function_count
    FROM information_schema.routines
    WHERE routine_name IN (
        'claim_task', 'complete_task', 'fail_task', 'create_task',
        'handoff_task', 'acknowledge_handoff', 'get_my_tasks',
        'get_pending_handoffs', 'agent_heartbeat', 'register_content'
    );
    
    RAISE NOTICE '';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'AI ORCHESTRATION DEPLOYMENT COMPLETE';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Tables created: % / 6', v_table_count;
    RAISE NOTICE 'Functions created: % / 10', v_function_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Agent states initialized:';
    RAISE NOTICE '  - desktop-claude: Ready';
    RAISE NOTICE '  - codex-max: Ready';
    RAISE NOTICE '  - vs-code-claude: Ready';
    RAISE NOTICE '  - local-ai: Offline (configure later)';
    RAISE NOTICE '  - human: Ready';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Test with: SELECT * FROM v_agent_dashboard;';
    RAISE NOTICE '  2. Create first task with create_task()';
    RAISE NOTICE '  3. Configure MCP connector for Desktop Claude';
    RAISE NOTICE '===========================================';
END $$;

-- Quick verification query
SELECT 
    agent,
    status,
    status_message
FROM ai_agent_state
ORDER BY agent;
