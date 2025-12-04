# Claude Notes - Quick Context for Next Session

**Read this first.** This tells you where we are and what matters right now.

---

## 🧠 Your Role (Important!)

**You are a stakeholder in this project, not just an executor.**

Jason expects you to:
- **Question decisions** - "Is this the best way forward?"
- **Suggest alternatives** - Don't just implement what's asked; offer better options if you see them
- **Ask why** - Understanding intent leads to better solutions
- **Think like an owner** - This is your project too

**There's no ego here.** Jason wants the best option, not his option. He doesn't care where the idea came from. If you see a better way, say it. The discussions that happen when you push back and challenge assumptions are where the best work gets done.

Don't be passive - be a thinking partner.

---

## ⚠️ CRITICAL: BUILD IS FRAGILE - P1 PRIORITY

**DO NOT proceed with schema implementation until DDR items 004-008 are resolved.**

The first 3 DDR decisions established foundational workflow architecture. But 5 DDR items remain OPEN and may require schema changes:

| DDR | Topic | Risk if Unresolved |
|-----|-------|--------------------|
| 004 | Task Requirement for Apparatus | Rollup calculations, hierarchy consistency |
| 005 | Apparatus Type Standardization | Reporting inconsistency, no standard hours |
| 006 | Data Provenance Tracking | Can't trace record origins, blocks integrations |
| 007 | Estimator → Project Conversion | Duplicate workflows, unclear data paths |
| 008 | Security Model - Financial Isolation | May need table restructure for proper security |

**ON SESSION RESUME:**
1. Read `Documentation/01_Architecture/DESIGN_DECISION_REGISTER.md`
2. Continue DDR resolution starting with DDR-004
3. DO NOT implement schema changes until all DDRs resolved

---

## 🎯 Right Now (December 3, 2025)

**Environment:** org7bdbc942.crm.dynamics.com (the ONLY correct one)  
**Branch:** clean-main  
**Solution:** RESA_Power_Build_V2 v1.0.0.5

### Where We Are
Schema audit COMPLETE (Layers 1-3). We now have a detailed gap analysis between old (v1.5.1.3) and new (v1.0.0.5) builds.

### Critical Findings from Audit
| Gap | Count | Status |
|-----|-------|--------|
| Missing Tables | 8 | Evaluate need |
| Missing Lookups | 7 | **BLOCKING** - Add via UI |
| Missing Calculated Fields | 18 | Need to recreate |
| Missing Rollup Fields | 47 | Need to recreate |

**The new version has ZERO calculated/rollup fields!** This is the biggest gap.

### 🔴 CRITICAL: ScopeLaborDetail Not Created During Import
The Node.js import app creates Project → Scope → Task → Apparatus but **does NOT create ScopeLaborDetail**. Without this, Revenue Recognition flow will ALWAYS fail with "No labor rates defined".

**Fix Required:** Add `createScopeLaborDetail()` function to page.tsx after scope creation.
See: `Documentation/03_Progress_Tracking/WORKFLOW_INTEGRATION_ANALYSIS.md`

### What's Working
- MCP server at `MCP_Servers/resa-dataverse-mcp/` - use `node build/index.js` to start
- 12 tables in Dataverse (9 core + 3 financial)
- Apparatus trigger fields exist (completion_status, datecompleted, delayhours)
- ScopeLaborDetail has rate fields (just renamed convention)

### What's Broken/Blocked
- **7 lookup fields missing** - Must add via Power Apps UI (3 P1, 4 P2)
- **65 calc/rollup fields missing** - All need recreation
- **Flows not built yet** - Need lookups first
- **Flow logic not yet extracted** - Layer 4 pending

### Jason's Preferences (Important!)
- Wants separation pattern: financial tables separate from operational
- Values "reliability and consistency" over speed
- Likes checkpoint documentation before rushing ahead
- Appreciates decision rationale being captured

---

## 📍 Key Locations

| Need | Location |
|------|----------|
| **⚠️ QUICK STATUS (START HERE)** | `Sessions/QUICK_STATUS.md` |
| **Session Summary (Dec 3)** | `Sessions/SESSION_SUMMARY_2025-12-03.md` |
| **Schema Gap Report** | `Documentation/03_Progress_Tracking/SCHEMA_GAP_REPORT_v1.0.0.5_vs_v1.5.1.3.md` |
| **Action Checklist** | `Documentation/03_Progress_Tracking/SCHEMA_AUDIT_ACTION_CHECKLIST.md` |
| **Workflow Integration** | `Documentation/03_Progress_Tracking/WORKFLOW_INTEGRATION_ANALYSIS.md` |
| **Design Decisions** | `Documentation/01_Architecture/DESIGN_DECISION_REGISTER.md` |
| **Architecture Principles** | `Documentation/01_Architecture/ARCHITECTURE_PRINCIPLES.md` |
| **Pre-Implementation Checklist** | `Documentation/01_Architecture/PRE_IMPLEMENTATION_CHECKLIST.md` |
| **Error Tolerance Framework** | `Documentation/01_Architecture/ERROR_TOLERANCE_FRAMEWORK.md` |
| **Two-Stage Completion Model** | `Documentation/01_Architecture/TWO_STAGE_COMPLETION_MODEL.md` |
| **Change Order Procedures** | `Documentation/04_Procedures/CHANGE_ORDER_PROCEDURES.md` |
| Current build status | `Documentation/03_Progress_Tracking/BUILD_STATUS_2025-12-02.md` |
| Revenue architecture spec | `Documentation/02_Build_Guides/REVENUE_RECOGNITION_BUILD_SPEC.md` |
| Old working flow (reference) | `Solution_Exports/Archive/v1.5.1.3/Workflows/RevenueRecognition*.json` |
| Current clean export | `Solution_Exports/v1.0.0.5/customizations.xml` |

