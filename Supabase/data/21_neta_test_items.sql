-- NETA Test Items Import
-- Generated: 2025-12-11T13:54:52.445511

BEGIN;

INSERT INTO neta_test_items (
  id, procedure_id, test_type, test_number,
  description, is_optional, sort_order
) VALUES
(
    'acaecb6d-d12e-4afd-ae92-c19e07849653',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '1334a407-810f-4fdf-8acd-bea85b3d524c',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical, electrical, and mechanical condition.',
    false,
    2
  ),
(
    '36b3ee62-b118-475a-ad55-fa202d58db18',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and required area clearances.',
    false,
    3
  ),
(
    '7e6f4b61-363d-4c0c-877f-b57efb5440eb',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean and all shipping bracing, loose parts, and documentation shipped inside cubicles have been removed.',
    false,
    4
  ),
(
    'c925b29e-d455-49cf-8a4b-cb1565bdb58d',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '5',
    'Compare mimic diagram and device labeling with drawings.',
    false,
    5
  ),
(
    '94fec954-67e6-4f8e-974e-6f1cec986a4f',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that fuse and circuit breaker sizes and types correspond to drawings and coordination study as well as to the circuit breaker address for microprocessor- communication packages.',
    false,
    6
  ),
(
    '24a6b93a-29ce-4bd6-aee8-b791e9d319a0',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that current and voltage transformer ratios correspond to drawings.',
    false,
    7
  ),
(
    '63543892-ded6-431e-aa77-2dce335519b7',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify that wiring connections are tight and that wiring is secure to prevent damage during routine operation of moving parts.',
    false,
    8
  ),
(
    '567fbca2-f176-4aae-8f93-1316f6ffcedb',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.1.1.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    9
  ),
(
    '9f3cd09f-14bc-484c-bda5-14d969c89342',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '10',
    'Confirm correct operation and sequencing of electrical and mechanical interlock systems.',
    false,
    10
  ),
(
    '7a6a7577-9802-42d1-bacd-05c27671c6d6',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Attempt closure on locked-open devices. Attempt to open locked-closed devices.',
    false,
    11
  ),
(
    '56b7eff8-a97c-4b53-a7b7-ed25271151b0',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Make key exchange with all devices included in the interlock scheme.',
    false,
    12
  ),
(
    '2fa80975-d223-4989-aac2-b84ee2404159',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '11',
    'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    13
  ),
(
    '1482cfd9-4087-4087-b212-a36532e6b37b',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '12',
    'Inspect insulators for evidence of physical damage or contaminated surfaces.',
    false,
    14
  ),
(
    'ac031b93-f180-4a08-a3eb-e490ab062b81',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '13',
    'Verify correct barrier and shutter installation and operation.',
    false,
    15
  ),
(
    '5385faa4-f4cd-4682-bd0e-6629c5319424',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '14',
    'Exercise all active components.',
    false,
    16
  ),
(
    '84e7c681-3ce9-47df-8740-534434c4e7e2',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '15',
    'Inspect mechanical indicating devices for correct operation.',
    false,
    17
  ),
(
    '26f136bd-8391-4ac6-a201-0ae3be759fa5',
    '9d4a3aad-c34e-4ca0-8519-4abb1858341e',
    'visual_mechanical'::neta_test_type,
    '16',
    'Verify that filters are in place and vents are clear. Page 35',
    false,
    18
  ),
(
    '53bb6bb2-ab2a-4920-a4bc-39f9d0084231',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '0032eb92-b9f9-4c3a-bdf5-125f036b4a49',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical, electrical, and mechanical condition.',
    false,
    2
  ),
(
    'a0038b41-8276-460b-87ef-a3b1a15fa981',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, bonding, and required area clearances.',
    false,
    3
  ),
(
    'b9a81836-df66-4c5b-b321-5c427ef164cf',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean and all shipping bracing and loose parts have been removed.',
    false,
    4
  ),
(
    '4ceb12bd-cb82-4259-aed9-e1a3e968300f',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify that fuse and circuit breaker sizes and types correspond to drawings and coordination study.',
    false,
    5
  ),
(
    '80fa8ee5-df27-4aa5-8788-960fa934f86a',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that wiring connections are tight, and that wiring is secure to prevent damage during routine operation of moving parts.',
    false,
    6
  ),
(
    '1b1a006e-e216-4e91-bea2-a4c3a111d497',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer''s data, use Table 100.12.',
    false,
    7
  ),
(
    '5b6fbd08-3417-4e15-ac39-0d6f2aea8cae',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '8',
    'Inspect insulators for evidence of physical damage or contaminated surfaces.',
    false,
    8
  ),
(
    '6fbf61d6-9640-4b16-a5dd-30e7045fc7c7',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify correct barrier installation.',
    false,
    9
  ),
(
    '8f36b9bc-de1a-4af8-b75d-8189043d8fe6',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '10',
    'Perform visual and mechanical inspection on surge protective devices.',
    false,
    10
  ),
(
    'cf6fb611-5f31-4e32-a485-6e9c5b6489a7',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '11',
    'Exercise all active components.',
    false,
    11
  ),
(
    'ac384a56-d6b7-4cfa-9d80-6f13d6515d48',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'visual_mechanical'::neta_test_type,
    '12',
    'Perform thermographic survey in accordance with Section 9',
    true,
    12
  ),
(
    '757ec377-7274-491d-a621-f53bb6c6b686',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'electrical'::neta_test_type,
    '1',
    'Perform insulation-resistance tests for one minute on each bus section, phase-to-phase and phase-to-ground. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.1.',
    false,
    13
  ),
(
    '0aaede53-f171-4488-b11e-baddadab9e28',
    'bfb2713d-95de-4cfe-a4dd-3989ff69ffc5',
    'electrical'::neta_test_type,
    '2',
    'Perform ground-resistance tests in accordance with Section 7.13.',
    false,
    14
  ),
(
    '577b9682-e033-4541-923d-83971f54a2b3',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    'd4feacff-4a08-47b7-a607-ae3a4139560e',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '4bcda2e5-76ff-4430-97af-eb97ec823393',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect impact recorder prior to unloading.',
    false,
    3
  ),
(
    'd1c5413a-5390-45c6-a15e-72b1ea8f21b1',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '4',
    'Test dew point of tank gases.',
    true,
    4
  ),
(
    '4e4013ca-2858-4655-94cd-184de343b4f8',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect anchorage, alignment, and grounding.',
    false,
    5
  ),
(
    'ff846c36-19bc-49ea-8d35-5463e2a152e4',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify the presence of PCB content labeling.',
    false,
    6
  ),
(
    'e91b5114-dc31-41da-a742-659e1aefc1f6',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify removal of any shipping bracing after placement.',
    false,
    7
  ),
(
    'bf31fd84-5998-48b2-848b-69f50e3ba80d',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify the bushings are clean.',
    false,
    8
  ),
(
    '63dced06-da67-4097-986f-98e2a65df3fb',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify that alarm, control, and trip settings on temperature and level indicators are as specified.',
    false,
    9
  ),
(
    'a7b33667-aee5-4730-875b-f073c36d5b60',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify operation of alarm, control, and trip circuits from temperature and level indicators, pressure relief device, gas accumulator, and fault pressure relay.',
    false,
    10
  ),
(
    '1297095b-3f4e-49de-b98b-cb687ba9019c',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '11',
    'Verify that cooling fans and pumps operate correctly and have appropriate overcurrent protection.',
    false,
    11
  ),
(
    '17d6c7a7-f349-4a05-97a4-2cff00b74593',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '12',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.2.2.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    12
  ),
(
    '989e8c09-16aa-4013-b0cd-d03693de193e',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '13',
    'Verify correct liquid level in tanks and bushings.',
    false,
    13
  ),
(
    'cd34ba55-7e06-44ff-80d6-0516a71c1690',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '14',
    'Verify valves are in the correct operating position.',
    false,
    14
  ),
(
    '36b61494-f2c7-4a34-b69b-f42f409d5353',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '15',
    'Verify that positive pressure is maintained on gas-blanketed transformers.',
    false,
    15
  ),
(
    'a738aafe-d18d-4b95-a2ce-3412cd0ccbcb',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '16',
    'Perform inspections and mechanical tests as recommended by the manufacturer.',
    false,
    16
  ),
(
    '7080b78f-b5d4-436c-bdc8-20117e58a991',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '17',
    'Test load tap-changer in accordance with Section 7.12.3.',
    false,
    17
  ),
(
    'ec5fafa4-1c4e-4d17-b3c5-6ae8da098617',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '18',
    'Verify presence of transformer surge arresters.',
    false,
    18
  ),
(
    'fd19d6b0-7c49-467b-bcc1-3eea3bdef385',
    '118d25d7-7230-4e73-bf42-0810025cdeda',
    'visual_mechanical'::neta_test_type,
    '19',
    'Verify de-energized tap-changer position is left as specified. Page 47',
    false,
    19
  ),
(
    '4f31acfe-c6de-4064-ad4a-74a0d7759e7c',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare cable data with drawings and specifications.',
    false,
    1
  ),
(
    'acab19ac-c1be-463f-88cd-9c49507d659f',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect exposed sections of cables and connectors for physical damage, proper termination, and correct connection in accordance with the single-line diagram.',
    false,
    2
  ),
(
    '98ce7351-ca1e-4431-9d0a-86f318126728',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    3
  ),
(
    '5262b7c8-af82-4fec-9616-9ad187cc87fa',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect compression-applied connectors for correct cable match and indentation.',
    false,
    4
  ),
(
    '7fb83308-476a-4e8c-885c-a913d8988f17',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect for correct identification and arrangements.',
    false,
    5
  ),
(
    '9cc26275-49cc-42e4-bad3-8eafd5dd046e',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'visual_mechanical'::neta_test_type,
    '6',
    'Inspect cable jacket insulation and condition.',
    false,
    6
  ),
(
    '6f49d18f-1fc8-417c-b326-1319a0f4e769',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'visual_mechanical'::neta_test_type,
    '7',
    'If cables are terminated through window-type current transformers, inspect to verify that neutral and ground conductors are correctly placed for operation of protective devices.',
    false,
    7
  ),
(
    '0f5ded20-10eb-484e-bfd7-8a2be06634b3',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'visual_mechanical'::neta_test_type,
    '8',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    8
  ),
(
    '9ce989c9-a233-411a-a2d9-ab22a71e4e18',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'electrical'::neta_test_type,
    '1',
    'Perform an insulation-resistance test on each phase/conductor with all other phase/conductors grounded. Applied potential shall be 500 volts dc for 300-volt rated cable and 1000 volts dc for 600-volt rated cable. Test duration shall be one minute.',
    false,
    9
  ),
(
    '6aa37a3a-b386-47be-8396-f28c55dfa107',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'electrical'::neta_test_type,
    '2',
    'Perform continuity tests to ensure correct cable connection.',
    false,
    10
  ),
(
    'b659d62d-4553-409f-acb0-5ffcf6f647d5',
    'fd867145-d4da-400c-8c03-6bfd4849b2f2',
    'electrical'::neta_test_type,
    '3',
    'Verify uniform resistance of parallel conductors.',
    true,
    11
  ),
(
    'dec5c553-28a7-4e34-b486-01fbd4601341',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare cable data with drawings and specifications.',
    false,
    1
  ),
(
    '576998cc-689d-4921-9482-ea4d6927a370',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect terminations, splices, and exposed sections of cables for physical damage.',
    false,
    2
  ),
(
    '9c40d6f7-adb1-44b3-ac63-9888bf0eb218',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    3
  ),
(
    '3f3bbce4-ef26-477d-8275-e8c7cb519e7a',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect compression-applied connectors for correct cable match and indentation.',
    false,
    4
  ),
(
    'e39d3c40-f9cf-45c7-bc38-f09a2999beab',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect shield grounding and cable supports.',
    false,
    5
  ),
(
    '1515c557-b29c-403b-be27-7a84bc0ac32c',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that visible cable bends are not less than ICEA and/or manufacturer’s minimum allowable bending radius.',
    false,
    6
  ),
(
    'fe241265-e7dd-4b96-92a6-b081553d8a35',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '7',
    'Inspect fireproofing in common cable areas.',
    true,
    7
  ),
(
    'e3f2b961-0791-42a5-a023-4c9f3158b41f',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '8',
    'If cables are terminated through window-type current transformers, inspect to verify that neutral and ground conductors are correctly placed and that shields are correctly terminated for operation of protective devices.',
    false,
    8
  ),
(
    '3405e83e-fa06-4243-98f3-b428048243d7',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '9',
    'Inspect for correct identification and arrangements.',
    false,
    9
  ),
(
    'd4ac2cc1-b681-4b09-8e35-0fc1c11d5283',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'visual_mechanical'::neta_test_type,
    '10',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    10
  ),
(
    '24fae5f2-43b6-4ab6-8e92-6be02a45fb54',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'electrical'::neta_test_type,
    '1',
    'Perform an insulation-resistance test individually between each phase/conductor and its shield with all other phase/conductors and shields grounded. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1.',
    false,
    11
  ),
(
    'f13ab6e9-011a-414e-a088-7320a5f198f2',
    '570c106f-77a7-4ef8-a033-e5de8f1e52fb',
    'electrical'::neta_test_type,
    '2',
    'Perform a shield-continuity test on each power cable by ohmmeter method. Page 55',
    false,
    12
  ),
(
    '7b1aeaeb-7af8-4214-8c6d-33904d371127',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '1e899d57-af8a-4e19-8f66-74656888f842',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    'badd010c-b4d8-49b7-9f06-06c3c43893bc',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and required clearances.',
    false,
    3
  ),
(
    '2a2846ec-adc6-49c9-841f-ce90079f0ba1',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    '790357e0-e09f-435d-8fa4-12d4180c562e',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '5',
    'Perform mechanical operator tests in accordance with manufacturer’s published data.',
    false,
    5
  ),
(
    '0077a14b-bc4f-4b9f-9932-7c46d4288dc0',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct operation and adjustment of motor operator limit switches and mechanical interlocks.',
    false,
    6
  ),
(
    '514226f7-a1d6-4338-a011-203102f0814f',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '7',
    'Test all electrical and mechanical interlock systems for correct operation and sequencing.',
    false,
    7
  ),
(
    '030dfa30-22e0-4cc3-8bd8-a9175e5c98ba',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify that each fuse has adequate mechanical support and contact integrity.',
    false,
    8
  ),
(
    'e3650f51-f47a-44c3-9cff-cbbc1148aaa0',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify that fuse sizes and types are in accordance with drawings, short-circuit study, and coordination study.',
    false,
    9
  ),
(
    'd254a0d8-5be1-4fef-b325-5c113ec6a265',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.5.2.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    10
  ),
(
    '7f28019a-166e-4f80-9eb3-4a6275cf7054',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '11',
    'Verify that insulating oil level is correct.',
    false,
    11
  ),
(
    '3b9b1dcf-1ea7-4811-bc89-5528cabb689a',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '12',
    'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    12
  ),
(
    '6e46eb1a-6ee2-45fc-8b59-0ec611f9dbb7',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '13',
    'Record as-found and as-left operation counter readings.',
    false,
    13
  ),
(
    '2ff3ace8-fdd3-4fa8-abd1-54995c2e5848',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'visual_mechanical'::neta_test_type,
    '14',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    14
  ),
(
    '3042ec15-2cd9-444e-92ae-e8b2231f0c21',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    15
  ),
(
    'c162617e-5330-46c6-a559-cba239cb85f3',
    'b07c5e26-00b0-46e8-9a22-fb379deef97e',
    'electrical'::neta_test_type,
    '2',
    'Perform a contact/pole-resistance test. Page 70',
    false,
    16
  ),
(
    '8adc73b0-d1a2-4d8c-aaf0-e000ec3b7244',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '76a2cc56-5ae8-476d-aac9-d1b9f36f516e',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '3c35c43d-7abc-42ca-a813-049785f6eb11',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and required clearances.',
    false,
    3
  ),
(
    '91c31a0d-0077-4d8d-8b92-a1a862f92c62',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    '09257028-dfe2-4cb2-9e2f-855c08d0e325',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '5',
    'Perform mechanical operator tests in accordance with manufacturer’s published data.',
    false,
    5
  ),
(
    'cc8c9b55-f7c2-41f4-965d-0aef33d97a85',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct operation and adjustment of motor operator limit switches and mechanical interlocks.',
    false,
    6
  ),
(
    '09f30cfc-d6ef-48f8-9fa2-69282122f5c6',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify critical distances on operating mechanism as recommended by the manufacturer.',
    false,
    7
  ),
(
    'a18f8fff-9c00-4003-841a-455d386c8704',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '8',
    'Test all electrical and mechanical interlock systems for correct operation and sequencing.',
    false,
    8
  ),
(
    '1327ab40-0696-4ab4-9fce-d92d06ce3314',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify that each fuse has adequate support and contact integrity.',
    false,
    9
  ),
(
    '5d768cb8-1ff9-418d-97b7-dbd013f1e9ac',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify that fuse sizes and types are in accordance with drawings, the short-circuit study, and the coordination study.',
    false,
    10
  ),
(
    'e4aba994-eeec-44e0-952d-bd3c3e814a72',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '11',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.5.3.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    11
  ),
(
    '73c6d0dd-f33f-47bd-97ba-be2617f6446c',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '12',
    'Verify that insulating oil level is correct.',
    false,
    12
  ),
(
    '06562008-d2f4-40e4-a8c9-7f11433da461',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '13',
    'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    13
  ),
(
    '58b5776b-55ea-4aef-9908-54763d708a30',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '14',
    'Record as-left operation counter reading.',
    false,
    14
  ),
(
    '30967b0d-bf7d-439f-9613-4a22871fc59d',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'visual_mechanical'::neta_test_type,
    '15',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    15
  ),
(
    '8e82c6cd-8ffe-4e66-af71-80bcb75b33a9',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted electrical connections with a low resistance ohmmeter.',
    false,
    16
  ),
(
    '8e24402d-c672-4b4e-9f14-eaa7e8c661fd',
    'd86bbb08-82e3-4556-8037-437d63694281',
    'electrical'::neta_test_type,
    '2',
    'Perform a contact/pole-resistance test. Page 73',
    false,
    17
  ),
(
    'a62d8966-f363-47c9-ac82-1f0470845ea0',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '518622dc-79e4-4337-a8f6-3fb0fff8d685',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    'e2f8aef6-dfcc-4106-aab2-f3325b0dc1de',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and required clearances.',
    false,
    3
  ),
(
    '4c67ffd3-e2f7-4360-bf2a-4c4f751da2fa',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    'f07afb84-e988-4add-9471-6acc4956dfa8',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify correct blade alignment, blade penetration, travel stops, latching mechanism, and mechanical operation.',
    false,
    5
  ),
(
    '024228fc-bb70-478b-a849-4ab1df2b05dc',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that each fuseholder has adequate mechanical support and contact integrity.',
    false,
    6
  ),
(
    '2537a562-7f54-4dd2-8cb6-818c3a7c1a9a',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that fuse size and types are in accordance with drawings, short-circuit study, and coordination study.',
    false,
    7
  ),
(
    'adf05d87-8375-433d-8d37-d76b763709a9',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.5.5.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    8
  ),
(
    '22e93cf0-7e06-40e7-a9ec-609f0f574cd8',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'visual_mechanical'::neta_test_type,
    '9',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    9
  ),
(
    '36bb5870-0766-4f22-95d2-0d5870853d35',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    10
  ),
(
    '2d67a166-ad88-4cc7-8eda-28c71f562715',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'electrical'::neta_test_type,
    '2',
    'Measure contact resistance across each cutout.',
    false,
    11
  ),
(
    '88529be6-8452-4107-884a-2edb2ec7a3a5',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'electrical'::neta_test_type,
    '3',
    'Perform insulation-resistance tests for one minute on each pole, phase-to-phase and phase-to-ground with switch closed and across each open pole. Apply voltage in accordance with manufacturer''s published data. In the absence of manufacturer''s data, use Table 100.1.',
    false,
    12
  ),
(
    'f390ba9a-ff4a-4642-9066-574783604acd',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'electrical'::neta_test_type,
    '4',
    'Perform a dielectric withstand voltage test on each pole, phase-to-ground with cutout closed. Ground adjacent cutouts. Test voltage shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.1.',
    false,
    13
  ),
(
    '8e9839ef-5986-48b0-a590-581cbd36385d',
    '0529c27e-8027-4ffb-b7aa-dd5ef7bdf839',
    'electrical'::neta_test_type,
    '5',
    'Measure fuse resistance. Page 79',
    false,
    14
  ),
(
    'b252f89c-ac85-4f23-a637-8691a6c729ec',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '1dba51e4-cfed-47f4-82cf-8fa08b8ea74b',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    'dee7edaf-e494-4c14-8c48-04faa9234c10',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and required clearances.',
    false,
    3
  ),
