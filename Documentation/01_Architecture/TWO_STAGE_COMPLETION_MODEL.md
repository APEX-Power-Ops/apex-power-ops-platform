# Two-Stage Completion Model

**Created:** December 3, 2025  
**Related Decision:** DDR-003 (Revenue Reversal Handling)  
**Status:** APPROVED - Implementation pending

---

## Overview

The Two-Stage Completion Model separates "work done" from "billable complete" through a Job Lead review gate. Combined with batch revenue processing, this creates natural error correction windows and a more reliable workflow.

**Core Principle:** Prevention is better than correction. Catch errors before they create financial records.

---

## The Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETION WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   FIELD TECH                JOB LEAD                  REVENUE FLOW          │
│   ──────────                ────────                  ────────────          │
│                                                                             │
│   ┌─────────────┐                                                           │
│   │   Planned   │  (Import creates apparatus)                               │
│   └──────┬──────┘                                                           │
│          │                                                                  │
│          ▼                                                                  │
│   ┌─────────────┐                                                           │
│   │ In Progress │  (Optional - tech starts work)                            │
│   └──────┬──────┘                                                           │
│          │                                                                  │
│          ▼                                                                  │
│   ┌─────────────┐         ┌─────────────┐                                   │
│   │  Work Done  │────────▶│   Review    │  (Job Lead validates)             │
│   └─────────────┘         └──────┬──────┘                                   │
│                                  │                                          │
│                    ┌─────────────┼─────────────┐                            │
│                    │             │             │                            │
│                    ▼             ▼             ▼                            │
│             ┌──────────┐  ┌──────────┐  ┌──────────┐                        │
│             │ Rejected │  │ On Hold  │  │Confirmed │                        │
│             │(→In Prog)│  │          │  │ Complete │                        │
│             └──────────┘  └──────────┘  └────┬─────┘                        │
│                                              │                              │
│                                              ▼                              │
│                                    ┌─────────────────┐                      │
│                                    │ Revenue Flow    │  (Scheduled batch)   │
│                                    │ Creates Revenue │                      │
│                                    └─────────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Completion Status Values

| Status | Value | Set By | Mobile UI | Revenue Eligible |
|--------|-------|--------|-----------|------------------|
| **Planned** | 1 | System | View only | No |
| **In Progress** | 2 | Tech | ✓ Tap to set | No |
| **Work Done** | 3 | Tech | ✓ Tap to set | No |
| **Confirmed Complete** | 4 | Job Lead | ✓ (Lead only) | **Yes** |
| **On Hold** | 5 | Anyone | ✓ Tap to set | No |

### Status Transitions

| From | To | Who | When |
|------|----|-----|------|
| Planned | In Progress | Tech | Starting work |
| Planned | Work Done | Tech | Quick jobs, skip In Progress |
| In Progress | Work Done | Tech | Finished testing |
| In Progress | On Hold | Anyone | Blocked |
| Work Done | Confirmed Complete | Job Lead | Review passed |
| Work Done | In Progress | Job Lead | Review failed (needs rework) |
| Work Done | On Hold | Anyone | Issue discovered |
| Confirmed Complete | Work Done | Job Lead | Error found, needs re-review |
| On Hold | In Progress | Anyone | Block cleared |

---

## Role Responsibilities

### Field Technician
- Marks apparatus "In Progress" when starting (optional)
- Marks apparatus "Work Done" when testing complete
- Can set "On Hold" if blocked
- **Cannot** mark "Confirmed Complete"
- **Cannot** undo "Confirmed Complete"

### Job Lead
- Reviews all "Work Done" items for their job
- Validates work quality, documentation complete
- Marks "Confirmed Complete" to approve for billing
- Can reject back to "In Progress" with reason
- Can un-confirm if error found before billing

### Revenue Flow (System)
- Runs on schedule (batch process)
- Processes only "Confirmed Complete" items
- Creates ApparatusRevenue records
- Does not run in real-time

---

## Error Windows

The two-stage model creates three natural error correction windows:

### Window 1: Before Job Lead Review
**Duration:** Until Job Lead reviews  
**Error caught by:** Job Lead  
**Recovery:** Don't confirm; set back to In Progress

```
Tech accidentally marks Apparatus #47 "Work Done"
→ Job Lead sees it in review queue
→ Job Lead: "This isn't done, tests missing"
→ Sets back to In Progress
→ No revenue impact
```

### Window 2: After Confirmation, Before Batch
**Duration:** Until next batch run (could be hours or days)  
**Error caught by:** Job Lead, PM, or Tech  
**Recovery:** Set back to "Work Done"

```
Job Lead confirms Apparatus #47
→ Next day, realizes test data was from wrong unit
→ Sets back to "Work Done"
→ Revenue flow hasn't run yet
→ No revenue impact
```

