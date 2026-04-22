-- NETA Test Items Import - Batch 2
-- Sections: 7.3.3, 7.5.2, 7.5.3, 7.5.5, 7.6.2, 7.9.1, 7.10.2, 7.10.3
-- Generated: 2025-12-11

-- ============================================================
-- Section 7.3.3 Shielded Cables, Medium- and High-Voltage
-- UUID: 06adef51-e5ef-4253-a361-7c6a5178ae89
-- ============================================================
INSERT INTO neta_test_items (procedure_id, test_type, test_number, description, is_optional, sort_order)
VALUES
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '1', 'Compare cable data with drawings and specifications.', false, 1),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '2', 'Inspect terminations, splices, and exposed sections of cables for physical damage.', false, 2),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '3', 'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer''s published data. In the absence of manufacturer''s data, use Table 100.12.', false, 3),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '4', 'Inspect compression-applied connectors for correct cable match and indentation.', false, 4),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '5', 'Inspect shield grounding and cable supports.', false, 5),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '6', 'Verify that visible cable bends are not less than ICEA and/or manufacturer''s minimum allowable bending radius.', false, 6),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '7', 'Inspect fireproofing in common cable areas.', true, 7),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '8', 'If cables are terminated through window-type current transformers, inspect to verify that neutral and ground conductors are correctly placed and that shields are correctly terminated for operation of protective devices.', false, 8),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '9', 'Inspect for correct identification and arrangements.', false, 9),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'visual_mechanical', '10', 'Perform thermographic survey in accordance with Section 9.', true, 10),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'electrical', '1', 'Perform an insulation-resistance test individually between each phase/conductor and its shield with all other phase/conductors and shields grounded. Apply voltage in accordance with manufacturer''s published data. In the absence of manufacturer''s published data, use Table 100.1.', false, 101),
  ('06adef51-e5ef-4253-a361-7c6a5178ae89', 'electrical', '2', 'Perform a shield-continuity test on each power cable by ohmmeter method.', false, 102);

-- ============================================================
-- Section 7.5.2 Switches, Oil, Medium-Voltage
-- UUID: c1441000-62b8-4aa8-999e-bb24986223d2
-- ============================================================
INSERT INTO neta_test_items (procedure_id, test_type, test_number, description, is_optional, sort_order)
VALUES
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '1', 'Compare equipment nameplate data with drawings.', false, 1),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '2', 'Inspect physical and mechanical condition.', false, 2),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '3', 'Inspect anchorage, alignment, grounding, and required clearances.', false, 3),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '4', 'Verify the unit is clean.', false, 4),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '5', 'Perform mechanical operator tests in accordance with manufacturer''s published data.', false, 5),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '6', 'Verify correct operation and adjustment of motor operator limit switches and mechanical interlocks.', false, 6),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '7', 'Test all electrical and mechanical interlock systems for correct operation and sequencing.', false, 7),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '8', 'Verify that each fuse has adequate mechanical support and contact integrity.', false, 8),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '9', 'Verify that fuse sizes and types are in accordance with drawings, short-circuit study, and coordination study.', false, 9),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '10', 'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer''s published data. In the absence of manufacturer''s data, use Table 100.12.', false, 10),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '11', 'Verify that insulating oil level is correct.', false, 11),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '12', 'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.', false, 12),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '13', 'Record as-found and as-left operation counter readings.', false, 13),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'visual_mechanical', '14', 'Perform thermographic survey in accordance with Section 9.', true, 14),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'electrical', '1', 'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.', false, 101),
  ('c1441000-62b8-4aa8-999e-bb24986223d2', 'electrical', '2', 'Perform a contact/pole-resistance test.', false, 102);

-- ============================================================
-- Section 7.5.3 Switches, Vacuum, Medium-Voltage
-- UUID: 844494d2-2fc2-4c67-bd77-34ee3528f804
-- ============================================================
INSERT INTO neta_test_items (procedure_id, test_type, test_number, description, is_optional, sort_order)
VALUES
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '1', 'Compare equipment nameplate data with drawings.', false, 1),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '2', 'Inspect physical and mechanical condition.', false, 2),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '3', 'Inspect anchorage, alignment, grounding, and required clearances.', false, 3),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '4', 'Verify the unit is clean.', false, 4),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '5', 'Perform mechanical operator tests in accordance with manufacturer''s published data.', false, 5),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '6', 'Verify correct operation and adjustment of motor operator limit switches and mechanical interlocks.', false, 6),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '7', 'Verify critical distances on operating mechanism as recommended by the manufacturer.', false, 7),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '8', 'Test all electrical and mechanical interlock systems for correct operation and sequencing.', false, 8),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '9', 'Verify that each fuse has adequate support and contact integrity.', false, 9),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '10', 'Verify that fuse sizes and types are in accordance with drawings, the short-circuit study, and the coordination study.', false, 10),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '11', 'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer''s published data. In the absence of manufacturer''s data, use Table 100.12.', false, 11),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '12', 'Verify that insulating oil level is correct.', false, 12),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '13', 'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.', false, 13),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '14', 'Record as-left operation counter reading.', false, 14),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'visual_mechanical', '15', 'Perform thermographic survey in accordance with Section 9.', true, 15),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'electrical', '1', 'Perform resistance measurements through bolted electrical connections with a low resistance ohmmeter.', false, 101),
  ('844494d2-2fc2-4c67-bd77-34ee3528f804', 'electrical', '2', 'Perform a contact/pole-resistance test.', false, 102);

