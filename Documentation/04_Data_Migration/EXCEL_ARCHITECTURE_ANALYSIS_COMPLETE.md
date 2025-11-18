# RESA Power Excel Architecture - Complete Analysis from VBA

**Purpose:** Definitive understanding of Excel structure for MCP development  
**Created:** November 16, 2025  
**Last Updated:** November 16, 2025  
**Version:** 1.0 - Initial VBA analysis from 10 modules  
**Status:** Complete  
**Source:** VBA Module Analysis (Project Data Entry MASTER.xlsm)

---

## 🎯 Executive Summary

### **Dual-Architecture System**

```
Generator Template                    Project Tracker
(Project Data Entry MASTER.xlsm)     (e.g., LASNAP16 MASTER.xlsm)
├── VBA Modules (10)                  ├── Scope Sheets (multiple)
├── Template Sheets                   │   ├── Scope 1
│   ├── Scope_Template                │   ├── Scope 2
│   ├── All_Lists (master data)       │   └── Scope N
│   ├── All_Tasks                     ├── All_Tasks (aggregated)
│   ├── All_Tasks_Billing            ├── All_Tasks_Billing
│   └── Scope_Labor_Rates            └── Scope_Labor_Rates
└── VBA Automation                    
    └── BuildAll() creates             
        project trackers
```

### **Critical Insight:**
The **generator template** contains:
- ✅ Master data (apparatus types, rates, standards)
- ✅ VBA business logic
- ✅ Template structures

**Project trackers** contain:
- ✅ Actual project data
- ✅ Scope-specific apparatus
- ✅ Hours tracking
- ✅ Status/completion data

---

## 📊 **VBA Modules Analyzed**

### **10 Modules - Complete Business Logic**

1. **Global_Constants.bas** ⭐ CRITICAL
   - Centralized column mappings for ALL modules
   - Prevents hardcoded column references
   - Self-documenting code
   - ~500 lines of constants and utility functions

2. **Build_All.bas**
   - Creates new scope sheets from template
   - Populates hierarchical task/apparatus structure
   - Applies formulas and validation
   - ~800 lines

3. **PopulateAllTasks.bas**
   - Aggregates apparatus from all scopes into All_Tasks
   - Protects Column V explicitly
   - Syncs with All_Tasks_Billing
   - ~400 lines

4. **ClearTaskEntry.bas** - Data clearing utilities
5. **Field_Workbook_Export.bas** - Export functions
6. **modDateModeRibbon.bas** - UI controls (AUTO/MANUAL mode)
7. **modGanttBuilder.bas** - Gantt chart generation
8. **PowerBIExportEnhanced.bas** - BI integration
9. **RemapBillingTasks.bas** - Billing workflows
10. **ThisWorkbook.cls** - Workbook-level events

---

## 📋 **Scope Sheet Structure (from Global_Constants)**

### **Critical Cells:**
- **G4 (SC_SCOPE_CELL):** Scope Name
- **H4 (SC_NETA_CELL):** NETA Standard (ATS, MTS, ECS, SPEC, OTHER)
- **T2 (SC_MODE_TOGGLE_CELL):** AUTO/MANUAL mode for date completion

### **Row Structure:**
```
Row 1-4:  Headers, logos, project info, NETA standard
Row 5:    Column Headers (SC_HEADER_ROW)
Row 6:    Parent Row Template (SC_TEMPLATE_PARENT_ROW)
Row 7:    Child Row Template (SC_TEMPLATE_CHILD_ROW)
Row 8+:   Actual data rows (SC_FIRST_DATA_ROW = 6)
Row N:    TOTALS row (SC_TEMPLATE_TOTALS_ROW = 21 in template)
```

### **Column Mapping (18 columns):**

