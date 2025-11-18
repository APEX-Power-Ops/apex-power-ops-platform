# ScopeLaborDetail Table - Clean Build Specification

**Version:** 1.3.0.1  
**Created:** November 16, 2025  
**Status:** Ready for Implementation  
**Build Time:** 20-25 minutes

---

## 🎯 Overview

Building ScopeLaborDetail from scratch with **14 optimized fields** (massive simplification from 55-field original).

**Purpose:** Store labor rate configurations per project scope that drive the entire revenue calculation chain from apparatus → scope → project levels.

**Key Design Principles:**
- **Excel Alignment:** Matches Excel Estimator structure exactly (Onsite/Offsite/Travel/Outside Services)
- **Dual Tracking:** Dollar totals (visibility) + Per-hour rates (calculation)
- **Weighted Average Model:** Totals ÷ Hours = Effective Rate (matches Excel NOT ADJUSTED / ADJUSTED logic)
- **Single Source of Truth:** Effective Labor Rate calculated once, used everywhere
- **Import-Ready:** Designed for hidden Excel sheet validation + MCP automation

---

## 📊 Table Configuration

### **Basic Information**

```
Display Name: Scope Labor Detail
Plural Name: Scope Labor Details
Schema Name: cr950_scopelabordetail
Primary Field: cr950_name (auto-generated, use pattern "Scope-{ScopeNumber}-Labor")
Ownership: Organization
```

### **Relationships**

```
1. ProjectScope (Parent) - Many-to-One
   - Lookup Field: cr950_projectscope_id
   - Relationship: N:1 (Each scope has ONE labor configuration)
   - Required: Yes
   - On Delete: Cascade (if scope deleted, labor config deleted)
```

---

## 🏗️ Field Definitions (14 Fields)

### **Category 1: Core Configuration (4 fields)**

#### **1. Project Scope** (Lookup)
```
Display Name: Project Scope
Schema Name: cr950_projectscope_id
Type: Lookup
Target: cr950_projectscope
Required: Yes
Description: Parent scope this labor configuration belongs to
Relationship: N:1 (Each scope has ONE labor configuration)
On Delete: Cascade All
```

#### **2. Total Apparatus Hours**
```
Display Name: Total Apparatus Hours
Schema Name: cr950_total_apparatus_hours
Type: Decimal
Precision: 2
Min: 0
Max: 50000.00
Required: Yes
Description: Total estimated hours across all apparatus in this scope (denominator for all rate calculations)
Example: 176 (from Excel screenshot)
Note: Used as divisor for all per-hour rate calculations. Decimal type allows precise rollup from apparatus-level hours.
Excel Source: "Total App Hours" cell
```

#### **3. Scope Multiplier**
```
Display Name: Scope Multiplier
Schema Name: cr950_scope_multiplier
Type: Decimal
Precision: 2
Min: 0.10
Max: 100.00
Default: 1.00
Required: Yes
Description: Multiplier applied to sum of all per-hour rates (markup, discount, or typical build quantity)
Examples: 
  - 1.00 = No adjustment (100%, from Excel "NOT ADJUSTED" vs "ADJUSTED")
  - 1.20 = 20% markup
  - 0.85 = 15% discount
  - 7.00 = 7 identical data center power blocks
Excel Source: "PercentAdjust" or similar cell (100% in screenshot = 1.00)
```

#### **4. Notes**
```
Display Name: Notes
Schema Name: cr950_notes
Type: Multiple Lines of Text
Max Length: 2000
Format: Text
Description: Additional context, special rate justifications, scope-specific notes
```

---

### **Category 2: Onsite Labor (2 fields)**

**Design:** Standardized terminology matching Excel "Onsite Labor Totals" section

