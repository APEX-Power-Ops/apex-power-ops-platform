# Revenue Architecture - Complete System Design

**Version:** 1.3.0.0  
**Created:** November 16, 2025  
**Status:** Core Architecture - Foundation Complete  

---

## 🎯 Architecture Overview

This document defines the **complete revenue calculation chain** from apparatus-level work through project-level financials.

**Design Philosophy:** 
- Bottom-up calculation (apparatus → scope → project)
- Single source of truth (one rate, one formula pattern)
- Real-time accuracy (calculated fields, no manual updates)
- Category visibility (track Onsite/Offsite/Travel/Outside Services separately)
- Excel alignment (matches Estimator structure exactly)

---

## 🏗️ Four-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 4: PROJECT FINANCIALS (Future - Aggregation)          │
│ Purpose: Executive dashboard, margin analysis               │
│ Data: Sum of all scope revenues, project-level P&L         │
└─────────────────────────────────────────────────────────────┘
                              ↑
                    Rollup from Tier 3
                              ↑
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: SCOPE FINANCIALS (Future - Rollup)                 │
│ Purpose: Scope-level revenue tracking, variance analysis    │
│ Data: Sum of apparatus revenues, compare to estimates       │
└─────────────────────────────────────────────────────────────┘
                              ↑
                    Rollup from Tier 2
                              ↑
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: APPARATUS REVENUE (Next Build - Phase 5D)          │
│ Purpose: Per-apparatus revenue calculation                  │
│ Formula: Apparatus_Hours × Effective_Labor_Rate             │
└─────────────────────────────────────────────────────────────┘
                              ↑
                    Lookup Effective Labor Rate
                              ↑
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: SCOPE LABOR DETAIL (Foundation - Phase 5C) ✓       │
│ Purpose: Define labor rate per scope (SINGLE SOURCE)       │
│ Formula: (Category Totals ÷ Hours) × Multiplier            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Tier 1: ScopeLaborDetail (Foundation)

**Status:** ✅ Schema Complete (14 fields)  
**Version:** 1.3.0.0  
**Purpose:** Define the **single authoritative labor rate** for each project scope

### **Core Calculation Model**

```
Excel Source Data (4 categories):
├─ Onsite Labor Total:        $45,936
├─ Offsite Labor Total:        $2,772
├─ Travel Total:               $5,175
└─ Outside Services Total:    $10,125
    ───────────────────────────────────
    NOT ADJUSTED Total:        $64,008

Denominator:
└─ Total Apparatus Hours:      176 hrs

Per-Hour Rates (calculated in Dataverse):
├─ Onsite Rate:   $45,936 ÷ 176 = $261.00/hr
├─ Offsite Rate:  $2,772 ÷ 176 =  $15.75/hr
├─ Travel Rate:   $5,175 ÷ 176 =  $29.40/hr
└─ Outside Rate:  $10,125 ÷ 176 =  $57.53/hr
    ─────────────────────────────────────
    Sum of Rates:              $363.68/hr

Final Multiplier:
└─ Scope Multiplier:           1.00 (100%)

Effective Labor Rate (SINGLE SOURCE OF TRUTH):
└─ $363.68 × 1.00 = $363.68/hr ⭐
```

### **Excel Verification**

```
Excel "NOT ADJUSTED" row: $64,008
Excel "ADJUSTED" row:     $64,008 × 100% = $64,008
Excel Total Hours:        176

Effective Rate: $64,008 ÷ 176 = $363.68/hr ✓
```

### **Schema (14 Fields)**

| Category | Fields | Type | Purpose |
|----------|--------|------|---------|
| **Core Config** | Project Scope | Lookup | Parent relationship |
| | Total Apparatus Hours | Decimal | Denominator (176) |
| | Scope Multiplier | Decimal | Final adjustment (1.00) |
| | Notes | Text | Context |
| **Onsite Labor** | Onsite Labor Total | Currency | Input from Excel ($45,936) |
| | Onsite Labor Rate | Calculated | $45,936 ÷ 176 = $261.00 |
| **Offsite Labor** | Offsite Labor Total | Currency | Input from Excel ($2,772) |
| | Offsite Labor Rate | Calculated | $2,772 ÷ 176 = $15.75 |
| **Travel** | Travel Total | Currency | Input from Excel ($5,175) |
| | Travel Rate | Calculated | $5,175 ÷ 176 = $29.40 |
| **Outside Services** | Outside Services Total | Currency | Input from Excel ($10,125) |
| | Outside Services Rate | Calculated | $10,125 ÷ 176 = $57.53 |
| **Revenue Calc** | **Effective Labor Rate** ⭐ | Calculated | **Sum of rates × multiplier** |
| **Metadata** | Source | Choice | ESTIMATOR/MANUAL/ADJUSTED |

