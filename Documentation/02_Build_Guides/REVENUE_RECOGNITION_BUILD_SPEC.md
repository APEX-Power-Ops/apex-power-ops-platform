# Revenue Recognition Build Specification

**Created:** December 2, 2025  
**Status:** APPROVED FOR BUILD  
**Environment:** org7bdbc942.crm.dynamics.com (Developer)  
**Architecture:** Financial/Operations Separation Pattern

---

## 📋 Overview

This specification defines the complete revenue recognition system using the **Financial/Operations Separation** pattern where financial calculations are isolated in dedicated tables, separate from operational data.

### Core Principle
> *"Financial metrics aggregated at [level] (separation from operations)"*

### Data Flow
```
Excel Estimator
    ↓ (VBA Export)
JSON File
    ↓ (Import Script)
┌─────────────────────────────────────────────────────────────────┐
│ OPERATIONAL TABLES                                              │
├─────────────────────────────────────────────────────────────────┤
│ Client → Site → Project → Scope → Task → Apparatus              │
│                              ↓                                  │
│                    ScopeLaborDetail (rates/totals)              │
└─────────────────────────────────────────────────────────────────┘
                               ↓ (Power Automate triggers)
┌─────────────────────────────────────────────────────────────────┐
│ FINANCIAL TABLES                                                │
├─────────────────────────────────────────────────────────────────┤
│ ApparatusRevenue → ScopeFinancialSummary → ProjectFinancialSummary
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLOW 1: ScopeLaborDetail Rate Calculation

### Purpose
Automatically calculate per-hour rates when financial totals are imported from Excel.

### Trigger
- **Table:** `cr950_scopelabordetails`
- **Event:** Create or Update
- **Condition:** `cr950_scopelabortotalhours > 0`

### Input Fields (from Excel Import)
| Field | Schema Name | Source |
|-------|-------------|--------|
| Total Hours | `cr950_scopelabortotalhours` | Cell J3 |
| Multiplier | `cr950_scopelabormultiplier` | Cell M4 |
| Onsite Total | `cr950_scopelaboronsitetotal` | Cell P14 |
| Offsite Total | `cr950_scopelaboroffsitetotal` | Cell P19 |
| Travel Total | `cr950_scopelabortraveltotal` | Cell P26 |
| Outside Services Total | `cr950_scopelaboroutsidetotal` | Cell P33 |

### Calculated Fields (set by Flow)
| Field | Schema Name | Formula |
|-------|-------------|---------|
| Onsite Rate | `cr950_scopelaboronsiterate` | `onsite_total / total_hours` |
| Offsite Rate | `cr950_scopelaboroffsiterate` | `offsite_total / total_hours` |
| Travel Rate | `cr950_scopelabortravelrate` | `travel_total / total_hours` |
| Outside Rate | `cr950_scopelaboroutsiderate` | `outside_total / total_hours` |
| Sum of Rates | `cr950_scopelaborsumofrates` | `onsite + offsite + travel + outside` |
| Effective Rate | `cr950_scopelaboreffectiverate` | `sum_of_rates × multiplier` |
| Unadjusted Total | `cr950_scopelaborunadjustedtotal` | `sum of 4 totals` |
| Adjusted Total | `cr950_scopelaboradjustedtotal` | `unadjusted × multiplier` |

### Flow Logic (Pseudo-code)
```
TRIGGER: When ScopeLaborDetail is created or modified

CONDITION: cr950_scopelabortotalhours > 0

ACTIONS:
  // Get current values
  total_hours = triggerBody()?['cr950_scopelabortotalhours']
  multiplier = triggerBody()?['cr950_scopelabormultiplier']
  onsite_total = triggerBody()?['cr950_scopelaboronsitetotal']
  offsite_total = triggerBody()?['cr950_scopelaboroffsitetotal']
  travel_total = triggerBody()?['cr950_scopelabortraveltotal']
  outside_total = triggerBody()?['cr950_scopelaboroutsidetotal']
  
  // Calculate rates (division)
  onsite_rate = onsite_total / total_hours
  offsite_rate = offsite_total / total_hours
  travel_rate = travel_total / total_hours
  outside_rate = outside_total / total_hours
  
  // Calculate aggregates
  sum_of_rates = onsite_rate + offsite_rate + travel_rate + outside_rate
  effective_rate = sum_of_rates * multiplier
  unadjusted = onsite_total + offsite_total + travel_total + outside_total
  adjusted = unadjusted * multiplier
  
  // Update record
  UPDATE cr950_scopelabordetails
  SET
    cr950_scopelaboronsiterate = onsite_rate,
    cr950_scopelaboroffsiterate = offsite_rate,
    cr950_scopelabortravelrate = travel_rate,
    cr950_scopelaboroutsiderate = outside_rate,
    cr950_scopelaborsumofrates = sum_of_rates,
    cr950_scopelaboreffectiverate = effective_rate,
    cr950_scopelaborunadjustedtotal = unadjusted,
    cr950_scopelaboradjustedtotal = adjusted
  WHERE id = triggerBody()?['cr950_scopelabordetailid']
