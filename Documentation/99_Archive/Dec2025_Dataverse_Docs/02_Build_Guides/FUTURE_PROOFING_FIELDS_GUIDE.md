# Future-Proofing Fields Implementation Guide

**Version:** 1.3.0.4  
**Created:** November 19, 2025  
**Purpose:** Add extensibility fields to support future integrations, UI options, and features  
**Time:** 2-3 hours (manual implementation via Power Apps portal)

---

## 🎯 Overview

This guide adds **optional fields** that enable future capabilities without requiring schema changes later. These fields won't impact current operations but provide flexibility for:

- External system integrations (QuickBooks, legacy systems)
- Map-based UIs (geographic visualization)
- Soft deletes (audit compliance, data recovery)
- Flexible categorization (tagging/filtering)
- Data lineage tracking (where did this data come from?)
- Version control (rate changes over time)

---

## 📋 Implementation Checklist

### **High Priority (Do This Week)**

- [ ] Task 1: Enable Auditing on all tables
- [ ] Task 2: Add External System ID fields (Project, Scope, Apparatus)
- [ ] Task 3: Verify currency field precision (all tables)
- [ ] Task 4: Add Soft Delete fields (all major tables)
- [ ] Task 5: Add Latitude/Longitude to Location

### **Medium Priority (This Sprint)**

- [ ] Task 6: Add Tags field (Project, Scope, Apparatus)
- [ ] Task 7: Add Data Source tracking (all tables)
- [ ] Task 8: Add Version Number to ScopeLaborDetail
- [ ] Task 9: Document status field architecture

---

## Task 1: Enable Auditing

**Time:** 5 minutes  
**Impact:** Essential for compliance, troubleshooting, timeline controls

### **Steps:**

1. Navigate to: **Power Apps maker portal** → **Tables**
2. For each table, click **Properties**:
   - cr950_project
   - cr950_location
   - cr950_projectscope
   - cr950_task
   - cr950_apparatus
   - cr950_apparatusrevenue
   - cr950_scopelabordetail

3. Scroll to **Advanced Options**
4. Check: ☑️ **Audit changes to its data**
5. Check: ☑️ **Track changes**
6. **Save**

### **What This Enables:**

- Timeline control shows "who changed what when"
- Compliance audit logs (required for some industries)
- Data forensics when issues arise
- Change history in Dataverse

---

## Task 2: Add External System ID Fields

**Time:** 15 minutes  
**Impact:** Enables future integrations without schema changes

### **Tables to Update:**

- cr950_project
- cr950_projectscope
- cr950_apparatus

### **Fields to Add:**

#### **Field 1: External System ID**

```
Display Name: External System ID
Logical Name: cr950_external_system_id
Data Type: Text
Max Length: 100
Description: Unique identifier from external system (QuickBooks, legacy DB, etc.)
Required: No
Searchable: Yes
```

**Example values:**
- `QB-CUST-12345` (QuickBooks Customer ID)
- `LEGACY-PRJ-8901` (Old system project number)
- `EXCEL-2025-001` (Excel import batch ID)

#### **Field 2: External System Name**

```
Display Name: External System Name
Logical Name: cr950_external_system_name
Data Type: Choice
Description: Which external system this record syncs with
Required: No

Options:
├─ 1: QuickBooks
├─ 2: Legacy System
├─ 3: Excel Import
└─ 4: Other
```

### **How to Add:**

1. **Power Apps maker portal** → **Tables** → Select table
2. Click **+ New** → **Column**
3. Enter field details above
4. **Save**
5. Repeat for all 3 tables

---

## Task 3: Verify Currency Field Precision

**Time:** 5 minutes  
**Impact:** Prevents calculation errors and rounding issues

### **Fields to Check:**

**ApparatusRevenue:**
- cr950_revenue_amount → Should be: **Currency, 2 decimals**
- cr950_effective_labor_rate → Should be: **Currency, 2 decimals**

**ScopeLaborDetail:**
- cr950_effective_labor_rate → Should be: **Currency, 2 decimals**
- cr950_onsite_labor_total → Should be: **Currency, 2 decimals**

**ScopeFinancialConfig:**
- cr950_planned_revenue → Should be: **Currency, 2 decimals**
- cr950_actual_costs → Should be: **Currency, 2 decimals**

