# ScopeLaborDetail Restructure Plan - From 55 to 20 Fields

**Date:** November 16, 2025  
**Purpose:** Simplify financial configuration from Excel's granular structure to practical Dataverse implementation  
**Priority:** CRITICAL FOUNDATION - Must complete before ApparatusRevenue enhancements  
**Status:** Ready to Execute

---

## 🎯 Executive Summary

### **Current State: 55 Fields (TOO COMPLEX)**

**cr950_ScopeLaborDetail (v1.2.0.3):**
```
6 Base config fields (including Base + Base_Base currency conversions)
18 Percentage-based rate fields (9 types × 2 = Rate + Percentage per type)
24 Fixed cost fields (12 types × 2 = Cost + Cost_Base per type)
1 Lookup field (Scope)
6 System fields

= 55 total fields
```

**Problems:**
- ❌ Mirrors Excel's per-row calculation structure (not needed in Dataverse)
- ❌ Too many rate categories (Daily_Commute, Mobilization, Office_PM, Office_Report, Onsite_LOTO, Onsite_Misc, Onsite_PM, etc.)
- ❌ Too many fixed cost types (Car_Rental, Flights, Generator, Hotel, Misc, Test_Equipment, Travel, XFMR_LAB, etc.)
- ❌ Currency base conversions redundant (Dataverse handles multi-currency)
- ❌ Maintenance nightmare for Finance team
- ❌ Overkill for actual business need

---

### **Target State: 20 Fields (STREAMLINED)**

**NEW cr950_ScopeLaborDetail:**
```
Core Configuration: 6 fields
Variable Cost Categories: 5 fields (combined from 18)
Fixed Cost Pools: 4 fields (combined from 24)
Calculated Fields: 3 fields
Metadata: 2 fields

= 20 total fields (64% reduction!)
```

**Benefits:**
- ✅ Simplifies without losing financial visibility
- ✅ Easy for Finance team to configure
- ✅ Clean import from Estimator Excel (MCP server maps complexity → simplicity)
- ✅ Effective_Labor_Rate calculated in Dataverse (single source of truth)
- ✅ Breakdown available for analysis without overwhelming detail

---

## 📊 **Field Mapping: Old → New**

### **CATEGORY 1: Core Configuration (6 Fields)**

| New Field | Data Type | Source (Excel/Old Fields) | Purpose |
|-----------|-----------|---------------------------|---------|
| `cr950_scope` | Lookup → ProjectScope | Existing `cr950_scope` | Links to scope |
| `cr950_base_labor_rate` | Currency | Existing `cr950_base_labor_rate` | Core labor rate (no _base field needed) |
| `cr950_scope_multiplier` | Decimal (3 precision) | Existing `cr950_scope_multiplier` | Markup factor (1.0 - 2.0 typical) |
| `cr950_total_apparatus_hours` | Decimal (2 precision) | Existing `cr950_total_apparatus_hours` | Planning/budget hours |
| `cr950_scope_total_value` | Currency | Existing `cr950_scope_total_value` | Total budget (calculated or manual) |
| `cr950_notes` | Multiline Text | NEW | Configuration notes |

**Changes:**
- ✅ Keep essential fields
- ❌ Remove `_base` currency conversion fields (Dataverse handles this)
- ✅ Add notes field for context

---

### **CATEGORY 2: Variable Cost Categories (5 Fields - SIMPLIFIED)**

**OLD (18 fields - 9 types):**
```
cr950_daily_commute, cr950_daily_commute_pct, cr950_daily_commute_base
cr950_mobilization, cr950_mobilization_pct, cr950_mobilization_base
cr950_office_pm, cr950_office_pm_pct, cr950_office_pm_base
cr950_office_report, cr950_office_report_pct, cr950_office_report_base
cr950_onsite_loto, cr950_onsite_loto_pct, cr950_onsite_loto_base
cr950_onsite_misc, cr950_onsite_misc_pct, cr950_onsite_misc_base
cr950_onsite_pm, cr950_onsite_pm_pct, cr950_onsite_pm_base
... (2 more types)
```

**NEW (5 fields - 3 combined categories):**

