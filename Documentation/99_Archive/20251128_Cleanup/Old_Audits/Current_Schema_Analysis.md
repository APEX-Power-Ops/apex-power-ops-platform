# RESA Power - Current Dataverse Schema Analysis
**Generated:** November 9, 2025  
**Environment:** RESA Power TEST

---

## 📊 TABLE SUMMARY

You have 4 core tables built with the following structure:

| Table | Columns | Key Relationships | Status |
|-------|---------|-------------------|--------|
| **Projects** | 24 total (7 custom) | Parent to Scopes, Tasks, Apparatus | ✅ Built |
| **Scopes** | 48 total (39 custom) | Child of Projects, Parent to Tasks/Apparatus | ✅ Built |
| **Tasks** | 28 total (14 custom) | Child of Projects & Scopes | ✅ Built |
| **Apparatus** | 30 total (19 custom) | Child of Projects & Scopes | ✅ Built |

---

## 1️⃣ PROJECTS TABLE (cr950_Projects)

### Custom Columns (Your Design)
| Column Name | Type | Required | Details |
|------------|------|----------|---------|
| **Name** | Text (850 char) | ✅ Required | Project identifier/name |
| **Job Number** | Text (100 char) | ✅ Required | Client job reference |
| **Client Name** | Text (100 char) | ✅ Required | |
| **Location** | Text (100 char) | Optional | |
| **Lead Technician** | Text (100 char) | Optional | |
| **Project Status** | Choice | ✅ Required | Status dropdown |
| **Start Date** | DateTime | Optional | |
| **Target Completion** | DateTime | Optional | |

### System Columns (Auto-generated)
- Created By, Created On, Modified By, Modified On
- Owner, Owning Business Unit, Owning Team, Owning User
- Status, Status Reason (system state management)
- Time Zone fields, Import Sequence Number

### Relationships
- **1 Project → Many Scopes**
- **1 Project → Many Tasks**
- **1 Project → Many Apparatus**

---

## 2️⃣ SCOPES TABLE (cr950_Scopes)

### Identification Columns
| Column Name | Type | Required | Details |
|------------|------|----------|---------|
| **Full Scope ID** | Text (850 char) | ✅ Required | Primary name field (e.g., LAS16.PPM01) |
| **Scope Number** | Whole Number | ✅ Required | Numeric identifier |
| **Drawing Reference** | Text (100 char) | Optional | Reference to drawings |
| **Project** | Lookup | ✅ Required | → Projects table |

### Financial Rate Columns (Currency fields with 2 decimals)
| Column Name | Purpose |
|------------|---------|
| **Labor Rate** | Base labor rate (required) |
| **Daily Commute Rate** | Commute rate |
| **Daily Commute Percent** | % of base |
| **Mobilization Rate** | Mobilization rate |
| **Mobilization Percent** | % of base |
| **Onsite PM Rate** | Project management rate |
| **Onsite PM Percent** | % of base |
| **PM Office Rate** | Office PM rate |
| **PM Office Percent** | % of base |
| **Onsite LOTO Rate** | Lockout/tagout rate |
| **Onsite LOTO Percent** | % of base |
| **Onsite Miscellaneous Rate** | Misc onsite rate |
| **Onsite Miscellaneous Percent** | % of base |
| **Report Rate** | Report writing rate |
| **Report Percent** | % of base |
| **Fixed Costs Travel** | Fixed travel costs |
| **Fix Cost M&E** | Fixed M&E costs |
| **Scope Multiplier** | Overall scope multiplier |
| **Scope Adjusted Total** | Calculated total |

> **Note:** Each currency field has a "(Base)" version for multi-currency support

### Work Tracking Columns
| Column Name | Type | Required |
|------------|------|----------|
| **Total Apparatus Hours** | Decimal (2) | ✅ Required |
| **Actual Hours** | Decimal (2) | Optional |
| **Scope Status** | Choice | Optional |
| **Scope Priority** | Choice | Optional |
| **Scope Availability** | Choice | Optional |

### Relationships
- **Lookup TO:** Projects (many scopes → 1 project)
- **Lookup FROM:** Tasks (1 scope → many tasks)
- **Lookup FROM:** Apparatus (1 scope → many apparatus)

