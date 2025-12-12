# Excel Estimator → Dataverse Mapping Specification

**Created:** November 27, 2025  
**Source:** Garney Central Mesa Reuse Estimator (434469 REV6)  
**Target:** RESA Power Project Tracker v1.5.0.0

---

## 📊 Executive Summary

The Excel Estimator workbook contains all data needed to populate a new project in Dataverse. This document maps Excel locations to Dataverse tables and fields.

### Data Flow Overview

```
Excel Estimator Workbook
    │
    ├── Equipment Reference Sheet → ApparatusTypeMaster (reference only)
    │
    ├── Print_Template Sheet → Projects (project-level summary)
    │
    └── Scope Sheets (IPS NETA ATS, NWWRP NETA ATS, etc.)
            │
            ├── Header Section (Rows 2-4) → ProjectScope
            │
            ├── Financial Config (Rows 6-33, Cols L-P) → ScopeLaborDetail
            │
            └── Apparatus List (Rows 6-488, Cols C-J) → Apparatus
```

---

## 🗂️ TABLE 1: Projects

**Source:** Print_Template sheet + First Scope Sheet header  
**Dataverse Table:** `cr950_Projects`

| Dataverse Field | Excel Location | Example Value |
|-----------------|----------------|---------------|
| `cr950_project_name` | First scope sheet B2 or manual entry | "Garney Central Mesa Reuse" |
| `cr950_project_number` | Filename prefix or manual | "434469" |
| `cr950_status` | Default | "Quoted" (Choice) |
| `cr950_total_value` | Print_Template R13 | $97,139.38 |
| `cr950_client` | Scope sheet E3 (parsed) | Lookup to Client |
| `cr950_site` | Scope sheet E4 (parsed) | Lookup to Site |

### Notes:
- Project Number extracted from filename: `434469 REV6 - Garney...`
- Client name parsed from scope header
- Total value aggregated from all scope sheets

---

## 🗂️ TABLE 2: ProjectScope

**Source:** Each scope sheet (IPS NETA ATS, NWWRP NETA ATS, etc.)  
**Dataverse Table:** `cr950_ProjectScope`

| Dataverse Field | Excel Location | Example Value |
|-----------------|----------------|---------------|
| `cr950_scope_name` | Cell B2 | "IPS NETA ATS" |
| `cr950_project` | Parent project lookup | → Projects record |
| `cr950_test_type` | Cell C4 | "ATS" or "MTS" (Choice) |
| `cr950_total_apparatus_hours` | Cell J3 | 333.75 |
| `cr950_total_scope_value` | Cell P4 | $61,025.62 |
| `cr950_customer_info` | Cell E3 | "Ludvik Electric..." |
| `cr950_site_address` | Cell E4 | "3626 E. Thomas Road..." |
| `cr950_sld_reference` | Cell F3 | "SLD: E-00-108/110" |

### Scope Sheets to Process:
Only process sheets where:
- Sheet name is NOT "Equipment Reference", "Print_Template", or ends with ".X"
- Cell P4 (Total Cost) has a non-zero value

---

## 🗂️ TABLE 3: ScopeLaborDetail

**Source:** Each scope sheet, Rows 6-33, Columns L-P  
**Dataverse Table:** `cr950_ScopeLaborDetail`

### ONSITE LABOR (Rows 6-13)

| Dataverse Field | Excel Row | M (%) | N (Hrs) | O (Rate) | P (Total) |
|-----------------|-----------|-------|---------|----------|-----------|
| `cr950_labor_blended_10hr_pct` | 6 | M6 | | | |
| `cr950_labor_blended_10hr_rate` | 6 | | | O6 | |
| `cr950_labor_blended_10hr_total` | 6 | | | | P6 |
| `cr950_labor_blended_12hr_pct` | 7 | M7 | | | |
| `cr950_labor_blended_12hr_rate` | 7 | | | O7 | |
| `cr950_labor_ot_rate_pct` | 8 | M8 | | | |
| `cr950_labor_ot_rate` | 8 | | | O8 | |
| `cr950_labor_dt_rate_pct` | 9 | M9 | | | |
| `cr950_labor_dt_rate` | 9 | | | O9 | |
| `cr950_badging_parking_pct` | 10 | M10 | | | |
| `cr950_loto_hours_pct` | 11 | M11 | | | |
| `cr950_pm_hours_pct` | 12 | M12 | | | |
| `cr950_daily_commute_pct` | 13 | M13 | | | |
| **ONSITE TOTALS** | 14 | M14 | N14 | O14 | P14 |