| New Field | Data Type | Combines (Old Fields) | Formula/Source |
|-----------|-----------|----------------------|----------------|
| `cr950_variable_labor_rate` | Currency | Daily_Commute + Office_PM + Onsite_PM | Excel MCP: SUM(rates) |
| `cr950_variable_labor_percent` | Decimal (4 precision) | Daily_Commute_% + Office_PM_% + Onsite_PM_% | Excel MCP: SUM(percentages) |
| `cr950_travel_cost_rate` | Currency | Mobilization + Misc_Travel | Excel MCP: SUM(travel-related rates) |
| `cr950_travel_cost_percent` | Decimal (4 precision) | Mobilization_% + Misc_Travel_% | Excel MCP: SUM(travel percentages) |
| `cr950_other_cost_rate` | Currency | Office_Report + Onsite_LOTO + Onsite_Misc | Excel MCP: SUM(other rates) |

**Rationale:**
- Combine similar cost types into logical categories
- Variable labor = Commute + PM costs (all labor-based variables)
- Travel = Mobilization + travel-related costs
- Other = Reports, LOTO, miscellaneous on-site costs
- Excel MCP does the math during import (combine Excel columns → single Dataverse field)
- Finance sees 3 categories instead of 9 (still granular enough for analysis)

---

### **CATEGORY 3: Fixed Cost Pools (4 Fields - POOLED)**

**OLD (24 fields - 12 types):**
```
cr950_car_rental_fixed, cr950_car_rental_fixed_base
cr950_flights_fixed, cr950_flights_fixed_base
cr950_generator_rental_fixed, cr950_generator_rental_fixed_base
cr950_hotel_perdiem_fixed, cr950_hotel_perdiem_fixed_base
cr950_misc_fixed, cr950_misc_fixed_base
cr950_misc_travel_fixed, cr950_misc_travel_fixed_base
cr950_test_equipment_fixed, cr950_test_equipment_fixed_base
cr950_travel_fixed, cr950_travel_fixed_base
cr950_xfmr_lab_fixed, cr950_xfmr_lab_fixed_base
... (3 more types)
```

**NEW (4 fields - 2 pools):**

| New Field | Data Type | Combines (Old Fields) | Formula/Source |
|-----------|-----------|----------------------|----------------|
| `cr950_travel_fixed_total` | Currency | Flights + Car_Rental + Hotel_PerDiem + Misc_Travel + Travel | Excel MCP: SUM(travel-related fixed) |
| `cr950_equipment_fixed_total` | Currency | Test_Equipment + Generator_Rental + XFMR_LAB + Misc | Excel MCP: SUM(equipment/misc fixed) |
| `cr950_fixed_cost_per_hour` | Currency (Calculated) | (Travel_Fixed + Equipment_Fixed) ÷ Total_Apparatus_Hours | Dataverse formula |
| `cr950_total_fixed_cost` | Currency (Calculated) | Travel_Fixed + Equipment_Fixed | Dataverse formula |

**Rationale:**
- Fixed costs don't need per-type tracking in Dataverse (pool them)
- Two pools: Travel-related vs. Equipment-related
- Excel MCP sums Excel columns into pool totals
- Dataverse calculates per-hour allocation (for apparatus revenue)
- Finance can drill into Excel Estimator if need per-type detail

---

### **CATEGORY 4: Calculated Fields (3 Fields - AUTO)**

| New Field | Data Type | Formula | Purpose |
|-----------|-----------|---------|---------|
| `cr950_effective_labor_rate` | Currency (Calculated) | `((Base_Labor_Rate + Variable_Labor_Rate + Travel_Cost_Rate + Other_Cost_Rate) × Scope_Multiplier) + Fixed_Cost_Per_Hour` | All-in rate per hour |
| `cr950_subtotal_before_multiplier` | Currency (Calculated) | `Base_Labor_Rate + Variable_Labor_Rate + Travel_Cost_Rate + Other_Cost_Rate + Fixed_Cost_Per_Hour` | Pre-markup subtotal |
| `cr950_estimated_total_revenue` | Currency (Calculated) | `Effective_Labor_Rate × Total_Apparatus_Hours` | Scope budget |

