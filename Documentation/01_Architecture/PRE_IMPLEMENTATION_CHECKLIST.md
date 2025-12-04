# Pre-Implementation Review Checklist

**Purpose:** Force discussion of design decisions BEFORE building  
**When to Use:** Before starting any significant development work

---

## Instructions

Before implementing any new feature, workflow, or schema change:

1. Answer each applicable question below
2. If you can't answer confidently, check the Design Decision Register
3. If no decision exists, ADD it to the register and discuss before building
4. Sign off at the bottom when complete

---

## The Checklist

### Data Model Questions

- [ ] **Does this create new relationships between tables?**
  - If yes: Are they documented? Do they need denormalized copies for performance?
  - Related DDR: DDR-001 (Denormalized Field Sync)

- [ ] **Does this involve financial data (rates, amounts, revenue)?**
  - If yes: Is it in a financial table (separated from operational)?
  - Is there an audit trail (timestamps, who changed what)?
  - Related DDR: DDR-002 (Rate Versioning), DDR-008 (Security Model)

- [ ] **Does this add a new table?**
  - If yes: Does it follow V2 naming conventions?
  - Is it documented in the schema?
  - What's the EntitySetName (plural form)?

- [ ] **Does this change an existing table?**
  - If yes: Is the change backward compatible with existing data?
  - Do any flows/apps need updating?

### Workflow Questions

- [ ] **Does this require a new Power Automate flow?**
  - If yes: What triggers it?
  - What happens if it fails?
  - Is there duplicate prevention?

- [ ] **Does this modify an existing flow?**
  - If yes: Is the flow spec document updated?
  - Has the old behavior been documented for comparison?

- [ ] **Can this workflow fail silently?**
  - If yes: How will you know it failed?
  - Who gets notified?

- [ ] **Does this workflow involve status changes?**
  - If yes: What happens if status changes back? (DDR-003)
  - Is there reversal handling?

### UI/UX Questions

- [ ] **Will field technicians use this?**
  - If yes: Can it be done in 3 taps / 15 seconds?
  - Does it work on mobile?

- [ ] **Does this expose financial information?**
  - If yes: Should field techs see this?
  - Is it properly secured?

### Integration Questions

- [ ] **Does this affect the VBA → JSON → Node.js import path?**
  - If yes: Does the JSON schema need updating?
  - Does `page.tsx` need updating?

- [ ] **Does this create data that needs to exist for other features to work?**
  - Example: ScopeLaborDetail must exist for Revenue Recognition
  - If yes: Where/when is it created?

### Consistency Questions

- [ ] **Have you checked if this problem is already solved in the old schema?**
  - V1.5.1.3 had many features. Don't reinvent if the pattern was good.

- [ ] **Does this align with the Architecture Principles?**
  - Zero Bottlenecks?
  - Separation of Concerns?
  - Reliability Over Speed?

- [ ] **Will this decision need to be revisited?**
  - If yes: Add it to the Design Decision Register as a future item

---

## Sign-Off

| Role | Name | Date | Notes |
|------|------|------|-------|
| **Designer/Builder** | | | |
| **Reviewer (if applicable)** | | | |

---

## Quick Reference: Design Decision Register Items

| ID | Topic | Status |
|----|-------|--------|
| DDR-001 | Denormalized Field Sync Strategy | 🟡 DECIDED |
| DDR-002 | Rate Versioning Strategy | 🟡 DECIDED |
| DDR-003 | Revenue Reversal Handling | 🟡 DECIDED |
| DDR-004 | Task Requirement for Apparatus | 🔴 OPEN |
| DDR-005 | Apparatus Type Standardization | 🔴 OPEN |
| DDR-006 | Data Provenance Tracking | 🔴 OPEN |
| DDR-007 | Estimator → Project Conversion Path | 🔴 OPEN |
| DDR-008 | Security Model - Financial Isolation | 🔴 OPEN |

**If your work touches any of these areas and the status is OPEN, resolve the decision first.**

---

*This checklist exists because it's easier to answer questions before building than to rebuild after discovering a flaw.*
