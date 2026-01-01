# RESA Power Supabase Schema - Quick Reference

> **Version:** 3.1.0  
> **Updated:** December 26, 2025  
> **Status:** ✅ DEPLOYED - Operations + AI Orchestration + Study Content

---

## 🎯 THE VISION

**One platform. Everything connected. Always available when it matters.**

When a field tech opens their task for a 12.47kV padmount transformer, they don't search scattered folders. Everything is there:
- NETA ATS 7.2.2 test requirements
- RESA transformer testing SOP
- Transformer safety JSA
- Manufacturer datasheet
- **Study guide: Transformer Testing Protocol**
- **Reference sheet: TTR Calculations**
- **Practice questions: Transformer Testing**

Same query. Same UI. Same junction table. All linked through `apparatus_type`.

---

## Schema Location

```
C:\RESA_Power_Build\Supabase\schema\
├── 00_enums.sql
├── 01_tables.sql
├── 02_relationships.sql
├── 03_triggers.sql
├── 04_views.sql
├── 05_indexes.sql
├── 06_neta_sop_tables.sql              # Resource linking tables
├── 07_equipment_project_assignment.sql
├── 08_apparatus_completion_workflow.sql
├── 09_schema_additions.sql             # Operational fields + rollup views
├── 09b_enum_updates.sql                # Assessment value additions
├── 10_ai_orchestration.sql             # AI task queue, agent state, handoffs
├── 11_ai_orchestration_functions.sql   # RPC functions for coordination
└── 12_study_content.sql                # ⭐ NEW - Study guides, questions, progress
```

## 📋 Additional Documentation

- [EXCEL_TO_DATABASE_MAPPING.md](EXCEL_TO_DATABASE_MAPPING.md) - Field mapping from Excel trackers
- [AI_ORCHESTRATION_PROTOCOL.md](docs/AI_ORCHESTRATION_PROTOCOL.md) - Agent coordination guide

---

## Table Summary (40 Tables)

| # | Table | Purpose | Rows |
|---|-------|---------|------|
| **Organization** ||||
| 1 | `locations` | Business units (Phoenix, Denver, Las Vegas, San Diego) | 5 |
| 2 | `clients` | Customer companies | 1 |
| 3 | `sites` | Physical locations | 1 |
| 4 | `employees` | RESA staff | 5 |
| 5 | `estimators` | Quote creators | 2 |
| **Project Hierarchy** ||||
| 6 | `projects` | Master jobs | 1 |
| 7 | `scopes` | Deliverables/phases | 4 |
| 8 | `tasks` | Work items | 12 |
| 9 | `apparatus` | Equipment being tested | 47 |
| **Equipment & Types** ||||
| 10 | `apparatus_types` | Equipment categories (MV CB, Transformer, etc.) | 15 |
| 11 | `equipment` | Company-owned test equipment | 0 |
| 12 | `equipment_assignments` | Equipment checkout history | 0 |
| **Financials** ||||
| 13 | `apparatus_revenue` | Revenue recognition per apparatus | 0 |
| 14 | `scope_labor_details` | Labor line items | 6 |
| 15 | `scope_financial_summaries` | Scope rollups (trigger-updated) | 0 |
| 16 | `project_financial_summaries` | Project rollups (trigger-updated) | 0 |
| **Resource Assignments** ||||
| 17 | `resource_assignments` | Employee-to-project/scope | 8 |
| **PSS Portal** ||||
| 18 | `pss_engineers` | External engineering vendors | 0 |
| 19 | `pss_studies` | Power System Studies | 0 |
| 20 | `pss_document_templates` | Doc checklist templates | 6 |
| 21 | `pss_documents` | Study documents | 0 |
| 22 | `pss_rfis` | Requests for Information | 0 |
| 23 | `pss_activity_log` | Audit trail | 0 |
| **NETA & Resource Linking** ||||
| 24 | `neta_procedures` | NETA standard sections (ATS/MTS/ECS/ETT) | 66 |
| 25 | `neta_test_items` | Individual test steps per procedure | 956 |
| 26 | `neta_test_templates` | Legacy test templates | 0 |
| 27 | `sops` | Company Standard Operating Procedures | 0 |
| 28 | `safety_documents` | JSAs, PPE requirements, arc flash | 0 |
| 29 | `datasheets` | Manufacturer specs, product data | 0 |
| 30 | `apparatus_type_resources` | **Junction table** linking types → resources | 0 |
| **AI Orchestration** ||||
| 31 | `ai_tasks` | Central task queue for agent coordination | 1 |
| 32 | `ai_agent_state` | Real-time status of each AI agent | 5 |
| 33 | `ai_task_history` | Audit trail of all task changes | 0 |
| 34 | `ai_knowledge` | Structured knowledge base for RAG | 0 |
| 35 | `content_registry` | Inventory of all produced content | 0 |
| 36 | `ai_handoffs` | Explicit agent-to-agent transfers | 0 |
| **Study Content** ⭐ NEW ||||
| 37 | `study_content` | Study guides, reference sheets (markdown/HTML) | 0 |
| 38 | `study_questions` | Practice question bank | 0 |
| 39 | `apparatus_type_questions` | Junction: questions ↔ apparatus types | 0 |
| 40 | `user_study_progress` | User progress tracking (auth Phase 2) | 0 |

