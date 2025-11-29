# REVENUE ARCHITECTURE SESSION - TECHNICAL DECISIONS CATALOG

**Session Date**: ~November 14, 2025 (estimated from context)  
**Source**: Chat session export - Revenue structure and billing configuration  
**Status**: 🔴 CRITICAL - Documents actual financial architecture implementation

---

## 🎯 SESSION CONTEXT

**Situation**: User (Jason) was completing rollup field implementation and needed to understand Apparatus_Revenue table architecture for revenue recognition automation.

**Key Milestone**: All 21 rollup fields completed! ✅

**Next Phase**: Implementing automated revenue recognition when apparatus marked complete.

---

## 💰 REVENUE RECOGNITION BUSINESS MODEL

### **Core Principle: All-or-Nothing Billing**

**Apparatus = Unit of Revenue Recognition**

- Each apparatus has `Labor_Hours` (quoted per-apparatus hours)
- When apparatus marked **Complete** → Revenue earned = `Labor_Hours × Rate`
- When apparatus **not Complete** → Revenue earned = $0
- **No partial billing** - either bill full Labor_Hours or nothing

### **Example**:
```
Apparatus: SW-1 (Main Switchgear)
Labor_Hours: 8.0 (quoted/billable hours)
Status: In Progress → Revenue: $0
Status: Complete → Revenue: $1,000 (8.0 × $125/hr)
```

---

## 📊 APPARATUS_REVENUE TABLE ARCHITECTURE

### **Purpose**
Track revenue recognition when apparatus is completed. Each record represents billable revenue for one completed apparatus.

### **Existing Fields** (Already in v1.2.0.3)
- ✅ `Revenue_Record_ID` (Primary column)
- ✅ `Apparatus` (Lookup → Apparatus)  
- ✅ `Scope_Labor_Detail` (Lookup → Financial Configuration)
- ✅ `Project` (Lookup → Projects - for reporting)

### **Fields to Add** (Agreed in Session)

#### **Category 1: Hours Tracking**

**1. Labor_Hours** (CRITICAL - What We Bill)
- **Type**: Decimal(2)
- **Required**: Yes
- **Source**: `Apparatus.Labor_Hours` (copied when complete)
- **Purpose**: Per-apparatus billable hours
- **Business Logic**: This is the quoted hours that become billable upon completion
- **Note**: User clarified this should be `Labor_Hours`, NOT `Completed_Hours` - semantically represents the quoted work

**2. Delays**
- **Type**: Decimal(2)
- **Default**: 0
- **Source**: `Apparatus.Delays` (copied when complete)
- **Purpose**: Document unbillable delay hours for change order justification
- **Use Case**: Site access delays, customer-caused delays, etc.

**3. Actual_Hours** (Calculated - Cost Analysis)
- **Type**: Calculated (Decimal)
- **Formula**: `cr950_labor_hours + cr950_delays`
- **Purpose**: Total time spent (billable + unbillable)
- **Use Case**: Profitability analysis, efficiency metrics

#### **Category 2: Financial Rates**

**4. Base_Labor_Rate** or **Labor_Rate**
- **Type**: Currency
- **Required**: Yes
- **Source**: `Scope_Labor_Detail.Base_Labor_Rate`
- **Purpose**: Hourly rate at time of completion (historical record)
- **Note**: Rate could change over project life, so capture it

**5. Scope_Multiplier** (Optional - if applicable)
- **Type**: Decimal(4 decimal places)
- **Default**: 1.0
- **Source**: `Scope_Labor_Detail.Scope_Multiplier`
- **Purpose**: Rate adjustment multiplier (e.g., 1.15 for 15% premium)
- **Use Case**: Scope-specific rate premiums/discounts

#### **Category 3: Calculated Revenue**

**6. Calculated_Revenue** or **Revenue_Amount**
- **Type**: Calculated (Currency)
- **Formula**: `cr950_labor_hours * cr950_labor_rate` (or × multiplier if used)
- **Purpose**: Total billable revenue auto-calculated
- **Display**: Primary revenue metric

#### **Category 4: Tracking Fields** (Optional - Future)

**7. Revenue_Recognized_Date**
- **Type**: DateTime
- **Auto-populate**: NOW() when record created
- **Purpose**: Audit trail for when revenue was recognized

**8. Billing_Status** (Choice)
- **Values**: Recognized, Invoiced, Paid, Disputed
- **Purpose**: Track revenue through billing lifecycle

**9. Invoice_Number**
- **Type**: Text(50)
- **Purpose**: Link to actual invoice when billed

---

## 🏗️ IMPLEMENTATION DECISION

### **Minimal Implementation** (Recommended Start)
**Add 5 core fields**:
1. Labor_Hours (Decimal)
2. Delays (Decimal)  
3. Actual_Hours (Calculated)
4. Labor_Rate (Currency)
5. Revenue_Amount (Calculated)

**Time**: ~10-12 minutes  
**Status**: Ready to implement