(
    '10bf0a56-a194-4e49-8cbf-318fcfe6c452',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify that all maintenance devices such as special tools and gauges specified by the manufacturer are available for servicing and operating the breaker.',
    false,
    4
  ),
(
    'b6cfba02-6389-4188-87f1-e4d9e3e53244',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify correct oil level in all tanks and bushings.',
    false,
    5
  ),
(
    '74d4f315-3462-4d1c-8595-e06532d37079',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that breather vents are clear.',
    false,
    6
  ),
(
    '19741103-1c9c-4a67-b73e-26d8a67f313c',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify the unit is clean.',
    false,
    7
  ),
(
    '95f8b2a6-ca0e-4757-9a2e-de26dd4a54fa',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '8',
    'Inspect hydraulic system and air compressor in accordance with manufacturer’s published data.',
    false,
    8
  ),
(
    '0ff96b67-4096-4b7c-9e1a-26e6fc4e9f94',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '9',
    'Test alarms and pressure-limit switches for pneumatic and hydraulic operators as recommended by the manufacturer.',
    false,
    9
  ),
(
    '2883f651-2cfd-40b7-9fee-cffaa3693dfc',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '10',
    'Perform mechanical operation tests on the operating mechanism in accordance with manufacturer’s published data.',
    false,
    10
  ),
(
    'daa09144-c541-4152-8d51-9dba8b60b05a',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform internal inspection:',
    true,
    11
  ),
(
    'e95c3b4d-a45b-4d3d-bba5-66b5d14783e5',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '1',
    'Remove oil. Lower tanks or remove manhole covers as necessary. Inspect bottom of tank for broken parts and debris.',
    false,
    12
  ),
(
    'c89cf0e9-d1dc-46be-90ea-2f7e35ce3eb0',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect lift rod and toggle assemblies, contacts, interrupters, bumpers, dashpots, bushing current transformers, tank liners, and gaskets.',
    false,
    13
  ),
(
    '40c6ed80-5216-43f6-8595-d017fe0d2455',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify that contact sequence is in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use IEEE C37.04.',
    false,
    14
  ),
(
    '05af6b77-3ab3-410c-aba8-7165de545d4f',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '4',
    'Fill tank(s) with filtered oil.',
    false,
    15
  ),
(
    'ebd6e687-17b8-44b1-8770-d5fba31ae5e0',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '12',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.6.2.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    16
  ),
(
    'be973973-0aef-4bd1-8157-00acc9fe2c60',
    '8ae18b82-7a5d-4e93-8953-7f021be82b27',
    'visual_mechanical'::neta_test_type,
    '13',
    'Verify racking mechanism operation. Page 93',
    false,
    17
  ),
(
    '24487693-e4ac-48e1-a80c-5ef1bc3e8ad5',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    'd1541d9a-816f-48ba-9224-f9605fd6f066',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    'a0bf594a-3280-40aa-b8f7-b488b019bdcf',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    'eead2dad-0065-4a33-83c4-986765be02eb',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify that all maintenance devices such as special tools and gauges specified by the manufacturer are available for servicing and operating the breaker.',
    false,
    4
  ),
(
    '639651c9-2b6e-4815-a082-d855011fc60c',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify the unit is clean.',
    false,
    5
  ),
(
    '17be16bf-6a27-458d-874c-06a4533ed7cc',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '6',
    'Perform all mechanical operation tests on the operating mechanism in accordance with manufacturer’s published data.',
    false,
    6
  ),
(
    '3f76593c-0998-410c-9097-30383d77b943',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '7',
    'Measure critical distances such as contact gap as recommended by manufacturer.',
    false,
    7
  ),
(
    '873695ef-0315-4db8-953f-fa2375c7c615',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    8
  ),
(
    'cb0e7eaf-6bea-41d2-9a1f-b7d03e698bc5',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify cell fit and element alignment.',
    false,
    9
  ),
(
    '5269dd13-dca2-462e-b86b-a11bd95cae43',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify racking mechanism operation.',
    false,
    10
  ),
(
    '214b8856-515f-4252-bdfb-adcbb7d88443',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '11',
    'Verify appropriate lubrication on moving, current-carrying parts and on moving and sliding surfaces.',
    false,
    11
  ),
(
    '1e2e71c0-34c0-4cdf-b3e0-d2e69706ad27',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '12',
    'Perform contact-timing test.',
    false,
    12
  ),
(
    '48698f83-4871-40c8-819f-952439df126f',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '13',
    'Perform trip/close coil current signature analysis.',
    true,
    13
  ),
(
    '763ae888-afd0-48bc-828e-c9f521a0ae89',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '14',
    'Perform mechanism motion analysis.',
    true,
    14
  ),
(
    '15591e79-6f61-4e04-8709-90e122a1dd9b',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '15',
    'Record as-found and as-left operation counter readings.',
    false,
    15
  ),
(
    '4e221fc4-2abd-410e-ada7-83a137896135',
    '49055e04-b80c-432f-b374-b7ec6229dcf9',
    'visual_mechanical'::neta_test_type,
    '16',
    'Perform thermographic survey in accordance with Section 9. Page 98',
    true,
    16
  ),
(
    '0b5331e2-308c-4e3a-a3c4-ac7c287eaa37',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '37b941f7-edba-45a0-92d5-4446ed454f83',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '128aed4c-adfe-459b-be1d-94724a8a2bf2',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    '82d4872f-b24b-45b9-a018-89b67930c903',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify that all maintenance devices such as special tools and gauges specified by the manufacturer are available for servicing and operating the breaker.',
    false,
    4
  ),
(
    '8e90597f-6cb8-47aa-824a-a48d24e04586',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify the unit is clean.',
    false,
    5
  ),
(
    '11bf14fc-df8c-4906-93f2-f0be14e28391',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '6',
    'When provisions are made for sampling, remove a sample of SF6 gas and test in accordance with Table 100.13. Do not break seal or distort “sealed-for-life” interrupters.',
    false,
    6
  ),
(
    '84487675-5302-41a1-9a4f-6b6440ab5635',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '7',
    'Inspect operating mechanism and/or hydraulic or pneumatic system and SF6 gas- insulated system in accordance with manufacturer’s published data.',
    false,
    7
  ),
(
    '2a0db52d-f9c1-488d-83ed-4d2ed36a0b94',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '8',
    'Test for SF6 gas leaks in accordance with manufacturer’s published data.',
    false,
    8
  ),
(
    'e17b119a-f793-4f05-95d4-dc37f369cb06',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify correct operation of alarms and pressure-limit switches for pneumatic, hydraulic, and SF6 gas pressure in accordance with manufacturer’s published data.',
    false,
    9
  ),
(
    '0f462797-dc64-43dd-a2f1-768df9e9f7d0',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '10',
    'If recommended by manufacturer, slow close/open breaker and check for binding, friction, contact alignment, and penetration. Verify that contact sequence is in accordance with manufacturer’s published data. In the absence of manufacturer’s data, refer to IEEE C37.04.',
    false,
    10
  ),
(
    '3ebf8f19-d828-4801-b938-769dcc2f81e8',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform all mechanical operation tests on the operating mechanism in accordance with the manufacturer’s published data.',
    false,
    11
  ),
(
    '01484d28-fd96-443e-8285-4270b86daf68',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '12',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.6.4.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    12
  ),
(
    '7fac82a3-6234-4d1b-a407-c428444daff3',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '13',
    'Verify the appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    13
  ),
(
    'fc6b2806-5a77-415a-a758-27eb3802700d',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '14',
    'Perform contact-timing test.',
    false,
    14
  ),
(
    '72756117-203f-47c7-b1c8-c3bd69997e46',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '15',
    'Perform trip/close coil signature analysis.',
    true,
    15
  ),
(
    'b64615e5-2189-4d55-a524-13f8af1f65b9',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '16',
    'Perform mechanism motion analysis for breakers rated 38kV and above. Page 102',
    false,
    16
  ),
(
    '0068ff7e-0fec-42af-881f-6c6599070090',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '17',
    'Record as-found and as-left operation counter readings.',
    false,
    17
  ),
(
    '37141440-b7f1-4bd5-9fb1-0d96fd6e3f01',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'visual_mechanical'::neta_test_type,
    '18',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    18
  ),
(
    '5867b2d9-87f3-45b7-b160-59810b067073',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through all bolted connections with a low-resistance ohmmeter.',
    false,
    19
  ),
(
    '360e31fa-16d3-44eb-88c6-2020481eec18',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests in accordance with Table 100.1 from each pole-to- ground with breaker closed and across open poles at each phase. For single-tank breakers, perform insulation resistance tests in accordance with Table 100.1 from pole-to-pole.',
    false,
    20
  ),
(
    '1a6c9e35-531c-4b53-97b8-16bc6f710092',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '3',
    'Perform a static contact/resistance test.',
    false,
    21
  ),
(
    'cbbb7ee8-abcc-4d9d-bdb9-f1651ad21c28',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '4',
    'Perform a dynamic contact/pole resistance test.',
    true,
    22
  ),
(
    '97d7c19e-d958-45e1-9727-7dcac4b95d4c',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '5',
    'Perform insulation-resistance tests on all control wiring with respect to ground. Applied potential shall be 500 volts dc for 300-volt rated cable and 1000 volts dc for 600-volt rated cable. Test duration shall be one minute. For units with solid-state components or for control devices that cannot tolerate the voltage, follow manufacturer’s recommendation.',
    true,
    23
  ),
(
    '97e14ed7-354e-4e6a-a525-05c099eebbd4',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '6',
    'Perform minimum pickup voltage tests on trip and close coils in accordance with manufacturer’s published data.',
    false,
    24
  ),
(
    '9402b2ea-6605-400a-8cb8-fba288588158',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '7',
    'Verify correct operation of any auxiliary features such as electrical close and trip operation, trip-free, and antipump function. Reset all trip logs and indicators.',
    false,
    25
  ),
(
    '34687073-42ef-488c-a513-da3d00fdf03e',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '8',
    'Trip circuit breaker by operation of each protective device.',
    false,
    26
  ),
(
    'be9056de-2e1d-48c8-92cf-78087332b77f',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '9',
    'Perform power-factor or dissipation-factor tests on each pole with the breaker open and on each phase with the breaker closed.',
    false,
    27
  ),
(
    '13cde99d-53a6-4440-945a-665623439b1e',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '10',
    'Perform power-factor or dissipation-factor tests on each bushing equipped with a power- factor/capacitance tap. In the absence of a power-factor/capacitance tap, perform hot- collar tests. These tests shall be in accordance with the test equipment manufacturer’s published data.',
    false,
    28
  ),
(
    '297a65cd-f6ff-402e-b8d4-15889ec7d484',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '11',
    'Perform a dielectric withstand voltage test in accordance with manufacturer’s published data.',
    true,
    29
  ),
(
    'dceeba6f-183f-4ec1-a6c8-e895379c3338',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '12',
    'Verify operation of heaters.',
    false,
    30
  ),
(
    '487c618e-27a0-4043-8bdb-6ab8a7ab6ec2',
    '467c3b0f-854c-45c7-9d7c-24b9e06fe267',
    'electrical'::neta_test_type,
    '13',
    'Test instrument transformers in accordance with Section 7.10. Page 103',
    false,
    31
  ),
(
    '23021dae-c229-4799-8528-c247f5be9285',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '3f50b23a-1b5c-473a-b4fa-2992bde867fd',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect relays and cases for physical damage. Remove shipping restraint material.',
    false,
    2
  ),
(
    'be1d9a7b-c7ff-42a4-a91a-04046e6abad2',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify the unit is clean.',
    false,
    3
  ),
(
    '5bede785-01ad-4461-8fbb-9ae8ad820b13',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect the unit.',
    false,
    4
  ),
(
    '00f034b5-39ee-40f7-81e9-67b0858a306a',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Tighten case connections.',
    false,
    5
  ),
(
    'e8661754-646e-4e2e-af62-e07503db0145',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect cover for correct gasket seal.',
    false,
    6
  ),
(
    '3938724b-e426-4f65-9baf-d7dbb1adc9f4',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect shorting hardware, connection paddles, and knife switches.',
    false,
    7
  ),
(
    '99032762-ca1d-426e-b9a1-f1d0db0307b4',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '4',
    'Remove any foreign material from the case.',
    false,
    8
  ),
(
    'b1a53f8f-d485-4490-855e-f1cef5a6183f',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify target reset.',
    false,
    9
  ),
(
    'f0f7dfc6-a5fe-404d-a8de-3f9f0b2da25a',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '6',
    'Clean cover glass.',
    false,
    10
  ),
(
    '79567fbe-cd66-49c6-9245-6c68d1b9a928',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect relay for foreign material, particularly in disk slots of the damping and electromagnets.',
    false,
    11
  ),
(
    '22a34c12-ae35-4460-a3ee-20dfab2f2b3f',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify disk clearance throughout its travel. Verify contact follow and spring tension.',
    false,
    12
  ),
(
    '74fdb74a-777c-45f3-a8a3-4e202613c42b',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect spiral spring convolutions.',
    false,
    13
  ),
(
    '91955759-c3d0-4cdc-9b12-3e64d58fce70',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect disk and contacts for freedom of movement and correct travel.',
    false,
    14
  ),
(
    '75c16794-b852-403a-b311-42c180e8a4a7',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify tightness of mounting hardware and connections.',
    false,
    15
  ),
(
    '16334f18-3ecb-4288-85ae-76441ed7afa0',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '6',
    'Burnish contacts.',
    false,
    16
  ),
(
    '273a283a-2719-4fc5-973a-667c4c767646',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '7',
    'Inspect bearings and pivots.',
    false,
    17
  ),
(
    '116475de-73b6-4560-b3ad-e14df2765a32',
    'e755ee88-fe8b-4e01-bd78-903e1c972f9e',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify that all settings are in accordance with coordination study or setting sheet supplied by owner. Page 113',
    false,
    18
  ),
(
    'd5d13f94-e15a-46b3-87be-e19cb65fc090',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '1',
    'Record model number, style number, serial number, firmware revision, software revision, and rated control voltage.',
    false,
    1
  ),
(
    '91e6b1a0-68f2-4784-878f-369f34eef5f3',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify operation of light-emitting diodes, display, and targets.',
    false,
    2
  ),
(
    '612f853f-2ad3-48ea-9c2f-99b05ffb59e7',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '3',
    'Record passwords for all access levels.',
    false,
    3
  ),
(
    '54e8e665-fafd-4c20-853d-10747c7e7497',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the front panel and remove foreign material from the case.',
    false,
    4
  ),
(
    'fb310fed-e226-43b7-b11a-f0f89303bcbc',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '5',
    'Check tightness of connections.',
    false,
    5
  ),
(
    '30132f86-5270-454b-86cc-a4f48b674bdb',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that the frame is grounded in accordance with manufacturer’s instructions.',
    false,
    6
  ),
(
    '58887696-85a3-4eea-b946-1e1d6de41b56',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '7',
    'Upload owner supplied relay settings file.',
    false,
    7
  ),
(
    'fe790e0a-19f2-4794-a955-c7341f9ac13e',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '8',
    'Download settings and logic from the relay and compare the settings to those specified in the coordination study or setting sheet supplied by owner.',
    false,
    8
  ),
(
    'daeafb37-7ba3-42fc-ab58-9ef73f627077',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '9',
    'Set clock if not controlled externally and verify relay displays the correct date and time.',
    false,
    9
  ),
(
    '07e0046d-8af6-47a7-b0da-fd05d5d311f0',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '10',
    'Check with setting engineer for applicable firmware updates and product recalls.',
    false,
    10
  ),
(
    '97779f72-57d3-49ab-864b-206130673640',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'visual_mechanical'::neta_test_type,
    '11',
    'Inspect, clean, and verify operation of shorting devices.',
    false,
    11
  ),
(
    'a684ac1d-01da-4da0-882e-c5c8d9bc43a6',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'electrical'::neta_test_type,
    '1',
    'Perform insulation-resistance tests from each circuit to the grounded frame in accordance with manufacturer’s published data.',
    false,
    12
  ),
(
    'ea7f76c5-040c-4f04-8e97-9945e5275948',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'electrical'::neta_test_type,
    '2',
    'Apply voltage or current to all analog inputs and verify correct registration of the relay meter functions.',
    false,
    13
  ),
(
    '9da007d0-1944-4b3c-a522-fbba9dc3cdea',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'electrical'::neta_test_type,
    '3',
    'Verify SCADA metering values and digital status points at remote terminals.',
    true,
    14
  ),
(
    '1302bb1f-946d-4bb2-9d7e-3b5c4df74a84',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'electrical'::neta_test_type,
    '4',
    'Protection Elements Check functional operation of each element used in the protection scheme as described for electromechanical and solid-state relays in 7.9.1.B.3. When not otherwise specified, use manufacturer’s recommended tolerances.',
    false,
    15
  ),
(
    'e47ed0c3-52c3-4d5a-805c-82be3b2a084d',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'electrical'::neta_test_type,
    '5',
    'Control Verification',
    false,
    16
  ),
(
    'ff165813-203b-41c4-a03d-0c40ca4d01d1',
    '928c78f1-e6b4-4448-baf8-517d3ba49b16',
    'electrical'::neta_test_type,
    '1',
    'Check operation of all active digital inputs. Page 121',
    false,
    17
  ),
(
    '325c9f5f-b82c-4fa8-a737-af9aee79cdae',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '09bc7ef0-b5c9-4750-8853-bae93ec05e33',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    'c9ca2627-8493-459c-a3d1-1fc27024f478',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify correct connection of transformers with system requirements.',
    false,
    3
  ),
(
    '97c7344c-100b-498e-b38c-2be59537d62a',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify that adequate clearances exist between primary and secondary circuit wiring.',
    false,
    4
  ),
(
    '29edd7b9-9921-4452-97cf-55969ea6910c',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify the unit is clean.',
    false,
    5
  ),
(
    '21be6d20-9d1a-43c5-b5a1-5f1ac07d326d',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    6
  ),
(
    '33abff7b-3c6c-4929-979f-95da3f914e30',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that all required grounding and shorting connections provide contact.',
    false,
    7
  ),
(
    '3273acd3-f2a3-414d-8d2a-91e285e532c9',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    8
  ),
(
    '14945d7d-0cc5-4a7e-b151-e38a02e8dfb9',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'visual_mechanical'::neta_test_type,
    '9',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    9
  ),
(
    '90df8df3-a9bd-4b9f-8a19-37f312b7c8f4',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'electrical'::neta_test_type,
    '1',
    'Perform insulation-resistance test of each current transformer and its secondary wiring with respect to ground at 1000 volts dc for one minute. For units with solid-state components that cannot tolerate the applied voltage, follow manufacturer’s recommendations.',
    false,
    10
  ),
(
    '963a64a2-8080-4445-b64f-d754a33d38ea',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'electrical'::neta_test_type,
    '2',
    'Perform a polarity test of each current transformer in accordance with IEEE C57.13.1.',
    false,
    11
  ),
(
    '8e4c6145-95d5-4202-b500-b3b696c2c3cb',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'electrical'::neta_test_type,
    '3',
    'Perform a ratio-verification test using the voltage or current method in accordance with IEEE C57.13.1.',
    false,
    12
  ),
(
    '69d59a78-567d-4250-a713-2ca625d8436b',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'electrical'::neta_test_type,
    '4',
    'Perform an excitation test on transformers used for relaying applications in accordance with IEEE C57.13.1.',
    false,
    13
  ),
(
    '70a8e173-900f-49ec-9450-ed83970af76e',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'electrical'::neta_test_type,
    '5',
    'Measure current circuit burdens at CT shorting terminal block in accordance with IEEE C57.13.1',
    false,
    14
  ),
(
    'cd285df7-86c1-423a-a8f5-941f3aa219aa',
    '66cfff24-7b98-4489-98fe-7d1a94f439dc',
    'electrical'::neta_test_type,
    '6',
    'Perform insulation-resistance tests on the primary winding of bar-type CTs with the secondary grounded. Test voltages shall be in accordance with Table 100.5. Page 124',
    false,
    15
  ),
(
    '4514f744-d7fa-4b32-a9d6-7df88c7b772f',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '53256e73-87c5-49b3-9213-04c5111f9e72',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '7623295b-1e95-408f-88dc-09ebf3c7fa41',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify correct connection of transformers with system requirements.',
    false,
    3
  ),
(
    'eccb936c-0f4e-4f77-aad4-b6b5d456eceb',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify that adequate clearances exist between primary and secondary circuit wiring.',
    false,
    4
  ),
(
    'b5ac4413-9dab-4ae3-9d07-18697505043e',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify the unit is clean.',
    false,
    5
  ),
(
    'f694cd34-22f3-4b59-a4c3-3b5745ef45e3',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    6
  ),
(
    'af83b1c4-4775-435d-9a37-2a86820a2dd7',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that all required grounding and connections provide contact.',
    false,
    7
  ),
(
    '3d83e6d4-9e26-4983-8570-934a603a2fe8',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify correct primary and secondary fuse sizes for voltage transformers.',
    false,
    8
  ),
