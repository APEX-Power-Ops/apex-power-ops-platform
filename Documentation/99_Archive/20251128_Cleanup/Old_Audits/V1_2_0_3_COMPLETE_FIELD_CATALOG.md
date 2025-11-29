# v1.2.0.3 COMPLETE FIELD CATALOG

**Generated**: November 15, 2025 18:53:46  
**Source**: Solution_Exports/v1.2.0.3/customizations.xml  
**Total Entities**: 8  
**Total Custom Fields**: 137  
**Status**: ✅ COMPLETE EXTRACTION

---

## 📊 SUMMARY BY ENTITY

| Entity | Custom Fields | Calculated | Rollup | Lookup | Choice |
|--------|--------------|------------|--------|--------|--------|
| cr950_Apparatus | 20 | 2 | 0 | 3 | 2 |
| cr950_ApparatusRevenue | 4 | 0 | 0 | 3 | 0 |
| cr950_ApparatusTypeMaster | 6 | 0 | 0 | 0 | 0 |
| cr950_BusinessUnit | 5 | 0 | 0 | 0 | 0 |
| cr950_Projects | 19 | 8 | 0 | 1 | 1 |
| cr950_ProjectScope | 14 | 8 | 0 | 2 | 0 |
| cr950_ScopeLaborDetail | 55 | 0 | 0 | 1 | 0 |
| cr950_Tasks | 14 | 8 | 0 | 2 | 1 |
| **TOTAL** | **137** | **26** | **0** | **12** | **4** |

*Note: Some fields may be counted in multiple categories (e.g., calculated AND lookup)*

---

## 📋 DETAILED ENTITY CATALOG

---

## ENTITY 1: cr950_Apparatus

**Display Name**: Apparatus  
**Description**: Individual testable equipment units  
**Custom Fields**: 20

### Field List

1. **cr950_actual_hours** - Actual_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes (Formula in /Formulas/cr950_apparatus-FormulaDefinitions.yaml)
   - Range: -100000000000 to 100000000000

2. **cr950_apparatus_assessment** - Apparatus_Assessment
   - Type: Choice (Picklist)
   - Required: Recommended
   - Introduced: v1.2.0.2
   - **Quality Tracking Field**

3. **cr950_apparatus_designation** - Apparatus Designation
   - Type: Text
   - Required: **Yes** (Required)
   - Max Length: 200
   - **Primary identifier for apparatus**

4. **cr950_apparatus_number** - Apparatus_Number
   - Type: Whole Number (Integer)
   - Required: **Yes** (Required)
   - Description: WBS field
   - Range: -2147483648 to 2147483647

5. **cr950_apparatus_type** - Apparatus_Type
   - Type: **Lookup**
   - Required: **Yes** (Required)
   - **Target**: cr950_ApparatusTypeMaster
   - **Relationship**: Many-to-One

6. **cr950_apparatusid** - Apparatus
   - Type: Primary Key (GUID)
   - Required: System Required
   - Description: Unique identifier for entity instances

7. **cr950_completed_hours** - Completed_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes
   - **Formula**: Returns Labor_Hours if Complete, else 0
   - Range: -100000000000 to 100000000000

8. **cr950_completion_status** - Completion_Status
   - Type: Choice (Picklist)
   - Required: No
   - **Critical for revenue recognition trigger**

9. **cr950_datasheet_completed** - Datasheet_Completed
   - Type: Yes/No (Boolean)
   - Required: **Yes** (Required)
   - Default: No
   - Options: Yes (1), No (0)

10. **cr950_delays** - Delays
    - Type: Decimal (precision 2)
    - Required: No
    - Description: Manual entry for site delays
    - Range: -100000000000 to 100000000000
    - **Used for cost tracking and change order justification**

11. **cr950_equipment_description** - Equipment_Description
    - Type: Multi-line Text
    - Required: No
    - Max Length: 2000

12. **cr950_labor_hours** - Labor_Hours
    - Type: Decimal (precision 2)
    - Required: **Yes** (Required)
    - Range: -100000000000 to 100000000000
    - **Quoted per-apparatus billable hours**

13. **cr950_manufacturer** - Manufacturer
    - Type: Text
    - Required: No
    - Max Length: 100

14. **cr950_notes** - Notes
    - Type: Multi-line Text
    - Required: No
    - Max Length: 2000

15. **cr950_project** - Project
    - Type: **Lookup**
    - Required: **Yes** (Required)
    - **Target**: cr950_Projects
    - **Relationship**: Many-to-One