#### **5. Onsite Labor Total**
```
Display Name: Onsite Labor Total
Schema Name: cr950_onsite_labor_total
Type: Currency
Precision: 2
Description: Total onsite labor costs (daily commute, mobilization, onsite work, LOTO, misc, PM)
Example: $45,936 (from Excel screenshot "Onsite Labor Totals" Bill Totals column)
Excel Source: Sum of "Onsite Labor Totals" section Bill Totals
Import Source: Hidden "Dataverse_Export" sheet, Column C
```

#### **6. Onsite Labor Rate** (Calculated)
```
Display Name: Onsite Labor Rate
Schema Name: cr950_onsite_labor_rate
Type: Currency (Calculated)
Precision: 2
Behavior: Calculated
Formula:
if(cr950_total_apparatus_hours > 0,
   cr950_onsite_labor_total / cr950_total_apparatus_hours,
   0
)

Example: $261.00/hr (if $45,936 ÷ 176 hrs)
Description: Per-hour rate for onsite labor component (component of Effective Labor Rate)
```

---

### **Category 3: Offsite Labor (2 fields)**

**Design:** Standardized terminology matching Excel "Offsite Labor Totals" section

#### **7. Offsite Labor Total**
```
Display Name: Offsite Labor Total
Schema Name: cr950_offsite_labor_total
Type: Currency
Precision: 2
Description: Total offsite labor costs (office PM, report writing, misc office work)
Example: $2,772 (from Excel screenshot "Offsite Labor Totals" Bill Totals column)
Excel Source: Sum of "Offsite Labor Totals" section Bill Totals
Import Source: Hidden "Dataverse_Export" sheet, Column D
```

#### **8. Offsite Labor Rate** (Calculated)
```
Display Name: Offsite Labor Rate
Schema Name: cr950_offsite_labor_rate
Type: Currency (Calculated)
Precision: 2
Behavior: Calculated
Formula:
if(cr950_total_apparatus_hours > 0,
   cr950_offsite_labor_total / cr950_total_apparatus_hours,
   0
)

Example: $15.75/hr (if $2,772 ÷ 176 hrs)
Description: Per-hour rate for offsite labor component (component of Effective Labor Rate)
```

---

### **Category 4: Travel (2 fields)**

**Design:** Matches Excel "Travel Cost/Rate Groups" section

#### **9. Travel Total**
```
Display Name: Travel Total
Schema Name: cr950_travel_total
Type: Currency
Precision: 2
Description: Total travel costs (flights, car rental, hotel, per diem, travel time)
Example: $5,175 (from Excel screenshot "Travel Cost/Rate Groups" Totals column)
Excel Source: Sum of "Travel Cost/Rate Groups" section Totals
Import Source: Hidden "Dataverse_Export" sheet, Column E
```

#### **10. Travel Rate** (Calculated)
```
Display Name: Travel Rate
Schema Name: cr950_travel_rate
Type: Currency (Calculated)
Precision: 2
Behavior: Calculated
Formula:
if(cr950_total_apparatus_hours > 0,
   cr950_travel_total / cr950_total_apparatus_hours,
   0
)

Example: $29.40/hr (if $5,175 ÷ 176 hrs)
Description: Per-hour rate for travel component (component of Effective Labor Rate)
```

---

### **Category 5: Outside Services (2 fields)**

**Design:** Matches Excel "Outside Services" section

#### **11. Outside Services Total**
```
Display Name: Outside Services Total
Schema Name: cr950_outside_services_total
Type: Currency
Precision: 2
Description: Total outside services costs (test equipment, generator, lab, subcontractors, misc)
Example: $10,125 (from Excel screenshot "Outside Services" Totals column)
Excel Source: Sum of "Outside Services" section Totals
Import Source: Hidden "Dataverse_Export" sheet, Column F
```

#### **12. Outside Services Rate** (Calculated)
```
Display Name: Outside Services Rate
Schema Name: cr950_outside_services_rate
Type: Currency (Calculated)
Precision: 2
Behavior: Calculated
Formula:
if(cr950_total_apparatus_hours > 0,
   cr950_outside_services_total / cr950_total_apparatus_hours,
   0
)

Example: $57.53/hr (if $10,125 ÷ 176 hrs)
Description: Per-hour rate for outside services component (component of Effective Labor Rate)
```

