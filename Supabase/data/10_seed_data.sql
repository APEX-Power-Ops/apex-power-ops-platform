-- =============================================================================
-- RESA Power Platform - Seed Data (Reference Tables)
-- =============================================================================
-- File: 10_seed_data.sql
-- Generated: 2025-12-05
-- Purpose: Populate reference/master tables with initial data
-- Run: AFTER all schema files (00-05)
-- =============================================================================

-- =============================================================================
-- 1. LOCATIONS (RESA Branch Offices)
-- =============================================================================

INSERT INTO locations (id, location_name, abbreviation, code, region, city, state, zip, is_active, sort_order) VALUES
('10000000-0000-0000-0000-000000000001', 'Fenton', 'FEN', 'FENTON', 'Midwest', 'Fenton', 'MO', '63026', true, 1),
('10000000-0000-0000-0000-000000000002', 'Dallas', 'DAL', 'DALLAS', 'Southwest', 'Dallas', 'TX', '75201', true, 2),
('10000000-0000-0000-0000-000000000003', 'Houston', 'HOU', 'HOUSTON', 'Southwest', 'Houston', 'TX', '77001', true, 3),
('10000000-0000-0000-0000-000000000004', 'Phoenix', 'PHX', 'PHOENIX', 'Southwest', 'Phoenix', 'AZ', '85001', true, 4),
('10000000-0000-0000-0000-000000000005', 'Atlanta', 'ATL', 'ATLANTA', 'Southeast', 'Atlanta', 'GA', '30301', true, 5);

-- =============================================================================
-- 2. APPARATUS TYPES (Equipment Categories)
-- =============================================================================

INSERT INTO apparatus_types (id, type_code, type_name, category, default_hours, default_rate, description, is_active, sort_order) VALUES
-- Transformers
('20000000-0000-0000-0000-000000000001', 'XFMR-DRY', 'Dry-Type Transformer', 'Transformer', 4.0, 175.00, 'Dry-type transformer testing per NETA 7.2', true, 10),
('20000000-0000-0000-0000-000000000002', 'XFMR-OIL', 'Oil-Filled Transformer', 'Transformer', 8.0, 175.00, 'Liquid-filled transformer testing per NETA 7.2', true, 11),
('20000000-0000-0000-0000-000000000003', 'XFMR-PAD', 'Pad-Mount Transformer', 'Transformer', 6.0, 175.00, 'Pad-mounted transformer testing', true, 12),

-- Switchgear
('20000000-0000-0000-0000-000000000010', 'SWGR-MV', 'Medium Voltage Switchgear', 'Switchgear', 6.0, 185.00, 'MV switchgear testing per NETA 7.3', true, 20),
('20000000-0000-0000-0000-000000000011', 'SWGR-LV', 'Low Voltage Switchgear', 'Switchgear', 4.0, 175.00, 'LV switchgear testing per NETA 7.3', true, 21),
('20000000-0000-0000-0000-000000000012', 'SWGR-ARC', 'Arc-Resistant Switchgear', 'Switchgear', 8.0, 195.00, 'Arc-resistant switchgear testing', true, 22),

-- Circuit Breakers
('20000000-0000-0000-0000-000000000020', 'CB-MV-VAC', 'MV Vacuum Circuit Breaker', 'Circuit Breaker', 3.0, 185.00, 'Medium voltage vacuum breaker per NETA 7.6', true, 30),
('20000000-0000-0000-0000-000000000021', 'CB-MV-SF6', 'MV SF6 Circuit Breaker', 'Circuit Breaker', 4.0, 195.00, 'SF6 circuit breaker testing', true, 31),
('20000000-0000-0000-0000-000000000022', 'CB-LV-ACB', 'LV Air Circuit Breaker', 'Circuit Breaker', 2.0, 175.00, 'Low voltage ACB testing per NETA 7.6', true, 32),
('20000000-0000-0000-0000-000000000023', 'CB-LV-MCCB', 'Molded Case Circuit Breaker', 'Circuit Breaker', 1.0, 165.00, 'MCCB testing per NETA 7.6', true, 33),
('20000000-0000-0000-0000-000000000024', 'CB-LV-ICCB', 'Insulated Case Circuit Breaker', 'Circuit Breaker', 1.5, 175.00, 'ICCB testing per NETA 7.6', true, 34),

