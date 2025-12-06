-- =============================================================================
-- RESA Power Platform - Test Data Population
-- =============================================================================
-- Run this AFTER 01_supabase_schema.sql
-- Creates sample data for testing
-- =============================================================================

-- =============================================================================
-- 1. LOCATIONS (RESA Branch Offices)
-- =============================================================================

INSERT INTO locations (id, location_name, abbreviation, code, region, city, state, is_active, sort_order) VALUES
    ('a0000000-0000-0000-0001-000000000001', 'Dallas', 'DAL', 'DAL', 'Texas', 'Dallas', 'TX', true, 1),
    ('a0000000-0000-0000-0001-000000000002', 'Houston', 'HOU', 'HOU', 'Texas', 'Houston', 'TX', true, 2),
    ('a0000000-0000-0000-0001-000000000003', 'San Antonio', 'SAT', 'SAT', 'Texas', 'San Antonio', 'TX', true, 3),
    ('a0000000-0000-0000-0001-000000000004', 'Denver', 'DEN', 'DEN', 'Mountain', 'Denver', 'CO', true, 4),
    ('a0000000-0000-0000-0001-000000000005', 'Phoenix', 'PHX', 'PHX', 'Southwest', 'Phoenix', 'AZ', true, 5);

-- =============================================================================
-- 2. CLIENTS
-- =============================================================================

INSERT INTO clients (id, client_name, client_code, city, state, phone, is_active) VALUES
    ('b0000000-0000-0000-0002-000000000001', 'Texas Industrial Corp', 'TIC', 'Houston', 'TX', '713-555-1000', true),
    ('b0000000-0000-0000-0002-000000000002', 'Southwest Manufacturing', 'SWM', 'Phoenix', 'AZ', '602-555-2000', true),
    ('b0000000-0000-0000-0002-000000000003', 'Mountain Power Systems', 'MPS', 'Denver', 'CO', '303-555-3000', true),
    ('b0000000-0000-0000-0002-000000000004', 'Gulf Energy Partners', 'GEP', 'Galveston', 'TX', '409-555-4000', true),
    ('b0000000-0000-0000-0002-000000000005', 'Lone Star Data Centers', 'LSDC', 'Dallas', 'TX', '214-555-5000', true);

-- =============================================================================
-- 3. SITES
-- =============================================================================

INSERT INTO sites (id, client_id, site_name, site_code, city, state, is_active) VALUES
    -- Texas Industrial Corp sites
    ('c0000000-0000-0000-0003-000000000001', 'b0000000-0000-0000-0002-000000000001', 'Houston Plant', 'TIC-HOU', 'Houston', 'TX', true),
    ('c0000000-0000-0000-0003-000000000002', 'b0000000-0000-0000-0002-000000000001', 'Baytown Facility', 'TIC-BAY', 'Baytown', 'TX', true),
    -- Southwest Manufacturing sites
    ('c0000000-0000-0000-0003-000000000003', 'b0000000-0000-0000-0002-000000000002', 'Phoenix Main', 'SWM-PHX', 'Phoenix', 'AZ', true),
    -- Mountain Power Systems sites
    ('c0000000-0000-0000-0003-000000000004', 'b0000000-0000-0000-0002-000000000003', 'Denver HQ', 'MPS-DEN', 'Denver', 'CO', true),
    -- Lone Star Data Centers sites
    ('c0000000-0000-0000-0003-000000000005', 'b0000000-0000-0000-0002-000000000005', 'Dallas DC1', 'LSDC-DC1', 'Dallas', 'TX', true),
    ('c0000000-0000-0000-0003-000000000006', 'b0000000-0000-0000-0002-000000000005', 'Dallas DC2', 'LSDC-DC2', 'Dallas', 'TX', true);

-- =============================================================================
-- 4. APPARATUS TYPE MASTER
-- =============================================================================

