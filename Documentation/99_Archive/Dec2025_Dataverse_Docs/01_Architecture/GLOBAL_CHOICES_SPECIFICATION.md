# RESA POWER - GLOBAL CHOICES SPECIFICATION
## Standardized Option Sets for Data Consistency

**Created:** November 10, 2025  
**Purpose:** Define global choice fields for use across all tables  
**Version:** 1.0

---

## 🎯 WHAT ARE GLOBAL CHOICES?

**Global Choices** (also called **Global Option Sets**) are reusable dropdown lists that can be used across multiple tables in Dataverse.

### **Benefits:**

✅ **Consistency** - Same values across all tables  
✅ **Maintainability** - Change once, updates everywhere  
✅ **Reporting** - Easier to filter and group across tables  
✅ **Data Quality** - Prevents inconsistent values  
✅ **Efficiency** - Create once, reuse many times  

### **When to Use Global vs. Local Choices:**

**Use GLOBAL when:**
- Field appears in multiple tables
- Values should be consistent across system
- Standard business terminology
- Values unlikely to need table-specific variations

**Use LOCAL when:**
- Field only used in one table
- Values specific to that table's context
- Needs flexibility per table

---

## 📊 RECOMMENDED GLOBAL CHOICES FOR RESA POWER

### **1. Work Status** (Most Important!)

**Name:** `resapower_workstatus`  
**Display Name:** Work Status  
**Description:** Standard status values for all work tracking (Projects, Scopes, Tasks, Apparatus)

**Values:**
```
Value | Label           | Color  | Description
------|-----------------|--------|------------------
1     | Not Started     | Gray   | Work not yet begun
2     | In Progress     | Blue   | Work currently underway
3     | Complete        | Green  | Work finished
4     | On Hold         | Yellow | Work paused/blocked
5     | Cancelled       | Red    | Work cancelled
```

**Used In:**
- Projects (ProjectStatus)
- Scopes (ScopeStatus)
- Tasks (TaskStatus)
- Apparatus (Status)

**⚠️ CRITICAL:** Apparatus.Status = "Complete" triggers revenue calculation!

---

### **2. Priority Level**

**Name:** `resapower_priority`  
**Display Name:** Priority  
**Description:** Standard priority levels for work items

**Values:**
```
Value | Label    | Color  | Description
------|----------|--------|------------------
1     | Critical | Red    | Immediate attention required
2     | High     | Orange | Important, schedule soon
3     | Medium   | Yellow | Normal priority
4     | Low      | Gray   | Can be deferred
```

**Used In:**
- Projects (ProjectPriority)
- Scopes (ScopePriority)
- Tasks (TaskPriority)
- Apparatus (Priority)

---

### **3. Availability Status**

**Name:** `resapower_availability`  
**Display Name:** Availability  
**Description:** Resource availability status

**Values:**
```
Value | Label         | Color  | Description
------|---------------|--------|------------------
1     | Available     | Green  | Ready to work
2     | On Hold       | Yellow | Temporarily unavailable
3     | Not Available | Red    | Cannot proceed
```

**Used In:**
- Scopes (ScopeAvailability)
- Apparatus (Availability)

---

### **4. Apparatus Type**

**Name:** `resapower_apparatustype`  
**Display Name:** Apparatus Type  
**Description:** Categories of electrical equipment

**Values:**
```
Value | Label                    | Description
------|--------------------------|---------------------------
1     | Pad Mount Transformer    | Outdoor pad-mounted transformers
2     | Dry Type Transformer     | Indoor dry-type transformers
3     | Liquid Filled Transformer| Oil-filled transformers
4     | Switchgear               | Low/medium voltage switchgear
5     | Circuit Breaker          | Individual breakers
6     | Motor Control Center     | MCC equipment
7     | Panel Board              | Distribution panels
8     | Generator                | Standby/emergency generators
9     | UPS                      | Uninterruptible power supply
10    | Battery System           | Battery banks/systems
11    | Transfer Switch          | Automatic transfer switches
12    | Surge Protective Device  | SPD equipment
13    | Metering Equipment       | Meters and CT/PT equipment
14    | Busway                   | Bus duct systems
15    | Other                    | Other electrical apparatus
```

