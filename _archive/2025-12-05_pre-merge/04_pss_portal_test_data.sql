-- =============================================================================
-- RESA Power Platform - PSS Portal Test Data
-- =============================================================================
-- Run this AFTER 03_pss_portal_tables.sql
-- Populates PSS Portal with sample data from the requirements document
-- =============================================================================

-- =============================================================================
-- 1. PSS ENGINEERS
-- =============================================================================

INSERT INTO pss_engineers (id, company_name, email, is_active, notes) VALUES
    ('e1000000-0000-0000-0001-000000000001', 'Shaw Engineering', 'paul@shawengineering.com', true, 'Primary engineering vendor for PSS studies');

-- =============================================================================
-- 2. PSS CONTACTS
-- =============================================================================

-- RESA Staff
INSERT INTO pss_contacts (id, full_name, email, role_title, contact_type, is_primary) VALUES
    ('c1000000-0000-0000-0001-000000000001', 'Chad Sheffield', 'chad.sheffield@resapower.com', 'PSS Coordinator', 'RESA', true);

-- Engineer Contacts
INSERT INTO pss_contacts (id, full_name, email, role_title, contact_type, engineer_id, is_primary) VALUES
    ('c1000000-0000-0000-0001-000000000002', 'Paul (Shaw)', 'paul@shawengineering.com', 'Lead Engineer', 'Engineer', 'e1000000-0000-0000-0001-000000000001', true);

-- Client Contacts (linked to existing clients table where applicable)
INSERT INTO pss_contacts (id, full_name, email, role_title, contact_type, is_primary) VALUES
    ('c1000000-0000-0000-0001-000000000003', 'Terri Aguiar', 'taguiar@rosendin.com', 'Project Manager', 'Client', true),
    ('c1000000-0000-0000-0001-000000000004', 'Hunter Wright Waddell', 'hwaddell@rosendin.com', 'Engineer', 'Client', false),
    ('c1000000-0000-0000-0001-000000000005', 'Nick Valentine', 'nvalentine@iconcompany.com', 'Project Manager', 'Client', true),
    ('c1000000-0000-0000-0001-000000000006', 'Sydney Trujillo', 'strujillo@k2electric.com', 'Contact', 'Client', true),
    ('c1000000-0000-0000-0001-000000000007', 'Joe Essay', 'jessay@dpelectric.com', 'Project Manager', 'Client', true),
    ('c1000000-0000-0000-0001-000000000008', 'Bret Riggs', 'briggs@swainelectric.com', 'Contact', 'Client', true),
    ('c1000000-0000-0000-0001-000000000009', 'Jeff Nihart', 'jnihart@jenco.com', 'Contact', 'Client', true);

-- Update engineer primary contact now that contact exists
UPDATE pss_engineers 
SET primary_contact_id = 'c1000000-0000-0000-0001-000000000002'
WHERE id = 'e1000000-0000-0000-0001-000000000001';

-- =============================================================================
-- 3. DOCUMENT TEMPLATES (Master checklist)
-- =============================================================================

INSERT INTO pss_document_templates (id, document_name, study_types, is_required, description, sort_order) VALUES
    ('t1000000-0000-0000-0001-000000000001', 'Single-Line Diagram', ARRAY['PSS', 'Arc Flash'], true, 
     'One-line showing electrical distribution system', 1),
    ('t1000000-0000-0000-0001-000000000002', 'Utility Fault Current Data', ARRAY['PSS', 'Arc Flash'], true, 
     'Available fault current from utility provider (prefer actual from utility)', 2),
    ('t1000000-0000-0000-0001-000000000003', 'Main Breaker Information', ARRAY['PSS', 'Arc Flash'], true, 
     'Manufacturer, catalog #, trip unit catalog #', 3),
    ('t1000000-0000-0000-0001-000000000004', 'Panel Schedules', ARRAY['PSS', 'Arc Flash'], true, 
     'Panel schedules showing breaker sizes', 4),
    ('t1000000-0000-0000-0001-000000000005', 'Transformer Data', ARRAY['PSS', 'Arc Flash'], true, 
     'kVA, voltage, impedance for all transformers', 5),
    ('t1000000-0000-0000-0001-000000000006', 'Cable/Conductor Schedule', ARRAY['PSS', 'Arc Flash'], false, 
     'Sizes, lengths, types of cables/conductors', 6),
    ('t1000000-0000-0000-0001-000000000007', 'Motor Schedules', ARRAY['PSS', 'Arc Flash'], false, 
     'HP, FLA, starting method for motors', 7),
    ('t1000000-0000-0000-0001-000000000008', 'Generator Data', ARRAY['PSS', 'Arc Flash'], false, 
     'kW, voltage, subtransient reactance', 8),
    ('t1000000-0000-0000-0001-000000000009', 'Existing Relay Settings', ARRAY['PSS', 'Coordination'], false, 
     'Current protective device settings', 9),
    ('t1000000-0000-0000-0001-000000000010', 'Working Distances', ARRAY['Arc Flash'], true, 
     'Distance from equipment during work', 10),
    ('t1000000-0000-0000-0001-000000000011', 'Equipment Enclosure Types', ARRAY['Arc Flash'], true, 
     'Open, box, MCC, switchgear, etc.', 11),
    ('t1000000-0000-0000-0001-000000000012', 'Existing Arc Flash Labels', ARRAY['Arc Flash'], false, 
     'Photos or data from existing labels', 12);