(
    '065550e9-b192-48a3-a7fe-9f43aa99e125',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    9
  ),
(
    '34458b38-844f-4d02-9cff-d95486cd36ee',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '10',
    'Perform as-left tests.',
    false,
    10
  ),
(
    '7a09c2b1-6d5d-481d-9b76-6216aab544d8',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    11
  ),
(
    '1dd1ee5a-cdaa-48a0-a6fc-48c0033ea88a',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'electrical'::neta_test_type,
    '1',
    'Perform insulation-resistance tests for one minute winding-to-winding and each winding- to-ground. Test voltages shall be applied for one minute in accordance with Table 100.5. For units with solid-state components that cannot tolerate the applied voltage, follow manufacturer’s recommendations.',
    false,
    12
  ),
(
    '21ea9210-ad5b-47d2-9d8f-4caf5f0f1365',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'electrical'::neta_test_type,
    '2',
    'Perform a polarity test on each transformer to verify the polarity marks or H1-X1 relationship as applicable.',
    false,
    13
  ),
(
    'c791e013-98d9-40df-940e-43382166818d',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'electrical'::neta_test_type,
    '3',
    'Perform a turns-ratio test on all tap positions.',
    false,
    14
  ),
(
    '9d06b007-08ab-4a2e-893f-a0031726bef7',
    '9d71631d-813e-4fc1-9c23-3e378993b7d7',
    'electrical'::neta_test_type,
    '4',
    'Measure voltage circuit burdens at transformer terminals. Page 126',
    false,
    15
  ),
(
    '0183bf30-8d0f-449a-99d9-b5f2e52308cb',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    'fb5f530e-0fb2-4d90-9536-f2f3078484e7',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    'edf81f22-4237-4743-963b-813ec45f2498',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify correct connection of transformers with system requirements.',
    false,
    3
  ),
(
    'ebd3fc9d-a0b6-42ea-8f9b-77f8d9f2585d',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify that adequate clearances exist between primary and secondary circuit wiring.',
    false,
    4
  ),
(
    '3653f3b0-2a31-4a4b-bea3-9263382177b3',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify the unit is clean.',
    false,
    5
  ),
(
    '83e2d1ab-26bf-40d4-a28c-51d4620823c5',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.10.3.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    6
  ),
(
    '4416f735-0815-44ef-97ec-9f350f2c7772',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that all required grounding and connections provide contact.',
    false,
    7
  ),
(
    '7c052bc0-5445-4eb3-b987-56160fd21b9e',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify correct primary and secondary fuse sizes for voltage transformers.',
    false,
    8
  ),
(
    '0e9d0fd3-a74b-4c12-9f65-87b0765d98bf',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    9
  ),
(
    '69ded93b-c94e-4a0a-8d8f-b4a6c35b766a',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '10',
    'Perform as-left tests.',
    false,
    10
  ),
(
    'c02280ef-fea5-434d-a5b1-1748191d29ab',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    11
  ),
(
    '92c3ba36-87be-4105-84ab-104a8979e752',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    12
  ),
(
    '4a417a0f-9439-4800-bad8-5e2287ca129a',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests for one minute winding-to-winding and each winding- to-ground. Test voltages shall be applied for one minute in accordance with Table 100.5. For units with solid-state components that cannot tolerate the applied voltage, follow manufacturer’s recommendations.',
    false,
    13
  ),
(
    '42b18d26-8ca2-47e3-8557-e396c7d22cc2',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'electrical'::neta_test_type,
    '3',
    'Perform a polarity test on each transformer to verify the polarity marking. See IEEE C93.1 for standard polarity marking.',
    false,
    14
  ),
(
    '876f4fd6-ac34-4b60-92df-84ea56ac7c22',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'electrical'::neta_test_type,
    '4',
    'Perform a ratio test on all tap positions.',
    false,
    15
  ),
(
    '0d67bcd3-b0ed-49d4-a312-6cc9545fc167',
    '7f4ec259-87f8-47b0-99dc-ea37fd945a25',
    'electrical'::neta_test_type,
    '5',
    'Measure voltage circuit burdens at transformer terminals. Page 129',
    false,
    16
  ),
(
    '2b250d6f-7dbe-48c1-9eee-74480308fd14',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '05c597b1-b938-4862-a378-fc7af117d3b7',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    'd7ea7d0f-789b-4783-8e80-05e680ff5b01',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify tightness of electrical connections.',
    false,
    3
  ),
(
    'f30ae9fb-8cca-4206-8dc3-c957ed5b7a0c',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect cover gasket, cover glass, condition of spiral spring, disk clearance, contacts, and case-shorting contacts, as applicable.',
    false,
    4
  ),
(
    'b276aa2f-7ce2-46e8-a995-70d68ece3a4b',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify the unit is clean.',
    false,
    5
  ),
(
    '1c193a63-fa13-448d-8954-157200b92ac7',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify freedom of movement, end play, and alignment of rotating disk(s).',
    false,
    6
  ),
(
    '0d450989-23fd-42f5-93dc-bd85c6b311c9',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'electrical'::neta_test_type,
    '1',
    'Verify accuracy of meters per manufacturer’s published data.',
    false,
    7
  ),
(
    'cf7f1959-ec9b-485f-ac32-0c3cf87bc4a2',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'electrical'::neta_test_type,
    '2',
    'Calibrate meters in accordance with manufacturer’s published data.',
    false,
    8
  ),
(
    '3be18458-b7de-4eed-baf7-a58a0b480f0b',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'electrical'::neta_test_type,
    '3',
    'Verify all instrument multipliers.',
    false,
    9
  ),
(
    '63c98039-8d8b-4b40-8c41-c638734a1924',
    'ea26f59a-fda9-4469-88d5-bea5261da75c',
    'electrical'::neta_test_type,
    '4',
    'Verify that current transformer and voltage transformer secondary circuits are intact.',
    false,
    10
  ),
(
    'c5696cbf-e282-49af-96ab-f74d79266a3d',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '8152867a-7dcb-4c6f-97c5-c2d6de37d640',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect meters and cases for physical damage.',
    false,
    2
  ),
(
    'b9e582e0-64a2-48f3-8613-739b2033f004',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify the unit is clean.',
    false,
    3
  ),
(
    '0eabf249-c16f-4941-982c-0bb68a8371ec',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify tightness of electrical connections.',
    false,
    4
  ),
(
    'cd024487-1211-47e1-b4bb-15116cc360c6',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '5',
    'Record model number, serial number, firmware revision, software revision, and rated control voltage.',
    false,
    5
  ),
(
    '908b8ba4-df02-4b1b-94a0-660d3b3d48fc',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify operation of display and indicating devices.',
    false,
    6
  ),
(
    'a9fa1fda-6ea5-4b7b-9c92-6fd494769cbf',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '7',
    'Record passwords.',
    false,
    7
  ),
(
    'aee1a225-2bdb-4e13-b5d0-922c5dec3636',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify unit is grounded in accordance with manufacturer’s instructions.',
    false,
    8
  ),
(
    '2dc969ce-f7c5-4429-808b-6fd239971d3b',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify unit is connected in accordance with manufacturer’s instructions and project drawings.',
    false,
    9
  ),
(
    '258a5620-f5c4-43bb-9081-689d85b94e9b',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'visual_mechanical'::neta_test_type,
    '10',
    'Upload owner supplied settings file.',
    false,
    10
  ),
(
    '45c78e29-e20d-431c-b6f4-dc9ba080d3b7',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'electrical'::neta_test_type,
    '1',
    'Apply voltage or current as appropriate to each analog input and verify correct measurement and indication.',
    false,
    11
  ),
(
    'dc5d4407-a6e9-4335-834f-0ca1b89c66d7',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'electrical'::neta_test_type,
    '2',
    'Confirm correct operation and setting of each auxiliary input/output feature in use, including mechanical relay, digital, and analog.',
    false,
    12
  ),
(
    'ff45f3c0-7f6e-4c7b-8858-d9a5480f0486',
    'dcb5d71f-1379-4057-af07-83036bf877bb',
    'electrical'::neta_test_type,
    '3',
    'After initial system energization, confirm measurements and indications are consistent with loads present in accordance with ANSI/NETA ECS Standard for Electrical Commissioning Specifications for Electrical Power Equipment and Systems.',
    false,
    13
  ),
(
    '8fb50ca9-0388-4ed7-acff-e0d40912487e',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '70656219-c1b5-4b6c-a64e-3f0101b21bd2',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '9bafd5ff-5b27-421d-8375-81193323f45d',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    '34100d5b-e970-4fc5-8a39-6460a74bc5ec',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect impact recorder.',
    false,
    4
  ),
(
    '400282b2-71c8-4532-962a-b6d621478bdd',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify removal of any shipping bracing and vent plugs.',
    false,
    5
  ),
(
    '613f1316-ef66-4f99-a425-fa4c1a48e565',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify the unit is clean.',
    false,
    6
  ),
(
    '88b9a7a5-18ca-410d-87ef-7f29505e15e7',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    7
  ),
(
    '93a7594b-c5d9-4f9b-9059-838f506bf21b',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify correct auxiliary device operation.',
    false,
    8
  ),
(
    '449e99be-0802-4f82-aef9-389a17078b7b',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify correct operation of motor and drive train and automatic motor cutoff at maximum lower and maximum raise positions.',
    false,
    9
  ),
(
    '263f810c-cd20-4e69-9a2e-2d5e69dd8da2',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify appropriate liquid level in all tanks.',
    false,
    10
  ),
(
    'becfda18-e2d2-4908-bbd8-76c474bbb36e',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform specific inspections and mechanical tests as recommended by the manufacturer.',
    false,
    11
  ),
(
    'dcc37ca6-eb7f-4eae-856b-c2c785ef2bd8',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '12',
    'Verify appropriate lubrication on motor components.',
    false,
    12
  ),
(
    '15faf31e-6a7a-4366-8d74-2ff9dfc56c70',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '13',
    'Record as-found and as-left operation counter readings.',
    false,
    13
  ),
(
    '4ac017f3-f8c9-4d8d-89a7-5104c0750bc5',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'visual_mechanical'::neta_test_type,
    '14',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    14
  ),
(
    '2d39f86e-9c76-4e3a-91a1-a8f34116147b',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'electrical'::neta_test_type,
    '1',
    'Perform insulation-resistance tests in any off-neutral position in accordance with Section 7.2.2.',
    false,
    15
  ),
(
    '8e41e4cc-22ac-46a5-b184-872bd3e0185c',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation power-factor or dissipation-factor tests in accordance with Section 7.2.2.',
    false,
    16
  ),
(
    'a0c199c9-a506-440b-ac11-36f79800c75e',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'electrical'::neta_test_type,
    '3',
    'Perform winding-resistance test at each tap position.',
    true,
    17
  ),
(
    '70b7d757-1777-4a31-a80d-1a77935487af',
    'd0d8dcd1-a0f3-4d5a-88ad-5190c5de0432',
    'electrical'::neta_test_type,
    '4',
    'Perform special tests and adjustments as recommended by the manufacturer. Page 143',
    false,
    18
  ),
(
    'c3ac710a-270d-47d9-9ec3-b8d5200e4a4b',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '7e7eba52-64f4-412a-a8b6-c700e90f0ebc',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '19391894-3a38-4dd2-a407-c8163cf935cc',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    'a5beacb6-4b51-4a25-8f95-4658d564a1a0',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect air baffles, filter media, stator winding, stator core, rotor, cooling fans, slip rings, brushes, brush rigging, and bearings.',
    false,
    4
  ),
(
    '14b49618-eb55-4180-be21-60429d81eb58',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.15.1.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    5
  ),
(
    '8e7c627e-8e7e-407d-bcaf-f5c79616a060',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '6',
    'Perform special tests such as air-gap spacing and machine alignment.',
    true,
    6
  ),
(
    '65eb9df6-3155-4303-8988-668d8b5414e5',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '7',
    'Manually rotate the rotor and check for problems with the bearings or shaft.',
    true,
    7
  ),
(
    'b3f3a060-912a-4f35-a6a2-31f9705f57e3',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '8',
    'Rotate the shaft and measure and record the shaft extension runout.',
    true,
    8
  ),
(
    '5d89bd94-7cf7-430f-aff4-2a2123a8e812',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify the application of appropriate lubrication and lubrication systems.',
    false,
    9
  ),
(
    '82a9a231-63f7-4f00-942a-b0f3f921eaa9',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify that resistance temperature detector (RTD) circuits conform to drawings.',
    false,
    10
  ),
(
    '69664737-b680-421a-ab2c-cdf4501b0a51',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    11
  ),
(
    '00b22959-28a6-44b9-95da-e41e9cb40bad',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    12
  ),
(
    '7d6f320a-11fa-43f3-83d6-43a65afc1b38',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests in accordance with IEEE Standard 43.',
    false,
    13
  ),
(
    '94d769dc-99e8-4d2c-b015-1765b5505756',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'electrical'::neta_test_type,
    '1',
    'Machines larger than 200 horsepower (150 kilowatts): Test duration shall be ten minutes. Calculate polarization index.',
    false,
    14
  ),
(
    '6659e155-505f-425c-b7eb-fb103042b6df',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'electrical'::neta_test_type,
    '2',
    'Machines 200 horsepower (150 kilowatts) and less: Test duration shall be one minute. Calculate dielectric-absorption ratio for 60/30 second periods.',
    false,
    15
  ),
(
    '1fff22d0-b6c0-4a9b-b845-624d92ac0148',
    'f31d1615-56c4-4cf3-bf27-fde69e42cbe8',
    'electrical'::neta_test_type,
    '3',
    'On machines rated at 2300 volts and greater, perform dielectric withstand voltage tests in accordance with: Page 150',
    false,
    16
  ),
(
    '284da5fc-e0e1-4403-841e-4e6ead68a3ce',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    'f2b35957-0a92-4d43-bed6-828a60278036',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '469039cb-a88d-4e40-9c72-c5cb4bcbbd40',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    '0e58673c-b228-440f-b5c2-3e011b46be98',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect air baffles, filter media, stator windings, stator core, rotor, cooling fans, slip rings, brushes, brush rigging, and bearings.',
    false,
    4
  ),
(
    '56d0a7b6-6488-4ade-86a3-a8344a5f4bcb',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.15.2.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    5
  ),
(
    '6faccb6e-cc66-4f8a-99b8-f4ac790d3221',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '6',
    'Perform special tests such as air-gap spacing and machine alignment.',
    false,
    6
  ),
(
    '1cdd2386-a7e7-46c9-a930-8974928154c4',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '7',
    'Manually rotate the rotor and check for problems with the bearings or shaft.',
    false,
    7
  ),
(
    '468a30ea-fbba-4322-8dbd-f941993640e8',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '8',
    'Rotate the shaft and measure and record the shaft extension runout.',
    false,
    8
  ),
(
    '26af13eb-d2e5-45b8-a052-c7b65e6153b2',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify the application of appropriate lubrication and lubrication systems.',
    false,
    9
  ),
(
    'f399ee63-e437-42a0-97f4-080d5ed11768',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify that resistance temperature detector (RTD) circuits conform to drawings.',
    false,
    10
  ),
(
    'ccf066f5-4936-4417-9d97-56452d5c2093',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    11
  ),
(
    '574654a2-0d42-4ab2-88e4-48e4f20a5cb2',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    12
  ),
(
    '72b18a2b-8ef7-4991-9dad-ba87294c5ac5',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests in accordance with IEEE Standard 43.',
    false,
    13
  ),
(
    'cbcf7971-ef2a-4b27-a48a-3060534a6dab',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'electrical'::neta_test_type,
    '1',
    'Machines larger than 200 horsepower (150 kilowatts): Test duration shall be for ten minutes. Calculate polarization index.',
    false,
    14
  ),
(
    '256ee35c-54f6-4273-b6d4-6bb048381472',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'electrical'::neta_test_type,
    '2',
    'Machines 200 horsepower (150 kilowatts) and less: Test duration shall be for one minute. Calculate dielectric-absorption ratio.',
    false,
    15
  ),
(
    '602bd03e-7e40-453a-b20d-fc5a33820cca',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'electrical'::neta_test_type,
    '3',
    'On machines rated at 2300 volts and greater perform dielectric withstand voltage tests in accordance with:',
    false,
    16
  ),
(
    'c580b5c7-f54b-4f52-b925-3ef74f57c191',
    'e55ea616-1c0f-414a-8092-cfcd0d7bd38f',
    'electrical'::neta_test_type,
    '1',
    'IEEE Standard 95 for dc dielectric withstand voltage tests. Page 154',
    false,
    17
  ),
(
    'd1640bb0-7c3d-414f-9ddf-f83a41ae4c2f',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    'c015283d-1987-4a63-aecd-0ff41e861a76',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '4bff5ba9-bfa6-4fea-979e-8879e16c8f10',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    '95de707a-3b9a-4330-8d63-97b2f2588cd1',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect air baffles, filter media, field poles and yokes, armature, cooling fans, commutator, brushes, brush rigging, and bearings.',
    false,
    4
  ),
(
    '01e5bb2a-2938-471b-a892-30f874ec5db4',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.15.3.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    5
  ),
(
    'afb56efb-d4bd-429f-977b-039857336118',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '6',
    'Inspect commutator and tachometer generator.',
    false,
    6
  ),
(
    'c284ede4-c1a5-403b-92fd-2cf121c70903',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '7',
    'Perform special tests such as air-gap spacing, bar tightness of commutator, and machine alignment.',
    true,
    7
  ),
(
    '071d8e87-0d3d-4f5d-a3a8-b4ec4f432105',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '8',
    'If the armature can be manually rotated, check for any obvious problems with the bearings or shaft.',
    true,
    8
  ),
(
    'caa0a8fa-7366-4890-a142-f647d4a1d2ba',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '9',
    'If the motor shaft can be rotated, measure and record the shaft extension runout.',
    true,
    9
  ),
(
    '959757f0-b30b-4c41-bcbd-779cdf7d56a5',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'visual_mechanical'::neta_test_type,
    '10',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    10
  ),
(
    'be210440-067d-4743-8282-25ddf80aa919',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    11
  ),
(
    'f25bbfa2-0514-4c94-ac6d-9a0fa30c9067',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests on all windings in accordance with IEEE Standard 43.',
    false,
    12
  ),
(
    '0ef5ae6a-b301-47c8-b7b4-b89e6c23ebba',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'electrical'::neta_test_type,
    '1',
    'Machines larger than 200 horsepower (150 kilowatts): Test duration shall be for ten minutes. Calculate polarization index.',
    false,
    13
  ),
(
    'f87cf50b-ecfc-4901-982b-a8d9ac0f0e49',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'electrical'::neta_test_type,
    '2',
    'Machines 200 horsepower (150 kilowatts) and less: Test duration shall be for one minute. Calculate dielectric absorption ratio for 60/30 second periods.',
    false,
    14
  ),
(
    '0c1da0a8-e37e-43af-8ce7-3962417ce533',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'electrical'::neta_test_type,
    '3',
    'Perform high-potential test in accordance with NEMA MG 1, Section 3.01.',
    true,
    15
  ),
(
    '96f14b31-1332-4b4f-9f0b-c96e156e2d31',
    '5962ca17-7d6b-43c5-a5ae-dedfd6314bfb',
    'electrical'::neta_test_type,
    '4',
    'Perform an ac voltage-drop test on all field poles. Page 160',
    true,
    16
  ),
(
    '13b73708-f371-4b03-a1d6-21fc598d6057',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '9f141bab-3556-403c-bc7c-20eefacad3b4',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect for physical and mechanical condition.',
    false,
    2
  ),
(
    '488de00d-355d-43a3-906a-506c33174466',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    '9c044109-d3c4-4250-a4df-5b582515d1c3',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    '5f600d3d-6119-45f1-99d4-58e37e0a8e97',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.18.2.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    5
  ),
(
    'f59904c4-050d-41ca-9a40-3b4bcaed0857',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'visual_mechanical'::neta_test_type,
    '6',
    'Inspect filter and tank capacitors.',
    false,
    6
  ),
(
    '1d36cc47-92b7-4afd-8a3c-ab903667c6af',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify operation of cooling fans and presence of filters.',
    false,
    7
  ),
(
    'b69bcbd3-7a0f-44dc-aa0a-febba5ec39ee',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'visual_mechanical'::neta_test_type,
    '8',
    'Perform thermographic survey in accordance with Section 9.',
    false,
    8
  ),
(
    '068330e0-3823-490e-bba1-5c13570f908e',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through all bolted connections with a low-resistance ohmmeter.',
    false,
    9
  ),
(
    'a8628630-cd87-495d-b39e-29f699ef2127',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'electrical'::neta_test_type,
    '2',
    'Verify float voltage and equalize voltage.',
    false,
    10
  ),
(
    '93ac20b4-435a-402d-b871-022d1535d1b0',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'electrical'::neta_test_type,
    '3',
    'Verify high-voltage shutdown settings.',
    false,
    11
  ),