-- Protective Relays
('20000000-0000-0000-0000-000000000030', 'RELAY-ELEC', 'Electromechanical Relay', 'Protective Relay', 2.0, 185.00, 'Electromechanical relay testing per NETA 7.9', true, 40),
('20000000-0000-0000-0000-000000000031', 'RELAY-SOLID', 'Solid-State Relay', 'Protective Relay', 2.5, 185.00, 'Solid-state relay testing per NETA 7.9', true, 41),
('20000000-0000-0000-0000-000000000032', 'RELAY-MICRO', 'Microprocessor Relay', 'Protective Relay', 3.0, 195.00, 'Microprocessor relay testing per NETA 7.9', true, 42),

-- Motor Control
('20000000-0000-0000-0000-000000000040', 'MCC-UNIT', 'MCC Unit', 'Motor Control', 1.5, 165.00, 'Motor control center unit testing', true, 50),
('20000000-0000-0000-0000-000000000041', 'MCC-SECT', 'MCC Section', 'Motor Control', 4.0, 175.00, 'MCC section testing', true, 51),
('20000000-0000-0000-0000-000000000042', 'VFD', 'Variable Frequency Drive', 'Motor Control', 2.0, 185.00, 'VFD testing and commissioning', true, 52),
('20000000-0000-0000-0000-000000000043', 'STARTER', 'Motor Starter', 'Motor Control', 1.0, 165.00, 'Motor starter testing', true, 53),

-- Transfer Switches
('20000000-0000-0000-0000-000000000050', 'ATS-AUTO', 'Automatic Transfer Switch', 'Transfer Switch', 3.0, 175.00, 'ATS testing per NETA 7.22', true, 60),
('20000000-0000-0000-0000-000000000051', 'ATS-MAN', 'Manual Transfer Switch', 'Transfer Switch', 1.5, 165.00, 'Manual transfer switch testing', true, 61),
('20000000-0000-0000-0000-000000000052', 'ATS-BYPASS', 'Bypass Isolation Switch', 'Transfer Switch', 2.0, 175.00, 'Bypass isolation switch testing', true, 62),

-- Cables
('20000000-0000-0000-0000-000000000060', 'CABLE-MV', 'Medium Voltage Cable', 'Cable', 2.0, 175.00, 'MV cable testing per NETA 7.3.2', true, 70),
('20000000-0000-0000-0000-000000000061', 'CABLE-LV', 'Low Voltage Cable', 'Cable', 1.0, 165.00, 'LV cable testing', true, 71),

-- Batteries & UPS
('20000000-0000-0000-0000-000000000070', 'BATT-VRLA', 'VRLA Battery System', 'Battery', 4.0, 175.00, 'VRLA battery testing per NETA 7.24', true, 80),
('20000000-0000-0000-0000-000000000071', 'BATT-FLOOD', 'Flooded Battery System', 'Battery', 6.0, 175.00, 'Flooded cell battery testing', true, 81),
('20000000-0000-0000-0000-000000000072', 'UPS-STATIC', 'Static UPS', 'UPS', 4.0, 185.00, 'Static UPS testing per NETA 7.25', true, 82),
('20000000-0000-0000-0000-000000000073', 'UPS-ROTARY', 'Rotary UPS', 'UPS', 6.0, 195.00, 'Rotary UPS testing', true, 83),

-- Generators
('20000000-0000-0000-0000-000000000080', 'GEN-DIESEL', 'Diesel Generator', 'Generator', 6.0, 185.00, 'Diesel generator testing per NETA 7.21', true, 90),
('20000000-0000-0000-0000-000000000081', 'GEN-GAS', 'Natural Gas Generator', 'Generator', 6.0, 185.00, 'Natural gas generator testing', true, 91),

