# REVENUE ARCHITECTURE - QUICK REFERENCE

**Last Updated**: November 15, 2025  
**Source**: Revenue Architecture Session Catalog  
**Status**: ✅ BUSINESS LOGIC DOCUMENTED | ⏳ FIELDS PENDING ADDITION

---

## 🎯 ONE-SENTENCE SUMMARY

Revenue is recognized on an **all-or-nothing basis per apparatus completion** - when an apparatus is marked complete, create a revenue record billing the full Labor_Hours at the configured rate from the scope's financial configuration.

---

## 💰 BUSINESS MODEL

### **Unit of Billing**: Individual Apparatus
- Each apparatus has quoted `Labor_Hours` (e.g., 8.0 hours)
- Complete = Bill full hours | Not Complete = $0
- **No partial billing**

### **Revenue Formula**
```
Revenue = Labor_Hours × Labor_Rate
```

### **Example**
```
Apparatus: SW-1 (Main Switchgear)
Labor_Hours: 8.0 (quoted)
Labor_Rate: $125/hr (from Scope_Labor_Detail)
Status: Complete → Revenue: $1,000
Status: In Progress → Revenue: $0
```

---

## 📊 THREE TABLES IN PLAY

### **1. Apparatus Table** (Operational)
**Fields Used**:
- `Labor_Hours` - Quoted per-apparatus hours (what we bill)
- `Delays` - Unbillable hours (cost tracking)
- `Completion_Status` - Trigger for revenue recognition

**Access**: Field technicians, project managers

---

### **2. ScopeLaborDetail Table** (Financial Configuration)
**Purpose**: Complete rate and cost configuration per scope (1:1 with ProjectScope)

**Structure (48 Custom Fields)**:
- **Base Rates** (6 fields): Base_Labor_Rate, Scope_Multiplier, Total_Apparatus_Hours
- **Percentage Rates** (18 fields): Daily_Commute, Mobilization, Office_PM, Office_Report, Onsite_LOTO, Onsite_Misc, Onsite_PM, etc.
- **Fixed Costs** (24 fields): Car_Rental, Flights, Generator_Rental, Hotel_PerDiem, Test_Equipment, Travel, XFMR_LAB, Misc, etc.

**Key Field**: `Base_Labor_Rate` - Used for apparatus revenue calculation

**Access**: Finance roles only (field-level security)

---

### **3. ApparatusRevenue Table** (Revenue Recognition)
**Purpose**: Create record when apparatus completed = revenue earned

**Current Fields (v1.2.0.3)** ✅:
- `Revenue_Record_ID` - Primary key
- `Apparatus` - Lookup to Apparatus
- `Scope_Labor_Detail` - Lookup to financial config
- `Project` - Lookup for reporting

**Planned Fields (v1.2.0.4+)** ⏳:
- `Labor_Hours` (Decimal) - Billable hours from apparatus
- `Delays` (Decimal) - Unbillable hours from apparatus
- `Actual_Hours` (Calculated) - Labor + Delays
- `Labor_Rate` (Currency) - Rate from Scope_Labor_Detail
- `Revenue_Amount` (Calculated) - Labor_Hours × Labor_Rate

**Access**: Finance roles only

---

## 🔄 REVENUE RECOGNITION WORKFLOW

### **Trigger**: Apparatus.Completion_Status changes to "Complete"

### **Power Automate Flow** (To Be Built):
```
1. When: Apparatus.Completion_Status = "Complete"

2. Create: Apparatus_Revenue record with:
   
   Relationships:
   - Apparatus: [This Apparatus]
   - Project: Apparatus.Project
   - Scope_Labor_Detail: Apparatus.Scope → Financial_Config
   
   Hours:
   - Labor_Hours: Copy from Apparatus.Labor_Hours
   - Delays: Copy from Apparatus.Delays
   - (Actual_Hours: Auto-calculates)
   
   Financial:
   - Labor_Rate: Get from Scope_Labor_Detail.Base_Labor_Rate
   - (Revenue_Amount: Auto-calculates = Labor × Rate)
   
   Tracking:
   - Revenue_Recognized_Date: utcNow()
   - Billing_Status: "Recognized"

3. Result: Revenue record created = $X earned
```

