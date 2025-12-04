# Change Order Procedures

**Created:** December 3, 2025  
**Related Decision:** DDR-002 (Rate Versioning Strategy)  
**Status:** DRAFT - Procedures documented, utilities pending implementation

---

## Overview

Change orders occur when project scope, pricing, or terms change after the original PO is issued. This document covers how to handle rate changes in the RESA Power Project Tracker.

**Key Principle:** ScopeLaborDetail represents the contracted PO. Changes update the ScopeLaborDetail; historical revenue records preserve what was actually billed at the time.

---

## Scenario Matrix

| Scenario | Action | Historical Revenue | Future Revenue |
|----------|--------|-------------------|----------------|
| **Add new work (new scope)** | Create new Scope + ScopeLaborDetail | N/A | New rate |
| **Add apparatus to existing scope** | Add apparatus, update ScopeLaborDetail totals | Unchanged | New rate |
| **Rate increase (going forward)** | Update ScopeLaborDetail | Unchanged | New rate |
| **Rate decrease (going forward)** | Update ScopeLaborDetail | Unchanged | New rate |
| **Retroactive rate change** | Update ScopeLaborDetail + Run Recalculation | Voided & Recreated | New rate |

---

## Procedure 1: Add New Work (New Scope)

**When to use:** Customer adds entirely new work that wasn't in original quote.

**Steps:**

1. **Create quote for new work** in Excel Estimator
2. **Export JSON** for the new scope only
3. **Import via Node.js** - select existing project, import new scope
4. **Verify ScopeLaborDetail** created with correct rates
5. **Document** change order number/reference on the scope

**Result:** New scope with its own rate structure, independent of existing scopes.

---

## Procedure 2: Add Apparatus to Existing Scope

**When to use:** More equipment discovered on site that falls under existing scope pricing.

**Steps:**

1. **Add apparatus** to existing task in Dataverse (manual or import)
2. **Update ScopeLaborDetail** totals:
   - New Total Apparatus Hours
   - Recalculated Effective Rate (if quoted amount stays same, rate drops)
   - OR new Quoted Amount (if customer agrees to pay more)
3. **Verify** by checking: `New Quoted Amount ÷ New Total Hours = Expected Rate`

**Result:** Existing completed apparatus keep their rate. New apparatus use updated rate.

**Example:**
```
Before: $10,000 quote ÷ 50 hours = $200/hr
Add 10 hours, customer pays more: $12,000 ÷ 60 hours = $200/hr (rate preserved)
Add 10 hours, same quote: $10,000 ÷ 60 hours = $166.67/hr (rate drops)
```

---

## Procedure 3: Rate Change (Going Forward)

**When to use:** Customer agrees to new rate, applies to future work only.

**Steps:**

1. **Document agreement** (email, change order form)
2. **Update ScopeLaborDetail:**
   - Update component totals (onsite, offsite, travel, outside services)
   - Update total quoted amount
   - Effective Rate recalculates automatically
3. **No action on existing revenue** - it stays at historical rate
4. **Future completions** automatically use new rate

**What happens in the system:**

| Apparatus | Status | Rate Used |
|-----------|--------|-----------|
| #1-50 | Completed before change | $200/hr (preserved) |
| #51-100 | Completed after change | $180/hr (new rate) |

**Reporting note:** Scope will show mixed rates. This is correct and auditable.

---

## Procedure 4: Retroactive Rate Change (Recalculation Required)

**When to use:** Business requires ALL revenue for a scope to reflect new rate.

**⚠️ Use sparingly** - this is the exception, not the rule.

**Steps:**

1. **Update ScopeLaborDetail** with new rate (per Procedure 3)
2. **Run Recalculation Utility:**
   - Utility voids all existing ApparatusRevenue for the scope (Status = Reversed)
   - Utility creates new ApparatusRevenue records at current rate
   - Original records preserved for audit trail
3. **Verify totals** match expected amounts
4. **Document reason** for retroactive change

**Utility Status:** 🔴 NOT YET BUILT

**Manual Workaround (until utility exists):**
1. Export list of completed apparatus in scope
2. For each ApparatusRevenue record:
   - Set Status = Reversed
   - Note reason in description
3. Manually create new ApparatusRevenue records at new rate
   - OR: Set apparatus completion status to "In Progress" then back to "Complete" to re-trigger flow

---

## Procedure 5: Update ScopeLaborDetail via JSON Import

**When to use:** Scope financial structure needs significant update.

**Steps:**

1. **Update Excel Estimator** with new scope financials
2. **Export JSON** for the scope
3. **Import process:**
   - Match to existing scope (by name or ID)
   - Update ScopeLaborDetail fields
   - Do NOT recreate apparatus (structure preserved)
4. **Verify** rates updated correctly

**⚠️ Current limitation:** Import process may need enhancement to support "update existing" vs "create new". Verify behavior before using.

---

## Effective Labor Rate Formula

For reference, the effective labor rate calculation:

```
Effective Labor Rate = Total Quoted Amount ÷ Total Apparatus Hours

Where Total Quoted Amount includes:
├── Onsite Labor Total
│   ├── Blended 10hr Rate hours × rate
│   ├── Blended 12hr Rate hours × rate  
│   ├── OT hours × rate
│   ├── DT hours × rate
│   └── Badging/Parking/Misc
├── Offsite Labor Total
│   ├── Report Hours
│   ├── Project Management
│   └── Loading/Prep/Misc
├── Travel Total
│   ├── Travel Hours
│   ├── Hotel & Per Diem
│   ├── Flights
│   └── Car Rental
└── Outside Services Total
    ├── Generator Rental
    ├── Test Equipment Rental
    └── Lab Services (Oil Samples, etc.)
```

**Key point:** Every apparatus hour in a scope uses the same effective rate. The blended rate absorbs all cost categories.

---

## Audit Trail

The system maintains audit trail through:

| Record | What It Shows |
|--------|---------------|
| ApparatusRevenue.EffectiveRate | Rate that was applied when created |
| ApparatusRevenue.DateCreated | When revenue was recognized |
| ApparatusRevenue.Status | Active, Reversed |
| ScopeLaborDetail.ModifiedOn | When rates were last changed |
| Dataverse Audit Log | Who changed what, when |

**Mixed rates within a scope are not a problem** - they're documentation of what happened.

---

## Error Recovery

| Problem | Solution |
|---------|----------|
| Wrong rate on ScopeLaborDetail | Update it; future revenue uses new rate |
| Apparatus completed at wrong rate | Either accept (it's documented) OR run recalculation |
| ScopeLaborDetail missing entirely | Create via import or manual entry |
| Revenue record created incorrectly | Set to Reversed, create correct one |

---

## Implementation Checklist

**Available Now:**
- [x] Update ScopeLaborDetail manually in Dataverse
- [x] Revenue records store rate at creation (audit trail)
- [x] New completions use current ScopeLaborDetail rate

**Needs Building:**
- [ ] ScopeLaborDetail update via JSON import (verify/enhance)
- [ ] Recalculation utility (void + recreate revenue)
- [ ] Reporting that handles mixed rates gracefully

---

## Related Documents

- `Documentation/01_Architecture/DESIGN_DECISION_REGISTER.md` - DDR-002
- `Documentation/01_Architecture/ERROR_TOLERANCE_FRAMEWORK.md`
- `Documentation/06_Implementation_Guides/REVENUE_RECOGNITION_FLOW_SPEC_V2.md`

---

*This document should be updated as procedures are tested and utilities are built.*