-- ============================================================
-- Section 7.5.5 Switches, Cutouts
-- UUID: 62e24d1c-21cb-406f-8b77-ad374bd5838a
-- ============================================================
INSERT INTO neta_test_items (procedure_id, test_type, test_number, description, is_optional, sort_order)
VALUES
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'visual_mechanical', '1', 'Compare equipment nameplate data with drawings.', false, 1),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'visual_mechanical', '2', 'Inspect physical and mechanical condition.', false, 2),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'visual_mechanical', '3', 'Inspect anchorage, alignment, grounding, and required clearances.', false, 3),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'visual_mechanical', '4', 'Verify the unit is clean.', false, 4),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'visual_mechanical', '5', 'Verify correct blade alignment, blade penetration, travel stops, latching mechanism, and mechanical operation.', false, 5),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'visual_mechanical', '6', 'Verify that each fuseholder has adequate mechanical support and contact integrity.', false, 6),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'visual_mechanical', '7', 'Verify that fuse size and types are in accordance with drawings, short-circuit study, and coordination study.', false, 7),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'visual_mechanical', '8', 'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer''s published data. In the absence of manufacturer''s data, use Table 100.12.', false, 8),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'visual_mechanical', '9', 'Perform thermographic survey in accordance with Section 9.', true, 9),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'electrical', '1', 'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.', false, 101),
  ('62e24d1c-21cb-406f-8b77-ad374bd5838a', 'electrical', '2', 'Measure contact resistance across each cutout.', false, 102);

-- ============================================================
-- Section 7.6.2 Circuit Breakers, Oil, Medium-/High-Voltage
-- UUID: c958d767-0998-4358-8832-d19ea14b212f
-- ============================================================
INSERT INTO neta_test_items (procedure_id, test_type, test_number, description, is_optional, sort_order)
VALUES
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '1', 'Compare equipment nameplate data with drawings.', false, 1),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '2', 'Inspect physical and mechanical condition.', false, 2),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '3', 'Inspect anchorage, alignment, and grounding.', false, 3),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '4', 'Verify that all maintenance devices such as special tools and gauges as specified by the manufacturer are available for servicing and operating the breaker.', false, 4),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '5', 'Verify the unit is clean.', false, 5),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '6', 'Verify that insulating liquid level is correct.', false, 6),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '7', 'Inspect operating mechanism in accordance with manufacturer''s published data.', false, 7),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '8', 'Inspect, adjust, and test all auxiliary features such as electrical close and trip operation, trip-free, and antipump function.', false, 8),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '9', 'Slow close and open breaker and check for binding, friction, and contact alignment.', false, 9),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '10', 'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer''s published data. In the absence of manufacturer''s data, use Table 100.12.', false, 10),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '11', 'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.', false, 11),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '12', 'Perform contact-timing tests.', false, 12),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '13', 'Record as-found and as-left operation counter readings.', false, 13),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'visual_mechanical', '14', 'Perform thermographic survey in accordance with Section 9.', true, 14),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'electrical', '1', 'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.', false, 101),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'electrical', '2', 'Perform insulation-resistance tests in accordance with Table 100.1 from each pole-to-ground with breaker closed and across open poles at each phase.', false, 102),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'electrical', '3', 'Perform a contact/pole-resistance test.', false, 103),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'electrical', '4', 'Perform insulation-resistance tests on all control wiring with respect to ground. Applied potential shall be 500 volts dc for 300-volt rated cable and 1000 volts dc for 600-volt rated cable. Test duration shall be one minute.', true, 104),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'electrical', '5', 'Perform minimum pickup voltage tests on trip and close coils in accordance with manufacturer''s published data.', false, 105),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'electrical', '6', 'Verify correct operation of any auxiliary features such as electrical close and trip operation, trip-free, and antipump function.', false, 106),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'electrical', '7', 'Trip circuit breaker by operation of each protective device.', false, 107),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'electrical', '8', 'Verify operation of heaters.', false, 108),
  ('c958d767-0998-4358-8832-d19ea14b212f', 'electrical', '9', 'Perform power-factor or dissipation-factor tests on each bushing equipped with a power-factor/capacitance tap.', false, 109);