```

### Validation Example
```
Input:
  Total Hours: 176 hrs
  Multiplier: 1.15
  Onsite Total: $50,000
  Offsite Total: $3,000
  Travel Total: $5,600
  Outside Total: $10,960

Calculated:
  Onsite Rate: $50,000 / 176 = $284.09/hr
  Offsite Rate: $3,000 / 176 = $17.05/hr
  Travel Rate: $5,600 / 176 = $31.82/hr
  Outside Rate: $10,960 / 176 = $62.27/hr
  
  Sum of Rates: $284.09 + $17.05 + $31.82 + $62.27 = $395.23/hr
  Effective Rate: $395.23 × 1.15 = $454.51/hr ⭐
  
  Unadjusted: $50,000 + $3,000 + $5,600 + $10,960 = $69,560
  Adjusted: $69,560 × 1.15 = $79,994
```

---

## 🏗️ TABLE 1: ApparatusRevenue

### Purpose
Track revenue for each individual apparatus when work is completed. This is the **granular financial record** that enables accurate revenue recognition.

### Schema: `cr950_apparatusrevenue`
**Display Name:** Apparatus Revenue  
**Plural Name:** Apparatus Revenue Records  
**Description:** Financial metrics for individual apparatus (separation from operations)

### Fields

| # | Display Name | Schema Name | Type | Required | Description |
|---|--------------|-------------|------|----------|-------------|
| 1 | Name | `cr950_name` | Text (100) | Auto | Auto-generated: "{Apparatus Name} - Revenue" |
| 2 | Apparatus | `cr950_apparatus_id` | Lookup | Yes | Parent apparatus record |
| 3 | Scope Labor Detail | `cr950_scopelabordetail_id` | Lookup | Yes | Source of effective rate |
| 4 | Planned Hours | `cr950_plannedhours` | Decimal | Yes | Initial hour estimate (from apparatus) |
| 5 | Delay Hours | `cr950_delayhours` | Decimal | No | Additional hours due to delays |
| 6 | Actual Hours | `cr950_actualhours` | Calculated | - | `planned_hours + delay_hours` |
| 7 | Labor Rate Applied | `cr950_laborrateapplied` | Money | - | Copied from effective rate at recognition |
| 8 | Revenue Amount | `cr950_revenueamount` | Money | - | `actual_hours × labor_rate_applied` |
| 9 | Revenue Status | `cr950_revenuestatus` | Choice | Yes | PLANNED/IN_PROGRESS/RECOGNIZED |
| 10 | Recognition Date | `cr950_recognitiondate` | DateTime | No | When revenue was recognized |
| 11 | Scope Financial Summary | `cr950_scopefinancialsummary_id` | Lookup | No | For rollup relationships |

### Choice: Revenue Status
| Value | Label | Description |
|-------|-------|-------------|
| 1 | Planned | Work not started |
| 2 | In Progress | Work started, not complete |
| 3 | Recognized | Work complete, revenue recognized |

### Relationships
| Type | Related Table | Field |
|------|---------------|-------|
| N:1 | Apparatus | `cr950_apparatus_id` |
| N:1 | ScopeLaborDetail | `cr950_scopelabordetail_id` |
| N:1 | ScopeFinancialSummary | `cr950_scopefinancialsummary_id` |

### Calculated Field Formulas

**Actual Hours:**
```
cr950_actualhours = cr950_plannedhours + COALESCE(cr950_delayhours, 0)
```

**Revenue Amount:**
```
cr950_revenueamount = cr950_actualhours * cr950_laborrateapplied
```

---

## 🔄 FLOW 2: Revenue Recognition Flow

### Purpose
When an Apparatus is marked complete, create/update the ApparatusRevenue record and recognize revenue.

### Trigger
- **Table:** `cr950_apparatuses`
- **Event:** Update
- **Condition:** `cr950_apparatusstatus` changed to "Complete" (value: 2)

### Flow Logic
```
TRIGGER: When Apparatus is modified

