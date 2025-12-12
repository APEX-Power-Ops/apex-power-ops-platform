# RESA Power Financial Layer Architecture - Complete Analysis

**Date:** November 16, 2025  
**Purpose:** Define financial tracking architecture for Dataverse implementation  
**Source:** Excel VBA analysis + current Dataverse schema  
**Status:** Architecture Decision Document

---

## 🎯 Executive Summary

### **Current State: Excel Financial Architecture**

Your Excel system has **sophisticated financial tracking** via `All_Tasks_Billing`:

```
All_Tasks (Operational)          All_Tasks_Billing (Financial)
├─ Columns A-U                  ├─ Columns A-U (mirrored from All_Tasks)
│  └─ P: Apparatus_Hours        │  └─ P: Apparatus_Hours (base for calculations)
│     (operational data)        └─ Columns V-AT (financial calculations)
                                    ├─ Base Labor ($)
                                    ├─ Variable Costs (Commute, PM, Report, Travel, Final)
                                    ├─ Fixed Costs (Travel, M&E)
                                    └─ Total Billable ($)
```

**Critical Discovery:**
- `All_Tasks_Billing` mirrors operational data (A-U)
- Financial calculations (V-AT) **all derive from Column P (Apparatus_Hours)**
- Rate configuration lives in `Scope_Labor_Rates` sheet
- Everything multiplies: `Hours × Rate × Completion = Revenue`

---

## 📊 **Excel Financial Tables Explained**

### **Table 1: All_Tasks (Operational)**
**Purpose:** Apparatus tracking (field operations)

**Key Fields:**
- Column A: Scope
- Column B: NETA_Standard
- Column P: Apparatus_Hours (quoted hours) ⭐ **BASE FOR ALL REVENUE**
- Column R: Actual_Hours (field entry)
- Column S: STATUS (COMPLETED triggers billing)

**Security:** Field techs can see this

---

### **Table 2: All_Tasks_Billing (Financial)**
**Purpose:** Revenue recognition and billing calculations

**Structure:**
```
Columns A-U: Mirror All_Tasks (linked formulas)
Column V: Scope_Helper (MATCH function to Scope_Labor_Rates)
Columns W-AT: Financial calculations
```

**Financial Calculations (All use Column P):**

**Base Labor (Column AC):**
```excel
=P × W × Z
Where:
  P = Apparatus_Hours (from All_Tasks)
  W = Base_Rate (from Scope_Labor_Rates)
  Z = Completion (binary: 1 if completed, 0 if not)
```

**Variable Costs (Columns AD-AM):**
```excel
Each follows pattern: Hours × Rate × Completion

Commute (AD-AE):
  Hours = P × Commute% (from Scope_Labor_Rates Column E)
  Cost  = Hours × Commute_Rate (Column D) × Completion

PM (AF-AG):
  Hours = P × PM% (Column G)
  Cost  = Hours × PM_Rate (Column F) × Completion

Report (AH-AI):
  Hours = P × Report% (Column I)
  Cost  = Hours × Report_Rate (Column H) × Completion

Travel (AJ-AK):
  Hours = P × Travel% (Column K)
  Cost  = Hours × Travel_Rate (Column J) × Completion

Final Report (AL-AM):
  Hours = P × Final% (Column M)
  Cost  = Hours × Final_Rate (Column L) × Completion
```

**Fixed Costs (Columns AN-AO):**
```excel
Travel Fixed (AN):
  = P × Travel_Per_Hour (from Scope_Labor_Rates Column O) × Completion

M&E Fixed (AO):
  = P × ME_Per_Hour (Column Q) × Completion
```

**Totals:**
```excel
Total Variable Hours (AP) = SUM(AD + AF + AH + AJ + AL)
Total Variable Cost (AQ) = SUM(AE + AG + AI + AK + AM)
Total Fixed Cost (AR) = SUM(AN + AO)
Subtotal (AS) = AC + AQ + AR
Total Billable (AT) = AS × Multiplier (Column Y)
```

**Security:** Finance team only

---

### **Table 3: Scope_Labor_Rates (Financial Configuration)**
**Purpose:** Rate and percentage configuration per scope