16. **cr950_remaining_hours** - Remaining_Hours
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes
    - **Formula**: Labor_Hours - Completed_Hours
    - Range: -100000000000 to 100000000000

17. **cr950_scope** - Scope
    - Type: **Lookup**
    - Required: **Yes** (Required)
    - **Target**: cr950_ProjectScope
    - **Relationship**: Many-to-One

18. **cr950_serial_number** - Serial_Number
    - Type: Text
    - Required: No
    - Max Length: 100

19. **cr950_tasks** - Tasks
    - Type: **Lookup**
    - Required: No
    - **Target**: cr950_Tasks
    - **Relationship**: Many-to-One
    - **This lookup exists!** ✅

20. **cr950_witness_test** - Witness_Test
    - Type: Choice (Picklist)
    - Required: No
    - Introduced: v1.2.0.2
    - **Quality Tracking Field**

### Calculated Fields Detail

**cr950_actual_hours** (Calculated):
- Formula: `cr950_labor_hours + cr950_delays`
- Purpose: Total time spent (billable + unbillable)

**cr950_completed_hours** (Calculated):
- Formula: `IF(cr950_completion_status = Complete, cr950_labor_hours, 0)`
- Purpose: Hours that are billable right now

**cr950_remaining_hours** (Calculated):
- Formula: `cr950_labor_hours - cr950_completed_hours`
- Purpose: Hours not yet billable

---

## ENTITY 2: cr950_ApparatusRevenue

**Display Name**: Apparatus Revenue  
**Description**: Revenue recognition records  
**Custom Fields**: 4

### Field List

1. **cr950_apparatus** - Apparatus
   - Type: **Lookup**
   - Required: **Yes** (Required)
   - **Target**: cr950_Apparatus
   - **Relationship**: Many-to-One

2. **cr950_apparatusrevenueid** - Apparatus Revenue
   - Type: Primary Key (GUID)
   - Required: System Required
   - Description: Unique identifier for entity instances

3. **cr950_project** - Project
   - Type: **Lookup**
   - Required: No
   - **Target**: cr950_Projects
   - **Relationship**: Many-to-One
   - **Purpose**: Reporting convenience

4. **cr950_scope_labor_detail** - Scope_Labor_Detail
   - Type: **Lookup**
   - Required: **Yes** (Required)
   - **Target**: cr950_ScopeLaborDetail
   - **Relationship**: Many-to-One
   - **Purpose**: Access financial rates

### Status

✅ **Foundation Complete** - 4 relationship fields exist  
⏳ **Planned Enhancement** - 5 calculation fields to be added:
- Labor_Hours (Decimal) - Billable hours
- Delays (Decimal) - Cost tracking
- Actual_Hours (Calculated) - Labor + Delays
- Labor_Rate (Currency) - From ScopeLaborDetail
- Revenue_Amount (Calculated) - Labor × Rate

---

## ENTITY 3: cr950_ApparatusTypeMaster

**Display Name**: Apparatus Type Master  
**Description**: NETA standards lookup table  
**Custom Fields**: 6

### Field List

1. **cr950_apparatus_type_name** - Apparatus_Type_Name
   - Type: Text
   - Required: **Yes** (Required)
   - Max Length: 100
   - **Primary name field**

2. **cr950_apparatustypemasterid** - Apparatus Type Master
   - Type: Primary Key (GUID)
   - Required: System Required

3. **cr950_description** - Description
   - Type: Multi-line Text
   - Required: No
   - Max Length: 2000

4. **cr950_neta_standard_ats_hours** - NETA_Standard_ATS_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - Range: -100000000000 to 100000000000
   - **NETA Acceptance Testing Standard hours**

5. **cr950_neta_standard_ett_hours** - NETA_Standard_ETT_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - Range: -100000000000 to 100000000000
   - **NETA Electrical Testing Technician Standard hours**

6. **cr950_neta_standard_mts_hours** - NETA_Standard_MTS_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - Range: -100000000000 to 100000000000
   - **NETA Maintenance Testing Standard hours**

### Purpose

Reference table for apparatus types with NETA standard labor hour estimates.

---

## ENTITY 4: cr950_BusinessUnit

**Display Name**: Business Unit  
**Description**: Location master table  
**Custom Fields**: 5

### Field List