-- =============================================================================
-- 4. PSS PROJECTS (Sample from requirements doc)
-- =============================================================================

INSERT INTO pss_projects (id, resa_job_number, project_name, engineer_id, service_type, status, order_date, target_report_date, data_collection_by, po_number, po_amount, notes) VALUES
    -- Rosendin - SWA Tech Ops (Partial Docs)
    ('p1000000-0000-0000-0001-000000000001', '629266', 'SWA Tech Ops', 
     'e1000000-0000-0000-0001-000000000001', 'PSS + Arc Flash', 'Partial Documents',
     '2025-10-15', '2025-12-31', 'Client', 'PO-629266', 1250.00,
     'Main breaker info still needed - catalog # and trip unit catalog #'),
    
    -- DP Electric - Hydro (Stickers Pending)
    ('p1000000-0000-0000-0001-000000000002', '627687', 'Hydro', 
     'e1000000-0000-0000-0001-000000000001', 'Arc Flash', 'Stickers Pending',
     '2025-09-01', '2025-11-15', 'RESA', 'PO-627687', 20000.00,
     'Report approved, awaiting sticker application'),
    
    -- ICON - Airport Center (Draft Submitted)
    ('p1000000-0000-0000-0001-000000000003', '659189', 'Airport Center', 
     'e1000000-0000-0000-0001-000000000001', 'PSS', 'Draft Submitted',
     '2025-10-01', '2025-12-01', 'Client', 'PO-659189', 2000.00,
     'Draft submitted 2025-11-01, awaiting client review'),
    
    -- City of Buckeye - P7 Lift Station (In Progress)
    ('p1000000-0000-0000-0001-000000000004', '673518', 'P7 Lift Station', 
     'e1000000-0000-0000-0001-000000000001', 'Arc Flash', 'In Progress',
     '2025-10-20', '2025-12-15', 'Client', 'PO-673518', 1250.00,
     'Data sent 2025-11-11, study in progress'),
    
    -- K2 - Scottsdale Ranch Park (Awaiting Docs)
    ('p1000000-0000-0000-0001-000000000005', '626206', 'Scottsdale Ranch Park', 
     'e1000000-0000-0000-0001-000000000001', 'PSS + Arc Flash', 'Awaiting Documents',
     '2025-11-01', '2026-01-15', 'Client', NULL, NULL,
     'Initial request sent, waiting for client to provide documents');

-- =============================================================================
-- 5. PSS DOCUMENTS (for SWA Tech Ops project - Job 629266)
-- =============================================================================

INSERT INTO pss_documents (id, project_id, template_id, document_name, status, requested_date, received_date, notes) VALUES
    -- SWA Tech Ops documents
    ('d1000000-0000-0000-0001-000000000001', 'p1000000-0000-0000-0001-000000000001',
     't1000000-0000-0000-0001-000000000001', 'SWA Tech Ops One-Line.pdf', 'Accepted', '2025-10-16', '2025-11-10', NULL),
    
    ('d1000000-0000-0000-0001-000000000002', 'p1000000-0000-0000-0001-000000000001',
     't1000000-0000-0000-0001-000000000002', NULL, 'Requested', '2025-10-16', NULL, 
     'Prefer actual from APS; can use table max if needed'),
    
    ('d1000000-0000-0000-0001-000000000003', 'p1000000-0000-0000-0001-000000000001',
     't1000000-0000-0000-0001-000000000003', NULL, 'Requested', '2025-10-16', NULL, 
     'Need breaker catalog number AND trip unit catalog number for 3000A main'),
    
    ('d1000000-0000-0000-0001-000000000004', 'p1000000-0000-0000-0001-000000000001',
     't1000000-0000-0000-0001-000000000004', 'SWA Equipment Schedules.xlsx', 'Received', '2025-10-16', '2025-11-10', NULL),
    
    ('d1000000-0000-0000-0001-000000000005', 'p1000000-0000-0000-0001-000000000001',
     't1000000-0000-0000-0001-000000000006', NULL, 'Not Requested', NULL, NULL, NULL);