### **Key Formula**

```javascript
cr950_effective_labor_rate = 
  (cr950_onsite_labor_rate + 
   cr950_offsite_labor_rate + 
   cr950_travel_rate + 
   cr950_outside_services_rate) * cr950_scope_multiplier
```

---

## 📊 Tier 2: ApparatusRevenue (Next Build)

**Status:** 🔨 Ready to Build (Phase 5D)  
**Estimated Time:** 45-65 minutes  
**Purpose:** Calculate revenue for each individual apparatus

### **Core Calculation Model**

```
Lookup from ScopeLaborDetail:
└─ Effective Labor Rate: $363.68/hr

Apparatus-Specific Data:
├─ Planned Labor Hours:  45.5 hrs (from Apparatus table)
├─ Delay Hours:          2.0 hrs (adjustments, issues)
└─ Status:               COMPLETE

Calculated Fields:
├─ Actual Labor Hours:   45.5 + 2.0 = 47.5 hrs
└─ Revenue Amount:       47.5 × $363.68 = $17,274.80 ⭐
```

### **Proposed Schema (8 Fields)**

| Field Name | Type | Purpose | Example |
|------------|------|---------|---------|
| **Apparatus** | Lookup | Parent apparatus | Switchgear-001 |
| **Scope Labor Detail** | Lookup | Get effective rate | Scope-001-Labor |
| **Planned Labor Hours** | Decimal | Initial estimate | 45.5 hrs |
| **Delay Hours** | Decimal | Additional hours | 2.0 hrs |
| **Status** | Choice | Work state | PLANNED/IN_PROGRESS/COMPLETE |
| **Actual Labor Hours** | Calculated | Planned + Delays | 47.5 hrs |
| **Labor Rate Applied** | Calculated | From lookup | $363.68/hr |
| **Revenue Amount** ⭐ | Calculated | Hours × Rate | $17,274.80 |

### **Key Formulas**

```javascript
// Actual Labor Hours
cr950_actual_labor_hours = 
  cr950_planned_labor_hours + cr950_delay_hours

// Labor Rate Applied (from lookup)
cr950_labor_rate_applied = 
  cr950_scopelabordetail_id.cr950_effective_labor_rate

// Revenue Amount (CRITICAL CALCULATION)
cr950_revenue_amount = 
  cr950_actual_labor_hours * cr950_labor_rate_applied
```

### **Power Automate Flow**

**Trigger:** Apparatus.Status changes to "COMPLETE"

**Actions:**
1. Get related ApparatusRevenue record
2. Update Status to "COMPLETE" (triggers calculations)
3. Log revenue recognition event
4. Update parent Scope/Project totals (future)

---

## 📊 Tier 3: ScopeFinancials (Future - Rollup)

**Status:** 📋 Design After ApparatusRevenue Production Data  
**Purpose:** Aggregate all apparatus revenues within a scope, track variance

### **Core Calculation Model**

```
Rollup from ApparatusRevenue:
├─ Total Apparatus Count:     12 apparatus
├─ Total Planned Hours:       450.5 hrs (sum of planned)
├─ Total Actual Hours:        478.2 hrs (sum of actual)
└─ Total Actual Revenue:      $173,924.58 (sum of revenue amounts)

Compare to ScopeLaborDetail Estimate:
├─ Estimated Hours:           450.0 hrs
├─ Estimated Revenue:         $163,656.00 (450 × $363.68)
└─ Variance:                  +$10,268.58 (6.3% over estimate)

Category Breakdown (track separately):
├─ Onsite Labor Revenue:      $124,849.80
├─ Offsite Labor Revenue:     $7,530.15
├─ Travel Revenue:            $14,059.08
└─ Outside Services Revenue:  $27,485.55
```

### **Proposed Schema (Future Design)**

