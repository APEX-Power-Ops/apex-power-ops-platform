-- =============================================================================
-- RESA Power Platform - LASNAP16 Test Data
-- =============================================================================
-- File: 11_test_data.sql
-- Generated: 2025-12-05
-- Source: spec/TEST_DATA_PLAN.md, LASNAP16/RESA Power - LASNAP16 MASTER.xlsm
-- Run: AFTER 10_seed_data.sql
-- =============================================================================

-- UUID Pattern: {prefix}-0000-0000-0000-{seq}
-- Prefix key:
--   11111111 = clients
--   22222222 = sites
--   33333333 = projects
--   44444444 = scopes
--   55555555 = tasks
--   66666666 = apparatus
--   77777777 = employees
--   88888888 = resource_assignments
--   99999999 = apparatus_revenue
--   AAAAAAAA = scope_labor_details
-- 
-- Reference IDs from 10_seed_data.sql:
--   10000000-...-00000000000X = locations (Fenton=001)
--   20000000-...-00000000000X = apparatus_types

BEGIN;

-- =============================================================================
-- EMPLOYEES (5 test employees)
-- =============================================================================

INSERT INTO employees (id, employee_number, first_name, last_name, email, phone, location_id, job_title, role_type, hourly_rate, overtime_rate, neta_certified, neta_level, is_active) VALUES
('77777777-0000-0000-0000-000000000001', 'EMP001', 'Mike', 'Johnson', 'mike.johnson@resapower.com', '314-555-0101', '10000000-0000-0000-0000-000000000001', 'Lead Technician', 'Lead Tech', 95.00, 142.50, true, 'Level III', true),
('77777777-0000-0000-0000-000000000002', 'EMP002', 'Sarah', 'Chen', 'sarah.chen@resapower.com', '314-555-0102', '10000000-0000-0000-0000-000000000001', 'Field Technician', 'Field Tech', 75.00, 112.50, true, 'Level II', true),
('77777777-0000-0000-0000-000000000003', 'EMP003', 'David', 'Martinez', 'david.martinez@resapower.com', '314-555-0103', '10000000-0000-0000-0000-000000000001', 'Field Technician', 'Field Tech', 75.00, 112.50, true, 'Level II', true),
('77777777-0000-0000-0000-000000000004', 'EMP004', 'Jennifer', 'Williams', 'jennifer.williams@resapower.com', '314-555-0104', '10000000-0000-0000-0000-000000000001', 'Project Manager', 'Project Manager', 125.00, 187.50, false, NULL, true),
('77777777-0000-0000-0000-000000000005', 'EMP005', 'Robert', 'Taylor', 'robert.taylor@resapower.com', '314-555-0105', '10000000-0000-0000-0000-000000000001', 'Engineer', 'Engineer', 110.00, 165.00, true, 'Level IV', true);

-- =============================================================================
-- CLIENT
-- =============================================================================

INSERT INTO clients (id, client_name, client_code, address, city, state, zip, phone, email, is_active) VALUES
('11111111-0000-0000-0000-000000000001', 'Louisiana Snap Foods Corporation', 'LASNAP', '1234 Industrial Pkwy', 'Baton Rouge', 'LA', '70801', '225-555-1000', 'facilities@lasnapfoods.com', true);

-- =============================================================================
-- SITE
-- =============================================================================

INSERT INTO sites (id, client_id, site_name, site_code, address, city, state, zip, contact_name, contact_phone, contact_email, is_active) VALUES
('22222222-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', 'LASNAP Main Manufacturing Plant', 'LASNAP16-MAIN', '5678 Plant Road', 'Baton Rouge', 'LA', '70802', 'Tom Richards', '225-555-1100', 'trichards@lasnapfoods.com', true);

-- =============================================================================
-- PROJECT
-- =============================================================================

INSERT INTO projects (id, project_number, project_name, client_id, site_id, location_id, status, project_type, business_unit, quote_date, start_date, end_date, contract_value, po_number, project_lead, estimator, description, is_active) VALUES
('33333333-0000-0000-0000-000000000001', 'LASNAP16', 'LASNAP Foods - Annual Maintenance Testing 2016', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'Active', 'Annual Maintenance', 'Electrical Testing', '2016-01-15', '2016-02-01', '2016-06-30', 187500.00, 'PO-2016-4521', 'Mike Johnson', 'Jennifer Williams', 'Comprehensive annual NETA maintenance testing for main manufacturing facility including substations, switchgear, transformers, and motor control centers.', true);