### OFFSITE LABOR (Rows 16-18)

| Dataverse Field | Excel Row | M (%) | O (Rate) | P (Total) |
|-----------------|-----------|-------|----------|-----------|
| `cr950_report_hours_pct` | 16 | M16 | O16 | P16 |
| `cr950_project_mgmt_pct` | 17 | M17 | O17 | P17 |
| `cr950_loading_prep_pct` | 18 | M18 | O18 | P18 |
| **OFFSITE TOTALS** | 19 | M19 | O19 | P19 |

### TRAVEL (Rows 21-25)

| Dataverse Field | Excel Row | M (Units) | N (Cost) | O (Mult) | P (Total) |
|-----------------|-----------|-----------|----------|----------|-----------|
| `cr950_travel_hours` | 21 | M21 | N21 | O21 | P21 |
| `cr950_hotel_per_diem` | 22 | M22 | N22 | O22 | P22 |
| `cr950_flights` | 23 | M23 | N23 | O23 | P23 |
| `cr950_car_rental` | 24 | M24 | N24 | O24 | P24 |
| `cr950_travel_misc` | 25 | M25 | N25 | O25 | P25 |
| **TRAVEL TOTALS** | 26 | | | | P26 |

### OUTSIDE SERVICES (Rows 28-32)

| Dataverse Field | Excel Row | M (Units) | N (Cost) | O (Mult) | P (Total) |
|-----------------|-----------|-----------|----------|----------|-----------|
| `cr950_generator_rental` | 28 | M28 | N28 | O28 | P28 |
| `cr950_test_equipment_rental` | 29 | M29 | N29 | O29 | P29 |
| `cr950_oil_sample` | 30 | M30 | N30 | O30 | P30 |
| `cr950_outside_misc_1` | 31 | M31 | N31 | O31 | P31 |
| `cr950_outside_misc_2` | 32 | M32 | N32 | O32 | P32 |
| **OUTSIDE SERVICES TOTALS** | 33 | | | | P33 |

### GRAND TOTALS

| Dataverse Field | Excel Cell |
|-----------------|------------|
| `cr950_scope_total_unadjusted` | P3 |
| `cr950_adjustment_multiplier` | M4 |
| `cr950_adjustment_percent` | N4 |
| `cr950_adjustment_fixed` | O4 |
| `cr950_scope_total_adjusted` | P4 |

---

## 🗂️ TABLE 4: Apparatus

**Source:** Each scope sheet, Rows 6-488, Columns C-J  
**Dataverse Table:** `cr950_Apparatus`

### Row Detection:
- Valid apparatus row: Column C (QTY) contains a numeric value > 0
- Skip rows where QTY is empty, 0, or contains section headers

| Dataverse Field | Excel Column | Example |
|-----------------|--------------|---------|
| `cr950_project_scope` | Parent scope lookup | → ProjectScope record |
| `cr950_project` | Parent project lookup | → Projects record |
| `cr950_quantity` | C (QTY) | 6 |
| `cr950_neta_section` | D (Section) | "7.7" |
| `cr950_apparatus_type_name` | E (Apparatus Type) | "Circuit Breaker MV - Vacuum Bkr" |
| `cr950_designation` | F (Designation) | "SWGR-00-001" |
| `cr950_notes` | G (Notes) | "E-00-108" |
| `cr950_hours_per_unit` | I (Hrs/Unit) | 4 |
| `cr950_total_hours` | J (Hrs/Line) | 24 |
| `cr950_apparatus_type_master` | Lookup via E | → ApparatusTypeMaster |
| `cr950_completion_status` | Default | "Not Started" |

### Apparatus Expansion Logic:
**Option A: One record per line** (simpler)
- QTY=6 becomes 1 Apparatus record with quantity field = 6
- Hours tracked at line level

**Option B: One record per unit** (more granular) 
- QTY=6 becomes 6 separate Apparatus records
- Each record has Hours = Hrs/Unit value
- Allows individual completion tracking

**Recommended:** Option B for granular tracking

---

## 🔄 Export Process Flow