### **How to Check:**

1. **Power Apps maker portal** → **Tables** → Select table
2. Click on currency field
3. Check **Properties** → **Precision** = 2
4. If wrong, update and **Save**

---

## Task 4: Add Soft Delete Fields

**Time:** 20 minutes  
**Impact:** Prevents permanent data loss, enables "recycle bin" feature

### **Tables to Update:**

- cr950_project
- cr950_location
- cr950_projectscope
- cr950_task
- cr950_apparatus
- cr950_apparatusrevenue
- cr950_scopelabordetail

### **Fields to Add (to each table):**

#### **Field 1: Is Deleted**

```
Display Name: Is Deleted
Logical Name: cr950_is_deleted
Data Type: Yes/No
Description: Indicates if record is soft-deleted (prevents permanent loss)
Default Value: No
Required: No
```

#### **Field 2: Deleted On**

```
Display Name: Deleted On
Logical Name: cr950_deleted_on
Data Type: Date and Time
Format: Date and Time
Behavior: User Local
Description: Date and time when record was soft-deleted
Required: No
```

### **Implementation Notes:**

**Current behavior:**
- User deletes record → permanently removed from database

**After adding these fields:**
- User deletes record → Set `Is Deleted = Yes`, `Deleted On = NOW()`
- Record stays in database but hidden from default views
- Can create "Recycle Bin" view: `Is Deleted = Yes`
- Can restore by setting `Is Deleted = No`

**Requires Power Automate flow:**
- Trigger: When record deleted (Dataverse)
- Action: Instead of delete, update `Is Deleted = Yes`

---

## Task 5: Add Latitude/Longitude to Location

**Time:** 10 minutes  
**Impact:** Enables map integrations (Bing Maps, Leaflet, Google Maps)

### **Table:** cr950_location

### **Fields to Add:**

#### **Field 1: Latitude**

```
Display Name: Latitude
Logical Name: cr950_latitude
Data Type: Decimal Number
Precision: 8 decimal places
Min Value: -90
Max Value: 90
Description: Geographic latitude for map integration
Required: No
```

#### **Field 2: Longitude**

```
Display Name: Longitude
Logical Name: cr950_longitude
Data Type: Decimal Number
Precision: 8 decimal places
Min Value: -180
Max Value: 180
Description: Geographic longitude for map integration
Required: No
```

#### **Field 3: Geocode Status**

```
Display Name: Geocode Status
Logical Name: cr950_geocode_status
Data Type: Choice
Description: Status of geocoding operation
Required: No

Options:
├─ 1: Not Geocoded (default)
├─ 2: Geocoded
├─ 3: Failed
└─ 4: Manual Entry
```

### **Future Enhancement:**

Add Power Automate flow:
- When Location address changes
- Call Bing Maps API to geocode
- Store lat/long + set status = "Geocoded"

---

## Task 6: Add Tags Field

**Time:** 10 minutes  
**Impact:** Flexible categorization without rigid choice fields

### **Tables to Update:**

- cr950_project
- cr950_projectscope
- cr950_apparatus

### **Field to Add:**

```
Display Name: Tags
Logical Name: cr950_tags
Data Type: Text
Max Length: 500
Description: Comma-separated tags for flexible categorization
Required: No
Searchable: Yes

Example values:
- "high-voltage,urgent,public-sector"
- "outdoor,pole-mount,residential"
- "emergency,after-hours,weekend"
```

### **Usage Examples:**

**Filtering in views:**
- Show all "urgent" projects
- Find "outdoor" apparatus
- Search "after-hours" work

**Power BI reports:**
- Group by tags
- Tag frequency analysis

**Canvas apps:**
- Filter by tag selection
- Tag-based search

---

## Task 7: Add Data Source Tracking Fields

**Time:** 30 minutes  
**Impact:** Know where data came from, sync status with external systems

### **Tables to Update:**

- cr950_project
- cr950_projectscope
- cr950_apparatus
- cr950_apparatusrevenue

### **Fields to Add (to each table):**

#### **Field 1: Data Source**

```
Display Name: Data Source
Logical Name: cr950_data_source
Data Type: Choice
Description: How this record was created
Required: No

Options:
├─ 1: Manual Entry
├─ 2: Excel Import
├─ 3: API Integration
├─ 4: Power Automate Flow
├─ 5: Mobile App
└─ 6: Bulk Import
```

