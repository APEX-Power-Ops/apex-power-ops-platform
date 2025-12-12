# CSV Import Templates - RESA Power Project Tracker

**Version:** 1.1  
**Date:** November 10, 2025  
**Purpose:** Standard CSV templates for importing data into Power Apps Dataverse tables

---

## 📋 TEMPLATE OVERVIEW

This directory contains 6 CSV templates for importing data into the RESA Power Project Tracker system:

| Template | Filename | Purpose | Import Priority | Notes |
|----------|----------|---------|----------------|-------|
| Locations | `00_Locations_Template.csv` | Master location data | **0 - IMPORT FIRST** | 4 Southwest Region offices |
| Projects | `01_Projects_Template.csv` | Core project records | 1 | Import after Locations |
| Scopes | `02_Scopes_Template.csv` | Work breakdown with NETA Standard | 2 | Includes NETA_Standard field (ATS/MTS) |
| Tasks | `03_Tasks_Template.csv` | Task organization | **MANUAL ONLY** | **NOT imported - PMs create manually** |
| Apparatus | `04_Apparatus_Template.csv` | Individual testable units | 3 | Labor hours vary by NETA_Standard |
| Scope Financial Config | `05_Scope_Financial_Config_Template.csv` | Financial rates & multipliers | 2 | **RESTRICTED ACCESS** |
| Apparatus Revenue | `06_Apparatus_Revenue_Template.csv` | Revenue recognition records | **AUTO-GENERATED** | Usually created by Power Automate |

---

## ⭐ CRITICAL UPDATES IN v1.1

### 1. NETA Standards Architecture
- **`02_Scopes_Template.csv`** now includes `NETA_Standard` column (ATS or MTS)
- ATS = Acceptance Testing Specifications (new installations)
- MTS = Maintenance Testing Specifications (existing equipment maintenance)
- NETA_Standard at Scope level determines which specifications apply to all Tasks and Apparatus

### 2. Tasks Table - Manual Creation Only
- **`03_Tasks_Template.csv`** is for **REFERENCE ONLY**
- Tasks are **NOT imported** from Excel estimators
- Excel estimators have no task-level structure
- Project Managers manually create tasks in Power Apps after scope/apparatus import
- Tasks organize apparatus into logical work groups for technician assignment

### 3. Financial Data Separation
- Financial configuration separated into `05_Scope_Financial_Config_Template.csv`
- Field technicians access operational data only (Projects, Scopes, Tasks, Apparatus)
- Financial data (rates, multipliers, revenue) restricted to PM/Admin/Billing roles

---

## 📥 IMPORT WORKFLOW

### Standard Import Process:

```
Step 0: Import Locations (00_Locations_Template.csv) ← Master data FIRST
   ↓
Step 1: Import Projects (01_Projects_Template.csv)
   ↓
Step 2a: Import Scopes (02_Scopes_Template.csv) - includes NETA_Standard
Step 2b: Import Scope Financial Config (05_Scope_Financial_Config_Template.csv)
   ↓
Step 3: Import Apparatus (04_Apparatus_Template.csv)
   ↓ 
Step 4: PM MANUALLY creates Tasks in Power Apps to organize apparatus
   ↓
Step 5: Revenue auto-calculates via Power Automate when apparatus completed
```

### Import from Excel Estimator:

```
Excel Estimator (existing tool)
   ↓
Project_Data Sheet (with Scope NETA_Standard in Cell C3)
   ↓
Import Script (Python or Power Automate)
   ↓
Creates:
   - Projects table records
   - Scopes table records (with NETA_Standard from Cell C3)
   - Apparatus table records (expanded from quantities)
   ↓
SKIP: Tasks table (no task structure in Excel)
   ↓
PM manually creates Tasks to organize apparatus
```

---

## 🗂️ TEMPLATE DETAILS

### 00_Locations_Template.csv ⭐ MASTER DATA - IMPORT FIRST

**Purpose:** Pre-populate the 4 Southwest Region RESA Power office locations  
**Required Fields:** Location_Code, Location_Name, Location_Abbreviation, Region, Active  
**Optional Fields:** Sort_Order, Office_Address, Office_Manager, Notes  

**Key Notes:**
- **IMPORT THIS FIRST** before any other tables
- Location_Code is a TEXT field (not auto-number) and serves as PRIMARY KEY
- Must be unique - these are the 3-digit office identifiers (575, 571, 578, 574)
- Projects table references Location_Code as foreign key
- Used in Full Project ID format: `{Location_Abbreviation}-{Job_Number}`
  - Example: PHX-674414 (Phoenix office, Job Number 674414)

**Pre-Populated Southwest Region Locations:**
1. **575 - San Diego (SD)** - San Diego Service Unit
2. **571 - Las Vegas (LAS)** - Las Vegas Service Unit  
3. **578 - Phoenix (PHX)** - Phoenix Service Unit (Primary office)
4. **574 - Denver (DEN)** - Denver Service Unit