**Used In:**
- Apparatus (ApparatusType)

**Why Global:** Standardizes equipment categories across all projects

---

### **5. Testing Standard** (Optional but Recommended)

**Name:** `resapower_testingstandard`  
**Display Name:** Testing Standard  
**Description:** Industry standards for testing procedures

**Values:**
```
Value | Label              | Description
------|--------------------|--------------------------
1     | NETA ATS           | NETA Acceptance Testing
2     | NETA MTS           | NETA Maintenance Testing
3     | NETA CPSD          | NETA Commissioning PSD
4     | IEEE               | IEEE Standards
5     | ANSI               | ANSI Standards
6     | Manufacturer Spec  | Per manufacturer specs
7     | Custom             | Custom test protocol
```

**Used In:**
- Scopes (TestingStandard) - if added
- Tasks (TestingStandard) - if added

---

### **6. Document Type** (For Future Use)

**Name:** `resapower_documenttype`  
**Display Name:** Document Type  
**Description:** Types of project documents

**Values:**
```
Value | Label              | Description
------|--------------------|--------------------------
1     | Test Report        | Equipment test report
2     | Datasheet          | Manufacturer datasheet
3     | Drawing            | Electrical drawings
4     | Photo              | Site photographs
5     | Certificate        | Certificates/calibration
6     | Estimate           | Project estimates
7     | Invoice            | Billing invoices
8     | Correspondence     | Email/letters
9     | Other              | Other documents
```

**Used In:**
- Document management system (future)
- SharePoint integration

---

## 🏗️ IMPLEMENTATION GUIDE

### **Step 1: Create Global Choices**

**In Power Apps:**
1. Go to make.powerapps.com
2. Solutions → Your solution
3. Add existing → Choice (option set)
4. Create new global choice
5. Enter values as specified above

**For each global choice:**
```
1. Click "New choice"
2. Display name: [from spec above]
3. Name: [resapower_choicename]
4. Type: Choice (not Yes/No)
5. Sync with global choice: Yes
6. Add all values from specification
7. Set colors (important for visual clarity)
8. Save
```

---

### **Step 2: Use in Tables**

**When creating fields in tables:**
```
Instead of:
├─ Create new local choice
└─ Define values again

Do this:
├─ Add column → Choice
├─ Sync with global choice: YES
└─ Select: resapower_workstatus (or other global choice)
```

**Example - Creating Status field in Apparatus:**
```
1. Open Apparatus table
2. Add column → Choice
3. Display name: Status
4. Logical name: cr950_status
5. Sync with global choice: YES ✅
6. Global choice: resapower_workstatus
7. Default value: Not Started
8. Required: Yes
9. Save
```

---

### **Step 3: Update Existing Tables**

**If you already created tables with local choices:**

```
Option A: Delete and Recreate (if no data)
├─ Delete the local choice field
├─ Add new field synced to global choice
└─ No data migration needed

Option B: Keep Local, Plan Migration (if data exists)
├─ Keep existing field temporarily
├─ Create new field with global choice
├─ Migrate data from old to new field
├─ Update forms to use new field
└─ Delete old field after verification
```

---

## 📋 UPDATED TABLE SCHEMAS WITH GLOBAL CHOICES

### **Projects Table:**
```
ProjectStatus → Global Choice: resapower_workstatus
ProjectPriority → Global Choice: resapower_priority
```

### **Scopes Table:**
```
ScopeStatus → Global Choice: resapower_workstatus
ScopePriority → Global Choice: resapower_priority
ScopeAvailability → Global Choice: resapower_availability
```