| Constant | Col | Letter | Field Name | Parent | Child | Notes |
|----------|-----|--------|------------|--------|-------|-------|
| SC_COL_STATUS | 2 | B | STATUS | Formula | Dropdown | Parent: auto-calculated |
| SC_COL_AVAIL | 3 | C | AVAILABILITY | Manual | Manual | READY, ON HOLD, NOT AVAILABLE |
| SC_COL_PRIORITY | 4 | D | PRIORITY | Manual | Manual | HIGH, MEDIUM, LOW |
| SC_COL_TASK_ID | 5 | E | TASK_ID | Text | Text | 1.1, 1.1.1, 1.1.2 |
| SC_COL_NAME_APP | 6 | F | TASK/APPARATUS | Task name | Apparatus name | Context-dependent |
| SC_COL_DES | 7 | G | DESIGNATION | - | Apparatus ID | Unique identifier |
| SC_COL_DRW | 8 | H | DRAWING | - | Drawing ref | Drawing number |
| SC_COL_DATE_DUE | 9 | I | DATE DUE | Rollup | Manual | Parent: formula |
| SC_COL_ASSESSMENT | 10 | J | ASSESSMENT | - | Dropdown | Quality status |
| SC_COL_DATASHEET | 11 | K | DATASHEET | - | Dropdown | YES, NO, N/A |
| SC_COL_DATE_COMP | 12 | L | DATE COMPLETED | Formula | Formula/Manual | Mode-dependent |
| SC_COL_NOTES | 13 | M | NOTES | Text | Text | Free-form |
| SC_COL_PCT | 14 | N | % COMPLETION | Formula | Formula | Decimal 0-1 |
| SC_COL_DELAY | 15 | O | TASK DELAYS | Rollup | Number | Hours |
| SC_COL_AHRS | 16 | P | **APPARATUS HOURS** | Rollup | Number | **CRITICAL** |
| SC_COL_REMHRS | 17 | Q | REMAINING HOURS | Rollup | Number | For progress |
| SC_COL_ACTHRS | 18 | R | ACTUAL HOURS | Rollup | Number | Field entry |

---

## 📊 **All_Tasks Sheet (DIFFERENT MAPPING!)**

### **Critical Difference:**
All_Tasks has a **completely different column order** than Scope sheets!

### **Column Mapping (22 columns):**

| Constant | Col | Letter | Field Name | Source (Scope) |
|----------|-----|--------|------------|----------------|
| AT_COL_SCOPE | 1 | A | Scope | Cell G4 |
| AT_COL_NETA | 2 | B | NETA_Standard | Cell H4 |
| AT_COL_TID | 3 | C | Task_ID | Column E |
| AT_COL_TASK | 4 | D | Task | Task name (parent) |
| AT_COL_APP | 5 | E | Apparatus | Column F (child) |
| AT_COL_DES | 6 | F | Designation | Column G |
| AT_COL_DRW | 7 | G | Drawing | Column H |
| AT_COL_DATE_DUE | 8 | H | Date Due | Column I |
| AT_COL_NOTES | 9 | I | Notes | - |
| AT_COL_ASSESSMENT | 10 | J | Assessment | Column J |
| AT_COL_DATASHEET | 11 | K | DATASHEET | Column K |
| AT_COL_DATE_COMP | 12 | L | DATE_COMPLETED | Column L |
| AT_COL_NOTES2 | 13 | M | NOTES2 | Column M |
| AT_COL_PCT | 14 | N | % COMPLETION | Column N |
| AT_COL_DELAY | 15 | O | TASK DELAYS | Column O |
| AT_COL_AHRS | 16 | P | Apparatus_Hours | Column P ✓ Same! |
| AT_COL_REMHRS | 17 | Q | Remaining_Hours | Column Q |
| AT_COL_ACTHRS | 18 | R | ACTUAL_HOURS | Column R |
| AT_COL_STATUS | 19 | S | **STATUS** | Column B ⚠️ MOVED! |
| AT_COL_AVAIL | 20 | T | AVAILABILITY | Column C |
| AT_COL_PRIORITY | 21 | U | PRIORITY | Column D |
| AT_COL_CATEGORY | 22 | V | **Apparatus Category** | 🚫 PROTECTED |

### **Column V Protection:**
```vba
Const MAX_POPULATE_COLUMN As Integer = 21  ' Column U - NEVER go past this
```
VBA explicitly stops at Column U (21), **never writing to Column V (22)**.

---

## 🔄 **VBA Process Flows**

### **BuildAll() - Creates Scope Sheet**