---

### **Category 6: Revenue Calculation (1 field)**

**This is the CRITICAL field that drives all apparatus-level revenue**

#### **13. Effective Labor Rate** ⭐ (Calculated)
```
Display Name: Effective Labor Rate
Schema Name: cr950_effective_labor_rate
Type: Currency (Calculated)
Precision: 2
Behavior: Calculated
Formula:
(cr950_onsite_labor_rate + 
 cr950_offsite_labor_rate + 
 cr950_travel_rate + 
 cr950_outside_services_rate) * cr950_scope_multiplier

Example: $363.68/hr
Calculation Breakdown:
  - Onsite Rate: $261.00
  - Offsite Rate: $15.75
  - Travel Rate: $29.40
  - Outside Services Rate: $57.53
  - Sum: $363.68
  - Multiplier: 1.00
  - Final: $363.68 × 1.00 = $363.68/hr

Excel Verification: $64,008 (NOT ADJUSTED) ÷ 176 hrs = $363.68/hr ✓

Description: **SINGLE SOURCE OF TRUTH** - Used by ApparatusRevenue for all revenue calculations
Usage Example: 45.5 apparatus hours × $363.68/hr = $16,547.44 apparatus revenue
```

---

### **Category 7: Metadata (1 field)**

#### **14. Source**
```
Display Name: Source
Schema Name: cr950_source
Type: Choice (Global Choice - Shared Option Set)
Global Choice Name: cr950_datasource
Options:
  - ESTIMATOR (Value: 1) - Imported from Excel Estimator via MCP
  - MANUAL (Value: 2) - Hand-entered by user
  - ADJUSTED (Value: 3) - Modified after initial import
  - API_IMPORT (Value: 4) - Imported via external API (future)
  - MIGRATION (Value: 5) - Data migration from legacy system (future)
Default: MANUAL
Required: Yes
Description: Tracks data origin for audit trail across all system tables
Note: Global choice allows consistent source tracking in ApparatusRevenue, ScopeFinancials, ProjectFinancials, etc.
```

---

## 🔧 Build Steps (Power Apps UI)

### **Step 1: Create Table (5 min)**

1. Navigate to: **Power Apps > Solutions > [Your Solution]**
2. Click **+ New > Table > Table**
3. Fill in:
   - Display Name: `Scope Labor Detail`
   - Plural Name: `Scope Labor Details`
   - Enable: Attachments ❌, Notes ✅, Activities ❌
4. Click **Save**

### **Step 2: Add Lookup to ProjectScope (3 min)**

1. In ScopeLaborDetail table > **Columns > + New Column**
2. Configure:
   ```
   Display Name: Project Scope
   Data Type: Lookup
   Related Table: ProjectScope
   Required: Yes (Business Required)
   ```
3. Click **Advanced Options**:
   - Delete Relationship Behavior: **Cascade All** (if scope deleted, labor config deleted)
4. **Save**

### **Step 3: Create Global Choice (2 min)**

**Create Data Source Global Choice (reusable across all tables)**

1. Navigate to: **Solutions > [Your Solution] > + New > More > Choice**
2. Configure:
   ```
   Display Name: Data Source
   Name: cr950_datasource
   Type: Global Choice (not local)
   ```
3. Add Options:
   ```
   + New Option > Label: ESTIMATOR > Value: 1 > Save
   + New Option > Label: MANUAL > Value: 2 > Save
   + New Option > Label: ADJUSTED > Value: 3 > Save
   + New Option > Label: API_IMPORT > Value: 4 > Save
   + New Option > Label: MIGRATION > Value: 5 > Save
   ```
4. Click **Save & Close**

### **Step 4: Add Simple Fields (8 min)**