INSERT INTO apparatus_type_master (id, type_code, type_name, category, default_hours, is_active, sort_order) VALUES
    ('d0000000-0000-0000-0004-000000000001', 'ATS', 'Automatic Transfer Switch', 'Switches', 4.0, true, 1),
    ('d0000000-0000-0000-0004-000000000002', 'SWGR', 'Switchgear', 'Switchgear', 8.0, true, 2),
    ('d0000000-0000-0000-0004-000000000003', 'SWBD', 'Switchboard', 'Switchgear', 6.0, true, 3),
    ('d0000000-0000-0000-0004-000000000004', 'XFMR', 'Transformer', 'Transformers', 6.0, true, 4),
    ('d0000000-0000-0000-0004-000000000005', 'PDC', 'Power Distribution Cabinet', 'Distribution', 3.0, true, 5),
    ('d0000000-0000-0000-0004-000000000006', 'MCC', 'Motor Control Center', 'Motor Controls', 8.0, true, 6),
    ('d0000000-0000-0000-0004-000000000007', 'GEN', 'Generator', 'Generators', 4.0, true, 7),
    ('d0000000-0000-0000-0004-000000000008', 'UPS', 'Uninterruptible Power Supply', 'UPS', 4.0, true, 8),
    ('d0000000-0000-0000-0004-000000000009', 'CB-LV', 'Circuit Breaker - Low Voltage', 'Breakers', 2.0, true, 9),
    ('d0000000-0000-0000-0004-000000000010', 'CB-MV', 'Circuit Breaker - Medium Voltage', 'Breakers', 4.0, true, 10),
    ('d0000000-0000-0000-0004-000000000011', 'RELAY', 'Protective Relay', 'Protection', 2.0, true, 11),
    ('d0000000-0000-0000-0004-000000000012', 'CABLE', 'Cable System', 'Cables', 2.0, true, 12);

-- =============================================================================
-- 5. ESTIMATORS
-- =============================================================================

INSERT INTO estimators (id, estimator_name, email, location_id, is_active) VALUES
    ('e0000000-0000-0000-0005-000000000001', 'Mike Thompson', 'mthompson@resapower.com', 'a0000000-0000-0000-0001-000000000001', true),
    ('e0000000-0000-0000-0005-000000000002', 'Sarah Chen', 'schen@resapower.com', 'a0000000-0000-0000-0001-000000000002', true),
    ('e0000000-0000-0000-0005-000000000003', 'David Rodriguez', 'drodriguez@resapower.com', 'a0000000-0000-0000-0001-000000000004', true);

-- =============================================================================
-- 6. PROJECTS
-- =============================================================================

INSERT INTO projects (id, project_number, project_name, client_id, site_id, location_id, status, quote_date, start_date, end_date, contract_value, project_lead, estimator, is_active) VALUES
    -- Active project - LASNAP16 example
    ('f0000000-0000-0000-0006-000000000001', 'LASNAP16', 'Lone Star DC1 Annual Maintenance', 
     'b0000000-0000-0000-0002-000000000005', 'c0000000-0000-0000-0003-000000000005', 'a0000000-0000-0000-0001-000000000001',
     'Active', '2024-10-01', '2025-01-06', '2025-03-31', 285000.00, 'John Smith', 'Mike Thompson', true),
    
    -- Quoted project
    ('f0000000-0000-0000-0006-000000000002', 'TIC-2025-001', 'Houston Plant Switchgear Upgrade', 
     'b0000000-0000-0000-0002-000000000001', 'c0000000-0000-0000-0003-000000000001', 'a0000000-0000-0000-0001-000000000002',
     'Quoted', '2025-01-10', NULL, NULL, 425000.00, 'Sarah Chen', 'Sarah Chen', true),
    
    -- Completed project
    ('f0000000-0000-0000-0006-000000000003', 'SWM-2024-003', 'Phoenix Annual Testing', 
     'b0000000-0000-0000-0002-000000000002', 'c0000000-0000-0000-0003-000000000003', 'a0000000-0000-0000-0001-000000000005',
     'Complete', '2024-08-15', '2024-10-01', '2024-12-15', 175000.00, 'David Rodriguez', 'David Rodriguez', true),
    
    -- New project
    ('f0000000-0000-0000-0006-000000000004', 'MPS-2025-001', 'Denver HQ New Construction', 
     'b0000000-0000-0000-0002-000000000003', 'c0000000-0000-0000-0003-000000000004', 'a0000000-0000-0000-0001-000000000004',
     'Active', '2024-12-01', '2025-02-01', '2025-06-30', 550000.00, 'Mike Thompson', 'Mike Thompson', true);

-- =============================================================================
-- 7. SCOPES (for LASNAP16 project)
-- =============================================================================

