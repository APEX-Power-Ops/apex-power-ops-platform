# NETA Import Task - Handoff to VS Code Claude

## Current Status
- **33 ATS procedures** inserted into `neta_procedures` table ✅
- **153 test items** inserted into `neta_test_items` table (9 procedures populated)
- **24 procedures** still need test items populated

## What Desktop Claude Completed
1. Inserted all ATS-2025 procedures from JSON
2. Populated test items for these sections:
   - 7.1.1 Switchgear (16 tests) ✅
   - 7.1.2 Panelboard (14 tests) ✅
   - 7.6.3 Circuit Breakers, Vacuum (16 tests) ✅
   - 7.9.2 Protective Relays, Microprocessor (16 tests) ✅
   - 7.10.1 Current Transformers (15 tests) ✅

## What VS Code Claude Completed (Dec 11)
3. Populated test items for priority sections:
   - 7.2.2 Transformers, Liquid-Filled (19 V/M tests) ✅
   - 7.3.1 Cables, Low-Voltage (8 V/M + 3 electrical = 11 tests) ✅
   - 7.6.4 Circuit Breakers, SF6 (18 V/M + 13 electrical = 31 tests) ✅
   - 7.22.3 Automatic Transfer Switches (11 V/M + 4 electrical = 15 tests) ✅

## Summary by Section (9 of 33 complete)

| Section | Title | V/M | Elec | Total | Status |
|---------|-------|-----|------|-------|--------|
| 7.1.1 | Switchgear | 16 | 0 | 16 | ✅ |
| 7.1.2 | Panelboard | 12 | 2 | 14 | ✅ |
| 7.2.2 | Transformers | 19 | 0 | 19 | ✅ |
| 7.3.1 | Cables LV | 8 | 3 | 11 | ✅ |
| 7.6.3 | CB Vacuum | 16 | 0 | 16 | ✅ |
| 7.6.4 | CB SF6 | 18 | 13 | 31 | ✅ |
| 7.9.2 | Relays Micro | 11 | 5 | 16 | ✅ |
| 7.10.1 | CT | 9 | 6 | 15 | ✅ |
| 7.22.3 | ATS | 11 | 4 | 15 | ✅ |
| **TOTAL** | | **120** | **33** | **153** | |

## Task for VS Code Claude

### Option A: Direct Supabase SQL (Recommended)
Use the Supabase MCP tool to execute INSERT statements directly.

### Option B: Generate SQL File
Create SQL file at: `C:\RESA_Power_Build\Supabase\data\21_neta_test_items.sql`

## Source Data Location
```
C:\RESA_Power_Build\Reference_Files\NETA\Extracted\ANSI_NETA_ATS-2025_Final_v2.json
```

## Procedure ID Mapping (ATS-2025)
Use this mapping to link test items to procedures:

