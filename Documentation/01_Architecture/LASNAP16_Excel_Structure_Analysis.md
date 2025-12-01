# LASNAP16 MASTER Workbook - Complete Structure Analysis

> **Analysis Date**: December 2024  
> **Source File**: `LASNAP16\RESA Power - LASNAP16 MASTER.xlsm`  
> **Purpose**: Comprehensive breakdown for Dataverse schema design

---

## Executive Summary

The LASNAP16 MASTER workbook is a **full project management and tracking system**, not just an estimator. It contains:

- **45 worksheets** organized by scope
- **~2,800 tasks** across all scopes with unique Task_IDs
- **22 tracking columns** per task including status, hours (quoted/remaining/actual), completion %, deliverables
- **Hierarchical Task IDs** following pattern: `Scope#.Section#.Task#` (e.g., `1.1.1`, `1.2.15`)

This structure needs to be mapped to Dataverse tables with proper relationships and autonumbering.

---

## I. Sheet Organization

### Sheet Categories

| Category | Sheets | Purpose |
|----------|--------|---------|
| **Templates** | Scope_Template, Gantt_Template | Master templates for new scopes |
| **Project Control** | Project_Form, Project_Status | Project-level info and status tracking |
| **Data Consolidation** | All_Tasks, All_Tasks_Billing, All_Lists | Aggregated views from all scope sheets |
| **Reference Data** | Apparatus_List_w_Hours | Master apparatus types with default hours |
| **Configuration** | Scope_Labor_Rates, Task_Entry, Financial_Income | Billing rates and financial config |
| **Reporting** | PowerBI_Data | Flattened data for BI reporting |
| **Instructions** | Instructions | User guide |
| **Scope Sheets (32)** | LAS16.PPM01-24, LAS16.GDB01-12, LAS16.GDB13-24, LAS16.HOUSE, MV, RPP's (1-120, 121-240, 241-360, 361-480) | Individual scope tracking |

### All 45 Sheets (in order)

1. Scope_Template
2. Gantt_Template  
3. Project_Form
4. All_Lists
5. Apparatus_List_w_Hours
6. All_Tasks
7. All_Tasks_Billing
8. PowerBI_Data
9. Scope_Labor_Rates
10. Task_Entry
11. Project_Status
12. Financial_Income
13. Instructions
14. LAS16.PPM01 through LAS16.PPM24 (24 sheets)
15. LAS16.GDB01-12
16. LAS16.GDB13-24
17. LAS16.HOUSE
18. MV
19. RPP's (1-120)
20. RPP's (121-240)
21. RPP's (241-360)
22. RPP's (361-480)

---

## II. Master Data: Apparatus_List_w_Hours

This sheet defines the master list of apparatus types with their default hours for ATS and MTS standards.

### Structure (A1:G35)

| Column A | Column B | Column C | Column E | Column F | Column G |
|----------|----------|----------|----------|----------|----------|
| Apparatus | ATS_Hours | MTS_Hours | Apparatus_Type | Category | ATS_Hours |

### Apparatus Types (34 unique)