```
Task_Entry Sheet (Input)
  ├── Cell A2: Scope Name
  ├── Cell B2: NETA Standard
  └── Rows 2+: Task/Apparatus data
      ↓
VBA BuildAll() Executes
  ├── Copy Scope_Template (entire sheet)
  ├── Name new sheet = Scope Name
  ├── Write G4 = Scope Name
  ├── Write H4 = NETA Standard
  ├── Delete Rows 8+ (keep templates)
  ├── Clear template rows 6-7 (content only, keep formatting)
  ├── Start output at Row 6
      ↓
Process Each Task_Entry Row
  ├── If Task_Header present:
  │   ├── Insert parent row (use Row 6 template)
  │   ├── Task_ID = First two parts (1.1)
  │   ├── Name = Task header
  │   ├── Status = Formula (OVERDUE/COMPLETED/IN PROGRESS/NOT STARTED)
  │   ├── Date Due = Rollup formula (AGGREGATE function)
  │   ├── Hours = Will be SUM of children (later)
  │   └── % = Calculated from hours
  ├── If Apparatus present:
  │   ├── Insert child row (use Row 7 template)
  │   ├── Task_ID = Full ID (1.1.1)
  │   ├── Apparatus = from Task_Entry Column E
  │   ├── Designation = from Task_Entry Column F
  │   ├── Drawing = from Task_Entry Column G
  │   ├── Apparatus_Hours = from Task_Entry Column H ⭐
  │   ├── % = Formula: (1 - Remaining/Apparatus)
  │   └── Status = Dropdown (COMPLETED/NOT STARTED only)
      ↓
Build Rollups
  ├── Parent rows get SUM formulas for hours
  ├── Parent % = calculated from rolled-up hours
  └── TOTALS row = SUMPRODUCT (only sum parents!)
      ↓
Apply Validation
  ├── Status (child only): COMPLETED, NOT STARTED
  ├── Availability: READY, ON HOLD, NOT AVAILABLE
  ├── Priority: HIGH, MEDIUM, LOW
  ├── Assessment: ACCEPTABLE, MINOR DEFICIENCY, NON-SERVICEABLE
  ├── Datasheet: YES, NO, N/A
  ├── Date Due: >= TODAY()
  └── **Stop validation at last data row (before TOTALS)**
```

### **PopulateAllTasks() - Aggregates Data**

```
All Scope Sheets
  ↓
Loop Each Sheet
  ├── Skip if not scope sheet (check CodeName, headers, Cell G4)
  ├── Start at Row 6 (SC_FIRST_DATA_ROW)
  ├── Read Task_ID from Column E
      ↓
Classify by Dot Count
  ├── Task_ID with 1 dot (e.g., "1.1"):
  │   ├── Parent row (Task level)
  │   ├── Save task name for children
  │   └── Skip (don't extract)
  ├── Task_ID with 2 dots (e.g., "1.1.1"):
  │   ├── Child row (Apparatus level)
  │   ├── Extract ALL data ⭐
  │   └── Add to collection
  ├── "TOTALS":
  │   └── Stop processing this sheet
      ↓
Build Output Row (Array 1-21)
  ├── Column 1-21: Data from scope sheet
  ├── Map scope columns → All_Tasks columns
  ├── Critical: STATUS from B→S, Task_ID from E→C
  ├── Apparatus_Hours (Column P→P) ✓ Same position
  └── **NEVER populate Column 22 (V) - PROTECTED**
      ↓
Write to All_Tasks
  ├── Clear existing data (Columns A-U only)
  ├── Write apparatus rows
  ├── Map columns correctly
  └── Sync All_Tasks_Billing (formulas in Columns W-AT)
```

---

## ⚠️ **Critical Gotchas for Excel MCP**

### **1. Column Mapping Differences**

**DANGER:** Scope → All_Tasks column positions change!

```
Scope Sheet:              All_Tasks:
Column B = STATUS    →    Column S (19) ⚠️ MAJOR CHANGE!
Column C = AVAIL     →    Column T (20)
Column D = PRIORITY  →    Column U (21)
Column E = TASK_ID   →    Column C (3)
```