**Effective Rate Calculation Example:**
```
Base_Labor_Rate: $125.00/hr
Variable_Labor_Rate: $45.00/hr (Commute + PM combined)
Travel_Cost_Rate: $25.00/hr
Other_Cost_Rate: $15.00/hr
Subtotal: $210.00/hr

Travel_Fixed_Total: $2,500
Equipment_Fixed_Total: $1,800
Total_Fixed: $4,300
Total_Apparatus_Hours: 100
Fixed_Cost_Per_Hour: $43.00/hr

Subtotal + Fixed: $210 + $43 = $253.00/hr
Scope_Multiplier: 1.20 (20% markup)

Effective_Labor_Rate: $253.00 × 1.20 = $303.60/hr
Estimated_Total_Revenue: $303.60 × 100 = $30,360
```

**Rationale:**
- Dataverse calculates effective rate (single source of truth)
- No manual calculation errors
- Updates automatically if config changes
- ApparatusRevenue simply looks up this calculated rate

---

### **CATEGORY 5: Metadata (2 Fields)**

| New Field | Data Type | Purpose |
|-----------|-----------|---------|
| `cr950_source` | Choice (ESTIMATOR, MANUAL, ADJUSTED) | How config was created |
| `cr950_last_updated` | DateTime | When last modified (auto) |

**Rationale:**
- Track data lineage (imported from Excel vs manual entry)
- Audit trail for rate changes

---

## 🗑️ **Fields to DELETE (35 Fields)**

### **Delete: Currency Base Fields (15 fields)**
```
cr950_base_labor_rate_base
cr950_daily_commute_base
cr950_mobilization_base
cr950_office_pm_base
cr950_office_report_base
cr950_onsite_loto_base
cr950_onsite_misc_base
cr950_onsite_pm_base
... (7 more _base fields)
```
**Reason:** Dataverse multi-currency handles conversion automatically

---

### **Delete: Granular Rate Fields (12 fields - consolidate to 5)**
```
cr950_daily_commute → part of cr950_variable_labor_rate
cr950_daily_commute_pct → part of cr950_variable_labor_percent
cr950_mobilization → part of cr950_travel_cost_rate
cr950_mobilization_pct → part of cr950_travel_cost_percent
cr950_office_pm → part of cr950_variable_labor_rate
cr950_office_pm_pct → part of cr950_variable_labor_percent
cr950_office_report → part of cr950_other_cost_rate
cr950_onsite_loto → part of cr950_other_cost_rate
cr950_onsite_misc → part of cr950_other_cost_rate
cr950_onsite_pm → part of cr950_variable_labor_rate
... (2 more + percentages)
```
**Reason:** Combined into 3 categories (Variable Labor, Travel, Other)

---

### **Delete: Granular Fixed Cost Fields (18 fields - consolidate to 2 pools)**
```
cr950_car_rental_fixed → part of cr950_travel_fixed_total
cr950_flights_fixed → part of cr950_travel_fixed_total
cr950_generator_rental_fixed → part of cr950_equipment_fixed_total
cr950_hotel_perdiem_fixed → part of cr950_travel_fixed_total
cr950_misc_fixed → part of cr950_equipment_fixed_total
cr950_misc_travel_fixed → part of cr950_travel_fixed_total
cr950_test_equipment_fixed → part of cr950_equipment_fixed_total
cr950_travel_fixed → part of cr950_travel_fixed_total
cr950_xfmr_lab_fixed → part of cr950_equipment_fixed_total
... (9 more including _base fields)
```
**Reason:** Pooled into Travel vs. Equipment categories

---

## 📋 **Complete New Schema Definition**

### **cr950_ScopeLaborDetail (NEW - 20 Fields)**