**Structure (Columns A-S):**
```
A: Scope Name (links to All_Tasks Column A)
B: Total Apparatus Hours (for planning)
C: Base Labor Rate ($/hr)
D: Commute Rate ($/hr)
E: Commute % (of apparatus hours)
F: PM Rate ($/hr)
G: PM % (of apparatus hours)
H: Daily Report Rate ($/hr)
I: Daily Report % (of apparatus hours)
J: Travel Rate ($/hr)
K: Travel % (of apparatus hours)
L: Final Report Rate ($/hr)
M: Final Report % (of apparatus hours)
N: Travel Sheet Total ($) - fixed cost pool
O: Travel $ per Apparatus Hour
P: M&E Sheet Total ($) - fixed cost pool
Q: M&E $ per Apparatus Hour
R: Scope Multiplier (markup factor, typically 1.0-1.3)
S: Scope Sheet Total (calculated budget)
```

**Example Row:**
```
Scope: "Switchgear Testing"
Base_Rate: $125.00/hr
Commute%: 15% (0.15)
PM%: 10% (0.10)
Multiplier: 1.20 (20% markup)
```

**For 10-hour apparatus completed:**
```
Base Labor: 10 × $125 × 1 = $1,250
Commute: (10 × 0.15) × $85 × 1 = $127.50
PM: (10 × 0.10) × $95 × 1 = $95.00
...
Subtotal: $1,800
Total Billable: $1,800 × 1.20 = $2,160
```

**Security:** Finance team only

---

## 🎯 **Dataverse Architecture Recommendation**

### **Option A: Exact Excel Mirroring** ❌ **NOT RECOMMENDED**

**Why not:**
- Mixing operational and financial in same views
- Complex Excel formulas hard to replicate
- Security boundaries unclear
- Percentage-based calculations inflexible

---

### **Option B: Clean Separation** ✅ **RECOMMENDED**

**Principle:** Operational and Financial are **separate hierarchies**

```
Operational Hierarchy              Financial Hierarchy
(Everyone)                         (Finance/Management)

Project                            ProjectFinancials
  ↓                                  ↓
ProjectScope                       ScopeFinancials
  ↓                                  ↓
Apparatus                          ApparatusRevenue
  ↓                                  ↓
Column P:                          Calculation Fields:
Apparatus_Hours ────────────→      - Labor_Hours (from Apparatus)
(operational)                      - Labor_Rate (from config)
                                   - Revenue_Amount (Hours × Rate)
```

---

## 📋 **Recommended Dataverse Schema**

### **Layer 1: Base Financial Record (Already Exists)**

**Table: `ApparatusRevenue`**
```
Current Fields (v1.2.0.3):
├─ cr950_apparatus (Lookup → Apparatus)
├─ cr950_project (Lookup → Projects)
└─ cr950_scope_labor_detail (Lookup → ScopeLaborDetail)

Add Fields (Phase 5C):
├─ cr950_labor_hours (Decimal) - Copy from Apparatus.Labor_Hours when completed
├─ cr950_delays (Decimal) - Copy from Apparatus.Delays
├─ cr950_actual_hours (Calculated) - Labor_Hours + Delays
├─ cr950_labor_rate (Currency) - From ScopeLaborDetail.Base_Labor_Rate
├─ cr950_revenue_amount (Calculated) - Actual_Hours × Labor_Rate
└─ cr950_completion_status (Choice) - NOT_STARTED, IN_PROGRESS, COMPLETED

Revenue Recognition Trigger:
  When Apparatus.Completion_Status = "COMPLETED":
    → Create ApparatusRevenue record
    → Copy Labor_Hours, Delays
    → Lookup Labor_Rate from ScopeLaborDetail
    → Calculate Revenue_Amount
```

**Maps to Excel:** Base Labor calculation (Column AC in All_Tasks_Billing)

---

### **Layer 2: Scope Financial Rollup (NEW)**

