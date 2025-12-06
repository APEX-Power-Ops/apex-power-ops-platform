# Trigger Flows

**Version:** 1.0.0  
**Created:** December 5, 2025  
**Author:** Desktop Claude  
**Purpose:** PostgreSQL trigger definitions for automated calculations and data integrity

---

## Overview

Triggers handle four categories of automation:

1. **Timestamps:** Auto-update `updated_at` on record changes
2. **Status Propagation:** Cascade status changes up/down hierarchy
3. **Rollup Calculations:** Aggregate child values to parent summaries
4. **Revenue Recognition:** Calculate revenue when apparatus completes

---

## 1. Timestamp Triggers

### update_updated_at_column()

**Purpose:** Automatically set `updated_at` to current timestamp on any UPDATE.

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Apply to all tables:**

```sql
-- Tables requiring updated_at trigger
CREATE TRIGGER update_locations_updated_at
    BEFORE UPDATE ON locations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sites_updated_at
    BEFORE UPDATE ON sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scopes_updated_at
    BEFORE UPDATE ON scopes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_apparatus_updated_at
    BEFORE UPDATE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equipment_updated_at
    BEFORE UPDATE ON equipment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Continue for all tables with updated_at column...
```

---

## 2. Apparatus Count Rollups

### Task Apparatus Count

**Trigger:** When apparatus is inserted, updated, or deleted  
**Action:** Update task.apparatus_count

```sql
-- Add column if not exists
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS apparatus_count INTEGER DEFAULT 0;

CREATE OR REPLACE FUNCTION update_task_apparatus_count()
RETURNS TRIGGER AS $$
DECLARE
    v_task_id UUID;
BEGIN
    -- Determine which task_id to update
    IF TG_OP = 'DELETE' THEN
        v_task_id := OLD.task_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.task_id IS DISTINCT FROM NEW.task_id THEN
        -- Task changed, update both old and new
        IF OLD.task_id IS NOT NULL THEN
            UPDATE tasks 
            SET apparatus_count = (
                SELECT COUNT(*) FROM apparatus 
                WHERE task_id = OLD.task_id AND is_active = true
            )
            WHERE id = OLD.task_id;
        END IF;
        v_task_id := NEW.task_id;
    ELSE
        v_task_id := COALESCE(NEW.task_id, OLD.task_id);
    END IF;
    
    -- Update the task count
    IF v_task_id IS NOT NULL THEN
        UPDATE tasks 
        SET apparatus_count = (
            SELECT COUNT(*) FROM apparatus 
            WHERE task_id = v_task_id AND is_active = true
        )
        WHERE id = v_task_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_apparatus_count_on_task
    AFTER INSERT OR UPDATE OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_task_apparatus_count();
```

---

### Scope Apparatus Count

**Trigger:** When apparatus is inserted, updated, or deleted  
**Action:** Update scope totals

```sql
-- Add columns if not exists
ALTER TABLE scopes ADD COLUMN IF NOT EXISTS total_apparatus_count INTEGER DEFAULT 0;
ALTER TABLE scopes ADD COLUMN IF NOT EXISTS completed_apparatus_count INTEGER DEFAULT 0;

CREATE OR REPLACE FUNCTION update_scope_apparatus_counts()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
BEGIN
    -- Determine which scope_id to update
    IF TG_OP = 'DELETE' THEN
        v_scope_id := OLD.scope_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.scope_id IS DISTINCT FROM NEW.scope_id THEN
        -- Scope changed, update both
        UPDATE scopes 
        SET total_apparatus_count = (
                SELECT COUNT(*) FROM apparatus 
                WHERE scope_id = OLD.scope_id AND is_active = true
            ),
            completed_apparatus_count = (
                SELECT COUNT(*) FROM apparatus 
                WHERE scope_id = OLD.scope_id 
                AND status = 'Complete' AND is_active = true
            )
        WHERE id = OLD.scope_id;
        v_scope_id := NEW.scope_id;
    ELSE
        v_scope_id := COALESCE(NEW.scope_id, OLD.scope_id);
    END IF;
    
    -- Update scope counts
    UPDATE scopes 
    SET total_apparatus_count = (
            SELECT COUNT(*) FROM apparatus 
            WHERE scope_id = v_scope_id AND is_active = true
        ),
        completed_apparatus_count = (
            SELECT COUNT(*) FROM apparatus 
            WHERE scope_id = v_scope_id 
            AND status = 'Complete' AND is_active = true
        ),
        percent_complete = CASE 
            WHEN (SELECT COUNT(*) FROM apparatus WHERE scope_id = v_scope_id AND is_active = true) > 0
            THEN (
                SELECT COUNT(*)::DECIMAL * 100 / 
                    NULLIF((SELECT COUNT(*) FROM apparatus WHERE scope_id = v_scope_id AND is_active = true), 0)
                FROM apparatus 
                WHERE scope_id = v_scope_id AND status = 'Complete' AND is_active = true
            )
            ELSE 0
        END
    WHERE id = v_scope_id;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_apparatus_count_on_scope
    AFTER INSERT OR UPDATE OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_scope_apparatus_counts();
```

