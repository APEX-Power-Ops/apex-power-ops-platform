# Revenue Recognition Flow Logic Reference

**Extracted From:** v1.5.1.3 RevenueRecognitiononApparatusCompletion  
**Purpose:** Blueprint for rebuilding flow with v1.0.0.5 schema  
**Date:** December 3, 2025

---

## Flow Overview

**Name:** RevenueRecognitiononApparatusCompletion  
**Type:** Cloud Flow (Dataverse trigger)  
**Connection:** shared_commondataserviceforapps  

### What It Does
When a field technician marks an Apparatus as "Complete", this flow:
1. Sets the completion date if not already set
2. Finds the related Scope and its labor rates
3. Checks for existing revenue record (prevents duplicates)
4. Creates an ApparatusRevenue record with calculated revenue

---

## Trigger Configuration

```json
{
  "type": "OpenApiConnectionWebhook",
  "entity": "cr950_apparatus",
  "message": 3,           // Update operation
  "scope": 4,             // Organization-wide
  "filteringattributes": "cr950_completion_status",
  "filterexpression": "cr950_completion_status eq 2"  // Only when = Complete
}
```

### Trigger Translation for New Schema

| Old Schema | New Schema | Notes |
|-----------|------------|-------|
| `cr950_apparatus` | `cr950_Apparatus` | Case may differ |
| `cr950_apparatuses` (EntitySet) | `cr950_apparatuses` | Verify in new env |
| `cr950_completion_status` | `cr950_completion_status` | Same |
| Filter value `2` | `2` | Same (Complete) |

---

## Flow Steps (Detailed)

### Step 1: Check Date Completed

**Action:** Condition check + Update record  
**Logic:**
```
IF cr950_datecompleted IS EMPTY THEN
    UPDATE Apparatus SET cr950_datecompleted = utcNow()
```

**Old Schema References:**
- Entity: `cr950_apparatuses`
- Field: `cr950_datecompleted`
- Record ID: `triggerOutputs()?['body/cr950_apparatusid']`

**New Schema Mapping:**
| Old Field | Purpose | New Field |
|-----------|---------|-----------|
| `cr950_apparatusid` | Primary key | `cr950_apparatusid` (same) |
| `cr950_datecompleted` | Completion timestamp | **NEEDS TO EXIST** |

---

### Step 2: Get Related Scope

**Action:** Get single record  
**Purpose:** Retrieve the parent Scope to get Project ID and find labor rates

**Old Schema:**
```json
{
  "operation": "GetItemWithOrganization",
  "entityName": "cr950_projectscopes",
  "recordId": "@triggerOutputs()?['body/_cr950_scope_value']"
}
```

**Key Fields Used:**
- `_cr950_scope_value` - Lookup field value from Apparatus
- `cr950_projectscopeid` - Primary key of retrieved Scope
- `_cr950_project_value` - Project lookup from Scope (used later)

**New Schema Mapping:**
| Old | Purpose | New |
|-----|---------|-----|
| `cr950_projectscopes` | Entity set | `cr950_scopes` |
| `_cr950_scope_value` | Lookup to Scope | **LOOKUP MUST EXIST** |
| `cr950_projectscopeid` | PK | `cr950_scopeid` |
| `_cr950_project_value` | Project lookup | **VERIFY EXISTS** |

---

### Step 3: List ScopeLaborDetail Records

**Action:** List records with filter  
**Purpose:** Find the labor rate configuration for this Scope

**Old Schema:**
```json
{
  "operation": "ListRecordsWithOrganization",
  "entityName": "cr950_scopelabordetailses",
  "filter": "_cr950_projectscope_id_value eq @{outputs('Get_Scope')?['body/cr950_projectscopeid']}"
}
```

**Note:** The entity set name `cr950_scopelabordetailses` has a double 's' - this appears to be intentional in old schema.

**New Schema Mapping:**
| Old | Purpose | New |
|-----|---------|-----|
| `cr950_scopelabordetailses` | Entity set | `cr950_scopelabordetails` (verify) |
| `_cr950_projectscope_id_value` | Lookup filter | **LOOKUP MUST EXIST** |
| `cr950_scopelabordetailsid` | PK | `cr950_scopelabordetailid` (verify) |
| `cr950_effectivelaborrate` | Rate value | **FIELD MUST EXIST** |

---

### Step 4: Check If Labor Rates Found