CONDITION: 
  cr950_apparatusstatus equals 2 (Complete)
  AND cr950_apparatusstatus changed

ACTIONS:
  // 1. Get Apparatus details
  apparatus = triggerBody()
  apparatus_id = apparatus['cr950_apparatusid']
  planned_hours = apparatus['cr950_apparatustotalhours']
  task_id = apparatus['_cr950_task_id_value']
  
  // 2. Navigate to get Scope and ScopeLaborDetail
  task = GET cr950_tasks(task_id)
  scope_id = task['_cr950_scope_id_value']
  
  scopelabor = GET cr950_scopelabordetails 
    WHERE cr950_scope_id = scope_id
  
  effective_rate = scopelabor['cr950_scopelaboreffectiverate']
  scopelabor_id = scopelabor['cr950_scopelabordetailid']
  
  // 3. Check if ApparatusRevenue exists
  existing = GET cr950_apparatusrevenue 
    WHERE cr950_apparatus_id = apparatus_id
  
  IF existing IS NULL THEN
    // 4a. Create new ApparatusRevenue
    CREATE cr950_apparatusrevenue
    SET
      cr950_name = apparatus['cr950_apparatusname'] + " - Revenue",
      cr950_apparatus_id = apparatus_id,
      cr950_scopelabordetail_id = scopelabor_id,
      cr950_plannedhours = planned_hours,
      cr950_delayhours = 0,
      cr950_laborrateapplied = effective_rate,
      cr950_revenuestatus = 3,  // Recognized
      cr950_recognitiondate = utcNow()
  ELSE
    // 4b. Update existing to Recognized
    UPDATE cr950_apparatusrevenue(existing.id)
    SET
      cr950_laborrateapplied = effective_rate,
      cr950_revenuestatus = 3,  // Recognized
      cr950_recognitiondate = utcNow()
  END IF
  
  // 5. (Optional) Log audit event
  // CREATE audit log entry for revenue recognition
```

### Validation Example
```
Apparatus Completed:
  Name: "15kV Switchgear Panel 1"
  Planned Hours: 45.5 hrs
  Delay Hours: 2.0 hrs (added during work)
  
ScopeLaborDetail Lookup:
  Effective Rate: $454.51/hr
  
ApparatusRevenue Created:
  Actual Hours: 45.5 + 2.0 = 47.5 hrs
  Revenue Amount: 47.5 × $454.51 = $21,589.23 ⭐
  Status: Recognized
  Recognition Date: 2025-12-02T14:30:00Z
```

---

## 🏗️ TABLE 2: ScopeFinancialSummary

### Purpose
Aggregate all apparatus revenues within a scope. Provides scope-level financial visibility without cluttering the operational Scope table.

### Schema: `cr950_scopefinancialsummary`
**Display Name:** Scope Financial Summary  
**Plural Name:** Scope Financial Summaries  
**Description:** Financial metrics aggregated at Scope level (separation from operations)

### Fields

| # | Display Name | Schema Name | Type | Description |
|---|--------------|-------------|------|-------------|
| 1 | Name | `cr950_name` | Text (100) | Auto: "{Scope Name} - Financials" |
| 2 | Scope | `cr950_scope_id` | Lookup | 1:1 link to Scope (required) |
| 3 | Scope Labor Detail | `cr950_scopelabordetail_id` | Lookup | Link to rate configuration |
| 4 | Apparatus Revenue Count | `cr950_apparatusrevenuecount` | Rollup | COUNT of ApparatusRevenue |
| 5 | Total Planned Hours | `cr950_totalplannedhours` | Rollup | SUM of planned_hours |
| 6 | Total Delay Hours | `cr950_totaldelayhours` | Rollup | SUM of delay_hours |
| 7 | Total Actual Hours | `cr950_totalactualhours` | Rollup | SUM of actual_hours |
| 8 | Total Revenue Pending | `cr950_totalrevenuepending` | Rollup | SUM WHERE status != Recognized |
| 9 | Total Revenue Recognized | `cr950_totalrevenuerecognized` | Rollup | SUM WHERE status = Recognized |
| 10 | Average Labor Rate | `cr950_averagelaborrate` | Calculated | revenue / hours |
| 11 | Estimated Revenue | `cr950_estimatedrevenue` | Calculated | From ScopeLaborDetail |
| 12 | Revenue Variance | `cr950_revenuevariance` | Calculated | Actual - Estimated |
| 13 | Variance Percent | `cr950_variancepercent` | Calculated | (Variance / Estimated) × 100 |
| 14 | Latest Revenue Date | `cr950_latestrevenue_date` | Rollup | MAX of recognition_date |
| 15 | Project Financial Summary | `cr950_projectfinancialsummary_id` | Lookup | For project rollup |

### Rollup Field Definitions

**Apparatus Revenue Count:**
```xml
<fetch>
  <entity name="cr950_apparatusrevenue">
    <attribute name="cr950_apparatusrevenueid" aggregate="count" alias="count"/>
    <filter>
      <condition attribute="cr950_scopefinancialsummary_id" operator="eq" value="{ID}"/>
    </filter>
  </entity>