| Apparatus Type | ATS Hours | MTS Hours | Category |
|---------------|-----------|-----------|----------|
| Circuit Breaker LV - Secondary Injection | 2 | 0.5 | Circuit Breakers - Secondary |
| Panelboard - Low Voltage | 0.5 | 5 | Panelboards |
| Circuit Breaker LV - (LS/LSI) | 3 | 16 | Circuit Breakers - Primary |
| Ground Resistance Test - Two-Point (PPM Lot) | 1.5 | 6 | Point-to-Point |
| Circuit Breaker LV - Draw-Out | 4 | 3 | Circuit Breakers - Primary |
| Switchboard - Low Voltage | 4 | 14 | Switchboard |
| Conductors LV - 3 Phase Feeder (PPM01&24) | 19.8 | - | LV Cables |
| Transformer (Dry Type up to 499kVA) | 2 | - | XFMR - Dry-Type, Small |
| Conductors MV - Set of 3 (DC Hipotential) | 4 | - | MV Cables |
| PDU Load Banking (Switch) | 5 | - | PDU Load Bank |
| Switch LV - Fused Disconnect | 1.5 | - | LV Disconnect |
| Transformer (Dry Type 500kVA & larger) | 4 | - | XFMR - Dry-Type, Large |
| Ground Resistance Test - FOP (Pods) | 6 | - | Ground Resistance - FOP |
| Transformer - Pad Mount Oil (TTR/IR/WR/PF/Oil) | 12 | - | XFMR, Oil-Filled, Padmount |
| Ground Resistance Test - Clamp Method | 2 | - | Ground Resistance - Clamp |
| Switch (Pad Mount Vista) - Medium Voltage | 4 | - | Padmount Vista Switch |
| Switch MV - Fused, Metal-Enclosed Disconnect | 2 | - | MV Fused Switch |
| Automatic Transfer Switch - (IR/DLRO) | 4 | - | ATS |
| Conductors LV - 3 Phase Feeder (Lot) | 18.6 | - | LV Cables |
| Ground Resistance Test - Two-Point (Gen) | 1 | - | Ground Resistance - 2pt |
| Conductors LV - 3 Phase Feeder | 0.3 | - | LV Cables |
| Ground Resistance Test - FOP (Gen) | 4 | - | Ground Resistance |
| Conductors LV - 3 Phase Feeder (GEN-H) | 1.2 | - | LV Cables |
| Conductors LV - 3 Phase Feeder (SES-H) | 1.2 | - | LV Cables |
| Conductors LV - 3 Phase Feeder (DB-H) | 2.7 | - | LV Cables |
| Conductors LV - 3 Phase Feeder (HP1/HP2) | 1.5 | - | LV Cables |
| Conductors LV - 3 Phase Feeder (HUPS1/HUPS2) | 0.9 | - | LV Cables |
| Conductors LV - 3 Phase Feeder (HPP1.1/2.1) | 1.2 | - | LV Cables |
| Conductors LV - 3 Phase Feeder (HPC1.1/2.1) | 1.8 | - | LV Cables |
| Conductors MV - Substation 2x3 (DC Hipotential) | 8 | - | LV Cables |
| Ground Resistance Test - Two-Point (MV Lot) | 10 | 6 | Point-to-Point |
| RPP - Remote Power Panel | 2.5 | - | RPP |

### Apparatus Categories (19 unique)

1. Circuit Breakers - Secondary
2. Circuit Breakers - Primary
3. Panelboards
4. Point-to-Point
5. Switchboard
6. LV Cables
7. MV Cables
8. PDU Load Bank
9. LV Disconnect
10. XFMR - Dry-Type, Small
11. XFMR - Dry-Type, Large
12. XFMR, Oil-Filled, Padmount
13. Ground Resistance - FOP
14. Ground Resistance - Clamp
15. Ground Resistance - 2pt
16. Ground Resistance
17. Padmount Vista Switch
18. MV Fused Switch
19. ATS
20. RPP

---

## III. Task Structure: All_Tasks Sheet

### Column Layout (A1:V2856)