**Batch 1: Core Config (3 fields)**
```
+ New Column > Total Apparatus Hours > Decimal (Precision 2) > Min 0 > Max 50000 > Required > Save
+ New Column > Scope Multiplier > Decimal (Precision 2) > Min 0.10 > Max 100.00 > Default 1.00 > Required > Save
+ New Column > Notes > Multiple Lines of Text (Max 2000) > Save
```

**Batch 2: Cost Category Totals (4 fields)**
```
+ New Column > Onsite Labor Total > Currency > Save
+ New Column > Offsite Labor Total > Currency > Save
+ New Column > Travel Total > Currency > Save
+ New Column > Outside Services Total > Currency > Save
```

**Batch 3: Metadata (1 field)**
```
+ New Column > Source > Choice
  ├─ Sync this choice with: Data Source (cr950_datasource) [select existing global choice]
  ├─ Default: MANUAL (2)
  └─ Required: Yes
  Save
```

### **Step 5: Add Calculated Fields (10 min)**

**Important:** Add in this order (dependencies matter - all rates depend on Total_Apparatus_Hours)

**Calc 1: Onsite Labor Rate**
```
+ New Column
Display Name: Onsite Labor Rate
Data Type: Currency
Behavior: Calculated
Formula: 
if(cr950_total_apparatus_hours > 0,
   cr950_onsite_labor_total / cr950_total_apparatus_hours,
   0
)
Save
```

**Calc 2: Offsite Labor Rate**
```
+ New Column
Display Name: Offsite Labor Rate
Data Type: Currency
Behavior: Calculated
Formula:
if(cr950_total_apparatus_hours > 0,
   cr950_offsite_labor_total / cr950_total_apparatus_hours,
   0
)
Save
```

**Calc 3: Travel Rate**
```
+ New Column
Display Name: Travel Rate
Data Type: Currency
Behavior: Calculated
Formula:
if(cr950_total_apparatus_hours > 0,
   cr950_travel_total / cr950_total_apparatus_hours,
   0
)
Save
```

**Calc 4: Outside Services Rate**
```
+ New Column
Display Name: Outside Services Rate
Data Type: Currency
Behavior: Calculated
Formula:
if(cr950_total_apparatus_hours > 0,
   cr950_outside_services_total / cr950_total_apparatus_hours,
   0
)
Save
```

**Calc 5: Effective Labor Rate** ⭐
```
+ New Column
Display Name: Effective Labor Rate
Data Type: Currency
Behavior: Calculated
Formula:
(cr950_onsite_labor_rate + 
 cr950_offsite_labor_rate + 
 cr950_travel_rate + 
 cr950_outside_services_rate) * cr950_scope_multiplier
Save
```

---

## ✅ Validation Test (Defer Until Dependencies Ready)

**Prerequisites:**
- ✅ ScopeLaborDetail table built with all fields
- ⏳ ProjectScope table exists with test data (required for lookup field)
- ⏳ Apparatus table exists with test data (for meaningful revenue calculation testing)

**Validation will be performed after Phase 5C-5D complete**, when all dependencies are in place.

### **Future Validation Test Data (Using Real Excel)**

**When dependencies ready, create test record:**

```
Name: Scope-001-Labor (auto-generated)
Project Scope: [Select existing test scope]

--- Core Config ---
Total Apparatus Hours: 176
Scope Multiplier: 1.00
Notes: Validation test using real Excel Estimator data

--- Cost Category Totals ---
Onsite Labor Total: $45,936.00
Offsite Labor Total: $2,772.00
Travel Total: $5,175.00
Outside Services Total: $10,125.00

--- Metadata ---
Source: ESTIMATOR
```

### **Expected Calculated Results (from Excel)**

```
✓ Onsite Labor Rate: $261.00/hr ($45,936 ÷ 176)
✓ Offsite Labor Rate: $15.75/hr ($2,772 ÷ 176)
✓ Travel Rate: $29.40/hr ($5,175 ÷ 176)
✓ Outside Services Rate: $57.53/hr ($10,125 ÷ 176)
✓ Effective Labor Rate: $363.68/hr ⭐
  Verification: $64,008 (NOT ADJUSTED) ÷ 176 hrs = $363.68/hr ✓
```

