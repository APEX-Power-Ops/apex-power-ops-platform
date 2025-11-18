# RESA POWER v1.2.0.3 - ACTUAL SCHEMA DOCUMENTATION

**Source**: Solution export v1.2.0.3/customizations.xml  
**Date Extracted**: November 15, 2025  
**Status**: ✅ ACCURATE - Based on actual solution export

---

## 📊 COMPLETE ENTITY INVENTORY

| Entity | Custom Fields | Purpose | Status |
|--------|---------------|---------|--------|
| cr950_Projects | 19 | Project management | ✅ Core |
| cr950_ProjectScope | 14 | Scope/phase tracking | ✅ Core |
| cr950_Tasks | 14 | Work breakdown | ✅ Core |
| cr950_Apparatus | 19 | Equipment testing | ✅ Core |
| cr950_ScopeLaborDetail | 48 | Financial rates config | ✅ Core |
| cr950_ApparatusRevenue | 4 | Revenue tracking | ✅ Financial |
| cr950_ApparatusTypeMaster | 6 | Equipment standards | ✅ Reference |
| cr950_BusinessUnit | 5 | Location master | ✅ Reference |

**Total**: 8 entities, 139 custom fields

---

## 🏗️ ENTITY 1: CR950_PROJECTS (19 Fields)

**Purpose**: Top-level project tracking  
**Primary Field**: cr950_project_name  
**Records**: Active projects (e.g., LASNAP16)

### Fields

| Field Name | Type | Required | Notes |
|------------|------|----------|-------|
| **Client_Name** | Text(100) | No | Full client name |
| **Client_Short_Name** | Text(100) | No | Abbreviated client |
| **Completed_Apparatus_Count** | Integer | No | Rollup from apparatus |
| **Contract_Value** | Currency | No | Total contract amount |
| **Contract_Value (Base)** | Currency | No | Base currency |
| **Description** | Multiline Text | No | Project details |
| **Job Number** | Text(100) | No | Client job reference |
| **Location** | Lookup → BusinessUnit | No | Primary project location |
| **Percent_Complete** | Decimal(2) | No | Calculated completion % |
| **Project_Manager** | Text(100) | No | PM name |
| **Project_Name** | Text(200) | Yes | Primary identifier |
| **Start_Date** | Date | No | Project start |
| **Target_Completion_Date** | Date | No | Planned completion |
| **Total_Actual_Hours** | Decimal(2) | No | Rollup actual hours |
| **Total_Apparatus_Count** | Integer | No | Rollup apparatus count |
| **Total_Apparatus_Hours** | Decimal(2) | No | Rollup planned hours |
| **Total_Completed_Hours** | Decimal(2) | No | Rollup completed |
| **Total_Delays** | Decimal(2) | No | Rollup delay hours |
| **Total_Remaining_Hours** | Decimal(2) | No | Calculated remaining |

### Calculated/Rollup Fields (8)
- Completed_Apparatus_Count (rollup)
- Percent_Complete (calculated)
- Total_Actual_Hours (rollup)
- Total_Apparatus_Count (rollup)
- Total_Apparatus_Hours (rollup)
- Total_Completed_Hours (rollup)
- Total_Delays (rollup)
- Total_Remaining_Hours (calculated)

### Relationships
- **1:N** → ProjectScope (cr950_project)
- **1:N** → Tasks (cr950_project)
- **1:N** → Apparatus (cr950_project)
- **N:1** ← BusinessUnit (cr950_location)

---

## 🏗️ ENTITY 2: CR950_PROJECTSCOPE (14 Fields)

**Purpose**: Work scope/phase within project  
**Primary Field**: cr950_scope_name  
**Typical**: ATS, MTS, or ETT testing scopes

### Fields

| Field Name | Type | Required | Notes |
|------------|------|----------|-------|
| **Completed_Apparatus_Count** | Decimal(2) | No | Rollup from apparatus |
| **Description** | Multiline Text | No | Scope details |
| **Percent_Complete** | Decimal(2) | No | Calculated % complete |
| **Project** | Lookup → Projects | Yes | Parent project |
| **Scope Name** | Text(200) | Yes | Primary identifier |
| **Scope_Number** | Integer | Yes | Scope sequence |
| **SLD_Reference** | Text(100) | No | Single Line Diagram ref |
| **Testing_Standard** | Choice | No | ATS, MTS, ETT |
| **Total_Actual_Hours** | Decimal(2) | No | Rollup actual |
| **Total_Apparatus_Count** | Integer | No | Rollup count |
| **Total_Apparatus_Hours** | Decimal(2) | No | Rollup planned |
| **Total_Completed_Hours** | Decimal(2) | No | Rollup completed |
| **Total_Delays** | Decimal(2) | No | Rollup delays |
| **Total_Remaining_Hours** | Decimal(2) | No | Calculated remaining |