| Column | Header | Description | Data Type |
|--------|--------|-------------|-----------|
| A | Scope | Scope name (e.g., "LAS16.PPM01") | Text |
| B | NETA_Standard | Testing standard (PPM, GDB, etc.) | Text |
| C | Task_ID | Hierarchical ID (e.g., "1.1.1") | Text |
| D | Task | Task/Section name (e.g., "Main Switchgear", "PDU") | Text |
| E | Apparatus | Apparatus type | Text (lookup) |
| F | Designation | Equipment designation/nameplate | Text |
| G | Drawing | Drawing reference | Text |
| H | Date Due | Target completion date | Date |
| I | Notes | Primary notes | Text |
| J | Assessment | Assessment status | Text |
| K | DATASHEET | Datasheet completed | Boolean |
| L | DATE COMPLETED | Actual completion date | Date |
| M | NOTES2 | Secondary notes | Text |
| N | % COMPLETION | Completion percentage | Number (0-100) |
| O | TASK DELAYS | Delay notes/reasons | Text |
| P | Apparatus Hours | Quoted hours for apparatus | Number |
| Q | Remaining Hours | Hours remaining | Number (calculated) |
| R | ACTUAL HOURS | Actual hours spent | Number |
| S | STATUS | Task status | Text (choice) |
| T | AVAILABILITY | Equipment availability | Text (choice) |
| U | PRIORITY | Task priority | Text (choice) |
| V | Apparatus Category | Category grouping | Text |

### Task ID Hierarchy Pattern

```
Scope.Section.Task
  │      │      │
  │      │      └── Sequential task number within section
  │      └── Section number (1=Main Switchgear, 2=PDU, 3=Grounding, etc.)
  └── Scope sequence number (1-24 for PPM, 25+ for GDB, etc.)
```

**Examples:**
- `1.1.1` = PPM01, Main Switchgear, Task 1 (Switchboard - Low Voltage)
- `1.2.15` = PPM01, PDU, Task 15 (Circuit Breaker LV - Secondary Injection)
- `2.3.2` = PPM02, Grounding, Task 2 (Ground Resistance Test - Clamp Method)

### Section Names (Column D - "Task" column)

| Section | Purpose |
|---------|---------|
| Main Switchgear | Primary electrical distribution equipment |
| PDU | Power Distribution Units |
| Grounding | Ground resistance testing |

---

## IV. Hours Tracking Model

### Three Hours Columns

| Column | Purpose | Calculation |
|--------|---------|-------------|
| Apparatus Hours (P) | Quoted/budgeted hours | From Apparatus_List_w_Hours based on type |
| Remaining Hours (Q) | Hours left to complete | Quoted - Actual (or formula-based) |
| ACTUAL HOURS (R) | Hours actually spent | Entered by technicians |

### Hours Flow
```
Apparatus Hours → (Initial Quote from Master List)
        ↓
Remaining Hours = Apparatus Hours - Actual Hours
        ↓
ACTUAL HOURS → (Field entry as work progresses)
```

---

## V. Recommended Dataverse Schema

Based on this analysis, here's the recommended table structure:

### Tables to Create/Modify

#### 1. **cr950_apparatustype** (NEW - Master Reference)
| Field | Type | Description |
|-------|------|-------------|
| cr950_name | Text | Apparatus type name |
| cr950_atshours | Decimal | Default ATS hours |
| cr950_mtshours | Decimal | Default MTS hours |
| cr950_category | Lookup → Category | Apparatus category |

#### 2. **cr950_apparatuscategory** (NEW - Master Reference)
| Field | Type | Description |
|-------|------|-------------|
| cr950_name | Text | Category name |
| cr950_displayorder | Integer | Sort order |

#### 3. **cr950_section** (NEW - Between Scope and Task)
| Field | Type | Description |
|-------|------|-------------|
| cr950_name | Text | Section name (Main Switchgear, PDU, etc.) |
| cr950_sectionnumber | Integer | Section sequence (1, 2, 3...) |
| cr950_scope | Lookup → Scope | Parent scope |

#### 4. **cr950_task** (RENAME/MODIFY cr950_apparatus)
| Field | Type | Description |
|-------|------|-------------|
| cr950_taskid | Auto-number | Hierarchical ID (generated) |
| cr950_section | Lookup → Section | Parent section |
| cr950_apparatustype | Lookup → ApparatusType | Equipment type |
| cr950_designation | Text | Equipment designation |
| cr950_drawing | Text | Drawing reference |
| cr950_datedue | Date | Target date |
| cr950_datecompleted | Date | Actual completion |
| cr950_quotedhours | Decimal | Budgeted hours |
| cr950_remaininghours | Decimal | Calculated remaining |
| cr950_actualhours | Decimal | Actual hours |
| cr950_completion | Integer | % Complete (0-100) |
| cr950_status | Choice | Status (Not Started, In Progress, Complete) |
| cr950_availability | Choice | Equipment availability |
| cr950_priority | Choice | Priority level |
| cr950_assessment | Choice | Assessment status |
| cr950_datasheetcomplete | Boolean | Datasheet done |
| cr950_notes | Text | Notes |
| cr950_taskdelays | Text | Delay notes |

