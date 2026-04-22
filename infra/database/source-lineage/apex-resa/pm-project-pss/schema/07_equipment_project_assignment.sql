-- ============================================================================
-- 07_equipment_project_assignment.sql
-- Equipment Project Assignment Enhancement
-- Adds project assignment capability and movement history tracking
-- Version: 1.0.0
-- Deployed: December 10, 2025
-- ============================================================================

-- ============================================================================
-- SECTION 1: EQUIPMENT TABLE ENHANCEMENT
-- ============================================================================

ALTER TABLE equipment
    ADD COLUMN IF NOT EXISTS current_project_id UUID REFERENCES projects(id),
    ADD COLUMN IF NOT EXISTS assignment_type VARCHAR(20) DEFAULT 'employee',
    ADD COLUMN IF NOT EXISTS last_movement_date TIMESTAMPTZ;

ALTER TABLE equipment
    ADD CONSTRAINT chk_assignment_type 
    CHECK (assignment_type IN ('employee', 'project', 'warehouse', 'maintenance'));

COMMENT ON COLUMN equipment.current_project_id IS 'Current project this equipment is assigned to';
COMMENT ON COLUMN equipment.assignment_type IS 'employee=tech, project=job site, warehouse=storage, maintenance=repair';

CREATE INDEX IF NOT EXISTS idx_equipment_current_project ON equipment(current_project_id);
CREATE INDEX IF NOT EXISTS idx_equipment_assignment_type ON equipment(assignment_type);

-- ============================================================================
-- SECTION 2: EQUIPMENT ASSIGNMENTS HISTORY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS equipment_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    assignment_type VARCHAR(20) NOT NULL,
    assigned_employee_id UUID REFERENCES employees(id),
    assigned_project_id UUID REFERENCES projects(id),
    assigned_location_id UUID REFERENCES locations(id),
    assigned_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    returned_date TIMESTAMPTZ,
    expected_return_date DATE,
    assigned_by UUID REFERENCES employees(id),
    returned_by UUID REFERENCES employees(id),
    reason TEXT,
    notes TEXT,
    condition_at_checkout VARCHAR(50),
    condition_at_return VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_eq_assignment_type 
        CHECK (assignment_type IN ('employee', 'project', 'warehouse', 'maintenance')),
    CONSTRAINT chk_assignment_target
        CHECK (
            (assignment_type = 'employee' AND assigned_employee_id IS NOT NULL) OR
            (assignment_type = 'project' AND assigned_project_id IS NOT NULL) OR
            (assignment_type = 'warehouse' AND assigned_location_id IS NOT NULL) OR
            (assignment_type = 'maintenance')
        )
);

CREATE INDEX IF NOT EXISTS idx_eq_assignments_equipment ON equipment_assignments(equipment_id);
CREATE INDEX IF NOT EXISTS idx_eq_assignments_employee ON equipment_assignments(assigned_employee_id);
CREATE INDEX IF NOT EXISTS idx_eq_assignments_project ON equipment_assignments(assigned_project_id);
CREATE INDEX IF NOT EXISTS idx_eq_assignments_active ON equipment_assignments(is_active) WHERE is_active = true;

COMMENT ON TABLE equipment_assignments IS 'History of equipment movements between employees, projects, and locations';

-- ============================================================================
-- SECTION 3: VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW v_equipment_current_status AS
SELECT 
    e.id AS equipment_id, e.equipment_number, e.equipment_name, e.category,
    e.manufacturer, e.model, e.serial_number, e.status, e.calibration_due,
    e.assignment_type,
    CASE e.assignment_type
        WHEN 'employee' THEN emp.first_name || ' ' || emp.last_name
        WHEN 'project' THEN p.project_name
        WHEN 'warehouse' THEN loc.location_name
        WHEN 'maintenance' THEN 'Out for Maintenance'
    END AS assigned_to,
    e.assigned_employee_id, e.current_project_id, p.project_number,
    e.location_id, loc.location_name, e.last_movement_date,
    CASE 
        WHEN e.calibration_due < CURRENT_DATE THEN 'OVERDUE'
        WHEN e.calibration_due < CURRENT_DATE + INTERVAL '30 days' THEN 'DUE_SOON'
        ELSE 'OK'
    END AS calibration_status
