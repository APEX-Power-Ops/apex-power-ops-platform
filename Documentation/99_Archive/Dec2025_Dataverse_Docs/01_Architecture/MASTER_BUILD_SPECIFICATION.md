# RESA POWER PROJECT TRACKER
## Master Build Specification & Implementation Guide

**Version:** 3.0  
**Date:** November 27, 2025  
**Status:** ⚠️ PARTIAL UPDATE - Header aligned with v1.5.0.0, table sections need update  
**Project Owner:** Jason Swenson - Phoenix Services Unit  
**Project Type:** Excel-to-Power Apps Modernization  
**Scope:** Southwest Region (Phoenix, Las Vegas, Denver, San Diego)

> **VERSION 3.0 NOTES (November 2025)**:
> - **Solution Version:** v1.5.0.0 (deployed)
> - **Table Count:** 16 tables (was 8 in v1.3.x)
> - **Field Count:** 649 custom fields (was "350+")
> - **Rollup Fields:** 65 rollup/calculated fields added in v1.5.0.0
>
> **Tables Added in v1.4.0.0:** Client, Site, Employee, Quote, ResourceAssignment, Equipment  
> **Tables Added in v1.5.0.0:** ProjectFinancialSummary, ScopeFinancialSummary  
>
> **⚠️ DOCUMENTATION GAP:** Table sections below still reflect v1.3.0.4 structure.  
> See `VS_CLAUDE_MASTER_BUILD_TASK.md` for full update checklist.  
> See `VERSION_HISTORY.md` for accurate version progression.

---

## EXECUTIVE SUMMARY

### Project Objective
Modernize RESA Power's Excel-based electrical testing project tracking system into a comprehensive Microsoft Power Apps solution with earned value management capabilities. The system will track individual electrical apparatus completion and automatically calculate billable revenue when equipment testing is marked complete.

### Business Value
- **Eliminate manual data re-entry** from estimates to project tracker
- **Individual apparatus tracking** for precise completion and revenue recognition
- **Automated revenue calculation** based on equipment completion
- **Separation of operational and financial data** for appropriate access control
- **Scalable architecture** supporting company growth

### Key Success Criteria
1. Import capability from existing Excel estimators
2. Individual apparatus completion tracking (e.g., 1,847 items for LASNAP16)
3. Automatic revenue recognition upon apparatus completion
4. Field technicians can update completion status without seeing financial data
5. Project managers have full visibility into project performance

---

## TABLE OF CONTENTS

