# Apex Power Ops - Workspace Protocol

**Version:** 1.0  
**Created:** December 5, 2025  
**Purpose:** Establish consistent, efficient workspace conventions for Apex Power Ops collaboration

---

## 1. Directory Structure (Clean & Predictable)

```
C:\Repos\apex-power-ops\
│
├── .claude/                          # SESSION CONTINUITY (NEW)
│   ├── CURRENT_STATE.md              # What's in progress, blockers, next steps
│   ├── DECISIONS_LOG.md              # All decisions with rationale
│   └── HANDOFF_TEMPLATE.md           # Standard format for session handoffs
│
├── Supabase/                         # DATABASE (ACTIVE DEVELOPMENT)
│   ├── schema/                       # SQL files (numbered, ordered)
│   │   ├── 00_enums.sql
│   │   ├── 01_core_schema.sql
│   │   ├── 02_pss_schema.sql
│   │   ├── 03_triggers_functions.sql
│   │   ├── 04_views.sql
│   │   └── 05_rls_policies.sql
│   ├── data/                         # Seed + test data
│   │   ├── 10_seed_data.sql
│   │   ├── 11_test_data.sql
│   │   └── 12_pss_test_data.sql
│   ├── docs/                         # Documentation
│   │   ├── README.md
│   │   ├── QUICK_START.md
│   │   └── SCHEMA_REFERENCE.md
│   └── archive/                      # Old versions (dated)
│       └── 2025-12-05_pre-merge/
│
├── Documentation/                    # PROJECT DOCS (unchanged)
│   └── ...existing structure...
│
├── _archive/                         # DEPRECATED FILES (move, don't delete)
│   └── Database_Setup/               # Old VS Code schema files
│
└── WORKSPACE_PROTOCOL.md             # THIS FILE (root level, always read first)
```

---

## 2. File Naming Conventions

### SQL Files
```
[NN]_[category]_[description].sql

Examples:
00_enums.sql                    # Infrastructure
01_core_schema.sql              # Tables
03_triggers_functions.sql       # Automation
10_seed_data.sql                # Reference data
11_test_data.sql                # Development data
```

### Documentation
```
[CATEGORY]_[description].md

Examples:
QUICK_START.md                  # How to deploy
SCHEMA_REFERENCE.md             # Table documentation
CURRENT_STATE.md                # Session continuity
```

### Naming Rules
- **Lowercase** for SQL files
- **UPPERCASE** for markdown documentation
- **Underscores** for word separation (never spaces)
- **Numbers prefix** for execution order (SQL only)

---

## 3. Session Continuity Protocol

### At Session START (Claude reads):
```markdown
1. Read: .claude/CURRENT_STATE.md
2. Read: .claude/DECISIONS_LOG.md (last 5 entries)
3. Read: Relevant schema files if DB work
4. Acknowledge context before proceeding
```

### At Session END (Claude writes):
```markdown
1. Update: .claude/CURRENT_STATE.md
2. Append: .claude/DECISIONS_LOG.md (any new decisions)
3. Commit message format: "[AREA] Brief description"
```

### CURRENT_STATE.md Format
```markdown
# Current State - [DATE]

## Active Work
- [ ] Task in progress
- [x] Completed this session

## Blockers
- None / List blockers

## Next Session Should
1. First priority
2. Second priority

## Open Questions
- Question needing decision?

## Files Modified This Session
- path/to/file.sql - Brief description
```

---

## 4. SQL File Standards

### Header Block (Required)
```sql
-- ============================================================================
-- APEX POWER OPS DATABASE - [FILE NAME]
-- ============================================================================
-- Purpose: [One-line description]
-- Dependencies: [List files that must run first, or "None"]
-- Author: [Desktop Claude | VS Code Claude]
-- Created: [Date]
-- Modified: [Date] - [Brief change description]
-- ============================================================================
```

### Section Markers
```sql
-- ============================================================================
-- SECTION N: [SECTION NAME]
-- ============================================================================
```

### Table Comments
```sql
-- Table: [table_name]
-- Purpose: [One-line description]
-- Relationships: [Key FKs]
CREATE TABLE table_name (
    ...
);
```

### Enum Documentation
```sql
-- Enum: [enum_name]
-- Used by: [table.column, table.column]
CREATE TYPE enum_name AS ENUM (...);
```

---

## 5. Handoff Protocol (Multi-Claude)

