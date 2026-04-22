-- =============================================================================
-- RESA Power Platform - PSS Portal Test Data
-- =============================================================================
-- File: 12_pss_test_data.sql
-- Generated: 2025-12-05
-- Source: spec/TEST_DATA_PLAN.md
-- Run: AFTER 11_test_data.sql
-- =============================================================================

-- UUID Pattern: {prefix}-0000-0000-0000-{seq}
-- Prefix key:
--   BBBBBBBB = pss_engineers
--   CCCCCCCC = pss_document_templates
--   DDDDDDDD = pss_studies
--   EEEEEEEE = pss_documents
--   FFFFFFFF = pss_rfis

BEGIN;

-- =============================================================================
-- PSS ENGINEERS (3 external engineers)
-- =============================================================================

INSERT INTO pss_engineers (id, engineer_name, company, email, phone, specialization, pe_license, pe_state, is_active) VALUES
('BBBBBBBB-0000-0000-0000-000000000001', 'Dr. James Patterson', 'Patterson Power Engineering', 'jpatterson@ppegroup.com', '512-555-0201', 'Arc Flash Analysis', 'PE-48291', 'TX', true),
('BBBBBBBB-0000-0000-0000-000000000002', 'Maria Rodriguez, PE', 'Southwest Engineering Solutions', 'mrodriguez@swes.com', '480-555-0202', 'Coordination Studies', 'PE-33847', 'AZ', true),
('BBBBBBBB-0000-0000-0000-000000000003', 'Robert Chang, PE', 'Chang Consulting Engineers', 'rchang@cce-power.com', '314-555-0203', 'Short Circuit Analysis', 'PE-52910', 'MO', true);

-- =============================================================================
-- PSS DOCUMENT TEMPLATES (8 templates)
-- =============================================================================

INSERT INTO pss_document_templates (id, template_code, template_name, document_type, description, sort_order, is_active) VALUES
('CCCCCCCC-0000-0000-0000-000000000001', 'TPL-SR', 'Study Report Template', 'Study Report', 'Standard template for comprehensive study reports', 1, true),
('CCCCCCCC-0000-0000-0000-000000000002', 'TPL-OLD', 'One-Line Diagram Template', 'One-Line Diagram', 'AutoCAD template for electrical one-line diagrams', 2, true),
('CCCCCCCC-0000-0000-0000-000000000003', 'TPL-DC', 'Data Collection Form', 'Data Collection', 'Field data collection form for equipment parameters', 3, true),
('CCCCCCCC-0000-0000-0000-000000000004', 'TPL-CALC', 'Calculation Sheet', 'Calculations', 'Excel template for engineering calculations', 4, true),
('CCCCCCCC-0000-0000-0000-000000000005', 'TPL-ES', 'Equipment Schedule Template', 'Equipment Schedule', 'Equipment database schedule template', 5, true),
('CCCCCCCC-0000-0000-0000-000000000006', 'TPL-AFL', 'Arc Flash Label Template', 'Arc Flash Labels', 'NFPA 70E compliant arc flash label template', 6, true),
('CCCCCCCC-0000-0000-0000-000000000007', 'TPL-CC', 'Coordination Curves Template', 'Coordination Curves', 'SKM/ETAP coordination curve export template', 7, true),
('CCCCCCCC-0000-0000-0000-000000000008', 'TPL-CVR', 'Cover Letter Template', 'Cover Letter', 'Standard project transmittal cover letter', 8, true);

-- =============================================================================
-- PSS STUDIES (5 studies across different statuses)
-- =============================================================================

INSERT INTO pss_studies (id, project_id, study_number, study_name, study_type, status, priority, engineer_id, requested_date, due_date, completed_date, description, is_active) VALUES
-- Study 1: Completed Arc Flash
('DDDDDDDD-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', 'PSS-2016-001', 'LASNAP Foods Arc Flash Analysis', 'Arc Flash', 'Completed', 'High', 'BBBBBBBB-0000-0000-0000-000000000001', '2016-01-15', '2016-02-15', '2016-02-10', 'Comprehensive arc flash hazard analysis for main substation and building MCCs per IEEE 1584-2018 and NFPA 70E-2024.', true),