(
    'a3659df2-670e-46cd-b986-2f54ec99bc66',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'electrical'::neta_test_type,
    '4',
    'Verify correct load sharing (parallel chargers).',
    false,
    12
  ),
(
    '83d0ea36-1d39-4761-89c5-b48894f35e5c',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'electrical'::neta_test_type,
    '5',
    'Verify calibration of meters in accordance with Section 7.11.',
    false,
    13
  ),
(
    '652727e3-ac02-4d0f-b191-55e84bd41e9e',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'electrical'::neta_test_type,
    '6',
    'Verify operation of alarms.',
    false,
    14
  ),
(
    '2870d0eb-22a6-4e0b-95e9-c69f38b24d24',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'electrical'::neta_test_type,
    '7',
    'Measure and record input and output voltage and current.',
    false,
    15
  ),
(
    'fa3bd7ea-983d-4078-9c24-6f4a0978e9d0',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'electrical'::neta_test_type,
    '8',
    'Measure and record ac ripple current and voltage imposed on the battery.',
    false,
    16
  ),
(
    'a6e115c6-74eb-4b02-bc71-4e9dd9aab7a8',
    'b43f7df3-ceec-462d-8d0d-48ed437c672f',
    'electrical'::neta_test_type,
    '9',
    'Perform full load testing and verify current limit of charger.',
    true,
    17
  ),
(
    '81e00d0e-4999-433f-b014-d18e3c8eebc4',
    '9c92e372-a313-4c3e-8e19-da2af5de3214',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '03e358a9-7789-4515-b7a2-df527ee36a58',
    '9c92e372-a313-4c3e-8e19-da2af5de3214',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    'cc527767-889b-40ce-afb8-e4a1500df656',
    '9c92e372-a313-4c3e-8e19-da2af5de3214',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and clearances.',
    false,
    3
  ),
(
    '5cc16248-c369-4f55-a6c8-b4b34575707c',
    '9c92e372-a313-4c3e-8e19-da2af5de3214',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the device is clean.',
    false,
    4
  ),
(
    '490db24f-7af7-4b10-a816-0e4833ade6a1',
    '9c92e372-a313-4c3e-8e19-da2af5de3214',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    5
  ),
(
    '25e2ad28-faec-43fc-905e-3cf5599d19fd',
    '9c92e372-a313-4c3e-8e19-da2af5de3214',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that the ground lead is attached to ground with the shortest wire length possible.',
    false,
    6
  ),
(
    '0fd9cdce-6dc9-4975-b8a0-a049a1df2fff',
    '9c92e372-a313-4c3e-8e19-da2af5de3214',
    'electrical'::neta_test_type,
    '1',
    'Verify self-test operation, alarms, counter-indication, and status indicators.',
    false,
    7
  ),
(
    '6fb43609-a845-460a-b4a9-87122aa9842b',
    '9c92e372-a313-4c3e-8e19-da2af5de3214',
    'electrical'::neta_test_type,
    '2',
    'Test grounding connection in accordance with Section 7.13.',
    false,
    8
  ),
(
    '08bb1649-d2e1-4966-9532-3d99eeb93105',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    'e1f280c5-b699-4a58-822f-e07333e1d631',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '6225b0c2-7295-4ab7-94e0-71ccd80304d7',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and clearances.',
    false,
    3
  ),
(
    'e37671f3-e356-4ca7-9c2b-4a0d367dcab6',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the arresters are clean.',
    false,
    4
  ),
(
    'f2b399fb-f51b-4518-8f9c-d3e7892d16ae',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.19.2.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    5
  ),
(
    '1c916719-f6b4-408c-928c-8181b374d1f4',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that the ground lead on each device is individually attached to ground with the shortest wire length possible.',
    false,
    6
  ),
(
    '9d302bcb-cad3-4d67-8967-91f43e3f3fc3',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that the stroke counter is correctly mounted and electrically connected.',
    false,
    7
  ),
(
    '77a676f2-5846-488b-b83e-6a278a4b577b',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'visual_mechanical'::neta_test_type,
    '8',
    'Record the stroke counter reading.',
    false,
    8
  ),
(
    'ad576f16-bf89-47c2-a85c-654a042cbedd',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    9
  ),
(
    'fdc2ca8b-6b29-4804-bb00-d2257d0bc2d0',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'electrical'::neta_test_type,
    '2',
    'Perform an insulation-resistance test on each arrester, phase terminal-to-ground. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.1.',
    false,
    10
  ),
(
    '2754a3f8-b5c6-4b5a-a12c-1e040a40925e',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'electrical'::neta_test_type,
    '3',
    'Test grounding connection in accordance with Section 7.13.',
    false,
    11
  ),
(
    '07fe538b-1c5e-43e7-b446-a69fc2102177',
    '39c0d5d8-0ce6-4e73-bae7-6dcea9fb34cb',
    'electrical'::neta_test_type,
    '4',
    'Perform a watts-loss test for substation class surge arresters.',
    false,
    12
  ),
(
    'fb5ec8d8-55f7-4f10-b36e-dfe2f7e811e7',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '2ed619a9-de47-45ad-9331-7a1c70b863a2',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '06e91e62-e8e7-40eb-bafd-c2938b249c77',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and clearances.',
    false,
    3
  ),
(
    'c5b4df6b-5a5c-4dbb-bb73-d7edf0ee7787',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    '384007c2-7503-417f-9f03-5b2a09af93ab',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify that capacitors are electrically connected in their specified configuration.',
    false,
    5
  ),
(
    'af400046-fec0-41da-9e8a-762ef45b6156',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify tightness of accessible-bolted electrical connections by calibrated torque-wrench method or in accordance with 7.20.1.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    6
  ),
(
    '9a1cd4ce-be6b-48c6-9090-c6b41c95fa66',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'visual_mechanical'::neta_test_type,
    '7',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    7
  ),
(
    '3730b1aa-89cd-4caf-96f7-05b38f3a45bc',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    8
  ),
(
    'f2bb96f6-1758-4578-8128-63d6be3b57d5',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests from phase terminal(s) to case for one minute. Test voltage shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.1.',
    false,
    9
  ),
(
    '20128280-48ac-415a-9be9-0d4e66efff23',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'electrical'::neta_test_type,
    '3',
    'Measure the capacitance of all terminal combinations.',
    false,
    10
  ),
(
    '854c4da6-7472-48ab-bf57-85cfcdf119e1',
    'c6eb4c59-cf12-48bf-909b-4e6abf014633',
    'electrical'::neta_test_type,
    '4',
    'Measure resistance of the internal discharge resistors.',
    false,
    11
  ),
(
    '57810d05-7056-43c8-ab19-3eeef3b1f775',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '79b751a6-cf99-418f-9b6d-a813b47040c7',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '67f2f15e-7916-40fb-bf91-a3d150545030',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    '09d54df6-916c-4e22-ba9c-09afb2201694',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    '3261b56a-6497-464e-a720-e91b1374f891',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'visual_mechanical'::neta_test_type,
    '5',
    'Perform insulation power-factor or dissipation-factor tests on all windings in accordance with test equipment manufacturer’s published data.',
    true,
    5
  ),
(
    '5d25e206-1c6d-493b-a372-28a848854c3d',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.20.3.1.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    6
  ),
(
    '5cefea32-d483-413c-9b95-a7f2b99aedc5',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that tap connections are as specified.',
    false,
    7
  ),
(
    '8d76afb3-268d-44d1-85e9-5e582cd8d45d',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'visual_mechanical'::neta_test_type,
    '8',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    8
  ),
(
    '933682a6-7354-44d8-ad46-4a4faa273b05',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with low-resistance ohmmeter.',
    false,
    9
  ),
(
    '38fd907b-c18f-443e-8b4a-9518f9d5d966',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'electrical'::neta_test_type,
    '2',
    'Perform winding-to-ground insulation-resistance tests. Test voltage shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, refer to Table 100.1.',
    false,
    10
  ),
(
    '29d9a445-4137-4e71-a914-3af88ce470d9',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'electrical'::neta_test_type,
    '3',
    'Measure winding resistance.',
    false,
    11
  ),
(
    'c53182f2-8ec6-4b3e-8d75-476db8015621',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'electrical'::neta_test_type,
    '4',
    'Perform dielectric withstand voltage tests on each winding to ground.',
    true,
    12
  ),
(
    '454d881a-4253-412c-9b97-4a7827b429d1',
    '9879a711-1397-42da-aa35-ced65ee03563',
    'electrical'::neta_test_type,
    '5',
    'Perform insulation resistance power-factor or dissipation-factor tests on all windings in accordance with test equipment manufacturer’s published data.',
    true,
    13
  ),
(
    '72cf05b2-284b-4b6c-ab60-317a1e94f709',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '4693c895-359d-409c-9221-7101c0460484',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '79e641b5-0723-4536-8f7e-b7cd7eba6354',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify proper anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    'fbfe9d2d-b397-44ba-bc70-1c82d13f70bf',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    '6d809b41-0ff8-428e-8d0b-c9609d621a07',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.20.4.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    5
  ),
(
    'd95378ee-4b22-4be3-964d-6177ffe61e85',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct liquid level in all tanks and bushings.',
    false,
    6
  ),
(
    '2c106efc-1c1b-464e-a42a-a2155b16b8a7',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '7',
    'Perform mechanical inspections and tests as recommended by the manufacturer.',
    false,
    7
  ),
(
    'fb9046a7-06b1-49a2-acf5-0e1e5e3c238e',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify that filters are in place and vents are clear.',
    false,
    8
  ),
(
    '83ce2e20-c877-41f2-8711-2c4c7ef7954e',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '9',
    'Perform visual and mechanical inspection of instrument transformers in accordance with Section 7.10.',
    false,
    9
  ),
(
    '5eab3f3b-b4a0-463a-9ff5-265dc1cb2031',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify monitoring and auxiliary systems.',
    false,
    10
  ),
(
    '611ccff3-461d-4a73-bbd8-043cf39336c4',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform a thermographic survey in accordance with Section 9.',
    true,
    11
  ),
(
    '6ffd1bcb-1af8-4b20-bd3a-a044f0b6141e',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with low-resistance ohmmeter.',
    false,
    12
  ),
(
    '17c11127-e969-4dc1-9424-d71776f002a1',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'electrical'::neta_test_type,
    '2',
    'Perform resistor-to-ground insulation-resistance tests. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1.',
    false,
    13
  ),
(
    '7254b250-7831-425c-89f4-e3a482523ea7',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'electrical'::neta_test_type,
    '3',
    'Measure resistance value.',
    false,
    14
  ),
(
    '4c4ee585-afa5-4925-8c8f-7cf4d84efcf0',
    'a96dac6a-435d-4aba-895a-55bf3534b4b8',
    'electrical'::neta_test_type,
    '4',
    'Perform electrical tests on instrument transformers in accordance with Section 7.10.',
    false,
    15
  ),
(
    '58a15899-2da6-4d24-b2a1-a9e23452707f',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    'a9c9198d-f487-4300-8bc2-30885259d511',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '41c3bf9d-7fd7-4fa4-a8ea-ab4452f34468',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    '9cc00085-9247-4cc9-b5cb-ec47942f09fd',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    'a2bf80c4-1e56-4b41-aeac-69e10cca4bc4',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Perform insulation-resistance tests in accordance with IEEE 43.',
    false,
    5
  ),
(
    '67706d9d-c361-450e-b504-295e6141acba',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Machines larger than 200 horsepower (150 kilowatts): Test duration shall be ten minutes. Calculate polarization index.',
    false,
    6
  ),
(
    '1f1dbc44-b64c-4af3-b4bb-ae6f846a8620',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Machines 200 horsepower (150 kilowatts) and less: Test duration shall be one minute. Calculate the dielectric-absorption ratio.',
    false,
    7
  ),
(
    '0f453b94-9f48-44c7-99be-d9806f1f3f93',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Test protective relay devices in accordance with Section 7.9.',
    false,
    8
  ),
(
    '550ba7d4-9eec-4b81-970e-269a4f5342fa',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify phase rotation, phasing, and synchronized operation as required by the application.',
    false,
    9
  ),
(
    'd8c922be-06aa-4609-9ede-c33ec7482fd0',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '4',
    'Functionally test engine shutdown for low oil pressure, overtemperature, overspeed, and other protection features as applicable.',
    false,
    10
  ),
(
    '676cbba4-7573-4504-9769-2cc97ad57ef7',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '5',
    'Perform vibration test for each main bearing cap.',
    true,
    11
  ),
(
    '06ad9586-5911-4223-9fa2-8e2d941dd2d4',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '6',
    'Conduct performance test in accordance with NFPA 110.',
    false,
    12
  ),
(
    '3f4ac1b8-3797-4cf1-8bea-2aeaae9f94fa',
    '9e610ef7-c45d-4c26-9e3f-68b76d89780e',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify correct functioning of the governor and regulator.',
    false,
    13
  ),
(
    'f598ce7a-b3f8-4113-882d-9d6414069817',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '5e4acb15-f1cb-4c31-99fc-5c4673566b55',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '23fa975c-354f-4676-8e9e-f0fcb6e7a69f',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and required clearances.',
    false,
    3
  ),
(
    '2d7bfe5a-6721-4e0d-845c-8bc47a1a1e9f',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify that fuse sizes and types correspond to drawings.',
    false,
    4
  ),
(
    '6366dce9-7951-4f97-b1d6-73daf383f5f0',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify the unit is clean.',
    false,
    5
  ),
(
    '3ab1845a-1d0e-4f20-ab9d-c560afcc9a56',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '6',
    'Test electrical and mechanical interlock systems for correct operation and sequencing.',
    false,
    6
  ),
(
    '1811b266-7aa5-4f3f-8d21-77799bb22fed',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.22.2.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    7
  ),
(
    '40bcde50-9727-439d-b44e-e2edebf75748',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify operation of forced ventilation.',
    false,
    8
  ),
(
    '289a6c8b-7a2f-402a-8546-045178e4daad',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify that filters are in place and/or vents are clear.',
    false,
    9
  ),
(
    '0c3da3b6-a704-4859-b682-4f85d498d407',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'visual_mechanical'::neta_test_type,
    '10',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    10
  ),
(
    'c47dc920-ce23-42ba-ad5e-dfd430415358',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    11
  ),
(
    'de55a56c-b629-4690-8fed-8ec6fd311118',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'electrical'::neta_test_type,
    '2',
    'Test static transfer from inverter to bypass and back. Use normal load, if possible.',
    false,
    12
  ),
(
    'b5d1381f-2ca7-4d39-a7ab-91c46e560f2c',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'electrical'::neta_test_type,
    '3',
    'Set free running frequency of oscillator.',
    false,
    13
  ),
(
    '37162319-dd3d-4462-a57e-2f84c743996d',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'electrical'::neta_test_type,
    '4',
    'Test dc undervoltage trip level on inverter input breaker. Set according to manufacturer’s published data.',
    false,
    14
  ),
(
    '27ca8f15-fc0f-405f-85bd-ceacfd97b1d7',
    'cae77ae2-792e-4cbc-a571-794e5bf140ec',
    'electrical'::neta_test_type,
    '5',
    'Test alarm circuits. Page 200',
    false,
    15
  ),
(
    'f4f8a3ca-640b-4cd5-a33e-cc587d4b5ce0',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    'fafb9810-10ce-4307-816c-65488b6c19ac',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    'f4ca151b-b155-4627-82e6-6c4964603f33',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, grounding, and required clearances.',
    false,
    3
  ),
(
    'e4a4b8c8-948b-4782-9ec9-0450641188ef',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    '003aeb91-019e-4dd3-94a1-78710d63f2e5',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    5
  ),
(
    'a9b32d40-b81d-46cf-ab72-191c610ff88d',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that warning labels are attached and visible.',
    false,
    6
  ),
(
    '1ba86c83-eece-4207-8f73-11f16fb35519',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify tightness of all control connections.',
    false,
    7
  ),
(
    '229d5dc2-9a81-4204-99eb-3a1048641720',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.22.3.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    8
  ),
(
    '148f986a-9c02-4cd5-aff7-2d5b4c4cfb22',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '9',
    'Perform manual transfer operation.',
    false,
    9
  ),
(
    'b5e91ce2-aaa5-434e-bab1-4e06c378a095',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify positive mechanical interlocking between normal and alternate sources.',
    false,
    10
  ),
(
    'a53ce190-3f5d-4bc4-b5f0-eac5684df1c2',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    11
  ),
(
    '55e69ca2-081f-4265-b62e-a39202706355',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    12
  ),
(
    '366b7850-fa6e-480f-b383-b4abf3826c89',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation resistance tests for one minute on each pole, phase-to-phase and phase-to-ground with switch in both source positions and across each open pole. Test voltage shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1.',
    false,
    13
  ),
(
    'b90a2dc3-87b1-44b0-99df-09e1b2f29855',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'electrical'::neta_test_type,
    '3',
    'Perform insulation-resistance tests on all control wiring with respect to ground. The applied potential shall be 500 volts dc for 300-volt rated cable and 1000 volts dc for 600- volt rated cable. Test duration shall be one minute. For units with solid-state components or for control devices that cannot tolerate the applied voltage, follow manufacturer’s recommendation.',
    true,
    14
  ),
(
    '705093e6-5b3b-404a-b409-54e9afcde96b',
    '024bac36-4a2f-4e87-9ff6-32060f6d4661',
    'electrical'::neta_test_type,
    '4',
    'Perform a contact/pole-resistance test. Page 202',
    false,
    15
  ),
(
    '78651076-8efd-46fc-8be0-4ac3fb281038',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    '7ab9fc13-cfb2-4f26-bb3f-3bfe6da282b6',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '686a3fc6-b58a-4d51-83f8-5802ce8aa702',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    '2c9a8610-5c17-4ac2-8f10-fc16f1d09b15',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    '97e64f38-fda6-45af-897b-6df61860c066',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'visual_mechanical'::neta_test_type,
    '5',
    'Perform all mechanical operation and contact alignment tests on both the recloser and its operating mechanism in accordance with manufacturer’s published data.',
    false,
    5
  ),
(
    'c948d697-10a5-49cc-a93e-3b9c3475edbb',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.24.1.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.12.',
    false,
    6
  ),
(
    'f21fb80e-f0e3-4b60-b6e9-a5947f222f93',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify appropriate insulating liquid level.',
    false,
    7
  ),
(
    '799297d7-e5a1-44bf-85b4-56af93d8ae3f',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'visual_mechanical'::neta_test_type,
    '8',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    8
  ),
(
    '4f946481-df7c-47fa-969e-23b41ad278ca',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    9
  ),
(
    '453c99fc-0b60-469c-89e8-fbfbbeb9f221',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests for one minute on each pole, phase-to-phase and phase-to-ground with recloser closed, and across each open pole. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1.',
    false,
    10
  ),
(
    'ffff31c5-bb18-4f11-af89-be65a8fdf3a4',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'electrical'::neta_test_type,
    '3',
    'Perform a contact/pole-resistance test.',
    false,
    11
  ),
(
    '5e64562e-3ee3-41c8-975d-875bf24d5c01',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'electrical'::neta_test_type,
    '4',
    'Perform insulation-resistance tests on all control wiring with respect to ground. Applied potential shall be 500 volts dc for 300-volt rated cable and 1000 volts dc for 600-volt rated cable. Test duration shall be one minute. For units with solid-state components, follow manufacturer’s recommendation.',
    true,
    12
  ),
(
    'ffc700fa-e642-4833-a51e-79a80ff1fe7b',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'electrical'::neta_test_type,
    '5',
    'Remove a sample of insulating liquid in accordance with ASTM D 923. Sample shall be tested in accordance with the referenced standard.',
    false,
    13
  ),
(
    'ad25f487-fc85-4ee5-94f5-d95fe80f2390',
    'b9be9162-e34b-4abb-8a02-c189d48affca',
    'electrical'::neta_test_type,
    '1',
    'Dielectric breakdown voltage: ASTM D 877 Page 207',
    false,
    14
  ),
(
    '9fe8cf9c-d2f7-4198-92ad-283cfddb5b9c',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'visual_mechanical'::neta_test_type,
    '1',
    'Compare equipment nameplate data with drawings.',
    false,
    1
  ),
(
    'b265b9b4-932a-4af4-953b-e001b96ed938',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect physical and mechanical condition.',
    false,
    2
  ),
(
    '2e0bf727-1239-4913-b7c7-3de1bb2efceb',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect anchorage, alignment, and grounding.',
    false,
    3
  ),
(
    '06e3a8a5-a2c9-4e10-9767-965741ced3e0',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify the unit is clean.',
    false,
    4
  ),
(
    'cb496d3a-31c8-4523-9363-e8e6de49ec84',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'visual_mechanical'::neta_test_type,
    '5',
    'Perform all mechanical operation and contact alignment tests on both the sectionalizer and its operating mechanism in accordance with manufacturer’s published data.',
    false,
    5
  ),