---

## 3️⃣ TASKS TABLE (cr950_Tasks)

### Core Columns
| Column Name | Type | Required | Details |
|------------|------|----------|---------|
| **Task Name** | Text (850 char) | ✅ Required | Primary name |
| **Task Number** | Whole Number | ✅ Required | Numeric identifier |
| **NETA Type** | Text (100 char) | ✅ Required | NETA standard reference |
| **Project** | Lookup | ✅ Required | → Projects table |
| **Scope** | Lookup | ✅ Required | → Scopes table |

### Work Tracking Columns
| Column Name | Type | Details |
|------------|------|---------|
| **Task Apparatus Hours** | Decimal (2) | Planned hours |
| **Task Actual Hours** | Decimal (2) | Actual hours worked |
| **Task Remaining Hours** | Decimal (2) | Hours remaining |
| **Task Status** | Choice | Status dropdown |
| **Task Priority** | Choice | Priority level |
| **Task Availability** | Choice | Availability status |

### Relationships
- **Lookup TO:** Projects (many tasks → 1 project)
- **Lookup TO:** Scopes (many tasks → 1 scope)

---

## 4️⃣ APPARATUS TABLE (cr950_Apparatus)

### Identification Columns
| Column Name | Type | Required | Details |
|------------|------|----------|---------|
| **Apparatus Designation** | Text (850 char) | ✅ Required | Primary name (e.g., XFMR-001) |
| **Apparatus Number** | Whole Number | ✅ Required | Numeric identifier |
| **Apparatus Type** | Text (100 char) | Optional | Equipment type |
| **Project** | Lookup | ✅ Required | → Projects table |
| **Scope** | Lookup | Optional | → Scopes table |

### Work Tracking Columns
| Column Name | Type | Details |
|------------|------|---------|
| **Apparatus Hours** | Decimal (2) | Quoted hours for this apparatus |
| **Actual Hours** | Decimal (2) | Actual hours worked |
| **Total Hours** | Decimal (2) | Total hours |
| **Quantity on Site** | Whole Number | Count on site |
| **Quantity Completed** | Whole Number | Count completed |
| **Quantity Remaining** | Whole Number | Count remaining |

### Status Columns
| Column Name | Type | Details |
|------------|------|---------|
| **Task Status** | Choice | Work status |
| **Priority** | Choice | Priority level |
| **Availability** | Choice | Availability status |

### Relationships
- **Lookup TO:** Projects (many apparatus → 1 project)
- **Lookup TO:** Scopes (many apparatus → 1 scope)

---

## 🔗 RELATIONSHIP DIAGRAM

```
Projects (1)
    │
    ├─→ Scopes (N)
    │       │
    │       ├─→ Tasks (N)
    │       │
    │       └─→ Apparatus (N)
    │
    ├─→ Tasks (N) [also direct link]
    │
    └─→ Apparatus (N) [also direct link]
```

**Key Design Pattern:**
- Tasks link to BOTH Project and Scope (dual relationship)
- Apparatus links to BOTH Project and Scope (dual relationship)
- This ensures data integrity and flexible querying

---

## 🎯 OBSERVATIONS & RECOMMENDATIONS

### ✅ What's Working Well

1. **Solid Hierarchy:** Your 4-level structure mirrors your Excel design
2. **Comprehensive Rates:** Scopes table has all the financial columns needed
3. **Dual Relationships:** Tasks and Apparatus linking to both Project AND Scope provides flexibility
4. **Status Tracking:** Good status/priority/availability fields across tables

### 🤔 Features You're NOT Currently Using (But Could)

#### 1. **Calculated Columns** (Auto-compute fields)
Currently missing:
- `Remaining Hours` = `Apparatus Hours` - `Actual Hours`
- `Percent Complete` = `Actual Hours` / `Apparatus Hours`
- Any rate calculations (Rate * Percent)

**Should you add these?**
- ✅ YES if you want real-time calculations visible in forms/views
- ❌ NO if you'll calculate in Power BI or apps instead

#### 2. **Rollup Fields** (Aggregate child data)
Currently missing:
- Scope: Sum of all Apparatus Hours from children
- Project: Sum of all Scope hours
- Project: Count of completed apparatus

