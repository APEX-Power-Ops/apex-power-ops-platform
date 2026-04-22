# SCHEMA_REFERENCE.md
## NETA ETT Study Platform — Supabase Database Schema
## Last Updated: 2026-02-28 | Audited from live database

> **This is the authoritative schema reference for all Claude instances.**
> Generated from live `information_schema` queries — not guesswork.
> Update this file after any migration.

---

## Quick Stats

| Table | Rows | Purpose |
|-------|------|---------|
| study_content | 335 | Study guides, practice tests, reference sheets, extractions |
| ksas | 483 | KSA registry (Knowledge, Skills, Abilities) |
| ksa_content_links | 4,915 | Bridge: which content covers which KSAs |
| study_questions | 2,144 | Atomic questions for dynamic quiz assembly |
| user_study_progress | 0 | Per-user study tracking (schema ready, no users yet) |
| user_test_attempts | 0 | Per-user test attempt history (schema ready) |
| user_profiles | 0 | User accounts (schema ready) |
| content_registry | 0 | AI task → content file tracking (schema ready) |
| neta_procedures | 129 | NETA ATS/MTS test procedures |
| neta_test_items | 2,977 | Individual test steps within procedures |
| apparatus_types | 87 | Equipment type definitions |
| apparatus_type_resources | 189 | Links apparatus types → study_content, SOPs, datasheets |

---

## Custom Enum Types

```
certification_level     I | II | III | IV
resource_type           neta_procedure | sop | safety_document | datasheet |
                        document | video | checklist | study_guide |
                        reference_sheet | practice_test
content_quality_tier    gold | high_quality | complete | draft | needs_review
ai_agent                desktop-claude | vs-code-claude | codex-max | local-ai | human
ai_task_type            create | enhance | review | assemble | migrate | document | test | deploy
ai_task_status          pending | claimed | blocked | review | complete | failed
ai_task_priority        critical | high | normal | low | background
neta_standard_type      ATS | MTS | ECS | ETT
neta_test_type          visual_mechanical | electrical | optional
neta_level              Level I | Level II | Level III | Level IV
user_role               technician | lead_technician | admin
voltage_class           extra_low | low | medium | high | all
```

---

## Core NETA ETT Tables

### study_content
> The central content table. Holds study guides, practice tests, reference sheets, and extracted source material.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid | NOT NULL | gen_random_uuid() | PK |
| content_id | varchar | NOT NULL | | Unique. Human-readable ID (e.g. `L3-SG-ET-001`, `EXT-ETT-012`) |
| title | varchar | NOT NULL | | Display title |
| slug | varchar | NOT NULL | | Unique. URL-safe identifier |
| resource_type | enum(resource_type) | NOT NULL | | `study_guide` \| `practice_test` \| `reference_sheet` \| `document` \| etc. |
| certification_level | enum(certification_level) | NOT NULL | | `I` \| `II` \| `III` \| `IV` |
| domain | varchar[] | NULL | '{}' | Domain codes array (e.g. `{ET, CT}`) |
| neta_section_primary | varchar | NULL | | Primary NETA section (e.g. `7.1`) |
| neta_sections_secondary | varchar[] | NULL | '{}' | Additional NETA sections covered |
| tags | text[] | NULL | '{}' | Freeform tags |
| body_markdown | text | NULL | | Full content in markdown |
| summary | text | NULL | | Brief description/abstract |
| metadata | jsonb | NULL | '{}' | Extensible metadata (standards versions, audit history, etc.) |
| quality_tier | enum(content_quality_tier) | NULL | 'complete' | `gold` \| `high_quality` \| `complete` \| `draft` \| `needs_review` |
| line_count | integer | NULL | | Content length metric |
| dimension_average | numeric | NULL | | Quality dimension score |
| source_filename | varchar | NULL | | Original source file |
| source_path | varchar | NULL | | Original source path |
| published_at | timestamptz | NULL | | Publication timestamp |
| is_active | boolean | NULL | true | Soft delete / hide flag |
| created_at | timestamptz | NULL | now() | |
| updated_at | timestamptz | NULL | now() | |

**Current distribution:**
- By resource_type: study_guide (99), practice_test (89), document (84), reference_sheet (63)
- By level: II (124), III (119), IV (92)
- All EXT-xxx extractions stored as resource_type = `document`