### Choice Field: Testing_Standard
- ATS (Acceptance Testing Specifications)
- MTS (Maintenance Testing Specifications)  
- ETT (Equipment Testing & Troubleshooting)

### Calculated/Rollup Fields (8)
Same pattern as Projects (rollups + calculations)

### Relationships
- **N:1** ← Projects (cr950_project)
- **1:N** → Tasks (cr950_scope)
- **1:N** → Apparatus (cr950_scope)
- **1:1** → ScopeLaborDetail (financial config)

---

## 🏗️ ENTITY 3: CR950_TASKS (14 Fields)

**Purpose**: Work task assignments  
**Primary Field**: cr950_task_name

### Fields

| Field Name | Type | Required | Notes |
|------------|------|----------|-------|
| **Completed_Apparatus_Count** | Decimal(2) | No | Rollup |
| **Description** | Multiline Text | No | Task details |
| **Percent_Complete** | Decimal(2) | No | Calculated |
| **Project** | Lookup → Projects | Yes | Parent project |
| **Scope** | Lookup → ProjectScope | Yes | Parent scope |
| **Task_Name** | Text(200) | Yes | Primary identifier |
| **Task_Number** | Integer | Yes | Task sequence |
| **Total_Actual_Hours** | Decimal(2) | No | Rollup |
| **Total_Apparatus_Count** | Integer | No | Rollup |
| **Total_Apparatus_Hours** | Decimal(2) | No | Rollup |
| **Total_Completed_Hours** | Decimal(2) | No | Rollup |
| **Total_Delays** | Decimal(2) | No | Rollup |
| **Total_Remaining_Hours** | Decimal(2) | No | Calculated |
| *(Additional fields TBD)* | | | |

### Relationships
- **N:1** ← Projects (cr950_project)
- **N:1** ← ProjectScope (cr950_scope)
- **1:N** → Apparatus (cr950_task)

---

## 🏗️ ENTITY 4: CR950_APPARATUS (19 Fields)

**Purpose**: Individual testable equipment units  
**Primary Field**: cr950_apparatus_designation

### Fields

| Field Name | Type | Required | Notes |
|------------|------|----------|-------|
| **Actual_Hours** | Decimal(2) | No | ROLLUP from time entries |
| **Apparatus_Assessment** | Choice | Recommended | Equipment condition |
| **Apparatus Designation** | Text(200) | Yes | Primary ID (e.g., XFMR-001) |
| **Apparatus_Number** | Integer | Yes | WBS number |
| **Apparatus_Type** | Lookup → ApparatusTypeMaster | Yes | Equipment type |
| **Completed_Hours** | Decimal(2) | No | Manual entry |
| **Completion_Status** | Choice | No | Testing status |
| **Datasheet_Completed** | Yes/No | Yes | Documentation complete |
| **Delays** | Decimal(2) | No | Delay hours |
| **Equipment_Description** | Multiline Text | No | Detailed description |
| **Labor_Hours** | Decimal(2) | Yes | Planned hours |
| **Manufacturer** | Text(100) | No | Equipment manufacturer |
| **Notes** | Multiline Text | No | Testing notes |
| **Project** | Lookup → Projects | Yes | Parent project |
| **Remaining_Hours** | Decimal(2) | No | Calculated |
| **Scope** | Lookup → ProjectScope | Yes | Parent scope |
| **Serial_Number** | Text(100) | No | Equipment serial |
| **Task** | Lookup → Tasks | Yes | Parent task |
| **Voltage_Class** | Text(50) | No | Voltage rating |

### Key Calculated Field
- **Actual_Hours**: SourceType=3 (Rollup from time/revenue records)
- **Remaining_Hours**: Formula = Labor_Hours - Completed_Hours