### **Tasks Table:**
```
TaskStatus → Global Choice: resapower_workstatus
TaskPriority → Global Choice: resapower_priority
```

### **Apparatus Table:**
```
Status → Global Choice: resapower_workstatus
Priority → Global Choice: resapower_priority
Availability → Global Choice: resapower_availability
ApparatusType → Global Choice: resapower_apparatustype
```

---

## 🎨 COLOR CODING RECOMMENDATIONS

**Status Colors (resapower_workstatus):**
```
Not Started  → #6B7280 (Gray)
In Progress  → #3B82F6 (Blue)
Complete     → #10B981 (Green)
On Hold      → #F59E0B (Yellow/Amber)
Cancelled    → #EF4444 (Red)
```

**Priority Colors (resapower_priority):**
```
Critical → #DC2626 (Dark Red)
High     → #F97316 (Orange)
Medium   → #EAB308 (Yellow)
Low      → #9CA3AF (Gray)
```

**Availability Colors (resapower_availability):**
```
Available     → #10B981 (Green)
On Hold       → #F59E0B (Yellow)
Not Available → #EF4444 (Red)
```

**Why Colors Matter:**
- Visual clarity in dashboards
- Quick status identification
- Professional appearance
- Consistent UI/UX

---

## 🔄 UPDATED CSV TEMPLATES

### **Modified Headers (Example - Apparatus):**

**BEFORE (Local Choices):**
```csv
Status,Priority,Availability,ApparatusType
Complete,High,Available,Pad Mount Transformer
```

**AFTER (Global Choices - Same Data, Different Implementation):**
```csv
Status,Priority,Availability,ApparatusType
Complete,High,Available,Pad Mount Transformer
```

**Note:** CSV data looks the same! The difference is in how you create the fields:
- **Before:** Each table defines its own Status values
- **After:** All tables use the same global Status values

---

## ⚡ POWER AUTOMATE CONSIDERATIONS

**When using global choices in flows:**

```javascript
// Checking status value in Power Automate
// Works the same with global or local choices

Trigger: When Apparatus is modified
Condition: Status equals "Complete"

// The LABEL is what you use in conditions
// Not the numeric value (1, 2, 3)
```

**Best Practice:**
- Use labels in conditions: "Complete", "In Progress"
- System handles numeric values automatically
- More readable and maintainable

---

## 📊 REPORTING BENEFITS

### **Without Global Choices:**
```
Problem: Different status values across tables
├─ Projects: "Active" vs. Tasks: "In Progress"
├─ Scopes: "Done" vs. Apparatus: "Complete"
└─ Inconsistent reporting and filtering
```

### **With Global Choices:**
```
Solution: Consistent values across all tables
├─ All use: "Not Started", "In Progress", "Complete"
├─ Reports can aggregate across all work items
└─ Single filter applies to Projects, Scopes, Tasks, Apparatus
```

**Example Report:**
```
"Show all items with Status = 'In Progress'"
├─ Returns: 5 Projects
├─ Returns: 12 Scopes
├─ Returns: 47 Tasks
└─ Returns: 234 Apparatus items
```

---

## 🎯 MIGRATION STRATEGY

### **For New Implementation (Recommended):**

```
Day 1: Create Global Choices
├─ Create all 6 global choices
├─ Define all values
└─ Set colors

Day 2-3: Build Tables Using Global Choices
├─ Projects: Use resapower_workstatus, resapower_priority
├─ Scopes: Use all 3 relevant global choices
├─ Tasks: Use resapower_workstatus, resapower_priority
└─ Apparatus: Use all 4 relevant global choices

Day 4: Verify and Test
├─ Create test records
├─ Verify dropdown values consistent
└─ Test Power Automate with new choices
```

### **For Existing Implementation:**