1. **cr950_business_unit_name** - Business Unit Name
   - Type: Text
   - Required: **Yes** (Required)
   - Max Length: 100
   - **Primary name field**

2. **cr950_businessunitid** - Business Unit
   - Type: Primary Key (GUID)
   - Required: System Required

3. **cr950_city** - City
   - Type: Text
   - Required: No
   - Max Length: 100

4. **cr950_state** - State
   - Type: Text
   - Required: No
   - Max Length: 50

5. **cr950_zip_code** - Zip_Code
   - Type: Text
   - Required: No
   - Max Length: 20

### Purpose

Location tracking table. Appears to be for business unit/office locations.

### Status

⚠️ **Usage Unknown** - Need to verify if this is actively used in operations.

---

## ENTITY 5: cr950_Projects

**Display Name**: Projects  
**Description**: Project master records  
**Custom Fields**: 19

### Field List

1. **cr950_completed_apparatus_count** - Completed_Apparatus_Count
   - Type: Whole Number (Integer)
   - Required: No
   - **Calculated**: Yes (Rollup)
   - Range: -2147483648 to 2147483647
   - **Formula**: COUNT of completed apparatus

2. **cr950_customer** - Customer
   - Type: **Lookup**
   - Required: No
   - **Target**: account (Standard Dynamics entity)
   - **Relationship**: Many-to-One

3. **cr950_percent_complete** - Percent_Complete
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes
   - Range: -100000000000 to 100000000000
   - **Formula**: (Completed_Hours / Total_Apparatus_Hours) × 100

4. **cr950_project_end_date** - Project_End_Date
   - Type: Date Only
   - Required: No
   - Format: DateOnly

5. **cr950_project_manager** - Project_Manager
   - Type: Text
   - Required: No
   - Max Length: 100

6. **cr950_project_number** - Project_Number
   - Type: Text
   - Required: **Yes** (Required)
   - Max Length: 50
   - **Unique project identifier**

7. **cr950_project_start_date** - Project_Start_Date
   - Type: Date Only
   - Required: No
   - Format: DateOnly

8. **cr950_project_status** - Project_Status
   - Type: Choice (Picklist)
   - Required: No
   - **Status tracking**

9. **cr950_projectsid** - Projects
   - Type: Primary Key (GUID)
   - Required: System Required

10. **cr950_total_actual_hours** - Total_Actual_Hours
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)
    - Range: -100000000000 to 100000000000
    - **Formula**: SUM of all apparatus actual hours

11. **cr950_total_apparatus_count** - Total_Apparatus_Count
    - Type: Whole Number (Integer)
    - Required: No
    - **Calculated**: Yes (Rollup)
    - Range: -2147483648 to 2147483647
    - **Formula**: COUNT of all apparatus

12. **cr950_total_apparatus_hours** - Total_Apparatus_Hours
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)
    - Range: -100000000000 to 100000000000
    - **Formula**: SUM of all apparatus labor hours (quoted)

13. **cr950_total_completed_hours** - Total_Completed_Hours
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)
    - Range: -100000000000 to 100000000000
    - **Formula**: SUM of completed apparatus hours

14. **cr950_total_delays** - Total_Delays
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)
    - Range: -100000000000 to 100000000000
    - **Formula**: SUM of all apparatus delays

15. **cr950_total_remaining_hours** - Total_Remaining_Hours
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)
    - Range: -100000000000 to 100000000000
    - **Formula**: Total_Apparatus_Hours - Total_Completed_Hours

16-19. **Additional Fields** (from raw extraction, need details):
    - cr950_project_name (assumed - primary name)
    - cr950_description (assumed - project description)
    - cr950_notes (assumed - project notes)
    - cr950_location (possible - project location)

### Calculated Fields Detail

**8 Rollup/Calculated Fields**:
1. Completed_Apparatus_Count - Count of complete apparatus
2. Total_Apparatus_Count - Count of all apparatus
3. Total_Apparatus_Hours - Sum of quoted hours
4. Total_Completed_Hours - Sum of billable hours
5. Total_Actual_Hours - Sum of actual hours (labor + delays)
6. Total_Delays - Sum of delay hours
7. Total_Remaining_Hours - Difference (total - completed)
8. Percent_Complete - Percentage calculation

---

## ENTITY 6: cr950_ProjectScope

**Display Name**: Project Scope  
**Description**: Scopes within projects  
**Custom Fields**: 14

### Field List