### **Comprehensive Implementation** (Later)
Add tracking fields when ready for billing integration:
- Revenue_Recognized_Date
- Billing_Status
- Invoice_Number
- Scope_Multiplier (if needed)

---

## 🔄 REVENUE RECOGNITION WORKFLOW

### **Trigger**: Apparatus.Completion_Status changes to "Complete"

### **Power Automate Flow**:
```
WHEN Apparatus.Completion_Status = "Complete"
THEN CREATE Apparatus_Revenue record:

  # Relationships
  Apparatus: [This Apparatus]
  Project: Apparatus.Project
  Scope_Labor_Detail: Apparatus.Scope → Financial_Config

  # Hours Data
  Labor_Hours: Apparatus.Labor_Hours ← Billable hours
  Delays: Apparatus.Delays ← Cost tracking
  (Actual_Hours: auto-calculates = Labor + Delays)

  # Financial Data
  Labor_Rate: Scope_Labor_Detail.Base_Labor_Rate
  (Revenue_Amount: auto-calculates = Labor × Rate)

  # Tracking
  Revenue_Recognized_Date: utcNow()
  Billing_Status: "Recognized"
```

---

## 📊 EXAMPLE REVENUE RECORD

```
APPARATUS_REVENUE RECORD #00123
================================
Apparatus: SW-1 (Main Switchgear)
Project: LASNAP16
Scope_Labor_Detail: Main Switchgear ATS Rates

Hours:
  Labor_Hours: 8.0 (quoted/billable)
  Delays: 2.5 (documented)
  Actual_Hours: 10.5 (calculated: 8.0 + 2.5)

Financial:
  Labor_Rate: $125.00/hr
  Revenue_Amount: $1,000.00 (8.0 × $125)

Tracking:
  Revenue_Recognized_Date: 2025-11-14 14:30:00
  Billing_Status: Recognized

Analysis:
  Billable Revenue: $1,000.00
  Cost (10.5 hrs @ $85/hr): $892.50
  Gross Profit: $107.50
  Margin: 10.8%
  Efficiency: 76% (8.0 / 10.5)
  Unbillable Delays: 2.5 hrs ($312.50 potential change order)
```

---

## 🔑 CRITICAL SEMANTIC CLARIFICATIONS

### **Issue**: Confusion over "Completed_Hours" vs "Labor_Hours"

**Initial Misunderstanding**: 
- Thought revenue should track `Completed_Hours`
- This created redundancy

**User's Correction**:
> "We're primarily concerned with tracking revenue earned based on apparatus completion hours"  
> "Apparatus_Hours or Labor Hours are per apparatus. Meaning it will be completed and recognized as revenue earned, eligible to bill at completed hours or not at all."

**Final Clarity**:
- **Apparatus.Labor_Hours** = Quoted per-apparatus hours (e.g., 8.0)
- **Apparatus.Completed_Hours** = Calculated field (Labor_Hours IF complete, else 0)
- **Revenue.Labor_Hours** = The billable hours being invoiced (copied from Apparatus.Labor_Hours)

**Why This Matters**:
- `Labor_Hours` is semantically correct for revenue (represents quoted work)
- `Completed_Hours` is just a helper calculation on Apparatus table
- Revenue table stores the actual hours being billed

### **Semantic Tracking**:

**On Apparatus Table**:
- `Labor_Hours` = "How many hours is this apparatus worth?"
- `Completed_Hours` (calc) = "How many of those hours are billable right now?" (0 or Labor_Hours)

**On Revenue Table**:
- `Labor_Hours` = "How many hours are we billing for this completed apparatus?"
- `Revenue_Amount` = "How much money did we earn from this completion?"

---

## 💼 SCOPE LABOR DETAIL (FINANCIAL CONFIGURATION)

### **Updated Structure** (from Excel export)

The session referenced a **Scope Labor Detail** Excel file showing the actual billing configuration structure with **77 total columns** (50 custom + 27 system).

### **Field Categories** (Confirmed in v1.2.0.3)

#### **1. Base Rates (6 fields)**
- Base_Labor_Rate + Base currency
- Scope_Multiplier
- Total_Apparatus_Hours

#### **2. Percentage-Based Rates (18 fields - 9 rates)**
Each has Rate + Base + Percentage:
- Daily_Commute (Pct, Rate, Rate Base)
- Mobilization (Pct, Rate, Rate Base)
- Office_PM (Pct, Rate, Rate Base)
- Office_Report (Pct, Rate, Rate Base)
- Onsite_LOTO (Pct, Rate, Rate Base)
- Onsite_Misc (Pct, Rate, Rate Base)
- Onsite_PM (Pct, Rate, Rate Base)

#### **3. Fixed Costs (24 fields - 12 costs)**
Each has Cost + Base currency:
- Car_Rental_Fixed
- Flights_Fixed
- Generator_Rental_Fixed
- Hotel_PerDiem_Fixed
- Misc_Fixed
- Misc_Travel_Fixed
- Test_Equipment_Fixed
- Travel_Fixed
- XFMR_LAB_Fixed (Transformer lab testing)
- (Additional fixed costs)