</fetch>
```

**Total Revenue Recognized:**
```xml
<fetch>
  <entity name="cr950_apparatusrevenue">
    <attribute name="cr950_revenueamount" aggregate="sum" alias="total"/>
    <filter>
      <condition attribute="cr950_scopefinancialsummary_id" operator="eq" value="{ID}"/>
      <condition attribute="cr950_revenuestatus" operator="eq" value="3"/>
    </filter>
  </entity>
</fetch>
```

---

## 🏗️ TABLE 3: ProjectFinancialSummary

### Purpose
Aggregate all scope financials within a project. Executive-level financial dashboard.

### Schema: `cr950_projectfinancialsummary`
**Display Name:** Project Financial Summary  
**Plural Name:** Project Financial Summaries  
**Description:** Financial metrics aggregated at Project level (separation from operations)

### Fields

| # | Display Name | Schema Name | Type | Description |
|---|--------------|-------------|------|-------------|
| 1 | Name | `cr950_name` | Text (100) | Auto: "{Project Name} - Financials" |
| 2 | Project | `cr950_project_id` | Lookup | 1:1 link to Project (required) |
| 3 | Scope Count | `cr950_scopecount` | Rollup | COUNT of ScopeFinancialSummary |
| 4 | Apparatus Revenue Count | `cr950_apparatusrevenuecount` | Rollup | SUM of scope counts |
| 5 | Total Project Hours | `cr950_totalprojecthours` | Rollup | SUM of actual_hours |
| 6 | Total Revenue Pending | `cr950_totalrevenuepending` | Rollup | SUM of scope pending |
| 7 | Total Revenue Recognized | `cr950_totalrevenuerecognized` | Rollup | SUM of scope recognized |
| 8 | Total Estimated Revenue | `cr950_totalestimatedrevenue` | Rollup | SUM of scope estimates |
| 9 | Total Variance | `cr950_totalvariance` | Calculated | Recognized - Estimated |
| 10 | Variance Percent | `cr950_variancepercent` | Calculated | (Variance / Estimated) × 100 |
| 11 | Average Effective Rate | `cr950_averageeffectiverate` | Calculated | revenue / hours |
| 12 | Latest Revenue Date | `cr950_latestrevenue_date` | Rollup | MAX across scopes |

---

## 🔄 FLOW 3: Auto-Create Financial Summary Records

### Purpose
Automatically create ScopeFinancialSummary and ProjectFinancialSummary when operational records are created.

### Flow 3a: Create ScopeFinancialSummary
```
TRIGGER: When Scope is created

ACTIONS:
  scope = triggerBody()
  scope_id = scope['cr950_scopeid']
  scope_name = scope['cr950_scopename']
  project_id = scope['_cr950_project_id_value']
  
  // Get or create ProjectFinancialSummary
  project_fin = GET cr950_projectfinancialsummary
    WHERE cr950_project_id = project_id
  
  IF project_fin IS NULL THEN
    project = GET cr950_projects(project_id)
    project_fin = CREATE cr950_projectfinancialsummary
    SET
      cr950_name = project['cr950_projectname'] + " - Financials",
      cr950_project_id = project_id
  END IF
  
  // Create ScopeFinancialSummary
  CREATE cr950_scopefinancialsummary
  SET
    cr950_name = scope_name + " - Financials",
    cr950_scope_id = scope_id,
    cr950_projectfinancialsummary_id = project_fin.id
