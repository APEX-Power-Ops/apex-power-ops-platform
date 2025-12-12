# Excel → Database Field Mapping

**Source**: `Garney- Central Mesa Reuse Tracker #677562.xlsm` (`tbl_PowerBI_Data`)  
**Generated**: 2025-12-11  
**Purpose**: Define how Excel tracker fields map to Supabase schema

---

## Core Identity Fields

| Excel Column | Database Table.Column | Transform | Notes |
|--------------|----------------------|-----------|-------|
| Scope | `scopes.scope_name` | Lookup/create | e.g., "IPS" |
| NETA_Standard | `apparatus.neta_procedure_id` | Lookup by code | e.g., "ATS" → NETA procedure |
| Task_ID | `apparatus.task_number` | Direct | Hierarchical: "1.1.1" |
| Task | `tasks.task_name` | Lookup/create | e.g., "SES-00-001" |
| Apparatus | `apparatus_types.name` | Lookup | e.g., "Circuit Breaker" |
| Designation | `apparatus.designation` | Direct | Equipment ID |
| Drawing | `apparatus.drawing_reference` | Direct | Drawing reference |

## Status & Tracking Fields

| Excel Column | Database Table.Column | Transform | Values |
|--------------|----------------------|-----------|--------|
| STATUS | `apparatus.status` | Case normalize | COMPLETED→Complete, NOT STARTED→Not Started |
| AVAILABILITY | `apparatus.availability` | Case normalize | READY→Ready, ON HOLD→On Hold, NOT AVAILABLE→Not Available |
| Assessment | `apparatus.assessment` | Case normalize | ACCEPTABLE→Acceptable, NON-SERVICEABLE→Non-Serviceable |
| DATASHEET | `apparatus.datasheet_complete` | Boolean | true/false |
| % COMPLETION | `apparatus.percent_complete` | Multiply by 100 | 1 → 100% |
| TASK DELAYS | `apparatus.task_delays` | Integer | Count of delays |
| PRIORITY | `apparatus.priority` | Integer | 1=High, 2=Med, 3=Low |

## Date Fields

| Excel Column | Database Table.Column | Transform | Notes |
|--------------|----------------------|-----------|-------|
| Date Due | `apparatus.date_due` | Excel serial → DATE | 46027 → 2026-01-15 |
| DATE COMPLETED | `apparatus.actual_end` | Excel serial → DATE | |
| Week_Ending | **Calculated** | Not stored | Derived from actual_end |
| Billing_Period | **Calculated** | Not stored | Derived from actual_end |

## Hours & Labor Fields

| Excel Column | Database Table.Column | Transform | Notes |
|--------------|----------------------|-----------|-------|
| Apparatus Hours | `apparatus.quoted_hours` | Direct | Estimated hours |
| Remaining Hours | **Calculated** | Not stored | quoted_hours - actual_hours |
| ACTUAL HOURS | `apparatus.actual_hours` | Direct | |

## Notes Fields

| Excel Column | Database Table.Column | Transform | Notes |
|--------------|----------------------|-----------|-------|
| Notes | `apparatus.notes` | Direct | Primary notes field |
| Notes2 | — | Ignore | Duplicate of Notes |

## Billing/Financial Fields (Scope-Level)

| Excel Column | Database Table.Column | Transform | Notes |
|--------------|----------------------|-----------|-------|
| Base_Rate | `scope_billing.labor_rate` | Direct | $165/hr typical |
| Scope_Budget | `scopes.quoted_revenue` | Direct | Total scope budget |
| Multiplier | `scope_billing.multiplier` | Direct | Rate multiplier |
| Scope_Helper | — | **Not stored** | Excel helper column |

### Calculated Billing Columns (Not Stored)

These columns are **calculated** in Excel and should be **derived via views** in the database:

- `Completion` - boolean/percentage
- `Base_Labor_$` - quoted_hours × rate × completion
- `Commute_Hrs`, `Commute_$` - From billing rules
- `PM_Hrs`, `PM_$` - From billing rules
- `Report_Hrs`, `Report_$` - From billing rules
- `Travel_Hrs`, `Travel_$` - From billing rules
- `Final_Hrs`, `Final_$` - From billing rules
- `Travel_Fixed_$`, `ME_Fixed_$` - Fixed costs
- `Total_Var_Hrs`, `Total_Var_$` - Sum of variable
- `Total_Fixed_$` - Sum of fixed
- `Subtotal_$`, `Total_Billable_$` - Grand totals

