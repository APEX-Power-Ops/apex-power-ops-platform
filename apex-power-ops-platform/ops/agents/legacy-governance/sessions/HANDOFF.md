# RESA Power - Active Handoffs

**Last Updated:** December 3, 2025, Claude Desktop Session

---

## ⚠️⚠️⚠️ BUILD IS FRAGILE - READ THIS FIRST ⚠️⚠️⚠️

**The schema implementation is ON HOLD until remaining DDR items are resolved.**

We made tremendous progress establishing foundational architecture (DDR 001-003), but 5 decisions remain that could impact schema design. Implementing now risks rework.

**Session of December 3, 2025 established:**
- Error Tolerance Framework (how we handle mistakes at every step)
- Two-Stage Completion Model (Tech → Job Lead → Revenue)
- Batch Processing for Revenue (scheduled, not real-time)
- 10 Architecture Principles (including "Better and More Reliable Wins")

**NEXT SESSION MUST START WITH:** Resolving DDR-004 through DDR-008

---

### TO: Jason/Claude (P1 - BLOCKING)

### Task: Resolve Remaining Design Decision Register Items

**Priority:** P1 - BLOCKING (Before ANY schema work)  
**Created:** December 3, 2025  
**Status:** 3 of 8 COMPLETE, 5 REMAINING

**Context:**
External audit identified 8 architectural decisions that have been made implicitly but not documented. These need explicit resolution and documentation before the system goes to production.

**Deliverable:**
Complete the Decision/Rationale sections in `Documentation/01_Architecture/DESIGN_DECISION_REGISTER.md`

**Items to Resolve:**
- [x] DDR-001: Denormalized Field Sync Strategy ✅ DECIDED
- [x] DDR-002: Rate Versioning Strategy ✅ DECIDED
- [x] DDR-003: Revenue Reversal Handling ✅ DECIDED
- [ ] DDR-004: Task Requirement for Apparatus
- [ ] DDR-005: Apparatus Type Standardization
- [ ] DDR-006: Data Provenance Tracking
- [ ] DDR-007: Estimator → Project Conversion Path
- [ ] DDR-008: Security Model - Financial Isolation

**Notes:**
- Can be resolved incrementally as you encounter each area
- Some may be "accept current behavior and document it"
- Others may require schema/code changes
- Claude can help analyze options when you're ready to discuss each one

---

## 📝 Active Handoffs (ALL BLOCKED EXCEPT DDR RESOLUTION)

### TO: VS Code Claude (or Web Claude)

### Task: Extract Revenue Recognition Flow Logic (Layer 4)

**Priority:** P2 (BLOCKED by DDR resolution)  
**Created:** December 3, 2025  
**Created By:** Claude Desktop

**⚠️ BLOCKED:** Do not start until DDR-004 through DDR-008 are resolved. These decisions may affect flow requirements.

**Context:**
Schema audit Layers 1-3 are complete. We've identified all table/field gaps. Now we need to extract the actual workflow logic from the old Revenue Recognition flow so we can rebuild it with the new schema names.

**Deliverable:**
Create `C:\RESA_Power_Build\Documentation\02_Build_Guides\REVENUE_FLOW_LOGIC_REFERENCE.md`

**Acceptance Criteria:**
- [ ] Trigger conditions documented (what field, what value)
- [ ] Step-by-step workflow actions listed
- [ ] Field mappings: old field name → purpose → new field name
- [ ] Calculation logic extracted
- [ ] Any error handling / edge cases noted

**Files to Reference:**
- `Solution_Exports/Archive/v1.5.1.3/Workflows/RevenueRecognitiononApparatusCompletion-*.json`
- `Documentation/03_Progress_Tracking/SCHEMA_GAP_REPORT_v1.0.0.5_vs_v1.5.1.3.md`

**Files to Create:**
- `Documentation/02_Build_Guides/REVENUE_FLOW_LOGIC_REFERENCE.md`

**Dependencies:**
- None - this is document extraction only

**Notes:**
- The flow JSON may be large - focus on the essential logic
- Old field names will need mapping to new conventions (see gap report Part B)
- This document will be the blueprint for building the new flow

---

### TO: VS Code Claude (or Web Claude)

### Task: Extract Calculated/Rollup Formulas (Layer 5)

**Priority:** P2 (BLOCKED by DDR resolution)  
**Created:** December 3, 2025  
**Created By:** Claude Desktop