```
Phase 1: Create Global Choices (Week 1)
├─ Don't change existing tables yet
└─ Just create the global choices

Phase 2: Add New Fields (Week 2)
├─ Add new fields using global choices
├─ Name them: Status_New, Priority_New, etc.
└─ Keep old fields for now

Phase 3: Migrate Data (Week 3)
├─ Create Power Automate flow to copy values
├─ Map old values to new values
└─ Run migration flow

Phase 4: Update Forms (Week 4)
├─ Update all forms to use new fields
├─ Hide old fields
└─ Test with users

Phase 5: Cleanup (Week 5)
├─ Delete old fields
├─ Rename new fields (remove _New suffix)
└─ Update documentation
```

---

## 🔍 VALIDATION CHECKLIST

**Before importing data, verify:**

```
□ All global choices created in solution
□ All values defined with correct labels
□ Colors assigned to all values
□ Table fields synced to global choices (not local)
□ Default values set appropriately
□ Power Automate flows updated to use correct labels
□ Forms display choices correctly
□ Dropdowns show consistent values across tables
□ Reports can filter by global choice values
□ No duplicate local choices with same values
```

---

## 💡 ADVANCED: CHOICE VALUE MAPPING

**For CSV imports with global choices:**

```
CSV Format (Use Labels):
Status,Priority,Availability
Complete,High,Available

Power Apps will:
├─ Match label to global choice
├─ Store numeric value (3, 2, 1)
└─ Display label in UI

If import fails:
├─ Check label spelling exactly matches
├─ Verify global choice values exist
└─ Use exact label text (case-sensitive)
```

---

## 🎉 BENEFITS SUMMARY

**Using global choices gives you:**

✅ **Consistency** - Same dropdown values everywhere  
✅ **Maintainability** - Add "Delayed" status once, appears in all tables  
✅ **Data Quality** - Impossible to have "Completed" vs "Complete" typos  
✅ **Better Reports** - Filter all work items by single status value  
✅ **Professional** - Color-coded statuses look polished  
✅ **Scalable** - Easy to add new values as business grows  
✅ **Integration-Friendly** - APIs use consistent values  

---

## 📋 QUICK REFERENCE: FIELD MAPPING

| Table | Field | Global Choice | Why Global? |
|-------|-------|---------------|-------------|
| Projects | ProjectStatus | resapower_workstatus | Consistent status |
| Projects | ProjectPriority | resapower_priority | Consistent priority |
| Scopes | ScopeStatus | resapower_workstatus | Same as Projects |
| Scopes | ScopePriority | resapower_priority | Same as Projects |
| Scopes | ScopeAvailability | resapower_availability | Resource tracking |
| Tasks | TaskStatus | resapower_workstatus | Same as Projects |
| Tasks | TaskPriority | resapower_priority | Same as Projects |
| Apparatus | Status | resapower_workstatus | Same as Projects |
| Apparatus | Priority | resapower_priority | Same as Projects |
| Apparatus | Availability | resapower_availability | Same as Scopes |
| Apparatus | ApparatusType | resapower_apparatustype | Equipment categories |

---

## 🚀 RECOMMENDATION

**Create global choices BEFORE building tables!**

This is the **professional approach** and will save you time in the long run.

**Order of Operations:**
1. Create all 6 global choices (30 minutes)
2. Build tables using global choices (2 hours)
3. Import data (labels match automatically)
4. Build Power Automate (references are consistent)

**vs. Not Using Global Choices:**
- Inconsistent values across tables ❌
- Hard to maintain (change in 4 places) ❌
- Difficult reporting (different values) ❌
- Looks unprofessional ❌

---

## 📝 NEXT STEPS

1. **Review this specification** - Understand the global choices
2. **Create global choices first** - Before building tables
3. **Update CSV templates** - Fields reference global choices
4. **Build tables** - Use global choices for all specified fields
5. **Test** - Verify dropdowns work correctly
6. **Import data** - Labels should match global choice values

---

**Document Version:** 1.0  
**Last Updated:** November 10, 2025  
**Status:** Ready for Implementation  
**Recommendation:** Implement BEFORE building tables!
