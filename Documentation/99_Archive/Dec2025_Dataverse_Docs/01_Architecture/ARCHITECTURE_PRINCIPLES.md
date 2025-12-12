# RESA Power Project Tracker - Architecture Principles

**Created:** December 3, 2025  
**Last Updated:** December 3, 2025 (Principles 9-10 added)  
**Purpose:** Foundational rules that guide all design decisions

---

## Why This Document Exists

This system is being built without formal specifications from the business. The architect (Jason) is discovering requirements as he builds, based on real operational needs. This document captures the principles that guide decisions when there's no spec to reference.

**When in doubt, check these principles.**

---

## Core Principles

### Principle 1: Zero Bottlenecks

> *"The system works without PM intervention."*

- Field technicians update their own status
- Flows trigger automatically, no manual steps
- Information flows up without someone having to pull it
- If a process requires a specific person to be available, redesign it

**Test:** Can the system function for a week if the PM is on vacation?

---

### Principle 2: Separation of Concerns

> *"If I don't know who should see what, keep it separate."*

- **Operational tables** (Projects, Scopes, Tasks, Apparatus) = Field work
- **Financial tables** (ApparatusRevenue, ScopeFinancialSummary, ProjectFinancialSummary) = Money
- Separation enables table-level security without complex configuration
- Better to over-separate now than try to untangle later

**Test:** Can you grant "field tech" access without touching financial tables?

---

### Principle 3: Denormalize for Performance

> *"The UI should never wait for the database."*

- Apparatus has direct links to Project, Client, Site (not just Scope)
- Avoids multi-level joins for common queries
- Accept that denormalized data could drift (but design to minimize it)
- Speed of daily operations > perfect normalization

**Test:** Can you show apparatus with project name in one query?

---

### Principle 4: Work With Constraints, Not Against Them

> *"Excel Estimator is a staple. Optimize around it."*

- Some legacy tools can't be replaced immediately
- Build bridges (VBA export, JSON import) rather than demanding change
- Reduce friction in existing workflows while enabling new ones
- When the business is ready to change, the system should be ready too

**Test:** Does the new system make existing workflows easier, not harder?

---

### Principle 5: Build for Discovery

> *"I don't know everything I need yet."*

- The schema will evolve. Design for change.
- Document decisions so future changes have context
- Question everything - if it can't be justified, reconsider it
- External audits (Claude reviews) catch what internal bias misses

**Test:** Can you explain WHY each table/field exists?

---

### Principle 6: Reliability Over Speed

> *"I value reliability and consistency over speed."*

- Don't rush to implement; implement correctly
- Checkpoint documentation before rushing ahead
- If a feature is half-built, it's a liability
- Production deployment only when fully tested

**Test:** Would you bet your job on this working correctly?

---

### Principle 7: Audit Trail Everything Financial

> *"If money is involved, we need to prove what happened."*

- Revenue recognition must be traceable
- Date stamps on all financial events
- No silent overwrites of financial data
- When in doubt, add a timestamp field

**Test:** Can you explain to an auditor how each revenue dollar was calculated?

---

### Principle 8: Mobile-First for Field Work

> *"3 taps, 15 seconds to complete apparatus status."*

- Field technicians are on job sites, not at desks
- Every field interaction should be thumb-friendly
- Minimize required fields for status updates
- Save the complexity for office dashboards

**Test:** Can a technician update status while holding a flashlight?

---

### Principle 9: Design for Error Tolerance

> *"People will make a mistake at every step in this process, and more than once."*

- Prevention adds friction - use sparingly
- Detection is the primary strategy - low friction, fast feedback
- Recovery must always exist - never paint into a corner
- Documentation at minimum - know what happened

The Error Tolerance Pyramid (top to bottom):
1. **PREVENT** - Stop before it happens (high friction, use sparingly)
2. **DETECT** - Surface quickly (low friction, primary strategy)
3. **RECOVER** - Path to fix (always required)
4. **DOCUMENT** - Audit trail (minimum baseline)

**Test:** For any error scenario, can you answer: "How does someone fix this?"

**Reference:** `Documentation/01_Architecture/ERROR_TOLERANCE_FRAMEWORK.md`

---

### Principle 10: Better and More Reliable Wins

> *"Does this create a better, more reliable process?"*

This is the ultimate decision test. When evaluating options:

- "Better" = less friction on the happy path, easier to use
- "More reliable" = fewer failure modes, errors caught earlier
- When in conflict, reliability usually wins
- Document the tradeoff either way

This principle drives architecture choices like:
- Two-stage completion (prevention over correction)
- Batch processing (forgiveness windows over real-time complexity)
- Soft commits (flexibility until it matters)

**Test:** Would you trust this process to work correctly for 1,000 apparatus without babysitting?

---

## Schema Conventions

### Naming Conventions (V2)

| Element | Convention | Example |
|---------|------------|---------|
| Table logical name | `cr950_entityname` (lowercase) | `cr950_apparatus` |
| Field logical name | `cr950_entityfieldname` (no underscores) | `cr950_apparatusname` |
| Lookup field | `cr950_EntityTarget` or `cr950_entity_targetid` | `cr950_apparatus_projectid` |
| Primary field | `cr950_entityname` | `cr950_apparatusname` |
| EntitySetName (plural) | `cr950_entitynames` | `cr950_apparatuses` |

### Environment

| Property | Value |
|----------|-------|
| **Production (Current Dev)** | org7bdbc942.crm.dynamics.com |
| **Deprecated** | org99cd6c6e.crm.dynamics.com |
| **Deprecated** | org284447bd.crm.dynamics.com |

---

## Decision Authority

| Decision Type | Authority | Documentation |
|---------------|-----------|---------------|
| Schema changes (new tables/fields) | Jason | Design Decision Register |
| Workflow changes | Jason | Flow Spec documents |
| Security model | Jason | Design Decision Register |
| Naming conventions | Established (above) | This document |
| UI/UX changes | Jason | N/A (iterate as needed) |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `DESIGN_DECISION_REGISTER.md` | Open questions requiring decisions |
| `SCHEMA_GAP_REPORT_*.md` | Delta between versions |
| `WORKFLOW_INTEGRATION_ANALYSIS.md` | How components connect |
| `CLAUDE_NOTES.md` | Quick context for AI assistants |

---

## Revision History

| Date | Changes |
|------|---------|
| 2025-12-03 | Initial creation from accumulated context |

---

*These principles should be reviewed when making any significant design decision. If a proposed change conflicts with a principle, either change the proposal or explicitly document why the principle doesn't apply.*