**Import Order:**
```
Step 0: Locations ← YOU ARE HERE (Master Data)
Step 1: Projects (references Location_Code)
Step 2: Scopes, Financial Config
Step 3: Apparatus
Step 4: Manual task creation by PMs
```

**Critical:**
- All 4 locations must be imported before creating any Projects
- Location_Code values are independent from Job Numbers
- Active = "Yes" controls whether location appears in dropdowns

---

### 01_Projects_Template.csv

**Purpose:** Import core project records  
**Required Fields:** Job_Number, Location_Code, Project_Name, Customer_Name, Project_Status  
**Optional Fields:** Description, Project_Manager, Contract_Value, dates  

**Key Notes:**
- Job_Number is the primary business key (6-7 digits, sequential company-wide)
- Location_Code must exist in Locations master table
- One row = one project

---

### 02_Scopes_Template.csv ⭐ UPDATED

**Purpose:** Import scopes with NETA Standard specification  
**Required Fields:** Scope_Name, Project_Job_Number, **NETA_Standard**  
**Optional Fields:** SLD_Reference, Scope_Status, Total_Apparatus_Hours, Notes  

**Key Notes:**
- **NETA_Standard is REQUIRED** - must be "ATS" or "MTS"
- NETA_Standard determines which labor hours and section references apply to apparatus
- In Excel estimator, NETA_Standard comes from Cell C3 (merged cell) on each scope sheet
- One row = one scope
- Project_Job_Number must exist in Projects table

**NETA Standard Options:**
- **ATS** (Acceptance Testing Specifications) - For new installations, commissioning work
- **MTS** (Maintenance Testing Specifications) - For existing equipment, ongoing maintenance

---

### 03_Tasks_Template.csv ⭐ REFERENCE ONLY

**Purpose:** REFERENCE template for task organization - NOT FOR IMPORT  
**Status:** **MANUAL CREATION ONLY**  

**Why Not Imported:**
- Excel estimators have no task-level structure
- Tasks are a Power Apps organizational construct
- PMs create tasks after import to group apparatus logically

**Manual Task Creation Workflow:**
1. After scope and apparatus import completes
2. PM reviews apparatus in each scope
3. PM creates tasks to group similar apparatus (e.g., "All Transformers", "Switchgear A-D")
4. PM assigns tasks to technicians
5. Technicians complete apparatus within assigned tasks

**Template Use:** Reference for field structure and data types only

---

### 04_Apparatus_Template.csv

**Purpose:** Import individual testable apparatus units  
**Required Fields:** Apparatus_Number, Project_Job_Number, Scope_Name, Apparatus_Type_Name, Labor_Hours  
**Optional Fields:** Task_Name (can assign later), Apparatus_Tag, Equipment_Description, Test_Voltage, etc.  

**Key Notes:**
- One row = ONE testable unit (e.g., "19x Transformer" = 19 separate rows)
- Labor_Hours should match parent Scope's NETA_Standard (ATS or MTS hours from Apparatus_Type_Master)
- NETA_Section auto-populates from Apparatus_Type_Master based on NETA_Standard
- Task_Name can be blank initially - assigned when PM creates tasks
- Completion_Status triggers revenue recognition when set to "Complete"

**Quantity Expansion:**
- Excel estimator shows "12x Circuit Breaker"
- Import process creates 12 separate apparatus records
- Each record can be individually tracked and completed

---

### 05_Scope_Financial_Config_Template.csv ⭐ RESTRICTED ACCESS

**Purpose:** Store financial rates and multipliers for revenue calculation  
**Required Fields:** Scope_Name, Project_Job_Number, Base_Labor_Rate  
**Optional Fields:** All multipliers, fixed costs, notes  

**🚨 SECURITY CRITICAL:**
- **Field technicians CANNOT access this data**
- Access restricted to: Project Managers, Administrators, Billing Team
- Contains sensitive pricing and markup information

**Key Notes:**
- One row = financial configuration for one scope
- Multipliers are percentages in decimal form (e.g., 0.043 = 4.3%)
- Power Automate flows use this data to calculate revenue when apparatus completed
- NETA_Standard may affect rates (MTS typically lower than ATS)

**Revenue Calculation Formula:**
```
Apparatus Revenue = (Labor_Hours × Base_Labor_Rate) × 
                   (1 + Commute_Multiplier + PM_Multiplier + 
                    Daily_Report_Multiplier + Travel_Multiplier + 
                    Final_Report_Multiplier) × 
                   Scope_Multiplier + 
                   Proportional_Fixed_Costs
```

---

### 06_Apparatus_Revenue_Template.csv ⭐ AUTO-GENERATED

**Purpose:** Revenue recognition records (usually auto-created)  
**Status:** **TYPICALLY NOT IMPORTED** - Auto-generated by Power Automate  

