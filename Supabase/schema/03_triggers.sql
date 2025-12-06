-- =============================================================================
-- RESA Power Platform - Triggers
-- =============================================================================
-- File: 03_triggers.sql
-- Generated: 2025-12-05
-- Source: spec/TRIGGER_FLOWS.md v1.0.0
-- Run: AFTER 02_relationships.sql
-- =============================================================================

-- =============================================================================
-- 1. TIMESTAMP TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
DO $$
DECLARE
    tbl TEXT;
    tables TEXT[] := ARRAY[
        'locations', 'clients', 'sites', 'employees', 'projects', 
        'scopes', 'tasks', 'apparatus', 'equipment', 'resource_assignments',
        'estimators', 'apparatus_revenue', 'scope_labor_details',
        'scope_financial_summaries', 'project_financial_summaries',
        'neta_test_templates', 'apparatus_types', 'pss_engineers',
        'pss_document_templates', 'pss_studies', 'pss_documents', 'pss_rfis'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%s_updated_at ON %s;
            CREATE TRIGGER update_%s_updated_at
            BEFORE UPDATE ON %s
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', tbl, tbl, tbl, tbl);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 2. APPARATUS COUNT ROLLUPS
-- =============================================================================

-- 2.1 Task Apparatus Count
CREATE OR REPLACE FUNCTION update_task_apparatus_count()
RETURNS TRIGGER AS $$
DECLARE
    v_task_id UUID;
    v_old_task_id UUID;
BEGIN
    -- Handle DELETE
    IF TG_OP = 'DELETE' THEN
        v_task_id := OLD.task_id;
        IF v_task_id IS NOT NULL THEN
            UPDATE tasks 
            SET apparatus_count = (
                SELECT COUNT(*) FROM apparatus 
                WHERE task_id = v_task_id AND is_active = true
            )
            WHERE id = v_task_id;
        END IF;
        RETURN OLD;
    END IF;
    
    -- Handle UPDATE with task change
    IF TG_OP = 'UPDATE' AND OLD.task_id IS DISTINCT FROM NEW.task_id THEN
        -- Update old task
        IF OLD.task_id IS NOT NULL THEN
            UPDATE tasks 
            SET apparatus_count = (
                SELECT COUNT(*) FROM apparatus 
                WHERE task_id = OLD.task_id AND is_active = true
            )
            WHERE id = OLD.task_id;
        END IF;
    END IF;
    
    -- Update new/current task
    IF NEW.task_id IS NOT NULL THEN
        UPDATE tasks 
        SET apparatus_count = (
            SELECT COUNT(*) FROM apparatus 
            WHERE task_id = NEW.task_id AND is_active = true
        )
        WHERE id = NEW.task_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_apparatus_count_on_task
    AFTER INSERT OR UPDATE OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_task_apparatus_count();

-- 2.2 Scope Apparatus Count and Percent Complete
CREATE OR REPLACE FUNCTION update_scope_apparatus_counts()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
    v_total INTEGER;
    v_completed INTEGER;
BEGIN
    -- Determine scope_id
    v_scope_id := COALESCE(NEW.scope_id, OLD.scope_id);
    
    -- Handle scope change on UPDATE
    IF TG_OP = 'UPDATE' AND OLD.scope_id IS DISTINCT FROM NEW.scope_id THEN
        -- Update old scope
        SELECT COUNT(*), COUNT(*) FILTER (WHERE status = 'Complete')
        INTO v_total, v_completed
        FROM apparatus WHERE scope_id = OLD.scope_id AND is_active = true;
        
        UPDATE scopes SET
            total_apparatus_count = v_total,
            completed_apparatus_count = v_completed,
            percent_complete = CASE WHEN v_total > 0 THEN (v_completed::DECIMAL / v_total * 100) ELSE 0 END
        WHERE id = OLD.scope_id;
    END IF;
    
    -- Update current scope
    SELECT COUNT(*), COUNT(*) FILTER (WHERE status = 'Complete')
    INTO v_total, v_completed
    FROM apparatus WHERE scope_id = v_scope_id AND is_active = true;
    
    UPDATE scopes SET
        total_apparatus_count = v_total,
        completed_apparatus_count = v_completed,
        percent_complete = CASE WHEN v_total > 0 THEN (v_completed::DECIMAL / v_total * 100) ELSE 0 END
    WHERE id = v_scope_id;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_apparatus_count_on_scope
    AFTER INSERT OR UPDATE OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_scope_apparatus_counts();

-- 2.3 Project Apparatus Count (triggered by scope changes)
CREATE OR REPLACE FUNCTION update_project_apparatus_counts()
RETURNS TRIGGER AS $$
DECLARE
    v_project_id UUID;
    v_total INTEGER;
    v_completed INTEGER;
BEGIN
    v_project_id := NEW.project_id;
    
    SELECT 
        COALESCE(SUM(total_apparatus_count), 0),
        COALESCE(SUM(completed_apparatus_count), 0)
    INTO v_total, v_completed
    FROM scopes WHERE project_id = v_project_id AND is_active = true;
    
    UPDATE projects SET
        total_apparatus_count = v_total,
        completed_apparatus_count = v_completed,
        percent_complete = CASE WHEN v_total > 0 THEN (v_completed::DECIMAL / v_total * 100) ELSE 0 END
    WHERE id = v_project_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_project_counts_from_scope
    AFTER UPDATE OF total_apparatus_count, completed_apparatus_count ON scopes
    FOR EACH ROW EXECUTE FUNCTION update_project_apparatus_counts();

-- =============================================================================
-- 3. HOURS ROLLUPS
-- =============================================================================

-- 3.1 Scope Hours from Apparatus
CREATE OR REPLACE FUNCTION update_scope_hours_from_apparatus()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
BEGIN
    v_scope_id := COALESCE(NEW.scope_id, OLD.scope_id);
    
    UPDATE scopes
    SET actual_hours = (
        SELECT COALESCE(SUM(actual_hours), 0)
        FROM apparatus
        WHERE scope_id = v_scope_id AND is_active = true
    )
    WHERE id = v_scope_id;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_scope_hours_from_apparatus
    AFTER INSERT OR UPDATE OF actual_hours OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_scope_hours_from_apparatus();

-- =============================================================================
-- 4. REVENUE RECOGNITION
-- =============================================================================

CREATE OR REPLACE FUNCTION create_revenue_on_apparatus_complete()
RETURNS TRIGGER AS $$
BEGIN
    -- Only trigger when status changes TO 'Complete'
    IF NEW.status = 'Complete' AND (OLD.status IS NULL OR OLD.status != 'Complete') THEN
        -- Check if revenue record already exists
        IF NOT EXISTS (
            SELECT 1 FROM apparatus_revenue 
            WHERE apparatus_id = NEW.id AND revenue_type = 'Testing'
        ) THEN
            INSERT INTO apparatus_revenue (
                apparatus_id,
                scope_id,
                revenue_type,
                quoted_amount,
                recognized_amount,
                recognition_date,
                recognition_percent
            ) VALUES (
                NEW.id,
                NEW.scope_id,
                'Testing',
                COALESCE(NEW.quoted_revenue, 0),
                COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0),
                CURRENT_DATE,
                CASE WHEN COALESCE(NEW.quoted_revenue, 0) > 0 
                    THEN (COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0) / NEW.quoted_revenue * 100)
                    ELSE 100
                END
            );
        ELSE
            -- Update existing revenue record
            UPDATE apparatus_revenue
            SET recognized_amount = COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0),
                recognition_date = CURRENT_DATE,
                recognition_percent = CASE WHEN COALESCE(NEW.quoted_revenue, 0) > 0 
                    THEN (COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0) / NEW.quoted_revenue * 100)
                    ELSE 100
                END,
                updated_at = NOW()
            WHERE apparatus_id = NEW.id AND revenue_type = 'Testing';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_revenue_on_apparatus_complete
    AFTER UPDATE OF status ON apparatus
    FOR EACH ROW EXECUTE FUNCTION create_revenue_on_apparatus_complete();