**Table: `ScopeFinancials`**
```
Purpose: Scope-level financial summary and billing tracking

Relationships:
├─ cr950_scope (Lookup → ProjectScope, One-to-One)
└─ cr950_scope_labor_detail (Lookup → ScopeLaborDetail)

Rollup Fields (from ApparatusRevenue):
├─ cr950_total_revenue_recognized (Currency, Rollup SUM)
├─ cr950_total_labor_hours (Decimal, Rollup SUM)
├─ cr950_total_delays (Decimal, Rollup SUM)
├─ cr950_completed_apparatus_count (Integer, Rollup COUNT)
└─ cr950_avg_labor_rate (Currency, Calculated Average)

Estimate/Budget Fields (Manual Entry):
├─ cr950_estimated_revenue (Currency) - From quote
├─ cr950_estimated_hours (Decimal) - From quote
├─ cr950_contract_value (Currency) - Signed contract amount
└─ cr950_budget_notes (Multiline Text)

Billing Tracking (Manual/API Entry):
├─ cr950_amount_billed_to_date (Currency) - What's been invoiced
├─ cr950_last_billing_date (Date)
├─ cr950_billing_period (Text) - "Nov-2025" format
└─ cr950_billing_status (Choice) - NOT_STARTED, PARTIAL, FULLY_BILLED, CLOSED

Cost Tracking (Manual/API Entry from CRM):
├─ cr950_actual_labor_cost (Currency) - From accounting
├─ cr950_actual_expense_cost (Currency) - Travel, M&E, etc.
├─ cr950_total_actual_cost (Calculated) - Labor + Expenses
└─ cr950_cost_entry_date (Date)

Calculated Analytics:
├─ cr950_revenue_variance (Calculated) - Total_Revenue - Estimated_Revenue
├─ cr950_hours_variance (Calculated) - Total_Hours - Estimated_Hours
├─ cr950_profit_amount (Calculated) - Revenue - Cost
├─ cr950_profit_margin_percent (Calculated) - Profit / Revenue
├─ cr950_billing_variance (Calculated) - Billed - Recognized (AR tracking)
└─ cr950_financial_status (Choice) - ON_BUDGET, UNDER_BUDGET, OVER_BUDGET, AT_RISK
```

**Maps to Excel:** Aggregation of All_Tasks_Billing per scope + Scope_Labor_Rates data

---

### **Layer 3: Project Financial Rollup (NEW)**

**Table: `ProjectFinancials`**
```
Purpose: Project-level P&L and management reporting

Relationships:
└─ cr950_project (Lookup → Projects, One-to-One)

Rollup Fields (from ScopeFinancials):
├─ cr950_total_revenue_recognized (Currency, Rollup SUM)
├─ cr950_total_amount_billed (Currency, Rollup SUM)
├─ cr950_total_actual_cost (Currency, Rollup SUM)
├─ cr950_total_labor_hours (Decimal, Rollup SUM)
└─ cr950_scope_count (Integer, Count of scopes)

Project-Level Budget (Manual Entry):
├─ cr950_contract_value (Currency) - Total contract
├─ cr950_estimated_profit_margin (Percent)
└─ cr950_target_completion_date (Date)

Calculated Metrics:
├─ cr950_total_profit (Calculated) - Revenue - Cost
├─ cr950_profit_margin_percent (Calculated) - Profit / Revenue
├─ cr950_revenue_vs_contract (Calculated) - Revenue / Contract
├─ cr950_cost_overrun (Calculated) - Actual_Cost - Budgeted_Cost
└─ cr950_financial_health_score (Calculated) - Composite metric

Status Fields:
├─ cr950_financial_status (Choice) - ON_TRACK, AT_RISK, OVER_BUDGET, PROFITABLE
├─ cr950_billing_readiness (Choice) - READY, NOT_READY, PENDING_REVIEW
└─ cr950_review_required (Yes/No) - Flags for management attention
```

**Maps to Excel:** Project-level aggregation across all scopes

---

### **Layer 4: Monthly Financial Tracking (NEW)**