(
    'b5bde157-61d2-409b-8c4c-f07465338f6d',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify tightness of accessible bolted electrical connections by calibrated torque-wrench method or in accordance with 7.24.2.B.1. Torque values shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    6
  ),
(
    'a4f29b28-f211-40d0-8319-5e885a401a89',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify appropriate insulating liquid level.',
    false,
    7
  ),
(
    '5b1ee3cc-d6f9-442c-8903-4e9a741ad38c',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'visual_mechanical'::neta_test_type,
    '8',
    'Perform thermographic survey in accordance with Section 9.',
    true,
    8
  ),
(
    'f9862ed2-759c-48ee-a1c6-58e3788200b1',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter.',
    false,
    9
  ),
(
    'f3377605-de4a-4f9a-a5ee-51a5883e479e',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests for one minute on each pole, phase-to-phase and phase-to-ground with sectionalizer closed, and across each open pole. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1.',
    false,
    10
  ),
(
    '7be2c2d2-fc81-42ed-aa6d-7a4180071c11',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'electrical'::neta_test_type,
    '3',
    'Perform a contact/pole-resistance test.',
    false,
    11
  ),
(
    'bab1fb41-9369-48b2-9ecf-5e1b0c1bc6f8',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'electrical'::neta_test_type,
    '4',
    'Remove a sample of insulating liquid in accordance with ASTM D923. The sample shall be tested in accordance with the referenced standard.',
    false,
    12
  ),
(
    'c26eb7a4-2239-49ed-9a13-8a1c92b1b0cf',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'electrical'::neta_test_type,
    '1',
    'Dielectric breakdown voltage: ASTM D877',
    false,
    13
  ),
(
    '4c44f36c-f498-48ac-bc92-f30d6f81b1c9',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'electrical'::neta_test_type,
    '2',
    'Color: ASTM D 1500',
    false,
    14
  ),
(
    'be9259bb-6f5a-49b4-90bd-e10cbf76bb86',
    'ddf592f0-7a10-472b-9b40-6109328d33ce',
    'electrical'::neta_test_type,
    '3',
    'Visual condition: ASTM D 1524 Page 211',
    false,
    15
  ),
(
    'b073e118-7a10-4afe-a426-1a0be5d13b31',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical, electrical, and mechanical condition.',
    false,
    1
  ),
(
    'd74d4dce-6f1a-498e-8c69-1f3d7372a869',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, grounding, and required area clearances. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    '72f45424-3be4-4257-9e95-e766f5ed0119',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    '72497dc4-9d5c-4156-beee-8f0f43a00c39',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify that fuse and/or circuit breaker sizes and types correspond to drawings and coordination study as well as to the circuit breaker address for microprocessor- communication packages.',
    false,
    4
  ),
(
    '48e54d4e-8969-4754-9675-9c6d3af93781',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that current and voltage transformer ratios correspond to drawings.',
    false,
    5
  ),
(
    'a209e5ba-32bc-4bb0-a9c1-0002db8f3488',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that wiring connections are tight and that wiring is secure to prevent damage during routine operation of moving parts.',
    false,
    6
  ),
(
    '5ee846c7-1807-4312-976d-3ca20ca056a7',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '8',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    7
  ),
(
    '99d4881a-a0fb-49e7-8a05-d54e2f22fa38',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.1.B.1.',
    false,
    8
  ),
(
    'd4730adb-3d36-4c67-a2aa-c9200c62b67a',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    9
  ),
(
    '6699d85f-2cdf-4485-984f-970d90227046',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    10
  ),
(
    'ccd9e173-15de-49ad-932c-685bccf2faca',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '9',
    'Confirm correct operation and sequencing of electrical and mechanical interlock systems.',
    false,
    11
  ),
(
    '042a708b-431c-43e1-9cbb-4984a6c61e7e',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '1',
    'Attempt closure on locked-open devices. Attempt to open locked-closed devices.',
    false,
    12
  ),
(
    'bbf30390-f0c2-4499-9075-d94e50fc7e31',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '2',
    'Make key exchange with all devices included in the interlock scheme as applicable.',
    false,
    13
  ),
(
    '76ab3984-5e09-44b4-a873-ac0576c1f02f',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '10',
    'Use appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    14
  ),
(
    '5d290d4e-f261-4187-a7cf-eaa5d8b017cb',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '11',
    'Inspect insulators for evidence of physical damage or contaminated surfaces.',
    false,
    15
  ),
(
    'b680eccd-ffd8-4630-9baa-f4b995bb1935',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '12',
    'Verify correct barrier and shutter installation and operation.',
    false,
    16
  ),
(
    'ed342022-27cf-4930-868f-826edabdc6dc',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '13',
    'Exercise all active components.',
    false,
    17
  ),
(
    'deed4c60-8beb-4efe-901f-ffce05ed2da3',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '14',
    'Inspect mechanical indicating devices for correct operation. * Optional Page 24',
    false,
    18
  ),
(
    'bf9cc2e1-783b-4ef0-b984-83a4f716a208',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '15',
    'Verify that filters are in place, filters are clean and free from debris, and vents are clear',
    false,
    19
  ),
(
    'e8a740a9-e558-4f7d-b955-fae476563bf5',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '16',
    'Perform visual and mechanical inspection of instrument transformers in accordance with Section 7.10.',
    false,
    20
  ),
(
    '2bc3fc09-8688-4e1b-aafd-9ee5007482da',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '17',
    'Perform visual and mechanical inspection of surge arresters in accordance with Section 7.19.',
    false,
    21
  ),
(
    '1b99c8ac-1486-4223-b68d-a41f7af7d5a2',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '18',
    'Inspect control power transformers.',
    false,
    22
  ),
(
    'be5acba2-8512-429e-b0da-ecb1bb48c081',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect for physical damage, cracked insulation, broken leads, tightness of connections, defective wiring, and overall general condition.',
    false,
    23
  ),
(
    'c33a0d3f-36f1-44d2-aa3f-e6069c6beeda',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify that primary and secondary fuse or circuit breaker ratings match drawings.',
    false,
    24
  ),
(
    '9d581a92-fe57-458a-a0f4-2b09a461f491',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify correct functioning of drawout disconnecting contacts, grounding contacts, and interlocks.',
    false,
    25
  ),
(
    '93bb20fe-e439-494b-a6cf-aa73f59c3b54',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'visual_mechanical'::neta_test_type,
    '19',
    'Perform as-left tests.',
    false,
    26
  ),
(
    '41b96a0a-117b-4773-81e6-9d2ed3ca935b',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted electrical connections with a low- resistance ohmmeter in accordance with Section 7.1.A.8.1.',
    false,
    27
  ),
(
    '176d6d45-5a1d-4b33-a484-3b5912240444',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests for one minute on each bus section, phase-to-phase and phase-to-ground. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1. *3. Perform a dielectric withstand voltage test on each bus section, each phase-to-ground with phases not under test grounded, in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.2. The test voltage shall be applied for one minute. Refer to Section 7.1.3 before performing test. *4. Perform insulation-resistance tests on control wiring with respect to ground. The applied potential shall be 500 volts dc for 300-volt rated cable and 1000 volts dc for 600-volt rated cable. Test duration shall be one minute. For units with solid-state components or control devices that cannot tolerate the applied voltage, follow manufacturer’s recommendation.',
    false,
    28
  ),
(
    '27a6e15d-1f9b-4917-91d1-8102d4198745',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '5',
    'Perform electrical tests on instrument transformers in accordance with Section 7.10.',
    false,
    29
  ),
(
    'b9a9326f-7da4-44ee-ba31-7a9c6d7d5c1c',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '6',
    'Perform ground-resistance tests in accordance with Section 7.13.',
    false,
    30
  ),
(
    '3a746163-274d-4b49-ab14-068780fa7140',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '7',
    'Test metering devices in accordance with Section 7.11.',
    false,
    31
  ),
(
    '38ab0ad1-1ab7-4f39-a65f-392ed02f5166',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '8',
    'Control Power Transformers. * Optional Page 25',
    false,
    32
  ),
(
    'fc764118-0397-4899-b7ef-c5e783285a23',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '1',
    'Perform insulation-resistance tests. Perform measurements from winding-to-winding and each winding-to-ground. Test voltages shall be in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1.',
    false,
    33
  ),
(
    'a1b6c1f9-bddd-42e6-ada3-bddfa5e83a3e',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '2',
    'Verify correct function of control transfer relays located in switchgear with multiple power sources.',
    false,
    34
  ),
(
    '06087b69-2ce7-435c-b38b-5807df390a2e',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '9',
    'Verify operation of switchgear/switchboard heaters and their controller.',
    false,
    35
  ),
(
    'e4dd359a-3a66-4ccf-bb0d-c63632e66b85',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '10',
    'Perform electrical tests of surge arresters in accordance with Section 7.19. *11. Perform online partial-discharge survey in accordance with Section 11.',
    false,
    36
  ),
(
    'da3114cf-a9b4-40ea-9002-7143ba92f9a2',
    '8046f431-68c9-43c5-8a85-9034df9d68b0',
    'electrical'::neta_test_type,
    '12',
    'Perform system function tests in accordance with Section 8.',
    false,
    37
  ),
(
    '98b22d30-70b9-4355-9aff-c11e2e9b3fcd',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    '0ad47aa7-4a6e-45c9-b0a4-331be124536d',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding.',
    false,
    2
  ),
(
    'c97afdc1-6196-4b3e-b096-82144183ba69',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify the presence of PCB labeling. *4. Prior to cleaning the unit, perform as-found tests.',
    false,
    3
  ),
(
    'd2afe044-0874-42c7-a9c4-ded3fe0d7566',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '5',
    'Clean bushings and control cabinets.',
    false,
    4
  ),
(
    '89378bba-103d-4bc2-9fe0-9ecbf71bb34d',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify operation of alarm, control, and trip circuits from temperature and level indicators, pressure-relief device, gas accumulator, and fault-pressure relay.',
    false,
    5
  ),
(
    '33bab883-2ead-48b5-8e75-9e6380161d8b',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that cooling fans and pumps operate correctly.',
    false,
    6
  ),
(
    '98e6551a-2b89-4054-b731-19fed0b7db92',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '8',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    7
  ),
(
    'c0849ed3-bdc9-4ed9-ba70-15896544dac7',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.2.2.B.1.',
    false,
    8
  ),
(
    'f52f61c3-0a22-40d1-8bfa-4ac5cc271e72',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    9
  ),
(
    'd21849dc-7502-4c71-84dd-74636e7e6f35',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    10
  ),
(
    'e27c8f99-df9f-420e-aadc-e4e6976b450a',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify correct liquid level in tanks and bushings.',
    false,
    11
  ),
(
    'e192fd97-a3ea-4d3f-b80b-db4008f04e8f',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify that positive pressure is maintained on gas-blanketed transformers.',
    false,
    12
  ),
(
    '9f46f011-f329-4436-8a4a-d455bbaef5d0',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform inspections and mechanical tests as recommended by the manufacturer.',
    false,
    13
  ),
(
    '00686614-7aaa-4c28-a001-1366ce2db944',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '12',
    'Test load tap-changer in accordance with Section 7.12.',
    false,
    14
  ),
(
    '16bcbbc3-7285-451c-b311-58b3de973fb8',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '13',
    'Verify the presence of transformer surge arresters.',
    false,
    15
  ),
(
    '040d6f52-5946-495a-bfa9-c4ad88df0bd7',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '14',
    'Perform as-left tests.',
    false,
    16
  ),
(
    '3d7802cf-ce16-4ea8-ad04-ec1209ca577b',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'visual_mechanical'::neta_test_type,
    '15',
    'Verify de-energized tap-changer position is left as specified.',
    false,
    17
  ),
(
    '8aeef055-7a5b-4b22-9033-4d41d1cf28dc',
    '77b6a41e-7f48-48de-9056-abff924f8576',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.2.2.A.8.1. * Optional Page 34',
    false,
    18
  ),
(
    'aeeb6afe-ffe1-4a9f-8827-5610d4383b16',
    '6823d363-01e6-48f6-9586-720c450dbed0',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect exposed sections of cables and connectors for physical damage and evidence of degradation.',
    false,
    1
  ),
(
    '09e5a97a-3f23-4e5f-93e8-317c8921c3f3',
    '6823d363-01e6-48f6-9586-720c450dbed0',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    2
  ),
(
    'a2d438b0-670f-42e8-8482-b95d97da9abc',
    '6823d363-01e6-48f6-9586-720c450dbed0',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.3.2.B.1.',
    false,
    3
  ),
(
    'dd4250fa-6335-4101-af29-86670610849e',
    '6823d363-01e6-48f6-9586-720c450dbed0',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    4
  ),
(
    '602e237f-abbf-4a3e-b33c-036d0e8cb312',
    '6823d363-01e6-48f6-9586-720c450dbed0',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    5
  ),
(
    '9b87eaee-a12c-4c09-a4c3-ce1247ebb4f7',
    '6823d363-01e6-48f6-9586-720c450dbed0',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect cable tray and cable supports.',
    false,
    6
  ),
(
    'f1e2bfcb-e433-4a6f-b788-5d41227e6def',
    '6823d363-01e6-48f6-9586-720c450dbed0',
    'visual_mechanical'::neta_test_type,
    '4',
    'If cables are terminated through window-type current transformers, inspect to verify that neutral and ground conductors are correctly placed for operation of protective devices. *5. Compare cable data with drawings and cable schedule.',
    false,
    7
  ),
(
    'd5d1f07e-9b5f-4b12-91c6-2c4bfe6cea69',
    '6823d363-01e6-48f6-9586-720c450dbed0',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.3.2.A.2.1.',
    false,
    8
  ),
(
    'f7c49c72-10dd-47e6-98a3-67a0e1d055e0',
    '6823d363-01e6-48f6-9586-720c450dbed0',
    'electrical'::neta_test_type,
    '2',
    'Perform an insulation-resistance test on each phase/conductor with all other phases/conductors grounded. The applied potential shall be 500 volts dc for 300-volt rated cable and 1000 volts dc for greater than 300-volt rated cable. The test duration shall be one minute. *3. Verify uniform resistance of parallel conductors.',
    false,
    9
  ),
(
    '03ecf048-6c92-4fa3-89ce-c7a03c17568b',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect exposed sections of cables and connectors for physical damage and evidence of degradation and corona.',
    false,
    1
  ),
(
    '6fb9aa24-4752-4c45-ba40-4a4798e004de',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect terminations and splices for physical damage, evidence of overheating, and corona.',
    false,
    2
  ),
(
    '3e635cf0-6934-4b4d-b6ad-83c04018698a',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    3
  ),
(
    '8a8a06bc-1e86-410c-82f6-edca05cc15be',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.3.3.B.1.',
    false,
    4
  ),
(
    '561d9829-638d-4d6f-9a22-4c83753cb2e2',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    5
  ),
(
    '64f686d4-613c-481b-aac3-0e78a663c34a',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    6
  ),
(
    '6af60d0c-417c-42bf-8057-d4d99e90cf90',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect shield grounding and cable support.',
    false,
    7
  ),
(
    '8137cbc4-738c-4ac2-b14e-03bfb19f0884',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify that visible cable bends are not less than ICEA and/or manufacturer’s minimum allowable bending radius. *6. Inspect fireproofing in common cable areas.',
    false,
    8
  ),
(
    '496d0ae6-d6e1-4857-a5bd-191432240aa9',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'visual_mechanical'::neta_test_type,
    '7',
    'If cables are terminated through window-type current transformers, inspect to verify that neutral and ground conductors are correctly placed and that shields are correctly terminated for operation of protective devices. *8. Compare cable data with drawings and cable schedule.',
    false,
    9
  ),
(
    '331b943a-6f4e-4058-a6b0-60042c6a53ba',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.3.3.A.3.1.',
    false,
    10
  ),
(
    '40aff003-719b-4e1c-a977-3f51263cc424',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'electrical'::neta_test_type,
    '2',
    'Perform an insulation-resistance test individually between each phase/conductor and its shield with all other phase/conductors and shields grounded. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1.',
    false,
    11
  ),
(
    '5cef0ff0-5ee9-435e-8572-f72ccc4d6454',
    'f4e45527-6c88-41c5-b224-9cc4c59f89da',
    'electrical'::neta_test_type,
    '3',
    'Perform a shield-continuity test on each power cable by ohmmeter method. * Optional Page 42',
    false,
    12
  ),
(
    'fef554f7-2e20-4e26-8ccc-b2e12bbd2aa1',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'f7c95c48-4523-45bb-a2fa-6ebb9bbc63c0',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, grounding, and required clearances. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    '5e34b69a-80b0-484d-b017-0697c85d72a6',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    '83c48fcb-ed71-4757-924a-6ce322a6491d',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '5',
    'Perform mechanical operator tests in accordance with manufacturer’s published data.',
    false,
    4
  ),
(
    'dec0c698-bffd-48ae-83e5-30a3cb47f2bf',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct operation and adjustment of motor operator limit switches and mechanical interlocks. *7. Verify correct blade alignment, blade penetration, travel stops, arc interrupter operation, and mechanical operation.',
    false,
    5
  ),
(
    '786ff5cb-30d3-4c26-9e08-f8f64afc33c0',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify that each fuseholder has adequate mechanical support and contact integrity.',
    false,
    6
  ),
(
    'f65b961a-140c-4f93-b67f-c2ddac09580b',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify that fuse sizes and types are in accordance with drawings, short circuit studies, and coordination study.',
    false,
    7
  ),
(
    '37251b4f-cb42-429f-9937-5c4b083110a7',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '10',
    'Test all electrical and mechanical interlock systems for correct operation and sequencing.',
    false,
    8
  ),
(
    '8346edda-4aa7-4dbd-a4f8-99efbdec35f1',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '11',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    9
  ),
(
    '6724b824-64f0-4dc5-a427-da8a9abf8cc1',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.5.2.B.1.',
    false,
    10
  ),
(
    '1c257c9e-9085-4185-a7f4-9ec25f4f5c77',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    11
  ),
(
    '9858a2d0-3649-4b3a-b277-ddb2e1d09234',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    12
  ),
(
    '6986d0b9-55da-4ea6-aa8e-930df7cdbb6a',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '12',
    'Verify that insulating oil level is correct.',
    false,
    13
  ),
(
    '610a745c-3010-4ea9-b714-911ccd5b210f',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '13',
    'Inspect and/or replace gaskets as recommended by the manufacturer.',
    false,
    14
  ),
(
    '1b8b7d91-492f-46cb-83a7-aee8fee5c7e4',
    '7606b8f9-c1a7-4664-8395-1cf28d76cfa1',
    'visual_mechanical'::neta_test_type,
    '14',
    'Use appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces. * Optional Page 58',
    false,
    15
  ),
(
    '4034614f-f878-44e9-8537-71d12e383f22',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    '1965d7c3-1e96-4a3a-9199-51e9850b2d5e',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, grounding, and required clearances. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    '527d91ef-a19c-4cfd-af09-d7b2a01e0dc6',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    '51dacc38-6f82-478b-ae94-5ea711da4ced',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '5',
    'Perform mechanical operator tests in accordance with manufacturer’s published data.',
    false,
    4
  ),
(
    '5042afe4-f9f3-4431-b052-0067e4873b54',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct operation and adjustment of motor operator limit switches and mechanical interlocks.',
    false,
    5
  ),
(
    '198add47-6a5b-43bb-8d09-7a23715ccba4',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '7',
    'Measure critical distances on operating mechanism as recommended by the manufacturer.',
    false,
    6
  ),
(
    '30e99242-0da6-4e7c-aaf9-91b6ed3bf8c9',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '8',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    7
  ),
(
    '09488593-3bf6-48eb-bc9d-48f40a25551b',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter. See Section 7.5.3.B.1.',
    false,
    8
  ),
(
    '1d121e9e-f757-42ff-ae3c-03d2f68addf6',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    9
  ),
(
    'c33bdabc-aedf-424e-9a04-9bfe9f7b2265',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    10
  ),
(
    '5083f0f5-6739-40a5-905f-43996411177b',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '9',
    'Inspect insulating assemblies for evidence of physical damage or contaminated surfaces.',
    false,
    11
  ),
(
    '3efd491f-f19c-4e19-8410-f2e3567ffb96',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify that each fuseholder has adequate support and contact integrity.',
    false,
    12
  ),
(
    '8b7aea0f-489d-41af-af8b-806afc661c50',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '11',
    'Verify that fuse sizes and types are in accordance with drawings, short-circuit studies, and coordination study.',
    false,
    13
  ),
(
    '21c7644b-da9c-40c4-b31a-7c20694e9ea6',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '12',
    'Test all electrical and mechanical interlock systems for correct operation and sequencing.',
    false,
    14
  ),
(
    '0178c672-6495-4b5b-84bb-6ac48158bf5f',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '13',
    'Use appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    15
  ),
(
    'ed8d1ffb-0ee1-4c01-9cc8-7196b54380f7',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '14',
    'Perform as-left tests.',
    false,
    16
  ),