**Use Cases for Manual Import:**
1. Historical data migration from legacy systems
2. Manual revenue adjustments (requires documented reason)
3. Revenue verification and audit purposes

**🚨 SECURITY CRITICAL:**
- **Field technicians CANNOT access this data**
- Access restricted to: Project Managers, Administrators, Billing Team

**Auto-Generation Trigger:**
- When Apparatus.Completion_Status changes to "Complete"
- Power Automate flow:
  1. Retrieves Scope_Financial_Configuration
  2. Calculates revenue using formula
  3. Creates record in Apparatus_Revenue table
  4. Updates Apparatus.Billable_Revenue field
  5. Triggers rollup to Scope and Project totals

---

## 🔐 DATA SECURITY & ACCESS CONTROL

### Access Levels:

| Role | Projects | Scopes | Tasks | Apparatus | Financial Config | Revenue |
|------|----------|--------|-------|-----------|-----------------|---------|
| Field Technician | Read | Read | Read/Write | Read/Write | **NO ACCESS** | **NO ACCESS** |
| Project Manager | Full | Full | Full | Full | Full | Full |
| Administrator | Full | Full | Full | Full | Full | Full |
| Billing Team | Read | Read | Read | Read | Read | Full |

### Security Implementation:
- Separate Dataverse tables for operational vs. financial data
- Field-level security on financial columns
- Security roles enforce access restrictions
- Power Automate flows use elevated permissions for calculations

---

## 📊 DATA VALIDATION RULES

### All Templates:
- ✅ UTF-8 encoding required
- ✅ First row must be column headers
- ✅ Date format: YYYY-MM-DD or MM/DD/YYYY
- ✅ Decimal separator: period (.)
- ✅ No special characters in IDs or keys
- ✅ Required fields cannot be blank

### Relationships:
- ✅ Location_Code must exist in Locations table before importing Projects
- ✅ Project_Job_Number must exist before importing Scopes
- ✅ Scope_Name must exist before importing Apparatus
- ✅ Apparatus_Type_Name must exist in Apparatus_Type_Master table
- ✅ NETA_Standard must be exactly "ATS" or "MTS" (case-sensitive)

### NETA Standards:
- ✅ Each Scope must have NETA_Standard defined (ATS or MTS)
- ✅ All Apparatus in a Scope inherit the Scope's NETA_Standard
- ✅ Labor_Hours must match the NETA_Standard (ATS or MTS hours from master)
- ✅ NETA_Section must match the NETA_Standard (ATS or MTS section from master)

---

## 🚨 COMMON IMPORT ERRORS & SOLUTIONS

### "Invalid NETA_Standard value"
**Error:** NETA_Standard column contains value other than "ATS" or "MTS"  
**Solution:** Check spelling, ensure exact match (case-sensitive), verify no extra spaces

### "Parent record not found"
**Error:** Lookup value doesn't exist (e.g., Project_Job_Number not in Projects table)  
**Solution:** Import tables in correct order (Projects → Scopes → Apparatus)

### "Duplicate key"
**Error:** Primary key or unique field has duplicate value  
**Solution:** Ensure Job_Numbers, Scope_Names, Apparatus_Numbers are unique within project

### "Wrong labor hours for NETA_Standard"
**Error:** Apparatus labor hours don't match parent Scope's NETA_Standard  
**Solution:** 
- Check parent Scope's NETA_Standard (ATS or MTS)
- Use corresponding labor hours from Apparatus_Type_Master
- ATS hours typically higher than MTS hours (more comprehensive testing)

### "Required field missing"
**Error:** Required column is blank  
**Solution:** Fill in all required fields before import

### "Apparatus quantity not expanded"
**Error:** Excel shows "12x Circuit Breaker" but only one record imported  
**Solution:** Use import script to expand quantities into individual records

---

## 🔄 VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-08 | Initial template creation |
| 1.1 | 2025-11-10 | **CRITICAL UPDATES:** |
| | | ⭐ Added NETA_Standard field to Scopes template |
| | | ⭐ Clarified Tasks template as REFERENCE ONLY (not imported) |
| | | ⭐ Updated Apparatus template with NETA_Standard considerations |
| | | ⭐ Added security notes for financial data templates |
| | | ⭐ Enhanced import workflow documentation |
| | | ⭐ Added NETA Standards validation rules |

---

## 📞 SUPPORT

**Questions about templates or import process:**
- Contact: Jason Smith, Phoenix Services Unit
- Email: [email placeholder]
- Documentation: See Master Build Specification v1.1

**Technical issues with Power Apps/Dataverse:**
- Contact: IT Support
- Submit ticket: [support portal placeholder]

---

**Document Owner:** Jason Smith  
**Last Updated:** November 10, 2025  
**Version:** 1.1  
**Classification:** Internal Use Only