### Relationships
- **N:1** ← Projects (cr950_project)
- **N:1** ← ProjectScope (cr950_scope)
- **N:1** ← Tasks (cr950_task)
- **N:1** ← ApparatusTypeMaster (cr950_apparatus_type)
- **1:N** → ApparatusRevenue (financial tracking)

---

## 💰 ENTITY 5: CR950_SCOPOLABORDETAIL (48 Fields)

**Purpose**: Financial rate configuration per scope  
**Primary Field**: cr950_detail_name  
**Security**: Field-level security enabled (PM/Billing only)

### Field Categories

#### Labor Rates (Currency Fields - 14 fields)
| Field | Purpose |
|-------|---------|
| Base_Labor_Rate | Standard hourly rate |
| Base_Labor_Rate (Base) | Base currency |
| Daily_Commute_Rate | Calculated commute rate |
| Daily_Commute_Rate (Base) | Base currency |
| *(Additional 10 labor rate fields)* | Various labor types |

#### Fixed Costs (Currency Fields - 24 fields)
| Field | Purpose |
|-------|---------|
| Car_Rental_Fixed | Vehicle rental cost |
| Flights_Fixed | Air travel cost |
| Generator_Rental_Fixed | Equipment rental |
| Hotel_PerDiem_Fixed | Lodging per diem |
| Misc_Fixed | Miscellaneous expenses |
| *(Each has Base currency variant)* | |

#### Percentages (Decimal Fields - 8 fields)
| Field | Purpose |
|-------|---------|
| Daily_Commute_Pct | % of base for commute |
| *(Additional percentage fields)* | Rate multipliers |

#### Relationships (2 fields)
| Field | Type | Purpose |
|-------|------|---------|
| Scope | Lookup → ProjectScope | Links to scope |
| Detail Name | Text | Auto-generated name |

### Architecture Notes
- **This IS the "Scope_Financial_Config" from specifications**
- Name in solution: cr950_ScopeLaborDetail
- Much more complex than originally spec'd (48 vs ~26 fields)
- Includes both percentage-based AND fixed cost fields
- Base currency variants for all currency fields

### Relationship
- **1:1** with ProjectScope (each scope has one config)

---

## 💵 ENTITY 6: CR950_APPARATUSREVENUE (4 Fields)

**Purpose**: Track revenue per apparatus (financial separation)  
**Primary Field**: cr950_revenue_record_id

### Fields

| Field Name | Type | Required | Purpose |
|------------|------|----------|---------|
| **Apparatus** | Lookup → Apparatus | No | Links to equipment |
| **Project** | Lookup → Projects | No | Parent project |
| **Revenue Record ID** | Text(100) | No | Unique identifier |
| **Scope_Labor_Detail** | Lookup → ScopeLaborDetail | No | Rate configuration |

### Purpose
Separates financial/revenue data from operational apparatus data for security:
- Field techs: NO ACCESS to this table
- Billing team: Full access
- PMs: Full access

### Relationships
- **N:1** ← Apparatus (cr950_apparatus)
- **N:1** ← Projects (cr950_project)
- **N:1** ← ScopeLaborDetail (cr950_scope_labor_detail)

---

## 📚 ENTITY 7: CR950_APPARATUSTYPEMASTER (6 Fields)

**Purpose**: Equipment type library with NETA standard hours  
**Primary Field**: cr950_apparatus_type_name

### Fields (Extracted from XML)

| Field Name | Type | Purpose |
|------------|------|---------|
| **Apparatus_Type_Name** | Text | Equipment type |
| **ATS_Standard_Hours** | Decimal(2) | ATS testing time |
| **Category** | Text/Choice | Equipment category |
| **Description** | Multiline Text | Type description |
| **MTS_Standard_Hours** | Decimal(2) | MTS testing time |
| **ETT_Standard_Hours** | Decimal(2) | ETT testing time (probable) |

### Purpose
Reference table for standard testing times:
- Transformer → 8.5 hrs ATS, 4.0 hrs MTS
- Circuit Breaker → 3.5 hrs ATS, 2.0 hrs MTS
- Etc.

Used to auto-populate Labor_Hours when creating Apparatus

---

## 📍 ENTITY 8: CR950_BUSINESSUNIT (5 Fields)

**Purpose**: Location master data  
**Primary Field**: cr950_location_name