**Action:** Condition  
**Logic:**
```
IF length(List_ScopeLaborDetail.value) > 0 THEN
    Continue to revenue creation
ELSE
    Terminate with error: "MissingRates"
```

**Error Response:**
```json
{
  "runStatus": "Failed",
  "runError": {
    "code": "MissingRates",
    "message": "Cannot recognize revenue: No labor rates defined for this scope"
  }
}
```

---

### Step 5: List Existing Revenue (Duplicate Check)

**Action:** List records with filter  
**Purpose:** Prevent duplicate revenue records for same Apparatus

**Old Schema:**
```json
{
  "operation": "ListRecordsWithOrganization",
  "entityName": "cr950_apparatusrevenues",
  "filter": "_cr950_apparatus_value eq @{triggerOutputs()?['body/cr950_apparatusid']}",
  "top": 1
}
```

**New Schema Mapping:**
| Old | Purpose | New |
|-----|---------|-----|
| `cr950_apparatusrevenues` | Entity set | `cr950_apparatusrevenues` (verify) |
| `_cr950_apparatus_value` | Lookup filter | **LOOKUP MUST EXIST** |

---

### Step 6: Condition - Revenue Exists?

**Logic:**
```
IF length(List_Existing_Revenue.value) == 0 THEN
    Create new revenue record
ELSE
    Terminate (success - already exists)
```

---

### Step 7: Create Apparatus Revenue Record (For Each ScopeLaborDetail)

**Action:** Apply to each + Create record  
**Loop:** Iterates over each ScopeLaborDetail (typically just 1)

**Old Schema - Record Creation:**
```json
{
  "operation": "CreateRecordWithOrganization",
  "entityName": "cr950_apparatusrevenues",
  "item": {
    "cr950_Apparatus@odata.bind": "cr950_apparatuses({apparatus_id})",
    "cr950_apparatushours": "{completed_hours from trigger}",
    "cr950_Project@odata.bind": "cr950_projectses({project_id from scope})",
    "cr950_revenuestatus": 2,
    "cr950_ScopeLaborDetail@odata.bind": "cr950_scopelabordetailses({scopelabordetail_id})",
    "cr950_delays": "{delays from trigger}",
    "cr950_effectivelaborrate": "{rate from scopelabordetail}",
    "cr950_revenuerecognitiondate": "{utcNow()}"
  }
}
```

### Field Mapping Table for Create Operation

| Field | Source | Expression | Notes |
|-------|--------|------------|-------|
| `cr950_Apparatus` | Trigger | `concat('cr950_apparatuses(',triggerOutputs()?['body/cr950_apparatusid'],')')` | OData bind |
| `cr950_apparatushours` | Trigger | `triggerOutputs()?['body/cr950_completed_hours']` | **Source field must exist** |
| `cr950_Project` | Scope lookup | `concat('cr950_projectses(',outputs('Get_Scope')?['body/_cr950_project_value'],')')` | OData bind |
| `cr950_revenuestatus` | Static | `2` | 2 = RECOGNIZED |
| `cr950_ScopeLaborDetail` | Loop item | `concat('cr950_scopelabordetailses(',items('Apply_to_each')?['cr950_scopelabordetailsid'],')')` | OData bind |
| `cr950_delays` | Trigger | `triggerOutputs()?['body/cr950_delays']` | **Source field must exist** |
| `cr950_effectivelaborrate` | Loop item | `items('Apply_to_each')?['cr950_effectivelaborrate']` | **Field must exist** |
| `cr950_revenuerecognitiondate` | System | `utcNow()` | Current timestamp |

---

## Complete New Schema Field Requirements

### Fields Apparatus MUST Have (Read by Flow)

| Field | Type | Purpose in Flow |
|-------|------|-----------------|
| `cr950_apparatusid` | GUID | Record identifier |
| `cr950_completion_status` | Choice | Trigger filter (value = 2) |
| `cr950_datecompleted` | DateTime | Updated by flow if null |
| `cr950_scope` (lookup) | Lookup | Get parent scope - `_cr950_scope_value` |
| `cr950_completed_hours` | Decimal | Copied to revenue record |
| `cr950_delays` | Decimal | Copied to revenue record |

### Fields Scope MUST Have (Read by Flow)

| Field | Type | Purpose in Flow |
|-------|------|-----------------|
| `cr950_scopeid` | GUID | Record identifier (old: cr950_projectscopeid) |
| `cr950_project` (lookup) | Lookup | Get project ID - `_cr950_project_value` |