### **Integration Test (After ApparatusRevenue Built)**

```
Test Scenario: Apparatus with 45.5 labor hours
Expected Revenue: 45.5 × $363.68 = $16,547.44

This validates the entire calculation chain:
ScopeLaborDetail → ApparatusRevenue → Revenue Amount
```

---

## 📤 Solution Export (5 min)

1. **Solutions > [Your Solution]**
2. **Overview > Version** → Update to `1.3.0.1`
3. **Export > Managed + Unmanaged**
4. Save both to: `C:\RESA_Power_Build\Solutions\v1_3_0_1\`
5. Git commit with message:
   ```
   feat: Built ScopeLaborDetail table v1.3.0.1 - 14 fields + global choice
   
   - Major schema simplification: 55 → 14 fields (75% reduction)
   - Matches Excel Estimator structure: Onsite/Offsite/Travel/Outside Services
   - Dual tracking: Dollar totals (input) + Per-hour rates (calculated)
   - Weighted average model: Totals ÷ Hours × Multiplier = Effective Rate
   - Global choice (cr950_datasource) for consistent audit trail across all tables
   - 5 options: ESTIMATOR, MANUAL, ADJUSTED, API_IMPORT, MIGRATION
   - Foundation for entire revenue calculation chain (apparatus → scope → project)
   - Schema validated, data testing deferred until dependencies ready
   - Ready for ApparatusRevenue integration (Phase 5D)
   ```

---

## 🔗 Next Steps After Build Complete

### **Immediate (Phase 5D - ApparatusRevenue):**
- Add lookup field: `cr950_scopelabordetail_id` (to get Effective Labor Rate)
- Add input fields: `Planned_Labor_Hours`, `Delay_Hours`, `Status` (choice)
- Add calculated fields:
  * `Actual_Labor_Hours` = Planned + Delays
  * `Labor_Rate_Applied` (from ScopeLaborDetail lookup)
  * `Revenue_Amount` = Actual_Hours × Labor_Rate_Applied
- Build Power Automate flow for revenue recognition (on Apparatus complete)
- Time: 45-65 minutes

### **Within 1-2 Weeks (Excel MCP Import):**
- Design hidden Excel sheet "Dataverse_Export" (xlVeryHidden = -2)
  * Columns: Scope_Name, Total_App_Hours, Onsite_Total, Offsite_Total, Travel_Total, Outside_Services_Total, Scope_Multiplier
  * Formulas link to main calculation sheets (auto-updates)
  * Finance can unhide to verify before import
- Build Excel MCP Server with `import_estimator` tool
  * Reads hidden "Dataverse_Export" sheet (simple CSV-like structure)
  * Maps 7 columns → 7 Dataverse fields (direct 1:1)
  * Validates totals match main sheets before import
- Test with actual Estimator file
- Time: 3-4 hours total

### **Future (Rollup Architecture):**
- **ScopeFinancials Table:** Aggregate from ApparatusRevenue
  * Total_Apparatus_Count, Total_Planned_Hours, Total_Actual_Hours, Total_Revenue
  * Compare to ScopeLaborDetail.Estimated_Total_Revenue (variance tracking)
  * Track Onsite/Offsite/Travel/Outside Services revenue separately
- **ProjectFinancials Table:** Aggregate from ScopeFinancials
  * Project_Total_Scopes, Project_Total_Hours, Project_Total_Revenue
  * Project margin analysis (actual vs estimated)
- Design after observing real data patterns (bottom-up approach)

---

## 📋 Field Quick Reference

| # | Field Name | Type | Required | Calculated | Purpose | Excel Source |
|---|------------|------|----------|------------|---------|--------------|
| 1 | Project Scope | Lookup | ✅ | ❌ | Parent relationship | N/A |
| 2 | Total Apparatus Hours | Decimal | ✅ | ❌ | Denominator for all rates | "Total App Hours" cell (176) |
| 3 | Scope Multiplier | Decimal | ✅ | ❌ | Final rate adjustment | "PercentAdjust" cell (1.00 = 100%) |
| 4 | Notes | Text | ❌ | ❌ | Context/justification | N/A |
| 5 | Onsite Labor Total | Currency | ❌ | ❌ | Onsite labor costs | "Onsite Labor Totals" Bill Totals ($45,936) |
| 6 | Onsite Labor Rate | Currency | ❌ | ✅ | Onsite rate component | Calculated: $45,936 ÷ 176 = $261.00/hr |
| 7 | Offsite Labor Total | Currency | ❌ | ❌ | Offsite labor costs | "Offsite Labor Totals" Bill Totals ($2,772) |
| 8 | Offsite Labor Rate | Currency | ❌ | ✅ | Offsite rate component | Calculated: $2,772 ÷ 176 = $15.75/hr |
| 9 | Travel Total | Currency | ❌ | ❌ | Travel costs | "Travel Cost/Rate Groups" Totals ($5,175) |
| 10 | Travel Rate | Currency | ❌ | ✅ | Travel rate component | Calculated: $5,175 ÷ 176 = $29.40/hr |
| 11 | Outside Services Total | Currency | ❌ | ❌ | Outside services costs | "Outside Services" Totals ($10,125) |
| 12 | Outside Services Rate | Currency | ❌ | ✅ | Outside services rate | Calculated: $10,125 ÷ 176 = $57.53/hr |
| 13 | **Effective Labor Rate** ⭐ | Currency | ❌ | ✅ | **Final blended rate** | **$64,008 ÷ 176 = $363.68/hr** |
| 14 | Source | Choice | ✅ | ❌ | Data origin tracking | N/A |

---

## ✨ Key Improvements Over Old Design

| Old Design (55 fields) | New Design (14 fields) | Benefit |
|------------------------|------------------------|---------|
| 55 granular line items | 4 category totals | **75% field reduction** |
| Mixed terminology | Standardized Onsite/Offsite | **Matches Excel exactly** |
| Unclear calculation model | Weighted average (Totals ÷ Hours) | **Crystal clear logic** |
| No per-hour visibility | Dual tracking (Total + Rate) | **Visibility + calculation** |
| Manual effective rate calc | Auto-calculated field | **Single source of truth** |
| Complex import mapping | Hidden Excel sheet (7 columns) | **Simple 1:1 mapping** |
| Additive component model | Weighted average model | **Matches Excel NOT ADJUSTED** |

---

## 🎯 Revenue Architecture Foundation

This table is the **foundation** for the entire revenue calculation chain:

```
ScopeLaborDetail (14 fields) - Defines rate per scope
    ↓ Provides: Effective Labor Rate ($363.68/hr)
    
ApparatusRevenue - Calculates per-apparatus revenue
    ↓ Formula: Apparatus_Hours × Effective_Labor_Rate
    ↓ Example: 45.5 hrs × $363.68 = $16,547.44
    
ScopeFinancials (future) - Aggregates scope totals
    ↓ Rollup: Sum(ApparatusRevenue.Revenue_Amount)
    ↓ Compare: Actual vs Estimated (variance tracking)
    
ProjectFinancials (future) - Aggregates project totals
    ↓ Rollup: Sum(ScopeFinancials.Total_Revenue)
    ↓ Analysis: Project margin, category breakdowns
```

**Key Architectural Benefits:**
- ✅ Single Source of Truth: Rate calculated once, used everywhere
- ✅ Category Visibility: Track Onsite/Offsite/Travel/Outside Services revenue separately
- ✅ Variance Tracking: Compare estimated vs actual at every level
- ✅ Consistent Model: Same calculation pattern (rate × hours) throughout
- ✅ Excel Alignment: Direct mapping from Excel → Dataverse → Apparatus

---

**Ready to build? Estimated time: 20-25 minutes total**