---

## 📈 REPORTING METRICS

### **At Apparatus Level** (Work Tracking)
- Total_Apparatus_Hours: All quoted hours
- Total_Completed_Hours: Hours from completed apparatus (billable)
- Total_Remaining_Hours: Hours from incomplete apparatus

### **At Revenue Level** (Financial Tracking)
- Total_Revenue: SUM(Revenue_Amount)
- Total_Hours_Billed: SUM(Labor_Hours)
- Average_Rate: Total_Revenue / Total_Hours_Billed

### **Profitability Analysis**
```
For each Revenue Record:
  Billable: Labor_Hours × Labor_Rate
  Cost: Actual_Hours × Internal_Rate
  Profit: Billable - Cost
  Margin: Profit / Billable
  Efficiency: Labor_Hours / Actual_Hours
  
Change Order Opportunity:
  Delays × Labor_Rate = Potential recovery
```

---

## 🔑 CRITICAL SEMANTIC CLARIFICATION

### **Labor_Hours vs. Completed_Hours**

**On Apparatus Table**:
- `Labor_Hours` = "How many hours is this apparatus worth?" (quoted, e.g., 8.0)
- `Completed_Hours` (calculated) = "Are these hours billable right now?" (0 if incomplete, Labor_Hours if complete)

**On Revenue Table**:
- `Labor_Hours` = "How many hours are we billing for this completion?" (copy from Apparatus.Labor_Hours)
- `Revenue_Amount` = "How much money did we earn?" (Labor_Hours × Rate)

**Why This Matters**:
- Use `Labor_Hours` for revenue (semantically represents quoted work being billed)
- `Completed_Hours` is just a helper calculation on Apparatus table
- Revenue table stores the actual billable hours and dollar amount

---

## ⚡ IMPLEMENTATION STATUS

### **Current State (v1.2.0.3)**:
✅ Apparatus table has Labor_Hours and Delays  
✅ ScopeLaborDetail has 48 financial fields including Base_Labor_Rate  
✅ ApparatusRevenue table exists with 4 relationship fields  
✅ 21 rollup fields completed across Tasks/Scopes/Projects  
⏳ ApparatusRevenue missing 5 calculation fields  
⏳ Power Automate flow not yet built  

### **Next Version (v1.2.0.4 Planned)**:
- Add 5 fields to ApparatusRevenue (Labor_Hours, Delays, Actual_Hours, Labor_Rate, Revenue_Amount)
- Build Power Automate flow for automatic revenue recognition
- Test with sample completions
- Verify calculations

**Time Estimate**: 30-40 minutes
- 10-15 min: Add 5 fields to ApparatusRevenue
- 20-30 min: Build and test Power Automate flow

---

## 📚 RELATED DOCUMENTATION

**Detailed Technical Spec**: `Documentation/03_Progress_Tracking/REVENUE_ARCHITECTURE_SESSION.md`  
**Schema Analysis**: `Documentation/05_Reviews_Analysis/V1_2_0_3_ACTUAL_SCHEMA.md`  
**Reconciliation Status**: `Documentation/05_Reviews_Analysis/V1_2_0_3_SCHEMA_RECONCILIATION.md`

---

## 🎯 KEY TAKEAWAYS

1. **Revenue = apparatus completion**, not time-based or task-based
2. **All-or-nothing billing** - bill full Labor_Hours or $0
3. **ScopeLaborDetail is comprehensive** - 48 fields of complete financial config
4. **ApparatusRevenue is automated** - Power Automate creates record on completion
5. **Two-tier security** - operational tables (field access) vs. financial tables (finance only)
6. **Rollups complete** - 21 rollup fields provide hours tracking at all levels
7. **Ready to implement** - Business logic clear, just need 5 fields + flow

---

**QUICK REFERENCE END**

*For complete technical details, see REVENUE_ARCHITECTURE_SESSION.md*