FROM equipment e
LEFT JOIN employees emp ON e.assigned_employee_id = emp.id
LEFT JOIN projects p ON e.current_project_id = p.id
LEFT JOIN locations loc ON e.location_id = loc.id
WHERE e.is_active = true;

CREATE OR REPLACE VIEW v_project_equipment AS
SELECT 
    p.id AS project_id, p.project_number, p.project_name, p.status AS project_status,
    e.id AS equipment_id, e.equipment_number, e.equipment_name, e.category,
    e.manufacturer, e.model, e.serial_number, e.status AS equipment_status,
    e.calibration_due, e.daily_rate, e.last_movement_date AS deployed_date,
    EXTRACT(DAY FROM NOW() - e.last_movement_date)::INTEGER AS days_on_site
FROM projects p
JOIN equipment e ON e.current_project_id = p.id
WHERE e.is_active = true AND e.assignment_type = 'project';

CREATE OR REPLACE VIEW v_equipment_movement_history AS
SELECT 
    ea.id AS assignment_id, e.equipment_number, e.equipment_name,
    ea.assignment_type,
    CASE ea.assignment_type
        WHEN 'employee' THEN emp.first_name || ' ' || emp.last_name
        WHEN 'project' THEN p.project_name
        WHEN 'warehouse' THEN loc.location_name
        WHEN 'maintenance' THEN 'Maintenance'
    END AS assigned_to,
    ea.assigned_date, ea.returned_date, ea.is_active,
    CASE 
        WHEN ea.returned_date IS NOT NULL 
        THEN EXTRACT(DAY FROM ea.returned_date - ea.assigned_date)::INTEGER
        ELSE EXTRACT(DAY FROM NOW() - ea.assigned_date)::INTEGER
    END AS days_assigned,
    ea.reason, ea.condition_at_checkout, ea.condition_at_return, ea.notes
FROM equipment_assignments ea
JOIN equipment e ON ea.equipment_id = e.id
LEFT JOIN employees emp ON ea.assigned_employee_id = emp.id
LEFT JOIN projects p ON ea.assigned_project_id = p.id
LEFT JOIN locations loc ON ea.assigned_location_id = loc.id;

-- ============================================================================
-- SECTION 4: TRIGGERS & RLS
-- ============================================================================

ALTER TABLE equipment_assignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Read equipment_assignments" ON equipment_assignments FOR SELECT USING (true);
CREATE POLICY "Manage equipment_assignments" ON equipment_assignments FOR ALL USING (true);

CREATE OR REPLACE FUNCTION update_equipment_on_assignment()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE equipment SET
            assignment_type = NEW.assignment_type,
            assigned_employee_id = NEW.assigned_employee_id,
            current_project_id = NEW.assigned_project_id,
            location_id = COALESCE(NEW.assigned_location_id, location_id),
            last_movement_date = NEW.assigned_date,
            updated_at = NOW()
        WHERE id = NEW.equipment_id;
    END IF;
    
    IF TG_OP = 'UPDATE' AND NEW.returned_date IS NOT NULL AND OLD.returned_date IS NULL THEN
        UPDATE equipment SET
            assignment_type = 'warehouse',
            assigned_employee_id = NULL,
            current_project_id = NULL,
            last_movement_date = NEW.returned_date,
            updated_at = NOW()
        WHERE id = NEW.equipment_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_equipment_assignment_sync ON equipment_assignments;
CREATE TRIGGER tr_equipment_assignment_sync
    AFTER INSERT OR UPDATE ON equipment_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_equipment_on_assignment();