(
    '8260d863-48cd-498d-83e1-9052d13257ff',
    '7a5d0c8f-758f-4dc5-9925-3f8fd417fec9',
    'visual_mechanical'::neta_test_type,
    '15',
    'Record as-found and as-left operation counter readings. * Optional Page 61',
    false,
    17
  ),
(
    'f169bad6-15e8-4f9b-b306-bc79b701fd26',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'a4f0f1e1-2f7a-4034-a7d6-94fa4d6d90b8',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, grounding, and required clearances. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    'd99eecaa-b30a-4026-93fe-b0d31176dde9',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    'd5d85aab-9897-410a-a720-721209abd187',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect and service mechanical operator and SF gas insulated system in accordance with 6 the manufacturer’s published data.',
    false,
    4
  ),
(
    '0fbb87a1-31d0-41d0-ba91-32658a8036a5',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct operation of SF gas pressure alarms and limit switches as recommended by 6 the manufacturer.',
    false,
    5
  ),
(
    '263e118b-cf00-46a3-8e5f-f89fa8aec31d',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '7',
    'Measure critical distances as recommended by the manufacturer.',
    false,
    6
  ),
(
    '07078803-4842-4b80-be27-915b3f09b6b1',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '8',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    7
  ),
(
    '49d6b4f5-b8ab-4c8f-96f3-001a599ab25c',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.5.4.B.1.',
    false,
    8
  ),
(
    '0c4f7fc9-b491-4379-b17d-2b0b2e40304a',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data. In the absence of manufacturer’s data, use Table 100.12.',
    false,
    9
  ),
(
    '1fccd973-097c-4f94-9520-d878cd9ef1fe',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    10
  ),
(
    '29484ced-94ce-4b71-93e1-9064e78bbd57',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify that fuse sizes and types are in accordance with drawings, short-circuit studies, and coordination study.',
    false,
    11
  ),
(
    '976d5613-e4dd-43d4-ac9f-d8aa9f3c253b',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify that each fuseholder has adequate mechanical support and contact integrity.',
    false,
    12
  ),
(
    '1f81a1dc-7430-4b1e-9ec6-091c33e18ac4',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '11',
    'Verify operation and sequencing of interlocking systems.',
    false,
    13
  ),
(
    'c7784ecb-78f1-4ee8-b62a-d8beffb66cd3',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '12',
    'Use appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    14
  ),
(
    'da23f4b1-0a34-44c7-9875-d44808fb9aca',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '13',
    'Test for SF gas leaks in accordance with manufacturer’s published data. 6',
    false,
    15
  ),
(
    'd5395ea8-7e3b-41c2-956b-c8cad24e5b4f',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '14',
    'Perform as-left tests.',
    false,
    16
  ),
(
    '5c652721-efe4-4cc4-a537-a04cb38da759',
    '09e552d2-935e-4ba5-9d33-c2c2b4e30e39',
    'visual_mechanical'::neta_test_type,
    '15',
    'Record as-found and as-left operation counter readings. * Optional Page 64',
    false,
    17
  ),
(
    'e5c0ce66-4a28-4061-9b94-d58055c1fc72',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'a176ce28-ea6c-45f6-8357-1c89eb37f154',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    '271d5639-4d1f-4e57-b731-7609aa669467',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    'cfe5063e-a5ad-43cd-9bec-d3ecd8e780b5',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    4
  ),
(
    'a6cf3bdb-a0d1-4e75-a7b2-0a4906f7383d',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.5.5.B.1.',
    false,
    5
  ),
(
    '93f774d3-9c96-465c-b4e0-ab76f41e3145',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.12.',
    false,
    6
  ),
(
    'b71480dc-4990-4ac7-a0c4-d278a6cea6f0',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    7
  ),
(
    '278b0a36-e9f5-4967-8c98-2d219b8171e9',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct blade alignment, blade penetration, travel stops, latching mechanism, and mechanical operation.',
    false,
    8
  ),
(
    '38458522-2e64-4ef6-ba60-d201fa0465b3',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that fuse size and types are in accordance with drawings, short-circuit study, and coordination study.',
    false,
    9
  ),
(
    '493e36c4-7b6b-445e-a279-589b03a70340',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify that each fuseholder has adequate mechanical support and contact integrity.',
    false,
    10
  ),
(
    'f7b13a27-86d6-40d8-8238-940e8c132f6b',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'visual_mechanical'::neta_test_type,
    '9',
    'Perform as-left tests.',
    false,
    11
  ),
(
    '08bef48a-da1f-4d85-86e7-9d005cb5a171',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.5.5.A.5.1.',
    false,
    12
  ),
(
    '19c2e65e-c645-4f11-8238-57f0507b78ce',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'electrical'::neta_test_type,
    '2',
    'Measure contact resistance across each cutout.',
    false,
    13
  ),
(
    'e0822736-9dd7-4e81-b59a-52de2cfb480a',
    'cffc80f6-bd2c-4748-b1a7-d856371a2c66',
    'electrical'::neta_test_type,
    '3',
    'Perform insulation-resistance tests for one minute on each pole, phase-to-phase and phase- to-ground with switch closed and across each open pole. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1. * Optional Page 67',
    false,
    14
  ),
(
    '3b6c1219-0c6a-47d8-89bd-65e5dd615efe',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'b3ff86b1-24f9-42d5-8345-389790abec7e',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding.',
    false,
    2
  ),
(
    '5f3fca4a-c2fe-46ef-9874-6d7bff68e82b',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify that maintenance devices are available for servicing and operating the breaker. *4. Perform operator analysis (first-trip) test.',
    false,
    3
  ),
(
    '79512525-406e-4bfd-824f-40d7dcd4c474',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify correct oil level in tanks and bushings.',
    false,
    4
  ),
(
    '4192730f-c68e-4ecd-81bd-7a9a362b1ba1',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that breather vents are clear. *7. Prior to cleaning the unit, perform as-found tests.',
    false,
    5
  ),
(
    'c3d5363b-15ec-4823-87ca-62920aa10cb2',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '8',
    'Clean the unit.',
    false,
    6
  ),
(
    'bac25760-c4f0-4c88-b14e-74a0bc661f39',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '9',
    'Inspect and service hydraulic or pneumatic system and/or air compressor in accordance with manufacturer’s published data.',
    false,
    7
  ),
(
    '4c79d455-6580-45b9-80d8-2e21eca93035',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '10',
    'Test alarms, pressure switches, and limit switches for pneumatic and/or hydraulic operators as recommended by the manufacturer.',
    false,
    8
  ),
(
    'cddf076c-fde0-4e13-ad83-09602814da94',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform all maintenance and tests on the operating mechanism in accordance with manufacturer’s published data. *12. Perform internal inspection:',
    false,
    9
  ),
(
    '19a4f2af-a282-44d8-b5ce-a4244c1dd8d6',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '1',
    'Remove oil. Lower tanks or remove manhole covers as necessary. Inspect bottom of tank for broken parts and debris and clean carbon residue from tank.',
    false,
    10
  ),
(
    '61bbc980-34d3-4d3f-8adb-f7437e6fdebb',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect lift rod and toggle assemblies, contacts, interrupters, bumpers, dashpots, bushing current transformers, tank liners, and gaskets.',
    false,
    11
  ),
(
    '009d4d07-beee-4e74-bd7a-118e8c328c14',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '3',
    'If recommended by manufacturer, slow close/open breaker and check for binding, friction, contact alignment, and penetration. Verify that contact sequence is in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, refer to IEEE C37.04.',
    false,
    12
  ),
(
    'dd9160d4-1e31-43ce-8c15-176e2a693785',
    '7105d1a3-e5f1-429c-9598-5d376fff07fb',
    'visual_mechanical'::neta_test_type,
    '4',
    'Refill tank(s) with new or filtered oil to correct levels. * Optional Page 80',
    false,
    13
  ),
(
    'de3b87c5-6b06-4938-bd0b-a48be7733188',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'c2fcb156-32c4-41c6-b77f-004136b18156',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding.',
    false,
    2
  ),
(
    'e5f4a9a3-1f54-4db2-868d-a9e6a508e3f8',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify that all maintenance devices are available for servicing and operating the breaker. *4. Perform operator analysis (first-trip) test. *5. Prior to cleaning the unit, perform as-found tests.',
    false,
    3
  ),
(
    '3d1ef83a-56ec-4c2f-823a-3dcb025a363c',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '6',
    'Clean the unit.',
    false,
    4
  ),
(
    'cf6bef75-0cab-44ac-8ba8-406c5e68aa90',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '7',
    'Inspect vacuum bottle assemblies.',
    false,
    5
  ),
(
    'ec0beb47-f242-4e2e-a74b-3e35d0d24305',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '8',
    'Measure critical distances such as contact gap as recommended by the manufacturer.',
    false,
    6
  ),
(
    '94587911-7f4e-420f-8ee6-d9431fb0f4c6',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '9',
    'If recommended by the manufacturer, slow close/open the breaker and check for binding, friction, contact alignment, contact sequence, and penetration.',
    false,
    7
  ),
(
    '58c287c7-6fcd-40dc-a6fc-e7f496e46cc4',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '10',
    'Perform all mechanical maintenance and tests on the operating mechanism in accordance with manufacturer’s published data.',
    false,
    8
  ),
(
    'f5b72d6b-8d07-4235-8a1d-d9f9479cb6ba',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '11',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    9
  ),
(
    'f5b8111f-6ca1-4e4d-96c9-dc590cc0d77e',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.6.3.B.1.',
    false,
    10
  ),
(
    '050b20c2-3414-4200-9682-bb6f3525e687',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.12.',
    false,
    11
  ),
(
    'e6e061ad-7fac-47f1-8e67-74558c6f6865',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    12
  ),
(
    '7c8ff362-98c9-48c8-815d-bba426958b54',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '12',
    'Verify cell fit and element alignment.',
    false,
    13
  ),
(
    '0e2e34e7-82f8-4a14-bf58-3b64c169c6c3',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '13',
    'Verify racking mechanism operation.',
    false,
    14
  ),
(
    '2a7f2a4b-31dc-4ca8-af0c-1de1464a9e62',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '14',
    'Inspect vacuum bellows operation.',
    false,
    15
  ),
(
    '96fec5d9-c32d-4c40-8710-6de24e499f1c',
    '8d9b41d5-d39a-491a-a4aa-86fd3cc00547',
    'visual_mechanical'::neta_test_type,
    '15',
    'Use appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces. * Optional Page 85',
    false,
    16
  ),
(
    '7c4c696e-14f2-4f4c-a898-2782b1f488a0',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'fc704b5e-6e1a-48e3-8615-a275fe2b697e',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding.',
    false,
    2
  ),
(
    'dc39b881-a268-4c39-9b61-85590067ce71',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify that all maintenance devices are available for servicing and operating the breaker. *4. Perform operator analysis (first-trip) test. *5. Prior to cleaning the unit, perform as-found tests.',
    false,
    3
  ),
(
    '88aec01e-c0b0-4636-afd6-144150b2fa37',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '6',
    'Clean the unit. *7. When provisions are made for sampling, remove a sample of SF gas and test in accordance 6 with Table 100.13. Do not break seal or distort sealed-for-life interrupters.',
    false,
    4
  ),
(
    '116dcf52-ebd5-4213-a20a-fc286566bf3f',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '8',
    'Inspect and service operating mechanism and/or hydraulic or pneumatic system and SF 6 gas-insulated system in accordance with manufacturer’s published data.',
    false,
    5
  ),
(
    '411200a4-7122-4785-a73f-c24093a25109',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '9',
    'Test for SF gas leaks in accordance with manufacturer’s published data. 6',
    false,
    6
  ),
(
    'e9136acc-89b1-483f-a07b-f678608d3202',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '10',
    'Test alarms, pressure switches, and limit switches for pneumatic and/or hydraulic operators and SF gas pressure in accordance with manufacturer’s published data. 6',
    false,
    7
  ),
(
    '588465c3-d6de-40a7-804e-e673aae401c1',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '11',
    'If recommended by manufacturer, slow close/open breaker and check for binding, friction, contact alignment, and penetration. Verify that contact sequence is in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, refer to IEEE C37.04.',
    false,
    8
  ),
(
    '52c6d0df-4945-4eb1-8b95-cb56edce2217',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '12',
    'Inspect all bolted electrical connections for high resistance using one or more of the following:',
    false,
    9
  ),
(
    '539515ce-86d1-4722-9d98-95b238d1ad98',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.6.4.B.1.',
    false,
    10
  ),
(
    '4a804d3b-ba4a-4c03-a2f6-3080b55f867a',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.12.',
    false,
    11
  ),
(
    '65aba7af-3ea1-496c-bb6c-36a99d3ba815',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    12
  ),
(
    '12a11f81-6dd4-4cc7-8456-97d28efec0c4',
    '87b76bf1-b80b-4fc9-9f8c-7ebd6e081f0a',
    'visual_mechanical'::neta_test_type,
    '13',
    'Verify cell fit and element alignment. * Optional Page 89',
    false,
    13
  ),
(
    '7387972f-32e2-48a7-b564-7af83865d818',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect relays and cases for physical damage. *2. Prior to cleaning the unit, perform as-found tests.',
    false,
    1
  ),
(
    '9f349148-63a6-4b62-ad35-1b41eba792c2',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '3',
    'Clean and inspect the unit.',
    false,
    2
  ),
(
    'b31de2c1-4565-4daf-baf6-4edcb1a41251',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '1',
    'Tighten case connections.',
    false,
    3
  ),
(
    '1272de6c-9bf8-4f6d-97e8-c13267c1efea',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect cover for correct gasket seal.',
    false,
    4
  ),
(
    'dbcee0d7-0e1b-4c71-a4c9-a5dd19a4ae26',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '3',
    'Clean cover glass.',
    false,
    5
  ),
(
    'b171940d-b8c7-48b9-b7fd-4fc0a7ea3bff',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect shorting hardware, connection paddles, and/or knife switches.',
    false,
    6
  ),
(
    'afa893cf-f810-45c9-873b-0dbf2909d073',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '5',
    'Remove any foreign material from the case.',
    false,
    7
  ),
(
    'ea27e5e0-d9e5-40b0-acbf-2dbea08b1285',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify target reset.',
    false,
    8
  ),
(
    'd36e471d-f789-4ce5-be05-f8044d4478ed',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect relay for foreign material, particularly in disk slots of the damping and electromagnets.',
    false,
    9
  ),
(
    '7c0674c8-625b-4e35-bcfd-2ef39c22fb9e',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify disk clearance. Verify contact clearance and spring bias.',
    false,
    10
  ),
(
    '9e544681-ccfb-40ac-946f-a59ab5adcfc8',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect spiral spring convolutions.',
    false,
    11
  ),
(
    'a585e35d-fff5-4dac-a350-4e854cc6b4d2',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect disk and contacts for freedom of movement and correct travel.',
    false,
    12
  ),
(
    'd8f834f5-aab6-47e7-8cd8-09af0064a5b9',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify tightness of mounting hardware and connections.',
    false,
    13
  ),
(
    '93ed4d3c-6f5f-460b-a43a-e43e0b8d722c',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '6',
    'Burnish contacts.',
    false,
    14
  ),
(
    'e216491d-bdb1-4a2d-97bf-3be94b1f4ce0',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '7',
    'Inspect bearings and pivots.',
    false,
    15
  ),
(
    'dc136886-2376-43ea-85d8-267f3721bb4d',
    'e942dd90-01e0-4b30-8d6a-5b2a773356dd',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify that all settings are in accordance with coordination study or setting sheet supplied by owner. * Optional Page 100',
    false,
    16
  ),
(
    '37d18891-a9d8-4773-ad5c-c76a3df48800',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'visual_mechanical'::neta_test_type,
    '1',
    'Record model number, style number, serial number, firmware revision, software revision, and rated control voltage. *2. Download all events from the event recorder in filtered and unfiltered mode before performing any tests on the relay.',
    false,
    1
  ),
(
    '058b69fb-2b1f-4c63-b469-31b6cc667a1a',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'visual_mechanical'::neta_test_type,
    '3',
    'Download the sequence of events, maintenance data, and statistical data prior to testing the relay.',
    false,
    2
  ),
(
    'fce34e3b-6617-4b89-b680-304942e5570f',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify operation of light-emitting diodes, display, and targets. *5. Record passwords for all access levels.',
    false,
    3
  ),
(
    '4ec8686c-9c6e-43ad-ac21-1b7af820282a',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'visual_mechanical'::neta_test_type,
    '6',
    'Clean the front panel and remove foreign material from the case.',
    false,
    4
  ),
(
    '90fffa28-eb01-414c-ab8f-6f880a97b83c',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'visual_mechanical'::neta_test_type,
    '7',
    'Check tightness of connections.',
    false,
    5
  ),
(
    '55627b1e-3f98-40cf-bffb-5039d9be314e',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify that the frame is grounded in accordance with manufacturer’s instructions.',
    false,
    6
  ),
(
    'e8180de5-2b5a-42ed-8316-000d70e2cdcd',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'visual_mechanical'::neta_test_type,
    '9',
    'Download settings and logic from the relay for the report and compare the settings to those specified in the coordination study. 10 Verify relay displays the correct date and time. Compare relay time to actual time and record the differential.',
    false,
    7
  ),
(
    '08719524-61c5-48ef-b30d-b7208057327f',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'visual_mechanical'::neta_test_type,
    '11',
    'Check with owner for applicable firmware updates and product recalls.',
    false,
    8
  ),
(
    '8f6d109c-6785-4efd-9b50-773da5a9a422',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'visual_mechanical'::neta_test_type,
    '12',
    'Inspect, clean, and verify operation of shorting devices.',
    false,
    9
  ),
(
    '5322fd7c-532d-4061-b5cf-cc2d4a3c75a4',
    'c8b7f0e1-445d-4069-a0af-eb24dda4dda9',
    'electrical'::neta_test_type,
    '2',
    'Apply voltage or current to all analog inputs and verify correct registration of the relay meter functions. *3. Verify SCADA metering values at remote terminals. *4. Protection Elements Check functional operation of each element used in the protection scheme as described for electromechanical and solid-state relays in 7.9.1.B.3. * Optional Page 108',
    false,
    10
  ),
(
    'dc5f9ec4-6166-4ccc-8aac-d4d52982979e',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition. *2. Prior to cleaning the unit, perform as-found tests.',
    false,
    1
  ),
(
    '6ac822b8-1d36-4d65-bf99-f9c0c71e3634',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'visual_mechanical'::neta_test_type,
    '3',
    'Clean the unit.',
    false,
    2
  ),
(
    'adb43855-4e54-471e-880a-3a509754dcae',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    3
  ),
(
    '5ac84e51-1121-4e08-b707-5d6e77d675e9',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.10.1.B.1.',
    false,
    4
  ),
(
    '05039f11-1750-4034-8914-c197fe9699d6',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    5
  ),
(
    '8fa36608-5e68-4cd1-b265-047d40871afc',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    6
  ),
(
    '89a0d85b-b41c-416a-9b1f-f4b6cebc21ea',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify that all required grounding and shorting connections provide contact.',
    false,
    7
  ),
(
    '589e1c51-ce46-495c-bf48-b9d35de61771',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'visual_mechanical'::neta_test_type,
    '6',
    'Use appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    8
  ),
(
    '7c4b05bb-aaea-4d87-b95d-2226b2f514f3',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'visual_mechanical'::neta_test_type,
    '7',
    'Perform as-left tests.',
    false,
    9
  ),
(
    '23729d6d-461a-413f-ae54-7efd4022fff9',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.10.1.A.4.1.',
    false,
    10
  ),
(
    '8f25e894-e226-460b-a11c-374cb09b9d45',
    '09257eca-2499-4254-8051-f4ce00c631f8',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance test of each current transformer and wiring-to-ground at 1000 volts dc for one minute. For units with solid-state components that cannot tolerate the applied voltage, follow manufacturer’s recommendations. *3. Perform a polarity test of each current transformer in accordance with IEEE C57.13.1. *4. Perform a ratio-verification test using the voltage or current method in accordance with IEEE C57.13.1. *5. Perform an excitation test on transformers used for relaying applications in accordance with IEEE C57.13.1. *6. Measure current circuit burdens at transformer terminals. * Optional Page 111',
    false,
    11
  ),
(
    '2c20898f-edd3-46ee-857a-da430b32aeb1',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition. *2. Prior to cleaning the unit, perform as-found tests.',
    false,
    1
  ),
(
    '05cd8ab5-92a2-46cd-b252-f8c096e88402',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '3',
    'Clean the unit.',
    false,
    2
  ),
(
    'fbfe68a3-fa1d-4889-b849-966bf4c99bb4',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    3
  ),
(
    'cdb93c7d-e859-4625-85ce-d1efb49439fa',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.10.2.B.1.',
    false,
    4
  ),
(
    'e3b77550-5a7e-4026-94d5-e6b229ed0ff1',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    5
  ),