```

### Flow 3b: Link ScopeLaborDetail to Financial Summary
```
TRIGGER: When ScopeLaborDetail is created

ACTIONS:
  scopelabor = triggerBody()
  scope_id = scopelabor['_cr950_scope_id_value']
  
  // Find ScopeFinancialSummary
  scope_fin = GET cr950_scopefinancialsummary
    WHERE cr950_scope_id = scope_id
  
  IF scope_fin IS NOT NULL THEN
    UPDATE cr950_scopefinancialsummary(scope_fin.id)
    SET
      cr950_scopelabordetail_id = scopelabor['cr950_scopelabordetailid']
  END IF
```

---

## 📊 Security Model

### Role: Finance
| Table | Create | Read | Update | Delete |
|-------|--------|------|--------|--------|
| ApparatusRevenue | ✅ | ✅ | ✅ | ❌ |
| ScopeFinancialSummary | ✅ | ✅ | ✅ | ❌ |
| ProjectFinancialSummary | ✅ | ✅ | ✅ | ❌ |
| ScopeLaborDetail | ✅ | ✅ | ✅ | ❌ |

### Role: Operations/Field
| Table | Create | Read | Update | Delete |
|-------|--------|------|--------|--------|
| ApparatusRevenue | ❌ | ❌ | ❌ | ❌ |
| ScopeFinancialSummary | ❌ | ❌ | ❌ | ❌ |
| ProjectFinancialSummary | ❌ | ❌ | ❌ | ❌ |
| ScopeLaborDetail | ❌ | View Only | ❌ | ❌ |

### Role: Project Manager
| Table | Create | Read | Update | Delete |
|-------|--------|------|--------|--------|
| ApparatusRevenue | ❌ | ✅ | ❌ | ❌ |
| ScopeFinancialSummary | ❌ | ✅ | ❌ | ❌ |
| ProjectFinancialSummary | ❌ | ✅ | ❌ | ❌ |
| ScopeLaborDetail | ❌ | ✅ | ❌ | ❌ |

---

## 🛠️ Implementation Order

### Phase 1: Tables (Day 1)
1. ✅ ScopeLaborDetail already exists
2. Create `cr950_apparatusrevenue` table
3. Create `cr950_scopefinancialsummary` table
4. Create `cr950_projectfinancialsummary` table

### Phase 2: Flows (Day 1-2)
1. Build Flow 1: ScopeLaborDetail Rate Calculation
2. Build Flow 3a: Auto-create Financial Summary on Scope create
3. Build Flow 3b: Link ScopeLaborDetail to Financial Summary

### Phase 3: Revenue Recognition (Day 2)
1. Build Flow 2: Revenue Recognition on Apparatus Complete
2. Test with sample apparatus completion

### Phase 4: Rollups (Day 2-3)
1. Configure rollup fields on ScopeFinancialSummary
2. Configure rollup fields on ProjectFinancialSummary
3. Test rollup calculations

### Phase 5: Views & Dashboards (Day 3)
1. Create Finance dashboard view
2. Create Revenue by Scope view
3. Create Revenue by Project view

---

## ✅ Validation Checklist

### Import Test
- [ ] JSON import creates ScopeLaborDetail
- [ ] Flow 1 calculates rates automatically
- [ ] Flow 3 creates Financial Summary records

### Revenue Recognition Test
- [ ] Mark apparatus as Complete
- [ ] Flow 2 creates ApparatusRevenue
- [ ] Revenue amount calculated correctly
- [ ] ScopeFinancialSummary rollups update
- [ ] ProjectFinancialSummary rollups update

### End-to-End Test
```
Import: 4 scopes, 56 apparatus
  → 4 ScopeLaborDetail (with calculated rates)
  → 4 ScopeFinancialSummary (auto-created)
  → 1 ProjectFinancialSummary (auto-created)

Complete: 10 apparatus
  → 10 ApparatusRevenue records
  → ScopeFinancialSummary totals update
  → ProjectFinancialSummary totals update
```

---

## 📎 Related Documents

- `REVENUE_ARCHITECTURE.md` - Four-tier architecture overview
- `SESSION_TRANSCRIPT_2025-12-01.md` - Original discussion
- `KPI_FIELDS_README.md` - Previous implementation scripts
- `TABLE_NAMES_REFERENCE.md` - Schema naming conventions

---

**Build Spec Status:** APPROVED FOR BUILD  
**Created:** December 2, 2025  
**Approved By:** [User confirmation in chat]