**Indexes:**
- `study_content_pkey` — PK on id
- `study_content_content_id_key` — UNIQUE on content_id
- `study_content_slug_key` — UNIQUE on slug
- `idx_study_content_level` — btree on certification_level
- `idx_study_content_type` — btree on resource_type
- `idx_study_content_slug` — btree on slug
- `idx_study_content_neta_section` — btree on neta_section_primary
- `idx_study_content_quality` — btree on quality_tier
- `idx_study_content_domain` — GIN on domain[]
- `idx_study_content_tags` — GIN on tags[]
- `idx_study_content_metadata` — GIN on metadata jsonb

---

### ksas
> KSA (Knowledge, Skills, Abilities) registry. 483 entries defining what technicians must know per certification level.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid | NOT NULL | gen_random_uuid() | PK |
| ksa_code | varchar | NOT NULL | | Unique. e.g. `KSA-III-CT-028` |
| certification_level | enum(certification_level) | NOT NULL | | `II` \| `III` \| `IV` |
| domain | varchar | NOT NULL | | Full name (e.g. `Component Testing`) |
| domain_code | varchar | NOT NULL | | Short code (e.g. `CT`, `ET`, `SC`) |
| subcategory | varchar | NULL | | Subcategory code |
| subcategory_name | varchar | NULL | | Display name (e.g. `Circuit Switchers`) |
| description | text | NOT NULL | | Full KSA description |
| bloom_level | varchar | NULL | | Bloom's taxonomy level |
| equipment_type | varchar | NULL | | Equipment classification |
| neta_section_prefix | varchar | NULL | | NETA section (e.g. `7.7`) |
| neta_sections | varchar[] | NULL | '{}' | All relevant NETA sections |
| equipment_tags | varchar[] | NULL | '{}' | Equipment classification tags |
| test_tags | varchar[] | NULL | '{}' | Test type tags |
| tags | varchar[] | NULL | '{}' | General tags |
| created_at | timestamptz | NULL | now() | |
| updated_at | timestamptz | NULL | now() | |

**Indexes:**
- `ksas_pkey` — PK on id
- `ksas_ksa_code_key` — UNIQUE on ksa_code
- `idx_ksas_level` — btree on certification_level
- `idx_ksas_domain` — btree on domain_code
- `idx_ksas_equipment` — partial btree on equipment_type (WHERE NOT NULL)
- `idx_ksas_neta_section` — partial btree on neta_section_prefix (WHERE NOT NULL)
- `idx_ksas_bloom` — btree on bloom_level
- `idx_ksas_tags` — GIN on tags[]

---

### ksa_content_links
> Bridge table connecting KSAs to study content. The intelligence layer that maps "what you need to know" to "where to learn it."

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid | NOT NULL | gen_random_uuid() | PK |
| ksa_id | uuid | NOT NULL | | FK → ksas.id |
| study_content_id | uuid | NOT NULL | | FK → study_content.id |
| coverage_level | varchar | NOT NULL | | `full` \| `partial` |
| mapping_method | varchar | NOT NULL | | `keyword_match` \| `l4_deterministic` \| `manual_override` \| `body_content_discovery` |
| confidence | numeric | NULL | | 0.00–1.00 confidence score |
| notes | text | NULL | | Mapping rationale |
| created_at | timestamptz | NULL | now() | |
| updated_at | timestamptz | NULL | now() | |

**Constraints:**
- UNIQUE on (ksa_id, study_content_id) — one link per KSA-content pair

**Coverage stats (2026-02-28):**
- 4,915 total links
- 471/483 KSAs have at least one link (97.5%)
- 12 KSAs with zero links (8 Circuit Switchers L2/L3, 4 Fiber Optic L4)

**Indexes:**
- `ksa_content_links_pkey` — PK on id
- `ksa_content_links_ksa_id_study_content_id_key` — UNIQUE composite
- `idx_kcl_ksa_id` — btree on ksa_id
- `idx_kcl_study_content_id` — btree on study_content_id
- `idx_kcl_mapping_method` — btree on mapping_method

---