-- Documents for Hydro project (complete)
INSERT INTO pss_documents (id, project_id, template_id, document_name, status, requested_date, received_date, reviewed_date) VALUES
    ('d1000000-0000-0000-0001-000000000006', 'p1000000-0000-0000-0001-000000000002',
     't1000000-0000-0000-0001-000000000001', 'Hydro One-Line Rev3.pdf', 'Accepted', '2025-09-02', '2025-09-10', '2025-09-12'),
    ('d1000000-0000-0000-0001-000000000007', 'p1000000-0000-0000-0001-000000000002',
     't1000000-0000-0000-0001-000000000002', 'APS Fault Current Letter.pdf', 'Accepted', '2025-09-02', '2025-09-15', '2025-09-16'),
    ('d1000000-0000-0000-0001-000000000008', 'p1000000-0000-0000-0001-000000000002',
     't1000000-0000-0000-0001-000000000003', 'Main Breaker Submittal.pdf', 'Accepted', '2025-09-02', '2025-09-10', '2025-09-12');

-- =============================================================================
-- 6. PSS RFIs (Sample RFI from requirements doc)
-- =============================================================================

INSERT INTO pss_rfis (id, project_id, subject, question, priority, status, submitted_by_id, submitted_date, related_document_id) VALUES
    ('r1000000-0000-0000-0001-000000000001', 'p1000000-0000-0000-0001-000000000001',
     'Main Breaker Model Information Required',
     'Need main breaker info (breaker catalog number and trip unit catalog number) for the 3000A main shown on one-line. This is required to complete the coordination study.',
     'Medium', 'Open',
     'c1000000-0000-0000-0001-000000000002',  -- Shaw engineer
     '2025-12-05',
     'd1000000-0000-0000-0001-000000000003');  -- Related to main breaker document

-- =============================================================================
-- 7. PSS ACTIVITY LOG (Sample activities)
-- =============================================================================

INSERT INTO pss_activity_log (id, project_id, activity_datetime, activity_type, description, performed_by_id, visible_to_client, visible_to_engineer) VALUES
    -- SWA Tech Ops activities
    ('a1000000-0000-0000-0001-000000000001', 'p1000000-0000-0000-0001-000000000001',
     '2025-10-15 09:00:00', 'Status Change', 'Project created - New Request', 
     'c1000000-0000-0000-0001-000000000001', true, true),
    
    ('a1000000-0000-0000-0001-000000000002', 'p1000000-0000-0000-0001-000000000001',
     '2025-10-16 10:30:00', 'Status Change', 'Document requests sent - Awaiting Documents', 
     'c1000000-0000-0000-0001-000000000001', true, true),
    
    ('a1000000-0000-0000-0001-000000000003', 'p1000000-0000-0000-0001-000000000001',
     '2025-11-10 14:00:00', 'Document Uploaded', 'Client uploaded one-line diagram and equipment schedules', 
     'c1000000-0000-0000-0001-000000000003', true, true),
    
    ('a1000000-0000-0000-0001-000000000004', 'p1000000-0000-0000-0001-000000000001',
     '2025-11-10 16:00:00', 'Status Change', 'Partial documents received - Partial Documents', 
     'c1000000-0000-0000-0001-000000000001', true, true),
    
    ('a1000000-0000-0000-0001-000000000005', 'p1000000-0000-0000-0001-000000000001',
     '2025-12-05 11:00:00', 'RFI Submitted', 'Shaw submitted RFI for main breaker information', 
     'c1000000-0000-0000-0001-000000000002', true, true);

-- =============================================================================
-- 8. PSS USERS
-- =============================================================================

INSERT INTO pss_users (id, email, contact_id, role, is_active) VALUES
    ('u1000000-0000-0000-0001-000000000001', 'chad.sheffield@resapower.com', 
     'c1000000-0000-0000-0001-000000000001', 'RESA Admin', true),
    ('u1000000-0000-0000-0001-000000000002', 'paul@shawengineering.com', 
     'c1000000-0000-0000-0001-000000000002', 'Engineer', true),
    ('u1000000-0000-0000-0001-000000000003', 'taguiar@rosendin.com', 
     'c1000000-0000-0000-0001-000000000003', 'Client', true);

-- =============================================================================
-- SUMMARY QUERY (verify data loaded)
-- =============================================================================

SELECT 'PSS Portal Data Population Summary:' as info;
SELECT 'PSS Engineers: ' || COUNT(*) FROM pss_engineers;
SELECT 'PSS Contacts: ' || COUNT(*) FROM pss_contacts;
SELECT 'PSS Projects: ' || COUNT(*) FROM pss_projects;
SELECT 'Document Templates: ' || COUNT(*) FROM pss_document_templates;
SELECT 'PSS Documents: ' || COUNT(*) FROM pss_documents;
SELECT 'PSS RFIs: ' || COUNT(*) FROM pss_rfis;
SELECT 'Activity Log Entries: ' || COUNT(*) FROM pss_activity_log;
SELECT 'PSS Users: ' || COUNT(*) FROM pss_users;
