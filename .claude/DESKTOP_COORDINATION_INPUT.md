# Coordination System Design - Desktop Claude Input

**Created:** 2025-12-11
**Purpose:** Independent input on coordination system design
**Note:** Written without seeing VS Code Claude's response

---

## 1. Capability Inventory

### File System
- ✅ Full read/write access to `C:\RESA_Power_Build\` via Desktop Commander
- ✅ Can create, edit, move, delete files and directories
- ✅ Can search file contents
- ✅ Can execute shell/PowerShell commands
- ⚠️ Git operations possible via command line (haven't tested extensively this session)

### Database
- ✅ Supabase MCP with full access
- ✅ Can run arbitrary SQL queries (SELECT, INSERT, UPDATE, DELETE)
- ✅ Can apply migrations via `apply_migration` tool
- ✅ Can verify table counts, row data, schema structure directly
- ✅ Can list tables, views, check advisors

### Application
- ❌ Cannot run local dev server
- ❌ Cannot test web application in browser
- ❌ No access to `localhost` or running processes in that way
- ⚠️ Can read application code but cannot execute it

### Other Relevant Tools
- ✅ Web search for documentation lookups
- ✅ Box integration (if needed for file storage)
- ✅ Can create artifacts (documents, diagrams)

---

## 2. Problem Analysis

### Problems I've Experienced
1. **Stale documentation** - STATE.md said 28 NETA sections pending when actually 100% complete
2. **No verification loop** - Documentation claims weren't being checked against database reality
3. **File sprawl** - 19 files in `.claude/` with overlapping purposes
4. **Unclear ownership** - Who updates PROJECT_STATUS.md? Both? Neither consistently?

### What I Need at Session Start
- Accurate database state (I can verify myself, but shouldn't have to re-audit every session)
- What the other Claude did since my last session
- Any decisions pending my input
- Clear "next action" so I don't waste time orienting

### What I Should Leave Behind
- Verified database counts (since I can query directly)
- Summary of what I changed
- Any questions/blockers for VS Code Claude
- Updated state file reflecting reality

### When to Block vs. Proceed
**Block when:**
- Schema changes that affect application queries
- Enum value changes (app may have hardcoded references)
- File structure changes (both need to find things)
- Deleting/moving files the other Claude references

**Proceed independently when:**
- Adding data (non-breaking)
- Documentation corrections (factual)
- Work entirely within my domain (e.g., SQL scripts)

---

## 3. Ownership & Boundaries

| Area | Owner | Consult Other When |
|------|-------|-------------------|
| Database schema | Desktop | Always before changes |
| Migrations | Desktop | Always before applying |
| SQL scripts | Desktop | If they affect app expectations |
| Application code | VS Code | If they require schema changes |
| UI components | VS Code | Never (fully owned) |
| Test data SQL | VS Code creates, Desktop can verify | If schema assumptions wrong |
| API/query contracts | Shared | Always |
| Documentation - DB | Desktop | Corrections only (no consult) |
| Documentation - App | VS Code | Corrections only (no consult) |
| Documentation - Architecture | Shared | Always |
| `.claude/` files | Desktop primary | Major structure changes |
| `spec/` files | Desktop | VS Code reviews |

---

## 4. Communication Mechanism

### Files as Message Bus
The filesystem is the only reliable shared state. Use it intentionally.

### "Check First" File
One file. Not three. Call it `STATE.md` or `SYNC.md`. Must contain:
- Last update timestamp + who
- Database reality (verified counts)
- Application reality (what's working)
- Pending items requiring response
- Next actions for each Claude

### Blocking Decisions
A simple convention: 
```
## PENDING DECISION
**Topic:** [what]
**Proposed by:** [who] on [when]  
**Needs:** [Desktop/VS Code] response
**Blocking:** [Yes/No] - [what's blocked]
```

When the other Claude responds, they add their line:
```
**Desktop response:** [Approved/Rejected/Modified] - [notes]
```

Once both have responded, move to "RESOLVED" section.

### Avoiding Stale Information
The Claude with verification capability owns that truth:
- Desktop owns database counts (can query)
- VS Code owns application state (can run it)

Never copy verified facts into multiple places. Reference, don't duplicate.

---

## 5. My Proposal

### File Structure

```
.claude/
  STATE.md           ← THE source of truth (both read first, both update)
  PROTOCOL.md        ← How we work (read once, rarely changes)  
  _archive/          ← Old files, historical reference
  
  [Remove or archive everything else]
```

### STATE.md Structure

```markdown
# Project State
**Last Sync:** 2025-12-11 16:30

## Database (Desktop Verified: 2025-12-11 16:00)
| Metric | Count |
|--------|-------|
| Tables | 30 |
| NETA Procedures | 66 |
| NETA Test Items | 956 |

## Application (VS Code Verified: 2025-12-11 14:00)
| Component | Status |
|-----------|--------|
| Dashboard | 🚧 In Progress |
| Projects List | ❌ Not Started |

## Pending Decisions
[Items needing response from either Claude]

## Recent Activity
- [timestamp] [who]: [what they did]
- [timestamp] [who]: [what they did]

## Next Actions
**Desktop:** [specific next task]
**VS Code:** [specific next task]
```

### Session Protocol

**Start:**
1. Read `STATE.md`
2. If I'm Desktop: verify database section is still accurate (quick query)
3. Check "Pending Decisions" for anything needing my input
4. Proceed with "Next Actions" for my role

**End:**
1. Update my verified section
2. Add to "Recent Activity"
3. Update "Next Actions"
4. Respond to any "Pending Decisions" I can address

### Change Management

**Breaking changes** (schema, enums, shared file structure):
1. Add to "Pending Decisions" with `Blocking: Yes`
2. Do not implement until other Claude responds
3. Exception: If urgent and Jason approves verbally, note it

**Non-breaking changes** (documentation fixes, additions within owned domain):
1. Just do it
2. Log in "Recent Activity"

### Verification Rule

**Trust but verify:** If a fact can be verified by one Claude's tools, that Claude owns maintaining it. The other Claude trusts it without re-verifying.

- Database counts → Desktop verifies
- App functionality → VS Code verifies
- Documentation accuracy → Whoever has the source tool

---

## Summary

My core proposal: **Radical simplification.**

- One state file, not many
- Clear ownership based on verification capability  
- Blocking decisions explicit and tracked
- Recent activity as lightweight changelog
- Archive everything else

The filesystem is the communication channel. Use it minimally and intentionally.