**Apparatus_Hours stays the same:**
```
Column P = APPARATUS_HOURS → Column P (16) ✓ Good!
```

### **2. Hierarchical Task Structure**

**Must count dots in Task_ID:**
```vba
Function CountDots(inputString As String) As Long
    ' Counts periods in string
End Function
```

**Extraction rules:**
- `1.1` (1 dot) = Parent → **SKIP** (has formulas, not actual data)
- `1.1.1` (2 dots) = Child → **EXTRACT** (actual apparatus data)
- `TOTALS` = Summary → **STOP**

**Only extract child rows (2 dots) for apparatus data!**

### **3. Column V Protection**

**All_Tasks Column V is SACRED:**
```vba
Const MAX_POPULATE_COLUMN As Integer = 21  ' Column U - NEVER go past this
```

**Why it's protected:**
- Reserved for standardized apparatus names
- Billing system relies on it
- PopulateAllTasks explicitly avoids it
- **Excel MCP must respect this!**

### **4. Formula vs. Manual Cells**

**Parent rows (1 dot):**
- Status: Formula (OVERDUE/COMPLETED/IN PROGRESS/NOT STARTED)
- Date Due: AGGREGATE rollup formula
- Hours: SUM formulas
- %: Calculated from hours

**Child rows (2 dots):**
- Status: Dropdown (COMPLETED/NOT STARTED)
- Apparatus data: Manual entry
- %: Formula (1 - Remaining/Apparatus)

**Don't extract formulas! Only extract child row values.**

### **5. TOTALS Row Detection**

**How to find TOTALS:**
```vba
' Look for "TOTALS" in Column M (NOTES)
If UCase(Trim(ws.Cells(row, SC_COL_NOTES).Value)) = "TOTALS" Then
    ' This is TOTALS row - STOP
End If
```

**TOTALS row has:**
- SUMPRODUCT formulas (only sum parent rows)
- Should NOT be included in apparatus extraction

### **6. NETA Standard Validation**

**Valid values (from All_Lists sheet):**
```
ATS   - Acceptance Testing Specifications
MTS   - Maintenance Testing Specifications  
ECS   - Engineering/Consulting Services
SPEC  - Specification-based testing
OTHER - Other testing types
```

**Location in files:**
- Scope sheets: Cell H4
- Task_Entry: Column B (Row 2)
- All_Tasks: Column B (for all apparatus)

---

## 🎯 **Excel MCP Tool Specifications**

### **Tool 1: extract_apparatus_master**

```python
def extract_apparatus_master(generator_template_path: str) -> pd.DataFrame:
    """
    Extract Apparatus Type Master from generator template
    
    File: RESA Power - Project Data Entry MASTER.xlsm
    Sheet: Apparatus_List_w_Hours
    
    Returns DataFrame with:
        - Apparatus_Type (text)
        - ATS_Hours (numeric)
        - MTS_Hours (numeric)
        - ECS_Hours (numeric)
        - SPEC_Hours (numeric)
        - Default_NETA_Standard (choice)
    
    Maps to Dataverse: Apparatus_Type_Master table
    """
```

### **Tool 2: extract_scope_financial_config**

```python
def extract_scope_financial_config(generator_template_path: str) -> pd.DataFrame:
    """
    Extract financial rates from generator template
    
    File: RESA Power - Project Data Entry MASTER.xlsm
    Sheet: Scope_Labor_Rates
    
    Uses Global_Constants:
        - SLR_COL_SCOPE (1) = Scope
        - SLR_COL_TOTAL_APP_HRS (2) = Total Apparatus Hours
        - SLR_COL_SCOPE_BILL_RATE (3) = Base rate
        - SLR_COL_COMMUTE_BILL_RATE (4-13) = Time adder rates
        - SLR_COL_SCOPE_MULTIPLIER (18) = Multiplier
    
    Returns: 19 columns of financial configuration
    Maps to Dataverse: Scope_Financial_Configuration table
    """
```

### **Tool 3: extract_project_scopes**