### study_questions
> Atomic questions for practice tests and dynamic quiz generation. Each question linked to a study_content row.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid | NOT NULL | gen_random_uuid() | PK |
| question_id | varchar | NOT NULL | | Unique. Human-readable ID |
| study_content_id | uuid | NOT NULL | | FK → study_content.id |
| certification_level | enum(certification_level) | NOT NULL | | Question target level |
| category | varchar | NULL | | Topic category |
| subcategory | varchar | NULL | | Topic subcategory |
| domain | varchar[] | NULL | '{}' | Domain codes |
| difficulty | varchar | NULL | | Difficulty rating |
| tags | text[] | NULL | '{}' | Freeform tags |
| question_text | text | NOT NULL | | The question |
| question_type | varchar | NULL | 'multiple_choice' | `multiple_choice` \| (extensible) |
| options | jsonb | NOT NULL | '{}' | Answer options (flexible format) |
| correct_answer | varchar | NOT NULL | | Correct answer key |
| explanation | text | NULL | | Why the answer is correct |
| formula | varchar | NULL | | Relevant formula if calculation-based |
| neta_section | varchar | NULL | | NETA section reference |
| standard_reference | text | NULL | | IEEE/NFPA/etc. reference |
| source_info | varchar | NULL | | Source attribution |
| is_active | boolean | NULL | true | Soft delete flag |
| created_at | timestamptz | NULL | now() | |
| updated_at | timestamptz | NULL | now() | |

**Indexes:**
- `study_questions_pkey` — PK on id
- `study_questions_question_id_key` — UNIQUE on question_id
- `idx_study_questions_content` — btree on study_content_id
- `idx_study_questions_level` — btree on certification_level
- `idx_study_questions_category` — btree on category
- `idx_study_questions_neta_section` — btree on neta_section
- `idx_study_questions_domain` — GIN on domain[]
- `idx_study_questions_tags` — GIN on tags[]

---

## User-Facing Tables (schema ready, 0 rows — awaiting platform launch)

### user_profiles
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| + 9 additional columns | | User account data |

### user_study_progress
> Tracks per-user study engagement with content.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| progress_id | uuid | NOT NULL | gen_random_uuid() | PK |
| user_id | uuid | NOT NULL | | FK → user_profiles.id |
| study_content_id | uuid | NOT NULL | | FK → study_content.id |
| status | varchar | NULL | | Study status |
| percent_complete | smallint | NULL | | 0–100 |
| total_study_minutes | integer | NULL | | Cumulative study time |
| last_accessed_at | timestamptz | NULL | | Last viewed |
| completed_at | timestamptz | NULL | | Completion timestamp |
| user_notes | text | NULL | | Personal notes |
| is_bookmarked | boolean | NULL | | Bookmark flag |
| created_at | timestamptz | NULL | now() | |
| updated_at | timestamptz | NULL | now() | |

**Constraints:** UNIQUE on (user_id, study_content_id)

**Indexes:**
- `user_study_progress_pkey` — PK on progress_id
- `uq_user_study_progress` — UNIQUE (user_id, study_content_id)
- `idx_study_progress_user` — btree on user_id
- `idx_study_progress_content` — btree on study_content_id
- `idx_study_progress_status` — btree on (user_id, status)
- `idx_study_progress_last_accessed` — btree on (user_id, last_accessed_at DESC)
- `idx_study_progress_bookmarked` — partial btree on (user_id, is_bookmarked) WHERE true

### user_test_attempts
> Records each practice test attempt with scores and answer details.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| attempt_id | uuid | NOT NULL | gen_random_uuid() | PK |
| user_id | uuid | NOT NULL | | FK → user_profiles.id |
| study_content_id | uuid | NOT NULL | | FK → study_content.id |
| total_questions | smallint | NULL | | Questions in attempt |
| correct_answers | smallint | NULL | | Correct count |
| score_percent | numeric | NULL | | Calculated score |
| started_at | timestamptz | NULL | | Attempt start |
| completed_at | timestamptz | NULL | | Attempt end |
| duration_seconds | integer | NULL | | Time taken |
| answers | jsonb | NULL | | Full answer record |
| weak_domains | varchar[] | NULL | | Domains needing review |
| created_at | timestamptz | NULL | now() | |

**Indexes:**
- `user_test_attempts_pkey` — PK on attempt_id
- `idx_test_attempts_user` — btree on user_id
- `idx_test_attempts_content` — btree on study_content_id
- `idx_test_attempts_user_recent` — btree on (user_id, created_at DESC)
- `idx_test_attempts_user_score` — btree on (user_id, score_percent DESC)
- `idx_test_attempts_weak_domains` — GIN on weak_domains[]

---

## NETA Procedures Tables

### neta_procedures
> NETA ATS/MTS test procedures by equipment type and section number.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| + 18 additional columns | | Procedure metadata, section numbers, standard type/version |
| apparatus_type_id | uuid | FK → apparatus_types.id |

**Constraints:** UNIQUE on (standard_type, standard_version, section_number)
**129 rows** covering ATS and MTS procedures.