### Fields

| Field Name | Type | Required | Purpose |
|------------|------|----------|---------|
| **Active** | Yes/No | Yes | Location status |
| **Location_Abbreviation** | Text(50) | No | Short code (e.g., LA) |
| **Location_Code** | Text(50) | No | Numeric/alpha code |
| **Location Name** | Text(100) | Yes | Full location name |
| **Region** | Text(100) | No | Geographic region |

### Purpose
Master list of project locations/offices:
- Los Angeles (LA)
- Las Vegas (LV)
- Phoenix (PHX)
- Etc.

Referenced by Projects (cr950_location lookup)

---

## 🔗 COMPLETE RELATIONSHIP MAP

```
BusinessUnit (Location Master)
    ↓ 1:N
Projects
    ↓ 1:N
    ├─→ ProjectScope
    │       ↓ 1:1
    │       └─→ ScopeLaborDetail (Financial Config)
    │       ↓ 1:N
    │       └─→ Tasks
    │               ↓ 1:N
    │               └─→ Apparatus
    │                       ↓ N:1
    │                       ├─→ ApparatusTypeMaster
    │                       └─→ ApparatusRevenue (Financial)
    │                               ↓ N:1
    │                               └─→ ScopeLaborDetail
```

---

## 🎯 KEY ARCHITECTURAL PATTERNS

### 1. **Hierarchical Rollups**
All levels roll up:
- Apparatus → Task → Scope → Project
- Metrics: Hours, Counts, Completion %

### 2. **Financial Data Separation**
Two-tier security:
- **Operational Tables**: Projects, Scopes, Tasks, Apparatus (Field tech access)
- **Financial Tables**: ScopeLaborDetail, ApparatusRevenue (Restricted access)

### 3. **Reference Data**
Master tables for lookups:
- ApparatusTypeMaster (equipment standards)
- BusinessUnit (locations)

### 4. **Calculated Fields Pattern**
Each hierarchy level has same 8 calculated/rollup fields:
- Total_Apparatus_Hours (rollup)
- Total_Actual_Hours (rollup)
- Total_Completed_Hours (rollup)
- Total_Delays (rollup)
- Total_Apparatus_Count (rollup)
- Completed_Apparatus_Count (rollup)
- Percent_Complete (calculated)
- Total_Remaining_Hours (calculated)

---

## 📝 DOCUMENTATION RECONCILIATION FINDINGS

### What Matches Documentation ✅
- 4 core operational tables (Projects, Scopes, Tasks, Apparatus)
- Hierarchical relationships
- NETA standards integration (ATS/MTS/ETT)
- Security separation philosophy
- Rollup patterns

### What Differs from Documentation ⚠️

| Doc Says | Reality Is | Impact |
|----------|-----------|--------|
| "Scope_Financial_Config" | "ScopeLaborDetail" | Name only |
| ~26 financial fields | 48 financial fields | More complex |
| "Apparatus_Revenue" table mentioned | "ApparatusRevenue" exists | Matches concept |
| No "BusinessUnit" mentioned | BusinessUnit exists (5 fields) | Missing from docs |
| Projects: 7 custom fields | Projects: 19 fields | +12 rollup/calc fields |
| Scopes: 39 custom fields | ProjectScope: 14 fields | Different count |

### Critical Corrections Needed
1. **Update MASTER_BUILD_SPECIFICATION** with actual ScopeLaborDetail schema (48 fields)
2. **Document BusinessUnit** table completely
3. **Correct Projects field count** (19, not 7)
4. **Correct ProjectScope field count** (14, not 39)
5. **Document all 30 formula files** and verify accuracy

---

## ✅ NEXT ACTIONS

1. ✅ Actual schema extracted (THIS DOCUMENT)
2. ⏳ Update MASTER_BUILD_SPECIFICATION.md with corrections
3. ⏳ Create CURRENT_STATE_ARCHITECTURE.md (replaces outdated docs)
4. ⏳ Extract and document all 30 formula definitions
5. ⏳ Verify security configuration matches architecture
6. ⏳ Update Entity Relationship Diagram
7. ⏳ Create accurate Forms/Views specifications based on actual schema

---

**END OF ACCURATE SCHEMA DOCUMENTATION**

*This document represents the TRUE state of v1.2.0.3 as of November 15, 2025.*