-- =============================================================================
-- SCOPES (4 scopes for LASNAP16)
-- =============================================================================

INSERT INTO scopes (id, project_id, client_id, site_id, scope_number, scope_name, scope_type, status, planned_start, planned_end, quoted_hours, quoted_revenue, sort_order, is_active) VALUES
('44444444-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', 'LASNAP16-01', 'Main Substation Testing', 'SWGR', 'In Progress', '2016-02-01', '2016-02-28', 120.00, 52500.00, 1, true),
('44444444-0000-0000-0000-000000000002', '33333333-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', 'LASNAP16-02', 'Transformer Testing', 'XFMR', 'Not Started', '2016-03-01', '2016-03-31', 80.00, 45000.00, 2, true),
('44444444-0000-0000-0000-000000000003', '33333333-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', 'LASNAP16-03', 'MCC Testing Building A', 'MCC', 'Not Started', '2016-04-01', '2016-04-30', 100.00, 47500.00, 3, true),
('44444444-0000-0000-0000-000000000004', '33333333-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', 'LASNAP16-04', 'MCC Testing Building B', 'MCC', 'Not Started', '2016-05-01', '2016-05-31', 90.00, 42500.00, 4, true);

-- =============================================================================
-- TASKS (12 tasks across scopes)
-- =============================================================================

-- Scope 1: Main Substation Tasks
INSERT INTO tasks (id, scope_id, task_number, task_name, task_type, status, estimated_hours, sort_order, is_active) VALUES
('55555555-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', 'T-001', 'Main Switchgear Visual & Mechanical', 'Inspection', 'In Progress', 24.00, 1, true),
('55555555-0000-0000-0000-000000000002', '44444444-0000-0000-0000-000000000001', 'T-002', 'Main Switchgear Electrical Testing', 'Testing', 'Not Started', 48.00, 2, true),
('55555555-0000-0000-0000-000000000003', '44444444-0000-0000-0000-000000000001', 'T-003', 'Protective Relay Testing', 'Testing', 'Not Started', 48.00, 3, true);

-- Scope 2: Transformer Tasks
INSERT INTO tasks (id, scope_id, task_number, task_name, task_type, status, estimated_hours, sort_order, is_active) VALUES
('55555555-0000-0000-0000-000000000004', '44444444-0000-0000-0000-000000000002', 'T-004', 'Main Transformer T1 Testing', 'Testing', 'Not Started', 24.00, 1, true),
('55555555-0000-0000-0000-000000000005', '44444444-0000-0000-0000-000000000002', 'T-005', 'Main Transformer T2 Testing', 'Testing', 'Not Started', 24.00, 2, true),
('55555555-0000-0000-0000-000000000006', '44444444-0000-0000-0000-000000000002', 'T-006', 'Dry-Type Transformer Testing', 'Testing', 'Not Started', 32.00, 3, true);

-- Scope 3: MCC Building A Tasks
INSERT INTO tasks (id, scope_id, task_number, task_name, task_type, status, estimated_hours, sort_order, is_active) VALUES
('55555555-0000-0000-0000-000000000007', '44444444-0000-0000-0000-000000000003', 'T-007', 'MCC-A1 Testing', 'Testing', 'Not Started', 32.00, 1, true),
('55555555-0000-0000-0000-000000000008', '44444444-0000-0000-0000-000000000003', 'T-008', 'MCC-A2 Testing', 'Testing', 'Not Started', 32.00, 2, true),
('55555555-0000-0000-0000-000000000009', '44444444-0000-0000-0000-000000000003', 'T-009', 'MCC-A3 Testing', 'Testing', 'Not Started', 36.00, 3, true);