| Category | Fields | Purpose |
|----------|--------|---------|
| **Core** | Project Scope (Lookup) | Parent relationship |
| | Scope Labor Detail (Lookup) | Link to rate config |
| **Apparatus Rollup** | Total Apparatus Count | Count of apparatus |
| | Total Planned Hours | Sum of planned |
| | Total Actual Hours | Sum of actual |
| | Total Actual Revenue | Sum of revenue amounts |
| **Variance Tracking** | Estimated Revenue | From ScopeLaborDetail |
| | Revenue Variance Amount | Actual - Estimated |
| | Revenue Variance Percent | (Variance / Estimated) × 100 |
| **Category Revenue** | Onsite Labor Revenue | Actual × Onsite Rate |
| | Offsite Labor Revenue | Actual × Offsite Rate |
| | Travel Revenue | Actual × Travel Rate |
| | Outside Services Revenue | Actual × Outside Services Rate |

**Note:** Design will be refined after observing real ApparatusRevenue data patterns in production.

---

## 📊 Tier 4: ProjectFinancials (Future - Aggregation)

**Status:** 📋 Design After ScopeFinancials Production Data  
**Purpose:** Executive dashboard, project-level P&L, margin analysis

### **Core Calculation Model**

```
Rollup from ScopeFinancials:
├─ Total Scope Count:          5 scopes
├─ Total Apparatus Count:      67 apparatus
├─ Total Project Hours:        2,845.7 hrs
└─ Total Project Revenue:      $1,034,562.18

Project-Level Analysis:
├─ Average Effective Rate:     $363.52/hr (weighted avg across scopes)
├─ Total Estimated Revenue:    $980,000.00
├─ Revenue Variance:           +$54,562.18 (5.6% over estimate)
└─ Project Margin:             [Calculate with cost data]

Category Breakdown:
├─ Onsite Labor:               $742,558.89 (71.8%)
├─ Offsite Labor:              $44,819.85 (4.3%)
├─ Travel:                     $83,663.50 (8.1%)
└─ Outside Services:           $163,519.94 (15.8%)
```

### **Proposed Schema (Future Design)**

| Category | Fields | Purpose |
|----------|--------|---------|
| **Core** | Project (Lookup) | Parent relationship |
| **Scope Rollup** | Total Scope Count | Count of scopes |
| | Total Apparatus Count | Sum across scopes |
| | Total Project Hours | Sum of actual hours |
| | Total Project Revenue | Sum of scope revenues |
| **Analysis** | Average Effective Rate | Weighted average |
| | Total Estimated Revenue | Sum of estimates |
| | Revenue Variance | Actual - Estimated |
| | Project Margin Percent | (Revenue - Costs) / Revenue |
| **Category Totals** | Onsite Labor Total | Sum across scopes |
| | Offsite Labor Total | Sum across scopes |
| | Travel Total | Sum across scopes |
| | Outside Services Total | Sum across scopes |

**Note:** Will incorporate cost tracking, profit margin calculations, and executive KPIs after revenue chain is proven.

---

## 🔄 Data Flow Architecture

### **Import Flow (Excel → Dataverse)**

```
Excel Estimator File
    ↓
Hidden Sheet "Dataverse_Export"
  ├─ Formula-driven (auto-calculated)
  ├─ 7 columns: Scope_Name, Hours, Onsite_Total, Offsite_Total, Travel_Total, Outside_Services_Total, Multiplier
  └─ xlVeryHidden (-2, Finance can unhide for verification)
    ↓
Excel Import Process
  ├─ Export hidden sheet to CSV
  ├─ Manual import or Power Automate flow
  └─ Validates totals before import
    ↓
ScopeLaborDetail Table
  ├─ 4 Totals (input fields)
  ├─ 1 Hours (input field)
  ├─ 1 Multiplier (input field)
  └─ 5 Rates (calculated automatically)
    ↓
Effective Labor Rate = $363.68/hr ⭐
```

### **Revenue Recognition Flow (Work Complete → Revenue)**

```
Field Tech marks Apparatus as "COMPLETE"
    ↓
Power Automate Flow triggers
    ↓
ApparatusRevenue.Status → "COMPLETE"
    ↓
Calculated fields update:
  ├─ Actual_Labor_Hours = Planned + Delays
  ├─ Labor_Rate_Applied = Lookup from ScopeLaborDetail
  └─ Revenue_Amount = Hours × Rate
    ↓
ScopeFinancials rollup fields update (future)
    ↓
ProjectFinancials aggregation updates (future)
    ↓
Executive Dashboard refreshes (future)
```

### **Variance Tracking Flow**