| Section | Procedure UUID | Title |
|---------|----------------|-------|
| 7.1.1 | 40317781-87a0-41f2-97a4-e232b9b92c7f | Switchgear ✅ |
| 7.1.2 | c6ea7cfa-98fb-46a4-8ba2-772f07f8eb92 | Panelboard ✅ |
| 7.2.2 | 5984049f-d80f-42c1-979f-d42d24392122 | Transformers, Liquid-Filled |
| 7.3.1 | 9688fbb4-ba49-4b63-bf55-bcca842aa07e | Cables, Low-Voltage |
| 7.3.3 | 06adef51-e5ef-4253-a361-7c6a5178ae89 | Shielded Cables, MV/HV |
| 7.5.2 | c1441000-62b8-4aa8-999e-bb24986223d2 | Switches, Oil, MV |
| 7.5.3 | 844494d2-2fc2-4c67-bd77-34ee3528f804 | Switches, Vacuum, MV |
| 7.5.5 | 62e24d1c-21cb-406f-8b77-ad374bd5838a | Switches, Cutouts |
| 7.6.2 | c958d767-0998-4358-8832-d19ea14b212f | CB Oil, MV/HV |
| 7.6.3 | 397255e6-b06d-469f-82a4-112fe42ea897 | CB Vacuum, MV ✅ |
| 7.6.4 | 135f1522-6990-4e50-8b29-beb6f8d73916 | CB SF6 |
| 7.9.1 | 3d2d5569-04bf-4d8c-b6ab-e3b84195c73b | Relays, Electromechanical |
| 7.9.2 | 1a876284-e1b9-4169-92d5-e572537c4cee | Relays, Microprocessor ✅ |
| 7.10.1 | c7891833-138a-47a1-93fc-2434de376789 | CT ✅ |
| 7.10.2 | 36bc3ad7-bdf5-4d31-b448-260577389194 | VT |
| 7.10.3 | 65046863-a2c3-4d6e-99a7-298c2ec0e1ec | CCVT |
| 7.11.1 | e58afefd-3fae-4f62-84b9-283b028f6b51 | Metering, Electromechanical |
| 7.11.2 | 54001b07-9834-4f51-a28b-e86c8341246f | Metering, Microprocessor |
| 7.12.3 | eb86dafa-a4f3-47a1-a5b9-979d38ba74de | Load Tap-Changers |
| 7.15.1 | 468604ef-8434-45a8-a7a5-9ea1d883a0a4 | AC Induction Motors |
| 7.15.2 | 2ec10f5a-bd54-4d04-b6c6-bb5a8c31922a | Synchronous Motors |
| 7.15.3 | 659137cb-2841-4476-9878-8efb41dc4679 | DC Motors |
| 7.18.2 | 3c6d8e18-145d-4bd1-95a1-92421c529aa8 | DC Chargers |
| 7.19.1 | 7f8f5d8c-0874-4d38-b66e-57af04d1fd02 | Surge Protective, LV |
| 7.19.2 | c97c872d-22d8-4457-91cc-8a5db2caf4d3 | Surge Arresters, MV/HV |
| 7.20.1 | 6998ab50-7782-4685-90eb-9b264fb8017b | Capacitors |
| 7.20.2 | 1e242616-335e-4c0b-a6dc-b1195abbf58b | Capacitor Control |
| 7.20.4 | 7e018561-44f8-4fd9-8d71-9d5fd8a9eb61 | Resistors |
| 7.22.1 | 54863422-07e4-40f2-bb62-cfdc7c0ae4b1 | Engine Generator |
| 7.22.2 | 907d9df2-2f43-4096-9de4-bc86d2eca209 | UPS Systems |
| 7.22.3 | 3fda70a7-2a9a-4c54-809f-1407c540b2c3 | ATS |
| 7.24.1 | d8f70e3a-34b0-4341-bf41-cd69afc7b883 | Reclosers, Oil/Vacuum |
| 7.24.2 | 4e245e25-37be-45a5-9389-69f083b8183d | Line Sectionalizers |

## SQL Template for Test Items
```sql
INSERT INTO neta_test_items (procedure_id, test_type, test_number, description, is_optional, sort_order)
VALUES
  ('PROCEDURE_UUID', 'visual_mechanical', '1', 'Test description here', false, 1),
  ('PROCEDURE_UUID', 'electrical', '1', 'Test description here', false, 10);
```

## JSON Structure Reference
```json
{
  "sections": {
    "7.2.2": {
      "visual_mechanical_tests": [
        {"number": "1", "description": "...", "optional": false}
      ],
      "electrical_tests": [
        {"number": "1", "description": "...", "optional": false}
      ]
    }
  }
}
```

## Priority Sections to Complete
1. **7.2.2** - Transformers (19 V/M tests) - MOST COMMON
2. **7.6.4** - SF6 Breakers (18 V/M + 13 electrical)
3. **7.22.3** - ATS (11 V/M + 4 electrical)
4. **7.3.1** - Cables LV (8 V/M + 3 electrical)

## Verification Query
```sql
SELECT 
  p.section_number,
  p.title,
  COUNT(ti.id) as test_count
FROM neta_procedures p
LEFT JOIN neta_test_items ti ON p.id = ti.procedure_id
WHERE p.standard_type = 'ATS'
GROUP BY p.id, p.section_number, p.title, p.sort_order
ORDER BY p.sort_order;
```

## After ATS Complete
Import remaining standards:
- MTS-2023: `ANSI_NETA_MTS-2023_FINAL_v2.json`
- ECS-2024: `ANSI_NETA_ECS-2024_v2.json`
- ETT-2022: `ANSI_NETA_ETT-2022_FINAL_v2.json`

---
*Created by Desktop Claude - 2025-12-11*