-- Scope 4: MCC Building B Tasks
INSERT INTO tasks (id, scope_id, task_number, task_name, task_type, status, estimated_hours, sort_order, is_active) VALUES
('55555555-0000-0000-0000-000000000010', '44444444-0000-0000-0000-000000000004', 'T-010', 'MCC-B1 Testing', 'Testing', 'Not Started', 30.00, 1, true),
('55555555-0000-0000-0000-000000000011', '44444444-0000-0000-0000-000000000004', 'T-011', 'MCC-B2 Testing', 'Testing', 'Not Started', 30.00, 2, true),
('55555555-0000-0000-0000-000000000012', '44444444-0000-0000-0000-000000000004', 'T-012', 'MCC-B3 Testing', 'Testing', 'Not Started', 30.00, 3, true);

-- =============================================================================
-- APPARATUS (47 equipment items)
-- =============================================================================

-- Scope 1 Apparatus: Main Substation (15 items)
INSERT INTO apparatus (id, scope_id, task_id, apparatus_designation, apparatus_name, apparatus_type, manufacturer, model, status, quoted_hours, quoted_revenue, building, room, sort_order, is_active) VALUES
-- Main Switchgear Visual/Mechanical (Task 1)
('66666666-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000001', 'SWGR-001', '15kV Main Switchgear', 'Switchgear', 'Square D', 'QED2', 'In Progress', 4.00, 1750.00, 'Substation', 'Main', 1, true),
('66666666-0000-0000-0000-000000000002', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000001', 'SWGR-002', '15kV Tie Switchgear', 'Switchgear', 'Square D', 'QED2', 'Not Started', 4.00, 1750.00, 'Substation', 'Main', 2, true),
('66666666-0000-0000-0000-000000000003', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000001', 'SWGR-003', '15kV Feeder Switchgear', 'Switchgear', 'Square D', 'QED2', 'Not Started', 4.00, 1750.00, 'Substation', 'Main', 3, true),
-- Main Switchgear Electrical Testing (Task 2)
('66666666-0000-0000-0000-000000000004', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-001', '15kV Main CB 52-1', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 4, true),
('66666666-0000-0000-0000-000000000005', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-002', '15kV Tie CB 52-T', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 5, true),
('66666666-0000-0000-0000-000000000006', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-003', '15kV Feeder CB 52-2', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 6, true),
('66666666-0000-0000-0000-000000000007', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-004', '15kV Feeder CB 52-3', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 7, true),
('66666666-0000-0000-0000-000000000008', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-005', '15kV Feeder CB 52-4', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 8, true),
('66666666-0000-0000-0000-000000000009', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-006', '15kV Spare CB', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 9, true),
-- Protective Relay Testing (Task 3)
('66666666-0000-0000-0000-000000000010', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-001', 'Main Overcurrent Relay 51-1', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 10, true),
('66666666-0000-0000-0000-000000000011', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-002', 'Tie Overcurrent Relay 51-T', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 11, true),
('66666666-0000-0000-0000-000000000012', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-003', 'Feeder Overcurrent Relay 51-2', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 12, true),
('66666666-0000-0000-0000-000000000013', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-004', 'Feeder Overcurrent Relay 51-3', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 13, true),
('66666666-0000-0000-0000-000000000014', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-005', 'Feeder Overcurrent Relay 51-4', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 14, true),
('66666666-0000-0000-0000-000000000015', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-006', 'Bus Differential Relay 87B', 'Protective Relay', 'SEL', '487E', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 15, true);

-- Scope 2 Apparatus: Transformers (8 items)
INSERT INTO apparatus (id, scope_id, task_id, apparatus_designation, apparatus_name, apparatus_type, manufacturer, model, status, quoted_hours, quoted_revenue, building, room, sort_order, is_active) VALUES
-- Main Transformer T1 Testing (Task 4)
('66666666-0000-0000-0000-000000000016', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000004', 'XFMR-001', 'Main Transformer T1', 'Transformer', 'ABB', 'PTG-3', 'Not Started', 12.00, 5250.00, 'Substation', 'Yard', 1, true),
('66666666-0000-0000-0000-000000000017', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000004', 'XFMR-001-LTC', 'T1 Load Tap Changer', 'LTC', 'ABB', 'UZF', 'Not Started', 6.00, 2625.00, 'Substation', 'Yard', 2, true),
('66666666-0000-0000-0000-000000000018', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000004', 'XFMR-001-FAN', 'T1 Cooling Fans', 'Cooling System', 'ABB', 'Standard', 'Not Started', 2.00, 875.00, 'Substation', 'Yard', 3, true),
-- Main Transformer T2 Testing (Task 5)
('66666666-0000-0000-0000-000000000019', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000005', 'XFMR-002', 'Main Transformer T2', 'Transformer', 'ABB', 'PTG-3', 'Not Started', 12.00, 5250.00, 'Substation', 'Yard', 4, true),
('66666666-0000-0000-0000-000000000020', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000005', 'XFMR-002-LTC', 'T2 Load Tap Changer', 'LTC', 'ABB', 'UZF', 'Not Started', 6.00, 2625.00, 'Substation', 'Yard', 5, true),
('66666666-0000-0000-0000-000000000021', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000005', 'XFMR-002-FAN', 'T2 Cooling Fans', 'Cooling System', 'ABB', 'Standard', 'Not Started', 2.00, 875.00, 'Substation', 'Yard', 6, true),
-- Dry-Type Transformer Testing (Task 6)
('66666666-0000-0000-0000-000000000022', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000006', 'DRY-001', 'Building A Main Dry Transformer', 'Dry Transformer', 'Square D', 'EE', 'Not Started', 4.00, 1750.00, 'Building A', 'Electrical', 7, true),
('66666666-0000-0000-0000-000000000023', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000006', 'DRY-002', 'Building B Main Dry Transformer', 'Dry Transformer', 'Square D', 'EE', 'Not Started', 4.00, 1750.00, 'Building B', 'Electrical', 8, true);

-- Scope 3 Apparatus: MCC Building A (12 items)
INSERT INTO apparatus (id, scope_id, task_id, apparatus_designation, apparatus_name, apparatus_type, manufacturer, model, status, quoted_hours, quoted_revenue, building, room, sort_order, is_active) VALUES
-- MCC-A1 Testing (Task 7)
('66666666-0000-0000-0000-000000000024', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000007', 'MCC-A1', 'MCC-A1 Bus/Structure', 'MCC', 'Allen Bradley', 'CENTERLINE', 'Not Started', 4.00, 1750.00, 'Building A', 'MCC Room 1', 1, true),
('66666666-0000-0000-0000-000000000025', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000007', 'MCC-A1-01', 'MCC-A1 Bucket 01 - Chiller 1', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 1', 2, true),
('66666666-0000-0000-0000-000000000026', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000007', 'MCC-A1-02', 'MCC-A1 Bucket 02 - Chiller 2', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 1', 3, true),
('66666666-0000-0000-0000-000000000027', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000007', 'MCC-A1-03', 'MCC-A1 Bucket 03 - AHU-1', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 1', 4, true),
-- MCC-A2 Testing (Task 8)
('66666666-0000-0000-0000-000000000028', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000008', 'MCC-A2', 'MCC-A2 Bus/Structure', 'MCC', 'Allen Bradley', 'CENTERLINE', 'Not Started', 4.00, 1750.00, 'Building A', 'MCC Room 2', 5, true),
('66666666-0000-0000-0000-000000000029', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000008', 'MCC-A2-01', 'MCC-A2 Bucket 01 - Pump 1', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 2', 6, true),
('66666666-0000-0000-0000-000000000030', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000008', 'MCC-A2-02', 'MCC-A2 Bucket 02 - Pump 2', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 2', 7, true),
('66666666-0000-0000-0000-000000000031', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000008', 'MCC-A2-03', 'MCC-A2 Bucket 03 - Compressor', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 2', 8, true),
-- MCC-A3 Testing (Task 9)
('66666666-0000-0000-0000-000000000032', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000009', 'MCC-A3', 'MCC-A3 Bus/Structure', 'MCC', 'Allen Bradley', 'CENTERLINE', 'Not Started', 4.00, 1750.00, 'Building A', 'MCC Room 3', 9, true),
('66666666-0000-0000-0000-000000000033', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000009', 'MCC-A3-01', 'MCC-A3 Bucket 01 - Conveyor 1', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 3', 10, true),
('66666666-0000-0000-0000-000000000034', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000009', 'MCC-A3-02', 'MCC-A3 Bucket 02 - Conveyor 2', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 3', 11, true),
('66666666-0000-0000-0000-000000000035', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000009', 'MCC-A3-03', 'MCC-A3 Bucket 03 - Mixer', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 3', 12, true);

-- Scope 4 Apparatus: MCC Building B (12 items)
INSERT INTO apparatus (id, scope_id, task_id, apparatus_designation, apparatus_name, apparatus_type, manufacturer, model, status, quoted_hours, quoted_revenue, building, room, sort_order, is_active) VALUES
-- MCC-B1 Testing (Task 10)
('66666666-0000-0000-0000-000000000036', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000010', 'MCC-B1', 'MCC-B1 Bus/Structure', 'MCC', 'Siemens', 'TiaSTAR', 'Not Started', 4.00, 1750.00, 'Building B', 'MCC Room 1', 1, true),
('66666666-0000-0000-0000-000000000037', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000010', 'MCC-B1-01', 'MCC-B1 Bucket 01 - Boiler Feed', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 1', 2, true),
('66666666-0000-0000-0000-000000000038', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000010', 'MCC-B1-02', 'MCC-B1 Bucket 02 - Condensate', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 1', 3, true),
('66666666-0000-0000-0000-000000000039', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000010', 'MCC-B1-03', 'MCC-B1 Bucket 03 - Blower', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 1', 4, true),
-- MCC-B2 Testing (Task 11)
('66666666-0000-0000-0000-000000000040', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000011', 'MCC-B2', 'MCC-B2 Bus/Structure', 'MCC', 'Siemens', 'TiaSTAR', 'Not Started', 4.00, 1750.00, 'Building B', 'MCC Room 2', 5, true),
('66666666-0000-0000-0000-000000000041', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000011', 'MCC-B2-01', 'MCC-B2 Bucket 01 - Package 1', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 2', 6, true),
('66666666-0000-0000-0000-000000000042', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000011', 'MCC-B2-02', 'MCC-B2 Bucket 02 - Package 2', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 2', 7, true),
('66666666-0000-0000-0000-000000000043', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000011', 'MCC-B2-03', 'MCC-B2 Bucket 03 - Package 3', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 2', 8, true),
-- MCC-B3 Testing (Task 12)
('66666666-0000-0000-0000-000000000044', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000012', 'MCC-B3', 'MCC-B3 Bus/Structure', 'MCC', 'Siemens', 'TiaSTAR', 'Not Started', 4.00, 1750.00, 'Building B', 'MCC Room 3', 9, true),
('66666666-0000-0000-0000-000000000045', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000012', 'MCC-B3-01', 'MCC-B3 Bucket 01 - Warehouse Fan', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 3', 10, true),
('66666666-0000-0000-0000-000000000046', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000012', 'MCC-B3-02', 'MCC-B3 Bucket 02 - Dock Door', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 3', 11, true),
('66666666-0000-0000-0000-000000000047', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000012', 'MCC-B3-03', 'MCC-B3 Bucket 03 - Lighting Panel', 'Panel', 'Siemens', 'P1', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 3', 12, true);

-- =============================================================================
-- RESOURCE ASSIGNMENTS (8 assignments)
-- =============================================================================

INSERT INTO resource_assignments (id, employee_id, project_id, scope_id, assignment_type, start_date, end_date, allocated_hours, is_primary, is_active) VALUES
-- Project-level assignments
('88888888-0000-0000-0000-000000000001', '77777777-0000-0000-0000-000000000004', '33333333-0000-0000-0000-000000000001', NULL, 'Primary', '2016-02-01', '2016-06-30', 40.00, true, true),
('88888888-0000-0000-0000-000000000002', '77777777-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', NULL, 'Primary', '2016-02-01', '2016-06-30', 200.00, true, true),
-- Scope-level assignments
('88888888-0000-0000-0000-000000000003', '77777777-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', 'Primary', '2016-02-01', '2016-02-28', 60.00, true, true),
('88888888-0000-0000-0000-000000000004', '77777777-0000-0000-0000-000000000002', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', 'Secondary', '2016-02-01', '2016-02-28', 60.00, false, true),
('88888888-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000002', 'Primary', '2016-03-01', '2016-03-31', 40.00, true, true),
('88888888-0000-0000-0000-000000000006', '77777777-0000-0000-0000-000000000003', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000002', 'Secondary', '2016-03-01', '2016-03-31', 40.00, false, true),
('88888888-0000-0000-0000-000000000007', '77777777-0000-0000-0000-000000000002', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000003', 'Primary', '2016-04-01', '2016-04-30', 100.00, true, true),
('88888888-0000-0000-0000-000000000008', '77777777-0000-0000-0000-000000000003', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000004', 'Primary', '2016-05-01', '2016-05-31', 90.00, true, true);

-- =============================================================================
-- SCOPE LABOR DETAILS (labor breakdown per scope)
-- =============================================================================

INSERT INTO scope_labor_details (id, scope_id, labor_category, labor_description, quoted_hours, rate, is_active) VALUES
-- Scope 1: Main Substation
('AAAAAAAA-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', 'Lead Tech', 'Lead Technician Hours', 60.00, 95.00, true),
('AAAAAAAA-0000-0000-0000-000000000002', '44444444-0000-0000-0000-000000000001', 'Field Tech', 'Field Technician Hours', 60.00, 75.00, true),
-- Scope 2: Transformer
('AAAAAAAA-0000-0000-0000-000000000003', '44444444-0000-0000-0000-000000000002', 'Lead Tech', 'Lead Technician Hours', 40.00, 95.00, true),
('AAAAAAAA-0000-0000-0000-000000000004', '44444444-0000-0000-0000-000000000002', 'Field Tech', 'Field Technician Hours', 40.00, 75.00, true),
-- Scope 3: MCC Building A
('AAAAAAAA-0000-0000-0000-000000000005', '44444444-0000-0000-0000-000000000003', 'Field Tech', 'Field Technician Hours', 100.00, 75.00, true),
-- Scope 4: MCC Building B
('AAAAAAAA-0000-0000-0000-000000000006', '44444444-0000-0000-0000-000000000004', 'Field Tech', 'Field Technician Hours', 90.00, 75.00, true);

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

-- Verify record counts
SELECT 'Test Data Verification' AS section;
SELECT 'clients' AS entity, COUNT(*) AS count FROM clients WHERE id LIKE '11111111%'
UNION ALL SELECT 'sites', COUNT(*) FROM sites WHERE id LIKE '22222222%'
UNION ALL SELECT 'projects', COUNT(*) FROM projects WHERE id LIKE '33333333%'
UNION ALL SELECT 'scopes', COUNT(*) FROM scopes WHERE id LIKE '44444444%'
UNION ALL SELECT 'tasks', COUNT(*) FROM tasks WHERE id LIKE '55555555%'
UNION ALL SELECT 'apparatus', COUNT(*) FROM apparatus WHERE id LIKE '66666666%'
UNION ALL SELECT 'employees', COUNT(*) FROM employees WHERE id LIKE '77777777%'
UNION ALL SELECT 'resource_assignments', COUNT(*) FROM resource_assignments WHERE id LIKE '88888888%'
UNION ALL SELECT 'scope_labor_details', COUNT(*) FROM scope_labor_details WHERE id LIKE 'AAAAAAAA%';

-- Verify FK integrity
SELECT 'FK Integrity Check' AS section;
SELECT 'orphan_scopes' AS check_name, COUNT(*) AS orphan_count 
FROM scopes WHERE project_id NOT IN (SELECT id FROM projects)
UNION ALL
SELECT 'orphan_tasks', COUNT(*) FROM tasks WHERE scope_id NOT IN (SELECT id FROM scopes)
UNION ALL
SELECT 'orphan_apparatus', COUNT(*) FROM apparatus WHERE scope_id NOT IN (SELECT id FROM scopes);

COMMIT;

-- =============================================================================
-- POST-INSERT: Trigger Verification
-- =============================================================================
-- After running, verify rollup triggers worked:
-- SELECT project_number, total_apparatus_count FROM projects WHERE project_number = 'LASNAP16';
-- Expected: total_apparatus_count = 47

-- SELECT scope_number, total_apparatus_count FROM scopes WHERE project_id = '33333333-0000-0000-0000-000000000001';
-- Expected: Scope 1 = 15, Scope 2 = 8, Scope 3 = 12, Scope 4 = 12