-- Grounding
('20000000-0000-0000-0000-000000000090', 'GND-SYSTEM', 'Grounding System', 'Grounding', 4.0, 175.00, 'Grounding system testing per NETA 7.13', true, 100),
('20000000-0000-0000-0000-000000000091', 'GND-GRID', 'Ground Grid', 'Grounding', 8.0, 185.00, 'Ground grid testing', true, 101),

-- Other
('20000000-0000-0000-0000-000000000100', 'CAP-BANK', 'Capacitor Bank', 'Capacitor', 3.0, 175.00, 'Capacitor bank testing per NETA 7.8', true, 110),
('20000000-0000-0000-0000-000000000101', 'PDC', 'Power Distribution Center', 'Distribution', 4.0, 175.00, 'PDC testing', true, 111),
('20000000-0000-0000-0000-000000000102', 'PANEL', 'Panelboard', 'Distribution', 1.5, 165.00, 'Panelboard testing per NETA 7.5', true, 112);

-- =============================================================================
-- 3. NETA TEST TEMPLATES
-- =============================================================================

INSERT INTO neta_test_templates (id, template_code, template_name, apparatus_type, test_category, description, estimated_hours, is_active, sort_order) VALUES
-- Transformer Tests
('30000000-0000-0000-0000-000000000001', 'NETA-7.2.1', 'Transformer Visual Inspection', 'Transformer', 'Visual', 'Visual and mechanical inspection per NETA ATS 7.2.1', 0.5, true, 1),
('30000000-0000-0000-0000-000000000002', 'NETA-7.2.2', 'Transformer Insulation Resistance', 'Transformer', 'Electrical', 'Insulation resistance testing per NETA ATS 7.2.2', 1.0, true, 2),
('30000000-0000-0000-0000-000000000003', 'NETA-7.2.3', 'Transformer Turns Ratio', 'Transformer', 'Electrical', 'Turns ratio testing per NETA ATS 7.2.3', 1.0, true, 3),
('30000000-0000-0000-0000-000000000004', 'NETA-7.2.4', 'Transformer Winding Resistance', 'Transformer', 'Electrical', 'Winding resistance per NETA ATS 7.2.4', 1.0, true, 4),
('30000000-0000-0000-0000-000000000005', 'NETA-7.2.5', 'Transformer Oil Analysis', 'Transformer', 'Oil', 'Insulating liquid tests per NETA ATS 7.2.5', 0.5, true, 5),

-- Switchgear Tests
('30000000-0000-0000-0000-000000000010', 'NETA-7.3.1', 'Switchgear Visual Inspection', 'Switchgear', 'Visual', 'Visual and mechanical inspection per NETA ATS 7.3.1', 1.0, true, 10),
('30000000-0000-0000-0000-000000000011', 'NETA-7.3.2', 'Switchgear Insulation Resistance', 'Switchgear', 'Electrical', 'Insulation resistance testing per NETA ATS 7.3.2', 1.5, true, 11),
('30000000-0000-0000-0000-000000000012', 'NETA-7.3.3', 'Switchgear Contact Resistance', 'Switchgear', 'Electrical', 'Contact resistance testing per NETA ATS 7.3.3', 1.0, true, 12),

-- Circuit Breaker Tests
('30000000-0000-0000-0000-000000000020', 'NETA-7.6.1', 'Breaker Visual Inspection', 'Circuit Breaker', 'Visual', 'Visual and mechanical inspection per NETA ATS 7.6.1', 0.5, true, 20),
('30000000-0000-0000-0000-000000000021', 'NETA-7.6.2', 'Breaker Contact Resistance', 'Circuit Breaker', 'Electrical', 'Contact resistance per NETA ATS 7.6.2', 0.5, true, 21),
('30000000-0000-0000-0000-000000000022', 'NETA-7.6.3', 'Breaker Insulation Resistance', 'Circuit Breaker', 'Electrical', 'Insulation resistance per NETA ATS 7.6.3', 0.5, true, 22),
('30000000-0000-0000-0000-000000000023', 'NETA-7.6.4', 'Breaker Trip Testing', 'Circuit Breaker', 'Functional', 'Trip unit testing per NETA ATS 7.6.4', 1.0, true, 23),
('30000000-0000-0000-0000-000000000024', 'NETA-7.6.5', 'Breaker Timing', 'Circuit Breaker', 'Timing', 'Operating time testing per NETA ATS 7.6.5', 0.5, true, 24),