-- Study 2: In Progress Coordination
('DDDDDDDD-0000-0000-0000-000000000002', '33333333-0000-0000-0000-000000000001', 'PSS-2016-002', 'LASNAP Foods Protective Device Coordination', 'Coordination', 'In Progress', 'High', 'BBBBBBBB-0000-0000-0000-000000000002', '2016-02-01', '2016-03-15', NULL, 'Time-current coordination study for main-tie-main switchgear and downstream protection. Includes relay settings recommendations.', true),

-- Study 3: Pending Short Circuit
('DDDDDDDD-0000-0000-0000-000000000003', '33333333-0000-0000-0000-000000000001', 'PSS-2016-003', 'LASNAP Foods Short Circuit Study', 'Short Circuit', 'Pending', 'Medium', 'BBBBBBBB-0000-0000-0000-000000000003', '2016-02-15', '2016-04-01', NULL, 'Short circuit analysis to verify equipment ratings and determine available fault currents at key points in the distribution system.', true),

-- Study 4: Data Collection Load Flow
('DDDDDDDD-0000-0000-0000-000000000004', '33333333-0000-0000-0000-000000000001', 'PSS-2016-004', 'LASNAP Foods Load Flow Analysis', 'Load Flow', 'Data Collection', 'Low', NULL, '2016-03-01', '2016-05-01', NULL, 'Load flow study to identify voltage drop issues and optimize transformer tap settings. Pending field measurements.', true),

-- Study 5: On Hold Comprehensive
('DDDDDDDD-0000-0000-0000-000000000005', NULL, 'PSS-2016-005', 'Generic Facility Comprehensive Study', 'Comprehensive', 'On Hold', 'Low', NULL, '2016-01-01', '2016-06-01', NULL, 'Comprehensive study template for future projects. Currently on hold pending project assignment.', true);

-- =============================================================================
-- PSS DOCUMENTS (15 documents, ~3 per study)
-- =============================================================================

INSERT INTO pss_documents (id, study_id, template_id, document_name, document_type, version, status, file_path, file_size, uploaded_by, uploaded_at, is_active) VALUES
-- Study 1: Arc Flash (Completed) - 4 documents
('EEEEEEEE-0000-0000-0000-000000000001', 'DDDDDDDD-0000-0000-0000-000000000001', 'CCCCCCCC-0000-0000-0000-000000000001', 'LASNAP16 Arc Flash Study Report v2.1', 'Study Report', '2.1', 'Approved', '/studies/PSS-2016-001/LASNAP16_ArcFlash_Report_v2.1.pdf', 4521890, '77777777-0000-0000-0000-000000000005', '2016-02-08 14:30:00', true),
('EEEEEEEE-0000-0000-0000-000000000002', 'DDDDDDDD-0000-0000-0000-000000000001', 'CCCCCCCC-0000-0000-0000-000000000002', 'LASNAP16 One-Line Diagram', 'One-Line Diagram', '1.0', 'Approved', '/studies/PSS-2016-001/LASNAP16_OneLine.dwg', 2145678, '77777777-0000-0000-0000-000000000005', '2016-01-20 09:15:00', true),
('EEEEEEEE-0000-0000-0000-000000000003', 'DDDDDDDD-0000-0000-0000-000000000001', 'CCCCCCCC-0000-0000-0000-000000000006', 'LASNAP16 Arc Flash Labels Package', 'Arc Flash Labels', '1.0', 'Approved', '/studies/PSS-2016-001/LASNAP16_ArcFlash_Labels.pdf', 892456, '77777777-0000-0000-0000-000000000005', '2016-02-09 16:45:00', true),
('EEEEEEEE-0000-0000-0000-000000000004', 'DDDDDDDD-0000-0000-0000-000000000001', 'CCCCCCCC-0000-0000-0000-000000000005', 'LASNAP16 Equipment Schedule', 'Equipment Schedule', '1.2', 'Approved', '/studies/PSS-2016-001/LASNAP16_Equipment_Schedule.xlsx', 456789, '77777777-0000-0000-0000-000000000005', '2016-02-05 11:20:00', true),