---

## 🔗 Resource Linking Architecture - THE CORE PATTERN

**Everything flows through `apparatus_type_resources`.**

```
┌──────────────────┐         ┌──────────────────────────────┐
│  apparatus_types │─────────│  apparatus_type_resources    │
│  (e.g., Power    │    1:N  │  (THE JUNCTION TABLE)        │
│   Transformer)   │         │  resource_id + resource_type │
└──────────────────┘         └──────────────┬───────────────┘
                                            │
         ┌──────────────┬───────────────────┼───────────────────┬──────────────┐
         │              │                   │                   │              │
         ▼              ▼                   ▼                   ▼              ▼
  ┌─────────────┐ ┌─────────────┐   ┌─────────────┐   ┌────────────┐ ┌────────────────┐
  │    neta_    │ │    sops     │   │   safety_   │   │ datasheets │ │ study_content  │
  │ procedures  │ │             │   │  documents  │   │            │ │   ⭐ NEW       │
  │  (66 rows)  │ │             │   │             │   │            │ │                │
  └──────┬──────┘ └─────────────┘   └─────────────┘   └────────────┘ └────────────────┘
         │
         ▼
  ┌─────────────┐
  │ neta_test_  │
  │   items     │
  │ (956 rows)  │
  └─────────────┘
```

**Field Tech Query Flow:**
```
Tech opens: "TRF-001 | 12.47kV Padmount Transformer"
    └── apparatus.apparatus_type_id = 'Power Transformer'
        └── apparatus_type_resources WHERE apparatus_type_id = [transformer-uuid]
            ├── neta_procedures (ATS 7.2.2, MTS 7.2.2)
            ├── sops (RESA-SOP-TRF-001)
            ├── safety_documents (JSA-Transformer)
            ├── datasheets (Cooper Envirotemp FR3)
            └── study_content (Transformer Testing Guide, Oil/DGA Analysis, TTR Reference)
```

**One query. All resources. Always connected.**

---

## ⭐ Study Content Schema (NEW - December 26, 2025)

### Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `study_content` | Guides, reference sheets | slug, certification_level, domain, body_markdown, quality_tier, embedding |
| `study_questions` | Practice question bank | stem, choices, explanation, difficulty, ksa_mappings, analytics |
| `apparatus_type_questions` | Question ↔ Type linking | apparatus_type_id, question_id, relevance_score |
| `user_study_progress` | User progress tracking | user_id, content_id, mastery_level, time_spent |

### New Enums

| Enum | Values |
|------|--------|
| `certification_level` | I, II, III, IV |
| `content_quality_tier` | gold, high_quality, complete, draft, needs_review |
| `question_type` | multiple_choice, true_false, calculation, scenario, fill_blank, matching |

### Resource Type Enum Extensions

Added to existing `resource_type`:
- `study_guide` - Comprehensive study materials
- `reference_sheet` - Quick reference cards
- `practice_questions` - Question collections

### Key Functions

| Function | Purpose |
|----------|---------|
| `register_study_content()` | Migration helper - load from HTML files |
| `link_content_to_apparatus_type()` | Connect content to equipment types |
| `publish_study_content()` | Make content live |
| `get_apparatus_resources()` | **Field tech query** - all resources for apparatus |
| `register_question()` | Add question to bank |
| `get_apparatus_type_questions()` | Get practice questions for equipment type |
| `record_content_progress()` | Track user study time/completion |
| `record_question_attempt()` | Track question answers with analytics |

### Views

