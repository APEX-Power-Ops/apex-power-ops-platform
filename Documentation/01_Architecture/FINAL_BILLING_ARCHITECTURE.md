# SCOPE LABOR DETAIL & APPARATUS REVENUE - FINAL ARCHITECTURE
## Based on Actual Dataverse Field Names

**Date:** November 14, 2025  
**Source:** cr950_ScopeLaborDetail export template

---

## ✅ SCOPE_LABOR_DETAIL (cr950_scopelabordetail) TABLE

### **STATUS: ALREADY EXISTS WITH CORRECT FIELDS!**

Your Scope Labor Detail table already has the complete financial configuration structure. Here's what you have:

---

### **EXISTING FIELDS (From Your Export):**

#### **Core Fields:**
- ✅ Detail Name (Primary column)
- ✅ Project (Lookup)
- ✅ Scope (Lookup)
- ✅ Status

#### **Base Rate:**
- ✅ Base_Labor_Rate (Currency)

#### **Time Adders (7 pairs = 14 fields):**
- ✅ Daily_Commute_Pct / Daily_Commute_Rate
- ✅ Mobilization_Pct / Mobilization_Rate
- ✅ Office_PM_Pct / Office_PM_Rate
- ✅ Office_Report_Pct / Office_Report_Rate
- ✅ Onsite_LOTO_Pct / Onsite_LOTO_Rate
- ✅ Onsite_Misc_Pct / Onsite_Misc_Rate
- ✅ Onsite_PM_Pct / Onsite_PM_Rate

#### **Fixed Costs (9 fields):**
- ✅ Car_Rental_Fixed
- ✅ Flights_Fixed
- ✅ Generator_Rental_Fixed
- ✅ Hotel_PerDiem_Fixed
- ✅ Misc_Fixed
- ✅ Misc_Travel_Fixed
- ✅ Test_Equipment_Fixed
- ✅ Travel_Fixed
- ✅ XFMR_LAB_Fixed

#### **Calculated Fields:**
- ✅ Scope_Multiplier (Decimal)
- ✅ Scope_Total_Value (Currency)
- ✅ Total_Apparatus_Hours (Rollup or Calculated)

---

## 🎯 WHAT THIS MEANS

**You already have the complete Scope Labor Detail structure!** ✅

The only thing you need to verify:
1. **Total_Apparatus_Hours** - Should be a ROLLUP field (SUM of Apparatus.Labor_Hours where Scope = this scope)
2. **Scope_Total_Value** - Should be a CALCULATED field using all the rates, percentages, and fixed costs

---

## 📊 APPARATUS_REVENUE TABLE - SIMPLIFIED ARCHITECTURE

Since Scope Labor Detail handles all the complex billing calculations, Apparatus_Revenue just needs to track:

### **Fields to ADD (6 fields):**

#### **1. Labor_Hours**
```
Display name: Labor Hours
Name: cr950_labor_hours
Data type: Decimal
Required: Yes
Description: Per-apparatus billable hours
Source: Apparatus.Labor_Hours when apparatus marked complete
```

#### **2. Delays**
```
Display name: Delays
Name: cr950_delays
Data type: Decimal
Default: 0
Description: Documented delays for change order tracking
Source: Apparatus.Delays when apparatus marked complete
```

#### **3. Actual_Hours**
```
Display name: Actual Hours
Name: cr950_actual_hours
Data type: Calculated (Decimal)
Formula: cr950_labor_hours + cr950_delays
Description: Total time spent (Labor + Delays)
```

#### **4. Scope_Effective_Rate**
```
Display name: Scope Effective Rate
Name: cr950_scope_effective_rate
Data type: Currency
Required: Yes
Description: Revenue per apparatus hour for this scope
Calculation: Scope_Labor_Detail.Scope_Total_Value / Scope_Labor_Detail.Total_Apparatus_Hours
Source: Power Automate calculates when creating revenue record
```

#### **5. Revenue_Amount**
```
Display name: Revenue Amount
Name: cr950_revenue_amount
Data type: Calculated (Currency)
Formula: cr950_labor_hours * cr950_scope_effective_rate
Description: Total revenue recognized for this apparatus
```

#### **6. Revenue_Recognized_Date**
```
Display name: Revenue Recognized Date
Name: cr950_revenue_recognized_date
Data type: Date and Time
Required: Yes
Auto-populate: NOW() when record created
Description: When apparatus completed and revenue recognized
```

**OPTIONAL (Add Later):**
- Billing_Status (Choice: Recognized, Invoiced, Paid)
- Invoice_Number (Text)

---

## 🔄 POWER AUTOMATE REVENUE RECOGNITION FLOW

**Trigger:** When Apparatus.Completion_Status = "Complete"