**Table: `MonthlyFinancialTracking`**
```
Purpose: Period-based financial reporting for monthly billing

Relationships:
├─ cr950_project (Lookup → Projects)
└─ cr950_scope (Lookup → ProjectScope, Optional)

Period Identification:
├─ cr950_month_year (Date, Month precision) - Primary key component
├─ cr950_billing_period (Text) - "Nov-2025" display format
└─ cr950_week_ending (Date) - For weekly rollups

Monthly Metrics (Manual/Flow Entry):
├─ cr950_revenue_recognized_this_month (Currency)
├─ cr950_amount_billed_this_month (Currency)
├─ cr950_labor_cost_this_month (Currency) - From CRM
├─ cr950_expense_cost_this_month (Currency) - From CRM
├─ cr950_hours_worked_this_month (Decimal)
└─ cr950_completion_count_this_month (Integer)

Calculated Metrics:
├─ cr950_total_cost_this_month (Calculated) - Labor + Expenses
├─ cr950_net_profit_this_month (Calculated) - Revenue - Cost
├─ cr950_profit_margin_this_month (Calculated)
└─ cr950_billing_efficiency (Calculated) - Billed / Recognized

Rollup to Date (Calculated):
├─ cr950_cumulative_revenue (Currency)
├─ cr950_cumulative_billed (Currency)
├─ cr950_cumulative_cost (Currency)
└─ cr950_cumulative_profit (Calculated)

Notes:
└─ cr950_notes (Multiline Text) - Month-end commentary
```

**Maps to Excel:** Billing_Period aggregation (Column AB in All_Tasks_Billing)

---

## 🔐 **Security Model**

### **Role-Based Access:**

```
Field Tech Role:
├─ Read/Write: Apparatus (operational data only)
├─ Read: Projects, ProjectScope (context)
└─ NO ACCESS: ApparatusRevenue, ScopeFinancials, ProjectFinancials, MonthlyFinancialTracking

PM Role:
├─ Read/Write: Projects, ProjectScope, Apparatus
├─ Read: ScopeFinancials (their projects only) - Limited fields:
│   └─ Can see: Revenue_Recognized, Hours, Billing_Status
│   └─ Cannot see: Cost, Profit, Margins
└─ NO ACCESS: ProjectFinancials (full P&L), MonthlyFinancialTracking

Finance Team Role:
├─ Read/Write: All Financial tables
├─ Read: All Operational tables
└─ Full visibility: Costs, profits, margins

Regional VP/Admin Role:
└─ Read: Everything (full dashboard visibility)
```

### **Field-Level Security:**

**ScopeFinancials - Two Access Levels:**
```
PM Access (Read-Only):
├─ ✅ Total_Revenue_Recognized
├─ ✅ Total_Labor_Hours
├─ ✅ Billing_Status
├─ ✅ Amount_Billed_To_Date
├─ ❌ Actual_Cost (HIDDEN)
├─ ❌ Profit_Amount (HIDDEN)
└─ ❌ Profit_Margin (HIDDEN)

Finance Access (Read/Write):
└─ ✅ ALL FIELDS
```

---

## 🔄 **Data Flow Architecture**

### **Revenue Recognition Flow:**

```
Field Tech completes apparatus
  ↓
Apparatus.Completion_Status = "COMPLETED"
  ↓
Power Automate Flow Triggers
  ↓
Create ApparatusRevenue record:
  ├─ Copy Apparatus.Labor_Hours → ApparatusRevenue.Labor_Hours
  ├─ Copy Apparatus.Delays → ApparatusRevenue.Delays
  ├─ Lookup ScopeLaborDetail.Base_Labor_Rate → ApparatusRevenue.Labor_Rate
  ├─ Calculate: Labor_Hours + Delays = Actual_Hours
  ├─ Calculate: Actual_Hours × Labor_Rate = Revenue_Amount
  └─ Set Status = "RECOGNIZED"
  ↓
ScopeFinancials Rollup Fields Auto-Update:
  ├─ Total_Revenue_Recognized (SUM of ApparatusRevenue.Revenue_Amount)
  ├─ Total_Labor_Hours (SUM of ApparatusRevenue.Labor_Hours)
  └─ Completed_Apparatus_Count (COUNT)
  ↓
ProjectFinancials Rollup Fields Auto-Update:
  └─ Total_Revenue_Recognized (SUM from ScopeFinancials)
```

### **Billing Flow (Manual/Semi-Automated):**

```
Finance team reviews ScopeFinancials
  ↓
Monthly billing cycle:
  ├─ View: ScopeFinancials where Billing_Status = "READY"
  ├─ Filter: Revenue_Recognized > Amount_Billed_To_Date
  └─ Generate invoice in billing system (outside Dataverse)
  ↓
Update ScopeFinancials:
  ├─ Amount_Billed_To_Date += Invoice_Amount
  ├─ Last_Billing_Date = TODAY()
  ├─ Billing_Period = "Nov-2025"
  └─ If fully billed: Billing_Status = "FULLY_BILLED"
  ↓
Create MonthlyFinancialTracking record:
  ├─ Revenue_Recognized_This_Month (from ScopeFinancials)
  ├─ Amount_Billed_This_Month (manual entry)
  └─ Calculate profit metrics
```