```python
def extract_project_scopes(project_tracker_path: str) -> pd.DataFrame:
    """
    Extract all scopes from a project tracker
    
    File: e.g., LASNAP16 MASTER.xlsm
    
    Identify scope sheets by:
        1. CodeName starts with "Scope_"
        2. OR Cell G4 (SC_SCOPE_CELL) is populated
        3. OR Row 5 has specific headers (TASK_ID, STATUS, etc.)
    
    For each scope sheet, extract:
        - Scope_Name (Cell G4)
        - NETA_Standard (Cell H4)
        - Mode (Cell T2) - optional
        - Total_Apparatus_Count (count child rows)
        - Total_Quoted_Hours (TOTALS row, Column P)
    
    Returns DataFrame ready for: 02_Scopes_Import.csv
    """
```

### **Tool 4: extract_apparatus_from_scope**

```python
def extract_apparatus_from_scope(
    project_tracker_path: str,
    scope_sheet_name: str
) -> pd.DataFrame:
    """
    Extract apparatus from specific scope sheet
    
    Process:
    1. Open sheet, start at Row 6 (SC_FIRST_DATA_ROW)
    2. Loop through rows until TOTALS or blank Task_ID
    3. Read Task_ID from Column E (SC_COL_TASK_ID)
    4. Count dots:
        - 1 dot = Parent (task) - save task name, continue
        - 2 dots = Child (apparatus) - EXTRACT THIS ROW
        - "TOTALS" or empty = STOP
    
    For each child row (2 dots), extract using SC_COL_* constants:
        - Task_ID (Column E)
        - Task_Name (from saved parent)
        - Apparatus (Column F - SC_COL_NAME_APP)
        - Designation (Column G - SC_COL_DES)
        - Drawing (Column H - SC_COL_DRW)
        - Quoted_Hours (Column P - SC_COL_AHRS) ⭐ CRITICAL
        - Assessment (Column J - SC_COL_ASSESSMENT)
        - Datasheet (Column K - SC_COL_DATASHEET)
        - Status (Column B - SC_COL_STATUS)
        - % Completion (Column N - SC_COL_PCT)
        - Remaining_Hours (Column Q - SC_COL_REMHRS)
        - Actual_Hours (Column R - SC_COL_ACTHRS)
        - Notes (Column M - SC_COL_NOTES)
    
    Add context fields:
        - Scope_Name (from Cell G4)
        - NETA_Standard (from Cell H4)
    
    Returns DataFrame ready for: 04_Apparatus_Import.csv
    """
```

### **Tool 5: extract_all_tasks (Alternative)**

```python
def extract_all_tasks(project_tracker_path: str) -> pd.DataFrame:
    """
    Extract pre-aggregated apparatus from All_Tasks sheet
    
    File: Project tracker
    Sheet: All_Tasks
    
    Read Columns A-U using AT_COL_* constants:
        - AT_COL_SCOPE (1) = Scope
        - AT_COL_NETA (2) = NETA_Standard
        - AT_COL_TID (3) = Task_ID
        - AT_COL_TASK (4) = Task name
        - AT_COL_APP (5) = Apparatus
        - AT_COL_AHRS (16) = Apparatus_Hours
        - AT_COL_STATUS (19) = STATUS ⚠️ Column S, not B!
        - AT_COL_AVAIL (20) = AVAILABILITY
        - AT_COL_PRIORITY (21) = PRIORITY
    
    CRITICAL: 
    - Column mapping is DIFFERENT from scope sheets!
    - STATUS is in Column S (19), not Column B!
    - NEVER read Column V (22) - it's protected
    
    Filter: Only apparatus rows (Task_ID with 2 dots)
    
    Returns DataFrame ready for: 04_Apparatus_Import.csv
    """
```

### **Tool 6: generate_import_csvs**

```python
def generate_import_csvs(
    apparatus_master_df: pd.DataFrame,
    scope_financial_df: pd.DataFrame,
    scopes_df: pd.DataFrame,
    apparatus_df: pd.DataFrame,
    output_dir: str
) -> Dict[str, str]:
    """
    Generate all import CSVs with validation
    
    Creates:
    1. Apparatus_Type_Master.csv (from template)
    2. Scope_Financial_Config.csv (from template)
    3. 02_Scopes_Import.csv (from project tracker)
    4. 04_Apparatus_Import.csv (from project tracker)
    
    Validations:
    - NETA_Standard in ['ATS', 'MTS', 'ECS', 'SPEC', 'OTHER']
    - Apparatus_Type exists in Apparatus_Type_Master
    - Numeric fields are actually numeric
    - Dates in proper format (mm/dd/yyyy)
    - % Completion as decimal (0-1, not 0-100%)
    - No duplicate apparatus designations
    - All scopes have valid NETA standard
    
    Returns: Dict mapping CSV type to file path
    """
```