### Window 3: After Revenue Created
**Duration:** Post-batch  
**Error caught by:** Anyone  
**Recovery:** Mark ApparatusRevenue as "Reversed"

```
Revenue created for Apparatus #47
→ Week later, audit finds error
→ Mark ApparatusRevenue status = "Reversed"
→ Create correcting entry if needed
→ Original record preserved for audit trail
```

**Expected frequency by window:**
- Window 1: ~80% of errors caught
- Window 2: ~15% of errors caught
- Window 3: ~5% of errors (rare)

---

## Batch Processing Schedule

### Normal Operations

| Day | Flow Runs? | Notes |
|-----|------------|-------|
| Monday | No | Week's work accumulating |
| Tuesday | **Yes** | First batch of week |
| Wednesday | No | |
| Thursday | No | |
| Friday | **Yes** | Second batch of week |
| Saturday | No | |
| Sunday | No | |

### Month-End (Last 5 Business Days)

| Day | Flow Runs? | Notes |
|-----|------------|-------|
| Day -5 | **Yes** | Start daily runs |
| Day -4 | **Yes** | |
| Day -3 | **Yes** | |
| Day -2 | **Yes** | |
| Day -1 (Last day) | **Yes** + On-demand | Final reconciliation |

### Manual Trigger
- Available to: PM, Operations Manager
- Use case: Month-end final run, special circumstances
- Button in Power Apps: "Run Revenue Recognition Now"

---

## Job Lead Review Interface

### Queue View: "Work Done - Pending Review"

| Project | Scope | Task | Apparatus | Tech | Date Marked | Hours |
|---------|-------|------|-----------|------|-------------|-------|
| Hospital | Switchgear | MV Breakers | CB-001 | J.Smith | Dec 2 | 4.0 |
| Hospital | Switchgear | MV Breakers | CB-002 | J.Smith | Dec 2 | 4.0 |
| Hospital | Switchgear | Transformers | TX-001 | M.Jones | Dec 3 | 8.0 |

### Actions per item:
- **Confirm** → Status = Confirmed Complete
- **Reject** → Status = In Progress (with reason)
- **Hold** → Status = On Hold (with reason)

### Bulk Actions:
- **Confirm All** for a Task/Scope
- **Confirm Selected** (checkbox selection)

---

## Revenue Status Values

| Status | Value | Meaning |
|--------|-------|---------|
| **Recognized** | 1 | Active revenue record |
| **Reversed** | 2 | Voided due to error |
| **Pending** | 3 | (Future: if approval workflow needed) |

When reversing:
- Original record stays with Status = Reversed
- Reversal date/reason captured
- New correcting record created if needed
- Audit trail preserved

---

## Benefits

1. **Error Prevention**
   - 95% of errors caught before financial impact
   - Natural quality gate aligns with existing practice

2. **Reduced Complexity**
   - No real-time reversal logic needed
   - Single flow, scheduled batch
   - Simple status progression

3. **Audit Trail**
   - Clear who approved what, when
   - Historical revenue records preserved
   - Status changes tracked

4. **Flexible Timing**
   - Normal operations: low urgency, weekly batches
   - Month-end: ramp up to daily
   - On-demand: when needed

5. **Field-Friendly**
   - Techs mark "done" quickly (no friction)
   - Confirmation is Job Lead's job, not Tech's
   - Mobile-optimized for Tech workflow

---

## Implementation Checklist

### Schema Changes
- [ ] Add completion status choices (1-5) to Apparatus
- [ ] Add revenue status choices (1-3) to ApparatusRevenue
- [ ] Add DateConfirmed field to Apparatus
- [ ] Add ConfirmedBy lookup to Apparatus (→ User)
- [ ] Add ReversalDate field to ApparatusRevenue
- [ ] Add ReversalReason field to ApparatusRevenue

### Flow Changes
- [ ] Update trigger: Status = 4 (not 2)
- [ ] Convert to scheduled (not real-time)
- [ ] Add manual trigger option
- [ ] Update duplicate check logic

### UI Changes
- [ ] Tech mobile: Show status progression
- [ ] Tech mobile: "Work Done" button (fast, 1 tap)
- [ ] Job Lead: Review queue view
- [ ] Job Lead: Bulk confirm capability
- [ ] PM: Manual flow trigger button

### Reporting
- [ ] "Pending Review" count by project
- [ ] "Confirmed but Not Yet Billed" (batch pending)
- [ ] Revenue by status (Recognized vs Reversed)

---

## Related Documents

- `Documentation/01_Architecture/DESIGN_DECISION_REGISTER.md` - DDR-003
- `Documentation/01_Architecture/ERROR_TOLERANCE_FRAMEWORK.md`
- `Documentation/04_Procedures/CHANGE_ORDER_PROCEDURES.md`

---

*This model was adopted because it creates a "better, more reliable process" - the core decision principle for this system.*
