# V1.5.1.3 Field Reference

**Generated:** December 5, 2025  
**Purpose:** Validation reference for Desktop Claude's DATA_DICTIONARY.md  
**Source:** Solution_Exports/Archive/v1.5.1.3/customizations.xml  
**Author:** VS Code Claude (corrected)

---

## Entities in Dataverse v1.5.1.3

| # | Dataverse Entity | PostgreSQL Table | Category |
|---|------------------|------------------|----------|
| 1 | cr950_Apparatus | apparatus | Core |
| 2 | cr950_ApparatusRevenue | apparatus_revenue | Financial |
| 3 | cr950_apparatussubmission | apparatus_submissions | Workflow (Phase 2?) |
| 4 | cr950_apparatustestchecklist | apparatus_test_checklists | QA (Phase 2?) |
| 5 | cr950_ApparatusTypeMaster | apparatus_types | Reference |
| 6 | cr950_BusinessUnit | locations | Core |
| 7 | cr950_Client | clients | Core |
| 8 | cr950_Employee | employees | Core |
| 9 | cr950_Equipment | equipment | Core |
| 10 | cr950_estimator | estimators | Financial |
| 11 | cr950_netatesttemplate | neta_test_templates | Reference |
| 12 | cr950_projectfinancialsummary | project_financial_summaries | Financial |
| 13 | cr950_Projects | projects | Core |
| 14 | cr950_ProjectScope | scopes | Core |
| 15 | cr950_Quote | quotes | Financial (Phase 2?) |
| 16 | cr950_ResourceAssignment | resource_assignments | Core |
| 17 | cr950_scopefinancialsummary | scope_financial_summaries | Financial |
| 18 | cr950_scopelabordetails | scope_labor_details | Financial |
| 19 | cr950_Site | sites | Core |
| 20 | cr950_Tasks | tasks | Core |

---

## PSS Tables (NEW - Not in Dataverse)

| # | PostgreSQL Table | Purpose |
|---|------------------|---------|
| 21 | pss_studies | Power system studies |
| 22 | pss_documents | Study documents |
| 23 | pss_document_templates | Document templates |
| 24 | pss_rfis | Requests for information |
| 25 | pss_activity_log | Audit trail |
| 26 | pss_engineers | External engineers |

---

## Phase 1 Target: 25 Tables

**Core (10):** clients, sites, locations, employees, projects, scopes, tasks, apparatus, equipment, resource_assignments

**Financial (6):** estimators, scope_labor_details, apparatus_revenue, scope_financial_summaries, project_financial_summaries, neta_test_templates

**Reference (1):** apparatus_types

**PSS Portal (6):** pss_studies, pss_documents, pss_document_templates, pss_rfis, pss_activity_log, pss_engineers

**Deferred to Phase 2 (3):** apparatus_submissions, apparatus_test_checklists, quotes

---

## Field Naming Convention

| Dataverse Pattern | PostgreSQL Pattern | Example |
|-------------------|-------------------|---------|
| cr950_fieldname | field_name | cr950_projectnumber → project_number |
| PascalCase | snake_case | ActualStart → actual_start |
| Lookup (cr950_xxxid) | _id foreign key | cr950_projectid → project_id |
| OptionSet | ENUM type | cr950_status → project_status ENUM |
| Currency | DECIMAL(15,2) | Revenue fields |
| Rollup/Calculated | Trigger-computed | Counts, totals, percentages |

---

## Validation Checklist

- [ ] All 20 Dataverse entities reviewed
- [ ] 17 tables included in Phase 1
- [ ] 3 tables deferred to Phase 2
- [ ] 6 PSS tables defined
- [ ] Field names use snake_case
- [ ] Lookups → foreign keys
- [ ] OptionSets → ENUMs
- [ ] Rollups → triggers documented