#### **Field 2: Sync Status**

```
Display Name: Sync Status
Logical Name: cr950_sync_status
Data Type: Choice
Description: External system synchronization status
Required: No

Options:
├─ 1: Not Synced
├─ 2: Pending
├─ 3: Synced
├─ 4: Error
└─ 5: Conflict
```

#### **Field 3: Last Sync Date**

```
Display Name: Last Sync Date
Logical Name: cr950_last_sync_date
Data Type: Date and Time
Format: Date and Time
Behavior: User Local
Description: Last successful sync with external system
Required: No
```

### **Usage:**

- **Excel Import:** Set `Data Source = Excel Import` when importing
- **QuickBooks Sync:** Set `Sync Status = Synced` after successful sync
- **Error Tracking:** Set `Sync Status = Error` if sync fails, check `Last Sync Date`

---

## Task 8: Add Version Number to ScopeLaborDetail

**Time:** 15 minutes  
**Impact:** Track rate changes over time for audit compliance

### **Table:** cr950_scopelabordetail

### **Fields to Add:**

#### **Field 1: Version Number**

```
Display Name: Version Number
Logical Name: cr950_version_number
Data Type: Whole Number
Min Value: 1
Description: Version number for rate changes (1, 2, 3...)
Required: No
```

#### **Field 2: Effective Date**

```
Display Name: Effective Date
Logical Name: cr950_effective_date
Data Type: Date Only
Description: Date when this version becomes active
Required: No
```

#### **Field 3: Expiration Date**

```
Display Name: Expiration Date
Logical Name: cr950_expiration_date
Data Type: Date Only
Description: Date when this version expires (next version takes over)
Required: No
```

#### **Field 4: Is Current Version**

```
Display Name: Is Current Version
Logical Name: cr950_is_current_version
Data Type: Yes/No
Default Value: Yes
Description: Indicates if this is the currently active version
Required: No
```

### **How to Use:**

**Scenario:** Labor rates increase mid-project

**Before (current approach):**
- Edit existing ScopeLaborDetail record
- Old rate is lost (no history)

**After (with versioning):**
1. Keep old record:
   - Version Number = 1
   - Effective Date = 1/1/2025
   - Expiration Date = 3/1/2025
   - Is Current Version = No

2. Create new record:
   - Version Number = 2
   - Effective Date = 3/1/2025
   - Expiration Date = (blank)
   - Is Current Version = Yes

3. Revenue recognition uses version based on `Apparatus.Date_Completed`

---

## Task 9: Document Status Field Architecture

**Time:** 30 minutes  
**Impact:** Consistent status handling across all entities

### **Create Documentation:**

File: `Documentation/01_Architecture/STATUS_FIELD_ARCHITECTURE.md`

**Content to document:**

#### **1. Status Field Pattern**

```
Every major entity has:
├─ Status Code (Dataverse native: Active/Inactive)
└─ Custom Status (Choice: entity-specific business statuses)
```

#### **2. Project Status Values**

```
cr950_project_status (Choice):
├─ 1: Planning
├─ 2: In Progress
├─ 3: On Hold
├─ 4: Complete
└─ 5: Cancelled
```

#### **3. Scope Status Values**

```
cr950_scope_status (Choice):
├─ 1: Estimating
├─ 2: Approved
├─ 3: In Progress
├─ 4: Complete
└─ 5: Voided
```

#### **4. Apparatus Status Values**

```
cr950_completion_status (Choice):
├─ 1: Not Started
├─ 2: In Progress
├─ 3: Complete
└─ 4: Voided
```

#### **5. Revenue Status Values**

```
cr950_revenue_status (Choice):
├─ 1: NOT RECOGNIZED
├─ 2: RECOGNIZED
├─ 3: ADJUSTED
└─ 4: VOIDED
```

**Document:**
- Status lifecycle (valid transitions)
- Business rules (when status can/cannot change)
- Power Automate triggers based on status
- UI behavior per status

---

## 🧪 Testing After Implementation

### **Test 1: External System ID**

1. Create test Project
2. Set External System ID = "TEST-QB-001"
3. Set External System Name = "QuickBooks"
4. Verify fields save correctly
5. Search for "TEST-QB-001" → Should find project