INSERT INTO scopes (id, project_id, client_id, site_id, scope_number, scope_name, scope_type, status, percent_complete, planned_start, planned_end, quoted_hours, quoted_revenue, sort_order, is_active) VALUES
    -- LASNAP16 Scopes
    ('g0000000-0000-0000-0007-000000000001', 'f0000000-0000-0000-0006-000000000001', 
     'b0000000-0000-0000-0002-000000000005', 'c0000000-0000-0000-0003-000000000005',
     'LASNAP16-01', 'UPS Systems Testing', 'UPS', 'In Progress', 65.00, '2025-01-06', '2025-01-24', 120.0, 45000.00, 1, true),
    
    ('g0000000-0000-0000-0007-000000000002', 'f0000000-0000-0000-0006-000000000001', 
     'b0000000-0000-0000-0002-000000000005', 'c0000000-0000-0000-0003-000000000005',
     'LASNAP16-02', 'ATS Systems', 'ATS', 'In Progress', 40.00, '2025-01-20', '2025-02-14', 80.0, 32000.00, 2, true),
    
    ('g0000000-0000-0000-0007-000000000003', 'f0000000-0000-0000-0006-000000000001', 
     'b0000000-0000-0000-0002-000000000005', 'c0000000-0000-0000-0003-000000000005',
     'LASNAP16-03', 'Main Switchgear', 'SWGR', 'Not Started', 0.00, '2025-02-10', '2025-03-07', 160.0, 72000.00, 3, true),
    
    ('g0000000-0000-0000-0007-000000000004', 'f0000000-0000-0000-0006-000000000001', 
     'b0000000-0000-0000-0002-000000000005', 'c0000000-0000-0000-0003-000000000005',
     'LASNAP16-04', 'Transformers', 'XFMR', 'Not Started', 0.00, '2025-02-24', '2025-03-14', 96.0, 48000.00, 4, true),
    
    ('g0000000-0000-0000-0007-000000000005', 'f0000000-0000-0000-0006-000000000001', 
     'b0000000-0000-0000-0002-000000000005', 'c0000000-0000-0000-0003-000000000005',
     'LASNAP16-05', 'Generator Systems', 'GEN', 'Not Started', 0.00, '2025-03-03', '2025-03-21', 64.0, 28000.00, 5, true),
    
    ('g0000000-0000-0000-0007-000000000006', 'f0000000-0000-0000-0006-000000000001', 
     'b0000000-0000-0000-0002-000000000005', 'c0000000-0000-0000-0003-000000000005',
     'LASNAP16-06', 'PDC Units', 'PDC', 'Not Started', 0.00, '2025-03-10', '2025-03-28', 80.0, 24000.00, 6, true);

-- =============================================================================
-- 8. TASKS (for first few scopes)
-- =============================================================================

INSERT INTO tasks (id, scope_id, task_number, task_name, task_type, status, percent_complete, planned_start, planned_end, estimated_hours, sort_order, is_active) VALUES
    -- UPS Systems Testing Tasks
    ('h0000000-0000-0000-0008-000000000001', 'g0000000-0000-0000-0007-000000000001', 
     '01', 'UPS-A Testing', 'Testing', 'Complete', 100.00, '2025-01-06', '2025-01-10', 24.0, 1, true),
    ('h0000000-0000-0000-0008-000000000002', 'g0000000-0000-0000-0007-000000000001', 
     '02', 'UPS-B Testing', 'Testing', 'Complete', 100.00, '2025-01-08', '2025-01-14', 24.0, 2, true),
    ('h0000000-0000-0000-0008-000000000003', 'g0000000-0000-0000-0007-000000000001', 
     '03', 'UPS-C Testing', 'Testing', 'In Progress', 50.00, '2025-01-13', '2025-01-17', 24.0, 3, true),
    ('h0000000-0000-0000-0008-000000000004', 'g0000000-0000-0000-0007-000000000001', 
     '04', 'UPS-D Testing', 'Testing', 'In Progress', 25.00, '2025-01-15', '2025-01-21', 24.0, 4, true),
    ('h0000000-0000-0000-0008-000000000005', 'g0000000-0000-0000-0007-000000000001', 
     '05', 'UPS-E Testing', 'Testing', 'Not Started', 0.00, '2025-01-20', '2025-01-24', 24.0, 5, true),
    
    -- ATS Systems Tasks
    ('h0000000-0000-0000-0008-000000000006', 'g0000000-0000-0000-0007-000000000002', 
     '01', 'ATS Bank 1', 'Testing', 'In Progress', 60.00, '2025-01-20', '2025-01-31', 40.0, 1, true),
    ('h0000000-0000-0000-0008-000000000007', 'g0000000-0000-0000-0007-000000000002', 
     '02', 'ATS Bank 2', 'Testing', 'Not Started', 0.00, '2025-02-03', '2025-02-14', 40.0, 2, true);

