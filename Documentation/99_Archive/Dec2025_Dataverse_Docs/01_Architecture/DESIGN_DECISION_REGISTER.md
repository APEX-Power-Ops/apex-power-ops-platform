# RESA Power Project Tracker - Design Decision Register

**Created:** December 3, 2025  
**Purpose:** Force explicit discussion and documentation of architectural decisions  
**Status:** ACTIVE - 5 DECISIONS REMAINING

---

## ⚠️ CURRENT STATUS: BUILD IS FRAGILE

| Status | Count | Items |
|--------|-------|-------|
| 🟡 DECIDED | 3 | DDR-001, DDR-002, DDR-003 |
| 🔴 OPEN | 5 | DDR-004, DDR-005, DDR-006, DDR-007, DDR-008 |
| 🟢 IMPLEMENTED | 0 | - |

**Schema implementation is ON HOLD until all decisions are resolved.**

Resolved decisions established foundational architecture:
- DDR-001: Soft commit at first completion + reconciliation
- DDR-002: Forward-only rates + manual recalc utility
- DDR-003: Two-stage completion + batch processing

Remaining decisions may require schema changes. Resolve before implementing.

---

## How To Use This Document

For each decision item:
1. **Read the context** - Understand what's being asked
2. **Review the options** - Consider the tradeoffs
3. **Make a decision** - Pick an approach
4. **Document the rationale** - Future you will thank present you
5. **Mark status** - Open → Decided → Implemented

**Decision Statuses:**
- 🔴 **OPEN** - Needs discussion and decision
- 🟡 **DECIDED** - Decision made, not yet implemented
- 🟢 **IMPLEMENTED** - Decision made and built into system
- ⚪ **DEFERRED** - Intentionally postponed to future phase

---

## Foundational Principles (Already Established)

These are decisions that have already been made. Documenting them here for reference.

| Principle | Decision | Rationale |
|-----------|----------|-----------|
| **Financial/Operational Separation** | Separate tables for financial data (ApparatusRevenue, ScopeFinancialSummary, ProjectFinancialSummary) | Enables table-level security. "I don't know who should see what, but if they're separate I can control it easily." |
| **Denormalized Lookups** | Apparatus has direct links to Project, Scope, Client, Site | UI performance. Avoid traversing multiple joins for common queries. |
| **Excel Estimator Retained** | VBA export → JSON → Node.js import | Estimator is a "staple" that must be maintained initially. Optimize around it, not against it. |
| **Schema Rebuild** | Fresh environment (org7bdbc942) with new naming conventions | Old schema had accumulated cruft. Clean start with deliberate design. |
| **Hierarchical Rollups** | Apparatus → Task → Scope → Project | Revenue and hours aggregate up the chain for visibility at multiple levels. |

---

## Decision Items

---

### DDR-001: Denormalized Field Sync Strategy

**Status:** 🟡 DECIDED

**Context:**
Apparatus has direct lookups to Project, Client, Site (denormalized from the Scope relationship). This improves query performance but creates potential data integrity issues.

**The Question:**
What happens when parent relationships change? For example:
- A Scope is moved to a different Project
- A Site's Client changes
- Someone edits the wrong record

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Immutable Relationships** | Once created, parent relationships cannot change | Simple, no sync needed | Inflexible, mistakes require delete/recreate |
| **B: Cascade Updates (Flow)** | Power Automate flow triggers on parent change, updates children | Keeps data in sync | Complex, potential for loops/failures |
| **C: Calculated Fields** | Remove denormalized fields, use calculated fields that traverse relationships | Always accurate | Worse query performance, defeats purpose |
| **D: Accept Drift** | Acknowledge data may drift, run periodic reconciliation | Simplest | Data integrity issues, confusing reports |

**Decision:** Hybrid of A + D - **Soft Commit with Reconciliation**

