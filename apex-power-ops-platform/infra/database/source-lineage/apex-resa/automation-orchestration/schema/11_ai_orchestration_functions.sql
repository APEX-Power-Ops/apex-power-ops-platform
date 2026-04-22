-- ============================================================================
-- AI ORCHESTRATION FUNCTIONS
-- Version: 1.0.0 | Deployed: December 24, 2025
-- Purpose: RPC functions for task management and agent coordination
-- ============================================================================

-- ============================================================================
-- TASK MANAGEMENT FUNCTIONS
-- ============================================================================

-- Function: Claim next available task (priority-sorted, dependency-aware)
CREATE OR REPLACE FUNCTION claim_task(
    p_agent ai_agent,
    p_project VARCHAR DEFAULT NULL,
    p_task_type ai_task_type DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_task_id UUID;
BEGIN
    -- Find highest priority pending task matching criteria
    SELECT id INTO v_task_id
    FROM ai_tasks
    WHERE status = 'pending'
        AND (p_project IS NULL OR project = p_project)
        AND (p_task_type IS NULL OR task_type = p_task_type)
        -- Check all dependencies are complete
        AND (depends_on IS NULL OR NOT EXISTS (
            SELECT 1 FROM ai_tasks dep 
            WHERE dep.id = ANY(ai_tasks.depends_on) 
            AND dep.status != 'complete'
        ))
    ORDER BY 
        CASE priority 
            WHEN 'critical' THEN 1 
            WHEN 'high' THEN 2 
            WHEN 'normal' THEN 3 
            WHEN 'low' THEN 4 
            WHEN 'background' THEN 5 
        END,
        created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED;  -- Prevents race conditions
    
    IF v_task_id IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Claim the task
    UPDATE ai_tasks 
    SET status = 'claimed', 
        assigned_agent = p_agent, 
        claimed_at = now(),
        updated_at = now()
    WHERE id = v_task_id;
    
    -- Update agent state
    UPDATE ai_agent_state 
    SET current_task_id = v_task_id, 
        status = 'working',
        updated_at = now()
    WHERE agent = p_agent;
    
    -- Log to history
    INSERT INTO ai_task_history (task_id, action, agent, old_status, new_status)
    VALUES (v_task_id, 'claimed', p_agent, 'pending', 'claimed');
    
    RETURN v_task_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION claim_task IS 'Agent claims next available task from queue';

-- Function: Complete a task with output
CREATE OR REPLACE FUNCTION complete_task(
    p_task_id UUID,
    p_agent ai_agent,
    p_output_payload JSONB DEFAULT NULL,
    p_output_files TEXT[] DEFAULT NULL,
    p_quality_score NUMERIC DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE ai_tasks 
    SET status = 'complete',
        output_payload = COALESCE(p_output_payload, output_payload),
        output_files = COALESCE(p_output_files, output_files),
        quality_score = p_quality_score,
        completed_at = now(),
        updated_at = now()
    WHERE id = p_task_id AND assigned_agent = p_agent;
    
    IF NOT FOUND THEN 
        RETURN FALSE; 
    END IF;
    
    -- Update agent state
    UPDATE ai_agent_state 
    SET current_task_id = NULL, 
        status = 'idle',
        updated_at = now()
    WHERE agent = p_agent;
    
    -- Log to history
    INSERT INTO ai_task_history (task_id, action, agent, old_status, new_status, payload)
    VALUES (p_task_id, 'completed', p_agent, 'claimed', 'complete', p_output_payload);
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION complete_task IS 'Mark task as complete with output payload';

-- Function: Fail a task with error
CREATE OR REPLACE FUNCTION fail_task(
    p_task_id UUID,
    p_agent ai_agent,
    p_error_message TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_retry_count INT;
    v_max_retries INT;
BEGIN
    SELECT retry_count, max_retries INTO v_retry_count, v_max_retries
    FROM ai_tasks WHERE id = p_task_id;
    
    IF v_retry_count < v_max_retries THEN
        -- Reset to pending for retry
        UPDATE ai_tasks 
        SET status = 'pending',
            assigned_agent = NULL,
            claimed_at = NULL,
            error_message = p_error_message,
            retry_count = retry_count + 1,
            updated_at = now()
        WHERE id = p_task_id;
    ELSE
        -- Max retries reached, mark as failed
        UPDATE ai_tasks 
        SET status = 'failed',
            error_message = p_error_message,
            updated_at = now()
        WHERE id = p_task_id;
    END IF;
    
    -- Update agent state
    UPDATE ai_agent_state 
    SET current_task_id = NULL, 
        status = 'idle',
        updated_at = now()
    WHERE agent = p_agent;
    
    -- Log to history
    INSERT INTO ai_task_history (task_id, action, agent, notes)
    VALUES (p_task_id, 'failed', p_agent, p_error_message);
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fail_task IS 'Mark task as failed, auto-retry if under limit';

-- Function: Create a new task
CREATE OR REPLACE FUNCTION create_task(
    p_title VARCHAR,
    p_task_type ai_task_type,
    p_project VARCHAR,
    p_domain VARCHAR DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_priority ai_task_priority DEFAULT 'normal',
    p_depends_on UUID[] DEFAULT NULL,
    p_input_payload JSONB DEFAULT NULL,
    p_input_files TEXT[] DEFAULT NULL,
    p_quality_gates JSONB DEFAULT NULL,
    p_created_by ai_agent DEFAULT 'human'
) RETURNS UUID AS $$
DECLARE
    v_task_id UUID;
BEGIN
    INSERT INTO ai_tasks (
        title, task_type, project, domain, description, 
        priority, depends_on, input_payload, input_files, 
        quality_gates, created_by
    ) VALUES (
        p_title, p_task_type, p_project, p_domain, p_description,
        p_priority, p_depends_on, p_input_payload, p_input_files,
        p_quality_gates, p_created_by
    ) RETURNING id INTO v_task_id;
    
    -- Log creation
    INSERT INTO ai_task_history (task_id, action, agent, new_status)
    VALUES (v_task_id, 'created', p_created_by, 'pending');
    
    RETURN v_task_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_task IS 'Add new task to queue with optional dependencies and quality gates';

-- ============================================================================
-- HANDOFF FUNCTIONS
-- ============================================================================

-- Function: Create a handoff to another agent
CREATE OR REPLACE FUNCTION handoff_task(
    p_task_id UUID,
    p_from_agent ai_agent,
    p_to_agent ai_agent,
    p_handoff_type VARCHAR DEFAULT 'task',
    p_context TEXT DEFAULT NULL,
    p_files TEXT[] DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_handoff_id UUID;
BEGIN
    INSERT INTO ai_handoffs (task_id, from_agent, to_agent, handoff_type, context, files)
    VALUES (p_task_id, p_from_agent, p_to_agent, p_handoff_type, p_context, p_files)
    RETURNING id INTO v_handoff_id;
    
    -- Log to task history
    INSERT INTO ai_task_history (task_id, action, agent, notes)
    VALUES (p_task_id, 'handoff_created', p_from_agent, 
            'Handed off to ' || p_to_agent::text || ': ' || COALESCE(p_context, ''));
    
    RETURN v_handoff_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION handoff_task IS 'Create explicit handoff between agents';

-- Function: Acknowledge a handoff
CREATE OR REPLACE FUNCTION acknowledge_handoff(
    p_handoff_id UUID,
    p_agent ai_agent
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE ai_handoffs
    SET status = 'acknowledged',
        acknowledged_at = now()
    WHERE id = p_handoff_id AND to_agent = p_agent AND status = 'pending';
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION acknowledge_handoff IS 'Agent acknowledges receipt of handoff';

-- ============================================================================
-- QUERY FUNCTIONS
-- ============================================================================

-- Function: Agent heartbeat (status check-in)
CREATE OR REPLACE FUNCTION agent_heartbeat(
    p_agent ai_agent,
    p_status VARCHAR DEFAULT 'idle',
    p_notes TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO ai_agent_state (agent, status, last_heartbeat, notes, updated_at)
    VALUES (p_agent, p_status, now(), p_notes, now())
    ON CONFLICT (agent) DO UPDATE SET
        status = EXCLUDED.status,
        last_heartbeat = now(),
        notes = COALESCE(EXCLUDED.notes, ai_agent_state.notes),
        updated_at = now();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION agent_heartbeat IS 'Agent reports current status';

-- Function: Get my current tasks
CREATE OR REPLACE FUNCTION get_my_tasks(p_agent ai_agent)
RETURNS TABLE (
    id UUID,
    title VARCHAR,
    task_type ai_task_type,
    project VARCHAR,
    priority ai_task_priority,
    status ai_task_status,
    claimed_at TIMESTAMPTZ,
    description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT t.id, t.title, t.task_type, t.project, t.priority, 
           t.status, t.claimed_at, t.description
    FROM ai_tasks t
    WHERE t.assigned_agent = p_agent
    AND t.status IN ('claimed', 'blocked', 'review')
    ORDER BY 
        CASE t.priority 
            WHEN 'critical' THEN 1 
            WHEN 'high' THEN 2 
            WHEN 'normal' THEN 3 
        END;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_my_tasks IS 'List all active tasks assigned to agent';

-- Function: Get pending handoffs for agent
CREATE OR REPLACE FUNCTION get_pending_handoffs(p_agent ai_agent)
RETURNS TABLE (
    id UUID,
    task_id UUID,
    task_title VARCHAR,
    from_agent ai_agent,
    handoff_type VARCHAR,
    context TEXT,
    files TEXT[],
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT h.id, h.task_id, t.title, h.from_agent, h.handoff_type,
           h.context, h.files, h.created_at
    FROM ai_handoffs h
    JOIN ai_tasks t ON h.task_id = t.id
    WHERE h.to_agent = p_agent AND h.status = 'pending'
    ORDER BY h.created_at;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_pending_handoffs IS 'List pending handoffs waiting for agent';

-- Function: Register content in registry
CREATE OR REPLACE FUNCTION register_content(
    p_project VARCHAR,
    p_domain VARCHAR,
    p_content_type VARCHAR,
    p_file_path TEXT,
    p_file_name VARCHAR,
    p_title VARCHAR DEFAULT NULL,
    p_line_count INT DEFAULT NULL,
    p_quality_score NUMERIC DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL,
    p_task_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_content_id UUID;
BEGIN
    INSERT INTO content_registry (
        project, domain, content_type, file_path, file_name,
        title, line_count, quality_score, metadata, created_by_task
    ) VALUES (
        p_project, p_domain, p_content_type, p_file_path, p_file_name,
        p_title, p_line_count, p_quality_score, p_metadata, p_task_id
    )
    ON CONFLICT (project, file_path) DO UPDATE SET
        title = COALESCE(EXCLUDED.title, content_registry.title),
        line_count = COALESCE(EXCLUDED.line_count, content_registry.line_count),
        quality_score = COALESCE(EXCLUDED.quality_score, content_registry.quality_score),
        metadata = COALESCE(EXCLUDED.metadata, content_registry.metadata),
        updated_at = now()
    RETURNING id INTO v_content_id;
    
    RETURN v_content_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION register_content IS 'Register or update content in central registry';
