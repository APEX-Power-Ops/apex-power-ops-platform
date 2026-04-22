-- ============================================================================
-- AI ORCHESTRATION LAYER
-- Version: 1.0.0 | Deployed: December 24, 2025
-- Purpose: Task queue, agent coordination, handoffs, content tracking
-- ============================================================================

-- ENUMS (prefixed to avoid conflicts with existing enums)
-- ----------------------------------------------------------------------------
CREATE TYPE ai_task_type AS ENUM (
    'create',      -- Build new content/components
    'enhance',     -- Improve existing content
    'review',      -- Quality check/audit
    'assemble',    -- Combine multiple pieces
    'migrate',     -- Move/convert data
    'document',    -- Create documentation
    'test',        -- Testing/validation
    'deploy'       -- Release/publish
);

CREATE TYPE ai_task_status AS ENUM (
    'pending',     -- Ready to be claimed
    'claimed',     -- Agent working on it
    'blocked',     -- Waiting on dependency
    'review',      -- Needs QC approval
    'complete',    -- Done
    'failed'       -- Error occurred
);

CREATE TYPE ai_agent AS ENUM (
    'desktop-claude',   -- Orchestrator: complex reasoning, QC, strategy
    'codex-max',        -- Executor: bulk creation, pattern replication
    'vs-code-claude',   -- Surgeon: precision edits, debugging
    'local-ai',         -- Processor: embeddings, preprocessing
    'human'             -- Director: approvals, strategy
);

CREATE TYPE ai_task_priority AS ENUM (
    'critical',    -- Drop everything
    'high',        -- Do today
    'normal',      -- Normal queue
    'low',         -- When time permits
    'background'   -- Idle time only
);

-- TABLES
-- ----------------------------------------------------------------------------

-- AI Tasks - Central task queue
CREATE TABLE ai_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    task_type ai_task_type NOT NULL,
    project VARCHAR(50) NOT NULL,        -- 'neta', 'resa', 'infrastructure'
    domain VARCHAR(100),                  -- 'study-guide', 'dashboard', etc.
    description TEXT,
    priority ai_task_priority DEFAULT 'normal',
    status ai_task_status DEFAULT 'pending',
    
    -- Assignment
    assigned_agent ai_agent,
    claimed_at TIMESTAMPTZ,
    
    -- Dependencies
    depends_on UUID[],                    -- Tasks that must complete first
    blocks UUID[],                        -- Tasks waiting on this one
    
    -- Payload
    input_payload JSONB,                  -- Parameters, context
    output_payload JSONB,                 -- Results, metrics
    input_files TEXT[],                   -- Input file paths
    output_files TEXT[],                  -- Created/modified file paths
    
    -- Quality
    quality_gates JSONB,                  -- Requirements to meet
    quality_score NUMERIC(5,2),           -- 0-100 score after review
    
    -- Metadata
    created_by ai_agent DEFAULT 'human',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    
    -- Error handling
    error_message TEXT,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3
);

COMMENT ON TABLE ai_tasks IS 'Central task queue for AI agent coordination';

-- AI Agent State - Real-time status
CREATE TABLE ai_agent_state (
    agent ai_agent PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'idle',    -- idle, working, blocked, offline
    current_task_id UUID REFERENCES ai_tasks(id),
    last_heartbeat TIMESTAMPTZ DEFAULT now(),
    capabilities JSONB,                   -- What this agent can do
    stats JSONB,                          -- Tasks completed, avg time, etc.
    notes TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE ai_agent_state IS 'Real-time status of each AI agent';

-- AI Task History - Audit trail
CREATE TABLE ai_task_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES ai_tasks(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,          -- created, claimed, completed, etc.
    agent ai_agent,
    old_status ai_task_status,
    new_status ai_task_status,
    notes TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE ai_task_history IS 'Complete audit trail of task state changes';

-- AI Knowledge - RAG-ready knowledge base
CREATE TABLE ai_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project VARCHAR(50) NOT NULL,
    domain VARCHAR(100),
    topic VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',  -- text, code, template, reference
    source_file TEXT,
    embedding VECTOR(1536),               -- For semantic search (pgvector)
    metadata JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE ai_knowledge IS 'Structured knowledge base with vector embeddings for RAG';

-- Content Registry - Inventory of produced content
CREATE TABLE content_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project VARCHAR(50) NOT NULL,
    domain VARCHAR(100),
    content_type VARCHAR(100) NOT NULL,   -- study-guide, practice-test, etc.
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    status VARCHAR(50) DEFAULT 'draft',   -- draft, review, published, archived
    quality_score NUMERIC(5,2),
    line_count INT,
    word_count INT,
    metadata JSONB,                       -- Flexible attributes
    created_by_task UUID REFERENCES ai_tasks(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project, file_path)
);

COMMENT ON TABLE content_registry IS 'Inventory of all produced content with quality tracking';

-- AI Handoffs - Explicit agent-to-agent transfers
CREATE TABLE ai_handoffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES ai_tasks(id),
    from_agent ai_agent NOT NULL,
    to_agent ai_agent NOT NULL,
    handoff_type VARCHAR(50) DEFAULT 'task',  -- task, review, continuation
    context TEXT,                         -- What receiving agent needs to know
    files TEXT[],                         -- Relevant file paths
    status VARCHAR(20) DEFAULT 'pending', -- pending, acknowledged, rejected
    created_at TIMESTAMPTZ DEFAULT now(),
    acknowledged_at TIMESTAMPTZ
);