**Indexes:**
- `idx_neta_procedures_apparatus_type` — btree on apparatus_type_id
- `idx_neta_procedures_category` — btree on equipment_category
- `idx_neta_procedures_section` — btree on section_number
- `idx_neta_procedures_standard` — btree on (standard_type, standard_version)
- `uq_neta_procedure_section` — UNIQUE composite

### neta_test_items
> Individual test steps within NETA procedures. 2,977 items — the searchable test index.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| procedure_id | uuid | FK → neta_procedures.id |
| test_type | enum(neta_test_type) | visual_mechanical \| electrical \| optional |
| test_number | varchar | Step number within procedure |
| + 14 additional columns | | Test description, acceptance criteria, references |

**Constraints:** UNIQUE on (procedure_id, test_type, test_number)

**Indexes:**
- `idx_neta_test_items_procedure` — btree on procedure_id
- `idx_neta_test_items_type` — btree on test_type
- `uq_neta_test_item` — UNIQUE composite

---

## Cross-Reference & AI Tables

### apparatus_type_resources (189 rows)
> Links equipment types to study materials, SOPs, datasheets, and safety docs.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| apparatus_type_id | uuid | FK → apparatus_types.id |
| study_content_id | uuid | FK → study_content.id (nullable) |
| datasheet_id | uuid | FK → datasheets.id (nullable) |
| safety_document_id | uuid | FK → safety_documents.id (nullable) |
| sop_id | uuid | FK → sops.id (nullable) |
| neta_procedure_id | uuid | FK → neta_procedures.id (nullable) |
| + 11 additional columns | | Relationship metadata |

### content_registry (0 rows — schema ready)
> Tracks content files generated by AI agents.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| project | varchar | Project identifier |
| domain | varchar | Content domain |
| content_type | varchar | File type classification |
| file_path | text | Filesystem path |
| file_name | varchar | Filename |
| title | varchar | Content title |
| status | varchar | Lifecycle status |
| quality_score | numeric | Automated quality metric |
| line_count | integer | File size metric |
| word_count | integer | Content volume metric |
| metadata | jsonb | Extensible metadata |
| created_by_task | uuid | FK → ai_tasks.id |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### AI Agent Infrastructure
> Task management system for cross-instance Claude coordination.

**ai_tasks** — Task queue with priority, status, assignment
**ai_task_history** — Audit trail of task state changes
**ai_handoffs** — Handoff records between agent instances
**ai_agent_state** — Current state per agent (includes current_task_id FK)
**ai_knowledge** — Shared knowledge base entries

Uses enums: `ai_agent`, `ai_task_type`, `ai_task_status`, `ai_task_priority`

---

## Foreign Key Relationship Map

```
study_content
  ├── ksa_content_links.study_content_id      → Which KSAs this content covers
  ├── study_questions.study_content_id         → Questions derived from this content
  ├── user_study_progress.study_content_id     → User engagement tracking
  ├── user_test_attempts.study_content_id      → Test attempts against this content
  └── apparatus_type_resources.study_content_id → Equipment type associations

ksas
  └── ksa_content_links.ksa_id                → Content coverage for this KSA

user_profiles
  ├── user_study_progress.user_id             → User's study records
  └── user_test_attempts.user_id              → User's test records

neta_procedures
  ├── neta_test_items.procedure_id            → Test steps within procedure
  └── apparatus_type_resources.neta_procedure_id → Equipment type link

apparatus_types
  ├── apparatus_type_resources.apparatus_type_id → Resource associations
  └── neta_procedures.apparatus_type_id          → NETA procedure link
```

---

## All Public Tables (68 total)

### NETA ETT Study Platform (starred)
```
★ study_content          (22 cols, 335 rows)
★ ksas                   (17 cols, 483 rows)
★ ksa_content_links       (9 cols, 4,915 rows)
★ study_questions         (21 cols, 2,144 rows)
★ user_study_progress     (12 cols, 0 rows)
★ user_test_attempts      (12 cols, 0 rows)
★ user_profiles           (10 cols, 0 rows)
★ content_registry        (15 cols, 0 rows)
★ neta_procedures         (19 cols, 129 rows)
★ neta_test_items         (18 cols, 2,977 rows)
★ neta_test_templates     (11 cols)
★ nfpa_70e_tables         (10 cols)
```