### Standard Handoff Format
```markdown
## Handoff: [From] → [To]
**Date:** YYYY-MM-DD HH:MM
**Context:** [Brief situation]

### Completed
- Item 1
- Item 2

### In Progress
- Item with status

### Needs Your Action
- [ ] Specific task
- [ ] Specific task

### Decisions Made
| Decision | Rationale |
|----------|-----------|
| Choice | Why |

### Files to Review
- `path/file.sql` - Review for X
```

---

## 6. Code Review Checklist

### SQL Schema Review
- [ ] Header block present
- [ ] Dependencies listed correctly
- [ ] Table has primary key
- [ ] Foreign keys reference correct tables
- [ ] Indexes on FK columns
- [ ] ENUMs used instead of VARCHAR for status fields
- [ ] `created_at` and `updated_at` on all tables
- [ ] Computed columns where applicable

### Test Data Review
- [ ] Uses predictable UUIDs
- [ ] Respects FK relationships (parent before child)
- [ ] Realistic values (not "test123")
- [ ] Covers edge cases (null values, empty strings)

### Documentation Review
- [ ] Matches current schema
- [ ] Examples are copy-pasteable
- [ ] No broken links/references

---

## 7. Git Commit Standards

### Commit Message Format
```
[AREA] Brief description (50 chars max)

- Detail 1
- Detail 2

Refs: #issue or "Part of schema merge"
```

### Area Tags
- `[SCHEMA]` - Database structure changes
- `[DATA]` - Seed or test data
- `[DOCS]` - Documentation
- `[FIX]` - Bug fixes
- `[REFACTOR]` - Code reorganization

### Examples
```
[SCHEMA] Add PSS portal tables with pss_* prefix

- pss_engineers, pss_studies, pss_documents
- pss_rfis, pss_activity_log, pss_contacts
- All tables have RLS policies

Refs: Part of schema merge
```

---

## 8. Decision Documentation

### DECISIONS_LOG.md Format
```markdown
## [DATE] - [Decision Title]

**Context:** Why was this decision needed?

**Options Considered:**
1. Option A - Pros/Cons
2. Option B - Pros/Cons

**Decision:** [What we chose]

**Rationale:** [Why]

**Stakeholder:** [Who approved]
```

---

## 9. Environment Checklist

### Before Starting Work
- [ ] Workspace folder open: `C:\Repos\apex-power-ops`
- [ ] Read `.claude/CURRENT_STATE.md`
- [ ] Confirm which Claude instance (Desktop/VS Code)
- [ ] Understand assigned tasks

### During Work
- [ ] Follow file naming conventions
- [ ] Include header blocks in SQL
- [ ] Test SQL syntax before saving
- [ ] Update CURRENT_STATE.md on major progress

### Before Ending Session
- [ ] Update `.claude/CURRENT_STATE.md`
- [ ] Add any decisions to `DECISIONS_LOG.md`
- [ ] Create handoff if partner Claude continues
- [ ] Commit with proper message format

---

## 10. Quick Reference

### File Locations
| Type | Location |
|------|----------|
| Schema SQL | `Supabase/schema/` |
| Data SQL | `Supabase/data/` |
| Docs | `Supabase/docs/` |
| Session state | `.claude/` |
| Archives | `_archive/` |

### UUID Pattern for Test Data
```
[entity-code][zeros]-0000-0000-[seq]-[sub-seq]

Examples:
a0000000-0000-0000-0001-000000000001  # Location 1
b0000000-0000-0000-0002-000000000001  # Client 1
c0000000-0000-0000-0003-000000000001  # Site 1
f0000000-0000-0000-0006-000000000001  # Project 1
g0000000-0000-0000-0007-000000000001  # Scope 1
```

### Execution Order
```
00 → 01 → 02 → 03 → 04 → 05 → 10 → 11 → 12
```

---

## 11. This Session's Setup

### Immediate Actions
1. Create `.claude/` directory
2. Create `CURRENT_STATE.md`
3. Create `DECISIONS_LOG.md`
4. Archive old files to `_archive/`
5. Create clean `Supabase/` structure

### Then Begin Parallel Work
- Desktop Claude: Schema files (00-05, 10)
- VS Code Claude: Docs + test data (11, 12, README)

---

*Protocol established by VS Code Claude & Desktop Claude | December 5, 2025*