---

### Project Apparatus Count

**Trigger:** When scope counts change  
**Action:** Update project totals

```sql
-- Add columns if not exists
ALTER TABLE projects ADD COLUMN IF NOT EXISTS total_apparatus_count INTEGER DEFAULT 0;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS completed_apparatus_count INTEGER DEFAULT 0;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS percent_complete DECIMAL(5,2) DEFAULT 0;

CREATE OR REPLACE FUNCTION update_project_apparatus_counts()
RETURNS TRIGGER AS $$
BEGIN
    -- Update project counts from all scopes
    UPDATE projects 
    SET total_apparatus_count = (
            SELECT COALESCE(SUM(total_apparatus_count), 0)
            FROM scopes WHERE project_id = NEW.project_id AND is_active = true
        ),
        completed_apparatus_count = (
            SELECT COALESCE(SUM(completed_apparatus_count), 0)
            FROM scopes WHERE project_id = NEW.project_id AND is_active = true
        ),
        percent_complete = CASE
            WHEN (SELECT COALESCE(SUM(total_apparatus_count), 0) FROM scopes WHERE project_id = NEW.project_id AND is_active = true) > 0
            THEN (
                SELECT COALESCE(SUM(completed_apparatus_count), 0)::DECIMAL * 100 /
                    NULLIF(COALESCE(SUM(total_apparatus_count), 0), 0)
                FROM scopes WHERE project_id = NEW.project_id AND is_active = true
            )
            ELSE 0
        END
    WHERE id = NEW.project_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_project_counts_from_scope
    AFTER UPDATE OF total_apparatus_count, completed_apparatus_count ON scopes
    FOR EACH ROW EXECUTE FUNCTION update_project_apparatus_counts();
```

---

## 3. Hours Rollups

### Scope Hours from Tasks

```sql
CREATE OR REPLACE FUNCTION update_scope_hours_from_tasks()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
BEGIN
    v_scope_id := COALESCE(NEW.scope_id, OLD.scope_id);
    
    UPDATE scopes
    SET actual_hours = (
        SELECT COALESCE(SUM(actual_hours), 0)
        FROM tasks
        WHERE scope_id = v_scope_id AND is_active = true
    )
    WHERE id = v_scope_id;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_scope_hours_from_tasks
    AFTER INSERT OR UPDATE OF actual_hours OR DELETE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_scope_hours_from_tasks();
```

---

### Scope Hours from Apparatus

```sql
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
```

---

## 4. Revenue Recognition Triggers

### Apparatus Completion → Revenue Record

**Trigger:** When apparatus.status changes to 'Complete'  
**Action:** Create apparatus_revenue record if not exists

```sql
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
                CASE WHEN NEW.quoted_revenue > 0 
                    THEN (COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0) / NEW.quoted_revenue * 100)
                    ELSE 100
                END
            );
        ELSE
            -- Update existing revenue record
            UPDATE apparatus_revenue
            SET recognized_amount = COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0),
                recognition_date = CURRENT_DATE,
                recognition_percent = CASE WHEN NEW.quoted_revenue > 0 
                    THEN (COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0) / NEW.quoted_revenue * 100)
                    ELSE 100
                END
            WHERE apparatus_id = NEW.id AND revenue_type = 'Testing';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_revenue_on_apparatus_complete
    AFTER UPDATE OF status ON apparatus
    FOR EACH ROW EXECUTE FUNCTION create_revenue_on_apparatus_complete();
```

---

## 5. Financial Summary Triggers

### Scope Financial Summary Update

**Trigger:** When apparatus_revenue or scope_labor_details change  
**Action:** Recalculate scope_financial_summaries

