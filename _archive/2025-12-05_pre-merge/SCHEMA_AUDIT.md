# RESA Power Database Schema Audit

## Comparison: Desktop Claude (001_complete_schema.sql) vs VS Code Claude (Database_Setup/)

**Audit Date:** December 5, 2025

---

## Executive Summary

| Aspect | Desktop Claude | VS Code Claude | Winner |
|--------|----------------|----------------|--------|
| **Tables** | 22 + 1 (estimators) | 24 (16 core + 8 PSS) | Desktop ✅ |
| **ENUMs** | 15 PostgreSQL ENUMs | VARCHAR with CHECK | Desktop ✅ |
| **Triggers** | 10+ complex triggers | 2 basic triggers | Desktop ✅ |
| **Views** | 7 dashboard views | None | Desktop ✅ |
| **RLS Security** | Full Supabase RLS | None | Desktop ✅ |
| **Seed Data** | 35 apparatus types | 12 apparatus types | Desktop ✅ |
| **Generated Columns** | Yes (computed fields) | No | Desktop ✅ |
| **Test Data** | None | Full LASNAP16 + PSS | VS Code ✅ |
| **Documentation** | SCHEMA_REFERENCE.md | README.md | Tie |

**RECOMMENDATION:** Use Desktop Claude's `001_complete_schema.sql` as the master, then add VS Code's test data.

---

## Detailed Table Comparison

### Organization Tables

| Table | Desktop | VS Code | Differences |
|-------|---------|---------|-------------|
| `locations` | ✅ | ✅ | Desktop adds `phone` |
| `clients` | ✅ | ✅ | Desktop adds billing fields, `client_type`, `industry`, `account_manager` |
| `sites` | ✅ | ✅ | Desktop adds `latitude/longitude`, `site_type`, `utility_provider` |
| `employees` | ✅ | ✅ | Desktop has `full_name` computed, `skill_level`, `overtime_multiplier`, `can_lead_crew`, `max_arc_flash_ppe` |
| `contacts` | ✅ | ❌ | **VS Code missing** - uses `pss_contacts` instead |
| `portal_users` | ✅ | ✅ (as `pss_users`) | Desktop unified, VS Code PSS-specific |

### Equipment Reference

| Table | Desktop | VS Code | Differences |
|-------|---------|---------|-------------|
| `apparatus_types` | ✅ | ✅ (as `apparatus_type_master`) | Desktop adds `neta_section`, `neta_table`, `default_unit_price` |
| `neta_test_templates` | ❌ | ✅ | **Desktop missing** - VS Code has template for test procedures |

### Project Hierarchy

| Table | Desktop | VS Code | Differences |
|-------|---------|---------|-------------|
| `projects` | ✅ | ✅ | Desktop has **rollup fields** (counts, hours, dates), `project_type` ENUM |
| `scopes` | ✅ | ✅ | Desktop has **rollup fields**, `neta_standard`, `multiplier` |
| `scope_labor_details` | ✅ | ✅ | Desktop has **computed `effective_rate`**, more rate fields |
| `tasks` | ✅ | ✅ | Desktop has **rollup fields**, `availability` ENUM, `parent_task_id` |
| `apparatus` | ✅ | ✅ | Desktop has **computed columns** (`completed_hours`, `remaining_hours`), assessment ENUM |
| `apparatus_revenue` | ✅ | ✅ | Desktop has **4 computed columns** (total_hours, base_revenue, delay_adjustment, revenue_amount) |
| `scope_financial_summaries` | ✅ | ✅ (as `scope_financial_summary`) | Desktop has `revenue_variance` computed |
| `project_financial_summaries` | ✅ | ✅ (as `project_financial_summary`) | Desktop has `total_variance` computed |
| `estimators` | ✅ | ✅ | VS Code simpler; Desktop has `scope_json` JSONB for import |

### PSS Portal Tables