-- =============================================================================
-- 9. APPARATUS (equipment being tested)
-- =============================================================================

INSERT INTO apparatus (id, scope_id, task_id, apparatus_designation, apparatus_name, apparatus_type, status, assessment, percent_complete, anticipated_start, actual_start, quoted_hours, quoted_revenue, building, sort_order, is_active) VALUES
    -- UPS-A Task apparatus
    ('i0000000-0000-0000-0009-000000000001', 'g0000000-0000-0000-0007-000000000001', 'h0000000-0000-0000-0008-000000000001',
     'UPS-A1', 'UPS System A1', 'UPS', 'Complete', 'Pass', 100.00, '2025-01-06', '2025-01-06', 8.0, 3000.00, 'Building A', 1, true),
    ('i0000000-0000-0000-0009-000000000002', 'g0000000-0000-0000-0007-000000000001', 'h0000000-0000-0000-0008-000000000001',
     'UPS-A2', 'UPS System A2', 'UPS', 'Complete', 'Pass', 100.00, '2025-01-07', '2025-01-07', 8.0, 3000.00, 'Building A', 2, true),
    ('i0000000-0000-0000-0009-000000000003', 'g0000000-0000-0000-0007-000000000001', 'h0000000-0000-0000-0008-000000000001',
     'UPS-A3', 'UPS System A3', 'UPS', 'Complete', 'Needs Work', 100.00, '2025-01-08', '2025-01-08', 8.0, 3000.00, 'Building A', 3, true),
    
    -- UPS-B Task apparatus
    ('i0000000-0000-0000-0009-000000000004', 'g0000000-0000-0000-0007-000000000001', 'h0000000-0000-0000-0008-000000000002',
     'UPS-B1', 'UPS System B1', 'UPS', 'Complete', 'Pass', 100.00, '2025-01-08', '2025-01-08', 8.0, 3000.00, 'Building B', 1, true),
    ('i0000000-0000-0000-0009-000000000005', 'g0000000-0000-0000-0007-000000000001', 'h0000000-0000-0000-0008-000000000002',
     'UPS-B2', 'UPS System B2', 'UPS', 'Complete', 'Pass', 100.00, '2025-01-09', '2025-01-09', 8.0, 3000.00, 'Building B', 2, true),
    ('i0000000-0000-0000-0009-000000000006', 'g0000000-0000-0000-0007-000000000001', 'h0000000-0000-0000-0008-000000000002',
     'UPS-B3', 'UPS System B3', 'UPS', 'Complete', 'Pass', 100.00, '2025-01-13', '2025-01-13', 8.0, 3000.00, 'Building B', 3, true),
    
    -- UPS-C Task apparatus (in progress)
    ('i0000000-0000-0000-0009-000000000007', 'g0000000-0000-0000-0007-000000000001', 'h0000000-0000-0000-0008-000000000003',
     'UPS-C1', 'UPS System C1', 'UPS', 'Complete', 'Pass', 100.00, '2025-01-13', '2025-01-13', 8.0, 3000.00, 'Building C', 1, true),
    ('i0000000-0000-0000-0009-000000000008', 'g0000000-0000-0000-0007-000000000001', 'h0000000-0000-0000-0008-000000000003',
     'UPS-C2', 'UPS System C2', 'UPS', 'In Progress', NULL, 50.00, '2025-01-14', '2025-01-14', 8.0, 3000.00, 'Building C', 2, true),
    ('i0000000-0000-0000-0009-000000000009', 'g0000000-0000-0000-0007-000000000001', 'h0000000-0000-0000-0008-000000000003',
     'UPS-C3', 'UPS System C3', 'UPS', 'Not Started', NULL, 0.00, '2025-01-15', NULL, 8.0, 3000.00, 'Building C', 3, true),
    
    -- ATS Bank 1 apparatus
    ('i0000000-0000-0000-0009-000000000010', 'g0000000-0000-0000-0007-000000000002', 'h0000000-0000-0000-0008-000000000006',
     'ATS-01', 'Auto Transfer Switch 01', 'ATS', 'Complete', 'Pass', 100.00, '2025-01-20', '2025-01-20', 4.0, 1600.00, 'Building A', 1, true),
    ('i0000000-0000-0000-0009-000000000011', 'g0000000-0000-0000-0007-000000000002', 'h0000000-0000-0000-0008-000000000006',
     'ATS-02', 'Auto Transfer Switch 02', 'ATS', 'Complete', 'Pass', 100.00, '2025-01-21', '2025-01-21', 4.0, 1600.00, 'Building A', 2, true),
    ('i0000000-0000-0000-0009-000000000012', 'g0000000-0000-0000-0007-000000000002', 'h0000000-0000-0000-0008-000000000006',
     'ATS-03', 'Auto Transfer Switch 03', 'ATS', 'In Progress', NULL, 40.00, '2025-01-22', '2025-01-22', 4.0, 1600.00, 'Building B', 3, true),
    ('i0000000-0000-0000-0009-000000000013', 'g0000000-0000-0000-0007-000000000002', 'h0000000-0000-0000-0008-000000000006',
     'ATS-04', 'Auto Transfer Switch 04', 'ATS', 'Not Started', NULL, 0.00, '2025-01-23', NULL, 4.0, 1600.00, 'Building B', 4, true),
    ('i0000000-0000-0000-0009-000000000014', 'g0000000-0000-0000-0007-000000000002', 'h0000000-0000-0000-0008-000000000006',
     'ATS-05', 'Auto Transfer Switch 05', 'ATS', 'Not Started', NULL, 0.00, '2025-01-24', NULL, 4.0, 1600.00, 'Building C', 5, true);