### RESA Power Operations Platform
```
  projects               (25 cols)    clients          (15 cols)
  scopes                 (25 cols)    sites            (16 cols)
  tasks                  (21 cols)    locations        (15 cols)
  apparatus              (35 cols)    employees        (22 cols)
  apparatus_types        (15 cols)    equipment        (22 cols)
  apparatus_revenue      (11 cols)    equipment_assignments (18 cols)
  apparatus_type_resources (18 cols)  estimators       (9 cols)
  datasheets             (30 cols)    resource_assignments (14 cols)
  safety_documents       (28 cols)    project_financial_summaries (17 cols)
  scope_financial_summaries (15 cols) scope_labor_details (11 cols)
```

### SOPs & Safety
```
  sops                   (26 cols)    ahas              (26 cols)
  sops_v2                (29 cols)    aha_task_steps    (22 cols)
  sop_task_steps         (22 cols)    aha_crew_signoffs (18 cols)
  sop_apparatus_types     (9 cols)
```

### Power System Studies (PSS)
```
  pss_studies            (16 cols)    pss_documents     (15 cols)
  pss_engineers          (12 cols)    pss_document_templates (10 cols)
  pss_rfis               (17 cols)    pss_activity_log  (13 cols)
```

### AI Agent Infrastructure
```
  ai_tasks               (25 cols)    ai_agent_state    (8 cols)
  ai_task_history         (9 cols)    ai_knowledge      (12 cols)
  ai_handoffs            (10 cols)
```

### Views (17)
```
  v_active_tasks, v_agent_dashboard, v_apparatus_approval_queue,
  v_apparatus_resources, v_apparatus_testing_status, v_apparatus_type_resources,
  v_approval_queue_summary, v_employee_roster, v_equipment_current_status,
  v_equipment_movement_history, v_neta_test_details, v_pending_handoffs,
  v_project_equipment, v_projects_active, v_projects_full,
  v_pss_dashboard, v_scope_financials, v_scope_summary
```

---

## Common Query Patterns

```sql
-- All study guides for Level III
SELECT content_id, title, quality_tier
FROM study_content
WHERE certification_level = 'III'
  AND resource_type = 'study_guide'
  AND is_active = true
ORDER BY neta_section_primary;

-- KSA coverage report: which KSAs have no content?
SELECT k.ksa_code, k.subcategory_name, k.certification_level
FROM ksas k
LEFT JOIN ksa_content_links kcl ON k.id = kcl.ksa_id
WHERE kcl.id IS NULL
ORDER BY k.ksa_code;

-- Generate a 25-question practice quiz for a topic
SELECT question_text, options, correct_answer, explanation
FROM study_questions
WHERE category = 'Transformers'
  AND certification_level = 'III'
  AND is_active = true
ORDER BY random()
LIMIT 25;

-- Content coverage for a specific KSA
SELECT sc.content_id, sc.title, sc.resource_type,
       kcl.coverage_level, kcl.confidence, kcl.mapping_method
FROM ksa_content_links kcl
JOIN study_content sc ON kcl.study_content_id = sc.id
WHERE kcl.ksa_id = (SELECT id FROM ksas WHERE ksa_code = 'KSA-III-CT-028')
ORDER BY kcl.confidence DESC;

-- What equipment types have study materials linked?
SELECT at.name, COUNT(atr.id) as resource_count
FROM apparatus_types at
LEFT JOIN apparatus_type_resources atr ON at.id = atr.apparatus_type_id
WHERE atr.study_content_id IS NOT NULL
GROUP BY at.name
ORDER BY resource_count DESC;
```

---

## Proposed Schema Additions (under discussion)

> See `Development/TASK-SCHEMA-ARCHITECTURE-DISCUSSION.md` for full context.
> See `Development/RESPONSE-Desktop_Claude.md` and `RESPONSE-VSCode_Claude.md` for recommendations.

### Confirmed needed:
```sql
ALTER TABLE study_content ADD COLUMN topic_slug TEXT;
ALTER TABLE study_content ADD COLUMN levels TEXT[] DEFAULT '{}';
CREATE INDEX idx_study_content_topic_slug ON study_content(topic_slug);
CREATE INDEX idx_study_content_levels ON study_content USING GIN(levels);
```

### Under consideration:
- Full-text search vector on study_content (tsvector + GIN index)
- `resource_type` enum expansion: add 'extraction' value
- RLS policies before user-facing launch

---

## Changelog

| Date | Change | Agent |
|------|--------|-------|
| 2026-02-28 | Initial creation from live schema audit | desktop-claude |
| 2026-02-28 | Deleted 12 false Circuit Switcher → Capacitor Reactor links | desktop-claude |
| | _Update this table after every migration_ | |