1. **Pre-Completion Window:** Structure (Project/Scope/Task assignments) is freely editable until the first apparatus in that scope is marked complete
2. **Post-Completion Lock:** Once first completion occurs, structure is locked via UI enforcement (not technical prevention)
3. **Reconciliation Report:** Weekly report surfaces any records where `apparatus.project_id ≠ apparatus.scope.project_id`
4. **No Cascade Sync:** No Power Automate flows to keep denormalized fields in sync - complexity not justified

**Rationale:** 

Business reality: The hierarchy (Project → Scope → Task → Apparatus) represents a contractual/bid structure that doesn't change after work begins. The structure is set at bid time.

Error scenario: Mistakes happen during import/setup, not during active work. Therefore:
- Errors during setup → RECOVERABLE (edit freely before commit point)
- Errors after work starts → DETECTABLE (reconciliation catches drift)
- No sync flows → Follows Error Tolerance Framework (don't add complexity for rare edge cases)

The "first completion" is a natural business commit point - once a technician has done work, the structure is real.

**Implementation Required:**
- [ ] UI: Disable structure changes when scope has completed apparatus
- [ ] Report: Structure integrity reconciliation view
- [ ] Field: Calculated or rollup to detect "has completed apparatus" on Scope

**Reference:** `Documentation/01_Architecture/ERROR_TOLERANCE_FRAMEWORK.md`

**Decided By:** Jason Swenson **Date:** December 3, 2025

---

### DDR-002: Rate Versioning Strategy

**Status:** 🟡 DECIDED

**Context:**
The old ScopeLaborDetail had versioning fields (iscurrentversion, versionnumber, effectivedate, expirationdate). The new schema dropped these.

**The Question:**
What happens when billing rates change mid-project?

**Scenario:**
- Project quoted at $350/hr
- 50 apparatus completed at $350/hr = $X revenue recorded
- Client renegotiates to $325/hr
- Remaining 100 apparatus completed at... which rate?

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Rates Locked at Creation** | ScopeLaborDetail rate never changes. New rate = new project/scope. | Simple, audit-friendly | Inflexible for change orders |
| **B: Rate Versioning** | Multiple ScopeLaborDetail records per scope, with effective dates. Revenue uses rate active at completion time. | Accurate, handles changes | Complex queries, flow logic |
| **C: Rate Overwrite** | Update rate in place. Historical revenue unchanged, future revenue uses new rate. | Moderate complexity | Audit trail unclear |
| **D: Revenue Recalculation** | When rate changes, recalculate ALL revenue for that scope | Consistent books | Retroactive changes, accounting nightmare |

**Decision:** Option C as default + Option D as manual utility

**Forward-Only Rate Changes (Default):**
- ScopeLaborDetail is updated with new effective rate (via JSON import or manual edit)
- Existing ApparatusRevenue records stay untouched - they store the rate used at creation
- New apparatus completions use the new rate from ScopeLaborDetail
- Mixed rates within a scope are acceptable and fully auditable

**Retroactive Recalculation (Manual Utility - When Needed):**
- Available for cases where business requires retroactive adjustment
- Process: Void existing ApparatusRevenue (status = Reversed), recreate at new rate
- Triggered manually, not automatic
- Original records preserved for audit trail

**Rationale:**

1. **Business Reality:** Change orders in NETA testing typically add work or adjust future pricing. Retroactive recalculation is the exception (perhaps 10% of cases), not the rule.

2. **Schema Already Supports This:** ApparatusRevenue stores the effective rate at time of creation. This is intentional - it preserves what was actually billed. No versioning fields needed on ScopeLaborDetail.

3. **Audit Trail:** Each ApparatusRevenue record shows exactly what rate was applied. Mixed rates within a scope tell the story: "first 50 at $182/hr, next 50 at $175/hr after change order."

4. **Error Tolerance Alignment:**
   - Default path = low friction (just update ScopeLaborDetail)
   - Recovery path exists (recalculation utility)
   - Audit trail preserved (reversed records kept)

**Effective Labor Rate Calculation:**
```
Effective Rate = (Onsite Labor + Offsite Labor + Travel + Outside Services) ÷ Total Apparatus Hours
```
Every apparatus hour in a scope uses the same effective rate. Different scopes in a project can have different rates.

**Implementation Required:**
- [ ] Verify ScopeLaborDetail can be updated via JSON import without destroying scope structure
- [ ] Document "Update Scope Rates" procedure
- [ ] Future: Build "Recalculate Scope Revenue" utility flow (when needed)

**Reference:** `Documentation/04_Procedures/CHANGE_ORDER_PROCEDURES.md` (to be created)

**Decided By:** Jason Swenson **Date:** December 3, 2025

---

### DDR-003: Revenue Reversal Handling

**Status:** 🟡 DECIDED

**Context:**
Revenue Recognition flow triggers when apparatus completion_status changes to "Complete". It creates an ApparatusRevenue record.

**The Question:**
What happens when someone marks apparatus complete by mistake, then changes it back?

**Original Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: No Reversal** | Revenue record stays. Manual intervention required to clean up. | Simple flow | Orphaned data, overstated revenue |
| **B: Reversal Flow** | Second flow triggers on status change FROM Complete, deletes or marks revenue as "Reversed" | Handles mistakes | Two flows to maintain, edge cases |
| **C: Soft Status on Revenue** | Revenue has status (Pending/Recognized/Reversed). Reversal marks as Reversed, not deleted. | Audit trail | More complex reporting |
| **D: Prevent Accidental Complete** | UI requires confirmation before marking complete, or supervisor approval | Prevents problem | Adds friction to field workflow |

**Decision:** Option D (Two-Stage Completion) + Option C (Soft Status for Edge Cases)

**Two-Stage Completion Model:**

```
Field Tech              Job Lead                Revenue Flow
    │                       │                        │
    │  Marks "Work Done"    │                        │
    │─────────────────────▶│                        │
    │                       │                        │
    │                       │  Reviews & Confirms    │
    │                       │──────────────────────▶│
    │                       │                        │
    │                       │              Creates Revenue
    │                       │              (Batch Process)
```

**Completion Status Values:**

| Status | Value | Who Sets | Revenue Eligible | Meaning |
|--------|-------|----------|------------------|----------|
| Planned | 1 | System | No | Work not started |
| In Progress | 2 | Tech | No | Work underway |
| Work Done | 3 | Tech | No | "I finished this" - awaiting review |
| Confirmed Complete | 4 | Job Lead | **Yes** | Verified, ready for billing |
| On Hold | 5 | Anyone | No | Blocked, waiting on something |

**Revenue Flow Trigger:** Status = 4 (Confirmed Complete) only

**Batch Processing Schedule:**

| Period | Frequency | Rationale |
|--------|-----------|----------|
| Normal operations | Weekly or 2x/week | No urgency, allows review time |
| Month-end (last 3-5 days) | Daily | Financial close needs current numbers |
| Month-end (last day) | On-demand | Final reconciliation |

**Error Windows:**

| Stage | Error Caught By | Recovery |
|-------|-----------------|----------|
| Tech marks wrong item "Work Done" | Job Lead review | Don't confirm, set back to In Progress |
| Job Lead confirms by mistake | Batch hasn't run yet | Un-confirm (set back to Work Done) |
| Revenue already created | Rare edge case | Mark ApparatusRevenue as "Reversed" |

**Rationale:**

1. **Prevention over correction:** Two-stage process catches most errors before revenue exists.

2. **Batch timing creates forgiveness:** Unlike real-time triggers, scheduled batches allow time to catch and fix mistakes.

3. **Aligns with field reality:** Job Leads already review work quality. This formalizes that checkpoint.

4. **Minimal reversal handling needed:** Only truly edge cases require revenue reversal. When needed, soft status (Reversed) preserves audit trail.

5. **"Better, more reliable process"** - Core decision principle. This architecture is more reliable than real-time triggers with complex reversal logic.

**Implementation Required:**
- [ ] Add completion status values (expand from 2 to 5 choices)
- [ ] Update Revenue Recognition flow trigger (Status = 4)
- [ ] Convert flow from real-time to scheduled batch
- [ ] Add "Reversed" status option to ApparatusRevenue
- [ ] Job Lead review UI (list of "Work Done" items pending confirmation)
- [ ] Month-end manual trigger option

**Reference:** `Documentation/01_Architecture/TWO_STAGE_COMPLETION_MODEL.md` (to be created)

**Decided By:** Jason Swenson **Date:** December 3, 2025

---

### DDR-004: Task Requirement for Apparatus

**Status:** 🔴 OPEN

**Context:**
Current schema allows apparatus to exist without a task assignment:
```
Project → Scope → Apparatus (no task)
Project → Scope → Task → Apparatus
```

**The Question:**
Should tasks be required, optional, or conditional?

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Always Required** | Every apparatus must belong to a task | Clean hierarchy, consistent rollups | Extra overhead for simple scopes |
| **B: Always Optional** | Tasks are organizational grouping, not required | Flexibility | Inconsistent data structure, rollup complexity |
| **C: Conditional by Scope Type** | ATS scopes require tasks (complex), MTS scopes don't (simple maintenance) | Right-sized per situation | More complex logic |
| **D: Auto-Create Default Task** | If no task assigned, system creates "General" or "Unassigned" task | Consistent structure | Clutters data with placeholder records |

**Business Questions to Answer:**
- What's the actual use case for apparatus without tasks?
- How are simple maintenance scopes organized in the field?
- Do rollup calculations need to handle both cases?

**Decision:** _________________________

**Rationale:** _________________________

**Decided By:** _____________ **Date:** _____________

---

### DDR-005: Apparatus Type Standardization

**Status:** 🔴 OPEN

**Context:**
Old schema had `cr950_apparatustypemaster` table with standard hours per equipment type (15kV Breaker = 2.5 hrs, etc.). New schema has `cr950_apparatustype` as a free-text string field.

**The Question:**
Should equipment types and standard hours be centrally managed or freeform?

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Freeform (Current)** | Estimator types whatever they want. Hours from estimator spreadsheet. | Maximum flexibility | No standardization, typos, inconsistent reporting |
| **B: Master Table Lookup** | ApparatusTypeMaster defines valid types with default hours. Apparatus references it. | Standardized, reporting-friendly | Must maintain master list, less flexibility |
| **C: Hybrid - Suggest but Allow Override** | Master table provides defaults, but estimator can override hours and add new types | Balance of both | More complex UI, "which hours do I trust?" |
| **D: Choice Field** | Limited picklist of equipment types, no master table | Simple standardization | Can't add new types without schema change |

**Business Questions to Answer:**
- Is equipment type standardization important for reporting? ("How many breakers did we test this year?")
- Do estimators need flexibility to add new equipment types on the fly?
- Are standard hours useful as starting points, or does every job vary too much?

**Decision:** _________________________

**Rationale:** _________________________

**Decided By:** _____________ **Date:** _____________

---

### DDR-006: Data Provenance Tracking

**Status:** 🔴 OPEN

**Context:**
Old schema had `datasource`, `syncstatus`, `lastsyncdate`, `isdeleted` fields on most tables. New schema dropped them.

**The Question:**
Do you need to track where records came from and their sync status?

**Data Sources to Consider:**
- Excel/VBA JSON import (current)
- Manual entry in Power Apps UI (current)
- PowerDB integration (future?)
- API integrations (future?)

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: No Tracking (Current)** | Records are records, doesn't matter where they came from | Simple | Can't answer "how was this created?" |
| **B: DataSource Field Only** | Single choice field: Import/Manual/PowerDB/API | Minimal overhead, answers basic question | No sync tracking |
| **C: Full Provenance** | DataSource + ExternalSystemID + LastSyncDate | Ready for integrations | Fields unused until needed, clutter |
| **D: Add When Needed** | Don't add now, add fields when integration work begins | No premature optimization | Schema change later, data backfill |

**Business Questions to Answer:**
- Is PowerDB integration definitely happening? Timeline?
- Would it be useful to know "this project was imported from Excel" vs "manually created"?
- Is soft-delete (isdeleted flag) needed, or is hard delete acceptable?

**Decision:** _________________________

**Rationale:** _________________________

**Decided By:** _____________ **Date:** _____________

---

### DDR-007: Estimator → Project Conversion Path

**Status:** 🔴 OPEN

**Context:**
Two project creation paths exist:
1. **SharePoint Path:** File saved → Estimator Import Flow → Estimator record created → Manual conversion → Project
2. **JSON Path:** VBA export → JSON file → Node.js import → Project created directly

**The Question:**
Are both paths needed, or is one deprecated?

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Both Paths (Current)** | SharePoint flow for tracking, JSON for actual import | Flexibility | Two systems to maintain, confusion |
| **B: JSON Path Only** | Deprecate SharePoint flow, use only VBA/JSON | Simpler | Lose automatic estimator tracking |
| **C: SharePoint → JSON** | SharePoint triggers file processing, exports JSON, auto-imports | Best of both | More complex flow |
| **D: Estimator = JSON Metadata** | JSON import creates Estimator record AND Project in one pass | Single source of truth | Need to add estimator creation to Node.js |

**Business Questions to Answer:**
- Is the SharePoint Estimator Import Flow actually being used?
- Is tracking estimators (quotes that haven't become projects) valuable?
- Should every project have a linked estimator record for audit trail?

**Decision:** _________________________

**Rationale:** _________________________

**Decided By:** _____________ **Date:** _____________

---

### DDR-008: Security Model - Financial Isolation Verification

**Status:** 🔴 OPEN

**Context:**
Financial tables are separate from operational tables for security purposes. But relationships exist between them (ApparatusRevenue → Apparatus lookup).

**The Question:**
Does the separation actually achieve the security goal?

**Considerations:**
- Dataverse security is primarily table-level, not relationship-level
- A user with access to ApparatusRevenue can traverse the Apparatus lookup
- But can they see Apparatus details, or just the GUID reference?

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: Accept Traversal** | Users who see financial data can follow links to operational data | Simple, natural behavior | May expose more than intended |
| **B: Denormalize into Financial** | Copy apparatus name/type into ApparatusRevenue. No lookup needed for display. | True isolation | Data duplication, sync issues |
| **C: Separate Apps** | Different model-driven apps with different table access per role | Clean separation | More apps to maintain |
| **D: Field-Level Security** | Hide sensitive fields rather than entire tables | Granular control | Complex to configure, performance |

**Needs Investigation:**
- What exactly do field techs need to NOT see?
- Is it dollar amounts? Rates? Margins? All financial data?
- What do location managers need to see that techs don't?

**Decision:** _________________________

**Rationale:** _________________________

**Decided By:** _____________ **Date:** _____________

---

## Decision Log (Completed Items)

| ID | Decision | Date | Rationale |
|----|----------|------|-----------|
| DDR-001 | Soft Commit with Reconciliation | 2025-12-03 | Structure locked at first completion. Reconciliation catches drift. No sync flows - complexity not justified for rare edge case. |
| DDR-002 | Forward-Only Rates + Manual Recalc Utility | 2025-12-03 | Rates update in place; historical revenue preserved. Recalculation available when needed. No versioning complexity. |
| DDR-003 | Two-Stage Completion + Batch Processing | 2025-12-03 | Job Lead review gate + scheduled batch creates error correction windows. Prevention over correction. Reversal only for rare edge cases. |

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-03 | Claude Desktop | DDR-003 resolved - Two-Stage Completion + Batch Processing |
| 2025-12-03 | Claude Desktop | DDR-002 resolved - Forward-Only Rates + Recalc Utility |
| 2025-12-03 | Claude Desktop | DDR-001 resolved - Soft Commit with Reconciliation |
| 2025-12-03 | Claude Desktop | Initial creation - 8 decision items |

---

*This document should be reviewed in every major planning session. Open items are blockers for production deployment.*
