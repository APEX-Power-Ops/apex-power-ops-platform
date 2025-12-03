# RESA Power - Active Handoffs

**Last Updated:** December 2, 2025, 6:45 PM

---

## 📋 Handoff Queue

*No active handoffs at this time. Jason is preparing workload split.*

---

## Template: Creating a Handoff

When you need to pass work to another Claude instance, use this format:

```markdown
---

## TO: [VS Claude / Web Claude]

### Task: [Clear, specific task name]

**Priority:** P0 / P1 / P2  
**Created:** [Date/Time]  
**Created By:** [Web Claude / VS Claude]

**Context:**
[2-3 sentences explaining the background needed to complete this task]

**Deliverable:**
[Specific output expected - file, code, configuration, etc.]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Files to Reference:**
- `path/to/file1.md`
- `path/to/file2.md`

**Files to Create/Update:**
- `path/to/output.md`

**Dependencies:**
- [What must be done before this can start]

**Notes:**
[Any additional context, warnings, or suggestions]

---
```

---

## Completed Handoffs (Recent)

### ✅ Schema Audit - December 2, 2025

**From:** Web Claude  
**Result:** Comprehensive audit of org7bdbc942 environment completed

**Files Created:**
- `C:\RESA_Power_Build\Documentation\SCHEMA_AUDIT_org7bdbc942_Dec2025.md`
- `C:\RESA_Power_Build\Sessions\SESSION_PROTOCOL.md`
- `C:\RESA_Power_Build\Sessions\CURRENT_STATE.md`
- `C:\RESA_Power_Build\Sessions\HANDOFF.md`

**Key Findings:**
- 9 tables deployed, 7 pending (by design)
- All relationships verified working
- V2 naming conventions confirmed
- Ready for revenue recognition table deployment

---

## Handoff Best Practices

1. **Be specific** - Vague tasks lead to wrong outcomes
2. **Include file paths** - Always use full paths from `C:\RESA_Power_Build\`
3. **List dependencies** - What must exist before starting
4. **Define done** - Clear acceptance criteria
5. **Update CURRENT_STATE.md** - When picking up or completing a handoff

---

## Instance Identification

| Instance | Typical Use | Strengths |
|----------|-------------|-----------|
| **Web Claude** | Documentation, planning, audits | Long context, file creation, research |
| **VS Claude** | Code generation, build specs, implementation | IDE integration, code execution |

---

*Handoff file maintained per SESSION_PROTOCOL.md*
