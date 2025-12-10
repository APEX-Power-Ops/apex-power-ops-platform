-- =====================================================
-- APPARATUS COMPLETION WORKFLOW
-- Two-stage approval: Tech submits -> Lead approves -> Revenue recognized
-- Created: December 10, 2025
-- =====================================================

-- =====================================================
-- 1. ADD WORKFLOW TRACKING COLUMNS
-- =====================================================

ALTER TABLE apparatus
    ADD COLUMN IF NOT EXISTS submitted_by UUID REFERENCES employees(id),
    ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES employees(id),
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS delay_hours NUMERIC(6,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS delay_reason TEXT,
    ADD COLUMN IF NOT EXISTS tech_notes TEXT;

COMMENT ON COLUMN apparatus.submitted_by IS 'Tech who marked apparatus as complete (pending review)';
COMMENT ON COLUMN apparatus.submitted_at IS 'When tech submitted for review';
COMMENT ON COLUMN apparatus.approved_by IS 'Lead who approved the completion';
COMMENT ON COLUMN apparatus.approved_at IS 'When lead approved - triggers revenue recognition';
COMMENT ON COLUMN apparatus.delay_hours IS 'Hours delayed beyond estimate (customer-caused)';
COMMENT ON COLUMN apparatus.delay_reason IS 'Explanation for delay hours';
COMMENT ON COLUMN apparatus.tech_notes IS 'Field notes from technician';

CREATE INDEX IF NOT EXISTS idx_apparatus_pending_review 
    ON apparatus(status) 
    WHERE status = 'Pending Review';

-- =====================================================
-- 2. APPROVAL QUEUE VIEW
-- =====================================================

CREATE OR REPLACE VIEW v_apparatus_approval_queue AS
SELECT 
    a.id AS apparatus_id,
    a.apparatus_name,
    a.apparatus_designation,
    a.apparatus_type,
    a.status,
    a.assessment,
    a.actual_hours,
    a.quoted_hours,
    a.delay_hours,
    a.delay_reason,
    a.tech_notes,
    a.submitted_at,
    a.submitted_by,
    sub.first_name || ' ' || sub.last_name AS submitted_by_name,
    t.task_name,
    t.id AS task_id,
    s.scope_name,
    s.id AS scope_id,
    p.project_name,
    p.project_number,
    p.id AS project_id,
    c.client_name,
    EXTRACT(EPOCH FROM (NOW() - a.submitted_at))/3600 AS hours_in_queue,
    DATE_PART('day', NOW() - a.submitted_at) AS days_in_queue
FROM apparatus a
JOIN scopes s ON a.scope_id = s.id
JOIN projects p ON s.project_id = p.id
JOIN clients c ON p.client_id = c.id
LEFT JOIN tasks t ON a.task_id = t.id
LEFT JOIN employees sub ON a.submitted_by = sub.id
WHERE a.status = 'Pending Review'
ORDER BY a.submitted_at ASC;

-- =====================================================
-- 3. REVENUE RECOGNITION TRIGGER
-- Only fires on APPROVAL (status -> Complete), not submission
-- =====================================================

CREATE OR REPLACE FUNCTION create_apparatus_revenue()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
    v_effective_rate NUMERIC;
    v_revenue_amount NUMERIC;
    v_hours NUMERIC;
BEGIN
    IF NEW.status = 'Complete' AND (OLD.status IS NULL OR OLD.status != 'Complete') THEN
        v_scope_id := NEW.scope_id;
        
        SELECT COALESCE(effective_rate, 125.00) INTO v_effective_rate
        FROM scope_labor_details WHERE scope_id = v_scope_id LIMIT 1;
        
        IF v_effective_rate IS NULL THEN v_effective_rate := 125.00; END IF;
        
        v_hours := COALESCE(NEW.actual_hours, NEW.quoted_hours, 0);
        v_revenue_amount := v_hours * v_effective_rate;
        
        IF v_hours > 0 THEN
            INSERT INTO apparatus_revenue (
                apparatus_id, revenue_amount, hours_applied, rate_applied,
                recognition_date, revenue_status, notes, created_at
            ) VALUES (
                NEW.id, v_revenue_amount, v_hours, v_effective_rate,
                CURRENT_DATE, 'PENDING',
                'Auto-generated on approval by ' || COALESCE(
                    (SELECT first_name || ' ' || last_name FROM employees WHERE id = NEW.approved_by),
                    'system'
                ),
                NOW()
            );
        END IF;
        
        NEW.actual_revenue := v_revenue_amount;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_create_revenue_on_approval ON apparatus;
CREATE TRIGGER tr_create_revenue_on_approval
    BEFORE UPDATE ON apparatus
    FOR EACH ROW
    EXECUTE FUNCTION create_apparatus_revenue();

-- =====================================================
-- 4. WORKFLOW HELPER FUNCTIONS
-- =====================================================

-- Tech submits apparatus for review
CREATE OR REPLACE FUNCTION submit_apparatus_for_review(
    p_apparatus_id UUID,
    p_tech_id UUID,
    p_actual_hours NUMERIC DEFAULT NULL,
    p_assessment apparatus_assessment DEFAULT NULL,
    p_delay_hours NUMERIC DEFAULT 0,
    p_delay_reason TEXT DEFAULT NULL,
    p_tech_notes TEXT DEFAULT NULL
)
RETURNS apparatus AS $$
DECLARE
    v_result apparatus;
BEGIN
    UPDATE apparatus SET
        status = 'Pending Review',
        submitted_by = p_tech_id,
        submitted_at = NOW(),
        actual_hours = COALESCE(p_actual_hours, actual_hours, quoted_hours),
        assessment = COALESCE(p_assessment, assessment),
        delay_hours = COALESCE(p_delay_hours, 0),
        delay_reason = p_delay_reason,
        tech_notes = p_tech_notes,
        actual_end = CURRENT_DATE
    WHERE id = p_apparatus_id
    AND status IN ('Not Started', 'In Progress')
    RETURNING * INTO v_result;
    
    IF v_result IS NULL THEN
        RAISE EXCEPTION 'Apparatus not found or already submitted/completed';
    END IF;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Lead approves apparatus (triggers revenue)
CREATE OR REPLACE FUNCTION approve_apparatus_completion(
    p_apparatus_id UUID,
    p_approver_id UUID,
    p_override_hours NUMERIC DEFAULT NULL,
    p_override_assessment apparatus_assessment DEFAULT NULL,
    p_approval_notes TEXT DEFAULT NULL
)
RETURNS apparatus AS $$
DECLARE
    v_result apparatus;
BEGIN
    UPDATE apparatus SET
        status = 'Complete',
        approved_by = p_approver_id,
        approved_at = NOW(),
        actual_hours = COALESCE(p_override_hours, actual_hours),
        assessment = COALESCE(p_override_assessment, assessment),
        notes = CASE 
            WHEN p_approval_notes IS NOT NULL 
            THEN COALESCE(notes || E'\n', '') || 'Approval note: ' || p_approval_notes
            ELSE notes
        END
    WHERE id = p_apparatus_id
    AND status = 'Pending Review'
    RETURNING * INTO v_result;
    
    IF v_result IS NULL THEN
        RAISE EXCEPTION 'Apparatus not found or not pending review';
    END IF;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Lead rejects apparatus (sends back to tech)
CREATE OR REPLACE FUNCTION reject_apparatus_submission(
    p_apparatus_id UUID,
    p_rejector_id UUID,
    p_rejection_reason TEXT
)
RETURNS apparatus AS $$
DECLARE
    v_result apparatus;
BEGIN
    UPDATE apparatus SET
        status = 'In Progress',
        submitted_by = NULL,
        submitted_at = NULL,
        notes = COALESCE(notes || E'\n', '') || 
            'REJECTED by ' || 
            COALESCE((SELECT first_name || ' ' || last_name FROM employees WHERE id = p_rejector_id), 'Lead') ||
            ' on ' || TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI') || 
            ': ' || p_rejection_reason
    WHERE id = p_apparatus_id
    AND status = 'Pending Review'
    RETURNING * INTO v_result;
    
    IF v_result IS NULL THEN
        RAISE EXCEPTION 'Apparatus not found or not pending review';
    END IF;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 5. APPROVAL QUEUE SUMMARY VIEW
-- =====================================================

CREATE OR REPLACE VIEW v_approval_queue_summary AS
SELECT 
    p.id AS project_id,
    p.project_number,
    p.project_name,
    c.client_name,
    p.project_lead,
    COUNT(*) AS pending_count,
    SUM(COALESCE(a.actual_hours, a.quoted_hours, 0)) AS pending_hours,
    MIN(a.submitted_at) AS oldest_submission,
    MAX(a.submitted_at) AS newest_submission,
    SUM(CASE WHEN a.submitted_at < NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END) AS overdue_count
FROM apparatus a
JOIN scopes s ON a.scope_id = s.id
JOIN projects p ON s.project_id = p.id
JOIN clients c ON p.client_id = c.id
WHERE a.status = 'Pending Review'
GROUP BY p.id, p.project_number, p.project_name, c.client_name, p.project_lead
ORDER BY pending_count DESC;