| View | Purpose |
|------|---------|
| `v_apparatus_type_all_resources` | Unified view: NETA + SOPs + Safety + Study Content |
| `v_apparatus_study_content` | Study content for specific apparatus |
| `v_study_content_inventory` | Content inventory by domain/level/quality |
| `v_question_bank_stats` | Question analytics by domain/level |

### Migration Path

```sql
-- 1. Register content from existing HTML
SELECT register_study_content(
    'Transformer Testing Protocol',           -- title
    'transformer-testing-protocol',           -- slug
    'study_guide',                            -- resource_type
    'III',                                    -- certification_level
    'transformers',                           -- domain
    '# Transformer Testing Protocol...',      -- body_markdown
    'Complete testing guide...',              -- summary
    '10-Transformer-Testing-Protocol.html',   -- original_file
    1057,                                     -- line_count
    ARRAY['ETT-III-2.4', 'ETT-III-2.7'],     -- ksa_mappings
    ARRAY['ATS-7.2.2', 'MTS-7.2.2']          -- neta_sections
);

-- 2. Link to apparatus type
SELECT link_content_to_apparatus_type(
    'transformer-testing-protocol',
    'Power Transformer'
);

-- 3. Publish
SELECT publish_study_content('transformer-testing-protocol');
```

---

## Key Enums (Option Sets)

| Enum | Values |
|------|--------|
| `project_status` | Draft, Quoted, Won, Active, On Hold, Complete, Cancelled |
| `scope_status` | Not Started, In Progress, On Hold, Complete, Cancelled |
| `apparatus_status` | Not Started, In Progress, Pending Review, Complete, Cancelled |
| `apparatus_assessment` | Pass, Fail, Marginal, Needs Repair, Deferred, Not Tested, Acceptable, Non-Serviceable, Minor Deficiency |
| `apparatus_availability` | Ready, On Hold, Not Available |
| `revenue_type` | Testing, Travel, Per Diem, Materials, Equipment, Engineering, Report, Other |
| `neta_standard_type` | ATS, MTS, ECS, ETT |
| `neta_test_type` | visual_mechanical, electrical, optional |
| `sop_category` | safety, testing, commissioning, maintenance, documentation, quality, administrative, equipment_specific, other |
| `safety_document_type` | jsa, sds, hazard_alert, ppe_requirement, lockout_tagout, arc_flash, confined_space, hot_work, electrical_safety, environmental, other |
| `resource_type` | neta_procedure, sop, safety_document, datasheet, document, video, checklist, **study_guide**, **reference_sheet**, **practice_questions** |
| `ai_task_type` | create, enhance, review, assemble, migrate, document, test, deploy |
| `ai_task_status` | pending, claimed, blocked, review, complete, failed |
| `ai_agent` | desktop-claude, codex-max, vs-code-claude, local-ai, human |
| `ai_task_priority` | critical, high, normal, low, background |
| `certification_level` | I, II, III, IV |
| `content_quality_tier` | gold, high_quality, complete, draft, needs_review |
| `question_type` | multiple_choice, true_false, calculation, scenario, fill_blank, matching |

---

## Apparatus Types with NETA Section Links

The `apparatus_types` table includes columns to directly link equipment categories to NETA standards:

| Column | Purpose | Example |
|--------|---------|---------|
| `neta_section_ats` | ATS (Acceptance) reference | "7.6.1" |
| `neta_section_mts` | MTS (Maintenance) reference | "7.6.1" |
| `neta_section_ecs` | ECS (Commissioning) reference | "7.6" |
| `neta_section_ett` | ETT (Technician) reference | NULL |

---

## Triggers & Automatic Features

| Trigger | Function |
|---------|----------|
| Apparatus completion | Creates `apparatus_revenue` record automatically |
| Financial rollups | Updates scope/project summaries when revenue changes |
| PSS status change | Logs to `pss_activity_log` |
| Rollup counts | Cascades: apparatus → task → scope → project |
| Study content updated | Auto-updates `updated_at` timestamp |
| Question analytics | Updates `times_shown`, `times_correct` on attempts |

---

## Dashboard Views