#### **4. Calculated Total**
- Scope_Total_Value + Base

**Purpose**: Each scope has a complete financial configuration that defines ALL rates and costs for that scope's work.

---

## 🎯 KEY BUSINESS INSIGHTS

### **1. Revenue Recognition Model**
- **Unit of billing**: Individual apparatus
- **Trigger**: Apparatus completion status
- **Amount**: Labor_Hours × Rate (from scope config)
- **Timing**: Immediate upon completion

### **2. Cost vs. Revenue Tracking**
- **Revenue (billable)**: Labor_Hours × Rate
- **Cost (actual)**: Actual_Hours × Internal_Rate
- **Efficiency**: Labor_Hours / Actual_Hours
- **Change Orders**: Delays tracked for potential billing

### **3. Financial Architecture Separation**
- **Operational Tables**: Projects, Scopes, Tasks, Apparatus (field tech access)
- **Financial Tables**: Scope_Labor_Detail, Apparatus_Revenue (restricted)
- **Security**: Two-tier access control

### **4. Scope-Level Financial Configuration**
- Each scope has unique rate structure (Scope_Labor_Detail record)
- Rates can vary by scope within same project
- Supports complex billing: percentage-based rates + fixed costs
- Rate multipliers for scope-specific premiums

---

## 🔗 RELATIONSHIP ARCHITECTURE

```
Project
  ↓
  └─→ Scope
        ↓
        ├─→ Scope_Labor_Detail (1:1 - Financial Config)
        │     ↓
        │     └─→ [All Rates & Costs]
        │
        └─→ Apparatus (1:N)
              ↓
              └─→ When Complete → Apparatus_Revenue
                    ↓
                    ├─→ Labor_Hours (from Apparatus)
                    ├─→ Labor_Rate (from Scope_Labor_Detail)
                    └─→ Revenue_Amount (calculated)
```

---

## 📋 ROLLUP IMPLICATIONS

### **At Apparatus Level** (Work Tracking)
- Total_Apparatus_Hours: All quoted hours
- Total_Completed_Hours: Billable hours (completed apparatus only)
- Total_Remaining_Hours: Not complete yet

### **At Revenue Level** (Financial Tracking)
- Total_Revenue: `SUM(Apparatus_Revenue.Revenue_Amount)`
- Total_Hours_Billed: `SUM(Apparatus_Revenue.Labor_Hours)`
- Average_Rate: `Total_Revenue / Total_Hours_Billed`

### **Comparison Metrics**
```
Project LASNAP16:
  Apparatus Table (Work):
    Total_Apparatus_Hours: 1,847.50 (all quoted)
    Total_Completed_Hours: 1,356.25 (billable)
    Total_Remaining_Hours: 491.25 (not complete)
  
  Revenue Table (Financial):
    Total_Revenue: $169,531.25 (actual earned)
    Total_Hours_Billed: 1,356.25
    Average_Rate: $125.00/hr
    
  Comparison:
    Completion: 73.4% (1,356.25 / 1,847.50)
    Revenue Recognition: 73.4% (matches completion)
```

---

## ⚠️ IMPLEMENTATION NOTES

### **Session Ended With**:
User indicated rollups are **100% complete** (all 21 fields done).

### **Next Steps Agreed**:
1. Implement Apparatus_Revenue fields (5 minimal fields)
2. Create Power Automate flow for revenue recognition
3. Test with one complete apparatus
4. Verify revenue calculations
5. Add billing integration fields later

### **Time Estimate**: 10-15 minutes for minimal fields + 20-30 minutes for Power Automate flow

---

## 🔄 RECONCILIATION WITH v1.2.0.3

### **Confirmed Matches** ✅
- Apparatus_Revenue table EXISTS in v1.2.0.3
- Has 4 fields (Revenue_Record_ID, Apparatus, Scope_Labor_Detail, Project)
- Scope_Labor_Detail has 48 custom fields (matches session discussion)
- Financial separation architecture confirmed

### **Fields to Add** (From Session)
The session identified 5 additional fields needed:
1. Labor_Hours ← **CRITICAL**
2. Delays
3. Actual_Hours (calculated)
4. Labor_Rate
5. Revenue_Amount (calculated)

### **Status**: Fields NOT YET ADDED to v1.2.0.3
- Session discussed implementation
- User completed rollups first
- Revenue fields likely planned for v1.2.0.4+

---

## 💡 KEY TAKEAWAYS

1. **Revenue recognition is apparatus-centric** - each completion triggers revenue
2. **Labor_Hours is the billing unit** - quoted per-apparatus hours
3. **Scope_Labor_Detail is comprehensive** - 48 fields of rates and costs
4. **All-or-nothing billing model** - no partial apparatus billing
5. **Financial data separation** - security enforced at table level
6. **Rollups completed** - 21 fields done, ready for next phase

---

**END OF SESSION CATALOG**

*This session documents the business logic and technical decisions for the revenue recognition architecture. Implementation status: Planning complete, fields awaiting addition.*
