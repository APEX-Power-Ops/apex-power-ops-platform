# Revenue Recognition Flow Specification - V2 Schema

**Version:** 2.0.0  
**Date:** December 2, 2025  
**Status:** READY FOR IMPLEMENTATION  
**Target Environment:** org284447bd.crm.dynamics.com  
**Author:** Jason Swenson / Claude AI Assistant

---

## 📋 Overview

**Purpose:** Automatically create ApparatusRevenue records when field technicians mark apparatus as complete. This flow handles date stamping, revenue record creation, and financial tracking.

**Trigger:** Dataverse webhook on Apparatus completion status change  
**Tables Used:** cr950_apparatus, cr950_scopes, cr950_scopelabordetails, cr950_apparatusrevenue, cr950_projects  
**Complexity:** 🟡 Moderate - Multiple entity renames required

---

## 🔴 CRITICAL V1 → V2 Changes

| Change Type | V1 EntitySetName | V2 EntitySetName | Impact |
|-------------|------------------|------------------|--------|
| **Environment** | org99cd6c6e.crm.dynamics.com | org284447bd.crm.dynamics.com | 🔴 5 locations |
| **Scopes Table** | cr950_projectscopes | cr950_scopes | 🔴 BREAKING |
| **Projects Table** | cr950_projectses | cr950_projects | 🔴 BREAKING |
| **ScopeLaborDetail** | cr950_scopelabordetailses | cr950_scopelabordetails | 🔴 BREAKING |
| Apparatus Table | cr950_apparatuses | cr950_apparatuses | ✅ No change |
| Revenue Table | cr950_apparatusrevenues | cr950_apparatusrevenues | ✅ No change |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│               REVENUE RECOGNITION FLOW - V2 SCHEMA                       │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  TRIGGER: Apparatus.Completion_Status = "Complete" (value = 2)          │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Step 1: CHECK DATE COMPLETED                                       │ │
│  │ Condition: empty(cr950_datecompleted) is equal to true            │ │
│  │ If YES → Update cr950_datecompleted = utcNow()                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Step 2: GET SCOPE                                                  │ │
│  │ Entity: cr950_scopes (was cr950_projectscopes)                    │ │
│  │ ID: _cr950_scope_value from trigger                               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Step 3: LIST SCOPELABORDETAIL                                      │ │
│  │ Entity: cr950_scopelabordetails (was cr950_scopelabordetailses)   │ │
│  │ Filter: _cr950_scopelabor_scope_value eq {ScopeId}               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Step 4: CHECK SCOPELABORDETAIL EXISTS                              │ │
│  │ Condition: length(List_ScopeLaborDetail) > 0                      │ │
│  │ If NO → Terminate with "No labor rates defined"                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Step 5: CHECK FOR EXISTING REVENUE (Duplicate Prevention)         │ │
│  │ Entity: cr950_apparatusrevenues                                    │ │
│  │ Filter: _cr950_apparatus_value eq {ApparatusId}                   │ │
│  │ If EXISTS → Terminate (Duplicate prevention)                      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                              ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Step 6: CREATE APPARATUS REVENUE                                   │ │
│  │ Entity: cr950_apparatusrevenues                                    │ │
│  │ Fields:                                                            │ │
│  │   - Apparatus (OData bind to cr950_apparatuses)                   │ │
│  │   - Project (OData bind to cr950_projects)                        │ │
│  │   - ScopeLaborDetail (OData bind to cr950_scopelabordetails)     │ │
│  │   - Apparatus_Hours = Completed_Hours                             │ │
│  │   - Delays = Delays                                               │ │
│  │   - Effective_Labor_Rate = from ScopeLaborDetail                  │ │
│  │   - Revenue_Status = RECOGNIZED (2)                               │ │
│  │   - Revenue_Recognition_Date = utcNow()                           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 V2 Field Mappings

### Trigger Output Fields (cr950_apparatus)

| V2 Field | Description |
|----------|-------------|
| `cr950_apparatusid` | Primary key |
| `cr950_completion_status` | Trigger filter (= 2 for Complete) |
| `cr950_datecompleted` | Date stamp when complete |
| `_cr950_scope_value` | FK to Scope (if direct) or Task |
| `cr950_completed_hours` | Hours to bill |
| `cr950_delays` | Non-billable delay hours |

### Scope Fields (cr950_scopes - RENAMED)

| V2 Field | V1 Field | Notes |
|----------|----------|-------|
| `cr950_scopeid` | cr950_projectscopeid | **PRIMARY KEY RENAMED** |
| `_cr950_scope_project_value` | _cr950_project_value | FK to Project |

### ScopeLaborDetail Fields (cr950_scopelabordetails - RENAMED)

| V2 Field | V1 Field | Notes |
|----------|----------|-------|
| `cr950_scopelaborid` | cr950_scopelabordetailsid | **PRIMARY KEY RENAMED** |
| `_cr950_scopelabor_scope_value` | _cr950_projectscope_id_value | **LOOKUP RENAMED** |
| `cr950_scopelabor_effective_rate` | cr950_effectivelaborrate | Blended labor rate |

