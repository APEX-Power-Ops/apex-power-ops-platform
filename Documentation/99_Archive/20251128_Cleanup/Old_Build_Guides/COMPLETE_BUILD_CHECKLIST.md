# 🚀 RESA Power Project Tracker - Complete Build Checklist

**Version:** 1.1  
**Date:** November 10, 2025  
**Purpose:** Comprehensive step-by-step checklist for building ALL Dataverse tables  
**Alignment:** Master Build Specification v1.1  
**Use:** Check off each step as you complete it

---

## 📋 TABLE OF CONTENTS

- [System Overview](#system-overview)
- [Phase 1: Master Data Tables](#phase-1-master-data-tables)
  - [Table 1: Locations](#table-1-locations)
  - [Table 2: Apparatus_Type_Master](#table-2-apparatus_type_master)
- [Phase 2: Operational Tables](#phase-2-operational-tables)
  - [Table 3: Projects](#table-3-projects)
  - [Table 4: Scopes](#table-4-scopes)
  - [Table 5: Tasks](#table-5-tasks)
  - [Table 6: Apparatus](#table-6-apparatus)
- [Phase 3: Financial Tables](#phase-3-financial-tables)
  - [Table 7: Scope_Financial_Configuration](#table-7-scope_financial_configuration)
  - [Table 8: Apparatus_Revenue](#table-8-apparatus_revenue)
- [Verification & Testing](#verification--testing)
- [Next Steps](#next-steps)

---

## SYSTEM OVERVIEW

### Total Tables: 8

**Master Data (Build First):**
1. Locations - 4 Southwest Region offices
2. Apparatus_Type_Master - 132 apparatus types with ATS/MTS specs

**Operational Layer (Field Tech Access):**
3. Projects - Core project records
4. Scopes - Work breakdown with NETA_Standard (ATS/MTS)
5. Tasks - Work organization (manual creation, NOT imported)
6. Apparatus - Individual testable units (ZERO financial data)

**Financial Layer (Management Only - RESTRICTED):**
7. Scope_Financial_Configuration - Rates, multipliers, markup
8. Apparatus_Revenue - Revenue recognition (auto-generated)

### Architectural Principle:
**Table-Level Security Separation**
- Operational tables visible to field technicians
- Financial tables accessible only to management/billing
- Clean security boundaries enforced at table level

### Build Order:
```
Phase 1: Master Data (Locations → Apparatus_Type_Master)
    ↓
Phase 2: Operational (Projects → Scopes → Tasks → Apparatus)
    ↓
Phase 3: Financial (Scope_Financial_Config → Apparatus_Revenue)
    ↓
Verification & Testing
```

**Estimated Total Time:** 6-8 hours for all 8 tables

---

## PHASE 1: MASTER DATA TABLES

**Purpose:** Build reference tables that other tables depend on  
**Status:** [ ] Not Started | [ ] In Progress | [ ] Complete

---

### TABLE 1: LOCATIONS

**Purpose:** Master reference for RESA Power business unit locations (Southwest Region)  
**Build Priority:** 1 (MUST BE FIRST)  
**Why First:** Projects table requires Location_Code lookup

#### Pre-Build Checklist:
- [ ] Logged into make.powerapps.com
- [ ] Selected "RESA Power TEST" environment
- [ ] Confirmed you're in correct environment (check upper right)

#### Build Steps:

**Create Table:**
- [ ] Navigate to "Tables" in left navigation
- [ ] Click "+ New table" → "Add columns and data"
- [ ] Table Name: `Locations`
- [ ] Description: "Master reference for RESA Power business unit locations"

**Configure Primary Key:**
- [ ] Primary column name: `Location_Name`
- [ ] Data type: Text
- [ ] Note: We'll add Location_Code as PRIMARY KEY separately

**Add Location_Code Field (CRITICAL - This is the PRIMARY KEY):**
- [ ] Add column: `Location_Code`
- [ ] Data type: Text
- [ ] Max length: 3
- [ ] Required: Yes
- [ ] Searchable: Yes
- [ ] ⚠️ This is the BUSINESS PRIMARY KEY (not auto-number)

**Add Location_Abbreviation Field:**
- [ ] Add column: `Location_Abbreviation`
- [ ] Data type: Text
- [ ] Max length: 10
- [ ] Required: Yes
- [ ] Searchable: Yes
- [ ] Used in Full Project ID: PHX-674414

**Add Region Field:**
- [ ] Add column: `Region`
- [ ] Data type: Text
- [ ] Max length: 50
- [ ] Required: No
- [ ] Default value: "Southwest"

**Add Active Field:**
- [ ] Add column: `Active`
- [ ] Data type: Yes/No
- [ ] Required: Yes
- [ ] Default value: Yes
- [ ] Controls visibility in dropdowns

**Add Sort_Order Field:**
- [ ] Add column: `Sort_Order`
- [ ] Data type: Whole Number
- [ ] Required: No
- [ ] Purpose: Display sequence

**Add Office_Address Field:**
- [ ] Add column: `Office_Address`
- [ ] Data type: Multiple Lines of Text
- [ ] Max length: 300
- [ ] Required: No

**Add Office_Manager Field:**
- [ ] Add column: `Office_Manager`
- [ ] Data type: Text
- [ ] Max length: 100
- [ ] Required: No

**Add Notes Field:**
- [ ] Add column: `Notes`
- [ ] Data type: Multiple Lines of Text
- [ ] Required: No

**Add 4 Southwest Region Locations:**
- [ ] Record 1:
  - Location_Code: 575
  - Location_Name: San Diego
  - Location_Abbreviation: SD
  - Region: Southwest
  - Active: Yes
  - Sort_Order: 1

- [ ] Record 2:
  - Location_Code: 571
  - Location_Name: Las Vegas
  - Location_Abbreviation: LAS
  - Region: Southwest
  - Active: Yes
  - Sort_Order: 2

- [ ] Record 3:
  - Location_Code: 578
  - Location_Name: Phoenix
  - Location_Abbreviation: PHX
  - Region: Southwest
  - Active: Yes
  - Sort_Order: 3
  - Office_Manager: Jason Smith

- [ ] Record 4:
  - Location_Code: 574
  - Location_Name: Denver
  - Location_Abbreviation: DEN
  - Region: Southwest
  - Active: Yes
  - Sort_Order: 4

**Save and Verify:**
- [ ] Save table
- [ ] Verify all 4 records appear
- [ ] Test: Can you see all location names?
- [ ] Test: Sort by Sort_Order - do they appear in correct sequence?

**Status:** [ ] Not Started | [ ] Complete ✅

---

### TABLE 2: APPARATUS_TYPE_MASTER

**Purpose:** Master catalog of apparatus types with ATS/MTS specifications  
**Build Priority:** 2  
**Note:** You mentioned this already exists with 132 records

#### Verify Existing Table Structure:

**If table already exists, verify it has these fields:**
- [ ] Apparatus_Type_ID (Auto-number, Primary Key)
- [ ] Apparatus_Type_Name (Text, Required)
- [ ] NETA_ATS_Section_Reference (Text, 50 chars) ⭐ v1.1
- [ ] NETA_MTS_Section_Reference (Text, 50 chars) ⭐ v1.1
- [ ] NETA_ATS_Labor_Hours (Decimal) ⭐ v1.1
- [ ] NETA_MTS_Labor_Hours (Decimal) ⭐ v1.1
- [ ] Category (Text, Optional)
- [ ] Active (Yes/No, Default: Yes)

**If table needs updating from old structure:**
- [ ] Check if has old fields: `NETA_Spec_Reference`, `Default_Labor_Hours`
- [ ] If yes, needs migration to 4-column structure (see migration guide)
- [ ] Backup existing data before migration

**Sample Record Verification:**
- [ ] Find "Transformer - Pad Mount Oil" record
- [ ] Verify has both ATS and MTS values:
  - NETA_ATS_Section_Reference: "7.2"
  - NETA_ATS_Labor_Hours: 12.0
  - NETA_MTS_Section_Reference: "7.2"
  - NETA_MTS_Labor_Hours: 8.5

**If table doesn't exist:**
- [ ] Create table following same pattern as Locations
- [ ] Import 132 apparatus types from CSV template
- [ ] Verify all records have both ATS and MTS specifications

**Status:** [ ] Verified ✅ | [ ] Needs Update | [ ] Doesn't Exist

---

## PHASE 2: OPERATIONAL TABLES

**Purpose:** Build tables for day-to-day project operations  
**Access:** Field technicians have full CRUD access to these tables  
**Status:** [ ] Not Started | [ ] In Progress | [ ] Complete

---

### TABLE 3: PROJECTS

**Purpose:** Core project records  
**Build Priority:** 3  
**Dependencies:** Requires Locations table (for Location_Code lookup)

#### Build Steps:

**Create Table:**
- [ ] Tables → "+ New table" → "Add columns and data"
- [ ] Table Name: `Projects`
- [ ] Description: "Core project records with job numbers and customer information"
- [ ] Primary column name: `Project_Name`

**Add Job_Number Field (PRIMARY BUSINESS KEY):**
- [ ] Add column: `Job_Number`
- [ ] Data type: Text
- [ ] Max length: 50
- [ ] Required: Yes
- [ ] Searchable: Yes
- [ ] Note: 6-7 digit sequential company-wide number

**Add Location_Code Lookup (CRITICAL RELATIONSHIP):**
- [ ] Add column: `Location_Code`
- [ ] Data type: **Lookup**
- [ ] Related table: **Locations**
- [ ] Required: Yes
- [ ] This creates the relationship to Locations

**Add Customer Fields:**
- [ ] Add column: `Customer_Name`
  - Data type: Text
  - Max length: 100
  - Required: Yes
  
- [ ] Add column: `Customer_Short_Name`
  - Data type: Text
  - Max length: 50
  - Required: No

**Add Project Details:**
- [ ] Add column: `Description`
  - Data type: Multiple Lines of Text
  - Max length: 2000
  - Required: No

- [ ] Add column: `Project_Manager`
  - Data type: Text
  - Max length: 100
  - Required: No

- [ ] Add column: `Contract_Value`
  - Data type: Currency
  - Required: No

- [ ] Add column: `Estimate_Version`
  - Data type: Text
  - Max length: 20
  - Required: No

**Add Project_Status Choice:**
- [ ] Add column: `Project_Status`
- [ ] Data type: Choice
- [ ] Required: Yes
- [ ] Default: Planning
- [ ] Options:
  - Planning
  - Active
  - On Hold
  - Complete
  - Cancelled

**Add Date Fields:**
- [ ] Add column: `Start_Date` (Date Only, Optional)
- [ ] Add column: `Target_Completion_Date` (Date Only, Optional)
- [ ] Add column: `Actual_Completion_Date` (Date Only, Optional)

**Add Test Record:**
- [ ] Project_Name: LASNAP16
- [ ] Job_Number: 674414
- [ ] Location_Code: 571 (Las Vegas)
- [ ] Customer_Name: Goodman Manufacturing
- [ ] Customer_Short_Name: Goodman
- [ ] Description: Las Vegas data center electrical testing
- [ ] Project_Manager: Jason Smith
- [ ] Project_Status: Active
- [ ] Start_Date: 2025-01-15

**Save and Verify:**
- [ ] Save table
- [ ] Verify record appears
- [ ] Test: Click Location_Code lookup - does it show "Las Vegas"?
- [ ] Test: Can navigate from Project to Location record?

**Status:** [ ] Not Started | [ ] Complete ✅

---

### TABLE 4: SCOPES

**Purpose:** Work breakdown structure with NETA Standard specification  
**Build Priority:** 4  
**Dependencies:** Requires Projects table (for Job_Number lookup)

#### Build Steps:

**Create Table:**
- [ ] Tables → "+ New table" → "Add columns and data"
- [ ] Table Name: `Scopes`
- [ ] Description: "Work breakdown structure with NETA testing standards"
- [ ] Primary column name: `Scope_Name`

**Add Identification Fields:**
- [ ] Add column: `Scope_Number`
  - Data type: Whole Number
  - Required: Yes
  - Searchable: Yes

- [ ] Add column: `Full_Scope_ID`
  - Data type: Text
  - Max length: 50
  - Required: No
  - Example: LAS16.PPM01

- [ ] Add column: `SLD_Reference`
  - Data type: Text
  - Max length: 100
  - Required: No
  - Purpose: Single Line Diagram reference

**Add Project Lookup (CRITICAL RELATIONSHIP):**
- [ ] Add column: `Job_Number`
- [ ] Data type: **Lookup**
- [ ] Related table: **Projects**
- [ ] Required: Yes

**⭐ Add NETA_Standard Choice (CRITICAL v1.1 ADDITION):**
- [ ] Add column: `NETA_Standard`
- [ ] Data type: **Choice**
- [ ] Required: **Yes**
- [ ] Default: **ATS**
- [ ] Options:
  - **ATS** (Acceptance Testing Specifications)
  - **MTS** (Maintenance Testing Specifications)
- [ ] Purpose: Determines which NETA specs apply to ALL apparatus in this scope

**Add Operational Fields:**
- [ ] Add column: `Total_Apparatus_Hours`
  - Data type: Decimal
  - Precision: 2
  - Required: No
  - Purpose: Rollup from Apparatus (will configure later)

- [ ] Add column: `Completed_Hours`
  - Data type: Decimal
  - Precision: 2
  - Required: No
  - Purpose: Rollup from Apparatus (will configure later)

- [ ] Add column: `Percent_Complete`
  - Data type: Decimal
  - Precision: 2
  - Required: No
  - Purpose: Calculated field (will configure later)

**Add Scope_Status Choice:**
- [ ] Add column: `Scope_Status`
- [ ] Data type: Choice
- [ ] Required: Yes
- [ ] Default: Not Started
- [ ] Options:
  - Not Started
  - In Progress
  - Complete

**Add Test Record:**
- [ ] Scope_Name: PPM01
- [ ] Scope_Number: 1
- [ ] Full_Scope_ID: LAS16.PPM01
- [ ] Job_Number: LASNAP16 (lookup/select)
- [ ] **NETA_Standard: ATS** ⭐
- [ ] SLD_Reference: DWG-001
- [ ] Total_Apparatus_Hours: 157.8
- [ ] Scope_Status: In Progress

**Save and Verify:**
- [ ] Save table
- [ ] Verify record appears
- [ ] Test: NETA_Standard shows "ATS"?
- [ ] Test: Can navigate from Scope to Project?
- [ ] Test: Can see Project details through lookup?

**Status:** [ ] Not Started | [ ] Complete ✅

---

### TABLE 5: TASKS

**Purpose:** Task-level organization of apparatus within scopes  
**Build Priority:** 5  
**Dependencies:** Requires Scopes and Projects tables

**⭐ CRITICAL: IMMEDIATE IMPLEMENTATION**
- Tasks table built in Phase 2 (NOT deferred)
- Created **MANUALLY by PMs** in Power Apps (NOT imported from Excel)
- Excel estimators have NO task-level structure
- Tasks organize apparatus into work packages after import

#### Build Steps:

**Create Table:**
- [ ] Tables → "+ New table" → "Add columns and data"
- [ ] Table Name: `Tasks`
- [ ] Description: "Task-level organization - manually created by Project Managers"
- [ ] Primary column name: `Task_Name`

**Add Identification Fields:**
- [ ] Add column: `Task_Number`
  - Data type: Whole Number
  - Required: Yes
  - Searchable: Yes

- [ ] Add column: `Description`
  - Data type: Multiple Lines of Text
  - Max length: 500
  - Required: No

**Add Relationship Lookups:**
- [ ] Add column: `Scope_ID`
  - Data type: **Lookup**
  - Related table: **Scopes**
  - Required: Yes

- [ ] Add column: `Job_Number`
  - Data type: **Lookup**
  - Related table: **Projects**
  - Required: Yes

**Add Work Definition Fields:**
- [ ] Add column: `Apparatus_Type`
  - Data type: Text
  - Max length: 200
  - Required: No
  - Purpose: Primary apparatus type for grouping

- [ ] Add column: `NETA_Section`
  - Data type: Text
  - Max length: 50
  - Required: No
  - Purpose: Inherits from Apparatus_Type_Master based on Scope's NETA_Standard

- [ ] Add column: `Total_Apparatus_Count`
  - Data type: Whole Number
  - Required: No
  - Purpose: Rollup from Apparatus (configure later)

- [ ] Add column: `Total_Task_Hours`
  - Data type: Decimal
  - Precision: 2
  - Required: No
  - Purpose: Rollup from Apparatus (configure later)

**Add Assignment Fields:**
- [ ] Add column: `Assigned_To`
  - Data type: Text
  - Max length: 100
  - Required: No

- [ ] Add column: `Due_Date`
  - Data type: Date Only
  - Required: No

**Add Task_Status Choice:**
- [ ] Add column: `Task_Status`
- [ ] Data type: Choice
- [ ] Required: Yes
- [ ] Default: Not Started
- [ ] Options:
  - Not Started
  - In Progress
  - Complete

**Add Test Record:**
- [ ] Task_Name: Pad Mount Transformers
- [ ] Task_Number: 2
- [ ] Scope_ID: PPM01 (lookup/select)
- [ ] Job_Number: LASNAP16 (lookup/select)
- [ ] Apparatus_Type: Transformer - Pad Mount Oil
- [ ] NETA_Section: 7.2 (will auto-populate in real system)
- [ ] Task_Status: In Progress
- [ ] Assigned_To: Brandon Valdavis

**Save and Verify:**
- [ ] Save table
- [ ] Verify record appears
- [ ] Test: Can navigate from Task to Scope?
- [ ] Test: Can navigate from Task to Project?
- [ ] Test: Relationships working correctly?

**Status:** [ ] Not Started | [ ] Complete ✅

---

### TABLE 6: APPARATUS

**Purpose:** Individual testable equipment units - atomic level of tracking  
**Build Priority:** 6  
**Dependencies:** Requires Projects, Scopes, Tasks, Apparatus_Type_Master

**⚠️ CRITICAL: ZERO FINANCIAL DATA IN THIS TABLE**
- This table contains ONLY operational data
- NO currency fields, NO rates, NO revenue
- All financial data in separate Apparatus_Revenue table (Phase 3)
- This separation enables field tech access without exposing financial data

#### Build Steps:

**Create Table:**
- [ ] Tables → "+ New table" → "Add columns and data"
- [ ] Table Name: `Apparatus`
- [ ] Description: "Individual testable equipment units - operational data only"
- [ ] Primary column name: `Apparatus_Designation`

**Add Identification Fields:**
- [ ] Add column: `Apparatus_Number`
  - Data type: Whole Number
  - Required: Yes
  - Searchable: Yes
  - Purpose: Sequential within scope

- [ ] Add column: `Hierarchy_ID`
  - Data type: Text
  - Max length: 50
  - Required: No
  - Example: "1.2.3"

- [ ] Add column: `Apparatus_Tag`
  - Data type: Text
  - Max length: 100
  - Required: No
  - Purpose: Equipment tag from drawings

**Add Relationship Lookups:**
- [ ] Add column: `Job_Number`
  - Data type: **Lookup**
  - Related table: **Projects**
  - Required: Yes

- [ ] Add column: `Scope_ID`
  - Data type: **Lookup**
  - Related table: **Scopes**
  - Required: Yes

- [ ] Add column: `Task_ID`
  - Data type: **Lookup**
  - Related table: **Tasks**
  - Required: **No** (assigned after import)

- [ ] Add column: `Apparatus_Type_ID`
  - Data type: **Lookup**
  - Related table: **Apparatus_Type_Master**
  - Required: No

**Add Work Definition Fields:**
- [ ] Add column: `Apparatus_Type_Name`
  - Data type: Text
  - Max length: 200
  - Required: No
  - Purpose: For cases without master link

- [ ] Add column: `Apparatus_Hours`
  - Data type: Decimal
  - Precision: 2
  - Required: Yes
  - Purpose: Estimated test hours (from master based on NETA_Standard)

- [ ] Add column: `Actual_Hours`
  - Data type: Decimal
  - Precision: 2
  - Required: No
  - Purpose: Field tech entry

- [ ] Add column: `Description`
  - Data type: Multiple Lines of Text
  - Max length: 500
  - Required: No

**Add Field Tech Update Fields:**
- [ ] Add column: `Status`
  - Data type: Choice
  - Required: Yes
  - Default: Not Started
  - Options:
    - Not Started
    - In Progress
    - Complete

- [ ] Add column: `Priority`
  - Data type: Choice
  - Required: No
  - Default: Medium
  - Options:
    - High
    - Medium
    - Low

- [ ] Add column: `Availability`
  - Data type: Choice
  - Required: No
  - Default: Available
  - Options:
    - Available
    - Waiting on Parts
    - Waiting on Customer
    - Not Available

- [ ] Add column: `Date_Started`
  - Data type: Date Only
  - Required: No

- [ ] Add column: `Date_Completed`
  - Data type: Date Only
  - Required: No

- [ ] Add column: `Date_Due`
  - Data type: Date Only
  - Required: No

- [ ] Add column: `Notes`
  - Data type: Multiple Lines of Text
  - Max length: 2000
  - Required: No
  - Purpose: Field tech notes and findings

**⚠️ VERIFY: NO FINANCIAL FIELDS**
- [ ] Confirm: NO "Billable_Revenue" field
- [ ] Confirm: NO "Revenue_Recognized_Date" field
- [ ] Confirm: NO currency fields of any kind
- [ ] Financial data goes in Apparatus_Revenue table (Phase 3)

**Add Test Record:**
- [ ] Apparatus_Designation: XFMR-001
- [ ] Apparatus_Number: 1
- [ ] Hierarchy_ID: 1.2.1
- [ ] Apparatus_Tag: XFMR-001
- [ ] Job_Number: LASNAP16 (lookup/select)
- [ ] Scope_ID: PPM01 (lookup/select)
- [ ] Task_ID: Pad Mount Transformers (lookup/select)
- [ ] Apparatus_Type_ID: Transformer - Pad Mount Oil (lookup from master)
- [ ] Apparatus_Hours: 12.0 (from master ATS hours)
- [ ] Status: Complete
- [ ] Date_Completed: 2025-11-10
- [ ] Priority: High
- [ ] Availability: Available

**Save and Verify:**
- [ ] Save table
- [ ] Verify record appears
- [ ] Test: All three lookups working (Project, Scope, Task)?
- [ ] Test: Can navigate through all relationships?
- [ ] Test: Apparatus_Type lookup shows equipment types?
- [ ] **CRITICAL TEST: No financial fields visible?**

**Status:** [ ] Not Started | [ ] Complete ✅

---

## PHASE 3: FINANCIAL TABLES

**Purpose:** Build tables for financial data - completely separated from operations  
**Access:** RESTRICTED - Management and Billing only (NO field tech access)  
**Status:** [ ] Not Started | [ ] In Progress | [ ] Complete

**⭐ ARCHITECTURAL PRINCIPLE:**
These tables contain ALL financial data. By separating operational and financial data at the table level, we achieve clean role-based security without complex field-level restrictions.

---

### TABLE 7: SCOPE_FINANCIAL_CONFIGURATION

**Purpose:** Financial rates and multipliers for revenue calculation  
**Build Priority:** 7  
**Dependencies:** Requires Scopes table (1:1 relationship)

**🚨 SECURITY CRITICAL - RESTRICTED ACCESS**

#### Build Steps:

**Create Table:**
- [ ] Tables → "+ New table" → "Add columns and data"
- [ ] Table Name: `Scope_Financial_Configuration`
- [ ] Description: "Financial rates and configuration - RESTRICTED ACCESS"
- [ ] Primary column name: `Config_Name`

**Add Scope Lookup (1:1 RELATIONSHIP):**
- [ ] Add column: `Scope_ID`
- [ ] Data type: **Lookup**
- [ ] Related table: **Scopes**
- [ ] Required: Yes
- [ ] Note: ONE config per scope (enforce through business rule)

**Add Base Rate Fields:**
- [ ] Add column: `Base_Rate`
  - Data type: Currency
  - Precision: 2 decimals
  - Required: No
  - Purpose: Base hourly labor rate

- [ ] Add column: `Base_Percent`
  - Data type: Decimal
  - Precision: 3 decimals
  - Required: No
  - Purpose: Base rate markup (0.050 = 5%)

**Add Multiplier Rate Fields:**
- [ ] Add column: `Commute_Rate` (Currency, 2 decimals, Optional)
- [ ] Add column: `Commute_Percent` (Decimal, 3 decimals, Optional)
- [ ] Add column: `PM_Rate` (Currency, 2 decimals, Optional)
- [ ] Add column: `PM_Percent` (Decimal, 3 decimals, Optional)
- [ ] Add column: `Daily_Report_Rate` (Currency, 2 decimals, Optional)
- [ ] Add column: `Daily_Report_Percent` (Decimal, 3 decimals, Optional)
- [ ] Add column: `Travel_Rate` (Currency, 2 decimals, Optional)
- [ ] Add column: `Travel_Percent` (Decimal, 3 decimals, Optional)
- [ ] Add column: `Final_Report_Rate` (Currency, 2 decimals, Optional)
- [ ] Add column: `Final_Report_Percent` (Decimal, 3 decimals, Optional)

**Add Fixed Cost Fields:**
- [ ] Add column: `Fixed_Cost_Travel`
  - Data type: Currency
  - Precision: 2 decimals
  - Required: No

- [ ] Add column: `Fixed_Cost_ME`
  - Data type: Currency
  - Precision: 2 decimals
  - Required: No
  - Purpose: Meals & Entertainment

**Add Scope Multiplier:**
- [ ] Add column: `Scope_Multiplier`
  - Data type: Decimal
  - Precision: 3 decimals
  - Required: No
  - Default: 1.000
  - Purpose: Overall scope complexity multiplier

**Add Notes:**
- [ ] Add column: `Notes`
  - Data type: Multiple Lines of Text
  - Required: No

**Add Test Record:**
- [ ] Config_Name: PPM01 Financial Config
- [ ] Scope_ID: PPM01 (lookup/select)
- [ ] Base_Rate: 150.00
- [ ] Commute_Percent: 0.025
- [ ] PM_Percent: 0.050
- [ ] Daily_Report_Percent: 0.043
- [ ] Travel_Percent: 0.065
- [ ] Final_Report_Percent: 0.100
- [ ] Fixed_Cost_Travel: 2500.00
- [ ] Fixed_Cost_ME: 1200.00
- [ ] Scope_Multiplier: 1.150
- [ ] Notes: Standard ATS testing rates

**Save and Verify:**
- [ ] Save table
- [ ] Verify record appears
- [ ] Test: Can navigate from Config to Scope?
- [ ] Test: Financial values displaying correctly?

**Configure Security (CRITICAL):**
- [ ] Create Field Technician security role
- [ ] **REMOVE all access** to Scope_Financial_Configuration table
- [ ] Test: Field tech role cannot see this table at all

**Status:** [ ] Not Started | [ ] Complete ✅

---

### TABLE 8: APPARATUS_REVENUE

**Purpose:** Revenue recognition records - auto-generated by Power Automate  
**Build Priority:** 8 (FINAL TABLE)  
**Dependencies:** Requires Apparatus, Scopes, Projects tables

**🚨 SECURITY CRITICAL - RESTRICTED ACCESS**  
**⭐ AUTO-GENERATED - Not typically manually populated**

#### Build Steps:

**Create Table:**
- [ ] Tables → "+ New table" → "Add columns and data"
- [ ] Table Name: `Apparatus_Revenue`
- [ ] Description: "Revenue recognition records - AUTO-GENERATED by Power Automate"
- [ ] Primary column name: `Revenue_Record_Name`

**Add Relationship Lookups:**
- [ ] Add column: `Apparatus_ID`
  - Data type: **Lookup**
  - Related table: **Apparatus**
  - Required: Yes
  - Note: 1:1 relationship (one revenue record per apparatus)

- [ ] Add column: `Scope_ID`
  - Data type: **Lookup**
  - Related table: **Scopes**
  - Required: Yes
  - Purpose: For rollups

- [ ] Add column: `Job_Number`
  - Data type: **Lookup**
  - Related table: **Projects**
  - Required: Yes
  - Purpose: For rollups

**Add Calculation Input Fields:**
- [ ] Add column: `Labor_Hours`
  - Data type: Decimal
  - Precision: 2 decimals
  - Required: Yes
  - Purpose: Snapshot from Apparatus at completion

- [ ] Add column: `Base_Labor_Rate`
  - Data type: Currency
  - Precision: 2 decimals
  - Required: No
  - Purpose: From Scope_Financial_Configuration

- [ ] Add column: `Applied_Multipliers`
  - Data type: Decimal
  - Precision: 4 decimals
  - Required: No
  - Purpose: Sum of all percentage multipliers

- [ ] Add column: `Scope_Multiplier`
  - Data type: Decimal
  - Precision: 3 decimals
  - Required: No
  - Default: 1.000
  - Purpose: From Scope_Financial_Configuration

**Add Revenue Fields:**
- [ ] Add column: `Calculated_Revenue`
  - Data type: Currency
  - Precision: 2 decimals
  - Required: Yes
  - Purpose: Auto-calculated by Power Automate

- [ ] Add column: `Revenue_Recognized_Date`
  - Data type: Date and Time
  - Required: Yes
  - Purpose: Timestamp when revenue recognized

- [ ] Add column: `Completed_By`
  - Data type: Text
  - Max length: 100
  - Required: No
  - Purpose: Technician who completed apparatus

**Add Override Fields:**
- [ ] Add column: `Manual_Override_Revenue`
  - Data type: Currency
  - Precision: 2 decimals
  - Required: No
  - Purpose: Manual adjustment (requires reason)

- [ ] Add column: `Manual_Override_Reason`
  - Data type: Multiple Lines of Text
  - Required: No
  - Purpose: REQUIRED if override used

**Add Billing_Status Choice:**
- [ ] Add column: `Billing_Status`
- [ ] Data type: Choice
- [ ] Required: Yes
- [ ] Default: Not Billed
- [ ] Options:
  - Not Billed
  - Billed
  - Paid
  - Disputed

**Add Billed_Date:**
- [ ] Add column: `Billed_Date`
  - Data type: Date Only
  - Required: No
  - Purpose: Date invoiced to customer

**Add Notes:**
- [ ] Add column: `Notes`
  - Data type: Multiple Lines of Text
  - Required: No

**Add Test Record (Manual for Testing):**
- [ ] Revenue_Record_Name: XFMR-001 Revenue
- [ ] Apparatus_ID: XFMR-001 (lookup/select)
- [ ] Scope_ID: PPM01 (lookup/select)
- [ ] Job_Number: LASNAP16 (lookup/select)
- [ ] Labor_Hours: 12.0
- [ ] Base_Labor_Rate: 150.00
- [ ] Applied_Multipliers: 0.183 (sum of all percentages)
- [ ] Scope_Multiplier: 1.150
- [ ] Calculated_Revenue: 2055.90
  - Formula: (12 × 150) × (1 + 0.183) × 1.150
- [ ] Revenue_Recognized_Date: 2025-11-10 (current timestamp)
- [ ] Completed_By: Brandon Valdavis
- [ ] Billing_Status: Not Billed

**Save and Verify:**
- [ ] Save table
- [ ] Verify record appears
- [ ] Test: All three lookups working?
- [ ] Test: Revenue calculation correct?
- [ ] Test: Can navigate from Revenue to Apparatus?

**Configure Security (CRITICAL):**
- [ ] Update Field Technician security role
- [ ] **REMOVE all access** to Apparatus_Revenue table
- [ ] Test: Field tech role cannot see this table at all
- [ ] Test: Management role CAN see both financial tables

**Status:** [ ] Not Started | [ ] Complete ✅

---

## VERIFICATION & TESTING

**Status:** [ ] Not Started | [ ] In Progress | [ ] Complete

### Phase 1: Individual Table Verification

**Master Data Tables:**
- [ ] Locations: 4 records present (SD, LAS, PHX, DEN)
- [ ] Apparatus_Type_Master: Has ATS and MTS specifications

**Operational Tables:**
- [ ] Projects: Test record created, Location lookup working
- [ ] Scopes: Test record created, NETA_Standard field present, Project lookup working
- [ ] Tasks: Test record created, Scope and Project lookups working
- [ ] Apparatus: Test record created, NO financial fields present, all lookups working

**Financial Tables:**
- [ ] Scope_Financial_Configuration: Test record created, rates populated
- [ ] Apparatus_Revenue: Test record created, revenue calculated correctly

### Phase 2: Relationship Verification

**Test Navigation:**
- [ ] Start at Apparatus XFMR-001
- [ ] Navigate to Task: Pad Mount Transformers ✅
- [ ] Navigate from Task to Scope: PPM01 ✅
- [ ] Navigate from Scope to Project: LASNAP16 ✅
- [ ] Navigate from Project to Location: Las Vegas ✅
- [ ] Navigate from Apparatus to Apparatus_Type_Master ✅
- [ ] Navigate from Scope to Scope_Financial_Configuration ✅
- [ ] Navigate from Apparatus to Apparatus_Revenue ✅

**Test Reverse Navigation:**
- [ ] Open Project LASNAP16
- [ ] View related Scopes (should show PPM01) ✅
- [ ] Open Scope PPM01
- [ ] View related Tasks (should show Pad Mount Transformers) ✅
- [ ] View related Apparatus (should show XFMR-001) ✅
- [ ] Open Task
- [ ] View related Apparatus (should show XFMR-001) ✅

### Phase 3: Architecture Verification

**Operational/Financial Separation:**
- [ ] Apparatus table has ZERO financial fields ✅
- [ ] All revenue data in Apparatus_Revenue table ✅
- [ ] Scope_Financial_Configuration separate from Scopes ✅
- [ ] Clear table-level security boundaries ✅

**NETA Standards Architecture:**
- [ ] Scopes table has NETA_Standard choice field (ATS/MTS) ✅
- [ ] Apparatus_Type_Master has both ATS and MTS specifications ✅
- [ ] Test scope shows NETA_Standard = ATS ✅
- [ ] Tasks can reference NETA sections ✅

### Phase 4: Security Testing

**Field Technician Role:**
- [ ] Can view/edit Apparatus table ✅
- [ ] Can view/edit Tasks table ✅
- [ ] Can view Projects and Scopes (read-only) ✅
- [ ] **CANNOT view** Scope_Financial_Configuration ✅
- [ ] **CANNOT view** Apparatus_Revenue ✅
- [ ] Test: Try to open financial tables - should be blocked ✅

**Management Role:**
- [ ] Can view/edit all operational tables ✅
- [ ] Can view/edit Scope_Financial_Configuration ✅
- [ ] Can view/edit Apparatus_Revenue ✅
- [ ] Full system visibility ✅

### Phase 5: Data Integrity

**Record Counts:**
- [ ] Locations: 4 records
- [ ] Apparatus_Type_Master: 132 records (or as per your data)
- [ ] Projects: 1 test record (LASNAP16)
- [ ] Scopes: 1 test record (PPM01)
- [ ] Tasks: 1 test record (Pad Mount Transformers)
- [ ] Apparatus: 1 test record (XFMR-001)
- [ ] Scope_Financial_Configuration: 1 test record
- [ ] Apparatus_Revenue: 1 test record

**Data Consistency:**
- [ ] All lookups resolve correctly
- [ ] No orphaned records (all foreign keys valid)
- [ ] NETA_Standard populated on all scopes
- [ ] Financial data separate from operational data

### Phase 6: Model-Driven App Test

- [ ] Create basic Model-Driven app
- [ ] Add all 8 tables to app
- [ ] Publish app
- [ ] Open app
- [ ] Navigate through all tables
- [ ] Verify relationships display correctly
- [ ] Test security roles in app

---

## NEXT STEPS

**Immediate (This Week):**
- [ ] Take screenshots of all 8 tables with test data
- [ ] Document table relationships in system diagram
- [ ] Configure security roles for field tech and management
- [ ] Test security with sample user accounts

**Phase 1 Completion (Next Week):**
- [ ] Import 4 Locations (if not already done)
- [ ] Verify/update Apparatus_Type_Master with ATS/MTS specs
- [ ] Import LASNAP16 project data:
  - [ ] 1 project record
  - [ ] 27 scope records (with NETA_Standard)
  - [ ] 27 scope financial config records
  - [ ] 1,905 apparatus records

**Manual Task Creation (After Import):**
- [ ] Train PM on task creation workflow
- [ ] PM reviews imported apparatus by scope
- [ ] PM creates tasks to group apparatus:
  - [ ] By equipment type (All Transformers)
  - [ ] By physical location (Switchgear A-D)
  - [ ] By test complexity
- [ ] PM assigns tasks to technicians
- [ ] Verify task organization supports field workflow

**Power Automate Configuration:**
- [ ] Build revenue recognition flow:
  - [ ] Trigger: Apparatus.Status = "Complete"
  - [ ] Action: Retrieve Scope_Financial_Configuration
  - [ ] Action: Calculate revenue
  - [ ] Action: Create Apparatus_Revenue record
- [ ] Test flow with completed apparatus
- [ ] Verify financial data remains hidden from field techs

**Model-Driven App Build:**
- [ ] Design forms for each entity
- [ ] Create views for operational users
- [ ] Create views for management users
- [ ] Build dashboards
- [ ] Configure business process flows

**Canvas App Development:**
- [ ] Build field technician mobile interface
- [ ] Test on mobile devices
- [ ] Deploy to pilot technicians

---

## SUCCESS CRITERIA

**You'll know Phase 1 (table build) is complete when:**

- ✅ All 8 tables created in Dataverse
- ✅ One test record in each table
- ✅ All relationships working (can navigate)
- ✅ NETA_Standard field functional in Scopes
- ✅ Apparatus table has ZERO financial fields
- ✅ Financial tables separate and restricted
- ✅ Security roles configured and tested
- ✅ Can view all data in Model-Driven app
- ✅ Architecture aligns with Master Build Specification v1.1
- ✅ Ready to import bulk data

**Estimated Total Time:** 6-8 hours for all 8 tables + security configuration

---

## COMMON ISSUES & FIXES

### "Can't find lookup table"
- Verify you're in correct environment (RESA Power TEST)
- Build tables in order (Master → Operational → Financial)
- Refresh browser if table just created
- Check that parent table has records before creating lookup

### "Lookup field not saving"
- Type first few letters, wait for search results
- Select from dropdown, don't just type
- Verify parent record exists
- Check relationship is configured correctly

### "Can't see Related records"
- Relationship may need time to activate (refresh page)
- Check in Model-Driven app instead of table editor
- Verify lookup was set correctly on child record
- Ensure parent record was saved before adding child

### "NETA_Standard not showing options"
- Verify choice column created with both "ATS" and "MTS" options
- Check that default value is set to "ATS"
- Refresh form if just added
- Verify choice is required

### "Financial tables visible to field techs"
- Security roles must REMOVE table access, not just limit fields
- Use table-level security, not field-level
- Test with actual user account, not as admin
- Verify security role assignments are correct

### "Revenue calculation incorrect"
- Check formula: (Labor_Hours × Base_Rate) × (1 + Applied_Multipliers) × Scope_Multiplier
- Verify Applied_Multipliers is SUM of all percentages (0.183 = 18.3% total)
- Ensure decimal precision is sufficient (4 decimals for multipliers)
- Power Automate flow will handle calculations automatically

---

## DOCUMENT CONTROL

**Document Owner:** Jason Smith, Phoenix Services Unit  
**Version:** 1.1  
**Date:** November 10, 2025  
**Alignment:** Master Build Specification v1.1  
**Purpose:** Complete step-by-step build guide for all 8 Dataverse tables  
**Classification:** Internal Use Only  

**Version History:**
- v1.0 (Nov 8, 2025): Initial "4 Tables" version - INCOMPLETE
- v1.1 (Nov 10, 2025): Complete 8-table version with:
  - Added Master Data tables (Locations, Apparatus_Type_Master)
  - Added Financial tables (Scope_Financial_Configuration, Apparatus_Revenue)
  - Organized into logical phases (Master → Operational → Financial)
  - Emphasized operational/financial separation architecture
  - Aligned completely with Master Build Specification v1.1

---

**END OF COMPLETE BUILD CHECKLIST**

*This document provides step-by-step instructions for building all 8 Dataverse tables in the correct order, with proper relationships, security configuration, and architectural alignment with the Master Build Specification. Follow each step carefully and check off as you complete them.*
