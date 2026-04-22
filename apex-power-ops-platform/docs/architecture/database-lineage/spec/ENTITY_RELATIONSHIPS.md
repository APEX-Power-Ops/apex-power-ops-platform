# Entity Relationships

**Version:** 1.0.0  
**Created:** December 5, 2025  
**Author:** Desktop Claude  
**Purpose:** Foreign key relationships and entity hierarchy documentation

---

## Relationship Overview

The RESA Power schema follows a hierarchical structure with three main domains:

1. **Organization Hierarchy:** locations → clients → sites
2. **Project Hierarchy:** projects → scopes → tasks → apparatus
3. **PSS Portal:** projects → pss_studies → documents/rfis/activity

---

## Visual Diagrams

### Core Project Hierarchy

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  locations  │      │   clients   │──────│    sites    │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       │                    └─────────┬──────────┘
       │                              │
       ▼                              ▼
┌─────────────────────────────────────────────────────┐
│                      projects                        │
│  (location_id, client_id, site_id)                  │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                       scopes                         │
│  (project_id, client_id, site_id)                   │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                       tasks                          │
│  (scope_id, parent_task_id)                         │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                     apparatus                        │
│  (scope_id, task_id)                                │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  apparatus_revenue                   │
│  (apparatus_id, scope_id)                           │
└─────────────────────────────────────────────────────┘
```

### Financial Rollup Structure

```
┌─────────────────────────────────────────────────────┐
│              project_financial_summaries             │
│  (project_id UNIQUE)                                │
└──────────────────────────▲──────────────────────────┘
                           │ Aggregates from
                           │
┌─────────────────────────────────────────────────────┐
│              scope_financial_summaries               │
│  (scope_id UNIQUE)                                  │
└──────────────────────────▲──────────────────────────┘
                           │ Aggregates from
                           │
           ┌───────────────┴───────────────┐
           │                               │
┌──────────┴──────────┐       ┌────────────┴────────────┐
│  scope_labor_details │       │    apparatus_revenue    │
│  (scope_id)          │       │  (apparatus_id, scope_id)│
└─────────────────────┘       └─────────────────────────┘
```

### PSS Portal Structure

```
┌─────────────┐
│  projects   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│                    pss_studies                       │
│  (project_id, engineer_id)                          │
└──────────────────────────┬──────────────────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────────┐
│pss_documents│   │  pss_rfis   │   │ pss_activity_log│
│ (study_id)  │   │ (study_id)  │   │   (study_id)    │
└──────┬──────┘   └─────────────┘   └─────────────────┘
       │
       ▼
┌───────────────────────┐
│pss_document_templates │
└───────────────────────┘

┌───────────────────────┐
│    pss_engineers      │───── Referenced by pss_studies
└───────────────────────┘
```

### Employee & Equipment

```
┌─────────────┐
│  locations  │
└──────┬──────┘
       │
       ├──────────────────────────────┐
       ▼                              ▼
┌─────────────┐              ┌─────────────┐
│  employees  │──────────────│  equipment  │
│(location_id)│              │(location_id,│
└──────┬──────┘              │ assigned_   │
       │                     │ employee_id)│
       │                     └─────────────┘
       ▼
┌─────────────────────┐
│ resource_assignments│
│ (employee_id,       │
│  project_id,        │
│  scope_id)          │
└─────────────────────┘
```

---

## Foreign Key Definitions

### Core Tables

#### sites
```sql
ALTER TABLE sites
    ADD CONSTRAINT fk_sites_client
    FOREIGN KEY (client_id) 
    REFERENCES clients(id) 
    ON DELETE CASCADE;
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| client_id | clients(id) | CASCADE | Sites belong to clients |

---