-- Study 2: Coordination (In Progress) - 4 documents
('EEEEEEEE-0000-0000-0000-000000000005', 'DDDDDDDD-0000-0000-0000-000000000002', 'CCCCCCCC-0000-0000-0000-000000000003', 'LASNAP16 Data Collection - Relay Settings', 'Data Collection', '1.0', 'Approved', '/studies/PSS-2016-002/LASNAP16_Data_RelaySettings.xlsx', 234567, '77777777-0000-0000-0000-000000000002', '2016-02-05 10:00:00', true),
('EEEEEEEE-0000-0000-0000-000000000006', 'DDDDDDDD-0000-0000-0000-000000000002', 'CCCCCCCC-0000-0000-0000-000000000007', 'LASNAP16 Coordination Curves - Draft', 'Coordination Curves', '0.9', 'In Review', '/studies/PSS-2016-002/LASNAP16_Coordination_Draft.pdf', 1567890, '77777777-0000-0000-0000-000000000005', '2016-02-28 15:30:00', true),
('EEEEEEEE-0000-0000-0000-000000000007', 'DDDDDDDD-0000-0000-0000-000000000002', 'CCCCCCCC-0000-0000-0000-000000000001', 'LASNAP16 Coordination Report - Draft', 'Study Report', '0.8', 'Draft', '/studies/PSS-2016-002/LASNAP16_Coordination_Report_Draft.docx', 2345678, '77777777-0000-0000-0000-000000000005', '2016-03-01 09:00:00', true),
('EEEEEEEE-0000-0000-0000-000000000008', 'DDDDDDDD-0000-0000-0000-000000000002', 'CCCCCCCC-0000-0000-0000-000000000004', 'LASNAP16 TCC Calculations', 'Calculations', '1.0', 'In Review', '/studies/PSS-2016-002/LASNAP16_TCC_Calcs.xlsx', 567890, '77777777-0000-0000-0000-000000000005', '2016-02-25 14:00:00', true),

-- Study 3: Short Circuit (Pending) - 3 documents
('EEEEEEEE-0000-0000-0000-000000000009', 'DDDDDDDD-0000-0000-0000-000000000003', 'CCCCCCCC-0000-0000-0000-000000000002', 'LASNAP16 One-Line (Copy for SC Study)', 'One-Line Diagram', '1.0', 'Approved', '/studies/PSS-2016-003/LASNAP16_OneLine_SC.dwg', 2145678, '77777777-0000-0000-0000-000000000005', '2016-02-16 10:00:00', true),
('EEEEEEEE-0000-0000-0000-000000000010', 'DDDDDDDD-0000-0000-0000-000000000003', 'CCCCCCCC-0000-0000-0000-000000000003', 'LASNAP16 Data Collection - Utility Info', 'Data Collection', '1.0', 'Draft', '/studies/PSS-2016-003/LASNAP16_Data_Utility.xlsx', 123456, '77777777-0000-0000-0000-000000000002', '2016-02-18 11:30:00', true),
('EEEEEEEE-0000-0000-0000-000000000011', 'DDDDDDDD-0000-0000-0000-000000000003', 'CCCCCCCC-0000-0000-0000-000000000005', 'LASNAP16 Equipment Schedule (Copy)', 'Equipment Schedule', '1.2', 'Approved', '/studies/PSS-2016-003/LASNAP16_Equipment_Schedule_SC.xlsx', 456789, '77777777-0000-0000-0000-000000000005', '2016-02-16 10:05:00', true),

-- Study 4: Load Flow (Data Collection) - 3 documents
('EEEEEEEE-0000-0000-0000-000000000012', 'DDDDDDDD-0000-0000-0000-000000000004', 'CCCCCCCC-0000-0000-0000-000000000003', 'LASNAP16 Data Collection - Load Data', 'Data Collection', '0.5', 'Draft', '/studies/PSS-2016-004/LASNAP16_Data_Loads.xlsx', 234567, '77777777-0000-0000-0000-000000000002', '2016-03-05 09:00:00', true),
('EEEEEEEE-0000-0000-0000-000000000013', 'DDDDDDDD-0000-0000-0000-000000000004', 'CCCCCCCC-0000-0000-0000-000000000002', 'LASNAP16 One-Line (Load Flow)', 'One-Line Diagram', '1.0', 'Approved', '/studies/PSS-2016-004/LASNAP16_OneLine_LF.dwg', 2145678, '77777777-0000-0000-0000-000000000005', '2016-03-02 14:00:00', true),