---

## Rollup Date Architecture

The Excel tracker calculates these at scope level. In the database, we compute them via views:

```
PROJECT LEVEL (v_project_rollup_dates)
├── earliest_scope_start    = MIN(scopes.actual_start)
├── latest_scope_complete   = MAX(scopes.actual_end)
├── earliest_apparatus_due  = MIN(apparatus.date_due)
├── latest_apparatus_due    = MAX(apparatus.date_due)
└── calculated_percent      = completed_apparatus / total_apparatus

SCOPE LEVEL (v_scope_rollup_dates)
├── earliest_task_start     = MIN(tasks.actual_start)
├── latest_task_complete    = MAX(tasks.actual_end)
├── earliest_apparatus_due  = MIN(apparatus.date_due)
├── latest_apparatus_due    = MAX(apparatus.date_due)
└── completed_apparatus     = COUNT WHERE status='Complete'

TASK LEVEL (v_task_rollup_dates)
├── earliest_apparatus_due  = MIN(apparatus.date_due)
├── latest_apparatus_due    = MAX(apparatus.date_due)
├── earliest_apparatus_start = MIN(apparatus.actual_start)
└── latest_apparatus_complete = MAX(apparatus.actual_end)
```

---

## Value Transformations

### Status Normalization
```javascript
function normalizeStatus(excelValue) {
  const map = {
    'COMPLETED': 'Complete',
    'NOT STARTED': 'Not Started',
    'IN PROGRESS': 'In Progress',
    '': 'Not Started'
  };
  return map[excelValue?.toUpperCase()] || 'Not Started';
}
```

### Availability Normalization
```javascript
function normalizeAvailability(excelValue) {
  const map = {
    'READY': 'Ready',
    'ON HOLD': 'On Hold',
    'NOT AVAILABLE': 'Not Available',
    '': 'Not Available'
  };
  return map[excelValue?.toUpperCase()] || 'Not Available';
}
```

### Assessment Normalization
```javascript
function normalizeAssessment(excelValue) {
  const map = {
    'ACCEPTABLE': 'Acceptable',
    'NON-SERVICEABLE': 'Non-Serviceable',
    'MINOR DEFICIENCY': 'Minor Deficiency',
    '': null
  };
  return map[excelValue?.toUpperCase()] ?? null;
}
```

### Excel Date Conversion
```javascript
function excelDateToISO(excelSerial) {
  if (!excelSerial) return null;
  // Excel dates start from 1900-01-01 (serial 1)
  // But Excel has a bug treating 1900 as leap year, so subtract 1 for dates after Feb 28 1900
  const date = new Date((excelSerial - 25569) * 86400 * 1000);
  return date.toISOString().split('T')[0];
}
```

---

## Import Priority

### Phase 1: Core Fields (Required for visibility)
1. ✅ Scope, Task, Apparatus type lookups
2. ✅ Status, Availability, Assessment
3. ✅ Date Due, Dates Started/Completed
4. ✅ Hours (quoted, actual)
5. ✅ Notes

### Phase 2: Enhanced Fields
- Designation, Drawing reference
- Datasheet complete, Task delays
- Priority

### Phase 3: Financial Integration
- Scope billing configuration
- Revenue calculations (via views)

---

## Dashboard Views Enabled

With this schema, these dashboard views become possible:

| View | Purpose | Key Fields |
|------|---------|------------|
| `v_apparatus_operational` | Daily work scheduling | status, availability, date_due |
| `v_schedule_health` | At-risk identification | overdue_items, on_hold_items |
| `v_project_rollup_dates` | Executive summary | calculated_percent, date spreads |
| `v_scope_rollup_dates` | PM view | task/apparatus rollups |

---

## Next Steps

1. [ ] Deploy `09_schema_additions.sql` to Supabase
2. [ ] Update import function to handle new fields
3. [ ] Create billing configuration table if needed
4. [ ] Build dashboard views in web app
5. [ ] Test with Garney tracker data