### ApparatusRevenue Fields

| V2 Field | V1 Field | Notes |
|----------|----------|-------|
| `cr950_apparatusrevenueid` | Same | Primary key |
| `cr950_Labor_Hours` | cr950_apparatushours | **POSSIBLE RENAME** - verify |
| `cr950_revenuestatus` | Same | Choice: RECOGNIZED = 2 |
| `Revenue_Recognized_Date` | cr950_revenuerecognitiondate | **POSSIBLE RENAME** |

---

## 🔧 Flow Actions - V2 Configuration

### Trigger Configuration - V2

```json
{
  "type": "OpenApiConnectionWebhook",
  "inputs": {
    "host": {
      "connectionName": "shared_commondataserviceforapps",
      "operationId": "SubscribeWebhookTrigger",
      "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps"
    },
    "parameters": {
      "subscriptionRequest/message": 3,
      "subscriptionRequest/entityname": "cr950_apparatus",
      "subscriptionRequest/scope": 4,
      "subscriptionRequest/filteringattributes": "cr950_completion_status",
      "subscriptionRequest/filterexpression": "cr950_completion_status eq 2"
    }
  }
}
```

### Action 1: Check Date Completed - V2

**Condition Expression:**
```
empty(triggerOutputs()?['body/cr950_datecompleted']) is equal to true
```

**Update Action:**
```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "host": {
      "connectionName": "shared_commondataserviceforapps",
      "operationId": "UpdateOnlyRecordWithOrganization"
    },
    "parameters": {
      "organization": "https://org284447bd.crm.dynamics.com",
      "entityName": "cr950_apparatuses",
      "recordId": "@triggerOutputs()?['body/cr950_apparatusid']",
      "item/cr950_datecompleted": "@utcNow()"
    }
  }
}
```

### Action 2: Get Scope - V2 🔴 CHANGED

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "host": {
      "connectionName": "shared_commondataserviceforapps",
      "operationId": "GetItemWithOrganization"
    },
    "parameters": {
      "organization": "https://org284447bd.crm.dynamics.com",
      "entityName": "cr950_scopes",
      "recordId": "@triggerOutputs()?['body/_cr950_scope_value']"
    }
  }
}
```

**⚠️ V1 → V2 CHANGE:** `cr950_projectscopes` → `cr950_scopes`

### Action 3: List ScopeLaborDetail - V2 🔴 CHANGED

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "host": {
      "connectionName": "shared_commondataserviceforapps",
      "operationId": "ListRecordsWithOrganization"
    },
    "parameters": {
      "organization": "https://org284447bd.crm.dynamics.com",
      "entityName": "cr950_scopelabordetails",
      "$filter": "_cr950_scopelabor_scope_value eq @{outputs('Get_Scope')?['body/cr950_scopeid']}"
    }
  }
}
```

**⚠️ V1 → V2 CHANGES:**
- EntityName: `cr950_scopelabordetailses` → `cr950_scopelabordetails`
- Filter field: `_cr950_projectscope_id_value` → `_cr950_scopelabor_scope_value`
- Scope ID field: `cr950_projectscopeid` → `cr950_scopeid`