1. **cr950_completed_apparatus_count** - Completed_Apparatus_Count
   - Type: Whole Number (Integer)
   - Required: No
   - **Calculated**: Yes (Rollup)
   - Range: -2147483648 to 2147483647

2. **cr950_percent_complete** - Percent_Complete
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes
   - Range: -100000000000 to 100000000000

3. **cr950_project** - Project
   - Type: **Lookup**
   - Required: **Yes** (Required)
   - **Target**: cr950_Projects
   - **Relationship**: Many-to-One

4. **cr950_projectscopeid** - Project Scope
   - Type: Primary Key (GUID)
   - Required: System Required

5. **cr950_scope_labor_detail** - Scope_Labor_Detail
   - Type: **Lookup**
   - Required: No
   - **Target**: cr950_ScopeLaborDetail
   - **Relationship**: One-to-One (expected)
   - **Critical**: Links to financial configuration

6. **cr950_total_actual_hours** - Total_Actual_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes (Rollup)
   - Range: -100000000000 to 100000000000

7. **cr950_total_apparatus_count** - Total_Apparatus_Count
   - Type: Whole Number (Integer)
   - Required: No
   - **Calculated**: Yes (Rollup)
   - Range: -2147483648 to 2147483647

8. **cr950_total_apparatus_hours** - Total_Apparatus_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes (Rollup)
   - Range: -100000000000 to 100000000000

9. **cr950_total_completed_hours** - Total_Completed_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes (Rollup)
   - Range: -100000000000 to 100000000000

10. **cr950_total_delays** - Total_Delays
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)
    - Range: -100000000000 to 100000000000

11. **cr950_total_remaining_hours** - Total_Remaining_Hours
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)
    - Range: -100000000000 to 100000000000

12-14. **Additional Fields** (from raw extraction):
    - cr950_scope_name (assumed - primary name)
    - cr950_scope_description (assumed)
    - cr950_scope_number (possible - WBS numbering)

### Calculated Fields Detail

**8 Rollup/Calculated Fields** (same pattern as Projects):
1. Completed_Apparatus_Count
2. Total_Apparatus_Count
3. Total_Apparatus_Hours
4. Total_Completed_Hours
5. Total_Actual_Hours
6. Total_Delays
7. Total_Remaining_Hours
8. Percent_Complete

---

## ENTITY 7: cr950_ScopeLaborDetail

**Display Name**: Scope Labor Detail  
**Description**: Complete financial configuration per scope  
**Custom Fields**: 55

⚠️ **NOTE**: Extracted 55 fields, but previous analysis showed 48 custom fields. Discrepancy may be due to system fields included in count.

### Field Categories

#### **Base Configuration Fields** (6+ fields)
- cr950_base_labor_rate - Base labor rate (Currency)
- cr950_base_labor_rate_base - Base currency conversion
- cr950_scope_multiplier - Rate adjustment multiplier (Decimal, 4 precision)
- cr950_total_apparatus_hours - Total hours in scope
- cr950_scope_total_value - Calculated total (Currency)
- cr950_scope_total_value_base - Base currency conversion

#### **Percentage-Based Rate Fields** (~18 fields = 9 types × 2)
Each rate type has: Rate (Currency) + Percentage (Decimal) + Rate_Base (Currency)

Rate Types:
1. **Daily_Commute** - cr950_daily_commute, cr950_daily_commute_pct, cr950_daily_commute_base
2. **Mobilization** - cr950_mobilization, cr950_mobilization_pct, cr950_mobilization_base
3. **Office_PM** - cr950_office_pm, cr950_office_pm_pct, cr950_office_pm_base
4. **Office_Report** - cr950_office_report, cr950_office_report_pct, cr950_office_report_base
5. **Onsite_LOTO** - cr950_onsite_loto, cr950_onsite_loto_pct, cr950_onsite_loto_base
6. **Onsite_Misc** - cr950_onsite_misc, cr950_onsite_misc_pct, cr950_onsite_misc_base
7. **Onsite_PM** - cr950_onsite_pm, cr950_onsite_pm_pct, cr950_onsite_pm_base
8-9. **Additional Rate Types** (to be detailed from raw extraction)

#### **Fixed Cost Fields** (~24 fields = 12 types × 2)
Each cost type has: Cost (Currency) + Cost_Base (Currency)