### Auto-Numbering Strategy

For Task IDs like "1.1.1", "1.2.15":

**Option A: Calculated at creation**
```
TaskID = {ScopeSequence}.{SectionNumber}.{TaskSequence}
```
- Use a plugin or workflow to calculate on create
- Scope sequence comes from cr950_projectscope order
- Section number from cr950_section
- Task sequence auto-increments within section

**Option B: Concatenated display field**
```
cr950_taskiddisplay = CONCATENATE(ScopeSeq, ".", SectionNum, ".", TaskNum)
```
- Use Power Automate to set on create
- Store components separately for filtering

---

## VI. Import Strategy from Excel

### Phase 1: Master Data Import
1. Import **Apparatus Categories** (19 records)
2. Import **Apparatus Types** with hours (34 records)

### Phase 2: Project Structure Import
1. Create **Sections** for each scope (typically 3 per scope: Main Switchgear, PDU, Grounding)
2. Link sections to existing scopes

### Phase 3: Task Import
1. Import tasks from **All_Tasks** sheet
2. Link each task to:
   - Appropriate Section (based on Task column)
   - Appropriate Apparatus Type (based on Apparatus column)
3. Generate Task IDs using hierarchical pattern

### JSON Structure for Power Automate Import

```json
{
  "project": "LASNAP16",
  "scopes": [
    {
      "name": "LAS16.PPM01",
      "standard": "PPM",
      "sections": [
        {
          "name": "Main Switchgear",
          "sectionNumber": 1,
          "tasks": [
            {
              "taskNumber": 1,
              "apparatus": "Switchboard - Low Voltage",
              "designation": null,
              "quotedHours": 4
            }
          ]
        }
      ]
    }
  ]
}
```

---

## VII. Key Insights for Design

### 1. Section Layer is Critical
- Scopes contain **Sections** (Main Switchgear, PDU, Grounding)
- Sections contain **Tasks** (individual apparatus items)
- Hours roll up: Tasks → Sections → Scopes → Project

### 2. Task IDs Must Be Hierarchical
- Format: `{ScopeSeq}.{SectionNum}.{TaskNum}`
- Must be unique project-wide
- Used for reporting and navigation

### 3. Hours Tracking is Core Functionality
- Three types: Quoted, Remaining, Actual
- Remaining = Quoted - Actual (or adjustable)
- Completion % may be independent or calculated

### 4. Status/Priority/Availability are Choice Fields
- From named ranges: STATUS, AVAILABILITY, PRIORITY
- Should map to Dataverse choice fields
- Allow filtering and reporting

### 5. Deliverables Tracking
- DATASHEET checkbox for each task
- Assessment status field
- DATE COMPLETED tracking

---

## VIII. Next Steps

1. **Create Dataverse Tables**
   - ApparatusCategory (master)
   - ApparatusType (master with hours)
   - Section (between Scope and Task)
   - Modify existing Apparatus table → Task table

2. **Import Master Data**
   - Load categories and types from Apparatus_List_w_Hours

3. **Design Auto-Numbering**
   - Implement plugin or flow for hierarchical Task IDs

4. **Build Import Flow**
   - Power Automate to parse All_Tasks format
   - Create Section records on-the-fly
   - Link tasks properly

5. **Update Model-Driven App**
   - Add Section entity to forms
   - Create task entry views with hours tracking
   - Add rollup calculations for totals