-- =============================================================================
-- 5. FINANCIAL SUMMARY TRIGGERS
-- =============================================================================

-- 5.1 Scope Financial Summary
CREATE OR REPLACE FUNCTION update_scope_financial_summary()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
    v_quoted_rev DECIMAL(15,2);
    v_recognized_rev DECIMAL(15,2);
    v_labor_cost DECIMAL(15,2);
    v_quoted_hrs DECIMAL(10,2);
    v_actual_hrs DECIMAL(10,2);
BEGIN
    v_scope_id := COALESCE(NEW.scope_id, OLD.scope_id);
    
    -- Get revenue totals
    SELECT COALESCE(SUM(quoted_amount), 0), COALESCE(SUM(recognized_amount), 0)
    INTO v_quoted_rev, v_recognized_rev
    FROM apparatus_revenue WHERE scope_id = v_scope_id;
    
    -- Get labor cost
    SELECT COALESCE(SUM(cost), 0)
    INTO v_labor_cost
    FROM scope_labor_details WHERE scope_id = v_scope_id;
    
    -- Get hours from scope
    SELECT COALESCE(quoted_hours, 0), COALESCE(actual_hours, 0)
    INTO v_quoted_hrs, v_actual_hrs
    FROM scopes WHERE id = v_scope_id;
    
    -- Upsert financial summary
    INSERT INTO scope_financial_summaries (
        scope_id,
        total_quoted_revenue,
        total_recognized_revenue,
        revenue_recognition_percent,
        total_quoted_hours,
        total_actual_hours,
        hours_variance,
        total_labor_cost,
        gross_margin,
        gross_margin_percent,
        last_calculated_at
    ) VALUES (
        v_scope_id,
        v_quoted_rev,
        v_recognized_rev,
        CASE WHEN v_quoted_rev > 0 THEN (v_recognized_rev / v_quoted_rev * 100) ELSE 0 END,
        v_quoted_hrs,
        v_actual_hrs,
        v_actual_hrs - v_quoted_hrs,
        v_labor_cost,
        v_recognized_rev - v_labor_cost,
        CASE WHEN v_recognized_rev > 0 THEN ((v_recognized_rev - v_labor_cost) / v_recognized_rev * 100) ELSE 0 END,
        NOW()
    )
    ON CONFLICT (scope_id) DO UPDATE SET
        total_quoted_revenue = EXCLUDED.total_quoted_revenue,
        total_recognized_revenue = EXCLUDED.total_recognized_revenue,
        revenue_recognition_percent = EXCLUDED.revenue_recognition_percent,
        total_quoted_hours = EXCLUDED.total_quoted_hours,
        total_actual_hours = EXCLUDED.total_actual_hours,
        hours_variance = EXCLUDED.hours_variance,
        total_labor_cost = EXCLUDED.total_labor_cost,
        gross_margin = EXCLUDED.gross_margin,
        gross_margin_percent = EXCLUDED.gross_margin_percent,
        last_calculated_at = NOW(),
        updated_at = NOW();
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_scope_financial_from_revenue
    AFTER INSERT OR UPDATE OR DELETE ON apparatus_revenue
    FOR EACH ROW EXECUTE FUNCTION update_scope_financial_summary();