#### projects
```sql
ALTER TABLE projects
    ADD CONSTRAINT fk_projects_client
    FOREIGN KEY (client_id) REFERENCES clients(id),
    
    ADD CONSTRAINT fk_projects_site
    FOREIGN KEY (site_id) REFERENCES sites(id),
    
    ADD CONSTRAINT fk_projects_location
    FOREIGN KEY (location_id) REFERENCES locations(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| client_id | clients(id) | SET NULL | Preserve project if client deleted |
| site_id | sites(id) | SET NULL | Preserve project if site deleted |
| location_id | locations(id) | SET NULL | Preserve project if location deleted |

---

#### scopes
```sql
ALTER TABLE scopes
    ADD CONSTRAINT fk_scopes_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(id) 
    ON DELETE CASCADE,
    
    ADD CONSTRAINT fk_scopes_client
    FOREIGN KEY (client_id) REFERENCES clients(id),
    
    ADD CONSTRAINT fk_scopes_site
    FOREIGN KEY (site_id) REFERENCES sites(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| project_id | projects(id) | CASCADE | Scopes are children of projects |
| client_id | clients(id) | SET NULL | Denormalized reference |
| site_id | sites(id) | SET NULL | Denormalized reference |

---

#### tasks
```sql
ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id) 
    ON DELETE CASCADE,
    
    ADD CONSTRAINT fk_tasks_parent
    FOREIGN KEY (parent_task_id) 
    REFERENCES tasks(id) 
    ON DELETE SET NULL;
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| scope_id | scopes(id) | CASCADE | Tasks are children of scopes |
| parent_task_id | tasks(id) | SET NULL | Preserve child if parent deleted |

---

#### apparatus
```sql
ALTER TABLE apparatus
    ADD CONSTRAINT fk_apparatus_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id) 
    ON DELETE CASCADE,
    
    ADD CONSTRAINT fk_apparatus_task
    FOREIGN KEY (task_id) 
    REFERENCES tasks(id) 
    ON DELETE SET NULL;
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| scope_id | scopes(id) | CASCADE | Apparatus belongs to scope |
| task_id | tasks(id) | SET NULL | Apparatus can exist without task |

---

### Financial Tables

#### apparatus_revenue
```sql
ALTER TABLE apparatus_revenue
    ADD CONSTRAINT fk_apparatus_revenue_apparatus
    FOREIGN KEY (apparatus_id) 
    REFERENCES apparatus(id) 
    ON DELETE CASCADE,
    
    ADD CONSTRAINT fk_apparatus_revenue_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| apparatus_id | apparatus(id) | CASCADE | Revenue tied to apparatus |
| scope_id | scopes(id) | SET NULL | Denormalized reference |

---

#### scope_labor_details
```sql
ALTER TABLE scope_labor_details
    ADD CONSTRAINT fk_scope_labor_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id) 
    ON DELETE CASCADE;
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| scope_id | scopes(id) | CASCADE | Labor details belong to scope |

---

#### scope_financial_summaries
```sql
ALTER TABLE scope_financial_summaries
    ADD CONSTRAINT fk_scope_financial_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id) 
    ON DELETE CASCADE;
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| scope_id | scopes(id) | CASCADE | One summary per scope |

---

#### project_financial_summaries
```sql
ALTER TABLE project_financial_summaries
    ADD CONSTRAINT fk_project_financial_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(id) 
    ON DELETE CASCADE;
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| project_id | projects(id) | CASCADE | One summary per project |

---

### Employee/Resource Tables