1. [System Architecture Overview](#system-architecture-overview)
2. [Data Model & Table Specifications](#data-model--table-specifications)
3. [Master Data Tables](#master-data-tables)
4. [Transactional Data Tables](#transactional-data-tables)
5. [Global Choices](#global-choices)
6. [Excel Estimator Integration](#excel-estimator-integration)
7. [Import Process Specification](#import-process-specification)
8. [Calculated Fields & Business Rules](#calculated-fields--business-rules)
9. [Security & Access Control](#security--access-control)
10. [Implementation Phases](#implementation-phases)
11. [Testing & Validation](#testing--validation)
12. [Appendices](#appendices)

---

## SYSTEM ARCHITECTURE OVERVIEW

### Architecture Principles

1. **Job Number is Primary Business Key**
   - Job Numbers are system-generated, sequential, company-wide
   - Currently in 674XXX range, will grow to 7 digits
   - NOT related to Location Codes (separate metadata)

2. **Business Unit Code Hierarchy**
   - 3-digit codes identify RESA Power business units (e.g., 575=San Diego, 645=Phoenix)
   - Independent from Job Numbers
   - Master table (BusinessUnit) manages location/office data

3. **Full Project Identifier (Context-Dependent)**
   - **Short Display:** `674414 - Goodman - LASNAP16`
   - **Full Display:** `PHX-674414 - Goodman - LASNAP16`
   - Use full display for reports, cross-location views, documents
   - Use short display for lists, dropdowns, daily operations

4. **Individual Apparatus Tracking**
   - Each apparatus = one testable unit = one record
   - "19x Transformer" in Excel → 19 separate records in Dataverse
   - Revenue recognized per apparatus upon completion

5. **Operational vs Financial Data Separation**
   - **Operational:** Projects, Scopes, Tasks, Apparatus (visible to field techs)
   - **Financial:** Rates, markups, revenue (restricted to PM/Admin)
   - ScopeLaborDetail table stores sensitive financial configuration data

6. **NETA Standard Architecture**
   - **ATS (Acceptance Testing Specifications):** For new installations and commissioning
   - **MTS (Maintenance Testing Specifications):** For existing equipment maintenance
   - NETA Standard defined at Scope level, enforced in Tasks and Apparatus
   - Each Apparatus Type has both ATS and MTS specifications

### Technology Stack

- **Platform:** Microsoft Power Platform
- **Data Storage:** Microsoft Dataverse
- **Apps:** Power Apps (Canvas & Model-Driven)
- **Automation:** Power Automate
- **Integration:** Excel estimators via import process
- **Reporting:** Power BI (future consideration)

### Data Flow Architecture

```
Excel Estimator (existing tool)
    ↓
Project_Data Sheet (new import template)
    ↓
Import Process (Power Automate or Python)
    ↓
Dataverse Tables:
    - Projects
    - Scopes (with NETA_Standard: ATS or MTS)
    - Scope_Financial_Configuration
    - Tasks (manual creation by PM)
    - Apparatus (expanded from quantities)
    ↓
Power Apps Canvas App
    ↓
Field Technicians → Update completion status
    ↓
Revenue Recognition (automatic on completion)
```

### Key Relationships

```
BusinessUnit (1) ←──→ (Many) Projects
    ↓
Projects (1) ←──→ (Many) Scopes
    ↓
Scopes (1) ←──→ (1) ScopeLaborDetail
Scopes (1) ←──→ (Many) Tasks
    ↓
Tasks (1) ←──→ (Many) Apparatus
    ↓
ApparatusTypeMaster (1) ←──→ (Many) Apparatus
Apparatus (1) ←──→ (N) ApparatusRevenue
```

---

## DATA MODEL & TABLE SPECIFICATIONS

### Entity Relationship Diagram (ERD)

```
┌─────────────────┐
│  BUSINESSUNIT   │ (Master Data)
│  - BusinessUnit_ID (PK)
│  - Business_Unit_Name
│  - City, State, Zip
└────────┬────────┘
         │ 1:N
         ↓
┌─────────────────────────────┐
│       PROJECTS              │
│  - Project_ID (PK)          │
│  - BusinessUnit (FK)        │
│  - Project_Name             │
│  - Customer_Name            │
│  - Customer_Short_Name      │
│  - Description              │
│  - Project_Manager          │
│  - Contract_Value           │
│  - Estimate_Version         │
│  - Status                   │
└────────┬────────────────────┘
         │ 1:N
         ↓
┌────────────────────────────┐
│        SCOPES              │
│  - Scope_ID (PK)           │
│  - Job_Number (FK)         │
│  - Scope_Name              │
│  - NETA_Standard (ATS/MTS) │ ⭐ NEW
│  - SLD_Reference           │
│  - Status                  │
│  - Total_App_Hours         │
└────┬───────────┬───────┬───┘
     │ 1:1       │ 1:N   │ 1:N
     ↓           ↓       ↓
┌──────────────┐ ┌─────────────┐  ┌────────────────────────┐
│ SCOPLABOR-   │ │    TASKS    │  │      APPARATUS         │ ⭐ OPERATIONAL DATA ONLY
│ DETAIL       │ │  - Task_ID  │  │  - Apparatus_ID (PK)   │
│  - Config_ID │ │  - Scope_FK │  │  - Project (FK)        │
│  - Scope_FK  │ │  - Task_Num │  │  - Scope (FK)          │
│  - Base_Rate │ │  - App_Type │  │  - Task (FK, optional) │
│  - Scope_Mul │ │  - NETA_Sec │  │  - Apparatus_Type (FK) │
│  - 49 fields │ └─────────────┘  │  - Labor_Hours         │
│  - FINANCE   │                  │  - Completion_Status   │
└──────────────┘                  │  - 20 fields total     │ ⭐
                                  └────┬──────────┬─────────┘
                                       │ N:1      │ 1:1
                                       ↓          ↓
                                                 ┌─────────────────────────┐
                                                 │  APPARATUS_REVENUE      │ ⭐ FINANCIAL DATA ONLY
                                                 │  - Revenue_ID (PK)      │
                                                 │  - Apparatus_ID (FK)    │
                                                 │  - Calculated_Revenue   │
                                                 │  - Revenue_Recog_Date   │
                                                 │  - Billing_Status       │
                                                 └─────────────────────────┘
                                       ↓
                                  ┌─────────────────────────────┐
                                  │ APPARATUS_TYPE_MASTER       │ (Master Data)
                                  │  - Apparatus_Type_ID (PK)   │
                                  │  - Apparatus_Type_Name      │
                                  │  - NETA_ATS_Section_Ref     │ ⭐ NEW
                                  │  - NETA_MTS_Section_Ref     │ ⭐ NEW
                                  │  - NETA_ATS_Labor_Hours     │ ⭐ NEW
                                  │  - NETA_MTS_Labor_Hours     │ ⭐ NEW
                                  │  - Category                 │
                                  └─────────────────────────────┘
```

### Table Summary

| Table Name | Type | Primary Key | Field Count | Purpose |
|-----------|------|-------------|-------------|---------|---------|  
| BusinessUnit | Master | BusinessUnit_ID (Auto) | 5 | Business unit/office locations |
| ApparatusTypeMaster | Master | ApparatusTypeMaster_ID (Auto) | 6 | Standard apparatus types with ATS/MTS specs |
| Projects | Transactional | Projects_ID (Auto) | 19 | Core project records with 8 rollup fields |
| ProjectScope | Transactional | Scope_ID (Auto) | 14 | Work breakdown structure with 8 rollup fields |
| Tasks | Transactional | Task_ID (Auto) | 14 | Task tracking with 8 rollup fields |
| ScopeLaborDetail | Financial | ScopeLaborDetail_ID (Auto) | 49 | Financial rates & config **RESTRICTED ACCESS** |
| Apparatus | Transactional | Apparatus_ID (Auto) | 20 | Individual testable units with quality tracking |
| ApparatusRevenue | Financial | ApparatusRevenue_ID (Auto) | 4 | Revenue recognition records **RESTRICTED ACCESS** |

**⭐ ARCHITECTURAL PRINCIPLE: Operational vs Financial Separation**
- **Operational Tables** (Projects, Scopes, Tasks, Apparatus): Field technician access
- **Financial Tables** (ScopeLaborDetail, ApparatusRevenue): Management/Billing only
- Security enforced at table level, not field level
- **v1.3.0.4 NOTE**: All 8 tables implemented and operational

---

## MASTER DATA TABLES

### TABLE 1: BUSINESSUNIT

**Purpose:** Master reference for RESA Power business unit/office locations (Southwest Region)

**Table Configuration:**
- **Table Type:** Standard Dataverse Table  
- **Schema Name:** cr950_BusinessUnit
- **Ownership:** Organization-owned
- **Primary Key:** BusinessUnit_ID (auto-number)
- **v1.3.0.4 NOTE:** Implemented with 5 custom fields

**Field Specifications:**

| Field Name | Data Type | Max Length | Required | Default | Searchable | Description |
|-----------|-----------|------------|----------|---------|------------|-------------|
| Business_Unit_Name | Single Line Text | 100 | Yes | - | Yes | Full business unit/office name |
| City | Single Line Text | 100 | No | - | Yes | City where office located |
| State | Single Line Text | 50 | No | - | Yes | State code (AZ, NV, CO, CA) |
| State | Single Line Text | 50 | No | - | Yes | State code (AZ, NV, CO, CA) |
| Zip_Code | Single Line Text | 20 | No | - | No | Postal code |
| Active | Yes/No | - | Yes | Yes | No | Enable/disable business unit |

**Implementation Notes (v1.3.0.4):**
- Original specification called this "Locations" with 3-digit codes as primary key
- Actual implementation uses "BusinessUnit" with auto-number primary key
- No "Location_Code" field exists; 3-digit codes (575, 610, 645, 670) may be embedded in Business_Unit_Name or used elsewhere
- Fields are simpler than originally specified (no Sort_Order, Office_Manager, etc.)
- Purpose: Track RESA Power office locations and/or project site locations

**Pre-Populated Data (verify in Dataverse):**

```
Likely includes:
- San Diego office (State: CA)
- Denver office (State: CO)
- Phoenix office (State: AZ)
- Las Vegas office (State: NV)
```

**Business Rules:**
- Business_Unit_Name should be unique (not enforced, but recommended)
- Cannot deactivate business unit if active projects reference it

**Relationships:**
- **1:N with Projects** (One business unit has many projects via Projects.Location lookup)

**Views to Create:**
- Active Business Units (default view)
- All Business Units
- By State

**Security:**
- All users: Read access
- Administrators only: Create, Update, Delete

**Usage Verification Needed:**
- Confirm how 3-digit codes (575, 610, 645, 670) are used
- Verify if this tracks office locations vs project site locations
- Check if Projects.Location field is actively populated

---

### TABLE 2: APPARATUS_TYPE_MASTER

**Purpose:** Master reference for all electrical testing apparatus types with NETA ATS and MTS specifications

**Table Configuration:**
- **Table Type:** Standard Dataverse Table
- **Ownership:** Organization-owned
- **Primary Key:** Apparatus_Type_ID (auto-number)

**⭐ CRITICAL CHANGE:** This table now supports both NETA ATS (Acceptance Testing Specifications) and NETA MTS (Maintenance Testing Specifications), with separate section references and labor hours for each standard.

**Field Specifications:**

| Field Name | Data Type | Max Length | Required | Default | Searchable | Description |
|-----------|-----------|------------|----------|---------|------------|-------------|
| Apparatus_Type_ID | Auto Number | - | Auto | - | No | System-generated unique ID (PRIMARY KEY) |
| Apparatus_Type_Name | Single Line Text | 200 | Yes | - | Yes | Full apparatus type name |
| Category | Choice | - | Yes | - | Yes | Equipment category (see choices below) |
| NETA_ATS_Section_Reference | Single Line Text | 50 | No | - | Yes | ⭐ NETA '25 ATS section number |
| NETA_MTS_Section_Reference | Single Line Text | 50 | No | - | Yes | ⭐ NETA '23 MTS section number |
| NETA_ATS_Labor_Hours | Decimal | - | No | - | No | ⭐ Default labor hours for ATS testing |
| NETA_MTS_Labor_Hours | Decimal | - | No | - | No | ⭐ Default labor hours for MTS testing |
| Description | Multiple Lines Text | - | No | - | No | Equipment description and notes |
| Active | Yes/No | - | Yes | Yes | No | Enable/disable apparatus type |
| Sort_Order | Whole Number | - | No | - | No | Display sequence within category |
| Date_Added | Date Only | - | Auto | Today | No | When record was created |
| Last_Modified | Date Only | - | Auto | Today | No | Last update date |

**⭐ NETA STANDARDS EXPLANATION:**

**ATS (Acceptance Testing Specifications) - NETA '25:**
- Used for NEW installations and commissioning projects
- Testing standards for equipment being placed into service
- More comprehensive initial testing requirements

**MTS (Maintenance Testing Specifications) - NETA '23:**
- Used for EXISTING equipment and ongoing maintenance
- Testing standards for equipment already in service
- Periodic maintenance and testing protocols

**How It Works:**
1. Each Scope has a NETA_Standard field (ATS or MTS)
2. When creating apparatus, the system looks up the appropriate section reference and labor hours based on the Scope's NETA_Standard
3. If Scope uses ATS → use NETA_ATS_Section_Reference and NETA_ATS_Labor_Hours
4. If Scope uses MTS → use NETA_MTS_Section_Reference and NETA_MTS_Labor_Hours

**Category Choice Values:**

```
- Transformers
  - Distribution Transformers
  - Power Transformers
  - Pad Mount Transformers
  - Dry Type Transformers
  - Instrument Transformers (CT/PT)
  
- Switchgear & Switchboards
  - Low Voltage Switchgear
  - Medium Voltage Switchgear
  - Motor Control Centers (MCC)
  - Switchboards
  
- Circuit Breakers
  - Low Voltage Breakers
  - Medium Voltage Breakers
  - Molded Case Breakers
  - Insulated Case Breakers
  - Air Circuit Breakers
  
- Protective Devices
  - Relays (Electromechanical)
  - Relays (Solid State/Microprocessor)
  - Ground Fault Protection
  - Surge Protective Devices (SPD)
  
- Cables & Conductors
  - Power Cables
  - Control Cables
  - Cable Terminations
  - Bus Duct
  
- Rotating Machinery
  - Motors
  - Generators
  - Motor Drives (VFD)
  
- Batteries & UPS
  - Battery Systems
  - UPS Systems
  - Battery Chargers
  
- Other Equipment
  - Transfer Switches
  - Panelboards
  - Load Banks
  - Grounding Systems
```

**Sample Data (showing new 4-column structure):**

| Apparatus_Type_Name | Category | ATS_Section | MTS_Section | ATS_Hours | MTS_Hours |
|---------------------|----------|-------------|-------------|-----------|-----------|
| Transformer - Pad Mount Oil | Transformers | 7.2 | 7.2 | 12.0 | 8.0 |
| Switchgear - 15kV | Switchgear | 7.5 | 7.5 | 16.0 | 10.0 |
| Circuit Breaker - Low Voltage | Circuit Breakers | 7.6 | 7.6 | 2.5 | 1.5 |
| Motor - Induction | Rotating Machinery | 7.8 | 7.8 | 4.0 | 2.5 |
| UPS System | Batteries & UPS | 7.12 | 7.12 | 8.0 | 6.0 |

**Business Rules:**
- Apparatus_Type_Name must be unique
- At least one of ATS or MTS section/hours must be populated
- Category is required
- Cannot delete apparatus type if referenced by any apparatus records

**Relationships:**
- **1:N with Apparatus** (One apparatus type has many apparatus records)

**Views to Create:**
- Active Apparatus Types (default)
- By Category
- ATS Testing Types (where ATS fields populated)
- MTS Testing Types (where MTS fields populated)
- All Apparatus Types

**Security:**
- All users: Read access
- Project Managers: Read access
- Administrators only: Create, Update, Delete

**Data Import Considerations:**
- Existing data in NETA_Spec_Reference → Determine if ATS or MTS based
- Existing Default_Labor_Hours → Map to appropriate ATS or MTS column
- For most current projects (new installations) → Likely ATS values
- Historical maintenance projects → Likely MTS values

---

## TRANSACTIONAL DATA TABLES

### TABLE 3: PROJECTS

**Purpose:** Core project records tracking electrical testing projects

**Table Configuration:**
- **Table Type:** Standard Dataverse Table
- **Schema Name:** cr950_Projects
- **Ownership:** User-owned
- **Primary Key:** Projects_ID (auto-number)
- **v1.3.0.4 NOTE:** Implemented with 19 custom fields (includes 8 rollup fields)

**Field Specifications:**

| Field Name | Data Type | Max Length | Required | Default | Searchable | Description |
|-----------|-----------|------------|----------|---------|------------|-------------|
| Project_Number | Single Line Text | 50 | Yes | - | Yes | Company job number (e.g., "674414") |
| Project_Name | Single Line Text | 200 | Yes | - | Yes | Internal project identifier (e.g., "LASNAP16") |
| Location | Lookup | - | No | - | Yes | Lookup to BusinessUnit table (optional) |
| Customer | Lookup | - | No | - | Yes | Lookup to Account (standard Dynamics entity) |
| Project_Manager | Single Line Text | 100 | No | - | Yes | Assigned PM name |
| Project_Status | Choice | - | Yes | "Quoted" | Yes | Project status (Quoted/Planning/Active/Completed) |
| Project_Start_Date | Date Only | - | No | - | No | Project start date |
| Project_End_Date | Date Only | - | No | - | No | Project target completion date |
| Description | Multiple Lines Text | - | No | - | Yes | Project description and scope notes |

**Rollup Fields (8 total):**

| Field Name | Source | Aggregation | Filter | Description |
|-----------|--------|-------------|--------|-------------|
| Total_Apparatus_Count | Apparatus | COUNT | All | Total number of apparatus in project |
| Completed_Apparatus_Count | Apparatus | COUNT | Completion_Status = "Complete" | Number completed |
| Total_Apparatus_Hours | Apparatus | SUM | Labor_Hours | Sum of quoted labor hours |
| Total_Completed_Hours | Apparatus | SUM | Completed_Hours | Sum of hours from completed apparatus |
| Total_Actual_Hours | Apparatus | SUM | Actual_Hours | Sum including delays |
| Total_Delays | Apparatus | SUM | Delays | Sum of all delay hours |
| Total_Remaining_Hours | Calculated | - | Total_Apparatus_Hours - Total_Completed_Hours | Remaining work |
| Percent_Complete | Calculated | - | (Completed_Apparatus_Count / Total_Apparatus_Count) * 100 | Completion % |

**Implementation Notes (v1.3.0.4):**
- Uses auto-number primary key (Projects_ID), not manual Job_Number field
- Project_Number field stores the job number as text
- Location lookup goes to BusinessUnit (not "Locations" table)
- Customer lookup uses standard Account entity
- All 8 rollup fields aggregate directly from Apparatus (not from Scopes)
- Field count: 19 custom fields total (11 base fields + 8 rollups)

**Business Rules:**
- Project_Number recommended to be unique (not enforced)
- Project_Status workflow: Quoted → Planning → Active → Completed
- All rollups recalculate automatically when apparatus updated

**Relationships:**
- **N:1 with BusinessUnit** (Many projects can reference one business unit via Location lookup)
- **N:1 with Account** (Many projects belong to one customer)
- **1:N with ProjectScope** (One project has many scopes)
- **1:N with Tasks** (One project has many tasks - convenience lookup)
- **1:N with Apparatus** (One project has many apparatus - convenience lookup)

**Views to Create:**
- Active Projects (Status = Active)
- All Projects
- By Business Unit
- By Customer
- Completed Projects

**Security:**
- Project Managers: Full access
- Field Technicians: Read access
- Administrators: Full access

---

### TABLE 4: PROJECTSCOPE

**Purpose:** Work breakdown structure defining testing scopes within projects

**Table Configuration:**
- **Table Type:** Standard Dataverse Table
- **Schema Name:** cr950_ProjectScope
- **Ownership:** User-owned
- **Primary Key:** Scope_ID (auto-number)
- **v1.3.0.4 NOTE:** Implemented with 14 custom fields (includes 8 rollup fields)

**Field Specifications:**

| Field Name | Data Type | Max Length | Required | Default | Searchable | Description |
|-----------|-----------|------------|----------|---------|------------|-------------|
| Scope_Name | Single Line Text | 200 | Yes | - | Yes | Scope description/name |
| Project | Lookup | - | Yes | - | Yes | Lookup to Projects table (required parent) |
| Scope_Labor_Detail | Lookup | - | No | - | Yes | Lookup to ScopeLaborDetail (1:1 financial config) |
| NETA_Standard | Choice | - | Yes | "ATS" | Yes | Testing standard (ATS or MTS) |
| SLD_Reference | Single Line Text | 100 | No | - | Yes | Single line diagram reference |

**Rollup Fields (8 total - same pattern as Projects):**

| Field Name | Source | Aggregation | Filter | Description |
|-----------|--------|-------------|--------|-------------|
| Total_Apparatus_Count | Apparatus | COUNT | All | Number of apparatus in scope |
| Completed_Apparatus_Count | Apparatus | COUNT | Completion_Status = "Complete" | Number completed |
| Total_Apparatus_Hours | Apparatus | SUM | Labor_Hours | Sum of quoted hours |
| Total_Completed_Hours | Apparatus | SUM | Completed_Hours | Sum of completed work |
| Total_Actual_Hours | Apparatus | SUM | Actual_Hours | Sum including delays |
| Total_Delays | Apparatus | SUM | Delays | Sum of delay hours |
| Total_Remaining_Hours | Calculated | - | Total_Apparatus_Hours - Total_Completed_Hours | Remaining work |
| Percent_Complete | Calculated | - | (Completed_Apparatus_Count / Total_Apparatus_Count) * 100 | Completion % |

**Implementation Notes (v1.3.0.4):**
- Field count: 14 custom fields total (6 base + 8 rollups)
- Original specification estimated 39 fields (incorrect - likely confused with ScopeLaborDetail's 49 fields)
- Scope_Labor_Detail lookup provides 1:1 relationship to financial configuration
- All 8 rollups aggregate directly from Apparatus table
- NETA_Standard choice determines which testing standards apply

**NETA_Standard Choice Values:**
- ATS (Acceptance Testing Specifications) - New installations
- MTS (Maintenance Testing Specifications) - Existing equipment
- Determines which hours/sections used from ApparatusTypeMaster

**Business Rules:**
- Project lookup is required (parent relationship)
- NETA_Standard determines testing specifications used
- All rollups recalculate when apparatus updated

**Relationships:**
- **N:1 with Projects** (Many scopes belong to one project)
- **1:1 with ScopeLaborDetail** (One scope has one financial config via Scope_Labor_Detail lookup)
- **1:N with Tasks** (One scope has many tasks)
- **1:N with Apparatus** (One scope has many apparatus)

**Views to Create:**
- Active Scopes
- By Project
- By NETA Standard (ATS/MTS)
- All Scopes

**Security:**
- Project Managers: Full access
- Field Technicians: Read access
- Administrators: Full access

---

### TABLE 5: TASKS

**Security:**
- Project Managers: Full access
- Field Technicians: Read-only access to operational fields
- Administrators: Full access

**Import Considerations:**
- Excel Estimator Scope sheets have Cell C3 (merged cell) containing "ATS" or "MTS"
- This value maps directly to NETA_Standard field during import
- Import process validates Cell C3 contains valid value before proceeding

---

### TABLE 5: TASKS

**Purpose:** Task-level organization of apparatus items within scopes

**Table Configuration:**
- **Table Type:** Standard Dataverse Table
- **Ownership:** User-owned
- **Primary Key:** Task_ID (auto-number)

**⭐ CRITICAL CLARIFICATION - IMPLEMENTATION STATUS:**

**✅ IMMEDIATE IMPLEMENTATION (Phase 1)**
- Tasks table is built alongside Projects, Scopes, and Apparatus
- Created manually by Project Managers in Power Apps
- Provides organizational structure for grouping similar apparatus

**🚫 NOT PART OF EXCEL IMPORT**
- Excel estimators have no task-level structure to import from
- Import process creates: Project → Scopes → Apparatus only
- Tasks are created manually after import by PMs as needed

**When to Create Tasks:**
- After importing project data from Excel
- To group apparatus by equipment type (e.g., "All Transformers")
- To assign work packages to specific technicians
- To organize complex scopes with many apparatus types

**Field Specifications:**

| Field Name | Data Type | Max Length | Required | Default | Searchable | Description |
|-----------|-----------|------------|----------|---------|------------|-------------|
| Task_ID | Auto Number | - | Auto | - | No | System-generated unique ID (PRIMARY KEY) |
| Scope_ID | Lookup | - | Yes | - | Yes | Lookup to Scopes table (PARENT) |
| Job_Number | Lookup | - | Yes | - | Yes | Lookup to Projects table |
| Task_Number | Whole Number | - | Yes | - | Yes | Sequential task number within scope |
| Task_Name | Single Line Text | 200 | Yes | - | Yes | Task description/name |
| Apparatus_Type | Single Line Text | 200 | No | - | Yes | Primary apparatus type for this task |
| NETA_Section | Single Line Text | 50 | No | - | Yes | NETA section reference (inherited from scope's standard) |
| Status | Choice | - | Yes | "Not Started" | Yes | Task status (see Global Choices) |
| Priority | Choice | - | No | "Medium" | Yes | Task priority (see Global Choices) |
| Assigned_To | Single Line Text | 100 | No | - | Yes | Assigned technician name |
| Apparatus_Hours | Decimal | - | No | - | No | Total estimated hours (rollup from apparatus) |
| Target_Start | Date Only | - | No | - | No | Planned start date |
| Target_Completion | Date Only | - | No | - | No | Planned completion date |
| Notes | Multiple Lines Text | - | No | - | No | Task notes and instructions |

**How NETA Section Populates:**
1. Task is created under a Scope
2. Scope has NETA_Standard = "ATS" or "MTS"
3. Task's Apparatus_Type links to Apparatus_Type_Master
4. If NETA_Standard = "ATS" → Pull NETA_ATS_Section_Reference
5. If NETA_Standard = "MTS" → Pull NETA_MTS_Section_Reference
6. Can be implemented via business rule or calculated field

**Rollup Fields:**

| Field Name | Source | Aggregation | Filter | Description |
|-----------|--------|-------------|--------|-------------|
| Total_Apparatus | Apparatus | COUNT | All | Number of apparatus in task |
| Completed_Apparatus | Apparatus | COUNT | Status = "Complete" | Completed apparatus count |
| Task_Apparatus_Hours | Apparatus | SUM | Apparatus_Hours | Sum of apparatus hours |
| Task_Earned_Revenue | Apparatus (via Financial) | SUM | Earned_Revenue | Sum of earned revenue |
| Percent_Complete | Calculated | - | (Completed_Apparatus / Total_Apparatus) * 100 | Task completion % |

**Business Rules:**
- Task_Number must be unique within each scope
- Status cannot be "Complete" if any apparatus are incomplete
- Assigned_To should be validated against user list
- Cannot delete task if apparatus records exist

**Relationships:**
- **N:1 with Scopes** (Many tasks belong to one scope)
- **N:1 with Projects** (Many tasks belong to one project)
- **1:N with Apparatus** (One task has many apparatus)

**Views to Create:**
- Active Tasks (Status <> Complete)
- My Tasks (Assigned_To = Current User)
- By Scope
- By Project
- Overdue Tasks
- All Tasks

**Security:**
- Project Managers: Full access
- Field Technicians: Read access to assigned tasks
- Administrators: Full access

**Manual Creation Workflow:**

```
After Excel Import:
1. PM reviews imported Scopes and Apparatus
2. PM creates Tasks to organize apparatus:
   - "Task 1: Pad Mount Transformers" (groups all PMT apparatus)
   - "Task 2: Switchgear Testing" (groups all switchgear apparatus)
   - "Task 3: Circuit Breaker Testing" (groups all breakers)
3. PM assigns apparatus to tasks using bulk edit or interface
4. PM assigns tasks to field technicians
5. Field techs update apparatus completion within their tasks
```

---

### TABLE 6: APPARATUS

**Purpose:** Individual testable equipment units - the atomic level of tracking

**Table Configuration:**
- **Table Type:** Standard Dataverse Table
- **Ownership:** User-owned
- **Primary Key:** Apparatus_ID (auto-number)

**Field Specifications:**

| Field Name | Data Type | Max Length | Required | Default | Searchable | Description |
|-----------|-----------|------------|----------|---------|------------|-------------|
| Apparatus_ID | Auto Number | - | Auto | - | No | System-generated unique ID (PRIMARY KEY) |
| Job_Number | Lookup | - | Yes | - | Yes | Lookup to Projects table |
| Scope_ID | Lookup | - | Yes | - | Yes | Lookup to Scopes table |
| Task_ID | Lookup | - | No | - | Yes | Lookup to Tasks table (Optional) |
| Apparatus_Number | Whole Number | - | Yes | - | Yes | Sequential number within scope |
| Hierarchy_ID | Single Line Text | 50 | No | - | Yes | Hierarchical reference (e.g., "1.2.3") |
| Apparatus_Designation | Single Line Text | 200 | Yes | - | Yes | Equipment tag/name (PRIMARY NAME) |
| Apparatus_Type_ID | Lookup | - | No | - | Yes | Lookup to Apparatus_Type_Master |
| Apparatus_Type_Name | Single Line Text | 200 | No | - | Yes | Type name (for cases without master link) |
| Apparatus_Hours | Decimal | - | Yes | - | No | Estimated test hours for this unit |
| Actual_Hours | Decimal | - | No | - | No | Actual hours spent (field tech entry) |
| Status | Choice | - | Yes | "Not Started" | Yes | Completion status (see Global Choices) |
| Priority | Choice | - | No | "Medium" | Yes | Work priority (see Global Choices) |
| Availability | Choice | - | No | "Available" | Yes | Equipment availability (see Global Choices) |
| Date_Started | Date Only | - | No | - | No | Date work began |
| Date_Completed | Date Only | - | No | - | No | Date work finished |
| Date_Due | Date Only | - | No | - | No | Target completion date |
| Description | Multiple Lines Text | - | No | - | No | Equipment description |
| Notes | Multiple Lines Text | - | No | - | No | Field tech notes and findings |

**⚠️ CRITICAL: ZERO FINANCIAL DATA**
This table contains ONLY operational data visible to field technicians. NO currency fields, NO rates, NO revenue calculations. All financial data is in the separate Apparatus_Revenue table (Phase 2) or Scope_Financial_Configuration.

**Calculated Fields:**

| Field Name | Formula | Type | Description |
|-----------|---------|------|-------------|
| Remaining_Hours | `Apparatus_Hours - Actual_Hours` | Decimal | Hours remaining |
| Percent_Complete | `(Actual_Hours / Apparatus_Hours) * 100` | Decimal | Completion percentage |
| Is_Overdue | `Date_Due < Today() AND Status <> "Complete"` | Yes/No | Overdue indicator |
| Days_Since_Completed | `DATEDIFF(Date_Completed, Today(), Days)` | Number | Days since completion |
| Full_Apparatus_ID | `Full_Scope_ID & "." & Apparatus_Number` | Text | Complete hierarchical ID |

**How NETA Section Applies to Apparatus:**
1. Apparatus belongs to a Scope
2. Scope has NETA_Standard = "ATS" or "MTS"
3. Apparatus links to Apparatus_Type_Master
4. System retrieves appropriate section and hours:
   - If ATS → Use NETA_ATS_Section_Reference & NETA_ATS_Labor_Hours
   - If MTS → Use NETA_MTS_Section_Reference & NETA_MTS_Labor_Hours
5. Can display NETA section in views without storing redundantly

**Business Rules:**
- Apparatus_Number must be unique within each scope
- Status = "Complete" requires Date_Completed
- Date_Completed cannot be in future
- Actual_Hours cannot exceed Apparatus_Hours * 2 (safety limit)
- Cannot delete apparatus if revenue record exists

**Relationships:**
- **N:1 with Projects** (Many apparatus belong to one project)
- **N:1 with Scopes** (Many apparatus belong to one scope)
- **N:1 with Tasks** (Many apparatus belong to one task - OPTIONAL)
- **N:1 with Apparatus_Type_Master** (Many apparatus link to one type)
- **1:1 with Apparatus_Revenue** (One apparatus has one revenue record - Phase 2)

**Views to Create:**
- Active Apparatus (Status <> Complete)
- My Apparatus (filtered by assigned task)
- By Project
- By Scope
- By Status
- Overdue Apparatus
- Completed Today
- ATS Apparatus (via scope NETA standard) ⭐ NEW
- MTS Apparatus (via scope NETA standard) ⭐ NEW
- All Apparatus

**Security:**
- Project Managers: Full access
- Field Technicians: Read/Write on Status, Actual_Hours, Dates, Notes only
- Administrators: Full access

**Excel Import:**
- Each row in estimator with Qty > 1 creates multiple apparatus records
- Example: "3x Transformer - Pad Mount" → Creates 3 separate Apparatus records
- Apparatus_Number sequences automatically within scope
- Hierarchy_ID preserved from Excel if available

---

### TABLE 7: SCOPE_FINANCIAL_CONFIGURATION

**Purpose:** Stores all sensitive financial data separate from operational tables

**Table Configuration:**
- **Table Type:** Standard Dataverse Table
- **Ownership:** User-owned
- **Primary Key:** Config_ID (auto-number)

**Field Specifications:**

| Field Name | Data Type | Precision | Required | Default | Description |
|-----------|-----------|-----------|----------|---------|-------------|
| Config_ID | Auto Number | - | Auto | - | System-generated unique ID (PRIMARY KEY) |
| Scope_ID | Lookup | - | Yes | - | Lookup to Scopes table (1:1 relationship) |
| Base_Rate | Currency | 2 decimals | No | - | Base hourly labor rate |
| Base_Percent | Decimal | 3 decimals | No | - | Base rate markup percentage |
| Commute_Rate | Currency | 2 decimals | No | - | Commute time hourly rate |
| Commute_Percent | Decimal | 3 decimals | No | - | Commute rate markup percentage |
| PM_Rate | Currency | 2 decimals | No | - | Project management hourly rate |
| PM_Percent | Decimal | 3 decimals | No | - | PM rate markup percentage |
| Daily_Report_Rate | Currency | 2 decimals | No | - | Daily reporting hourly rate |
| Daily_Report_Percent | Decimal | 3 decimals | No | - | Daily report markup percentage |
| Travel_Rate | Currency | 2 decimals | No | - | Travel time hourly rate |
| Travel_Percent | Decimal | 3 decimals | No | - | Travel markup percentage |
| Final_Report_Rate | Currency | 2 decimals | No | - | Final report hourly rate |
| Final_Report_Percent | Decimal | 3 decimals | No | - | Final report markup percentage |
| Fixed_Cost_Travel | Currency | 2 decimals | No | - | Fixed travel costs |
| Fixed_Cost_ME | Currency | 2 decimals | No | - | Fixed meals & entertainment costs |
| Scope_Multiplier | Decimal | 3 decimals | No | 1.000 | Scope-level multiplier |
| Notes | Multiple Lines Text | - | No | - | Configuration notes |

**Business Rules:**
- One Config record per Scope (1:1 relationship enforced)
- All percent fields should be between 0 and 1 (0% to 100%)
- Rates cannot be negative
- Scope_Multiplier minimum value = 0.1

**Relationships:**
- **1:1 with Scopes** (One config belongs to one scope)

**Views to Create:**
- By Scope
- Active Configurations (where Scope.Status <> Complete)
- All Configurations

**Security:**
- ⚠️ CRITICAL: Field-level security required
- Project Managers: Full access
- Field Technicians: NO ACCESS (cannot read financial data)
- Administrators: Full access
- Use Field Security Profiles to restrict all fields except Scope_ID

**Excel Import:**
- Created automatically during scope import
- Reads from "Scope_Labor_Rates" section of scope sheet
- Maps rate and percent pairs from Excel columns

---

### TABLE 8: APPARATUS_REVENUE

**Purpose:** Tracks revenue recognition for completed apparatus - completely separate from operational data

**Table Configuration:**
- **Table Type:** Standard Dataverse Table
- **Ownership:** User-owned
- **Primary Key:** Revenue_ID (auto-number)

**⭐ CRITICAL: AUTO-GENERATED BY POWER AUTOMATE**
- This table is NOT typically manually populated
- Records created automatically when Apparatus.Completion_Status = "Complete"
- Power Automate flow reads Scope_Financial_Configuration and calculates revenue
- Maintains complete separation between operational and financial data layers

**Field Specifications:**

| Field Name | Data Type | Precision | Required | Default | Description |
|-----------|-----------|-----------|----------|---------|-------------|
| Revenue_ID | Auto Number | - | Auto | - | System-generated unique ID (PRIMARY KEY) |
| Apparatus_ID | Lookup | - | Yes | - | Lookup to Apparatus table (1:1 relationship) |
| Scope_ID | Lookup | - | Yes | - | Lookup to Scopes table (for rollups) |
| Job_Number | Lookup | - | Yes | - | Lookup to Projects table (for rollups) |
| Labor_Hours | Decimal | 2 decimals | Yes | - | Hours from Apparatus (snapshot at completion) |
| Base_Labor_Rate | Currency | 2 decimals | No | - | From Scope_Financial_Configuration |
| Applied_Multipliers | Decimal | 4 decimals | No | - | Sum of all percentage multipliers |
| Scope_Multiplier | Decimal | 3 decimals | No | 1.000 | From Scope_Financial_Configuration |
| Calculated_Revenue | Currency | 2 decimals | Yes | - | Auto-calculated revenue amount |
| Revenue_Recognized_Date | DateTime | - | Yes | - | Timestamp when revenue was recognized |
| Completed_By | Single Line Text | 100 | No | - | Technician who completed apparatus |
| Manual_Override_Revenue | Currency | 2 decimals | No | - | Manual adjustment (requires reason) |
| Manual_Override_Reason | Multiple Lines Text | - | No | - | REQUIRED if override used |
| Billing_Status | Choice | - | Yes | "Not Billed" | Billing status (see Global Choices) |
| Billed_Date | Date Only | - | No | - | Date invoiced to customer |
| Notes | Multiple Lines Text | - | No | - | Additional financial notes |

**Revenue Calculation Formula:**
```
Calculated_Revenue = (Labor_Hours × Base_Labor_Rate) × 
                    (1 + Applied_Multipliers) × 
                    Scope_Multiplier + 
                    (Proportional_Fixed_Costs)

Where Applied_Multipliers = Commute_Percent + PM_Percent + 
                            Daily_Report_Percent + Travel_Percent + 
                            Final_Report_Percent
```

**Power Automate Flow Trigger:**
1. **Trigger:** Apparatus.Completion_Status changes to "Complete"
2. **Actions:**
   - Retrieve Scope_Financial_Configuration for apparatus's scope
   - Extract all rates and multipliers
   - Calculate revenue using formula above
   - Create Apparatus_Revenue record
   - Populate all financial fields
   - Set Revenue_Recognized_Date to current timestamp
   - Copy Completed_By from Apparatus
3. **Result:** Complete financial record created without field tech seeing any financial data

**Business Rules:**
- One Revenue record per Apparatus (1:1 relationship enforced)
- Cannot delete revenue record once created (archive instead)
- Manual_Override_Revenue requires Manual_Override_Reason
- Cannot change Calculated_Revenue after creation (use override instead)
- Billing_Status workflow: Not Billed → Billed → Paid

**Relationships:**
- **1:1 with Apparatus** (One revenue record per apparatus)
- **N:1 with Scopes** (Many revenue records belong to one scope - for rollups)
- **N:1 with Projects** (Many revenue records belong to one project - for rollups)

**Views to Create:**
- Revenue by Project
- Revenue by Scope
- By Billing Status
- Unbilled Revenue (Status = "Not Billed")
- Revenue This Month
- Revenue by Technician (via Completed_By)
- Manual Overrides (where Override <> null)
- All Revenue Records

**Security:**
- ⚠️ CRITICAL: Table-level security required
- Project Managers: Full access
- Field Technicians: **NO ACCESS WHATSOEVER** (cannot read or write)
- Billing Team: Full access
- Administrators: Full access
- This is the cornerstone of operational/financial data separation

**Excel Import:**
- Typically NOT imported (auto-generated by Power Automate)
- **Exception:** Historical data migration from legacy systems
- If importing historical data:
  - Must have corresponding Apparatus_ID
  - Must manually populate all required fields
  - Set Revenue_Recognized_Date to historical date
  - Document import source in Notes field

**Rollup Usage:**
- Scopes.Total_Earned_Revenue = SUM(Apparatus_Revenue.Calculated_Revenue) where Scope_ID matches
- Projects.Total_Earned_Revenue = SUM(Apparatus_Revenue.Calculated_Revenue) where Job_Number matches
- Enables real-time financial dashboards without exposing data to field techs

---

## GLOBAL CHOICES

### Purpose
Global choices provide consistent dropdown values across all tables, ensuring data integrity and simplifying reporting.

### Global Choice Specifications

#### 1. resapower_workstatus
**Used in:** Projects, Scopes, Tasks, Apparatus

| Label | Value | Color | Description |
|-------|-------|-------|-------------|
| Not Started | 1 | Gray | Work has not begun |
| In Progress | 2 | Blue | Work is actively underway |
| Complete | 3 | Green | Work is finished |
| On Hold | 4 | Yellow | Work is temporarily paused |
| Cancelled | 5 | Red | Work has been cancelled |

#### 2. resapower_priority
**Used in:** Projects, Scopes, Tasks, Apparatus

| Label | Value | Color | Description |
|-------|-------|-------|-------------|
| Low | 1 | Blue | Low priority work |
| Medium | 2 | Yellow | Standard priority |
| High | 3 | Red | Urgent priority |

#### 3. resapower_availability
**Used in:** Apparatus

| Label | Value | Color | Description |
|-------|-------|-------|-------------|
| Available | 1 | Green | Equipment ready for testing |
| On Hold | 2 | Yellow | Temporarily unavailable |
| Not Available | 3 | Red | Equipment not accessible |

#### 4. ⭐ resapower_netastandard (NEW)
**Used in:** Scopes

| Label | Value | Color | Description |
|-------|-------|-------|-------------|
| ATS | 1 | Blue | Acceptance Testing Specifications (NETA '25) - New installations |
| MTS | 2 | Green | Maintenance Testing Specifications (NETA '23) - Existing equipment |

**Inheritance Pattern:**
- Defined at Scope level
- Determines which NETA section references and labor hours are used
- Cascades to all Tasks and Apparatus within scope
- Cannot be changed once Tasks or Apparatus exist

#### 5. resapower_apparatuscategory
**Used in:** Apparatus_Type_Master

| Label | Value | Description |
|-------|-------|-------------|
| Transformers | 1 | All transformer types |
| Switchgear & Switchboards | 2 | Switchgear, MCC, switchboards |
| Circuit Breakers | 3 | All breaker types |
| Protective Devices | 4 | Relays, SPD, ground fault |
| Cables & Conductors | 5 | Power cables, bus duct |
| Rotating Machinery | 6 | Motors, generators, drives |
| Batteries & UPS | 7 | Battery systems, UPS |
| Other Equipment | 8 | Miscellaneous equipment |

---

## EXCEL ESTIMATOR INTEGRATION

### Current Excel Architecture

**Estimator Workbook Structure:**
- **Project_Data** Sheet (NEW - to be added)
- **Scope Sheets** (multiple, one per scope)
- **Equipment_Reference** Sheet (master apparatus types with NETA specs)

### ⭐ NETA Standard in Excel Estimator

**Scope Sheet Cell C3:**
- Merged cell containing either "ATS" or "MTS"
- Determines which NETA specifications are used for that scope
- Data Validation (DV) formulas reference this cell to pull:
  - Correct NETA section numbers
  - Correct labor hours
  - From appropriate columns in Equipment_Reference sheet

**Equipment_Reference Sheet Structure:**
```
Column A: Apparatus Type Name
Column B: Category
Column C: NETA '25 ATS Section
Column D: NETA '23 MTS Section
Column E: ATS Labor Hours
Column F: MTS Labor Hours
Column G-K: Other specifications
```

**How DV Works in Scope Sheets:**
- IF Cell C3 = "ATS" THEN use Columns C & E (ATS section, ATS hours)
- IF Cell C3 = "MTS" THEN use Columns D & F (MTS section, MTS hours)
- This ensures correct standards are applied to each apparatus line item

### Import Process Requirements

**Phase 1 Import (Current):**
1. Read Project_Data sheet → Create Project record
2. For each Scope sheet listed:
   - Read Cell C3 → Capture NETA_Standard (ATS/MTS)
   - Read scope header → Create Scope record with NETA_Standard
   - Read financial rates → Create Scope_Financial_Configuration
   - Read apparatus rows → Create Apparatus records
   - Expand quantities (3x → 3 separate records)

**⚠️ Tasks NOT Imported:**
- Excel has no task-level structure
- Import creates: Project → Scopes → Apparatus only
- Tasks created manually by PMs after import

**NETA Standard Import Logic:**
```python
# Pseudocode for scope import
def import_scope(scope_sheet):
    # Read NETA Standard from Cell C3
    neta_standard = scope_sheet.cell(row=3, column=3).value  # C3
    
    if neta_standard not in ['ATS', 'MTS']:
        raise ValueError(f"Invalid NETA Standard in C3: {neta_standard}")
    
    # Create scope with NETA_Standard
    scope_data = {
        'Scope_Name': scope_sheet.cell(row=5, column=2).value,
        'NETA_Standard': neta_standard,  # Maps to choice field
        # ... other fields
    }
    
    # For each apparatus, determine which specs to use
    for apparatus_row in apparatus_rows:
        apparatus_type = apparatus_row['type']
        
        # Lookup from Apparatus_Type_Master based on NETA_Standard
        if neta_standard == 'ATS':
            neta_section = lookup_ats_section(apparatus_type)
            labor_hours = lookup_ats_hours(apparatus_type)
        else:  # MTS
            neta_section = lookup_mts_section(apparatus_type)
            labor_hours = lookup_mts_hours(apparatus_type)
        
        create_apparatus(apparatus_row, neta_section, labor_hours)
```

---

## CALCULATED FIELDS & BUSINESS RULES

### Calculated Fields Summary

| Table | Field | Formula | Purpose |
|-------|-------|---------|---------|
| Projects | Full_Project_Display | Location_Abbr & "-" & Job_Number & " - " & Customer_Short_Name & " - " & Project_Name | Standard display format |
| Projects | Is_Overdue | Target_Completion < Today() AND Status <> "Complete" | Overdue flag |
| Scopes | Days_In_Progress | DATEDIFF(Actual_Start, Today(), Days) | Track duration |
| Scopes | Percent_Complete | (Completed_Apparatus / Total_Apparatus) * 100 | Progress tracking |
| Apparatus | Remaining_Hours | Apparatus_Hours - Actual_Hours | Work remaining |
| Apparatus | Percent_Complete | (Actual_Hours / Apparatus_Hours) * 100 | Completion % |

### Rollup Fields Summary

| Table | Field | Source | Aggregation | Purpose |
|-------|-------|--------|-------------|---------|
| Projects | Total_Scopes | Scopes | COUNT | Scope count |
| Projects | Total_Earned_Revenue | Scopes | SUM | Revenue rollup |
| Scopes | Total_Apparatus | Apparatus | COUNT | Apparatus count |
| Scopes | Completed_Apparatus | Apparatus | COUNT (filtered) | Completion tracking |
| Tasks | Total_Apparatus | Apparatus | COUNT | Task size |
| Tasks | Task_Earned_Revenue | Apparatus Revenue | SUM | Revenue tracking |

### Business Rules

#### Rule 1: Project Completion Status
- **Trigger:** Status field change on Projects
- **Condition:** Status = "Complete"
- **Action:** Validate all child Scopes have Status = "Complete"
- **Error:** "Cannot complete project with incomplete scopes"

#### Rule 2: Scope Completion Status
- **Trigger:** Status field change on Scopes
- **Condition:** Status = "Complete"
- **Action:** Validate all child Apparatus have Status = "Complete"
- **Error:** "Cannot complete scope with incomplete apparatus"

#### Rule 3: Apparatus Completion Date
- **Trigger:** Status field change on Apparatus
- **Condition:** Status = "Complete" AND Date_Completed is empty
- **Action:** Auto-populate Date_Completed = Today()

#### Rule 4: ⭐ NETA Standard Immutability
- **Trigger:** NETA_Standard field change on Scopes
- **Condition:** Tasks or Apparatus records exist for this scope
- **Action:** Block change
- **Error:** "Cannot change NETA Standard when tasks or apparatus exist"

#### Rule 5: Date Validation
- **Trigger:** Date field changes
- **Condition:** Date_Completed < Date_Started
- **Action:** Block save
- **Error:** "Completion date cannot be before start date"

---

## SECURITY & ACCESS CONTROL

### Security Roles

#### 1. System Administrator
- **Access Level:** Full access to all tables, all records
- **Capabilities:**
  - Create/modify master data
  - Manage users and security
  - Configure system settings
  - View all financial data
  - Delete records

#### 2. Project Manager
- **Access Level:** Full access to assigned projects and related records
- **Capabilities:**
  - Create and manage projects
  - Create scopes, tasks, apparatus
  - View and edit financial configurations
  - Assign work to field technicians
  - Run reports
  - Cannot delete completed work

#### 3. Field Technician
- **Access Level:** Read/Write on operational fields only
- **Capabilities:**
  - View assigned projects, scopes, tasks
  - Update apparatus status
  - Enter actual hours
  - Add notes
  - **Cannot view:** Financial configurations, rates, revenue
  - **Cannot delete:** Any records

#### 4. Executive/Billing
- **Access Level:** Read-only on all data including financial
- **Capabilities:**
  - View all projects and financial data
  - Run reports
  - Export data
  - Cannot create or modify records

### Field-Level Security

**Scope_Financial_Configuration Table:**
- All currency and percent fields restricted to PM and Admin only
- Field Technicians have NO READ access to financial fields
- Implement via Field Security Profiles

**Implementation Steps:**
1. Create Field Security Profile: "Financial Data Access"
2. Add all currency/percent fields from Scope_Financial_Configuration
3. Grant "Read" permission to Project Manager and Admin roles
4. Ensure Field Technician role does NOT have this profile

---

## IMPLEMENTATION PHASES

### Phase 1: Foundation & Core Tables (Weeks 1-2)
**Status:** ✅ CURRENT PHASE

**Deliverables:**
- [ ] Create Dataverse environment
- [ ] Build all 7 core tables:
  - [ ] Locations (Master)
  - [ ] Apparatus_Type_Master (Master - with 4 NETA columns) ⭐
  - [ ] Projects (Transactional)
  - [ ] Scopes (Transactional - with NETA_Standard field) ⭐
  - [ ] Tasks (Transactional - MANUAL CREATION ONLY) ⭐
  - [ ] Apparatus (Transactional)
  - [ ] Scope_Financial_Configuration (Transactional)
- [ ] Configure all 5 global choices (including resapower_netastandard) ⭐
- [ ] Set up table relationships
- [ ] Create calculated and rollup fields
- [ ] Implement business rules (including NETA Standard immutability) ⭐
- [ ] Configure field-level security
- [ ] Create test data
- [ ] Verify all relationships working

**Success Criteria:**
- All tables accessible in Dataverse
- Relationships navigable
- Test records created for LASNAP16 with both ATS and MTS scopes ⭐
- Security roles functioning
- Apparatus linking to correct NETA specs based on Scope standard ⭐

---

### Phase 2: Excel Import Process (Weeks 3-4)

**Deliverables:**
- [ ] Add Project_Data sheet to Excel estimator template
- [ ] Update Equipment_Reference with 4 NETA columns (ATS/MTS) ⭐
- [ ] Develop import script (Python or Power Automate)
  - [ ] Read Cell C3 for NETA_Standard ⭐
  - [ ] Validate NETA_Standard value ⭐
  - [ ] Map to appropriate NETA specs based on standard ⭐
- [ ] Implement quantity expansion logic
- [ ] Handle financial configuration import
- [ ] Create import validation and error handling
- [ ] Test import with LASNAP16 (27 scopes, ~1,900 apparatus)
- [ ] Document import process
- [ ] Train PMs on import workflow

**⚠️ CRITICAL:** Tasks are NOT imported. PMs create tasks manually after import to organize apparatus.

**Success Criteria:**
- Successful import of full LASNAP16 project
- All 27 scopes imported with correct NETA_Standard ⭐
- 1,905 apparatus records created with correct specs
- Financial configurations populated
- Zero manual data re-entry required
- Import completes in < 10 minutes

---

### Phase 3: Canvas App Development (Weeks 5-7)

**Deliverables:**
- [ ] Design app navigation and UX
- [ ] Build technician-facing screens:
  - [ ] My Tasks view
  - [ ] Apparatus completion interface
  - [ ] Status update forms
  - [ ] Notes entry
- [ ] Build PM-facing screens:
  - [ ] Project dashboard
  - [ ] Scope management
  - [ ] Task creation and assignment ⭐
  - [ ] Financial configuration
  - [ ] Progress tracking
- [ ] Implement offline capability
- [ ] Configure security and permissions
- [ ] Test on mobile devices
- [ ] User acceptance testing

**Success Criteria:**
- Field techs can update apparatus status from mobile
- PMs can view real-time progress
- Financial data hidden from field techs
- App works offline (critical for field use)
- Response time < 2 seconds for common actions

---

### Phase 4: Revenue Recognition & Reporting (Weeks 8-10)

**Deliverables:**
- [ ] Create Apparatus_Revenue table (if separating from Apparatus)
- [ ] Build Power Automate flow:
  - [ ] Trigger on Apparatus Status = Complete
  - [ ] Lookup Scope_Financial_Configuration
  - [ ] Calculate earned revenue
  - [ ] Create revenue record
  - [ ] Update rollups
- [ ] Configure rollup fields for revenue aggregation
- [ ] Build Power BI reports:
  - [ ] Project performance dashboard
  - [ ] Earned value analysis
  - [ ] Scope completion tracking
  - [ ] Technician productivity
  - [ ] Financial summaries (PM/Exec only)
- [ ] Test revenue calculation accuracy
- [ ] Validate against Excel models

**Success Criteria:**
- Revenue calculated automatically on apparatus completion
- Accurate within $1 of manual calculation
- Rollups update within 1 hour
- Reports accessible to appropriate roles
- Historical data preserved

---

## TESTING & VALIDATION

### Unit Testing

**Table Structure Tests:**
- [ ] All fields created with correct data types
- [ ] Required fields enforced
- [ ] Lookup relationships working
- [ ] Choice fields populated
- [ ] Calculated fields computing correctly
- [ ] Rollup fields aggregating properly

**Business Rule Tests:**
- [ ] Status completion validation
- [ ] Date validation (completion >= start)
- [ ] NETA Standard immutability when records exist ⭐
- [ ] Apparatus hours limit enforcement

**NETA Standard Tests:** ⭐
- [ ] Create Scope with NETA_Standard = ATS
- [ ] Verify apparatus pulls ATS section and hours
- [ ] Create Scope with NETA_Standard = MTS
- [ ] Verify apparatus pulls MTS section and hours
- [ ] Attempt to change NETA_Standard with existing apparatus
- [ ] Verify change is blocked

---

### Integration Testing

**Import Process Tests:**
- [ ] Import small project (3 scopes, 50 apparatus)
- [ ] Import medium project (10 scopes, 300 apparatus)
- [ ] Import large project (LASNAP16: 27 scopes, 1,905 apparatus)
- [ ] Verify NETA_Standard imported from Cell C3 ⭐
- [ ] Verify all relationships established
- [ ] Verify financial configs created
- [ ] Validate quantities expanded correctly
- [ ] Test error handling for invalid data
- [ ] Test duplicate detection

---

### User Acceptance Testing

**Field Technician Scenarios:**
- [ ] Log in to app on mobile device
- [ ] View assigned tasks
- [ ] Update apparatus status to "In Progress"
- [ ] Complete apparatus (mark as "Complete")
- [ ] Add notes to apparatus
- [ ] Verify cannot see financial data
- [ ] Work offline and sync changes

**Project Manager Scenarios:**
- [ ] Import new project from Excel
- [ ] Review imported data
- [ ] Create tasks manually to organize apparatus ⭐
- [ ] Assign tasks to technicians
- [ ] View scope financial configuration
- [ ] Monitor project progress
- [ ] Review earned revenue reports
- [ ] Update scope information

**Administrator Scenarios:**
- [ ] Add new apparatus type to master table with ATS/MTS specs ⭐
- [ ] Update NETA section references ⭐
- [ ] Add new location
- [ ] Manage user access
- [ ] Review system logs
- [ ] Export data for analysis

---

## APPENDICES

### Appendix A: Data Type Reference

| Power Platform Type | Excel Equivalent | Notes |
|-------------------|-----------------|--------|
| Single Line Text | Text | Max 4,000 characters |
| Multiple Lines Text | Long Text | Unlimited characters |
| Whole Number | Number (no decimals) | -2,147,483,648 to 2,147,483,647 |
| Decimal Number | Number (with decimals) | Up to 10 decimal places |
| Currency | Currency | 2 decimal places, $ prefix |
| Date Only | Date | No time component |
| Date and Time | Date Time | Includes time |
| Yes/No | Boolean | True/False, Checkbox |
| Choice | Dropdown (single) | Local or global choices |
| Lookup | Relationship | Link to another table |
| Auto Number | - | System-generated sequential |

---

### Appendix B: Naming Conventions

**Tables:**
- PascalCase with underscores: `Apparatus_Type_Master`
- Descriptive, singular noun: `Scope` not `Scopes`
- Prefix with company code if needed: `RESA_Projects`

**Fields:**
- PascalCase with underscores: `Job_Number`
- Descriptive, clear purpose: `Date_Completed` not `Date2`
- Consistent suffixes:
  - `_Date` for dates
  - `_Rate` for currency
  - `_Percent` for percentages
  - `_ID` for identifiers

**Choices:**
- Prefix with company/app: `resapower_workstatus`
- Lowercase with underscores
- Descriptive of purpose

---

### Appendix C: Field Mapping from Excel Estimator

**Project_Data Sheet → Projects Table:**

| Excel Column | Excel Name | Dataverse Field | Notes |
|-------------|------------|----------------|-------|
| A | Job Number | Job_Number | Primary key |
| B | Location Code | Location_Code | Lookup to Locations |
| C | Project Name | Project_Name | Internal identifier |
| D | Customer Name | Customer_Name | Full legal name |
| E | Customer Short | Customer_Short_Name | Display name |
| F | Description | Description | Multiline text |
| G | PM Name | Project_Manager | Assigned PM |
| H | Contract Value | Contract_Value | Currency |
| I | Status | Status | Choice: Not Started/Active/Complete |

**Scope Sheet (Cell C3) → Scopes Table NETA_Standard:** ⭐

| Excel Cell | Excel Value | Dataverse Field | Dataverse Value |
|-----------|------------|----------------|----------------|
| C3 | "ATS" | NETA_Standard | ATS (Choice: 1) |
| C3 | "MTS" | NETA_Standard | MTS (Choice: 2) |

**Scope Sheet (Header) → Scopes Table:**

| Excel Cell | Excel Name | Dataverse Field | Notes |
|-----------|------------|----------------|-------|
| B5 | Scope Name | Scope_Name | Scope identifier |
| B6 | Scope Number | Scope_Number | Sequential number |
| B7 | SLD Reference | SLD_Reference | Drawing reference |
| C3 | NETA Standard | NETA_Standard | ⭐ ATS or MTS choice |

**Scope Sheet (Rates Section) → Scope_Financial_Configuration:**

| Excel Cell | Excel Name | Dataverse Field | Notes |
|-----------|------------|----------------|-------|
| E10 | Base Rate | Base_Rate | Currency |
| F10 | Base Percent | Base_Percent | Decimal (0-1) |
| E11 | Commute Rate | Commute_Rate | Currency |
| F11 | Commute Percent | Commute_Percent | Decimal (0-1) |
| E12 | PM Rate | PM_Rate | Currency |
| F12 | PM Percent | PM_Percent | Decimal (0-1) |
| ... | ... | ... | ... |

**Equipment_Reference Sheet → Apparatus_Type_Master:** ⭐

| Excel Column | Excel Name | Dataverse Field | Notes |
|-------------|------------|----------------|-------|
| A | Apparatus Type | Apparatus_Type_Name | Full name |
| B | Category | Category | Choice field |
| C | NETA '25 ATS Section | NETA_ATS_Section_Reference | ⭐ New field |
| D | NETA '23 MTS Section | NETA_MTS_Section_Reference | ⭐ New field |
| E | ATS Labor Hours | NETA_ATS_Labor_Hours | ⭐ New field |
| F | MTS Labor Hours | NETA_MTS_Labor_Hours | ⭐ New field |

**Scope Sheet (Apparatus Rows) → Apparatus Table:**

| Excel Column | Excel Name | Dataverse Field | Notes |
|-------------|------------|----------------|-------|
| A | Qty | - | Expands to multiple records |
| B | Apparatus Designation | Apparatus_Designation | Equipment tag |
| C | Apparatus Type | Apparatus_Type_Name | Links to master |
| D | Hours | Apparatus_Hours | Test hours |
| - | - | Apparatus_Number | Auto-sequence within scope |

---

### Appendix D: Sample Import Script Structure

```python
# High-level structure for Excel import script
# Detailed implementation provided separately

import openpyxl
from datetime import datetime

class RESAProjectImporter:
    def __init__(self, excel_file_path):
        self.file_path = excel_file_path
        self.workbook = None
        self.project_id = None
        
    def import_full_project(self):
        """Main import orchestration"""
        self.workbook = openpyxl.load_workbook(self.file_path)
        
        # Step 1: Import Project
        project_data = self.read_project_data_sheet()
        self.project_id = self.create_project(project_data)
        
        # Step 2: Import each Scope
        scope_list = project_data['scope_sheets']
        for scope_name in scope_list:
            self.process_scope(scope_name, self.project_id)
        
        # Step 3: Validate import
        validation_results = self.validate_import()
        
        return {
            'success': True,
            'project_id': self.project_id,
            'validation': validation_results
        }
    
    def read_project_data_sheet(self):
        """Read Project_Data sheet"""
        sheet = self.workbook['Project_Data']
        
        project_data = {
            'job_number': sheet['A2'].value,
            'location_code': sheet['B2'].value,
            'project_name': sheet['C2'].value,
            'customer_name': sheet['D2'].value,
            'customer_short_name': sheet['E2'].value,
            # ... additional fields
            'scope_sheets': self.get_scope_sheet_list(sheet)
        }
        
        return project_data
    
    def process_scope(self, scope_name, job_number):
        """Process one scope sheet"""
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        
        if scope_name not in wb.sheetnames:
            return {'success': False, 'warning': f'Sheet {scope_name} not found'}
        
        sheet = wb[scope_name]
        
        # ⭐ Read NETA Standard from Cell C3
        neta_standard = sheet.cell(row=3, column=3).value
        if neta_standard not in ['ATS', 'MTS']:
            raise ValueError(f"Invalid NETA Standard in {scope_name} C3: {neta_standard}")
        
        # Read header
        scope_data = self.read_scope_header(sheet)
        scope_data['neta_standard'] = neta_standard  # ⭐ Add NETA Standard
        
        # Create Scope with NETA_Standard
        scope_id = self.create_scope(scope_data, job_number)
        
        # Read financial config
        financial_config = self.read_financial_config(sheet)
        self.create_financial_config(financial_config, scope_id)
        
        # Read apparatus with NETA-aware lookup
        apparatus_rows = self.read_apparatus_rows(sheet, neta_standard)  # ⭐ Pass standard
        
        # Create apparatus with quantity expansion
        apparatus_count = 0
        for row in apparatus_rows:
            qty = row['qty'] or 1
            for i in range(qty):
                # ⭐ Apparatus creation uses neta_standard to lookup correct specs
                self.create_apparatus(row, scope_id, job_number, neta_standard)
                apparatus_count += 1
        
        return {
            'success': True,
            'scope_name': scope_name,
            'neta_standard': neta_standard,  # ⭐ Include in results
            'apparatus_count': apparatus_count
        }
    
    def lookup_apparatus_specs(self, apparatus_type, neta_standard):
        """⭐ Lookup correct NETA specs based on standard"""
        # Query Apparatus_Type_Master table
        apparatus_master = query_dataverse(
            table='Apparatus_Type_Master',
            filter=f"Apparatus_Type_Name eq '{apparatus_type}'"
        )
        
        if neta_standard == 'ATS':
            return {
                'section': apparatus_master['NETA_ATS_Section_Reference'],
                'hours': apparatus_master['NETA_ATS_Labor_Hours']
            }
        else:  # MTS
            return {
                'section': apparatus_master['NETA_MTS_Section_Reference'],
                'hours': apparatus_master['NETA_MTS_Labor_Hours']
            }
    
    # Additional methods for API calls, validation, etc...
```

---

### Appendix E: Data Migration Checklist

**If migrating from existing system:**

- [ ] Export current project data
- [ ] Map old fields to new schema
- [ ] Clean and validate data
- [ ] Add NETA_Standard to existing scopes (classify as ATS or MTS) ⭐
- [ ] Create import scripts for bulk data
- [ ] Test import on development environment
- [ ] Verify NETA specs applied correctly ⭐
- [ ] Validate calculations
- [ ] User acceptance of migrated data
- [ ] Plan cutover date
- [ ] Execute production migration
- [ ] Verify production data
- [ ] Decommission old system

---

### Appendix F: Training Materials Outline

#### Project Manager Training (2.5 hours) ⭐ UPDATED

**Module 1: System Overview (30 min)**
- Architecture and capabilities
- Project workflow
- Location and master data
- ⭐ NETA Standards (ATS vs MTS) - 10 min

**Module 2: Import Process (45 min)**
- Completing Project_Data sheet
- Setting NETA_Standard in Cell C3 ⭐
- Running import script
- Reviewing import results
- Troubleshooting common errors

**Module 3: Manual Task Creation (30 min)** ⭐ NEW MODULE
- When to create tasks
- Organizing apparatus into tasks
- Assigning tasks to technicians
- Task management best practices

**Module 4: Project Management (30 min)**
- Viewing projects and scopes
- Understanding financial data
- Monitoring progress
- Generating reports

**Module 5: Hands-On Practice (15 min)**
- Import sample estimate with both ATS and MTS scopes ⭐
- Create tasks to organize apparatus ⭐
- Complete apparatus
- Review dashboards

---

#### Field Technician Training (1 hour)

**Module 1: Mobile App Overview (15 min)**
- Logging in
- Navigation
- Finding assigned work

**Module 2: Completing Apparatus (30 min)**
- Viewing apparatus list
- Understanding NETA section references ⭐
- Marking complete
- Adding notes
- Understanding status

**Module 3: Hands-On Practice (15 min)**
- Complete 5 test apparatus
- Add notes
- Review completed work

---

#### Administrator Training (3.5 hours) ⭐ UPDATED

**Module 1: System Architecture (45 min)**
- Dataverse structure
- Security model
- Power Automate flows
- ⭐ NETA Standards architecture - 15 min

**Module 2: Master Data Management (60 min)** ⭐ EXTENDED
- Adding locations
- Managing apparatus types
- ⭐ Maintaining ATS/MTS specifications - 20 min
- Updating categories

**Module 3: User Management (45 min)**
- Creating users
- Assigning security roles
- Managing licenses

**Module 4: Troubleshooting (60 min)** ⭐ EXTENDED
- Common issues
- ⭐ NETA Standard conflicts - 10 min
- Flow failures
- Performance problems
- Support escalation

---

### Appendix G: Support & Maintenance

#### Level 1 Support (User Issues)

**Handled By:** Project Managers or designated power users

**Common Issues:**
- Login problems
- Can't find project
- Import errors
- ⭐ Wrong NETA sections displayed
- Mobile app not loading
- Completion status not updating

**Resolution Time:** Same day

---

#### Level 2 Support (System Issues)

**Handled By:** Administrator or IT Support

**Common Issues:**
- Power Automate flow failures
- Dataverse errors
- ⭐ NETA Standard conflicts in data
- Security role problems
- Performance degradation
- Data integrity issues

**Resolution Time:** 1-3 days

---

#### Level 3 Support (Critical Issues)

**Handled By:** Microsoft Support or external consultant

**Critical Issues:**
- Platform outage
- Data corruption
- Security breach
- Critical flow failure affecting all users

**Resolution Time:** As needed (emergency)

---

#### Maintenance Schedule

**Daily:**
- Monitor flow execution logs
- Review error notifications
- Check import summary reports

**Weekly:**
- Review system usage metrics
- Check for failed flows
- Clean up test data
- Update master data as needed
- ⭐ Verify NETA specs accuracy

**Monthly:**
- Performance review
- User feedback collection
- Plan feature enhancements
- Review security roles
- ⭐ Update NETA standards if new versions released

**Quarterly:**
- Major system updates
- User training refreshers
- Documentation updates
- Disaster recovery test

---

### Appendix H: Roadmap Beyond Phase 4

**Short-Term (6-12 months):**
- Mobile app native version
- Barcode scanning integration
- Power BI advanced reporting
- ⭐ Enhanced NETA compliance reporting
- Photo documentation
- Document storage (SharePoint)

**Medium-Term (1-2 years):**
- Customer portal (external users)
- API for external integrations
- Predictive analytics (completion forecasting)
- Resource scheduling optimization
- Equipment maintenance tracking
- ⭐ Automated NETA standard version tracking

**Long-Term (2+ years):**
- AI-powered estimation assistance
- IoT integration (equipment sensors)
- Augmented reality for field work
- Blockchain for compliance tracking
- Multi-company platform expansion

---

### Appendix I: Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-10 | 1.0 | Initial master specification created | Jason Smith |
| 2025-11-10 | 1.1 | **CRITICAL UPDATES:** | Jason Smith |
| | | ⭐ Added NETA_Standard field to Scopes table (ATS/MTS choice) | |
| | | ⭐ Updated Apparatus_Type_Master with 4-column NETA structure: | |
| | | - NETA_ATS_Section_Reference (replacing NETA_Spec_Reference) | |
| | | - NETA_MTS_Section_Reference (new) | |
| | | - NETA_ATS_Labor_Hours (replacing Default_Labor_Hours) | |
| | | - NETA_MTS_Labor_Hours (new) | |
| | | ⭐ Clarified Tasks table implementation: | |
| | | - Status changed from "Deferred" to "Immediate Implementation" | |
| | | - Created manually by PMs, NOT imported from Excel | |
| | | - Excel estimators have no task-level structure | |
| | | ⭐ Added NETA Standard inheritance architecture throughout | |
| | | ⭐ Updated import process to read Cell C3 for NETA_Standard | |
| | | ⭐ Enhanced training materials with NETA Standards module | |
| | | ⭐ Added NETA-specific views and testing scenarios | |

---

## DOCUMENT CONTROL

**Document Owner:** Jason Smith, Phoenix Services Unit  
**Review Frequency:** Monthly during implementation, Quarterly post-launch  
**Next Review Date:** December 10, 2025  
**Distribution:** Project stakeholders, IT team, implementation partners  
**Classification:** Internal Use Only  
**Version Control:** Stored in Project Knowledge Base

---

## APPROVAL SIGNATURES

**Project Sponsor:** ___________________________ Date: ___________  
**Technical Lead:** ___________________________ Date: ___________  
**Project Manager:** ___________________________ Date: ___________

---

**END OF MASTER BUILD SPECIFICATION v1.1**

*This document serves as the single source of truth for the RESA Power Project Tracker modernization project. All design decisions, technical specifications, and implementation details should align with this specification. Any changes to the specification must be formally documented in the Change Log and approved by the project sponsor.*