CREATE TRIGGER trg_scope_financial_from_labor
    AFTER INSERT OR UPDATE OR DELETE ON scope_labor_details
    FOR EACH ROW EXECUTE FUNCTION update_scope_financial_summary();

-- 5.2 Project Financial Summary
CREATE OR REPLACE FUNCTION update_project_financial_summary()
RETURNS TRIGGER AS $$
DECLARE
    v_project_id UUID;
BEGIN
    -- Get project_id from scope
    SELECT project_id INTO v_project_id
    FROM scopes WHERE id = NEW.scope_id;
    
    IF v_project_id IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Upsert project financial summary
    INSERT INTO project_financial_summaries (
        project_id,
        total_quoted_revenue,
        total_recognized_revenue,
        revenue_recognition_percent,
        total_quoted_hours,
        total_actual_hours,
        total_labor_cost,
        total_expense_cost,
        total_cost,
        gross_margin,
        gross_margin_percent,
        total_scopes,
        completed_scopes,
        last_calculated_at
    )
    SELECT 
        v_project_id,
        COALESCE(SUM(sfs.total_quoted_revenue), 0),
        COALESCE(SUM(sfs.total_recognized_revenue), 0),
        CASE WHEN SUM(sfs.total_quoted_revenue) > 0
            THEN (SUM(sfs.total_recognized_revenue) / SUM(sfs.total_quoted_revenue) * 100)
            ELSE 0
        END,
        COALESCE(SUM(sfs.total_quoted_hours), 0),
        COALESCE(SUM(sfs.total_actual_hours), 0),
        COALESCE(SUM(sfs.total_labor_cost), 0),
        COALESCE(SUM(sfs.total_expense_cost), 0),
        COALESCE(SUM(sfs.total_labor_cost), 0) + COALESCE(SUM(sfs.total_expense_cost), 0),
        COALESCE(SUM(sfs.gross_margin), 0),
        CASE WHEN SUM(sfs.total_recognized_revenue) > 0
            THEN (SUM(sfs.gross_margin) / SUM(sfs.total_recognized_revenue) * 100)
            ELSE 0
        END,
        (SELECT COUNT(*) FROM scopes WHERE project_id = v_project_id AND is_active = true),
        (SELECT COUNT(*) FROM scopes WHERE project_id = v_project_id AND status = 'Complete' AND is_active = true),
        NOW()
    FROM scope_financial_summaries sfs
    JOIN scopes s ON s.id = sfs.scope_id
    WHERE s.project_id = v_project_id AND s.is_active = true
    ON CONFLICT (project_id) DO UPDATE SET
        total_quoted_revenue = EXCLUDED.total_quoted_revenue,
        total_recognized_revenue = EXCLUDED.total_recognized_revenue,
        revenue_recognition_percent = EXCLUDED.revenue_recognition_percent,
        total_quoted_hours = EXCLUDED.total_quoted_hours,
        total_actual_hours = EXCLUDED.total_actual_hours,
        total_labor_cost = EXCLUDED.total_labor_cost,
        total_expense_cost = EXCLUDED.total_expense_cost,
        total_cost = EXCLUDED.total_cost,
        gross_margin = EXCLUDED.gross_margin,
        gross_margin_percent = EXCLUDED.gross_margin_percent,
        total_scopes = EXCLUDED.total_scopes,
        completed_scopes = EXCLUDED.completed_scopes,
        last_calculated_at = NOW(),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_project_financial_from_scope
    AFTER INSERT OR UPDATE ON scope_financial_summaries
    FOR EACH ROW EXECUTE FUNCTION update_project_financial_summary();