```sql
CREATE OR REPLACE FUNCTION update_scope_financial_summary()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
BEGIN
    -- Get the scope_id
    v_scope_id := COALESCE(NEW.scope_id, OLD.scope_id);
    
    -- Upsert scope financial summary
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
    )
    SELECT 
        v_scope_id,
        COALESCE(s.quoted_revenue, 0),
        COALESCE(SUM(ar.recognized_amount), 0),
        CASE WHEN COALESCE(s.quoted_revenue, 0) > 0 
            THEN (COALESCE(SUM(ar.recognized_amount), 0) / s.quoted_revenue * 100)
            ELSE 0
        END,
        COALESCE(s.quoted_hours, 0),
        COALESCE(s.actual_hours, 0),
        COALESCE(s.actual_hours, 0) - COALESCE(s.quoted_hours, 0),
        COALESCE(SUM(sld.cost), 0),
        COALESCE(SUM(ar.recognized_amount), 0) - COALESCE(SUM(sld.cost), 0),
        CASE WHEN COALESCE(SUM(ar.recognized_amount), 0) > 0
            THEN ((COALESCE(SUM(ar.recognized_amount), 0) - COALESCE(SUM(sld.cost), 0)) / SUM(ar.recognized_amount) * 100)
            ELSE 0
        END,
        NOW()
    FROM scopes s
    LEFT JOIN apparatus_revenue ar ON ar.scope_id = s.id
    LEFT JOIN scope_labor_details sld ON sld.scope_id = s.id
    WHERE s.id = v_scope_id
    GROUP BY s.id, s.quoted_revenue, s.quoted_hours, s.actual_hours
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
```

---

### Project Financial Summary Update

**Trigger:** When scope_financial_summaries change  
**Action:** Recalculate project_financial_summaries

```sql
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
```

---

## 6. PSS Portal Triggers

### Activity Log on Status Change

**Trigger:** When pss_studies.status changes  
**Action:** Insert activity log record

```sql
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
            'Study status changed from ' || COALESCE(OLD.status, 'NULL') || ' to ' || NEW.status,
            'pss_studies',
            NEW.id,
            OLD.status,
            NEW.status,
            NOW()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_study_status
    AFTER UPDATE OF status ON pss_studies
    FOR EACH ROW EXECUTE FUNCTION log_pss_study_status_change();
```

---

### Activity Log on Document Upload

```sql
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
```

---

## Trigger Execution Order

PostgreSQL executes triggers alphabetically by name within each timing category.

**Naming Convention:** `trg_{action}_{table}_{description}`

| Order | Trigger Name | Table | Timing |
|-------|--------------|-------|--------|
| 1 | trg_apparatus_count_on_scope | apparatus | AFTER INSERT/UPDATE/DELETE |
| 2 | trg_apparatus_count_on_task | apparatus | AFTER INSERT/UPDATE/DELETE |
| 3 | trg_log_document_upload | pss_documents | AFTER INSERT |
| 4 | trg_log_study_status | pss_studies | AFTER UPDATE |
| 5 | trg_project_counts_from_scope | scopes | AFTER UPDATE |
| 6 | trg_project_financial_from_scope | scope_financial_summaries | AFTER INSERT/UPDATE |
| 7 | trg_revenue_on_apparatus_complete | apparatus | AFTER UPDATE |
| 8 | trg_scope_financial_from_labor | scope_labor_details | AFTER INSERT/UPDATE/DELETE |
| 9 | trg_scope_financial_from_revenue | apparatus_revenue | AFTER INSERT/UPDATE/DELETE |
| 10 | trg_scope_hours_from_apparatus | apparatus | AFTER INSERT/UPDATE/DELETE |
| 11 | trg_scope_hours_from_tasks | tasks | AFTER INSERT/UPDATE/DELETE |
| 12 | update_*_updated_at | all tables | BEFORE UPDATE |

---

## Testing Triggers

### Test Apparatus Count Rollup

```sql
-- Create test data
INSERT INTO scopes (id, project_id, scope_name) 
VALUES ('11111111-0000-0000-0000-000000000001', 
        '33333333-0000-0000-0000-000000000001', 
        'Test Scope');

INSERT INTO apparatus (scope_id, apparatus_designation) 
VALUES ('11111111-0000-0000-0000-000000000001', 'TEST-01');

-- Verify count
SELECT scope_name, total_apparatus_count 
FROM scopes WHERE id = '11111111-0000-0000-0000-000000000001';
-- Expected: total_apparatus_count = 1
```

### Test Revenue Recognition

```sql
-- Update apparatus to complete
UPDATE apparatus 
SET status = 'Complete', quoted_revenue = 1000, actual_revenue = 1000
WHERE apparatus_designation = 'TEST-01';

-- Verify revenue record created
SELECT * FROM apparatus_revenue WHERE apparatus_id = (
    SELECT id FROM apparatus WHERE apparatus_designation = 'TEST-01'
);
-- Expected: One record with recognized_amount = 1000
```

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-05 | Desktop Claude | Initial creation |

---

*Trigger Flows v1.0.0 | RESA Power Supabase Migration*