| Table | Desktop | VS Code | Differences |
|-------|---------|---------|-------------|
| `engineers` | ✅ | ✅ (as `pss_engineers`) | Desktop adds `accepts_new_projects` |
| `pss_studies` | ✅ | ❌ | **VS Code uses `pss_projects`** - Desktop links to main `projects` table |
| `document_templates` | ✅ | ✅ (as `pss_document_templates`) | Same structure |
| `pss_documents` | ✅ | ✅ | Desktop has `mime_type`, `file_size_bytes`, more computed fields |
| `rfis` | ✅ | ✅ (as `pss_rfis`) | Desktop has `response_attachments` array |
| `activity_log` | ✅ | ✅ (as `pss_activity_log`) | **Desktop polymorphic** - links to ALL entities (project, scope, task, apparatus, RFI) |

---

## Key Advantages: Desktop Claude Schema

### 1. PostgreSQL ENUMs (Type Safety)
```sql
-- Desktop uses proper ENUMs
CREATE TYPE project_status AS ENUM (
    'NOT_STARTED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED'
);

-- vs VS Code VARCHAR with CHECK
status VARCHAR(50) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Quoted', ...))
```
**Benefit:** Database enforced, can't insert invalid values, IDE autocomplete.

### 2. Computed/Generated Columns
```sql
-- Desktop auto-calculates
percent_complete DECIMAL(5, 2) GENERATED ALWAYS AS (
    CASE WHEN total_apparatus_count > 0 
         THEN ROUND((completed_apparatus_count::DECIMAL / total_apparatus_count) * 100, 2)
         ELSE 0 
    END
) STORED
```
**Benefit:** No manual calculation needed, always accurate.

### 3. Cascading Rollup Triggers
```sql
-- Apparatus → Task → Scope → Project automatic aggregation
CREATE TRIGGER apparatus_rollup_to_task
    AFTER INSERT OR UPDATE OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_task_rollups();
```
**Benefit:** Counts/hours automatically bubble up hierarchy.

### 4. Unified Activity Log (Polymorphic)
```sql
-- Can link to ANY entity
project_id UUID REFERENCES projects(id),
pss_study_id UUID REFERENCES pss_studies(id),
scope_id UUID REFERENCES scopes(id),
apparatus_id UUID REFERENCES apparatus(id),
rfi_id UUID REFERENCES rfis(id),
```
**Benefit:** Single history view across all activities.

### 5. Row Level Security (RLS)
```sql
-- Clients only see their own projects
CREATE POLICY "Clients see own projects" ON projects
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM portal_users pu
            JOIN contacts c ON c.portal_user_id = pu.id
            WHERE pu.auth_user_id = auth.uid()
            AND c.client_id = projects.client_id
        )
    );
```
**Benefit:** Security at database level, not application level.

### 6. Dashboard Views Ready
- `v_project_dashboard` - Projects with rollups
- `v_scope_dashboard` - Scopes with rates
- `v_apparatus_tracking` - Full hierarchy
- `v_pss_dashboard` - PSS with doc/RFI counts
- `v_revenue_summary` - Financial aggregation
- `v_outstanding_documents` - Outstanding docs
- `v_open_rfis` - Open RFIs sorted by priority

---

## Key Advantages: VS Code Claude Schema

### 1. Complete Test Data
```sql
-- Full LASNAP16 project with real data
INSERT INTO projects (id, project_number, project_name, ...) VALUES
    ('f0000000-...', 'LASNAP16', 'Lone Star DC1 Annual Maintenance', ...);

-- 6 scopes, 7 tasks, 14 apparatus with realistic status
```
**Benefit:** Immediate testing without manual data entry.

### 2. NETA Test Templates Table
```sql
CREATE TABLE IF NOT EXISTS neta_test_templates (
    template_code VARCHAR(50) NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    apparatus_type VARCHAR(100),
    test_category VARCHAR(100),
    estimated_hours DECIMAL(10, 2),
    ...
);
```
**Benefit:** Standard test procedures per equipment type.

### 3. Equipment Table (Company Assets)
```sql
CREATE TABLE IF NOT EXISTS equipment (
    equipment_number VARCHAR(50) UNIQUE,
    category VARCHAR(100),
    calibration_date DATE,
    calibration_due DATE,
    daily_rate DECIMAL(10, 2),
    ...
);
```
**Benefit:** Track test equipment, calibration, rental rates.