```
TABLE: cr950_ScopeLaborDetail
Display Name: Scope Labor Detail
Primary Name Field: cr950_name (auto: Scope name + " - Labor Config")

FIELDS:

1. cr950_scopelabordetailid (Primary Key - GUID, System)
   - Unique identifier

2. cr950_name (Primary Name - Text, Auto-generated, System)
   - Display name for record

3. cr950_scope (Lookup → cr950_ProjectScope, Required)
   - Relationship: One-to-One
   - Links financial config to scope

--- CORE CONFIGURATION (4 fields) ---

4. cr950_base_labor_rate (Currency, Required)
   - Base labor rate per hour
   - Precision: 2 decimal places
   - Range: 0 - 1,000,000

5. cr950_scope_multiplier (Decimal, Required)
   - Markup/margin factor
   - Precision: 3 decimal places
   - Range: 0.5 - 5.0
   - Default: 1.0

6. cr950_total_apparatus_hours (Decimal, Optional)
   - Planning/budget hours for scope
   - Precision: 2 decimal places
   - Range: 0 - 100,000

7. cr950_scope_total_value (Currency, Optional)
   - Total estimated scope value
   - Precision: 2 decimal places
   - Can be calculated or manual override

--- VARIABLE COSTS (5 fields) ---

8. cr950_variable_labor_rate (Currency, Optional)
   - Combined: Commute + PM costs
   - Precision: 2 decimal places
   - Default: 0

9. cr950_variable_labor_percent (Decimal, Optional)
   - % of base hours for variable labor
   - Precision: 4 decimal places
   - Range: 0 - 2.0 (0% - 200%)
   - Default: 0

10. cr950_travel_cost_rate (Currency, Optional)
    - Combined: Mobilization + travel costs
    - Precision: 2 decimal places
    - Default: 0

11. cr950_travel_cost_percent (Decimal, Optional)
    - % of base hours for travel
    - Precision: 4 decimal places
    - Range: 0 - 2.0
    - Default: 0

12. cr950_other_cost_rate (Currency, Optional)
    - Combined: Reports + LOTO + misc
    - Precision: 2 decimal places
    - Default: 0

--- FIXED COSTS (4 fields) ---

13. cr950_travel_fixed_total (Currency, Optional)
    - Pool: Flights + hotel + car + travel expenses
    - Precision: 2 decimal places
    - Default: 0

14. cr950_equipment_fixed_total (Currency, Optional)
    - Pool: Test equip + generators + lab + misc
    - Precision: 2 decimal places
    - Default: 0

15. cr950_fixed_cost_per_hour (Currency, Calculated)
    - Formula: (Travel_Fixed + Equipment_Fixed) ÷ Total_Apparatus_Hours
    - Handles divide-by-zero: IF(Total_Hours > 0, calculation, 0)

16. cr950_total_fixed_cost (Currency, Calculated)
    - Formula: Travel_Fixed + Equipment_Fixed

--- CALCULATED RATES (3 fields) ---

17. cr950_subtotal_before_multiplier (Currency, Calculated)
    - Formula: Base_Labor + Variable_Labor + Travel_Cost + Other_Cost + Fixed_Per_Hour

18. cr950_effective_labor_rate (Currency, Calculated)
    - Formula: Subtotal_Before_Multiplier × Scope_Multiplier
    - This is the ALL-IN rate used by ApparatusRevenue

19. cr950_estimated_total_revenue (Currency, Calculated)
    - Formula: Effective_Labor_Rate × Total_Apparatus_Hours

--- METADATA (2 fields) ---

20. cr950_source (Choice, Optional)
    - Options: ESTIMATOR, MANUAL, ADJUSTED
    - Default: MANUAL

21. cr950_last_updated (DateTime, Auto)
    - System field: Modified On
    - Tracks last change
```

---

## 🔄 **Excel MCP Mapping Logic**

### **How Excel MCP Converts 55 → 20 Fields**