-- =============================================================================
-- 10. EMPLOYEES (sample field techs)
-- =============================================================================

INSERT INTO employees (id, employee_number, first_name, last_name, email, location_id, job_title, department, role_type, hourly_rate, neta_certified, neta_level, is_active) VALUES
    ('j0000000-0000-0000-0010-000000000001', 'EMP001', 'John', 'Smith', 'jsmith@resapower.com', 
     'a0000000-0000-0000-0001-000000000001', 'Senior Field Technician', 'Field Services', 'Field Tech', 65.00, true, 'Level III', true),
    ('j0000000-0000-0000-0010-000000000002', 'EMP002', 'Maria', 'Garcia', 'mgarcia@resapower.com', 
     'a0000000-0000-0000-0001-000000000001', 'Field Technician', 'Field Services', 'Field Tech', 55.00, true, 'Level II', true),
    ('j0000000-0000-0000-0010-000000000003', 'EMP003', 'Robert', 'Johnson', 'rjohnson@resapower.com', 
     'a0000000-0000-0000-0001-000000000002', 'Senior Field Technician', 'Field Services', 'Field Tech', 65.00, true, 'Level III', true),
    ('j0000000-0000-0000-0010-000000000004', 'EMP004', 'Jennifer', 'Williams', 'jwilliams@resapower.com', 
     'a0000000-0000-0000-0001-000000000004', 'Project Manager', 'Operations', 'PM', 75.00, true, 'Level IV', true),
    ('j0000000-0000-0000-0010-000000000005', 'EMP005', 'Michael', 'Brown', 'mbrown@resapower.com', 
     'a0000000-0000-0000-0001-000000000005', 'Field Technician', 'Field Services', 'Field Tech', 50.00, true, 'Level I', true);

-- =============================================================================
-- SUMMARY QUERY (verify data loaded)
-- =============================================================================

SELECT 'Data Population Summary:' as info;
SELECT 'Locations: ' || COUNT(*) FROM locations;
SELECT 'Clients: ' || COUNT(*) FROM clients;
SELECT 'Sites: ' || COUNT(*) FROM sites;
SELECT 'Projects: ' || COUNT(*) FROM projects;
SELECT 'Scopes: ' || COUNT(*) FROM scopes;
SELECT 'Tasks: ' || COUNT(*) FROM tasks;
SELECT 'Apparatus: ' || COUNT(*) FROM apparatus;
SELECT 'Apparatus Types: ' || COUNT(*) FROM apparatus_type_master;
SELECT 'Estimators: ' || COUNT(*) FROM estimators;
SELECT 'Employees: ' || COUNT(*) FROM employees;
