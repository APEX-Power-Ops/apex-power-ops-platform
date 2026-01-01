# Coordination Protocol

How Desktop Claude and VS Code Claude coordinate on RESA Power.

---

## Core Principles

1. **Single source of truth:** `SYNC.md` is THE state file
2. **Trust but verify:** Owner of capability verifies their domain
3. **Blocking is explicit:** Schema changes block until both approve
4. **Files are messages:** The filesystem is our communication channel

---

## Ownership Model

| Domain | Owner | Consult When |
|--------|-------|--------------|
| Database schema | Desktop | Always before changes |
| Migrations | Desktop | Always before applying |
| SQL scripts | Desktop | If app expectations affected |
| Application code | VS Code | If schema changes needed |
| UI components | VS Code | Never (fully owned) |
| API contracts | Shared | Always |
| Coordination files | Desktop primary | Major structure changes |
| Specifications | Desktop | VS Code reviews |

---

## Session Protocol

### On Start
1. Read `SYNC.md`
2. Check `HANDOFFS/TO_[YOUR_NAME].md` for messages
3. Verify your domain state if stale (>24h)
4. Check "Pending Decisions" for items needing response

### On End
1. Update your verified section in `SYNC.md`
2. Add entry to `SESSION_LOG.md`
3. Respond to any pending decisions you can address
4. Update "Next Actions" for both roles
5. Drop messages in `HANDOFFS/TO_[OTHER].md` if needed

---

## Change Levels

| Level | Type | Action |
|-------|------|--------|
| 0 | Read-only | No coordination needed |
| 1 | Additive (new data, new files) | Log in SYNC.md, proceed |
| 2 | Modification (update existing) | Log in SYNC.md, proceed with care |
| 3 | Breaking (schema, enums, contracts) | Add to Pending Decisions, WAIT for approval |

### Level 3 Examples (Must Block)
- Adding/removing database columns
- Changing enum values
- Modifying view definitions
- Changing file structures both rely on
- Deleting files the other Claude references

---

## Verification Responsibility

| What | Who Verifies | How |
|------|--------------|-----|
| Database counts | Desktop | SQL query |
| Schema accuracy | Desktop | Compare to Supabase |
| App functionality | VS Code | Run dev server, test |
| Documentation accuracy | Topic owner | Direct verification |

---

## Communication Patterns

### Quick Update (Level 1-2)
Just add to `SYNC.md` Recent Activity section.

### Need Input (Level 2-3)
1. Add to `HANDOFFS/TO_[OTHER].md`
2. Update "Pending Decisions" in `SYNC.md` if blocking

### Decision Required (Level 3)
```markdown
### [Topic]
**Proposed by:** [who] on [date]
**Needs:** [who] response  
**Blocking:** Yes - [what's blocked]
**Details:** [explanation]

**Desktop:** ⏳ Pending
**VS Code:** ⏳ Pending
```

---

## File Locations

| File | Purpose | Read Frequency |
|------|---------|----------------|
| `SYNC.md` | Current state | Every session start |
| `SESSION_LOG.md` | History | When need context |
| `PROTOCOL.md` | Rules | Once, reference as needed |
| `HANDOFFS/TO_DESKTOP.md` | Desktop's inbox | Desktop reads each session |
| `HANDOFFS/TO_VSCODE.md` | VS Code's inbox | VS Code reads each session |