(
    'f37b59e8-1f6c-454f-a975-8e2af5f1fb49',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    6
  ),
(
    'e04d1589-c37f-4181-b141-f9aec6bba548',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify that all required grounding and connections provide contact.',
    false,
    7
  ),
(
    '61c52a4c-3698-4b64-838d-5e9229a1a372',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct operation of transformer withdrawal mechanism and grounding operation.',
    false,
    8
  ),
(
    '6ebbfe73-72cd-4283-84e3-d297123bb0ae',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify correct primary and secondary fuse sizes for voltage transformers.',
    false,
    9
  ),
(
    '57a38b03-3c0d-4e7d-89bf-2f582033ffec',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '8',
    'Use appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    10
  ),
(
    'd34f4568-8768-481f-8327-bc197ad9e588',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'visual_mechanical'::neta_test_type,
    '9',
    'Perform as-left tests.',
    false,
    11
  ),
(
    '3e432f68-53f9-4e4a-8313-71baad763c00',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.10.2.A.4.1',
    false,
    12
  ),
(
    '50e56548-9a74-4dde-bf85-20cc312e08f0',
    '3f2fa895-bc71-4cee-b94b-15dabe91c680',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests for one minute winding-to-winding and each winding-to- ground. Test voltages shall be applied in accordance with Table 100.5. For units with solid- state components that cannot tolerate the applied voltage, follow manufacturer’s recommendations. *3. Perform a polarity test on each transformer, as applicable, to verify the polarity marks or H1-X1 relationship. *4. Perform a turns-ratio test on as-found tap position. *5. Measure voltage circuit burdens at transformer terminals. * Optional Page 114',
    false,
    13
  ),
(
    '0414438b-275e-4a59-a7f7-5a5925ba7c1b',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition. *2. Prior to cleaning the unit, perform as-found tests.',
    false,
    1
  ),
(
    '21bf690b-7f86-44c0-8e9d-3a70503796ef',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '3',
    'Clean the unit.',
    false,
    2
  ),
(
    'cf4f9663-76aa-4f7c-a34f-da9e6e3ef2ec',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    3
  ),
(
    '642b1108-3bb1-4b04-af70-1efc118ea242',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.10.3.B.1.',
    false,
    4
  ),
(
    '36571e1c-1a52-4731-bff7-14532d5db555',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    5
  ),
(
    '69054f33-8c5c-49ac-8e05-c298a62df058',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    6
  ),
(
    '6e37b40f-e8d5-4bee-b6f2-9e0b5e523dc5',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify that all required grounding and connections provide contact.',
    false,
    7
  ),
(
    '18e4a6fd-4411-412d-8f66-f3c5b5456406',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct operation of the grounding switches.',
    false,
    8
  ),
(
    '067dc542-9063-41db-b5b7-8decd715c519',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify correct primary and secondary fuse sizes for voltage transformers.',
    false,
    9
  ),
(
    '76b8039d-682e-4d59-a0b5-6b11dd1dcfeb',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '8',
    'Use appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    10
  ),
(
    'b230d37c-4d6f-4a33-9cb7-468f070c5d8c',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'visual_mechanical'::neta_test_type,
    '9',
    'Perform as-left tests.',
    false,
    11
  ),
(
    'b1529166-74af-4079-98bb-701090c81ae8',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.10.3.A.4.1.',
    false,
    12
  ),
(
    'be13e9b1-2d32-45d5-a63c-79f5a26d7624',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests for one minute, winding-to-winding and each winding- to-ground. Test voltages shall be applied in accordance with Table 100.5. For units with solid-state components that cannot tolerate the applied voltage, follow manufacturer’s recommendations. *3. Perform a polarity test on each transformer, as applicable, to verify the polarity marks or H1-X1 relationship. See IEEE C93.1 for standard polarity marking.',
    false,
    13
  ),
(
    'f700a86e-6d3b-4e23-ab23-5470e0ae07c0',
    '42d123a0-d8c7-47f4-bc7a-a8f3f271b0a7',
    'electrical'::neta_test_type,
    '4',
    'Perform a ratio test on the designated tap position. * Optional Page 117',
    false,
    14
  ),
(
    'b1398c92-56cd-4860-91ba-40b19fc1b4e6',
    'a2608550-83b8-4a53-a3cc-c05fc62518d4',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'bd1b87fb-7af7-42b4-8204-0f760b7117c3',
    'a2608550-83b8-4a53-a3cc-c05fc62518d4',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of electrical connections',
    false,
    2
  ),
(
    '17f4dc9b-ab51-4911-8a97-d8ea72cfcdaf',
    'a2608550-83b8-4a53-a3cc-c05fc62518d4',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect cover gasket, cover glass, condition of spiral spring, disk clearance, contacts, and case-shorting contacts, as applicable. *4. Prior to cleaning the unit, perform as-found tests.',
    false,
    3
  ),
(
    '1a1433fd-543c-4663-bc9c-bc5be39b5b00',
    'a2608550-83b8-4a53-a3cc-c05fc62518d4',
    'visual_mechanical'::neta_test_type,
    '5',
    'Clean the unit.',
    false,
    4
  ),
(
    '4042c126-417d-4657-9ba3-324398c708c7',
    'a2608550-83b8-4a53-a3cc-c05fc62518d4',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify freedom of movement, end play, and alignment of rotating disk(s).',
    false,
    5
  ),
(
    '85fa944d-e03e-4dbd-9af0-aacb2166b157',
    'a2608550-83b8-4a53-a3cc-c05fc62518d4',
    'visual_mechanical'::neta_test_type,
    '7',
    'Perform as-left tests.',
    false,
    6
  ),
(
    '527099c1-d9ee-4ecb-a239-45eef7c6415c',
    'a2608550-83b8-4a53-a3cc-c05fc62518d4',
    'electrical'::neta_test_type,
    '1',
    'Verify accuracy of meters per the manufacturers published data.',
    false,
    7
  ),
(
    '28fd6773-6903-4385-9613-8adc4f8024ba',
    'a2608550-83b8-4a53-a3cc-c05fc62518d4',
    'electrical'::neta_test_type,
    '2',
    'Calibrate meters in accordance with manufacturer’s published data. *3. Verify all instrument multipliers. * Optional Page 121',
    false,
    8
  ),
(
    '81abf059-179f-48b1-8685-b76cfb4773e9',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect meters and cases for physical damage.',
    false,
    1
  ),
(
    '2d7dda6f-008f-468e-9f79-5c3d8a8f3d27',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'visual_mechanical'::neta_test_type,
    '2',
    'Clean front panel.',
    false,
    2
  ),
(
    'cb640817-5bcd-46a3-be81-46ca4c2e5877',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify tightness of electrical connections.',
    false,
    3
  ),
(
    '876d6274-318b-4c24-b11a-abfe57c2f400',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'visual_mechanical'::neta_test_type,
    '4',
    'Record model number, serial number, firmware revision, software revision, and rated control voltage.',
    false,
    4
  ),
(
    '4e3429e6-9b5d-4254-a64c-6423e439d7f7',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify operation of display and indicating devices.',
    false,
    5
  ),
(
    '9667146d-ba2f-4a72-9848-a5496789ce12',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'visual_mechanical'::neta_test_type,
    '6',
    'Record passwords.',
    false,
    6
  ),
(
    '0936a59e-56ca-4b78-bc73-12ae043cd42d',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify unit is grounded in accordance with manufacturer’s instructions.',
    false,
    7
  ),
(
    'f69f4788-4821-401e-b704-83c9c5b47970',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify unit is connected in accordance with manufacturer’s instructions and project drawings.',
    false,
    8
  ),
(
    '792c04c0-37c3-4d57-9f3e-9b6194ddd123',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'visual_mechanical'::neta_test_type,
    '9',
    'Download settings from the meter, print a copy of the settings for the report, and compare the settings to those specified.',
    false,
    9
  ),
(
    '08a98343-98b3-4906-997f-6a75f4db2162',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'electrical'::neta_test_type,
    '1',
    'Apply voltage or current as appropriate to each analog input and verify correct measurement and indication.',
    false,
    10
  ),
(
    'e3ae7d5f-3aa3-4926-9cba-9540a422baa9',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'electrical'::neta_test_type,
    '2',
    'Confirm correct operation and setting of each auxiliary input/output feature in use, including mechanical relay, digital, and analog.',
    false,
    11
  ),
(
    '5c794caa-b50f-41b9-a514-600ec7eee477',
    '46a969eb-76a0-4cd1-bba9-23c0cb9bab07',
    'electrical'::neta_test_type,
    '3',
    'Confirm measurements and indications are consistent with loads present.',
    false,
    12
  ),
(
    '91a857f8-078d-4aa0-b655-4382bf941794',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'd6cb0270-a315-4504-a248-cc75ea31ca8d',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding.',
    false,
    2
  ),
(
    '83018bfd-1ab3-4eab-b244-ae06e254fce6',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '3',
    'Record position indicator as-found, maximum, and minimum values. *4. Prior to cleaning the unit, perform as-found tests.',
    false,
    3
  ),
(
    '94317063-fa34-451f-aef8-ecd8a9d9365e',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '5',
    'Clean bushings and control cabinets.',
    false,
    4
  ),
(
    '67e2a5d8-e2b9-4a9a-9921-832b5f1f03b8',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '6',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    5
  ),
(
    '48d6d5f2-5340-4721-b865-4da7ef653a61',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.12.3.B.1.',
    false,
    6
  ),
(
    '6053c9c1-450d-495c-842a-271a1eb11e6c',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.12.',
    false,
    7
  ),
(
    'f4f53eef-cef0-48f9-ac4c-03dbf8493f10',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    8
  ),
(
    'ca000119-49f7-421e-ad95-b81f65f7774e',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify correct auxiliary device operation.',
    false,
    9
  ),
(
    '2f701d34-bd9d-4cb9-b6b6-f57544bb7278',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify motor and drive train for correct operation and automatic motor cutoff at maximum lower and maximum raise.',
    false,
    10
  ),
(
    '3520fdd3-9e56-4b59-b6e6-dbbeec020839',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify correct liquid level in all tanks.',
    false,
    11
  ),
(
    '711aedc1-19b0-4ae5-9263-e7cfcaf87c66',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '10',
    'Perform mechanical maintenance, inspections, and tests as recommended by the manufacturer. *11. Visually inspect wear/erosion indicators on vacuum bottles. *12. Perform an internal inspection:',
    false,
    12
  ),
(
    'a21fa60f-1baf-4caa-b61a-563e13760138',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '2',
    'Clean carbon residue and debris from compartment.',
    false,
    13
  ),
(
    '37b0e49f-ed81-49cb-91b5-0938875881f0',
    'a690967f-968b-4334-ba0a-eb44da78e0ac',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect contacts for wear and alignment. * Optional Page 135',
    false,
    14
  ),
(
    'b637ead8-a65a-421f-91ad-d3812dbcc528',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'ee50fe23-ebe6-4a29-ac08-867f61608393',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding.',
    false,
    2
  ),
(
    'aa7fb0f9-8578-4c66-9166-726d7f8e7245',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect air baffles, filter media, stator winding, stator core, rotor, cooling fans, slip rings, brushes, brush rigging, and bearings.',
    false,
    3
  ),
(
    'aca9cad9-dd69-4eec-8966-5174c5fb2eaa',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    4
  ),
(
    '787ee712-db13-424e-8ed9-a5915da0704c',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of low-resistance ohmmeter in accordance with Section 7.15.1.B.1.',
    false,
    5
  ),
(
    'a11000df-b2be-4617-a11d-2d0a758e9ba5',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.12.',
    false,
    6
  ),
(
    '19857bd1-03d9-474f-8161-06bdb3ef40eb',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform thermographic survey in accordance with Section 9. *5. Perform special tests such as air-gap spacing and machine alignment.',
    false,
    7
  ),
(
    'a3ff472a-8d6d-484a-ad66-432bc0670652',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify the application of appropriate lubrication and lubrication systems.',
    false,
    8
  ),
(
    'a4d9dae1-5a7a-43e4-a15e-9bf8f76a9ef4',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify the absence of unusual mechanical or electrical noise or signs of overheating.',
    false,
    9
  ),
(
    '5732a816-6b2f-405a-a613-61ccf07a1d6e',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify that resistance temperature detector (RTD) circuits conform to drawings.',
    false,
    10
  ),
(
    'e682d914-53e5-4cef-b415-fe64b32ef17e',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.15.1.A.4.1.',
    false,
    11
  ),
(
    'bc620903-7c86-4668-a0fa-3cc93334869a',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests in accordance with IEEE 43.',
    false,
    12
  ),
(
    'd31858a8-7ab1-4a09-bd2a-5f9f9b75ed16',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'electrical'::neta_test_type,
    '1',
    'Machines larger than 200 horsepower (150 kilowatts): Test duration shall be for ten minutes. Calculate polarization index.',
    false,
    13
  ),
(
    '6e361cd9-4ad0-4cce-a8a3-31f0ce6d44c3',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'electrical'::neta_test_type,
    '2',
    'Machines 200 horsepower (150 kilowatts) and less: Test duration shall be for one minute. Calculate the dielectric-absorption ratio.',
    false,
    14
  ),
(
    'ac645736-525e-45c9-b5a9-8e7de1c50568',
    '48b01f3c-524d-42cd-88a9-edb7edcebf8d',
    'electrical'::neta_test_type,
    '3',
    'Perform dielectric withstand voltage tests on machines rated at 2300 volts and greater in accordance with: * Optional Page 145',
    false,
    15
  ),
(
    '5465489a-4979-4083-868b-b89ccc2e13ef',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'c632ab67-6711-46fa-99e0-6a39ac620313',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding.',
    false,
    2
  ),
(
    '4d063df6-a667-4401-8878-a9c94949a0aa',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect air baffles, filter media, cooling fans, stator winding, stator core, rotor, slip rings, brushes, and brush rigging or brushless exciter.',
    false,
    3
  ),
(
    '3d8dc4ca-5a47-4993-98a5-1c59b1535782',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect bearings.',
    false,
    4
  ),
(
    '6c75baf3-a804-4856-95fa-1598cbc66274',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    5
  ),
(
    '891e691e-cd21-4715-b59d-c6760171cf8a',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of low-resistance ohmmeter in accordance with Section 7.15.2.B.1.',
    false,
    6
  ),
(
    '89ee0db5-228a-4ef4-8dcd-b5678279d58d',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.12.',
    false,
    7
  ),
(
    'bdca4470-9ebb-4e18-8c60-e09783b7f631',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform thermographic survey in accordance with Section 9. *6. Perform special tests such as air-gap spacing and machine alignment.',
    false,
    8
  ),
(
    'b75f0c25-e7e2-411c-a1c5-6b2eb0773f21',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify the application of appropriate lubrication and lubrication systems.',
    false,
    9
  ),
(
    '656df6e8-747e-4813-9b96-35bac4a23e02',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify the absence of unusual mechanical or electrical noise or signs of overheating.',
    false,
    10
  ),
(
    '9b844a52-cfd3-4c41-84fa-e2cc11e18275',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify that resistance temperature detector (RTD) circuits conform to drawings.',
    false,
    11
  ),
(
    '0ca1f46d-bf94-4a72-ba2f-1b920349404c',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.15.2.A.5.1.',
    false,
    12
  ),
(
    '978ef5e6-e0e8-4e1c-9623-6cac4b463a06',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests in accordance with IEEE 43.',
    false,
    13
  ),
(
    'c8df4ec5-6f80-4cfd-a855-8cd5440fe0e3',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'electrical'::neta_test_type,
    '1',
    'Machines larger than 200 horsepower (150 kilowatts): Test duration shall be for ten minutes. Calculate polarization index.',
    false,
    14
  ),
(
    '9e744653-aaab-457e-a096-96537ce34553',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'electrical'::neta_test_type,
    '2',
    'Machines 200 horsepower (150 kilowatts) and less: Test duration shall be for one minute. Calculate the dielectric-absorption ratio.',
    false,
    15
  ),
(
    '069c9171-c86f-4506-aa77-d42bdd8f880d',
    'bbd96d3e-4c9e-426d-a549-2b1b660ea444',
    'electrical'::neta_test_type,
    '3',
    'Perform dc dielectric withstand voltage tests on machines rated at 2300 volts and greater in accordance with IEEE 95. * Optional Page 150',
    false,
    16
  ),
(
    '942ddf79-5201-49f2-9fc6-19fd9f15a285',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'fccbf655-557b-4d64-8bec-2cf76f624a66',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding.',
    false,
    2
  ),
(
    '69127417-5f38-4fcd-9e7b-d72ea4937624',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'visual_mechanical'::neta_test_type,
    '3',
    'Inspect air baffles, field poles and yokes, armature, cooling fans, commutator, brushes, and brush rigging, and bearings.',
    false,
    3
  ),
(
    'd6287403-6027-4b1b-bd57-a0829fd8ceaa',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'visual_mechanical'::neta_test_type,
    '4',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    4
  ),
(
    'd18957e0-000b-4eb7-ab24-1aceedfc5c1b',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of low-resistance ohmmeter in accordance with Section 7.15.3.B.1.',
    false,
    5
  ),
(
    '463ef88b-5226-4e93-bcfe-ec5077c79b3c',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.12.',
    false,
    6
  ),
(
    '69b47a50-c0f9-4438-83a9-f8d9f429db73',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform thermographic survey in accordance with Section 9.',
    false,
    7
  ),
(
    '6367bde8-c332-484b-a571-ad54e7d8fa8d',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect commutator and tachometer generator. *6. Perform special tests such as air-gap spacing and machine alignment.',
    false,
    8
  ),
(
    '57d05d9b-31de-4aa4-88c1-d50d7814cdc5',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.15.3.A.4.1.',
    false,
    9
  ),
(
    '502ec68b-47f8-4c07-a46f-07e89d736fc6',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests on all windings in accordance with IEEE 43.',
    false,
    10
  ),
(
    '5a1167df-500b-4b17-bee0-ee6730ad2a71',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'electrical'::neta_test_type,
    '1',
    'Machines larger than 200 horsepower (150 kilowatts): Test duration shall be for ten minutes. Calculate polarization index.',
    false,
    11
  ),
(
    'bec8add5-fa4a-459e-aac6-ea6b016b11c7',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'electrical'::neta_test_type,
    '2',
    'Machines 200 horsepower (150 kilowatts) and less: Test duration shall be for one minute. Calculate the dielectric absorption ratio.',
    false,
    12
  ),
(
    'a0cb5641-8ae3-41c1-b3c4-d834b2bf24e2',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'electrical'::neta_test_type,
    '3',
    'Perform high-potential test in accordance with NEMA MG 1, paragraph 3.01. *4. Perform an ac voltage-drop test on all field poles.',
    false,
    13
  ),
(
    'fef9f29c-736f-45c7-8a53-5e45747bd21e',
    '66b64f75-1843-408e-9430-be6c76ab5673',
    'electrical'::neta_test_type,
    '5',
    'Measure armature running current and field current or voltage. Compare to nameplate. *6. Perform vibration tests while machine is running under load. * Optional Page 156',
    false,
    14
  ),
(
    'c174402d-af71-46c7-b0fe-e392c9072e77',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect for physical and mechanical condition.',
    false,
    1
  ),
(
    '9f7c3848-8901-4fdb-b4ed-cad177668e9d',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    '31b08522-d033-474f-b6ad-e16ef83949b0',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    'f87696fc-13b7-49b9-9c8a-f444ad78461c',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect all bolted electrical connections for high resistance using one or more of the following:',
    false,
    4
  ),
(
    'ff5a4a46-55e5-4fc5-b0e6-033fcb43dbf0',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter.',
    false,
    5
  ),
(
    'de27f293-7963-477f-adfb-c88ccc457ca9',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    6
  ),
(
    '77fbde92-e932-409d-bef3-d800480ec504',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey under load in accordance with Section 9.',
    false,
    7
  ),
(
    'da1a5530-bd76-439f-863c-b3f5755fcb3a',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '6',
    'Inspect filter and tank capacitors.',
    false,
    8
  ),
(
    'ac5fbfd6-67f1-41b7-85d7-ad172eaa309a',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify operation of cooling fans. Clean filters if provided.',
    false,
    9
  ),
(
    '546d5cad-b7fb-4118-a0f9-cc12384f2d41',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'visual_mechanical'::neta_test_type,
    '8',
    'Perform as-left tests.',
    false,
    10
  ),
(
    '7cd631b8-e0e5-4a24-8d99-5694ba5378a8',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through all bolted connections with a low-resistance ohmmeter.',
    false,
    11
  ),
(
    'c4d73bfc-33cc-4782-9fa4-01b2155befb7',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'electrical'::neta_test_type,
    '2',
    'Verify float voltage and equalize voltage. *3. Verify high-voltage shutdown settings.',
    false,
    12
  ),
(
    '32b59301-3d72-4425-af48-5b16483b8c51',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'electrical'::neta_test_type,
    '4',
    'Verify correct load sharing (parallel chargers).',
    false,
    13
  ),