-- Relay Tests
('30000000-0000-0000-0000-000000000030', 'NETA-7.9.1', 'Relay Visual Inspection', 'Protective Relay', 'Visual', 'Visual inspection per NETA ATS 7.9.1', 0.25, true, 30),
('30000000-0000-0000-0000-000000000031', 'NETA-7.9.2', 'Relay Settings Verification', 'Protective Relay', 'Settings', 'Settings verification per NETA ATS 7.9.2', 0.5, true, 31),
('30000000-0000-0000-0000-000000000032', 'NETA-7.9.3', 'Relay Pickup Testing', 'Protective Relay', 'Functional', 'Pickup testing per NETA ATS 7.9.3', 1.0, true, 32),
('30000000-0000-0000-0000-000000000033', 'NETA-7.9.4', 'Relay Timing Testing', 'Protective Relay', 'Timing', 'Timing curve verification per NETA ATS 7.9.4', 1.0, true, 33),

-- Cable Tests
('30000000-0000-0000-0000-000000000040', 'NETA-7.3.2.1', 'Cable Insulation Resistance', 'Cable', 'Electrical', 'Cable insulation resistance per NETA ATS', 0.5, true, 40),
('30000000-0000-0000-0000-000000000041', 'NETA-7.3.2.2', 'Cable Hi-Pot Testing', 'Cable', 'Electrical', 'Cable DC hi-pot testing', 1.0, true, 41),
('30000000-0000-0000-0000-000000000042', 'NETA-7.3.2.3', 'Cable VLF Testing', 'Cable', 'Electrical', 'VLF withstand testing', 1.5, true, 42),

-- ATS Tests
('30000000-0000-0000-0000-000000000050', 'NETA-7.22.1', 'ATS Visual Inspection', 'Transfer Switch', 'Visual', 'Visual inspection per NETA ATS 7.22', 0.5, true, 50),
('30000000-0000-0000-0000-000000000051', 'NETA-7.22.2', 'ATS Transfer Testing', 'Transfer Switch', 'Functional', 'Transfer operation testing', 1.0, true, 51),
('30000000-0000-0000-0000-000000000052', 'NETA-7.22.3', 'ATS Timing Verification', 'Transfer Switch', 'Timing', 'Transfer timing verification', 0.5, true, 52),

-- Battery Tests
('30000000-0000-0000-0000-000000000060', 'NETA-7.24.1', 'Battery Visual Inspection', 'Battery', 'Visual', 'Visual inspection per NETA ATS 7.24', 0.5, true, 60),
('30000000-0000-0000-0000-000000000061', 'NETA-7.24.2', 'Battery Impedance Testing', 'Battery', 'Electrical', 'Cell impedance testing', 2.0, true, 61),
('30000000-0000-0000-0000-000000000062', 'NETA-7.24.3', 'Battery Capacity Testing', 'Battery', 'Capacity', 'Discharge capacity testing', 4.0, true, 62),

-- UPS Tests
('30000000-0000-0000-0000-000000000070', 'NETA-7.25.1', 'UPS Visual Inspection', 'UPS', 'Visual', 'Visual inspection per NETA ATS 7.25', 0.5, true, 70),
('30000000-0000-0000-0000-000000000071', 'NETA-7.25.2', 'UPS Functional Testing', 'UPS', 'Functional', 'Transfer and bypass testing', 2.0, true, 71),
('30000000-0000-0000-0000-000000000072', 'NETA-7.25.3', 'UPS Load Bank Testing', 'UPS', 'Load', 'Load bank testing', 2.0, true, 72),