### Fields ScopeLaborDetail MUST Have (Read by Flow)

| Field | Type | Purpose in Flow |
|-------|------|-----------------|
| `cr950_scopelabordetailid` | GUID | Record identifier |
| `cr950_scope` (lookup) | Lookup | Filter to find rates - `_cr950_projectscope_id_value` |
| `cr950_effectivelaborrate` | Currency | Copied to revenue record |

### Fields ApparatusRevenue MUST Have (Written by Flow)

| Field | Type | Purpose in Flow |
|-------|------|-----------------|
| `cr950_apparatus` (lookup) | Lookup | Link to source apparatus |
| `cr950_apparatushours` | Decimal | Hours being recognized |
| `cr950_project` (lookup) | Lookup | Link to project |
| `cr950_revenuestatus` | Choice | Set to 2 (Recognized) |
| `cr950_scopelabordetail` (lookup) | Lookup | Link to rate source |
| `cr950_delays` | Decimal | Delay hours |
| `cr950_effectivelaborrate` | Currency | Rate snapshot |
| `cr950_revenuerecognitiondate` | DateTime | When recognized |

---

## Entity Set Name Changes (Old → New)

| Table | Old EntitySet | New EntitySet (Expected) |
|-------|---------------|-------------------------|
| Apparatus | `cr950_apparatuses` | `cr950_apparatuses` |
| Project | `cr950_projectses` | `cr950_projects` (verify) |
| Scope | `cr950_projectscopes` | `cr950_scopes` |
| ScopeLaborDetail | `cr950_scopelabordetailses` | `cr950_scopelabordetails` |
| ApparatusRevenue | `cr950_apparatusrevenues` | `cr950_apparatusrevenues` |

**⚠️ IMPORTANT:** Verify actual EntitySet names in new environment before building flow. Use:
```
GET https://org7bdbc942.crm.dynamics.com/api/data/v9.2/EntityDefinitions?$select=LogicalName,EntitySetName&$filter=startswith(LogicalName,'cr950_')
```

---

## Flow Rebuild Checklist

### Before Building

- [ ] All lookup fields exist in new schema
- [ ] All source fields exist (completed_hours, delays, effectivelaborrate)
- [ ] EntitySet names verified for new environment
- [ ] Choice field options match (completion_status=2, revenuestatus=2)

### Flow Actions to Create

1. [ ] **Trigger:** When Apparatus updated with completion_status filter
2. [ ] **Condition 1:** Check datecompleted is null
3. [ ] **Action:** Update Apparatus with datecompleted = utcNow()
4. [ ] **Action:** Get Scope record using lookup value
5. [ ] **Action:** List ScopeLaborDetail filtered by scope
6. [ ] **Condition 2:** Check if ScopeLaborDetail found
7. [ ] **Terminate (error):** If no rates found
8. [ ] **Action:** List existing ApparatusRevenue for apparatus
9. [ ] **Condition 3:** Check if revenue already exists
10. [ ] **Terminate (success):** If duplicate
11. [ ] **Apply to each:** Loop through ScopeLaborDetail
12. [ ] **Action:** Create ApparatusRevenue record

### Testing Scenarios

1. **Happy Path:** Mark apparatus complete → Revenue record created
2. **Missing Rates:** Apparatus complete but no ScopeLaborDetail → Error terminates
3. **Duplicate Prevention:** Complete same apparatus twice → Second run succeeds but creates nothing
4. **Date Stamp:** Verify datecompleted is set on first completion

---

## Alternative Approaches (Considerations)

### Option 1: Simplify the Loop
The original flow uses "Apply to each" over ScopeLaborDetail results. In practice, there's typically only 1 ScopeLaborDetail per Scope. Could simplify to:
- Use `first()` expression instead of loop
- Reduces flow complexity

### Option 2: Use Calculated Revenue Amount
Instead of copying effectivelaborrate and calculating in reports:
- Add calculated field `cr950_revenueamount` on ApparatusRevenue
- Formula: `apparatushours * effectivelaborrate`
- Pro: Revenue is pre-calculated
- Con: Additional field to maintain

### Option 3: Power Fx Low-Code Plugin
Instead of Power Automate:
- Create Dataverse low-code plugin
- Triggers on Apparatus completion
- Runs synchronously (immediate)
- No separate flow to maintain

**Recommendation:** Start with Power Automate flow matching old design. Optimize in future iterations.

---

*End of Flow Logic Reference*