-- Study 5: Comprehensive (On Hold) - 1 document
('EEEEEEEE-0000-0000-0000-000000000014', 'DDDDDDDD-0000-0000-0000-000000000005', 'CCCCCCCC-0000-0000-0000-000000000001', 'Comprehensive Study Template', 'Study Report', '1.0', 'Draft', '/templates/Comprehensive_Study_Template.docx', 345678, '77777777-0000-0000-0000-000000000005', '2016-01-02 08:00:00', true);

-- =============================================================================
-- PSS RFIs (10 RFIs across studies)
-- =============================================================================

INSERT INTO pss_rfis (id, study_id, rfi_number, subject, question, response, status, priority, requested_by, assigned_to, requested_date, due_date, responded_date, is_active) VALUES
-- Study 1: Arc Flash RFIs (Closed)
('FFFFFFFF-0000-0000-0000-000000000001', 'DDDDDDDD-0000-0000-0000-000000000001', 'RFI-001', 'Utility Available Fault Current', 'Please provide the available fault current from the utility at the main service entrance (Point of Common Coupling).', 'Per utility letter dated 2016-01-25: Available 3-phase fault current is 12,500 amps at 13.8kV. X/R ratio = 15.', 'Closed', 'High', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000004', '2016-01-18', '2016-01-25', '2016-01-25', true),
('FFFFFFFF-0000-0000-0000-000000000002', 'DDDDDDDD-0000-0000-0000-000000000001', 'RFI-002', 'Transformer T1 Impedance', 'What is the nameplate impedance of Main Transformer T1? Field data shows tag is unreadable.', 'Confirmed with ABB: T1 impedance is 5.75% on 2500 kVA base. See attached factory test report.', 'Closed', 'High', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-01-20', '2016-01-27', '2016-01-24', true),

-- Study 2: Coordination RFIs (Mix of statuses)
('FFFFFFFF-0000-0000-0000-000000000003', 'DDDDDDDD-0000-0000-0000-000000000002', 'RFI-003', 'Existing Relay Settings', 'Please provide current relay settings for SEL-751 relays at main switchgear positions 52-1, 52-T, and 52-2.', 'Settings provided via email on 2016-02-10. See attached Excel file with complete settings summary.', 'Closed', 'High', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-02-05', '2016-02-12', '2016-02-10', true),
('FFFFFFFF-0000-0000-0000-000000000004', 'DDDDDDDD-0000-0000-0000-000000000002', 'RFI-004', 'Motor Starting Current Data', 'Need locked rotor current and starting time for Chiller 1 and Chiller 2 motors for coordination with MCC feeder breakers.', 'Working with facilities to obtain motor data sheets. Expected by 2016-03-10.', 'In Progress', 'Medium', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-02-28', '2016-03-10', NULL, true),
('FFFFFFFF-0000-0000-0000-000000000005', 'DDDDDDDD-0000-0000-0000-000000000002', 'RFI-005', 'Future Expansion Plans', 'Are there any planned additions to the electrical system in the next 5 years that should be considered in the coordination study?', NULL, 'Open', 'Low', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000004', '2016-03-01', '2016-03-15', NULL, true),

-- Study 3: Short Circuit RFIs (Pending)
('FFFFFFFF-0000-0000-0000-000000000006', 'DDDDDDDD-0000-0000-0000-000000000003', 'RFI-006', 'Cable Lengths Main Feeder', 'Please provide cable lengths and sizes for feeders from main switchgear to Building A and Building B MCCs.', NULL, 'Open', 'High', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-02-20', '2016-03-01', NULL, true),
('FFFFFFFF-0000-0000-0000-000000000007', 'DDDDDDDD-0000-0000-0000-000000000003', 'RFI-007', 'Transformer T2 Test Report', 'Please provide factory test report for Transformer T2 showing impedance values.', NULL, 'Pending Info', 'Medium', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000004', '2016-02-22', '2016-03-05', NULL, true),

-- Study 4: Load Flow RFIs (Data Collection)
('FFFFFFFF-0000-0000-0000-000000000008', 'DDDDDDDD-0000-0000-0000-000000000004', 'RFI-008', 'Peak Demand Data', 'Please provide 12 months of peak demand data from utility bills for load flow baseline.', NULL, 'Open', 'Medium', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000004', '2016-03-05', '2016-03-20', NULL, true),
('FFFFFFFF-0000-0000-0000-000000000009', 'DDDDDDDD-0000-0000-0000-000000000004', 'RFI-009', 'Motor Load List', 'Please provide complete motor load list including HP ratings and duty cycles for all motors > 10 HP.', NULL, 'Open', 'Medium', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-03-05', '2016-03-20', NULL, true),

-- Study 5: Generic
('FFFFFFFF-0000-0000-0000-000000000010', 'DDDDDDDD-0000-0000-0000-000000000005', 'RFI-010', 'Template Review Request', 'Please review comprehensive study template and provide feedback on section organization.', 'Template approved with minor formatting suggestions. See marked-up PDF.', 'Answered', 'Low', '77777777-0000-0000-0000-000000000004', '77777777-0000-0000-0000-000000000005', '2016-01-05', '2016-01-15', '2016-01-12', true);

-- =============================================================================
-- PSS ACTIVITY LOG (25 audit entries)
-- =============================================================================

INSERT INTO pss_activity_log (id, study_id, activity_type, activity_description, entity_type, entity_id, old_value, new_value, performed_by, performed_at) VALUES
-- Study 1: Arc Flash Activity
('00000001-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Created', 'Study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', NULL, 'Pending', '77777777-0000-0000-0000-000000000004', '2016-01-15 09:00:00'),
('00000002-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Status Change', 'Study status changed', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', 'Pending', 'In Progress', '77777777-0000-0000-0000-000000000005', '2016-01-18 10:30:00'),
('00000003-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Document Upload', 'One-line diagram uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000002', NULL, 'LASNAP16_OneLine.dwg', '77777777-0000-0000-0000-000000000005', '2016-01-20 09:15:00'),
('00000004-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Assignment', 'Engineer assigned to study', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', NULL, 'Dr. James Patterson', '77777777-0000-0000-0000-000000000004', '2016-01-16 11:00:00'),
('00000005-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Status Change', 'Study status changed', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', 'In Progress', 'Review', '77777777-0000-0000-0000-000000000005', '2016-02-05 16:00:00'),
('00000006-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Document Upload', 'Final report uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000001', NULL, 'LASNAP16_ArcFlash_Report_v2.1.pdf', '77777777-0000-0000-0000-000000000005', '2016-02-08 14:30:00'),
('00000007-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Approval', 'Study report approved', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000001', 'In Review', 'Approved', '77777777-0000-0000-0000-000000000004', '2016-02-09 10:00:00'),
('00000008-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Status Change', 'Study completed', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', 'Review', 'Completed', '77777777-0000-0000-0000-000000000004', '2016-02-10 09:00:00'),

-- Study 2: Coordination Activity
('00000009-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Created', 'Study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000002', NULL, 'Pending', '77777777-0000-0000-0000-000000000004', '2016-02-01 08:00:00'),
('00000010-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Assignment', 'Engineer assigned', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000002', NULL, 'Maria Rodriguez, PE', '77777777-0000-0000-0000-000000000004', '2016-02-02 09:00:00'),
('00000011-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Status Change', 'Data collection started', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000002', 'Pending', 'Data Collection', '77777777-0000-0000-0000-000000000005', '2016-02-03 10:00:00'),
('00000012-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Document Upload', 'Relay settings data uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000005', NULL, 'LASNAP16_Data_RelaySettings.xlsx', '77777777-0000-0000-0000-000000000002', '2016-02-05 10:00:00'),
('00000013-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Status Change', 'Engineering work started', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000002', 'Data Collection', 'In Progress', '77777777-0000-0000-0000-000000000005', '2016-02-15 08:00:00'),
('00000014-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Document Upload', 'Draft coordination curves', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000006', NULL, 'LASNAP16_Coordination_Draft.pdf', '77777777-0000-0000-0000-000000000005', '2016-02-28 15:30:00'),
('00000015-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Comment', 'Review comments added to draft report', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000007', NULL, '3 comments added', '77777777-0000-0000-0000-000000000004', '2016-03-02 11:00:00'),

-- Study 3: Short Circuit Activity
('00000016-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000003', 'Created', 'Study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000003', NULL, 'Pending', '77777777-0000-0000-0000-000000000004', '2016-02-15 14:00:00'),
('00000017-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000003', 'Assignment', 'Engineer assigned', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000003', NULL, 'Robert Chang, PE', '77777777-0000-0000-0000-000000000004', '2016-02-16 09:00:00'),
('00000018-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000003', 'Document Upload', 'One-line diagram copied', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000009', NULL, 'LASNAP16_OneLine_SC.dwg', '77777777-0000-0000-0000-000000000005', '2016-02-16 10:00:00'),

-- Study 4: Load Flow Activity
('00000019-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000004', 'Created', 'Study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000004', NULL, 'Pending', '77777777-0000-0000-0000-000000000004', '2016-03-01 10:00:00'),
('00000020-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000004', 'Status Change', 'Data collection phase', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000004', 'Pending', 'Data Collection', '77777777-0000-0000-0000-000000000005', '2016-03-02 08:00:00'),
('00000021-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000004', 'Document Upload', 'Load data form uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000012', NULL, 'LASNAP16_Data_Loads.xlsx', '77777777-0000-0000-0000-000000000002', '2016-03-05 09:00:00'),

-- Study 5: Generic Activity
('00000022-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000005', 'Created', 'Template study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000005', NULL, 'Pending', '77777777-0000-0000-0000-000000000005', '2016-01-01 08:00:00'),
('00000023-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000005', 'Document Upload', 'Template uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000014', NULL, 'Comprehensive_Study_Template.docx', '77777777-0000-0000-0000-000000000005', '2016-01-02 08:00:00'),
('00000024-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000005', 'Status Change', 'Study placed on hold', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000005', 'Pending', 'On Hold', '77777777-0000-0000-0000-000000000004', '2016-01-10 15:00:00'),
('00000025-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000005', 'Comment', 'On hold pending project assignment', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000005', NULL, 'Awaiting Q2 project assignments', '77777777-0000-0000-0000-000000000004', '2016-01-10 15:05:00');

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

SELECT 'PSS Test Data Verification' AS section;
SELECT 'pss_engineers' AS entity, COUNT(*) AS count FROM pss_engineers WHERE id LIKE 'BBBBBBBB%'
UNION ALL SELECT 'pss_document_templates', COUNT(*) FROM pss_document_templates WHERE id LIKE 'CCCCCCCC%'
UNION ALL SELECT 'pss_studies', COUNT(*) FROM pss_studies WHERE id LIKE 'DDDDDDDD%'
UNION ALL SELECT 'pss_documents', COUNT(*) FROM pss_documents WHERE id LIKE 'EEEEEEEE%'
UNION ALL SELECT 'pss_rfis', COUNT(*) FROM pss_rfis WHERE id LIKE 'FFFFFFFF%'
UNION ALL SELECT 'pss_activity_log', COUNT(*) FROM pss_activity_log;

-- Verify FK integrity
SELECT 'PSS FK Integrity Check' AS section;
SELECT 'orphan_studies' AS check_name, COUNT(*) AS orphan_count 
FROM pss_studies WHERE project_id IS NOT NULL AND project_id NOT IN (SELECT id FROM projects)
UNION ALL
SELECT 'orphan_documents', COUNT(*) FROM pss_documents WHERE study_id NOT IN (SELECT id FROM pss_studies)
UNION ALL
SELECT 'orphan_rfis', COUNT(*) FROM pss_rfis WHERE study_id NOT IN (SELECT id FROM pss_studies);

-- Study summary by status
SELECT 'PSS Studies by Status' AS section;
SELECT status, COUNT(*) as count FROM pss_studies GROUP BY status ORDER BY count DESC;

-- RFIs by status
SELECT 'RFIs by Status' AS section;
SELECT status, COUNT(*) as count FROM pss_rfis GROUP BY status ORDER BY count DESC;

COMMIT;

-- =============================================================================
-- VERIFICATION: View Test
-- =============================================================================
-- After running, verify PSS views work:
-- SELECT * FROM v_pss_studies_full;
-- SELECT * FROM v_pss_dashboard;