### **Cost Tracking Flow (Manual/API from CRM):**

```
Month-end process:
  ↓
Accounting exports from CRM:
  ├─ Labor cost per project (actual payroll + burden)
  └─ Expense costs (travel, M&E, per diem, etc.)
  ↓
Finance team enters into ScopeFinancials:
  ├─ Actual_Labor_Cost (manual entry or API)
  ├─ Actual_Expense_Cost (manual entry or API)
  └─ Cost_Entry_Date = TODAY()
  ↓
Calculated fields auto-update:
  ├─ Total_Actual_Cost = Labor + Expenses
  ├─ Profit_Amount = Revenue - Cost
  ├─ Profit_Margin = Profit / Revenue
  └─ Financial_Status = IF(Margin < 10%, "AT_RISK", "ON_BUDGET")
  ↓
ProjectFinancials rollups auto-update
```

---

## 📊 **Dashboard Views**

### **PM Dashboard - "My Projects Financial Summary"**

**View: ScopeFinancials (Filtered to PM's projects)**
```
Columns:
├─ Scope Name
├─ Total Revenue Recognized
├─ Total Labor Hours
├─ Billing Status
├─ Amount Billed To Date
├─ Unbilled Revenue (Recognized - Billed)
└─ Last Billing Date

Security: Read-Only, NO cost/profit columns visible
```

---

### **Finance Dashboard - "Billing Pipeline"**

**View: ScopeFinancials (All projects)**
```
Columns:
├─ Scope Name
├─ Total Revenue Recognized
├─ Amount Billed To Date
├─ Unbilled Revenue ⭐
├─ Billing Status
├─ Actual Cost To Date
├─ Profit Amount
├─ Profit Margin %
└─ Financial Status

Filters:
├─ Billing Status = "READY" or "PARTIAL"
├─ Unbilled Revenue > $0
└─ Financial Status = Any

Sort: Unbilled Revenue (Descending)
```

---

### **Executive Dashboard - "Project P&L"**

**View: ProjectFinancials (All projects)**
```
Columns:
├─ Project Name
├─ Contract Value
├─ Total Revenue Recognized
├─ Total Amount Billed
├─ Total Actual Cost
├─ Total Profit
├─ Profit Margin %
├─ Financial Status
└─ Revenue vs Contract %

Security: Regional VP / Admin only
```

---

### **Monthly Billing Report**

**View: MonthlyFinancialTracking (Current month)**
```
Grouped by: Project
Columns:
├─ Project Name
├─ Month/Year
├─ Revenue Recognized This Month
├─ Amount Billed This Month
├─ Cost This Month
├─ Net Profit This Month
├─ Cumulative Revenue
├─ Cumulative Billed
├─ Cumulative Profit
└─ Notes

Export: PDF for management review
```

---

## ⚡ **Implementation Phases**

### **Phase 5C: ApparatusRevenue Base Layer** (CURRENT)
**Time:** 45-65 minutes
```
✅ Add 5 fields to ApparatusRevenue
✅ Build Power Automate flow for revenue recognition
✅ Test with sample apparatus completions
```

**Deliverable:** Revenue recognition automation working

---

### **Phase 5D: Financial Tables Infrastructure** (NEW - PRIORITY)
**Time:** 75-90 minutes
```
1. Create ScopeFinancials table (all fields)
2. Create ProjectFinancials table (all fields)
3. Create MonthlyFinancialTracking table
4. Configure rollup fields (automatic aggregation)
5. Set up security roles (Finance vs PM access)
6. Build PM Dashboard view (read-only financial summary)
7. Build Finance Dashboard view (full billing pipeline)
```

**Deliverable:** Complete financial layer with clean separation

---

### **Phase 5E: Cost Tracking & Billing Workflows** (NEXT)
**Time:** 60-75 minutes
```
1. Build "Monthly Cost Entry" form (Finance team)
2. Create "Billing Readiness" view (filter for unbilled revenue)
3. Build Power Automate flow: "Update Billing Status"
4. Create MonthlyFinancialTracking entry form
5. Build Executive P&L dashboard
6. Test end-to-end: Completion → Revenue → Billing → Cost → Profit
```

**Deliverable:** Complete financial workflows operational

---

## 🎯 **Key Decisions**

### **Decision 1: Mimic Excel vs. Clean Separation**
**✅ DECISION: Clean Separation**

**Rationale:**
- Excel mixes operational/financial for convenience (single file)
- Dataverse has security model - can enforce separation
- Easier to grant/revoke access at table level than field level
- Clearer data model for future enhancements

---

### **Decision 2: Percentage-Based Costs (Excel) vs. Flat Rates**
**✅ DECISION: Flat Base Rate Only (Initially)**

**Rationale:**
- Excel's complexity (Commute%, PM%, Report%, Travel%, Final%) is for:
  * Detailed cost allocation
  * Variable project structures
  * Billing transparency
- Your boss needs: "How much revenue? What's the profit?"
- **Start simple:** Base Labor Rate × Hours = Revenue
- **Future:** Add variable cost fields to ScopeFinancials if needed

---

### **Decision 3: Automatic vs. Manual Cost Entry**
**✅ DECISION: Manual Entry First, API Later**

**Rationale:**
- CRM integration exists but "outside your purview"
- Build fields that accept both manual and API data
- Finance team can enter costs monthly (15 minutes/month)
- **Future:** Connect API when CRM team ready
- Design doesn't change - just data source changes

---

### **Decision 4: Real-Time vs. Period-Based Reporting**
**✅ DECISION: Both**

**Rationale:**
- Real-time: ScopeFinancials / ProjectFinancials (rollups update automatically)
- Period-based: MonthlyFinancialTracking (manual monthly entry)
- Best of both: PMs see current status, Finance sees monthly trends

---

## 📋 **Updated Todo List Integration**

**Current Phase 5C remains:**
```
Phase 5C: Revenue Automation Complete
  - Add 5 calculation fields to ApparatusRevenue
  - Build Power Automate flow for revenue recognition
  - Test automation
  Time: 45-65 min
  PRIORITY: CRITICAL
```

**NEW Phase 5D (insert before Phase 6):**
```
Phase 5D: Financial Layer Infrastructure
  - Create ScopeFinancials table (complete schema)
  - Create ProjectFinancials table (project-level rollups)
  - Create MonthlyFinancialTracking table (period tracking)
  - Configure all rollup fields (automatic aggregation)
  - Set up security roles (Finance vs PM vs Field Tech)
  - Build PM Financial Dashboard (read-only view)
  - Build Finance Billing Pipeline view
  Time: 75-90 min
  PRIORITY: FOUNDATION (enables all future financial features)
```

**Phase 6 UPDATED:**
```
Phase 6: BusinessUnit & Location Rollups
  - Add BusinessUnit rollup fields (total projects, revenue, hours, tech count)
  - Add revenue rollup from ProjectFinancials to BusinessUnit
  - Create Location Manager financial dashboard view
  - Enable multi-location performance tracking
  Time: 45-60 min
```

---

## 🚀 **Next Steps**

1. **Review this architecture** - Confirm understanding and alignment
2. **Decision checkpoint** - Approve clean separation approach
3. **Build Phase 5C** - Complete ApparatusRevenue foundation (45-65 min)
4. **Build Phase 5D** - Create financial tables (75-90 min)
5. **Test workflows** - End-to-end: Complete → Recognize → Bill → Cost → Profit
6. **Iterate** - Refine based on real usage

---

## 📝 **Questions for Clarification**

1. **Variable costs:** Do you need Excel's detailed variable cost tracking (Commute%, PM%, etc.) in Dataverse, or is Base Labor Rate sufficient initially?

2. **Cost tracking frequency:** Monthly entry acceptable, or need more frequent updates?

3. **PM visibility:** Should PMs see ANY financial data, or keep completely locked down to Finance team?

4. **Billing approval workflow:** Does billing require approval before invoice generation, or Finance team discretion?

5. **CRM integration timeline:** When might CRM cost data API be available? (Plan for it now even if not immediate)

---

**END OF ARCHITECTURE ANALYSIS**

*This architecture provides clean operational/financial separation while preserving Excel's sophisticated financial calculation logic in a secure, scalable Dataverse implementation.*