### **Test 2: Soft Delete**

1. Create test Apparatus
2. Mark `Is Deleted = Yes`
3. Set `Deleted On = NOW()`
4. Verify record hidden from default views
5. Create custom view: `Is Deleted = Yes` → Should see record

### **Test 3: Geographic Fields**

1. Create test Location with address
2. Manually set Latitude = 29.9511 (New Orleans)
3. Manually set Longitude = -90.0715
4. Set Geocode Status = "Manual Entry"
5. (Future) Test map control shows location correctly

### **Test 4: Tags**

1. Create test Project
2. Set Tags = "urgent,high-voltage,public-sector"
3. Search for "urgent" → Should find project
4. Filter views by tags

### **Test 5: Data Source**

1. Create Apparatus via Excel import
2. Set Data Source = "Excel Import"
3. Set Sync Status = "Not Synced"
4. View should show data lineage clearly

---

## 📊 Field Summary by Table

### **Project (7 new fields)**

- External System ID, External System Name
- Is Deleted, Deleted On
- Tags
- Data Source, Sync Status, Last Sync Date

### **Location (5 new fields)**

- Is Deleted, Deleted On
- Latitude, Longitude, Geocode Status

### **Project Scope (9 new fields)**

- External System ID, External System Name
- Is Deleted, Deleted On
- Tags
- Data Source, Sync Status, Last Sync Date

### **Task (2 new fields)**

- Is Deleted, Deleted On

### **Apparatus (9 new fields)**

- External System ID, External System Name
- Is Deleted, Deleted On
- Tags
- Data Source, Sync Status, Last Sync Date

### **Apparatus Revenue (3 new fields)**

- Is Deleted, Deleted On
- Data Source

### **Scope Labor Detail (6 new fields)**

- Is Deleted, Deleted On
- Version Number, Effective Date, Expiration Date, Is Current Version

**Total: 41 new fields across 7 tables**

---

## 🎯 Why These Fields Matter

### **Integration Example:**

**Without External System ID:**
- Sync with QuickBooks: How do you know which Dataverse Project matches which QB Customer?
- Must match on name (error-prone, names change)

**With External System ID:**
- Store QB Customer ID in Project.External_System_ID
- Perfect 1:1 mapping, never loses sync

---

### **Audit Example:**

**Without Soft Deletes:**
- User accidentally deletes project
- Data permanently lost
- Must restore from backup (if exists)

**With Soft Deletes:**
- User deletes project → marked `Is Deleted = Yes`
- Data still in database
- Admin checks "Recycle Bin" view → restores project

---

### **Map Example:**

**Without Lat/Long:**
- Can't show projects on map
- Must geocode addresses every time (slow, API costs)

**With Lat/Long:**
- Geocode once, store forever
- Map loads instantly
- Works offline (coords stored locally)

---

### **Versioning Example:**

**Without Version Number:**
- Rates change mid-project
- Can't answer: "What rate was active on March 5?"
- Audit compliance issues

**With Version Number:**
- Full history of rate changes
- Know exactly which rate to use for any date
- Audit-ready

---

## 🚀 Next Steps After Implementation

1. **Test each field** with sample data
2. **Update forms** to show new fields (make read-only if not user-editable)
3. **Create views** filtered by new fields (e.g., "External System Records")
4. **Document usage** in project wiki/training materials
5. **Export solution** with new fields (v1.3.0.4)

---

## 📝 Git Commit Message

```
feat: Add future-proofing fields v1.3.0.4

Schema enhancements for extensibility:
- External System ID fields (Project, Scope, Apparatus) for integrations
- Soft delete fields (all tables) to prevent data loss
- Geographic fields (Location) for map integration
- Tags field (Project, Scope, Apparatus) for flexible categorization
- Data Source tracking (all tables) for lineage
- Version Number (ScopeLaborDetail) for rate change history
- Enabled auditing on all tables for compliance

Total: 41 new optional fields across 7 tables
No impact on existing functionality
All fields nullable (no data migration required)
Ready for QuickBooks sync, maps, external portal, mobile apps

Next: Test fields, update forms, export solution v1.3.0.4
```

---

**Ready to implement! Start with Task 1 (Enable Auditing) - takes 5 minutes.**
