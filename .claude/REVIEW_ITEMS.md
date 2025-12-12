# Review Items & Considerations

Quick capture for ideas, questions, and decisions that arise during sessions but shouldn't derail current focus.

**How to Use:**
- Add items when they come up (don't overthink format)
- Include date and brief context
- Periodically review: promote to tasks, resolve, or discard
- Mark items `[RESOLVED]` with outcome rather than deleting

---

## Pending Schema Decisions

### Assessment Enum Values
**Added:** 2025-12-11  
**Context:** Excel tracker analysis revealed NETA assessment values not in current enum

- Current enum: `Pass`, `Fail`, `N/A`
- Excel uses: `ACCEPTABLE`, `NON-SERVICEABLE`, `MINOR DEFICIENCY`
- **Question:** Add new values alongside existing? Replace? Map old→new?

### Billing Calculations - Store vs Derive
**Added:** 2025-12-11  
**Context:** Excel trackers have 20+ billing-related columns

- Store calculated values in database?
- Or derive via views/queries at runtime?
- Consider: audit trail, performance, sync complexity

### Priority Field Type
**Added:** 2025-12-11  
**Context:** Need priority for apparatus/task scheduling

- Integer (1, 2, 3) - flexible, sortable
- Enum (High, Medium, Low) - self-documenting, constrained
- **Leaning:** Integer with view that adds labels

---

## Integration Questions

### CRM Job Number Lookup
**Added:** 2025-12-11  
**Context:** Manual Job # entry from CRM into project records

- Is API query possible from CRM?
- Or always manual entry?
- Affects: project creation workflow

### n8n Workflow Automation
**Added:** 2025-12-11  
**Context:** Discussed as option for notifications, reports, QuickBooks sync

- Worth exploring for MVP?
- Or defer until core platform stable?
- **Leaning:** Defer - focus on core first

---

## Ideas to Explore

### v0.dev for UI Components
**Added:** 2025-12-11  
**Context:** Generates shadcn/ui + Tailwind code from prompts

- Good for rapid prototyping dashboard layouts
- Could accelerate UI development
- Try: operations dashboard mockup

### NETA/SOP Resource Linking
**Added:** 2025-12-10  
**Context:** Auto-link apparatus types to relevant procedures

- Tables needed: `neta_procedures`, `sops`, junction table
- Add section references to `apparatus_types`
- **Status:** Discussed, not yet designed

---

## Resolved Items

_Move items here when decided, with outcome noted_

<!-- Example:
### [RESOLVED] Database Platform Choice
**Added:** 2025-12-01 | **Resolved:** 2025-12-05  
**Decision:** Supabase (PostgreSQL)  
**Rationale:** API-ready, real-time, Row Level Security, generous free tier
-->