```python
def extract_scope_labor_detail(excel_file, scope_name):
    """
    Read Estimator Scope_Labor_Rates sheet
    Combine granular fields into simplified categories
    """
    rates_sheet = excel_file["Scope_Labor_Rates"]
    scope_row = find_scope_row(rates_sheet, scope_name)
    
    # CORE CONFIG - Direct mapping
    base_labor_rate = rates_sheet["C" + scope_row]
    scope_multiplier = rates_sheet["R" + scope_row]
    total_apparatus_hours = rates_sheet["B" + scope_row]
    scope_total_value = rates_sheet["S" + scope_row]
    
    # VARIABLE COSTS - Combine categories
    # Combine: Daily Commute + Office PM + Onsite PM
    variable_labor_rate = (
        rates_sheet["D" + scope_row] +  # Daily Commute rate
        rates_sheet["F" + scope_row] +  # Office PM rate
        rates_sheet["?" + scope_row]    # Onsite PM rate (column TBD)
    )
    
    variable_labor_percent = (
        rates_sheet["E" + scope_row] +  # Daily Commute %
        rates_sheet["G" + scope_row] +  # Office PM %
        rates_sheet["?" + scope_row]    # Onsite PM % (column TBD)
    )
    
    # Combine: Mobilization + Misc Travel
    travel_cost_rate = (
        rates_sheet["?" + scope_row] +  # Mobilization rate (column TBD)
        rates_sheet["?" + scope_row]    # Misc Travel rate (column TBD)
    )
    
    travel_cost_percent = (
        rates_sheet["?" + scope_row] +  # Mobilization % (column TBD)
        rates_sheet["?" + scope_row]    # Misc Travel % (column TBD)
    )
    
    # Combine: Office Report + Onsite LOTO + Onsite Misc
    other_cost_rate = (
        rates_sheet["H" + scope_row] +  # Office Report rate
        rates_sheet["?" + scope_row] +  # Onsite LOTO rate (column TBD)
        rates_sheet["?" + scope_row]    # Onsite Misc rate (column TBD)
    )
    
    # FIXED COSTS - Pool into 2 categories
    # Pool: All travel-related fixed costs
    travel_fixed_total = rates_sheet["N" + scope_row]  # Travel sheet total
    # Note: May need to sum multiple Excel columns if broken down
    
    # Pool: All equipment-related fixed costs
    equipment_fixed_total = rates_sheet["P" + scope_row]  # M&E sheet total
    # Note: May need to sum multiple Excel columns if broken down
    
    # CALCULATED - Excel MCP can pre-calculate or let Dataverse do it
    fixed_cost_per_hour = (travel_fixed_total + equipment_fixed_total) / total_apparatus_hours
    
    effective_labor_rate = (
        (base_labor_rate + variable_labor_rate + travel_cost_rate + other_cost_rate)
        * scope_multiplier
    ) + fixed_cost_per_hour
    
    return {
        "scope": scope_name,
        "base_labor_rate": base_labor_rate,
        "scope_multiplier": scope_multiplier,
        "total_apparatus_hours": total_apparatus_hours,
        "scope_total_value": scope_total_value,
        "variable_labor_rate": variable_labor_rate,
        "variable_labor_percent": variable_labor_percent,
        "travel_cost_rate": travel_cost_rate,
        "travel_cost_percent": travel_cost_percent,
        "other_cost_rate": other_cost_rate,
        "travel_fixed_total": travel_fixed_total,
        "equipment_fixed_total": equipment_fixed_total,
        "source": "ESTIMATOR"
    }
```

**Key Point:** Excel MCP does the complexity reduction during import. Dataverse stores simple, usable data.

---

## 🛠️ **Implementation Steps**

### **Phase 5C.1: ScopeLaborDetail Restructure (45-60 minutes)**

**Step 1: Backup Current Data (5 min)**
```powershell
# Export existing ScopeLaborDetail records (if any)
# Use Power Platform CLI or manual export
pac data export --entity cr950_scopelabordetail --output backup_scopelabordetail.csv
```

**Step 2: Delete Old Fields (15 min)**
- Go to Dataverse solution
- Navigate to cr950_ScopeLaborDetail table
- Delete 35 deprecated fields (all _base fields, granular rate fields, granular fixed cost fields)
- **WARNING:** This is destructive - ensure backup exists

**Step 3: Add New Fields (20 min)**
Create 14 new fields in order:

Core Config (4 fields):
- cr950_base_labor_rate (Currency)
- cr950_scope_multiplier (Decimal, 3 precision)
- cr950_total_apparatus_hours (Decimal, 2 precision)
- cr950_scope_total_value (Currency)

Variable Costs (5 fields):
- cr950_variable_labor_rate (Currency)
- cr950_variable_labor_percent (Decimal, 4 precision)
- cr950_travel_cost_rate (Currency)
- cr950_travel_cost_percent (Decimal, 4 precision)
- cr950_other_cost_rate (Currency)

