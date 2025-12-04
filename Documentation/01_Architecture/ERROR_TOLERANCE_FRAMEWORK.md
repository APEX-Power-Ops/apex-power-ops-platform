# Error Tolerance Design Framework

**Created:** December 3, 2025  
**Author:** Jason Swenson / Claude  
**Status:** FOUNDATIONAL - Applies to All Design Decisions

---

## Core Philosophy

> **"People will make a mistake at every step in this process, and more than once."**

This system must be designed with the assumption that errors are **inevitable**, not exceptional. The goal is not to prevent all errors (impossible) but to:

1. **Minimize friction** on the happy path (don't punish everyone for potential mistakes)
2. **Make errors visible** quickly (detection over prevention where possible)
3. **Make recovery straightforward** (not catastrophic to fix)

---

## The Error Tolerance Pyramid

```
                    ▲
                   /|\
                  / | \
                 /  |  \
                / PREVENT \        ← Use sparingly (adds friction)
               /    |      \
              /─────|───────\
             /   DETECT      \     ← Primary strategy (low friction, fast feedback)
            /       |         \
           /────────|──────────\
          /      RECOVER        \  ← Always have a path (never paint into corner)
         /          |            \
        /───────────|─────────────\
       /        DOCUMENT           \ ← At minimum (know what happened)
      /─────────────────────────────\
```

### Prevention
- Stops errors before they happen
- **Cost:** Adds friction, slows workflow, frustrates users
- **Use when:** Error is catastrophic AND unrecoverable AND common
- **Example:** Requiring confirmation before deleting a project with revenue

### Detection
- Allows errors but surfaces them quickly
- **Cost:** Low friction, but requires monitoring/review
- **Use when:** Error is recoverable AND visibility enables quick action
- **Example:** Reconciliation report showing mismatched project references

### Recovery
- Provides a path to fix errors after they occur
- **Cost:** Some effort to fix, but not catastrophic
- **Use when:** Always - every error should have a recovery path
- **Example:** Ability to un-complete apparatus and void the revenue record

### Documentation
- Records what happened for audit/troubleshooting
- **Cost:** Minimal
- **Use when:** Always - even if you can't prevent/detect/recover, know what happened
- **Example:** Audit log of who changed what, when

---

## Error Mapping: Every Step Where Things Go Wrong

### Phase 1: Estimating (Excel)

| Error | Likelihood | Impact | Current Safeguard | Recommended Approach |
|-------|------------|--------|-------------------|---------------------|
| Wrong client name | High | Medium | None | DETECT: Validate against existing clients during import |
| Wrong site address | Medium | Low | None | RECOVER: Editable after import |
| Incorrect hours per apparatus | High | High | None | DETECT: Flag outliers (e.g., >20 hrs per unit) |
| Wrong scope type (ATS vs MTS) | Medium | Medium | None | RECOVER: Editable until first completion |
| Duplicate apparatus entries | High | Medium | None | DETECT: Warning during import review |
| Math errors in quoted amount | Medium | High | Excel formulas | DETECT: Compare quoted vs. calculated in import |

### Phase 2: VBA Export

| Error | Likelihood | Impact | Current Safeguard | Recommended Approach |
|-------|------------|--------|-------------------|---------------------|
| Export wrong worksheet | Medium | High | None | PREVENT: Validate worksheet structure before export |
| Corrupted JSON output | Low | High | None | DETECT: JSON schema validation in Node.js |
| Missing required fields | Medium | High | None | DETECT: Node.js validates before showing preview |
| Wrong file selected for import | Medium | High | None | PREVENT: Show project name/client in confirmation |

### Phase 3: Node.js Import (page.tsx)

| Error | Likelihood | Impact | Current Safeguard | Recommended Approach |
|-------|------------|--------|-------------------|---------------------|
| Create under wrong client | Medium | High | None | DETECT: Show client in preview, require confirmation |
| Duplicate project created | Medium | High | None | PREVENT: Check for existing project with same name/number |
| Task assignment mistakes | High | Medium | Manual review | RECOVER: Reassign apparatus to tasks post-import |
| Wrong scope → apparatus mapping | Medium | High | Visual preview | DETECT: Summary counts in preview |
| Import fails midway | Low | High | None | RECOVER: Transaction rollback or cleanup utility |
| ScopeLaborDetail not created | Certain | Critical | **NONE - GAP** | PREVENT: Add to import process |

### Phase 4: Data Corrections (Post-Import)

| Error | Likelihood | Impact | Current Safeguard | Recommended Approach |
|-------|------------|--------|-------------------|---------------------|
| Edit wrong record | High | Variable | None | DOCUMENT: Audit log of changes |
| Delete record with children | Medium | High | Dataverse relationship | PREVENT: Restrict delete or cascade warning |
| Change completed apparatus | Medium | High | None | DETECT: Flag changes to completed items |
| Orphan records after delete | Low | Medium | None | DETECT: Periodic orphan report |

### Phase 5: Field Operations (Technician Updates)

| Error | Likelihood | Impact | Current Safeguard | Recommended Approach |
|-------|------------|--------|-------------------|---------------------|
| Mark wrong apparatus complete | High | Medium | None | RECOVER: Allow un-complete with revenue reversal |
| Enter wrong hours | High | Medium | None | DETECT: Flag outliers, RECOVER: Edit before billing |
| Complete apparatus on wrong project | Low | High | App shows project context | PREVENT: Confirmation showing project name |
| Accidental double-tap (duplicate completion) | Medium | Low | Flow duplicate check | PREVENT: Already handled ✓ |

### Phase 6: Revenue Recognition (Flow)

| Error | Likelihood | Impact | Current Safeguard | Recommended Approach |
|-------|------------|--------|-------------------|---------------------|
| Rate lookup fails (no ScopeLaborDetail) | Certain* | Critical | Flow terminates | PREVENT: Ensure ScopeLaborDetail exists at import |
| Wrong rate applied | Low | High | Single source (ScopeLaborDetail) | DOCUMENT: Store rate used on revenue record |
| Revenue created for wrong project | Low | High | Denormalized lookup | DETECT: Reconciliation report |
| Duplicate revenue (flow runs twice) | Low | High | Duplicate check | PREVENT: Already handled ✓ |

*Currently certain because ScopeLaborDetail isn't created during import

### Phase 7: Reporting & Billing

| Error | Likelihood | Impact | Current Safeguard | Recommended Approach |
|-------|------------|--------|-------------------|---------------------|
| Bill with incorrect totals | Low | Critical | Rollup fields | DETECT: Manual review before sending |
| Report includes voided revenue | Low | Medium | None | PREVENT: Filter by status |
| Missing revenue (apparatus complete but no revenue record) | Low | High | None | DETECT: Reconciliation report |

---

## Standard Safeguard Patterns

### Pattern 1: Confirmation with Context

**When:** User is about to do something significant (delete, complete, submit)

**Implementation:**
- Show exactly what will happen: "Mark 'Transformer T-1' complete? This will create revenue of ~$X"
- Include identifying context: Project name, scope name, not just record ID
- Require explicit action (not just Enter key)

**Applies to:**
- Completing apparatus
- Deleting records with children
- Importing projects
- Changing financial data

---

### Pattern 2: Soft State with Hard Commit

**When:** Workflow has a natural "point of no return"

**Implementation:**
- Allow free editing until commit point
- Clear visual indicator of committed vs. draft state
- Commit requires confirmation
- Post-commit changes require elevated action or leave audit trail

**Commit Points in This System:**
| Entity | Commit Trigger | What Locks |
|--------|---------------|------------|
| Apparatus | First completion | Cannot delete, limited edits |
| Scope | First apparatus completion | Cannot change project |
| Project | First revenue recognized | Cannot delete |
| Revenue Record | Created | Immutable (void, don't edit) |

---

### Pattern 3: Reconciliation Reports

**When:** Data consistency can drift and periodic check is acceptable

**Implementation:**
- Saved views or reports that surface inconsistencies
- Run on schedule or on-demand
- Clear action path when issues found

**Reconciliation Reports Needed:**
| Report | What It Checks | Frequency |
|--------|---------------|-----------|
| Structure Integrity | Apparatus.Project matches Apparatus.Scope.Project | Weekly |
| Orphan Records | Tasks with no apparatus, Scopes with no tasks | Weekly |
| Revenue Completeness | Completed apparatus with no revenue record | Daily |
| Hours Outliers | Apparatus with hours >2x type standard | On import |
| Missing Labor Detail | Scopes with no ScopeLaborDetail | On import |

---

### Pattern 4: Reversible Actions

**When:** Users need to "undo" but true undo isn't practical

**Implementation:**
- Don't delete - mark as voided/reversed
- Create offsetting records rather than editing
- Preserve audit trail

**Reversible Action Patterns:**
| Action | Reversal Method | Audit Trail |
|--------|-----------------|-------------|
| Complete apparatus | Set status back to In Progress | Keep completion date, add reversal date |
| Create revenue | Mark revenue status as "Reversed" | Keep record, add reversal date |
| Delete apparatus | Soft delete (is_deleted flag) or restrict if completed | Deleted_date, deleted_by |

---

### Pattern 5: Outlier Detection

**When:** Valid range is known and outliers likely indicate error

**Implementation:**
- Flag but don't prevent
- Visual indicator (yellow/orange warning, not red error)
- Allow override with confirmation

**Outlier Rules:**
| Field | Expected Range | Flag If |
|-------|---------------|---------|
| Apparatus hours | 0.5 - 16 | < 0.25 or > 20 |
| Quoted amount | $1,000 - $500,000 | < $500 or > $1,000,000 |
| Apparatus count per scope | 5 - 200 | < 1 or > 500 |
| Effective rate | $200 - $500/hr | < $100 or > $750 |

---

## Implementation Priority

### Immediate (Before More Projects Imported)

| Safeguard | Pattern | Effort |
|-----------|---------|--------|
| Add ScopeLaborDetail to import | Prevention | Medium |
| Duplicate project check | Prevention | Low |
| Import preview with totals | Detection | Low |

### Short-Term (Before Field Use)

| Safeguard | Pattern | Effort |
|-----------|---------|--------|
| Un-complete apparatus + revenue reversal | Recovery | Medium |
| Completion confirmation with context | Prevention | Low |
| Structure integrity report | Detection | Low |

### Medium-Term (Before Billing)

| Safeguard | Pattern | Effort |
|-----------|---------|--------|
| Revenue completeness report | Detection | Low |
| Orphan record report | Detection | Low |
| Change audit log | Documentation | Medium |

### Long-Term (System Maturity)

| Safeguard | Pattern | Effort |
|-----------|---------|--------|
| Outlier flagging on import | Detection | Medium |
| Soft delete pattern | Recovery | Medium |
| Full audit trail | Documentation | High |

---

## Decision: DDR-001 Resolution

Based on this framework, the recommendation for **Denormalized Field Sync** is:

**Decision:** Combination of Soft Commit + Reconciliation

1. **Before first completion:** Structure is editable (fix mistakes easily)
2. **After first completion:** Structure locked (business rule, UI enforced)
3. **Reconciliation report:** Catches any drift that occurs
4. **No cascade sync flows:** Complexity not justified

**Rationale:**
- Errors at setup are DETECTED (preview) and RECOVERABLE (edit before commit)
- Errors after work starts are DETECTED (reconciliation) and DOCUMENTED (audit)
- No friction added to happy path
- Clear point of no return that aligns with business reality

---

## Next Steps

1. Update DDR-001 in Design Decision Register with this decision
2. Add reconciliation report to build backlog
3. Add "first completion" lock logic to UI requirements
4. Continue through remaining DDR items with this framework

---

*This framework should be referenced when making any design decision. Ask: "What's the error scenario? Which level of the pyramid is appropriate?"*