```
Estimated (ScopeLaborDetail):
└─ 176 hrs × $363.68 = $64,008 estimated revenue

Actual (ApparatusRevenue rollup):
├─ Apparatus 1: 45.5 hrs × $363.68 = $16,547.44
├─ Apparatus 2: 38.2 hrs × $363.68 = $13,892.58
├─ Apparatus 3: 52.7 hrs × $363.68 = $19,165.94
├─ ... (9 more apparatus)
└─ Total: 185.3 hrs × $363.68 = $67,409.90 actual revenue

Variance (ScopeFinancials):
├─ Hour Variance: 185.3 - 176 = +9.3 hrs (5.3% over)
├─ Revenue Variance: $67,409.90 - $64,008 = +$3,401.90 (5.3% over)
└─ Root Cause: 9.3 hrs of delays across 12 apparatus
```

---

## 🎯 Architecture Benefits

### **1. Single Source of Truth**
- ✅ Effective Labor Rate calculated **once** in ScopeLaborDetail
- ✅ All downstream calculations reference this one field
- ✅ No rate duplication, no sync issues

### **2. Real-Time Accuracy**
- ✅ Calculated fields update automatically
- ✅ No manual revenue calculations
- ✅ No end-of-month reconciliation needed

### **3. Category Visibility**
- ✅ Track Onsite/Offsite/Travel/Outside Services separately
- ✅ Analyze cost drivers at every level
- ✅ Identify optimization opportunities

### **4. Variance Tracking**
- ✅ Compare estimated vs actual at apparatus/scope/project levels
- ✅ Identify patterns (delays, scope creep, efficiency gains)
- ✅ Improve future estimates

### **5. Excel Alignment**
- ✅ Matches Excel Estimator structure exactly
- ✅ Finance team recognizes terminology
- ✅ Simple import validation (hidden sheet)

### **6. Scalability**
- ✅ Works for 1 apparatus or 10,000 apparatus
- ✅ Supports multi-scope, multi-project tracking
- ✅ Foundation for future cost tracking, margin analysis

---

## 📅 Implementation Timeline

### **Phase 5C: Foundation (COMPLETE)** ✅
- ScopeLaborDetail table built (14 fields)
- Validated with real Excel data ($363.68/hr)
- Ready for production use

### **Phase 5D: Revenue Calculation (Next - 1 day)**
- Build ApparatusRevenue table (8 fields)
- Add calculated revenue fields
- Build Power Automate flow
- Test with production data
- **Estimated Time:** 45-65 minutes build + testing

### **Phase 5E: Excel Import Automation (1-2 weeks)**
- Design hidden Excel sheet "Dataverse_Export"
- Build import process (CSV or Power Automate flow)
- Test with actual Estimator files
- Deploy to Finance team
- **Estimated Time:** 2-3 hours total

### **Future: Rollup Tables (Observe data patterns first)**
- ScopeFinancials rollup (design after 30 days of ApparatusRevenue data)
- ProjectFinancials aggregation (design after 60 days of production data)
- Executive dashboards, margin analysis, forecasting

---

## 🔗 Related Documentation

- **ScopeLaborDetail Build Spec:** `02_Implementation/SCOPELABORDETAIL_BUILD_SPEC.md`
- **ApparatusRevenue Build Spec:** (To be created in Phase 5D)
- **User Experience Architecture:** `01_Architecture/USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md`
- **Master Build Specification:** (To be updated with revenue architecture)

---

## 📝 Design Decisions & Rationale

### **Why Bottom-Up Architecture?**
- **Accuracy:** Revenue calculated at most granular level (apparatus)
- **Flexibility:** Supports partial scope completion, phased projects
- **Auditability:** Clear trail from apparatus work → scope → project revenue
- **No manual aggregation:** Rollup fields auto-update

### **Why Weighted Average Model?**
- **Matches Excel:** Excel uses Totals ÷ Hours, not additive components
- **Simplicity:** One clear formula, easy to verify
- **Accuracy:** Reflects actual cost structure (fixed costs spread across hours)

### **Why Dual Tracking (Total + Rate)?**
- **Visibility:** Finance sees dollar totals (familiar from Excel)
- **Calculation:** Dataverse calculates per-hour rates automatically
- **Validation:** Can verify rates match Excel before import
- **Flexibility:** Can adjust totals, rates recalculate automatically

### **Why Category Separation?**
- **Analysis:** Identify which cost categories drive variance
- **Optimization:** Target high-cost areas for improvement
- **Reporting:** Executive dashboards need category breakdowns
- **Standardization:** Matches industry-standard cost accounting

---

**Architecture Status:** Foundation Complete, Revenue Calculation Next  
**Last Updated:** November 16, 2025  
**Next Review:** After ApparatusRevenue production deployment