**Should you add these?**
- ✅ YES for dashboard displays and quick metrics
- ⚠️ CAUTION: Rollups recalculate hourly by default (can impact performance with 2000+ records)

#### 3. **Autonumber Format**
Currently: Using Whole Number for IDs (Apparatus Number, Scope Number, Task Number)

**Alternative:** Autonumber with format like:
- `APP-{SEQNUM:5}` → APP-00001, APP-00002
- `{RANDSTRING:4}-{SEQNUM:4}` → AB12-0001

**Should you change?**
- ❌ NO if you're importing existing numbers from Excel
- ✅ YES if you want auto-generated IDs for NEW records going forward

#### 4. **Business Rules** (Auto-set fields without code)
Examples you could add:
- When Status = "Complete" → Auto-set Date Completed to today
- When Availability = "On Hold" → Clear Assigned To
- When Priority = "High" → Send notification

**Should you add these?**
- ✅ YES for simple field automation
- Use Power Automate for complex workflows

#### 5. **Choice Column Options**
I see you have Choice columns but can't see the options from the export.

**Current Choice Columns:**
- Project Status
- Task Status, Task Priority, Task Availability
- Scope Status, Scope Priority, Scope Availability  
- Apparatus Task Status, Priority, Availability

**Question:** Do these match your Excel dropdowns from the All_Lists sheet?

#### 6. **Currency Fields - Base Currency**
You have currency fields set up with "(Base)" versions.

**This means you can:**
- Track rates in multiple currencies
- System converts to base currency automatically
- Good for international projects

**Do you need this?** Probably not if all work is USD-based.

---

## 🚨 POTENTIAL ISSUES TO ADDRESS

### 1. **Scope Lookup on Apparatus is OPTIONAL**
- Your checklist says it should be REQUIRED
- This could allow orphaned apparatus records
- **Fix:** Change Scope lookup to Required

### 2. **No Date Fields on Apparatus**
- Missing: Date Started, Date Completed
- Your checklist shows these fields
- **Fix:** Add these date fields

### 3. **No Description/Notes Fields**
- Apparatus should have Notes field (per your checklist)
- Tasks might need Notes/Task Delays field
- **Fix:** Add text area columns

### 4. **No Hierarchy ID Field**
- Your checklist shows "Hierarchy ID" field for Apparatus
- Useful for nested equipment (e.g., 1.2.1, 1.2.2)
- **Fix:** Add if you need hierarchical tracking

---

## 💡 KEY QUESTIONS FOR YOU

### About Current Schema:

1. **Are the Choice Column values set correctly?**
   - Status: Not Started, In Progress, Complete
   - Priority: High, Medium, Low
   - Availability: Ready, On Hold, Not Available

2. **Do you want calculated fields for:**
   - Remaining Hours?
   - Percent Complete?
   - Any rate calculations?

3. **Do you want rollup fields to auto-sum hours up the hierarchy?**

### About Missing Fields:

4. **Should I generate a list of fields to ADD based on your checklist vs. what's built?**

5. **Do you need the rate inheritance pattern (scope rates → apparatus)?**
   - This would likely be handled in Power Automate or app logic, not in table structure

### About Data Import:

6. **Are you ready to import LASNAP16 data (1,905 apparatus)?**
   - Need to finalize schema first
   - Then generate import CSVs from your Excel files

---

## 📋 NEXT STEPS RECOMMENDATION

1. **Schema Finalization** (This session)
   - Review missing fields from checklist
   - Decide on calculated vs. rollup fields
   - Verify choice column values

2. **Schema Updates** (30 min)
   - Add missing fields identified
   - Set proper required/optional settings
   - Configure calculated/rollup fields if desired

3. **Data Preparation** (1-2 hours)
   - Export LASNAP16 Excel to CSVs
   - Map Excel columns to Dataverse fields
   - Clean and validate data

4. **Data Import** (2-3 hours)
   - Import Projects (just LASNAP16)
   - Import 27 Scopes with rates
   - Import Tasks by apparatus type
   - Import 1,905 Apparatus records

5. **Build Model-Driven App** (Next session)
   - Create views
   - Configure forms
   - Test navigation

---

**Ready to discuss?** What aspect would you like to focus on first?