Fixed Costs (2 manual + 2 calculated):
- cr950_travel_fixed_total (Currency)
- cr950_equipment_fixed_total (Currency)
- cr950_fixed_cost_per_hour (Currency, Calculated)
- cr950_total_fixed_cost (Currency, Calculated)

Metadata (1 field):
- cr950_source (Choice: ESTIMATOR, MANUAL, ADJUSTED)

**Step 4: Create Calculated Fields (10 min)**

**Field: cr950_fixed_cost_per_hour**
```
Formula:
IF(cr950_total_apparatus_hours > 0,
   (cr950_travel_fixed_total + cr950_equipment_fixed_total) / cr950_total_apparatus_hours,
   0
)
```

**Field: cr950_total_fixed_cost**
```
Formula:
cr950_travel_fixed_total + cr950_equipment_fixed_total
```

**Field: cr950_subtotal_before_multiplier**
```
Formula:
cr950_base_labor_rate + 
cr950_variable_labor_rate + 
cr950_travel_cost_rate + 
cr950_other_cost_rate + 
cr950_fixed_cost_per_hour
```

**Field: cr950_effective_labor_rate**
```
Formula:
cr950_subtotal_before_multiplier * cr950_scope_multiplier
```

**Field: cr950_estimated_total_revenue**
```
Formula:
cr950_effective_labor_rate * cr950_total_apparatus_hours
```

**Step 5: Test Manual Entry (10 min)**
- Create test ScopeLaborDetail record
- Enter sample rates:
  - Base: $125
  - Variable: $45
  - Travel: $25
  - Other: $15
  - Multiplier: 1.20
  - Travel Fixed: $2,500
  - Equipment Fixed: $1,800
  - Total Hours: 100
- Verify calculated fields:
  - Fixed Per Hour: $43
  - Subtotal: $253
  - Effective Rate: $303.60
  - Total Revenue: $30,360

**Step 6: Update Solution Version (5 min)**
- Increment version to v1.2.0.4
- Export solution (unmanaged for dev, managed for backup)
- Commit to GitHub

---

## ✅ **Success Criteria**

### **Phase 5C.1 Complete When:**
- ✅ Old 35 fields deleted
- ✅ New 20 fields created
- ✅ All 5 calculated fields working correctly
- ✅ Test record validates:
  - Manual entry works
  - Calculations are accurate
  - Formulas handle edge cases (divide by zero)
- ✅ Solution exported and committed to Git
- ✅ Documentation updated

---

## 📊 **Impact Analysis**

### **Benefits:**
- ✅ **64% field reduction** (55 → 20)
- ✅ **Simplified Finance team workflow** (easier configuration)
- ✅ **Clean Excel MCP import** (complexity handled in code, not schema)
- ✅ **Effective rate calculated in Dataverse** (single source of truth)
- ✅ **Easier maintenance** (fewer fields to manage)
- ✅ **Better performance** (fewer fields, faster queries)

### **Trade-offs:**
- ⚠️ **Less granularity** in Dataverse (9 rate types → 3 categories)
- ⚠️ **Less granularity** in fixed costs (12 types → 2 pools)
- ✅ **Mitigation:** Excel Estimator retains full detail, can drill down if needed
- ✅ **Mitigation:** 3 categories still provide meaningful cost analysis

### **No Breaking Changes:**
- ✅ ApparatusRevenue relationship unchanged (still looks up ScopeLaborDetail)
- ✅ Effective rate calculation works same way (just simpler inputs)
- ✅ Power Automate flows unaffected (use new field names)

---

## 🎯 **Next Steps After Phase 5C.1**

1. **Phase 5C:** Build ApparatusRevenue with lookup to new ScopeLaborDetail.Effective_Labor_Rate
2. **Phase 5C.2:** Build Excel MCP with mapping logic (55 Excel columns → 20 Dataverse fields)
3. **Phase 5D:** Build rollup tables (ScopeFinancials, ProjectFinancials) - structure will define itself naturally

---

**END OF RESTRUCTURE PLAN**

*This simplification maintains financial accuracy while dramatically improving usability and maintainability.*