### Step 1: Parse Workbook Structure
```python
1. Load Excel workbook
2. Identify scope sheets (exclude Equipment Reference, Print_Template, *.X)
3. For each scope sheet with P4 > 0:
   - Extract scope header data
   - Extract financial config
   - Extract apparatus list
```

### Step 2: Create Project Record
```python
1. Extract project name from first scope or filename
2. Extract project number from filename
3. Sum all scope totals for project total
4. Create Project record in Dataverse
5. Store Project ID for child records
```

### Step 3: Create Scope Records
```python
For each valid scope sheet:
    1. Extract header data (B2, C4, E3, E4, F3, J3, P4)
    2. Create ProjectScope record with Project lookup
    3. Store Scope ID for child records
```

### Step 4: Create ScopeLaborDetail Records
```python
For each scope:
    1. Extract all financial config cells
    2. Create ScopeLaborDetail record
    3. Link to ProjectScope via lookup
```

### Step 5: Create Apparatus Records
```python
For each scope:
    For each row where C > 0:
        If Option B (expand by quantity):
            For i = 1 to QTY:
                Create Apparatus record with Hrs/Unit
        Else (Option A):
            Create single Apparatus record with total hours
```

---

## 📋 Validation Rules

### Before Export:
1. ✅ At least one scope sheet has P4 > 0
2. ✅ Each scope has valid test type (ATS/MTS) in C4
3. ✅ Apparatus rows have valid NETA section in D column
4. ✅ Financial config rates are positive numbers

### After Export:
1. ✅ Project total = SUM of scope totals
2. ✅ Scope apparatus hours = SUM of apparatus hours
3. ✅ ScopeLaborDetail linked to correct scope
4. ✅ All apparatus have valid parent lookups

---

## 🛠️ Implementation Options

### Option 1: Power Automate Flow
- **Trigger:** File upload to SharePoint/OneDrive
- **Process:** Parse Excel → Create records via Dataverse connector
- **Pros:** Native Microsoft integration, no code maintenance
- **Cons:** Complex Excel parsing, limited error handling

### Option 2: Python Script + Dataverse API
- **Trigger:** Manual run or scheduled
- **Process:** openpyxl parsing → REST API calls
- **Pros:** Full control, rich error handling, can run locally
- **Cons:** Requires Python environment, API authentication

### Option 3: Power Apps Canvas App
- **Trigger:** User uploads file in app
- **Process:** Office Scripts or Power Automate backend
- **Pros:** User-friendly interface, integrated with ecosystem
- **Cons:** Limited Excel parsing capabilities

### Option 4: Excel VBA Export
- **Trigger:** Button click in Excel
- **Process:** VBA generates JSON → Power Automate webhook
- **Pros:** Familiar to users, works in existing workflow
- **Cons:** VBA maintenance, security restrictions

**Recommended:** Option 2 (Python) for initial development, then Option 1 (Power Automate) for production automation.

---

## 📊 Sample Data Structure (JSON)

```json
{
  "project": {
    "name": "Garney Central Mesa Reuse",
    "number": "434469",
    "total_value": 97139.38,
    "status": "Quoted"
  },
  "scopes": [
    {
      "name": "IPS NETA ATS",
      "test_type": "ATS",
      "total_hours": 333.75,
      "total_value": 61025.62,
      "labor_detail": {
        "blended_10hr_pct": 1.0,
        "blended_10hr_rate": 165,
        "commute_pct": 0.05,
        "report_hours_pct": 0.05,
        "oil_sample_units": 1,
        "oil_sample_cost": 300
      },
      "apparatus": [
        {
          "quantity": 1,
          "neta_section": "7.1",
          "type": "Switchgear - Medium Voltage",
          "designation": "SES-00-001",
          "notes": "E-00-108",
          "hours_per_unit": 2.5
        }
      ]
    }
  ]
}
```

---

## ✅ Next Steps

1. **Decide on apparatus expansion logic** (Option A vs B)
2. **Choose implementation approach** (Python recommended for dev)
3. **Create test dataset** in Dataverse manually first
4. **Build extraction script** to generate JSON
5. **Build import script** to create Dataverse records
6. **Test with Garney sample file**
7. **Validate rollup calculations**

---

**Document Version:** 1.0  
**Status:** Ready for Review