---

## GAPS IDENTIFIED

### Missing from Both:
1. **Time Entry Table** - No way to track actual hours per employee/day
2. **Expense Table** - No travel, materials, per diem tracking
3. **Resource Assignment Table** - Which employees on which projects (exists in Dataverse)
4. **Quote/Proposal Table** - Separate from Estimators
5. **Invoice Table** - Billing/AR tracking
6. **Vehicle Table** - Fleet management (mentioned in unified schema doc)
7. **Certification Tracking** - Employee NETA levels, expiration dates (Desktop has neta_level field, but no history)

### Missing from Desktop:
1. `neta_test_templates` - Standard test procedures
2. `equipment` - Company-owned test equipment
3. Test data for immediate development

### Missing from VS Code:
1. Computed columns (must calculate in app)
2. Cascading triggers (must manually update rollups)
3. Dashboard views (must write queries)
4. RLS security (must implement in app)
5. Unified `contacts` table (split into PSS-specific)

---

## CONSOLIDATION RECOMMENDATION

### Master Schema: Use `001_complete_schema.sql` with these additions:

```sql
-- ADD TO SECTION 3 (after apparatus_types)

-- 3.2 NETA TEST TEMPLATES
CREATE TABLE neta_test_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_code TEXT NOT NULL,
    template_name TEXT NOT NULL,
    apparatus_type_id UUID REFERENCES apparatus_types(id),
    test_category TEXT,
    neta_section TEXT,
    description TEXT,
    estimated_hours DECIMAL(6, 2),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ADD TO SECTION 2 (Company Resources)

-- 2.6 EQUIPMENT (Company-owned test equipment)
CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_number TEXT UNIQUE,
    name TEXT NOT NULL,
    category TEXT,
    manufacturer TEXT,
    model TEXT,
    serial_number TEXT,
    location_id UUID REFERENCES locations(id),
    assigned_employee_id UUID REFERENCES employees(id),
    status TEXT DEFAULT 'Available',
    calibration_date DATE,
    calibration_due DATE,
    purchase_date DATE,
    purchase_cost DECIMAL(12, 2),
    daily_rate DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_equipment_location ON equipment(location_id);
CREATE INDEX idx_equipment_assigned ON equipment(assigned_employee_id);
CREATE INDEX idx_equipment_calibration ON equipment(calibration_due);
```

### Test Data: Create `002_test_data.sql` from VS Code files

---

## FILE CONSOLIDATION PLAN

### Final Structure:
```
C:\RESA_Power_Build\Supabase\
├── 001_complete_schema.sql     # Master schema (Desktop + additions)
├── 002_seed_data.sql           # Reference data (apparatus types, doc templates)
├── 003_test_data.sql           # LASNAP16 + PSS test projects
├── SCHEMA_REFERENCE.md         # Quick reference (updated)
└── MIGRATION_FROM_DATAVERSE.md # Migration guide
```

### Delete (redundant):
```
C:\RESA_Power_Build\Database_Setup\  # Merge into Supabase folder
```

---

## ACTION ITEMS

1. ✅ **Audit complete** - This document
2. 🔲 **Merge additions** - Add NETA templates, equipment to Desktop schema
3. 🔲 **Create test data file** - Consolidate VS Code test data
4. 🔲 **Update SCHEMA_REFERENCE.md** - Add new tables
5. 🔲 **Delete redundant files** - Clean up Database_Setup folder
6. 🔲 **Deploy to Supabase** - Test execution

---

## APPROVAL NEEDED

Before proceeding with consolidation:

1. **Confirm Desktop schema as master?** (Recommended: YES)
2. **Add NETA test templates?** (Recommended: YES)
3. **Add equipment tracking?** (Recommended: YES)
4. **Keep or archive Database_Setup folder?** (Recommended: Archive then delete)
5. **Additional tables needed?** (Time entry, expenses, invoices - future phase?)

---

*Audit prepared by VS Code Claude | December 5, 2025*