### Action 4: List Existing Revenue (Duplicate Check)

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "host": {
      "connectionName": "shared_commondataserviceforapps",
      "operationId": "ListRecordsWithOrganization"
    },
    "parameters": {
      "organization": "https://org284447bd.crm.dynamics.com",
      "entityName": "cr950_apparatusrevenues",
      "$filter": "_cr950_apparatus_value eq @{triggerOutputs()?['body/cr950_apparatusid']}",
      "$top": 1
    }
  }
}
```

### Action 5: Create Apparatus Revenue - V2 🔴 CRITICAL CHANGES

```json
{
  "type": "OpenApiConnection",
  "inputs": {
    "host": {
      "connectionName": "shared_commondataserviceforapps",
      "operationId": "CreateRecordWithOrganization"
    },
    "parameters": {
      "organization": "https://org284447bd.crm.dynamics.com",
      "entityName": "cr950_apparatusrevenues",
      "item/cr950_Apparatus@odata.bind": "@concat('cr950_apparatuses(',triggerOutputs()?['body/cr950_apparatusid'],')')",
      "item/cr950_Project@odata.bind": "@concat('cr950_projects(',outputs('Get_Scope')?['body/_cr950_scope_project_value'],')')",
      "item/cr950_ScopeLaborDetail@odata.bind": "@concat('cr950_scopelabordetails(',first(outputs('List_ScopeLaborDetail')?['body/value'])?['cr950_scopelaborid'],')')",
      "item/cr950_apparatushours": "@triggerOutputs()?['body/cr950_completed_hours']",
      "item/cr950_delays": "@triggerOutputs()?['body/cr950_delays']",
      "item/cr950_effectivelaborrate": "@first(outputs('List_ScopeLaborDetail')?['body/value'])?['cr950_scopelabor_effective_rate']",
      "item/cr950_revenuestatus": 2,
      "item/cr950_revenuerecognitiondate": "@utcNow()"
    }
  }
}
```

**⚠️ V1 → V2 CHANGES:**
| Field | V1 Value | V2 Value |
|-------|----------|----------|
| Project binding | `cr950_projectses(...)` | `cr950_projects(...)` |
| ScopeLaborDetail binding | `cr950_scopelabordetailses(...)` | `cr950_scopelabordetails(...)` |
| ScopeLaborDetail ID field | `cr950_scopelabordetailsid` | `cr950_scopelaborid` |
| Project lookup field | `_cr950_project_value` | `_cr950_scope_project_value` |
| Effective rate field | `cr950_effectivelaborrate` | `cr950_scopelabor_effective_rate` |

---

## ⚠️ Proven Patterns - DO NOT CHANGE

These patterns were debugged and verified in V1. Maintain them in V2:

### Pattern 1: Null Check with empty()

```
empty(triggerOutputs()?['body/cr950_datecompleted']) is equal to true
```

**DO NOT USE:** `contains()`, `equals("")`, or `isNull()`

### Pattern 2: OData Binding with concat()

```
@concat('cr950_apparatuses(',triggerOutputs()?['body/cr950_apparatusid'],')')
```

**DO NOT USE:** Plain GUID values without OData bind format

### Pattern 3: Apply to Each for ScopeLaborDetail

The flow uses `Apply to each` to iterate ScopeLaborDetail results, even though there should only be one. This ensures the flow handles any edge cases properly.

---

## 🧪 Test Scenarios

### Test 1: Basic Revenue Recognition
1. Create Apparatus with Completion_Status = Pending
2. Create ScopeLaborDetail with Effective_Rate > $0
3. Update Apparatus.Completion_Status = Complete
4. **Expected:** ApparatusRevenue created with correct amounts

### Test 2: Date Stamping
1. Apparatus has NULL Date_Completed
2. Mark Complete
3. **Expected:** Date_Completed populated with current timestamp

### Test 3: Duplicate Prevention
1. Revenue record already exists for Apparatus
2. Re-mark Apparatus as Complete
3. **Expected:** Flow terminates, no duplicate created

### Test 4: Missing Rates
1. No ScopeLaborDetail exists for Scope
2. Mark Apparatus Complete
3. **Expected:** Flow terminates with "No labor rates defined"

---

## ✅ Implementation Checklist

### Pre-Implementation
- [ ] Confirm cr950_scopes table exists (renamed from projectscopes)
- [ ] Confirm cr950_scopelabordetails table exists (renamed)
- [ ] Verify field names match V2 schema
- [ ] Test ScopeLaborDetail has populated Effective_Rate

### Flow Updates (5 Required)
- [ ] Update organization URL in all actions
- [ ] Change Get_Scope entityName: `cr950_projectscopes` → `cr950_scopes`
- [ ] Change List_ScopeLaborDetail:
  - [ ] entityName → `cr950_scopelabordetails`
  - [ ] filter field → `_cr950_scopelabor_scope_value`
  - [ ] ID reference → `cr950_scopeid`
- [ ] Change Create_Revenue:
  - [ ] Project binding → `cr950_projects(...)`
  - [ ] ScopeLaborDetail binding → `cr950_scopelabordetails(...)`
  - [ ] ID field → `cr950_scopelaborid`
  - [ ] Rate field → `cr950_scopelabor_effective_rate`

### Testing
- [ ] Mark test apparatus complete
- [ ] Verify Date_Completed populated
- [ ] Verify ApparatusRevenue created
- [ ] Verify Revenue_Recognition_Date populated
- [ ] Verify amounts calculate correctly

---

## ❌ Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Resource not found" on Get_Scope | Wrong entity name | Use `cr950_scopes` not `cr950_projectscopes` |
| "No labor rates defined" | ScopeLaborDetail missing | Create ScopeLaborDetail for scope |
| "ODataUriParser error" | Wrong binding format | Use `cr950_projects(...)` not `cr950_projectses(...)` |
| Revenue = $0 | Effective_Rate = 0 | Populate ScopeLaborDetail financial fields |
| "InvalidTemplate" on condition | Using contains() on null | Use `empty(...)` pattern |

---

## 📁 Related Files

| Item | Location |
|------|----------|
| V1 Flow JSON | `Solution_Exports/v1.5.1.3/Workflows/RevenueRecognitiononApparatusCompletion-*.json` |
| V1 Flow Spec | `Documentation/02_Implementation/REVENUE_RECOGNITION_FLOW_SPEC.md` |
| Schema Audit | `Documentation/FLOW_SCHEMA_AUDIT_DEC2025.md` |
| Scope Schema | `CSV_Templates/Schema/04_Scope_Schema.csv` |
| ScopeLaborDetail Schema | `CSV_Templates/Schema/07_ScopeLaborDetail_Schema.csv` |

---

**Document Owner:** Jason Swenson  
**Created:** December 2, 2025  
**Status:** Ready for implementation