---

## 📋 **Validation Rules (from All_Lists)**

### **Dropdown Values:**

**NETA_Standard:**
```
Source: =All_Lists!$F$2:$F$3
Values: ATS, MTS
Extended: ECS, SPEC, OTHER
```

**Status (Parent):**
```
Source: =All_Lists!$B$2:$B$5
Values: COMPLETED, NOT STARTED, IN PROGRESS, OVERDUE
```

**Status (Child):**
```
Source: =All_Lists!$B$2:$B$3
Values: COMPLETED, NOT STARTED
```

**Assessment:**
```
Source: =All_Lists!$A$2:$A$4
Values: ACCEPTABLE, MINOR DEFICIENCY, NON-SERVICEABLE
```

**Availability:**
```
Source: =All_Lists!$C$2:$C$4
Values: READY, ON HOLD, NOT AVAILABLE
```

**Priority:**
```
Source: =All_Lists!$D$2:$D$4
Values: HIGH, MEDIUM, LOW
```

**Datasheet:**
```
List: YES,NO,N/A
```

### **Data Type Rules:**

**Dates:**
- Format: mm/dd/yyyy
- Date Due: Must be >= TODAY()
- Date Completed: Auto in AUTO mode, Manual in MANUAL mode

**Numbers:**
- Apparatus_Hours: Decimal, >= 0
- Remaining_Hours: Decimal, >= 0
- Actual_Hours: Decimal, >= 0
- Task_Delays: Integer, >= 0

**Percentages:**
- Storage: Decimal (0 to 1)
- Display: Percentage format
- Formula: `=(1 - (Remaining_Hours / Apparatus_Hours))`

---

## 🎯 **Implementation Priorities**

### **Phase 1: Foundation (Week 1)**

1. ✅ Create Python project structure
2. ✅ Install dependencies (openpyxl, pandas, mcp SDK)
3. ✅ Create Global_Constants mapping (Python dict)
4. ✅ Implement sheet identification functions
5. ✅ Test with generator template

**Deliverable:** Can identify scope sheets and read cells

### **Phase 2: Master Data Extraction (Week 1)**

6. ✅ Implement extract_apparatus_master
7. ✅ Implement extract_scope_financial_config
8. ✅ Generate master data CSVs
9. ✅ Validate against Dataverse schema

**Deliverable:** Master data ready for import

### **Phase 3: Project Data Extraction (Week 2)**

10. ✅ Implement extract_project_scopes
11. ✅ Implement extract_apparatus_from_scope
12. ✅ Implement hierarchical Task_ID logic
13. ✅ Test with LASNAP16

**Deliverable:** Project data extraction working

### **Phase 4: Validation & CSV Generation (Week 2)**

14. ✅ Implement all validation rules
15. ✅ Generate import CSVs
16. ✅ Cross-validation (apparatus types exist, etc.)
17. ✅ Error reporting

**Deliverable:** Validated, import-ready CSVs

### **Phase 5: MCP Integration (Week 3)**

18. ✅ Package as MCP server
19. ✅ Add to claude_desktop_config.json
20. ✅ Integration with Filesystem MCP
21. ✅ Integration with Dataverse MCP

**Deliverable:** Full MCP automation

---

## 📝 **Next Steps**

1. **Review this analysis** - Confirm understanding
2. **View actual LASNAP16** - Verify against real data
3. **Create Python constants** - Port Global_Constants
4. **Build first tool** - extract_apparatus_master
5. **Test iteratively** - One tool at a time

---

**Created:** November 16, 2025  
**Source:** Analysis of 10 VBA modules (~2,000+ lines)  
**Classification:** Internal - Technical Documentation  
**Version:** 1.0