-- ============================================================
-- Section 7.9.1 Protective Relays, Electromechanical and Solid-State
-- UUID: 3d2d5569-04bf-4d8c-b6ab-e3b84195c73b
-- ============================================================
INSERT INTO neta_test_items (procedure_id, test_type, test_number, description, is_optional, sort_order)
VALUES
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '1', 'Compare equipment nameplate data with drawings.', false, 1),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '2', 'Inspect relays and cases for physical damage. Remove shipping restraint material.', false, 2),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '3', 'Verify the unit is clean.', false, 3),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '4', 'Tighten case connections.', false, 4),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '5', 'Inspect cover for correct gasket seal.', false, 5),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '6', 'Inspect glass and interior for moisture.', false, 6),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '7', 'Verify settings and operation in accordance with coordination study, including available time-current curves.', false, 7),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '8', 'Verify that wiring connections are tight and that wiring is secure to prevent damage during operation.', false, 8),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '9', 'Inspect condition of target and flag indicators.', false, 9),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'visual_mechanical', '10', 'Inspect mechanical operation and timing of seal-in units.', false, 10),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'electrical', '1', 'Perform insulation-resistance tests on relay circuits. Applied voltage shall be 500 volts dc.', false, 101),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'electrical', '2', 'Perform pickup and timing tests at 100% of setting.', false, 102),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'electrical', '3', 'Verify correct operation of targets and indicators.', false, 103),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'electrical', '4', 'Calibrate in accordance with coordination study settings.', false, 104),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'electrical', '5', 'Trip circuit breaker by operation of each protective device.', false, 105),
  ('3d2d5569-04bf-4d8c-b6ab-e3b84195c73b', 'electrical', '6', 'Perform contact-resistance tests on auxiliary relays and lockouts.', false, 106);

-- ============================================================
-- Section 7.10.2 Instrument Transformers, Voltage Transformers
-- UUID: 36bc3ad7-bdf5-4d31-b448-260577389194
-- ============================================================
INSERT INTO neta_test_items (procedure_id, test_type, test_number, description, is_optional, sort_order)
VALUES
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'visual_mechanical', '1', 'Compare equipment nameplate data with drawings.', false, 1),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'visual_mechanical', '2', 'Verify connections in accordance with single-line and three-line diagrams.', false, 2),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'visual_mechanical', '3', 'Verify that all required grounding and shorting connections are made.', false, 3),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'visual_mechanical', '4', 'Verify correct wiring and grounding of secondary circuits. Verify grounding of secondaries at one point only.', false, 4),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'visual_mechanical', '5', 'Verify correct operation of primary disconnect devices and associated interlocks.', false, 5),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'visual_mechanical', '6', 'Verify correct fuse sizes and types if fuses are used.', false, 6),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'visual_mechanical', '7', 'Verify that taps and polarity are in accordance with drawings and meter requirements.', false, 7),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'electrical', '1', 'Perform insulation-resistance tests in accordance with Table 100.1 on primary winding and on secondary winding.', false, 101),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'electrical', '2', 'Measure winding resistance and compare to factory test data if available.', false, 102),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'electrical', '3', 'Perform ratio verification test at tap specified on drawings or as close to tap as is practical with test equipment limitations.', false, 103),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'electrical', '4', 'Verify polarity.', false, 104),
  ('36bc3ad7-bdf5-4d31-b448-260577389194', 'electrical', '5', 'Perform insulation power-factor or dissipation-factor tests on voltage transformers rated above 600 volts.', true, 105);

-- ============================================================
-- Section 7.10.3 Instrument Transformers, CCVTs
-- UUID: 65046863-a2c3-4d6e-99a7-298c2ec0e1ec
-- ============================================================
INSERT INTO neta_test_items (procedure_id, test_type, test_number, description, is_optional, sort_order)
VALUES
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'visual_mechanical', '1', 'Compare equipment nameplate data with drawings.', false, 1),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'visual_mechanical', '2', 'Verify connections in accordance with single-line and three-line diagrams.', false, 2),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'visual_mechanical', '3', 'Verify that all required grounding and shorting connections are made.', false, 3),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'visual_mechanical', '4', 'Verify correct wiring and grounding of secondary circuits. Verify grounding of secondaries at one point only.', false, 4),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'visual_mechanical', '5', 'Verify liquid level if applicable.', false, 5),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'visual_mechanical', '6', 'Verify correct fuse sizes and types if fuses are used.', false, 6),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'visual_mechanical', '7', 'Verify that taps and polarity are in accordance with drawings and meter requirements.', false, 7),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'electrical', '1', 'Perform insulation-resistance tests on secondary windings.', false, 101),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'electrical', '2', 'Measure capacitance and dissipation factor on main capacitor (C1) and auxiliary capacitor (C2).', false, 102),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'electrical', '3', 'Perform ratio verification test.', false, 103),
  ('65046863-a2c3-4d6e-99a7-298c2ec0e1ec', 'electrical', '4', 'Verify polarity.', false, 104);

-- ============================================================
-- Summary: Batch 2 adds approximately 100 test items
-- ============================================================