COMMENT ON TABLE ai_handoffs IS 'Explicit work transfers between AI agents';

-- INDEXES
-- ----------------------------------------------------------------------------
CREATE INDEX idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX idx_ai_tasks_priority ON ai_tasks(priority);
CREATE INDEX idx_ai_tasks_agent ON ai_tasks(assigned_agent);
CREATE INDEX idx_ai_tasks_project ON ai_tasks(project);
CREATE INDEX idx_ai_task_history_task ON ai_task_history(task_id);
CREATE INDEX idx_ai_knowledge_project ON ai_knowledge(project, domain);
CREATE INDEX idx_content_registry_project ON content_registry(project, domain);
CREATE INDEX idx_ai_handoffs_to_agent ON ai_handoffs(to_agent, status);

-- VIEWS
-- ----------------------------------------------------------------------------

-- Active tasks with agent info
CREATE VIEW v_active_tasks AS
SELECT 
    t.id,
    t.title,
    t.task_type,
    t.project,
    t.domain,
    t.priority,
    t.status,
    t.assigned_agent,
    t.claimed_at,
    t.created_at,
    EXTRACT(EPOCH FROM (now() - t.claimed_at))/3600 as hours_claimed,
    a.status as agent_status
FROM ai_tasks t
LEFT JOIN ai_agent_state a ON t.assigned_agent = a.agent
WHERE t.status NOT IN ('complete', 'failed')
ORDER BY 
    CASE t.priority 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'normal' THEN 3 
        WHEN 'low' THEN 4 
        WHEN 'background' THEN 5 
    END,
    t.created_at;

-- Agent dashboard overview
CREATE VIEW v_agent_dashboard AS
SELECT 
    a.agent,
    a.status,
    a.last_heartbeat,
    a.notes,
    COUNT(t.id) FILTER (WHERE t.status = 'claimed') as active_tasks,
    COUNT(t.id) FILTER (WHERE t.status = 'complete') as completed_today,
    COUNT(h.id) FILTER (WHERE h.status = 'pending') as pending_handoffs
FROM ai_agent_state a
LEFT JOIN ai_tasks t ON t.assigned_agent = a.agent 
    AND (t.status = 'claimed' OR (t.status = 'complete' AND t.completed_at > now() - interval '24 hours'))
LEFT JOIN ai_handoffs h ON h.to_agent = a.agent AND h.status = 'pending'
GROUP BY a.agent, a.status, a.last_heartbeat, a.notes;

-- Pending handoffs view
CREATE VIEW v_pending_handoffs AS
SELECT 
    h.id,
    h.task_id,
    t.title as task_title,
    h.from_agent,
    h.to_agent,
    h.handoff_type,
    h.context,
    h.files,
    h.created_at,
    EXTRACT(EPOCH FROM (now() - h.created_at))/3600 as hours_waiting
FROM ai_handoffs h
JOIN ai_tasks t ON h.task_id = t.id
WHERE h.status = 'pending'
ORDER BY h.created_at;

-- TRIGGERS
-- ----------------------------------------------------------------------------

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_ai_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ai_tasks_updated 
    BEFORE UPDATE ON ai_tasks 
    FOR EACH ROW EXECUTE FUNCTION update_ai_updated_at();

CREATE TRIGGER ai_agent_state_updated 
    BEFORE UPDATE ON ai_agent_state 
    FOR EACH ROW EXECUTE FUNCTION update_ai_updated_at();

-- Log status changes automatically
CREATE OR REPLACE FUNCTION log_task_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO ai_task_history (task_id, action, agent, old_status, new_status)
        VALUES (NEW.id, 'status_change', NEW.assigned_agent, OLD.status, NEW.status);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ai_tasks_status_logged
    AFTER UPDATE ON ai_tasks
    FOR EACH ROW EXECUTE FUNCTION log_task_status_change();

-- INITIAL DATA
-- ----------------------------------------------------------------------------
INSERT INTO ai_agent_state (agent, status, notes) VALUES
    ('desktop-claude', 'idle', 'Ready for orchestration'),
    ('codex-max', 'idle', 'Ready for bulk work'),
    ('vs-code-claude', 'idle', 'Ready for precision work'),
    ('local-ai', 'offline', 'Not yet configured'),
    ('human', 'idle', 'Jason available')
ON CONFLICT (agent) DO NOTHING;