-- =============================================================================
-- 6. PSS PORTAL TRIGGERS
-- =============================================================================

-- 6.1 Log Study Status Changes
CREATE OR REPLACE FUNCTION log_pss_study_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO pss_activity_log (
            study_id,
            activity_type,
            activity_description,
            entity_type,
            entity_id,
            old_value,
            new_value,
            performed_at
        ) VALUES (
            NEW.id,
            'Status Change',
            'Study status changed from ' || COALESCE(OLD.status::TEXT, 'NULL') || ' to ' || NEW.status::TEXT,
            'pss_studies',
            NEW.id,
            OLD.status::TEXT,
            NEW.status::TEXT,
            NOW()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_study_status
    AFTER UPDATE OF status ON pss_studies
    FOR EACH ROW EXECUTE FUNCTION log_pss_study_status_change();

-- 6.2 Log Document Uploads
CREATE OR REPLACE FUNCTION log_pss_document_upload()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO pss_activity_log (
        study_id,
        activity_type,
        activity_description,
        entity_type,
        entity_id,
        new_value,
        performed_by,
        performed_at
    ) VALUES (
        NEW.study_id,
        'Document Upload',
        'Document uploaded: ' || NEW.document_name,
        'pss_documents',
        NEW.id,
        NEW.document_name,
        NEW.uploaded_by,
        NOW()
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_document_upload
    AFTER INSERT ON pss_documents
    FOR EACH ROW EXECUTE FUNCTION log_pss_document_upload();

-- =============================================================================
-- VERIFICATION
-- =============================================================================

SELECT 'All triggers created successfully!' AS status;

SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_timing
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;
