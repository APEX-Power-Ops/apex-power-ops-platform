# Test Data Generation Plan

**Purpose:** Structure for Phase 2 test data generation  
**Owner:** VS Code Claude  
**Status:** TEMPLATE READY - Awaiting schema completion

---

## Test Data Strategy

### Primary Test Project: LASNAP16
**Real project data available in:** `LASNAP16/RESA Power - LASNAP16 MASTER.xlsm`

| Entity | Record Count | Source |
|--------|--------------|--------|
| clients | 1 | LASNAP16 customer |
| sites | 1 | LASNAP16 site |
| projects | 1 | LASNAP16 project |
| scopes | 4 | Per LASNAP16 scope breakdown |
| tasks | 12 | Per LASNAP16 task structure |
| apparatus | 47 | Per LASNAP16 equipment list |
| apparatus_revenue | 47 | One per apparatus |
| employees | 5 | Sample RESA staff |
| resource_assignments | 8 | Sample assignments |

### PSS Test Data: 5 Studies
| Entity | Record Count | Notes |
|--------|--------------|-------|
| pss_engineers | 3 | Sample external engineers |
| pss_studies | 5 | Various status states |
| pss_documents | 15 | 3 per study average |
| pss_document_templates | 8 | Standard document types |
| pss_rfis | 10 | 2 per study average |
| pss_activity_log | 25 | Audit trail entries |

---

## Seed Data (Reference Tables)

### apparatus_types
**Source:** `CSV_Templates/04_Apparatus_Type_Master.csv`
- Transformer types
- Circuit breaker types
- Switchgear types
- Relay types
- Cable types
- etc.

### neta_test_templates
**Source:** NETA MTS standards
- Section 7.2 - Transformers
- Section 7.3 - Switchgear
- Section 7.4 - Circuit Breakers
- Section 7.5 - Protective Relays
- etc.

### locations (RESA branches)
- Fenton, MO (headquarters)
- Dallas, TX
- Houston, TX
- Phoenix, AZ
- Atlanta, GA

### estimators (rate configurations)
- Standard field rate
- Overtime rate
- Travel rate
- Emergency rate

---

## Data Relationships to Test

### Hierarchy Integrity
```
locations
    └── projects
        └── scopes
            └── tasks
                └── apparatus
                    └── apparatus_revenue
```

### Cross-References
```
clients ──→ sites ──→ projects
employees ──→ resource_assignments ──→ projects/scopes
apparatus_types ──→ apparatus
neta_test_templates ──→ apparatus_types
```

### PSS Relationships
```
projects ──→ pss_studies
pss_engineers ──→ pss_studies
pss_studies ──→ pss_documents
pss_studies ──→ pss_rfis
pss_studies ──→ pss_activity_log
pss_document_templates ──→ pss_documents
```

---

## Test Scenarios to Cover

### Status Transitions
- [ ] Project NOT_STARTED → IN_PROGRESS → COMPLETED
- [ ] Apparatus PLANNED → IN_PROGRESS → COMPLETE
- [ ] PSS Study PENDING → IN_PROGRESS → COMPLETED

### Rollup Calculations
- [ ] Task apparatus_count updates from apparatus INSERT
- [ ] Scope total_hours updates from task changes
- [ ] Project percent_complete updates from apparatus completion
- [ ] Financial rollups cascade correctly

### Revenue Recognition
- [ ] Apparatus completion triggers revenue record creation
- [ ] Revenue amounts match scope_labor_details rates
- [ ] Delay hours calculated correctly
- [ ] Financial summary rollups accurate

---

## File Generation Order

| # | File | Dependencies | Content |
|---|------|--------------|---------|
| 10 | 10_seed_data.sql | Schema complete | Reference tables |
| 11 | 11_test_data.sql | 10_seed_data.sql | LASNAP16 project |
| 12 | 12_pss_test_data.sql | 11_test_data.sql | PSS portal data |

---

## UUID Strategy

Generate predictable UUIDs for test data to enable:
- FK reference integrity
- Easy debugging
- Repeatable test runs

**Pattern:** `{entity_prefix}-0000-0000-0000-{sequential_id}`

Examples:
```sql
'11111111-0000-0000-0000-000000000001'  -- client 1
'22222222-0000-0000-0000-000000000001'  -- site 1
'33333333-0000-0000-0000-000000000001'  -- project 1
'44444444-0000-0000-0000-000000000001'  -- scope 1
'55555555-0000-0000-0000-000000000001'  -- task 1
'66666666-0000-0000-0000-000000000001'  -- apparatus 1
```

---

## Validation Queries to Include

```sql
-- Verify rollup accuracy
SELECT p.project_number, 
       p.total_apparatus_count,
       (SELECT COUNT(*) FROM apparatus a 
        JOIN tasks t ON a.task_id = t.id 
        JOIN scopes s ON t.scope_id = s.id 
        WHERE s.project_id = p.id) as actual_count
FROM projects p;

-- Verify FK integrity
SELECT 'orphan_apparatus' as check, COUNT(*) 
FROM apparatus WHERE task_id NOT IN (SELECT id FROM tasks)
UNION ALL
SELECT 'orphan_tasks', COUNT(*) 
FROM tasks WHERE scope_id NOT IN (SELECT id FROM scopes);
```

---

*Test data plan ready | VS Code Claude | December 5, 2025*
*Awaiting: Schema completion before generating SQL files*
