# APEX Platform - Current State

**Last Updated:** 2026-01-01 21:30  
**Updated By:** Desktop Claude  
**Session:** Field Workflow & Enum Refinement

---

## Active Work

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| Decision log completion | Jason + Desktop | In Progress | Section 4 (Field Ops) major progress |

---

## Current Phase

**Phase 0: Foundation & Standards**

Establishing project identity, coordination protocols, and decision framework before building.

---

## What's Complete

- [x] Project name decided: APEX Platform
- [x] LLC filed: APEX Power Operations, LLC (via LegalZoom)
- [x] Domains secured: apexpowerops.com, apexpoweroperations.com
- [x] Database schema deployed (40+ tables)
- [x] NETA procedures loaded (66 procedures, 956 test items)
- [x] Coordination framework created (MASTER.md)
- [x] Old .claude/ files archived (30+ files)
- [x] Clean file structure established
- [x] **Section 4.2 Status Workflow - DECIDED** (5 states: NOT_STARTED, IN_PROGRESS, PENDING_REVIEW, COMPLETED, ISSUE_LOG)
- [x] **Section 4.3 Availability - DECIDED** (binary: AVAILABLE, NOT_AVAILABLE)
- [x] **Section 4.4 Assessment - DECIDED** (NETA values: ACCEPTABLE, MINOR_DEFICIENCY, NON_SERVICEABLE)
- [x] **Section 4.6.2 Approval/Revenue - DECIDED** (Job Lead approval = revenue recognition)
- [x] **Section 4.7 Field Requirements - FRAMEWORK ADDED** (contextual validation: Project Build vs Field Work vs Approval)

---

## Key Decisions This Session

### Status Workflow (Final)
```
NOT_STARTED → IN_PROGRESS → PENDING_REVIEW
                    ↑              ↓
                    └── (reject) ──┤
                                   ├── COMPLETED (approve → revenue)
                                   └── ISSUE_LOG (can't complete/failed)
```

### Three-Tier Operations Model
- **Tech:** Execute checklist, enter Assessment + Task Delays, submit
- **Job Lead:** Set Availability/Priority, approve/reject submissions, customer liaison  
- **PM/Office:** Cross-project resource allocation, financials

### Field Requirements Principle
"Required" depends on **when** and **who**:
- Project Build: Scope, Equipment Type, Hours (from Estimator)
- Tech Submit: Assessment (required), Task Delays (default 0)
- Job Lead: Availability flip, Priority (optional)

### No Partial Completion
Apparatus either completes fully or goes to ISSUE_LOG. No "done for today" intermediate state.

---

## What's Blocked

| Item | Blocked By | Owner |
|------|------------|-------|
| Phase 1 scope definition | DECISION_LOG.md Section 1.2 | Jason |
| UI development | Phase 1 scope + Auth setup | VS Code |
| Field Requirements finalization | Business decisions on each field | Jason |

---

## Decisions Needed from Jason

Next session priorities:
1. **Section 1.2** - Scope Boundaries (what's in/out of Phase 1)
2. **Section 4.7** - Finalize Field Requirements matrix (required vs recommended vs optional)
3. **Section 2** - User & Access Design (roles, auth)

---

## Database State

| Item | Status |
|------|--------|
| Supabase Project | fxoyniqnrlkxfligbxmg |
| Tables | 40+ deployed |
| NETA Data | Loaded |
| Auth | Not configured |
| RLS | Policies defined, not enabled |

---

## Resume Prompt

```
APEX Platform - Resume Session

Read these files in order:
1. C:\APEX Platform\.claude\STATE.md (this file)
2. C:\APEX Platform\.claude\DECISION_LOG.md (Section 4 has new decisions)

Continue with Section 1.2 (Scope Boundaries) or Section 4.7 (Field Requirements finalization).
```

---

*Update this file at the end of every session*