-- Generator Tests
('30000000-0000-0000-0000-000000000080', 'NETA-7.21.1', 'Generator Visual Inspection', 'Generator', 'Visual', 'Visual inspection per NETA ATS 7.21', 0.5, true, 80),
('30000000-0000-0000-0000-000000000081', 'NETA-7.21.2', 'Generator Insulation Resistance', 'Generator', 'Electrical', 'Stator insulation resistance', 1.0, true, 81),
('30000000-0000-0000-0000-000000000082', 'NETA-7.21.3', 'Generator Load Bank Test', 'Generator', 'Load', 'Load bank testing', 2.0, true, 82),

-- Grounding Tests
('30000000-0000-0000-0000-000000000090', 'NETA-7.13.1', 'Ground Resistance Testing', 'Grounding', 'Electrical', 'Ground resistance per NETA ATS 7.13', 1.0, true, 90),
('30000000-0000-0000-0000-000000000091', 'NETA-7.13.2', 'Ground Grid Testing', 'Grounding', 'Electrical', 'Ground grid integrity testing', 2.0, true, 91);

-- =============================================================================
-- 4. PSS DOCUMENT TEMPLATES
-- =============================================================================

INSERT INTO pss_document_templates (id, template_code, template_name, document_type, description, is_active, sort_order) VALUES
('40000000-0000-0000-0000-000000000001', 'PSS-RPT-AF', 'Arc Flash Study Report', 'Study Report', 'Standard arc flash analysis report template', true, 1),
('40000000-0000-0000-0000-000000000002', 'PSS-RPT-SC', 'Short Circuit Study Report', 'Short Circuit Report', 'Short circuit analysis report template', true, 2),
('40000000-0000-0000-0000-000000000003', 'PSS-RPT-COORD', 'Coordination Study Report', 'Study Report', 'Protective device coordination report template', true, 3),
('40000000-0000-0000-0000-000000000004', 'PSS-DWG-OL', 'One-Line Diagram', 'One-Line Diagram', 'Electrical one-line diagram template', true, 4),
('40000000-0000-0000-0000-000000000005', 'PSS-TCC', 'Time-Current Curves', 'Coordination Curves', 'TCC curve package template', true, 5),
('40000000-0000-0000-0000-000000000006', 'PSS-LBL-AF', 'Arc Flash Labels', 'Arc Flash Labels', 'Arc flash warning label package', true, 6),
('40000000-0000-0000-0000-000000000007', 'PSS-DATA', 'Data Collection Form', 'Data Collection', 'Field data collection template', true, 7),
('40000000-0000-0000-0000-000000000008', 'PSS-EQUIP', 'Equipment Schedule', 'Equipment Schedule', 'Equipment data schedule template', true, 8);

-- =============================================================================
-- 5. ESTIMATORS (Sample)
-- =============================================================================

INSERT INTO estimators (id, estimator_name, email, location_id, is_active) VALUES
('50000000-0000-0000-0000-000000000001', 'Standard Field Rate', 'estimating@resapower.com', '10000000-0000-0000-0000-000000000001', true),
('50000000-0000-0000-0000-000000000002', 'Premium Rate', 'estimating@resapower.com', '10000000-0000-0000-0000-000000000001', true),
('50000000-0000-0000-0000-000000000003', 'Emergency Rate', 'estimating@resapower.com', '10000000-0000-0000-0000-000000000001', true);

-- =============================================================================
-- VERIFICATION
-- =============================================================================

SELECT 'Seed data inserted successfully!' AS status;

SELECT 'Locations' AS table_name, COUNT(*) AS row_count FROM locations
UNION ALL
SELECT 'Apparatus Types', COUNT(*) FROM apparatus_types
UNION ALL
SELECT 'NETA Templates', COUNT(*) FROM neta_test_templates
UNION ALL
SELECT 'PSS Doc Templates', COUNT(*) FROM pss_document_templates
UNION ALL
SELECT 'Estimators', COUNT(*) FROM estimators;