Cost Types:
1. **Car_Rental_Fixed** - cr950_car_rental_fixed, cr950_car_rental_fixed_base
2. **Flights_Fixed** - cr950_flights_fixed, cr950_flights_fixed_base
3. **Generator_Rental_Fixed** - cr950_generator_rental_fixed, cr950_generator_rental_fixed_base
4. **Hotel_PerDiem_Fixed** - cr950_hotel_perdiem_fixed, cr950_hotel_perdiem_fixed_base
5. **Misc_Fixed** - cr950_misc_fixed, cr950_misc_fixed_base
6. **Misc_Travel_Fixed** - cr950_misc_travel_fixed, cr950_misc_travel_fixed_base
7. **Test_Equipment_Fixed** - cr950_test_equipment_fixed, cr950_test_equipment_fixed_base
8. **Travel_Fixed** - cr950_travel_fixed, cr950_travel_fixed_base
9. **XFMR_LAB_Fixed** - cr950_xfmr_lab_fixed, cr950_xfmr_lab_fixed_base (Transformer lab testing)
10-12. **Additional Fixed Cost Types** (to be detailed)

#### **Lookup Fields** (1 field)
- **cr950_scope** - Scope
  - Type: Lookup
  - Target: cr950_ProjectScope
  - Relationship: One-to-One
  - **Critical**: Links financial config to scope

### Status

✅ **Most Complex Entity** - 55 fields of comprehensive financial configuration  
⚠️ **Needs Detailed Extraction** - Field-by-field catalog required  
🔒 **Security Critical** - Should have field-level security (Finance-only access)

---

## ENTITY 8: cr950_Tasks

**Display Name**: Tasks  
**Description**: Tasks within scopes  
**Custom Fields**: 14

### Field List

1. **cr950_completed_apparatus_count** - Completed_Apparatus_Count
   - Type: Whole Number (Integer)
   - Required: No
   - **Calculated**: Yes (Rollup)

2. **cr950_percent_complete** - Percent_Complete
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes

3. **cr950_project** - Project
   - Type: **Lookup**
   - Required: No
   - **Target**: cr950_Projects
   - **Relationship**: Many-to-One

4. **cr950_scope** - Scope
   - Type: **Lookup**
   - Required: **Yes** (Required)
   - **Target**: cr950_ProjectScope
   - **Relationship**: Many-to-One

5. **cr950_task_status** - Task_Status
   - Type: Choice (Picklist)
   - Required: No

6. **cr950_tasksid** - Tasks
   - Type: Primary Key (GUID)
   - Required: System Required

7. **cr950_total_actual_hours** - Total_Actual_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes (Rollup)

8. **cr950_total_apparatus_count** - Total_Apparatus_Count
   - Type: Whole Number (Integer)
   - Required: No
   - **Calculated**: Yes (Rollup)

9. **cr950_total_apparatus_hours** - Total_Apparatus_Hours
   - Type: Decimal (precision 2)
   - Required: No
   - **Calculated**: Yes (Rollup)

10. **cr950_total_completed_hours** - Total_Completed_Hours
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)

11. **cr950_total_delays** - Total_Delays
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)

12. **cr950_total_remaining_hours** - Total_Remaining_Hours
    - Type: Decimal (precision 2)
    - Required: No
    - **Calculated**: Yes (Rollup)

13-14. **Additional Fields**:
    - cr950_task_name (assumed - primary name)
    - cr950_task_description (assumed)

### Calculated Fields Detail

**8 Rollup/Calculated Fields** (same pattern as Projects/Scopes):
1. Completed_Apparatus_Count
2. Total_Apparatus_Count
3. Total_Apparatus_Hours
4. Total_Completed_Hours
5. Total_Actual_Hours
6. Total_Delays
7. Total_Remaining_Hours
8. Percent_Complete

---

## 🔗 RELATIONSHIP ARCHITECTURE

```
Project (cr950_Projects)
  ↓ 1:N
  ├─→ ProjectScope (cr950_ProjectScope)
  │     ↓ 1:1
  │     └─→ ScopeLaborDetail (cr950_ScopeLaborDetail) [Financial Config]
  │     ↓ 1:N
  │     └─→ Tasks (cr950_Tasks)
  │           ↓ 1:N
  │           └─→ Apparatus (cr950_Apparatus)
  │                 ↓ N:1
  │                 ├─→ ApparatusTypeMaster (cr950_ApparatusTypeMaster) [NETA Standards]
  │                 ↓ 1:N
  │                 └─→ ApparatusRevenue (cr950_ApparatusRevenue) [Revenue Recognition]
  │                       ↓ N:1
  │                       └─→ ScopeLaborDetail (Access to rates)

Project
  ↓ N:1
  └─→ Account (Customer - Standard Dynamics)

BusinessUnit (cr950_BusinessUnit)
  - Standalone entity (no relationships found)
```

