# RESA Power Project - Claude Instructions

**Add this to Claude Project Instructions for automatic context.**

---

## Workspace Location
```
C:\RESA_Power_Build\
```

## First Action Every Session
Before doing anything else, read the state file:
```
C:\RESA_Power_Build\.claude\STATE.md
```

## Key Paths
| Purpose | Path |
|---------|------|
| State | `.claude/STATE.md` (read first, update last) |
| Protocol | `.claude/SESSION_PROTOCOL.md` |
| Specs | `spec/` |
| Schema SQL | `Supabase/schema/` (files 00-05) |
| Data SQL | `Supabase/data/` (files 10-12) |
| Docs | `Supabase/docs/` |
| Archive | `_archive/` |

## Session Rules
- Read STATE.md at start of every session
- Update STATE.md before ending session
- Keep sessions under 50 messages
- Use explicit file paths, not descriptions
- Fresh chats are fine - context is in STATE.md

## Current Phase
**PHASE 0: SPEC CREATION**

Parallel execution:
- **Desktop Claude:** Creates spec docs (DATA_DICTIONARY, ENUMS, etc.) + schema SQL
- **VS Code Claude:** Creates test data, README, reviews Desktop's work

## Project Context
RESA Power is a field service company. We're building:
- Supabase PostgreSQL database
- PSS Portal (Power System Studies tracking)
- Field testing project management
- Migrating from Microsoft Dataverse

## Approach
Spec-first development:
1. Create 5 spec documents (DATA_DICTIONARY, ENUMS, ERD, TRIGGERS, VIEWS)
2. Generate schema SQL from specs
3. Generate test data from schema
4. Documentation alongside

Current status and next tasks are always in STATE.md.
