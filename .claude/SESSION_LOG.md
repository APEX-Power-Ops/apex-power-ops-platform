# APEX Platform - Session Log

Append-only history of all sessions. Newest entries at top.

---

## 2026-01-01 ~20:00-21:30 - Desktop Claude

**Duration:** ~90 min  
**Focus:** Field Operations Workflow - Enum definitions and dashboard KPIs

**Completed:**
- Analyzed Garney tracker Excel formulas and PowerBI data structure
- Defined three-tier operations model: Tech → Job Lead → PM/Office
- Finalized STATUS enum (5 values): NOT_STARTED, IN_PROGRESS, PENDING_REVIEW, COMPLETED, ISSUE_LOG
- Finalized AVAILABILITY enum (binary): AVAILABLE, NOT_AVAILABLE
- Confirmed ASSESSMENT enum (NETA standard): ACCEPTABLE, MINOR_DEFICIENCY, NON_SERVICEABLE
- Defined PRIORITY as optional PM flag (HIGH, MEDIUM, LOW)
- Established revenue recognition trigger: Job Lead approval timestamp
- Created Field Requirements framework (contextual validation by role/phase)
- Added Section 4.7 to DECISION_LOG.md

**Key Decisions Made:**
- Status is system-calculated from workflow state (except ISSUE_LOG = manual)
- Job Lead approval = revenue recognition (approved_at timestamp)
- Rejection sends back to IN_PROGRESS with notes
- No partial completion - either complete or Issue Log
- "Required" depends on context: Project Build vs Field Work vs Approval
- OVERDUE remains a calculated overlay (not a status value)

**Dashboard KPIs Mapped:**
- Ready to Work = AVAILABILITY=AVAILABLE AND STATUS≠COMPLETED
- Apparatus Blocked = AVAILABILITY=NOT_AVAILABLE AND STATUS≠COMPLETED
- Completion % = 1 - (Remaining Hours / Total Hours)
- Issue Log/Failed = ASSESSMENT=NON_SERVICEABLE or has_issue=true
- Past Due = is_overdue=true AND STATUS≠COMPLETED

**In Progress:**
- DECISION_LOG.md Section 4.7 (Field Requirements matrix) - framework added, specific fields TBD
- Section 1.2 (Scope Boundaries) - not started

**Files Modified:**
- .claude/DECISION_LOG.md (Sections 4.2, 4.3, 4.6, 4.7 updated)
- .claude/STATE.md (session summary)
- .claude/SESSION_LOG.md (this entry)

**Next Session:**
- Section 1.2 Scope Boundaries OR
- Section 4.7 Field Requirements finalization (which fields required/recommended/optional)

---

## 2025-12-31 22:55-23:55 - Desktop Claude

**Duration:** ~60 min  
**Focus:** Project identity, framework consolidation, coordination protocols

**Completed:**
- Decided project name: APEX Platform
- Decided LLC name: APEX Power Operations, LLC
- Secured domains: apexpowerops.com (primary), apexpoweroperations.com (backup)
- Designed AI coordination workflow (file-based, Desktop orchestrates, VS Code implements)
- Archived 30+ old .claude/ files to _archive/2025-12-31_pre-consolidation/
- Created MASTER.md - comprehensive project guidelines (~400 lines)
- Created clean 6-file coordination structure
- Started DECISION_LOG.md - Section 1.1 complete

**Decisions Made:**
- Project: APEX Platform / APEX Power Operations, LLC
- Domain: apexpowerops.com
- Jason owns 100% IP - no RESA involvement
- File-based coordination (not database ai_tasks)
- Desktop Claude = orchestrator, VS Code Claude = implementer
- Priority order: Scope Decisions → Field Ops → User Access → Build

**In Progress:**
- DECISION_LOG.md - Section 1.1 done, Sections 1.2-10 open (~100 questions remaining)

**Handed Off:**
- None - session paused, Jason taking break

**Files Created:**
- .claude/MASTER.md (project constitution)
- .claude/STATE.md (current status)
- .claude/SESSION_LOG.md (this file)
- .claude/BACKLOG.md (work queue)
- .claude/HANDOFFS/TO_DESKTOP.md (inbox template)
- .claude/HANDOFFS/TO_VSCODE.md (inbox template)

**Files Archived:**
- 30+ files moved to _archive/2025-12-31_pre-consolidation/

**Next Session:**
- Continue DECISION_LOG.md starting with Section 1.2 (Scope Boundaries)

---
