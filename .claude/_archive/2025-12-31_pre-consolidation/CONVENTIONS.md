# RESA Power - Coding Conventions

**Purpose:** Single source for naming standards and coding conventions  
**Owner:** Both Claudes reference this file  
**Last Updated:** December 5, 2025

---

## PostgreSQL Naming Conventions

### Tables
| Rule | Example |
|------|---------|
| Lowercase | `projects` not `Projects` |
| Snake_case | `scope_labor_details` not `scopelabordetails` |
| Plural for collections | `clients`, `projects`, `tasks` |
| Singular for junction | `resource_assignment` (if 1:1) |

### Columns
| Rule | Example |
|------|---------|
| Lowercase snake_case | `project_number`, `created_at` |
| Primary key | `id` (UUID type) |
| Foreign key | `{table_singular}_id` → `project_id`, `scope_id` |
| Timestamps | `created_at`, `updated_at` (TIMESTAMPTZ) |
| Booleans | `is_` or `has_` prefix → `is_active`, `has_delay` |
| Counts | `_count` suffix → `apparatus_count`, `completed_count` |
| Totals | `total_` prefix → `total_hours`, `total_revenue` |

### ENUMs
| Rule | Example |
|------|---------|
| Lowercase snake_case | `project_status`, `completion_status` |
| Values UPPERCASE | `'NOT_STARTED'`, `'IN_PROGRESS'`, `'COMPLETED'` |
| Suffix `_status` or `_type` | `scope_type`, `task_type` |

### Triggers & Functions
| Rule | Example |
|------|---------|
| Verb prefix | `update_`, `calculate_`, `create_` |
| Descriptive name | `update_task_rollups`, `create_revenue_on_completion` |
| Trigger suffix | `_trigger` → `apparatus_after_update_trigger` |

### Views
| Rule | Example |
|------|---------|
| Prefix `v_` | `v_project_dashboard`, `v_scope_summary` |
| Descriptive purpose | `v_apparatus_completion_report` |

### Indexes
| Rule | Example |
|------|---------|
| Prefix `idx_` | `idx_apparatus_task_id` |
| Table + column(s) | `idx_projects_status`, `idx_tasks_scope_id_status` |

---

## Dataverse → PostgreSQL Mapping

| Dataverse Pattern | PostgreSQL Pattern |
|-------------------|-------------------|
| `cr950_fieldname` | `field_name` |
| `cr950_Projects` | `projects` |
| `cr950_ProjectScope` | `scopes` |
| `cr950_projectid` (lookup) | `project_id` (FK) |
| OptionSet | ENUM type |
| Currency | `DECIMAL(15,2)` |
| Whole Number | `INTEGER` |
| Decimal | `DECIMAL(10,2)` or as specified |
| DateTime | `TIMESTAMPTZ` |
| Text (single) | `VARCHAR(n)` or `TEXT` |
| Text (multi) | `TEXT` |
| Yes/No | `BOOLEAN` |
| Lookup | `UUID` with FK constraint |

---

## SQL File Standards

### File Header Block
```sql
-- ============================================
-- File: {filename}.sql
-- Purpose: {description}
-- Author: {Desktop Claude | VS Code Claude}
-- Created: YYYY-MM-DD
-- Spec Reference: spec/{source_spec}.md
-- ============================================
```

### Section Separators
```sql
-- ============================================
-- SECTION: {Section Name}
-- ============================================
```

### Table Creation Template
```sql
CREATE TABLE IF NOT EXISTS {table_name} (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core Fields
    {field_name} {TYPE} {CONSTRAINTS},
    
    -- Foreign Keys
    {parent}_id UUID REFERENCES {parent_table}(id) ON DELETE {CASCADE|SET NULL},
    
    -- Computed/Rollup Fields
    {computed_field} {TYPE} DEFAULT {default},
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_{table}_{column} ON {table_name}({column});

-- Comments
COMMENT ON TABLE {table_name} IS '{description}';
COMMENT ON COLUMN {table_name}.{column} IS '{description}';
```

### ENUM Creation Template
```sql
-- ENUM: {enum_name}
-- Used by: {table.column}
-- Business rule: {description}
CREATE TYPE {enum_name} AS ENUM (
    'VALUE_ONE',
    'VALUE_TWO',
    'VALUE_THREE'
);
```

### Trigger Template
```sql
-- Trigger: {trigger_name}
-- Purpose: {description}
-- Fires: {BEFORE|AFTER} {INSERT|UPDATE|DELETE} ON {table}

CREATE OR REPLACE FUNCTION {function_name}()
RETURNS TRIGGER AS $$
BEGIN
    -- Logic here
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER {trigger_name}
    {BEFORE|AFTER} {INSERT|UPDATE|DELETE} ON {table}
    FOR EACH ROW
    EXECUTE FUNCTION {function_name}();
```

---

## Test Data Standards

### UUID Pattern for Test Data
Use predictable UUIDs for easy debugging:
```
{entity_code}-0000-0000-0000-{sequence_12_digits}

Entity codes:
11111111 = clients
22222222 = sites  
33333333 = locations
44444444 = projects
55555555 = scopes
66666666 = tasks
77777777 = apparatus
88888888 = employees
99999999 = pss_studies
```

Example:
```sql
'44444444-0000-0000-0000-000000000001'  -- project #1 (LASNAP16)
'55555555-0000-0000-0000-000000000001'  -- scope #1
'55555555-0000-0000-0000-000000000002'  -- scope #2
```

### Test Data Comments
```sql
-- ============================================
-- TEST DATA: {Entity Name}
-- Records: {count}
-- Source: {LASNAP16 | generated | seed}
-- ============================================
```

---

## Git Commit Standards

### Commit Message Format
```
{type}: {short description}

{detailed description if needed}

Spec: {spec file reference}
Files: {files changed}
```

### Types
- `spec:` - Specification document changes
- `schema:` - Database schema changes
- `data:` - Seed or test data changes
- `docs:` - Documentation changes
- `fix:` - Bug fixes
- `refactor:` - Code refactoring

### Examples
```
spec: Complete DATA_DICTIONARY.md with all 25 tables

schema: Add triggers for apparatus completion rollups

data: LASNAP16 test data with 47 apparatus records
```

---

## Review Checklist

### For Spec Documents
- [ ] All tables from V1513_FIELD_REFERENCE.md included
- [ ] Field names follow snake_case convention
- [ ] FK relationships documented
- [ ] ENUMs have valid transition rules
- [ ] Triggers have cascade effects documented

### For SQL Files
- [ ] Header block present
- [ ] Follows naming conventions
- [ ] References spec document
- [ ] Indexes on FK columns
- [ ] Comments on tables and key columns
- [ ] No hardcoded values (use ENUMs)

### For Test Data
- [ ] Uses predictable UUID pattern
- [ ] FK references exist in parent tables
- [ ] ENUM values are valid
- [ ] Dates are realistic
- [ ] Amounts are reasonable

---

*Conventions document | VS Code Claude | December 5, 2025*