| View | Purpose |
|------|---------|
| `v_project_dashboard` | Projects with client, site, progress, revenue |
| `v_scope_dashboard` | Scopes with project context, labor rates |
| `v_apparatus_tracking` | Apparatus with full hierarchy |
| `v_pss_dashboard` | PSS studies with doc/RFI counts |
| `v_apparatus_operational` | Daily scheduling - what's ready? |
| `v_project_apparatus_summary` | Per-project KPIs |
| `v_apparatus_by_category` | Category breakdown |
| **`v_master_operations`** | Multi-project dashboard |
| `v_resource_allocation` | Staffing decisions |
| `v_equipment_needs` | Test equipment planning |
| `v_blockers_summary` | Bottleneck identification |
| `v_schedule_health` | Risk identification |
| `v_active_tasks` | AI tasks in progress |
| `v_agent_dashboard` | AI agent status |
| `v_pending_handoffs` | AI handoffs waiting |
| **`v_apparatus_type_all_resources`** | **All resources for equipment type** |
| **`v_apparatus_study_content`** | **Study content for apparatus** |
| **`v_study_content_inventory`** | **Content by domain/level** |
| **`v_question_bank_stats`** | **Question analytics** |

---

## AI Orchestration Layer

### Tables (6)
| Table | Purpose |
|-------|---------|
| `ai_tasks` | Central task queue for agent coordination |
| `ai_agent_state` | Real-time status of each AI agent |
| `ai_task_history` | Audit trail of all task changes |
| `ai_knowledge` | Structured knowledge base for RAG |
| `content_registry` | Inventory of all produced content |
| `ai_handoffs` | Explicit agent-to-agent transfers |

### Key Functions
| Function | Purpose |
|----------|---------|
| `claim_task()` | Agent claims next available task |
| `complete_task()` | Mark task done with output |
| `create_task()` | Add new task to queue |
| `handoff_task()` | Transfer work between agents |
| `agent_heartbeat()` | Agent status check-in |

---

## Supabase Connection

- **Project**: resa-power-db (fxoyniqnrlkxfligbxmg)
- **API URL**: https://fxoyniqnrlkxfligbxmg.supabase.co
- **Credentials**: `.secrets/SUPABASE_CREDENTIALS.md`

---

## Deployment Status

### ✅ Deployed
- Core schema (01-05)
- NETA/Resource linking (06)
- Equipment assignment (07)
- Apparatus workflow (08)
- Operational views (09, 09b)
- AI Orchestration (10, 11)

### 🔲 Ready to Deploy
- **Study Content (12)** - Run `schema/12_study_content.sql`

### Data Loaded
- 66 NETA procedures (33 ATS + 33 MTS)
- 956 test items
- 5 AI agents initialized
- 1 task queued (Dashboard MVP)

### Next: Content Migration
1. Deploy `12_study_content.sql`
2. Build HTML → Markdown migration script
3. Load NETA 2/3/4 study guides
4. Link to apparatus_types
5. Generate embeddings for RAG

---

## The Connected Platform

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RESA POWER PLATFORM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   FIELD TECH                    PM                      EXECUTIVE       │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐      │
│   │ My Tasks        │   │ Project Status  │   │ Multi-Project   │      │
│   │ ├─ TRF-001     │   │ ├─ Progress     │   │ Dashboard       │      │
│   │ │  └─ Resources│   │ ├─ Budget       │   │ ├─ Revenue      │      │
│   │ │     ├─ NETA  │   │ ├─ Resources    │   │ ├─ Utilization  │      │
│   │ │     ├─ SOP   │   │ └─ Timeline     │   │ └─ Pipeline     │      │
│   │ │     ├─ Safety│   └─────────────────┘   └─────────────────┘      │
│   │ │     ├─ Study │                                                   │
│   │ │     └─ Quiz  │   SHARED FOUNDATION                               │
│   │ └─ Hours Entry │   ═══════════════════════════════════════════     │
│   └─────────────────┘   apparatus_type_resources (junction table)      │
│                         └─ NETA procedures (66)                        │
│                         └─ SOPs                                        │
│                         └─ Safety documents                            │
│                         └─ Datasheets                                  │
│                         └─ Study content (guides, refs, questions)     │
│                                                                         │
│   AI ORCHESTRATION          STUDY PLATFORM         ANALYTICS            │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐      │
│   │ Task Queue      │   │ Study Guides    │   │ Progress Track  │      │
│   │ Agent State     │   │ Practice Tests  │   │ Question Stats  │      │
│   │ Handoffs        │   │ Reference Sheets│   │ Mastery Levels  │      │
│   │ Knowledge Base  │   │ RAG Search      │   │ Team Readiness  │      │
│   └─────────────────┘   └─────────────────┘   └─────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

Everything connected. Everything queryable. Everything available when it matters.
```