#### employees
```sql
ALTER TABLE employees
    ADD CONSTRAINT fk_employees_location
    FOREIGN KEY (location_id) 
    REFERENCES locations(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| location_id | locations(id) | SET NULL | Employee can exist without location |

---

#### equipment
```sql
ALTER TABLE equipment
    ADD CONSTRAINT fk_equipment_location
    FOREIGN KEY (location_id) 
    REFERENCES locations(id),
    
    ADD CONSTRAINT fk_equipment_employee
    FOREIGN KEY (assigned_employee_id) 
    REFERENCES employees(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| location_id | locations(id) | SET NULL | Equipment can exist without location |
| assigned_employee_id | employees(id) | SET NULL | Equipment can be unassigned |

---

#### resource_assignments
```sql
ALTER TABLE resource_assignments
    ADD CONSTRAINT fk_resource_employee
    FOREIGN KEY (employee_id) 
    REFERENCES employees(id),
    
    ADD CONSTRAINT fk_resource_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(id),
    
    ADD CONSTRAINT fk_resource_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| employee_id | employees(id) | CASCADE | Assignment requires employee |
| project_id | projects(id) | CASCADE | Delete assignment if project deleted |
| scope_id | scopes(id) | SET NULL | Assignment can be project-level |

---

### PSS Portal Tables

#### pss_studies
```sql
ALTER TABLE pss_studies
    ADD CONSTRAINT fk_pss_studies_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(id),
    
    ADD CONSTRAINT fk_pss_studies_engineer
    FOREIGN KEY (engineer_id) 
    REFERENCES pss_engineers(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| project_id | projects(id) | SET NULL | Study can exist without project |
| engineer_id | pss_engineers(id) | SET NULL | Study can be unassigned |

---

#### pss_documents
```sql
ALTER TABLE pss_documents
    ADD CONSTRAINT fk_pss_documents_study
    FOREIGN KEY (study_id) 
    REFERENCES pss_studies(id) 
    ON DELETE CASCADE,
    
    ADD CONSTRAINT fk_pss_documents_template
    FOREIGN KEY (template_id) 
    REFERENCES pss_document_templates(id),
    
    ADD CONSTRAINT fk_pss_documents_employee
    FOREIGN KEY (uploaded_by) 
    REFERENCES employees(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| study_id | pss_studies(id) | CASCADE | Documents belong to study |
| template_id | pss_document_templates(id) | SET NULL | Template reference optional |
| uploaded_by | employees(id) | SET NULL | Preserve doc if employee deleted |

---

#### pss_rfis
```sql
ALTER TABLE pss_rfis
    ADD CONSTRAINT fk_pss_rfis_study
    FOREIGN KEY (study_id) 
    REFERENCES pss_studies(id) 
    ON DELETE CASCADE,
    
    ADD CONSTRAINT fk_pss_rfis_requested_by
    FOREIGN KEY (requested_by) 
    REFERENCES employees(id),
    
    ADD CONSTRAINT fk_pss_rfis_assigned_to
    FOREIGN KEY (assigned_to) 
    REFERENCES employees(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| study_id | pss_studies(id) | CASCADE | RFIs belong to study |
| requested_by | employees(id) | SET NULL | Preserve RFI if requester deleted |
| assigned_to | employees(id) | SET NULL | Preserve RFI if assignee deleted |

---

#### pss_activity_log
```sql
ALTER TABLE pss_activity_log
    ADD CONSTRAINT fk_pss_activity_study
    FOREIGN KEY (study_id) 
    REFERENCES pss_studies(id) 
    ON DELETE CASCADE,
    
    ADD CONSTRAINT fk_pss_activity_employee
    FOREIGN KEY (performed_by) 
    REFERENCES employees(id);
```

| FK Column | References | On Delete | Rationale |
|-----------|------------|-----------|-----------|
| study_id | pss_studies(id) | CASCADE | Activity belongs to study |
| performed_by | employees(id) | SET NULL | Preserve log if employee deleted |

---

## Cardinality Summary

| Parent | Child | Cardinality | Notes |
|--------|-------|-------------|-------|
| clients | sites | 1:N | One client, many sites |
| clients | projects | 1:N | One client, many projects |
| sites | projects | 1:N | One site, many projects |
| locations | projects | 1:N | One branch, many projects |
| locations | employees | 1:N | One branch, many employees |
| projects | scopes | 1:N | One project, many scopes |
| scopes | tasks | 1:N | One scope, many tasks |
| scopes | apparatus | 1:N | One scope, many apparatus |
| tasks | apparatus | 1:N | One task, many apparatus |
| tasks | tasks | 1:N | Self-reference for hierarchy |
| apparatus | apparatus_revenue | 1:N | One apparatus, many revenue lines |
| scopes | scope_labor_details | 1:N | One scope, many labor lines |
| scopes | scope_financial_summaries | 1:1 | One summary per scope |
| projects | project_financial_summaries | 1:1 | One summary per project |
| employees | resource_assignments | 1:N | One employee, many assignments |
| employees | equipment | 1:N | One employee, many equipment |
| projects | pss_studies | 1:N | One project, many studies |
| pss_engineers | pss_studies | 1:N | One engineer, many studies |
| pss_studies | pss_documents | 1:N | One study, many documents |
| pss_studies | pss_rfis | 1:N | One study, many RFIs |
| pss_studies | pss_activity_log | 1:N | One study, many activities |

---

## Cascade Behavior Summary

### CASCADE DELETE (Child deleted with parent)
- sites → clients
- scopes → projects
- tasks → scopes
- apparatus → scopes
- apparatus_revenue → apparatus
- scope_labor_details → scopes
- scope_financial_summaries → scopes
- project_financial_summaries → projects
- resource_assignments → employees
- resource_assignments → projects
- pss_documents → pss_studies
- pss_rfis → pss_studies
- pss_activity_log → pss_studies

### SET NULL (Reference cleared, record preserved)
- projects.client_id → clients
- projects.site_id → sites
- projects.location_id → locations
- apparatus.task_id → tasks
- tasks.parent_task_id → tasks
- equipment.location_id → locations
- equipment.assigned_employee_id → employees
- pss_studies.project_id → projects
- pss_studies.engineer_id → pss_engineers
- pss_documents.template_id → pss_document_templates
- pss_documents.uploaded_by → employees
- pss_rfis.requested_by → employees
- pss_rfis.assigned_to → employees
- pss_activity_log.performed_by → employees

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-05 | Desktop Claude | Initial creation |

---

*Entity Relationships v1.0.0 | RESA Power Supabase Migration*