**⚠️ BLOCKED:** Do not start until DDR-004 through DDR-008 are resolved. DDR-003 (Two-Stage Completion) already changed the completion status structure, affecting which fields and formulas are needed.

**Context:**
We discovered the new version has ZERO calculated or rollup fields. The old version has 65. We need the exact formulas extracted so Jason can recreate them in Power Apps.

**Deliverable:**
Create `C:\RESA_Power_Build\Documentation\02_Build_Guides\CALCULATED_ROLLUP_FORMULAS.md`

**Acceptance Criteria:**
- [ ] All 18 calculated field formulas documented
- [ ] All 47 rollup field configurations documented
- [ ] Grouped by table for easy reference
- [ ] Notes on creation order (dependencies)

**Files to Reference:**
- `Solution_Exports/Archive/v1.5.1.3/customizations.xml`
- May need to check individual `Entities/[EntityName]/Entity.xml` files

**Dependencies:**
- Schema Gap Report complete (done)

**Notes:**
- Formulas in XML may use internal syntax - translate to human-readable
- Rollups need: aggregate type (SUM/COUNT/AVG/MAX/MIN), source field, filter condition
- Calculated fields need: formula expression

---

## ✅ Completed Handoffs

### ✅ Schema Audit + Governance Framework - December 3, 2025

**From:** HANDOFF_CLAUDE_DESKTOP_SCHEMA_AUDIT.md  
**Completed By:** Claude Desktop  
**Status:** ✅ COMPLETE

**Deliverables Created:**
- `Documentation/03_Progress_Tracking/SCHEMA_GAP_REPORT_v1.0.0.5_vs_v1.5.1.3.md`
- `Documentation/03_Progress_Tracking/SCHEMA_AUDIT_ACTION_CHECKLIST.md`
- `Documentation/03_Progress_Tracking/WORKFLOW_INTEGRATION_ANALYSIS.md`
- `Documentation/01_Architecture/DESIGN_DECISION_REGISTER.md` (8 open items)
- `Documentation/01_Architecture/ARCHITECTURE_PRINCIPLES.md`
- `Documentation/01_Architecture/PRE_IMPLEMENTATION_CHECKLIST.md`
- Updated `Sessions/CLAUDE_NOTES.md`

**Key Findings:**
- **20 tables in old → 12 tables in new** (8 missing, 1 new)
- **65 calculated/rollup fields missing** - ALL need recreation
- **7 lookup fields missing** - 3 P1 (block flow), 4 P2 (block rollups)
- **ScopeLaborDetail not created during import** - blocks Revenue Recognition
- **8 design decisions identified** - 3 resolved (DDR-001, DDR-002, DDR-003), 5 remaining

**Documents Created:**
- `Documentation/01_Architecture/ERROR_TOLERANCE_FRAMEWORK.md`
- `Documentation/04_Procedures/CHANGE_ORDER_PROCEDURES.md`
- `Documentation/01_Architecture/TWO_STAGE_COMPLETION_MODEL.md`
- Architecture Principles updated with Principle 9 (Error Tolerance)

**Immediate Actions for Jason:**
1. Add 3 P1 lookups to ApparatusRevenue via Power Apps UI
2. Add `createScopeLaborDetail()` to page.tsx
3. Expand completion status choices (5 values per DDR-003)
4. Review and resolve remaining 5 DDR items (can do incrementally)

---

### ✅ Schema Audit - December 2, 2025

**From:** Web Claude  
**Result:** Comprehensive audit of org7bdbc942 environment completed

**Files Created:**
- `Documentation/SCHEMA_AUDIT_org7bdbc942_Dec2025.md`
- `Sessions/SESSION_PROTOCOL.md`
- `Sessions/CURRENT_STATE.md`
- `Sessions/HANDOFF.md`

---

## Handoff Best Practices

1. **Be specific** - Vague tasks lead to wrong outcomes
2. **Include file paths** - Always use full paths from `C:\RESA_Power_Build\`
3. **List dependencies** - What must exist before starting
4. **Define done** - Clear acceptance criteria
5. **Update CLAUDE_NOTES.md** - When completing a handoff

---

## Instance Identification

| Instance | Typical Use | Strengths |
|----------|-------------|-----------|
| **Claude Desktop** | File operations, PowerShell, audits | Desktop access, long context |
| **VS Code Claude** | Code generation, MCP operations | IDE integration, code execution |
| **Web Claude** | Documentation, planning | Mobile access, quick lookups |

---

*Handoff file maintained per SESSION_PROTOCOL.md*