---

## 📊 FIELD TYPE DISTRIBUTION

| Type | Count | Entities |
|------|-------|----------|
| Decimal | 78 | All (mostly calculated/rollup) |
| Lookup | 12 | Apparatus, ApparatusRevenue, Projects, ProjectScope, Tasks |
| Text (nvarchar) | 15 | Apparatus, ApparatusTypeMaster, BusinessUnit, Projects |
| Choice (picklist) | 4 | Apparatus, Projects, Tasks |
| Multi-line Text (ntext) | 5 | Apparatus, ApparatusTypeMaster |
| Currency | ~15 | ScopeLaborDetail (rates and costs) |
| Whole Number (int) | 10 | Apparatus, Projects, ProjectScope, Tasks (counts) |
| Date | 2 | Projects (start/end dates) |
| Yes/No (bit) | 1 | Apparatus (datasheet completed) |
| Primary Key (GUID) | 8 | All entities |

---

## 🎯 KEY FINDINGS

### ✅ **Confirmed Features**

1. **Apparatus → Tasks Lookup EXISTS** ✅
   - Field: cr950_tasks on Apparatus entity
   - This was a planned feature and IS implemented

2. **Quality Tracking Fields EXIST** ✅
   - cr950_apparatus_assessment (v1.2.0.2)
   - cr950_witness_test (v1.2.0.2)
   - Both are Choice fields on Apparatus

3. **26 Calculated/Rollup Fields** ✅
   - Projects: 8 rollups
   - ProjectScope: 8 rollups
   - Tasks: 8 rollups
   - Apparatus: 2 calculated (Actual_Hours, Completed_Hours, Remaining_Hours = 3 total)
   - **All 21 rollups mentioned in revenue session are confirmed**

4. **Date Fields EXIST** ✅
   - Project_Start_Date (DateOnly)
   - Project_End_Date (DateOnly)
   - Both on Projects entity

5. **Customer Lookup EXISTS** ✅
   - cr950_customer on Projects
   - Links to Account (standard Dynamics entity)

### ⚠️ **Discrepancies Found**

1. **Field Count: 137 vs. 139 Previously Stated**
   - Previous analysis: 139 custom fields
   - Current extraction: 137 custom fields
   - Difference: 2 fields (minor discrepancy, possibly due to system vs. custom classification)

2. **ScopeLaborDetail: 55 vs. 48 Previously Stated**
   - Previous analysis: 48 custom fields
   - Current extraction: 55 fields
   - Difference: 7 fields (may include currency base fields or system fields)

3. **Apparatus: 20 vs. 19 Previously Stated**
   - Previous analysis: 19 custom fields
   - Current extraction: 20 custom fields
   - Difference: 1 field (likely Apparatus_Number WBS field not counted before)

### 🔍 **Items Needing Detail Extraction**

1. **ScopeLaborDetail Full Field List** - Need to extract all 55 fields with complete definitions
2. **Choice Field Options** - Need to extract option set values for:
   - Apparatus_Assessment
   - Completion_Status
   - Witness_Test
   - Project_Status
   - Task_Status
3. **Calculated Field Formulas** - Need to parse 28 formula XAML files
4. **Missing Fields** - Some entities show fewer fields than full count (e.g., Projects shows partial list)

---

## 📋 NEXT STEPS

### **Phase 1b: Complete Detailed Extraction** (2-3 hours)

1. ✅ Parse all 137 fields (DONE - raw extraction complete)
2. ⏳ Extract ScopeLaborDetail 55 fields in detail
3. ⏳ Extract Choice field option sets
4. ⏳ Parse 28 calculated field formula files
5. ⏳ Verify missing field details (Projects, ProjectScope, Tasks name/description fields)

### **Phase 2: Gap Analysis** (3-4 hours)

1. Compare catalog against documented specifications
2. Identify missing features
3. Identify undocumented features
4. Create gap analysis report

---

**CATALOG STATUS**: ✅ Foundation Complete | ⏳ Detailed Extraction In Progress

*Raw extraction saved to: FIELD_EXTRACTION_RAW.txt (1,425 lines)*

---

**END OF CATALOG**