(
    '8ba1ff34-5fed-48c8-8cc1-4aef6336b39d',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'electrical'::neta_test_type,
    '5',
    'Verify calibration of meters in accordance with Section 7.11.',
    false,
    14
  ),
(
    '866d7ab8-1b73-491a-a43d-8280924adfc3',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'electrical'::neta_test_type,
    '6',
    'Verify operation of alarms.',
    false,
    15
  ),
(
    '26457969-31da-46d9-a56f-07eb2326cc5e',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'electrical'::neta_test_type,
    '7',
    'Measure and record input and output voltage and current.',
    false,
    16
  ),
(
    '4fda76c1-522b-439f-98eb-2f1003f1154d',
    '6cf1bc38-6723-4fb4-b4b1-a99d9a3d5477',
    'electrical'::neta_test_type,
    '8',
    'Measure and record ac ripple current and voltage imposed on battery. *9. Perform full load testing and verify current limit of charger. * Optional Page 177',
    false,
    17
  ),
(
    '65e21db3-d6b9-4e9a-9cf4-71e002ab4743',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'b0a9f4fe-d5b1-4c11-9465-4825272c4932',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    'f7fc617b-fb75-48b1-ae89-d45cd1000578',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    'aecf0e0d-a75f-4460-9313-ce2e2d6ee0a5',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    4
  ),
(
    '8c7be7b3-6116-42bc-be98-a6a2133ac544',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.19.1.B.1.',
    false,
    5
  ),
(
    'df770879-cbbd-4314-a1d2-650ea033c571',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    6
  ),
(
    '51535439-bed2-45d0-8bbf-0e433f87ebc1',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that the ground lead on each device is individually attached to a ground bus or ground electrode.',
    false,
    7
  ),
(
    '2240cb6f-b714-4a36-ba60-af5843f64922',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'visual_mechanical'::neta_test_type,
    '7',
    'Perform as-left tests.',
    false,
    8
  ),
(
    '27c8ba4f-1c60-415f-bfcd-0287d78b7651',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'visual_mechanical'::neta_test_type,
    '8',
    'Verify healthy status in accordance with manufacturer’s data.',
    false,
    9
  ),
(
    '761d9edc-575a-4b4d-abf8-007b54561af7',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.19.1.A.5.1.',
    false,
    10
  ),
(
    '40b33b8f-df38-4019-9ae9-b10d74948110',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance test on each arrester, from the phase terminal to ground. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1.',
    false,
    11
  ),
(
    '3534129b-c171-4724-9b74-585c58d05f67',
    'f60097e4-f73d-4b70-b3ac-5e0b8b6655bc',
    'electrical'::neta_test_type,
    '3',
    'Test grounding connection in accordance with Section 7.13. * Optional Page 180',
    false,
    12
  ),
(
    'e349217b-44fb-4a34-8091-e5e72523cd9d',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    '1dd845da-3b8f-419a-a731-081891e4aa88',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    '26a07775-6c41-4951-85c2-1d69af56c695',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    'eff95656-f26d-487f-9063-d5ecc5d04306',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    4
  ),
(
    'e81c5150-4d20-4685-a220-9ec8b66595e5',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.19.2.B.1.',
    false,
    5
  ),
(
    'baca5281-c956-4978-a000-8aaafa965097',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    6
  ),
(
    'd8b701ed-ff32-4a08-8ffd-18a0d422712a',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that the ground lead on each device is individually attached to a ground bus or ground electrode.',
    false,
    7
  ),
(
    'c27d2176-86b5-479d-9205-b99058d889ed',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify that stroke counter, if present, is correctly mounted and electrically connected.',
    false,
    8
  ),
(
    '94663e04-4f97-49db-be35-e41ff19ea208',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'visual_mechanical'::neta_test_type,
    '8',
    'Perform as-left tests.',
    false,
    9
  ),
(
    'f021b457-3946-4afd-b855-74cc36a6465b',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.19.2.A.5.1.',
    false,
    10
  ),
(
    '28cf8d8b-0b85-4e94-aa0e-575340c43eeb',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests from phase terminals(s) to case for one minute. Test voltage and minimum resistance shall be in accordance with manufacturer''s published data. In the absence of manufacturer''s published data, refer to Table 100.1.',
    false,
    11
  ),
(
    '0f0c4061-3ddc-47ec-bfb6-12f836033d51',
    '0eea2c31-7c99-44d4-8295-2237f6581e07',
    'electrical'::neta_test_type,
    '3',
    'Test the grounding connection in accordance with Section 7.13. *4. Perform a watts-loss test in accordance with test equipment manufacturer’s published data. * Optional Page 182',
    false,
    12
  ),
(
    '385765d9-d224-49f9-8595-fd4ee95b63d4',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    '199b6eea-2135-43ad-afad-164483df18b3',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, grounding, and required clearances. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    '17f57fd4-ca85-4e45-95b3-0efdec516357',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    'd35be3e2-f0c9-4425-9d6b-de68b64a5604',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'visual_mechanical'::neta_test_type,
    '5',
    'Verify that capacitors are electrically connected in their specified configuration.',
    false,
    4
  ),
(
    '898b50eb-478b-46ff-a5b3-97e559ab4204',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'visual_mechanical'::neta_test_type,
    '6',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    5
  ),
(
    '00851b68-99ae-4126-ab95-28e0303b7200',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.20.1.B.1.',
    false,
    6
  ),
(
    'cceb7104-eead-49ef-8e63-e61e394526c9',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    7
  ),
(
    '30150074-f310-4963-af53-f7132b802715',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    8
  ),
(
    'e65fd3c4-c47c-43af-bd3f-4735f085fac6',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'visual_mechanical'::neta_test_type,
    '7',
    'Perform as-left tests.',
    false,
    9
  ),
(
    'c5d8f5d0-c862-4735-bebe-80767f387315',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.20.1.A.6.1.',
    false,
    10
  ),
(
    'c0f9ffc4-ef4f-4c58-baff-8e07dbadebe6',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'electrical'::neta_test_type,
    '2',
    'Perform insulation-resistance tests from phase terminal(s) to case for one minute. Test voltage and minimum resistance should be in accordance with manufacturer''s published data. In the absence of manufacturer''s published data, refer to Table 100.1.',
    false,
    11
  ),
(
    '2ad0f499-affd-49ac-a180-236aea3b21d7',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'electrical'::neta_test_type,
    '3',
    'Measure the capacitance of all terminal combinations.',
    false,
    12
  ),
(
    'db7136f4-757c-4952-b99f-41a33ac180a1',
    '6cd91ec1-2969-464a-be24-98a0a6297624',
    'electrical'::neta_test_type,
    '4',
    'Measure resistance of internal discharge resistors. * Optional Page 184',
    false,
    13
  ),
(
    '09de6f9d-9a0d-4d82-8824-eb368d41e0be',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    '853f6d49-bb7c-4562-810e-f7d6e905fdc9',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    '6c1392ad-4fe6-4df7-a2a5-d75176daf1b1',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    '09eedd38-878d-4f72-bee5-8cc732c8929a',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    4
  ),
(
    'fe31f2b3-468c-44fa-b180-a42dff652b70',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.20.3.1.B.1.',
    false,
    5
  ),
(
    '66d90f2e-449e-47dd-9b7b-431b9641cc61',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    6
  ),
(
    'cdad2609-eb67-41e6-85b6-c38f20c69be7',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    7
  ),
(
    'eef5cf9c-ac6b-48cc-85f4-8e9f7e227eca',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that tap connections are as specified.',
    false,
    8
  ),
(
    '258fcddf-6379-419b-926c-73e9fa4a45aa',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'visual_mechanical'::neta_test_type,
    '7',
    'Perform as-left tests.',
    false,
    9
  ),
(
    'f0cf8313-9ee7-4c55-872d-5f593c92811b',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with low-resistance ohmmeter in accordance with Section 7.20.3.1.A.5.1.',
    false,
    10
  ),
(
    '43c53597-eac0-45c3-ae2f-40c79a323331',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'electrical'::neta_test_type,
    '2',
    'Perform winding-to-ground insulation-resistance tests. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1.',
    false,
    11
  ),
(
    '419a8702-57c6-47cc-b935-195ed1863980',
    '3d0f6c2a-4e4b-4c12-b5b5-66f3ae5a8f2e',
    'electrical'::neta_test_type,
    '3',
    'Measure winding resistance. *4. Perform dielectric withstand voltage tests on each winding-to-ground. *5. Perform online partial-discharge survey in accordance with Section 11. * Optional Page 187',
    false,
    12
  ),
(
    '42988b25-2ffc-4376-988b-a5987689224a',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'a75c4f7b-2e6c-4cd4-b53e-e7781f024650',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    'caf4d4bd-7bef-4fb5-a8bc-48908677a956',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    '87f00812-8a63-4588-b8db-9c7bf969fbb6',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '5',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    4
  ),
(
    '5c552b4b-aa53-4fdb-8d56-e71b58302105',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.20.3.2.B.1.',
    false,
    5
  ),
(
    '34b279a3-8b8d-491b-8fa0-0f613a66f04a',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    6
  ),
(
    '58b8c6ff-261a-44a0-a65b-05c37a6029f8',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    7
  ),
(
    'f9fdd585-e9e8-4bc9-a1a7-fbd657d83295',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '6',
    'Perform as-left tests.',
    false,
    8
  ),
(
    'db80c4ec-1015-4700-902f-ec3f7196dddf',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify correct liquid level in all tanks and bushings.',
    false,
    9
  ),
(
    'f02d1f34-deed-47b0-900a-cdc4daf35d87',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'visual_mechanical'::neta_test_type,
    '8',
    'Perform mechanical maintenance, inspections, and tests as recommended by the manufacturer.',
    false,
    10
  ),
(
    '575867f9-bbde-4049-8b19-56627e2eeff3',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'electrical'::neta_test_type,
    '1',
    'Perform resistance measurements through bolted connections with a low-resistance ohmmeter in accordance with Section 7.20.3.2.A8.1.',
    false,
    11
  ),
(
    '30d0c4c3-7553-41b9-8ef0-c6065f4da70c',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'electrical'::neta_test_type,
    '2',
    'Perform resistor-to-ground insulation-resistance tests. Apply voltage in accordance with manufacturer’s published data. In the absence of manufacturer’s published data, use Table 100.1. Calculate polarization index.',
    false,
    12
  ),
(
    '09228191-bd2a-4cc1-a4ad-96fbe308e055',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'electrical'::neta_test_type,
    '3',
    'Perform power-factor or dissipation-factor tests on each bushing equipped with a power- factor/ capacitance tap. In the absence of a power-factor/ capacitance tap, perform hot- collar tests. These tests shall be in accordance with the test equipment manufacturer’s published data.',
    false,
    13
  ),
(
    'e344e178-3702-4b2a-b04a-9286148ef305',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'electrical'::neta_test_type,
    '5',
    'Measure resistor resistance.',
    false,
    14
  ),
(
    'fe26880e-85ed-45fb-a759-a565bcc95846',
    '29810238-bea4-49ae-87ce-0c161e2c8075',
    'electrical'::neta_test_type,
    '6',
    'Perform electrical tests on current transformer in accordance with Section 7.10.1. * Optional Page 193',
    false,
    15
  ),
(
    '51f77637-f3d0-4641-890e-ad3883b29db1',
    '4edbfac4-5586-4178-b7b6-271002ac1050',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    '52dc76d6-740a-40f0-94de-b66c4743cfe4',
    '4edbfac4-5586-4178-b7b6-271002ac1050',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, and grounding. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    '57cacb05-66d6-46a2-8dec-da78d0574ee6',
    '4edbfac4-5586-4178-b7b6-271002ac1050',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    'e0e413b0-d63e-4943-bee6-c3d64567ea78',
    '4edbfac4-5586-4178-b7b6-271002ac1050',
    'visual_mechanical'::neta_test_type,
    '5',
    'Perform as-left tests.',
    false,
    4
  ),
(
    'f6a15b80-4b26-43a1-9635-dd5acbf8c84b',
    '4edbfac4-5586-4178-b7b6-271002ac1050',
    'visual_mechanical'::neta_test_type,
    '1',
    'Perform insulation-resistance test on the generator winding-to-ground in accordance with IEEE 43. Calculate the polarization index.',
    false,
    5
  ),
(
    '63c1cdd5-234c-4252-ba34-1c6423ea1f9c',
    '4edbfac4-5586-4178-b7b6-271002ac1050',
    'visual_mechanical'::neta_test_type,
    '2',
    'Test protective relay devices in accordance with Section 7.9.',
    false,
    6
  ),
(
    '5dd382c6-23b8-4ccd-9362-b24909b0d21b',
    '4edbfac4-5586-4178-b7b6-271002ac1050',
    'visual_mechanical'::neta_test_type,
    '3',
    'Functionally test engine shutdown for low oil pressure, overtemperature, overspeed, and other protection features as applicable. *4. Perform vibration test for each main bearing cap.',
    false,
    7
  ),
(
    '7c4e1eb5-bcc6-4a53-95ce-a358acf999fd',
    '4edbfac4-5586-4178-b7b6-271002ac1050',
    'visual_mechanical'::neta_test_type,
    '5',
    'Conduct performance test in accordance with NFPA 110.',
    false,
    8
  ),
(
    '438b0cc8-c241-4b15-bcf9-0617b111a3fc',
    '4edbfac4-5586-4178-b7b6-271002ac1050',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify correct functioning of governor and regulator.',
    false,
    9
  ),
(
    'b7594e6b-a256-4283-aa65-e5592743517a',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    'b44df1e1-46f8-424f-beb6-30973f18602e',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '2',
    'Check for anchorage, alignment, grounding, and required clearances.',
    false,
    2
  ),
(
    '0c9313b7-e31c-4745-b55f-232fd5a3dbca',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify that fuse sizes and types correspond to drawings. *4. Prior to cleaning the unit, perform as-found tests.',
    false,
    3
  ),
(
    '8016bcfe-e1c6-43b4-a26f-9368dd33c3af',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '5',
    'Clean the unit.',
    false,
    4
  ),
(
    'ea634dcf-d93b-4866-a55d-a01a0634c31a',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '6',
    'Test all electrical and mechanical interlock systems for correct operation and sequencing.',
    false,
    5
  ),
(
    '1a14765f-46c9-4471-b344-b75e1a6018cf',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '7',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    6
  ),
(
    '84e9d58a-3b4e-4b63-9029-bf023230f099',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.22.2.B.1.',
    false,
    7
  ),
(
    '9152024e-a03f-490a-a763-b55d31254170',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    8
  ),
(
    '610c19bd-35e7-4bef-868d-d6974bb114b0',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    9
  ),
(
    'f66b2754-4a07-4cae-a746-7cc2c99c1900',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '8',
    'Perform as-left tests.',
    false,
    10
  ),
(
    'd2a1c5cd-ee86-4709-8cfc-a6c2d76f90b7',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '9',
    'Check operation of forced ventilation.',
    false,
    11
  ),
(
    'd2c91842-678a-4ffb-88bb-142692ced360',
    'f3ed7d17-e1ae-439c-a6ad-16f627f677a9',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify that filters are in place, filters are clean and free from debris, and/or vents are clear. * Optional Page 199',
    false,
    12
  ),
(
    '73a52056-dc0f-481b-b87f-1a4fbdbc3b44',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '1',
    'Inspect physical and mechanical condition.',
    false,
    1
  ),
(
    '3856ced6-73a9-4b59-866c-d515bb296889',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect anchorage, alignment, grounding, and required clearances. *3. Prior to cleaning the unit, perform as-found tests.',
    false,
    2
  ),
(
    'd709d0c6-090e-42f1-8975-826e88b90299',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '4',
    'Clean the unit.',
    false,
    3
  ),
(
    'f823e752-95ed-4a18-889c-6f149e3c55b7',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '5',
    'Use appropriate lubrication on moving current-carrying parts and on moving and sliding surfaces.',
    false,
    4
  ),
(
    'a3363e61-6759-4674-90ba-cce4c16217f5',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify that warning labels are attached and visible.',
    false,
    5
  ),
(
    '396e5f29-eaef-40ba-a2ad-40a3455e4791',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify tightness of all control connections.',
    false,
    6
  ),
(
    '49652eca-a06f-4b2e-8990-47f042c51ef1',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '8',
    'Inspect bolted electrical connections for high resistance using one or more of the following:',
    false,
    7
  ),
(
    '6d377021-0c79-4011-a4bc-7c694e324fa7',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '1',
    'Use of a low-resistance ohmmeter in accordance with Section 7.22.3.B.1.',
    false,
    8
  ),
(
    'f6e11572-4aca-41fc-b155-778f3fd58f1d',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '2',
    'Verify tightness of accessible bolted electrical connections by calibrated torque- wrench method in accordance with manufacturer’s published data or Table 100.12.',
    false,
    9
  ),
(
    '553e6074-f742-4b71-876b-bd4bfc9950e7',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '3',
    'Perform a thermographic survey in accordance with Section 9.',
    false,
    10
  ),
(
    '267a0192-000e-4790-9b79-d34b411422f0',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '9',
    'Perform manual transfer operation.',
    false,
    11
  ),
(
    '1519fd33-82d7-407e-a3ff-3709313bf4b6',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify positive mechanical interlocking between normal and alternate sources.',
    false,
    12
  ),
(
    'a2199ee6-41f6-45d5-9d18-cb64bb59b6f3',
    '8b780cec-6ab8-4878-9d33-04b1462ff86d',
    'visual_mechanical'::neta_test_type,
    '11',
    'Perform as-left tests. * Optional Page 202',
    false,
    13
  ),
(
    '4a467069-f046-4d5a-be9d-645ee42370f6',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '1',
    'Record model numbers, style numbers, serial numbers, firmware revisions, software revisions, and rated control voltage.',
    false,
    1
  ),
(
    'cf43a2db-7c69-4d41-bcce-dd5eb26d655a',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '2',
    'Inspect the physical and mechanical condition of equipment and wiring.',
    false,
    2
  ),
(
    'fd79361a-f49d-4588-9a79-16097b5f9540',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '3',
    'Verify operation of light-emitting diodes, displays, and targets.',
    false,
    3
  ),
(
    '137bf5d4-a417-4877-adaf-ecd6969a6c6f',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '4',
    'Verify equipment is clean.',
    false,
    4
  ),
(
    '3a50dd07-cd01-4930-853f-9f8879943d81',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '5',
    'Check tightness of all connections.',
    false,
    5
  ),
(
    '1e8b30bf-d43f-4469-acc0-27cb358644e1',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '6',
    'Verify appropriate grounding equipment and circuits.',
    false,
    6
  ),
(
    '6d79577d-dc8c-4110-9787-1afd188006c1',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '7',
    'Verify backup batteries are healthy and connected.',
    false,
    7
  ),
(
    '13d55201-ee95-4243-85ef-08786e6301de',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '8',
    'Check with setting engineer for applicable firmware updates and product recalls.',
    false,
    8
  ),
(
    '499cfc5e-de06-4b46-93a4-5fa5c4b91925',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '9',
    'Verify settings and application configurations are in accordance with engineered settings.',
    false,
    9
  ),
(
    '96730259-d93b-43f6-815a-052b55ef65d0',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '10',
    'Verify devices display the correct date and time.',
    false,
    10
  ),
(
    '0f265e3f-062f-472f-893e-9b0867fac419',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '11',
    'Reset and clear events, maintenance data, statistical data, and alarms from the devices after any tests.',
    false,
    11
  ),
(
    'f0ebbc6e-55e4-46bf-8a52-df6957bbbfa4',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'visual_mechanical'::neta_test_type,
    '12',
    'Download or document settings and logic from the devices.',
    false,
    12
  ),
(
    'be462b3e-2cd6-4fe0-9be3-ba26c38bc448',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'electrical'::neta_test_type,
    '1',
    'Perform metering tests on all analog inputs and verify metering values on the human machine interface (HMI) and at remote terminals.',
    false,
    13
  ),
(
    '6c4cb286-acd6-4aad-8374-009f0d72d8de',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'electrical'::neta_test_type,
    '2',
    'Verify operation of all enabled digital inputs.',
    false,
    14
  ),
(
    '157c0813-2b69-49bf-b69c-0627e2c37d8a',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'electrical'::neta_test_type,
    '3',
    'Verify operation of all digital outputs by operating the controlled device.',
    false,
    15
  ),
(
    '1d372960-aff1-47f7-84fb-a4fa518e2f8c',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'electrical'::neta_test_type,
    '4',
    'Verify all communication links are operational and function test failovers of redundant communication links.',
    false,
    16
  ),
(
    '9056e9bc-d511-4a7f-9f9f-39fa21bff9a2',
    'd5acd81c-caa9-4dd5-b996-dabe9b2f6688',
    'electrical'::neta_test_type,
    '5',
    'Verify operation of all internal logic functions including tagging, lockouts, and local/remote control. * Optional Page 206',
    false,
    17
  );

COMMIT;