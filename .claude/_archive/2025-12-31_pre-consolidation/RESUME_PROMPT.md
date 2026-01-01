# RESA Power Project - Resume Prompt

## Quick Resume (Copy & Paste This)

```
RESA Power Project - Resume Session

Workspace: C:\RESA_Power_Build\

Read the state file first:
C:\RESA_Power_Build\.claude\STATE.md

Confirm current phase and next actions, then continue.
```

---

## Shortest Version

```
Read C:\RESA_Power_Build\.claude\STATE.md and continue RESA Power project.
```

---

## If Claude Seems Confused

```
RESA Power project workspace: C:\RESA_Power_Build\

Key files:
- .claude/STATE.md - Current status (READ THIS FIRST)
- .claude/SESSION_PROTOCOL.md - How sessions work
- spec/ - Specification documents
- Supabase/schema/ - SQL files (00-05)
- Supabase/data/ - Test data files (10-12)

Read STATE.md and tell me what phase we're in.
```

---

## Full Context Prompt (Use If Starting Fresh)

```
RESA Power Database Project

WORKSPACE: C:\RESA_Power_Build\

PROJECT CONTEXT:
- Building Supabase PostgreSQL database for RESA Power (field service company)
- PSS Portal (Power System Studies tracking)
- Field testing project management
- Migrating from Microsoft Dataverse

APPROACH: Spec-first development
- 5 spec documents before any SQL
- Then schema generation from specs
- Then test data

COLLABORATION:
- Desktop Claude: Specs + Schema SQL
- VS Code Claude: Test data + Documentation

FIRST ACTION:
Read C:\RESA_Power_Build\.claude\STATE.md and confirm:
1. What phase are we in?
2. What's complete?
3. What should I do next?
```

---

## Session Rules Reminder

| Rule | Why |
|------|-----|
| Read STATE.md first | Instant context |
| Keep under 50 messages | Quality degrades after |
| Update STATE.md at end | Next session knows where we are |
| Use explicit file paths | Claude can't search/guess |
| Fresh chats are OK | Clean context = better work |

---

## Key Paths Reference

```
State:    C:\RESA_Power_Build\.claude\STATE.md
Protocol: C:\RESA_Power_Build\.claude\SESSION_PROTOCOL.md
Specs:    C:\RESA_Power_Build\spec\
Schema:   C:\RESA_Power_Build\Supabase\schema\
Data:     C:\RESA_Power_Build\Supabase\data\
Docs:     C:\RESA_Power_Build\Supabase\docs\
```

---

*Keep this file handy for starting new Claude sessions*