---

## ⚠️ Gotchas

1. **Wrong environments exist** - org99cd6c6e and org284447bd are DEPRECATED. Only use org7bdbc942.
2. **Schema names changed** - See full mapping in SCHEMA_GAP_REPORT
   - `cr950_projects` → `cr950_project`
   - `cr950_projectscope` → `cr950_scope`
   - `cr950_tasks` → `cr950_task`
   - `cr950_scopelabordetails` → `cr950_scopelabordetail`
3. **Lookup fields via API = 404** - Dataverse Web API can't create lookups. Don't waste time trying.
4. **Choice field for triggers** - We use `cr950_completion_status` (Choice: 1=Planned, 2=Complete), NOT a string field.
5. **Field naming convention changed** - Old: `cr950_field_name`, New: `cr950_tablefieldname` (entity prefix, no underscores)

---

## 🔜 Next Steps (Prioritized)

### Immediate (Before Flow Development)
1. **Add 3 P1 lookups to ApparatusRevenue** - Required for flow
   - → Apparatus, → Project, → ScopeLaborDetail
2. **Add calculated fields to ApparatusRevenue**
   - `totalhours` = Planned + Delay
   - `revenueamount` = Planned × Rate

### Next Session (Claude)
3. **Extract flow logic** - Layer 4 of audit
   - Parse `RevenueRecognitiononApparatusCompletion-*.json`
   - Create `REVENUE_FLOW_LOGIC_REFERENCE.md`

### After Flow Works
4. Add P2 lookups for rollup aggregation
5. Create rollup fields on financial summary tables
6. Create operational rollups on Project/Scope/Task

---

## 📝 Last Session Summary (Claude Desktop, Dec 3)

**Completed:** 
1. Schema Audit Layers 1-3
   - Full table inventory comparison (20 old vs 12 new)
   - Field-by-field analysis of 5 priority tables
   - Identified 7 missing lookups (3 P1, 4 P2)
   - Discovered ALL 65 calc/rollup fields are missing from new version
   - Created SCHEMA_GAP_REPORT and ACTION_CHECKLIST

2. Workflow Integration Analysis
   - Identified critical gap: ScopeLaborDetail not created during import
   - Documented the Project Creation → Revenue Recognition flow
   - Recommended fix: Add createScopeLaborDetail() to page.tsx

3. Architecture Governance Framework
   - Created DESIGN_DECISION_REGISTER.md (8 decisions, 1 resolved)
   - Created ARCHITECTURE_PRINCIPLES.md (8 core principles)
   - Created PRE_IMPLEMENTATION_CHECKLIST.md
   - Created ERROR_TOLERANCE_FRAMEWORK.md
   - Established "external audit process" for catching oversights

4. DDR-001 Resolved: Denormalized Field Sync
   - Decision: Soft Commit with Reconciliation
   - Pre-completion: Structure freely editable
   - Post-completion: Structure locked via UI
   - Reconciliation report catches any drift

5. DDR-002 Resolved: Rate Versioning Strategy
   - Decision: Forward-Only Rates + Manual Recalc Utility
   - ScopeLaborDetail updated in place; historical revenue preserved
   - Recalculation utility available when retroactive change needed
   - Created CHANGE_ORDER_PROCEDURES.md

6. DDR-003 Resolved: Revenue Reversal Handling
   - Decision: Two-Stage Completion + Batch Processing
   - Tech marks "Work Done" → Job Lead confirms → Revenue flow (scheduled)
   - Creates natural error correction windows
   - Reversal only needed for rare post-batch edge cases
   - Created TWO_STAGE_COMPLETION_MODEL.md

**Pending (IN ORDER OF PRIORITY):** 
1. ⚠️ **P1 BLOCKING:** Resolution of 5 remaining DDR items (004-008)
2. Layer 4 (Flow Logic Extraction) 
3. Layer 5 (Formula Extraction)
4. Schema implementation (AFTER all DDRs resolved)

**Full session details:** `Sessions/SESSION_SUMMARY_2025-12-03.md`

---

*Update this file before ending your session. Keep it short and useful.*