**Steps:**

### **1. Get Related Records:**
```
Get Apparatus: [Trigger Item]
Get Scope: Apparatus.Scope (lookup)
Get Scope_Labor_Detail: Scope.Scope_Labor_Detail (lookup to financial config)
```

### **2. Calculate Scope Effective Rate:**
```
Scope_Effective_Rate = 
  Scope_Labor_Detail.Scope_Total_Value / Scope_Labor_Detail.Total_Apparatus_Hours
```

Example:
- Scope_Total_Value: $34,533
- Total_Apparatus_Hours: 160.8 hrs
- Effective_Rate: $214.68/hr

### **3. Create Apparatus_Revenue Record:**
```
Field Mappings:
  Apparatus: [Trigger Item - This Apparatus]
  Project: Apparatus.Project
  Scope_Labor_Detail: Scope.Scope_Labor_Detail
  
  Labor_Hours: Apparatus.Labor_Hours (e.g., 8.0)
  Delays: Apparatus.Delays (e.g., 2.5)
  (Actual_Hours: auto-calculates = 10.5)
  
  Scope_Effective_Rate: [calculated in step 2] (e.g., $214.68)
  (Revenue_Amount: auto-calculates = 8.0 × $214.68 = $1,717.44)
  
  Revenue_Recognized_Date: utcNow()
```

---

## 📊 EXAMPLE: COMPLETE REVENUE CALCULATION

### **Scope Configuration (from Scope_Labor_Detail):**
```
Total_Apparatus_Hours: 160.8

Base Labor: 160.8 hrs × $165 = $26,532.00
Daily Commute: 16.08 hrs (10%) × $175 = $2,814.00
Mobilization: 8.04 hrs (5%) × $175 = $1,407.00
Office PM: 8.04 hrs (5%) × $225 = $1,809.00
Office Report: 8.04 hrs (5%) × $175 = $1,407.00
Onsite LOTO: 3.22 hrs (2%) × $175 = $563.50
Onsite PM: 8.04 hrs (5%) × $175 = $1,407.00

Fixed Costs: $0 (example - could have travel, equipment costs)

Scope_Multiplier: 1.0
Scope_Total_Value: $35,939.50

Scope_Effective_Rate: $35,939.50 / 160.8 = $223.50/hr
```

### **Apparatus SW-1 Completed:**
```
Labor_Hours: 8.0
Delays: 2.5
```

### **Apparatus_Revenue Record Created:**
```
Labor_Hours: 8.0
Scope_Effective_Rate: $223.50
Revenue_Amount: $1,788.00 (8.0 × $223.50)

Delays: 2.5
Actual_Hours: 10.5 (8.0 + 2.5)

Cost Analysis:
- Revenue: $1,788.00
- Actual Time: 10.5 hrs
- Actual Cost (at $85/hr internal): $892.50
- Gross Profit: $895.50
- Margin: 50.1%
```

---

## ✅ ACTION ITEMS

### **For Scope_Labor_Detail Table:**
1. **VERIFY Total_Apparatus_Hours is a ROLLUP field**
   - If not, convert to rollup: SUM of Apparatus.Labor_Hours where Scope = this scope
   
2. **VERIFY Scope_Total_Value is CALCULATED**
   - Should use all rates, percentages, and fixed costs in formula
   - If not automated, may need Power Automate flow to calculate

### **For Apparatus_Revenue Table:**
1. **ADD 6 fields** (as specified above)
   - Labor_Hours (Decimal)
   - Delays (Decimal)
   - Actual_Hours (Calculated)
   - Scope_Effective_Rate (Currency)
   - Revenue_Amount (Calculated)
   - Revenue_Recognized_Date (DateTime)

2. **CREATE Power Automate Flow** (revenue recognition)

---

## 🎯 BOTTOM LINE

**Your Scope_Labor_Detail table is already built correctly!** ✅

You just need to:
1. Add 6 simple fields to Apparatus_Revenue table (~12 minutes)
2. Create Power Automate flow for revenue recognition (~30 minutes later)

**Then you'll have complete revenue tracking based on apparatus completion!**

---

## 💡 RECOMMENDATION

**Right now:**
- Continue finishing your 21 rollup fields
- You're making great progress!

**After rollups are complete:**
- Add 6 Apparatus_Revenue fields
- Add 6 calculated fields (Percent_Complete fields)
- Publish everything
- Then build Power Automate flow

**Don't context-switch now - finish the rollups first!** 🚀

---

**END OF ARCHITECTURE SUMMARY**

Your billing model is sophisticated but well-structured. The Scope_Labor_Detail table handles all complexity, and Apparatus_Revenue just tracks per-apparatus completion using the scope's effective rate.
